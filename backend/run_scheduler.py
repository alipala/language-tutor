"""
Background Job Scheduler - Simplified & Optimized
==================================================

This scheduler runs essential background jobs for the Language Tutor platform:

ACTIVE JOBS:
- Heart refill notifications (every 30 minutes) - User engagement
- Practice reminders (every hour) - User retention
- Free user monthly reset (daily at 2:30 AM UTC) - Business logic
- Reference challenge generation (monthly at 3:00 AM UTC) - Content refresh

DEPRECATED JOBS:
- User challenge pool replenishment - No longer needed with new completion tracking system
  (Users now get challenges from shared reference_challenges with completion filtering)

Architecture:
- Runs as a separate Railway service for isolation and reliability
- Uses schedule library for cron-like job scheduling
- Async operations via asyncio event loop
- Graceful shutdown on SIGINT

Author: Language Tutor Team
Last Updated: 2026-04-07
"""

import os
import asyncio
import schedule
import time
from datetime import datetime, date
from typing import Optional
from enum import Enum

# Job imports
from notification_triggers import run_heart_refill_check
from practice_reminder_trigger import run_practice_reminder_check
from story_reminder_trigger import run_story_reminder_check
from news_reminder_trigger import run_news_reminder_check
from learning_plan_reminder_trigger import run_plan_reminder_check
from cron_jobs.reset_free_user_usage import reset_expired_free_user_periods


# ==============================================================================
# CONFIGURATION
# ==============================================================================

class JobFrequency(Enum):
    """Supported job frequencies"""
    DISABLED = "disabled"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


FREQUENCY_INTERVALS = {
    JobFrequency.DAILY: 1,
    JobFrequency.WEEKLY: 7,
    JobFrequency.BIWEEKLY: 14,
    JobFrequency.MONTHLY: 30,
}


# ==============================================================================
# EVENT LOOP MANAGEMENT
# ==============================================================================

# Global event loop for all async operations
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get existing event loop or create a new one.

    Returns:
        asyncio.AbstractEventLoop: The event loop instance
    """
    global _event_loop

    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)

    return _event_loop


# ==============================================================================
# JOB WRAPPERS
# ==============================================================================

def heart_refill_job_wrapper() -> None:
    """
    Wrapper to run heart refill notification check.
    Sends push notifications when users' hearts have refilled.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 🔔 Heart Refill Check Triggered at {timestamp}")

    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_heart_refill_check())


def practice_reminder_job_wrapper() -> None:
    """
    Wrapper to run practice reminder check.
    Sends push notifications to encourage users to practice.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 📚 Practice Reminder Check Triggered at {timestamp}")

    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_practice_reminder_check())


def story_reminder_job_wrapper() -> None:
    """Wrapper: Story Worlds reminders (resume / unlock / discover)."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 📖 Story Reminder Check Triggered at {timestamp}")
    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_story_reminder_check())


def news_reminder_job_wrapper() -> None:
    """Wrapper: morning news reminders (generic / category-personalized)."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 📰 News Reminder Check Triggered at {timestamp}")
    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_news_reminder_check())


def plan_reminder_job_wrapper() -> None:
    """Wrapper: learning-plan continue reminders."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 🎯 Learning Plan Reminder Check Triggered at {timestamp}")
    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_plan_reminder_check())


