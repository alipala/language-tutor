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
from database import learning_plans_collection
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
    def calculate_total_sessions_from_schedule(weekly_schedule: List[Dict[str, Any]]) -> int:
        """Calculate total sessions from the weekly schedule structure"""
        total = 0
        for week in weekly_schedule:
            session_details = week.get("session_details", [])
            if session_details:
                total += len(session_details)
            else:
                # Default to 2 sessions per week if no session_details
                total += 2
        return total
    
    @staticmethod
    def ensure_session_structure(weekly_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure each week in the schedule has proper session_details structure"""
        
        sessions_per_week = 2  # Default sessions per week
        
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
