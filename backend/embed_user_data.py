"""
Embed User Data to Pinecone Vector Database
Populates vector DB with existing user content for semantic search
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    users_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,
    flashcard_sets_collection,
    learning_plans_collection,
    session_completions_collection,
    assessments_collection
)
from services.vector_db_service import vector_db
from services.rich_embedding_service import RichEmbeddingBuilder, RichEmbeddingQualityValidator
from bson import ObjectId

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def embed_conversations(user_id: str) -> int:
    """
    Embed user's conversation sessions with RICH CONTENT.

    NEW: Uses RichEmbeddingBuilder for high-quality embeddings
    - Includes actual conversation content
    - Extracts topics, vocabulary, highlights
    - Validates quality before embedding
    """
    try:
        conversations = await conversation_sessions_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)

        if not conversations:
            logger.info(f"  No conversations found for user {user_id}")
            return 0

        logger.info(f"  Embedding {len(conversations)} conversations with rich content...")

        contents = []
        quality_stats = {"high": 0, "medium": 0, "low": 0, "invalid": 0, "filtered": 0}

        for conv in conversations:
            # PHASE 1 FIX: Filter low-quality sessions BEFORE embedding
            should_embed, reason = RichEmbeddingBuilder.should_embed_session(conv)

            if not should_embed:
                quality_stats["filtered"] += 1
                logger.debug(f"    Session {conv.get('_id')} SKIPPED: {reason}")
                continue

            # Build RICH embedding text (topic + conversation + highlights + vocabulary)
            text = RichEmbeddingBuilder.build_conversation_embedding(conv)

            # Build metadata
            metadata = RichEmbeddingBuilder.build_metadata(conv, user_id)

            # Validate quality
            validation = RichEmbeddingQualityValidator.validate(text, metadata)

            # Track quality stats
            score = validation["quality_score"]
            if score >= 0.8:
                quality_stats["high"] += 1
            elif score >= 0.6:
                quality_stats["medium"] += 1
            elif score >= 0.4:
                quality_stats["low"] += 1
            else:
                quality_stats["invalid"] += 1

            # Log warnings for low-quality embeddings
            if validation["warnings"]:
                logger.debug(f"    Session {conv.get('_id')}: Quality {score:.2f} - {validation['warnings'][0]}")

            # Add to batch (even low quality - better than nothing)
            contents.append({
                "id": f"conv_{user_id}_{str(conv['_id'])}",
                "text": text,
                "metadata": metadata
            })

        # Log quality summary
        logger.info(f"    Quality: {quality_stats['high']} high, {quality_stats['medium']} medium, "
                   f"{quality_stats['low']} low, {quality_stats['invalid']} invalid, "
                   f"{quality_stats['filtered']} filtered (billing placeholders)")

        return await vector_db.upsert_batch(contents)

    except Exception as e:
        logger.error(f"  ❌ Failed to embed conversations: {str(e)}")
        return 0


async def embed_challenges(user_id: str) -> int:
    """Embed user's challenge sessions"""
    try:
        challenges = await challenge_sessions_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)

        if not challenges:
            logger.info(f"  No challenges found for user {user_id}")
            return 0

        logger.info(f"  Embedding {len(challenges)} challenge sessions...")

        contents = []
        for challenge in challenges:
            # Build searchable text
            text_parts = [
                f"Challenge Type: {challenge.get('challenge_type', 'unknown')}",
                f"Language: {challenge.get('language', 'unknown')}",
                f"Level: {challenge.get('level', 'unknown')}",
            ]

            # Add challenge content
            if challenge.get("challenge_data"):
                data = challenge["challenge_data"]
                if isinstance(data, dict):
                    if data.get("title"):
                        text_parts.append(f"Title: {data['title']}")
                    if data.get("content"):
                        text_parts.append(f"Content: {data['content']}")
                    if data.get("question"):
                        text_parts.append(f"Question: {data['question']}")

            # Add result
            if challenge.get("is_correct") is not None:
                text_parts.append(f"Result: {'correct' if challenge['is_correct'] else 'incorrect'}")

            text = " | ".join(text_parts)

            contents.append({
                "id": f"challenge_{user_id}_{str(challenge['_id'])}",
                "text": text,
                "metadata": {
                    "user_id": user_id,
                    "content_type": "challenge",
                    "challenge_type": challenge.get("challenge_type", "unknown"),
                    "language": challenge.get("language", "unknown"),
                    "level": challenge.get("level", "unknown"),
                    "is_correct": challenge.get("is_correct", False),
                    "created_at": challenge.get("created_at", datetime.utcnow()).isoformat(),
                }
            })

        return await vector_db.upsert_batch(contents)

    except Exception as e:
        logger.error(f"  ❌ Failed to embed challenges: {str(e)}")
        return 0


