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

async def test_user_duration_tracking(user_id: str):
    """
    Test the current duration tracking functionality for a specific user
    """
    print("=" * 80)
    print(f"🧪 TESTING CURRENT DURATION TRACKING")
    print(f"User ID: {user_id}")
    print(f"Test Date: {datetime.utcnow()}")
    print("=" * 80)
    
    try:
        # Convert user ID to proper format
        try:
            user_object_id = ObjectId(user_id)
            user_query = {"_id": user_object_id}
        except:
            user_query = {"_id": user_id}
        
        # 1. GET CURRENT USER STATE
        print("\n📊 CURRENT USER STATE:")
        print("-" * 40)
        
        user = await database.users.find_one(user_query)
        if not user:
            print(f"❌ User {user_id} not found!")
            return
        
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Subscription Plan: {user.get('subscription_plan', 'N/A')}")
        print(f"Period Start: {user.get('current_period_start', 'N/A')}")
        print(f"Period End: {user.get('current_period_end', 'N/A')}")
        print(f"Sessions Used: {user.get('practice_sessions_used', 0)}")
        print(f"Minutes Used: {user.get('practice_minutes_used', 0.0)}")
        print(f"Assessments Used: {user.get('assessments_used', 0)}")
        
        # 2. GET SUBSCRIPTION STATUS
        print("\n🎯 SUBSCRIPTION STATUS:")
        print("-" * 40)
        
        status = await SubscriptionService.get_user_subscription_status(user_id)
        if status.limits:
            print(f"Plan: {status.limits.plan}")
            print(f"Sessions: {status.limits.sessions_used}/{status.limits.sessions_limit} (Remaining: {status.limits.sessions_remaining})")
            print(f"Minutes: {status.limits.minutes_used:.2f}/{status.limits.minutes_limit} (Remaining: {status.limits.minutes_remaining:.2f})")
            print(f"Assessments: {status.limits.assessments_used}/{status.limits.assessments_limit} (Remaining: {status.limits.assessments_remaining})")
            print(f"Period: {status.limits.period_start} to {status.limits.period_end}")
        
        # 3. SIMULATE SPEAKING TIME TRACKING (like learning plan sessions do)
        print("\n🧪 SIMULATING SPEAKING TIME TRACKING:")
        print("-" * 40)
        
        from models import SpeakingTimeTrackingRequest
        
        # Test 1: Track a completed session (should increment both minutes and sessions)
        print("Test 1: Tracking completed session (5 minutes)")
        test_request = SpeakingTimeTrackingRequest(
            user_id=user_id,
            speaking_minutes=5.0,
            session_completed=True
        )
        
        success = await SubscriptionService.track_speaking_time(test_request)
        print(f"Tracking Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Check updated status
        updated_status = await SubscriptionService.get_user_subscription_status(user_id)
        if updated_status.limits:
            print(f"Updated Sessions: {updated_status.limits.sessions_used} (Change: +{updated_status.limits.sessions_used - status.limits.sessions_used})")
            print(f"Updated Minutes: {updated_status.limits.minutes_used:.2f} (Change: +{updated_status.limits.minutes_used - status.limits.minutes_used:.2f})")
        
        # 4. TEST FEATURE ACCESS
        print("\n🔒 TESTING FEATURE ACCESS:")
        print("-" * 40)
        
        can_practice, practice_message = await SubscriptionService.can_access_feature(user_id, "practice_session")
        print(f"Can Practice: {'✅ Yes' if can_practice else '❌ No'} - {practice_message}")
        
        can_assess, assess_message = await SubscriptionService.can_access_feature(user_id, "assessment")
        print(f"Can Assess: {'✅ Yes' if can_assess else '❌ No'} - {assess_message}")
        
        can_start, start_message = await SubscriptionService.can_start_session(user_id)
        print(f"Can Start Session: {'✅ Yes' if can_start else '❌ No'} - {start_message}")
        
        # 5. ANALYZE CURRENT PERIOD DATA
        print("\n📅 CURRENT PERIOD ANALYSIS:")
        print("-" * 40)
        
        if updated_status.limits and updated_status.limits.period_start and updated_status.limits.period_end:
            period_start = updated_status.limits.period_start
            period_end = updated_status.limits.period_end
            
            # Count conversation sessions in current period
            conversation_sessions = await database.conversation_sessions.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": period_start,
                    "$lt": period_end
                }
            }).to_list(length=None)
            
            conv_duration = sum(s.get('duration_minutes', 0.0) for s in conversation_sessions)
            print(f"Conversation Sessions: {len(conversation_sessions)} sessions, {conv_duration:.2f} minutes")
            
            # Count learning plan sessions in current period
            learning_plans = await database.learning_plans.find({
                "user_id": user_id
            }).to_list(length=None)
            
            learning_sessions = 0
            learning_duration = 0.0
            
            for plan in learning_plans:
                weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
                for week in weekly_schedule:
                    for session_detail in week.get('session_details', []):
                        completed_at_str = session_detail.get('completed_at')
                        if completed_at_str:
                            try:
                                completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                if period_start <= completed_at < period_end:
                                    learning_sessions += 1
                                    learning_duration += session_detail.get('duration_minutes', 5.0)
                            except:
                                continue
            
            print(f"Learning Plan Sessions: {learning_sessions} sessions, {learning_duration:.2f} minutes")
            
            # Calculate totals and compare with subscription tracking
            actual_total_sessions = len(conversation_sessions) + learning_sessions
            actual_total_duration = conv_duration + learning_duration
            
            print(f"\nACTUAL PERIOD TOTALS:")
            print(f"  Total Sessions: {actual_total_sessions}")
            print(f"  Total Duration: {actual_total_duration:.2f} minutes")
            
            print(f"\nSUBSCRIPTION TRACKING:")
            print(f"  Tracked Sessions: {updated_status.limits.sessions_used}")
            print(f"  Tracked Minutes: {updated_status.limits.minutes_used:.2f}")
            
            # Check for discrepancies
            session_diff = actual_total_sessions - updated_status.limits.sessions_used
            duration_diff = actual_total_duration - updated_status.limits.minutes_used
            
            print(f"\nDISCREPANCY CHECK:")
            print(f"  Session Difference: {session_diff:+d} ({'✅ OK' if abs(session_diff) <= 1 else '❌ ISSUE'})")
            print(f"  Duration Difference: {duration_diff:+.2f} minutes ({'✅ OK' if abs(duration_diff) <= 5 else '❌ ISSUE'})")
        
        # 6. CALCULATE REMAINING TIME UNTIL RESET
        print("\n⏰ TIME UNTIL RESET:")
        print("-" * 40)
        
        if updated_status.limits and updated_status.limits.period_end:
            now = datetime.utcnow()
            time_until_reset = updated_status.limits.period_end - now
            days_remaining = time_until_reset.days
            hours_remaining = time_until_reset.seconds // 3600
            
            print(f"Period End: {updated_status.limits.period_end}")
            print(f"Time Remaining: {days_remaining} days, {hours_remaining} hours")
            print(f"Sessions will reset to 0")
            print(f"Minutes will reset to 0.0")
        
        print(f"\n🎯 DURATION TRACKING TEST COMPLETE!")
        print("=" * 80)
        
        return {
            "user_id": user_id,
            "tracking_works": success,
            "current_sessions": updated_status.limits.sessions_used if updated_status.limits else 0,
            "current_minutes": updated_status.limits.minutes_used if updated_status.limits else 0.0,
            "can_practice": can_practice,
            "discrepancy_found": abs(session_diff) > 1 or abs(duration_diff) > 5 if 'session_diff' in locals() else False
        }
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

async def main():
    """Main function to run the test"""
    
    # User ID from the provided data
    USER_ID = "688921c268819565ef1ce3dc"
    
    print("🚀 Starting Duration Tracking Test...")
    
    # Initialize database connection
    from database import init_db
    await init_db()
    
    # Run test
    result = await test_user_duration_tracking(USER_ID)
    
    if result:
        print(f"\n✅ Test completed successfully!")
        print(f"🔧 Tracking functionality: {'Working' if result.get('tracking_works') else 'Needs fixing'}")
        print(f"📊 Current usage: {result.get('current_sessions')} sessions, {result.get('current_minutes', 0):.2f} minutes")
        if result.get('discrepancy_found'):
            print(f"⚠️ Discrepancy detected - data inconsistency found")

if __name__ == "__main__":
    asyncio.run(main())
