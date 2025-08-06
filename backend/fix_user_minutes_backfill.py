#!/usr/bin/env python3
"""
Backfill script to fix the missing minutes for the specific user
This will estimate and update the missing speaking minutes based on completed learning plan sessions
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection details from Railway
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

# Target user details
TARGET_USER_EMAIL = "alipala.ist@gmail.com"
TARGET_USER_ID = "688921c268819565ef1ce3dc"

async def fix_user_minutes_backfill():
    """Fix the missing minutes for the specific user by backfilling estimated usage"""
    
    print("=" * 80)
    print("🔧 FIXING USER MINUTE CALCULATION - BACKFILL OPERATION")
    print("=" * 80)
    print(f"Target User: {TARGET_USER_EMAIL}")
    print(f"User ID: {TARGET_USER_ID}")
    print()
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        database = client[DATABASE_NAME]
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Get collections
        users_collection = database.users
        conversation_sessions_collection = database.conversation_sessions
        learning_plans_collection = database.learning_plans
        
        # Get user
        user = await users_collection.find_one({"_id": ObjectId(TARGET_USER_ID)})
        if not user:
            print("❌ User not found")
            return
        
        print(f"👤 User: {user.get('email')} ({user.get('name')})")
        print()
        
        # Current state
        current_minutes_used = user.get('practice_minutes_used', 0.0)
        current_sessions_used = user.get('practice_sessions_used', 0)
        
        print("📊 CURRENT STATE")
        print("-" * 40)
        print(f"Sessions Used: {current_sessions_used}")
        print(f"Minutes Used: {current_minutes_used:.2f}")
        print()
        
        # Get learning plan sessions
        learning_plan = await learning_plans_collection.find_one({"user_id": TARGET_USER_ID})
        learning_plan_sessions = 0
        if learning_plan:
            learning_plan_sessions = learning_plan.get('completed_sessions', 0)
            print(f"Learning Plan Sessions: {learning_plan_sessions}")
        
        # Get conversation sessions
        conversation_sessions = await conversation_sessions_collection.find({"user_id": TARGET_USER_ID}).to_list(length=None)
        conversation_minutes = sum(session.get('duration_minutes', 0) for session in conversation_sessions)
        
        print(f"Conversation Sessions: {len(conversation_sessions)}")
        print(f"Conversation Minutes: {conversation_minutes:.2f}")
        print()
        
        # Calculate expected minutes
        # Learning plan sessions: estimate 5 minutes each (typical session length)
        estimated_learning_plan_minutes = learning_plan_sessions * 5.0
        total_expected_minutes = estimated_learning_plan_minutes + conversation_minutes
        
        print("🧮 CALCULATION")
        print("-" * 40)
        print(f"Learning Plan Sessions: {learning_plan_sessions} × 5 min = {estimated_learning_plan_minutes:.2f} min")
        print(f"Conversation Minutes: {conversation_minutes:.2f} min")
        print(f"Total Expected Minutes: {total_expected_minutes:.2f} min")
        print(f"Current Tracked Minutes: {current_minutes_used:.2f} min")
        print(f"Missing Minutes: {total_expected_minutes - current_minutes_used:.2f} min")
        print()
        
        # Confirm the fix
        if total_expected_minutes > current_minutes_used:
            missing_minutes = total_expected_minutes - current_minutes_used
            
            print("🔧 APPLYING FIX")
            print("-" * 40)
            print(f"Will update practice_minutes_used from {current_minutes_used:.2f} to {total_expected_minutes:.2f}")
            print(f"This adds {missing_minutes:.2f} minutes to account for learning plan sessions")
            print()
            
            # Apply the fix
            result = await users_collection.update_one(
                {"_id": ObjectId(TARGET_USER_ID)},
                {"$set": {
                    "practice_minutes_used": total_expected_minutes,
                    "backfill_applied": True,
                    "backfill_date": datetime.utcnow().isoformat(),
                    "backfill_details": {
                        "original_minutes": current_minutes_used,
                        "learning_plan_sessions": learning_plan_sessions,
                        "estimated_learning_minutes": estimated_learning_plan_minutes,
                        "conversation_minutes": conversation_minutes,
                        "total_minutes": total_expected_minutes,
                        "added_minutes": missing_minutes
                    }
                }}
            )
            
            if result.modified_count > 0:
                print("✅ BACKFILL SUCCESSFUL")
                print("-" * 40)
                print(f"Updated user {TARGET_USER_ID}")
                print(f"Practice minutes: {current_minutes_used:.2f} → {total_expected_minutes:.2f}")
                print(f"Added {missing_minutes:.2f} minutes")
                print()
                
                # Verify the fix
                updated_user = await users_collection.find_one({"_id": ObjectId(TARGET_USER_ID)})
                new_minutes_used = updated_user.get('practice_minutes_used', 0.0)
                
                # Calculate new remaining minutes (fluency_builder monthly = 150 minutes)
                minutes_limit = 150
                minutes_remaining = minutes_limit - new_minutes_used
                
                print("🎯 VERIFICATION")
                print("-" * 40)
                print(f"New Minutes Used: {new_minutes_used:.2f}")
                print(f"Minutes Limit: {minutes_limit}")
                print(f"Minutes Remaining: {minutes_remaining:.2f}")
                print(f"Expected Display: {minutes_remaining:.0f}/150 minutes remaining")
                print()
                
                if minutes_remaining < 137:  # Should be much less than the original 137
                    print("✅ Fix appears successful - remaining minutes are now realistic")
                else:
                    print("⚠️ Fix may not be complete - remaining minutes still seem high")
                    
            else:
                print("❌ BACKFILL FAILED")
                print("No documents were modified")
        else:
            print("ℹ️ NO FIX NEEDED")
            print("Current minutes tracking appears to be accurate")
        
        print()
        print("=" * 80)
        print("🔧 BACKFILL OPERATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during backfill: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
    
    finally:
        if 'client' in locals():
            client.close()
            print("📡 MongoDB connection closed")

if __name__ == "__main__":
    print("⚠️  WARNING: This script will modify production data!")
    print("This will backfill missing minutes for user:", TARGET_USER_EMAIL)
    print()
    
    # Safety confirmation
    confirm = input("Are you sure you want to proceed? (type 'YES' to confirm): ")
    if confirm == "YES":
        asyncio.run(fix_user_minutes_backfill())
    else:
        print("❌ Operation cancelled")
