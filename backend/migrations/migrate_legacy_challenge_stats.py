#!/usr/bin/env python3
"""
Migration Script: Backfill daily_stats from legacy challengeStats

This script migrates historical challenge completion data from the legacy
`users.challengeStats` field to the new `daily_stats` collection.

Purpose:
- Fix "Your Journey Awaits" placeholder showing for users with legacy data
- Enable Recent Performance Card to display historical challenge data
- Bridge the gap between old and new stats architecture

What it does:
1. Finds all users with challengeStats.completionHistory
2. For each date in completion history:
   - Creates/updates daily_stats record
   - Aggregates: total challenges, correct/incorrect, accuracy
3. Updates users.stats with lifetime totals
4. Preserves existing streaks

Usage:
    python backend/migrations/migrate_legacy_challenge_stats.py [--dry-run] [--user-email EMAIL]

Options:
    --dry-run: Show what would be migrated without making changes
    --user-email: Migrate only a specific user (for testing)
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import database
from services.stats_service import calculate_accuracy

async def migrate_user_challenge_stats(
    user_id: str,
    challenge_stats: Dict[str, Any],
    user_timezone: str = "UTC",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate a single user's legacy challengeStats to daily_stats

    Args:
        user_id: User ID
        challenge_stats: Legacy challengeStats document
        user_timezone: User's timezone
        dry_run: If True, don't make changes

    Returns:
        Migration summary
    """
    completion_history = challenge_stats.get("completionHistory", {})

    if not completion_history:
        return {
            "user_id": user_id,
            "migrated_days": 0,
            "total_challenges": 0,
            "status": "no_data"
        }

    migrated_days = 0
    total_challenges = 0
    total_correct = 0
    total_incorrect = 0

    daily_stats_collection = database.daily_stats
    users_collection = database.users

    print(f"  📅 Found {len(completion_history)} days of completion history")

    # Process each day in completion history
    for date_str, day_challenges in completion_history.items():
        if not day_challenges:
            continue

        # Count correct/incorrect for this day
        day_total = len(day_challenges)
        day_correct = sum(1 for c in day_challenges if c.get("correct", True))
        day_incorrect = day_total - day_correct
        day_accuracy = calculate_accuracy(day_correct, day_total)

        # Aggregate by language, level, type (use defaults if not available)
        by_language = {}
        by_level = {}
        by_type = {}

        for challenge in day_challenges:
            # Extract metadata (may not exist in legacy data)
            lang = challenge.get("language", "unknown")
            level = challenge.get("level", "unknown")
            chal_type = challenge.get("challenge_type", "unknown")
            is_correct = challenge.get("correct", True)

            # Aggregate by language
            if lang not in by_language:
                by_language[lang] = {"challenges": 0, "correct": 0, "incorrect": 0, "accuracy": 0.0, "xp": 0}
            by_language[lang]["challenges"] += 1
            by_language[lang]["correct"] += 1 if is_correct else 0
            by_language[lang]["incorrect"] += 0 if is_correct else 1
            by_language[lang]["xp"] += 10 if is_correct else 5

            # Aggregate by level
            if level not in by_level:
                by_level[level] = {"challenges": 0, "correct": 0, "incorrect": 0, "accuracy": 0.0, "xp": 0}
            by_level[level]["challenges"] += 1
            by_level[level]["correct"] += 1 if is_correct else 0
            by_level[level]["incorrect"] += 0 if is_correct else 1
            by_level[level]["xp"] += 10 if is_correct else 5

            # Aggregate by type
            if chal_type not in by_type:
                by_type[chal_type] = {"challenges": 0, "correct": 0, "incorrect": 0, "accuracy": 0.0, "xp": 0}
            by_type[chal_type]["challenges"] += 1
            by_type[chal_type]["correct"] += 1 if is_correct else 0
            by_type[chal_type]["incorrect"] += 0 if is_correct else 1
            by_type[chal_type]["xp"] += 10 if is_correct else 5

        # Calculate accuracy for each breakdown
        for lang_stats in by_language.values():
            lang_stats["accuracy"] = calculate_accuracy(lang_stats["correct"], lang_stats["challenges"])

        for level_stats in by_level.values():
            level_stats["accuracy"] = calculate_accuracy(level_stats["correct"], level_stats["challenges"])

        for type_stats in by_type.values():
            type_stats["accuracy"] = calculate_accuracy(type_stats["correct"], type_stats["challenges"])

        # Create/update daily_stats document
        daily_stat = {
            "user_id": user_id,
            "local_date": date_str,
            "user_timezone": user_timezone,
            "total_sessions": 1,  # Legacy: treat all challenges in a day as one session
            "total_challenges": day_total,
            "correct_challenges": day_correct,
            "incorrect_challenges": day_incorrect,
            "accuracy_percent": day_accuracy,
            "total_xp": day_correct * 10 + day_incorrect * 5,  # Estimated XP
            "total_time_seconds": 0,  # Not available in legacy data
            "by_language": by_language,
            "by_level": by_level,
            "by_type": by_type,
            "is_streak_day": True,  # Assume all legacy days count for streak
            "streak_count": challenge_stats.get("currentStreak", 0),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        if not dry_run:
            # Upsert daily_stats (update if exists, insert if not)
            await daily_stats_collection.update_one(
                {"user_id": user_id, "local_date": date_str},
                {"$set": daily_stat},
                upsert=True
            )

        migrated_days += 1
        total_challenges += day_total
        total_correct += day_correct
        total_incorrect += day_incorrect

        print(f"    ✅ {date_str}: {day_total} challenges ({day_correct} correct, {day_accuracy:.1f}% accuracy)")

    # Update users.stats with lifetime totals (if not already set)
    if not dry_run and total_challenges > 0:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        current_stats = user.get("stats", {})

        # Only update if current stats show 0 challenges (avoid overwriting newer data)
        if current_stats.get("total_challenges", 0) == 0:
            await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "stats.total_challenges": total_challenges,
                        "stats.total_xp": total_correct * 10 + total_incorrect * 5,
                        "stats.current_streak": challenge_stats.get("currentStreak", 0),
                        "stats.longest_streak": challenge_stats.get("currentStreak", 0),
                        "stats.last_practice_date": challenge_stats.get("lastChallengeDate")
                    }
                }
            )
            print(f"  ✅ Updated users.stats: {total_challenges} total challenges")

    return {
        "user_id": user_id,
        "migrated_days": migrated_days,
        "total_challenges": total_challenges,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "accuracy": calculate_accuracy(total_correct, total_challenges),
        "status": "success"
    }


