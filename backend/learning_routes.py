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
    session_summaries: Optional[List[str]] = []

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
        
        # Generate comprehensive weekly schedule based on duration
        def generate_weekly_schedule(duration_months: int, areas_for_improvement: list, strengths: list, next_steps: list, language: str, level: str):
            """Generate a comprehensive weekly schedule for the learning plan"""
            total_weeks = duration_months * 4  # 4 weeks per month
            weekly_schedule = []
            
            # Define learning themes that cycle through the plan
            learning_themes = [
                "Foundation Building",
                "Skill Development", 
                "Practical Application",
                "Advanced Practice",
                "Fluency Enhancement",
                "Cultural Integration",
                "Professional Communication",
                "Creative Expression"
            ]
            
            # Define activity templates based on proficiency level
            level_activities = {
                "A1": [
                    "Learn basic vocabulary (20-30 new words)",
                    "Practice simple sentence structures",
                    "Listen to beginner-level audio content",
                    "Complete pronunciation exercises",
                    "Practice greetings and introductions"
                ],
                "A2": [
                    "Expand vocabulary in specific topics",
                    "Practice past and future tenses",
                    "Engage in simple conversations",
                    "Read short texts and articles",
                    "Write simple paragraphs"
                ],
                "B1": [
                    "Master intermediate grammar structures",
                    "Practice expressing opinions and preferences",
                    "Engage in longer conversations",
                    "Read news articles and stories",
                    "Write detailed descriptions"
                ],
                "B2": [
                    "Refine complex grammar usage",
                    "Practice debate and argumentation",
                    "Analyze authentic materials",
                    "Write formal and informal texts",
                    "Develop presentation skills"
                ],
                "C1": [
                    "Perfect advanced language structures",
                    "Practice nuanced expression",
                    "Analyze complex texts and media",
                    "Write sophisticated compositions",
                    "Develop academic/professional communication"
                ],
                "C2": [
                    "Master native-like expression",
                    "Practice subtle language nuances",
                    "Engage with complex literature",
                    "Write at near-native level",
                    "Develop specialized vocabulary"
                ]
            }
            
            base_activities = level_activities.get(level, level_activities["B1"])
            
            for week in range(1, total_weeks + 1):
                # Determine focus based on week progression
                if week <= 4:
                    # First month: Address key improvement areas
                    focus_area = areas_for_improvement[0] if areas_for_improvement else "Building foundational skills"
                    focus = f"Addressing key improvement areas: {focus_area}"
                    activities = next_steps[:3] if next_steps else base_activities[:3]
                elif week <= 8:
                    # Second month: Build on strengths
                    strength_area = strengths[0] if strengths else "communication skills"
                    focus = f"Building on your strengths: {strength_area}"
                    activities = [
                        f"Continue working on {areas_for_improvement[0] if areas_for_improvement else 'vocabulary expansion'}",
                        f"Practice {strength_area.lower()}",
                        "Complete targeted exercises for your proficiency level"
                    ]
                else:
                    # Subsequent months: Cycle through themes
                    theme_index = ((week - 9) // 4) % len(learning_themes)
                    theme = learning_themes[theme_index]
                    focus = f"{theme}: {areas_for_improvement[(week-1) % len(areas_for_improvement)] if areas_for_improvement else 'Comprehensive skill development'}"
                    
                    # Generate activities based on theme and level
                    if theme == "Foundation Building":
                        activities = [
                            f"Review and strengthen {areas_for_improvement[0] if areas_for_improvement else 'core skills'}",
                            base_activities[0],
                            base_activities[1]
                        ]
                    elif theme == "Skill Development":
                        activities = [
                            f"Advanced practice in {areas_for_improvement[1] if len(areas_for_improvement) > 1 else 'speaking fluency'}",
                            base_activities[2],
                            base_activities[3]
                        ]
                    elif theme == "Practical Application":
                        activities = [
                            "Apply skills in real-world scenarios",
                            "Practice with authentic materials",
                            "Engage in practical conversations"
                        ]
                    elif theme == "Advanced Practice":
                        activities = [
                            "Challenge yourself with complex tasks",
                            "Practice advanced grammar structures",
                            "Develop specialized vocabulary"
                        ]
                    elif theme == "Fluency Enhancement":
                        activities = [
                            "Focus on natural speech patterns",
                            "Practice spontaneous conversation",
                            "Work on rhythm and intonation"
                        ]
                    elif theme == "Cultural Integration":
                        activities = [
                            f"Learn about {language} culture and customs",
                            "Practice culturally appropriate communication",
                            "Explore cultural expressions and idioms"
                        ]
                    elif theme == "Professional Communication":
                        activities = [
                            "Practice business/academic language",
                            "Develop formal writing skills",
                            "Master professional presentations"
                        ]
                    else:  # Creative Expression
                        activities = [
                            "Express creativity through language",
                            "Practice storytelling and narrative",
                            "Explore artistic and literary language"
                        ]
                
                weekly_schedule.append({
                    "week": week,
                    "focus": focus,
                    "activities": activities,
                    "sessions_completed": 0,
                    "total_sessions": 2  # 2 sessions per week
                })
            
            return weekly_schedule
        
        weekly_schedule = generate_weekly_schedule(
            plan_request.duration_months, 
            areas_for_improvement, 
            strengths, 
            next_steps,
            plan_request.language,
            recommended_level
        )
        
        # Create a personalized plan based on assessment data
        plan_content_json = {
            "title": f"{plan_request.duration_months}-Month {plan_request.language.capitalize()} Learning Plan for {recommended_level} Level",
            "overview": f"This comprehensive plan is designed based on your speaking assessment results. You demonstrated a {recommended_level} level proficiency with an overall score of {overall_score}/100. The plan spans {plan_request.duration_months} months with {len(weekly_schedule)} weeks of structured learning.",
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
            "weekly_schedule": weekly_schedule,
            "learning_objectives": [
                f"Improve {areas_for_improvement[0] if areas_for_improvement else 'overall communication skills'}",
                f"Build upon existing strengths in {strengths[0] if strengths else 'language use'}",
                f"Achieve consistent {recommended_level} level performance",
                "Develop confidence in real-world communication",
                "Master advanced language structures and vocabulary"
            ],
            "resources": [
                f"{plan_request.language.capitalize()} Grammar Guide for {recommended_level} Level",
                f"Vocabulary Builder for {plan_request.language.capitalize()} Learners",
                "Language Practice App with Speaking Exercises",
                f"Authentic {plan_request.language.capitalize()} Media Resources",
                f"Cultural Context Guide for {plan_request.language.capitalize()} Speakers"
            ],
            "progress_tracking": {
                "total_weeks": len(weekly_schedule),
                "sessions_per_week": 2,
                "total_sessions": len(weekly_schedule) * 2,
                "milestone_weeks": [4, 8, 12, 24, 36, 48] if plan_request.duration_months >= 12 else [4, 8, 12]
            }
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
            # Update the user's profile with the latest assessment data only
            # Don't overwrite preferred_language and preferred_level as users can have multiple languages
            await users_collection.update_one(
                {"_id": current_user.id},
                {"$set": {
                    "last_assessment_data": plan_request.assessment_data,
                    "assessment_history": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": plan_request.assessment_data,
                        "language": plan_request.language,
                        "level": plan_request.proficiency_level
                    }
                }}
            )
            print(f"Updated user profile with assessment data for user {current_user.id} (language: {plan_request.language}, level: {plan_request.proficiency_level})")
            
            # IMPORTANT: Track assessment usage for subscription limits
            # This was the missing piece causing the bug!
            try:
                await users_collection.update_one(
                    {"_id": current_user.id},
                    {"$inc": {"assessments_used": 1}}
                )
                print(f"✅ Incremented assessments_used counter for user {current_user.id}")
            except Exception as e:
                print(f"⚠️ Warning: Failed to track assessment usage: {str(e)}")
                # Don't fail the entire operation if usage tracking fails
        
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

@router.post("/session-summary")
async def save_session_summary(
    plan_id: str,
    session_summary: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Save a session summary to the correct week in the learning plan structure
    """
    try:
        # Find the learning plan
        learning_plan = await learning_plans_collection.find_one({"id": plan_id})
        
        if not learning_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found"
            )
        
        # Check if the plan belongs to the current user
        if learning_plan.get("user_id") and learning_plan.get("user_id") != str(current_user.id):
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
        
        print(f"[SESSION_SUMMARY] Saving session {session_number} to Week {week_index + 1}, Session {session_in_week}")
        
        # Get the weekly schedule
        weekly_schedule = learning_plan.get("plan_content", {}).get("weekly_schedule", [])
        
        if week_index >= len(weekly_schedule):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session {session_number} exceeds available weeks in the plan"
            )
        
        # Update the specific week with session details
        week = weekly_schedule[week_index]
        
        # Initialize session_details if it doesn't exist
        if 'session_details' not in week:
            week['session_details'] = []
        
        # Create session detail object
        session_detail = {
            "session_number": session_in_week,
            "global_session_number": session_number,
            "summary": session_summary,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        # Add to session_details
        week['session_details'].append(session_detail)
        
        # Update sessions_completed for this week
        week['sessions_completed'] = len(week['session_details'])
        
        # Calculate new progress
        new_completed = session_number
        progress_percentage = (new_completed / total_sessions) * 100 if total_sessions > 0 else 0.0
        
        # Update the learning plan
        result = await learning_plans_collection.update_one(
            {"_id": learning_plan["_id"]},
            {
                "$set": {
                    "plan_content.weekly_schedule": weekly_schedule,
                    "completed_sessions": new_completed,
                    "progress_percentage": progress_percentage,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"[SESSION_SUMMARY] ✅ Session summary saved to Week {week_index + 1}, Session {session_in_week}")
            print(f"[SESSION_SUMMARY] ✅ Updated progress: {new_completed}/{total_sessions} sessions ({progress_percentage:.1f}%)")
            
            # CRITICAL FIX: Track subscription usage for practice sessions
            # This was the missing piece causing the "30/30" display issue!
            try:
                from subscription_service import SubscriptionService
                from models import UsageTrackingRequest
                
                usage_request = UsageTrackingRequest(
                    user_id=str(current_user.id),
                    usage_type="practice_session"
                )
                
                usage_tracked = await SubscriptionService.track_usage(usage_request)
                if usage_tracked:
                    print(f"[SESSION_SUMMARY] ✅ Tracked practice session usage for user {current_user.id}")
                    print(f"[SESSION_SUMMARY] ✅ Subscription usage counter incremented")
                else:
                    print(f"[SESSION_SUMMARY] ⚠️ Failed to track practice session usage (may have exceeded limit)")
                    
            except Exception as usage_error:
                print(f"[SESSION_SUMMARY] ⚠️ Warning: Failed to track subscription usage: {str(usage_error)}")
                # Don't fail the entire operation if usage tracking fails
                # The session summary is still saved successfully
            
            return {
                "success": True,
                "message": "Session summary saved successfully",
                "session_number": session_number,
                "week": week_index + 1,
                "session_in_week": session_in_week,
                "progress_percentage": progress_percentage
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save session summary"
            )
            
    except Exception as e:
        logger.error(f"Error saving session summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving session summary: {str(e)}"
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
        
        # IMPORTANT: Track assessment usage for subscription limits
        # This ensures the assessment counter is properly updated
        try:
            usage_result = await users_collection.update_one(
                {"_id": user_id},
                {"$inc": {"assessments_used": 1}}
            )
            print(f"✅ Incremented assessments_used counter for user {user_id} (modified count: {usage_result.modified_count})")
        except Exception as e:
            print(f"⚠️ Warning: Failed to track assessment usage: {str(e)}")
            # Don't fail the entire operation if usage tracking fails
        
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
