"""
Challenge Pool Helper Functions
Clean, reusable functions for managing challenge pools
"""

import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database import database
from challenge_generator_ai import generate_challenges_with_ai


# Configuration
MIN_CHALLENGES_PER_TYPE = 10  # Trigger replenishment when below this
TARGET_CHALLENGES_PER_TYPE = 10  # Target to maintain


async def get_reference_challenges_collection():
    """Get reference challenges collection"""
    return database.reference_challenges


async def get_pool_collection():
    """Get user pool collection"""
    return database.challenge_pool


async def copy_reference_to_pool(
    user_id: str,
    user_level: str,
    language: str = "english",
    challenges_per_type: int = 10
) -> int:
    """
    Copy random reference challenges to user's pool
    Used for new users to give instant challenges

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        language: Target language (default: "english")
        challenges_per_type: Number per type (default 10)

    Returns:
        Number of challenges copied
    """
    try:
        print(f"[POOL_HELPER] 📋 Copying {challenges_per_type} reference challenges per type for new user")

        reference_collection = await get_reference_challenges_collection()
        pool_collection = await get_pool_collection()

        # XP rebalance PR2: dropped `swipe_fix` — no mobile screen implements it.
        challenge_types = [
            "error_spotting",
            "micro_quiz",
            "smart_flashcard",
            "native_check",
            "brain_tickler",
            "story_builder",
        ]

        pool_items = []

        for challenge_type in challenge_types:
            # Get random reference challenges of this type, level, and language
            cursor = reference_collection.aggregate([
                {
                    "$match": {
                        "cefr_level": user_level,
                        "challenge_type": challenge_type,
                        "language": language
                    }
                },
                {"$sample": {"size": challenges_per_type}}
            ])

            reference_challenges = await cursor.to_list(length=challenges_per_type)

            # Copy to user's pool
            for ref_challenge in reference_challenges:
                pool_item = {
                    "user_id": user_id,
                    "language": language,
                    "cefr_level": user_level,
                    "challenge_type": challenge_type,
                    "challenge_data": ref_challenge.get("challenge_data"),
                    "status": "available",
                    "created_at": datetime.utcnow(),
                    "completed_at": None,
                    "expires_at": datetime.utcnow() + timedelta(days=30)
                }
                pool_items.append(pool_item)

        if pool_items:
            result = await pool_collection.insert_many(pool_items)
            print(f"[POOL_HELPER] ✅ Copied {len(result.inserted_ids)} reference challenges")
            return len(result.inserted_ids)

        return 0

    except Exception as e:
        print(f"[POOL_HELPER] ❌ Error copying reference challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 0


async def generate_personalized_challenges(
    user_id: str,
    user_level: str,
    language: str = "english",
    challenges_needed: int = 30
) -> int:
    """
    Generate AI-powered personalized challenges
    Used for active users who need fresh content

    Args:
        user_id: User ID
        user_level: CEFR level
        language: Target language (default: "english")
        challenges_needed: Total number needed (default: 30)

    Returns:
        Number of challenges generated
    """
    try:
        print(f"[POOL_HELPER] 🤖 Generating {challenges_needed} personalized challenges")

        pool_collection = await get_pool_collection()

        # Calculate batches needed (each batch = 6 challenges)
        batches_needed = (challenges_needed + 5) // 6  # Round up

        challenges_by_type = {
            "error_spotting": [],
            "swipe_fix": [],
            "micro_quiz": [],
            "smart_flashcard": [],
            "native_check": [],
            "brain_tickler": []
        }

        # Generate batches
        for batch_num in range(batches_needed):
            batch = await generate_challenges_with_ai(user_id, user_level, language)
            if batch:
                for challenge in batch:
                    challenge_type = challenge.get("type")
                    if challenge_type in challenges_by_type:
                        challenges_by_type[challenge_type].append(challenge)

        # Insert into pool
        pool_items = []
        for challenge_type, challenges in challenges_by_type.items():
            for challenge in challenges:
                pool_items.append({
                    "user_id": user_id,
                    "language": language,
                    "cefr_level": user_level,
                    "challenge_type": challenge_type,
                    "challenge_data": challenge,
                    "status": "available",
                    "created_at": datetime.utcnow(),
                    "completed_at": None,
                    "expires_at": datetime.utcnow() + timedelta(days=30)
                })

        if pool_items:
            result = await pool_collection.insert_many(pool_items)
            print(f"[POOL_HELPER] ✅ Generated {len(result.inserted_ids)} personalized challenges")
            return len(result.inserted_ids)

        return 0

    except Exception as e:
        print(f"[POOL_HELPER] ❌ Error generating personalized challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 0


async def ensure_pool_has_challenges(
    user_id: str,
    user_level: str,
    language: str = "english",
    is_new_user: bool = False
) -> Dict[str, int]:
    """
    Main function: Ensures user has enough challenges

    Strategy:
    - New users: Copy from reference (instant)
    - Active users: Generate personalized (AI)
    - Auto-replenish when low

    Args:
        user_id: User ID
        user_level: CEFR level
        language: Target language (default: "english")
        is_new_user: True if user has no activity history

    Returns:
        Dict of counts per type
    """
    try:
        pool_collection = await get_pool_collection()

        # XP rebalance PR2: dropped `swipe_fix` — no mobile screen implements it.
        challenge_types = [
            "error_spotting",
            "micro_quiz",
            "smart_flashcard",
            "native_check",
            "brain_tickler"
        ]

        # Get current counts - FILTER BY LANGUAGE AND CEFR LEVEL!
        counts = {}
        total = 0
        needs_replenishment = False

        print(f"[POOL_HELPER] 📊 Counting challenges for user {user_id}, language: {language}, level: {user_level}")

        for challenge_type in challenge_types:
            count = await pool_collection.count_documents({
                "user_id": user_id,
                "language": language,
                "challenge_type": challenge_type,
                "cefr_level": user_level,
                "status": "available"
            })
            counts[challenge_type] = count
            total += count

            if count < MIN_CHALLENGES_PER_TYPE:
                needs_replenishment = True

        # SCENARIO 1: Completely empty (new user)
        if total == 0:
            if is_new_user:
                print(f"[POOL_HELPER] 🆕 New user - copying from reference")
                await copy_reference_to_pool(user_id, user_level, language, TARGET_CHALLENGES_PER_TYPE)
            else:
                print(f"[POOL_HELPER] 🔄 Existing user - generating personalized")
                await generate_personalized_challenges(
                    user_id,
                    user_level,
                    language,
                    TARGET_CHALLENGES_PER_TYPE * 6
                )

        # SCENARIO 2: Low on challenges (needs replenishment)
        elif needs_replenishment:
            print(f"[POOL_HELPER] ⚠️ Pool running low - replenishing")

            # Calculate how many needed per type
            for challenge_type in challenge_types:
                current = counts[challenge_type]
                if current < MIN_CHALLENGES_PER_TYPE:
                    needed = TARGET_CHALLENGES_PER_TYPE - current
                    print(f"[POOL_HELPER] 📊 {challenge_type}: {current}/{TARGET_CHALLENGES_PER_TYPE} (need {needed})")

            # Generate personalized challenges
            await generate_personalized_challenges(
                user_id,
                user_level,
                language,
                30  # Generate ~30 new challenges
            )

        # Recalculate counts - FILTER BY LANGUAGE AND CEFR LEVEL!
        final_counts = {}
        for challenge_type in challenge_types:
            count = await pool_collection.count_documents({
                "user_id": user_id,
                "language": language,
                "challenge_type": challenge_type,
                "cefr_level": user_level,
                "status": "available"
            })
            final_counts[challenge_type] = count

        final_counts["total"] = sum(final_counts.values())

        print(f"[POOL_HELPER] ✅ Final counts for language {language}, level {user_level}: {final_counts}")

        return final_counts

    except Exception as e:
        print(f"[POOL_HELPER] ❌ Error ensuring pool: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {}


async def is_new_user(user_id: str) -> bool:
    """
    Determine if user is new (no activity history)

    Checks:
    - Practice sessions
    - Learning plans
    - Flashcards

    Returns:
        True if new user, False if has activity
    """
    try:
        # Check practice sessions
        sessions_collection = database.conversation_sessions
        session_count = await sessions_collection.count_documents({
            "user_id": user_id
        })

        if session_count > 0:
            return False

        # Check learning plans
        learning_plans_collection = database.learning_plans
        plan_count = await learning_plans_collection.count_documents({
            "user_id": user_id
        })

        if plan_count > 0:
            return False

        # Check flashcards
        flashcards_collection = database.flashcards
        flashcard_count = await flashcards_collection.count_documents({
            "user_id": user_id
        })

        if flashcard_count > 0:
            return False

        # No activity found = new user
        return True

    except Exception as e:
        print(f"[POOL_HELPER] ⚠️ Error checking new user status: {str(e)}")
        # Default to False (existing user) to be safe
        return False


# ==================== REFERENCE CHALLENGES (FREESTYLE PRACTICE) ====================

async def get_reference_challenge_counts(
    language: str,
    level: str
) -> Dict[str, int]:
    """
    Get challenge counts from reference_challenges collection
    Fast - no AI generation, no pool management
    Used for Freestyle Practice mode

    Args:
        language: Target language (e.g., "french", "spanish")
        level: CEFR level (e.g., "C2", "B1")

    Returns:
        Dict of counts per type + total
    """
    try:
        print(f"[REFERENCE] 📊 Getting reference challenge counts for {language} {level}")

        reference_collection = await get_reference_challenges_collection()

        challenge_types = [
            "error_spotting",
            "swipe_fix",
            "micro_quiz",
            "smart_flashcard",
            "native_check",
            "brain_tickler",
            "story_builder"
        ]

        # Build aggregation pipeline to count by type
        pipeline = [
            {
                "$match": {
                    "language": language,
                    "cefr_level": level
                }
            },
            {
                "$group": {
                    "_id": "$challenge_type",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = await reference_collection.aggregate(pipeline).to_list(None)

        # Convert to dict
        counts = {item["_id"]: item["count"] for item in results}

        # Ensure all 7 types exist (even if 0)
        for challenge_type in challenge_types:
            if challenge_type not in counts:
                counts[challenge_type] = 0

        counts["total"] = sum(counts.values())

        print(f"[REFERENCE] ✅ Reference counts: {counts}")

        return counts

    except Exception as e:
        print(f"[REFERENCE] ❌ Error getting reference counts: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # Return empty counts on error
        return {
            "error_spotting": 0,
            "swipe_fix": 0,
            "micro_quiz": 0,
            "smart_flashcard": 0,
            "native_check": 0,
            "brain_tickler": 0,
            "story_builder": 0,
            "total": 0
        }


async def get_reference_challenges(
    challenge_type: str,
    language: str,
    level: str,
    limit: int = 50,
    user_id: str = None
) -> List[Dict[str, Any]]:
    """
    Get challenges from reference_challenges collection
    Fast - no AI generation, no pool management
    Used for Freestyle Practice mode

    Args:
        challenge_type: Type of challenge (e.g., "error_spotting")
        language: Target language (e.g., "french", "spanish")
        level: CEFR level (e.g., "C2", "B1")
        limit: Maximum number to return (default: 50)
        user_id: Optional user ID to exclude completed challenges

    Returns:
        List of challenge dictionaries (randomized and excluding completed)
    """
    try:
        print(f"[REFERENCE] 📚 Getting {limit} {challenge_type} challenges for {language} {level}")

        reference_collection = await get_reference_challenges_collection()

        # Get completed challenge IDs for this user (if provided)
        exclude_ids = []
        if user_id:
            challenge_sessions_collection = database.challenge_sessions
            completed_sessions = challenge_sessions_collection.find({
                "user_id": user_id
            })

            # Extract all challenge IDs from completed sessions
            async for session in completed_sessions:
                # NEW format: check for challenge_ids array (added for completion tracking)
                if "challenge_ids" in session:
                    exclude_ids.extend(session["challenge_ids"])
                # OLD format: check for challenges array (backward compatibility)
                elif "challenges" in session:
                    for challenge in session["challenges"]:
                        if "id" in challenge:
                            exclude_ids.append(challenge["id"])

            print(f"[REFERENCE] 🚫 Excluding {len(exclude_ids)} completed challenges")

        base_match = {
            "challenge_type": challenge_type,
            "language": language,
            "cefr_level": level
        }

        # Attempt 1: exclude completed challenges so the user sees fresh content
        pipeline = [{"$match": {**base_match, **({"challenge_data.id": {"$nin": exclude_ids}} if exclude_ids else {})}}]
        pipeline.append({"$sample": {"size": limit}})
        reference_challenges = await reference_collection.aggregate(pipeline).to_list(limit)

        # Attempt 2: if all challenges are exhausted, recycle — serve any challenges
        # (user has done them all; repeating is better than blocking them)
        if not reference_challenges and exclude_ids:
            print(f"[REFERENCE] ♻️  All {challenge_type}/{language}/{level} challenges completed — recycling")
            pipeline_recycle = [{"$match": base_match}, {"$sample": {"size": limit}}]
            reference_challenges = await reference_collection.aggregate(pipeline_recycle).to_list(limit)

        # Extract challenge_data from each reference challenge
        challenges = []
        for ref_item in reference_challenges:
            challenge_data = ref_item.get("challenge_data", {})
            if "_id" in challenge_data:
                challenge_data["_id"] = str(challenge_data["_id"])
            challenges.append(challenge_data)

        print(f"[REFERENCE] ✅ Found {len(challenges)} reference challenges (randomized)")

        return challenges

    except Exception as e:
        print(f"[REFERENCE] ❌ Error getting reference challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []
