from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import openai
import uuid
import logging
from datetime import datetime
from auth import get_current_user
from models import UserResponse
from database import database, users_collection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/learning", tags=["learning"])

# Models for learning goals and plans
class LearningGoal(BaseModel):
    id: str
    text: str
    category: str

class LearningPlanRequest(BaseModel):
    language: str
    proficiency_level: str
    goals: List[str]
    duration_months: int
    custom_goal: Optional[str] = None
    assessment_data: Optional[Dict[str, Any]] = None

class LearningPlan(BaseModel):
    id: str
    user_id: Optional[str] = None
    language: str
    proficiency_level: str
    goals: List[str]
    duration_months: int
    custom_goal: Optional[str] = None
    plan_content: Dict[str, Any]
    assessment_data: Optional[Dict[str, Any]] = None
    created_at: str
    total_sessions: Optional[int] = None
    completed_sessions: Optional[int] = 0
    progress_percentage: Optional[float] = 0.0

# Initialize learning goals collection
learning_goals_collection = database.learning_goals
learning_plans_collection = database.learning_plans

# Predefined learning goals
PREDEFINED_GOALS = [
    {"id": "travel", "text": "Travel and tourism", "category": "general"},
    {"id": "business", "text": "Business and professional communication", "category": "general"},
    {"id": "academic", "text": "Academic study", "category": "general"},
    {"id": "culture", "text": "Cultural understanding", "category": "general"},
    {"id": "daily", "text": "Daily conversation", "category": "general"}
]

@router.get("/goals", response_model=List[LearningGoal])
async def get_learning_goals():
    """
    Get a list of predefined learning goals
    """
    try:
        # Force refresh of learning goals from the predefined list
        # This ensures we always have the latest goals definition
        await learning_goals_collection.delete_many({})
        await learning_goals_collection.insert_many(PREDEFINED_GOALS)
        return PREDEFINED_GOALS
    
    except Exception as e:
        # If any error occurs, log it and return the predefined goals
        print(f"Error refreshing learning goals: {str(e)}")
        print("Returning predefined goals instead")
        return PREDEFINED_GOALS

