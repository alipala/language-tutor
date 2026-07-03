"""
Story Worlds reminder trigger.

Three tiers, gated on notification_preferences.story_reminders_enabled and the
shared reminder budget in reminder_common:

  A. RESUME  — an in_progress series untouched for >= STALE_DAYS days.
               Fired in the EVENING (preferred hour) so it lands when people
               settle in to play. "Your story is waiting — pick up where you
               left off."

  B. UNLOCK  — the daily-drip next episode became playable today (its
               current.unlocked_at has just passed). Fired in the MORNING so
               the freshly-unlocked episode greets them. "A new episode is
               ready." Only for users actively mid-series.

  C. DISCOVER — an engaged user (has a push token, practices) who has NEVER
               completed a Story Worlds episode. Weekly, low-frequency. "Try a
               story adventure." Runs at most once/week via the shared budget +
               per-kind daily stamp; we additionally gate to one local weekday
               so it can't nag daily.

Precedence per user per run: A and B are the high-intent nudges; if either
fires we do NOT also send C. Only ONE story push per user per run.

This trigger reads story_progress + users + notification_preferences and is
meant to be called hourly by run_scheduler (like practice reminders), so the
"morning"/"evening" gating is expressed via the user's preferred hour and a
fixed morning window.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from bson import ObjectId

from database import (
    users_collection,
    notification_preferences_collection,
    story_progress_collection,
)
from notification_service import NotificationService
import reminder_common as rc

import logging
logger = logging.getLogger(__name__)

# An in_progress series is "stale" (resume-worthy) after this many days idle.
STALE_DAYS = int(os.getenv("STORY_REMINDER_STALE_DAYS", "3"))
# Morning window for unlock (B) reminders — user's LOCAL hour in [start, end).
MORNING_START = int(os.getenv("STORY_REMINDER_MORNING_START", "8"))
MORNING_END = int(os.getenv("STORY_REMINDER_MORNING_END", "11"))
# Discover (C) fires only on this local weekday (0=Mon .. 6=Sun) to bound it.
DISCOVER_WEEKDAY = int(os.getenv("STORY_REMINDER_DISCOVER_WEEKDAY", "5"))  # Saturday


def _parse_dt(v: Any) -> Optional[datetime]:
    """Coerce a stored value (datetime or ISO string) to an aware UTC datetime."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


