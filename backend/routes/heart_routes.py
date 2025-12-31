"""
Heart System API endpoints for the Focus Energy gamification feature.

Endpoints:
- GET /api/hearts/status - Get heart status for all challenge types
- GET /api/hearts/status/{challenge_type} - Get heart status for specific challenge type
- POST /api/hearts/consume - Consume heart after challenge answer
- POST /api/hearts/log-modal - Log out-of-hearts modal interaction
- POST /api/hearts/log-session-ended - Log session ended early
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from auth import get_current_user
from models import UserInDB, UserResponse
from services.heart_service import HeartService

router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RefillInfoResponse(BaseModel):
    """Refill information for hearts"""
    refill_started_at: str = Field(..., alias="refillStartedAt")
    refill_complete_at: str = Field(..., alias="refillCompleteAt")
    total_refill_minutes: int = Field(..., alias="totalRefillMinutes")
    minutes_per_heart: int = Field(..., alias="minutesPerHeart")
    next_heart_in_minutes: float = Field(..., alias="nextHeartInMinutes")
    hearts_refilled_so_far: int = Field(..., alias="heartsRefilledSoFar")

    class Config:
        populate_by_name = True
        by_alias = True


class HeartStatusResponse(BaseModel):
    """Current heart status for a specific challenge type"""
    challenge_type: str = Field(..., alias="challengeType")
    current_hearts: int = Field(..., alias="currentHearts")
    max_hearts: int = Field(..., alias="maxHearts")
    refill_in_progress: bool = Field(..., alias="refillInProgress")
    refill_info: Optional[RefillInfoResponse] = Field(None, alias="refillInfo")
    shield_active: bool = Field(..., alias="shieldActive")
    shield_expires_at: Optional[str] = Field(None, alias="shieldExpiresAt")
    current_streak: int = Field(..., alias="currentStreak")

    class Config:
        populate_by_name = True
        by_alias = True


class AllHeartsStatusResponse(BaseModel):
    """Heart status for all 6 challenge types"""
    error_spotting: HeartStatusResponse
    swipe_fix: HeartStatusResponse
    micro_quiz: HeartStatusResponse
    smart_flashcard: HeartStatusResponse
    native_check: HeartStatusResponse
    brain_tickler: HeartStatusResponse
    subscription_plan: str = Field(..., alias="subscriptionPlan")
    subscription_status: str = Field(..., alias="subscriptionStatus")

    class Config:
        populate_by_name = True
        by_alias = True


class ConsumeHeartRequest(BaseModel):
    """Request to consume heart after challenge answer"""
    challenge_type: str
    is_correct: bool
    session_id: Optional[str] = None


class ConsumeHeartResponse(BaseModel):
    """Response after consuming heart"""
    hearts_lost: bool = Field(..., alias="heartsLost")
    hearts_remaining: int = Field(..., alias="heartsRemaining")
    shield_used: bool = Field(..., alias="shieldUsed")
    shield_activated: bool = Field(..., alias="shieldActivated")
    shield_active: bool = Field(..., alias="shieldActive")
    current_streak: int = Field(..., alias="currentStreak")
    out_of_hearts: bool = Field(..., alias="outOfHearts")
    refill_info: Optional[RefillInfoResponse] = Field(None, alias="refillInfo")

    class Config:
        populate_by_name = True
        by_alias = True


class LogModalRequest(BaseModel):
    """Log out-of-hearts modal interaction"""
    challenge_type: str
    user_action: str  # "upgrade", "wait", "dismissed"
    session_id: str
    session_progress: Dict[str, int]


class LogSessionEndedRequest(BaseModel):
    """Log session ended early (quit or out of hearts)"""
    challenge_type: str
    session_id: str
    completed: int
    total: int


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/status", response_model=AllHeartsStatusResponse)
async def get_all_hearts_status(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current heart status for all 6 challenge types

    Used by iOS app on ExploreScreen to show available hearts before starting session
    """
    heart_service = HeartService()

    # Fetch full user document from database (convert string ID to ObjectId if needed)
    user_id = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    user_doc = await heart_service.db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert ObjectId to string for Pydantic model
    user_doc["_id"] = str(user_doc["_id"])
    user = UserInDB(**user_doc)

    # Ensure heart system is initialized
    if not user.heart_system:
        await heart_service.initialize_heart_system(user)
        # Refetch user after initialization
        user_doc = await heart_service.db.users.find_one({"_id": user_id})
        user_doc["_id"] = str(user_doc["_id"])
        user = UserInDB(**user_doc)

    response = {}

    for challenge_type in HeartService.CHALLENGE_TYPES:
        current_hearts, heart_pool = await heart_service.get_current_hearts(
            user.id,
            challenge_type
        )

        refill_info = None
        if heart_pool.refill_started_at:
            refill_info_dict = heart_service._get_refill_info(heart_pool)
            if refill_info_dict:
                refill_info = RefillInfoResponse(**refill_info_dict)

        shield_expires_at = None
        if heart_pool.streak_shield_active and heart_pool.streak_shield_activated_at:
            shield_expires_at = (
                heart_pool.streak_shield_activated_at + timedelta(hours=24)
            ).isoformat()

        response[challenge_type] = HeartStatusResponse(
            challenge_type=challenge_type,
            current_hearts=current_hearts,
            max_hearts=heart_pool.max_hearts,
            refill_in_progress=bool(heart_pool.refill_started_at),
            refill_info=refill_info,
            shield_active=heart_pool.streak_shield_active,
            shield_expires_at=shield_expires_at,
            current_streak=heart_pool.current_correct_streak
        )

    return AllHeartsStatusResponse(
        **response,
        subscription_plan=user.subscription_plan or "try_learn",
        subscription_status=user.subscription_status or "inactive"
    )


