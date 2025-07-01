#!/usr/bin/env python3
"""
Script to fix Kamile's subscription usage data to reflect actual sessions completed
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB connection for Railway
MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("DATABASE_URL")

async def fix_kamile_subscription_usage():
    """Fix Kamile's subscription usage to reflect actual sessions and assessments completed"""
    
    if not MONGODB_URL:
        print("❌ MONGODB_URL not found in environment variables")
        print("Please set MONGODB_URL environment variable")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.language_tutor
        users_collection = db.users
        learning_plans_collection = db.learning_plans
        
        print("🔗 Connected to Railway MongoDB")
        
        # Find Kamile's user record
        from bson import ObjectId
        user_id_str = "6863ba8450b8c0aa0d78de51"
        user_id = ObjectId(user_id_str)
        
        user = await users_collection.find_one({"_id": user_id})
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"✅ Found user: {user.get('name', 'Unknown')}")
        print(f"📧 Email: {user.get('email', 'Unknown')}")
        print(f"📋 Subscription Plan: {user.get('subscription_plan', 'Unknown')}")
        
        # Get current usage data
        current_practice_sessions = user.get("practice_sessions_used", 0)
        current_assessments = user.get("assessments_used", 0)
        
        print(f"\n📊 CURRENT USAGE DATA:")
        print(f"  Practice Sessions Used: {current_practice_sessions}")
        print(f"  Assessments Used: {current_assessments}")
        
        # Find Kamile's learning plan to get actual completed sessions
        # Try both ObjectId and string formats
        learning_plan = await learning_plans_collection.find_one({"user_id": user_id})
        if not learning_plan:
            learning_plan = await learning_plans_collection.find_one({"user_id": user_id_str})
        
        if learning_plan:
            completed_sessions = learning_plan.get("completed_sessions", 0)
            print(f"  Learning Plan Sessions Completed: {completed_sessions}")
            
            # Check if user has assessment data (they completed 1 assessment)
            has_assessment = bool(user.get("last_assessment_data") or user.get("assessment_history"))
            assessments_completed = 1 if has_assessment else 0
            
            print(f"  Assessments Completed: {assessments_completed}")
            
            # Calculate correct usage
            correct_practice_sessions = completed_sessions  # 3 sessions completed
            correct_assessments = assessments_completed     # 1 assessment completed
            
            print(f"\n🎯 CORRECT USAGE DATA:")
            print(f"  Practice Sessions Should Be: {correct_practice_sessions}")
            print(f"  Assessments Should Be: {correct_assessments}")
            
            # Update user record
            update_data = {
                "practice_sessions_used": correct_practice_sessions,
                "assessments_used": correct_assessments,
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print("✅ Successfully updated subscription usage!")
                
                # Calculate remaining for Fluency Builder (30 sessions, 2 assessments per month)
                sessions_limit = 30
                assessments_limit = 2
                
                sessions_remaining = sessions_limit - correct_practice_sessions
                assessments_remaining = assessments_limit - correct_assessments
                
                print(f"\n📈 UPDATED SUBSCRIPTION STATUS:")
                print(f"  Practice Sessions: {correct_practice_sessions}/{sessions_limit} used")
                print(f"  Sessions Remaining: {sessions_remaining}")
                print(f"  Assessments: {correct_assessments}/{assessments_limit} used") 
                print(f"  Assessments Remaining: {assessments_remaining}")
                
                print(f"\n🎯 PROFILE DISPLAY SHOULD NOW SHOW:")
                print(f"  Practice Sessions: {sessions_remaining}/{sessions_limit}")
                print(f"  Assessments: {assessments_remaining}/{assessments_limit}")
                
            else:
                print("⚠️ No changes were made to the user record")
        else:
            print("❌ No learning plan found for user")
        
        # Verify the update
        updated_user = await users_collection.find_one({"_id": user_id})
        if updated_user:
            print(f"\n📋 VERIFICATION:")
            print(f"  practice_sessions_used: {updated_user.get('practice_sessions_used')}")
            print(f"  assessments_used: {updated_user.get('assessments_used')}")
        
        if client:
            client.close()
        print("\n🎉 Subscription usage fix completed!")
        
    except Exception as e:
        print(f"❌ Error fixing subscription usage: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(fix_kamile_subscription_usage())
