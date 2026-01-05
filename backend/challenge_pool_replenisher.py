"""
Challenge Pool Replenishment Service
Runs daily to replenish completed challenges in users' pools
Ensures each user always has 50 available challenges per type
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from database import database

# Feature flag: Choose between simple AI or CrewAI agents
USE_CREWAI = os.getenv("USE_CREWAI", "false").lower() == "true"

if USE_CREWAI:
    print("[REPLENISH] 🤖 Using CrewAI Multi-Agent System")
    from challenge_generator_crew import generate_challenges_with_ai
else:
    print("[REPLENISH] 🔄 Using Simple AI Generation")
    from challenge_generator_ai import generate_challenges_with_ai


async def replenish_user_pool(user_id: str, user_level: str, target_per_type: int = 50) -> Dict[str, Any]:
    """
    Replenish a single user's challenge pool

    Args:
        user_id: User ID
        user_level: CEFR level
        target_per_type: Target number of available challenges per type (default 50)

    Returns:
        Dict with replenishment stats
    """
    try:
        print(f"[REPLENISH] 🔄 Checking user {user_id} (level: {user_level})")

        pool_collection = database.challenge_pool

        challenge_types = [
            "error_spotting",
            "swipe_fix",
            "micro_quiz",
            "smart_flashcard",
            "native_check",
            "brain_tickler"
        ]

        stats = {
            "user_id": user_id,
            "types_replenished": 0,
            "challenges_added": 0,
            "by_type": {}
        }

        # Check each type and replenish if needed
        for challenge_type in challenge_types:
            # Count available challenges of this type
            available_count = await pool_collection.count_documents({
                "user_id": user_id,
                "challenge_type": challenge_type,
                "status": "available"
            })

            needed = target_per_type - available_count

            if needed > 0:
                print(f"[REPLENISH]   - {challenge_type}: {available_count}/{target_per_type} (need {needed})")

                # Generate batches to fill the gap
                # Each AI call generates 6 challenges (1 of each type)
                # We only take the one we need from each batch
                challenges_generated = []

                # Generate enough batches to get the needed challenges
                batches_needed = needed
                for batch_num in range(batches_needed):
                    batch = await generate_challenges_with_ai(user_id, user_level)

                    if batch and len(batch) > 0:
                        # Extract the challenge of the type we need
                        for challenge in batch:
                            if challenge.get("type") == challenge_type:
                                challenges_generated.append(challenge)
                                break

                # Insert generated challenges into pool
                if challenges_generated:
                    pool_items = []
                    for challenge in challenges_generated:
                        pool_item = {
                            "user_id": user_id,
                            "cefr_level": user_level,
                            "challenge_type": challenge_type,
                            "challenge_data": challenge,
                            "status": "available",
                            "created_at": datetime.utcnow(),
                            "completed_at": None,
                            "expires_at": datetime.utcnow() + timedelta(days=30)
                        }
                        pool_items.append(pool_item)

                    if pool_items:
                        result = await pool_collection.insert_many(pool_items)
                        added = len(result.inserted_ids)

                        stats["types_replenished"] += 1
                        stats["challenges_added"] += added
                        stats["by_type"][challenge_type] = added

                        print(f"[REPLENISH]     ✅ Added {added} {challenge_type} challenges")
            else:
                print(f"[REPLENISH]   - {challenge_type}: {available_count}/{target_per_type} ✓")

        if stats["challenges_added"] > 0:
            print(f"[REPLENISH] ✅ User {user_id}: Added {stats['challenges_added']} challenges")
        else:
            print(f"[REPLENISH] ✓ User {user_id}: Pool is full")

        return stats

    except Exception as e:
        print(f"[REPLENISH] ❌ Error replenishing user {user_id}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "user_id": user_id,
            "types_replenished": 0,
            "challenges_added": 0,
            "error": str(e)
        }


async def replenish_all_users(target_per_type: int = 50):
    """
    Replenish challenge pools for all active users

    This should run daily via cron job or scheduler
    Only replenishes users with:
    - Active subscription OR
    - Recent activity (sessions in last 30 days)

    Args:
        target_per_type: Target number of available challenges per type (default 50)
    """
    try:
        print(f"\n{'='*70}")
        print(f"[REPLENISH] 🔄 Starting Daily Pool Replenishment")
        print(f"[REPLENISH] 📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"[REPLENISH] 🎯 Target: {target_per_type} available per type")
        print(f"{'='*70}\n")

        users_collection = database.users
        sessions_collection = database.conversation_sessions

        # Get all users with is_active=True
        all_users = await users_collection.find({
            "is_active": True
        }).to_list(length=None)

        # Filter to truly active users (subscription or recent activity)
        print(f"[REPLENISH] 🔍 Filtering active users...")
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = []

        for user in all_users:
            user_id = str(user["_id"])
            user_email = user.get("email", "")

            # Skip test accounts
            if "test" in user_email.lower() or "demo" in user_email.lower():
                continue

            # Check subscription or activity
            subscription_status = user.get("subscription_status")
            has_active_sub = subscription_status in ["active", "trialing"]

            if has_active_sub:
                active_users.append(user)
                continue

            # Check recent activity
            session_count = await sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": thirty_days_ago}
            })

            if session_count > 0:
                active_users.append(user)

        users = active_users

        print(f"[REPLENISH] 👥 Found {len(users)} active users\n")

        total_challenges_added = 0
        users_replenished = 0

        for idx, user in enumerate(users, 1):
            user_id = str(user["_id"])
            user_level = user.get("preferred_level") or "B1"
            user_email = user.get("email", "Unknown")

            print(f"[REPLENISH] 👤 User {idx}/{len(users)}: {user_email}")

            stats = await replenish_user_pool(user_id, user_level, target_per_type)

            if stats["challenges_added"] > 0:
                total_challenges_added += stats["challenges_added"]
                users_replenished += 1

            print()  # Blank line between users

        print(f"{'='*70}")
        print(f"[REPLENISH] 🎉 Daily Replenishment Complete!")
        print(f"[REPLENISH] ✅ Replenished pools for {users_replenished}/{len(users)} users")
        print(f"[REPLENISH] 📊 Total challenges added: {total_challenges_added}")
        print(f"[REPLENISH] 📅 Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"[REPLENISH] ❌ Error during replenishment: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def cleanup_expired_challenges():
    """
    Clean up expired challenges
    MongoDB TTL index should handle this automatically, but this is a manual backup

    IMPORTANT: Only delete AVAILABLE challenges that have expired.
    Completed challenges should be preserved indefinitely for user history.
    """
    try:
        print(f"[REPLENISH] 🧹 Cleaning up expired challenges...")

        pool_collection = database.challenge_pool

        # Find and delete ONLY available (not completed) expired challenges
        # This preserves users' completed challenge history
        result = await pool_collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()},
            "status": "available"  # Only delete available challenges, preserve completed ones
        })

        if result.deleted_count > 0:
            print(f"[REPLENISH] 🗑️ Deleted {result.deleted_count} expired available challenges")
        else:
            print(f"[REPLENISH] ✓ No expired available challenges to clean up")

    except Exception as e:
        print(f"[REPLENISH] ⚠️ Error cleaning up: {str(e)}")


async def run_daily_job():
    """
    Main daily job entry point
    Run this via cron or scheduler
    """
    # Cleanup expired challenges first
    await cleanup_expired_challenges()

    # Replenish all user pools
    await replenish_all_users(target_per_type=50)


if __name__ == "__main__":
    # Run the daily job
    asyncio.run(run_daily_job())
