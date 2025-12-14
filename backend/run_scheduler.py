"""
Challenge Pool Scheduler
Runs the daily replenishment job automatically
Can be run as a separate process or integrated into main FastAPI app
"""

import asyncio
import schedule
import time
from datetime import datetime
from challenge_pool_replenisher import run_daily_job


def job_wrapper():
    """Wrapper to run async job in sync context"""
    print(f"\n[SCHEDULER] ⏰ Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(run_daily_job())


def run_scheduler():
    """
    Run the scheduler
    Executes daily job at 2:00 AM UTC every day
    """
    print("="*70)
    print("[SCHEDULER] 🚀 Challenge Pool Scheduler Started")
    print(f"[SCHEDULER] 📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[SCHEDULER] ⏰ Daily job scheduled for: 02:00 AM UTC")
    print("="*70 + "\n")

    # Schedule daily job at 2:00 AM UTC
    schedule.every().day.at("02:00").do(job_wrapper)

    # For testing: uncomment to run every minute
    # schedule.every(1).minutes.do(job_wrapper)

    # Run immediately on startup (optional)
    print("[SCHEDULER] 🔄 Running initial replenishment job...\n")
    job_wrapper()

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
