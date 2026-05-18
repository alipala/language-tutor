"""
Daily Missions Routes — /api/missions/today

Generates, persists, and tracks today's 3 personalised missions.

Mission slots (always exactly 3):
  BRONZE — "Speak today":       complete 1 plan/practice session
  SILVER — "Train your weakness": complete 1 full challenge session
                                  (10 questions = 1 session = 1 unit of work)
  GOLD   — "Review flashcards":  open and review N unreviewed flashcard sets

────────────────────────────────────────────────────────────────
SILVER challenge type — 4-source priority stack
────────────────────────────────────────────────────────────────
  P1  sentence_analysis_feedback  (last 3 days — most specific/recent)
      verb_conjugation / preposition / article errors → error_spotting
      vocabulary errors                               → smart_flashcard

  P2  conversation_sessions.enhanced_analysis         (last session)
      recommendation mentions "vocabulary"            → smart_flashcard
      recommendation mentions "fluency"               → native_check
      recommendation mentions "grammar"               → error_spotting
      recommendation mentions "coherence/story"       → story_builder

  P3  learning_plans.assessment_data skill scores     (baseline assessment)
      fluency < 20                                    → native_check
      grammar < 30                                    → error_spotting
      vocabulary < 30                                 → smart_flashcard
      coherence < 25                                  → story_builder

  P4  speaking_dna_profiles strands                   (running average)
      grammar_accuracy  lowest                        → error_spotting
      confidence.score  lowest                        → native_check
      vocabulary rate   lowest                        → smart_flashcard
      rhythm.consistency lowest                       → story_builder
      (default)                                       → micro_quiz

────────────────────────────────────────────────────────────────
SILVER progress counting
────────────────────────────────────────────────────────────────
  We count completed challenge_sessions (is_active=False, total_challenges>=10)
  for today's local_date — NOT individual challenge taps.
  Rationale: a challenge "session" in the app is 10 questions.
  The user only sees the celebration + end-analysis after 10 questions.
  Counting individual taps would let 1/10 of a session count as complete.

────────────────────────────────────────────────────────────────
GOLD progress counting
────────────────────────────────────────────────────────────────
  We count flashcard_sets where is_reviewed=True.
  The flashcard viewer calls POST /api/flashcards/set/{id}/mark-reviewed
  when the user opens a set — that write immediately advances this mission.

────────────────────────────────────────────────────────────────
Reset / cache
────────────────────────────────────────────────────────────────
  Missions are generated ONCE per day (keyed on user_id + local_date).
  Challenge type for Silver is LOCKED at generation — no mid-day drift.
  Progress is always read LIVE on every GET (no staleness).
  TTL index auto-expires docs after 3 days.
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
    challenge_sessions_collection,
    speaking_dna_profiles_collection,
    flashcard_sets_collection,
    learning_plans_collection,
    conversation_sessions_collection,
    users_collection,
    database,
)
from services.timezone_utils import get_current_local_date, get_day_start_end
from bson import ObjectId

router = APIRouter()


def _missions_coll():
    return database.daily_missions


# ─────────────────────────────────────────────────────────────
# Pydantic response models
# ─────────────────────────────────────────────────────────────

class MissionProgress(BaseModel):
    current: int
    target: int
    done: bool


class DailyMission(BaseModel):
    id: str                           # plan_session | challenge | flashcards | news_session | freestyle | challenge_gold
    tier: str                         # bronze | silver | gold
    title: str
    subtitle: Optional[str] = None   # e.g. "Dutch A1 · English A2" for flashcard mission
    challenge_type: Optional[str] = None
    progress: MissionProgress


class DailyMissionsResponse(BaseModel):
    success: bool = True
    date: str
    timezone: str
    missions: List[DailyMission]
    all_complete: bool
    generated_at: str


class PredictedMission(BaseModel):
    """Tomorrow's preview mission — same shape as DailyMission minus progress."""
    id: str
    tier: str
    title: str
    challenge_type: Optional[str] = None
    target: int


class MissionsPreview(BaseModel):
    """Path A — read-only forecast of tomorrow's missions."""
    missions: List[PredictedMission]
    silver_reason: str
    silver_source: str       # "P1" | "P2" | "P3" | "P4" | "default"
    next_local_date: str     # ISO date the preview applies to (in user TZ)


# ─────────────────────────────────────────────────────────────
# Challenge type config
# ─────────────────────────────────────────────────────────────

CHALLENGE_CFG: Dict[str, Dict[str, Any]] = {
    "error_spotting":  {"title": "Play Spot the Mistake",    "target": 1},
    "native_check":    {"title": "Play Sounds Natural?",     "target": 1},
    "smart_flashcard": {"title": "Play Smart Flashcard",     "target": 1},
    "story_builder":   {"title": "Play Story Builder",       "target": 1},
    "micro_quiz":      {"title": "Play Quick Quiz",          "target": 1},
    "brain_tickler":   {"title": "Play Brain Tickler",       "target": 1},
}

