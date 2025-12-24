"""
Delete All Challenges Script
=============================
Safely delete all challenges from reference_challenges and challenge_pool collections.

USAGE:
    python delete_all_challenges.py --confirm

    Add --dry-run to see what would be deleted without actually deleting
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment variables - try multiple locations
load_dotenv()  # scripts/.env
backend_env = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env, override=False)
root_env = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(root_env):
    load_dotenv(root_env, override=False)

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

if not MONGODB_URL:
    print("❌ ERROR: MONGODB_URL not found. Please set it in .env file or as environment variable.")
    sys.exit(1)


async def get_collection_stats(db, collection_name: str):
    """Get statistics for a collection"""
    collection = db[collection_name]

    total = await collection.count_documents({})

    # Count by language
    by_language = await collection.aggregate([
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(length=100)

    # Count by level
    by_level = await collection.aggregate([
        {"$group": {"_id": "$cefr_level", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(length=100)

    # Count by type
    by_type = await collection.aggregate([
        {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(length=100)

    return {
        "total": total,
        "by_language": by_language,
        "by_level": by_level,
        "by_type": by_type
    }


async def print_stats(stats, collection_name):
    """Print collection statistics"""
    print(f"\n📊 {collection_name} Statistics:")
    print(f"   Total: {stats['total']:,} challenges")

    if stats['by_language']:
        print(f"\n   By Language:")
        for item in stats['by_language']:
            lang = item['_id'] or 'MISSING'
            print(f"     {lang}: {item['count']:,}")

    if stats['by_level']:
        print(f"\n   By CEFR Level:")
        for item in stats['by_level']:
            level = item['_id'] or 'MISSING'
            print(f"     {level}: {item['count']:,}")

    if stats['by_type']:
        print(f"\n   By Type:")
        for item in stats['by_type']:
            ctype = item['_id'] or 'MISSING'
            print(f"     {ctype}: {item['count']:,}")


async def delete_collection(db, collection_name: str, dry_run: bool = False):
    """Delete all documents from a collection"""
    collection = db[collection_name]

    if dry_run:
        count = await collection.count_documents({})
        print(f"   [DRY RUN] Would delete {count:,} documents from {collection_name}")
        return count
    else:
        result = await collection.delete_many({})
        print(f"   ✅ Deleted {result.deleted_count:,} documents from {collection_name}")
        return result.deleted_count


async def main():
    parser = argparse.ArgumentParser(description='Delete all challenges from database')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm deletion (required to actually delete)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    parser.add_argument('--collection', choices=['reference_challenges', 'challenge_pool', 'both'],
                       default='both', help='Which collection(s) to delete from')

    args = parser.parse_args()

    # Require --confirm unless it's a dry run
    if not args.confirm and not args.dry_run:
        print("❌ ERROR: Must specify --confirm to delete challenges")
        print("   Use --dry-run to see what would be deleted")
        print("\nUsage:")
        print("  python delete_all_challenges.py --dry-run")
        print("  python delete_all_challenges.py --confirm")
        print("  python delete_all_challenges.py --confirm --collection reference_challenges")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"🗑️  DELETE ALL CHALLENGES")
    print(f"{'='*70}")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else '⚠️  LIVE DELETION'}")
    print(f"Target: {args.collection}")
    print(f"{'='*70}\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)

    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        db = client[DATABASE_NAME]

        collections_to_process = []
        if args.collection in ['reference_challenges', 'both']:
            collections_to_process.append('reference_challenges')
        if args.collection in ['challenge_pool', 'both']:
            collections_to_process.append('challenge_pool')

        # Get and display current stats
        print("📊 CURRENT STATE:")
        print("="*70)

        all_stats = {}
        for coll_name in collections_to_process:
            stats = await get_collection_stats(db, coll_name)
            all_stats[coll_name] = stats
            await print_stats(stats, coll_name)

        print(f"\n{'='*70}")

        total_to_delete = sum(s['total'] for s in all_stats.values())

        if total_to_delete == 0:
            print("\n✅ Collections are already empty. Nothing to delete.")
            return

        # Confirm deletion
        if not args.dry_run:
            print(f"\n⚠️  WARNING: About to delete {total_to_delete:,} challenges!")
            print("   This action CANNOT be undone.")

            response = input("\n   Type 'DELETE' to confirm: ")

            if response != 'DELETE':
                print("\n❌ Deletion cancelled.")
                return

        # Perform deletion
        print(f"\n{'='*70}")
        print(f"🗑️  {'SIMULATING' if args.dry_run else 'EXECUTING'} DELETION:")
        print(f"{'='*70}\n")

        total_deleted = 0
        for coll_name in collections_to_process:
            deleted = await delete_collection(db, coll_name, dry_run=args.dry_run)
            total_deleted += deleted

        # Verify deletion
        if not args.dry_run:
            print(f"\n{'='*70}")
            print(f"✅ VERIFICATION:")
            print(f"{'='*70}\n")

            for coll_name in collections_to_process:
                remaining = await db[coll_name].count_documents({})
                if remaining == 0:
                    print(f"   ✅ {coll_name}: Empty (0 documents)")
                else:
                    print(f"   ⚠️  {coll_name}: {remaining} documents remaining")

        print(f"\n{'='*70}")
        print(f"{'✅ DRY RUN COMPLETE' if args.dry_run else '✅ DELETION COMPLETE'}")
        print(f"{'='*70}")
        print(f"Total {'would be deleted' if args.dry_run else 'deleted'}: {total_deleted:,} challenges")

        if args.dry_run:
            print("\n💡 To actually delete, run with --confirm flag")
        else:
            print("\n✅ Database is ready for new challenge generation")

        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

    finally:
        client.close()
        print("🔌 MongoDB connection closed\n")


if __name__ == "__main__":
    asyncio.run(main())
