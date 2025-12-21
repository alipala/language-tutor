"""
Migration Script: Enhance Challenge Sessions

This script backfills existing challenge_sessions with new fields required
for the gamification and statistics system.

Run this once after deploying the Phase 1 changes.

Usage:
    python -m backend.migrations.001_enhance_sessions
"""

import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# Import timezone utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.timezone_utils import convert_to_local_date


def is_weekend(dt: datetime) -> bool:
    """Check if datetime is on weekend."""
    return dt.weekday() in [5, 6]


async def migrate_challenge_sessions():
    """
    Backfill existing challenge_sessions with new fields.
    """
    print("[MIGRATION] Starting challenge_sessions migration...")
    print(f"[MIGRATION] Connecting to: {MONGODB_URL}")
    print(f"[MIGRATION] Database: {DATABASE_NAME}")

    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    database = client[DATABASE_NAME]
    challenge_sessions_collection = database.challenge_sessions
    users_collection = database.users

    try:
        # Test connection
        await client.admin.command('ping')
        print("[MIGRATION] ✅ Database connection successful")

        # Find sessions missing the new fields
        cursor = challenge_sessions_collection.find({
            '$or': [
                {'total_challenges': {'$exists': False}},
                {'local_date': {'$exists': False}}
            ]
        })

        migrated = 0
        skipped = 0
        errors = 0

        async for session in cursor:
            try:
                session_id = session.get('_id')

                # Skip if already migrated
                if session.get('total_challenges') and session.get('local_date'):
                    skipped += 1
                    continue

                # Calculate new fields
                correct_answers = session.get('correct_answers', 0)
                wrong_answers = session.get('wrong_answers', 0)
                total_challenges = correct_answers + wrong_answers

                # Calculate accuracy
                accuracy = (correct_answers / total_challenges * 100) if total_challenges > 0 else 0

                # Calculate duration
                start_time = session.get('start_time')
                end_time = session.get('end_time')
                if start_time and end_time:
                    duration_seconds = (end_time - start_time).total_seconds()
                else:
                    # Estimate based on average 15 seconds per challenge
                    duration_seconds = total_challenges * 15

                # Get user timezone (default to UTC for old data)
                user_id = session.get('user_id')
                user = None
                if user_id:
                    try:
                        from bson import ObjectId
                        user = await users_collection.find_one({'_id': ObjectId(user_id)})
                    except:
                        pass

                user_timezone = "UTC"
                if user and user.get('timezone'):
                    user_timezone = user['timezone']

                # Calculate local_date
                created_at = session.get('created_at', datetime.utcnow())
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                local_date = convert_to_local_date(created_at, user_timezone)

                # Prepare update
                update_fields = {
                    'total_challenges': total_challenges,
                    'accuracy': round(accuracy, 2),
                    'duration_seconds': duration_seconds,
                    'user_timezone': user_timezone,
                    'local_date': local_date,
                    'tags': {
                        'is_first_session': False,  # Unknown for historical data
                        'is_weekend': is_weekend(created_at),
                        'session_number_today': 1  # Unknown
                    }
                }

                # Only add start_time if it doesn't exist
                if not start_time:
                    update_fields['start_time'] = created_at

                # Update session
                result = await challenge_sessions_collection.update_one(
                    {'_id': session_id},
                    {'$set': update_fields}
                )

                if result.modified_count > 0:
                    migrated += 1

                    if migrated % 100 == 0:
                        print(f"[MIGRATION] Migrated {migrated} sessions...")

            except Exception as e:
                errors += 1
                print(f"[MIGRATION] ❌ Error migrating session {session.get('_id')}: {str(e)}")
                if errors > 10:
                    print(f"[MIGRATION] ⚠️  Too many errors, stopping migration")
                    break

        print(f"\n[MIGRATION] ✅ Migration complete!")
        print(f"[MIGRATION] Migrated: {migrated} sessions")
        print(f"[MIGRATION] Skipped: {skipped} sessions (already migrated)")
        print(f"[MIGRATION] Errors: {errors}")

    except Exception as e:
        print(f"[MIGRATION] ❌ Fatal error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()
        print("[MIGRATION] Database connection closed")


async def rebuild_daily_stats():
    """
    Rebuild daily_stats collection from migrated challenge_sessions.

    This creates daily_stats documents for all historical sessions.
    """
    print("\n[MIGRATION] Rebuilding daily_stats collection...")

    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    database = client[DATABASE_NAME]
    challenge_sessions_collection = database.challenge_sessions
    daily_stats_collection = database.daily_stats

    try:
        # Test connection
        await client.admin.command('ping')

        # OPTION 1: Clear and rebuild (recommended for fresh start)
        print("[MIGRATION] Clearing existing daily_stats...")
        await daily_stats_collection.delete_many({})

        # OPTION 2: Skip clearing to preserve existing data
        # print("[MIGRATION] Preserving existing daily_stats...")

        # Aggregate sessions by user and local_date
        print("[MIGRATION] Aggregating sessions...")
        pipeline = [
            {
                '$match': {
                    'local_date': {'$exists': True},  # Only migrated sessions
                    'user_id': {'$exists': True}
                }
            },
            {
                '$group': {
                    '_id': {
                        'user_id': '$user_id',
                        'local_date': '$local_date'
                    },
                    'sessions': {'$push': '$$ROOT'}
                }
            }
        ]

        cursor = challenge_sessions_collection.aggregate(pipeline)

        rebuilt = 0
        async for group in cursor:
            try:
                user_id = group['_id']['user_id']
                local_date = group['_id']['local_date']
                sessions = group['sessions']

                # Aggregate all sessions for this user-date
                total_sessions = len(sessions)
                total_challenges = sum(s.get('total_challenges', 0) for s in sessions)
                correct_challenges = sum(s.get('correct_answers', 0) for s in sessions)
                incorrect_challenges = sum(s.get('wrong_answers', 0) for s in sessions)
                total_xp = sum(s.get('total_xp', 0) for s in sessions)
                total_time = sum(s.get('duration_seconds', 0) for s in sessions)
                user_timezone = sessions[0].get('user_timezone', 'UTC')

                # Calculate accuracy
                accuracy = (correct_challenges / total_challenges * 100) if total_challenges > 0 else 0

                # Aggregate by language
                by_language = {}
                for session in sessions:
                    lang = session.get('language', 'unknown')
                    if lang not in by_language:
                        by_language[lang] = {
                            'challenges': 0,
                            'correct': 0,
                            'incorrect': 0,
                            'xp': 0
                        }
                    by_language[lang]['challenges'] += session.get('total_challenges', 0)
                    by_language[lang]['correct'] += session.get('correct_answers', 0)
                    by_language[lang]['incorrect'] += session.get('wrong_answers', 0)
                    by_language[lang]['xp'] += session.get('total_xp', 0)

                # Calculate accuracy for each language
                for lang_data in by_language.values():
                    total = lang_data['challenges']
                    correct = lang_data['correct']
                    lang_data['accuracy'] = (correct / total * 100) if total > 0 else 0

                # Aggregate by level
                by_level = {}
                for session in sessions:
                    level = session.get('level', 'B1')
                    if level not in by_level:
                        by_level[level] = {
                            'challenges': 0,
                            'correct': 0,
                            'incorrect': 0
                        }
                    by_level[level]['challenges'] += session.get('total_challenges', 0)
                    by_level[level]['correct'] += session.get('correct_answers', 0)
                    by_level[level]['incorrect'] += session.get('wrong_answers', 0)

                # Calculate accuracy for each level
                for level_data in by_level.values():
                    total = level_data['challenges']
                    correct = level_data['correct']
                    level_data['accuracy'] = (correct / total * 100) if total > 0 else 0

                # Aggregate by type
                by_type = {}
                for session in sessions:
                    ctype = session.get('challenge_type', 'unknown')
                    if ctype not in by_type:
                        by_type[ctype] = {
                            'challenges': 0,
                            'correct': 0,
                            'incorrect': 0,
                            'xp': 0
                        }
                    by_type[ctype]['challenges'] += session.get('total_challenges', 0)
                    by_type[ctype]['correct'] += session.get('correct_answers', 0)
                    by_type[ctype]['incorrect'] += session.get('wrong_answers', 0)
                    by_type[ctype]['xp'] += session.get('total_xp', 0)

                # Calculate accuracy for each type
                for type_data in by_type.values():
                    total = type_data['challenges']
                    correct = type_data['correct']
                    type_data['accuracy'] = (correct / total * 100) if total > 0 else 0

                # Create daily_stat document
                daily_stat = {
                    'user_id': user_id,
                    'local_date': local_date,
                    'user_timezone': user_timezone,
                    'total_sessions': total_sessions,
                    'total_challenges': total_challenges,
                    'correct_challenges': correct_challenges,
                    'incorrect_challenges': incorrect_challenges,
                    'accuracy_percent': round(accuracy, 2),
                    'total_xp': total_xp,
                    'total_time_seconds': total_time,
                    'by_language': by_language,
                    'by_level': by_level,
                    'by_type': by_type,
                    'is_streak_day': True,
                    'streak_count': 0,  # Will be calculated separately
                    'created_at': sessions[0].get('created_at', datetime.utcnow()),
                    'updated_at': datetime.utcnow(),
                    'last_session_id': sessions[-1].get('_id')
                }

                # Upsert daily_stat
                await daily_stats_collection.update_one(
                    {
                        'user_id': user_id,
                        'local_date': local_date
                    },
                    {'$set': daily_stat},
                    upsert=True
                )

                rebuilt += 1

                if rebuilt % 100 == 0:
                    print(f"[MIGRATION] Rebuilt {rebuilt} daily stats...")

            except Exception as e:
                print(f"[MIGRATION] ❌ Error rebuilding daily stat: {str(e)}")

        print(f"\n[MIGRATION] ✅ Daily stats rebuild complete!")
        print(f"[MIGRATION] Rebuilt: {rebuilt} daily stat documents")

    except Exception as e:
        print(f"[MIGRATION] ❌ Fatal error rebuilding daily stats: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


async def main():
    """Main migration entry point."""
    print("=" * 70)
    print("GAMIFICATION & STATISTICS SYSTEM MIGRATION")
    print("Phase 1: Enhance Challenge Sessions & Rebuild Daily Stats")
    print("=" * 70)
    print()

    # Step 1: Enhance challenge sessions
    await migrate_challenge_sessions()

    # Step 2: Rebuild daily stats
    await rebuild_daily_stats()

    print()
    print("=" * 70)
    print("MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Verify data integrity in MongoDB")
    print("2. Test /api/stats/daily endpoint")
    print("3. Monitor logs for any errors")
    print()


if __name__ == "__main__":
    asyncio.run(main())