# Sentence error type → challenge type
SENTENCE_ERROR_MAP: Dict[str, str] = {
    "verb_conjugation":    "error_spotting",
    "verb_tense":          "error_spotting",
    "subject_verb":        "error_spotting",
    "preposition":         "native_check",
    "article":             "native_check",
    "article_contraction": "native_check",
    "vocabulary":          "smart_flashcard",
    "word_choice":         "smart_flashcard",
}


# ─────────────────────────────────────────────────────────────
# Priority stack — pick Silver challenge type
# ─────────────────────────────────────────────────────────────
#
# Returns a SilverPick describing the winner, the runner-up
# (used by the variety guard / Path C), and a short, human-readable
# reason string ("Picked because grammar is your top focus") used
# both for telemetry and for Tomorrow's Preview (Path A).
# ─────────────────────────────────────────────────────────────

class SilverPick(BaseModel):
    winner:    str                # e.g. "error_spotting"
    runner_up: Optional[str] = None  # e.g. "smart_flashcard"
    source:    str                # "P1" | "P2" | "P3" | "P4" | "default"
    reason:    str                # human-readable, ≤ ~70 chars


# Friendly labels used to build reason strings.
CHALLENGE_REASON_LABEL: Dict[str, str] = {
    "error_spotting":  "grammar",
    "native_check":    "fluency",
    "smart_flashcard": "vocabulary",
    "story_builder":   "story-telling",
    "micro_quiz":      "quick recall",
    "brain_tickler":   "puzzle thinking",
}


async def _pick_challenge_type(user_id: str, language: Optional[str]) -> str:
    """Backwards-compatible thin wrapper — returns just the winner type."""
    pick = await _pick_silver_pick(user_id, language)
    return pick.winner


