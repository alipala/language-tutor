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
from database import user_achievements_collection, challenge_sessions_collection, users_collection
from models import (
    UserInDB,
    AchievementUnlockRequest,
    UserAchievementInDB,
    UserAchievementResponse,
    UserAchievementsResponse,
    ChallengeSessionComplete,
    AchievementBase
)
from services.timezone_utils import convert_to_local_date
from services.stats_service import process_session_completion
from bson import ObjectId

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

        # Get user's timezone from profile or request
        user_timezone = request.user_timezone or current_user.timezone or "UTC"

        # Calculate derived fields
        end_time = datetime.utcnow()
        total_challenges = request.correct_answers + request.wrong_answers
        accuracy = (request.correct_answers / total_challenges * 100) if total_challenges > 0 else 0

        if not session:
            # Session doesn't exist yet (client-side generated ID)
            # This shouldn't happen normally, but handle it gracefully
            print(f"⚠️ Warning: Session {session_id} not found, creating minimal record")

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
                "end_time": end_time,

                # NEW: Required fields for stats (use client values or defaults)
                "language": request.language or "unknown",
                "level": request.level or "B1",
                "challenge_type": request.challenge_type or "unknown",
                "source": "freestyle",  # Freestyle practice since no session exists
                "total_challenges": total_challenges,
                "accuracy": accuracy,
                "duration_seconds": 0,
                "user_timezone": user_timezone,
                "local_date": convert_to_local_date(datetime.utcnow(), user_timezone),
                "start_time": datetime.utcnow(),

                # NEW: Store challenge IDs for completion tracking
                "challenge_ids": request.challenge_ids or []
            }
            await challenge_sessions_collection.insert_one(session_doc)
            session = session_doc
            print(f"✅ Created new session record: {session_id}")
        else:
            # Verify session belongs to current user
            if session.get("user_id") != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to complete this session"
                )

            # Calculate duration
            start_time = session.get("start_time", datetime.utcnow())
            duration_seconds = (end_time - start_time).total_seconds()

            # Calculate local_date using timezone
            local_date = convert_to_local_date(end_time, user_timezone)

            # Update existing session with completion data
            update_fields = {
                "correct_answers": request.correct_answers,
                "wrong_answers": request.wrong_answers,
                "max_combo": request.max_combo,
                "total_xp": request.total_xp,
                "answer_times": request.answer_times,
                "is_active": False,
                "end_time": end_time,

                # NEW: Pre-calculated fields for statistics
                "total_challenges": total_challenges,
                "accuracy": accuracy,
                "duration_seconds": duration_seconds,
                "user_timezone": user_timezone,
                "local_date": local_date,

                # NEW: Store challenge IDs for completion tracking
                "challenge_ids": request.challenge_ids or []
            }

            # Update language/level/type if provided by client (overrides existing values)
            if request.language:
                update_fields["language"] = request.language
            if request.level:
                update_fields["level"] = request.level
            if request.challenge_type:
                update_fields["challenge_type"] = request.challenge_type

            update_result = await challenge_sessions_collection.update_one(
                {"_id": session_id},
                {"$set": update_fields}
            )

            if update_result.modified_count == 0:
                print(f"⚠️ Warning: Session {session_id} was not updated")

            # Fetch updated session for stats processing
            session = await challenge_sessions_collection.find_one({"_id": session_id})

        # NEW: Process session completion for statistics
        try:
            await process_session_completion(session)
            print(f"[STATS] ✅ Statistics updated for session {session_id}")
        except Exception as e:
            print(f"[STATS] ❌ Error updating statistics: {str(e)}")
            # Don't fail the request if stats update fails

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

        # ===== FIRST SESSION WELCOME NOTIFICATION =====
        # Check if this is the user's first completed session
        total_sessions = await challenge_sessions_collection.count_documents({
            "user_id": current_user.id,
            "is_active": False  # Only count completed sessions
        })

        if total_sessions == 1:  # First session just completed
            print(f"🎉 First session completed for user {current_user.id}!")

            # Check notification preferences
            from database import notification_preferences_collection, users_collection
            prefs = await notification_preferences_collection.find_one({"user_id": current_user.id})

            # Default to True if no preferences set (matches default for achievement_alerts)
            send_notification = True
            if prefs:
                send_notification = prefs.get("achievement_alerts_enabled", True)

            if send_notification:
                # Fetch full user document to get push_token
                from bson import ObjectId
                user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
                user_doc = await users_collection.find_one({"_id": user_id_obj})

                if user_doc and user_doc.get("push_token"):
                    push_token = user_doc["push_token"]
                    print(f"📤 Sending first session welcome notification to user {current_user.id}")

                    try:
                        from notification_service import NotificationService
                        notification_service = NotificationService()

                        # Send push notification
                        result = notification_service.send_expo_push_notification(
                            push_tokens=[push_token],
                            title="Great First Session! 🎉",
                            body=f"You earned {request.total_xp} XP! Come back tomorrow to build your streak.",
                            data={
                                "type": "first_session_welcome",
                                "session_id": session_id,
                                "xp_earned": request.total_xp
                            },
                            priority="default"
                        )

                        if result.get("success"):
                            print(f"✅ First session welcome notification sent successfully")
                        else:
                            print(f"⚠️ Failed to send first session welcome notification: {result.get('message')}")

                    except Exception as notif_error:
                        print(f"❌ Error sending first session welcome notification: {str(notif_error)}")
                        # Don't fail the session completion if notification fails
                else:
                    print(f"⚠️ No push token for user {current_user.id}, skipping notification")
            else:
                print(f"⚠️ User {current_user.id} has achievement alerts disabled, skipping notification")
        # ===== END FIRST SESSION WELCOME NOTIFICATION =====

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
