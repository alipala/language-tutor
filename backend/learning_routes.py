from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
import os
import uuid
import logging
import json
from datetime import datetime
from bson import ObjectId
from auth import get_current_user
from models import UserResponse
from database import database, users_collection
from openai_client import get_async_openai
from services.voice_check_service import voice_check_service

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
    from_final_assessment: Optional[bool] = None
    previous_plan_id: Optional[str] = None
    preferred_session_duration: Optional[int] = None  # Minutes per session chosen at plan creation (1, 3, or 5)

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
    updated_at: Optional[str] = None
    total_sessions: Optional[int] = None
    completed_sessions: Optional[int] = 0
    progress_percentage: Optional[float] = 0.0
    practice_minutes_used: Optional[float] = 0.0
    session_summaries: Optional[List[str]] = []
    status: Optional[str] = "in_progress"  # "in_progress" | "awaiting_final_assessment" | "completed" | "failed_assessment"
    final_assessment: Optional[Dict[str, Any]] = None
    all_sessions_completed_at: Optional[str] = None
    from_final_assessment: Optional[bool] = None
    previous_plan_id: Optional[str] = None
    preferred_session_duration: Optional[int] = None  # Minutes per session chosen at plan creation (1, 3, or 5)
    voice_check_schedule: Optional[List[int]] = None
    voice_checks_completed: Optional[List[int]] = None

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
    enriched: bool = False,
):
    """
    Get a list of learning goals.
    Goal text/descriptions are translated client-side via locale keys.
    """
    try:
        if enriched and INTELLIGENT_SYSTEM_AVAILABLE:
            logger.info("[LEARNING_ROUTES] 📊 Returning enriched goals")
            return get_all_main_goals()
        else:
            logger.info("[LEARNING_ROUTES] 📊 Returning legacy goals")
            return PREDEFINED_GOALS
    except Exception as e:
        logger.error(f"[LEARNING_ROUTES] ❌ Error fetching goals: {str(e)}")
        return PREDEFINED_GOALS