async def _pick_silver_pick(user_id: str, language: Optional[str]) -> SilverPick:
    """
    4-source priority stack — returns the most targeted challenge type
    along with the runner-up and a short reason.
    Runs all DB reads in parallel.
    """

    # Fire all reads concurrently
    three_days_ago = datetime.utcnow() - timedelta(days=3)

    # Build language filter — scope P1 errors and P2 session to THIS language
    lang_filter = {"language": language.lower()} if language else {}

    (sentence_errors, last_session, active_plan, dna_doc) = await asyncio.gather(
        # P1: sentence errors from last 3 days, scoped to current language
        _sentence_collection().find(
            {"user_id": user_id, "created_at": {"$gte": three_days_ago}, **lang_filter}
        ).to_list(length=20),

        # P2: most recent conversation session with enhanced_analysis
        conversation_sessions_collection.find_one(
            {"user_id": user_id, "enhanced_analysis": {"$ne": None}},
            sort=[("created_at", -1)],
        ),

        # P3: most recent learning plan with assessment_data, scoped to language
        learning_plans_collection.find_one(
            {
                "user_id": user_id,
                "assessment_data": {"$exists": True, "$ne": {}},
                **({"language": language.lower()} if language else {}),
            },
            sort=[("updated_at", -1)],
        ),

        # P4: DNA profile
        speaking_dna_profiles_collection.find_one(
            {"user_id": user_id, **({"language": language.lower()} if language else {})}
        ),
    )

    # ── P1: sentence errors ───────────────────────────────────
    if sentence_errors:
        error_counts: Dict[str, int] = {}
        for doc in sentence_errors:
            et = doc.get("error_type", "")
            if et in SENTENCE_ERROR_MAP:
                mapped = SENTENCE_ERROR_MAP[et]
                error_counts[mapped] = error_counts.get(mapped, 0) + 1
        if error_counts:
            ranked = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
            winner = ranked[0][0]
            runner_up = ranked[1][0] if len(ranked) > 1 else None
            print(f"[MISSIONS] P1 sentence_errors → {winner} ({error_counts})")
            return SilverPick(
                winner=winner,
                runner_up=runner_up,
                source="P1",
                reason=f"Picked because {CHALLENGE_REASON_LABEL[winner]} mistakes show up most in your recent sessions",
            )

    # ── P2: enhanced_analysis recommendations ────────────────
    # P2 is single-signal (one keyword wins). No meaningful runner-up.
    if last_session:
        ea = last_session.get("enhanced_analysis") or {}
        recs = ea.get("recommendations") or []
        rec_text = " ".join(str(r) for r in recs).lower()
        p2_match: Optional[str] = None
        if "vocabulary" in rec_text or "words" in rec_text:
            p2_match = "smart_flashcard"
        elif "fluency" in rec_text or "flow" in rec_text:
            p2_match = "native_check"
        elif "grammar" in rec_text or "verb" in rec_text:
            p2_match = "error_spotting"
        elif "coherence" in rec_text or "story" in rec_text or "connect" in rec_text:
            p2_match = "story_builder"

        if p2_match:
            print(f"[MISSIONS] P2 enhanced_analysis → {p2_match}")
            return SilverPick(
                winner=p2_match,
                runner_up=None,
                source="P2",
                reason=f"Your last session flagged {CHALLENGE_REASON_LABEL[p2_match]} as the next thing to work on",
            )

    # ── P3: assessment skill scores ───────────────────────────
    if active_plan:
        ad = active_plan.get("assessment_data") or {}
        fluency_raw   = ad.get("fluency")
        grammar_raw   = ad.get("grammar")
        vocab_raw     = ad.get("vocabulary")
        coherence_raw = ad.get("coherence")

        def _score(raw) -> float:
            if isinstance(raw, (int, float)):
                return float(raw)
            if isinstance(raw, dict):
                return float(raw.get("score", 100))
            return 100.0

        scores = [
            ("native_check",    _score(fluency_raw)),
            ("error_spotting",  _score(grammar_raw)),
            ("smart_flashcard", _score(vocab_raw)),
            ("story_builder",   _score(coherence_raw)),
        ]
        scores.sort(key=lambda x: x[1])
        weakest_type, weakest_score = scores[0]
        runner_up = scores[1][0] if len(scores) > 1 else None
        if weakest_score < 40:   # Only override DNA if assessment shows a real weakness
            print(f"[MISSIONS] P3 assessment scores → {weakest_type} ({weakest_score:.0f})")
            return SilverPick(
                winner=weakest_type,
                runner_up=runner_up,
                source="P3",
                reason=f"Your baseline assessment shows {CHALLENGE_REASON_LABEL[weakest_type]} is your top growth area",
            )

    # ── P4: DNA strands (fallback) ────────────────────────────
    if dna_doc:
        strands = dna_doc.get("dna_strands") or {}
        gram  = (strands.get("accuracy",   {}) or {}).get("grammar_accuracy",        1.0)
        conf  = (strands.get("confidence", {}) or {}).get("score",                   1.0)
        vocab = (strands.get("vocabulary", {}) or {}).get("new_word_attempt_rate",   1.0)
        rhy   = (strands.get("rhythm",     {}) or {}).get("consistency_score",       1.0)

        dna_scores = [
            ("error_spotting",  float(gram  if gram  is not None else 1)),
            ("native_check",    float(conf  if conf  is not None else 1)),
            ("smart_flashcard", float(vocab if vocab is not None else 1)),
            ("story_builder",   float(rhy   if rhy   is not None else 1)),
        ]
        dna_scores.sort(key=lambda x: x[1])
        winner = dna_scores[0][0]
        runner_up = dna_scores[1][0] if len(dna_scores) > 1 else None
        print(f"[MISSIONS] P4 DNA strands → {winner} (score={dna_scores[0][1]:.2f})")
        return SilverPick(
            winner=winner,
            runner_up=runner_up,
            source="P4",
            reason=f"Your speaking DNA shows {CHALLENGE_REASON_LABEL[winner]} is your top focus area right now",
        )

    print(f"[MISSIONS] default → micro_quiz")
    return SilverPick(
        winner="micro_quiz",
        runner_up=None,
        source="default",
        reason="A short warm-up while we learn what you're working on",
    )


def _sentence_collection():
    """Lazy accessor for sentence_analysis_feedback collection."""
    return database.sentence_analysis_feedback


# ─────────────────────────────────────────────────────────────
# Path B — Streak-scaling Bronze target
# ─────────────────────────────────────────────────────────────
#
# A 30-day-streak user is doing a different job from a fresh user.
# Bronze target scales: 1 → 2 → 3 sessions as the streak grows.
# Silver stays at 1 (one full 10-Q session is already meaningful).
# Gold scales independently with unreviewed-set count.
# ─────────────────────────────────────────────────────────────

# (min_streak, target). Sorted descending so the first hit wins.
BRONZE_STREAK_LADDER: List[tuple] = [
    (30, 3),
    (7,  2),
    (0,  1),
]


def _bronze_target_for_streak(current_streak: int) -> int:
    """Pure function — picks Bronze target from streak ladder."""
    for min_streak, target in BRONZE_STREAK_LADDER:
        if current_streak >= min_streak:
            return target
    return 1


async def _get_current_streak(user_id: str) -> int:
    """Read users.stats.current_streak. Returns 0 if missing."""
    try:
        user = await users_collection.find_one(
            {"_id": ObjectId(user_id)}, {"stats.current_streak": 1}
        )
        if not user:
            return 0
        return int((user.get("stats") or {}).get("current_streak", 0))
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────
# Path C — Anti-repeat variety guard
# ─────────────────────────────────────────────────────────────
#
# If a user got the same Silver challenge_type two days in a row,
# tomorrow we promote the runner-up — provided one exists.
# Keeps weekly variety without overriding pedagogy: we still target
# a real weakness, just the second-most-pressing one.
# ─────────────────────────────────────────────────────────────

