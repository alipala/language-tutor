#!/usr/bin/env python3
"""
Verify migration results - check daily_stats collection directly
"""

from pymongo import MongoClient
from datetime import datetime

# Database Configuration
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=60000&retryWrites=true&retryReads=true"
DATABASE_NAME = "language_tutor"

TEST_EMAIL = "alipala.ist@gmail.com"

def main():
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    # Get user
    user = db.users.find_one({"email": TEST_EMAIL})
    if not user:
        print("User not found")
        return

    user_id = str(user.get("_id") or user.get("id"))

    print(f"\n{'='*80}")
    print(f"VERIFICATION: {TEST_EMAIL}")
    print(f"User ID: {user_id}")
    print(f"{'='*80}\n")

    # Check daily_stats directly
    daily_stats = list(db.daily_stats.find({"user_id": user_id}).sort("local_date", -1))

    print(f"✅ Found {len(daily_stats)} daily_stats records\n")

    if daily_stats:
        for stat in daily_stats:
            print(f"📅 Date: {stat.get('local_date')}")
            print(f"   Challenges: {stat.get('total_challenges', 0)}")
            print(f"   Correct: {stat.get('correct_challenges', 0)}")
            print(f"   Accuracy: {stat.get('accuracy_percent', 0):.1f}%")
            print(f"   XP: {stat.get('total_xp', 0)}")
            print(f"   By Language: {list(stat.get('by_language', {}).keys())}")
            print(f"   By Type: {list(stat.get('by_type', {}).keys())}")
            print()
    else:
        print("❌ NO daily_stats found!")
        print("\nPossible issues:")
        print("1. Migration script didn't run properly")
        print("2. User ID mismatch")
        print("3. Database connection issue")

    # Check users.stats
    user_stats = user.get("stats", {})
    print(f"\n{'='*80}")
    print(f"USER STATS (users.stats field)")
    print(f"{'='*80}")
    print(f"Total Challenges: {user_stats.get('total_challenges', 0)}")
    print(f"Total XP: {user_stats.get('total_xp', 0)}")
    print(f"Current Streak: {user_stats.get('current_streak', 0)}")
    print(f"Last Practice: {user_stats.get('last_practice_date', 'N/A')}")

    client.close()

if __name__ == "__main__":
    main()
