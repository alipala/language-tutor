"""
Progression Service (Phase A — Games Spine)

Pure, deterministic helpers for the persistent progression spine surfaced by
`GET /api/challenges/progression` and `GET /api/challenges/next-step`.

Design notes:
- All thresholds / weights live here as named tunables so the curve, formula,
  and recommender ladder can evolve without touching handlers.
- Nothing in this module reads or writes the database; callers pass in the
  data they already have. That keeps these easy to unit-test and reason about.
"""

from math import isqrt
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Level curve
# ---------------------------------------------------------------------------
# Curve: level = floor(sqrt(total_xp / LEVEL_XP_DIVISOR)) + 1
# XP rebalance PR2: the divisor dropped from 100 to 35 so progression feels
# rewarding under the new XP economy (per-answer XP is much lower; voice is
# bigger; daily goal is XP-based). Worked examples under the new curve:
#
#   total_xp =     0  ->  level  1
#   total_xp =   140  ->  level  3   (140 = 4 × 35)
#   total_xp =   500  ->  level  4
#   total_xp = 2_000  ->  level  8
#   total_xp = 6_225  ->  level 14   (real user — dutch heavy)
#   total_xp = 9_430  ->  level 17
#   total_xp =19_880  ->  level 24
#
# Existing users see a one-time positive level bump (see migration script at
# backend/scripts/migrate_levels_for_curve_change.py).
LEVEL_XP_DIVISOR: int = 35


