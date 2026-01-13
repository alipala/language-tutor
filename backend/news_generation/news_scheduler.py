"""
News Generation Scheduler
Runs daily news generation at 1:00 AM CET
Uses APScheduler for reliable scheduling with retry logic
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import logging

from news_generation.news_generator import generate_daily_news, NewsGenerationError

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def init_news_scheduler():
    """
    Initialize the news generation scheduler
    Schedule daily generation at 1:00 AM CET
    """
    global scheduler

    if scheduler is not None:
        logger.warning("[NEWS_SCHEDULER] Scheduler already initialized")
        return scheduler

    logger.info("[NEWS_SCHEDULER] Initializing daily news scheduler...")

    # Create scheduler with CET timezone
    cet = pytz.timezone('CET')
    scheduler = AsyncIOScheduler(timezone=cet)

    # Primary job: 1:00 AM CET daily
    scheduler.add_job(
        run_daily_generation,
        trigger=CronTrigger(hour=1, minute=0, timezone=cet),
        id="daily_news_generation_primary",
        name="Daily News Generation (1:00 AM CET)",
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )

    # Retry job 1: 1:30 AM CET (if primary fails)
    scheduler.add_job(
        run_retry_generation_if_needed,
        trigger=CronTrigger(hour=1, minute=30, timezone=cet),
        id="daily_news_generation_retry_1",
        name="Daily News Generation Retry 1 (1:30 AM CET)",
        replace_existing=True,
        max_instances=1
    )

    # Retry job 2: 2:00 AM CET (if retry 1 fails)
    scheduler.add_job(
        run_retry_generation_if_needed,
        trigger=CronTrigger(hour=2, minute=0, timezone=cet),
        id="daily_news_generation_retry_2",
        name="Daily News Generation Retry 2 (2:00 AM CET)",
        replace_existing=True,
        max_instances=1
    )

    # Final retry: 6:00 AM CET (last chance)
    scheduler.add_job(
        run_retry_generation_if_needed,
        trigger=CronTrigger(hour=6, minute=0, timezone=cet),
        id="daily_news_generation_retry_3",
        name="Daily News Generation Retry 3 (6:00 AM CET)",
        replace_existing=True,
        max_instances=1
    )

    # Start the scheduler
    scheduler.start()
    logger.info("[NEWS_SCHEDULER] ✅ Scheduler started successfully")
    logger.info("[NEWS_SCHEDULER] Next generation: 1:00 AM CET")

    return scheduler


async def run_daily_generation():
    """
    Run the daily news generation
    Called by scheduler at 1:00 AM CET
    """
    logger.info("[NEWS_SCHEDULER] 🚀 Starting daily news generation (scheduled)")

    try:
        result = await generate_daily_news()

        if result.get("success"):
            logger.info(f"[NEWS_SCHEDULER] ✅ Generation successful: {result.get('article_count')} articles in {result.get('duration_seconds'):.1f}s")
        else:
            logger.error(f"[NEWS_SCHEDULER] ❌ Generation failed: {result}")

        return result

    except NewsGenerationError as e:
        logger.error(f"[NEWS_SCHEDULER] ❌ Generation error: {str(e)}")
        # Retry will be handled by retry jobs
        return {"success": False, "error": str(e)}

    except Exception as e:
        logger.error(f"[NEWS_SCHEDULER] ❌ Unexpected error: {str(e)}")
        return {"success": False, "error": str(e)}


async def run_retry_generation_if_needed():
    """
    Check if today's generation failed and retry if needed
    Called by retry jobs at 1:30 AM, 2:00 AM, and 6:00 AM CET
    """
    from database import news_batches_collection

    logger.info("[NEWS_SCHEDULER] Checking if retry is needed...")

    # Get current date in CET
    cet = pytz.timezone('CET')
    today = datetime.now(cet).date()
    today_start = datetime.combine(today, datetime.min.time())
    today_start = cet.localize(today_start)

    # Check if today's batch exists and is completed
    batch = await news_batches_collection.find_one(
        {"date": {"$gte": today_start}}
    )

    if not batch:
        logger.info("[NEWS_SCHEDULER] No batch found for today, starting generation...")
        return await run_daily_generation()

    if batch.get("status") == "completed":
        logger.info("[NEWS_SCHEDULER] Today's news already generated successfully, skipping retry")
        return {"success": True, "skipped": True}

    if batch.get("status") == "in_progress":
        logger.warning("[NEWS_SCHEDULER] Generation still in progress, skipping retry")
        return {"success": True, "skipped": True, "reason": "in_progress"}

    if batch.get("status") == "failed":
        logger.info("[NEWS_SCHEDULER] Previous generation failed, retrying...")
        return await run_daily_generation()

    logger.warning(f"[NEWS_SCHEDULER] Unknown batch status: {batch.get('status')}")
    return {"success": True, "skipped": True, "reason": "unknown_status"}


def stop_news_scheduler():
    """
    Stop the news scheduler
    Called on application shutdown
    """
    global scheduler

    if scheduler is not None:
        logger.info("[NEWS_SCHEDULER] Stopping scheduler...")
        scheduler.shutdown()
        scheduler = None
        logger.info("[NEWS_SCHEDULER] Scheduler stopped")


def get_scheduler_status():
    """
    Get current scheduler status and next run times
    Returns information about scheduled jobs
    """
    if scheduler is None:
        return {
            "status": "not_initialized",
            "jobs": []
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "status": "running",
        "jobs": jobs
    }


# For testing: Run generation immediately
async def test_generation_now():
    """
    Test function to run generation immediately (not scheduled)
    Useful for development and testing
    """
    logger.info("[NEWS_SCHEDULER] Running test generation immediately...")
    result = await run_daily_generation()
    logger.info(f"[NEWS_SCHEDULER] Test generation result: {result}")
    return result


if __name__ == "__main__":
    # Test the scheduler
    import asyncio

    async def test():
        # Run generation immediately for testing
        result = await test_generation_now()
        print(f"Result: {result}")

    asyncio.run(test())
