#!/usr/bin/env python3
"""
Backfill daily_stats using session_history data from learning plans
This uses session_history which has completed_at timestamps
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

async def backfill_from_session_history():
    """Backfill daily_stats using session_history"""

    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'language_tutor')

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    learning_plans_collection = db['learning_plans']
    daily_stats_collection = db['daily_stats']
    users_collection = db['users']

    print("🔧 Backfilling daily_stats from session_history...")
    print()

    # Get all learning plans
    learning_plans = await learning_plans_collection.find({}).to_list(None)

    # Collect session data by user_id and date
    sessions_by_user_date = defaultdict(lambda: {'total_minutes': 0, 'session_count': 0})
    user_total_minutes = defaultdict(float)

    for plan in learning_plans:
        user_id = plan.get('user_id')
        session_history = plan.get('session_history', [])

        for session in session_history:
            completed_at_str = session.get('completed_at')
            duration = session.get('duration_minutes', 0)

            if completed_at_str and duration:
                try:
                    # Parse completed_at timestamp
                    completed_dt = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00')).replace(tzinfo=None)

                    # Get local date
                    local_date = completed_dt.strftime('%Y-%m-%d')

                    # Aggregate by user and date
                    key = (user_id, local_date)
                    sessions_by_user_date[key]['total_minutes'] += duration
                    sessions_by_user_date[key]['session_count'] += 1

                    # Track total minutes per user
                    user_total_minutes[user_id] += duration

                except Exception as e:
                    print(f"   ⚠️ Error parsing session: {e}")

    print(f"Found {len(sessions_by_user_date)} unique user-date combinations")
    print(f"Found sessions for {len(user_total_minutes)} users")
    print()

    # Update daily_stats
    daily_updated = 0
    daily_created = 0

    for (user_id, local_date), data in sessions_by_user_date.items():
        total_minutes = data['total_minutes']
        time_seconds = total_minutes * 60

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
            daily_created += 1
        elif result.modified_count > 0:
            daily_updated += 1

    # Update user practice_minutes_used
    user_updated = 0

    for user_id, total_minutes in user_total_minutes.items():
        result = await users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'practice_minutes_used': total_minutes}}
        )
        if result.modified_count > 0:
            user_updated += 1
            print(f"User {user_id[:8]}...: +{total_minutes} minutes")

    print()
    print(f"✅ Backfill complete!")
    print(f"   Daily stats created: {daily_created}")
    print(f"   Daily stats updated: {daily_updated}")
    print(f"   Users updated: {user_updated}")

    await client.close()

if __name__ == "__main__":
    from bson import ObjectId
    asyncio.run(backfill_from_session_history())
