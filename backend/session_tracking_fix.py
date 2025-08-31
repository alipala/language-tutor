#!/usr/bin/env python3
"""
SESSION TRACKING AUTOMATIC FIX
==============================
This script fixes the automatic session tracking in learning_routes.py
to ensure sessions are properly saved and subscription usage is tracked.
"""

import os
import sys
from pathlib import Path

def fix_save_session_summary():
    """Fix the save_session_summary function in learning_routes.py"""
    
    learning_routes_path = Path("learning_routes.py")
    if not learning_routes_path.exists():
        print("❌ learning_routes.py not found!")
        return False
    
    print("🔧 FIXING AUTOMATIC SESSION TRACKING")
    print("=" * 60)
    
    # Read the current file
    with open(learning_routes_path, 'r') as f:
        content = f.read()
    
    # Find the save_session_summary function and add enhanced error handling
    enhanced_function = '''@router.post("/session-summary")
async def save_session_summary(
    plan_id: str,
    session_summary: str,
    request: Optional[SessionSummaryRequest] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Save a session summary to the correct week in the learning plan structure
    Also tracks speaking minutes for the learning plan
    """
    try:
        print(f"[SESSION_SUMMARY] 🎯 Starting session save for plan_id: {plan_id}")
        print(f"[SESSION_SUMMARY] 👤 User: {current_user.id} ({getattr(current_user, 'email', 'N/A')})")
        
        # Find the learning plan
        learning_plan = await learning_plans_collection.find_one({"id": plan_id})
        
        if not learning_plan:
            print(f"[SESSION_SUMMARY] ❌ Learning plan not found with id: {plan_id}")
            # Try to find by _id as fallback
            try:
                from bson import ObjectId
                learning_plan = await learning_plans_collection.find_one({"_id": ObjectId(plan_id)})
                if learning_plan:
                    print(f"[SESSION_SUMMARY] ✅ Found learning plan by _id: {plan_id}")
                else:
                    print(f"[SESSION_SUMMARY] ❌ Learning plan not found by _id either: {plan_id}")
            except:
                pass
            
            if not learning_plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Learning plan not found with id: {plan_id}"
                )
        
        print(f"[SESSION_SUMMARY] ✅ Found learning plan: {learning_plan.get('language', 'N/A')} - {learning_plan.get('proficiency_level', 'N/A')}")
        
        # Check if the plan belongs to the current user
        if learning_plan.get("user_id") and learning_plan.get("user_id") != str(current_user.id):
            print(f"[SESSION_SUMMARY] ❌ Permission denied: plan user_id {learning_plan.get('user_id')} != current user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this learning plan"
            )
        
        # Get current progress
        current_completed = learning_plan.get("completed_sessions", 0)
        total_sessions = learning_plan.get("total_sessions", 96)
        sessions_per_week = 2
        
        # Calculate which week and session this belongs to
        session_number = current_completed + 1  # Next session to be completed
        week_index = (session_number - 1) // sessions_per_week  # 0-based week index
        session_in_week = ((session_number - 1) % sessions_per_week) + 1  # 1-based session in week
        
        print(f"[SESSION_SUMMARY] 📊 Session calculation:")
        print(f"[SESSION_SUMMARY]    Current completed: {current_completed}")
        print(f"[SESSION_SUMMARY]    New session number: {session_number}")
        print(f"[SESSION_SUMMARY]    Week index: {week_index}")
        print(f"[SESSION_SUMMARY]    Session in week: {session_in_week}")
        
        # Get the weekly schedule
        weekly_schedule = learning_plan.get("plan_content", {}).get("weekly_schedule", [])
        
        if week_index >= len(weekly_schedule):
            print(f"[SESSION_SUMMARY] ❌ Session {session_number} exceeds available weeks ({len(weekly_schedule)})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session {session_number} exceeds available weeks in the plan"
            )
        
        # Update the specific week with session details
        week = weekly_schedule[week_index]
        
        # Initialize session_details if it doesn't exist
        if 'session_details' not in week:
            week['session_details'] = []
        
        # Track speaking minutes if provided in request
        duration_minutes = 0.0
        if request and request.duration_minutes:
            duration_minutes = request.duration_minutes
            print(f"[SESSION_SUMMARY] 🕐 Duration from request: {duration_minutes} minutes")
        else:
            # Default to 5 minutes if no duration provided (typical session length)
            duration_minutes = 5.0
            print(f"[SESSION_SUMMARY] 🕐 No duration provided, defaulting to {duration_minutes} minutes")
        
        # Create session detail object
        session_detail = {
            "session_number": session_in_week,
            "global_session_number": session_number,
            "summary": session_summary,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "duration_minutes": duration_minutes
        }
        
        # Add request details if available
        if request:
            if request.language:
                session_detail["language"] = request.language
            if request.level:
                session_detail["level"] = request.level
            if request.topic:
                session_detail["topic"] = request.topic
            if request.messages:
                session_detail["message_count"] = len(request.messages)
        
        print(f"[SESSION_SUMMARY] 📝 Session detail created: {session_detail}")
        
        # Add to session_details
        week['session_details'].append(session_detail)
        
        # Update sessions_completed for this week
        week['sessions_completed'] = len(week['session_details'])
        
        # Calculate new progress
        new_completed = session_number
        progress_percentage = (new_completed / total_sessions) * 100 if total_sessions > 0 else 0.0
        
        # Update practice minutes used in learning plan
        current_minutes_used = learning_plan.get("practice_minutes_used", 0.0)
        new_minutes_used = current_minutes_used + duration_minutes
        
        # Update the learning plan
        update_fields = {
            "plan_content.weekly_schedule": weekly_schedule,
            "completed_sessions": new_completed,
            "progress_percentage": progress_percentage,
            "practice_minutes_used": new_minutes_used,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        print(f"[SESSION_SUMMARY] 📊 Learning plan update:")
        print(f"[SESSION_SUMMARY]    Sessions: {current_completed} → {new_completed}")
        print(f"[SESSION_SUMMARY]    Minutes: {current_minutes_used} → {new_minutes_used}")
        print(f"[SESSION_SUMMARY]    Progress: {progress_percentage:.1f}%")
        
        result = await learning_plans_collection.update_one(
            {"_id": learning_plan["_id"]},
            {"$set": update_fields}
        )
        
        if result.modified_count > 0:
            print(f"[SESSION_SUMMARY] ✅ Learning plan updated successfully")
            
            # CRITICAL FIX: Track subscription usage for both sessions AND minutes
            try:
                from subscription_service import SubscriptionService
                from models import SpeakingTimeTrackingRequest
                
                print(f"[SESSION_SUMMARY] 🔄 Tracking subscription usage...")
                
                # FIXED: Use track_speaking_time with session_completed=True
                # This will track BOTH the speaking minutes AND increment the session counter
                speaking_time_request = SpeakingTimeTrackingRequest(
                    user_id=str(current_user.id),
                    speaking_minutes=duration_minutes,
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
            
            print(f"[SESSION_SUMMARY] 🎉 Session summary saved successfully!")
            return {
                "success": True,
                "message": "Session summary saved successfully",
                "session_number": session_number,
                "week": week_index + 1,
                "session_in_week": session_in_week,
                "progress_percentage": progress_percentage,
                "duration_minutes": duration_minutes
            }
        else:
            print(f"[SESSION_SUMMARY] ❌ Failed to update learning plan in database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save session summary"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[SESSION_SUMMARY] ❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error saving session summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving session summary: {str(e)}"
        )'''
    
    # Replace the function in the file
    import re
    
    # Find the existing function
    pattern = r'@router\.post\("/session-summary"\).*?(?=@router\.|$)'
    
    if re.search(pattern, content, re.DOTALL):
        # Replace the existing function
        new_content = re.sub(pattern, enhanced_function, content, flags=re.DOTALL)
        
        # Write the updated content back
        with open(learning_routes_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Enhanced save_session_summary function with better error handling")
        print("✅ Added comprehensive logging for debugging")
        print("✅ Improved subscription tracking integration")
        print("✅ Added fallback for learning plan lookup")
        
        return True
    else:
        print("❌ Could not find save_session_summary function to replace")
        return False

def main():
    """Main function to apply the session tracking fix"""
    print("🔧 APPLYING SESSION TRACKING AUTOMATIC FIX")
    print("=" * 60)
    
    success = fix_save_session_summary()
    
    if success:
        print("\n🎉 SESSION TRACKING FIX APPLIED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ Enhanced error handling and logging")
        print("✅ Improved subscription service integration")
        print("✅ Better debugging capabilities")
        print("✅ Fallback mechanisms for edge cases")
        print("\n📝 Next steps:")
        print("1. Test the session saving functionality")
        print("2. Monitor logs for any remaining issues")
        print("3. Verify subscription tracking works correctly")
    else:
        print("\n❌ FAILED TO APPLY SESSION TRACKING FIX")
        print("Manual intervention may be required")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
