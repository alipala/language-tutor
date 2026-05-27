"""
Speaking DNA API Routes
=======================
REST endpoints for Speaking DNA feature.

Endpoints:
- POST /api/speaking-dna/analyze-session - Analyze a session and update DNA
- GET /api/speaking-dna/profile/{language} - Get user's DNA profile
- GET /api/speaking-dna/evolution/{language} - Get DNA evolution history
- GET /api/speaking-dna/acoustic-evolution/{language} - Get acoustic metrics evolution
- GET /api/speaking-dna/breakthroughs/{language} - Get breakthrough moments
- POST /api/speaking-dna/breakthroughs/{breakthrough_id}/celebrate - Mark breakthrough as celebrated
- GET /api/speaking-dna/coach-instructions/{language} - Get DNA-aware coach instructions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Any, Dict, List
import logging
import math

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
from cache_helpers import invalidate_coach_context_smart  # PHASE 4.2: Smart cache invalidation

logger = logging.getLogger(__name__)


def sanitize_floats(obj: Any, default_value: float = 0.0) -> Any:
    """
    Recursively sanitize float values to ensure JSON compliance.
    Replaces inf, -inf, and nan with a default value (0.0 by default).

    Args:
        obj: The object to sanitize (dict, list, float, or other)
        default_value: The value to use for invalid floats (default: 0.0)

    Returns:
        The sanitized object with invalid floats replaced
    """
    if isinstance(obj, dict):
        return {key: sanitize_floats(value, default_value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_floats(item, default_value) for item in obj]
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            logger.warning(f"[DNA API] 🔧 Found invalid float value: {obj}, replacing with {default_value}")
            return default_value
        return obj
    else:
        return obj

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
        # Check if user has premium access (allow "canceling" status - user has access until period ends)
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing", "canceling"]:
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
            "topics_discussed": session_data.topics_discussed or [],
            # Voice check audio for acoustic analysis
            "audio_base64": session_data.audio_base64,
            "audio_format": session_data.audio_format
        }

        # Analyze session
        result = await speaking_dna_service.analyze_session_for_dna(
            user_id=str(current_user.id),
            language=language,
            session_data=session_dict
        )

        logger.info(f"[DNA API] Analysis complete. Breakthroughs: {len(result['breakthroughs'])}")

        # PHASE 4.2: Invalidate TaalCoach cache after DNA analysis
        await invalidate_coach_context_smart(
            str(current_user.id),
            ["dna", "sentence_analysis"]
        )
        logger.info(f"[CACHE] ✅ Invalidated TaalCoach cache after DNA analysis")

        return AnalyzeSessionResponse(
            success=True,
            breakthroughs=result["breakthroughs"],
            session_insights=result["session_insights"],
            previous_strand_values=result.get("previous_strand_values"),
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
        # Check if user has premium access (allow "canceling" status - user has access until period ends)
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing", "canceling"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription."
            )

        logger.info(f"[DNA API] Getting profile for user {current_user.id}, language {language}")

        profile = await speaking_dna_service.get_dna_profile(
            user_id=str(current_user.id),
            language=language
        )

        # 🔥 FIX: Sanitize float values to ensure JSON compliance
        if profile:
            profile = sanitize_floats(profile)

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
        # Check if user has premium access (allow "canceling" status - user has access until period ends)
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing", "canceling"]:
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

        # 🔥 FIX: Sanitize float values to ensure JSON compliance
        evolution = sanitize_floats(evolution)

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
# Acoustic Evolution Endpoint
# ============================================================================

@router.get("/acoustic-evolution/{language}")
async def get_acoustic_evolution(
    language: str,
    weeks: int = Query(default=12, ge=1, le=52, description="Number of weeks to retrieve"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the evolution history of acoustic metrics (Voice Fingerprint) over time.

    Returns weekly snapshots of acoustic metrics for visualization:
    - Vocal Pitch (Hz)
    - Voice Quality (%)
    - Speaking Rate (WPM)
    - Vocal Energy (dB)
    - Speech Fluency (filler words/min)
    - Voice Stability (shimmer %)

    **Premium Feature**: Only available to users with active subscription.

    Args:
        language: Target language code
        weeks: Number of weeks to retrieve (1-52, default 12)
        current_user: Authenticated user from JWT token

    Returns:
        List of weekly acoustic metric snapshots

    Raises:
        403: User not authorized (not premium subscriber)
        500: Server error during retrieval
    """
    try:
        # Check if user has premium access (allow "canceling" status - user has access until period ends)
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing", "canceling"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Speaking DNA is a premium feature. Please upgrade your subscription."
            )

        logger.info(f"[DNA API] Getting acoustic evolution for user {current_user.id}, language {language}, weeks {weeks}")

        evolution = await speaking_dna_service.get_acoustic_evolution(
            user_id=str(current_user.id),
            language=language,
            weeks=weeks
        )

        # 🔥 FIX: Sanitize float values to ensure JSON compliance
        evolution = sanitize_floats(evolution)

        return {
            "evolution": evolution,
            "weeks_tracked": len(evolution)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DNA API] Error getting acoustic evolution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get acoustic evolution: {str(e)}"
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
        # Check if user has premium access (allow "canceling" status - user has access until period ends)
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing", "canceling"]:
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

        # 🔥 FIX: Sanitize float values to ensure JSON compliance
        breakthroughs = sanitize_floats(breakthroughs)

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
        # Check if user has premium access (allow "canceling" status - user has access until period ends)
        if not current_user.subscription_status or current_user.subscription_status not in ["active", "trialing", "canceling"]:
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


