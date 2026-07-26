"""
News morning reminder trigger.

Fires ONCE in the user's morning window when fresh news is available for the
day, gated on notification_preferences.news_reminders_enabled and the shared
reminder budget.

Two flavours of the same push, chosen per user:
  - PERSONALIZED: the user has a dominant news interest (from
    stats.lifetime.news_by_category, populated in Phase 1). We name that
    category — "Fresh Technology news is ready to read."
  - GENERIC: no interest signal yet (new user / never did a news session).
    "Today's news is ready — practice while you read."

We only send when TODAY's news actually exists (a news_batches doc for the
user's local date with visible articles), so the deep-link never lands on an
empty list. We do NOT send if the user already did a news session today
(last_news_session_at is today, local) — they clearly don't need a nudge.

Anti-spam: shared weekly budget + per-kind daily stamp ("news"). Morning
window is the user's local [MORNING_START, MORNING_END).
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from bson import ObjectId

from database import (
    users_collection,
    notification_preferences_collection,
    news_batches_collection,
)
from notification_service import NotificationService
import reminder_common as rc

import logging
logger = logging.getLogger(__name__)

MORNING_START = int(os.getenv("NEWS_REMINDER_MORNING_START", "7"))
MORNING_END = int(os.getenv("NEWS_REMINDER_MORNING_END", "11"))
# A category must have at least this many sessions to be "dominant" enough to
# name in a personalized push (avoids naming a one-off tap).
MIN_CATEGORY_SESSIONS = int(os.getenv("NEWS_REMINDER_MIN_CATEGORY", "2"))

# Human labels for the deep-link category chip.
_CATEGORY_LABELS = {
    "technology": "Technology",
    "business": "Business",
    "science": "Science",
    "health": "Health",
    "sports": "Sports",
    "entertainment": "Entertainment",
    "world": "World",
    "politics": "Politics",
    "environment": "Environment",
    "culture": "Culture",
}


def _parse_dt(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _top_category(user: Dict[str, Any]) -> Optional[str]:
    """Return the user's dominant news category key, or None."""
    buckets = (
        ((user or {}).get("stats", {}) or {})
        .get("lifetime", {})
        .get("news_by_category", {})
    ) or {}
    if not isinstance(buckets, dict) or not buckets:
        return None
    # Highest-count category that clears the minimum threshold.
    top_key, top_val = None, 0
    for k, v in buckets.items():
        try:
            v = int(v)
        except Exception:
            continue
        if v > top_val:
            top_key, top_val = k, v
    if top_key and top_val >= MIN_CATEGORY_SESSIONS:
        return top_key
    return None