@router.get("/goals/{goal_id}/sub-goals")
async def get_sub_goals(goal_id: str):
    """
    Get sub-goals for a specific main goal.
    Sub-goal text/descriptions are translated client-side via locale keys.
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

    # RETRY FEATURE: Track assessment usage ONLY when user creates learning plan
    # This ensures users can retry assessments without consuming their quota
    if assessment_data:
        try:
            print(f"[ASSESSMENT_TRACKING] User created learning plan - tracking assessment usage for user {current_user.id}")

            from subscription_service import SubscriptionService
            from models import UsageTrackingRequest

            # Create usage tracking request
            usage_request = UsageTrackingRequest(
                user_id=current_user.id,
                usage_type="assessment",
                duration_minutes=None
            )

            # Track the usage
            success = await SubscriptionService.track_usage(usage_request)
            if success:
                print(f"[ASSESSMENT_TRACKING] Successfully tracked assessment usage for user {current_user.id}")
            else:
                print(f"[ASSESSMENT_TRACKING] Usage tracking returned false for user {current_user.id}")

        except Exception as tracking_error:
            print(f"[ASSESSMENT_TRACKING] Error tracking assessment usage: {str(tracking_error)}")
            # Don't fail the plan creation if usage tracking fails
            pass
    
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
                
                session_details = []
                sessions_per_week = 4  # 4 sessions per week
                
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
                "sessions_per_week": 4,
                "total_sessions": len(weekly_schedule) * 4,
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

    logger.info(
        f"Creating learning plan for: language={plan_request.language}, "
        f"level={plan_request.proficiency_level}, goals={goals_text}"
    )
    try:
        # ──────────────────────────────────────────────────────────────────────
        # GPT-4.1: Generate deeply personalised plan content
        # Uses function calling + strict mode (more reliable than json_schema on
        # gpt-4.1 per documented community reports).
        # Falls back to programmatic defaults on any failure so the plan is
        # always created successfully.
        # ──────────────────────────────────────────────────────────────────────
        openai_client = get_async_openai()
        if openai_client and assessment_data:
            logger.info("[LEARNING_PLAN] 🤖 Calling gpt-4.1 to generate personalised plan content")

            # ── Build rich context sections ──────────────────────────────────

            # 1. Skill scores with per-skill feedback (not just numbers)
            skill_details_lines = []
            for skill_key, label in [
                ("pronunciation", "Pronunciation"),
                ("grammar", "Grammar"),
                ("vocabulary", "Vocabulary"),
                ("fluency", "Fluency"),
                ("coherence", "Coherence"),
            ]:
                skill_obj = assessment_data.get(skill_key, {})
                score = skill_obj.get("score", 0) if isinstance(skill_obj, dict) else 0
                feedback = skill_obj.get("feedback", "") if isinstance(skill_obj, dict) else ""
                skill_details_lines.append(
                    f"  - {label}: {score}/100"
                    + (f" — {feedback}" if feedback else "")
                )
            skill_details_block = "\n".join(skill_details_lines)

            # 2. Sub-goals — full enriched config including level-specific activities,
            #    vocabulary, phrases, and skill priorities (cross-goal safe lookup)
            sub_goals = request_data.get("sub_goals", []) or []
            sub_goal_details_lines = []
            if sub_goals and INTELLIGENT_SYSTEM_AVAILABLE:
                try:
                    from enriched_goals_config import ENRICHED_GOALS as _EG, get_level_category as _get_lc
                    _level_cat = _get_lc(recommended_level)  # e.g. "A1-A2"

                    for sg_id in sub_goals:
                        sg_cfg = None
                        for _gid, _gdata in _EG.items():
                            if sg_id in _gdata.get("sub_goals", {}):
                                sg_cfg = _gdata["sub_goals"][sg_id]
                                break

                        if not sg_cfg:
                            sub_goal_details_lines.append(f"  [{sg_id}] (no config found)")
                            continue

                        # Level-appropriate activities (e.g. A1-A2 activities for an A1 learner)
                        level_activities = (
                            sg_cfg.get("level_focus", {}).get(_level_cat, [])
                            or sg_cfg.get("level_focus", {}).get("A1-A2", [])  # fallback
                        )
                        key_vocab = sg_cfg.get("key_vocabulary", [])
                        key_phrases = sg_cfg.get("key_phrases", [])
                        # Top skill priority for this sub-goal
                        skill_prios = sg_cfg.get("skill_priorities", {})
                        top_skill = (
                            max(skill_prios, key=skill_prios.get)
                            if skill_prios else "fluency"
                        )

                        lines = [
                            f"  [{sg_cfg.get('text', sg_id)}]",
                            f"    Goal: {sg_cfg.get('description', '')}",
                            f"    Level-specific activities ({_level_cat}):",
                        ]
                        for act in level_activities:
                            lines.append(f"      • {act}")
                        if key_vocab:
                            lines.append(f"    Key vocabulary: {', '.join(key_vocab)}")
                        if key_phrases:
                            lines.append(f"    Key phrases: {', '.join(key_phrases)}")
                        lines.append(f"    Primary skill focus: {top_skill}")
                        sub_goal_details_lines.extend(lines)

                except Exception as _eg_err:
                    logger.warning(f"[LEARNING_PLAN] Sub-goal enrichment failed: {_eg_err}")
                    sub_goal_details_lines = [f"  - {sg}" for sg in sub_goals]

            sub_goals_block = (
                "\n".join(sub_goal_details_lines)
                if sub_goal_details_lines
                else "  (not specified)"
            )

            # 3. DNA profile — learner archetype + growth areas
            dna_block = ""
            dna_profile = assessment_data.get("dna_profile", {})
            if dna_profile:
                overall_profile = dna_profile.get("overall_profile", {})
                dna_strands = dna_profile.get("dna_strands", {})
                archetype = overall_profile.get("speaker_archetype", "")
                growth_areas = overall_profile.get("growth_areas", [])
                coach_approach = overall_profile.get("coach_approach", "")

                rhythm = dna_strands.get("rhythm", {})
                confidence = dna_strands.get("confidence", {})
                learning_type = dna_strands.get("learning", {})
                emotional = dna_strands.get("emotional", {})

                dna_block = f"""
Speaking DNA Profile:
  - Archetype: {archetype}
  - Coach approach: {coach_approach}
  - Speaking rhythm: {rhythm.get('type', 'unknown')} — {rhythm.get('description', '')}
  - Confidence level: {confidence.get('level', 'unknown')} (score {confidence.get('score', 0):.0%}) — {confidence.get('description', '')}
  - Learning style: {learning_type.get('type', 'unknown')} — {learning_type.get('description', '')}
  - Emotional pattern: {emotional.get('pattern', 'unknown')} — {emotional.get('description', '')}
  - Key growth areas: {', '.join(growth_areas) if growth_areas else 'general improvement'}"""

            # 4. Session capacity context — tight 1-month plans need sharper priorities
            total_sessions_available = len(weekly_schedule)
            _capacity_advice = (
                "With limited sessions, prioritise the learner's weakest skills sharply."
                if total_sessions_available <= 10
                else "There is enough time for a balanced, progressive approach."
            )
            session_capacity_note = (
                f"This plan has {total_sessions_available} sessions total "
                f"({plan_request.duration_months} month(s) × 4 sessions/week). "
                f"{_capacity_advice}"
            )

            # 5. Weekly schedule summary (week focuses already generated)
            week_summary_lines = []
            for w in weekly_schedule[:8]:  # cap to avoid token bloat
                week_num = w.get("week", "?")
                focus = w.get("focus", "")
                week_summary_lines.append(f"  Week {week_num}: {focus}")
            week_summary_block = "\n".join(week_summary_lines)

            # ── Build the prompt ─────────────────────────────────────────────
            gpt_prompt = f"""You are an expert CEFR-certified language learning curriculum designer.
