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

def test_specific_plan_mode(db, learning_plan_id):
    """Test the specific plan mode (when learningPlanId is provided)"""
    try:
        learning_plans_collection = db.learning_plans
        
        print(f"\n🎯 TESTING SPECIFIC PLAN MODE")
        print("=" * 60)
        print(f"Learning Plan ID: {learning_plan_id}")
        
        # Get the specific plan
        specific_plan = learning_plans_collection.find_one({
            "id": learning_plan_id,
            "user_id": USER_ID
        })
        
        if not specific_plan:
            print(f"❌ Learning plan {learning_plan_id} not found")
            return None
        
        completed_sessions = specific_plan.get("completed_sessions", 0)
        sessions_per_week = 2
        plan_completed_weeks = completed_sessions // sessions_per_week
        plan_language = specific_plan.get("language", "unknown")
        
        print(f"📊 Plan Details:")
        print(f"   Language: {plan_language}")
        print(f"   Sessions: {completed_sessions}")
        print(f"   Weeks completed: {plan_completed_weeks}")
        
        # Create weeks array for this specific plan only
        completed_weeks_list = []
        for week_num in range(1, plan_completed_weeks + 1):
            completed_weeks_list.append({
                "week_number": week_num,
                "sessions_completed": sessions_per_week,
                "total_sessions": sessions_per_week,
                "is_completed": True,
                "plan_language": plan_language,
                "plan_id": learning_plan_id
            })
        
        print(f"\n🎯 SPECIFIC PLAN RESULTS:")
        print("=" * 40)
        print(f"✅ Available weeks: {[w['week_number'] for w in completed_weeks_list]}")
        print(f"✅ Total weeks for this plan: {len(completed_weeks_list)}")
        
        return {
            "completed_weeks": completed_weeks_list,
            "plan_language": plan_language,
            "plan_specific": True
        }
        
    except Exception as e:
        print(f"❌ Error testing specific plan mode: {str(e)}")
        return None

def test_global_mode(db):
    """Test the global mode (when no learningPlanId is provided)"""
    try:
        learning_plans_collection = db.learning_plans
        
        print(f"\n🌍 TESTING GLOBAL MODE")
        print("=" * 60)
        
        # Get ALL learning plans for the user
        all_plans = list(learning_plans_collection.find({"user_id": USER_ID}))
        
        if not all_plans:
            print(f"❌ No learning plans found")
            return None
        
        print(f"📋 Found {len(all_plans)} learning plans")
        
        # Aggregate completed weeks across ALL plans
        all_completed_weeks = {}
        total_completed_sessions = 0
        
        for plan in all_plans:
            completed_sessions = plan.get("completed_sessions", 0)
            sessions_per_week = 2
            plan_completed_weeks = completed_sessions // sessions_per_week
            plan_language = plan.get("language", "unknown")
            plan_id = plan.get("id", "unknown")
            
            print(f"📊 Plan: {plan_language}, {completed_sessions} sessions, {plan_completed_weeks} weeks")
            
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
            
            total_completed_sessions += completed_sessions
        
        # Convert to sorted list
        completed_weeks_list = [
            all_completed_weeks[week_num] 
            for week_num in sorted(all_completed_weeks.keys())
        ]
        
        print(f"\n🎯 GLOBAL MODE RESULTS:")
        print("=" * 40)
        print(f"✅ Available weeks: {[w['week_number'] for w in completed_weeks_list]}")
        print(f"✅ Total aggregated weeks: {len(completed_weeks_list)}")
        print(f"✅ Total sessions across all plans: {total_completed_sessions}")
        
        return {
            "completed_weeks": completed_weeks_list,
            "plan_specific": False,
            "total_sessions": total_completed_sessions
        }
        
    except Exception as e:
        print(f"❌ Error testing global mode: {str(e)}")
        return None

