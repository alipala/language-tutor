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
    id: str                           # plan_session | challenge | flashcards
    tier: str                         # bronze | silver | gold
    title: str
    challenge_type: Optional[str] = None
    progress: MissionProgress


class DailyMissionsResponse(BaseModel):
    success: bool = True
    date: str
    timezone: str
    missions: List[DailyMission]
    all_complete: bool
    generated_at: str


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

async def _pick_challenge_type(user_id: str, language: Optional[str]) -> str:
    """
    4-source priority stack — returns the most targeted challenge type.
    Runs all DB reads in parallel.
    """

    # Fire all reads concurrently
    three_days_ago = datetime.utcnow() - timedelta(days=3)

    (sentence_errors, last_session, active_plan, dna_doc) = await asyncio.gather(
        # P1: sentence errors from last 3 days
        _sentence_collection().find(
            {"user_id": user_id, "created_at": {"$gte": three_days_ago}}
        ).to_list(length=20),

        # P2: most recent conversation session with enhanced_analysis
        conversation_sessions_collection.find_one(
            {"user_id": user_id, "enhanced_analysis": {"$ne": None}},
            sort=[("created_at", -1)],
        ),

        # P3: most recent learning plan with assessment_data
        learning_plans_collection.find_one(
            {"user_id": user_id, "assessment_data": {"$exists": True, "$ne": {}}},
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
            winner = max(error_counts, key=lambda k: error_counts[k])
            print(f"[MISSIONS] P1 sentence_errors → {winner} ({error_counts})")
            return winner

    # ── P2: enhanced_analysis recommendations ────────────────
    if last_session:
        ea = last_session.get("enhanced_analysis") or {}
        recs = ea.get("recommendations") or []
        rec_text = " ".join(str(r) for r in recs).lower()
        if "vocabulary" in rec_text or "words" in rec_text:
            print(f"[MISSIONS] P2 enhanced_analysis → smart_flashcard")
            return "smart_flashcard"
        if "fluency" in rec_text or "flow" in rec_text:
            print(f"[MISSIONS] P2 enhanced_analysis → native_check")
            return "native_check"
        if "grammar" in rec_text or "verb" in rec_text:
            print(f"[MISSIONS] P2 enhanced_analysis → error_spotting")
            return "error_spotting"
        if "coherence" in rec_text or "story" in rec_text or "connect" in rec_text:
            print(f"[MISSIONS] P2 enhanced_analysis → story_builder")
            return "story_builder"

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

        fluency   = _score(fluency_raw)
        grammar   = _score(grammar_raw)
        vocab     = _score(vocab_raw)
        coherence = _score(coherence_raw)

        # Map lowest score to challenge type
        scores = [
            ("native_check",    fluency),
            ("error_spotting",  grammar),
            ("smart_flashcard", vocab),
            ("story_builder",   coherence),
        ]
        scores.sort(key=lambda x: x[1])
        weakest_type, weakest_score = scores[0]
        if weakest_score < 40:   # Only override DNA if assessment shows a real weakness
            print(f"[MISSIONS] P3 assessment scores → {weakest_type} ({weakest_score:.0f})")
            return weakest_type

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
        print(f"[MISSIONS] P4 DNA strands → {winner} (score={dna_scores[0][1]:.2f})")
        return winner

    print(f"[MISSIONS] default → micro_quiz")
    return "micro_quiz"


def _sentence_collection():
    """Lazy accessor for sentence_analysis_feedback collection."""
    return database.sentence_analysis_feedback


# ─────────────────────────────────────────────────────────────
# Mission generation (runs once per day, result persisted)
# ─────────────────────────────────────────────────────────────

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
    # Resolve language from active plan if not on user profile
    if not language:
        plan = await learning_plans_collection.find_one(
            {"user_id": user_id, "status": {"$in": ["in_progress", "active", None]}},
            sort=[("updated_at", -1)],
        )
        if plan:
            language = plan.get("language")

    # Pick Silver challenge type via priority stack
    challenge_type = await _pick_challenge_type(user_id, language)
    cfg = CHALLENGE_CFG.get(challenge_type, CHALLENGE_CFG["micro_quiz"])

    # Gold: unreviewed flashcard sets (cap at 3, min 1)
    unreviewed = await flashcard_sets_collection.count_documents(
        {"user_id": user_id, "is_reviewed": {"$ne": True}}
    )
    flash_target = min(3, max(1, unreviewed)) if unreviewed > 0 else 1
    flash_title  = (
        f"Review {flash_target} flashcard set{'s' if flash_target > 1 else ''}"
        if unreviewed > 0
        else "All flashcard sets reviewed!"
    )

    # Bronze: plan session OR news (news for users with no active plan)
    has_active_plan = await learning_plans_collection.count_documents(
        {"user_id": user_id, "status": {"$in": ["in_progress", "active", None]}}
    ) > 0

    if has_active_plan:
        bronze = {
            "id":             "plan_session",
            "tier":           "bronze",
            "title":          "Complete today's plan session",
            "challenge_type": None,
            "target":         1,
        }
    else:
        bronze = {
            "id":             "news_session",
            "tier":           "bronze",
            "title":          "Read & discuss today's news",
            "challenge_type": None,
            "target":         1,
        }

    missions: List[Dict] = [
        bronze,
        {
            "id":             "challenge",
            "tier":           "silver",
            "title":          cfg["title"],
            "challenge_type": challenge_type,
            "target":         cfg["target"],
        },
        {
            "id":             "flashcards",
            "tier":           "gold",
            "title":          flash_title,
            "challenge_type": None,
            "target":         flash_target,
        },
    ]

    bronze_label = "plan_session" if has_active_plan else "news_session"
    await _missions_coll().replace_one(
        {"user_id": user_id, "local_date": local_date},
        {
            "user_id":      user_id,
            "local_date":   local_date,
            "timezone":     timezone,
            "language":     language,
            "missions":     missions,
            "generated_at": datetime.utcnow(),
            "expires_at":   datetime.utcnow() + timedelta(days=3),
        },
        upsert=True,
    )
    print(f"[MISSIONS] Generated for user {user_id} on {local_date}: "
          f"bronze={bronze_label}  silver={challenge_type}  gold=flashcards({flash_target})")
    return missions


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

    (today_sessions, today_news_sessions, completed_challenge_sessions, reviewed_sets) = \
        await asyncio.gather(
            _get_today_sessions(user_id, local_date),
            _get_today_news_sessions(user_id, local_date),
            _get_completed_challenge_sessions_today(user_id, local_date, challenge_type),
            _get_reviewed_flashcard_count(user_id),
        )

    result: List[DailyMission] = []
    for m in missions:
        target = m["target"]

        if m["id"] == "plan_session":
            # Count sessions that are NOT news type
            current = min(1, max(0, today_sessions - today_news_sessions))

        elif m["id"] == "news_session":
            current = min(1, today_news_sessions)

        elif m["id"] == "challenge":
            current = min(target, completed_challenge_sessions)

        else:  # flashcards
            if m["title"].startswith("All flashcard"):
                current = target  # already all reviewed at generation time
            else:
                current = min(target, reviewed_sets)

        result.append(DailyMission(
            id=m["id"],
            tier=m["tier"],
            title=m["title"],
            challenge_type=m.get("challenge_type"),
            progress=MissionProgress(
                current=current,
                target=target,
                done=(current >= target),
            ),
        ))

    return result


async def _get_today_sessions(user_id: str, local_date: str) -> int:
    doc = await daily_stats_collection.find_one(
        {"user_id": user_id, "local_date": local_date},
        {"total_sessions": 1},
    )
    return int(doc.get("total_sessions", 0)) if doc else 0


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


async def _get_reviewed_flashcard_count(user_id: str) -> int:
    return await flashcard_sets_collection.count_documents(
        {"user_id": user_id, "is_reviewed": True}
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