@router.post("/plan", response_model=LearningPlan)
async def create_learning_plan(
    plan_request: LearningPlanRequest,
    current_user: Optional[UserResponse] = None
):
    """
    Create a custom learning plan based on user's proficiency level, goals, and duration.
    Authentication is optional - if authenticated, the plan will be associated with the user.
    """
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured"
        )
    
    # Check if assessment data is provided
    assessment_data = plan_request.assessment_data
    
    # Log assessment data if available
    if assessment_data:
        print(f"Using assessment data for plan creation:\n{assessment_data}")
    else:
        print("No assessment data provided, using default plan template")
    
    # Create plan content based on assessment data if available, otherwise use mock data
    if assessment_data:
        # Extract key assessment information
        recognized_text = assessment_data.get('recognized_text', '')
        recommended_level = assessment_data.get('recommended_level', plan_request.proficiency_level)
        overall_score = assessment_data.get('overall_score', 50)
        strengths = assessment_data.get('strengths', [])
        areas_for_improvement = assessment_data.get('areas_for_improvement', [])
        next_steps = assessment_data.get('next_steps', [])
        
        # Extract skill scores
        pronunciation_score = assessment_data.get('pronunciation', {}).get('score', 50)
        pronunciation_feedback = assessment_data.get('pronunciation', {}).get('feedback', '')
        grammar_score = assessment_data.get('grammar', {}).get('score', 50)
        grammar_feedback = assessment_data.get('grammar', {}).get('feedback', '')
        vocabulary_score = assessment_data.get('vocabulary', {}).get('score', 50)
        vocabulary_feedback = assessment_data.get('vocabulary', {}).get('feedback', '')
        fluency_score = assessment_data.get('fluency', {}).get('score', 50)
        fluency_feedback = assessment_data.get('fluency', {}).get('feedback', '')
        coherence_score = assessment_data.get('coherence', {}).get('score', 50)
        coherence_feedback = assessment_data.get('coherence', {}).get('feedback', '')
        
        # Create a personalized plan based on assessment data
        plan_content_json = {
            "title": f"{plan_request.duration_months}-Month {plan_request.language.capitalize()} Learning Plan for {recommended_level} Level",
            "overview": f"This plan is designed based on your speaking assessment results. You demonstrated a {recommended_level} level proficiency with an overall score of {overall_score}/100.",
            "assessment_summary": {
                "overall_score": overall_score,
                "recommended_level": recommended_level,
                "strengths": strengths,
                "areas_for_improvement": areas_for_improvement,
                "skill_scores": {
                    "pronunciation": pronunciation_score,
                    "grammar": grammar_score,
                    "vocabulary": vocabulary_score,
                    "fluency": fluency_score,
                    "coherence": coherence_score
                }
            },
            "weekly_schedule": [
                {
                    "week": 1,
                    "focus": f"Addressing key improvement areas: {', '.join(areas_for_improvement[:2]) if areas_for_improvement else 'Building foundational skills'}",
                    "activities": next_steps[:3] if next_steps else [
                        "Practice basic conversation skills",
                        "Review fundamental grammar structures",
                        "Build essential vocabulary"
                    ]
                },
                {
                    "week": 2,
                    "focus": "Building on your strengths while addressing weaker areas",
                    "activities": [
                        f"Continue working on {areas_for_improvement[0] if areas_for_improvement else 'vocabulary expansion'}",
                        f"Practice {strengths[0].lower() if strengths else 'speaking fluency'}",
                        "Complete targeted exercises for your proficiency level"
                    ]
                }
            ],
            "resources": [
                f"{plan_request.language.capitalize()} Grammar Guide for {recommended_level} Level",
                f"Vocabulary Builder for {plan_request.language.capitalize()} Learners",
                "Language Practice App with Speaking Exercises"
            ]
        }
    else:
        # Use mock plan content for testing when no assessment data is available
        print("Using mock plan content for testing purposes")
        plan_content_json = {
            "title": f"{plan_request.duration_months}-Month {plan_request.language.capitalize()} Learning Plan for {plan_request.proficiency_level} Level",
            "overview": f"This plan is designed for a {plan_request.proficiency_level} level {plan_request.language} learner who wants to improve their language skills over {plan_request.duration_months} months.",
            "weekly_schedule": [
                {
                    "week": 1,
                    "focus": "Basic vocabulary and simple reading materials",
                    "activities": [
                        "Learn 20 common phrases",
                        "Read short paragraphs about everyday topics",
                        "Practice basic conversation skills"
                    ]
                },
                {
                    "week": 2,
                    "focus": "Building on foundational skills",
                    "activities": [
                        "Expand vocabulary with themed word lists",
                        "Practice reading and comprehension exercises",
                        "Complete exercises on common grammar structures"
                    ]
                }
            ],
            "resources": [
                f"{plan_request.language.capitalize()} for Beginners (guide)",
                "Graded Readers - Level 2",
                "Language Learning App Recommendations"
            ]
        }
    
    # Prepare goals text
    goals_text = ", ".join(plan_request.goals)
    if plan_request.custom_goal:
        goals_text += f", and specifically: {plan_request.custom_goal}"
    
    # Log information about the request
    goals_text = ", ".join(plan_request.goals)
    custom_goal_text = f" and {plan_request.custom_goal}" if plan_request.custom_goal else ""
    print(f"Creating learning plan for:\n"
          f"- Target language: {plan_request.language}\n"
          f"- Current proficiency level: {plan_request.proficiency_level}\n"
          f"- Learning goals: {goals_text}")
    
    try:
        # Log what would have been sent to OpenAI
        print(f"Would have created a plan for {plan_request.proficiency_level} level {plan_request.language} learner focusing on {goals_text}{custom_goal_text} for {plan_request.duration_months} months")
        
        # We're using the mock plan content defined above
        # No need to call OpenAI API or parse the response
        
        # Calculate total sessions based on duration
        def calculate_total_sessions(duration_months: int) -> int:
            """Calculate total sessions based on duration"""
            session_mapping = {
                1: 8,   # 1 month = 4 weeks, 8 sessions
                2: 16,  # 2 months = 8 weeks, 16 sessions
                3: 24,  # 3 months = 12 weeks, 24 sessions
                6: 48,  # 6 months = 24 weeks, 48 sessions
                12: 96  # 12 months = 48 weeks, 96 sessions
            }
            return session_mapping.get(duration_months, duration_months * 8)  # Default: 8 sessions per month
        
        total_sessions = calculate_total_sessions(plan_request.duration_months)
        
        # Create a new learning plan
        from datetime import datetime
        import uuid
        
        new_plan = {
            "id": str(uuid.uuid4()),
            "user_id": str(current_user.id) if current_user else None,
            "language": plan_request.language,
            "proficiency_level": plan_request.proficiency_level,
            "goals": plan_request.goals,
            "duration_months": plan_request.duration_months,
            "custom_goal": plan_request.custom_goal,
            "plan_content": plan_content_json,
            "assessment_data": plan_request.assessment_data,
            "created_at": datetime.utcnow().isoformat(),
            "total_sessions": total_sessions,
            "completed_sessions": 0,
            "progress_percentage": 0.0
        }
        
        # If user is authenticated and assessment data is provided, update user profile
        if current_user and plan_request.assessment_data:
            from database import users_collection
            # Update the user's profile with the assessment data
            await users_collection.update_one(
                {"_id": current_user.id},
                {"$set": {
                    "last_assessment_data": plan_request.assessment_data,
                    "preferred_language": plan_request.language,
                    "preferred_level": plan_request.proficiency_level
                }}
            )
            print(f"Updated user profile with assessment data for user {current_user.id}")
        
        # Save the plan to the database
        result = await learning_plans_collection.insert_one(new_plan)
        
        # Return the created plan
        return new_plan
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning plan: {str(e)}"
        )

