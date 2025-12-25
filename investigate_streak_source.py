#!/usr/bin/env python3
"""
Investigate where user streaks are coming from if not from challenge_sessions
"""

import os
from pymongo import MongoClient
from datetime import datetime

# Database Configuration
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=60000&retryWrites=true&retryReads=true"
DATABASE_NAME = "language_tutor"

TEST_USERS = [
    "6d7fe617-e8f5-49dc-b71e-d4ddd1553f94@mailslurp.biz",
    "alipala.ist@gmail.com"
]

def main():
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    for email in TEST_USERS:
        print(f"\n{'='*80}")
        print(f"INVESTIGATING: {email}")
        print(f"{'='*80}")

        user = db.users.find_one({"email": email})
        if not user:
            print("User not found")
            continue

        user_id = user.get("_id") or user.get("id")

        # Check user stats
        user_stats = user.get("stats", {})
        print(f"\nUser Stats:")
        print(f"  Current Streak: {user_stats.get('current_streak', 0)}")
        print(f"  Longest Streak: {user_stats.get('longest_streak', 0)}")
        print(f"  Last Practice Date: {user_stats.get('last_practice_date', 'N/A')}")
        print(f"  Total Challenges: {user_stats.get('total_challenges', 0)}")
        print(f"  Total XP: {user_stats.get('total_xp', 0)}")

        # Check old challengeStats field (might be legacy data)
        challenge_stats = user.get("challengeStats", {})
        if challenge_stats:
            print(f"\nLegacy challengeStats Field:")
            print(f"  Total Completed: {challenge_stats.get('totalCompleted', 0)}")
            print(f"  Current Streak: {challenge_stats.get('currentStreak', 0)}")
            print(f"  Last Challenge Date: {challenge_stats.get('lastChallengeDate', 'N/A')}")
            print(f"  Completed Today: {len(challenge_stats.get('completedToday', []))}")

            # Check completion history
            history = challenge_stats.get('completionHistory', {})
            if history:
                print(f"  Completion History Dates: {len(history)} days")
                for date in sorted(history.keys(), reverse=True)[:5]:
                    print(f"    - {date}: {len(history[date])} challenges")

        # Check conversation sessions (might be updating streak)
        conv_count = db.conversation_sessions.count_documents({"user_id": user_id})
        if conv_count > 0:
            print(f"\nConversation Sessions: {conv_count}")
            recent_conv = db.conversation_sessions.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            if recent_conv:
                print(f"  Most Recent: {recent_conv.get('created_at')}")
                print(f"  Streak Eligible: {recent_conv.get('is_streak_eligible', False)}")

        # Check for any other collections that might track challenges
        all_collections = db.list_collection_names()
        challenge_related = [c for c in all_collections if 'challenge' in c.lower() or 'session' in c.lower()]

        print(f"\nAll Challenge/Session Collections:")
        for coll in challenge_related:
            count = db[coll].count_documents({"user_id": user_id})
            if count > 0:
                print(f"  - {coll}: {count} documents")
                # Get a sample
                sample = db[coll].find_one({"user_id": user_id})
                if sample:
                    print(f"    Sample keys: {list(sample.keys())[:10]}")

    client.close()

if __name__ == "__main__":
    main()
