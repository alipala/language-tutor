"""
28-day rhythm ribbon + timezone-correct streak for PROFILE_STORY_V1.

Streak fix (§5.2): the global `calculate_streaks` in progress_routes.py
compares `datetime.utcnow().date()` against `daily_stats.local_date`
(which is in the user's local timezone). That causes off-by-one resets at
day boundaries for non-UTC users. This module computes the streak using
the same local-date timeline as `daily_stats`, anchored on the resolved
user timezone. The OFF path is left untouched (parity).

Read-only. Anxiety-aware: caption is a positive count ("spoke on X of the
last Y days"), never "missed".
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo
import logging

from services.timezone_utils import get_user_timezone_obj
from services.profile_story.language_normalizer import language_match_filter

logger = logging.getLogger(__name__)


def _local_today(tz: str) -> str:
    """Today's local date string YYYY-MM-DD in user tz."""
    try:
        zone = get_user_timezone_obj(tz)
        return datetime.now(zone).strftime("%Y-%m-%d")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%d")


def _date_minus(date_str: str, days: int) -> str:
    return (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")


async def build_rhythm_and_streak(
    *,
    user_id: str,
    timezone_str: str,
    language: Optional[str],
    daily_stats_collection: Any,
    conversation_sessions_collection: Any,
    challenge_sessions_collection: Any,
) -> dict:
    """
    Compute:
      - rhythm.days: list of 28 day dicts {date, active} ending today (user local).
      - rhythm.active_days: count where active=true.
      - rhythm.window_days: 28.
      - current_streak: int, TZ-correct.
      - longest_streak: int, derived from the same daily_stats series.

    When `language` is set, filters activity to that language (matching both
    ISO and English-name spellings). When None, "All" mode — any activity counts.

    Performance: at most one daily_stats range scan + at most two range scans of
    sessions (only when language filter is active). Bounded to the 28-day window
    + the full daily_stats series for longest_streak.
    """
    today = _local_today(timezone_str)
    start_28 = _date_minus(today, 27)  # 28 days inclusive

    active_local_dates: set[str] = set()

    if not language:
        # "All" mode — daily_stats is the source of truth.
        try:
            cursor = daily_stats_collection.find(
                {
                    "user_id": user_id,
                    "local_date": {"$gte": start_28, "$lte": today},
                },
                {"local_date": 1, "total_challenges": 1, "conversation_time_seconds": 1},
            )
            async for ds in cursor:
                d = ds.get("local_date")
                if not d:
                    continue
                if (ds.get("total_challenges") or 0) > 0 or (
                    ds.get("conversation_time_seconds") or 0
                ) > 0:
                    active_local_dates.add(d)
        except Exception as e:
            logger.warning(f"[PROFILE_STORY] rhythm daily_stats scan failed: {e}")
    else:
        # Per-language mode — daily_stats is keyed by user_id+date only, NOT by
        # language, so we must look at session collections in the 28-day window.
        lang_variants = language_match_filter(language)
        if lang_variants:
            try:
                # Convert the local-date window to a UTC datetime range that
                # safely brackets it (±1 day each side to absorb tz drift, then
                # re-bucket by user-local date below).
                zone = get_user_timezone_obj(timezone_str)
                start_dt_local = datetime.strptime(start_28, "%Y-%m-%d").replace(tzinfo=zone)
                end_dt_local = datetime.strptime(today, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, tzinfo=zone
                )
                # Bracket UTC range (we'll re-bucket by tz below)
                start_dt_utc = (start_dt_local - timedelta(days=1)).astimezone(ZoneInfo("UTC"))
                end_dt_utc = (end_dt_local + timedelta(days=1)).astimezone(ZoneInfo("UTC"))

                # conversation_sessions
                cs_cursor = conversation_sessions_collection.find(
                    {
                        "user_id": user_id,
                        "language": {"$in": lang_variants},
                        "created_at": {"$gte": start_dt_utc, "$lte": end_dt_utc},
                    },
                    {"created_at": 1},
                )
                async for s in cs_cursor:
                    ca = s.get("created_at")
                    if not isinstance(ca, datetime):
                        continue
                    if ca.tzinfo is None:
                        ca = ca.replace(tzinfo=ZoneInfo("UTC"))
                    local_d = ca.astimezone(zone).strftime("%Y-%m-%d")
                    if start_28 <= local_d <= today:
                        active_local_dates.add(local_d)

                # challenge_sessions (uses local_date directly when present)
                ch_cursor = challenge_sessions_collection.find(
                    {
                        "user_id": user_id,
                        "language": {"$in": lang_variants},
                        "local_date": {"$gte": start_28, "$lte": today},
                    },
                    {"local_date": 1},
                )
                async for s in ch_cursor:
                    d = s.get("local_date")
                    if d:
                        active_local_dates.add(d)
            except Exception as e:
                logger.warning(f"[PROFILE_STORY] rhythm per-language scan failed: {e}")

    # Build 28-day strip
    days = []
    cursor_date = datetime.strptime(start_28, "%Y-%m-%d")
    end_date = datetime.strptime(today, "%Y-%m-%d")
    while cursor_date <= end_date:
        d = cursor_date.strftime("%Y-%m-%d")
        days.append({"date": d, "active": d in active_local_dates})
        cursor_date += timedelta(days=1)

    rhythm = {
        "active_days": sum(1 for d in days if d["active"]),
        "window_days": 28,
        "days": days,
    }

    current_streak, longest_streak = await _calc_streaks(
        user_id=user_id,
        timezone_str=timezone_str,
        today=today,
        daily_stats_collection=daily_stats_collection,
    )

    return {
        "rhythm": rhythm,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


async def _calc_streaks(
    *,
    user_id: str,
    timezone_str: str,
    today: str,
    daily_stats_collection: Any,
) -> tuple[int, int]:
    """
    TZ-correct current + longest streak from daily_stats.

    A "practice day" = local_date with total_challenges > 0 or conversation_time_seconds > 0.

    Note: this is intentionally language-agnostic because daily_stats are not
    sharded by language. Per-language streaks would need a session-level
    re-bucket; out of scope for V1 (rhythm above already shows per-language activity).
    """
    if daily_stats_collection is None:
        return 0, 0

    try:
        cursor = daily_stats_collection.find(
            {"user_id": user_id},
            {"local_date": 1, "total_challenges": 1, "conversation_time_seconds": 1},
        )
        practice_dates: set[str] = set()
        async for ds in cursor:
            d = ds.get("local_date")
            if not d:
                continue
            if (ds.get("total_challenges") or 0) > 0 or (
                ds.get("conversation_time_seconds") or 0
            ) > 0:
                practice_dates.add(d)
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] streak scan failed: {e}")
        return 0, 0

    if not practice_dates:
        return 0, 0

    # Current streak — walk backward from today (or yesterday if today empty).
    current = 0
    yesterday = _date_minus(today, 1)
    if today in practice_dates:
        anchor = today
    elif yesterday in practice_dates:
        anchor = yesterday
    else:
        anchor = None

    if anchor is not None:
        cursor_date = datetime.strptime(anchor, "%Y-%m-%d")
        while cursor_date.strftime("%Y-%m-%d") in practice_dates:
            current += 1
            cursor_date -= timedelta(days=1)

    # Longest streak — sweep sorted dates once.
    sorted_dates = sorted(
        datetime.strptime(d, "%Y-%m-%d") for d in practice_dates
    )
    longest = 0
    run = 0
    prev: Optional[datetime] = None
    for d in sorted_dates:
        if prev is None or (d - prev).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = d

    return current, longest
