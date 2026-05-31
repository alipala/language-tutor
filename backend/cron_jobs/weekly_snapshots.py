# DEPRECATED: Weekly snapshots replaced by session-level history.
# This cron job is kept for reference but should no longer be scheduled.
# See speaking_dna_service._append_session_history() for the new approach.

"""
Weekly Snapshots Cron Job
=========================
Creates weekly DNA snapshots for all active users.
Run every Monday at 00:00 UTC.

Usage:
    python cron_jobs/weekly_snapshots.py

Environment Variables Required:
    - MONGODB_URL: MongoDB connection string
    - DATABASE_NAME: Database name (default: language_tutor)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from services.speaking_dna_service import speaking_dna_service


async def create_weekly_snapshots_for_all_users():
    """
    Create weekly snapshots for all users with DNA profiles.

    This job:
    1. Finds all DNA profiles in the database
    2. For each user+language combination, creates/updates the weekly snapshot
    3. Snapshots are created for the Monday of the current week

    Returns:
        dict: Results summary with success/error counts
    """
    start_time = datetime.utcnow()
    print(f"[CRON] ⏰ Starting weekly snapshot creation at {start_time}")
    print(f"[CRON] 📅 Week starting: {_get_week_start(start_time).date()}")

    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "language_tutor")

    if not mongodb_url:
        print("[CRON] ❌ ERROR: MONGODB_URL environment variable not set")
        return {"success": False, "error": "MONGODB_URL not set"}

    print(f"[CRON] 🔌 Connecting to MongoDB database: {database_name}")
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    # Create a simple database object wrapper for the service
    class DBWrapper:
        def __init__(self, db):
            self.speaking_dna_profiles_collection = db.speaking_dna_profiles
            self.speaking_dna_history_collection = db.speaking_dna_history

    # Inject database into service
    speaking_dna_service.db = DBWrapper(db)

    try:
        # Get all unique user+language combinations from DNA profiles
        print("[CRON] 🔍 Querying DNA profiles...")
        profiles = await db.speaking_dna_profiles.find({}).to_list(None)

        print(f"[CRON] 📊 Found {len(profiles)} DNA profiles to process")

        if len(profiles) == 0:
            print("[CRON] ℹ️  No DNA profiles found. Nothing to do.")
            return {"success": True, "processed": 0, "succeeded": 0, "failed": 0}

        success_count = 0
        error_count = 0
        errors = []

        for i, profile in enumerate(profiles, 1):
            try:
                user_id = profile["user_id"]
                language = profile["language"]

                print(f"[CRON] [{i}/{len(profiles)}] Processing user {user_id[:8]}... ({language})")

                # DEPRECATED: Weekly snapshot creation disabled.
                # Session-level history is now appended in speaking_dna_service._append_session_history().
                # await speaking_dna_service._create_weekly_snapshot(
                #     user_id=user_id,
                #     language=language,
                #     strands=strands,
                #     session_duration_minutes=0,  # No new session, just snapshot
                #     breakthroughs_count=0
                # )

                success_count += 1
                print(f"[CRON]   ✅ Success (no-op: weekly snapshots deprecated)")

            except Exception as e:
                error_count += 1
                error_msg = f"{user_id[:8]}.../{language}: {str(e)}"
                errors.append(error_msg)
                print(f"[CRON]   ❌ Error: {str(e)}")

        # Summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n[CRON] 🎉 Completed in {duration:.1f}s")
        print(f"[CRON] ✅ Success: {success_count}")
        print(f"[CRON] ❌ Errors: {error_count}")

        if errors:
            print(f"\n[CRON] Error details:")
            for error in errors:
                print(f"[CRON]   - {error}")

        return {
            "success": True,
            "processed": len(profiles),
            "succeeded": success_count,
            "failed": error_count,
            "duration_seconds": duration,
            "errors": errors if errors else None
        }

    except Exception as e:
        print(f"[CRON] 💥 Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

    finally:
        print("[CRON] 🔌 Closing MongoDB connection")
        client.close()


def _get_week_start(date: datetime) -> datetime:
    """Get Monday of the current week at 00:00:00 UTC"""
    week_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    return week_start - timedelta(days=week_start.weekday())


if __name__ == "__main__":
    print("=" * 60)
    print("Weekly DNA Snapshots Cron Job")
    print("=" * 60)

    result = asyncio.run(create_weekly_snapshots_for_all_users())

    print("\n" + "=" * 60)
    print("Final Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Processed: {result.get('processed', 0)}")
    print(f"  Succeeded: {result.get('succeeded', 0)}")
    print(f"  Failed: {result.get('failed', 0)}")
    if result.get('duration_seconds'):
        print(f"  Duration: {result['duration_seconds']:.1f}s")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)
