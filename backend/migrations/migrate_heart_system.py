"""
Heart System Migration Script

This script initializes the heart system for all existing users.
Run this once after deploying the heart system.

Usage:
    python migrations/migrate_heart_system.py
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from services.heart_service import HeartService
from models import UserInDB

# MongoDB connection string
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=60000&retryWrites=true&retryReads=true"


async def migrate_heart_system():
    """
    Initialize heart system for all existing users
    Run this once after deploying heart system
    """
    print("="*80)
    print("HEART SYSTEM MIGRATION")
    print("="*80)
    print()

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.language_tutor

    heart_service = HeartService()
    heart_service.db = db  # Override database connection

    # Find all users without heart_system
    users_to_migrate = await db.users.find({
        "heart_system": {"$exists": False}
    }).to_list(length=None)

    print(f"Found {len(users_to_migrate)} users to migrate")
    print()

    migrated_count = 0
    error_count = 0
    skipped_count = 0

    for user_doc in users_to_migrate:
        try:
            # Keep original ObjectId for update query
            original_id = user_doc['_id']

            # Convert to UserInDB model
            user_doc['_id'] = str(user_doc['_id'])  # Convert ObjectId to string for model
            user = UserInDB(**user_doc)

            # Check subscription plan
            subscription_plan = user.subscription_plan or "try_learn"
            subscription_status = user.subscription_status or "inactive"

            print(f"Migrating user: {user.email}")
            print(f"  - Plan: {subscription_plan}")
            print(f"  - Status: {subscription_status}")

            # Initialize heart system (manually to use original ObjectId)
            tier_config = heart_service.TIER_CONFIG.get(
                subscription_plan,
                heart_service.TIER_CONFIG["try_learn"]
            )

            heart_pools = {}
            for challenge_type in heart_service.CHALLENGE_TYPES:
                heart_pools[challenge_type] = {
                    "challenge_type": challenge_type,
                    "current_hearts": tier_config["max_hearts"],
                    "max_hearts": tier_config["max_hearts"],
                    "refill_rate_minutes": tier_config["refill_minutes_per_heart"],
                    "last_heart_lost_at": None,
                    "refill_started_at": None,
                    "streak_shield_active": False,
                    "streak_shield_activated_at": None,
                    "current_correct_streak": 0
                }

            heart_system_dict = {
                "heart_pools": heart_pools,
                "last_updated": datetime.utcnow(),
                "feature_enabled": True
            }

            # Update user document using original ObjectId
            result = await db.users.update_one(
                {"_id": original_id},
                {"$set": {"heart_system": heart_system_dict}}
            )

            if result.modified_count == 0:
                print(f"  ⚠️  Warning: No document modified for {user.email}")

            # Convert back to HeartSystemState for display
            from models import HeartPool, HeartSystemState
            heart_pools_models = {
                k: HeartPool(**v) for k, v in heart_pools.items()
            }
            heart_system = HeartSystemState(
                heart_pools=heart_pools_models,
                last_updated=heart_system_dict["last_updated"],
                feature_enabled=True
            )

            print(f"  ✅ Initialized with hearts:")
            for challenge_type, pool in heart_system.heart_pools.items():
                print(f"     - {challenge_type}: {pool.current_hearts}/{pool.max_hearts} hearts")

            migrated_count += 1
            print()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            error_count += 1
            import traceback
            print(traceback.format_exc())
            print()

    print("="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print(f"✅ Migrated: {migrated_count}")
    print(f"❌ Errors: {error_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"Total: {len(users_to_migrate)}")
    print()

    # Verify migration
    print("="*80)
    print("VERIFICATION")
    print("="*80)

    total_users = await db.users.count_documents({})
    users_with_hearts = await db.users.count_documents({
        "heart_system": {"$exists": True}
    })

    print(f"Total users: {total_users}")
    print(f"Users with heart system: {users_with_hearts}")
    print(f"Coverage: {(users_with_hearts / total_users * 100):.1f}%")
    print()

    # Show sample user's heart status
    print("="*80)
    print("SAMPLE USER HEART STATUS")
    print("="*80)

    sample_user = await db.users.find_one({"heart_system": {"$exists": True}})
    if sample_user:
        print(f"User: {sample_user.get('email', 'N/A')}")
        print(f"Subscription: {sample_user.get('subscription_plan', 'try_learn')}")
        print(f"Heart System:")

        heart_system = sample_user.get('heart_system', {})
        heart_pools = heart_system.get('heart_pools', {})

        for challenge_type, pool in heart_pools.items():
            print(f"  - {challenge_type}:")
            print(f"      Current: {pool.get('current_hearts', 0)}")
            print(f"      Max: {pool.get('max_hearts', 0)}")
            print(f"      Shield: {'✅ Active' if pool.get('streak_shield_active', False) else '❌ Inactive'}")
            print(f"      Streak: {pool.get('current_correct_streak', 0)}")

    print()
    print("="*80)
    print("✅ Migration completed successfully!")
    print("="*80)

    # Close MongoDB connection
    client.close()


if __name__ == "__main__":
    print()
    print("⚠️  WARNING: This will initialize heart system for ALL users")
    print("⚠️  Make sure you have backed up your database!")
    print()

    response = input("Do you want to continue? (yes/no): ")

    if response.lower() == "yes":
        asyncio.run(migrate_heart_system())
    else:
        print("Migration cancelled.")
