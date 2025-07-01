#!/usr/bin/env python3
"""
Fix Felicia's subscription usage counter to reflect ALL completed sessions across ALL learning plans.

The user has:
- English learning plan: 1/8 sessions completed
- Dutch learning plan: 1/8 sessions completed
- Total sessions completed: 2
- Current subscription counter: 1 (should be 2)
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

# MongoDB connection - will use Railway's production MongoDB URL
MONGODB_URL = os.getenv("MONGODB_URL")

async def fix_felicia_total_sessions():
    """Fix Felicia's subscription usage counter to reflect total sessions across all learning plans"""
    
    print("🔧 Fixing Felicia's Total Session Count")
    print("=" * 50)
    
    if not MONGODB_URL:
        print("❌ MONGODB_URL environment variable not set")
        return
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()
    users_collection = db.users
    learning_plans_collection = db.learning_plans
    
    try:
        # Felicia's user ID
        user_id = "686441cb2edf7bab502693aa"
        
        print(f"🔍 Looking for user: {user_id}")
        
        # Find the user
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"✅ Found user: {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
        
        # Check current subscription status
        current_sessions_used = user.get("practice_sessions_used", 0)
        subscription_plan = user.get("subscription_plan", "unknown")
        
        print(f"📊 Current Subscription Status:")
        print(f"   - Plan: {subscription_plan}")
        print(f"   - Practice Sessions Used: {current_sessions_used}")
        
        # Find ALL learning plans for this user
        learning_plans_cursor = learning_plans_collection.find({"user_id": user_id})
        learning_plans = await learning_plans_cursor.to_list(length=None)
        
        if not learning_plans:
            print(f"❌ No learning plans found for user {user_id}")
            return
        
        print(f"📚 Found {len(learning_plans)} learning plans:")
        
        total_completed_sessions = 0
        
        for i, plan in enumerate(learning_plans, 1):
            language = plan.get('language', 'Unknown')
            level = plan.get('proficiency_level', 'Unknown')
            completed = plan.get('completed_sessions', 0)
            total = plan.get('total_sessions', 0)
            
            print(f"   {i}. {language.title()} ({level}): {completed}/{total} sessions completed")
            total_completed_sessions += completed
        
        print(f"\n🧮 Calculating Correct Usage:")
        print(f"   - Total sessions completed across all plans: {total_completed_sessions}")
        print(f"   - Current subscription counter: {current_sessions_used}")
        print(f"   - Correct value should be: {total_completed_sessions}")
        
        if current_sessions_used == total_completed_sessions:
            print(f"✅ Subscription usage is already correct!")
            return
        
        # Ask for confirmation before making changes
        print(f"\n⚠️  PROPOSED CHANGE:")
        print(f"   - Update practice_sessions_used: {current_sessions_used} → {total_completed_sessions}")
        
        confirm = input(f"\nDo you want to proceed with this update? (yes/no): ").lower().strip()
        
        if confirm != 'yes':
            print(f"❌ Update cancelled by user")
            return
        
        # Update the user's subscription usage
        print(f"\n🔄 Updating subscription usage...")
        
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"practice_sessions_used": total_completed_sessions}}
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
                print(f"   - English plan shows: 1/8 sessions")
                print(f"   - Dutch plan shows: 1/8 sessions")
                print(f"✅ SUCCESS: All metrics are now synchronized!")
            
        else:
            print(f"❌ Failed to update subscription usage")
        
    except Exception as e:
        print(f"❌ Error during fix: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_felicia_total_sessions())