REPEAT_THRESHOLD_DAYS = 2  # If both yesterday + day-before were the same → demote.


async def _recent_silver_types(user_id: str, local_date: str) -> List[str]:
    """
    Return Silver challenge_types for the previous N days, newest first.
    Skips days with no doc rather than returning a sparse list — callers
    only care whether the most-recent run repeats.
    """
    try:
        cursor = _missions_coll().find(
            {"user_id": user_id, "local_date": {"$lt": local_date}},
            {"missions": 1, "local_date": 1},
            sort=[("local_date", -1)],
            limit=REPEAT_THRESHOLD_DAYS,
        )
        out: List[str] = []
        async for doc in cursor:
            for m in doc.get("missions", []):
                if m.get("id") == "challenge" and m.get("challenge_type"):
                    out.append(m["challenge_type"])
                    break
        return out
    except Exception as e:
        print(f"[MISSIONS] _recent_silver_types failed: {e}")
        return []


def _apply_variety_guard(pick: SilverPick, recent: List[str]) -> SilverPick:
    """
    If `pick.winner` matches the last REPEAT_THRESHOLD_DAYS Silver types
    AND a runner-up exists, promote the runner-up. Otherwise return pick
    unchanged.
    """
    if not pick.runner_up:
        return pick
    if len(recent) < REPEAT_THRESHOLD_DAYS:
        return pick
    if any(t != pick.winner for t in recent[:REPEAT_THRESHOLD_DAYS]):
        return pick

    # All recent days were the same as the current winner — swap.
    print(
        f"[MISSIONS] Variety guard: {pick.winner} repeated {REPEAT_THRESHOLD_DAYS}d "
        f"→ promoting runner-up {pick.runner_up}"
    )
    return SilverPick(
        winner=pick.runner_up,
        runner_up=pick.winner,  # keep the original winner as the new runner-up
        source=pick.source,
        reason=(
            f"Switching it up — you've worked on "
            f"{CHALLENGE_REASON_LABEL.get(pick.winner, pick.winner)} "
            f"two days running. Time for "
            f"{CHALLENGE_REASON_LABEL.get(pick.runner_up, pick.runner_up)}."
        ),
    )


async def _resolve_silver(
    user_id: str,
    language: Optional[str],
    local_date: str,
) -> SilverPick:
    """
    Single entry point: 4-source priority stack + variety guard.
    Pure orchestration — used by both generation and prediction (Path A).
    """
    pick = await _pick_silver_pick(user_id, language)
    recent = await _recent_silver_types(user_id, local_date)
    return _apply_variety_guard(pick, recent)


# ─────────────────────────────────────────────────────────────
# Mission generation (runs once per day, result persisted)
# ─────────────────────────────────────────────────────────────

async def _resolve_language(user_id: str, language: Optional[str]) -> Optional[str]:
    """If language wasn't passed in, fall back to the active learning plan."""
    if language:
        return language
    plan = await learning_plans_collection.find_one(
        {"user_id": user_id, "status": {"$in": ["in_progress", "active", None]}},
        sort=[("updated_at", -1)],
    )
    return plan.get("language") if plan else None


async def _get_today_freestyle_sessions(user_id: str, local_date: str) -> int:
    """Count freestyle/practice conversation sessions completed today.
    The mobile saves free conversations as conversation_type='practice' (the default
    when no explicit sessionType is passed). Both 'freestyle' and 'practice' count.
    Uses the user's local date window to avoid UTC-midnight timezone mismatch.
    """
    try:
        day_start, day_end = get_day_start_end(local_date, "UTC")
        return await conversation_sessions_collection.count_documents({
            "user_id": user_id,
            "conversation_type": {"$in": ["freestyle", "practice"]},
            "created_at": {"$gte": day_start, "$lte": day_end},
        })
    except Exception:
        return 0


