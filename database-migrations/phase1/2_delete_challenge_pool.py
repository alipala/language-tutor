"""
Phase 1 - Step 2: Delete Challenge Pool
========================================
⚠️  DESTRUCTIVE: Deletes all challenge_pool documents
✅ SAFE: challenge_pool is isolated, no foreign key constraints

This script deletes all 2,363 documents from challenge_pool collection.
The system will regenerate challenges automatically.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

async def delete_challenge_pool():
    """Delete all documents from challenge_pool collection"""

    print("=" * 80)
    print("🗑️  PHASE 1 - STEP 2: DELETE CHALLENGE POOL")
    print("=" * 80)
    print(f"\n📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📂 Database: {DATABASE_NAME}\n")

    # Connect
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    db = client[DATABASE_NAME]

    try:
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        challenge_pool = db.challenge_pool

        # Count before deletion
        count_before = await challenge_pool.count_documents({})
        print(f"📊 Current challenge_pool documents: {count_before}\n")

        if count_before == 0:
            print("ℹ️  Collection is already empty. Nothing to delete.")
            return

        print("⚠️  WARNING: This will DELETE all challenge_pool documents!")
        print("   - Users will get fresh challenges automatically")
        print("   - Completed challenge stats will remain (in users collection)")
        print("   - This operation is REVERSIBLE from backup\n")

        # SAFETY: Optional cleanup of user stats
        print("🔧 Optional: Clean up stale challenge IDs in user stats?")
        print("   This resets 'completedToday' arrays (cosmetic fix)")
        cleanup_stats = input("   Clean up user stats? (yes/no): ")

        if cleanup_stats.lower() == 'yes':
            print("\n🔄 Cleaning up user challengeStats.completedToday...")
            users_collection = db.users
            result = await users_collection.update_many(
                {"challengeStats.completedToday": {"$exists": True}},
                {"$set": {"challengeStats.completedToday": []}}
            )
            print(f"   ✅ Cleaned {result.modified_count} user records")

        # Final confirmation
        print("\n" + "=" * 80)
        print("⚠️  FINAL CONFIRMATION REQUIRED")
        print("=" * 80)
        confirm = input(f"\nType 'DELETE {count_before}' to confirm deletion: ")

        if confirm == f"DELETE {count_before}":
            print("\n🗑️  Deleting challenge_pool...")

            # Perform deletion
            result = await challenge_pool.delete_many({})

            print(f"   ✅ Deleted {result.deleted_count} documents")

            # Verify deletion
            count_after = await challenge_pool.count_documents({})
            print(f"   📊 Remaining documents: {count_after}")

            if count_after == 0:
                print("\n" + "=" * 80)
                print("✅ DELETION COMPLETE!")
                print("=" * 80)
                print(f"\n📊 Summary:")
                print(f"   - Deleted: {result.deleted_count} documents")
                print(f"   - Remaining: {count_after} documents")
                print(f"\n💡 Next steps:")
                print(f"   - System will regenerate challenges automatically")
                print(f"   - New users: Get reference challenges (instant)")
                print(f"   - Active users: Get personalized challenges (30s)")
                print(f"\n✅ App continues working normally!\n")
            else:
                print(f"\n⚠️  WARNING: {count_after} documents remain. Deletion may have failed.")

        else:
            print("\n❌ Deletion cancelled. Confirmation did not match.")

    except Exception as e:
        print(f"\n❌ Error during deletion: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("⚠️  DESTRUCTIVE OPERATION - READ CAREFULLY")
    print("=" * 80)
    print("\nThis script will DELETE all challenge_pool documents.")
    print("\n✅ Safety checks:")
    print("   1. challenge_pool is isolated (no foreign keys)")
    print("   2. You have backups (created in Step 1)")
    print("   3. Operation is reversible (restore from backup)")
    print("   4. App continues working (regenerates challenges)")
    print("\n⚠️  Impact:")
    print("   - Users will have empty challenge pools temporarily")
    print("   - System regenerates challenges in 30 seconds")
    print("   - No data loss (learning plans, sessions, flashcards safe)")
    print("\n")

    confirm = input("Have you created backups in Step 1? (yes/no): ")
    if confirm.lower() != 'yes':
        print("\n❌ Please run Step 1 (backup) first!")
        print("   Run: python 1_backup_collections.py\n")
        exit(1)

    asyncio.run(delete_challenge_pool())
