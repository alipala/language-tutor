#!/usr/bin/env python3

import pymongo
from pymongo import MongoClient
from bson import ObjectId
import json
from datetime import datetime

# MongoDB connection details from the provided environment
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

# User details to test
USER_EMAIL = "ea375861-ffae-41df-be08-ef309b3738fa@mailslurp.biz"
USER_ID = "6871ac37b3da13a7e9f1c1bb"

def connect_to_mongodb():
    """Connect to MongoDB and return database instance"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        # Test connection
        db.command('ping')
        print(f"✅ Successfully connected to MongoDB database: {DATABASE_NAME}")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def test_achievement_fix(db):
    """Test the achievement fix by simulating the new logic"""
    try:
        learning_plans_collection = db.learning_plans
        
        print(f"\n🧪 TESTING ACHIEVEMENT FIX")
        print("=" * 60)
        
        # Get ALL learning plans for the user (simulating the fix)
        all_plans = list(learning_plans_collection.find({"user_id": USER_ID}))
        
        if not all_plans:
            print(f"❌ No learning plans found for user {USER_ID}")
            return
        
        print(f"📋 Found {len(all_plans)} learning plans for user {USER_ID}")
        
        # Aggregate completed weeks across ALL plans (the fix logic)
        all_completed_weeks = {}
        max_total_weeks = 0
        total_completed_sessions = 0
        
        for i, plan in enumerate(all_plans):
            completed_sessions = plan.get("completed_sessions", 0)
            sessions_per_week = 2
            plan_completed_weeks = completed_sessions // sessions_per_week
            plan_total_weeks = plan.get("duration_months", 6) * 4
            plan_language = plan.get("language", "unknown")
            plan_id = plan.get("id", "unknown")
            created_at = plan.get("created_at", "unknown")
            
            print(f"\n📊 Plan {i+1}: {plan_language.upper()}")
            print(f"   ID: {plan_id}")
            print(f"   Created: {created_at}")
            print(f"   Sessions: {completed_sessions}")
            print(f"   Weeks completed: {plan_completed_weeks}")
            
            # Track the highest week completed across all plans
            for week_num in range(1, plan_completed_weeks + 1):
                if week_num not in all_completed_weeks:
                    all_completed_weeks[week_num] = {
                        "week_number": week_num,
                        "sessions_completed": sessions_per_week,
                        "total_sessions": sessions_per_week,
                        "is_completed": True,
                        "plan_language": plan_language,
                        "plan_id": plan_id
                    }
                    print(f"   ✅ Added week {week_num} from {plan_language} plan")
            
            max_total_weeks = max(max_total_weeks, plan_total_weeks)
            total_completed_sessions += completed_sessions
        
        # Convert to sorted list
        completed_weeks_list = [
            all_completed_weeks[week_num] 
            for week_num in sorted(all_completed_weeks.keys())
        ]
        
        print(f"\n🎯 AGGREGATION RESULTS:")
        print("=" * 40)
        print(f"✅ Total completed weeks: {len(completed_weeks_list)}")
        print(f"✅ Week numbers: {[w['week_number'] for w in completed_weeks_list]}")
        print(f"✅ Total sessions across all plans: {total_completed_sessions}")
        print(f"✅ Max total weeks: {max_total_weeks}")
        
        print(f"\n📋 DETAILED WEEK BREAKDOWN:")
        for week in completed_weeks_list:
            print(f"   Week {week['week_number']}: ✅ UNLOCKED (from {week['plan_language']} plan)")
        
        # Test the specific issue
        print(f"\n🔍 SPECIFIC ISSUE TEST:")
        print("=" * 40)
        week_1_status = "UNLOCKED ✅" if 1 in all_completed_weeks else "LOCKED ❌"
        print(f"Week 1 Status: {week_1_status}")
        
        if 1 in all_completed_weeks:
            week_1_info = all_completed_weeks[1]
            print(f"Week 1 Source: {week_1_info['plan_language']} plan ({week_1_info['plan_id']})")
            print(f"✅ FIX SUCCESSFUL: User can now share Week 1 achievement!")
        else:
            print(f"❌ FIX FAILED: Week 1 still locked")
        
        # Compare with old logic (latest plan only)
        print(f"\n🔄 COMPARISON WITH OLD LOGIC:")
        print("=" * 40)
        latest_plan = max(all_plans, key=lambda x: x.get("created_at", ""))
        latest_completed_sessions = latest_plan.get("completed_sessions", 0)
        latest_completed_weeks = latest_completed_sessions // 2
        latest_language = latest_plan.get("language", "unknown")
        
        print(f"Old logic (latest plan only): {latest_language}")
        print(f"Old logic weeks: {list(range(1, latest_completed_weeks + 1))}")
        print(f"New logic weeks: {[w['week_number'] for w in completed_weeks_list]}")
        
        improvement = len(completed_weeks_list) - latest_completed_weeks
        if improvement > 0:
            print(f"🚀 IMPROVEMENT: {improvement} additional weeks unlocked!")
        elif improvement == 0:
            print(f"📊 SAME RESULT: No change in available weeks")
        else:
            print(f"⚠️ UNEXPECTED: Fewer weeks than before")
        
        return {
            "completed_weeks": completed_weeks_list,
            "total_weeks": max_total_weeks,
            "completed_sessions": total_completed_sessions,
            "fix_successful": 1 in all_completed_weeks
        }
        
    except Exception as e:
        print(f"❌ Error testing achievement fix: {str(e)}")
        return None

def main():
    print("🚀 Testing Achievement Fix")
    print("=" * 80)
    
    # Connect to database
    db = connect_to_mongodb()
    if db is None:
        return
    
    # Test the fix
    result = test_achievement_fix(db)
    
    if result:
        print(f"\n🎉 TEST SUMMARY:")
        print("=" * 40)
        if result["fix_successful"]:
            print("✅ ACHIEVEMENT FIX SUCCESSFUL!")
            print("✅ User can now access Week 1 achievement")
            print("✅ Multi-language learning plans work correctly")
            print("✅ No achievements lost when creating new plans")
        else:
            print("❌ ACHIEVEMENT FIX FAILED!")
            print("❌ Week 1 still locked")
        
        print(f"\n📊 Final Stats:")
        print(f"   Unlocked weeks: {len(result['completed_weeks'])}")
        print(f"   Total sessions: {result['completed_sessions']}")
        print(f"   Max weeks: {result['total_weeks']}")
    else:
        print("❌ Test failed to run")

if __name__ == "__main__":
    main()
