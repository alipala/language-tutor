"""
Background Job Scheduler
Runs scheduled jobs:
- Challenge pool replenishment (configurable frequency)
- Reference challenge generation (configurable frequency)
- Heart refill notifications (every 30 minutes)
- Practice reminders (every hour)
Can be run as a separate process or integrated into main FastAPI app
"""

import os
import asyncio
import schedule
import time
from datetime import datetime, date
from challenge_pool_replenisher import run_daily_job
from notification_triggers import run_heart_refill_check
from practice_reminder_trigger import run_practice_reminder_check

# Global event loop for all async operations
loop = None


def get_or_create_event_loop():
    """Get existing event loop or create a new one"""
    global loop
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def daily_job_wrapper():
    """Wrapper to run daily challenge pool replenishment"""
    print(f"\n[SCHEDULER] ⏰ Daily Job Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_daily_job())


def heart_refill_job_wrapper():
    """Wrapper to run heart refill notification check"""
    print(f"\n[SCHEDULER] 🔔 Heart Refill Check Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_heart_refill_check())


def practice_reminder_job_wrapper():
    """Wrapper to run practice reminder check"""
    print(f"\n[SCHEDULER] 📚 Practice Reminder Check Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_practice_reminder_check())


def reference_generation_job_wrapper():
    """Wrapper to run reference challenge generation"""
    frequency = os.getenv("REFERENCE_GENERATION_FREQUENCY", "weekly").lower()

    # Calculate if we should run today based on frequency
    days_since_epoch = (date.today() - date(1970, 1, 1)).days

    frequency_map = {
        "daily": 1,
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30
    }

    interval = frequency_map.get(frequency, 7)

    if days_since_epoch % interval != 0:
        print(f"\n[SCHEDULER] ⏭️ Skipping reference generation (frequency: {frequency}, next run in {interval - (days_since_epoch % interval)} days)")
        return

    print(f"\n[SCHEDULER] 📖 Reference Challenge Generation Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[SCHEDULER] 🔄 Frequency: {frequency}")

    event_loop = get_or_create_event_loop()

    # Import the reference generation function
    try:
        from generate_reference_challenges_crew import replenish_reference_challenges
        event_loop.run_until_complete(replenish_reference_challenges())
    except Exception as e:
        print(f"[SCHEDULER] ❌ Error running reference generation: {str(e)}")
        import traceback
        print(traceback.format_exc())


def user_pool_replenishment_job_wrapper():
    """Wrapper to run user challenge pool replenishment"""
    frequency = os.getenv("USER_POOL_FREQUENCY", "daily").lower()

    # Calculate if we should run today based on frequency
    days_since_epoch = (date.today() - date(1970, 1, 1)).days

    frequency_map = {
        "daily": 1,
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30
    }

    interval = frequency_map.get(frequency, 1)  # Default daily

    if days_since_epoch % interval != 0:
        print(f"\n[SCHEDULER] ⏭️ Skipping user pool replenishment (frequency: {frequency}, next run in {interval - (days_since_epoch % interval)} days)")
        return

    print(f"\n[SCHEDULER] ⏰ User Pool Replenishment Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[SCHEDULER] 🔄 Frequency: {frequency}")

    event_loop = get_or_create_event_loop()
    event_loop.run_until_complete(run_daily_job())


def run_scheduler():
    """
    Run the scheduler with multiple jobs:
    - User challenge pool replenishment (configurable frequency) at 2:00 AM UTC
    - Reference challenge generation (configurable frequency) at 3:00 AM UTC
    - Heart refill notifications every 30 minutes
    - Practice reminders every hour
    """
    # Get configuration from environment
    user_pool_freq = os.getenv("USER_POOL_FREQUENCY", "daily")
    reference_freq = os.getenv("REFERENCE_GENERATION_FREQUENCY", "weekly")
    use_crewai = os.getenv("USE_CREWAI", "false").lower() == "true"

    print("="*80)
    print("[SCHEDULER] 🚀 Background Job Scheduler Started")
    print(f"[SCHEDULER] 📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("[SCHEDULER] Configuration:")
    print(f"  🔄 User pool replenishment: {user_pool_freq} at 02:00 AM UTC")
    print(f"  🤖 CrewAI for users: {'ENABLED' if use_crewai else 'DISABLED'}")
    print(f"  📖 Reference generation: {reference_freq} at 03:00 AM UTC")
    print(f"  🔔 Heart refill check: Every 30 minutes")
    print(f"  📚 Practice reminders: Every hour")
    print("="*80 + "\n")

    # Schedule user challenge pool replenishment at 2:00 AM UTC
    # This checks the frequency inside the wrapper
    schedule.every().day.at("02:00").do(user_pool_replenishment_job_wrapper)

    # Schedule reference challenge generation at 3:00 AM UTC
    # This checks the frequency inside the wrapper
    schedule.every().day.at("03:00").do(reference_generation_job_wrapper)

    # Schedule heart refill notifications every 30 minutes
    schedule.every(30).minutes.do(heart_refill_job_wrapper)

    # Schedule practice reminders every hour
    schedule.every().hour.do(practice_reminder_job_wrapper)

    # For testing: uncomment to run jobs every minute
    # schedule.every(1).minutes.do(daily_job_wrapper)
    # schedule.every(1).minutes.do(heart_refill_job_wrapper)

    # Run notification jobs immediately on startup (NOT challenge generation - too expensive!)
    print("[SCHEDULER] 🔄 Running initial notification checks...\n")
    print("[SCHEDULER] ⚠️ Skipping challenge generation on startup:")
    print(f"[SCHEDULER]    - User pool: runs at 02:00 AM UTC ({user_pool_freq})")
    print(f"[SCHEDULER]    - Reference: runs at 03:00 AM UTC ({reference_freq})\n")
    heart_refill_job_wrapper()
    print()
    practice_reminder_job_wrapper()

    # Keep running
    print("\n[SCHEDULER] 👀 Scheduler is now running. Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n[SCHEDULER] 🛑 Scheduler stopped by user")


if __name__ == "__main__":
    # Install schedule package if not already installed
    try:
        import schedule
    except ImportError:
        print("Installing required package: schedule")
        import subprocess
        subprocess.check_call(["pip", "install", "schedule"])
        import schedule

    run_scheduler()
