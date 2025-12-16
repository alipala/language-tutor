"""
Phase 1 - Step 1: Backup Collections
=====================================
SAFE: Read-only operation, creates backups

This script backs up challenge_pool and reference_challenges collections
before making any changes. Always run this first!
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
from datetime import datetime
import os

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

async def backup_collections():
    """Backup challenge_pool and reference_challenges collections"""

    print("=" * 80)
    print("🔒 PHASE 1 - STEP 1: BACKUP COLLECTIONS")
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

        # Create backup directory
        backup_dir = f"backups_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        print(f"📁 Created backup directory: {backup_dir}\n")

        # Backup challenge_pool
        print("🔄 Backing up challenge_pool...")
        challenge_pool = db.challenge_pool
        pool_docs = await challenge_pool.find({}).to_list(length=None)

        pool_backup_file = f"{backup_dir}/challenge_pool_backup.json"
        with open(pool_backup_file, 'w') as f:
            # Convert ObjectId to string for JSON serialization
            for doc in pool_docs:
                doc['_id'] = str(doc['_id'])
            json.dump(pool_docs, f, indent=2, default=str)

        print(f"   ✅ Backed up {len(pool_docs)} documents")
        print(f"   📄 File: {pool_backup_file}")

        # Backup reference_challenges
        print("\n🔄 Backing up reference_challenges...")
        reference_challenges = db.reference_challenges
        ref_docs = await reference_challenges.find({}).to_list(length=None)

        ref_backup_file = f"{backup_dir}/reference_challenges_backup.json"
        with open(ref_backup_file, 'w') as f:
            # Convert ObjectId to string for JSON serialization
            for doc in ref_docs:
                doc['_id'] = str(doc['_id'])
            json.dump(ref_docs, f, indent=2, default=str)

        print(f"   ✅ Backed up {len(ref_docs)} documents")
        print(f"   📄 File: {ref_backup_file}")

        # Create metadata file
        metadata = {
            "backup_date": datetime.utcnow().isoformat(),
            "database": DATABASE_NAME,
            "collections": {
                "challenge_pool": {
                    "count": len(pool_docs),
                    "file": pool_backup_file
                },
                "reference_challenges": {
                    "count": len(ref_docs),
                    "file": ref_backup_file
                }
            }
        }

        metadata_file = f"{backup_dir}/backup_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n📋 Metadata saved: {metadata_file}")

        print("\n" + "=" * 80)
        print("✅ BACKUP COMPLETE!")
        print("=" * 80)
        print(f"\n💾 Backup location: {backup_dir}/")
        print(f"📊 Total documents backed up: {len(pool_docs) + len(ref_docs)}")
        print("\n⚠️  IMPORTANT: Keep these backups safe!")
        print("   You can restore from these if needed.\n")

    except Exception as e:
        print(f"\n❌ Error during backup: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n⚠️  This script will backup collections before making changes.")
    print("   This is a READ-ONLY operation - completely safe.\n")

    confirm = input("Continue with backup? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(backup_collections())
    else:
        print("\n❌ Backup cancelled.")
