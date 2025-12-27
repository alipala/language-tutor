from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
import os
import openai
import uuid
import logging
import json
from datetime import datetime
from bson import ObjectId
from auth import get_current_user
from models import UserResponse
from database import database, users_collection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/learning", tags=["learning"])

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
    # NEW: Final Assessment Fields
    status: Optional[str] = "in_progress"  # "in_progress" | "awaiting_final_assessment" | "completed" | "failed_assessment"
    final_assessment: Optional[Dict[str, Any]] = None  # Assessment requirements and attempts
    all_sessions_completed_at: Optional[str] = None  # When last session was completed

# Initialize learning goals collection
learning_goals_collection = database.learning_goals
learning_plans_collection = database.learning_plans

# Import new intelligent modules
try:
    from enriched_goals_config import (
        get_all_main_goals,
        get_sub_goals_for_main_goal,
        ENRICHED_GOALS
    )
    from intelligent_schedule_generator import IntelligentScheduleGenerator
    INTELLIGENT_SYSTEM_AVAILABLE = True
    logger.info("[LEARNING_ROUTES] ✅ Intelligent system modules loaded successfully")
except ImportError as e:
    INTELLIGENT_SYSTEM_AVAILABLE = False
    logger.warning(f"[LEARNING_ROUTES] ⚠️ Intelligent system not available: {str(e)}")
    logger.warning("[LEARNING_ROUTES] ⚠️ Falling back to legacy system")

# Predefined learning goals (legacy - kept for backward compatibility)
PREDEFINED_GOALS = [
    {"id": "travel", "text": "Travel and tourism", "category": "general"},
    {"id": "business", "text": "Business and professional communication", "category": "general"},
    {"id": "academic", "text": "Academic study", "category": "general"},
    {"id": "culture", "text": "Cultural understanding", "category": "general"},
    {"id": "daily", "text": "Daily conversation", "category": "general"}
]

@router.get("/goals", response_model=List[Dict[str, Any]])
async def get_learning_goals(
    enriched: bool = False
):
    """
    Get a list of learning goals
    
    Args:
        enriched: If True, return enriched goals with sub-goals. If False, return legacy format.
    """
    try:
        # If enriched goals requested and intelligent system available
        if enriched and INTELLIGENT_SYSTEM_AVAILABLE:
            logger.info("[LEARNING_ROUTES] 📊 Returning enriched goals")
            enriched_goals = get_all_main_goals()
            return enriched_goals
        else:
            # Return legacy format - DON'T insert to database, just return
            logger.info("[LEARNING_ROUTES] 📊 Returning legacy goals")
            # 🔥 FIX: Don't insert to database to avoid ObjectId serialization issues
            # Just return the predefined goals directly
            return PREDEFINED_GOALS
    
    except Exception as e:
        logger.error(f"[LEARNING_ROUTES] ❌ Error fetching goals: {str(e)}")
        # Fallback to legacy goals
        return PREDEFINED_GOALS

@router.get("/goals/{goal_id}/sub-goals")
async def get_sub_goals(goal_id: str):
    """
    Get sub-goals for a specific main goal
    
    Args:
        goal_id: Main goal identifier (e.g., "travel", "business")
        
    Returns:
        List of sub-goals with descriptions
    """
    try:
        if not INTELLIGENT_SYSTEM_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Enriched goals system not available"
            )
        
        logger.info(f"[LEARNING_ROUTES] 📊 Fetching sub-goals for: {goal_id}")
        sub_goals = get_sub_goals_for_main_goal(goal_id)
        
        if not sub_goals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No sub-goals found for goal: {goal_id}"
            )
        
        return sub_goals
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LEARNING_ROUTES] ❌ Error fetching sub-goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sub-goals: {str(e)}"
        )

