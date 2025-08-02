#!/usr/bin/env python3
"""
Script to fix Kamile's Week 2 progress after completing her 3rd session
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB connection for Railway
MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("DATABASE_URL")

async def fix_kamile_week2_progress():
    """Fix Kamile's Week 2 progress to reflect her 3rd session completion"""
    
    if not MONGODB_URL:
        print("❌ MONGODB_URL not found in environment variables")
        print("Please set MONGODB_URL environment variable")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.language_tutor
        learning_plans_collection = db.learning_plans
        
        print("🔗 Connected to Railway MongoDB")
        
        # Find Kamile's learning plan
        learning_plan_id = "c9a0b7e9-1938-4353-95d0-c91c6b339769"
        user_id = "6863ba8450b8c0aa0d78de51"
        
        plan = await learning_plans_collection.find_one({"id": learning_plan_id})
        
        if not plan:
            print(f"❌ Learning plan {learning_plan_id} not found")
            return
        
        print(f"✅ Found learning plan for user {user_id}")
        
        # Get current progress
        completed_sessions = plan.get("completed_sessions", 0)
        total_sessions = plan.get("total_sessions", 48)
        
        print(f"📊 Current progress: {completed_sessions} sessions completed")
        
        # Calculate sessions per week (2 sessions per week)
        sessions_per_week = 2
        
        # Get the weekly schedule
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        
        if not weekly_schedule:
            print("❌ No weekly schedule found in learning plan")
            return
        
        print(f"📅 Weekly schedule has {len(weekly_schedule)} weeks")
        
        # Fix the weekly schedule based on completed sessions
        for session_num in range(1, completed_sessions + 1):
            # Calculate which week this session belongs to
            week_number = ((session_num - 1) // sessions_per_week) + 1
            session_in_week = ((session_num - 1) % sessions_per_week) + 1
            
            week_index = week_number - 1  # Convert to 0-based index
            
            if week_index < len(weekly_schedule):
                # Update the sessions_completed for this week
                current_sessions_in_week = weekly_schedule[week_index].get("sessions_completed", 0)
                if session_in_week > current_sessions_in_week:
                    weekly_schedule[week_index]["sessions_completed"] = session_in_week
                    print(f"🔄 Updated Week {week_number} to show {session_in_week} sessions completed")
        
        # Show the final state
        print(f"\n📋 FINAL WEEKLY SCHEDULE:")
        for i, week in enumerate(weekly_schedule[:4]):  # Show first 4 weeks
            week_num = i + 1
            sessions_completed = week.get("sessions_completed", 0)
            total_sessions_week = week.get("total_sessions", 2)
            print(f"  Week {week_num}: {sessions_completed}/{total_sessions_week} sessions completed")
        
        # Update the learning plan document
        update_data = {
            "plan_content.weekly_schedule": weekly_schedule,
            "updated_at": datetime.utcnow()
        }
        
        result = await learning_plans_collection.update_one(
            {"id": learning_plan_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully updated weekly schedule!")
            print(f"📊 Total progress: {completed_sessions}/{total_sessions} sessions")
            
            # Show expected state
            print(f"\n🎯 EXPECTED STATE:")
            print(f"  Week 1: 2/2 sessions completed ✅")
            print(f"  Week 2: 1/2 sessions completed ✅")
            print(f"  Week 3: 0/2 sessions completed")
            print(f"  Next session will be Week 2, Session 2")
        else:
            print("⚠️ No changes were made to the learning plan")
        
        # Verify the update
        updated_plan = await learning_plans_collection.find_one({"id": learning_plan_id})
        if updated_plan:
            updated_schedule = updated_plan.get("plan_content", {}).get("weekly_schedule", [])
            print(f"\n📋 VERIFICATION:")
            for i, week in enumerate(updated_schedule[:4]):
                week_num = i + 1
                sessions_completed = week.get("sessions_completed", 0)
                total_sessions_week = week.get("total_sessions", 2)
                status = "✅" if sessions_completed > 0 else "⏳"
                print(f"  Week {week_num}: {sessions_completed}/{total_sessions_week} sessions {status}")
        
        if client:
            client.close()
        print("\n🎉 Week 2 progress fix completed!")
        
    except Exception as e:
        print(f"❌ Error fixing Week 2 progress: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(fix_kamile_week2_progress())
