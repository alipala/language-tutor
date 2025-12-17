"""
MongoDB Database Explorer (Synchronous Version)
Connect to Railway MongoDB and analyze collections
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import json

# MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

def explore_database():
    """Explore MongoDB database structure and data"""

    try:
        print("=" * 80)
        print("🔍 MONGODB DATABASE EXPLORATION")
        print("=" * 80)
        print(f"\n📡 Connecting to: {MONGODB_URL.split('@')[1].split('/')[0]}")
        print(f"📂 Database: {DATABASE_NAME}\n")

        # Connect
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        db = client[DATABASE_NAME]

        # Test connection
        client.admin.command('ping')
        print("✅ Connected successfully!\n")

        # List all collections
        collections = db.list_collection_names()
        print(f"📚 Found {len(collections)} collections:")
        print("-" * 80)
        for i, coll_name in enumerate(sorted(collections), 1):
            count = db[coll_name].count_documents({})
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
            count = collection.count_documents({})

            print(f"📈 Total Documents: {count:,}")

            if count == 0:
                print("   (Empty collection)")
                continue

            # Get sample document
            sample = collection.find_one()

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
                        return {k: truncate_value(v, 50) for k, v in list(value.items())[:10]}
                    return value

                for key, value in sample.items():
                    truncated = truncate_value(value)
                    if isinstance(truncated, (dict, list)):
                        print(f"  • {key}: {json.dumps(truncated, indent=4, default=str)[:300]}")
                    else:
                        print(f"  • {key}: {truncated}")

            # Special analysis for specific collections
            if coll_name == "learning_plans":
                print("\n📋 Learning Plans Analysis:")
                print("-" * 80)

                # Check for language field
                plans_with_language = collection.count_documents({"language": {"$exists": True}})
                plans_with_target_language = collection.count_documents({"target_language": {"$exists": True}})

                print(f"  • Plans with 'language' field: {plans_with_language}")
                print(f"  • Plans with 'target_language' field: {plans_with_target_language}")

                # Get unique languages
                pipeline = [
                    {"$group": {"_id": "$language", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                languages = list(collection.aggregate(pipeline))

                if languages:
                    print(f"\n  Languages in learning plans:")
                    for lang in languages:
                        print(f"    - {lang['_id'] or 'null/missing'}: {lang['count']} plans")

                # Get unique proficiency levels
                pipeline = [
                    {"$group": {"_id": "$proficiency_level", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                levels = list(collection.aggregate(pipeline))

                if levels:
                    print(f"\n  Proficiency levels:")
                    for level in levels:
                        print(f"    - {level['_id'] or 'null/missing'}: {level['count']} plans")

                # Sample a few plans with their fields
                print(f"\n  Sample learning plan fields (first 3):")
                sample_plans = collection.find().limit(3)
                for i, plan in enumerate(sample_plans, 1):
                    print(f"\n    Plan {i}:")
                    print(f"      - language: {plan.get('language', 'NOT SET')}")
                    print(f"      - proficiency_level: {plan.get('proficiency_level', 'NOT SET')}")
                    print(f"      - user_id: {str(plan.get('user_id', 'NOT SET'))[:20]}...")
                    print(f"      - completed_sessions: {plan.get('completed_sessions', 0)}")
                    print(f"      - total_sessions: {plan.get('total_sessions', 0)}")

            elif coll_name == "challenge_pool":
                print("\n🎯 Challenge Pool Analysis:")
                print("-" * 80)

                # Check for language field
                pool_with_language = collection.count_documents({"language": {"$exists": True}})
                pool_with_cefr = collection.count_documents({"cefr_level": {"$exists": True}})

                print(f"  • Pool items with 'language' field: {pool_with_language}")
                print(f"  • Pool items with 'cefr_level' field: {pool_with_cefr}")

                # Challenge types
                pipeline = [
                    {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                types = list(collection.aggregate(pipeline))

                if types:
                    print(f"\n  Challenge types distribution:")
                    for type_info in types:
                        print(f"    - {type_info['_id']}: {type_info['count']}")

                # Status distribution
                pipeline = [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                statuses = list(collection.aggregate(pipeline))

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
                top_users = list(collection.aggregate(pipeline))

                if top_users:
                    print(f"\n  Top users with most challenges:")
                    for user in top_users:
                        user_id = str(user['_id'])[:20] if user['_id'] else 'null'
                        print(f"    - User {user_id}...: {user['count']} challenges")

                # Sample a pool item
                print(f"\n  Sample challenge pool item:")
                sample_pool = collection.find_one()
                if sample_pool:
                    print(f"    - user_id: {str(sample_pool.get('user_id', 'NOT SET'))[:20]}...")
                    print(f"    - cefr_level: {sample_pool.get('cefr_level', 'NOT SET')}")
                    print(f"    - language: {sample_pool.get('language', 'NOT SET')}")
                    print(f"    - challenge_type: {sample_pool.get('challenge_type', 'NOT SET')}")
                    print(f"    - status: {sample_pool.get('status', 'NOT SET')}")

            elif coll_name == "reference_challenges":
                print("\n📚 Reference Challenges Analysis:")
                print("-" * 80)

                # Check for language field
                ref_with_language = collection.count_documents({"language": {"$exists": True}})

                print(f"  • Reference challenges with 'language' field: {ref_with_language}")

                # Challenge types
                pipeline = [
                    {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                types = list(collection.aggregate(pipeline))

                if types:
                    print(f"\n  Challenge types:")
                    for type_info in types:
                        print(f"    - {type_info['_id']}: {type_info['count']}")

                # CEFR levels
                pipeline = [
                    {"$group": {"_id": "$cefr_level", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                levels = list(collection.aggregate(pipeline))

                if levels:
                    print(f"\n  CEFR levels:")
                    for level in levels:
                        print(f"    - {level['_id']}: {level['count']}")

                # Sample reference challenge
                print(f"\n  Sample reference challenge:")
                sample_ref = collection.find_one()
                if sample_ref:
                    print(f"    - cefr_level: {sample_ref.get('cefr_level', 'NOT SET')}")
                    print(f"    - language: {sample_ref.get('language', 'NOT SET')}")
                    print(f"    - challenge_type: {sample_ref.get('challenge_type', 'NOT SET')}")

            elif coll_name == "users":
                print("\n👥 Users Analysis:")
                print("-" * 80)

                # Check for language preferences
                users_with_pref_lang = collection.count_documents({"preferred_language": {"$exists": True}})
                users_with_pref_level = collection.count_documents({"preferred_level": {"$exists": True}})

                print(f"  • Users with 'preferred_language': {users_with_pref_lang}")
                print(f"  • Users with 'preferred_level': {users_with_pref_level}")

                # Get unique preferred languages
                pipeline = [
                    {"$group": {"_id": "$preferred_language", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                langs = list(collection.aggregate(pipeline))

                if langs:
                    print(f"\n  Preferred languages:")
                    for lang in langs[:10]:
                        print(f"    - {lang['_id'] or 'null/missing'}: {lang['count']} users")

                # Preferred levels
                pipeline = [
                    {"$group": {"_id": "$preferred_level", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                levels = list(collection.aggregate(pipeline))

                if levels:
                    print(f"\n  Preferred levels:")
                    for level in levels[:10]:
                        print(f"    - {level['_id'] or 'null/missing'}: {level['count']} users")

            elif coll_name == "conversation_sessions":
                print("\n💬 Conversation Sessions Analysis:")
                print("-" * 80)

                # Check language field
                sessions_with_lang = collection.count_documents({"language": {"$exists": True}})
                sessions_with_target_lang = collection.count_documents({"target_language": {"$exists": True}})

                print(f"  • Sessions with 'language' field: {sessions_with_lang}")
                print(f"  • Sessions with 'target_language' field: {sessions_with_target_lang}")

                # Recent sessions (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent = collection.count_documents({"created_at": {"$gte": thirty_days_ago}})

                print(f"  • Recent sessions (last 30 days): {recent}")

                # Get unique languages
                pipeline = [
                    {"$group": {"_id": "$language", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                langs = list(collection.aggregate(pipeline))

                if langs:
                    print(f"\n  Languages in sessions:")
                    for lang in langs[:10]:
                        print(f"    - {lang['_id'] or 'null/missing'}: {lang['count']} sessions")

        print("\n\n" + "=" * 80)
        print("✅ DATABASE EXPLORATION COMPLETE")
        print("=" * 80)

        client.close()

    except Exception as e:
        print(f"\n❌ Error exploring database: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    explore_database()
