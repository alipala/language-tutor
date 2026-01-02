"""
Background Job Scheduler
Runs scheduled jobs:
- Daily challenge pool replenishment (2:00 AM UTC)
- Heart refill notifications (every 30 minutes)
Can be run as a separate process or integrated into main FastAPI app
"""

import asyncio
import schedule
import time
from datetime import datetime
from challenge_pool_replenisher import run_daily_job
from notification_triggers import run_heart_refill_check


def daily_job_wrapper():
    """Wrapper to run daily challenge pool replenishment"""
    print(f"\n[SCHEDULER] ⏰ Daily Job Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(run_daily_job())


def heart_refill_job_wrapper():
    """Wrapper to run heart refill notification check"""
    print(f"\n[SCHEDULER] 🔔 Heart Refill Check Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(run_heart_refill_check())


def run_scheduler():
    """
    Run the scheduler with multiple jobs:
    - Daily challenge pool replenishment at 2:00 AM UTC
    - Heart refill notifications every 30 minutes
    """
    print("="*70)
    print("[SCHEDULER] 🚀 Background Job Scheduler Started")
    print(f"[SCHEDULER] 📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[SCHEDULER] ⏰ Daily challenge pool job: 02:00 AM UTC")
    print("[SCHEDULER] 🔔 Heart refill check: Every 30 minutes")
    print("="*70 + "\n")

    # Schedule daily challenge pool replenishment at 2:00 AM UTC
    schedule.every().day.at("02:00").do(daily_job_wrapper)

    # Schedule heart refill notifications every 30 minutes
    schedule.every(30).minutes.do(heart_refill_job_wrapper)

    # For testing: uncomment to run jobs every minute
    # schedule.every(1).minutes.do(daily_job_wrapper)
    # schedule.every(1).minutes.do(heart_refill_job_wrapper)

    # Run jobs immediately on startup (optional)
    print("[SCHEDULER] 🔄 Running initial jobs...\n")
    daily_job_wrapper()
    print()
    heart_refill_job_wrapper()

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
