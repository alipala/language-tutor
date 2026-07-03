"""
Shared reminder infrastructure.

Extracts the timezone / quiet-hours / weekly-cap / anti-spam gating logic
that every scheduled reminder (practice, news, story, learning-plan) needs,
so each trigger only has to express its OWN "who should get this" rule.

Design: a reminder trigger loops over notification_preferences docs, and for
each user asks two questions:

    1. Is it the right MOMENT to even consider this user?
         -> local_time_for(prefs)  gives the user's local time
         -> is_preferred_hour(...) / is_quiet_hours(...) answer timing
    2. Is this user allowed ANOTHER notification right now?
         -> can_send_more_this_week(prefs)  enforces the weekly cap
         -> already_sent_today(prefs, kind) prevents same-kind spam per day

    ...then AFTER a successful send:
         -> record_send(user_id, kind)  bumps the weekly counter + stamps time

The weekly cap is shared across ALL reminder kinds (one budget per user), so a
chatty week of news reminders correctly suppresses a story reminder. Per-kind
daily anti-spam is tracked separately under last_sent_by_kind.<kind> so two
DIFFERENT reminders can still both land on the same day (up to the weekly cap).
"""

from datetime import datetime
from typing import Any, Dict, Optional
import pytz

from database import notification_preferences_collection

import logging
logger = logging.getLogger(__name__)


def user_timezone(prefs: Dict[str, Any]) -> str:
    """Return a valid IANA tz string for the user, falling back to UTC."""
    tz = prefs.get("timezone") or "UTC"
    try:
        pytz.timezone(tz)
        return tz
    except Exception:
        return "UTC"


def local_time_for(prefs: Dict[str, Any], now_utc: Optional[datetime] = None) -> datetime:
    """Convert the current UTC time into the user's local wall-clock time."""
    now_utc = now_utc or datetime.utcnow()
    tz_name = user_timezone(prefs)
    try:
        tz = pytz.timezone(tz_name)
        return now_utc.replace(tzinfo=pytz.UTC).astimezone(tz)
    except Exception:
        return now_utc


def is_preferred_hour(prefs: Dict[str, Any], local_time: datetime,
                      default_hour: int = 18) -> bool:
    """True only during the user's chosen 1-hour notification window."""
    preferred_hour = prefs.get("preferred_notification_time", default_hour)
    return local_time.hour == preferred_hour


def is_quiet_hours(prefs: Dict[str, Any], local_time: datetime) -> bool:
    """True if the user's local hour falls inside their quiet-hours window."""
    if not prefs.get("quiet_hours_enabled", False):
        return False
    start = prefs.get("quiet_hours_start", 22)
    end = prefs.get("quiet_hours_end", 8)
    hour = local_time.hour
    if start > end:  # window crosses midnight, e.g. 22 -> 8
        return hour >= start or hour < end
    return start <= hour < end


def can_send_more_this_week(prefs: Dict[str, Any],
                            now_utc: Optional[datetime] = None) -> bool:
    """
    Enforce the shared weekly notification budget. The counter auto-resets
    once the week (week_start_date) is >= 7 days old; we treat an expired
    week as 0 used here so a stale counter never permanently silences a user.
    """
    now_utc = now_utc or datetime.utcnow()
    max_per_week = prefs.get("max_notifications_per_week", 3)
    count = prefs.get("notification_count_this_week", 0)

    week_start = prefs.get("week_start_date", now_utc)
    if isinstance(week_start, str):
        try:
            week_start = datetime.fromisoformat(week_start)
        except Exception:
            week_start = now_utc
    if (now_utc - week_start).days >= 7:
        return True  # week expired -> budget effectively reset
    return count < max_per_week


def _coerce_dt(v: Any) -> Optional[datetime]:
    """Coerce a stored value (datetime or ISO-ish string) to a datetime, or None."""
    if v is None:
        return None
    # Real datetime OR any datetime subclass (isinstance covers subclasses).
    if isinstance(v, datetime):
        return v
    s = str(v).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        # Last resort: take the leading YYYY-MM-DD if present.
        head = s[:10]
        try:
            return datetime.strptime(head, "%Y-%m-%d")
        except Exception:
            return None


def already_sent_today(prefs: Dict[str, Any], kind: str,
                       local_time: Optional[datetime] = None) -> bool:
    """
    Per-kind daily anti-spam. Compares against the user's LOCAL date so a
    reminder fires at most once per local day per kind. Robust to stamps stored
    as datetime OR string (space- or T-separated), so malformed persistence
    never silently defeats the dedup.
    """
    local_time = local_time or local_time_for(prefs)
    local_date = local_time.strftime("%Y-%m-%d")

    by_kind = (prefs.get("last_sent_by_kind") or {})
    last_dt = _coerce_dt(by_kind.get(kind))
    if last_dt is not None and last_dt.strftime("%Y-%m-%d") == local_date:
        return True
    return False


async def record_send(user_id: str, kind: str,
                      now_utc: Optional[datetime] = None) -> None:
    """
    Book a successful send: bump the shared weekly counter (resetting it if the
    week rolled over) and stamp both the shared and per-kind last-sent times.
    Call this ONLY after the push actually succeeded.
    """
    now_utc = now_utc or datetime.utcnow()

    prefs = await notification_preferences_collection.find_one({"user_id": user_id}) or {}
    week_start = prefs.get("week_start_date", now_utc)
    if isinstance(week_start, str):
        try:
            week_start = datetime.fromisoformat(week_start)
        except Exception:
            week_start = now_utc
    count = prefs.get("notification_count_this_week", 0)

    if (now_utc - week_start).days >= 7:
        new_count = 1
        new_week_start = now_utc
    else:
        new_count = count + 1
        new_week_start = week_start

    await notification_preferences_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "last_notification_sent_at": now_utc,
            "notification_count_this_week": new_count,
            "week_start_date": new_week_start,
            f"last_sent_by_kind.{kind}": now_utc,
        }}
    )