def free_user_reset_job_wrapper() -> None:
    """
    Wrapper to run free user monthly reset.
    Resets usage counters for free tier users on a monthly basis.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 🆓 Free User Monthly Reset Triggered at {timestamp}")

    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(reset_expired_free_user_periods())


def reference_generation_job_wrapper() -> None:
    """
    Wrapper to run reference challenge generation.

    Generates new template challenges in the reference_challenges collection.
    Uses frequency-based scheduling to avoid unnecessary AI costs.

    Note: Uses simple AI generator (gpt-5.4-mini) for cost efficiency.
          CrewAI is disabled as simple generator produces high-quality results.
    """
    # Get configuration
    frequency_str = os.getenv("REFERENCE_GENERATION_FREQUENCY", "monthly").lower()

    # Parse frequency
    try:
        frequency = JobFrequency(frequency_str)
    except ValueError:
        print(f"[SCHEDULER] ⚠️ Invalid REFERENCE_GENERATION_FREQUENCY: {frequency_str}, using monthly")
        frequency = JobFrequency.MONTHLY

    # Check if disabled
    if frequency == JobFrequency.DISABLED:
        print(f"\n[SCHEDULER] ⏭️ Reference generation is DISABLED")
        return

    # Calculate if we should run today based on frequency
    days_since_epoch = (date.today() - date(1970, 1, 1)).days
    interval = FREQUENCY_INTERVALS[frequency]

    if days_since_epoch % interval != 0:
        days_until_next = interval - (days_since_epoch % interval)
        print(f"\n[SCHEDULER] ⏭️ Skipping reference generation")
        print(f"[SCHEDULER]    Frequency: {frequency.value}")
        print(f"[SCHEDULER]    Next run in: {days_until_next} days")
        return

    # Run generation
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[SCHEDULER] 📖 Reference Challenge Generation Triggered at {timestamp}")
    print(f"[SCHEDULER] 🔄 Frequency: {frequency.value}")
    print(f"[SCHEDULER] 🤖 Using: Simple AI Generator (gpt-5.4-mini)")

    event_loop = get_or_create_event_loop()

    # Import the simple AI reference generation function
    # Note: We use simple AI generator instead of CrewAI for cost efficiency
    try:
        from generate_reference_challenges_ai import replenish_reference_challenges
        event_loop.run_until_complete(replenish_reference_challenges())
        print(f"[SCHEDULER] ✅ Reference generation completed successfully")
    except ImportError:
        # Fallback to CrewAI if simple AI generator not available
        print(f"[SCHEDULER] ⚠️ Simple AI generator not found, falling back to CrewAI")
        try:
            from generate_reference_challenges_crew import replenish_reference_challenges
            event_loop.run_until_complete(replenish_reference_challenges())
            print(f"[SCHEDULER] ✅ Reference generation completed successfully (CrewAI)")
        except Exception as e:
            print(f"[SCHEDULER] ❌ Error running reference generation: {str(e)}")
            import traceback
            print(traceback.format_exc())
    except Exception as e:
        print(f"[SCHEDULER] ❌ Error running reference generation: {str(e)}")
        import traceback
        print(traceback.format_exc())


# ==============================================================================
# DEPRECATED JOB (kept for reference)
# ==============================================================================

def user_pool_replenishment_job_wrapper() -> None:
    """
    [DEPRECATED] Wrapper to run user challenge pool replenishment.

    This job is NO LONGER NEEDED as of 2026-04-07.

    Reason: New completion tracking system introduced in April 2026 eliminates
    the need for per-user challenge pools. Users now get challenges directly
    from the shared reference_challenges collection with intelligent completion
    filtering based on challenge_ids tracking.

    Migration: Set USER_POOL_FREQUENCY=disabled in environment variables.

    For more info, see: docs/COMPLETION_TRACKING_MIGRATION.md
    """
    frequency_str = os.getenv("USER_POOL_FREQUENCY", "disabled").lower()

    # Check if explicitly disabled
    if frequency_str == "disabled":
        print(f"\n[SCHEDULER] ℹ️ User pool replenishment is DISABLED")
        print(f"[SCHEDULER]    Reason: New completion tracking system replaces user pools")
        print(f"[SCHEDULER]    See: docs/COMPLETION_TRACKING_MIGRATION.md")
        return

    # Warn if still enabled
    print(f"\n[SCHEDULER] ⚠️ WARNING: User pool replenishment is still ENABLED")
    print(f"[SCHEDULER]    This job is DEPRECATED and should be disabled")
    print(f"[SCHEDULER]    Set USER_POOL_FREQUENCY=disabled in environment")
    print(f"[SCHEDULER]    Skipping execution to prevent unnecessary AI costs...")


# ==============================================================================
# MAIN SCHEDULER
# ==============================================================================

def run_scheduler() -> None:
    """
    Run the background job scheduler.

    Schedules and executes all background jobs with proper timing:
    - Heart refill notifications: Every 30 minutes (user engagement)
    - Practice reminders: Every hour (user retention)
    - Free user reset: Daily at 2:30 AM UTC (business logic)
    - Reference generation: Monthly at 3:00 AM UTC (content refresh)

    The scheduler runs in an infinite loop, checking for pending jobs every minute.
    Gracefully handles SIGINT (Ctrl+C) for clean shutdown.
    """
    # ==============================================================================
    # LOAD CONFIGURATION
    # ==============================================================================

    reference_freq = os.getenv("REFERENCE_GENERATION_FREQUENCY", "monthly").lower()
    user_pool_freq = os.getenv("USER_POOL_FREQUENCY", "disabled").lower()
    use_crewai = os.getenv("USE_CREWAI", "false").lower() == "true"
    gpt_model = os.getenv("GPT_MODEL", "gpt-5.4-mini")

    # ==============================================================================
    # PRINT STARTUP BANNER
    # ==============================================================================

    print("=" * 80)
    print("[SCHEDULER] 🚀 Background Job Scheduler Started (Simplified)")
    print(f"[SCHEDULER] 📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print("\n[SCHEDULER] 📋 Active Jobs:")
    print(f"  🔔 Heart refill notifications: Every 30 minutes")
    print(f"  📚 Practice reminders: Every hour")
    print(f"  📖 Story reminders: Every hour (local-time gated)")
    print(f"  📰 News reminders: Every hour (local-time gated)")
    print(f"  🎯 Learning plan reminders: Every hour (local-time gated)")
    print(f"  🆓 Free user monthly reset: Daily at 02:30 AM UTC")
    print(f"  📖 Reference generation: {reference_freq} at 03:00 AM UTC")

    print("\n[SCHEDULER] ⚙️ Configuration:")
    print(f"  🤖 AI Generator: {'CrewAI' if use_crewai else 'Simple AI'}")
    print(f"  🧠 Model: {gpt_model}")
    print(f"  🔄 User pool replenishment: {user_pool_freq} (deprecated)")

    print("\n[SCHEDULER] ℹ️ System Architecture:")
    print(f"  ✅ Completion tracking: ENABLED (Apr 2026)")
    print(f"  ✅ Challenge source: Shared reference_challenges collection")
    print(f"  ❌ User challenge pools: DEPRECATED (no longer needed)")

    print("=" * 80 + "\n")

    # ==============================================================================
    # SCHEDULE JOBS
    # ==============================================================================

    # 1. Free user monthly reset (daily at 2:30 AM UTC)
    # Runs daily, checks expiration internally
    schedule.every().day.at("02:30").do(free_user_reset_job_wrapper)

    # 2. Reference challenge generation (monthly at 3:00 AM UTC)
    # Checks frequency internally before running
    schedule.every().day.at("03:00").do(reference_generation_job_wrapper)

    # 3. Heart refill notifications (every 30 minutes)
    # Critical for user engagement
    schedule.every(30).minutes.do(heart_refill_job_wrapper)

    # 4. Practice reminders (every hour)
    # Drives user retention
    schedule.every().hour.do(practice_reminder_job_wrapper)

    # 4b. Smart reminders (every hour) — each trigger internally gates on the
    # user's local morning/evening window, quiet hours, the shared weekly cap,
    # and its own preference flag, so hourly ticking is cheap and safe. A single
    # kill-switch (SMART_REMINDERS_ENABLED=0) disables all three for rollback.
    if os.getenv("SMART_REMINDERS_ENABLED", "1") != "0":
        schedule.every().hour.do(story_reminder_job_wrapper)
        schedule.every().hour.do(news_reminder_job_wrapper)
        schedule.every().hour.do(plan_reminder_job_wrapper)
        print("[SCHEDULER] ✅ Smart reminders (story/news/plan) scheduled hourly")
    else:
        print("[SCHEDULER] ⏸️ Smart reminders DISABLED (SMART_REMINDERS_ENABLED=0)")

    # 5. [DEPRECATED] User pool replenishment
    # Only schedule if explicitly not disabled (for migration period)
    if user_pool_freq != "disabled":
        print("[SCHEDULER] ⚠️ Scheduling deprecated user pool job (should be disabled)\n")
        schedule.every().day.at("02:00").do(user_pool_replenishment_job_wrapper)

    # ==============================================================================
    # RUN INITIAL CHECKS
    # ==============================================================================

    print("[SCHEDULER] 🔄 Running initial notification checks...\n")
    print("[SCHEDULER] ℹ️ Skipping challenge generation on startup (runs at 03:00 AM UTC)\n")

    # Run notification jobs immediately to verify they work
    heart_refill_job_wrapper()
    print()
    practice_reminder_job_wrapper()

    # ==============================================================================
    # START MAIN LOOP
    # ==============================================================================

    print("\n[SCHEDULER] 👀 Scheduler is now running. Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n[SCHEDULER] 🛑 Scheduler stopped by user (SIGINT received)")
        print("[SCHEDULER] 👋 Shutting down gracefully...")
    finally:
        # Clean up event loop
        global _event_loop
        if _event_loop and not _event_loop.is_closed():
            _event_loop.close()
        print("[SCHEDULER] ✅ Shutdown complete\n")


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Ensure schedule package is installed
    try:
        import schedule
    except ImportError:
        print("[SCHEDULER] 📦 Installing required package: schedule")
        import subprocess
        subprocess.check_call(["pip", "install", "schedule"])
        import schedule

    # Start the scheduler
    run_scheduler()
