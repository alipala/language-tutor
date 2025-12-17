"""
ROLLBACK SCRIPT - Phase 1
==========================
⚠️  Use this to restore from backups if needed

This script restores challenge_pool and reference_challenges
from backup files created in Step 1.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
from datetime import datetime
import os
from bson import ObjectId

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

async def restore_from_backup(backup_dir: str):
    """Restore collections from backup directory"""

    print("=" * 80)
    print("🔄 ROLLBACK - RESTORE FROM BACKUP")
    print("=" * 80)
    print(f"\n📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📂 Backup directory: {backup_dir}\n")

    # Check backup directory exists
    if not os.path.exists(backup_dir):
        print(f"❌ Error: Backup directory '{backup_dir}' not found!")
        print(f"\nAvailable backups:")
        backup_dirs = [d for d in os.listdir('.') if d.startswith('backups_')]
        if backup_dirs:
            for d in backup_dirs:
                print(f"   - {d}")
        else:
            print(f"   (No backups found)")
        return

    # Connect
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    db = client[DATABASE_NAME]

    try:
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        # Load metadata
        metadata_file = os.path.join(backup_dir, "backup_metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                print(f"📋 Backup metadata:")
                print(f"   - Created: {metadata['backup_date']}")
                print(f"   - Database: {metadata['database']}")
                for coll_name, info in metadata['collections'].items():
                    print(f"   - {coll_name}: {info['count']} documents")
                print()

        # Restore challenge_pool
        pool_file = os.path.join(backup_dir, "challenge_pool_backup.json")
        if os.path.exists(pool_file):
            print("🔄 Restoring challenge_pool...")

            with open(pool_file, 'r') as f:
                pool_docs = json.load(f)

            # Current count
            challenge_pool = db.challenge_pool
            current_count = await challenge_pool.count_documents({})
            print(f"   Current documents: {current_count}")

            if current_count > 0:
                confirm = input(f"   ⚠️  Delete {current_count} existing documents first? (yes/no): ")
                if confirm.lower() == 'yes':
                    await challenge_pool.delete_many({})
                    print(f"   ✅ Deleted {current_count} documents")
                else:
                    print(f"   ⚠️  Keeping existing documents (may create duplicates)")

            # Convert string IDs back to ObjectId
            for doc in pool_docs:
                if '_id' in doc and isinstance(doc['_id'], str):
                    doc['_id'] = ObjectId(doc['_id'])

            # Insert
            if pool_docs:
                result = await challenge_pool.insert_many(pool_docs)
                print(f"   ✅ Restored {len(result.inserted_ids)} documents")
        else:
            print(f"⚠️  challenge_pool backup not found in {backup_dir}")

        # Restore reference_challenges
        ref_file = os.path.join(backup_dir, "reference_challenges_backup.json")
        if os.path.exists(ref_file):
            print("\n🔄 Restoring reference_challenges...")

            with open(ref_file, 'r') as f:
                ref_docs = json.load(f)

            # Current count
            ref_challenges = db.reference_challenges
            current_count = await ref_challenges.count_documents({})
            print(f"   Current documents: {current_count}")

            if current_count > 0:
                confirm = input(f"   ⚠️  Delete {current_count} existing documents first? (yes/no): ")
                if confirm.lower() == 'yes':
                    await ref_challenges.delete_many({})
                    print(f"   ✅ Deleted {current_count} documents")
                else:
                    print(f"   ⚠️  Keeping existing documents (may create duplicates)")

            # Convert string IDs back to ObjectId
            for doc in ref_docs:
                if '_id' in doc and isinstance(doc['_id'], str):
                    doc['_id'] = ObjectId(doc['_id'])

            # Insert
            if ref_docs:
                result = await ref_challenges.insert_many(ref_docs)
                print(f"   ✅ Restored {len(result.inserted_ids)} documents")
        else:
            print(f"⚠️  reference_challenges backup not found in {backup_dir}")

        print("\n" + "=" * 80)
        print("✅ ROLLBACK COMPLETE!")
        print("=" * 80)
        print(f"\n💡 What was restored:")
        print(f"   - challenge_pool: Restored from backup")
        print(f"   - reference_challenges: Restored from backup")
        print(f"\n⚠️  NOTE:")
        print(f"   - Language casing changes NOT rolled back")
        print(f"   - To rollback casing, restore from backup manually")
        print(f"\n")

    except Exception as e:
        print(f"\n❌ Error during rollback: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🔄 ROLLBACK SCRIPT")
    print("=" * 80)
    print("\nThis script restores collections from backup.")
    print("\n⚠️  WARNING:")
    print("   - This will replace current data with backup data")
    print("   - Make sure you have the correct backup directory")
    print("\n")

    # List available backups
    print("📁 Available backups:")
    backup_dirs = [d for d in os.listdir('.') if d.startswith('backups_')]
    if backup_dirs:
        for i, d in enumerate(backup_dirs, 1):
            print(f"   {i}. {d}")
    else:
        print("   (No backups found)")
        print("\n❌ Please run Step 1 (backup) first!")
        exit(1)

    print()
    backup_dir = input("Enter backup directory name (e.g., backups_20251216_123456): ")

    if not backup_dir:
        print("\n❌ No directory specified.")
        exit(1)

    confirm = input(f"\n⚠️  Restore from '{backup_dir}'? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(restore_from_backup(backup_dir))
    else:
        print("\n❌ Rollback cancelled.")