async def _resolve_gold_mission(
    user_id: str,
    silver_winner: str,
    unreviewed: int,
    has_any_flashcards: int,
    language: Optional[str] = None,
) -> Dict:
    """
    5-profile decision tree for the Gold (slot 3) mission.

    Priority order:
      P1  New to THIS language (≤3 conversations in language) → freestyle
      P2  Game-heavy in this language (challenges > 2× convs) → news session
      P3  Talk-heavy, avoids games (convs>5, games<3)         → second challenge
      P4  Has unreviewed flashcard sets                        → flashcards
      P5  Default / balanced                                   → freestyle

    All conversation/challenge counts are scoped to `language` so that activity
    in Dutch does not contaminate mission selection for Spanish or Portuguese.
    """
    # Build language filter — scope counts to THIS language only
    lang_filter = {"language": language.lower()} if language else {}

    try:
        total_conversations, total_challenges = await asyncio.gather(
            conversation_sessions_collection.count_documents({"user_id": user_id, **lang_filter}),
            challenge_sessions_collection.count_documents({"user_id": user_id, **lang_filter}),
        )
    except Exception:
        total_conversations, total_challenges = 0, 0

    # P1 — new to this language (≤3 conversations in this specific language)
    if total_conversations <= 3:
        return {
            "id":             "freestyle",
            "tier":           "gold",
            "title":          "i18n:gold_freestyle_title",
            "subtitle":       "i18n:gold_freestyle_sub_new",
            "challenge_type": None,
            "target":         1,
        }

    # P2 — plays games much more than speaking
    if total_challenges > total_conversations * 2:
        return {
            "id":             "news_session",
            "tier":           "gold",
            "title":          "i18n:gold_news_title",
            "subtitle":       "i18n:gold_news_sub",
            "challenge_type": None,
            "target":         1,
        }

    # P3 — speaks a lot but avoids games
    if total_conversations > 5 and total_challenges < 3:
        GOLD_FALLBACK_ORDER = [
            "error_spotting", "native_check", "story_builder",
            "brain_tickler", "micro_quiz", "smart_flashcard",
        ]
        gold_type = next(
            (t for t in GOLD_FALLBACK_ORDER if t != silver_winner),
            "micro_quiz",
        )
        gold_cfg = CHALLENGE_CFG.get(gold_type, CHALLENGE_CFG["micro_quiz"])
        return {
            "id":             "challenge_gold",
            "tier":           "gold",
            "title":          gold_cfg["title"],
            "subtitle":       "i18n:gold_challenge_sub",
            "challenge_type": gold_type,
            "target":         gold_cfg["target"],
        }

    # P4 — has unreviewed flashcard sets
    if unreviewed > 0:
        flash_target = min(3, unreviewed)
        title_key = "i18n:gold_flash_title_plural" if flash_target > 1 else "i18n:gold_flash_title"
        return {
            "id":             "flashcards",
            "tier":           "gold",
            "title":          f"{title_key}:{flash_target}",
            "subtitle":       None,  # filled live in _hydrate_progress
            "challenge_type": None,
            "target":         flash_target,
        }

    # P5 — balanced / default
    return {
        "id":             "freestyle",
        "tier":           "gold",
        "title":          "i18n:gold_freestyle_title",
        "subtitle":       "i18n:gold_freestyle_sub",
        "challenge_type": None,
        "target":         1,
    }


async def _build_missions(
    user_id: str,
    language: Optional[str],
    local_date: str,
) -> tuple:
    """
    Pure builder — returns (missions, silver_pick, bronze_id).
    Used by both generation (writes) and prediction (read-only).

    Runs three independent reads in parallel:
      - Silver pick (priority stack + variety guard)
      - Streak (drives Bronze target)
      - Unreviewed flashcards count (drives Gold target)
      - Active-plan presence (decides Bronze id)
    """
    # Build the plan filter scoped to the requested language so bronze mission
    # reflects THIS language's plan, not plans from other languages.
    plan_filter: dict = {"user_id": user_id, "status": {"$in": ["in_progress", "active", None]}}
    if language:
        plan_filter["language"] = language.lower()

    silver, current_streak, unreviewed, has_active_plan = await asyncio.gather(
        _resolve_silver(user_id, language, local_date),
        _get_current_streak(user_id),
        flashcard_sets_collection.count_documents(
            {"user_id": user_id, "is_reviewed": {"$ne": True}}
        ),
        learning_plans_collection.count_documents(plan_filter),
    )

    silver_cfg = CHALLENGE_CFG.get(silver.winner, CHALLENGE_CFG["micro_quiz"])

    # ── Bronze: plan_session OR news_session, target scales with streak ──
    bronze_target = _bronze_target_for_streak(current_streak)
    if has_active_plan:
        bronze_id    = "plan_session"
        bronze_title = (
            "i18n:bronze_plan_title"
            if bronze_target == 1
            else f"i18n:bronze_plan_title_plural:{bronze_target}"
        )
    else:
        bronze_id    = "news_session"
        bronze_title = (
            "i18n:bronze_news_title"
            if bronze_target == 1
            else f"i18n:bronze_news_title_plural:{bronze_target}"
        )

    bronze = {
        "id":             bronze_id,
        "tier":           "bronze",
        "title":          bronze_title,
        "challenge_type": None,
        "target":         bronze_target,
    }

    # ── Gold mission — resolved via 5-profile decision tree ─────
    has_any_flashcards = await flashcard_sets_collection.count_documents(
        {"user_id": user_id}
    )
    gold_mission = await _resolve_gold_mission(
        user_id=user_id,
        silver_winner=silver.winner,
        unreviewed=unreviewed,
        has_any_flashcards=has_any_flashcards,
        language=language,
    )

    missions: List[Dict] = [
        bronze,
        {
            "id":             "challenge",
            "tier":           "silver",
            "title":          silver_cfg["title"],
            "subtitle":       "i18n:silver_subtitle",
            "challenge_type": silver.winner,
            "target":         silver_cfg["target"],
        },
        {
            **gold_mission,
        },
    ]
    return missions, silver, bronze_id


