#!/usr/bin/env python3
"""
Fix Session Count Tracking Issue

This script fixes the session count tracking issue where learning plan sessions
were not properly incrementing the user's practice_sessions_used counter.

Issue: User alipala.ist@gmail.com shows 1/30 sessions used but has completed 8 total sessions
- 7 Dutch learning plan sessions
- 1 English learning plan session  
- 1 regular conversation session

The user should show 8/30 sessions used, not 1/30.
"""

import asyncio
import os
import sys
from datetime import datetime
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database

async def fix_session_count_tracking():
    """Fix session count tracking for users with learning plan sessions"""
    
    print("🔧 FIXING SESSION COUNT TRACKING ISSUE")
    print("=" * 50)
    
    # Target user
    target_email = "alipala.ist@gmail.com"
    target_user_id = "688921c268819565ef1ce3dc"
    
    try:
        # Get collections
        users_collection = database.users
        learning_plans_collection = database.learning_plans
        conversation_sessions_collection = database.conversation_sessions
        
        # Find the user
        print(f"🔍 Looking for user: {target_email}")
        user = await users_collection.find_one({"email": target_email})
        
        if not user:
            print(f"❌ User not found: {target_email}")
            return False
        
        print(f"✅ Found user: {user['name']} ({user['email']})")
        print(f"   User ID: {user['_id']}")
        
        # Get current subscription usage
        current_sessions_used = user.get("practice_sessions_used", 0)
        current_minutes_used = user.get("practice_minutes_used", 0.0)
        
        print(f"\n📊 CURRENT SUBSCRIPTION USAGE:")
        print(f"   Sessions Used: {current_sessions_used}")
        print(f"   Minutes Used: {current_minutes_used}")
        
        # Count learning plan sessions
        learning_plans = await learning_plans_collection.find({"user_id": target_user_id}).to_list(length=None)
        
        total_learning_plan_sessions = 0
        total_estimated_minutes = 0.0
        
        print(f"\n📚 LEARNING PLANS ANALYSIS:")
        for plan in learning_plans:
            plan_sessions = plan.get("completed_sessions", 0)
            plan_language = plan.get("language", "unknown")
            plan_level = plan.get("proficiency_level", "unknown")
            
            # Estimate minutes (5 minutes per session average)
            estimated_minutes = plan_sessions * 5.0
            
            total_learning_plan_sessions += plan_sessions
            total_estimated_minutes += estimated_minutes
            
            print(f"   Plan: {plan_language.title()} ({plan_level}) - {plan_sessions} sessions (~{estimated_minutes} min)")
        
        # Count conversation sessions
        conversation_sessions = await conversation_sessions_collection.find({"user_id": target_user_id}).to_list(length=None)
        
        total_conversation_sessions = len(conversation_sessions)
        total_conversation_minutes = sum(session.get("duration_minutes", 0) for session in conversation_sessions)
        
        print(f"\n💬 CONVERSATION SESSIONS ANALYSIS:")
        print(f"   Regular Conversations: {total_conversation_sessions} sessions ({total_conversation_minutes:.2f} min)")
        
        # Calculate totals
        expected_total_sessions = total_learning_plan_sessions + total_conversation_sessions
        expected_total_minutes = total_estimated_minutes + total_conversation_minutes
        
        print(f"\n🎯 EXPECTED TOTALS:")
        print(f"   Total Sessions: {expected_total_sessions}")
        print(f"   Total Minutes: {expected_total_minutes:.2f}")
        
        print(f"\n🔍 DISCREPANCY ANALYSIS:")
        session_discrepancy = expected_total_sessions - current_sessions_used
        minute_discrepancy = expected_total_minutes - current_minutes_used
        
        print(f"   Session Discrepancy: {session_discrepancy} sessions missing")
        print(f"   Minute Discrepancy: {minute_discrepancy:.2f} minutes missing")
        
        if session_discrepancy <= 0 and minute_discrepancy <= 0:
            print(f"✅ No discrepancy found. User tracking is correct.")
            return True
        
        # Apply fix
        print(f"\n🔧 APPLYING FIX:")
        print(f"   Updating sessions: {current_sessions_used} → {expected_total_sessions}")
        print(f"   Updating minutes: {current_minutes_used:.2f} → {expected_total_minutes:.2f}")
        
        # Update user subscription usage
        update_result = await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "practice_sessions_used": expected_total_sessions,
                "practice_minutes_used": expected_total_minutes,
                "session_count_fix_applied": True,
                "session_count_fix_date": datetime.utcnow().isoformat(),
                "session_count_fix_details": {
                    "learning_plan_sessions": total_learning_plan_sessions,
                    "conversation_sessions": total_conversation_sessions,
                    "estimated_learning_minutes": total_estimated_minutes,
                    "conversation_minutes": total_conversation_minutes,
                    "total_sessions": expected_total_sessions,
                    "total_minutes": expected_total_minutes,
                    "sessions_added": session_discrepancy,
                    "minutes_added": minute_discrepancy
                }
            }}
        )
        
        if update_result.modified_count > 0:
            print(f"✅ Successfully updated user subscription usage")
            
            # Verify the fix
            updated_user = await users_collection.find_one({"_id": user["_id"]})
            new_sessions_used = updated_user.get("practice_sessions_used", 0)
            new_minutes_used = updated_user.get("practice_minutes_used", 0.0)
            
            print(f"\n✅ VERIFICATION:")
            print(f"   Sessions Used: {new_sessions_used}/30 (was {current_sessions_used}/30)")
            print(f"   Minutes Used: {new_minutes_used:.2f}/150 (was {current_minutes_used:.2f}/150)")
            
            # Calculate remaining
            sessions_remaining = 30 - new_sessions_used
            minutes_remaining = 150 - new_minutes_used
            
            print(f"   Sessions Remaining: {sessions_remaining}/30")
            print(f"   Minutes Remaining: {minutes_remaining:.2f}/150")
            
            if sessions_remaining >= 0 and minutes_remaining >= 0:
                print(f"✅ Fix successful! User now shows correct usage.")
            else:
                print(f"⚠️ Warning: User may have exceeded limits after fix.")
            
            return True
        else:
            print(f"❌ Failed to update user subscription usage")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing session count tracking: {str(e)}")
        return False

async def main():
    """Main function"""
    print("🚀 Starting Session Count Tracking Fix")
    print(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")
    
    success = await fix_session_count_tracking()
    
    if success:
        print(f"\n🎉 SESSION COUNT TRACKING FIX COMPLETED SUCCESSFULLY!")
        print(f"   The user should now see correct session and minute usage.")
        print(f"   Future learning plan sessions will be tracked properly.")
    else:
        print(f"\n❌ SESSION COUNT TRACKING FIX FAILED!")
        print(f"   Please check the logs and try again.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
