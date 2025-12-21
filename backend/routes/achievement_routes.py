"""
Achievement persistence API endpoints for the gamified challenge system.

Endpoints:
- POST /api/achievements/unlock - Unlock an achievement
- GET /api/achievements - Get user's unlocked achievements
- POST /api/achievements/sessions/complete - Complete a challenge session
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.exceptions import RequestValidationError
import json
from typing import List
from datetime import datetime

from auth import get_current_user
from database import user_achievements_collection, challenge_sessions_collection
from models import (
    UserInDB,
    AchievementUnlockRequest,
    UserAchievementInDB,
    UserAchievementResponse,
    UserAchievementsResponse,
    ChallengeSessionComplete,
    AchievementBase
)

router = APIRouter()

# Available achievements (static data)
ACHIEVEMENTS = {
    "perfect_session": {
        "id": "perfect_session",
        "title": "Perfect Session",
        "description": "Complete a session with 100% accuracy",
        "icon": "🎯",
        "xpBonus": 100
    },
    "speed_demon": {
        "id": "speed_demon",
        "title": "Speed Demon",
        "description": "Answer all challenges in under 10 seconds each",
        "icon": "⚡",
        "xpBonus": 75
    },
    "combo_master": {
        "id": "combo_master",
        "title": "Combo Master",
        "description": "Reach a 5x combo streak",
        "icon": "🔥",
        "xpBonus": 50
    },
    "ultimate_combo": {
        "id": "ultimate_combo",
        "title": "Ultimate Combo",
        "description": "Reach a 10x combo streak",
        "icon": "💥",
        "xpBonus": 150
    },
}


@router.post("/api/achievements/unlock")
async def unlock_achievement(
    request: AchievementUnlockRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Unlock an achievement for the current user."""
    try:
        achievement_id = request.achievement_id

        # Validate achievement exists
        if achievement_id not in ACHIEVEMENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Achievement '{achievement_id}' does not exist"
            )

        # Check if user already has this achievement
        existing = await user_achievements_collection.find_one({
            "user_id": current_user.id,
            "achievement_id": achievement_id
        })

        if existing:
            # Already unlocked, return existing
            achievement_data = ACHIEVEMENTS[achievement_id]
            return {
                "success": True,
                "already_unlocked": True,
                "achievement": {
                    **achievement_data,
                    "unlocked_at": existing["unlocked_at"],
                    "session_id": existing.get("session_id")
                }
            }

        # Create new achievement unlock
        achievement_doc = UserAchievementInDB(
            user_id=current_user.id,
            achievement_id=achievement_id,
            unlocked_at=datetime.utcnow(),
            session_id=request.session_id
        )

        result = await user_achievements_collection.insert_one(achievement_doc.dict(by_alias=True))

        if result.inserted_id:
            achievement_data = ACHIEVEMENTS[achievement_id]
            return {
                "success": True,
                "already_unlocked": False,
                "achievement": {
                    **achievement_data,
                    "unlocked_at": achievement_doc.unlocked_at,
                    "session_id": achievement_doc.session_id
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unlock achievement"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error unlocking achievement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unlocking achievement: {str(e)}"
        )


@router.get("/api/achievements", response_model=UserAchievementsResponse)
async def get_user_achievements(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all achievements unlocked by the current user."""
    try:
        # Fetch all user achievements
        cursor = user_achievements_collection.find({"user_id": current_user.id})
        user_achievements = await cursor.to_list(length=None)

        # Enrich with achievement data
        achievements_response = []
        total_xp = 0

        for ua in user_achievements:
            achievement_id = ua["achievement_id"]
            if achievement_id in ACHIEVEMENTS:
                achievement_data = ACHIEVEMENTS[achievement_id]
                achievements_response.append(
                    UserAchievementResponse(
                        id=achievement_data["id"],
                        title=achievement_data["title"],
                        description=achievement_data["description"],
                        icon=achievement_data["icon"],
                        xpBonus=achievement_data["xpBonus"],
                        unlocked_at=ua["unlocked_at"],
                        session_id=ua.get("session_id")
                    )
                )
                total_xp += achievement_data["xpBonus"]

        return UserAchievementsResponse(
            achievements=achievements_response,
            total_count=len(achievements_response),
            total_xp=total_xp
        )

    except Exception as e:
        print(f"❌ Error fetching achievements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching achievements: {str(e)}"
        )


@router.post("/api/achievements/sessions/complete")
async def complete_challenge_session(
    raw_request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Complete a challenge session and unlock achievements.
    Called when user finishes a gamified challenge session.
    """
    try:
        # Parse request body
        body = await raw_request.json()
        print(f"📥 Received request body: {json.dumps(body, indent=2)}")

        # Validate request
        try:
            request = ChallengeSessionComplete(**body)
        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            print(f"❌ Body received: {json.dumps(body, indent=2)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {str(e)}"
            )

        session_id = request.session_id

        # Find the session
        session = await challenge_sessions_collection.find_one({"_id": session_id})

        if not session:
            # Session doesn't exist yet (client-side generated ID)
            # Create a new session record
            session_doc = {
                "_id": session_id,
                "user_id": current_user.id,
                "correct_answers": request.correct_answers,
                "wrong_answers": request.wrong_answers,
                "max_combo": request.max_combo,
                "total_xp": request.total_xp,
                "answer_times": request.answer_times,
                "is_active": False,
                "created_at": datetime.utcnow(),
                "end_time": datetime.utcnow()
            }
            await challenge_sessions_collection.insert_one(session_doc)
            print(f"✅ Created new session record: {session_id}")
        else:
            # Verify session belongs to current user
            if session.get("user_id") != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to complete this session"
                )

            # Update existing session with completion data
            update_result = await challenge_sessions_collection.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "correct_answers": request.correct_answers,
                        "wrong_answers": request.wrong_answers,
                        "max_combo": request.max_combo,
                        "total_xp": request.total_xp,
                        "answer_times": request.answer_times,
                        "is_active": False,
                        "end_time": datetime.utcnow()
                    }
                }
            )

            if update_result.modified_count == 0:
                print(f"⚠️ Warning: Session {session_id} was not updated")

        # Unlock achievements
        unlocked_achievements = []
        for achievement_id in request.achievements:
            if achievement_id in ACHIEVEMENTS:
                # Check if already unlocked
                existing = await user_achievements_collection.find_one({
                    "user_id": current_user.id,
                    "achievement_id": achievement_id
                })

                if not existing:
                    # Unlock new achievement
                    achievement_doc = UserAchievementInDB(
                        user_id=current_user.id,
                        achievement_id=achievement_id,
                        unlocked_at=datetime.utcnow(),
                        session_id=session_id
                    )

                    await user_achievements_collection.insert_one(achievement_doc.dict(by_alias=True))

                    achievement_data = ACHIEVEMENTS[achievement_id]
                    unlocked_achievements.append({
                        **achievement_data,
                        "unlocked_at": achievement_doc.unlocked_at
                    })

                    print(f"🏆 Achievement unlocked: {achievement_id} for user {current_user.id}")

        return {
            "success": True,
            "session_id": session_id,
            "unlocked_achievements": unlocked_achievements,
            "total_xp": request.total_xp
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error completing challenge session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing challenge session: {str(e)}"
        )


@router.get("/api/achievements/available")
async def get_available_achievements():
    """Get list of all available achievements (public endpoint)."""
    return {
        "achievements": list(ACHIEVEMENTS.values()),
        "total_count": len(ACHIEVEMENTS)
    }