async def _generate_missions_for_today(
    user_id: str,
    local_date: str,
    timezone: str,
    language: Optional[str],
) -> List[Dict]:
    """
    Build today's 3 missions using real user data.
    Writes result to daily_missions collection.
    Returns raw mission list (without live progress).
    """
    language = await _resolve_language(user_id, language)
    missions, silver, bronze_id = await _build_missions(user_id, language, local_date)

    MISSIONS_CACHE_VERSION = 2  # must match hub_routes.py

    lang_key = (language or "").lower()
    await _missions_coll().replace_one(
        {"user_id": user_id, "local_date": local_date, "language": lang_key},
        {
            "user_id":       user_id,
            "local_date":    local_date,
            "timezone":      timezone,
            "language":      lang_key,
            "missions":      missions,
            "silver_reason": silver.reason,
            "silver_source": silver.source,
            "cache_version": MISSIONS_CACHE_VERSION,
            "generated_at":  datetime.utcnow(),
            "expires_at":    datetime.utcnow() + timedelta(days=3),
        },
        upsert=True,
    )
    print(
        f"[MISSIONS] Generated for user {user_id} on {local_date}: "
        f"bronze={bronze_id}(target={missions[0]['target']})  "
        f"silver={silver.winner}(src={silver.source})  "
        f"gold=flashcards({missions[2]['target']})"
    )
    return missions


# ─────────────────────────────────────────────────────────────
# Path A — Predicted preview of tomorrow's missions (read-only)
# ─────────────────────────────────────────────────────────────
#
# Runs the same builder as _generate_missions_for_today, but uses
# tomorrow's local_date so the variety guard sees today's mission
# in the "recent" window. Does NOT write to the missions collection.
#
# Caveat: prediction can disagree with what gets generated tomorrow if
# the user's signals shift overnight (e.g. they finish a session at
# 11:58 PM that flips P1's winner). This is acceptable — the preview
# is best-effort and never marketed as final.
# ─────────────────────────────────────────────────────────────

def _next_local_date(local_date: str) -> str:
    """Add one calendar day to a YYYY-MM-DD string."""
    try:
        d = datetime.strptime(local_date, "%Y-%m-%d") + timedelta(days=1)
        return d.strftime("%Y-%m-%d")
    except Exception:
        # Defensive — should never happen with our local_date producer.
        return local_date


async def _predict_missions_preview(
    user_id: str,
    language: Optional[str],
    today_local_date: str,
) -> MissionsPreview:
    """
    Predict tomorrow's 3 missions without writing anything.
    Reads only — safe to call from any GET path.
    """
    language = await _resolve_language(user_id, language)
    next_date = _next_local_date(today_local_date)

    # IMPORTANT: pass next_date so the variety guard's "recent" lookup
    # treats today's missions (just generated) as part of history.
    missions, silver, _ = await _build_missions(user_id, language, next_date)

    return MissionsPreview(
        missions=[PredictedMission(**m) for m in missions],
        silver_reason=silver.reason,
        silver_source=silver.source,
        next_local_date=next_date,
    )


# ─────────────────────────────────────────────────────────────
# Progress hydration (always live — called on every GET)
# ─────────────────────────────────────────────────────────────