@router.get("/plan/{plan_id}", response_model=LearningPlan)
async def get_learning_plan(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific learning plan by ID
    """
    plan = await learning_plans_collection.find_one({"id": plan_id})
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not found"
        )
    
    # Check if the plan belongs to the current user
    if plan.get("user_id") and plan.get("user_id") != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this learning plan"
        )
    
    # Ensure backward compatibility - add missing progress fields for existing plans
    if "total_sessions" not in plan or plan.get("total_sessions") is None:
        def calculate_total_sessions(duration_months: int) -> int:
            """Calculate total sessions based on duration"""
            session_mapping = {
                1: 8,   # 1 month = 4 weeks, 8 sessions
                2: 16,  # 2 months = 8 weeks, 16 sessions
                3: 24,  # 3 months = 12 weeks, 24 sessions
                6: 48,  # 6 months = 24 weeks, 48 sessions
                12: 96  # 12 months = 48 weeks, 96 sessions
            }
            return session_mapping.get(duration_months, duration_months * 8)  # Default: 8 sessions per month
        
        total_sessions = calculate_total_sessions(plan.get("duration_months", 1))
        completed_sessions = plan.get("completed_sessions", 0)
        progress_percentage = (completed_sessions / total_sessions) * 100 if total_sessions > 0 else 0.0
        
        # Update the plan in the database
        await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "progress_percentage": progress_percentage
            }}
        )
        
        # Update the plan object to return
        plan["total_sessions"] = total_sessions
        plan["completed_sessions"] = completed_sessions
        plan["progress_percentage"] = progress_percentage
        
        print(f"Updated existing plan {plan_id} with progress tracking: {completed_sessions}/{total_sessions} sessions ({progress_percentage:.1f}%)")
    
    return plan

@router.put("/plan/{plan_id}/assign", response_model=LearningPlan)
async def assign_plan_to_user(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Assign an anonymous learning plan to the current user
    """
    # Convert user ID to string for consistent handling
    user_id = str(current_user.id)
    
    # Log the operation for debugging
    logger.info(f"Assigning plan {plan_id} to user {user_id}")
    
    try:
        # Find the plan
        plan = await learning_plans_collection.find_one({"id": plan_id})
        
        if not plan:
            logger.warning(f"Learning plan {plan_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found"
            )
        
        # Check if the plan is not already assigned to a user
        if plan.get("user_id"):
            current_owner = plan.get("user_id")
            logger.warning(f"Plan {plan_id} already assigned to user {current_owner}")
            
            # If it's already assigned to the current user, return it as is
            if current_owner == user_id:
                logger.info(f"Plan {plan_id} already assigned to current user {user_id}")
                return plan
                
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This learning plan is already assigned to a user"
            )
        
        # Update the plan with the current user's ID
        result = await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {"user_id": user_id}}
        )
        
        if result.modified_count == 0:
            logger.error(f"Failed to assign plan {plan_id} to user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign learning plan to user"
            )
        
        logger.info(f"Successfully assigned plan {plan_id} to user {user_id}")
        
        # Get the updated plan
        updated_plan = await learning_plans_collection.find_one({"id": plan_id})
    except Exception as e:
        logger.error(f"Error assigning plan to user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning plan to user: {str(e)}"
        )
    
    return updated_plan

