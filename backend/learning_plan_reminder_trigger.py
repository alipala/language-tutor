"""
Learning-plan reminder trigger — revives the previously-dead
learning_plan_updates_enabled preference.

Fires at the user's preferred hour when they have an ACTIVE learning plan
(status not archived, completed_sessions < total_sessions) that has gone stale
(no update for >= STALE_DAYS days). "You're N% through your plan — your next
session is ready." Deep-links to the learning plan.

Gated on notification_preferences.learning_plan_updates_enabled + the shared
reminder budget + per-kind daily stamp ("learning_plan"). Picks the most
recently touched active plan if the user has several.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from bson import ObjectId

from database import (
    users_collection,
    notification_preferences_collection,
    learning_plans_collection,
)
from notification_service import NotificationService
import reminder_common as rc

import logging
logger = logging.getLogger(__name__)

STALE_DAYS = int(os.getenv("PLAN_REMINDER_STALE_DAYS", "2"))


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


def _is_active(plan: Dict[str, Any]) -> bool:
    if plan.get("status") == "archived":
        return False
    total = plan.get("total_sessions") or 0
    done = plan.get("completed_sessions") or 0
    # No schedule yet (total 0) -> not actionable as a "continue" nudge.
    if total <= 0:
        return False
    return done < total


class LearningPlanReminderTrigger:
    def __init__(self):
        self.notification_service = NotificationService()

    async def check_plan_reminders(self) -> Dict[str, Any]:
        now_utc = datetime.utcnow()
        now_utc_aware = now_utc.replace(tzinfo=timezone.utc)
        sent = skipped = errors = 0

        print(f"\n🎯 [PLAN REMINDER] Start {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        try:
            # Default-ON semantics: match unless EXPLICITLY disabled.
            prefs_cursor = notification_preferences_collection.find({
                "learning_plan_updates_enabled": {"$ne": False}
            })

            async for prefs in prefs_cursor:
                try:
                    user_id = prefs["user_id"]
                    local_time = rc.local_time_for(prefs, now_utc)

                    if not rc.is_preferred_hour(prefs, local_time):
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
                    if not prefs.get("timezone") and user.get("timezone"):
                        prefs = {**prefs, "timezone": user["timezone"]}
                        local_time = rc.local_time_for(prefs, now_utc)
                        if not rc.is_preferred_hour(prefs, local_time):
                            skipped += 1
                            continue

                    plan = await self._active_stale_plan(user_id, now_utc_aware)
                    if not plan:
                        skipped += 1
                        continue

                    total = plan.get("total_sessions") or 0
                    done = plan.get("completed_sessions") or 0
                    pct = int(round((done / total) * 100)) if total else 0
                    lang = (plan.get("language") or "").title()

                    title = "Your learning plan 🎯"
                    if pct > 0:
                        body = (f"You're {pct}% through your {lang} plan — "
                                f"your next session is ready.").replace("  ", " ")
                    else:
                        body = (f"Your {lang} plan is waiting — "
                                f"start your next session today.").replace("  ", " ")

                    # Learning plans live on the Dashboard (DailyHub) tab inside
                    # the "Main" tab navigator — there is no root "LearningPlan"
                    # route. App.js taps navigate(data.screen, data.params).
                    data = {
                        "type": "learning_plan_reminder",
                        "screen": "Main",
                        "params": {"screen": "Dashboard"},
                        "plan_id": str(plan.get("_id") or plan.get("id") or ""),
                        "user_id": user_id,
                    }

                    ok = await self._send(user_id, user["push_token"],
                                          title, body, data, now_utc)
                    if ok:
                        sent += 1
                    else:
                        errors += 1

                except Exception as ue:
                    errors += 1
                    print(f"❌ [PLAN REMINDER] user error: {ue}")
                    continue

            print(f"✅ [PLAN REMINDER] Sent {sent}, skipped {skipped}, errors {errors}")
            return {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": sent,
                "reminders_skipped": skipped,
                "errors": errors,
            }
        except Exception as e:
            print(f"❌ [PLAN REMINDER] fatal: {e}")
            return {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": sent,
                "reminders_skipped": skipped,
                "errors": errors + 1,
                "error": str(e),
            }

    async def _active_stale_plan(self, user_id: str, now_utc_aware: datetime):
        """Most recently updated ACTIVE plan that's gone stale, else None."""
        cursor = learning_plans_collection.find(
            {"user_id": user_id}
        ).sort("updated_at", -1)
        async for plan in cursor:
            if not _is_active(plan):
                continue
            updated = _parse_dt(plan.get("updated_at")) or _parse_dt(plan.get("created_at"))
            if updated and (now_utc_aware - updated).days >= STALE_DAYS:
                return plan
            # Newest active plan is fresh -> no stale nudge for this user.
            return None
        return None

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
                await rc.record_send(user_id, "learning_plan", now_utc)
                print(f"✅ [PLAN REMINDER] -> {user_id}")
                return True
            print(f"⚠️ [PLAN REMINDER] send failed -> {user_id}: {result.get('message')}")
            return False
        except Exception as e:
            print(f"❌ [PLAN REMINDER] send error -> {user_id}: {e}")
            return False


learning_plan_reminder_trigger = LearningPlanReminderTrigger()


async def run_plan_reminder_check():
    return await learning_plan_reminder_trigger.check_plan_reminders()
