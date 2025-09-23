#!/usr/bin/env python3
"""
COMPREHENSIVE SPEAKING MINUTES CALCULATION FIX

This script addresses the root cause of speaking minutes not being tracked properly
for learning plan sessions, despite multiple previous fix attempts.

PROBLEM IDENTIFIED:
- User has 16 completed learning plan sessions but 0 minutes tracked
- Learning plan sessions increment session count but don't track speaking minutes
- Multiple previous fixes have failed to resolve the core issue

ROOT CAUSE:
The save_session_summary endpoint in learning_routes.py is not properly calling
the subscription service to track speaking minutes, even though the code appears
to be there.

SOLUTION:
1. Fix the learning_routes.py session tracking logic
2. Backfill missing minutes for existing completed sessions
3. Add comprehensive logging and validation
4. Test the fix thoroughly
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
from bson import ObjectId

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from subscription_service import SubscriptionService
from models import SpeakingTimeTrackingRequest

class SpeakingMinutesFix:
    """Comprehensive fix for speaking minutes calculation issues"""
    
    @staticmethod
    async def analyze_user_sessions(user_id: str) -> Dict[str, Any]:
        """Analyze a user's sessions to identify missing minute tracking"""
        print(f"🔍 Analyzing sessions for user {user_id}")
        
        try:
            user_object_id = ObjectId(user_id)
            user_query = {"_id": user_object_id}
        except:
            user_query = {"_id": user_id}
        
        # Get user data
        user = await database.users.find_one(user_query)
        if not user:
            print(f"❌ User {user_id} not found!")
            return {}
        
        # Get learning plans
        learning_plans = await database.learning_plans.find({
            "user_id": user_id
        }).to_list(length=None)
        
        analysis = {
            "user_email": user.get("email", "N/A"),
            "stored_sessions": user.get("practice_sessions_used", 0),
            "stored_minutes": user.get("practice_minutes_used", 0.0),
            "learning_plans": [],
            "total_completed_sessions": 0,
            "total_expected_minutes": 0.0,
            "missing_minutes": 0.0
        }
        
        for plan in learning_plans:
            plan_analysis = {
                "id": plan.get("id"),
                "language": plan.get("language"),
                "level": plan.get("proficiency_level"),
                "completed_sessions": plan.get("completed_sessions", 0),
                "sessions_with_duration": 0,
                "total_duration": 0.0,
                "expected_duration": 0.0
            }
            
            # Check weekly schedule for session details
            weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
            for week in weekly_schedule:
                session_details = week.get("session_details", [])
                for session_detail in session_details:
                    duration = session_detail.get("duration_minutes", 0.0)
                    if duration > 0:
                        plan_analysis["sessions_with_duration"] += 1
                        plan_analysis["total_duration"] += duration
            
            # Calculate expected duration (5 minutes per completed session)
            plan_analysis["expected_duration"] = plan_analysis["completed_sessions"] * 5.0
            
            analysis["learning_plans"].append(plan_analysis)
            analysis["total_completed_sessions"] += plan_analysis["completed_sessions"]
            analysis["total_expected_minutes"] += plan_analysis["expected_duration"]
        
        # Calculate missing minutes
        analysis["missing_minutes"] = analysis["total_expected_minutes"] - analysis["stored_minutes"]
        
        return analysis
    
    @staticmethod
    async def backfill_missing_minutes(user_id: str, dry_run: bool = True) -> Dict[str, Any]:
        """Backfill missing speaking minutes for completed learning plan sessions"""
        print(f"🔧 {'DRY RUN: ' if dry_run else ''}Backfilling missing minutes for user {user_id}")
        
        analysis = await SpeakingMinutesFix.analyze_user_sessions(user_id)
        
        if analysis["missing_minutes"] <= 0:
            print("✅ No missing minutes detected - user data is correct")
            return {"success": True, "minutes_added": 0, "message": "No backfill needed"}
        
        print(f"📊 Analysis Results:")
        print(f"   User: {analysis['user_email']}")
        print(f"   Completed Sessions: {analysis['total_completed_sessions']}")
        print(f"   Expected Minutes: {analysis['total_expected_minutes']:.2f}")
        print(f"   Stored Minutes: {analysis['stored_minutes']:.2f}")
        print(f"   Missing Minutes: {analysis['missing_minutes']:.2f}")
        
        if dry_run:
            print("🔍 DRY RUN - Would add the missing minutes but not actually updating database")
            return {
                "success": True,
                "dry_run": True,
                "minutes_to_add": analysis["missing_minutes"],
                "analysis": analysis
            }
        
        # Actually update the user's minutes
        try:
            user_object_id = ObjectId(user_id)
            user_query = {"_id": user_object_id}
        except:
            user_query = {"_id": user_id}
        
        new_minutes = analysis["stored_minutes"] + analysis["missing_minutes"]
        
        result = await database.users.update_one(
            user_query,
            {
                "$set": {
                    "practice_minutes_used": new_minutes,
                    "backfill_date": datetime.utcnow().isoformat(),
                    "backfill_reason": "comprehensive_speaking_minutes_fix",
                    "backfill_minutes_added": analysis["missing_minutes"]
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully backfilled {analysis['missing_minutes']:.2f} minutes")
            print(f"   Old minutes: {analysis['stored_minutes']:.2f}")
            print(f"   New minutes: {new_minutes:.2f}")
            return {
                "success": True,
                "minutes_added": analysis["missing_minutes"],
                "old_minutes": analysis["stored_minutes"],
                "new_minutes": new_minutes
            }
        else:
            print("❌ Failed to update user minutes")
            return {"success": False, "error": "Database update failed"}
    
    @staticmethod
    async def fix_learning_routes_tracking():
        """Generate the corrected learning_routes.py code"""
        print("🔧 Generating corrected learning_routes.py tracking code...")
        
        corrected_code = '''
# CORRECTED SESSION TRACKING CODE FOR learning_routes.py
# This should replace the existing tracking logic in save_session_summary()

# CRITICAL FIX: Track subscription usage for both sessions AND minutes
try:
    from subscription_service import SubscriptionService
    from models import SpeakingTimeTrackingRequest
    
    print(f"[SESSION_SUMMARY] 🔄 Tracking subscription usage...")
    print(f"[SESSION_SUMMARY]    Duration: {duration_minutes} minutes")
    print(f"[SESSION_SUMMARY]    Session completed: True")
    
    # FIXED: Use track_speaking_time with session_completed=True
    # This will track BOTH the speaking minutes AND increment the session counter
    speaking_time_request = SpeakingTimeTrackingRequest(
        user_id=str(current_user.id),
        speaking_minutes=float(duration_minutes),  # Ensure it's a float
        session_completed=True  # This will increment both minutes AND session count
    )
    
    tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)
    if tracking_success:
        print(f"[SESSION_SUMMARY] ✅ Subscription tracking successful:")
        print(f"[SESSION_SUMMARY]    User: {getattr(current_user, 'email', current_user.id)}")
        print(f"[SESSION_SUMMARY]    Minutes tracked: {duration_minutes}")
        print(f"[SESSION_SUMMARY]    Session completed: True")
        print(f"[SESSION_SUMMARY]    Both counters updated")
    else:
        print(f"[SESSION_SUMMARY] ⚠️ Subscription tracking failed - user may have exceeded limits")
        # Don't fail the session save, but log the issue
        
except Exception as usage_error:
    print(f"[SESSION_SUMMARY] ⚠️ Warning: Failed to track subscription usage: {str(usage_error)}")
    import traceback
    traceback.print_exc()
    # Don't fail the entire operation if usage tracking fails
    # The session summary is still saved successfully
'''
        
        print("✅ Corrected code generated")
        return corrected_code
    
    @staticmethod
    async def test_tracking_functionality(user_id: str) -> Dict[str, Any]:
        """Test the speaking time tracking functionality"""
        print(f"🧪 Testing speaking time tracking for user {user_id}")
        
        # Get initial state
        try:
            user_object_id = ObjectId(user_id)
            user_query = {"_id": user_object_id}
        except:
            user_query = {"_id": user_id}
        
        user_before = await database.users.find_one(user_query)
        if not user_before:
            return {"success": False, "error": "User not found"}
        
        initial_sessions = user_before.get("practice_sessions_used", 0)
        initial_minutes = user_before.get("practice_minutes_used", 0.0)
        
        print(f"📊 Initial state:")
        print(f"   Sessions: {initial_sessions}")
        print(f"   Minutes: {initial_minutes:.2f}")
        
        # Test tracking 5 minutes with session completed
        test_minutes = 5.0
        tracking_request = SpeakingTimeTrackingRequest(
            user_id=user_id,
            speaking_minutes=test_minutes,
            session_completed=True
        )
        
        print(f"🔄 Testing tracking of {test_minutes} minutes with session_completed=True")
        
        success = await SubscriptionService.track_speaking_time(tracking_request)
        
        if not success:
            return {"success": False, "error": "Tracking function returned False"}
        
        # Check final state
        user_after = await database.users.find_one(user_query)
        final_sessions = user_after.get("practice_sessions_used", 0)
        final_minutes = user_after.get("practice_minutes_used", 0.0)
        
        print(f"📊 Final state:")
        print(f"   Sessions: {final_sessions} (expected: {initial_sessions + 1})")
        print(f"   Minutes: {final_minutes:.2f} (expected: {initial_minutes + test_minutes:.2f})")
        
        # Verify results
        sessions_correct = final_sessions == initial_sessions + 1
        minutes_correct = abs(final_minutes - (initial_minutes + test_minutes)) < 0.01
        
        if sessions_correct and minutes_correct:
            print("✅ Test PASSED - Both sessions and minutes tracked correctly")
            return {
                "success": True,
                "sessions_tracked": True,
                "minutes_tracked": True,
                "initial_sessions": initial_sessions,
                "final_sessions": final_sessions,
                "initial_minutes": initial_minutes,
                "final_minutes": final_minutes
            }
        else:
            print("❌ Test FAILED")
            if not sessions_correct:
                print(f"   Sessions not tracked correctly: {final_sessions} != {initial_sessions + 1}")
            if not minutes_correct:
                print(f"   Minutes not tracked correctly: {final_minutes:.2f} != {initial_minutes + test_minutes:.2f}")
            
            return {
                "success": False,
                "sessions_tracked": sessions_correct,
                "minutes_tracked": minutes_correct,
                "initial_sessions": initial_sessions,
                "final_sessions": final_sessions,
                "initial_minutes": initial_minutes,
                "final_minutes": final_minutes
            }

async def main():
    """Main function to run the comprehensive fix"""
    
    # User ID from the investigation
    USER_ID = "688921c268819565ef1ce3dc"
    
    print("🚀 COMPREHENSIVE SPEAKING MINUTES FIX")
    print("=" * 60)
    
    # Initialize database connection
    from database import init_db
    await init_db()
    
    # Step 1: Analyze the current state
    print("\n📊 STEP 1: ANALYZING CURRENT STATE")
    print("-" * 40)
    analysis = await SpeakingMinutesFix.analyze_user_sessions(USER_ID)
    
    if not analysis:
        print("❌ Failed to analyze user sessions")
        return
    
    print(f"Analysis complete:")
    print(f"  User: {analysis['user_email']}")
    print(f"  Completed Sessions: {analysis['total_completed_sessions']}")
    print(f"  Expected Minutes: {analysis['total_expected_minutes']:.2f}")
    print(f"  Stored Minutes: {analysis['stored_minutes']:.2f}")
    print(f"  Missing Minutes: {analysis['missing_minutes']:.2f}")
    
    # Step 2: Test current tracking functionality
    print("\n🧪 STEP 2: TESTING CURRENT TRACKING FUNCTIONALITY")
    print("-" * 40)
    test_result = await SpeakingMinutesFix.test_tracking_functionality(USER_ID)
    
    if test_result["success"]:
        print("✅ Tracking functionality is working correctly")
        print("   The issue may be in the learning_routes.py implementation")
    else:
        print("❌ Tracking functionality has issues")
        print(f"   Sessions tracked: {test_result.get('sessions_tracked', False)}")
        print(f"   Minutes tracked: {test_result.get('minutes_tracked', False)}")
    
    # Step 3: Generate corrected code
    print("\n🔧 STEP 3: GENERATING CORRECTED CODE")
    print("-" * 40)
    corrected_code = await SpeakingMinutesFix.fix_learning_routes_tracking()
    
    # Step 4: Backfill missing minutes (dry run first)
    print("\n💾 STEP 4: BACKFILL MISSING MINUTES (DRY RUN)")
    print("-" * 40)
    dry_run_result = await SpeakingMinutesFix.backfill_missing_minutes(USER_ID, dry_run=True)
    
    if dry_run_result["success"] and dry_run_result.get("minutes_to_add", 0) > 0:
        print(f"\n❓ Would you like to apply the backfill of {dry_run_result['minutes_to_add']:.2f} minutes?")
        print("   This will update the user's practice_minutes_used to reflect completed sessions")
        
        # For now, we'll just show what would be done
        print("   To apply the backfill, run this script with apply_backfill=True")
    
    print("\n🎯 COMPREHENSIVE FIX ANALYSIS COMPLETE")
    print("=" * 60)
    
    # Summary of findings
    print("\n📋 SUMMARY OF FINDINGS:")
    print(f"1. User has {analysis['total_completed_sessions']} completed learning plan sessions")
    print(f"2. Expected minutes: {analysis['total_expected_minutes']:.2f}")
    print(f"3. Stored minutes: {analysis['stored_minutes']:.2f}")
    print(f"4. Missing minutes: {analysis['missing_minutes']:.2f}")
    print(f"5. Tracking functionality test: {'✅ PASSED' if test_result['success'] else '❌ FAILED'}")
    
    print("\n🔧 RECOMMENDED ACTIONS:")
    print("1. Fix the learning_routes.py session tracking logic")
    print("2. Backfill missing minutes for existing users")
    print("3. Test the fix with new sessions")
    print("4. Monitor future session tracking")

if __name__ == "__main__":
    asyncio.run(main())
