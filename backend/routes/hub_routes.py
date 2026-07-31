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

    # Why the silver (challenge) mission was picked — e.g. "grammar"
    silver_reason: str = ""

    # Phase 0 — which of the 4 priority sources picked Silver today.
    # One of "P1" | "P2" | "P3" | "P4" | "default". Already stored on the
    # missions doc (missions_routes._generate_missions_for_today L717-718);
    # we just surface it. Lets the UI tune the tone of the "why" line
    # ("based on your last session" vs "based on your assessment").
    silver_source: str = ""

    # Phase 0 — server-side all-missions-complete flag. Authoritative trigger
    # for the celebration. Mobile keeps its client-side recompute as fallback
    # so older builds and this field's absence both remain safe.
    all_complete: bool = False

    # S3.7: weakest DNA strand key for spine integration (null when no DNA data)
    weakest_strand: Optional[str] = None

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
        # Exclude user-archived plans ("delete my plan"). This is the single
        # source for the hub: active-plan resolution, missions, plan_session,
        # planDay all derive from this list, so filtering here hides an
        # archived plan from the hero card + Today's Path everywhere at once.
        # $ne also matches docs with no status field (legacy plans stay visible).
        {"user_id": user_id, "status": {"$ne": "archived"}},
        {
            "_id": 1,  # kept only as a fallback for legacy plans missing `id`
            "id": 1, "language": 1, "proficiency_level": 1, "status": 1,
            "completed_sessions": 1, "total_sessions": 1, "duration_months": 1,
            "goals": 1, "progress_percentage": 1, "updated_at": 1, "created_at": 1,
            "voice_check_schedule": 1, "voice_checks_completed": 1,
            "plan_content": 1, "assessment_data": 1, "sessions_per_week": 1,
            "preferred_session_duration": 1,
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


async def _get_weekly_totals(user_id: str, local_date: str) -> Dict[str, int]:
    """
    Phase 3 — read-time aggregation of weekly XP + sessions.

    Walks the daily_stats docs whose local_date falls in the current ISO
    week (Monday → today) in the user's timezone. No schema change, no
    cron, no migration. Additive: the resulting dict is folded into
    progress_stats by _get_progress_stats.

    `local_date` is the hub's IANA-aware today (already computed by the
    handler). We derive Monday-of-that-week purely by date arithmetic on
    the date strings, so it's timezone-agnostic from this function's
    perspective.

    Returns {"weekly_xp": int, "weekly_sessions": int}. Empty week → zeros.
    """
    try:
        today_dt   = datetime.strptime(local_date, "%Y-%m-%d")
        # Monday of the current ISO week (weekday() returns 0 for Monday).
        week_start = today_dt - timedelta(days=today_dt.weekday())
        week_dates = [
            (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(today_dt.weekday() + 1)  # Monday through today, inclusive
        ]

        cursor = daily_stats_collection.find(
            {"user_id": user_id, "local_date": {"$in": week_dates}},
            {"total_xp": 1, "total_sessions": 1}
        )
        weekly_xp = 0
        weekly_sessions = 0
        async for doc in cursor:
            weekly_xp       += int(doc.get("total_xp") or 0)
            weekly_sessions += int(doc.get("total_sessions") or 0)
        return {"weekly_xp": weekly_xp, "weekly_sessions": weekly_sessions}
    except Exception as e:
        print(f"[HUB] weekly totals failed: {e}")
        return {"weekly_xp": 0, "weekly_sessions": 0}


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
            # 🏫 B2B sponsorship — powers the teal Premium badge + "sponsored by
            # <school>" in the Hub plan modal. None for B2C users.
            "institution":        getattr(status, "institution", None),
        }
    except Exception:
        return {
            "plan": "try_learn",
            "limits": {"minutes_remaining": 0, "is_unlimited": False, "minutes_limit": 15},
        }


async def _get_progress_stats(user_id: str, local_date: Optional[str] = None) -> Dict:
    """
    Aggregate lifetime progress from the denormalized user.stats.lifetime doc.

    Why denormalized and NOT live aggregation:
    - challenge_sessions only captures recent sessions; the bulk of historical
      XP was incremented directly into stats.lifetime via individual challenge
      answer paths and is NOT in any session document.
    - stats.lifetime.total_xp is the single authoritative counter — incremented
      atomically on every XP-earning event by all paths.
    - xp_by_source is also denormalized (incremented alongside total_xp) so
      it stays in sync without any aggregation queries.

    Breakdown derivation for users who pre-date xp_by_source tracking:
    - Challenge XP = sum of by_language[lang].total_xp (challenge sessions are
      the only events that write per-language XP).
    - Conversation XP = total_xp - challenge_xp (remainder).

    Phase 2 — adds `streak_incremented_today: bool` so the celebration can
    honestly show "+1 today" only when the streak actually grew. Computed
    by comparing the canonical write-side anchor (`stats.last_practice_date`)
    to today's local date passed by the caller. Additive; defaults to False
    when `local_date` is not supplied (older callers).
    """
    user = await users_collection.find_one(
        {"_id": ObjectId(user_id)},
        {"stats": 1}
    )
    if not user:
        return {}
    stats    = user.get("stats") or {}
    lifetime = stats.get("lifetime") or {}
    total_xp = lifetime.get("total_xp") or stats.get("total_xp", 0)

    # Prefer the explicitly tracked breakdown (written since the fix)
    xp_by_source = lifetime.get("xp_by_source") or {}
    challenge_xp    = xp_by_source.get("challenges", 0)
    conversation_xp = xp_by_source.get("conversations", 0)
    achievement_xp  = xp_by_source.get("achievements", 0)

    # Fallback for pre-fix users: derive from by_language (challenge-only source)
    if challenge_xp == 0 and conversation_xp == 0 and total_xp > 0:
        challenge_xp = sum(
            lang.get("total_xp", 0)
            for lang in lifetime.get("by_language", {}).values()
        )
        # Anything not attributed to challenges must be conversation XP
        conversation_xp = max(0, total_xp - challenge_xp)

    challenge_count    = lifetime.get("total_challenges", 0)
    conversation_count = lifetime.get("total_sessions", 0)

    # Phase 2 — honest "streak incremented today" signal. True iff the
    # write-side anchor (stats.last_practice_date) equals today's local date
    # in the user's timezone. Used by the celebration to render "+1 today"
    # only when the streak actually grew; never fabricated.
    last_practice_date = stats.get("last_practice_date")
    streak_incremented_today = bool(local_date and last_practice_date == local_date)

    # Phase 3 — additive weekly aggregation for the launchpad "On a roll?"
    # surface and the optional weekly goal indicator. Read-time over
    # daily_stats, current ISO week. Zero schema change. Missing local_date
    # → returns zeros and the launchpad UI degrades gracefully.
    weekly = {"weekly_xp": 0, "weekly_sessions": 0}
    if local_date:
        weekly = await _get_weekly_totals(user_id, local_date)

    # CHAL.1 — per-language recent level signal.
    # Sourced from stats.lifetime.by_language.<lang>.highest_level which is
    # already tracked at stats_service.py:249 (updated whenever a higher level
    # is played in a given language). Used by the mobile Silver-mission press
    # handler so a Dutch-learning user without a plan no longer gets a default
    # English/B1 challenge — they get Dutch at the level they've actually
    # played before, falling back to A1 in code when nothing exists. Pure
    # read-side projection: no schema change, no new write, additive.
    recent_level_by_language: Dict[str, str] = {}
    for lang, lang_data in (lifetime.get("by_language") or {}).items():
        if not isinstance(lang_data, dict):
            continue
        lvl = lang_data.get("highest_level")
        if isinstance(lvl, str) and lvl:
            recent_level_by_language[lang.lower()] = lvl

    return {
        "current_streak":          stats.get("current_streak", 0),
        "longest_streak":          stats.get("longest_streak", 0),
        "streak_incremented_today": streak_incremented_today,
        "total_sessions":          conversation_count or stats.get("total_sessions", 0),
        "total_minutes":           lifetime.get("total_time_minutes") or stats.get("total_minutes", 0),
        "total_xp":                total_xp,
        "average_minutes_per_day": stats.get("average_minutes_per_day", 0),
        "xp_by_source": {
            "challenges":    challenge_xp,
            "conversations": conversation_xp,
            "achievements":  achievement_xp,
        },
        "challenge_count":    challenge_count,
        "conversation_count": conversation_count,
        # Phase 3 additive — weekly totals for the launchpad
        "weekly_xp":       weekly["weekly_xp"],
        "weekly_sessions": weekly["weekly_sessions"],
        # CHAL.1 additive — per-language "what level did the user last play"
        # so a no-plan user's Silver press routes to the right CEFR level.
        "recent_level_by_language": recent_level_by_language,
    }


async def _get_journey_state(user_id: str) -> Dict:
    """Use the cached 6-hour journey state (no recalculation on every load)."""
    try:
        state = await journey_state_detector.detect_journey_stage(user_id, force_recalculate=False)
        return state.dict()
    except Exception:
        return {"stage": "exploring", "days_since_last_activity": 0, "dna_improvement_trend": "stable"}


def _compute_weekly_deltas(dna_strands: Optional[Dict]) -> Dict[str, Dict[str, Any]]:
    """
    Phase 3 — per-strand weekly window-diff from the in-document history arrays.

    Honesty rules (never fabricate acceleration):
      - Transcript strands (vocabulary, accuracy, fluency) read `history`
        (one entry per session). We require >=2 history points within the
        last 7 days AND the latest > the oldest in the window. Only entries
        with positive delta are emitted.
      - Acoustic strands (rhythm, confidence, pronunciation) read
        `voice_check_history` (sparse — one entry per voice check). If <2
        entries in the 7-day window, we omit the strand entirely rather
        than infer a trend from a single point. Same positive-delta rule.
      - Any flat or negative result is omitted. Cold-start strands omitted.

    Returns: {strand_key: {"delta": float, "points": int, "window_days": 7}}.
    """
    if not dna_strands:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    window_days = 7
    now = datetime.utcnow()
    cutoff = now - timedelta(days=window_days)

    TRANSCRIPT_STRANDS = ("vocabulary", "accuracy", "fluency")
    ACOUSTIC_STRANDS   = ("rhythm", "confidence", "pronunciation")

    def _in_window(entries: List[Dict]) -> List[Dict]:
        """Filter to last 7d using `timestamp` if present, else accept all."""
        kept: List[Dict] = []
        for e in entries or []:
            ts = e.get("timestamp")
            if not ts:
                # If timestamp is missing, fall through and accept (older
                # entries predating the field). We sort by index later.
                kept.append(e)
                continue
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    kept.append(e)
                    continue
            if isinstance(ts, datetime) and ts >= cutoff:
                kept.append(e)
        return kept

    for strand_key in TRANSCRIPT_STRANDS + ACOUSTIC_STRANDS:
        strand_doc = dna_strands.get(strand_key) or {}
        if strand_key in ACOUSTIC_STRANDS:
            history = strand_doc.get("voice_check_history") or []
        else:
            history = strand_doc.get("history") or []

        windowed = _in_window(history)
        # Honesty: <2 points in the window → can't infer a trend.
        # Acoustic sparsity gets the same rule as transcript (no special case),
        # which means most users will simply not see acoustic strands in the
        # weekly_deltas dict — that's the correct, honest behavior.
        if len(windowed) < 2:
            continue

        try:
            oldest_val = float(windowed[0].get("value") or 0.0)
            latest_val = float(windowed[-1].get("value") or 0.0)
            delta = round(latest_val - oldest_val, 4)
        except Exception:
            continue

        if delta <= 0:
            # Flat or declining → omit. Never fabricate "faster".
            continue

        out[strand_key] = {
            "delta":       delta,
            "points":      len(windowed),
            "window_days": window_days,
        }

    return out


async def _get_dna_summary(user_id: str, language: Optional[str]) -> Optional[Dict]:
    """Return only the strand scores — not the full profile — to keep payload small.

    Phase 0: also project `last_session_delta`. Written by
    SpeakingDNAService.analyze_session_for_dna() on every session of every type
    (background task chained off save-conversation / session-summary).
    Shape on the profile doc:
      last_session_delta: {
        session_id, session_type, computed_at,
        strands: { rhythm: {previous, current, delta}, ... 6 strands ... },
        top_strand: str | null,
        top_delta:  float (0-1)
      }
    Surfaced here so the hub can power "Your <strand> climbed +X today"
    without needing the background DNA task to be synchronous.

    Phase 3: computes `weekly_deltas` from the in-document strand history
    arrays. Honesty rules enforced inside _compute_weekly_deltas: never
    fabricate "faster"; sparse acoustic data is omitted rather than
    inferred from one point.
    """
    query: Dict[str, Any] = {"user_id": user_id}
    if language:
        query["language"] = language.lower()
    doc = await speaking_dna_profiles_collection.find_one(
        query,
        {
            "dna_strands": 1,
            "overall_profile": 1,
            "sessions_analyzed": 1,
            "last_session_delta": 1,
        }
    )
    if not doc:
        return None
    doc.pop("_id", None)

    # Phase 3 — add the additive weekly_deltas dict computed from the
    # already-projected dna_strands history arrays. No extra DB read.
    doc["weekly_deltas"] = _compute_weekly_deltas(doc.get("dna_strands"))

    return doc


def _weakest_strand_key(dna_summary: Optional[Dict]) -> Optional[str]:
    """Return the StrandKey with the lowest score from a dna_summary dict."""
    if not dna_summary:
        return None
    strands = dna_summary.get("dna_strands", {})
    if not strands:
        return None
    _SCORE_FIELDS = {
        "rhythm": "consistency_score",
        "confidence": "score",
        "vocabulary": "diversity_score",
        "accuracy": "grammar_accuracy",
        "learning": "challenge_acceptance",
        "emotional": "positivity_score",
    }
    lowest_key: Optional[str] = None
    lowest_score: float = float("inf")
    for key, field in _SCORE_FIELDS.items():
        strand = strands.get(key)
        if not strand:
            continue
        score = float(strand.get(field, 0) or 0)
        if score < lowest_score:
            lowest_score = score
            lowest_key = key
    return lowest_key


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
    user_id: str, local_date: str, timezone: str, language: Optional[str],
    has_active_plan: Optional[bool] = None,
) -> tuple:
    """Load cached missions and attach live progress inline.
    Returns (missions_list, silver_reason, silver_source) tuple.

    Cache versioning: bump MISSIONS_CACHE_VERSION whenever mission generation
    logic changes so existing cached docs are automatically regenerated.

    has_active_plan: live plan state for THIS language, resolved by the hub
    route from the plans it already fetched. Used to reconcile a cached
    bronze that predates a mid-day plan create/archive (bronze swaps to
    plan_session/news_session; silver+gold untouched).

    Phase 0: also returns silver_source (already stored on the missions doc
    by _generate_missions_for_today) and passes silver_reason through to
    _hydrate_progress so each Silver mission carries its reason field inline.
    """
    from routes.missions_routes import (
        _generate_missions_for_today,
        _hydrate_progress,
        _reconcile_bronze_with_plan_state,
    )

    MISSIONS_CACHE_VERSION = 2  # bump when mission generation logic changes

    coll = get_missions_collection()
    lang_key = (language or "").lower()
    cached = await coll.find_one({"user_id": user_id, "local_date": local_date, "language": lang_key})

    cache_valid = (
        cached is not None and
        cached.get("cache_version", 1) >= MISSIONS_CACHE_VERSION
    )

    if cache_valid:
        raw = cached["missions"]
        silver_reason: str = cached.get("silver_reason", "")
        silver_source: str = cached.get("silver_source", "")
        # Mid-day plan create/archive: bronze must follow the live plan state.
        raw = await _reconcile_bronze_with_plan_state(
            user_id, local_date, language, raw, has_active_plan
        )
    else:
        if cached:
            print(f"[MISSIONS] Cache version mismatch for {user_id} lang={lang_key} — regenerating")
        raw = await _generate_missions_for_today(user_id, local_date, timezone, language)
        # After generation the doc now exists — read reason + source back
        doc = await coll.find_one({"user_id": user_id, "local_date": local_date, "language": lang_key})
        silver_reason = doc.get("silver_reason", "") if doc else ""
        silver_source = doc.get("silver_source", "") if doc else ""

    hydrated = await _hydrate_progress(
        user_id, local_date, raw, silver_reason=silver_reason,
        language=lang_key or None, tz=timezone,
    )
    return [m.dict() for m in hydrated], silver_reason, silver_source


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
    language: Optional[str] = Query(None, description="Active practice language selected by the user"),
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

    # Backfill users.timezone from the device zone — see the same call in
    # missions_routes.get_today_missions. The Hub is the first screen most
    # users land on, so this is usually where the zone gets persisted first.
    # Idempotent, best-effort, never raises.
    from services.timezone_utils import persist_user_timezone
    await persist_user_timezone(
        users_collection, user_id, getattr(current_user, "timezone", None), timezone
    )

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
        _get_progress_stats(user_id, local_date),
        _get_journey_state(user_id),
        _get_flashcard_sets(user_id),
    )

    # Resolve active language: query param wins, then user profile, then most-recent plan
    if not language:
        language = getattr(current_user, "preferred_language", None)
    if not language and plans:
        active = next(
            (p for p in plans if p.get("status") in ("in_progress", "active") or not p.get("status")),
            None,
        )
        if active:
            language = active.get("language")

    # Live plan state for the resolved language — same predicate as
    # _build_missions' plan_filter (in_progress/active/None + language match).
    # Reused by the bronze reconcile guard so it costs zero extra queries.
    _lang_lower = (language or "").lower()
    has_active_plan = any(
        (p.get("status") in ("in_progress", "active") or not p.get("status"))
        and (not _lang_lower or (p.get("language") or "").lower() == _lang_lower)
        for p in plans
    )

    # DNA + missions can now run with resolved language
    dna_summary, (missions, silver_reason, silver_source) = await asyncio.gather(
        _get_dna_summary(user_id, language),
        _get_or_generate_missions(user_id, local_date, tz, language, has_active_plan),
    )

    # Path A — predicted preview of tomorrow's missions.
    # Runs AFTER mission generation so the variety guard's "recent" window
    # includes today's just-written silver type.
    next_preview = await _safe_predict_next(user_id, language, local_date)

    # Phase 0 — server-side all-missions-complete. Uses the same rule the
    # standalone /api/missions/today endpoint uses (missions_routes.py:980).
    # Mobile keeps its client-side fallback computation so older builds work.
    all_complete = bool(missions) and all(
        bool(m.get("progress", {}).get("done")) for m in missions
    )

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
        silver_reason=silver_reason,
        silver_source=silver_source,
        all_complete=all_complete,
        weakest_strand=_weakest_strand_key(dna_summary),
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
