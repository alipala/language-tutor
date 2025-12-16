"""
MongoDB Database Explorer
Connect to Railway MongoDB and analyze collections
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def explore_database():
    """Explore MongoDB database structure and data"""

    try:
        print("=" * 80)
        print("🔍 MONGODB DATABASE EXPLORATION")
        print("=" * 80)
        print(f"\n📡 Connecting to: {MONGODB_URL.split('@')[1].split('/')[0]}")
        print(f"📂 Database: {DATABASE_NAME}\n")

        # Connect
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        db = client[DATABASE_NAME]

        # Test connection
        await client.admin.command('ping')
        print("✅ Connected successfully!\n")

        # List all collections
        collections = await db.list_collection_names()
        print(f"📚 Found {len(collections)} collections:")
        print("-" * 80)
        for i, coll_name in enumerate(sorted(collections), 1):
            count = await db[coll_name].count_documents({})
            print(f"  {i:2d}. {coll_name:40s} ({count:,} documents)")

        print("\n" + "=" * 80)
        print("🔬 DETAILED COLLECTION ANALYSIS")
        print("=" * 80)

        # Analyze key collections
        collections_to_analyze = [
            "learning_plans",
            "challenge_pool",
            "reference_challenges",
            "challenges",
            "users",
            "conversation_sessions",
            "flashcards",
            "daily_challenges_cache"
        ]

        for coll_name in collections_to_analyze:
            if coll_name not in collections:
                print(f"\n❌ Collection '{coll_name}' not found")
                continue

            print(f"\n\n{'=' * 80}")
            print(f"📊 COLLECTION: {coll_name.upper()}")
            print("=" * 80)

            collection = db[coll_name]
            count = await collection.count_documents({})

            print(f"📈 Total Documents: {count:,}")

            if count == 0:
                print("   (Empty collection)")
                continue

            # Get sample document
            sample = await collection.find_one()

            if sample:
                print("\n🔑 Document Structure (sample):")
                print("-" * 80)

                # Remove _id for cleaner output
                if "_id" in sample:
                    sample["_id"] = str(sample["_id"])

                # Pretty print with truncation
                def truncate_value(value, max_len=100):
                    """Truncate long values for readability"""
                    if isinstance(value, str) and len(value) > max_len:
                        return value[:max_len] + "..."
                    elif isinstance(value, list) and len(value) > 3:
                        return value[:3] + [f"... ({len(value) - 3} more items)"]
                    elif isinstance(value, dict):
                        return {k: truncate_value(v, 50) for k, v in list(value.items())[:5]}
                    return value

                for key, value in sample.items():
                    truncated = truncate_value(value)
                    if isinstance(truncated, (dict, list)):
                        print(f"  • {key}: {json.dumps(truncated, indent=4, default=str)[:200]}")
                    else:
                        print(f"  • {key}: {truncated}")

            # Special analysis for specific collections
            if coll_name == "learning_plans":
                print("\n📋 Learning Plans Analysis:")
                print("-" * 80)

                # Check for language field
                plans_with_language = await collection.count_documents({"language": {"$exists": True}})
                plans_with_target_language = await collection.count_documents({"target_language": {"$exists": True}})

                print(f"  • Plans with 'language' field: {plans_with_language}")
                print(f"  • Plans with 'target_language' field: {plans_with_target_language}")

                # Get unique languages
                pipeline = [
                    {"$group": {"_id": "$language", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                languages = await collection.aggregate(pipeline).to_list(length=100)

                if languages:
                    print(f"\n  Languages in learning plans:")
                    for lang in languages:
                        print(f"    - {lang['_id'] or 'null/missing'}: {lang['count']} plans")

                # Get unique proficiency levels
                pipeline = [
                    {"$group": {"_id": "$proficiency_level", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                levels = await collection.aggregate(pipeline).to_list(length=100)

                if levels:
                    print(f"\n  Proficiency levels:")
                    for level in levels:
                        print(f"    - {level['_id'] or 'null/missing'}: {level['count']} plans")

            elif coll_name == "challenge_pool":
                print("\n🎯 Challenge Pool Analysis:")
                print("-" * 80)

                # Check for language field
                pool_with_language = await collection.count_documents({"language": {"$exists": True}})
                pool_with_cefr = await collection.count_documents({"cefr_level": {"$exists": True}})

                print(f"  • Pool items with 'language' field: {pool_with_language}")
                print(f"  • Pool items with 'cefr_level' field: {pool_with_cefr}")

                # Challenge types
                pipeline = [
                    {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                types = await collection.aggregate(pipeline).to_list(length=100)

                if types:
                    print(f"\n  Challenge types distribution:")
                    for type_info in types:
                        print(f"    - {type_info['_id']}: {type_info['count']}")

                # Status distribution
                pipeline = [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                statuses = await collection.aggregate(pipeline).to_list(length=100)

                if statuses:
                    print(f"\n  Status distribution:")
                    for status in statuses:
                        print(f"    - {status['_id']}: {status['count']}")

                # Users with pools
                pipeline = [
                    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 5}
                ]
                top_users = await collection.aggregate(pipeline).to_list(length=5)

                if top_users:
                    print(f"\n  Top users with most challenges:")
                    for user in top_users:
                        print(f"    - User {user['_id'][:8]}...: {user['count']} challenges")

            elif coll_name == "reference_challenges":
                print("\n📚 Reference Challenges Analysis:")
                print("-" * 80)

                # Check for language field
                ref_with_language = await collection.count_documents({"language": {"$exists": True}})

                print(f"  • Reference challenges with 'language' field: {ref_with_language}")

                # Challenge types
                pipeline = [
                    {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                types = await collection.aggregate(pipeline).to_list(length=100)

                if types:
                    print(f"\n  Challenge types:")
                    for type_info in types:
                        print(f"    - {type_info['_id']}: {type_info['count']}")

            elif coll_name == "users":
                print("\n👥 Users Analysis:")
                print("-" * 80)

                # Check for language preferences
                users_with_pref_lang = await collection.count_documents({"preferred_language": {"$exists": True}})
                users_with_pref_level = await collection.count_documents({"preferred_level": {"$exists": True}})

                print(f"  • Users with 'preferred_language': {users_with_pref_lang}")
                print(f"  • Users with 'preferred_level': {users_with_pref_level}")

                # Get unique preferred languages
                pipeline = [
                    {"$group": {"_id": "$preferred_language", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                langs = await collection.aggregate(pipeline).to_list(length=100)

                if langs:
                    print(f"\n  Preferred languages:")
                    for lang in langs[:10]:
                        print(f"    - {lang['_id'] or 'null/missing'}: {lang['count']} users")

            elif coll_name == "conversation_sessions":
                print("\n💬 Conversation Sessions Analysis:")
                print("-" * 80)

                # Check language field
                sessions_with_lang = await collection.count_documents({"language": {"$exists": True}})
                sessions_with_target_lang = await collection.count_documents({"target_language": {"$exists": True}})

                print(f"  • Sessions with 'language' field: {sessions_with_lang}")
                print(f"  • Sessions with 'target_language' field: {sessions_with_target_lang}")

                # Recent sessions (last 30 days)
                from datetime import timedelta
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent = await collection.count_documents({"created_at": {"$gte": thirty_days_ago}})

                print(f"  • Recent sessions (last 30 days): {recent}")

        print("\n\n" + "=" * 80)
        print("✅ DATABASE EXPLORATION COMPLETE")
        print("=" * 80)

        client.close()

    except Exception as e:
        print(f"\n❌ Error exploring database: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(explore_database())
