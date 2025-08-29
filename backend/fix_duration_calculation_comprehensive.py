#!/usr/bin/env python3

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from bson import ObjectId

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from subscription_service import SubscriptionService

async def fix_user_duration_calculations(user_id: str):
    """
    Comprehensive fix for duration calculation issues
    """
    print("=" * 80)
    print(f"🔧 DURATION CALCULATION FIX")
    print(f"User ID: {user_id}")
    print(f"Fix Date: {datetime.utcnow()}")
    print("=" * 80)
    
    try:
        # Convert user ID to proper format
        try:
            user_object_id = ObjectId(user_id)
            user_query = {"_id": user_object_id}
        except:
            user_query = {"_id": user_id}
        
        # 1. GET CURRENT USER DATA
        print("\n📊 CURRENT USER DATA:")
        print("-" * 40)
        
        user = await database.users.find_one(user_query)
        if not user:
            print(f"❌ User {user_id} not found!")
            return
        
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Subscription Plan: {user.get('subscription_plan', 'N/A')}")
        print(f"Period Start: {user.get('current_period_start', 'N/A')}")
        print(f"Period End: {user.get('current_period_end', 'N/A')}")
        print(f"Current Sessions Used: {user.get('practice_sessions_used', 0)}")
        print(f"Current Minutes Used: {user.get('practice_minutes_used', 0.0)}")
        
        # 2. CALCULATE ACTUAL USAGE FROM ALL SOURCES
        print("\n🔍 CALCULATING ACTUAL USAGE:")
        print("-" * 40)
        
        current_period_start = user.get('current_period_start')
        current_period_end = user.get('current_period_end')
        
        if not current_period_start or not current_period_end:
            print("⚠️ Period dates missing, calculating from subscription data...")
            # Set current period based on subscription plan
            now = datetime.utcnow()
            if user.get('subscription_period') == 'monthly':
                # For monthly subscriptions, use the subscription start date or current month
                period_start = user.get('subscription_started_at')
                if period_start and period_start <= now:
                    # Calculate the current monthly period based on subscription start
                    months_since_start = (now.year - period_start.year) * 12 + (now.month - period_start.month)
                    current_period_start = datetime(
                        period_start.year + months_since_start // 12,
                        period_start.month + months_since_start % 12,
                        period_start.day,
                        period_start.hour,
                        period_start.minute,
                        period_start.second
                    )
                    # Handle month overflow
                    if current_period_start.month > 12:
                        current_period_start = current_period_start.replace(
                            year=current_period_start.year + 1,
                            month=current_period_start.month - 12
                        )
                    
                    # Calculate period end (add one month)
                    if current_period_start.month == 12:
                        current_period_end = current_period_start.replace(
                            year=current_period_start.year + 1,
                            month=1
                        )
                    else:
                        current_period_end = current_period_start.replace(
                            month=current_period_start.month + 1
                        )
                else:
                    # Use the period dates from user data as fallback
                    current_period_start = user.get('current_period_start', now)
                    current_period_end = user.get('current_period_end', now + timedelta(days=30))
        
        print(f"Period: {current_period_start} to {current_period_end}")
        
        # 3. ANALYZE CONVERSATION SESSIONS IN CURRENT PERIOD
        conversation_sessions = await database.conversation_sessions.find({
            "user_id": user_id,
            "created_at": {
                "$gte": current_period_start,
                "$lt": current_period_end
            }
        }).to_list(length=None)
        
        conversation_duration = sum(s.get('duration_minutes', 0.0) for s in conversation_sessions)
        conversation_count = len(conversation_sessions)
        
        print(f"Conversation Sessions: {conversation_count} sessions, {conversation_duration:.2f} minutes")
        
        # 4. ANALYZE LEARNING PLAN SESSIONS IN CURRENT PERIOD
        learning_plans = await database.learning_plans.find({
            "user_id": user_id
        }).to_list(length=None)
        
        learning_plan_duration = 0.0
        learning_plan_sessions = 0
        learning_sessions_without_duration = 0
        
        for plan in learning_plans:
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            for week in weekly_schedule:
                session_details = week.get('session_details', [])
                for session_detail in session_details:
                    completed_at_str = session_detail.get('completed_at')
                    duration = session_detail.get('duration_minutes', 0.0)
                    
                    if completed_at_str:
                        try:
                            completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
                            if current_period_start <= completed_at < current_period_end:
                                learning_plan_sessions += 1
                                if duration > 0:
                                    learning_plan_duration += duration
                                else:
                                    # Estimate 5 minutes for sessions without duration
                                    learning_plan_duration += 5.0
                                    learning_sessions_without_duration += 1
                        except Exception as e:
                            print(f"⚠️ Could not parse date: {completed_at_str}")
        
        print(f"Learning Plan Sessions: {learning_plan_sessions} sessions, {learning_plan_duration:.2f} minutes")
        if learning_sessions_without_duration > 0:
            print(f"⚠️ {learning_sessions_without_duration} learning sessions had missing duration (estimated 5min each)")
        
        # 5. CALCULATE TOTALS
        total_sessions = conversation_count + learning_plan_sessions
        total_duration = conversation_duration + learning_plan_duration
        
        print(f"\nTOTAL CALCULATED USAGE:")
        print(f"  Sessions: {total_sessions}")
        print(f"  Duration: {total_duration:.2f} minutes")
        
        # 6. COMPARE WITH STORED VALUES
        stored_sessions = user.get('practice_sessions_used', 0)
        stored_minutes = user.get('practice_minutes_used', 0.0)
        
        session_discrepancy = total_sessions - stored_sessions
        duration_discrepancy = total_duration - stored_minutes
        
        print(f"\nCOMPARISON WITH STORED VALUES:")
        print(f"  Stored Sessions: {stored_sessions} (Difference: {session_discrepancy:+d})")
        print(f"  Stored Minutes: {stored_minutes:.2f} (Difference: {duration_discrepancy:+.2f})")
        
        # 7. APPLY FIX IF NEEDED
        needs_fix = abs(session_discrepancy) > 1 or abs(duration_discrepancy) > 5
        
        if needs_fix:
            print(f"\n🔧 APPLYING FIXES:")
            print("-" * 40)
            
            update_data = {
                "practice_sessions_used": total_sessions,
                "practice_minutes_used": total_duration,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "duration_fix_applied": True,
                "duration_fix_date": datetime.utcnow(),
                "duration_fix_details": {
                    "old_sessions": stored_sessions,
                    "old_minutes": stored_minutes,
                    "new_sessions": total_sessions,
                    "new_minutes": total_duration,
                    "conversation_sessions": conversation_count,
                    "learning_plan_sessions": learning_plan_sessions,
                    "conversation_duration": conversation_duration,
                    "learning_plan_duration": learning_plan_duration,
                    "sessions_without_duration": learning_sessions_without_duration
                }
            }
            
            result = await database.users.update_one(user_query, {"$set": update_data})
            
            if result.modified_count > 0:
                print(f"✅ Updated user duration data:")
                print(f"  Sessions: {stored_sessions} → {total_sessions}")
                print(f"  Minutes: {stored_minutes:.2f} → {total_duration:.2f}")
            else:
                print(f"❌ Failed to update user data")
        else:
            print(f"\n✅ NO FIX NEEDED - Data is already accurate")
        
        # 8. CALCULATE REMAINING BASED ON SUBSCRIPTION PLAN
        print(f"\n📊 SUBSCRIPTION LIMITS AND REMAINING:")
        print("-" * 40)
        
        plan_id = user.get('subscription_plan', 'fluency_builder')
        period = user.get('subscription_period', 'monthly')
        
        # Get plan limits
        from subscription_service import SubscriptionService
        plan_details = SubscriptionService.get_plan_details(plan_id)
        
        if plan_details:
            if period == 'annual':
                session_limit = plan_details.annual_sessions
                minute_limit = plan_details.annual_minutes
            else:
                session_limit = plan_details.monthly_sessions
                minute_limit = plan_details.monthly_minutes
            
            sessions_remaining = session_limit - total_sessions if session_limit != -1 else -1
            minutes_remaining = minute_limit - total_duration if minute_limit != -1 else -1
            
            print(f"Plan: {plan_details.name} ({period})")
            print(f"Sessions: {total_sessions}/{session_limit} used, {sessions_remaining} remaining")
            print(f"Minutes: {total_duration:.2f}/{minute_limit} used, {minutes_remaining:.2f} remaining")
            
            # Calculate days until period end
            days_until_reset = (current_period_end - datetime.utcnow()).days
            print(f"Days until reset: {days_until_reset}")
        
        # 9. VALIDATE LEARNING PLAN SESSION DURATION TRACKING
        print(f"\n🔧 VALIDATING LEARNING PLAN DURATION TRACKING:")
        print("-" * 40)
        
        sessions_fixed = 0
        for plan in learning_plans:
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            plan_updated = False
            
            for week in weekly_schedule:
                session_details = week.get('session_details', [])
                for session_detail in session_details:
                    if session_detail.get('duration_minutes', 0.0) == 0:
                        # Add default duration for sessions without duration
                        session_detail['duration_minutes'] = 5.0
                        sessions_fixed += 1
                        plan_updated = True
            
            if plan_updated:
                await database.learning_plans.update_one(
                    {"_id": plan["_id"]},
                    {"$set": {"plan_content.weekly_schedule": weekly_schedule}}
                )
        
        if sessions_fixed > 0:
            print(f"✅ Fixed duration tracking for {sessions_fixed} learning plan sessions")
        else:
            print(f"✅ All learning plan sessions have duration tracking")
        
        print(f"\n🎯 DURATION CALCULATION FIX COMPLETE!")
        print("=" * 80)
        
        return {
            "user_id": user_id,
            "fix_applied": needs_fix,
            "old_sessions": stored_sessions,
            "old_minutes": stored_minutes,
            "new_sessions": total_sessions,
            "new_minutes": total_duration,
            "sessions_remaining": sessions_remaining if 'sessions_remaining' in locals() else None,
            "minutes_remaining": minutes_remaining if 'minutes_remaining' in locals() else None,
            "sessions_fixed": sessions_fixed
        }
        
    except Exception as e:
        print(f"❌ Error during fix: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

async def main():
    """Main function to run the fix"""
    
    # User ID from the provided data
    USER_ID = "688921c268819565ef1ce3dc"
    
    print("🚀 Starting Duration Calculation Fix...")
    
    # Initialize database connection
    from database import init_db
    await init_db()
    
    # Run fix
    result = await fix_user_duration_calculations(USER_ID)
    
    if result:
        print(f"\n✅ Fix completed successfully!")
        if result.get('fix_applied'):
            print(f"📊 Updated sessions: {result['old_sessions']} → {result['new_sessions']}")
            print(f"📊 Updated minutes: {result['old_minutes']:.2f} → {result['new_minutes']:.2f}")
        if result.get('sessions_fixed', 0) > 0:
            print(f"🔧 Fixed {result['sessions_fixed']} learning plan sessions")

if __name__ == "__main__":
    asyncio.run(main())