@router.post("/plan", response_model=LearningPlan)
async def create_learning_plan(
    request_data: dict,  # 🔥 CRITICAL FIX: Accept raw dict first for flexible validation
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a custom learning plan based on user's proficiency level, goals, and duration.
    Authentication is required for assessment data processing.
    🔥 FIXED: Now handles missing required fields and different request formats gracefully
    """
    
    # 🔥 CRITICAL FIX: Debug logging to see exactly what frontend sends
    print(f"[LEARNING_PLAN_DEBUG] 🔍 Raw request data received:")
    print(f"[LEARNING_PLAN_DEBUG] {json.dumps(request_data, indent=2, default=str)}")
    
    # STEP 1: Handle different request formats that frontend might send
    plan_request_data = None
    
    # Check if request is wrapped in 'plan_request' or 'planRequest'
    if 'plan_request' in request_data:
        plan_request_data = request_data['plan_request']
        print(f"[LEARNING_PLAN_DEBUG] ✅ Found wrapped request in 'plan_request'")
    elif 'planRequest' in request_data:
        plan_request_data = request_data['planRequest']
        print(f"[LEARNING_PLAN_DEBUG] ✅ Found wrapped request in 'planRequest'")
    else:
        plan_request_data = request_data.copy()
        print(f"[LEARNING_PLAN_DEBUG] ✅ Using direct request data")
    
    # STEP 2: Handle assessment_data that might be at root level
    if 'assessment_data' in request_data and 'assessment_data' not in plan_request_data:
        plan_request_data['assessment_data'] = request_data['assessment_data']
        print(f"[LEARNING_PLAN_DEBUG] ✅ Moved assessment_data from root to plan_request_data")
    
    # STEP 3: 🔥 CRITICAL FIX: Fill in missing required fields with smart defaults
    
    # Language: Default to english if missing
    if 'language' not in plan_request_data or not plan_request_data['language']:
        plan_request_data['language'] = 'english'
        print(f"[LEARNING_PLAN_DEBUG] ✅ Added default language: english")
    
    # Proficiency Level: Try to get from assessment, otherwise default to B1
    if 'proficiency_level' not in plan_request_data or not plan_request_data['proficiency_level']:
        assessment_data = plan_request_data.get('assessment_data', {})
        recommended_level = assessment_data.get('recommended_level')
        
        if recommended_level:
            plan_request_data['proficiency_level'] = recommended_level
            print(f"[LEARNING_PLAN_DEBUG] ✅ Set proficiency_level from assessment: {recommended_level}")
        else:
            plan_request_data['proficiency_level'] = 'B1'
            print(f"[LEARNING_PLAN_DEBUG] ✅ Added default proficiency_level: B1")
    
    # Goals: Default to common learning goals if missing
    if 'goals' not in plan_request_data or not plan_request_data['goals']:
        plan_request_data['goals'] = ['daily', 'travel']
        print(f"[LEARNING_PLAN_DEBUG] ✅ Added default goals: ['daily', 'travel']")
    
    # Duration: Default to 3 months if missing
    if 'duration_months' not in plan_request_data or not plan_request_data['duration_months']:
        plan_request_data['duration_months'] = 3
        print(f"[LEARNING_PLAN_DEBUG] ✅ Added default duration_months: 3")
    
    # STEP 4: Validate the corrected request
    try:
        plan_request = LearningPlanRequest(**plan_request_data)
        print(f"[LEARNING_PLAN_DEBUG] ✅ Request validation successful after fixes")
        print(f"[LEARNING_PLAN_DEBUG] Final request: language={plan_request.language}, level={plan_request.proficiency_level}, goals={plan_request.goals}, duration={plan_request.duration_months}")
    except ValidationError as e:
        print(f"[LEARNING_PLAN_DEBUG] ❌ Request validation still failed after fixes: {e}")
        print(f"[LEARNING_PLAN_DEBUG] Final plan_request_data: {plan_request_data}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid plan request format after applying fixes: {str(e)}. Please ensure all required fields are provided."
        )
    
    print(f"[LEARNING_PLAN_DEBUG] 🎯 Proceeding with plan creation...")
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
                
                # CRITICAL FIX: Initialize session_details array properly
                session_details = []
                sessions_per_week = 2  # Default 2 sessions per week
                
                # Create placeholder session objects for each session in the week
                for session_idx in range(sessions_per_week):
                    session_details.append({
                        "session_number": session_idx + 1,
                        "focus": focus,
                        "completed_at": None,
                        "duration_minutes": None,
                        "session_summary": None,
                        "status": "pending"
                    })
                
                weekly_schedule.append({
                    "week": week,
                    "focus": focus,
                    "activities": activities,
                    "sessions_completed": 0,
                    "total_sessions": sessions_per_week,
                    "session_details": session_details  # CRITICAL: Properly initialized session_details
                })
            
            return weekly_schedule
        
        # 🔥 NEW: Use intelligent schedule generator if available
        if INTELLIGENT_SYSTEM_AVAILABLE:
            try:
                logger.info("[LEARNING_PLAN] 🎯 Using intelligent schedule generator")
                
                # Extract sub_goals from request if provided
                sub_goals = request_data.get('sub_goals', [])
                
                weekly_schedule = IntelligentScheduleGenerator.generate_optimized_schedule(
                    duration_months=plan_request.duration_months,
                    assessment_data=assessment_data,
                    goals=plan_request.goals,
                    language=plan_request.language,
                    sub_goals=sub_goals if sub_goals else None
                )
                
                logger.info(f"[LEARNING_PLAN] ✅ Intelligent schedule generated: {len(weekly_schedule)} weeks")
            except Exception as e:
                logger.warning(f"[LEARNING_PLAN] ⚠️ Intelligent generator failed: {str(e)}")
                logger.info("[LEARNING_PLAN] 📋 Falling back to legacy generator")
                # Fallback to legacy generator
                weekly_schedule = generate_weekly_schedule(
                    plan_request.duration_months, 
                    areas_for_improvement, 
                    strengths, 
                    next_steps,
                    plan_request.language,
                    recommended_level
                )
        else:
            # Use legacy generator
            logger.info("[LEARNING_PLAN] 📋 Using legacy schedule generator")
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
        
        # Import the new learning plan service
        from learning_plan_service import LearningPlanService
        
        # Ensure proper session structure
        weekly_schedule = LearningPlanService.ensure_session_structure(weekly_schedule)
        
        # Calculate total sessions from the generated weekly schedule
        total_sessions = LearningPlanService.calculate_total_sessions_from_schedule(weekly_schedule)
        
        print(f"[LEARNING_PLAN] ✅ Generated weekly schedule:")
        print(f"[LEARNING_PLAN]    Total weeks: {len(weekly_schedule)}")
        print(f"[LEARNING_PLAN]    Total sessions: {total_sessions}")
        print(f"[LEARNING_PLAN]    Sessions per week: 2")
        
        # Create a new learning plan with safe creation
        new_plan = {
            # Note: id will be generated by the service
            "user_id": str(current_user.id) if current_user else None,
            "language": plan_request.language,
            "proficiency_level": plan_request.proficiency_level,
            "goals": plan_request.goals,
            "duration_months": plan_request.duration_months,
            "custom_goal": plan_request.custom_goal,
            "plan_content": plan_content_json,
            "assessment_data": plan_request.assessment_data,
            "total_sessions": total_sessions,
            "completed_sessions": 0,
            "progress_percentage": 0.0,
            "practice_minutes_used": 0.0,
            "total_practice_minutes": total_sessions * 5.0  # Assume 5 minutes per session average
        }
        
        # ATOMIC SAVE: Use the safe learning plan service with duplicate prevention
        if current_user and plan_request.assessment_data:
            print(f"[ATOMIC_SAVE] 🔄 Starting atomic save of assessment + learning plan")
            print(f"[ATOMIC_SAVE] User: {current_user.id}, Language: {plan_request.language}, Level: {plan_request.proficiency_level}")
            
            # 🔥 CRITICAL FIX: Assessment limits are now checked BEFORE assessment starts in /api/speaking/assess
            # No need to check limits here since the assessment was already completed and limits were validated
            print(f"[ATOMIC_SAVE] ℹ️ Assessment limits already validated during assessment creation")
            
            # STEP 1: Save the learning plan first using safe creation
            created_plan = await LearningPlanService.create_learning_plan_safe(new_plan)
            
            print(f"[ATOMIC_SAVE] ✅ Learning plan created with ID: {created_plan['id']}")
            
            # STEP 2: 🔥 BULLETPROOF IDEMPOTENT ASSESSMENT SAVE - Prevent Double Increments
            try:
                # Generate assessment fingerprint BEFORE any database operations
                # This fingerprint is based on user + language + level, NOT plan ID
                assessment_fingerprint = f"{current_user.id}_{plan_request.language}_{plan_request.proficiency_level}"
                assessment_timestamp = datetime.utcnow().isoformat()
                
                print(f"[IDEMPOTENT_SAVE] 🔒 Checking for duplicate assessment: {assessment_fingerprint}")
                
                # Check if this assessment fingerprint was already processed
                user_doc = await users_collection.find_one({"_id": ObjectId(current_user.id)})
                existing_assessment_history = user_doc.get("assessment_history", {})
                
                # 🔥 CRITICAL FIX: Check fingerprint, not plan ID
                # This prevents double increment even on retries/duplicates
                if (existing_assessment_history and 
                    existing_assessment_history.get("assessment_fingerprint") == assessment_fingerprint):
                    print(f"[IDEMPOTENT_SAVE] ⚠️ Assessment already processed for {assessment_fingerprint}")
                    print(f"[IDEMPOTENT_SAVE] ✅ Returning existing plan without incrementing counter")
                    
                    # Return the existing plan linked to this assessment
                    existing_plan_id = existing_assessment_history.get("learning_plan_id")
                    if existing_plan_id:
                        existing_plan = await learning_plans_collection.find_one({"id": existing_plan_id})
                        if existing_plan:
                            print(f"[IDEMPOTENT_SAVE] ✅ Returning existing plan: {existing_plan_id}")
                            new_plan = existing_plan
                        else:
                            print(f"[IDEMPOTENT_SAVE] ⚠️ Existing plan not found, using newly created plan")
                            new_plan = created_plan
                    else:
                        print(f"[IDEMPOTENT_SAVE] ⚠️ No plan ID in history, using newly created plan")
                        new_plan = created_plan
                else:
                    # This is a new assessment - proceed with increment
                    print(f"[IDEMPOTENT_SAVE] ✅ New assessment detected - proceeding with increment")
                    
                    # Generate unique assessment ID for tracking
                    assessment_id = f"{assessment_fingerprint}_{assessment_timestamp}"
                    
                    # Prepare the update operations with bulletproof idempotency protection
                    update_operations = {
                        "$set": {
                            "last_assessment_data": plan_request.assessment_data,
                            "assessment_history": {
                                "assessment_fingerprint": assessment_fingerprint,  # 🔥 NEW: Use fingerprint
                                "assessment_id": assessment_id,
                                "timestamp": assessment_timestamp,
                                "data": plan_request.assessment_data,
                                "language": plan_request.language,
                                "level": plan_request.proficiency_level,
                                "learning_plan_id": created_plan['id']  # Link to the created plan
                            }
                        },
                        "$inc": {"assessments_used": 1}  # Increment counter atomically
                    }
                    
                    print(f"[IDEMPOTENT_SAVE] 🔥 BULLETPROOF FIX: Incrementing assessment counter with fingerprint protection")
                    print(f"[IDEMPOTENT_SAVE] 📊 Assessment counter will be incremented for user {current_user.id}")
                    
                    # 🔥 CRITICAL: Execute atomic update with fingerprint-based conditional check
                    # This ensures only ONE increment happens even with retries/duplicates
                    update_result = await users_collection.update_one(
                        {
                            "_id": ObjectId(current_user.id),
                            # 🔥 BULLETPROOF: Ensure fingerprint doesn't already exist
                            "$or": [
                                {"assessment_history": {"$exists": False}},
                                {"assessment_history.assessment_fingerprint": {"$ne": assessment_fingerprint}}
                            ]
                        },
                        update_operations
                    )
                    
                    if update_result.modified_count > 0:
                        print(f"[IDEMPOTENT_SAVE] ✅ Assessment data saved to user profile")
                        print(f"[IDEMPOTENT_SAVE] ✅ Assessment counter incremented (bulletproof idempotent)")
                        print(f"[IDEMPOTENT_SAVE] 🎯 BULLETPROOF SAVE COMPLETE: Assessment + Plan saved together")
                    else:
                        print(f"[IDEMPOTENT_SAVE] ⚠️ User profile update had no changes - duplicate detected by fingerprint")
                        
                        # Double-check if this was due to duplicate protection
                        fresh_user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
                        fresh_history = fresh_user.get("assessment_history", {})
                        if fresh_history.get("assessment_fingerprint") == assessment_fingerprint:
                            print(f"[IDEMPOTENT_SAVE] ✅ Bulletproof duplicate protection worked - assessment already exists")
                            
                            # Return the existing plan instead of creating a duplicate
                            existing_plan_id = fresh_history.get("learning_plan_id")
                            if existing_plan_id:
                                existing_plan = await learning_plans_collection.find_one({"id": existing_plan_id})
                                if existing_plan:
                                    print(f"[IDEMPOTENT_SAVE] ✅ Returning existing plan from duplicate check: {existing_plan_id}")
                                    new_plan = existing_plan
                                    # Don't return here, let it fall through to the return statement
                                else:
                                    new_plan = created_plan
                            else:
                                new_plan = created_plan
                        else:
                            print(f"[IDEMPOTENT_SAVE] ❌ Unexpected update failure - fingerprint mismatch")
                            new_plan = created_plan
                    
                    # Update new_plan with the created plan data for return
                    if update_result.modified_count > 0:
                        new_plan = created_plan
                    
            except Exception as e:
                print(f"[ATOMIC_SAVE] ⚠️ Warning: Failed to save assessment data: {str(e)}")
                # The learning plan was already created, so we don't fail the operation
                # But log this for monitoring
                print(f"[ATOMIC_SAVE] ⚠️ Learning plan created but assessment data not saved")
                new_plan = created_plan  # Still return the created plan
        else:
            # No assessment data - just save the plan normally using safe creation
            created_plan = await LearningPlanService.create_learning_plan_safe(new_plan)
            new_plan = created_plan
            print(f"[LEARNING_PLAN] ✅ Learning plan created without assessment data")
        
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

class SessionSummaryRequest(BaseModel):
    """Model for session summary with optional duration and batch analysis"""
    messages: Optional[List[Dict[str, Any]]] = []
    duration_minutes: Optional[float] = 0.0
    language: Optional[str] = None
    level: Optional[str] = None
    topic: Optional[str] = None
    sentences_for_analysis: Optional[List[Dict[str, Any]]] = []  # 🔥 NEW: Batch analysis support

# 🔥 REFACTORED: This endpoint moved to routes/session_summary_routes.py with LearningPlanOptimizer integration
# @router.post("/session-summary")
async def save_session_summary_OLD_DEPRECATED(
    plan_id: str,
    session_summary: str,
    request: Optional[SessionSummaryRequest] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    DEPRECATED: Moved to routes/session_summary_routes.py with LearningPlanOptimizer integration

    Save a session summary to the correct week in the learning plan structure
    Also tracks speaking minutes for the learning plan
    UNIFIED TRACKING: Ensures both learning plan and subscription usage are tracked
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
        
        # BULLETPROOF FIX: Ensure INTEGER tracking for all sessions
        if request and request.duration_minutes:
            # Convert to float first to handle any input type
            raw_duration = float(request.duration_minutes)
            
            # BULLETPROOF INTEGER ENFORCEMENT
            # 1. Cap at 5 minutes maximum (frontend counter issue protection)
            if raw_duration > 5:
                duration_minutes = 5
                print(f"[SESSION_SUMMARY] ⚠️ Capping duration from {raw_duration} to 5 minutes (max allowed)")
            else:
                # 2. Round to nearest integer
                duration_minutes = round(raw_duration)
                if duration_minutes != raw_duration:
                    print(f"[SESSION_SUMMARY] 🔄 Converted float {raw_duration} to integer {duration_minutes}")
            
            # 3. Minimum 1 minute for any session
            if duration_minutes < 1:
                duration_minutes = 1
                print(f"[SESSION_SUMMARY] ⚠️ Setting minimum duration to 1 minute")
            
            # 4. Ensure it's an integer
            duration_minutes = int(duration_minutes)
            
            # Determine session status based on integer duration
            if duration_minutes >= 5:
                session_status = "completed"
                print(f"[SESSION_SUMMARY] ✅ Complete session: {duration_minutes} minutes (INTEGER)")
            else:
                session_status = "partial"
                print(f"[SESSION_SUMMARY] ⏰ Partial session: {duration_minutes} minutes (INTEGER)")
        else:
            # Default: 5 minutes for a complete session (INTEGER)
            duration_minutes = 5
            session_status = "completed"
            print(f"[SESSION_SUMMARY] 🕐 Default complete session: {duration_minutes} minutes (INTEGER)")
        
        # Add completion timestamp for subscription period tracking
        completion_timestamp = datetime.utcnow()
        
        # Create session detail object
        session_detail = {
            "session_number": session_in_week,
            "global_session_number": session_number,
            "summary": session_summary,
            "completed_at": completion_timestamp.isoformat(),
            "status": session_status,
            "duration_minutes": duration_minutes,
            "subscription_tracked": False  # Will be set to True after tracking
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
        
        # 🔥 CRITICAL FIX: Call the fixed /api/stripe/track-speaking-time endpoint
        # This ensures learning plan sessions use the same fixed minute deduction logic
        subscription_tracked = False
        session_counted = False
        
        try:
            from models import SpeakingTimeTrackingRequest
            from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker
            
            print(f"[SESSION_SUMMARY] 🔥 CRITICAL FIX: Using fixed bulletproof tracking system...")
            
            # Generate session ID for learning plan session
            import uuid
            learning_plan_session_id = f"learning_plan_{plan_id}_{session_number}_{uuid.uuid4()}"
            
            # Create tracking request (same as /api/stripe/track-speaking-time endpoint)
            tracking_request = SpeakingTimeTrackingRequest(
                user_id=str(current_user.id),
                session_id=learning_plan_session_id,
                speaking_minutes=duration_minutes,
                session_completed=duration_minutes >= 2  # Same business rules as practice sessions
            )
            
            print(f"[SESSION_SUMMARY] 📋 Tracking request:")
            print(f"[SESSION_SUMMARY]    User: {current_user.id}")
            print(f"[SESSION_SUMMARY]    Session ID: {learning_plan_session_id}")
            print(f"[SESSION_SUMMARY]    Duration: {duration_minutes} minutes")
            print(f"[SESSION_SUMMARY]    Completed: {tracking_request.session_completed}")
            
            # Use the SAME bulletproof tracking system as /api/stripe/track-speaking-time
            tracking_success = await BulletproofTracker.track_speaking_time_atomic(tracking_request)
            
            if tracking_success:
                subscription_tracked = True
                session_counted = tracking_request.session_completed
                print(f"[SESSION_SUMMARY] ✅ BULLETPROOF TRACKING successful:")
                print(f"[SESSION_SUMMARY]    User: {getattr(current_user, 'email', current_user.id)}")
                print(f"[SESSION_SUMMARY]    Duration tracked: {duration_minutes} minutes")
                print(f"[SESSION_SUMMARY]    Session complete: {session_counted}")
                print(f"[SESSION_SUMMARY]    Using SAME system as practice sessions!")
                
                session_detail["subscription_tracked"] = True
                session_detail["session_counted"] = session_counted
            else:
                print(f"[SESSION_SUMMARY] ❌ BULLETPROOF TRACKING failed - insufficient balance or limits exceeded")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subscription limit exceeded - not enough minutes remaining"
                )
                
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as usage_error:
            print(f"[SESSION_SUMMARY] ❌ BULLETPROOF TRACKING error: {str(usage_error)}")
            import traceback
            traceback.print_exc()
            
            # CRITICAL: If subscription tracking fails, abort the entire operation
            # This ensures consistency between learning plan and subscription tracking
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to track session: {str(usage_error)}"
            )
        
        # Update the learning plan
        update_fields = {
            "plan_content.weekly_schedule": weekly_schedule,
            "completed_sessions": new_completed,
            "progress_percentage": progress_percentage,
            "practice_minutes_used": new_minutes_used,
            "updated_at": datetime.utcnow().isoformat(),
            "last_subscription_sync": completion_timestamp.isoformat() if subscription_tracked else None
        }
        
        print(f"[SESSION_SUMMARY] 📊 Learning plan update:")
        print(f"[SESSION_SUMMARY]    Sessions: {current_completed} → {new_completed}")
        print(f"[SESSION_SUMMARY]    Minutes: {current_minutes_used} → {new_minutes_used}")
        print(f"[SESSION_SUMMARY]    Progress: {progress_percentage:.1f}%")
        print(f"[SESSION_SUMMARY]    Subscription tracked: {subscription_tracked}")
        
        result = await learning_plans_collection.update_one(
            {"_id": learning_plan["_id"]},
            {"$set": update_fields}
        )
        
        # 🔥 INTEGRATE FLASHCARD GENERATION: Generate flashcards after session completion
        flashcard_generation_success = False
        generated_flashcards = 0

        try:
            from flashcard_service import FlashcardService
            from models import FlashcardGenerationRequest

            # 🔥 CRITICAL FIX: Use the learning_plan_session_id so frontend can filter properly
            # Frontend filter checks: set.session_id.startsWith('learning_plan_')
            # This ensures flashcards appear in the "Learning Plans" filter
            flashcard_request = FlashcardGenerationRequest(
                session_id=learning_plan_session_id,  # Use the proper learning_plan session ID!
                language=learning_plan.get("language", "english"),
                level=learning_plan.get("proficiency_level", "B1"),
                topic=request.topic if request and request.topic else None,
                conversation_content=None,  # Could be added later if conversation data is available
                session_summary=session_summary,
                count=5  # Generate 5 flashcards per session
            )

            print(f"[FLASHCARD_INTEGRATION] 🎯 Generating flashcards for learning plan session: {learning_plan_session_id}")
            print(f"[FLASHCARD_INTEGRATION] Language: {flashcard_request.language}, Level: {flashcard_request.level}")

            # Generate flashcards
            flashcard_set = await FlashcardService.generate_flashcards(flashcard_request, str(current_user.id))

            if flashcard_set and flashcard_set.flashcards:
                # 🔥 CRITICAL FIX: Save flashcards to database (they were being generated but not saved!)
                from bson import ObjectId
                
                # Save flashcard set to database
                flashcard_set_doc = flashcard_set.dict()
                flashcard_set_doc["_id"] = ObjectId()
                flashcard_set_doc["created_at"] = datetime.utcnow()
                
                # Save individual flashcards
                flashcard_docs = []
                for flashcard in flashcard_set.flashcards:
                    card_doc = flashcard.dict()
                    card_doc["_id"] = ObjectId()
                    flashcard_docs.append(card_doc)
                
                # Insert flashcard set
                flashcard_sets_collection = database.flashcard_sets
                set_result = await flashcard_sets_collection.insert_one(flashcard_set_doc)
                
                # Insert individual flashcards
                if flashcard_docs:
                    flashcards_collection = database.flashcards
                    cards_result = await flashcards_collection.insert_many(flashcard_docs)
                    print(f"[FLASHCARD_INTEGRATION] 💾 Saved {len(cards_result.inserted_ids)} flashcards to database")
                
                generated_flashcards = len(flashcard_set.flashcards)
                flashcard_generation_success = True
                print(f"[FLASHCARD_INTEGRATION] ✅ Generated and saved {generated_flashcards} flashcards successfully")
            else:
                print(f"[FLASHCARD_INTEGRATION] ⚠️ Flashcard generation returned empty result")

        except Exception as flashcard_error:
            print(f"[FLASHCARD_INTEGRATION] ❌ Flashcard generation failed: {str(flashcard_error)}")
            # Don't fail the session save if flashcard generation fails
            flashcard_generation_success = False
            generated_flashcards = 0

        # 🔥 NEW: Process batch sentence analysis if sentences were provided
        background_analyses = []
        if request and request.sentences_for_analysis and len(request.sentences_for_analysis) > 0:
            try:
                from background_sentence_analysis import batch_analyze_sentences
                
                print(f"[BATCH_ANALYSIS] 📊 Processing {len(request.sentences_for_analysis)} sentences for learning plan session")
                
                # Extract sentence texts from the request
                sentence_texts = [s.get('text', '') for s in request.sentences_for_analysis if s.get('text')]
                
                if sentence_texts:
                    # Use the same batch analysis system as practice sessions
                    analyses = await batch_analyze_sentences(
                        sentences=sentence_texts,
                        language=learning_plan.get("language", "english"),
                        level=learning_plan.get("proficiency_level", "B1")
                    )
                    
                    background_analyses = analyses
                    print(f"[BATCH_ANALYSIS] ✅ Generated {len(background_analyses)} analyses for learning plan session")
                else:
                    print(f"[BATCH_ANALYSIS] ⚠️ No valid sentence texts found in request")
                    
            except Exception as analysis_error:
                print(f"[BATCH_ANALYSIS] ❌ Batch analysis failed: {str(analysis_error)}")
                # Don't fail the session save if analysis fails
                background_analyses = []
        
        if result.modified_count > 0:
            print(f"[SESSION_SUMMARY] ✅ Learning plan updated successfully")
            print(f"[SESSION_SUMMARY] 🎉 Session summary saved with UNIFIED TRACKING!")
            return {
                "success": True,
                "message": "Session summary saved successfully",
                "session_number": session_number,
                "week": week_index + 1,
                "session_in_week": session_in_week,
                "progress_percentage": progress_percentage,
                "duration_minutes": duration_minutes,
                "subscription_tracked": subscription_tracked,
                "flashcards_generated": generated_flashcards,
                "flashcard_generation_success": flashcard_generation_success,
                "background_analyses": background_analyses  # 🔥 NEW: Return analyses to frontend
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
        )@router.post("/save-assessment", response_model=UserResponse)
async def save_assessment_data(
    assessment: SpeakingAssessmentData,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    DEPRECATED: This endpoint should not be used anymore.
    Assessment data should only be saved when a learning plan is created.
    
    This endpoint is kept for backward compatibility but will NOT:
    - Save assessment data to user profile
    - Increment assessment counter
    
    Instead, assessments are saved atomically with learning plan creation.
    """
    print(f"[DEPRECATED] ⚠️ save-assessment endpoint called - this should not be used")
    print(f"[DEPRECATED] Assessment data should be included when creating a learning plan")
    print(f"[DEPRECATED] User: {current_user.id}")
    
    # Import ObjectId for proper MongoDB ID handling
    from bson import ObjectId
    
    # Convert user ID to the correct format for MongoDB
    user_id = current_user.id
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception as e:
            print(f"Warning: Could not convert user ID to ObjectId: {str(e)}")
    
    # Get the user data without modifying it
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        # Try alternate formats as fallback
        user = await users_collection.find_one({"_id": str(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found with ID {user_id}")
    
    # DO NOT SAVE ASSESSMENT DATA OR INCREMENT COUNTER
    # This is now handled atomically with learning plan creation
    
    print(f"[DEPRECATED] ℹ️ Returning user data without saving assessment")
    print(f"[DEPRECATED] ℹ️ Assessment will only be saved when learning plan is created")
    
    # Return the user data without modifications
    user_data = dict(user)
    
    # Ensure _id is properly set for UserResponse
    if "_id" in user_data:
        user_data["_id"] = str(user_data["_id"])
    else:
        raise HTTPException(
            status_code=500,
            detail="User document is missing _id field"
        )
    
    try:
        return UserResponse(**user_data)
    except Exception as e:
        print(f"Error creating UserResponse: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user response object: {str(e)}"
        )
