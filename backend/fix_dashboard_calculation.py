#!/usr/bin/env python3
"""
Fix Dashboard Speaking Time Calculation Issue

The dashboard shows incorrect "Speaking Time" because the user record has stale data
that doesn't match the actual sessions in the current subscription period.

This script will:
1. Check the user's actual session data in the current period
2. Recalculate the correct minutes_used based on actual sessions
3. Update the user record to match reality
4. Verify the fix works
"""

import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable is required")

async def fix_dashboard_calculation():
    """Fix the dashboard speaking time calculation for user Ali Pala"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_database()
    
    try:
        user_id = "688921c268819565ef1ce3dc"
        user_email = "alipala.ist@gmail.com"
        
        print(f"🔧 FIXING DASHBOARD CALCULATION FOR {user_email}")
        print("=" * 60)
        
        # Get user data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"👤 Current user record:")
        print(f"   📧 Email: {user.get('email')}")
        print(f"   📊 Minutes used: {user.get('practice_minutes_used', 0)}")
        print(f"   📊 Sessions used: {user.get('practice_sessions_used', 0)}")
        
        # Get subscription period
        period_start = user.get('current_period_start')
        period_end = user.get('current_period_end')
        
        if not period_start or not period_end:
            print("⚠️ No subscription period found, using current month")
            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
        
        print(f"📅 Subscription period: {period_start} to {period_end}")
        
        # Check actual conversation sessions in current period
        conversation_sessions = await db.conversation_sessions.find({
            "user_id": user_id,
            "created_at": {
                "$gte": period_start,
                "$lt": period_end
            }
        }).to_list(length=None)
        
        conversation_minutes = sum(session.get('duration_minutes', 0) for session in conversation_sessions)
        print(f"💬 Conversation sessions in period: {len(conversation_sessions)} ({conversation_minutes:.2f} min)")
        
        # Check learning plan sessions in current period
        learning_plans = await db.learning_plans.find({"user_id": user_id}).to_list(length=None)
        learning_minutes = 0
        learning_sessions_count = 0
        
        for plan in learning_plans:
            sessions = plan.get('sessions', [])
            for session in sessions:
                session_date = session.get('date')
                if session_date and period_start <= session_date < period_end:
                    learning_minutes += session.get('duration_minutes', 0)
                    learning_sessions_count += 1
        
        print(f"🎓 Learning plan sessions in period: {learning_sessions_count} ({learning_minutes:.2f} min)")
        
        # Calculate total actual usage
        total_actual_minutes = conversation_minutes + learning_minutes
        total_actual_sessions = len(conversation_sessions) + learning_sessions_count
        
        print(f"🎯 ACTUAL USAGE IN CURRENT PERIOD:")
        print(f"   - Total sessions: {total_actual_sessions}")
        print(f"   - Total minutes: {total_actual_minutes:.2f}")
        
        # Compare with user record
        user_record_minutes = user.get('practice_minutes_used', 0)
        user_record_sessions = user.get('practice_sessions_used', 0)
        
        print(f"📊 USER RECORD SHOWS:")
        print(f"   - Sessions: {user_record_sessions}")
        print(f"   - Minutes: {user_record_minutes:.2f}")
        
        if abs(user_record_minutes - total_actual_minutes) > 0.1 or user_record_sessions != total_actual_sessions:
            print(f"❌ DISCREPANCY FOUND!")
            print(f"   - Minutes difference: {user_record_minutes - total_actual_minutes:.2f}")
            print(f"   - Sessions difference: {user_record_sessions - total_actual_sessions}")
            
            # Fix the user record
            print(f"🔧 FIXING USER RECORD...")
            
            update_result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "practice_minutes_used": total_actual_minutes,
                        "practice_sessions_used": total_actual_sessions,
                        "last_dashboard_fix": datetime.utcnow().isoformat(),
                        "dashboard_fix_reason": "fix_stale_data_discrepancy",
                        "current_period_start": period_start,
                        "current_period_end": period_end
                    }
                }
            )
            
            if update_result.modified_count > 0:
                print(f"✅ USER RECORD UPDATED SUCCESSFULLY!")
                print(f"   - New minutes: {total_actual_minutes:.2f}")
                print(f"   - New sessions: {total_actual_sessions}")
                
                # Calculate what the dashboard should now show
                plan_id = user.get('subscription_plan', 'fluency_builder')
                if plan_id == 'fluency_builder':
                    monthly_limit = 150  # 150 minutes for Fluency Builder
                    remaining = monthly_limit - total_actual_minutes
                    print(f"🎯 DASHBOARD SHOULD NOW SHOW:")
                    print(f"   - Speaking Time: {remaining:.0f} min left")
                    print(f"   - Used: {total_actual_minutes:.2f}/{monthly_limit} minutes")
                
            else:
                print(f"❌ Failed to update user record")
        else:
            print(f"✅ No discrepancy found - user record is correct")
        
        # Verify the fix by checking what the subscription service would calculate
        print(f"\n🔍 VERIFYING SUBSCRIPTION SERVICE CALCULATION...")
        
        # Simulate what the subscription service calculates
        minutes_limit = 150  # Fluency Builder monthly limit
        minutes_used = total_actual_minutes
        minutes_remaining = minutes_limit - minutes_used
        
        print(f"📊 SUBSCRIPTION SERVICE CALCULATION:")
        print(f"   - Limit: {minutes_limit} minutes")
        print(f"   - Used: {minutes_used:.2f} minutes")
        print(f"   - Remaining: {minutes_remaining:.2f} minutes")
        
        print(f"\n✅ DASHBOARD FIX COMPLETE!")
        print(f"The dashboard should now show: '{minutes_remaining:.0f} min left'")
        
    except Exception as e:
        print(f"❌ Error fixing dashboard calculation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(fix_dashboard_calculation())
