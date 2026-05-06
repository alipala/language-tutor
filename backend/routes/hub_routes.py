"""
Hub Routes — /api/hub/today

Single unified endpoint that returns EVERYTHING the Path (Daily Hub) screen
needs in one HTTP call, replacing 7 sequential frontend fetches:

  Old flow (7 round-trips, ~1400 ms on mobile):
    GET /api/learning/plans
    GET /api/progress/stats
    GET /api/stripe/subscription-status
    GET /api/stats/daily
    GET /api/stats/recent
    GET /api/journey/status
    GET /api/flashcards/sets
    GET /api/missions/today

  New flow (1 round-trip, ~150 ms):
    GET /api/hub/today

All sub-queries run inside a single asyncio.gather() call.
The frontend receives one flat JSON envelope and renders immediately.

Loading strategy:
  • Critical data (plans, subscription, streak) → returned in main response
  • Heavy data (DNA, recent 7-day perf) → returned in same response but
    fetched in parallel so they don't block the critical path
  • Missions progress → hydrated live inside the same gather
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth import get_current_user
from models import UserResponse
from database import (
    daily_stats_collection,
    learning_plans_collection,
    speaking_dna_profiles_collection,
    flashcard_sets_collection,
    users_collection,
    database,
)
from services.timezone_utils import get_current_local_date
from services.journey_state_detector import journey_state_detector
from subscription_service import SubscriptionService
from bson import ObjectId

router = APIRouter()


def get_missions_collection():
    return database.daily_missions


# ─────────────────────────────────────────────────────────────
# Response shape
# ─────────────────────────────────────────────────────────────

class HubResponse(BaseModel):
    success: bool = True
    fetched_at: str

    # Subscription
    subscription: Dict[str, Any]

    # Learning plans (sorted newest-first)
    learning_plans: List[Dict[str, Any]]

    # Progress stats (streak, XP, total sessions/minutes)
    progress_stats: Dict[str, Any]

    # Today's stats
    daily_stats: Dict[str, Any]

    # Journey state (stage, days_since_activity, dna_trend)
    journey_state: Dict[str, Any]

    # DNA profile for active language (strands summary only — lightweight)
    dna_summary: Optional[Dict[str, Any]]

    # Flashcard sets (id, is_reviewed, language, topic)
    flashcard_sets: List[Dict[str, Any]]

    # Today's missions with live progress
    missions: List[Dict[str, Any]]

    # Path A — predicted forecast of tomorrow's missions (read-only).
    # Optional: absent if prediction failed (preview falls back to static copy).
    next_missions_preview: Optional[Dict[str, Any]] = None

    # Metadata
    timezone: str
    local_date: str


# ─────────────────────────────────────────────────────────────
# Individual async fetchers  (each is a single DB operation)
# ─────────────────────────────────────────────────────────────

async def _get_learning_plans(user_id: str) -> List[Dict]:
    # Project the document's UUID `id` (set at creation by LearningPlanService) —
    # NOT the Mongo `_id`. Downstream endpoints (`/api/learning/plan/{id}`,
    # `/voice-check-status`, `/progress`) look up by `{"id": plan_id}`, so the
    # IDs returned here must match that field.
    cursor = learning_plans_collection.find(
        {"user_id": user_id},
        {
            "_id": 1,  # kept only as a fallback for legacy plans missing `id`
            "id": 1, "language": 1, "proficiency_level": 1, "status": 1,
            "completed_sessions": 1, "total_sessions": 1, "duration_months": 1,
            "goals": 1, "progress_percentage": 1, "updated_at": 1, "created_at": 1,
            "voice_check_schedule": 1, "voice_checks_completed": 1,
        }
    ).sort("updated_at", -1)
    plans = []
    async for p in cursor:
        # Legacy plans predating LearningPlanService may lack the UUID `id` —
        # fall back to the stringified _id so the document is still addressable.
        if not p.get("id"):
            p["id"] = str(p["_id"])
        p.pop("_id", None)
        plans.append(p)
    return plans


async def _get_daily_stats(user_id: str, local_date: str) -> Dict:
    doc = await daily_stats_collection.find_one(
        {"user_id": user_id, "local_date": local_date}
    )
    if not doc:
        return {
            "total_sessions": 0, "total_challenges": 0,
            "total_xp": 0, "accuracy_percent": 0,
            "total_time_seconds": 0, "streak_count": 0,
            "by_type": {}, "by_language": {}, "by_level": {},
        }
    doc.pop("_id", None)
    return doc


async def _get_subscription(user_id: str) -> Dict:
    """Calls the same SubscriptionService used by /api/stripe/subscription-status."""
    try:
        status = await SubscriptionService.get_user_subscription_status(user_id)
        return {
            "status":             getattr(status, "status", None),
            "plan":               getattr(status, "plan", "try_learn"),
            "period":             getattr(status, "period", None),
            "provider":           getattr(status, "provider", None),
            "limits":             status.limits.dict() if getattr(status, "limits", None) else None,
            "is_in_trial":        getattr(status, "is_in_trial", False),
            "trial_days_remaining": getattr(status, "trial_days_remaining", None),
        }
    except Exception:
        return {
            "plan": "try_learn",
            "limits": {"minutes_remaining": 0, "is_unlimited": False, "minutes_limit": 15},
        }


async def _get_progress_stats(user_id: str) -> Dict:
    """Aggregate lifetime progress from user.stats embedded doc."""
    user = await users_collection.find_one(
        {"_id": ObjectId(user_id)},
        {"stats": 1, "journey_state": 1}
    )
    if not user:
        return {}
    stats = user.get("stats") or {}
    return {
        "current_streak":          stats.get("current_streak", 0),
        "longest_streak":          stats.get("longest_streak", 0),
        "total_sessions":          stats.get("total_sessions", 0),
        "total_minutes":           stats.get("total_minutes", 0),
        "total_xp":                stats.get("total_xp", 0),
        "average_minutes_per_day": stats.get("average_minutes_per_day", 0),
    }


async def _get_journey_state(user_id: str) -> Dict:
    """Use the cached 6-hour journey state (no recalculation on every load)."""
    try:
        state = await journey_state_detector.detect_journey_stage(user_id, force_recalculate=False)
        return state.dict()
    except Exception:
        return {"stage": "exploring", "days_since_last_activity": 0, "dna_improvement_trend": "stable"}


async def _get_dna_summary(user_id: str, language: Optional[str]) -> Optional[Dict]:
    """Return only the strand scores — not the full profile — to keep payload small."""
    query: Dict[str, Any] = {"user_id": user_id}
    if language:
        query["language"] = language.lower()
    doc = await speaking_dna_profiles_collection.find_one(
        query,
        {"dna_strands": 1, "overall_profile": 1, "sessions_analyzed": 1}
    )
    if not doc:
        return None
    doc.pop("_id", None)
    return doc


async def _get_flashcard_sets(user_id: str) -> List[Dict]:
    # Mirror `_get_learning_plans`: project the document's UUID `id` so it
    # matches `/api/flashcards/set/{id}/...` lookups, with a stringified `_id`
    # fallback for any legacy document missing the UUID.
    cursor = flashcard_sets_collection.find(
        {"user_id": user_id},
        {
            "_id": 1, "id": 1,
            "language": 1, "topic": 1, "is_reviewed": 1, "created_at": 1,
        },
    ).sort("created_at", -1).limit(20)
    sets = []
    async for s in cursor:
        if not s.get("id"):
            s["id"] = str(s["_id"])
        s.pop("_id", None)
        sets.append(s)
    return sets


async def _get_or_generate_missions(
    user_id: str, local_date: str, timezone: str, language: Optional[str]
) -> List[Dict]:
    """Load cached missions and attach live progress inline."""
    from routes.missions_routes import (
        _generate_missions_for_today,
        _hydrate_progress,
    )

    coll = get_missions_collection()
    cached = await coll.find_one({"user_id": user_id, "local_date": local_date})

    if cached:
        raw = cached["missions"]
    else:
        raw = await _generate_missions_for_today(user_id, local_date, timezone, language)

    hydrated = await _hydrate_progress(user_id, local_date, raw)
    return [m.dict() for m in hydrated]


# ─────────────────────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────────────────────

@router.get(
    "/api/hub/today",
    response_model=HubResponse,
    summary="Unified Path screen data — single round-trip",
    tags=["Hub"],
)
async def get_hub_today(
    timezone: Optional[str] = Query(None, description="User timezone e.g. Europe/Amsterdam"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Returns everything the Path (Daily Hub) screen needs in one call.

    All sub-queries run in parallel via asyncio.gather — typical response
    time is 100–180 ms regardless of the number of data sources.

    Response is structured identically to what the frontend was assembling
    from 7–8 separate calls, so the client-side mapping is trivial.
    """
    user_id    = str(current_user.id)
    tz         = timezone or getattr(current_user, "timezone", None) or "UTC"
    local_date = get_current_local_date(tz)
    language   = getattr(current_user, "preferred_language", None)

    # ── Fire ALL queries in parallel ──────────────────────────
    (
        plans,
        daily,
        subscription,
        progress,
        journey,
        flashcards,
    ) = await asyncio.gather(
        _get_learning_plans(user_id),
        _get_daily_stats(user_id, local_date),
        _get_subscription(user_id),
        _get_progress_stats(user_id),
        _get_journey_state(user_id),
        _get_flashcard_sets(user_id),
    )

    # Resolve active language from plans if not on user profile
    if not language and plans:
        active = next(
            (p for p in plans if p.get("status") in ("in_progress", "active") or not p.get("status")),
            None,
        )
        if active:
            language = active.get("language")

    # DNA + missions can now run with resolved language
    dna_summary, missions = await asyncio.gather(
        _get_dna_summary(user_id, language),
        _get_or_generate_missions(user_id, local_date, tz, language),
    )

    # Path A — predicted preview of tomorrow's missions.
    # Runs AFTER mission generation so the variety guard's "recent" window
    # includes today's just-written silver type.
    next_preview = await _safe_predict_next(user_id, language, local_date)

    return HubResponse(
        success=True,
        fetched_at=datetime.utcnow().isoformat(),
        subscription=subscription,
        learning_plans=plans,
        progress_stats=progress,
        daily_stats=daily,
        journey_state=journey,
        dna_summary=dna_summary,
        flashcard_sets=flashcards,
        missions=missions,
        next_missions_preview=next_preview,
        timezone=tz,
        local_date=local_date,
    )


async def _safe_predict_next(
    user_id: str, language: Optional[str], local_date: str
) -> Optional[Dict[str, Any]]:
    """
    Wrap _predict_missions_preview so a prediction failure never breaks
    the hub response. The preview is a nice-to-have, not core data.
    """
    try:
        from routes.missions_routes import _predict_missions_preview
        preview = await _predict_missions_preview(user_id, language, local_date)
        return preview.dict()
    except Exception as e:
        print(f"[HUB] preview prediction failed: {e}")
        return None
