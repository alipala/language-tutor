"""
Profile Story V1 — backend route.

Additive endpoint feeding the new mobile per-language storytelling screen.
Behind the mobile-side `PROFILE_STORY_V1` flag, but the endpoint itself is
unconditional (purely read; no existing contract changed).

Endpoints:
  - GET /api/profile/story
      ?language=<canonical|iso|english-name>    (optional; omit for All)
      ?before=<iso>                              (paginate older moments)
      ?limit=<int, 1..100, default 20>           (cap older group)

Never 500s on sparse data. Composes existing services + the new
services/profile_story/* modules.
"""

from datetime import datetime
from typing import Any, Optional
import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, HTTPException, status

from auth import get_current_user
from models import UserResponse

from database import (
    users_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,
    learning_plans_collection,
    daily_stats_collection,
    speaking_breakthroughs_collection,
    notification_preferences_collection,
    speaking_time_tracking_collection,
    flashcards_collection,
)

from services.profile_story.language_normalizer import (
    canonical_code,
    canonical_name,
    normalize_language,
)
from services.profile_story.timezone_resolver import resolve_user_timezone
from services.profile_story.confidence_ladder import compute_confidence
from services.profile_story.rhythm_streak import build_rhythm_and_streak
from services.profile_story.memory_mapper import build_story, RECENT_SESSIONS_BOUND
from services.profile_story.proof_builder import build_proof

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])

PREMIUM_STATUSES = {"active", "trialing", "canceling"}