Create a deeply personalised learning plan for a real student.

=== STUDENT PROFILE ===
Language: {plan_request.language.capitalize()}
CEFR Level: {recommended_level}
Plan duration: {plan_request.duration_months} month(s)
Overall assessment score: {assessment_data.get('overall_score', 0)}/100

=== SKILL ASSESSMENT (scores + assessor feedback) ===
{skill_details_block}

=== LEARNER'S GOALS ===
Main goals: {goals_text}
Specific focus topics:
{sub_goals_block}

=== STRENGTHS ===
{chr(10).join(f'  - {s}' for s in strengths) if strengths else '  - Basic communication'}

=== AREAS FOR IMPROVEMENT ===
{chr(10).join(f'  - {a}' for a in areas_for_improvement) if areas_for_improvement else '  - Overall improvement'}

=== NEXT STEPS (from assessment) ===
{chr(10).join(f'  - {n}' for n in next_steps) if next_steps else '  - Continue practising'}
{dna_block}

=== SESSION CAPACITY ===
{session_capacity_note}

=== GENERATED WEEKLY SCHEDULE (already fixed — do NOT change) ===
{week_summary_block}

=== YOUR TASK ===
Using ALL the information above, provide:

1. overview (2-3 sentences, {recommended_level}-level vocabulary):
   - Address the learner by their strengths directly
   - Explain how this SPECIFIC plan targets their EXACT weak areas
   - Mention their focus topics ({', '.join(sub_goals) if sub_goals else goals_text})
   - Reference their DNA (e.g., "as a thoughtful pacer…") if available
   - Write as if speaking to the learner (second person "you")

2. learning_objectives (exactly 5, laser-focused):
   - Each objective must map directly to a specific skill gap shown above
   - Use CEFR {recommended_level} language complexity in the objective text itself
   - Reference the focus topics and sub-goals where relevant
   - Be concrete and measurable, not generic (avoid "improve overall skills")

3. resources (exactly 5, {plan_request.language}-specific for {recommended_level} level):
   - Real resource types (apps, books, podcasts, YouTube channels)
   - Tailored to {plan_request.language} learners at {recommended_level}
   - Match the learner's focus topics ({', '.join(sub_goals) if sub_goals else goals_text})