async def _hydrate_progress(
    user_id: str,
    local_date: str,
    missions: List[Dict],
) -> List[DailyMission]:
    """
    Attach live progress to each mission.
    Runs 3 DB reads in parallel:
      - daily_stats total_sessions    → bronze
      - challenge_sessions count      → silver (completed 10-Q sessions today)
      - flashcard_sets reviewed count → gold
    """
    challenge_type = next(
        (m["challenge_type"] for m in missions if m["id"] == "challenge"),
        "micro_quiz",
    )

    (today_learning_plan_sessions, today_news_sessions, completed_challenge_sessions, reviewed_sets, today_freestyle) = \
        await asyncio.gather(
            _get_today_learning_plan_sessions(user_id, local_date),
            _get_today_news_sessions(user_id, local_date),
            _get_completed_challenge_sessions_today(user_id, local_date, challenge_type),
            _get_reviewed_flashcard_count(user_id, local_date),
            _get_today_freestyle_sessions(user_id, local_date),
        )

    # Build flashcard subtitle live (works from cache too)
    flash_subtitle: Optional[str] = None
    try:
        unreviewed_sets = await flashcard_sets_collection.find(
            {"user_id": user_id, "is_reviewed": {"$ne": True}},
            {"language": 1, "level": 1}
        ).limit(3).to_list(3)
        parts = []
        seen: set = set()
        for s in unreviewed_sets:
            lang = (s.get("language") or "").capitalize()
            lvl  = (s.get("level") or "").upper()
            if lang and lvl:
                key = f"{lang} {lvl}"
                if key not in seen:
                    seen.add(key)
                    parts.append(key)
        if parts:
            flash_subtitle = " · ".join(parts)
    except Exception:
        pass  # subtitle is optional

    result: List[DailyMission] = []
    for m in missions:
        target = m["target"]

        if m["id"] == "plan_session":
            current = min(1, today_learning_plan_sessions)

        elif m["id"] == "news_session":
            current = min(1, today_news_sessions)

        elif m["id"] == "challenge":
            current = min(target, completed_challenge_sessions)

        elif m["id"] == "challenge_gold":
            gold_challenge_type = m.get("challenge_type", "")
            gold_count = await _get_completed_challenge_sessions_today(
                user_id, local_date, gold_challenge_type
            ) if gold_challenge_type else 0
            current = min(target, gold_count)

        elif m["id"] == "freestyle":
            current = min(target, today_freestyle)

        else:  # flashcards
            current = min(target, reviewed_sets)

        # Use live subtitle for flashcard mission; carry through stored subtitle for others
        subtitle = flash_subtitle if m["id"] == "flashcards" and current < target else m.get("subtitle")

        result.append(DailyMission(
            id=m["id"],
            tier=m["tier"],
            title=m["title"],
            subtitle=subtitle,
            challenge_type=m.get("challenge_type"),
            progress=MissionProgress(
                current=current,
                target=target,
                done=(current >= target),
            ),
        ))

    return result


async def _get_today_learning_plan_sessions(user_id: str, local_date: str) -> int:
    doc = await daily_stats_collection.find_one(
        {"user_id": user_id, "local_date": local_date},
        {"learning_plan_sessions": 1},
    )
    return int(doc.get("learning_plan_sessions", 0)) if doc else 0


async def _get_today_news_sessions(user_id: str, local_date: str) -> int:
    """
    Count news conversation sessions completed today.
    News sessions are stored in conversation_sessions with conversation_type='news'.
    daily_stats.total_sessions includes them, so we need this to isolate news vs plan.
    """
    day_start, day_end = get_day_start_end(local_date, "UTC")
    return await conversation_sessions_collection.count_documents({
        "user_id": user_id,
        "conversation_type": "news",
        "created_at": {"$gte": day_start, "$lte": day_end},
    })


async def _get_completed_challenge_sessions_today(
    user_id: str,
    local_date: str,
    challenge_type: str,
) -> int:
    """
    Count fully completed challenge sessions (10 questions) today
    for the specific challenge_type assigned to this user's Silver mission.

    A session is "complete" when:
      - is_active = False  (session has ended)
      - total_challenges >= 10  (full 10-question round)
      - local_date matches today
      - challenge_type matches
    """
    return await challenge_sessions_collection.count_documents({
        "user_id": user_id,
        "local_date": local_date,
        "challenge_type": challenge_type,
        "is_active": False,
        "total_challenges": {"$gte": 10},
    })