async def embed_flashcards(user_id: str) -> int:
    """Embed user's flashcard sets"""
    try:
        flashcard_sets = await flashcard_sets_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)

        if not flashcard_sets:
            logger.info(f"  No flashcard sets found for user {user_id}")
            return 0

        logger.info(f"  Embedding {len(flashcard_sets)} flashcard sets...")

        contents = []
        for fs in flashcard_sets:
            # Build searchable text
            text_parts = [
                f"Flashcard Set: {fs.get('title', 'Untitled')}",
                f"Language: {fs.get('language', 'unknown')}",
                f"Level: {fs.get('level', 'unknown')}",
                f"Total Cards: {fs.get('total_cards', 0)}",
                f"Mastered: {fs.get('mastered_cards', 0)}",
            ]

            if fs.get("created_from"):
                text_parts.append(f"Source: {fs['created_from']}")

            text = " | ".join(text_parts)

            contents.append({
                "id": f"flashcard_{user_id}_{str(fs['_id'])}",
                "text": text,
                "metadata": {
                    "user_id": user_id,
                    "content_type": "flashcard_set",
                    "language": fs.get("language", "unknown"),
                    "level": fs.get("level", "unknown"),
                    "total_cards": fs.get("total_cards", 0),
                    "mastered_cards": fs.get("mastered_cards", 0),
                    "created_at": fs.get("created_at", datetime.utcnow()).isoformat(),
                }
            })

        return await vector_db.upsert_batch(contents)

    except Exception as e:
        logger.error(f"  ❌ Failed to embed flashcards: {str(e)}")
        return 0


async def embed_learning_plans(user_id: str) -> int:
    """Embed user's learning plans"""
    try:
        plans = await learning_plans_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)

        if not plans:
            logger.info(f"  No learning plans found for user {user_id}")
            return 0

        logger.info(f"  Embedding {len(plans)} learning plans...")

        contents = []
        for plan in plans:
            # Build searchable text
            text_parts = [
                f"Learning Plan: {plan.get('language', 'unknown')} {plan.get('level', 'unknown')}",
                f"Progress: {plan.get('completed_sessions', 0)}/{plan.get('total_sessions', 0)} sessions",
            ]

            if plan.get("goal"):
                text_parts.append(f"Goal: {plan['goal']}")

            if plan.get("plan_objective"):
                text_parts.append(f"Objective: {plan['plan_objective']}")

            text = " | ".join(text_parts)

            contents.append({
                "id": f"plan_{user_id}_{str(plan['_id'])}",
                "text": text,
                "metadata": {
                    "user_id": user_id,
                    "content_type": "learning_plan",
                    "language": plan.get("language", "unknown"),
                    "level": plan.get("level", "unknown"),
                    "completed_sessions": plan.get("completed_sessions", 0),
                    "total_sessions": plan.get("total_sessions", 0),
                    "created_at": plan.get("created_at", datetime.utcnow()).isoformat(),
                }
            })

        return await vector_db.upsert_batch(contents)

    except Exception as e:
        logger.error(f"  ❌ Failed to embed learning plans: {str(e)}")
        return 0