@router.get("/plans", response_model=List[LearningPlan])
async def get_user_learning_plans(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all learning plans for the current user
    """
    # Convert user ID to string and handle ObjectId conversion properly
    user_id = str(current_user.id)
    
    # Log the user ID being used for debugging
    logger.info(f"Fetching learning plans for user ID: {user_id}")
    
    try:
        # Try to find plans with the string user ID
        plans = await learning_plans_collection.find({"user_id": user_id}).to_list(100)
        
        if not plans:
            # If no plans found, try with ObjectId (in case it was stored that way)
            try:
                from bson import ObjectId
                object_id = ObjectId(user_id)
                plans = await learning_plans_collection.find({"user_id": object_id}).to_list(100)
                
                # If plans are found with ObjectId, log this for debugging
                if plans:
                    logger.info(f"Found {len(plans)} plans using ObjectId format")
            except Exception as e:
                logger.error(f"Error trying ObjectId conversion: {str(e)}")
                # Continue with empty plans list if ObjectId conversion fails
                pass
        else:
            logger.info(f"Found {len(plans)} plans using string user ID")
        
        # Ensure backward compatibility - add missing progress fields for existing plans
        def calculate_total_sessions(duration_months: int) -> int:
            """Calculate total sessions based on duration"""
            session_mapping = {
                1: 8,   # 1 month = 4 weeks, 8 sessions
                2: 16,  # 2 months = 8 weeks, 16 sessions
                3: 24,  # 3 months = 12 weeks, 24 sessions
                6: 48,  # 6 months = 24 weeks, 48 sessions
                12: 96  # 12 months = 48 weeks, 96 sessions
            }
            return session_mapping.get(duration_months, duration_months * 8)  # Default: 8 sessions per month
        
        updated_plans = []
        for plan in plans:
            # Check if plan needs progress tracking fields
            if "total_sessions" not in plan or plan.get("total_sessions") is None:
                total_sessions = calculate_total_sessions(plan.get("duration_months", 1))
                completed_sessions = plan.get("completed_sessions", 0)
                progress_percentage = (completed_sessions / total_sessions) * 100 if total_sessions > 0 else 0.0
                
                # Update the plan in the database
                await learning_plans_collection.update_one(
                    {"id": plan["id"]},
                    {"$set": {
                        "total_sessions": total_sessions,
                        "completed_sessions": completed_sessions,
                        "progress_percentage": progress_percentage
                    }}
                )
                
                # Update the plan object
                plan["total_sessions"] = total_sessions
                plan["completed_sessions"] = completed_sessions
                plan["progress_percentage"] = progress_percentage
                
                print(f"Updated existing plan {plan['id']} with progress tracking: {completed_sessions}/{total_sessions} sessions ({progress_percentage:.1f}%)")
            
            updated_plans.append(plan)
        
        return updated_plans
    
    except Exception as e:
        logger.error(f"Error fetching learning plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching learning plans: {str(e)}")


class SpeakingAssessmentData(BaseModel):
    """Model for speaking assessment data"""
    assessment_data: Dict[str, Any]


class SessionProgressUpdate(BaseModel):
    """Model for updating session progress"""
    plan_id: str
    completed_sessions: int

@router.put("/plan/{plan_id}/progress")
async def update_session_progress(
    plan_id: str,
    progress_update: SessionProgressUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update the session progress for a learning plan
    """
    try:
        # Find the plan
        plan = await learning_plans_collection.find_one({"id": plan_id})
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found"
            )
        
        # Check if the plan belongs to the current user
        if plan.get("user_id") and plan.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this learning plan"
            )
        
        # Calculate progress percentage
        total_sessions = plan.get("total_sessions", 1)
        progress_percentage = min((progress_update.completed_sessions / total_sessions) * 100, 100.0)
        
        # Update the plan
        result = await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {
                "completed_sessions": progress_update.completed_sessions,
                "progress_percentage": progress_percentage
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update learning plan progress"
            )
        
        # Get the updated plan
        updated_plan = await learning_plans_collection.find_one({"id": plan_id})
        return updated_plan
        
    except Exception as e:
        logger.error(f"Error updating session progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating session progress: {str(e)}"
        )

