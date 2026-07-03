"""
One-shot backfill: add news_reminders_enabled / story_reminders_enabled = True
to any notification_preferences doc that predates those fields.

Idempotent: only touches docs where the field is MISSING (never overwrites an
explicit user choice). Safe to run multiple times. Read-then-write with a count
report; makes no other changes.

Run:  railway run --service web ./venv/bin/python backfill_reminder_prefs.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient


async def main():
    url = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL")
    dbname = os.getenv("DATABASE_NAME", "language_tutor")
    if not url:
        print("❌ No MONGODB_URL in env")
        return

    client = AsyncIOMotorClient(url)
    db = client[dbname]
    prefs = db.notification_preferences

    total = await prefs.count_documents({})
    news_missing = await prefs.count_documents({"news_reminders_enabled": {"$exists": False}})
    story_missing = await prefs.count_documents({"story_reminders_enabled": {"$exists": False}})
    print(f"total prefs docs:            {total}")
    print(f"news field missing:          {news_missing}")
    print(f"story field missing:         {story_missing}")

    # Add news flag where missing.
    r_news = await prefs.update_many(
        {"news_reminders_enabled": {"$exists": False}},
        {"$set": {"news_reminders_enabled": True}},
    )
    # Add story flag where missing.
    r_story = await prefs.update_many(
        {"story_reminders_enabled": {"$exists": False}},
        {"$set": {"story_reminders_enabled": True}},
    )
    print(f"news backfilled (modified):  {r_news.modified_count}")
    print(f"story backfilled (modified): {r_story.modified_count}")

    # Verify post-state.
    news_on = await prefs.count_documents({"news_reminders_enabled": True})
    story_on = await prefs.count_documents({"story_reminders_enabled": True})
    still_missing = await prefs.count_documents(
        {"$or": [
            {"news_reminders_enabled": {"$exists": False}},
            {"story_reminders_enabled": {"$exists": False}},
        ]}
    )
    print(f"--- post ---")
    print(f"news_reminders_enabled=True: {news_on}")
    print(f"story_reminders_enabled=True:{story_on}")
    print(f"still missing either field:  {still_missing}")
    print("✅ backfill complete" if still_missing == 0 else "⚠️ some docs still missing")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
