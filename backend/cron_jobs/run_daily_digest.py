"""
Daily Digest Scheduler - Proactive Coach Messages

This scheduled job runs every morning to:
1. Generate personalized daily digest messages for all active users
2. Send digest messages via push notifications at optimal times
3. Track delivery and engagement metrics

Schedule: Runs every hour to check for pending digest messages to send

Author: MyTacoAI Backend Team
Date: 2026-04-20
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# Initialize MongoDB connection
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

users_collection = database.users
daily_digest_messages_collection = database.daily_digest_messages

# Import services (after DB setup)
from services.daily_digest_generator import daily_digest_generator
from notification_service import send_push_notification


async def generate_digests_for_active_users():
    """
    Generate daily digest messages for all active users.

    Active users are defined as:
    - Users who have practiced in the last 30 days, OR
    - Users who have never practiced (new users)
    """
    print("\n" + "="*60)
    print(f"Daily Digest Generation - {datetime.utcnow().isoformat()}")
    print("="*60)

    try:
        # Find active users
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Query for users who:
        # 1. Have push tokens (can receive notifications)
        # 2. Either have journey_state.days_since_last_activity < 30 OR no journey_state yet
        active_users = await users_collection.find({
            "push_token": {"$exists": True, "$ne": None},
            "$or": [
                {"journey_state.days_since_last_activity": {"$lt": 30}},
                {"journey_state": {"$exists": False}}  # New users
            ]
        }).to_list(None)

        print(f"Found {len(active_users)} active users with push tokens")

        # Generate digests
        generated_count = 0
        error_count = 0

        for user in active_users:
            try:
                user_id = str(user["_id"])
                user_name = user.get("name", "User")

                # Generate digest
                digest = await daily_digest_generator.generate_daily_digest(user_id)

                if digest:
                    generated_count += 1
                    print(f"✓ Generated digest for {user_name} (ID: {user_id[:8]}...)")
                else:
                    print(f"  Skip: {user_name} already has today's digest")

            except Exception as e:
                error_count += 1
                print(f"✗ Error generating digest for user {user.get('name', 'Unknown')}: {str(e)}")

        print(f"\nGeneration Summary:")
        print(f"  - Digests generated: {generated_count}")
        print(f"  - Errors: {error_count}")
        print(f"  - Total processed: {len(active_users)}")

        return generated_count

    except Exception as e:
        print(f"ERROR in generate_digests_for_active_users: {str(e)}")
        return 0


async def send_pending_digest_messages():
    """
    Send digest messages that are scheduled for now or earlier.

    Checks for digest messages where:
    - scheduled_for <= now
    - sent = False
    """
    print("\n" + "="*60)
    print(f"Daily Digest Delivery - {datetime.utcnow().isoformat()}")
    print("="*60)

    try:
        # Find pending digest messages
        now = datetime.utcnow()

        pending_digests = await daily_digest_messages_collection.find({
            "scheduled_for": {"$lte": now},
            "sent": False
        }).to_list(None)

        print(f"Found {len(pending_digests)} pending digest messages to send")

        sent_count = 0
        error_count = 0

        for digest in pending_digests:
            try:
                user_id = digest["user_id"]

                # Get user for push token
                user = await users_collection.find_one({"_id": user_id})
                if not user:
                    print(f"  Skip: User not found for digest {digest['_id']}")
                    continue

                push_token = user.get("push_token")
                if not push_token:
                    print(f"  Skip: No push token for user {user.get('name', 'Unknown')}")
                    # Mark as sent anyway (can't deliver)
                    await daily_digest_messages_collection.update_one(
                        {"_id": digest["_id"]},
                        {"$set": {"sent": True, "sent_at": datetime.utcnow()}}
                    )
                    continue

                # Send push notification
                notification_data = {
                    "title": digest["subject"],
                    "body": digest["message"],
                    "data": {
                        "type": "daily_digest",
                        "digest_id": str(digest["_id"]),
                        "message_type": digest["message_type"],
                        "quick_actions": digest.get("quick_actions", []),
                        "screen": "Coach"  # Open coach modal
                    }
                }

                success = await send_push_notification(
                    push_token=push_token,
                    title=notification_data["title"],
                    body=notification_data["body"],
                    data=notification_data["data"],
                    user_id=user_id
                )

                if success:
                    sent_count += 1
                    print(f"✓ Sent digest to {user.get('name', 'User')} - {digest['subject']}")

                    # Update digest as sent
                    await daily_digest_messages_collection.update_one(
                        {"_id": digest["_id"]},
                        {
                            "$set": {
                                "sent": True,
                                "sent_at": datetime.utcnow(),
                                "notification_id": str(digest["_id"])  # For tracking
                            }
                        }
                    )
                else:
                    error_count += 1
                    print(f"✗ Failed to send digest to {user.get('name', 'User')}")

            except Exception as e:
                error_count += 1
                print(f"✗ Error sending digest {digest.get('_id', 'unknown')}: {str(e)}")

        print(f"\nDelivery Summary:")
        print(f"  - Digests sent: {sent_count}")
        print(f"  - Errors: {error_count}")
        print(f"  - Total pending: {len(pending_digests)}")

        return sent_count

    except Exception as e:
        print(f"ERROR in send_pending_digest_messages: {str(e)}")
        return 0


async def cleanup_old_digests():
    """
    Clean up old digest messages (older than 30 days).

    Note: TTL index should handle this automatically, but this is a backup.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        result = await daily_digest_messages_collection.delete_many({
            "generated_at": {"$lt": thirty_days_ago}
        })

        if result.deleted_count > 0:
            print(f"\nCleaned up {result.deleted_count} old digest messages")

        return result.deleted_count

    except Exception as e:
        print(f"ERROR in cleanup_old_digests: {str(e)}")
        return 0


async def run_daily_digest_job():
    """
    Main job function - runs both generation and delivery.

    This should be called:
    1. Once per day (early morning) for generation
    2. Every hour for delivery check
    """
    print("\n" + "🌅 DAILY DIGEST JOB STARTED " + "="*40)

    # Step 1: Generate new digests (only run once per day, e.g., at 2 AM UTC)
    current_hour = datetime.utcnow().hour
    if current_hour == 2:  # Generate at 2 AM UTC
        print("\n[GENERATION PHASE]")
        generated = await generate_digests_for_active_users()
        print(f"Generation phase complete: {generated} digests created")

    # Step 2: Send pending digests (run every hour)
    print("\n[DELIVERY PHASE]")
    sent = await send_pending_digest_messages()
    print(f"Delivery phase complete: {sent} digests sent")

    # Step 3: Cleanup (run once per day, e.g., at 3 AM UTC)
    if current_hour == 3:
        print("\n[CLEANUP PHASE]")
        cleaned = await cleanup_old_digests()
        print(f"Cleanup phase complete: {cleaned} old digests removed")

    print("\n" + "✅ DAILY DIGEST JOB COMPLETED " + "="*40 + "\n")


async def main():
    """Main entry point for the scheduled job"""
    try:
        await run_daily_digest_job()
    except Exception as e:
        print(f"FATAL ERROR in daily digest job: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close MongoDB connection
        client.close()


if __name__ == "__main__":
    # Run the job
    asyncio.run(main())
