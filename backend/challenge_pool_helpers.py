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
    challenges_per_type: int = 10
) -> int:
    """
    Copy random reference challenges to user's pool
    Used for new users to give instant challenges

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        challenges_per_type: Number per type (default 10)

    Returns:
        Number of challenges copied
    """
    try:
        print(f"[POOL_HELPER] 📋 Copying {challenges_per_type} reference challenges per type for new user")

        reference_collection = await get_reference_challenges_collection()
        pool_collection = await get_pool_collection()

        challenge_types = [
            "error_spotting",
            "swipe_fix",
            "micro_quiz",
            "smart_flashcard",
            "native_check",
            "brain_tickler"
        ]

        pool_items = []

        for challenge_type in challenge_types:
            # Get random reference challenges of this type and level
            cursor = reference_collection.aggregate([
                {
                    "$match": {
                        "cefr_level": user_level,
                        "challenge_type": challenge_type
                    }
                },
                {"$sample": {"size": challenges_per_type}}
            ])

            reference_challenges = await cursor.to_list(length=challenges_per_type)

            # Copy to user's pool
            for ref_challenge in reference_challenges:
                pool_item = {
                    "user_id": user_id,
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
    challenges_needed: int
) -> int:
    """
    Generate AI-powered personalized challenges
    Used for active users who need fresh content

    Args:
        user_id: User ID
        user_level: CEFR level
        challenges_needed: Total number needed

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
            batch = await generate_challenges_with_ai(user_id, user_level)
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
        is_new_user: True if user has no activity history

    Returns:
        Dict of counts per type
    """
    try:
        pool_collection = await get_pool_collection()

        challenge_types = [
            "error_spotting",
            "swipe_fix",
            "micro_quiz",
            "smart_flashcard",
            "native_check",
            "brain_tickler"
        ]

        # Get current counts - FILTER BY CEFR LEVEL!
        counts = {}
        total = 0
        needs_replenishment = False

        print(f"[POOL_HELPER] 📊 Counting challenges for user {user_id}, level: {user_level}")

        for challenge_type in challenge_types:
            count = await pool_collection.count_documents({
                "user_id": user_id,
                "challenge_type": challenge_type,
                "cefr_level": user_level,  # ← FIX: Filter by CEFR level
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
                await copy_reference_to_pool(user_id, user_level, TARGET_CHALLENGES_PER_TYPE)
            else:
                print(f"[POOL_HELPER] 🔄 Existing user - generating personalized")
                await generate_personalized_challenges(
                    user_id,
                    user_level,
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
                30  # Generate ~30 new challenges
            )

        # Recalculate counts - FILTER BY CEFR LEVEL!
        final_counts = {}
        for challenge_type in challenge_types:
            count = await pool_collection.count_documents({
                "user_id": user_id,
                "challenge_type": challenge_type,
                "cefr_level": user_level,  # ← FIX: Filter by CEFR level
                "status": "available"
            })
            final_counts[challenge_type] = count

        final_counts["total"] = sum(final_counts.values())

        print(f"[POOL_HELPER] ✅ Final counts for level {user_level}: {final_counts}")

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
