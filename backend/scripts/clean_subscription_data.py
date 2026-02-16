"""
One-time script to clean up subscription data
Run BEFORE deploying new code to start with a clean slate

Usage:
    python scripts/clean_subscription_data.py

Options:
    - Delete all users (default, as requested by user)
    - Reset subscription data only (commented out, can be uncommented if needed)
"""

import asyncio
import sys
import os

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import database
from logging_config import logger


async def delete_all_users():
    """
    Delete all users from the database
    WARNING: This is destructive and cannot be undone!
    """
    logger.warning("=" * 80)
    logger.warning("⚠️  WARNING: About to delete ALL users from database!")
    logger.warning("=" * 80)

    # Safety confirmation
    confirmation = input("\nType 'DELETE ALL USERS' to confirm: ")
    if confirmation != "DELETE ALL USERS":
        logger.info("❌ Operation cancelled by user")
        return 0

    try:
        # Delete all users
        result = await database["users"].delete_many({})
        count = result.deleted_count

        logger.info(f"✅ Deleted {count} users from database")

        return count

    except Exception as e:
        logger.error(f"❌ Error deleting users: {str(e)}")
        raise


async def reset_subscription_data_only():
    """
    Alternative: Keep users but reset their subscription data
    This preserves user accounts, authentication, and progress
    """
    logger.warning("=" * 80)
    logger.warning("⚠️  WARNING: About to reset subscription data for ALL users!")
    logger.warning("=" * 80)

    # Safety confirmation
    confirmation = input("\nType 'RESET SUBSCRIPTIONS' to confirm: ")
    if confirmation != "RESET SUBSCRIPTIONS":
        logger.info("❌ Operation cancelled by user")
        return 0

    try:
        # Reset all subscription-related fields
        result = await database["users"].update_many(
            {},
            {
                "$set": {
                    # Reset to free plan
                    "subscription_plan": "try_learn",
                    "subscription_status": "inactive",
                    "subscription_provider": None,
                    "subscription_period": None,
                    "subscription_expires_at": None,

                    # Reset usage counters
                    "practice_minutes_used": 0.0,
                    "practice_sessions_used": 0,
                    "assessments_used": 0,

                    # Reset period tracking
                    "current_period_start": None,
                    "current_period_end": None,
                },
                "$unset": {
                    # Remove nested subscription object (old format)
                    "subscription": 1,

                    # Remove provider-specific fields
                    "stripe_customer_id": 1,
                    "stripe_subscription_id": 1,
                    "apple_transaction_id": 1,
                    "apple_product_id": 1,
                    "apple_original_transaction_id": 1,
                    "apple_is_trial": 1,
                    "google_play_product_id": 1,
                    "google_play_purchase_token": 1,
                    "google_play_order_id": 1,
                    "google_play_is_trial": 1,
                    "google_play_auto_renewing": 1,
                }
            }
        )

        count = result.modified_count
        logger.info(f"✅ Reset subscription data for {count} users")

        return count

    except Exception as e:
        logger.error(f"❌ Error resetting subscription data: {str(e)}")
        raise


async def main():
    """
    Main entry point
    Allows choosing between deletion and reset
    """
    print("\n" + "=" * 80)
    print("🔧 SUBSCRIPTION DATA CLEANUP SCRIPT")
    print("=" * 80)
    print("\nOptions:")
    print("  1. Delete ALL users (recommended for clean slate)")
    print("  2. Reset subscription data only (preserve user accounts)")
    print("  3. Cancel")
    print()

    choice = input("Enter your choice (1-3): ").strip()

    if choice == "1":
        count = await delete_all_users()
        print(f"\n✅ Cleanup complete: {count} users deleted")
    elif choice == "2":
        count = await reset_subscription_data_only()
        print(f"\n✅ Cleanup complete: {count} users reset")
    elif choice == "3":
        print("\n❌ Operation cancelled")
    else:
        print("\n❌ Invalid choice")

    print()


if __name__ == "__main__":
    logger.info("=== Subscription Data Cleanup Script - Manual Execution ===")
    asyncio.run(main())
