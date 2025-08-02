#!/usr/bin/env python3
"""
Fix existing user's subscription usage counter in production.

This script will:
1. Connect to the production MongoDB database
2. Find the specific user with the issue
3. Calculate the correct practice_sessions_used based on their learning plan progress
4. Update their subscription usage counter to match their actual usage
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

# MongoDB connection - will use Railway's production MongoDB URL
MONGODB_URL = os.getenv("MONGODB_URL")

async def fix_user_subscription_usage():
    """Fix the subscription usage counter for the existing user"""
    
    print("🔧 Fixing Existing User Subscription Usage")
    print("=" * 50)
    
    if not MONGODB_URL:
        print("❌ MONGODB_URL environment variable not set")
        print("Please set the Railway production MongoDB URL:")
        print("export MONGODB_URL='mongodb://...'")
        return
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    users_collection = db.users
    learning_plans_collection = db.learning_plans
    
    try:
        # Find the specific user from the logs (user ID: 686441cb2edf7bab502693aa)
        user_id = "686441cb2edf7bab502693aa"
        
        print(f"🔍 Looking for user: {user_id}")
        
        # Try to find the user with ObjectId
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"✅ Found user: {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
        
        # Check current subscription status
        current_sessions_used = user.get("practice_sessions_used", 0)
        current_assessments_used = user.get("assessments_used", 0)
        subscription_status = user.get("subscription_status", "unknown")
        subscription_plan = user.get("subscription_plan", "unknown")
        
        print(f"📊 Current Status:")
        print(f"   - Plan: {subscription_plan}")
        print(f"   - Status: {subscription_status}")
        print(f"   - Practice Sessions Used: {current_sessions_used}")
        print(f"   - Assessments Used: {current_assessments_used}")
        
        # Find their learning plan to see actual progress
        learning_plan = await learning_plans_collection.find_one({"user_id": user_id})
        
        if not learning_plan:
            print(f"❌ No learning plan found for user {user_id}")
            return
        
        completed_sessions = learning_plan.get("completed_sessions", 0)
        total_sessions = learning_plan.get("total_sessions", 0)
        
        print(f"📈 Learning Plan Progress:")
        print(f"   - Language: {learning_plan.get('language', 'Unknown')}")
        print(f"   - Level: {learning_plan.get('proficiency_level', 'Unknown')}")
        print(f"   - Completed Sessions: {completed_sessions}/{total_sessions}")
        
        # Calculate the correct subscription usage
        # The user has completed 1 session, so practice_sessions_used should be 1
        correct_sessions_used = completed_sessions
        
        print(f"\n🧮 Calculating Correct Usage:")
        print(f"   - Learning plan shows: {completed_sessions} sessions completed")
        print(f"   - Subscription counter shows: {current_sessions_used} sessions used")
        print(f"   - Correct value should be: {correct_sessions_used}")
        
        if current_sessions_used == correct_sessions_used:
            print(f"✅ Subscription usage is already correct!")
            return
        
        # Ask for confirmation before making changes
        print(f"\n⚠️  PROPOSED CHANGE:")
        print(f"   - Update practice_sessions_used: {current_sessions_used} → {correct_sessions_used}")
        
        # In production, we want to be extra careful
        confirm = input(f"\nDo you want to proceed with this update? (yes/no): ").lower().strip()
        
        if confirm != 'yes':
            print(f"❌ Update cancelled by user")
            return
        
        # Update the user's subscription usage
        print(f"\n🔄 Updating subscription usage...")
        
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"practice_sessions_used": correct_sessions_used}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated subscription usage!")
            
            # Verify the update
            updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
            new_sessions_used = updated_user.get("practice_sessions_used", 0)
            
            print(f"📊 Updated Status:")
            print(f"   - Practice Sessions Used: {current_sessions_used} → {new_sessions_used}")
            
            # Calculate what the frontend will now show
            if subscription_plan == "fluency_builder":
                sessions_limit = 30  # Monthly limit for Fluency Builder
                sessions_remaining = max(0, sessions_limit - new_sessions_used)
                print(f"   - Frontend will now show: {sessions_remaining}/{sessions_limit}")
                print(f"   - Learning plan shows: {completed_sessions}/{total_sessions}")
                print(f"✅ SUCCESS: Both metrics are now synchronized!")
            
        else:
            print(f"❌ Failed to update subscription usage")
        
    except Exception as e:
        print(f"❌ Error during fix: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_user_subscription_usage())