async def embed_assessments(user_id: str) -> int:
    """Embed user's assessments"""
    try:
        assessments = await assessments_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)

        if not assessments:
            logger.info(f"  No assessments found for user {user_id}")
            return 0

        logger.info(f"  Embedding {len(assessments)} assessments...")

        contents = []
        for assessment in assessments:
            # Build searchable text
            text_parts = [
                f"Assessment: {assessment.get('language', 'unknown')} {assessment.get('level', 'unknown')}",
                f"Score: {assessment.get('score', 0)}%",
            ]

            if assessment.get("feedback"):
                text_parts.append(f"Feedback: {assessment['feedback']}")

            text = " | ".join(text_parts)

            contents.append({
                "id": f"assessment_{user_id}_{str(assessment['_id'])}",
                "text": text,
                "metadata": {
                    "user_id": user_id,
                    "content_type": "assessment",
                    "language": assessment.get("language", "unknown"),
                    "level": assessment.get("level", "unknown"),
                    "score": assessment.get("score", 0),
                    "created_at": assessment.get("created_at", datetime.utcnow()).isoformat(),
                }
            })

        return await vector_db.upsert_batch(contents)

    except Exception as e:
        logger.error(f"  ❌ Failed to embed assessments: {str(e)}")
        return 0


async def embed_user_all_content(user_id: str) -> Dict[str, int]:
    """
    Embed all content for a single user

    Returns:
        Dict with counts of embedded items per type
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Embedding all content for user: {user_id}")
    logger.info(f"{'='*60}")

    results = {
        "conversations": await embed_conversations(user_id),
        "challenges": await embed_challenges(user_id),
        "flashcards": await embed_flashcards(user_id),
        "learning_plans": await embed_learning_plans(user_id),
        "assessments": await embed_assessments(user_id),
    }

    total = sum(results.values())
    logger.info(f"\n✅ Total embedded for user {user_id}: {total} items")
    logger.info(f"   Breakdown: {results}")

    return results


async def embed_all_users(limit: int = None):
    """
    Embed content for all users

    Args:
        limit: Maximum number of users to process (None = all)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"EMBEDDING ALL USER DATA TO PINECONE")
    logger.info(f"{'='*60}\n")

    # Get all users
    users_cursor = users_collection.find()
    if limit:
        users_cursor = users_cursor.limit(limit)

    users = await users_cursor.to_list(length=limit or 1000)

    logger.info(f"Found {len(users)} users to process\n")

    all_results = {}
    total_items = 0

    for i, user in enumerate(users, 1):
        user_id = str(user["_id"])
        email = user.get("email", "N/A")

        logger.info(f"\n[{i}/{len(users)}] Processing: {email} ({user_id})")

        try:
            results = await embed_user_all_content(user_id)
            all_results[user_id] = results
            total_items += sum(results.values())

        except Exception as e:
            logger.error(f"❌ Failed to process user {user_id}: {str(e)}")
            all_results[user_id] = {"error": str(e)}

        # Small delay to avoid rate limiting
        if i < len(users):
            await asyncio.sleep(0.5)

    # Print summary
    logger.info(f"\n\n{'='*60}")
    logger.info(f"EMBEDDING COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total users processed: {len(users)}")
    logger.info(f"Total items embedded: {total_items}")

    # Get index stats
    stats = vector_db.get_index_stats()
    logger.info(f"\nPinecone Index Stats:")
    logger.info(f"  Total vectors: {stats.get('total_vectors', 0):,}")
    logger.info(f"  Dimensions: {stats.get('dimensions', 0)}")
    logger.info(f"  Index fullness: {stats.get('index_fullness', 0):.2%}")

    logger.info(f"\n✅ Embedding pipeline complete!")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Embed user data to Pinecone")
    parser.add_argument("--user-id", help="Embed data for specific user only")
    parser.add_argument("--limit", type=int, help="Limit number of users to process")
    args = parser.parse_args()

    if args.user_id:
        # Single user
        await embed_user_all_content(args.user_id)
    else:
        # All users
        await embed_all_users(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
