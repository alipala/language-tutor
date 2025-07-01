#!/usr/bin/env python3
"""
Fix Session Summary Structure

This script fixes the session summary storage structure to store summaries
within the weekly_schedule structure instead of a separate session_summaries array.

For the user Selimiye (686400809bb1effaa5448dcc), we need to move the session
summary from the root-level session_summaries array into the proper week 1
session_details structure.
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId

def get_mongo_client():
    """Get MongoDB client"""
    try:
        mongo_url = os.getenv('MONGODB_URL')
        if not mongo_url:
            print("❌ MONGODB_URL environment variable not set!")
            return None
            
        client = MongoClient(mongo_url)
        print(f"✅ Connected to Railway Production MongoDB")
        
        # Test the connection
        client.admin.command('ping')
        print(f"✅ Database connection verified")
        return client
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def fix_session_summary_structure():
    """Fix session summary structure for Selimiye user"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client['language_tutor']
        selimiye_user_id = "686400809bb1effaa5448dcc"
        
        print(f"🎯 Fixing session summary structure for Selimiye: {selimiye_user_id}")
        
        # Get Selimiye's learning plan
        learning_plan = db.learning_plans.find_one({"user_id": selimiye_user_id})
        if not learning_plan:
            print(f"❌ Learning plan not found!")
            return False
        
        print(f"\n📚 Learning Plan: {learning_plan.get('id')}")
        print(f"📊 Current completed sessions: {learning_plan.get('completed_sessions', 0)}")
        print(f"📋 Current session_summaries count: {len(learning_plan.get('session_summaries', []))}")
        
        # Get the session summaries from the root level
        session_summaries = learning_plan.get('session_summaries', [])
        weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
        
        if not session_summaries:
            print("ℹ️ No session summaries to move")
            return True
        
        if not weekly_schedule:
            print("❌ No weekly schedule found")
            return False
        
        print(f"\n🔄 Moving {len(session_summaries)} session summaries to weekly structure...")
        
        # Process each session summary and place it in the correct week
        sessions_per_week = 2
        updated_weekly_schedule = weekly_schedule.copy()
        
        for session_index, summary in enumerate(session_summaries):
            # Calculate which week this session belongs to (0-based)
            week_index = session_index // sessions_per_week
            session_in_week = (session_index % sessions_per_week) + 1  # 1-based session number in week
            
            if week_index < len(updated_weekly_schedule):
                week = updated_weekly_schedule[week_index]
                
                # Initialize session_details if it doesn't exist
                if 'session_details' not in week:
                    week['session_details'] = []
                
                # Create session detail object
                session_detail = {
                    "session_number": session_in_week,
                    "global_session_number": session_index + 1,
                    "summary": summary,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "completed"
                }
                
                # Add to session_details
                week['session_details'].append(session_detail)
                
                print(f"✅ Moved session {session_index + 1} to Week {week_index + 1}, Session {session_in_week}")
            else:
                print(f"⚠️ Session {session_index + 1} exceeds available weeks")
        
        # Update the learning plan with the new structure
        result = db.learning_plans.update_one(
            {"_id": learning_plan["_id"]},
            {
                "$set": {"plan_content.weekly_schedule": updated_weekly_schedule},
                "$unset": {"session_summaries": ""}  # Remove the old session_summaries array
            }
        )
        
        if result.modified_count > 0:
            print(f"\n✅ Successfully updated learning plan structure!")
            print(f"✅ Moved {len(session_summaries)} session summaries to weekly structure")
            print(f"✅ Removed old session_summaries array")
            
            # Verify the update
            updated_plan = db.learning_plans.find_one({"_id": learning_plan["_id"]})
            updated_weekly_schedule = updated_plan.get('plan_content', {}).get('weekly_schedule', [])
            
            # Count sessions in weekly structure
            total_sessions_in_weeks = 0
            for week in updated_weekly_schedule:
                session_details = week.get('session_details', [])
                total_sessions_in_weeks += len(session_details)
            
            print(f"\n📊 Verification:")
            print(f"   Sessions now in weekly structure: {total_sessions_in_weeks}")
            print(f"   Old session_summaries array: {'REMOVED' if 'session_summaries' not in updated_plan else 'STILL EXISTS'}")
            
            return True
        else:
            print(f"❌ Failed to update learning plan structure")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing session summary structure: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    print("🔧 Starting session summary structure fix...")
    success = fix_session_summary_structure()
    if success:
        print("✅ Session summary structure fix completed successfully!")
    else:
        print("❌ Session summary structure fix failed!")
    sys.exit(0 if success else 1)
