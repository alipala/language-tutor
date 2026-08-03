"""
Learning Plan Service
Provides robust learning plan creation with duplicate prevention and proper error handling.
Handles MongoDB _id conflicts and ensures atomic operations.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from database import (
    learning_plans_collection,
    sentence_analysis_jobs_collection,
    speaking_time_tracking_collection,
    notifications_collection,
    user_achievements_collection,
)
from models import UserResponse

logger = logging.getLogger(__name__)

class LearningPlanService:
    """Service for managing learning plan creation and updates with duplicate prevention"""
    
    @staticmethod
    async def create_learning_plan_safe(
        plan_data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Create a learning plan with duplicate prevention and retry logic
        
        Args:
            plan_data: The plan data to insert
            max_retries: Maximum number of retry attempts
            
        Returns:
            The created plan data with MongoDB _id
            
        Raises:
            Exception: If plan creation fails after all retries
        """
        
        for attempt in range(max_retries):
            try:
                # Generate a new unique ID for each attempt
                unique_plan_id = str(uuid.uuid4())
                
                # Ensure the plan has a unique custom id field
                plan_data_copy = plan_data.copy()
                plan_data_copy["id"] = unique_plan_id

                # Add creation timestamp
                plan_data_copy["created_at"] = datetime.utcnow().isoformat()

                # Every plan must carry an explicit lifecycle status. Plans created
                # without one relied on readers defaulting a missing field
                # (hub_routes / missions_routes both special-case `not status`),
                # which worked by accident and made "is this plan active?" ambiguous
                # in the DB. Set it once, here, without overriding a caller value.
                plan_data_copy.setdefault("status", "in_progress")
                
                # CRITICAL: Remove any existing _id field to let MongoDB generate it
                if "_id" in plan_data_copy:
                    del plan_data_copy["_id"]
                
                logger.info(f"[LEARNING_PLAN_SERVICE] Attempt {attempt + 1}: Creating plan with id: {unique_plan_id}")
                
                # Check if a plan with this custom id already exists (double-check)
                existing_plan = await learning_plans_collection.find_one({"id": unique_plan_id})
                if existing_plan:
                    logger.warning(f"[LEARNING_PLAN_SERVICE] Plan with id {unique_plan_id} already exists, generating new ID")
                    continue  # Try again with a new UUID
                
                # Attempt to insert the plan
                result = await learning_plans_collection.insert_one(plan_data_copy)
                
                if result.inserted_id:
                    # Add the MongoDB _id to the plan data for return
                    plan_data_copy["_id"] = str(result.inserted_id)
                    
                    logger.info(f"[LEARNING_PLAN_SERVICE] ✅ Successfully created plan: {unique_plan_id} (MongoDB _id: {result.inserted_id})")
                    return plan_data_copy
                else:
                    logger.error(f"[LEARNING_PLAN_SERVICE] Insert returned no inserted_id")
                    raise Exception("Failed to insert plan: no inserted_id returned")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[LEARNING_PLAN_SERVICE] Attempt {attempt + 1} failed: {error_msg}")
                
                # Check if it's a duplicate key error
                if "duplicate key error" in error_msg or "E11000" in error_msg:
                    logger.warning(f"[LEARNING_PLAN_SERVICE] Duplicate key error detected, retrying with new UUID...")
                    
                    if attempt == max_retries - 1:
                        logger.error(f"[LEARNING_PLAN_SERVICE] Max retries exceeded for duplicate key error")
                        raise Exception(f"Failed to create learning plan after {max_retries} attempts due to duplicate key conflicts")
                    
                    # Wait a bit before retrying
                    import asyncio
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    # For non-duplicate errors, fail immediately
                    logger.error(f"[LEARNING_PLAN_SERVICE] Non-duplicate error encountered: {error_msg}")
                    raise Exception(f"Failed to create learning plan: {error_msg}")
        
        # If we reach here, all retries failed
        raise Exception(f"Failed to create learning plan after {max_retries} attempts")
    
    @staticmethod
    async def update_learning_plan_safe(
        plan_id: str,
        update_data: Dict[str, Any],
        current_user: Optional[UserResponse] = None
    ) -> Dict[str, Any]:
        """
        Safely update a learning plan with proper validation
        
        Args:
            plan_id: The plan ID to update
            update_data: The data to update
            current_user: Current user for permission checking
            
        Returns:
            The updated plan data
            
        Raises:
            Exception: If plan not found or update fails
        """
        
        try:
            # Find the existing plan
            existing_plan = await learning_plans_collection.find_one({"id": plan_id})
            
            if not existing_plan:
                logger.error(f"[LEARNING_PLAN_SERVICE] Plan not found: {plan_id}")
                raise Exception(f"Learning plan not found: {plan_id}")
            
            # Check permissions if user is provided
            if current_user and existing_plan.get("user_id"):
                if existing_plan.get("user_id") != str(current_user.id):
                    logger.error(f"[LEARNING_PLAN_SERVICE] Permission denied for plan {plan_id}")
                    raise Exception("You don't have permission to update this learning plan")
            
            # Add update timestamp
            update_data_copy = update_data.copy()
            update_data_copy["updated_at"] = datetime.utcnow().isoformat()
            
            # Perform the update
            result = await learning_plans_collection.update_one(
                {"id": plan_id},
                {"$set": update_data_copy}
            )
            
            if result.modified_count == 0:
                logger.warning(f"[LEARNING_PLAN_SERVICE] No changes made to plan {plan_id}")
                # This might not be an error - the data might be the same
            else:
                logger.info(f"[LEARNING_PLAN_SERVICE] ✅ Successfully updated plan {plan_id}")
            
            # Return the updated plan
            updated_plan = await learning_plans_collection.find_one({"id": plan_id})
            return updated_plan
            
        except Exception as e:
            logger.error(f"[LEARNING_PLAN_SERVICE] Error updating plan {plan_id}: {str(e)}")
            raise Exception(f"Failed to update learning plan: {str(e)}")
    
    @staticmethod
    async def get_learning_plan_safe(
        plan_id: str,
        current_user: Optional[UserResponse] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Safely retrieve a learning plan with proper validation
        
        Args:
            plan_id: The plan ID to retrieve
            current_user: Current user for permission checking
            
        Returns:
            The plan data or None if not found
            
        Raises:
            Exception: If permission denied
        """
        
        try:
            # Find the plan
            plan = await learning_plans_collection.find_one({"id": plan_id})
            
            if not plan:
                logger.info(f"[LEARNING_PLAN_SERVICE] Plan not found: {plan_id}")
                return None
            
            # Check permissions if user is provided
            if current_user and plan.get("user_id"):
                if plan.get("user_id") != str(current_user.id):
                    logger.error(f"[LEARNING_PLAN_SERVICE] Permission denied for plan {plan_id}")
                    raise Exception("You don't have permission to access this learning plan")
            
            logger.info(f"[LEARNING_PLAN_SERVICE] ✅ Successfully retrieved plan {plan_id}")
            return plan
            
        except Exception as e:
            logger.error(f"[LEARNING_PLAN_SERVICE] Error retrieving plan {plan_id}: {str(e)}")
            raise Exception(f"Failed to retrieve learning plan: {str(e)}")
    
    @staticmethod
    async def delete_learning_plan_safe(
        plan_id: str,
        current_user: Optional[UserResponse] = None
    ) -> bool:
        """
        Safely delete a learning plan with proper validation
        
        Args:
            plan_id: The plan ID to delete
            current_user: Current user for permission checking
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            Exception: If permission denied or delete fails
        """
        
        try:
            # Find the plan first
            plan = await learning_plans_collection.find_one({"id": plan_id})
            
            if not plan:
                logger.info(f"[LEARNING_PLAN_SERVICE] Plan not found for deletion: {plan_id}")
                return False
            
            # Check permissions if user is provided
            if current_user and plan.get("user_id"):
                if plan.get("user_id") != str(current_user.id):
                    logger.error(f"[LEARNING_PLAN_SERVICE] Permission denied for plan deletion {plan_id}")
                    raise Exception("You don't have permission to delete this learning plan")
            
            # Perform the deletion
            result = await learning_plans_collection.delete_one({"id": plan_id})
            
            if result.deleted_count > 0:
                logger.info(f"[LEARNING_PLAN_SERVICE] ✅ Successfully deleted plan {plan_id}")
                return True
            else:
                logger.warning(f"[LEARNING_PLAN_SERVICE] No plan deleted for {plan_id}")
                return False
                
        except Exception as e:
            logger.error(f"[LEARNING_PLAN_SERVICE] Error deleting plan {plan_id}: {str(e)}")
            raise Exception(f"Failed to delete learning plan: {str(e)}")

    @staticmethod
    async def archive_learning_plan_safe(
        plan_id: str,
        current_user: Optional[UserResponse] = None
    ) -> bool:
        """
        Soft-delete ("archive") a learning plan the user owns, then cascade-
        clean all operational data that was tied exclusively to this plan.

        What is KEPT (user's general learning history, independent of any plan):
          - conversation_sessions  (freestyle / news practice)
          - speaking_breakthroughs (breakthrough moments earned per language)
          - challenge_sessions     (games / flashcard XP)
          - daily_stats / XP       (XP is never rolled back)
          - @lang / @level scoped badges (DNA, CEFR, fluency, streaks…)
          - story_progress         (games tab progression)
          - The learning_plan doc itself (kept as "archived" for analytics /
            admin / tutor AI-report reads)

        What is DELETED (orphaned operational data tied to this plan only):
          - sentence_analysis_jobs  (plan_id = this plan)
          - speaking_time_tracking  (session_id prefix = "plan_<plan_id>_")
          - notifications           (session_id prefix = "plan_<plan_id>_")
          - plan_ prefix badges in user_achievements — BUT ONLY when the user
            has no remaining active plans.  If the user still has an active
            plan those badges stay valid.  When all plans are gone the user is
            starting fresh (Duolingo-style reset) so plan milestones should
            reset too; they'll be re-earned on the new plan.

        Already-earned XP / streaks are never touched — archive is not undo.

        Returns True if archived, False if not found. Raises on permission
        denial.
        """
        try:
            plan = await learning_plans_collection.find_one({"id": plan_id})
            if not plan:
                logger.info(f"[LEARNING_PLAN_SERVICE] Plan not found for archive: {plan_id}")
                return False

            if current_user and plan.get("user_id"):
                if plan.get("user_id") != str(current_user.id):
                    logger.error(f"[LEARNING_PLAN_SERVICE] Permission denied for plan archive {plan_id}")
                    raise Exception("You don't have permission to delete this learning plan")

            # Already archived → idempotent success (skip cascade; already ran).
            if plan.get("status") == "archived":
                return True

            user_id = plan.get("user_id")

            # ── 1. Soft-archive the plan document ─────────────────────────────
            result = await learning_plans_collection.update_one(
                {"id": plan_id},
                {"$set": {
                    "status": "archived",
                    "archived_at": datetime.utcnow(),
                    "status_before_archive": plan.get("status"),
                    "is_active": False,
                    "updated_at": datetime.utcnow(),
                }},
            )
            if result.modified_count == 0:
                logger.warning(f"[LEARNING_PLAN_SERVICE] No plan archived for {plan_id}")
                return False

            logger.info(f"[LEARNING_PLAN_SERVICE] ✅ Archived plan {plan_id}")

            # ── 2. Cascade cleanup — best-effort, never raise ─────────────────
            # Failures are logged but must not surface to the caller; the plan
            # is already archived so the user-facing action succeeded.
            session_id_prefix = f"plan_{plan_id}_"

            try:
                r = await sentence_analysis_jobs_collection.delete_many(
                    {"plan_id": plan_id}
                )
                logger.info(f"[LEARNING_PLAN_SERVICE] Deleted {r.deleted_count} sentence_analysis_jobs for plan {plan_id}")
            except Exception as ce:
                logger.warning(f"[LEARNING_PLAN_SERVICE] sentence_analysis_jobs cleanup failed: {ce}")

            try:
                r = await speaking_time_tracking_collection.delete_many(
                    {"session_id": {"$regex": f"^{session_id_prefix}"}}
                )
                logger.info(f"[LEARNING_PLAN_SERVICE] Deleted {r.deleted_count} speaking_time_tracking rows for plan {plan_id}")
            except Exception as ce:
                logger.warning(f"[LEARNING_PLAN_SERVICE] speaking_time_tracking cleanup failed: {ce}")

            try:
                r = await notifications_collection.delete_many(
                    {"session_id": {"$regex": f"^{session_id_prefix}"}}
                )
                logger.info(f"[LEARNING_PLAN_SERVICE] Deleted {r.deleted_count} notifications for plan {plan_id}")
            except Exception as ce:
                logger.warning(f"[LEARNING_PLAN_SERVICE] notifications cleanup failed: {ce}")

            # ── 3. plan_ prefix badges — only when user has no remaining active plans ──
            if user_id:
                try:
                    active_plan_count = await learning_plans_collection.count_documents(
                        {"user_id": user_id, "status": {"$nin": ["archived"]}}
                    )
                    if active_plan_count == 0:
                        r = await user_achievements_collection.delete_many(
                            {"user_id": user_id, "achievement_id": {"$regex": "^plan_"}}
                        )
                        logger.info(
                            f"[LEARNING_PLAN_SERVICE] Deleted {r.deleted_count} plan_ badges for user {user_id} "
                            f"(no active plans remaining)"
                        )
                    else:
                        logger.info(
                            f"[LEARNING_PLAN_SERVICE] Kept plan_ badges for user {user_id} "
                            f"({active_plan_count} active plan(s) still exist)"
                        )
                except Exception as ce:
                    logger.warning(f"[LEARNING_PLAN_SERVICE] plan_ badge cleanup failed: {ce}")

            return True

        except Exception as e:
            logger.error(f"[LEARNING_PLAN_SERVICE] Error archiving plan {plan_id}: {str(e)}")
            raise Exception(f"Failed to archive learning plan: {str(e)}")

    @staticmethod
    def calculate_total_sessions_from_schedule(weekly_schedule: List[Dict[str, Any]]) -> int:
        """Calculate total sessions from the weekly schedule structure"""
        total = 0
        for week in weekly_schedule:
            session_details = week.get("session_details", [])
            if session_details:
                total += len(session_details)
            else:
                # Default to 4 sessions per week if no session_details
                total += 4
        return total
    
    @staticmethod
    def ensure_session_structure(weekly_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure each week in the schedule has proper session_details structure"""
        
        sessions_per_week = 4  # 4 sessions per week
        
        for week_idx, week in enumerate(weekly_schedule):
            # Initialize session_details if not present
            if 'session_details' not in week:
                week['session_details'] = []
            
            # Ensure we have the expected number of session placeholders
            current_sessions = len(week.get('session_details', []))
            if current_sessions < sessions_per_week:
                # Add missing session placeholders
                for session_idx in range(current_sessions, sessions_per_week):
                    week['session_details'].append({
                        "session_number": session_idx + 1,
                        "focus": week.get("focus", "Language practice"),
                        "completed_at": None,
                        "duration_minutes": None,
                        "session_summary": None,
                        "status": "pending"
                    })
            
            # Update sessions_completed count
            completed_count = sum(1 for session in week['session_details'] if session.get('status') in ['completed', 'partial'])
            week['sessions_completed'] = completed_count
            week['total_sessions'] = len(week['session_details'])
        
        return weekly_schedule
