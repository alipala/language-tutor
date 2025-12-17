"""
Updated Challenge Pool Replenishment Service
Uses Phase 3.1 approach: Copy from reference challenges first, AI only when needed
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from database import database
from challenge_pool_helpers import ensure_pool_has_challenges, is_new_user


async def replenish_user_pool_v2(
    user_id: str,
    user_level: str,
    language: str = "english"
) -> Dict[str, Any]:
    """
    Replenish a single user's challenge pool using new Phase 3.1 approach

    Strategy:
    1. Copy from reference challenges (3,643 available) - FAST & FREE
    2. Only use AI if reference challenges are exhausted

    Args:
        user_id: User ID
        user_level: CEFR level
        language: Target language (from learning plan)

    Returns:
        Dict with replenishment stats
    """
    try:
        print(f"[REPLENISH_V2] 🔄 Checking user {user_id} ({language} {user_level})")

        # Check if new user
        new_user = await is_new_user(user_id)

        # Use Phase 3.1 helper - handles everything automatically
        counts = await ensure_pool_has_challenges(
            user_id=user_id,
            user_level=user_level,
            language=language,
            is_new_user=new_user
        )

        total = counts.get("total", 0)

        if total > 0:
            print(f"[REPLENISH_V2] ✅ User {user_id}: Pool has {total} challenges")
        else:
            print(f"[REPLENISH_V2] ⚠️ User {user_id}: No challenges available")

        return {
            "user_id": user_id,
            "language": language,
            "level": user_level,
            "total_challenges": total,
            "by_type": counts
        }

    except Exception as e:
        print(f"[REPLENISH_V2] ❌ Error replenishing user {user_id}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "user_id": user_id,
            "error": str(e)
        }


async def replenish_all_users_v2():
    """
    Replenish challenge pools for all users with active learning plans
    Uses Phase 3.1 language-aware approach
    """
    try:
        print(f"\n{'='*80}")
        print(f"[REPLENISH_V2] 🔄 Starting Daily Pool Replenishment (Phase 3.1)")
        print(f"[REPLENISH_V2] 📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"[REPLENISH_V2] ✨ Using reference challenges (fast & free)")
        print(f"{'='*80}\n")

        # Get all active learning plans
        learning_plans_collection = database.learning_plans
        active_plans = await learning_plans_collection.find({
            "is_active": True
        }).to_list(length=None)

        print(f"[REPLENISH_V2] 📊 Found {len(active_plans)} active learning plans\n")

        users_processed = 0
        total_challenges = 0

        for idx, plan in enumerate(active_plans, 1):
            user_id = plan.get("user_id")
            language = plan.get("language", "english").lower()

            # Get user's preferred level
            user = await database.users.find_one({"_id": user_id})
            if not user:
                print(f"[REPLENISH_V2] ⚠️ User {user_id} not found, skipping...")
                continue

            user_level = user.get("preferred_level", "B1")
            user_email = user.get("email", "Unknown")

            print(f"[REPLENISH_V2] 👤 {idx}/{len(active_plans)}: {user_email}")
            print(f"[REPLENISH_V2]    Language: {language}, Level: {user_level}")

            # Replenish using Phase 3.1 approach
            stats = await replenish_user_pool_v2(user_id, user_level, language)

            if "error" not in stats:
                total_challenges += stats.get("total_challenges", 0)
                users_processed += 1

            print()  # Blank line

        print(f"{'='*80}")
        print(f"[REPLENISH_V2] 🎉 Daily Replenishment Complete!")
        print(f"[REPLENISH_V2] ✅ Processed {users_processed}/{len(active_plans)} users")
        print(f"[REPLENISH_V2] 📊 Total challenges available: {total_challenges}")
        print(f"[REPLENISH_V2] 📅 Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"[REPLENISH_V2] ❌ Error during replenishment: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def run_daily_job():
    """
    Main daily job entry point for Phase 3.1
    """
    await replenish_all_users_v2()


if __name__ == "__main__":
    print("🚀 Challenge Pool Replenisher V2 (Phase 3.1)")
    print("Uses reference challenges - fast & free!\n")
    asyncio.run(run_daily_job())
