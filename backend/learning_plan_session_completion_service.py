#!/usr/bin/env python3
"""
LEARNING PLAN SESSION COMPLETION SERVICE
Bulletproof service to ensure proper session completion tracking in learning plans

INTEGRATION: This service should be used by learning_routes.py session-summary endpoint
"""

from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from database import database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningPlanSessionCompletionService:
    """Service to ensure proper session completion tracking in learning plans"""
    
    @classmethod
    async def complete_session(
        cls,
        user_id: str,
        learning_plan_id: str,
        session_summary: str,
        duration_minutes: float = 5.0,
        selected_duration: int = 5,  # 🆕 NEW: User's selected session duration (3 or 5)
        language: Optional[str] = None,
        level: Optional[str] = None,
        topic: Optional[str] = None,
        message_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Mark a session as completed with proper tracking in learning plan session_details
        This ensures session completion data is stored in the correct place
        """
        try:
            logger.info(f"[SESSION_COMPLETION] Starting session completion for user {user_id}, plan {learning_plan_id}")
            
            # Get learning plan
            plan = await database["learning_plans"].find_one({"id": learning_plan_id, "user_id": user_id})
            if not plan:
                logger.error(f"[SESSION_COMPLETION] Learning plan not found: {learning_plan_id} for user {user_id}")
                return {"success": False, "error": "Learning plan not found"}
            
            # Get current progress
            current_completed = plan.get("completed_sessions", 0)
            total_sessions = plan.get("total_sessions", 24)
            sessions_per_week = 2
            
            # Calculate which week and session this belongs to
            session_number = current_completed + 1  # Next session to be completed
            week_index = (session_number - 1) // sessions_per_week  # 0-based week index
            session_in_week = ((session_number - 1) % sessions_per_week) + 1  # 1-based session in week
            
            logger.info(f"[SESSION_COMPLETION] Session calculation: session {session_number}, week {week_index + 1}, session in week {session_in_week}")
            
            # Get weekly schedule
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            
            if week_index >= len(weekly_schedule):
                logger.error(f"[SESSION_COMPLETION] Session {session_number} exceeds available weeks ({len(weekly_schedule)})")
                return {"success": False, "error": f"Session {session_number} exceeds available weeks in the plan"}
            
            week = weekly_schedule[week_index]
            
            # Initialize session_details if it doesn't exist
            if 'session_details' not in week:
                week['session_details'] = []
                logger.info(f"[SESSION_COMPLETION] Initialized session_details for week {week_index + 1}")
            
            # 🆕 UPDATED: Use selected_duration as completion threshold
            completion_threshold = selected_duration  # User's selected duration (3 or 5)

            if duration_minutes >= completion_threshold:
                enforced_duration = float(completion_threshold)  # Cap at selected (3 or 5)
                session_status = "completed"
                logger.info(f"[SESSION_COMPLETION] Complete session: {duration_minutes} → {enforced_duration} minutes (threshold: {completion_threshold})")
            else:
                enforced_duration = float(max(1, int(round(duration_minutes))))
                session_status = "partial"
                logger.info(f"[SESSION_COMPLETION] Partial session: {duration_minutes} → {enforced_duration} minutes (threshold: {completion_threshold})")
            
            # Create completion timestamp
            completion_time = datetime.utcnow().isoformat()
            
            # Create session detail object
            session_detail = {
                "session_number": session_in_week,
                "global_session_number": session_number,
                "focus": week.get("focus", "Language learning session"),
                "completed_at": completion_time,
                "duration_minutes": enforced_duration,
                "selected_duration": selected_duration,  # 🆕 Store selected duration
                "session_summary": session_summary,
                "status": session_status
            }
            
            # Add optional fields if provided
            if language:
                session_detail["language"] = language
            if level:
                session_detail["level"] = level
            if topic:
                session_detail["topic"] = topic
            if message_count:
                session_detail["message_count"] = message_count
            
            logger.info(f"[SESSION_COMPLETION] Created session detail: {session_detail}")
            
            # Find existing session detail or add new one
            existing_session_index = None
            for i, existing_session in enumerate(week['session_details']):
                if existing_session.get('session_number') == session_in_week:
                    existing_session_index = i
                    break
            
            if existing_session_index is not None:
                # Update existing session
                week['session_details'][existing_session_index] = session_detail
                logger.info(f"[SESSION_COMPLETION] Updated existing session detail at index {existing_session_index}")
            else:
                # Add new session detail
                week['session_details'].append(session_detail)
                logger.info(f"[SESSION_COMPLETION] Added new session detail")
            
            # Update sessions_completed for the week
            completed_in_week = sum(1 for s in week['session_details'] if s.get('status') == 'completed')
            week['sessions_completed'] = completed_in_week
            
            # Update total completed_sessions for the plan
            total_completed = sum(w.get('sessions_completed', 0) for w in weekly_schedule)
            progress_percentage = (total_completed / total_sessions) * 100 if total_sessions > 0 else 0.0

            # Update practice minutes used in learning plan
            current_minutes_used = plan.get("practice_minutes_used", 0.0)
            new_minutes_used = current_minutes_used + enforced_duration

            logger.info(f"[SESSION_COMPLETION] Progress update: {current_completed} → {total_completed} sessions, {progress_percentage:.1f}%")
            logger.info(f"[SESSION_COMPLETION] Minutes update: {current_minutes_used} → {new_minutes_used}")

            # CRITICAL: Check if this is the LAST session - trigger final assessment requirement
            is_last_session = total_completed >= total_sessions
            update_fields = {
                "plan_content.weekly_schedule": weekly_schedule,
                "completed_sessions": total_completed,
                "progress_percentage": progress_percentage,
                "practice_minutes_used": new_minutes_used,
                "updated_at": datetime.utcnow().isoformat()
            }

            if is_last_session:
                logger.info(f"[SESSION_COMPLETION] 🎉 LAST SESSION COMPLETED! Triggering final assessment requirement")

                # Get current status and final_assessment
                current_status = plan.get("status", "in_progress")
                final_assessment = plan.get("final_assessment", {})

                # Only update if not already completed or awaiting assessment
                if current_status not in ["completed", "awaiting_final_assessment"]:
                    update_fields["status"] = "awaiting_final_assessment"
                    update_fields["all_sessions_completed_at"] = datetime.utcnow().isoformat()

                    # Ensure final_assessment structure exists
                    if not final_assessment.get("required"):
                        # Calculate assessment duration based on level
                        level = plan.get("proficiency_level", "A1").upper()
                        duration_map = {'A1': 2, 'A2': 3, 'B1': 4, 'B2': 5, 'C1': 5, 'C2': 5}
                        assessment_duration = duration_map.get(level, 3)

                        update_fields["final_assessment"] = {
                            "required": True,
                            "completed": False,
                            "attempts": final_assessment.get("attempts", []),
                            "minimum_duration_minutes": assessment_duration,
                            "passed": False,
                            "last_attempt_date": final_assessment.get("last_attempt_date")
                        }

                    logger.info(f"[SESSION_COMPLETION] Status changed: in_progress → awaiting_final_assessment")

            # Update the learning plan
            result = await database["learning_plans"].update_one(
                {"_id": plan["_id"]},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                logger.info(f"[SESSION_COMPLETION] ✅ Successfully updated learning plan")

                response = {
                    "success": True,
                    "session_number": session_number,
                    "week": week_index + 1,
                    "session_in_week": session_in_week,
                    "completed_at": completion_time,
                    "duration_minutes": enforced_duration,
                    "total_completed": total_completed,
                    "progress_percentage": progress_percentage,
                    "status": session_status,
                    "is_last_session": is_last_session,
                    "plan_status": update_fields.get("status", plan.get("status", "in_progress"))
                }

                # If last session, include assessment information
                if is_last_session:
                    response["final_assessment_required"] = True
                    response["assessment_info"] = {
                        "minimum_duration_minutes": update_fields.get("final_assessment", {}).get("minimum_duration_minutes", 3),
                        "can_postpone": True,
                        "message": "Congratulations on completing all sessions! Please take your final assessment to complete this learning plan."
                    }

                return response
            else:
                logger.error(f"[SESSION_COMPLETION] ❌ Failed to update learning plan")
                return {"success": False, "error": "Failed to update learning plan"}
                
        except Exception as e:
            logger.error(f"[SESSION_COMPLETION] ❌ Error completing session: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def get_session_completion_status(cls, user_id: str, learning_plan_id: str) -> Dict[str, Any]:
        """
        Get the current session completion status for a learning plan
        """
        try:
            # Get learning plan
            plan = await database["learning_plans"].find_one({"id": learning_plan_id, "user_id": user_id})
            if not plan:
                return {"success": False, "error": "Learning plan not found"}
            
            # Get weekly schedule
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            
            # Count completed sessions with proper completion data
            sessions_with_completion_data = 0
            sessions_without_completion_data = 0
            
            for week in weekly_schedule:
                session_details = week.get('session_details', [])
                for session in session_details:
                    if session.get('status') == 'completed' and session.get('completed_at') and session.get('duration_minutes'):
                        sessions_with_completion_data += 1
                    elif session.get('status') == 'completed':
                        sessions_without_completion_data += 1
            
            return {
                "success": True,
                "plan_id": learning_plan_id,
                "total_sessions": plan.get("total_sessions", 0),
                "completed_sessions": plan.get("completed_sessions", 0),
                "sessions_with_completion_data": sessions_with_completion_data,
                "sessions_without_completion_data": sessions_without_completion_data,
                "progress_percentage": plan.get("progress_percentage", 0.0),
                "weekly_schedule_weeks": len(weekly_schedule)
            }
            
        except Exception as e:
            logger.error(f"[SESSION_COMPLETION] Error getting completion status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def fix_missing_completion_data(cls, user_id: str, learning_plan_id: str) -> Dict[str, Any]:
        """
        Fix sessions that are marked as completed but missing completion data
        """
        try:
            logger.info(f"[SESSION_COMPLETION] Fixing missing completion data for plan {learning_plan_id}")
            
            # Get learning plan
            plan = await database["learning_plans"].find_one({"id": learning_plan_id, "user_id": user_id})
            if not plan:
                return {"success": False, "error": "Learning plan not found"}
            
            # Get weekly schedule
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            session_summaries = plan.get('session_summaries', [])
            
            fixed_sessions = 0
            
            # Fix sessions with missing completion data
            for week_index, week in enumerate(weekly_schedule):
                session_details = week.get('session_details', [])
                
                for session_index, session in enumerate(session_details):
                    # Check if session needs fixing
                    if (session.get('status') == 'pending' and 
                        (session.get('completed_at') is None or session.get('duration_minutes') is None)):
                        
                        # Check if we should mark this as completed based on plan progress
                        global_session_number = session.get('global_session_number')
                        completed_sessions = plan.get('completed_sessions', 0)
                        
                        if global_session_number and global_session_number <= completed_sessions:
                            # This session should be marked as completed
                            completion_time = datetime.utcnow().isoformat()
                            
                            session.update({
                                "status": "completed",
                                "completed_at": completion_time,
                                "duration_minutes": 5.0,  # Standard session duration
                                "session_summary": session_summaries[global_session_number - 1] if global_session_number <= len(session_summaries) else "Session completed successfully"
                            })
                            
                            fixed_sessions += 1
                            logger.info(f"[SESSION_COMPLETION] Fixed session {global_session_number} in week {week_index + 1}")
            
            if fixed_sessions > 0:
                # Update the learning plan
                result = await database["learning_plans"].update_one(
                    {"_id": plan["_id"]},
                    {"$set": {"plan_content.weekly_schedule": weekly_schedule}}
                )
                
                if result.modified_count > 0:
                    logger.info(f"[SESSION_COMPLETION] ✅ Fixed {fixed_sessions} sessions with missing completion data")
                    return {
                        "success": True,
                        "fixed_sessions": fixed_sessions,
                        "message": f"Fixed {fixed_sessions} sessions with missing completion data"
                    }
                else:
                    return {"success": False, "error": "Failed to update learning plan"}
            else:
                return {
                    "success": True,
                    "fixed_sessions": 0,
                    "message": "No sessions needed fixing"
                }
                
        except Exception as e:
            logger.error(f"[SESSION_COMPLETION] Error fixing missing completion data: {str(e)}")
            return {"success": False, "error": str(e)}
