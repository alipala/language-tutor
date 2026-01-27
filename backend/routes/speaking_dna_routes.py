"""
Speaking DNA API Routes
=======================
REST endpoints for Speaking DNA feature.

Endpoints:
- POST /api/speaking-dna/analyze-session - Analyze a session and update DNA
- GET /api/speaking-dna/profile/{language} - Get user's DNA profile
- GET /api/speaking-dna/evolution/{language} - Get DNA evolution history
- GET /api/speaking-dna/breakthroughs/{language} - Get breakthrough moments
- POST /api/speaking-dna/breakthroughs/{breakthrough_id}/celebrate - Mark breakthrough as celebrated
- GET /api/speaking-dna/coach-instructions/{language} - Get DNA-aware coach instructions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from auth import get_current_user
from models import (
    SessionAnalysisInput,
    AnalyzeSessionResponse,
    DNAProfileResponse,
    DNAEvolutionResponse,
    DNABreakthroughsResponse,
    CoachInstructionsResponse,
    UserResponse
)
from services.speaking_dna_service import speaking_dna_service

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/speaking-dna", tags=["Speaking DNA"])


# ============================================================================
# Session Analysis Endpoint
# ============================================================================

@router.post("/analyze-session", response_model=AnalyzeSessionResponse)
async def analyze_session(
    language: str = Query(..., description="Target language (e.g., 'dutch', 'spanish')"),
    session_data: SessionAnalysisInput = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze a completed session and update Speaking DNA profile.

    This endpoint should be called after each speaking session ends.
    It updates the user's DNA profile and detects any breakthroughs.

    **Premium Feature**: Only available to users with active subscription.

    Args:
        language: Target language code
        session_data: Session data including user turns, corrections, challenges
        current_user: Authenticated user from JWT token

    Returns:
        AnalyzeSessionResponse with breakthroughs and session insights

    Raises:
        400: Invalid session data
        403: User not authorized (not premium subscriber)
        500: Server error during analysis
    """
    try:
        # Check if user has premium access
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription to access this feature."
            )

        logger.info(f"[DNA API] Analyzing session for user {current_user.id}, language {language}")

        # Convert Pydantic model to dict for service
        session_dict = {
            "session_id": session_data.session_id,
            "session_type": session_data.session_type,
            "duration_seconds": session_data.duration_seconds,
            "user_turns": [turn.dict() for turn in session_data.user_turns],
            "corrections_received": session_data.corrections_received or [],
            "challenges_offered": session_data.challenges_offered,
            "challenges_accepted": session_data.challenges_accepted,
            "topics_discussed": session_data.topics_discussed or []
        }

        # Analyze session
        result = await speaking_dna_service.analyze_session_for_dna(
            user_id=str(current_user.id),
            language=language,
            session_data=session_dict
        )

        logger.info(f"[DNA API] Analysis complete. Breakthroughs: {len(result['breakthroughs'])}")

        return AnalyzeSessionResponse(
            success=True,
            breakthroughs=result["breakthroughs"],
            session_insights=result["session_insights"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error analyzing session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze session: {str(e)}"
        )


# ============================================================================
# Profile Retrieval Endpoint
# ============================================================================

@router.get("/profile/{language}", response_model=DNAProfileResponse)
async def get_dna_profile(
    language: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the user's current Speaking DNA profile for a language.

    Returns the full profile including all 6 DNA strands,
    overall archetype, strengths, and growth areas.

    **Premium Feature**: Only available to users with active subscription.

    Args:
        language: Target language code
        current_user: Authenticated user from JWT token

    Returns:
        DNAProfileResponse with profile data or null if not exists

    Raises:
        403: User not authorized (not premium subscriber)
        500: Server error during retrieval
    """
    try:
        # Check if user has premium access
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription."
            )

        logger.info(f"[DNA API] Getting profile for user {current_user.id}, language {language}")

        profile = await speaking_dna_service.get_dna_profile(
            user_id=str(current_user.id),
            language=language
        )

        return DNAProfileResponse(
            profile=profile,
            has_profile=profile is not None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error getting profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DNA profile: {str(e)}"
        )


# ============================================================================
# Evolution History Endpoint
# ============================================================================

@router.get("/evolution/{language}", response_model=DNAEvolutionResponse)
async def get_dna_evolution(
    language: str,
    weeks: int = Query(default=12, ge=1, le=52, description="Number of weeks to retrieve"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the evolution history of Speaking DNA over time.

    Returns weekly snapshots for visualization in the
    evolution timeline chart.

    **Premium Feature**: Only available to users with active subscription.

    Args:
        language: Target language code
        weeks: Number of weeks to retrieve (1-52, default 12)
        current_user: Authenticated user from JWT token

    Returns:
        DNAEvolutionResponse with weekly snapshots

    Raises:
        403: User not authorized (not premium subscriber)
        500: Server error during retrieval
    """
    try:
        # Check if user has premium access
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription."
            )

        logger.info(f"[DNA API] Getting evolution for user {current_user.id}, language {language}, weeks {weeks}")

        evolution = await speaking_dna_service.get_dna_evolution(
            user_id=str(current_user.id),
            language=language,
            weeks=weeks
        )

        return DNAEvolutionResponse(
            evolution=evolution,
            weeks_tracked=len(evolution)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error getting evolution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DNA evolution: {str(e)}"
        )


# ============================================================================
# Breakthroughs Endpoint
# ============================================================================

@router.get("/breakthroughs/{language}", response_model=DNABreakthroughsResponse)
async def get_breakthroughs(
    language: str,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of breakthroughs to return"),
    uncelebrated_only: bool = Query(default=False, description="Return only uncelebrated breakthroughs"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the user's breakthrough moments.

    Can filter to only uncelebrated breakthroughs for
    displaying celebration modals.

    **Premium Feature**: Only available to users with active subscription.

    Args:
        language: Target language code
        limit: Maximum number of breakthroughs (1-100, default 20)
        uncelebrated_only: Filter to uncelebrated breakthroughs only
        current_user: Authenticated user from JWT token

    Returns:
        DNABreakthroughsResponse with breakthrough list

    Raises:
        403: User not authorized (not premium subscriber)
        500: Server error during retrieval
    """
    try:
        # Check if user has premium access
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription."
            )

        logger.info(f"[DNA API] Getting breakthroughs for user {current_user.id}, language {language}")

        breakthroughs = await speaking_dna_service.get_breakthroughs(
            user_id=str(current_user.id),
            language=language,
            limit=limit,
            uncelebrated_only=uncelebrated_only
        )

        return DNABreakthroughsResponse(
            breakthroughs=breakthroughs,
            total_count=len(breakthroughs)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error getting breakthroughs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get breakthroughs: {str(e)}"
        )


# ============================================================================
# Celebrate Breakthrough Endpoint
# ============================================================================

@router.post("/breakthroughs/{breakthrough_id}/celebrate")
async def celebrate_breakthrough(
    breakthrough_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark a breakthrough as celebrated.

    Called when the user dismisses a breakthrough celebration modal.

    Args:
        breakthrough_id: Breakthrough MongoDB ObjectId
        current_user: Authenticated user from JWT token

    Returns:
        Success status

    Raises:
        403: User not authorized
        404: Breakthrough not found
        500: Server error
    """
    try:
        # Check if user has premium access
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription."
            )

        logger.info(f"[DNA API] Celebrating breakthrough {breakthrough_id} for user {current_user.id}")

        success = await speaking_dna_service.mark_breakthrough_celebrated(breakthrough_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Breakthrough not found"
            )

        return {"success": True, "message": "Breakthrough marked as celebrated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error celebrating breakthrough: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to celebrate breakthrough: {str(e)}"
        )


# ============================================================================
# Coach Instructions Endpoint (Internal Use)
# ============================================================================

@router.get("/coach-instructions/{language}", response_model=CoachInstructionsResponse)
async def get_coach_instructions(
    language: str,
    session_type: str = Query(..., description="Session type: learning, freestyle, or news"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get DNA-aware coaching instructions for the AI tutor.

    Called at the start of each session to personalize
    the AI coach's behavior based on the user's DNA profile.

    This is primarily used internally by the realtime session creation endpoint.

    Args:
        language: Target language code
        session_type: Type of session (learning, freestyle, news)
        current_user: Authenticated user from JWT token

    Returns:
        CoachInstructionsResponse with personalized instructions

    Raises:
        400: Invalid session type
        500: Server error
    """
    try:
        # Validate session type
        valid_session_types = ["learning", "freestyle", "news"]
        if session_type not in valid_session_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid session_type. Must be one of: {', '.join(valid_session_types)}"
            )

        logger.info(f"[DNA API] Getting coach instructions for user {current_user.id}, language {language}, type {session_type}")

        instructions = await speaking_dna_service.build_coach_instructions(
            user_id=str(current_user.id),
            language=language,
            session_type=session_type
        )

        profile = await speaking_dna_service.get_dna_profile(
            user_id=str(current_user.id),
            language=language
        )

        return CoachInstructionsResponse(
            instructions=instructions,
            has_profile=profile is not None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error getting coach instructions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get coach instructions: {str(e)}"
        )