@router.post("/save-assessment", response_model=UserResponse)
async def save_assessment_data(
    assessment: SpeakingAssessmentData,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Save speaking assessment data to user profile and create a learning plan if requested
    """
    try:
        # Import ObjectId for proper MongoDB ID handling
        from bson import ObjectId
        
        # Convert user ID to the correct format for MongoDB
        # If it's already an ObjectId, use it as is; if it's a string, convert it
        user_id = current_user.id
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except Exception as e:
                print(f"Warning: Could not convert user ID to ObjectId: {str(e)}")
        
        # First try to find the user to confirm they exist
        user = await users_collection.find_one({"_id": user_id})
        if not user:
            # Try alternate formats as fallback
            user = await users_collection.find_one({"_id": str(user_id)})
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found with ID {user_id}")
            else:
                # If found with string ID, use that format
                user_id = str(user_id)
        
        # Update the user's profile with the assessment data
        result = await users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "last_assessment_data": assessment.assessment_data,
                "assessment_history": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": assessment.assessment_data
                }
            }}
        )
        
        # Log the update
        print(f"Updated user profile with assessment data for user {user_id} (modified count: {result.modified_count})")
        
        # Get the updated user data
        updated_user = await users_collection.find_one({"_id": user_id})
        if not updated_user:
            raise HTTPException(status_code=404, detail=f"User not found after update with ID {user_id}")
        
        # Properly handle the MongoDB _id field for UserResponse
        # First, make a copy of the user data to avoid modifying the original
        user_data = dict(updated_user)
        
        # Ensure _id is properly set for UserResponse
        if "_id" in user_data:
            # Convert ObjectId to string if needed
            user_data["_id"] = str(user_data["_id"])
        else:
            # If _id is missing for some reason, raise a clear error
            raise HTTPException(
                status_code=500,
                detail="User document is missing _id field"
            )
        
        try:
            # Create UserResponse object with the properly formatted data
            return UserResponse(**user_data)
        except Exception as e:
            # Log detailed validation errors
            print(f"Error creating UserResponse: {str(e)}")
            print(f"User data keys: {user_data.keys()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user response object: {str(e)}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save assessment data: {str(e)}"
        )