class StoryReminderTrigger:
    def __init__(self):
        self.notification_service = NotificationService()

    async def check_story_reminders(self) -> Dict[str, Any]:
        now_utc = datetime.utcnow()
        now_utc_aware = now_utc.replace(tzinfo=timezone.utc)
        sent = skipped = errors = 0
        by_tier = {"resume": 0, "unlock": 0, "discover": 0}

        print(f"\n📖 [STORY REMINDER] Start {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        try:
            prefs_cursor = notification_preferences_collection.find({
                "story_reminders_enabled": True
            })

            async for prefs in prefs_cursor:
                try:
                    user_id = prefs["user_id"]
                    local_time = rc.local_time_for(prefs, now_utc)

                    # Global gates shared with every reminder kind.
                    if rc.is_quiet_hours(prefs, local_time):
                        skipped += 1
                        continue
                    if not rc.can_send_more_this_week(prefs, now_utc):
                        skipped += 1
                        continue

                    # Fetch user once — need push token + timezone truth.
                    user = await users_collection.find_one({"_id": ObjectId(user_id)})
                    if not user or not user.get("push_token"):
                        skipped += 1
                        continue
                    push_token = user["push_token"]

                    # Prefer the user doc's timezone if prefs didn't carry one.
                    if not prefs.get("timezone") and user.get("timezone"):
                        prefs = {**prefs, "timezone": user["timezone"]}
                        local_time = rc.local_time_for(prefs, now_utc)

                    # Decide which tier (if any) applies. One push per user.
                    tier, payload = await self._decide_tier(
                        user_id, prefs, local_time, now_utc_aware
                    )
                    if not tier:
                        skipped += 1
                        continue

                    # Per-kind daily anti-spam: never two of the SAME story
                    # reminder in one local day. (A different kind on another
                    # day is fine.)
                    if rc.already_sent_today(prefs, f"story_{tier}", local_time):
                        skipped += 1
                        continue

                    title, body, data = payload
                    ok = await self._send(user_id, push_token, title, body, data,
                                          kind=f"story_{tier}", now_utc=now_utc)
                    if ok:
                        sent += 1
                        by_tier[tier] += 1
                    else:
                        errors += 1

                except Exception as ue:
                    errors += 1
                    print(f"❌ [STORY REMINDER] user error: {ue}")
                    continue

            print(f"✅ [STORY REMINDER] Sent {sent} (resume={by_tier['resume']}, "
                  f"unlock={by_tier['unlock']}, discover={by_tier['discover']}), "
                  f"skipped {skipped}, errors {errors}")
            return {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": sent,
                "reminders_skipped": skipped,
                "errors": errors,
                "by_tier": by_tier,
            }
        except Exception as e:
            print(f"❌ [STORY REMINDER] fatal: {e}")
            return {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": sent,
                "reminders_skipped": skipped,
                "errors": errors + 1,
                "error": str(e),
            }

    async def _decide_tier(self, user_id: str, prefs: Dict[str, Any],
                           local_time: datetime, now_utc_aware: datetime):
        """
        Returns (tier, (title, body, data)) or (None, None).
        Precedence: UNLOCK (morning, high intent) > RESUME (evening) > DISCOVER.
        """
        preferred_hour = prefs.get("preferred_notification_time", 18)
        in_morning = MORNING_START <= local_time.hour < MORNING_END
        in_preferred = local_time.hour == preferred_hour

        # Newest in_progress series for this user (index-covered sort).
        active = await story_progress_collection.find_one(
            {"user_id": user_id, "status": "in_progress"},
            sort=[("last_played_at", -1)],
        )

        # ── B. UNLOCK (morning only) ─────────────────────────────────────
        if in_morning and active:
            cur = active.get("current") or {}
            unlocked_at = _parse_dt(cur.get("unlocked_at"))
            last_played = _parse_dt(active.get("last_played_at"))
            if unlocked_at and unlocked_at <= now_utc_aware:
                # Episode is now playable. Only nudge if they haven't already
                # played SINCE it unlocked (else they clearly know).
                if not last_played or last_played < unlocked_at:
                    ep = cur.get("episode_number")
                    data = {
                        "type": "story_reminder",
                        "tier": "unlock",
                        "screen": "StoryWorlds",
                        "series_id": active.get("series_id"),
                        "user_id": user_id,
                    }
                    return "unlock", (
                        "New episode unlocked 📖",
                        (f"Episode {ep} is ready to play — continue your story!"
                         if ep else "A new episode is ready — continue your story!"),
                        data,
                    )

        # ── A. RESUME (evening / preferred hour only) ────────────────────
        if in_preferred and active:
            last_played = _parse_dt(active.get("last_played_at"))
            if last_played and (now_utc_aware - last_played).days >= STALE_DAYS:
                data = {
                    "type": "story_reminder",
                    "tier": "resume",
                    "screen": "StoryWorlds",
                    "series_id": active.get("series_id"),
                    "user_id": user_id,
                }
                return "resume", (
                    "Your story is waiting 📖",
                    "Pick up where you left off — your next scene is ready.",
                    data,
                )

        # ── C. DISCOVER (weekly, engaged-but-never-played) ───────────────
        # Only on the configured local weekday, at the user's preferred hour,
        # so it's at most once/week even before the budget cap.
        if in_preferred and local_time.weekday() == DISCOVER_WEEKDAY and not active:
            # Never completed an episode AND has no in_progress series.
            user = await users_collection.find_one(
                {"_id": ObjectId(user_id)},
                {"stats.lifetime.story_episodes_completed": 1},
            )
            completed = (
                ((user or {}).get("stats", {}) or {})
                .get("lifetime", {})
                .get("story_episodes_completed", 0)
            )
            if not completed:
                # Confirm they're actually engaged (any story_progress doc means
                # they at least opened one; require ZERO docs => truly never
                # tried, which is exactly the discover target).
                any_progress = await story_progress_collection.find_one(
                    {"user_id": user_id}
                )
                if not any_progress:
                    data = {
                        "type": "story_reminder",
                        "tier": "discover",
                        "screen": "StoryWorlds",
                        "user_id": user_id,
                    }
                    return "discover", (
                        "Try a Story Adventure ✨",
                        "Learn through an interactive story — start your first episode today.",
                        data,
                    )

        return None, None

    async def _send(self, user_id, push_token, title, body, data, kind, now_utc):
        try:
            result = self.notification_service.send_expo_push_notification(
                push_tokens=[push_token],
                title=title,
                body=body,
                data=data,
                priority="default",
            )
            if result.get("success"):
                await rc.record_send(user_id, kind, now_utc)
                print(f"✅ [STORY REMINDER] {kind} -> {user_id}")
                return True
            print(f"⚠️ [STORY REMINDER] send failed {kind} -> {user_id}: {result.get('message')}")
            return False
        except Exception as e:
            print(f"❌ [STORY REMINDER] send error {kind} -> {user_id}: {e}")
            return False


story_reminder_trigger = StoryReminderTrigger()


async def run_story_reminder_check():
    return await story_reminder_trigger.check_story_reminders()