@router.get("/story")
async def get_profile_story(
    language: Optional[str] = Query(None, description="ISO code or English name; omit for All"),
    before: Optional[str] = Query(None, description="ISO datetime cursor for older-moments pagination"),
    limit: int = Query(20, ge=1, le=100, description="Cap on older-group moments"),
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """
    Build the per-language Profile Story response.

    Returns a 200 with safe defaults for new users and sparse data —
    NEVER 500s on missing fields. See module docstring for shape.
    """
    user_id = str(current_user.id)

    # ── User doc ──────────────────────────────────────────────────────────
    user_doc: dict = {}
    try:
        if users_collection is not None:
            user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}) or {}
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] users.find_one failed for {user_id}: {e}")
        user_doc = {}

    # ── Timezone ──────────────────────────────────────────────────────────
    tz = await resolve_user_timezone(
        user_id=user_id,
        user_doc=user_doc,
        notification_preferences_collection=notification_preferences_collection,
        daily_stats_collection=daily_stats_collection,
    )

    # ── Languages discovered from session collections (truth, not lifetime) ─
    discovered = await _discover_languages(
        user_id=user_id,
        user_doc=user_doc,
    )

    # ── Selected language ────────────────────────────────────────────────
    selected_canon = normalize_language(language) if language else None
    selected_code: Optional[str] = selected_canon["code"] if selected_canon else None

    # If the caller specified a language we don't know about for this user,
    # we still honor it (returns empty per-language scopes). No 4xx noise.

    # ── Confidence ───────────────────────────────────────────────────────
    recent_sessions = await _recent_sessions_for_confidence(
        user_id=user_id,
        language=selected_canon["name"] if selected_canon else None,
    )
    journey_state = (user_doc.get("journey_state") or None)
    confidence = compute_confidence(
        recent_sessions=recent_sessions,
        journey_state=journey_state,
    )

    # ── Rhythm + streaks ─────────────────────────────────────────────────
    rs = await build_rhythm_and_streak(
        user_id=user_id,
        timezone_str=tz,
        language=selected_canon["name"] if selected_canon else None,
        daily_stats_collection=daily_stats_collection,
        conversation_sessions_collection=conversation_sessions_collection,
        challenge_sessions_collection=challenge_sessions_collection,
    )

    # ── Story ────────────────────────────────────────────────────────────
    story = await build_story(
        user_id=user_id,
        user_doc=user_doc,
        language=selected_canon["name"] if selected_canon else None,
        timezone_str=tz,
        before=before,
        limit=limit,
        conversation_sessions_collection=conversation_sessions_collection,
        challenge_sessions_collection=challenge_sessions_collection,
        speaking_breakthroughs_collection=speaking_breakthroughs_collection,
        learning_plans_collection=learning_plans_collection,
    )

    # ── Proof (always GLOBAL / all-time — does NOT re-scope by language) ─
    # Grid + next-milestone bar both source from `lifetime.*` so they can
    # never disagree (the dev-test bug we just fixed).
    proof = await build_proof(
        user_id=user_id,
        user_doc=user_doc,
        current_streak=rs["current_streak"],
        longest_streak=rs["longest_streak"],
        users_collection=users_collection,
        speaking_time_tracking_collection=speaking_time_tracking_collection,
        flashcards_collection=flashcards_collection,
    )

    # ── Premium flag (additive, never gates the core hero) ──────────────
    is_premium = (
        getattr(current_user, "subscription_status", None) in PREMIUM_STATUSES
    )

    # ── Final shape ──────────────────────────────────────────────────────
    return {
        "success": True,
        "languages": discovered["languages_payload"],
        "selected_language": selected_code,
        "confidence": {
            "value": confidence["value"],
            "trend": confidence["trend"],
            "sessions_counted": confidence["sessions_counted"],
            "source": confidence["source"],
            "band": confidence["band"],
        },
        "rhythm": rs["rhythm"],
        "story": story,
        "proof": proof,
        "is_premium": bool(is_premium),
        "timezone": tz,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


# ──────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────


async def _discover_languages(
    *,
    user_id: str,
    user_doc: dict,
) -> dict:
    """
    Build `languages[]` from session collections (R10 — never trust
    users.stats.lifetime.by_language alone, which drops ISO-keyed activity).

    Output:
      {
        "languages_payload": [
          {"code":"nl","name":"dutch","level":"B1","is_primary":true,"has_activity":true},
          ...
        ]
      }
    """
    seen_names: set[str] = set()

    try:
        if conversation_sessions_collection is not None:
            for raw in await conversation_sessions_collection.distinct(
                "language", {"user_id": user_id}
            ):
                nm = canonical_name(raw)
                if nm:
                    seen_names.add(nm)
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] distinct conv languages failed: {e}")

    try:
        if challenge_sessions_collection is not None:
            for raw in await challenge_sessions_collection.distinct(
                "language", {"user_id": user_id}
            ):
                nm = canonical_name(raw)
                if nm:
                    seen_names.add(nm)
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] distinct challenge languages failed: {e}")

    lifetime = (user_doc.get("stats") or {}).get("lifetime") or {}
    by_language = lifetime.get("by_language") or {}

    preferred = (user_doc.get("preferred_language") or "").strip()
    preferred_name = canonical_name(preferred) if preferred else None

    # If we have no session activity but user has a preferred_language, still
    # show that single chip so the page never feels empty.
    if not seen_names and preferred_name:
        seen_names.add(preferred_name)

    payload = []
    for nm in sorted(seen_names):
        lvl = None
        lang_data = by_language.get(nm) or {}
        if isinstance(lang_data, dict):
            lvl = lang_data.get("highest_level")
        payload.append({
            "code": canonical_code(nm) or nm,
            "name": nm,
            "level": lvl,
            "is_primary": (preferred_name == nm) if preferred_name else False,
            "has_activity": nm in seen_names,
        })
    return {"languages_payload": payload}


async def _recent_sessions_for_confidence(
    *,
    user_id: str,
    language: Optional[str],
) -> list[dict]:
    """
    Fetch up to RECENT_SESSIONS_BOUND newest conversation_sessions for the
    user (and language, if filtered) that have an enhanced_analysis field
    present. Used solely by the confidence ladder.
    """
    if conversation_sessions_collection is None:
        return []
    q: dict[str, Any] = {
        "user_id": user_id,
        "enhanced_analysis": {"$exists": True, "$ne": None},
    }
    if language:
        from services.profile_story.language_normalizer import language_match_filter
        variants = language_match_filter(language)
        if variants:
            q["language"] = {"$in": variants}
    try:
        cursor = (
            conversation_sessions_collection.find(
                q,
                {"created_at": 1, "enhanced_analysis.ai_insights.confidence_level": 1},
            )
            .sort("created_at", -1)
            .limit(RECENT_SESSIONS_BOUND)
        )
        out = []
        async for s in cursor:
            out.append(s)
        return out
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] recent sessions scan failed: {e}")
        return []
