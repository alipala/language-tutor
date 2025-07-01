#!/usr/bin/env python3
"""
Script to fix session summary structure and improve data organization
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

# MongoDB connection for Railway
MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("DATABASE_URL")

async def fix_session_summary_structure():
    """Fix session summary structure to store summaries within weekly schedule"""
    
    if not MONGODB_URL:
        print("❌ MONGODB_URL not found in environment variables")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.language_tutor
        learning_plans_collection = db.learning_plans
        
        print("🔗 Connected to Railway MongoDB")
        
        # Find Kamile's learning plan
        user_id_str = "6863ba8450b8c0aa0d78de51"
        plan_id = "c9a0b7e9-1938-4353-95d0-c91c6b339769"
        
        learning_plan = await learning_plans_collection.find_one({"id": plan_id})
        
        if not learning_plan:
            print(f"❌ Learning plan {plan_id} not found")
            return
        
        print(f"✅ Found learning plan: {learning_plan.get('id')}")
        print(f"📋 Language: {learning_plan.get('language')}")
        print(f"📋 Level: {learning_plan.get('proficiency_level')}")
        print(f"📋 Completed Sessions: {learning_plan.get('completed_sessions', 0)}")
        
        # Get current session summaries
        session_summaries = learning_plan.get("session_summaries", [])
        print(f"📊 Current session summaries count: {len(session_summaries)}")
        
        # Get weekly schedule
        weekly_schedule = learning_plan.get("plan_content", {}).get("weekly_schedule", [])
        print(f"📅 Weekly schedule weeks: {len(weekly_schedule)}")
        
        # Restructure data to include session summaries in weekly schedule
        sessions_per_week = 2
        
        for week_index, week in enumerate(weekly_schedule):
            week_number = week_index + 1
            sessions_completed = week.get("sessions_completed", 0)
            
            print(f"\n📅 Processing Week {week_number}:")
            print(f"  Sessions completed: {sessions_completed}")
            
            # Initialize session_details array if not exists
            if "session_details" not in week:
                week["session_details"] = []
            
            # Add session summaries to this week
            for session_in_week in range(1, sessions_completed + 1):
                # Calculate global session number
                global_session_number = (week_number - 1) * sessions_per_week + session_in_week
                
                # Get the corresponding session summary
                if global_session_number <= len(session_summaries):
                    session_summary = session_summaries[global_session_number - 1]
                    
                    # Create session detail object
                    session_detail = {
                        "session_number": session_in_week,
                        "global_session_number": global_session_number,
                        "summary": session_summary,
                        "completed_at": datetime.utcnow().isoformat(),
                        "status": "completed"
                    }
                    
                    # Check if this session detail already exists
                    existing_session = next(
                        (s for s in week["session_details"] if s.get("session_number") == session_in_week),
                        None
                    )
                    
                    if existing_session:
                        # Update existing session
                        existing_session.update(session_detail)
                        print(f"  ✅ Updated session {session_in_week} (global #{global_session_number})")
                    else:
                        # Add new session
                        week["session_details"].append(session_detail)
                        print(f"  ✅ Added session {session_in_week} (global #{global_session_number})")
                    
                    print(f"    Summary preview: {session_summary[:100]}...")
        
        # Update the learning plan with restructured data
        update_data = {
            "plan_content.weekly_schedule": weekly_schedule,
            "updated_at": datetime.utcnow().isoformat(),
            # Keep the original session_summaries for backward compatibility
            "session_summaries": session_summaries
        }
        
        result = await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"\n✅ Successfully restructured session summary data!")
            print(f"📊 Updated weekly schedule with session details")
            print(f"🔄 Maintained backward compatibility with session_summaries array")
            
            # Verify the update
            updated_plan = await learning_plans_collection.find_one({"id": plan_id})
            updated_weekly_schedule = updated_plan.get("plan_content", {}).get("weekly_schedule", [])
            
            print(f"\n📋 VERIFICATION:")
            for week_index, week in enumerate(updated_weekly_schedule[:3]):  # Show first 3 weeks
                week_number = week_index + 1
                session_details = week.get("session_details", [])
                print(f"  Week {week_number}: {len(session_details)} session details")
                for session in session_details:
                    session_num = session.get("session_number")
                    global_num = session.get("global_session_number")
                    summary_preview = session.get("summary", "")[:50]
                    print(f"    Session {session_num} (#{global_num}): {summary_preview}...")
        else:
            print("⚠️ No changes were made to the learning plan")
        
        if client:
            client.close()
        print("\n🎉 Session summary structure fix completed!")
        
    except Exception as e:
        print(f"❌ Error fixing session summary structure: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(fix_session_summary_structure())
