"""
Achievement persistence API endpoints for the gamified challenge system.

Endpoints:
- POST /api/achievements/unlock - Unlock an achievement
- GET /api/achievements - Get user's unlocked achievements
- POST /api/achievements/sessions/complete - Complete a challenge session
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
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

        # Process session completion for statistics — gated on the explicit
        # `abandoned` flag declared by the client (mobile's quit-path sets this
        # to True only when the user opened a tile and quit without answering
        # any questions). The audit row is already persisted above; what we
        # gate here is the downstream stats / streak orchestration so a
        # 0-engagement abandon never advances the user's totals.
        #
        # Server-side hardening: honor the skip ONLY when the totals
        # corroborate it (total_challenges == 0). A future mis-flagging
        # client cannot silently discard a session that contained real work.
        is_corroborated_abandon = bool(request.abandoned) and total_challenges == 0
        if is_corroborated_abandon:
            print(
                f"[STATS] ⏭️  Skipping stats/streak for session {session_id} — "
                f"client-flagged abandon (challenges=0, xp={request.total_xp})"
            )
        else:
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
        # Check if this is the user's first completed session.
        #
        # IMPORTANT: the mobile quit-path also hits /complete-session with
        # zeros (correct_answers=0, wrong_answers=0, total_xp=0) so it can
        # persist the abandoned-session record. Without this gate, a user
        # who taps a challenge tile and backs out without answering would
        # receive a misleading "Great First Session! 🎉 You earned 0 XP!"
        # push notification.
        #
        # We treat a session as "real" when it was NOT a corroborated
        # abandon (mirrors the stats-orchestration gate above). A wrong
        # answer still counts as a real first session — the user engaged
        # even though they earned 0 XP — so they still get the welcome.
        is_real_first_session = not is_corroborated_abandon

        total_sessions = await challenge_sessions_collection.count_documents({
            "user_id": current_user.id,
            "is_active": False  # Only count completed sessions
        })

        if is_real_first_session and total_sessions == 1:  # First REAL session just completed
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
                        from notification_service import NotificationService, get_notification_strings
                        notification_service = NotificationService()

                        # Localise notification using user's UI language preference
                        user_locale = user_doc.get("app_language") or "en"
                        ns = get_notification_strings(user_locale)
                        notif_title = ns["first_session_title"]
                        notif_body = ns["first_session_body"].format(xp=request.total_xp)

                        # Send push notification
                        result = notification_service.send_expo_push_notification(
                            push_tokens=[push_token],
                            title=notif_title,
                            body=notif_body,
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


# ============================================================================
# YOU-TAB BADGE SYNC (server-authoritative "earned forever" store)
# ============================================================================
#
# The mobile "You" tab derives 180+ badges live from the user's own stats
# (deriveBadges(ctx)). Historically the "once earned, stays earned" flag lived
# ONLY in the device's AsyncStorage — so a badge could vanish on reinstall,
# differ across devices, or (worse) show badges the backend data no longer
# supports (a stale device store outliving a data reset). These endpoints move
# that earned-flag into the DB so it is device-independent and reconcilable.
#
# Storage: we REUSE the existing `user_achievements` collection. A You-tab
# badge is just a row whose `achievement_id` is the badge id (e.g. "streak_7")
# or a scope-suffixed id ("confidence_fluent@dutch"). This coexists with the
# 4 legacy challenge achievements (perfect_session, …) in the same collection
# WITHOUT collision — the id spaces are disjoint.
#
# CRITICAL RULE — renewable badges are NEVER persisted here. Their mobile
# earned-key embeds a period stamp ("daily_check_in@2026-07-01",
# "on_the_rise@2026-W27", "monthly_sprint@2026-07"). Persisting them would
# add unbounded rows per user and, worse, force-earn a badge whose window has
# closed. We detect and reject any id whose suffix matches a period stamp so a
# buggy/old client can never write one. Renewables stay live-derived only.

import re as _re

# Matches the period-stamp suffixes produced by badgeEarnedStore.periodStamp:
#   daily  -> @YYYY-MM-DD   weekly -> @YYYY-Www   monthly -> @YYYY-MM
# A plain scoped suffix like "@dutch" (a language) does NOT match, so scoped
# DNA/CEFR badges persist correctly while renewables are filtered out.
_RENEWABLE_SUFFIX = _re.compile(r"@\d{4}-(\d{2}-\d{2}|W\d{2}|\d{2})$")


def _is_renewable_key(badge_id: str) -> bool:
    return bool(_RENEWABLE_SUFFIX.search(badge_id or ""))


class BadgeSyncRequest(BaseModel):
    """Client posts the full set of PERMANENT earned badge ids it currently
    holds. The server upserts any it hasn't recorded yet (idempotent). We do
    NOT delete rows the client omits — a badge, once earned, stays earned; the
    client simply may not have re-derived it this session."""
    earned: List[str]


@router.post("/api/badges/sync")
async def sync_badges(
    request: BadgeSyncRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """Idempotently persist the user's earned You-tab badges to the DB.

    - Renewable (period-stamped) ids are silently skipped — never stored.
    - Empty / duplicate ids are ignored.
    - Uses upsert on (user_id, achievement_id) so repeated syncs are no-ops.
    """
    try:
        # Sanitize: drop blanks, renewables, and de-dupe while preserving that
        # a legacy challenge achievement re-synced here is harmless (same row).
        seen = set()
        to_write = []
        skipped_renewable = 0
        for raw in request.earned:
            bid = (raw or "").strip()
            if not bid or bid in seen:
                continue
            seen.add(bid)
            if _is_renewable_key(bid):
                skipped_renewable += 1
                continue
            to_write.append(bid)

        now = datetime.utcnow()
        written = 0
        for bid in to_write:
            # Upsert: insert only if this (user, badge) pair is new. $setOnInsert
            # preserves the ORIGINAL unlocked_at on repeat syncs.
            result = await user_achievements_collection.update_one(
                {"user_id": current_user.id, "achievement_id": bid},
                {"$setOnInsert": {
                    "user_id": current_user.id,
                    "achievement_id": bid,
                    "unlocked_at": now,
                    "session_id": None,
                }},
                upsert=True,
            )
            if result.upserted_id is not None:
                written += 1

        return {
            "success": True,
            "written": written,
            "skipped_renewable": skipped_renewable,
            "received": len(request.earned),
        }
    except Exception as e:
        print(f"❌ Error syncing badges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing badges: {str(e)}",
        )


@router.get("/api/badges")
async def get_earned_badges(
    current_user: UserInDB = Depends(get_current_user),
):
    """Return the flat list of earned badge ids for the current user.

    This is the device-independent source of truth the You tab hydrates from
    (falling back to its local AsyncStorage cache only when this call fails).
    Returns BOTH the legacy 4 challenge achievements and the You-tab badge ids
    — the client's earned-store keys on the same id space, so it just works.
    Renewable ids are never present here (they're never written)."""
    try:
        cursor = user_achievements_collection.find(
            {"user_id": current_user.id},
            {"achievement_id": 1, "unlocked_at": 1, "_id": 0},
        )
        rows = await cursor.to_list(length=None)
        earned = {}
        for r in rows:
            bid = r.get("achievement_id")
            if not bid:
                continue
            ua = r.get("unlocked_at")
            earned[bid] = ua.isoformat() if hasattr(ua, "isoformat") else ua
        return {
            "success": True,
            "earned": list(earned.keys()),
            "earned_at": earned,  # {id: iso-date} — lets the client seed its cache
            "total": len(earned),
        }
    except Exception as e:
        print(f"❌ Error fetching earned badges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching earned badges: {str(e)}",
        )
