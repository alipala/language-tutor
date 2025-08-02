#!/usr/bin/env python3
"""
Script to update Kamile's learning plan data in Railway MongoDB
to properly reflect completed sessions and weekly progress
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB connection for Railway
MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("DATABASE_URL")

async def update_kamile_learning_plan():
    """Update Kamile's learning plan to reflect proper progress"""
    
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
        print(f"📊 Current progress: {plan.get('completed_sessions', 0)} sessions")
        
        # Update the learning plan data
        # User has completed 2 sessions, so Week 1 should show 2/2 completed
        # Next session will be Week 2, Session 1
        
        # Get the weekly schedule
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        
        if not weekly_schedule:
            print("❌ No weekly schedule found in learning plan")
            return
        
        # Update Week 1 to show 2 sessions completed
        if len(weekly_schedule) >= 1:
            weekly_schedule[0]["sessions_completed"] = 2
            print("✅ Updated Week 1: sessions_completed = 2")
        
        # Ensure Week 2 starts with 0 sessions completed
        if len(weekly_schedule) >= 2:
            weekly_schedule[1]["sessions_completed"] = 0
            print("✅ Updated Week 2: sessions_completed = 0")
        
        # Update the learning plan document
        update_data = {
            "completed_sessions": 2,
            "progress_percentage": (2 / 48) * 100,  # 2 out of 48 total sessions
            "plan_content.weekly_schedule": weekly_schedule,
            "updated_at": datetime.utcnow()
        }
        
        result = await learning_plans_collection.update_one(
            {"id": learning_plan_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully updated learning plan!")
            print(f"📊 Progress: 2/48 sessions ({(2/48)*100:.1f}%)")
            print("📅 Week 1: 2/2 sessions completed")
            print("📅 Week 2: 0/2 sessions completed")
            print("🎯 Next session will be Week 2, Session 1")
        else:
            print("⚠️ No changes were made to the learning plan")
        
        # Verify the update
        updated_plan = await learning_plans_collection.find_one({"id": learning_plan_id})
        if updated_plan:
            print("\n📋 VERIFICATION:")
            print(f"✅ completed_sessions: {updated_plan.get('completed_sessions')}")
            print(f"✅ progress_percentage: {updated_plan.get('progress_percentage'):.1f}%")
            
            updated_schedule = updated_plan.get("plan_content", {}).get("weekly_schedule", [])
            if len(updated_schedule) >= 2:
                print(f"✅ Week 1 sessions_completed: {updated_schedule[0].get('sessions_completed')}")
                print(f"✅ Week 2 sessions_completed: {updated_schedule[1].get('sessions_completed')}")
        
        if client:
            client.close()
        print("\n🎉 Update completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating learning plan: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(update_kamile_learning_plan())