async def migrate_all_users(dry_run: bool = False, target_email: str = None):
    """
    Migrate all users with legacy challengeStats

    Args:
        dry_run: If True, show what would be migrated without making changes
        target_email: If provided, only migrate this user
    """
    users_collection = database.users

    # Build query
    query = {"challengeStats.completionHistory": {"$exists": True, "$ne": {}}}

    if target_email:
        query["email"] = target_email

    users_cursor = users_collection.find(query)
    users = await users_cursor.to_list(length=None)

    if not users:
        print("ℹ️  No users found with legacy challengeStats to migrate")
        return

    print(f"\n{'='*80}")
    print(f"MIGRATION: Legacy challengeStats → daily_stats")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Users to migrate: {len(users)}")
    print(f"{'='*80}\n")

    total_migrated = 0
    total_challenges = 0

    for user in users:
        user_id = str(user.get("_id"))
        email = user.get("email", "unknown")
        challenge_stats = user.get("challengeStats", {})
        timezone = user.get("timezone", "UTC")

        print(f"\n👤 User: {email}")
        print(f"   ID: {user_id}")

        result = await migrate_user_challenge_stats(
            user_id,
            challenge_stats,
            timezone,
            dry_run
        )

        if result["status"] == "success":
            total_migrated += 1
            total_challenges += result["total_challenges"]
            print(f"   ✅ Migrated {result['migrated_days']} days, {result['total_challenges']} challenges")
        else:
            print(f"   ⚠️  {result['status']}")

    print(f"\n{'='*80}")
    print(f"MIGRATION COMPLETE")
    print(f"{'='*80}")
    print(f"Users migrated: {total_migrated}")
    print(f"Total challenges: {total_challenges}")
    print(f"Mode: {'DRY RUN (no changes made)' if dry_run else 'LIVE (data updated)'}")
    print(f"{'='*80}\n")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate legacy challengeStats to daily_stats")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--user-email", type=str, help="Migrate only a specific user (for testing)")

    args = parser.parse_args()

    await migrate_all_users(dry_run=args.dry_run, target_email=args.user_email)


if __name__ == "__main__":
    asyncio.run(main())
