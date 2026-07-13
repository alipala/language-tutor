"""
FINAL ASSESSMENT ROUTES
=======================

API endpoints for learning plan final assessments.

Endpoints:
- GET /api/learning-plans/{plan_id}/final-assessment-status - Check if assessment is required
- POST /api/learning-plans/{plan_id}/final-assessment - Submit and evaluate final assessment
- GET /api/learning-plans/{plan_id}/next-level-suggestion - Get suggested next level plan
- POST /api/learning-plans/create-next-level - Create next level plan after passing assessment

IMPORTANT: Final assessments DO NOT count toward subscription assessment limits.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import traceback
import logging

from auth import get_current_user
from models import UserResponse

# Use the existing get_current_user function from auth.py
get_current_user_from_request = get_current_user
from services.learning_plan_final_assessment_service import LearningPlanFinalAssessmentService
from speaking_assessment import recognize_speech, evaluate_language_proficiency

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class FinalAssessmentStatusResponse(BaseModel):
    required: bool
    status: str
    all_sessions_completed: bool
    completed_sessions: int
    total_sessions: int
    last_attempt: Optional[Dict[str, Any]] = None
    can_retry: bool
    attempts_count: int
    passed: bool
    message: str


class FinalAssessmentRequirementsResponse(BaseModel):
    learning_plan_id: str
    language: str
    current_level: str
    next_level: str
    minimum_duration_minutes: int
    goals: List[str]
    focus_areas: List[str]
    assessment_type: str
    instructions: str
    attempts_made: int


class FinalAssessmentSubmitRequest(BaseModel):
    audio_base64: str
    duration: int  # Duration in seconds
    prompt: Optional[str] = None


class FinalAssessmentResultResponse(BaseModel):
    passed: bool
    current_level: str
    next_level: str
    overall_score: int
    current_level_mastery: Dict[str, Any]
    next_level_readiness: Dict[str, Any]
    skills: Dict[str, int]
    recommendation: str
    message: str
    strengths: List[str]
    areas_for_improvement: List[str]
    next_steps: List[str]
    attempt_number: int


class NextLevelPlanSuggestionResponse(BaseModel):
    suggested: bool
    based_on_plan: str
    language: str
    proficiency_level: str
    previous_level: str
    goals: List[str]
    duration_months: int
    focus_areas: List[str]
    customizable: bool
    message: str


class CreateNextLevelPlanRequest(BaseModel):
    current_plan_id: str
    # Optional customizations
    duration_months: Optional[int] = None
    goals: Optional[List[str]] = None
    custom_goal: Optional[str] = None
    interface_language: Optional[str] = None


# Routes
@router.get(
    "/api/learning-plans/{plan_id}/final-assessment-status",
    response_model=FinalAssessmentStatusResponse
)
async def get_final_assessment_status(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user_from_request)
):
    """
    Check if user needs to take final assessment for their learning plan.

    Returns assessment status, last attempt info, and whether user can retry.
    """
    try:
        logger.info(f"[FINAL_ASSESSMENT_API] Getting assessment status for plan {plan_id}, user {current_user.id}")

        result = await LearningPlanFinalAssessmentService.check_final_assessment_required(
            user_id=current_user.id,
            learning_plan_id=plan_id
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if result.get("status") == "not_found" else status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return FinalAssessmentStatusResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FINAL_ASSESSMENT_API] Error getting assessment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting assessment status: {str(e)}"
        )


@router.get(
    "/api/learning-plans/{plan_id}/final-assessment-requirements",
    response_model=FinalAssessmentRequirementsResponse
)
async def get_final_assessment_requirements(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user_from_request)
):
    """
    Get the assessment requirements for a learning plan.

    Returns duration, focus areas, and instructions based on current level and plan goals.
    """
    try:
        logger.info(f"[FINAL_ASSESSMENT_API] Getting assessment requirements for plan {plan_id}")

        result = await LearningPlanFinalAssessmentService.get_assessment_requirements(
            learning_plan_id=plan_id,
            user_id=current_user.id
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return FinalAssessmentRequirementsResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FINAL_ASSESSMENT_API] Error getting requirements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting requirements: {str(e)}"
        )


@router.post(
    "/api/learning-plans/{plan_id}/final-assessment",
    response_model=FinalAssessmentResultResponse
)
async def submit_final_assessment(
    plan_id: str,
    request: FinalAssessmentSubmitRequest,
    current_user: UserResponse = Depends(get_current_user_from_request)
):
    """
    Submit and evaluate final assessment for a learning plan.

    IMPORTANT: Final assessments DO NOT count toward subscription limits.

    Evaluates with dual criteria:
    1. Current level mastery (must >= 75)
    2. Next level readiness (must >= 70)

    Both must pass for user to advance to next level.
    """
    try:
        logger.info(f"[FINAL_ASSESSMENT_API] Submitting final assessment for plan {plan_id}, user {current_user.id}")

        # Server-side voice-check guard. A user with a pending voice
        # check shouldn't be able to short-cut into the final
        # assessment via the API — the mobile CTA reroutes them, but
        # this is the belt to those braces.
        from database import learning_plans_collection as _lp_coll
        from services.voice_check_service import voice_check_service as _vc_svc
        _guard_plan = await _lp_coll.find_one({"id": plan_id})
        if _guard_plan and _vc_svc.has_pending_voice_check(_guard_plan):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "VOICE_CHECK_PENDING",
                    "plan_id": plan_id,
                    "session_number": int(_guard_plan.get("completed_sessions", 0) or 0),
                    "message": "Finish your voice check first — final assessment unlocks after that.",
                },
            )

        # Get assessment requirements first
        requirements = await LearningPlanFinalAssessmentService.get_assessment_requirements(
            learning_plan_id=plan_id,
            user_id=current_user.id
        )

        if "error" in requirements:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=requirements["error"]
            )

        # Validate duration
        duration_seconds = request.duration
        required_minutes = requirements["minimum_duration_minutes"]
        required_seconds = required_minutes * 60

        if duration_seconds < required_seconds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assessment duration too short. Minimum {required_minutes} minutes ({required_seconds} seconds) required, got {duration_seconds} seconds."
            )

        # Transcribe audio
        try:
            logger.info(f"[FINAL_ASSESSMENT_API] Transcribing audio for assessment...")
            recognized_text = await recognize_speech(
                request.audio_base64,
                requirements["language"]
            )
            logger.info(f"[FINAL_ASSESSMENT_API] Transcribed: '{recognized_text[:100]}...'")
        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT_API] Error transcribing audio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to transcribe audio: {str(e)}"
            )

        if not recognized_text or recognized_text.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No speech detected in audio"
            )

        # Evaluate language proficiency using speaking assessment
        try:
            logger.info(f"[FINAL_ASSESSMENT_API] Evaluating language proficiency...")
            assessment_result = await evaluate_language_proficiency(
                text=recognized_text,
                language=requirements["language"],
                duration=duration_seconds,
                prompt=request.prompt
            )
        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT_API] Error evaluating proficiency: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error evaluating assessment: {str(e)}"
            )

        # Evaluate with dual criteria (current mastery + next level readiness)
        evaluation_result = await LearningPlanFinalAssessmentService.evaluate_final_assessment(
            user_id=current_user.id,
            learning_plan_id=plan_id,
            assessment_data={
                "recognized_text": recognized_text,
                "overall_score": assessment_result.get("overall_score", 0),
                "pronunciation": assessment_result.get("pronunciation", {}),
                "grammar": assessment_result.get("grammar", {}),
                "vocabulary": assessment_result.get("vocabulary", {}),
                "fluency": assessment_result.get("fluency", {}),
                "coherence": assessment_result.get("coherence", {}),
                "strengths": assessment_result.get("strengths", []),
                "areas_for_improvement": assessment_result.get("areas_for_improvement", []),
                "next_steps": assessment_result.get("next_steps", []),
                "duration": duration_seconds
            }
        )

        if "error" in evaluation_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=evaluation_result["error"]
            )

        # Record the assessment attempt
        record_result = await LearningPlanFinalAssessmentService.record_assessment_attempt(
            user_id=current_user.id,
            learning_plan_id=plan_id,
            assessment_data={
                "recognized_text": recognized_text,
                "duration": duration_seconds
            },
            evaluation_result=evaluation_result
        )

        if not record_result.get("success", False):
            logger.error(f"[FINAL_ASSESSMENT_API] Failed to record attempt: {record_result.get('error')}")
            # Don't fail the request, just log the error

        logger.info(f"[FINAL_ASSESSMENT_API] Assessment completed. Passed: {evaluation_result.get('passed', False)}")

        return FinalAssessmentResultResponse(
            passed=evaluation_result.get("passed", False),
            current_level=evaluation_result.get("current_level", ""),
            next_level=evaluation_result.get("next_level", ""),
            overall_score=evaluation_result.get("overall_score", 0),
            current_level_mastery=evaluation_result.get("current_level_mastery", {}),
            next_level_readiness=evaluation_result.get("next_level_readiness", {}),
            skills=evaluation_result.get("skills", {}),
            recommendation=evaluation_result.get("recommendation", "practice_more"),
            message=evaluation_result.get("message", ""),
            strengths=evaluation_result.get("strengths", []),
            areas_for_improvement=evaluation_result.get("areas_for_improvement", []),
            next_steps=evaluation_result.get("next_steps", []),
            attempt_number=record_result.get("attempt_number", 1)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FINAL_ASSESSMENT_API] Error submitting assessment: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting assessment: {str(e)}"
        )


@router.get(
    "/api/learning-plans/{plan_id}/next-level-suggestion",
    response_model=NextLevelPlanSuggestionResponse
)
async def get_next_level_plan_suggestion(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user_from_request)
):
    """
    Get auto-generated suggestion for next level learning plan.

    This is called after user passes final assessment.
    User can review and customize before confirming.
    """
    try:
        logger.info(f"[FINAL_ASSESSMENT_API] Getting next level plan suggestion for plan {plan_id}")

        result = await LearningPlanFinalAssessmentService.generate_next_level_plan_suggestion(
            user_id=current_user.id,
            current_plan_id=plan_id
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return NextLevelPlanSuggestionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FINAL_ASSESSMENT_API] Error getting next level suggestion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting suggestion: {str(e)}"
        )


@router.post("/api/learning-plans/create-next-level")
async def create_next_level_plan(
    request: CreateNextLevelPlanRequest,
    current_user: UserResponse = Depends(get_current_user_from_request)
):
    """
    Create next level learning plan after passing final assessment.

    User can customize duration, goals before creating.
    This uses the existing learning plan creation logic.
    """
    try:
        logger.info(f"[FINAL_ASSESSMENT_API] Creating next level plan for user {current_user.id}")

        # Voice-check guard. A user can only level-up if their *current*
        # plan has cleared every scheduled voice check. Skipping the
        # final check and jumping into the next plan would leave the
        # DNA history with a gap, which the strand trajectory math
        # depends on. Mobile routes the user back to the voice-check
        # screen on this 403.
        from database import learning_plans_collection as _lp_coll
        from services.voice_check_service import voice_check_service as _vc_svc
        _guard_plan = await _lp_coll.find_one({"id": request.current_plan_id})
        if _guard_plan and _vc_svc.has_pending_voice_check(_guard_plan):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "VOICE_CHECK_PENDING",
                    "plan_id": request.current_plan_id,
                    "session_number": int(_guard_plan.get("completed_sessions", 0) or 0),
                    "message": "Finish your voice check on the current plan before starting the next level.",
                },
            )

        # Get the suggestion first
        suggestion = await LearningPlanFinalAssessmentService.generate_next_level_plan_suggestion(
            user_id=current_user.id,
            current_plan_id=request.current_plan_id
        )

        if "error" in suggestion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=suggestion["error"]
            )

        # Use customizations if provided, otherwise use suggestion
        duration_months = request.duration_months or suggestion["duration_months"]
        goals = request.goals or suggestion["goals"]
        custom_goal = request.custom_goal

        # Get the current plan to extract assessment data
        from database import database
        current_plan = await database["learning_plans"].find_one({
            "id": request.current_plan_id,
            "user_id": current_user.id
        })

        # Extract assessment data from the current plan's final assessment
        assessment_data = None
        if current_plan and current_plan.get("final_assessment", {}).get("attempts"):
            last_attempt = current_plan["final_assessment"]["attempts"][-1]

            # Build assessment_data in the format expected by create_learning_plan
            assessment_data = {
                "recognized_text": f"Completed {suggestion['previous_level']} level with score {last_attempt.get('overall_score', 0)}",
                "overall_score": last_attempt.get("overall_score", 0),
                "recommended_level": suggestion["proficiency_level"],
                "pronunciation": {
                    "score": last_attempt.get("scores", {}).get("pronunciation", 0),
                    "feedback": f"Ready for {suggestion['proficiency_level']} pronunciation practice"
                },
                "grammar": {
                    "score": last_attempt.get("scores", {}).get("grammar", 0),
                    "feedback": f"Continue improving grammar at {suggestion['proficiency_level']} level"
                },
                "vocabulary": {
                    "score": last_attempt.get("scores", {}).get("vocabulary", 0),
                    "feedback": f"Build {suggestion['proficiency_level']} level vocabulary"
                },
                "fluency": {
                    "score": last_attempt.get("scores", {}).get("fluency", 0),
                    "feedback": f"Enhance fluency for {suggestion['proficiency_level']} level"
                },
                "coherence": {
                    "score": last_attempt.get("scores", {}).get("coherence", 0),
                    "feedback": f"Develop {suggestion['proficiency_level']} coherence skills"
                },
                "strengths": last_attempt.get("strengths", []),
                "areas_for_improvement": last_attempt.get("areas_for_improvement", []),
                "next_steps": [f"Progress to {suggestion['proficiency_level']} level", "Practice regularly", "Focus on weak areas"]
            }
            logger.info(f"[FINAL_ASSESSMENT_API] Using assessment data from previous plan: overall_score={assessment_data['overall_score']}")

        # Call the learning plan creation directly
        from learning_routes import create_learning_plan

        # Create plan data matching the expected format
        plan_data = {
            "language": suggestion["language"],
            "proficiency_level": suggestion["proficiency_level"],
            "goals": goals if goals else [],
            "duration_months": duration_months,
            "custom_goal": custom_goal,
            "assessment_data": assessment_data,  # Add assessment data for proper plan generation
            "from_final_assessment": True,
            "previous_plan_id": request.current_plan_id,
            "interface_language": request.interface_language,
        }

        # Create the plan by calling the endpoint
        result = await create_learning_plan(
            request_data=plan_data,
            current_user=current_user
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        logger.info(f"[FINAL_ASSESSMENT_API] ✅ Created next level plan: {result.get('plan_id')}")

        return {
            "success": True,
            "plan_id": result.get("plan_id"),
            "message": f"Successfully created {suggestion['proficiency_level']} level learning plan!",
            "plan": result.get("plan")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FINAL_ASSESSMENT_API] Error creating next level plan: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating plan: {str(e)}"
        )
