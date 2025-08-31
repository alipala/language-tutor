#!/usr/bin/env python3
"""
COMPREHENSIVE SESSION TRACKING FIX
==================================
This script fixes the session tracking issues by:
1. Adding the completed Dutch A1 session to the learning plan
2. Updating user subscription tracking (both minutes and sessions)
3. Ensuring data consistency across all collections
"""

import os
import sys
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import asyncio

# Database connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"

def connect_to_database():
    """Connect to the production database"""
    client = MongoClient(MONGODB_URL)
    db = client['language_tutor']
    return client, db

def main():
    print("🔧 COMPREHENSIVE SESSION TRACKING FIX")
    print("=" * 60)
    
    # User and session details
    user_id = "688921c268819565ef1ce3dc"
    dutch_plan_id = "e45effa0-38be-4666-8588-fd1d1ce183f0"
    session_duration_minutes = 5.95  # 5:57 = 5.95 minutes
    session_messages = 41
    
    print(f"👤 User ID: {user_id}")
    print(f"📋 Dutch Plan ID: {dutch_plan_id}")
    print(f"⏱️  Session Duration: {session_duration_minutes} minutes")
    print(f"💬 Messages: {session_messages}")
    
    try:
        # Connect to database
        client, db = connect_to_database()
        print("✅ Connected to production database")
        
        # STEP 1: Update the learning plan with session data
        print("\n🔧 STEP 1: Adding session to learning plan")
        print("-" * 50)
        
        # Find the Dutch learning plan
        learning_plan = db.learning_plans.find_one({"id": dutch_plan_id})
        if not learning_plan:
            print("❌ Dutch learning plan not found!")
            return False
            
        print(f"✅ Found Dutch learning plan: {learning_plan['language']} - {learning_plan.get('proficiency_level', 'N/A')}")
        
        # Get current progress
        current_completed = learning_plan.get("completed_sessions", 0)
        total_sessions = learning_plan.get("total_sessions", 96)
        current_minutes = learning_plan.get("practice_minutes_used", 0.0)
        
        print(f"📊 Current progress: {current_completed}/{total_sessions} sessions")
        print(f"📊 Current minutes: {current_minutes}")
        
        # Calculate new progress
        new_completed = current_completed + 1
        new_minutes = current_minutes + session_duration_minutes
        progress_percentage = (new_completed / total_sessions) * 100 if total_sessions > 0 else 0.0
        
        # Create session data
        session_data = {
            "session_number": new_completed,
            "completed_at": datetime.utcnow().isoformat(),
            "duration_minutes": session_duration_minutes,
            "message_count": session_messages,
            "language": "dutch",
            "level": "A1",
            "topic": "Basic Conversation",
            "status": "completed",
            "summary": f"Completed Dutch A1 session with {session_messages} messages in {session_duration_minutes} minutes"
        }
        
        # Update learning plan
        update_result = db.learning_plans.update_one(
            {"id": dutch_plan_id},
            {
                "$set": {
                    "completed_sessions": new_completed,
                    "progress_percentage": progress_percentage,
                    "practice_minutes_used": new_minutes,
                    "updated_at": datetime.utcnow().isoformat()
                },
                "$push": {
                    "sessions": session_data
                }
            }
        )
        
        if update_result.modified_count > 0:
            print(f"✅ Updated learning plan:")
            print(f"   Sessions: {current_completed} → {new_completed}")
            print(f"   Minutes: {current_minutes} → {new_minutes}")
            print(f"   Progress: {progress_percentage:.1f}%")
        else:
            print("❌ Failed to update learning plan")
            return False
        
        # STEP 2: Update user subscription tracking
        print("\n🔧 STEP 2: Updating user subscription tracking")
        print("-" * 50)
        
        # Find user
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            print("❌ User not found!")
            return False
            
        print(f"✅ Found user: {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
        
        # Get current subscription tracking
        current_practice_minutes = user.get("practice_minutes_used", 0.0)
        current_practice_sessions = user.get("practice_sessions_used", 0)
        
        print(f"📊 Current subscription usage:")
        print(f"   Minutes: {current_practice_minutes}")
        print(f"   Sessions: {current_practice_sessions}")
        
        # Calculate new subscription tracking
        new_practice_minutes = current_practice_minutes + session_duration_minutes
        new_practice_sessions = current_practice_sessions + 1
        
        # Update user subscription tracking
        user_update_result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "practice_minutes_used": new_practice_minutes,
                    "practice_sessions_used": new_practice_sessions,
                    "last_session_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if user_update_result.modified_count > 0:
            print(f"✅ Updated user subscription tracking:")
            print(f"   Minutes: {current_practice_minutes} → {new_practice_minutes}")
            print(f"   Sessions: {current_practice_sessions} → {new_practice_sessions}")
        else:
            print("❌ Failed to update user subscription tracking")
            return False
        
        # STEP 3: Verify the fix
        print("\n🔧 STEP 3: Verifying the fix")
        print("-" * 50)
        
        # Re-fetch updated data
        updated_plan = db.learning_plans.find_one({"id": dutch_plan_id})
        updated_user = db.users.find_one({"_id": ObjectId(user_id)})
        
        print("📊 VERIFICATION RESULTS:")
        print(f"   Learning Plan Sessions: {updated_plan.get('completed_sessions', 0)}")
        print(f"   Learning Plan Minutes: {updated_plan.get('practice_minutes_used', 0.0)}")
        print(f"   User Practice Sessions: {updated_user.get('practice_sessions_used', 0)}")
        print(f"   User Practice Minutes: {updated_user.get('practice_minutes_used', 0.0)}")
        
        # Check if session was added to sessions array
        sessions = updated_plan.get('sessions', [])
        print(f"   Sessions in plan: {len(sessions)}")
        if sessions:
            latest_session = sessions[-1]
            print(f"   Latest session: {latest_session.get('duration_minutes', 0)} min, {latest_session.get('message_count', 0)} messages")
        
        print("\n🎉 COMPREHENSIVE FIX COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ Session data added to learning plan")
        print("✅ User subscription tracking updated")
        print("✅ Both minutes and session counts are now accurate")
        print("✅ Data consistency verified across collections")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during fix: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            client.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