"""

            # ── Function schema for strict structured output ─────────────────
            plan_content_function = {
                "name": "set_plan_content",
                "description": "Set the personalised overview, objectives and resources for the learning plan.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "overview": {
                            "type": "string",
                            "description": "2-3 sentence personalised plan overview addressing the learner directly."
                        },
                        "learning_objectives": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exactly 5 specific, measurable learning objectives.",
                            "minItems": 5,
                            "maxItems": 5
                        },
                        "resources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exactly 5 language-specific resources.",
                            "minItems": 5,
                            "maxItems": 5
                        }
                    },
                    "required": ["overview", "learning_objectives", "resources"],
                    "additionalProperties": False
                }
            }

            try:
                gpt_response = await get_async_openai().chat.completions.create(
                    model="gpt-4.1",
                    tools=[{"type": "function", "function": plan_content_function}],
                    tool_choice={"type": "function", "function": {"name": "set_plan_content"}},
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert CEFR-certified language learning curriculum "
                                "designer. Your task is to produce concise, deeply personalised "
                                "plan content based on a real speaking assessment. Be specific, "
                                "encouraging, and always reference the learner's actual data."
                            )
                        },
                        {"role": "user", "content": gpt_prompt}
                    ],
                    temperature=0.6,
                    max_tokens=1200
                )

                # Extract function call arguments (strict mode guarantees valid JSON)
                tool_call = gpt_response.choices[0].message.tool_calls[0]
                gpt_content = json.loads(tool_call.function.arguments)
                logger.info("[LEARNING_PLAN] ✅ gpt-4.1 generated personalised content via function call")

                # Validate minimum field lengths before accepting
                raw_objectives = gpt_content.get("learning_objectives", [])
                raw_resources = gpt_content.get("resources", [])
                if (
                    gpt_content.get("overview")
                    and len(raw_objectives) >= 3
                    and len(raw_resources) >= 3
                ):
                    plan_content_json["overview"] = gpt_content["overview"]
                    plan_content_json["learning_objectives"] = raw_objectives
                    plan_content_json["resources"] = raw_resources
                    logger.info(
                        f"[LEARNING_PLAN] Applied gpt-4.1 content: "
                        f"{len(raw_objectives)} objectives, {len(raw_resources)} resources"
                    )
                else:
                    logger.warning(
                        "[LEARNING_PLAN] ⚠️ gpt-4.1 returned incomplete fields — "
                        "keeping programmatic defaults"
                    )

            except json.JSONDecodeError as json_err:
                logger.warning(
                    f"[LEARNING_PLAN] ⚠️ Could not parse gpt-4.1 function arguments: {json_err} "
                    "— keeping programmatic defaults"
                )
            except (IndexError, AttributeError, KeyError) as struct_err:
                logger.warning(
                    f"[LEARNING_PLAN] ⚠️ Unexpected gpt-4.1 response structure: {struct_err} "
                    "— keeping programmatic defaults"
                )
            except Exception as gpt_error:
                logger.warning(
                    f"[LEARNING_PLAN] ⚠️ gpt-4.1 call failed: {gpt_error} "
                    "— keeping programmatic defaults"
                )
        else:
            if not assessment_data:
                logger.info("[LEARNING_PLAN] ℹ️ No assessment data — using template content")
            else:
                logger.warning("[LEARNING_PLAN] ⚠️ OpenAI client unavailable — using template content")

        # Import the new learning plan service
        from learning_plan_service import LearningPlanService

        # Extract weekly_schedule from plan_content_json
        weekly_schedule = plan_content_json.get("weekly_schedule", [])

        # Ensure proper session structure
        weekly_schedule = LearningPlanService.ensure_session_structure(weekly_schedule)

        # Update the plan_content_json with structured schedule
        plan_content_json["weekly_schedule"] = weekly_schedule

        # Calculate total sessions from the generated weekly schedule
        total_sessions = LearningPlanService.calculate_total_sessions_from_schedule(weekly_schedule)
        
        print(f"[LEARNING_PLAN] ✅ Generated weekly schedule:")
        print(f"[LEARNING_PLAN]    Total weeks: {len(weekly_schedule)}")
        print(f"[LEARNING_PLAN]    Total sessions: {total_sessions}")
        print(f"[LEARNING_PLAN]    Sessions per week: 4")

        # Calculate voice check schedule for Speaking DNA acoustic analysis
        voice_check_schedule = voice_check_service.calculate_voice_check_schedule(plan_request.duration_months)

        print(f"[LEARNING_PLAN] 🎙️ Voice check schedule calculated:")
        print(f"[LEARNING_PLAN]    Duration: {plan_request.duration_months} months")
        print(f"[LEARNING_PLAN]    Voice checks scheduled at sessions: {voice_check_schedule}")

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
            "total_practice_minutes": total_sessions * 5.0,  # Assume 5 minutes per session average
            "from_final_assessment": plan_request.from_final_assessment if plan_request.from_final_assessment else None,
            "previous_plan_id": plan_request.previous_plan_id if plan_request.previous_plan_id else None,
            # Voice check fields for Speaking DNA acoustic analysis (premium feature)
            "preferred_session_duration": plan_request.preferred_session_duration,
            "voice_check_schedule": voice_check_schedule,
            "voice_checks_completed": []
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
                    # Save assessment data for plan personalization — counter already incremented by /api/speaking/assess
                    print(f"[IDEMPOTENT_SAVE] ✅ New assessment data detected - saving for plan personalization")
                    print(f"[IDEMPOTENT_SAVE] ℹ️ assessments_used counter NOT incremented here (already tracked by /api/speaking/assess)")

                    # Generate unique assessment ID for tracking
                    assessment_id = f"{assessment_fingerprint}_{assessment_timestamp}"

                    # Save assessment data only — do NOT increment assessments_used (already done by assessment endpoint)
                    update_operations = {
                        "$set": {
                            "last_assessment_data": plan_request.assessment_data,
                            "assessment_history": {
                                "assessment_fingerprint": assessment_fingerprint,
                                "assessment_id": assessment_id,
                                "timestamp": assessment_timestamp,
                                "data": plan_request.assessment_data,
                                "language": plan_request.language,
                                "level": plan_request.proficiency_level,
                                "learning_plan_id": created_plan['id']
                            }
                        }
                        # NOTE: No $inc on assessments_used — /api/speaking/assess already counted it
                    }
                    
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
                        print(f"[IDEMPOTENT_SAVE] 🎯 SAVE COMPLETE: Assessment data linked to plan (counter unchanged)")
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
        
        # Convert datetime fields to ISO strings before serialization (Pydantic requires strings)
        for _dt_field in ("updated_at", "created_at", "all_sessions_completed_at"):
            if _dt_field in new_plan and isinstance(new_plan[_dt_field], datetime):
                new_plan[_dt_field] = new_plan[_dt_field].isoformat()

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

    # 🔥 FIX: Convert datetime fields to ISO strings for Pydantic validation
    if "updated_at" in plan and isinstance(plan["updated_at"], datetime):
        plan["updated_at"] = plan["updated_at"].isoformat()
        logger.info(f"Converted updated_at to ISO string for plan {plan.get('id', 'unknown')}")

    if "created_at" in plan and isinstance(plan["created_at"], datetime):
        plan["created_at"] = plan["created_at"].isoformat()

    if "all_sessions_completed_at" in plan and isinstance(plan["all_sessions_completed_at"], datetime):
        plan["all_sessions_completed_at"] = plan["all_sessions_completed_at"].isoformat()

    # Ensure backward compatibility - add missing progress fields for existing plans
    if "total_sessions" not in plan or plan.get("total_sessions") is None:
        def calculate_total_sessions(duration_months: int) -> int:
            """Calculate total sessions based on duration (4 sessions/week × 4 weeks/month)"""
            session_mapping = {
                1: 16,   # 1 month = 4 weeks × 4 sessions/week
                2: 32,   # 2 months = 8 weeks × 4 sessions/week
                3: 48,   # 3 months = 12 weeks × 4 sessions/week
                6: 96,   # 6 months = 24 weeks × 4 sessions/week
                12: 192  # 12 months = 48 weeks × 4 sessions/week
            }
            return session_mapping.get(duration_months, duration_months * 16)  # Default: 16 sessions per month

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

    # Ensure voice check fields exist for existing plans (backward compatibility)
    if "voice_check_schedule" not in plan or plan.get("voice_check_schedule") is None:
        duration_months = plan.get("duration_months", 3)
        voice_check_schedule = voice_check_service.calculate_voice_check_schedule(duration_months)

        # Update the plan in the database with voice check fields
        await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {
                "voice_check_schedule": voice_check_schedule,
                "voice_checks_completed": plan.get("voice_checks_completed", [])
            }}
        )

        # Update local plan object
        plan["voice_check_schedule"] = voice_check_schedule
        plan["voice_checks_completed"] = plan.get("voice_checks_completed", [])
        
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
            """Calculate total sessions based on duration (4 sessions/week × 4 weeks/month)"""
            session_mapping = {
                1: 16,   # 1 month = 4 weeks × 4 sessions/week
                2: 32,   # 2 months = 8 weeks × 4 sessions/week
                3: 48,   # 3 months = 12 weeks × 4 sessions/week
                6: 96,   # 6 months = 24 weeks × 4 sessions/week
                12: 192  # 12 months = 48 weeks × 4 sessions/week
            }
            return session_mapping.get(duration_months, duration_months * 16)  # Default: 16 sessions per month
        
        updated_plans = []
        for plan in plans:
            # 🔥 FIX: Convert datetime fields to ISO strings for Pydantic validation
            if "updated_at" in plan and isinstance(plan["updated_at"], datetime):
                plan["updated_at"] = plan["updated_at"].isoformat()
                logger.info(f"Converted updated_at to ISO string for plan {plan.get('id', 'unknown')}")

            if "created_at" in plan and isinstance(plan["created_at"], datetime):
                plan["created_at"] = plan["created_at"].isoformat()

            if "all_sessions_completed_at" in plan and isinstance(plan["all_sessions_completed_at"], datetime):
                plan["all_sessions_completed_at"] = plan["all_sessions_completed_at"].isoformat()

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

            # Check if plan needs voice check fields (backward compatibility)
            if "voice_check_schedule" not in plan or plan.get("voice_check_schedule") is None:
                duration_months = plan.get("duration_months", 3)
                voice_check_schedule = voice_check_service.calculate_voice_check_schedule(duration_months)

                # Update the plan in the database
                await learning_plans_collection.update_one(
                    {"id": plan["id"]},
                    {"$set": {
                        "voice_check_schedule": voice_check_schedule,
                        "voice_checks_completed": plan.get("voice_checks_completed", [])
                    }}
                )

                # Update the plan object
                plan["voice_check_schedule"] = voice_check_schedule
                plan["voice_checks_completed"] = plan.get("voice_checks_completed", [])

                print(f"Updated plan {plan['id']} with voice check schedule: {voice_check_schedule}")

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
        total_sessions = learning_plan.get("total_sessions", 192)
        sessions_per_week = 4
        
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
        
        # 🆕 UPDATED: Flexible duration enforcement based on selected_duration
        selected_duration = getattr(request, 'selected_duration', None) or 5  # Default 5 for backward compatibility

        if request and request.duration_minutes:
            # Convert to float first to handle any input type
            raw_duration = float(request.duration_minutes)

            # 1. Cap at selected_duration maximum (frontend counter issue protection)
            if raw_duration > selected_duration:
                duration_minutes = selected_duration
                print(f"[SESSION_SUMMARY] ⚠️ Capping duration from {raw_duration} to {selected_duration} minutes (max allowed)")
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

            # Determine session status based on selected_duration threshold
            if duration_minutes >= selected_duration:
                session_status = "completed"
                print(f"[SESSION_SUMMARY] ✅ Complete session: {duration_minutes} minutes (threshold: {selected_duration})")
            else:
                session_status = "partial"
                print(f"[SESSION_SUMMARY] ⏰ Partial session: {duration_minutes} minutes (threshold: {selected_duration})")
        else:
            # Default: Use selected_duration for a complete session
            duration_minutes = selected_duration
            session_status = "completed"
            print(f"[SESSION_SUMMARY] 🕐 Default complete session: {duration_minutes} minutes")
        
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
            "selected_duration": selected_duration,  # 🆕 Store selected duration
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
                session_completed=(duration_minutes >= selected_duration)  # 🆕 FIXED: Use selected_duration threshold
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


# ============================================================================
# VOICE CHECK ENDPOINTS - Speaking DNA Acoustic Analysis
# ============================================================================

@router.get("/plan/{plan_id}/voice-check-status")
async def get_voice_check_status(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get voice check status for a learning plan.

    Returns:
    - is_due: Whether a voice check is due after the current session
    - next_check: Next scheduled voice check session number
    - schedule: Full voice check schedule
    - progress: Voice check completion statistics
    - prompt: Next voice check prompt to display

    Free for all users. Voice checks themselves are pedagogical
    primitives — the *DNA view* surfaces (profile / evolution /
    breakthroughs) stay premium-only, but reaching and clearing a
    scheduled check must work even when a subscription has lapsed,
    otherwise the LP gets permanently blocked behind a paywall.
    """
    try:
        # 🚀 REDIS CACHE: Check cache first (10 second TTL)
        from redis_client import get_cached, set_cached
        cache_key = f"voice_check_status:{plan_id}"

        try:
            cached = await get_cached(cache_key)
            if cached:
                print(f"[VOICE_CHECK] ✅ Cache HIT for plan {plan_id}")
                return cached
            print(f"[VOICE_CHECK] ❌ Cache MISS for plan {plan_id}")
        except Exception as cache_error:
            print(f"[VOICE_CHECK] ⚠️ Cache read error: {cache_error}")

        # Get the learning plan
        plan = await learning_plans_collection.find_one({"id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        # Verify ownership
        if str(plan.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get plan data
        duration_months = plan.get("duration_months", 3)
        completed_sessions = plan.get("completed_sessions", 0)
        voice_checks_completed = plan.get("voice_checks_completed", [])

        # Recalculate schedule with current algorithm and sync to DB if stale
        current_schedule = voice_check_service.calculate_voice_check_schedule(duration_months)
        if plan.get("voice_check_schedule") != current_schedule:
            await learning_plans_collection.update_one(
                {"id": plan_id},
                {"$set": {"voice_check_schedule": current_schedule}}
            )

        # Calculate if voice check is due
        is_due = voice_check_service.is_voice_check_due(
            completed_sessions=completed_sessions,
            duration_months=duration_months,
            voice_checks_completed=voice_checks_completed
        )

        # Get next voice check
        next_check = voice_check_service.get_next_voice_check(
            completed_sessions=completed_sessions,
            duration_months=duration_months,
            voice_checks_completed=voice_checks_completed
        )

        # Get progress statistics
        progress = voice_check_service.get_voice_check_progress(
            duration_months=duration_months,
            voice_checks_completed=voice_checks_completed
        )

        # Get the prompt for the current voice check
        check_number = len(voice_checks_completed)
        prompt = voice_check_service.get_voice_check_prompt(check_number)

        # `was_skipped` lets the client distinguish "user hit Skip
        # earlier and still needs to finish" from "first time we're
        # showing this prompt", so the hero CTA copy can be tuned.
        # Only meaningful while `is_due` is true.
        voice_checks_skipped = plan.get("voice_checks_skipped", []) or []
        was_skipped = bool(is_due and completed_sessions in voice_checks_skipped)

        print(
            f"[VOICE_CHECK] plan={plan_id} completed={completed_sessions} "
            f"schedule={progress['schedule']} completed_checks={voice_checks_completed} "
            f"skipped={voice_checks_skipped} is_due={is_due} was_skipped={was_skipped}"
        )

        result = {
            "is_due": is_due,
            "was_skipped": was_skipped,
            "next_check": next_check,
            "current_session": completed_sessions,
            "schedule": progress["schedule"],
            "progress": progress,
            "prompt": prompt,
            "plan_id": plan_id,
            "language": plan.get("language", "").lower()
        }

        # 🚀 REDIS CACHE: Store result (10 second TTL - invalidated on session completion)
        try:
            await set_cached(cache_key, result, ttl_seconds=10)
            print(f"[VOICE_CHECK] 📦 Cached result for plan {plan_id}")
        except Exception as cache_error:
            print(f"[VOICE_CHECK] ⚠️ Cache write error: {cache_error}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice check status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting voice check status: {str(e)}"
        )


@router.post("/plan/{plan_id}/complete-voice-check")
async def complete_voice_check(
    plan_id: str,
    session_number: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark a voice check as completed.

    Args:
    - plan_id: Learning plan ID
    - session_number: Session number where voice check was completed

    Premium Feature: Only available for active subscribers.
    """
    try:
        # Premium-only feature check
        if current_user.subscription_status not in ["active", "trialing", "canceling"]:
            raise HTTPException(
                status_code=403,
                detail="Voice checks are a premium feature."
            )

        # Get the learning plan
        plan = await learning_plans_collection.find_one({"id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        # Verify ownership
        if str(plan.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get current voice checks completed
        voice_checks_completed = plan.get("voice_checks_completed", [])

        # Mark as completed
        updated_checks = voice_check_service.mark_voice_check_completed(
            voice_checks_completed=voice_checks_completed,
            session_number=session_number
        )

        # Update in database
        await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {"voice_checks_completed": updated_checks}}
        )

        # Get updated progress
        progress = voice_check_service.get_voice_check_progress(
            duration_months=plan.get("duration_months", 3),
            voice_checks_completed=updated_checks
        )

        logger.info(f"[VOICE_CHECK] ✅ Completed voice check for plan {plan_id}, session {session_number}")
        logger.info(f"[VOICE_CHECK] Progress: {progress['completed']}/{progress['total_scheduled']} ({progress['completion_percentage']}%)")

        return {
            "success": True,
            "session_number": session_number,
            "voice_checks_completed": updated_checks,
            "progress": progress
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing voice check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error completing voice check: {str(e)}"
        )


@router.post("/plan/{plan_id}/skip-voice-check")
async def skip_voice_check(
    plan_id: str,
    session_number: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Record that the user dismissed the voice-check modal at this
    session. The voice check itself stays *pending* — `is_due` will
    keep returning True until the user actually completes one. This is
    a deliberate change from the earlier "skip = silently complete"
    behaviour: skipping the DNA scan now blocks plan progression
    (the hero CTA reroutes to the voice-check screen) until the user
    finishes a check. `voice_checks_skipped` is tracked separately for
    analytics + so the client can show a "you skipped earlier" tone.

    No premium gate. Voice checks are pedagogical and free for all
    learners; only the resulting DNA view is premium-gated.
    """
    try:
        plan = await learning_plans_collection.find_one({"id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        # Verify ownership
        if str(plan.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get next voice check info
        duration_months = plan.get("duration_months", 3)
        completed_sessions = plan.get("completed_sessions", 0)
        voice_checks_completed = plan.get("voice_checks_completed", [])

        # Record the skip for analytics ONLY. Do NOT push to
        # voice_checks_completed — that array drives `is_due`, and
        # adding the session number there would silently mark the
        # check as done, which is the opposite of the new behaviour.
        await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$addToSet": {"voice_checks_skipped": session_number}},
        )

        next_check = voice_check_service.get_next_voice_check(
            completed_sessions=completed_sessions,
            duration_months=duration_months,
            voice_checks_completed=voice_checks_completed
        )

        logger.info(f"[VOICE_CHECK] ⏭️ Skip recorded for plan {plan_id}, session {session_number} — is_due remains true")
        logger.info(f"[VOICE_CHECK] Next scheduled check: session {next_check}")

        return {
            "success": True,
            "skipped": True,
            "session_number": session_number,
            "next_check": next_check,
            "still_pending": True,
            "message": "Voice check still waiting — you can finish it anytime from your plan.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping voice check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error skipping voice check: {str(e)}"
        )


@router.patch("/plan/{plan_id}/add-spoken-time")
async def add_spoken_time(
    plan_id: str,
    duration_minutes: float,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Lightweight endpoint to add spoken minutes to a learning plan's practice_minutes_used.
    Called on early exit to record actual time spent without triggering full session processing
    (no AI analysis, no session counting, no subscription tracking).
    """
    try:
        if duration_minutes <= 0:
            return {"success": True, "message": "No time to add"}

        # Cap at 5 minutes and ensure positive
        capped_minutes = min(float(duration_minutes), 5.0)

        plan = await learning_plans_collection.find_one({"id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        if str(plan.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        current_minutes = float(plan.get("practice_minutes_used", 0.0))
        new_minutes = current_minutes + capped_minutes

        await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {
                "practice_minutes_used": new_minutes,
                "updated_at": datetime.utcnow().isoformat()
            }}
        )

        print(f"[ADD_SPOKEN_TIME] ✅ Plan {plan_id}: {current_minutes} + {capped_minutes} = {new_minutes} min (early exit)")

        # Write to daily_stats so the weekly bar chart stays in sync with the minutes card.
        # The partial exit doesn't go through session_summary_routes so daily_stats
        # would otherwise miss this time, causing a mismatch between the two sources.
        try:
            from database import daily_stats_collection
            from services.timezone_utils import get_current_local_date
            local_date = get_current_local_date(user_timezone=getattr(current_user, 'timezone', None) or 'UTC')
            time_seconds = capped_minutes * 60
            await daily_stats_collection.update_one(
                {"user_id": str(current_user.id), "local_date": local_date},
                {
                    "$inc": {
                        "conversation_time_seconds": time_seconds,
                        "total_time_seconds": time_seconds,
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {
                        "created_at": datetime.utcnow(),
                        "is_streak_day": False,
                        "total_sessions": 0,
                        "learning_plan_sessions": 0,
                        "total_challenges": 0,
                        "correct_challenges": 0,
                        "incorrect_challenges": 0,
                        "total_xp": 0,
                    }
                },
                upsert=True
            )
            print(f"[ADD_SPOKEN_TIME] ✅ daily_stats updated: +{capped_minutes} min for {local_date}")
        except Exception as stats_err:
            print(f"[ADD_SPOKEN_TIME] ⚠️ daily_stats update failed (non-fatal): {stats_err}")

        return {
            "success": True,
            "practice_minutes_used": new_minutes,
            "added_minutes": capped_minutes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding spoken time: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding spoken time: {str(e)}"
        )


# Allowed durations per CEFR tier
_ALLOWED_DURATIONS: dict[str, list[int]] = {
    "A1": [1, 3],
    "A2": [1, 3],
    "B1": [3, 5],
    "B2": [3, 5],
    "C1": [3, 5],
    "C2": [3, 5],
}


@router.patch("/plan/{plan_id}/session-duration")
async def update_session_duration(
    plan_id: str,
    new_duration: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update the preferred session duration for a learning plan.

    Allowed transitions (CEFR-gated):
      A1 / A2  → 1 min  ↔  3 min
      B1+      → 3 min  ↔  5 min

    Recalculates total_practice_minutes = total_sessions × new_duration.
    Does NOT touch completed_sessions, practice_minutes_used, or voice_check_schedule.
    Cannot be changed once all sessions are completed.
    """
    try:
        plan = await learning_plans_collection.find_one({"id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        if str(plan.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Guard: plan must not be completed
        if plan.get("status") in ("completed", "awaiting_final_assessment"):
            raise HTTPException(
                status_code=400,
                detail="Cannot change session duration after all sessions are completed"
            )

        level = (plan.get("proficiency_level") or "A1").upper()
        allowed = _ALLOWED_DURATIONS.get(level, [3, 5])

        if new_duration not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid duration {new_duration} min for level {level}. Allowed: {allowed}"
            )

        current_duration = plan.get("preferred_session_duration") or allowed[0]
        if new_duration == current_duration:
            return {
                "success": True,
                "preferred_session_duration": current_duration,
                "total_practice_minutes": plan.get("total_practice_minutes"),
                "message": "No change — duration already set to this value"
            }

        # Guard: cannot downgrade if already have completed sessions with the higher duration
        # (e.g. completed 3-min sessions, then trying to switch to 1 min would make progress inconsistent)
        completed = plan.get("completed_sessions", 0)
        if completed > 0 and new_duration < current_duration:
            # Allow downgrade but warn — existing sessions recorded at the old duration are not
            # retroactively changed. Only future sessions use the new duration.
            logger.info(
                f"[SESSION_DURATION] Downgrade on plan {plan_id}: "
                f"{current_duration}→{new_duration} min with {completed} sessions already done"
            )

        total_sessions = plan.get("total_sessions", 48)
        new_total_practice_minutes = float(total_sessions * new_duration)

        await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": {
                "preferred_session_duration": new_duration,
                "total_practice_minutes": new_total_practice_minutes,
                "updated_at": datetime.utcnow().isoformat()
            }}
        )

        logger.info(
            f"[SESSION_DURATION] Plan {plan_id}: {current_duration}→{new_duration} min, "
            f"total_practice_minutes={new_total_practice_minutes}"
        )

        return {
            "success": True,
            "preferred_session_duration": new_duration,
            "total_practice_minutes": new_total_practice_minutes,
            "previous_duration": current_duration,
            "completed_sessions_kept": completed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SESSION_DURATION] Error updating session duration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating session duration: {str(e)}")
