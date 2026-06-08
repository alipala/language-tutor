"""
Proof block for PROFILE_STORY_V1.

GLOBAL / ALL-TIME by design (decision after dev test):

  Only `confidence`, `rhythm`, and `story` re-scope with the language chip.
  `proof` is always the user's lifetime totals across all languages — the
  grid (sessions, challenges, XP, minutes_spoken, words_mastered, streaks)
  and the next-milestone bar both read from the same global source, so the
  grid and the milestone can never disagree (e.g. grid "0 challenges" vs
  bar "10 / 100 challenges" — the bug this fixes).

  The mobile screen labels this section "All-time".

Composes existing services:
  - lifetime_progress_service.calculate_milestones → next_milestone
  - users.stats.lifetime.*                          → totals + xp_by_source
  - rhythm_streak                                   → current_streak, longest_streak
  - minutes_spoken                                  → see _minutes_spoken below

Minutes source-of-truth (§5.3 pin, now always global):
  - users.practice_minutes_used (if > 0)
  - else sum speaking_time_tracking.speaking_minutes for the user

words_mastered: count of `flashcards` with mastery_level >= a "mastered"
threshold (SRS canonical "mature card" boundary = 4), gated to is_active=true.
Also global — no per-language filter on flashcards in the proof block.

Read-only. Never 500s — returns safe defaults on missing pieces.
"""

from typing import Any
import logging

from services.lifetime_progress_service import calculate_milestones

logger = logging.getLogger(__name__)

MASTERED_THRESHOLD = 4


async def build_proof(
    *,
    user_id: str,
    user_doc: dict,
    current_streak: int,
    longest_streak: int,
    users_collection: Any,
    speaking_time_tracking_collection: Any,
    flashcards_collection: Any,
) -> dict:
    """
    Build the global proof block. Always all-time; never re-scopes by language.
    """
    lifetime = (user_doc.get("stats") or {}).get("lifetime") or {}
    summary_for_milestones = {
        "total_challenges": int(lifetime.get("total_challenges") or 0),
        # calculate_milestones only reads total_challenges; other fields unused.
    }

    # Language-mastery progress (used to derive upcoming language milestones).
    by_language = lifetime.get("by_language") or {}
    language_progress = {}
    for lang_name, lang_data in by_language.items():
        if not isinstance(lang_data, dict):
            continue
        mp = lang_data.get("mastery_percent")
        if mp is None:
            # Soft derivation from CEFR when no explicit mastery_percent.
            level_order = {"A1": 16.6, "A2": 33.3, "B1": 50.0, "B2": 66.6, "C1": 83.3, "C2": 100.0}
            mp = level_order.get((lang_data.get("highest_level") or "").upper(), 0)
        language_progress[lang_name] = {"mastery_percent": mp}

    try:
        ms = calculate_milestones(summary_for_milestones, language_progress)
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] calculate_milestones failed: {e}")
        ms = {}
    next_milestone = ms.get("next_milestone")
    next_milestone_out = None
    if next_milestone:
        next_milestone_out = {
            "label": f"{int(next_milestone['target']):,} challenges",
            "current": int(next_milestone["current"]),
            "target": int(next_milestone["target"]),
        }

    minutes_spoken = await _minutes_spoken(
        user_doc=user_doc,
        user_id=user_id,
        speaking_time_tracking_collection=speaking_time_tracking_collection,
    )

    words_mastered = await _words_mastered(
        user_id=user_id,
        flashcards_collection=flashcards_collection,
    )

    xp_by_source = lifetime.get("xp_by_source") or {}

    return {
        "current_streak": int(current_streak),
        "longest_streak": int(longest_streak),
        "total_sessions": int(lifetime.get("total_sessions") or 0),
        "total_challenges": int(lifetime.get("total_challenges") or 0),
        "total_xp": int(lifetime.get("total_xp") or 0),
        # Always a number now — global lifetime minutes spoken.
        "minutes_spoken": int(minutes_spoken),
        "words_mastered": int(words_mastered),
        "xp_by_source": {
            "conversations": int(xp_by_source.get("conversations") or 0),
            "challenges": int(xp_by_source.get("challenges") or 0),
            "achievements": int(xp_by_source.get("achievements") or 0),
            "missions": int(xp_by_source.get("missions") or 0),
        },
        "next_milestone": next_milestone_out,
    }


async def _minutes_spoken(
    *,
    user_doc: dict,
    user_id: str,
    speaking_time_tracking_collection: Any,
) -> float:
    """
    Pinned global source:
      1. users.practice_minutes_used if > 0
      2. else sum of speaking_time_tracking.speaking_minutes for the user
      3. else 0.0
    """
    pmu = user_doc.get("practice_minutes_used")
    if isinstance(pmu, (int, float)) and pmu > 0:
        return float(pmu)

    if speaking_time_tracking_collection is not None:
        try:
            pipe = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": None, "minutes": {"$sum": "$speaking_minutes"}}},
            ]
            async for row in speaking_time_tracking_collection.aggregate(pipe):
                return float(row.get("minutes") or 0)
        except Exception as e:
            logger.warning(f"[PROFILE_STORY] speaking_time_tracking sum failed: {e}")

    return 0.0


async def _words_mastered(
    *,
    user_id: str,
    flashcards_collection: Any,
) -> int:
    """Count of mastered, active flashcards across all languages."""
    if flashcards_collection is None:
        return 0
    q: dict = {
        "user_id": user_id,
        "mastery_level": {"$gte": MASTERED_THRESHOLD},
        "is_active": True,
    }
    try:
        return await flashcards_collection.count_documents(q)
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] words_mastered count failed: {e}")
        return 0
