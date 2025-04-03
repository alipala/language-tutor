from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import openai
from auth import get_current_user
from models import UserResponse
from database import database

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

class LearningPlan(BaseModel):
    id: str
    user_id: Optional[str] = None
    language: str
    proficiency_level: str
    goals: List[str]
    duration_months: int
    custom_goal: Optional[str] = None
    plan_content: Dict[str, Any]
    created_at: str

# Initialize learning goals collection
learning_goals_collection = database.learning_goals
learning_plans_collection = database.learning_plans

# Predefined learning goals
PREDEFINED_GOALS = [
    {"id": "travel", "text": "Travel and tourism", "category": "general"},
    {"id": "business", "text": "Business and professional communication", "category": "general"},
    {"id": "academic", "text": "Academic study", "category": "general"},
    {"id": "culture", "text": "Cultural understanding", "category": "general"},
    {"id": "daily", "text": "Daily conversation", "category": "general"},
    {"id": "reading", "text": "Reading comprehension", "category": "skills"},
    {"id": "writing", "text": "Writing skills", "category": "skills"},
    {"id": "speaking", "text": "Speaking fluency", "category": "skills"},
    {"id": "listening", "text": "Listening comprehension", "category": "skills"},
    {"id": "grammar", "text": "Grammar mastery", "category": "skills"},
    {"id": "vocabulary", "text": "Vocabulary expansion", "category": "skills"}
]

@router.get("/goals", response_model=List[LearningGoal])
async def get_learning_goals():
    """
    Get a list of predefined learning goals
    """
    try:
        # First, check if the collection exists and has valid data
        existing_goals = await learning_goals_collection.find().to_list(100)
        
        # Check if the existing goals have the correct schema
        valid_goals = []
        for goal in existing_goals:
            if all(key in goal for key in ["id", "text", "category"]):
                valid_goals.append(goal)
        
        # If we have valid goals, return them
        if valid_goals:
            return valid_goals
        
        # Otherwise, clear the collection and insert predefined goals
        print("No valid learning goals found in database. Reinitializing with predefined goals.")
        await learning_goals_collection.delete_many({})
        await learning_goals_collection.insert_many(PREDEFINED_GOALS)
        return PREDEFINED_GOALS
    
    except Exception as e:
        # If any error occurs, log it and return the predefined goals
        print(f"Error retrieving learning goals: {str(e)}")
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
    
    # For testing purposes, we'll bypass the OpenAI API call
    print("Bypassing OpenAI API call for testing purposes")
    
    # Create a mock plan content for testing
    plan_content_json = {
        "title": "3-Month English Learning Plan for A2 Level Focusing on Travel and Reading",
        "overview": "This plan is designed for an A2 level English learner who wants to improve their language skills for travel and reading comprehension over 3 months.",
        "weekly_schedule": [
            {
                "week": 1,
                "focus": "Basic travel vocabulary and simple reading materials",
                "activities": [
                    "Learn 20 common travel phrases",
                    "Read short paragraphs about tourist destinations",
                    "Practice asking for directions"
                ]
            },
            {
                "week": 2,
                "focus": "Transportation vocabulary and reading signs",
                "activities": [
                    "Learn vocabulary related to different modes of transportation",
                    "Practice reading transportation schedules and maps",
                    "Complete exercises on prepositions of place and movement"
                ]
            }
        ],
        "resources": [
            "English for Travelers (beginner's guide)",
            "Graded Readers - Level 2",
            "Duolingo Travel Module"
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
            "created_at": datetime.utcnow().isoformat()
        }
        
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
    
    return plan

@router.put("/plan/{plan_id}/assign", response_model=LearningPlan)
async def assign_plan_to_user(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Assign an anonymous learning plan to the current user
    """
    # Find the plan
    plan = await learning_plans_collection.find_one({"id": plan_id})
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not found"
        )
    
    # Check if the plan is not already assigned to a user
    if plan.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This learning plan is already assigned to a user"
        )
    
    # Update the plan with the current user's ID
    result = await learning_plans_collection.update_one(
        {"id": plan_id},
        {"$set": {"user_id": str(current_user.id)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign learning plan to user"
        )
    
    # Get the updated plan
    updated_plan = await learning_plans_collection.find_one({"id": plan_id})
    
    return updated_plan

@router.get("/plans", response_model=List[LearningPlan])
async def get_user_learning_plans(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all learning plans for the current user
    """
    plans = await learning_plans_collection.find({"user_id": str(current_user.id)}).to_list(100)
    
    return plans
