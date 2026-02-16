"""
Reset Free User Usage - Monthly Cron Job

This cron job runs daily to check for free tier users whose billing period has expired
and resets their usage counters to give them a fresh monthly allocation.

Schedule: Runs daily at 2:00 AM UTC
Provider: Railway Cron Jobs
"""

from datetime import datetime
from database import database
from subscription_service import SubscriptionService
from logging_config import logger
import asyncio


async def reset_expired_free_user_periods():
    """
    Reset usage for free users whose billing period has expired

    Logic:
    1. Find all users on 'try_learn' plan
    2. Check if their current_period_end is in the past
    3. If they have non-zero usage, reset it
    4. Call SubscriptionService.reset_monthly_usage() for proper reset
    """
    try:
        now = datetime.utcnow()
        logger.info(f"[FREE_USER_RESET] Starting free user usage reset at {now}")

        # Find free users with expired periods and non-zero usage
        free_users = await database["users"].find({
            "subscription_plan": "try_learn",
            "current_period_end": {"$lt": now},
            "$or": [
                {"practice_minutes_used": {"$gt": 0}},
                {"practice_sessions_used": {"$gt": 0}},
                {"assessments_used": {"$gt": 0}}
            ]
        }).to_list(None)

        logger.info(f"[FREE_USER_RESET] Found {len(free_users)} free users needing reset")

        if len(free_users) == 0:
            logger.info("[FREE_USER_RESET] No users need reset. Job complete.")
            return 0

        reset_count = 0
        error_count = 0

        for user in free_users:
            try:
                user_id = str(user["_id"])
                email = user.get("email", "unknown")
                old_minutes = user.get("practice_minutes_used", 0)

                # Use SubscriptionService.reset_monthly_usage for proper reset with audit trail
                success = await SubscriptionService.reset_monthly_usage(user_id)

                if success:
                    reset_count += 1
                    logger.info(f"[FREE_USER_RESET] ✅ Reset usage for {email} (had {old_minutes:.1f} minutes used)")
                else:
                    error_count += 1
                    logger.warning(f"[FREE_USER_RESET] ⚠️ Failed to reset {email}")

            except Exception as e:
                error_count += 1
                logger.error(f"[FREE_USER_RESET] ❌ Error resetting user {user['_id']}: {str(e)}")

        logger.info(f"[FREE_USER_RESET] ✅ Job complete: {reset_count} users reset, {error_count} errors")
        return reset_count

    except Exception as e:
        logger.error(f"[FREE_USER_RESET] ❌ Fatal error in reset job: {str(e)}")
        return 0


# Entry point for direct execution
if __name__ == "__main__":
    logger.info("=== Free User Monthly Reset - Manual Execution ===")
    result = asyncio.run(reset_expired_free_user_periods())
    logger.info(f"=== Reset {result} users ===")