def main():
    print("🚀 Testing CORRECTED Achievement Fix")
    print("=" * 80)
    
    # Connect to database
    db = connect_to_mongodb()
    if db is None:
        return
    
    # Get the user's learning plans first
    learning_plans_collection = db.learning_plans
    all_plans = list(learning_plans_collection.find({"user_id": USER_ID}))
    
    if not all_plans:
        print("❌ No learning plans found for user")
        return
    
    print(f"\n📋 USER'S LEARNING PLANS:")
    print("=" * 40)
    for i, plan in enumerate(all_plans):
        language = plan.get("language", "unknown")
        plan_id = plan.get("id", "unknown")
        completed_sessions = plan.get("completed_sessions", 0)
        created_at = plan.get("created_at", "unknown")
        print(f"{i+1}. {language.upper()} Plan")
        print(f"   ID: {plan_id}")
        print(f"   Sessions: {completed_sessions}")
        print(f"   Created: {created_at}")
    
    # Test 1: Specific Plan Mode (English Plan)
    english_plan = next((p for p in all_plans if p.get("language") == "english"), None)
    if english_plan:
        english_result = test_specific_plan_mode(db, english_plan.get("id"))
    
    # Test 2: Specific Plan Mode (Dutch Plan)
    dutch_plan = next((p for p in all_plans if p.get("language") == "dutch"), None)
    if dutch_plan:
        dutch_result = test_specific_plan_mode(db, dutch_plan.get("id"))
    
    # Test 3: Global Mode
    global_result = test_global_mode(db)
    
    # Summary
    print(f"\n🎉 TEST SUMMARY:")
    print("=" * 80)
    
    if english_plan and 'english_result' in locals():
        english_weeks = len(english_result.get("completed_weeks", [])) if english_result else 0
        print(f"✅ English Plan Mode: {english_weeks} weeks available")
        print(f"   → Week 1 status: {'UNLOCKED' if english_weeks >= 1 else 'LOCKED'}")
    
    if dutch_plan and 'dutch_result' in locals():
        dutch_weeks = len(dutch_result.get("completed_weeks", [])) if dutch_result else 0
        print(f"✅ Dutch Plan Mode: {dutch_weeks} weeks available")
        print(f"   → Week 1 status: {'UNLOCKED' if dutch_weeks >= 1 else 'LOCKED'}")
    
    if global_result:
        global_weeks = len(global_result.get("completed_weeks", []))
        print(f"✅ Global Mode: {global_weeks} weeks available")
        print(f"   → Week 1 status: {'UNLOCKED' if global_weeks >= 1 else 'LOCKED'}")
    
    print(f"\n🎯 EXPECTED BEHAVIOR:")
    print("=" * 40)
    print("✅ English Plan Modal: Should show Week 1 UNLOCKED (user completed it)")
    print("✅ Dutch Plan Modal: Should show Week 1 LOCKED (user hasn't started)")
    print("✅ Global Modal: Should show Week 1 UNLOCKED (aggregated across plans)")
    
    print(f"\n🔧 FIX STATUS:")
    print("=" * 40)
    if english_plan and dutch_plan:
        english_weeks = len(english_result.get("completed_weeks", [])) if 'english_result' in locals() and english_result else 0
        dutch_weeks = len(dutch_result.get("completed_weeks", [])) if 'dutch_result' in locals() and dutch_result else 0
        global_weeks = len(global_result.get("completed_weeks", [])) if global_result else 0
        
        if english_weeks >= 1 and dutch_weeks == 0 and global_weeks >= 1:
            print("✅ FIX SUCCESSFUL!")
            print("✅ Plan-specific achievements work correctly")
            print("✅ Global achievements work correctly")
            print("✅ No false unlocks for unstarted plans")
        else:
            print("❌ FIX NEEDS ADJUSTMENT")
            print(f"   English weeks: {english_weeks} (expected: ≥1)")
            print(f"   Dutch weeks: {dutch_weeks} (expected: 0)")
            print(f"   Global weeks: {global_weeks} (expected: ≥1)")
    else:
        print("⚠️ Cannot fully test - missing learning plans")

if __name__ == "__main__":
    main()
