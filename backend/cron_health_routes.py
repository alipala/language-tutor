"""
Cron Job Health Check Routes

Endpoints to monitor the health and execution of background cron jobs,
particularly the free user monthly reset job.

Author: Language Tutor Team
Created: 2026-04-18
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from database import database
from logging_config import logger

router = APIRouter()


@router.get("/api/cron/health/monthly-reset")
async def cron_health_check_monthly_reset():
    """
    Health check for the free user monthly reset cron job.

    Checks if there are any free users with expired periods that haven't been reset.
    A healthy state means no users are stuck with expired periods.

    Returns:
        dict: Health status with details about stale users
    """
    try:
        now = datetime.now(timezone.utc)

        # Find users who should have been reset but weren't
        # Grace period: 2 days (cron runs daily, so max 1 day delay + 1 day buffer)
        grace_cutoff = now - timedelta(days=2)

        stale_users = await database["users"].find({
            "subscription_plan": "try_learn",
            "current_period_end": {"$lt": grace_cutoff},
            "$or": [
                {"practice_minutes_used": {"$gt": 0}},
                {"practice_sessions_used": {"$gt": 0}},
                {"assessments_used": {"$gt": 0}}
            ]
        }).to_list(length=100)

        # Get summary info
        stale_count = len(stale_users)

        # Create user details for debugging
        user_details = []
        for user in stale_users[:10]:  # Limit to 10 for response size
            period_end = user.get("current_period_end")
            if period_end and period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=timezone.utc)

            days_overdue = (now - period_end).days if period_end else 0

            user_details.append({
                "email": user.get("email", "unknown"),
                "period_end": period_end.isoformat() if period_end else None,
                "days_overdue": days_overdue,
                "minutes_used": user.get("practice_minutes_used", 0),
                "sessions_used": user.get("practice_sessions_used", 0)
            })

        # Determine health status
        is_healthy = stale_count == 0

        response = {
            "status": "healthy" if is_healthy else "unhealthy",
            "stale_users_count": stale_count,
            "grace_period_days": 2,
            "check_timestamp": now.isoformat(),
            "message": "All free users are current" if is_healthy else f"{stale_count} free users have expired periods that need reset",
            "user_details": user_details if not is_healthy else []
        }

        if not is_healthy:
            logger.warning(f"[CRON_HEALTH] Monthly reset cron job appears to be failing: {stale_count} stale users")
        else:
            logger.info(f"[CRON_HEALTH] Monthly reset cron job is healthy")

        return response

    except Exception as e:
        logger.error(f"[CRON_HEALTH] Error checking cron health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking cron health: {str(e)}")


@router.get("/api/cron/stats/monthly-reset")
async def cron_stats_monthly_reset():
    """
    Get statistics about free user periods and resets.

    Returns:
        dict: Statistics about free user subscription periods
    """
    try:
        now = datetime.now(timezone.utc)

        # Count total free users
        total_free_users = await database["users"].count_documents({
            "subscription_plan": "try_learn"
        })

        # Count users with active periods (period_end in future)
        active_period_users = await database["users"].count_documents({
            "subscription_plan": "try_learn",
            "current_period_end": {"$gte": now}
        })

        # Count users with expired periods (should be 0 if cron is working)
        expired_period_users = await database["users"].count_documents({
            "subscription_plan": "try_learn",
            "current_period_end": {"$lt": now}
        })

        # Count users with usage (currently using their allocation)
        users_with_usage = await database["users"].count_documents({
            "subscription_plan": "try_learn",
            "$or": [
                {"practice_minutes_used": {"$gt": 0}},
                {"practice_sessions_used": {"$gt": 0}}
            ]
        })

        # Count users who have exhausted their minutes
        exhausted_users = await database["users"].count_documents({
            "subscription_plan": "try_learn",
            "practice_minutes_used": {"$gte": 15}  # Free tier limit
        })

        return {
            "timestamp": now.isoformat(),
            "total_free_users": total_free_users,
            "active_period_users": active_period_users,
            "expired_period_users": expired_period_users,
            "users_with_usage": users_with_usage,
            "exhausted_users": exhausted_users,
            "cron_status": "healthy" if expired_period_users == 0 else "issues_detected",
            "message": "Cron job is resetting users properly" if expired_period_users == 0 else f"{expired_period_users} users have expired periods"
        }

    except Exception as e:
        logger.error(f"[CRON_STATS] Error getting cron stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting cron stats: {str(e)}")


@router.post("/api/cron/trigger/monthly-reset")
async def trigger_monthly_reset_manually():
    """
    Manually trigger the free user monthly reset.

    Use this endpoint to force a reset if the cron job is failing.

    Returns:
        dict: Result of the manual reset operation
    """
    try:
        from cron_jobs.reset_free_user_usage import reset_expired_free_user_periods

        logger.info("[CRON_MANUAL] Manual trigger of monthly reset requested")

        reset_count = await reset_expired_free_user_periods()

        return {
            "status": "success",
            "users_reset": reset_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Successfully reset {reset_count} free users"
        }

    except Exception as e:
        logger.error(f"[CRON_MANUAL] Error manually triggering reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering reset: {str(e)}")