async def _get_reviewed_flashcard_count(user_id: str, local_date: str) -> int:
    """Count flashcard sets reviewed TODAY — not all-time — so the mission
    resets properly each day and can't be pre-completed by past activity."""
    day_start, day_end = get_day_start_end(local_date, "UTC")
    return await flashcard_sets_collection.count_documents(
        {
            "user_id": user_id,
            "is_reviewed": True,
            "reviewed_at": {"$gte": day_start, "$lte": day_end},
        }
    )


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@router.get(
    "/api/missions/today",
    response_model=DailyMissionsResponse,
    summary="Get today's personalised daily missions",
    tags=["Missions"],
)
async def get_today_missions(
    timezone: Optional[str] = Query(None, description="User timezone e.g. Europe/Amsterdam"),
    force_regenerate: bool = Query(False, description="Force new mission generation (dev only)"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Returns today's 3 personalised missions with live progress.

    Missions are generated once per day and cached in `daily_missions`.
    Progress is always read live on every call.
    """
    user_id    = str(current_user.id)
    tz         = timezone or getattr(current_user, "timezone", None) or "UTC"
    local_date = get_current_local_date(tz)

    # Load or generate missions
    cached = None
    if not force_regenerate:
        cached = await _missions_coll().find_one(
            {"user_id": user_id, "local_date": local_date}
        )

    if cached:
        raw       = cached["missions"]
        generated = cached["generated_at"].isoformat()
    else:
        language  = getattr(current_user, "preferred_language", None)
        raw       = await _generate_missions_for_today(user_id, local_date, tz, language)
        generated = datetime.utcnow().isoformat()

    # Always hydrate progress live
    missions   = await _hydrate_progress(user_id, local_date, raw)
    all_done   = all(m.progress.done for m in missions)

    return DailyMissionsResponse(
        success=True,
        date=local_date,
        timezone=tz,
        missions=missions,
        all_complete=all_done,
        generated_at=generated,
    )


# ─────────────────────────────────────────────────────────────
# Mission XP award request model
# ─────────────────────────────────────────────────────────────

class MissionXpRequest(BaseModel):
    tier: str        # "bronze" | "silver" | "gold"
    xp:   int        # XP amount shown on the card (50 | 75 | 60)
    local_date: str  # YYYY-MM-DD in user's timezone
    timezone: str    # e.g. "Europe/Amsterdam"


@router.post(
    "/api/missions/xp",
    summary="Award XP when a mission is completed",
    tags=["Missions"],
)
async def award_mission_xp(
    body: MissionXpRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Awards XP to the user when a mission completes.

    Idempotency guarantee: each tier can only be awarded once per local_date.
    The awarded tiers are stored in the daily_missions doc under `xp_awarded_tiers`.
    Calling this endpoint twice for the same tier on the same day is a safe no-op.

    XP is incremented in:
      - users.stats.lifetime.total_xp
      - users.stats.lifetime.xp_by_source.missions
      - daily_stats.total_xp  (so the hub top-bar counter updates immediately)
    """
    user_id    = str(current_user.id)
    tier       = body.tier
    xp         = max(0, body.xp)           # defensive clamp
    local_date = body.local_date
    timezone   = body.timezone

    if tier not in ("bronze", "silver", "gold"):
        return {"success": False, "reason": "invalid_tier"}
    if xp <= 0:
        return {"success": False, "reason": "invalid_xp"}

    coll = _missions_coll()

    # ── Idempotency check + atomic claim ─────────────────────
    # addToSet is atomic: if tier already in xp_awarded_tiers the
    # document doesn't change, so matched_count=1 but modified_count=0.
    result = await coll.update_one(
        {
            "user_id":    user_id,
            "local_date": local_date,
            # Only update if this tier has NOT already been awarded
            "xp_awarded_tiers": {"$ne": tier},
        },
        {"$addToSet": {"xp_awarded_tiers": tier}},
    )

    if result.modified_count == 0:
        # Either missions doc doesn't exist or tier already awarded — safe no-op
        return {"success": True, "awarded": False, "reason": "already_awarded_or_no_doc"}

    # ── Award XP atomically ───────────────────────────────────
    try:
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$inc": {
                    "stats.lifetime.total_xp":               xp,
                    "stats.lifetime.xp_by_source.missions":  xp,
                }
            },
        )

        # Also update daily_stats so the hub XP counter reflects it immediately.
        # Use upsert so this works even if no session was played today.
        day_start, _ = get_day_start_end(local_date, timezone)
        await daily_stats_collection.update_one(
            {"user_id": user_id, "local_date": local_date},
            {
                "$inc": {"total_xp": xp},
                "$set": {"updated_at": datetime.utcnow()},
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )

        print(f"[MISSIONS] ✅ Awarded {xp} XP ({tier}) to user {user_id} on {local_date}")
        return {"success": True, "awarded": True, "xp": xp, "tier": tier}

    except Exception as e:
        print(f"[MISSIONS] ❌ Error awarding mission XP: {e}")
        # Roll back the tier claim so it can be retried
        await coll.update_one(
            {"user_id": user_id, "local_date": local_date},
            {"$pull": {"xp_awarded_tiers": tier}},
        )
        return {"success": False, "reason": "internal_error"}


@router.post(
    "/api/missions/reset",
    summary="Force-reset today's missions (dev only)",
    tags=["Missions"],
    include_in_schema=False,
)
async def reset_today_missions(
    current_user: UserResponse = Depends(get_current_user),
):
    """Deletes today's cached missions so they regenerate on next GET."""
    user_id    = str(current_user.id)
    tz         = getattr(current_user, "timezone", None) or "UTC"
    local_date = get_current_local_date(tz)
    result     = await _missions_coll().delete_one(
        {"user_id": user_id, "local_date": local_date}
    )
    return {"success": True, "deleted": result.deleted_count > 0}


@router.get(
    "/api/missions/preview",
    response_model=MissionsPreview,
    summary="Preview tomorrow's missions (read-only)",
    tags=["Missions"],
)
async def get_missions_preview(
    timezone: Optional[str] = Query(None, description="User timezone e.g. Europe/Amsterdam"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Returns a read-only forecast of tomorrow's 3 missions, computed by
    running the same builder against tomorrow's local_date. No writes.

    Note: this can disagree with what gets generated tomorrow if the
    user's signals shift overnight. The preview is best-effort.
    """
    user_id    = str(current_user.id)
    tz         = timezone or getattr(current_user, "timezone", None) or "UTC"
    local_date = get_current_local_date(tz)
    language   = getattr(current_user, "preferred_language", None)
    return await _predict_missions_preview(user_id, language, local_date)