# ============================================================================
# ADMIN ENDPOINTS (For Testing & Maintenance)
# ============================================================================

@router.post("/admin/create-weekly-snapshots")
async def create_weekly_snapshots_admin(
    admin_key: str = Query(..., description="Admin API key for authentication"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    **ADMIN ONLY**: Manually trigger weekly snapshot creation for all users.

    This endpoint is protected by admin_key and can be used to:
    - Test the weekly snapshot functionality
    - Manually trigger snapshot creation outside of scheduled cron
    - Backfill missing snapshots

    **Security:** Requires both JWT authentication AND admin API key.

    **Usage:**
    ```bash
    curl -X POST "https://api.example.com/api/speaking-dna/admin/create-weekly-snapshots?admin_key=YOUR_KEY" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```

    Args:
        admin_key: Admin API key (set via ADMIN_API_KEY env var)
        current_user: Authenticated user from JWT

    Returns:
        Summary of snapshot creation results
    """
    import os
    from database import speaking_dna_profiles_collection

    # Verify admin key
    ADMIN_KEY = os.getenv("ADMIN_API_KEY")
    if not ADMIN_KEY:
        logger.error("[DNA ADMIN] ADMIN_API_KEY environment variable not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin functionality not configured on server"
        )

    if admin_key != ADMIN_KEY:
        logger.warning(f"[DNA ADMIN] Invalid admin key attempt from user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key"
        )

    logger.info(f"[DNA ADMIN] Manual snapshot creation triggered by user {current_user.email}")

    try:
        from datetime import datetime

        start_time = datetime.utcnow()

        # Get all DNA profiles
        profiles = await speaking_dna_profiles_collection.find({}).to_list(None)
        logger.info(f"[DNA ADMIN] Found {len(profiles)} DNA profiles to process")

        results = {
            "success_list": [],
            "error_list": []
        }

        for profile in profiles:
            try:
                user_id = profile["user_id"]
                language = profile["language"]

                # Create/update weekly snapshot
                await speaking_dna_service._create_weekly_snapshot(
                    user_id=user_id,
                    language=language,
                    strands=profile.get("dna_strands", {}),
                    session_duration_minutes=0,  # No new session, just maintenance
                    breakthroughs_count=0
                )

                results["success_list"].append(f"{user_id}-{language}")
                logger.debug(f"[DNA ADMIN] ✅ Created snapshot for {user_id}-{language}")

            except Exception as e:
                error_detail = {
                    "user_language": f"{user_id}-{language}",
                    "error": str(e)
                }
                results["error_list"].append(error_detail)
                logger.error(f"[DNA ADMIN] ❌ Error for {user_id}-{language}: {str(e)}")

        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()

        summary = {
            "success": True,
            "triggered_by": current_user.email,
            "triggered_at": start_time.isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "total_profiles": len(profiles),
            "succeeded": len(results["success_list"]),
            "failed": len(results["error_list"]),
            "details": {
                "successes": results["success_list"][:10],  # First 10
                "errors": results["error_list"]
            }
        }

        if len(results["success_list"]) > 10:
            summary["details"]["note"] = f"Showing first 10 of {len(results['success_list'])} successes"

        logger.info(
            f"[DNA ADMIN] Completed. "
            f"Success: {summary['succeeded']}, "
            f"Failed: {summary['failed']}, "
            f"Duration: {duration_seconds:.1f}s"
        )

        return summary

    except Exception as e:
        logger.error(f"[DNA ADMIN] Fatal error during snapshot creation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create weekly snapshots: {str(e)}"
        )
