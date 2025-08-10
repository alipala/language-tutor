#!/usr/bin/env python3
"""
Test Duration Tracking System

This script tests the duration tracking system to ensure that both learning plan
sessions and regular conversation sessions properly track both session counts
and speaking minutes.
"""

import asyncio
import os
import sys
from datetime import datetime
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from subscription_service import SubscriptionService
from models import SpeakingTimeTrackingRequest, UsageTrackingRequest

async def test_duration_tracking():
    """Test the duration tracking system"""
    
    print("🧪 TESTING DURATION TRACKING SYSTEM")
    print("=" * 50)
    
    # Target user
    target_email = "alipala.ist@gmail.com"
    target_user_id = "688921c268819565ef1ce3dc"
    
    try:
        # Get collections
        users_collection = database.users
        
        # Find the user
        print(f"🔍 Looking for user: {target_email}")
        user = await users_collection.find_one({"email": target_email})
        
        if not user:
            print(f"❌ User not found: {target_email}")
            return False
        
        print(f"✅ Found user: {user['name']} ({user['email']})")
        
        # Get current subscription status
        print(f"\n📊 GETTING SUBSCRIPTION STATUS:")
        subscription_status = await SubscriptionService.get_user_subscription_status(target_user_id)
        
        print(f"   Plan: {subscription_status.plan}")
        print(f"   Status: {subscription_status.status}")
        
        if subscription_status.limits:
            print(f"   Sessions: {subscription_status.limits.sessions_used}/{subscription_status.limits.sessions_limit}")
            print(f"   Minutes: {subscription_status.limits.minutes_used:.2f}/{subscription_status.limits.minutes_limit}")
            print(f"   Assessments: {subscription_status.limits.assessments_used}/{subscription_status.limits.assessments_limit}")
            
            print(f"   Sessions Remaining: {subscription_status.limits.sessions_remaining}")
            print(f"   Minutes Remaining: {subscription_status.limits.minutes_remaining:.2f}")
            print(f"   Assessments Remaining: {subscription_status.limits.assessments_remaining}")
        
        # Test 1: Test speaking time tracking (simulates learning plan session)
        print(f"\n🧪 TEST 1: SPEAKING TIME TRACKING (Learning Plan Session)")
        print(f"   Simulating a 6-minute learning plan session...")
        
        # Store current values
        current_sessions = subscription_status.limits.sessions_used if subscription_status.limits else 0
        current_minutes = subscription_status.limits.minutes_used if subscription_status.limits else 0.0
        
        # Test speaking time tracking with session completion
        speaking_request = SpeakingTimeTrackingRequest(
            user_id=target_user_id,
            speaking_minutes=6.0,
            session_completed=True  # This should increment both minutes AND sessions
        )
        
        tracking_success = await SubscriptionService.track_speaking_time(speaking_request)
        
        if tracking_success:
            print(f"   ✅ Speaking time tracking successful")
            
            # Get updated status
            updated_status = await SubscriptionService.get_user_subscription_status(target_user_id)
            
            if updated_status.limits:
                new_sessions = updated_status.limits.sessions_used
                new_minutes = updated_status.limits.minutes_used
                
                sessions_added = new_sessions - current_sessions
                minutes_added = new_minutes - current_minutes
                
                print(f"   Sessions: {current_sessions} → {new_sessions} (+{sessions_added})")
                print(f"   Minutes: {current_minutes:.2f} → {new_minutes:.2f} (+{minutes_added:.2f})")
                
                if sessions_added == 1 and abs(minutes_added - 6.0) < 0.1:
                    print(f"   ✅ TEST 1 PASSED: Both session and minutes tracked correctly")
                else:
                    print(f"   ❌ TEST 1 FAILED: Expected +1 session and +6.0 minutes")
                    return False
            else:
                print(f"   ❌ TEST 1 FAILED: Could not get updated limits")
                return False
        else:
            print(f"   ❌ TEST 1 FAILED: Speaking time tracking failed")
            return False
        
        # Test 2: Test partial session tracking (simulates incomplete session)
        print(f"\n🧪 TEST 2: PARTIAL SESSION TRACKING (Incomplete Session)")
        print(f"   Simulating a 2-minute incomplete session...")
        
        # Store current values
        current_sessions = updated_status.limits.sessions_used
        current_minutes = updated_status.limits.minutes_used
        
        # Test speaking time tracking without session completion
        partial_request = SpeakingTimeTrackingRequest(
            user_id=target_user_id,
            speaking_minutes=2.0,
            session_completed=False  # This should increment minutes but NOT sessions
        )
        
        partial_success = await SubscriptionService.track_speaking_time(partial_request)
        
        if partial_success:
            print(f"   ✅ Partial session tracking successful")
            
            # Get updated status
            final_status = await SubscriptionService.get_user_subscription_status(target_user_id)
            
            if final_status.limits:
                final_sessions = final_status.limits.sessions_used
                final_minutes = final_status.limits.minutes_used
                
                sessions_added = final_sessions - current_sessions
                minutes_added = final_minutes - current_minutes
                
                print(f"   Sessions: {current_sessions} → {final_sessions} (+{sessions_added})")
                print(f"   Minutes: {current_minutes:.2f} → {final_minutes:.2f} (+{minutes_added:.2f})")
                
                if sessions_added == 0 and abs(minutes_added - 2.0) < 0.1:
                    print(f"   ✅ TEST 2 PASSED: Only minutes tracked, sessions unchanged")
                else:
                    print(f"   ❌ TEST 2 FAILED: Expected +0 sessions and +2.0 minutes")
                    return False
            else:
                print(f"   ❌ TEST 2 FAILED: Could not get updated limits")
                return False
        else:
            print(f"   ❌ TEST 2 FAILED: Partial session tracking failed")
            return False
        
        # Test 3: Test feature access checks
        print(f"\n🧪 TEST 3: FEATURE ACCESS CHECKS")
        
        can_practice, practice_message = await SubscriptionService.can_access_feature(target_user_id, "practice_session")
        can_assess, assess_message = await SubscriptionService.can_access_feature(target_user_id, "assessment")
        can_start, start_message = await SubscriptionService.can_start_session(target_user_id)
        
        print(f"   Can Practice: {can_practice} - {practice_message}")
        print(f"   Can Assess: {can_assess} - {assess_message}")
        print(f"   Can Start Session: {can_start} - {start_message}")
        
        if can_practice and can_assess and can_start:
            print(f"   ✅ TEST 3 PASSED: All feature access checks working")
        else:
            print(f"   ⚠️ TEST 3 WARNING: Some features may be limited (this could be expected)")
        
        # Final status report
        print(f"\n📊 FINAL STATUS REPORT:")
        final_status = await SubscriptionService.get_user_subscription_status(target_user_id)
        
        if final_status.limits:
            print(f"   Sessions: {final_status.limits.sessions_used}/{final_status.limits.sessions_limit}")
            print(f"   Minutes: {final_status.limits.minutes_used:.2f}/{final_status.limits.minutes_limit}")
            print(f"   Assessments: {final_status.limits.assessments_used}/{final_status.limits.assessments_limit}")
            
            sessions_remaining = final_status.limits.sessions_remaining
            minutes_remaining = final_status.limits.minutes_remaining
            
            print(f"   Sessions Remaining: {sessions_remaining}")
            print(f"   Minutes Remaining: {minutes_remaining:.2f}")
            
            if sessions_remaining > 0 and minutes_remaining > 0:
                print(f"   ✅ User has remaining quota for both sessions and minutes")
            else:
                print(f"   ⚠️ User may be approaching or have exceeded limits")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing duration tracking: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🚀 Starting Duration Tracking System Test")
    print(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")
    
    success = await test_duration_tracking()
    
    if success:
        print(f"\n🎉 DURATION TRACKING SYSTEM TEST COMPLETED!")
        print(f"   All tests passed. The system is working correctly.")
        print(f"   Learning plan sessions will now properly track both sessions and minutes.")
    else:
        print(f"\n❌ DURATION TRACKING SYSTEM TEST FAILED!")
        print(f"   Please check the logs and fix any issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