@router.get("/status/{challenge_type}", response_model=HeartStatusResponse)
async def get_heart_status(
    challenge_type: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current heart status for specific challenge type

    Used by iOS app before starting a session to check availability
    """
    if challenge_type not in HeartService.CHALLENGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid challenge type")

    heart_service = HeartService()

    # Fetch full user document from database (convert string ID to ObjectId if needed)
    user_id = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    user_doc = await heart_service.db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert ObjectId to string for Pydantic model
    user_doc["_id"] = str(user_doc["_id"])
    user = UserInDB(**user_doc)

    # Ensure heart system is initialized
    if not user.heart_system:
        await heart_service.initialize_heart_system(user)
        # Refetch user after initialization
        user_doc = await heart_service.db.users.find_one({"_id": user_id})
        user_doc["_id"] = str(user_doc["_id"])
        user = UserInDB(**user_doc)

    current_hearts, heart_pool = await heart_service.get_current_hearts(
        user.id,
        challenge_type
    )

    refill_info = None
    if heart_pool.refill_started_at:
        refill_info_dict = heart_service._get_refill_info(heart_pool)
        if refill_info_dict:
            refill_info = RefillInfoResponse(**refill_info_dict)

    shield_expires_at = None
    if heart_pool.streak_shield_active and heart_pool.streak_shield_activated_at:
        shield_expires_at = (
            heart_pool.streak_shield_activated_at + timedelta(hours=24)
        ).isoformat()

    return HeartStatusResponse(
        challenge_type=challenge_type,
        current_hearts=current_hearts,
        max_hearts=heart_pool.max_hearts,
        refill_in_progress=bool(heart_pool.refill_started_at),
        refill_info=refill_info,
        shield_active=heart_pool.streak_shield_active,
        shield_expires_at=shield_expires_at,
        current_streak=heart_pool.current_correct_streak
    )


@router.post("/consume", response_model=ConsumeHeartResponse)
async def consume_heart(
    request: ConsumeHeartRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Consume heart after challenge answer

    Called by iOS app after each challenge answer within a session

    This endpoint:
    1. Checks if answer is correct/wrong
    2. Updates streak counter
    3. Activates shield if 3-correct streak
    4. Consumes heart if wrong (unless shield active)
    5. Starts refill timer if hearts hit 0
    6. Returns updated heart status
    """
    if request.challenge_type not in HeartService.CHALLENGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid challenge type")

    heart_service = HeartService()

    # Fetch full user document from database (convert string ID to ObjectId if needed)
    user_id = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    user_doc = await heart_service.db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert ObjectId to string for Pydantic model
    user_doc["_id"] = str(user_doc["_id"])
    user = UserInDB(**user_doc)

    # Ensure heart system is initialized
    if not user.heart_system:
        await heart_service.initialize_heart_system(user)

    result = await heart_service.consume_heart(
        user_id=user.id,
        challenge_type=request.challenge_type,
        is_correct=request.is_correct,
        session_id=request.session_id
    )

    # Convert refill_info dict to RefillInfoResponse if present
    if result.get("refill_info"):
        result["refill_info"] = RefillInfoResponse(**result["refill_info"])

    return ConsumeHeartResponse(**result)


@router.post("/log-modal")
async def log_out_of_hearts_modal(
    request: LogModalRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Log when user interacts with out-of-hearts modal

    Called by iOS app when:
    - Modal is shown (user_action: "shown")
    - User clicks "Upgrade" (user_action: "upgrade")
    - User clicks "Wait" (user_action: "wait")
    - User dismisses modal (user_action: "dismissed")
    """
    heart_service = HeartService()

    await heart_service.log_out_of_hearts_modal(
        user_id=current_user.id,
        challenge_type=request.challenge_type,
        user_action=request.user_action,
        session_id=request.session_id,
        session_progress=request.session_progress
    )

    return {"success": True}


@router.post("/log-session-ended")
async def log_session_ended_early(
    request: LogSessionEndedRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Log when session ends early due to no hearts or user quit

    Called by iOS app when session is terminated due to:
    - 0 hearts (out of hearts)
    - User quit voluntarily
    """
    heart_service = HeartService()

    await heart_service.log_session_ended_early(
        user_id=current_user.id,
        challenge_type=request.challenge_type,
        session_id=request.session_id,
        session_progress={"completed": request.completed, "total": request.total}
    )

    return {"success": True}


@router.post("/sync-with-subscription")
async def sync_hearts_with_subscription(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Manually sync heart system with current subscription plan

    This endpoint updates heart max_hearts and refill_rate based on the user's
    current subscription_plan. Useful when:
    - User upgrades subscription but hearts weren't updated
    - Fixing sync issues between Stripe and heart system

    Should be called by iOS app after successful subscription upgrade
    """
    heart_service = HeartService()

    # Fetch full user document from database
    user_id = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    user_doc = await heart_service.db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    current_plan = user_doc.get("subscription_plan", "try_learn")

    # Update hearts for the new subscription plan
    # This will upgrade max_hearts and refill_rate_minutes for all challenge types
    await heart_service.update_hearts_on_subscription_change(
        user_id=str(user_id),
        old_plan="try_learn",  # Assume upgrade from free
        new_plan=current_plan
    )

    return {
        "success": True,
        "subscription_plan": current_plan,
        "message": f"Heart system synced with {current_plan} plan"
    }
