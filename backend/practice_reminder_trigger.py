"""
Daily Practice Reminder Trigger
Sends reminders to users who haven't practiced today at their preferred time
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from bson import ObjectId
import pytz

from database import (
    users_collection,
    notification_preferences_collection,
    daily_stats_collection
)
from notification_service import NotificationService
from reminder_common import (
    already_sent_any_today,
    can_send_more_this_week,
    record_send,
)

import logging
logger = logging.getLogger(__name__)


class PracticeReminderTrigger:
    """Service for checking and sending daily practice reminders"""

    def __init__(self):
        self.notification_service = NotificationService()

    async def check_practice_reminders(self) -> Dict[str, Any]:
        """
        Check for users who need practice reminders and send notifications.
        Should be called every hour (or more frequently).

        Returns summary of reminders sent.
        """
        print(f"\n📚 [PRACTICE REMINDER] Starting practice reminder check at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        reminders_sent = 0
        reminders_skipped = 0
        errors = 0

        try:
            # Get current UTC time
            now_utc = datetime.utcnow()

            # Find all users with practice reminders enabled. Default-ON
            # semantics ($ne False) match the news/story/plan triggers: a doc
            # that predates the field isn't an opt-out.
            prefs_cursor = notification_preferences_collection.find({
                "practice_reminders_enabled": {"$ne": False}
            })

            async for prefs in prefs_cursor:
                try:
                    user_id = prefs["user_id"]

                    # Get user's timezone (default to UTC if not set)
                    user_timezone = prefs.get("timezone", "UTC")
                    preferred_hour = prefs.get("preferred_notification_time", 18)  # Default 6 PM (works well globally)

                    # Convert current UTC time to user's local time
                    try:
                        tz = pytz.timezone(user_timezone)
                        local_time = now_utc.replace(tzinfo=pytz.UTC).astimezone(tz)
                    except Exception as tz_error:
                        logger.warning(f"Invalid timezone {user_timezone} for user {user_id}, using UTC")
                        local_time = now_utc
                        user_timezone = "UTC"

                    current_hour = local_time.hour

                    # Check if it's the user's preferred notification time
                    # Allow 1-hour window (e.g., if preferred is 10 AM, send between 10:00-10:59)
                    if current_hour != preferred_hour:
                        continue  # Not their preferred time yet

                    # Check if in quiet hours
                    if prefs.get("quiet_hours_enabled", False):
                        quiet_start = prefs.get("quiet_hours_start", 22)
                        quiet_end = prefs.get("quiet_hours_end", 8)

                        if quiet_start > quiet_end:  # Crosses midnight
                            in_quiet_hours = current_hour >= quiet_start or current_hour < quiet_end
                        else:
                            in_quiet_hours = quiet_start <= current_hour < quiet_end

                        if in_quiet_hours:
                            reminders_skipped += 1
                            continue

                    # Check the shared weekly notification budget.
                    #
                    # This MUST go through reminder_common: the inline version that
                    # used to live here compared the raw counter against the cap with
                    # no week-expiry check. Because the counter is only ever reset
                    # inside the post-send block below, a user who reached the cap
                    # could never send again, so the reset could never run — a
                    # permanent lockout. Three prod docs sat silently at cnt=3 from
                    # January onward because of exactly this.
                    if not can_send_more_this_week(prefs, now_utc):
                        reminders_skipped += 1
                        continue

                    # Check if they already practiced today
                    local_date = local_time.strftime("%Y-%m-%d")
                    daily_stats = await daily_stats_collection.find_one({
                        "user_id": user_id,
                        "date": local_date
                    })

                    if daily_stats and daily_stats.get("total_challenges", 0) > 0:
                        # User already practiced today, skip reminder
                        reminders_skipped += 1
                        continue

                    # One reminder per local day, of ANY kind. The replaced
                    # version compared last_notification_sent_at against the UTC
                    # date, which drifts from the user's day near midnight, and
                    # it could not see sends made by the news/story/plan triggers
                    # at all — so all four could stack inside the same hour.
                    if already_sent_any_today(prefs, local_time):
                        reminders_skipped += 1
                        continue

                    # Get user's push token
                    user = await users_collection.find_one({"_id": ObjectId(user_id)})

                    if not user or not user.get("push_token"):
                        reminders_skipped += 1
                        continue

                    push_token = user["push_token"]

                    # Get user's current streak for personalized message
                    current_streak = user.get("current_streak", 0)

                    # Create personalized message
                    if current_streak > 0:
                        body = f"Keep your {current_streak}-day streak alive! 🔥 Practice for 5 minutes today."
                    else:
                        body = "Time to practice! 📚 Start building your learning streak today."

                    # Send notification
                    print(f"📤 Sending practice reminder to user {user_id} ({user_timezone} {current_hour}:00)")

                    try:
                        result = self.notification_service.send_expo_push_notification(
                            push_tokens=[push_token],
                            title="Time to Practice! 📚",
                            body=body,
                            data={
                                "type": "practice_reminder",
                                "user_id": user_id
                            },
                            priority="default"
                        )

                        if result.get("success"):
                            reminders_sent += 1
                            print(f"✅ Practice reminder sent to user {user_id}")

                            # Book the send through the shared helper so the weekly
                            # rollover matches the budget CHECK above exactly, and
                            # so this reminder also lands in last_sent_by_kind
                            # alongside news/story/plan.
                            await record_send(user_id, "practice", now_utc)
                        else:
                            errors += 1
                            print(f"⚠️ Failed to send practice reminder: {result.get('message')}")

                    except Exception as notif_error:
                        errors += 1
                        print(f"❌ Error sending practice reminder to user {user_id}: {str(notif_error)}")

                except Exception as user_error:
                    errors += 1
                    print(f"❌ Error processing user for practice reminder: {str(user_error)}")
                    continue

            summary = {
                "timestamp": now_utc.isoformat(),
                "reminders_sent": reminders_sent,
                "reminders_skipped": reminders_skipped,
                "errors": errors
            }

            print(f"✅ [PRACTICE REMINDER] Complete - Sent: {reminders_sent}, Skipped: {reminders_skipped}, Errors: {errors}")

            return summary

        except Exception as e:
            print(f"❌ [PRACTICE REMINDER] Fatal error: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "reminders_sent": reminders_sent,
                "reminders_skipped": reminders_skipped,
                "errors": errors + 1,
                "error": str(e)
            }


# Singleton instance
practice_reminder_trigger = PracticeReminderTrigger()


async def run_practice_reminder_check():
    """Standalone function to run practice reminder check (for scheduler)"""
    return await practice_reminder_trigger.check_practice_reminders()
