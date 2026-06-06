"""
Timezone resolver for PROFILE_STORY_V1.

Walks the production fallback chain in order:
    users.timezone                  (3/34 users)
  → notification_preferences.timezone   (10/34)
  → daily_stats.user_timezone (most recent)  (most session-active users)
  → "UTC" (default)

Returns a stable string suitable for zoneinfo.ZoneInfo. Never raises.
Read-only.
"""

from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

_DEFAULT_TZ = "UTC"


async def resolve_user_timezone(
    user_id: str,
    user_doc: Optional[dict],
    notification_preferences_collection: Any,
    daily_stats_collection: Any,
) -> str:
    """
    Resolve the best-known timezone string for a user.

    Args:
        user_id: stringified user_id (matches Mongo schema).
        user_doc: the already-fetched users doc (avoids a second round-trip).
        notification_preferences_collection: Motor collection or None.
        daily_stats_collection: Motor collection or None.

    Returns:
        Timezone string like "Europe/Amsterdam" or "UTC".
    """
    # 1. users.timezone
    if user_doc:
        tz = (user_doc.get("timezone") or "").strip()
        if tz:
            return tz

    # 2. notification_preferences.timezone
    if notification_preferences_collection is not None:
        try:
            pref = await notification_preferences_collection.find_one(
                {"user_id": user_id}, {"timezone": 1}
            )
            if pref and (pref.get("timezone") or "").strip():
                return pref["timezone"].strip()
        except Exception as e:
            logger.warning(f"[PROFILE_STORY] tz fallback to prefs failed: {e}")

    # 3. daily_stats.user_timezone (latest)
    if daily_stats_collection is not None:
        try:
            latest = await daily_stats_collection.find_one(
                {"user_id": user_id, "user_timezone": {"$exists": True, "$ne": None, "$ne": ""}},
                {"user_timezone": 1},
                sort=[("local_date", -1)],
            )
            if latest and (latest.get("user_timezone") or "").strip():
                return latest["user_timezone"].strip()
        except Exception as e:
            logger.warning(f"[PROFILE_STORY] tz fallback to daily_stats failed: {e}")

    # 4. UTC default
    return _DEFAULT_TZ


def tz_was_resolved(tz: str) -> bool:
    """True if the resolved timezone came from real user data (not the UTC fallback)."""
    return tz != _DEFAULT_TZ
