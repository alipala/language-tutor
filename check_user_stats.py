#!/usr/bin/env python3
"""
Script to check user statistics data in MongoDB production database.
Investigates why users with completed challenges are seeing placeholder cards.
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId
import json

# Database Configuration
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=60000&retryWrites=true&retryReads=true"
DATABASE_NAME = "language_tutor"

# Test Users
TEST_USERS = [
    "6d7fe617-e8f5-49dc-b71e-d4ddd1553f94@mailslurp.biz",
    "alipala.ist@gmail.com"
]

def pretty_print(data, title=""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    print(json.dumps(data, indent=2, default=str))

def get_user_id(users_collection, email):
    """Get user ID from email"""
    user = users_collection.find_one({"email": email})
    if user:
        return user.get("_id") or user.get("id")
    return None

def check_user_stats(email):
    """Check all statistics data for a user"""
    print(f"\n{'#'*80}")
    print(f"# CHECKING USER: {email}")
    print(f"{'#'*80}")

    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]

        # Get collections
        users_collection = db.users
        challenge_sessions_collection = db.challenge_sessions
        conversation_sessions_collection = db.conversation_sessions
        daily_stats_collection = db.daily_stats
        recent_performance_collection = db.recent_performance

        # Get user ID
        user = users_collection.find_one({"email": email})

        if not user:
            print(f"\n❌ USER NOT FOUND: {email}")
            return

        user_id = user.get("_id") or user.get("id")
        print(f"\n✅ USER FOUND")
        print(f"   User ID: {user_id}")
        print(f"   Email: {email}")

        # Check user stats document
        print(f"\n{'='*80}")
        print(f"1. USER DOCUMENT - EMBEDDED STATS")
        print(f"{'='*80}")

        user_stats = user.get("stats", {})
        if user_stats:
            print(f"   Current Streak: {user_stats.get('current_streak', 0)}")
            print(f"   Longest Streak: {user_stats.get('longest_streak', 0)}")
            print(f"   Total XP: {user_stats.get('total_xp', 0)}")
            print(f"   Total Challenges: {user_stats.get('total_challenges', 0)}")
            print(f"   Last Practice Date: {user_stats.get('last_practice_date', 'N/A')}")

            # Languages stats
            languages_stats = user_stats.get('by_language', {})
            if languages_stats:
                print(f"\n   Languages Practiced:")
                for lang, lang_stats in languages_stats.items():
                    print(f"      - {lang}: {lang_stats.get('total_challenges', 0)} challenges, {lang_stats.get('total_xp', 0)} XP")
        else:
            print(f"   ⚠️  No embedded stats found in user document")

        # Check challenge_sessions
        print(f"\n{'='*80}")
        print(f"2. CHALLENGE SESSIONS (Event Log)")
        print(f"{'='*80}")

        sessions_count = challenge_sessions_collection.count_documents({"user_id": user_id})
        print(f"   Total Sessions: {sessions_count}")

        if sessions_count > 0:
            # Get recent sessions
            recent_sessions = list(challenge_sessions_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(5))

            print(f"\n   Recent 5 Sessions:")
            for idx, session in enumerate(recent_sessions, 1):
                print(f"      {idx}. Date: {session.get('created_at')} | "
                      f"Language: {session.get('language', 'N/A')} | "
                      f"Level: {session.get('level', 'N/A')} | "
                      f"Type: {session.get('challenge_type', 'N/A')}")
                print(f"         Challenges: {session.get('total_challenges', 0)} | "
                      f"Correct: {session.get('correct_challenges', 0)} | "
                      f"XP: {session.get('total_xp', 0)}")

            # Get date range
            oldest = challenge_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", 1)]
            )
            newest = challenge_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )

            if oldest and newest:
                print(f"\n   First Session: {oldest.get('created_at')}")
                print(f"   Last Session: {newest.get('created_at')}")
        else:
            print(f"   ❌ NO CHALLENGE SESSIONS FOUND")

        # Check conversation_sessions
        print(f"\n{'='*80}")
        print(f"2b. CONVERSATION SESSIONS (AI Tutor Practice)")
        print(f"{'='*80}")

        conv_sessions_count = conversation_sessions_collection.count_documents({"user_id": user_id})
        print(f"   Total Conversation Sessions: {conv_sessions_count}")

        if conv_sessions_count > 0:
            # Get recent conversation sessions
            recent_conv_sessions = list(conversation_sessions_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(5))

            print(f"\n   Recent 5 Conversation Sessions:")
            for idx, session in enumerate(recent_conv_sessions, 1):
                print(f"      {idx}. Date: {session.get('created_at')} | "
                      f"Language: {session.get('language', 'N/A')} | "
                      f"Level: {session.get('level', 'N/A')} | "
                      f"Topic: {session.get('topic', 'N/A')}")
                print(f"         Duration: {session.get('duration', 0)} sec | "
                      f"XP: {session.get('xp_earned', 0)} | "
                      f"Messages: {session.get('total_messages', 0)}")

            # Get date range
            oldest_conv = conversation_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", 1)]
            )
            newest_conv = conversation_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )

            if oldest_conv and newest_conv:
                print(f"\n   First Conversation: {oldest_conv.get('created_at')}")
                print(f"   Last Conversation: {newest_conv.get('created_at')}")
        else:
            print(f"   ⚠️  NO CONVERSATION SESSIONS FOUND")

        # Check daily_stats
        print(f"\n{'='*80}")
        print(f"3. DAILY STATS (Pre-aggregated Daily Summaries)")
        print(f"{'='*80}")

        daily_stats_count = daily_stats_collection.count_documents({"user_id": user_id})
        print(f"   Total Daily Stats Records: {daily_stats_count}")

        if daily_stats_count > 0:
            # Get today's stats
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_stats = daily_stats_collection.find_one({
                "user_id": user_id,
                "local_date": today_str
            })

            if today_stats:
                print(f"\n   TODAY'S STATS ({today_str}):")
                print(f"      Total Sessions: {today_stats.get('total_sessions', 0)}")
                print(f"      Total Challenges: {today_stats.get('total_challenges', 0)}")
                print(f"      Correct: {today_stats.get('correct_challenges', 0)}")
                print(f"      Accuracy: {today_stats.get('accuracy_percent', 0):.1f}%")
                print(f"      XP: {today_stats.get('total_xp', 0)}")
                print(f"      Streak: {today_stats.get('streak_count', 0)}")
            else:
                print(f"\n   ⚠️  NO STATS FOR TODAY ({today_str})")

            # Get recent daily stats
            recent_daily = list(daily_stats_collection.find(
                {"user_id": user_id}
            ).sort("local_date", -1).limit(7))

            print(f"\n   Last 7 Days:")
            for stat in recent_daily:
                print(f"      {stat.get('local_date')}: "
                      f"{stat.get('total_challenges', 0)} challenges, "
                      f"{stat.get('accuracy_percent', 0):.1f}% accuracy, "
                      f"{stat.get('total_xp', 0)} XP")
        else:
            print(f"   ❌ NO DAILY STATS FOUND")

        # Check recent_performance cache
        print(f"\n{'='*80}")
        print(f"4. RECENT PERFORMANCE CACHE (7-day Rolling Window)")
        print(f"{'='*80}")

        recent_perf = recent_performance_collection.find_one({"user_id": user_id})

        if recent_perf:
            print(f"   ✅ RECENT PERFORMANCE CACHE EXISTS")
            print(f"      Calculated At: {recent_perf.get('calculated_at')}")
            print(f"      Expires At: {recent_perf.get('expires_at')}")
            print(f"      Window: {recent_perf.get('window_start')} to {recent_perf.get('window_end')}")
            print(f"\n      Summary:")
            print(f"         Total Sessions: {recent_perf.get('total_sessions', 0)}")
            print(f"         Total Challenges: {recent_perf.get('total_challenges', 0)}")
            print(f"         Average Accuracy: {recent_perf.get('average_accuracy', 0):.1f}%")
            print(f"         Total XP: {recent_perf.get('total_xp', 0)}")
            print(f"\n      Insights:")
            print(f"         Most Practiced Type: {recent_perf.get('most_practiced_type', 'N/A')}")
            print(f"         Most Practiced Language: {recent_perf.get('most_practiced_language', 'N/A')}")
            print(f"         Weakest Level: {recent_perf.get('weakest_level', 'N/A')}")
            print(f"         Strongest Level: {recent_perf.get('strongest_level', 'N/A')}")

            # Check if cache is expired
            expires_at = recent_perf.get('expires_at')
            if expires_at and isinstance(expires_at, datetime):
                now = datetime.now(timezone.utc)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if now > expires_at:
                    print(f"\n      ⚠️  CACHE IS EXPIRED (needs refresh)")
                else:
                    print(f"\n      ✅ CACHE IS VALID")
        else:
            print(f"   ⚠️  NO RECENT PERFORMANCE CACHE FOUND")
            print(f"      This is normal if the user hasn't been active recently")
            print(f"      Cache is created on-demand when /api/stats/recent is called")

        print(f"\n{'='*80}")
        print(f"SUMMARY FOR {email}")
        print(f"{'='*80}")

        if sessions_count > 0:
            print(f"✅ User has {sessions_count} challenge sessions")
        else:
            print(f"❌ User has NO challenge sessions")

        if conv_sessions_count > 0:
            print(f"✅ User has {conv_sessions_count} conversation sessions (AI Tutor)")
        else:
            print(f"❌ User has NO conversation sessions")

        if daily_stats_count > 0:
            print(f"✅ User has {daily_stats_count} daily stats records")
        else:
            print(f"❌ User has NO daily stats records")

        if recent_perf:
            print(f"✅ User has recent performance cache")
        else:
            print(f"⚠️  User has NO recent performance cache (will be created on API call)")

        # IMPORTANT: Check for data inconsistency
        total_activity = sessions_count + conv_sessions_count
        if total_activity > 0 and daily_stats_count == 0:
            print(f"\n⚠️  WARNING: User has {total_activity} total sessions but NO daily_stats!")
            print(f"   This indicates that stats aggregation may not be working properly.")
            print(f"   Stats should be created when challenge_sessions are completed.")

        client.close()

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print(f"\n{'#'*80}")
    print(f"# STATISTICS DATA CHECK - PRODUCTION DATABASE")
    print(f"# Database: {DATABASE_NAME}")
    print(f"# Time: {datetime.now()}")
    print(f"{'#'*80}")

    for email in TEST_USERS:
        check_user_stats(email)

    print(f"\n{'#'*80}")
    print(f"# CHECK COMPLETE")
    print(f"{'#'*80}\n")

if __name__ == "__main__":
    main()
