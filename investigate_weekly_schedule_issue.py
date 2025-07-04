#!/usr/bin/env python3

import pymongo
import json
from bson import ObjectId
from datetime import datetime

# MongoDB connection details from Railway
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

def connect_to_mongodb():
    """Connect to MongoDB production database"""
    try:
        client = pymongo.MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        # Test connection
        db.command('ping')
        print("✅ Successfully connected to MongoDB production database")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def investigate_learning_plan_issue():
    """Investigate the weekly schedule tracking issue"""
    db = connect_to_mongodb()
    if db is None:
        return
    
    try:
        # Find the learning plan from the JSON file
        learning_plans = db.learning_plans
        
        # Search for the specific learning plan ID from the JSON
        plan_id = "96862ad9-5c92-4048-9824-915e25d5d580"
        
        print(f"\n🔍 Searching for learning plan with ID: {plan_id}")
        
        plan = learning_plans.find_one({"id": plan_id})
        
        if not plan:
            print(f"❌ Learning plan with ID {plan_id} not found")
            return
        
        print(f"✅ Found learning plan for user: {plan.get('user_id', 'Unknown')}")
        print(f"📊 Global completed_sessions: {plan.get('completed_sessions', 0)}")
        print(f"📊 Global total_sessions: {plan.get('total_sessions', 0)}")
        print(f"📊 Progress percentage: {plan.get('progress_percentage', 0)}%")
        
        # Check weekly schedule
        weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
        
        print(f"\n📅 Weekly Schedule Analysis:")
        print(f"Total weeks in plan: {len(weekly_schedule)}")
        
        for i, week in enumerate(weekly_schedule[:4]):  # Show first 4 weeks
            week_num = week.get('week', i + 1)
            sessions_completed = week.get('sessions_completed', 0)
            total_sessions = week.get('total_sessions', 2)
            focus = week.get('focus', 'No focus specified')
            
            # Determine status
            if sessions_completed >= total_sessions:
                status = "✅ COMPLETED"
                color = "GREEN"
            elif sessions_completed > 0:
                status = "🔄 IN PROGRESS"
                color = "BLUE"
            else:
                status = "⏳ UPCOMING"
                color = "GRAY"
            
            print(f"  Week {week_num}: {sessions_completed}/{total_sessions} sessions - {status}")
            print(f"    Focus: {focus[:80]}...")
            print(f"    Expected UI Color: {color}")
            print()
        
        # Check session summaries
        session_summaries = plan.get('session_summaries', [])
        print(f"📝 Session summaries count: {len(session_summaries)}")
        
        # Show the issue clearly
        print(f"\n🐛 ISSUE ANALYSIS:")
        print(f"Week 1: {weekly_schedule[0].get('sessions_completed', 0)}/{weekly_schedule[0].get('total_sessions', 2)} sessions")
        print(f"  -> Should show as: ✅ GREEN (COMPLETED)")
        print(f"  -> Currently shows as: 🔵 BLUE (according to screenshots)")
        print()
        print(f"Week 2: {weekly_schedule[1].get('sessions_completed', 0)}/{weekly_schedule[1].get('total_sessions', 2)} sessions")
        print(f"  -> Should show as: 🔄 BLUE (IN PROGRESS)")
        print(f"  -> This is correct")
        
        print(f"\n💡 ROOT CAUSE:")
        print(f"The frontend is using global 'completed_sessions' ({plan.get('completed_sessions', 0)}) to calculate week status")
        print(f"instead of using individual week's 'sessions_completed' field from weekly_schedule array")
        
    except Exception as e:
        print(f"❌ Error investigating learning plan: {e}")

if __name__ == "__main__":
    print("🔍 Investigating Weekly Schedule Tracking Issue")
    print("=" * 60)
    investigate_learning_plan_issue()