def compute_level(total_xp: int) -> int:
    """Return the gameplay level for a given lifetime XP total.

    Pure, deterministic. ``total_xp`` is clamped at 0; callers can pass
    ``None`` or negative numbers and still get level 1 back.
    """
    if not total_xp or total_xp < 0:
        return 1
    return isqrt(total_xp // LEVEL_XP_DIVISOR) + 1


def xp_for_level(level: int) -> int:
    """Inverse of :func:`compute_level` — the minimum XP for a given level."""
    if level <= 1:
        return 0
    return (level - 1) ** 2 * LEVEL_XP_DIVISOR


def xp_to_next(total_xp: int) -> Dict[str, int]:
    """Return progress within the current level.

    Output:
      - ``level``: current level
      - ``xp_into_level``: XP earned past the current level threshold
      - ``xp_for_level``: XP span of the current level (i.e. how much to climb)
      - ``xp_to_next``: XP still needed for the next level

    The four fields together let the client render either a "x / N" label or
    a percentage bar without doing the math.
    """
    safe_xp = max(int(total_xp or 0), 0)
    level = compute_level(safe_xp)
    current_floor = xp_for_level(level)
    next_floor = xp_for_level(level + 1)
    span = max(next_floor - current_floor, 1)  # guard against 0
    return {
        "level": level,
        "xp_into_level": safe_xp - current_floor,
        "xp_for_level": span,
        "xp_to_next": max(next_floor - safe_xp, 0),
    }


# ---------------------------------------------------------------------------
# Readiness (computed on read; no new persisted field for v1)
# ---------------------------------------------------------------------------
# readiness = W_ACC * accuracy + W_VOL * volume + W_CON * consistency
# (each component clamped to 0..1; final scaled to 0..100)
READINESS_W_ACCURACY: float = 0.5
READINESS_W_VOLUME: float = 0.3
READINESS_W_CONSISTENCY: float = 0.2

# Volume saturates at this many lifetime challenges in the target language.
READINESS_VOLUME_CAP: int = 50

# Consistency saturates at this current-streak length (days).
READINESS_STREAK_CAP: int = 7


def _safe_div(num: float, den: float) -> float:
    return (num / den) if den else 0.0


def compute_readiness(
    *,
    by_language_lang: Optional[Dict[str, Any]],
    by_level_level: Optional[Dict[str, Any]],
    current_streak: int,
) -> int:
    """Compute the speaking-readiness signal, 0..100.

    Inputs come straight out of ``users.stats.lifetime``:
      - ``by_language_lang``: ``stats.lifetime.by_language.{lang}`` (or None)
      - ``by_level_level``:   ``stats.lifetime.by_level.{level}``   (or None)
      - ``current_streak``:   ``stats.current_streak``

    v1 keeps it deliberately simple — three signals, weighted, clamped.
    Future enrichment (DNA, per-skill confidence) plugs in here.
    """
    by_level = by_level_level or {}
    by_lang = by_language_lang or {}

    level_total = int(by_level.get("total_challenges", 0) or 0)
    level_correct = int(by_level.get("correct", 0) or 0)
    accuracy = _safe_div(level_correct, level_total)  # 0..1
    accuracy = min(max(accuracy, 0.0), 1.0)

    lang_total = int(by_lang.get("total_challenges", 0) or 0)
    volume = min(lang_total / READINESS_VOLUME_CAP, 1.0) if READINESS_VOLUME_CAP else 0.0

    streak = max(int(current_streak or 0), 0)
    consistency = min(streak / READINESS_STREAK_CAP, 1.0) if READINESS_STREAK_CAP else 0.0

    readiness = (
        READINESS_W_ACCURACY * accuracy
        + READINESS_W_VOLUME * volume
        + READINESS_W_CONSISTENCY * consistency
    )
    return int(round(max(0.0, min(readiness, 1.0)) * 100))


# ---------------------------------------------------------------------------
# Daily goal
# ---------------------------------------------------------------------------
# XP rebalance PR2: daily goal is now XP-based (voice contributes; games
# contribute; one currency). Tiers: Casual 30 · Regular 50 (default) ·
# Serious 100 · Intense 200. The legacy challenge-count constant is kept
# only as a back-compat alias for any internal caller; it points at the
# new default so behavior stays sensible if anything still reads it.
DEFAULT_DAILY_GOAL_XP: int = 50
DAILY_GOAL_XP_TIERS: Tuple[int, ...] = (30, 50, 100, 200)
DEFAULT_DAILY_GOAL_CHALLENGES: int = DEFAULT_DAILY_GOAL_XP  # back-compat alias


# ---------------------------------------------------------------------------
# Recommender ("next-step")
# ---------------------------------------------------------------------------
# Types the recommender will NEVER suggest. Smart Flashcard is a passive
# review surface that earns no XP/hearts; it remains available via Free Play
# but is not a coherent "Continue" pick.
RECOMMENDER_EXCLUDED_TYPES: Tuple[str, ...] = (
    "smart_flashcard",
)

# Cold-start ladder — lowest-anxiety first. Lead with Micro Quiz now that
# Smart Flashcard is excluded from recommendations.
COLD_START_LADDER: Tuple[str, ...] = (
    "micro_quiz",
    "native_check",
    "error_spotting",
)

# Variety rotation order for users with some history but no clear weak area.
# Mirrors COLD_START_LADDER's safety ordering, with the harder types trailing.
ALL_CHALLENGE_TYPES: Tuple[str, ...] = (
    "micro_quiz",
    "native_check",
    "error_spotting",
    "story_builder",
    "brain_tickler",
)

# A type must have at least this much volume before we trust its accuracy
# enough to call it a "weak area".
WEAK_AREA_MIN_VOLUME: int = 10

# Below this accuracy ratio (0..1), with enough volume, a type qualifies as
# the weak area to target.
WEAK_AREA_ACCURACY_THRESHOLD: float = 0.75

# Rough wall-clock estimate of a single challenge of this type, in seconds.
# Used purely for the UI ("~30 sec"); not persisted.
ESTIMATED_DURATION_SEC: Dict[str, int] = {
    "smart_flashcard": 25,
    "micro_quiz": 30,
    "native_check": 25,
    "error_spotting": 40,
    "story_builder": 60,
    "brain_tickler": 15,
}

# Human-readable display titles (snake_case → on-screen label).
DISPLAY_TITLES: Dict[str, str] = {
    "smart_flashcard": "Smart Flashcard",
    "micro_quiz": "Quick Quiz",
    "native_check": "Sounds Natural?",
    "error_spotting": "Spot the Mistake",
    "story_builder": "Story Builder",
    "brain_tickler": "10-Second Challenge",
}


def _accuracy_of(type_bucket: Dict[str, Any]) -> Tuple[float, int]:
    """Return (accuracy_ratio, total_challenges) for a by_type entry."""
    total = int(type_bucket.get("total_challenges", 0) or 0)
    correct = int(type_bucket.get("correct", 0) or 0)
    return (_safe_div(correct, total), total)


def pick_next_step(
    *,
    by_type: Optional[Dict[str, Dict[str, Any]]],
    last_challenge_type: Optional[str],
    excluded_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Pick the next ``challenge_type`` to recommend.

    Priority:
      1. Weak area  — any type with volume >= ``WEAK_AREA_MIN_VOLUME`` AND
         accuracy < ``WEAK_AREA_ACCURACY_THRESHOLD``. Lowest accuracy wins.
      2. Variety   — first type in ``ALL_CHALLENGE_TYPES`` the user has *not*
         just played (skip ``last_challenge_type``).
      3. Cold start — first type in ``COLD_START_LADDER`` the user hasn't
         touched yet; falls back to the first entry of the ladder.

    Args:
      by_type: ``users.stats.lifetime.by_type`` shape, or None / {}.
      last_challenge_type: the type from the most recent session, or None.
      excluded_types: types to never return (e.g. depleted hearts pool).

    Returns:
      dict with ``challenge_type``, ``reason``, ``estimated_duration_sec``,
      ``display_title``.
    """
    excluded = set(excluded_types or []) | set(RECOMMENDER_EXCLUDED_TYPES)
    available = [t for t in ALL_CHALLENGE_TYPES if t not in excluded]
    if not available:
        # Defensive: caller excluded everything. Return ladder head.
        head = COLD_START_LADDER[0]
        # User-facing fallback only — never leak engineer copy to the card.
        return _format_pick(head, reason="a good next step for you")

    by_type = by_type or {}

    # ── 1. Weak-area path ──
    candidates: List[Tuple[float, int, str]] = []
    for ctype in available:
        bucket = by_type.get(ctype)
        if not bucket:
            continue
        acc, vol = _accuracy_of(bucket)
        if vol >= WEAK_AREA_MIN_VOLUME and acc < WEAK_AREA_ACCURACY_THRESHOLD:
            # Sort key: lowest accuracy first, tie-break on highest volume so
            # the recommendation is grounded in real signal.
            candidates.append((acc, -vol, ctype))
    if candidates:
        candidates.sort()
        _, _, weakest = candidates[0]
        # Encouragement-framed, game-name-agnostic — the card already shows
        # the game title above, so don't repeat it in the reason line.
        return _format_pick(
            weakest,
            reason="a good place to build your confidence",
        )

    # ── 2. Variety rotation (has *some* history) ──
    touched = {t for t, bucket in by_type.items() if (bucket or {}).get("total_challenges", 0)}
    if touched:
        for ctype in available:
            if ctype == last_challenge_type:
                continue
            return _format_pick(ctype, reason="mixing it up with a fresh game")

        # Only the most-recent type is in the available pool (edge case): use it.
        return _format_pick(available[0], reason="continuing where you left off")

    # ── 3. Cold start (no history) ──
    for ctype in COLD_START_LADDER:
        if ctype in available:
            return _format_pick(ctype, reason="a gentle warm-up to get started")
    return _format_pick(available[0], reason="a gentle warm-up to get started")


def _format_pick(challenge_type: str, *, reason: str) -> Dict[str, Any]:
    return {
        "challenge_type": challenge_type,
        "display_title": DISPLAY_TITLES.get(challenge_type, challenge_type),
        "reason": reason,
        "estimated_duration_sec": ESTIMATED_DURATION_SEC.get(challenge_type, 30),
    }
