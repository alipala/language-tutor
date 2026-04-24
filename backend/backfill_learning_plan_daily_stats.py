#!/usr/bin/env python3
"""
Backfill daily_stats with learning plan session data
This adds conversation practice time to daily_stats for historical sessions
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

async def backfill_daily_stats():
    """Backfill daily_stats with learning plan practice time"""

    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'language_tutor')

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    learning_plans_collection = db['learning_plans']
    daily_stats_collection = db['daily_stats']

    print("🔧 Backfilling daily_stats with learning plan session data...")
    print()

    # Get all learning plans
    learning_plans = await learning_plans_collection.find({}).to_list(None)

    # Collect all session data by user_id and date
    sessions_by_user_date = defaultdict(lambda: {'total_minutes': 0, 'session_count': 0})

    for plan in learning_plans:
        user_id = plan.get('user_id')
        weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])

        for week in weekly_schedule:
            session_details = week.get('session_details', [])
            for session in session_details:
                completed_at = session.get('completed_at')
                duration = session.get('duration_minutes', 0)

                if completed_at and duration:
                    try:
                        # Parse completed_at timestamp
                        if isinstance(completed_at, str):
                            completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).replace(tzinfo=None)
                        else:
                            completed_dt = completed_at

                        # Get local date (YYYY-MM-DD)
                        local_date = completed_dt.strftime('%Y-%m-%d')

                        # Aggregate by user and date
                        key = (user_id, local_date)
                        sessions_by_user_date[key]['total_minutes'] += duration
                        sessions_by_user_date[key]['session_count'] += 1

                    except Exception as e:
                        print(f"   ⚠️ Error parsing session: {e}")

    print(f"Found {len(sessions_by_user_date)} unique user-date combinations")
    print()

    # Update daily_stats for each user-date combination
    updated_count = 0
    created_count = 0

    for (user_id, local_date), data in sessions_by_user_date.items():
        total_minutes = data['total_minutes']
        session_count = data['session_count']
        time_seconds = total_minutes * 60

        print(f"User {user_id[:8]}... on {local_date}: {total_minutes} minutes ({session_count} sessions)")

        # Upsert daily_stats
        result = await daily_stats_collection.update_one(
            {
                'user_id': user_id,
                'local_date': local_date
            },
            {
                '$inc': {
                    'conversation_time_seconds': time_seconds,
                    'total_time_seconds': time_seconds,
                },
                '$set': {
                    'updated_at': datetime.utcnow(),
                },
                '$setOnInsert': {
                    'created_at': datetime.utcnow(),
                    'user_timezone': 'UTC',
                    'is_streak_day': True,
                    'total_sessions': 0,
                    'total_challenges': 0,
                    'correct_challenges': 0,
                    'incorrect_challenges': 0,
                    'total_xp': 0,
                }
            },
            upsert=True
        )

        if result.upserted_id:
            created_count += 1
            print(f"   ✅ Created new daily_stats entry")
        elif result.modified_count > 0:
            updated_count += 1
            print(f"   ✅ Updated existing daily_stats entry")

    print()
    print(f"✅ Backfill complete!")
    print(f"   Created: {created_count}")
    print(f"   Updated: {updated_count}")
    print(f"   Total: {len(sessions_by_user_date)}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(backfill_daily_stats())