class NewsReminderTrigger:
    def __init__(self):
        self.notification_service = NotificationService()
        self._fresh_cache: Dict[str, bool] = {}  # local_date_str -> has fresh news

    async def _has_fresh_news(self, local_date: datetime) -> bool:
        """
        True if a news batch with visible articles exists for the given local
        date. Cached per run per date (news is global, not per-user), so a
        sweep over thousands of users hits the DB at most once per date.
        """
        key = local_date.strftime("%Y-%m-%d")
        if key in self._fresh_cache:
            return self._fresh_cache[key]

        day_start = datetime(local_date.year, local_date.month, local_date.day)
        batch = await news_batches_collection.find_one({"date": {"$gte": day_start}})
        has = False
        if batch:
            status = batch.get("status")
            if status == "completed":
                has = True
            elif status == "in_progress" and (batch.get("article_count") or 0) > 0:
                has = True
        self._fresh_cache[key] = has
        return has

    async def check_news_reminders(self) -> Dict[str, Any]:
        now_utc = datetime.utcnow()
        sent = skipped = errors = 0
        personalized = 0
        self._fresh_cache = {}

        print(f"\n📰 [NEWS REMINDER] Start {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        try:
            # Default-ON semantics: match unless EXPLICITLY disabled (older docs
            # lack this field — "missing" != opted-out).
            prefs_cursor = notification_preferences_collection.find({
                "news_reminders_enabled": {"$ne": False}
            })

            async for prefs in prefs_cursor:
                try:
                    user_id = prefs["user_id"]
                    local_time = rc.local_time_for(prefs, now_utc)

                    # Must be in the morning window.
                    if not (MORNING_START <= local_time.hour < MORNING_END):
                        skipped += 1
                        continue
                    if rc.is_quiet_hours(prefs, local_time):
                        skipped += 1
                        continue
                    if not rc.can_send_more_this_week(prefs, now_utc):
                        skipped += 1
                        continue
                    if rc.already_sent_any_today(prefs, local_time):
                        skipped += 1
                        continue

                    user = await users_collection.find_one({"_id": ObjectId(user_id)})
                    if not user or not user.get("push_token"):
                        skipped += 1
                        continue

                    # Realign local time to the user-doc timezone if prefs lacked one.
                    if not prefs.get("timezone") and user.get("timezone"):
                        prefs = {**prefs, "timezone": user["timezone"]}
                        local_time = rc.local_time_for(prefs, now_utc)
                        if not (MORNING_START <= local_time.hour < MORNING_END):
                            skipped += 1
                            continue

                    # Don't nudge if they already read news today (local date).
                    last_news = _parse_dt(
                        ((user.get("stats", {}) or {}).get("lifetime", {}) or {})
                        .get("last_news_session_at")
                    )
                    if last_news:
                        last_news_local = last_news.astimezone(
                            local_time.tzinfo or timezone.utc
                        )
                        if last_news_local.strftime("%Y-%m-%d") == local_time.strftime("%Y-%m-%d"):
                            skipped += 1
                            continue

                    # Only send if fresh news actually exists for today.
                    if not await self._has_fresh_news(local_time):
                        skipped += 1
                        continue

                    title, body, data = self._compose(user_id, user)
                    if data.get("category"):
                        personalized += 1

                    ok = await self._send(user_id, user["push_token"],
                                          title, body, data, now_utc)
                    if ok:
                        sent += 1
                    else:
                        errors += 1

                except Exception as ue:
                    errors += 1
                    print(f"❌ [NEWS REMINDER] user error: {ue}")
                    continue

            print(f"✅ [NEWS REMINDER] Sent {sent} ({personalized} personalized), "
                  f"skipped {skipped}, errors {errors}")
            return {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": sent,
                "personalized": personalized,
                "reminders_skipped": skipped,
                "errors": errors,
            }
        except Exception as e:
            print(f"❌ [NEWS REMINDER] fatal: {e}")
            return {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": sent,
                "reminders_skipped": skipped,
                "errors": errors + 1,
                "error": str(e),
            }

    def _compose(self, user_id: str, user: Dict[str, Any]):
        cat = _top_category(user)
        # News is a TAB inside the "Main" tab navigator, not a root Stack route.
        # App.js taps do navigate(data.screen, data.params), so target Main->News.
        data = {"type": "news_reminder", "screen": "Main",
                "params": {"screen": "News"}, "user_id": user_id}
        if cat:
            label = _CATEGORY_LABELS.get(cat, cat.title())
            data["category"] = cat
            return (
                "Fresh news for you 📰",
                f"New {label} news is ready — read and practice this morning.",
                data,
            )
        return (
            "Today's news is ready 📰",
            "Fresh articles to read and practice — start your morning here.",
            data,
        )

    async def _send(self, user_id, push_token, title, body, data, now_utc):
        try:
            result = self.notification_service.send_expo_push_notification(
                push_tokens=[push_token],
                title=title,
                body=body,
                data=data,
                priority="default",
            )
            if result.get("success"):
                await rc.record_send(user_id, "news", now_utc)
                print(f"✅ [NEWS REMINDER] -> {user_id} (cat={data.get('category')})")
                return True
            print(f"⚠️ [NEWS REMINDER] send failed -> {user_id}: {result.get('message')}")
            return False
        except Exception as e:
            print(f"❌ [NEWS REMINDER] send error -> {user_id}: {e}")
            return False


news_reminder_trigger = NewsReminderTrigger()


async def run_news_reminder_check():
    return await news_reminder_trigger.check_news_reminders()
