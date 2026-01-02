"""
Notification Triggers
Background services that check for events and send automated notifications
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from bson import ObjectId

from database import (
    users_collection,
    notification_preferences_collection
)
from notification_service import NotificationService
from services.heart_service import HeartService
from models import HeartPool

import logging
logger = logging.getLogger(__name__)


class NotificationTriggers:
    """Service for checking triggers and sending automated notifications"""

    def __init__(self):
        self.notification_service = NotificationService()
        self.heart_service = HeartService()

    async def check_heart_refills(self) -> Dict[str, Any]:
        """
        Check for users whose hearts have fully refilled and send notifications.
        This should be called periodically (e.g., every 30 minutes).

        Returns summary of notifications sent.
        """
        print("\n🔔 [HEART REFILL CHECK] Starting heart refill notification check...")

        notifications_sent = 0
        notifications_skipped = 0
        errors = 0

        try:
            # Find all users with heart system initialized
            users_with_hearts = users_collection.find({
                "heart_system": {"$exists": True}
            })

            async for user in users_with_hearts:
                try:
                    user_id = str(user["_id"])
                    heart_system = user.get("heart_system", {})
                    heart_pools = heart_system.get("heart_pools", {})

                    # Check notification preferences
                    prefs = await notification_preferences_collection.find_one({"user_id": user_id})

                    # Default to True if no preferences (achievement_alerts covers game mechanics)
                    send_notification = True
                    if prefs:
                        send_notification = prefs.get("achievement_alerts_enabled", True)

                    if not send_notification:
                        notifications_skipped += 1
                        continue

                    # Check if user has push token
                    push_token = user.get("push_token")
                    if not push_token:
                        notifications_skipped += 1
                        continue

                    # Check each challenge type's heart pool
                    for challenge_type, pool_data in heart_pools.items():
                        pool = HeartPool(**pool_data)

                        # Skip if not refilling
                        if not pool.refill_started_at:
                            continue

                        # Skip if hearts not depleted (shouldn't happen, but safety check)
                        if pool.current_hearts >= pool.max_hearts:
                            continue

                        # Calculate refilled hearts
                        elapsed_minutes = (datetime.utcnow() - pool.refill_started_at).total_seconds() / 60
                        refilled_count = int(elapsed_minutes / pool.refill_rate_minutes) if pool.refill_rate_minutes > 0 else 0
                        new_hearts = min(pool.current_hearts + refilled_count, pool.max_hearts)

                        # Check if just became fully refilled
                        if new_hearts >= pool.max_hearts and pool.current_hearts < pool.max_hearts:
                            # Check if we already notified for this refill
                            # Use a tracking field to avoid duplicate notifications
                            last_notified = pool_data.get("last_refill_notified_at")

                            if last_notified:
                                last_notified_dt = last_notified if isinstance(last_notified, datetime) else datetime.fromisoformat(last_notified)

                                # Only notify if it's been more than 1 hour since last notification
                                # (prevents spam if hearts were refilled multiple times)
                                if (datetime.utcnow() - last_notified_dt).total_seconds() < 3600:
                                    notifications_skipped += 1
                                    continue

                            # Send notification!
                            print(f"📤 Sending heart refill notification to user {user_id} for {challenge_type}")

                            try:
                                result = self.notification_service.send_expo_push_notification(
                                    push_tokens=[push_token],
                                    title="Hearts Refilled! ❤️",
                                    body=f"{pool.max_hearts} hearts ready for {challenge_type.replace('_', ' ').title()} challenges!",
                                    data={
                                        "type": "heart_refill",
                                        "challenge_type": challenge_type,
                                        "hearts_refilled": pool.max_hearts
                                    },
                                    priority="default"
                                )

                                if result.get("success"):
                                    notifications_sent += 1
                                    print(f"✅ Heart refill notification sent to user {user_id}")

                                    # Update last_refill_notified_at
                                    await users_collection.update_one(
                                        {"_id": ObjectId(user_id)},
                                        {"$set": {
                                            f"heart_system.heart_pools.{challenge_type}.last_refill_notified_at": datetime.utcnow()
                                        }}
                                    )
                                else:
                                    errors += 1
                                    print(f"⚠️ Failed to send heart refill notification: {result.get('message')}")

                            except Exception as notif_error:
                                errors += 1
                                print(f"❌ Error sending heart refill notification to user {user_id}: {str(notif_error)}")

                except Exception as user_error:
                    errors += 1
                    print(f"❌ Error processing user for heart refill: {str(user_error)}")
                    continue

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "notifications_sent": notifications_sent,
                "notifications_skipped": notifications_skipped,
                "errors": errors
            }

            print(f"✅ [HEART REFILL CHECK] Complete - Sent: {notifications_sent}, Skipped: {notifications_skipped}, Errors: {errors}")

            return summary

        except Exception as e:
            print(f"❌ [HEART REFILL CHECK] Fatal error: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "notifications_sent": notifications_sent,
                "notifications_skipped": notifications_skipped,
                "errors": errors + 1,
                "error": str(e)
            }


# Singleton instance
notification_triggers = NotificationTriggers()


async def run_heart_refill_check():
    """Standalone function to run heart refill check (for scheduler)"""
    return await notification_triggers.check_heart_refills()
