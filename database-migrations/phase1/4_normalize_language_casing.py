"""
Phase 1 - Step 4: Normalize Language Casing
============================================
✅ SAFE: Only changes string values to lowercase
✅ REVERSIBLE: Can restore from backup if needed

This script normalizes inconsistent language casing across collections:
- "English" → "english"
- "Dutch" → "dutch"
- "Spanish" → "spanish"

Fixes the issue where "English" != "english" in queries.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

async def normalize_language_casing():
    """Normalize language field to lowercase across all collections"""

    print("=" * 80)
    print("🔧 PHASE 1 - STEP 4: NORMALIZE LANGUAGE CASING")
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

        total_updated = 0

        # Collection 1: learning_plans
        print("🔄 Normalizing learning_plans...")
        learning_plans = db.learning_plans

        # Check current state
        pipeline = [
            {"$match": {"language": {"$exists": True}}},
            {"$group": {"_id": "$language", "count": {"$sum": 1}}}
        ]
        before_plans = await learning_plans.aggregate(pipeline).to_list(length=100)

        print(f"   Before:")
        for item in before_plans:
            print(f"     - {item['_id']}: {item['count']} plans")

        # Normalize
        result = await learning_plans.update_many(
            {"language": {"$exists": True}},
            [{"$set": {"language": {"$toLower": "$language"}}}]
        )
        print(f"   ✅ Updated {result.modified_count} documents")
        total_updated += result.modified_count

        # Check after
        after_plans = await learning_plans.aggregate(pipeline).to_list(length=100)
        print(f"   After:")
        for item in after_plans:
            print(f"     - {item['_id']}: {item['count']} plans")

        # Collection 2: users (preferred_language)
        print("\n🔄 Normalizing users.preferred_language...")
        users = db.users

        # Check current state
        pipeline = [
            {"$match": {"preferred_language": {"$exists": True}}},
            {"$group": {"_id": "$preferred_language", "count": {"$sum": 1}}}
        ]
        before_users = await users.aggregate(pipeline).to_list(length=100)

        print(f"   Before:")
        for item in before_users:
            print(f"     - {item['_id']}: {item['count']} users")

        # Normalize
        result = await users.update_many(
            {"preferred_language": {"$exists": True}},
            [{"$set": {"preferred_language": {"$toLower": "$preferred_language"}}}]
        )
        print(f"   ✅ Updated {result.modified_count} documents")
        total_updated += result.modified_count

        # Check after
        after_users = await users.aggregate(pipeline).to_list(length=100)
        print(f"   After:")
        for item in after_users:
            print(f"     - {item['_id']}: {item['count']} users")

        # Collection 3: conversation_sessions
        print("\n🔄 Normalizing conversation_sessions.language...")
        sessions = db.conversation_sessions

        # Check current state
        pipeline = [
            {"$match": {"language": {"$exists": True}}},
            {"$group": {"_id": "$language", "count": {"$sum": 1}}}
        ]
        before_sessions = await sessions.aggregate(pipeline).to_list(length=100)

        print(f"   Before:")
        for item in before_sessions:
            print(f"     - {item['_id']}: {item['count']} sessions")

        # Normalize
        result = await sessions.update_many(
            {"language": {"$exists": True}},
            [{"$set": {"language": {"$toLower": "$language"}}}]
        )
        print(f"   ✅ Updated {result.modified_count} documents")
        total_updated += result.modified_count

        # Check after
        after_sessions = await sessions.aggregate(pipeline).to_list(length=100)
        print(f"   After:")
        for item in after_sessions:
            print(f"     - {item['_id']}: {item['count']} sessions")

        # Collection 4: reference_challenges (if any have uppercase)
        print("\n🔄 Normalizing reference_challenges.language...")
        ref_challenges = db.reference_challenges

        result = await ref_challenges.update_many(
            {"language": {"$exists": True}},
            [{"$set": {"language": {"$toLower": "$language"}}}]
        )
        print(f"   ✅ Updated {result.modified_count} documents")
        total_updated += result.modified_count

        # Collection 5: flashcards (already lowercase, but check anyway)
        print("\n🔄 Normalizing flashcards.language...")
        flashcards = db.flashcards

        result = await flashcards.update_many(
            {"language": {"$exists": True}},
            [{"$set": {"language": {"$toLower": "$language"}}}]
        )
        print(f"   ✅ Updated {result.modified_count} documents")
        total_updated += result.modified_count

        print("\n" + "=" * 80)
        print("✅ LANGUAGE CASING NORMALIZED!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"   - Total documents updated: {total_updated}")
        print(f"   - Collections affected: 5")
        print(f"     • learning_plans")
        print(f"     • users (preferred_language)")
        print(f"     • conversation_sessions")
        print(f"     • reference_challenges")
        print(f"     • flashcards")
        print(f"\n💡 Result:")
        print(f"   - All languages now lowercase (english, dutch, spanish)")
        print(f"   - Queries will work consistently")
        print(f"   - No more filtering bugs due to casing\n")

    except Exception as e:
        print(f"\n❌ Error during normalization: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("✅ SAFE OPERATION - STRING TRANSFORMATION ONLY")
    print("=" * 80)
    print("\nThis script normalizes language casing to lowercase.")
    print("\n📊 Changes:")
    print("   - 'English' → 'english'")
    print("   - 'Dutch' → 'dutch'")
    print("   - 'Spanish' → 'spanish'")
    print("\n✅ Safety:")
    print("   - Only changes string values")
    print("   - Doesn't affect structure")
    print("   - Reversible from backup")
    print("   - Fixes query filtering bugs")
    print("\n")

    confirm = input("Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(normalize_language_casing())
    else:
        print("\n❌ Operation cancelled.")
