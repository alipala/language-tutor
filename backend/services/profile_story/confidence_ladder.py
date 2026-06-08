"""
Confidence ladder for PROFILE_STORY_V1.

Pins a single deterministic source per request. The endpoint never returns
a "0" or fake reading — when no real signal is available, confidence is null
and the screen shows an empty-state invitation.

Source order (P1 sign-off):
  1. enhanced_analysis.ai_insights.confidence_level
     - Mean of last N=7 analysed sessions for the selected language.
     - Requires ≥3 sessions in window. Otherwise falls through.
     - source = "session_analysis", value = round(mean), 0–100.
  2. users.journey_state.confidence_level × 100
     - Excludes sentinel 0.35 (seed default — 9/27 users; not a real signal).
     - Rounds value to nearest 5 (lifecycle proxy, not a test score).
     - source = "journey_state", value = nearest 5 in 0–100.
  3. Empty.
     - source = "none", value = null.

Trend (separate ladder, same shape):
  1. enhanced_analysis trend (requires ≥14 sessions in language):
       mean(last 7) vs mean(prev 7) → "rising" / "steady" / "easing".
  2. journey_state.dna_improvement_trend, mapped anxiety-aware:
       "improving" → "rising", "stable" → "steady", "declining" → "easing".
  3. Default → "steady".

Wording rule (anxiety-aware brand law):
  Never "declining" / "falling". Always "rising" / "steady" / "easing".
"""

from typing import Any, Optional, TypedDict, Literal
import logging

logger = logging.getLogger(__name__)

# Sentinel — appears verbatim on 9/27 users including brand-new zero-activity users.
# Treat as "no real signal" rather than as a 35 confidence reading.
JOURNEY_SENTINEL = 0.35

ConfidenceSource = Literal["session_analysis", "journey_state", "none"]
Trend = Literal["rising", "steady", "easing"]


class ConfidenceResult(TypedDict):
    value: Optional[int]        # 0–100 or None
    trend: Trend
    sessions_counted: int       # how many sessions backed the value (0 for fallback/empty)
    source: ConfidenceSource    # debug tag, not user-visible
    band: Optional[str]         # word band, used when source == "journey_state"


_BANDS = [
    (0, 20, "Starting out"),
    (20, 40, "Finding your feet"),
    (40, 60, "Comfortable"),
    (60, 80, "Confident"),
    (80, 101, "Flowing"),  # 101 to include exact 100
]


def _band_for(value: int) -> str:
    for lo, hi, label in _BANDS:
        if lo <= value < hi:
            return label
    return "Confident"


def _mean(xs: list[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def _coerce_confidence(raw: Any) -> Optional[float]:
    """Pull a numeric 0–100 confidence out of an enhanced_analysis session, or None."""
    try:
        ea = raw.get("enhanced_analysis") if isinstance(raw, dict) else None
        ai = ea.get("ai_insights") if isinstance(ea, dict) else None
        v = ai.get("confidence_level") if isinstance(ai, dict) else None
        if isinstance(v, (int, float)):
            f = float(v)
            if 0 <= f <= 100:
                return f
        return None
    except Exception:
        return None


def _map_journey_trend(trend: Optional[str]) -> Optional[Trend]:
    if not trend:
        return None
    t = str(trend).strip().lower()
    if t == "improving":
        return "rising"
    if t == "stable":
        return "steady"
    if t == "declining":
        return "easing"
    return None


def compute_confidence(
    *,
    recent_sessions: list[dict],
    journey_state: Optional[dict],
) -> ConfidenceResult:
    """
    Deterministic 3-step ladder for value + trend.

    Args:
        recent_sessions: conversation_sessions for the user (and language, if
            filtered), sorted newest-first. Caller is responsible for the
            language filter and the bound (e.g. last 50). May contain sessions
            without enhanced_analysis — they are skipped.
        journey_state: users.journey_state dict, or None.

    Returns:
        ConfidenceResult — always safe to serialize.
    """
    # ── Primary: enhanced_analysis ────────────────────────────────────────
    confidences = []
    for s in recent_sessions:
        v = _coerce_confidence(s)
        if v is not None:
            confidences.append(v)

    last7 = confidences[:7]
    prev7 = confidences[7:14]

    if len(last7) >= 3:
        value = round(_mean(last7))

        # Trend from enhanced_analysis only if both windows are full enough.
        if len(last7) >= 7 and len(prev7) >= 7:
            delta = _mean(last7) - _mean(prev7)
            if delta >= 3:
                trend: Trend = "rising"
            elif delta <= -3:
                trend = "easing"
            else:
                trend = "steady"
        else:
            # Lean on journey_state trend if available, else steady.
            trend = _map_journey_trend(
                (journey_state or {}).get("dna_improvement_trend")
            ) or "steady"

        return {
            "value": int(value),
            "trend": trend,
            "sessions_counted": len(last7),
            "source": "session_analysis",
            "band": None,  # not used when source is session_analysis
        }

    # ── Fallback: journey_state.confidence_level ──────────────────────────
    jc = (journey_state or {}).get("confidence_level")
    if isinstance(jc, (int, float)):
        f = float(jc)
        # Skip the seed sentinel — it is not a real reading.
        if abs(f - JOURNEY_SENTINEL) > 1e-9 and 0 <= f <= 1.0:
            raw_value = f * 100.0
            # Round to nearest 5 — lifecycle proxy, not a precise score.
            value = int(round(raw_value / 5.0) * 5)
            value = max(0, min(100, value))
            trend = _map_journey_trend(
                (journey_state or {}).get("dna_improvement_trend")
            ) or "steady"
            return {
                "value": value,
                "trend": trend,
                "sessions_counted": 0,
                "source": "journey_state",
                "band": _band_for(value),
            }

    # ── Empty ─────────────────────────────────────────────────────────────
    return {
        "value": None,
        "trend": "steady",
        "sessions_counted": 0,
        "source": "none",
        "band": None,
    }
