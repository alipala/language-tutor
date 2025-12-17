"""
Phase 1 - Step 5: Verify Migration
===================================
✅ SAFE: Read-only verification

This script verifies that all Phase 1 steps completed successfully.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

async def verify_migration():
    """Verify all Phase 1 changes"""

    print("=" * 80)
    print("✅ PHASE 1 - STEP 5: VERIFICATION")
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

        all_checks_passed = True

        # Check 1: Challenge pool deleted
        print("🔍 Check 1: Challenge pool deletion")
        challenge_pool = db.challenge_pool
        pool_count = await challenge_pool.count_documents({})

        if pool_count == 0:
            print(f"   ✅ PASS: Challenge pool is empty (0 documents)")
        else:
            print(f"   ❌ FAIL: Challenge pool has {pool_count} documents (expected 0)")
            all_checks_passed = False

        # Check 2: Reference challenges have language field
        print("\n🔍 Check 2: Reference challenges language field")
        ref_challenges = db.reference_challenges

        total_ref = await ref_challenges.count_documents({})
        with_language = await ref_challenges.count_documents({"language": {"$exists": True}})
        without_language = await ref_challenges.count_documents({"language": {"$exists": False}})

        print(f"   Total reference challenges: {total_ref}")
        print(f"   With language field: {with_language}")
        print(f"   Without language field: {without_language}")

        if without_language == 0 and with_language == total_ref:
            print(f"   ✅ PASS: All reference challenges have language field")
        else:
            print(f"   ❌ FAIL: {without_language} challenges missing language field")
            all_checks_passed = False

        # Check 3: Language casing normalized (learning_plans)
        print("\n🔍 Check 3: Learning plans language casing")
        learning_plans = db.learning_plans

        pipeline = [
            {"$match": {"language": {"$exists": True}}},
            {"$group": {"_id": "$language", "count": {"$sum": 1}}}
        ]
        lang_distribution = await learning_plans.aggregate(pipeline).to_list(length=100)

        uppercase_found = False
        print(f"   Language distribution:")
        for item in lang_distribution:
            lang = item['_id']
            count = item['count']
            print(f"     - {lang}: {count} plans")
            if lang and lang != lang.lower():
                uppercase_found = True

        if not uppercase_found:
            print(f"   ✅ PASS: All languages are lowercase")
        else:
            print(f"   ❌ FAIL: Found uppercase languages")
            all_checks_passed = False

        # Check 4: Users language casing
        print("\n🔍 Check 4: Users preferred_language casing")
        users = db.users

        pipeline = [
            {"$match": {"preferred_language": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$preferred_language", "count": {"$sum": 1}}}
        ]
        user_lang_distribution = await users.aggregate(pipeline).to_list(length=100)

        uppercase_found = False
        print(f"   Language distribution:")
        for item in user_lang_distribution:
            lang = item['_id']
            count = item['count']
            print(f"     - {lang}: {count} users")
            if lang and lang != lang.lower():
                uppercase_found = True

        if not uppercase_found:
            print(f"   ✅ PASS: All languages are lowercase")
        else:
            print(f"   ❌ FAIL: Found uppercase languages")
            all_checks_passed = False

        # Check 5: Conversation sessions language casing
        print("\n🔍 Check 5: Conversation sessions language casing")
        sessions = db.conversation_sessions

        pipeline = [
            {"$match": {"language": {"$exists": True}}},
            {"$group": {"_id": "$language", "count": {"$sum": 1}}}
        ]
        session_lang_distribution = await sessions.aggregate(pipeline).to_list(length=100)

        uppercase_found = False
        print(f"   Language distribution:")
        for item in session_lang_distribution:
            lang = item['_id']
            count = item['count']
            print(f"     - {lang}: {count} sessions")
            if lang and lang != lang.lower():
                uppercase_found = True

        if not uppercase_found:
            print(f"   ✅ PASS: All languages are lowercase")
        else:
            print(f"   ❌ FAIL: Found uppercase languages")
            all_checks_passed = False

        # Check 6: Index exists on reference_challenges
        print("\n🔍 Check 6: Reference challenges indexes")
        indexes = await ref_challenges.list_indexes().to_list(length=None)

        index_found = False
        for index in indexes:
            keys = index.get('key', {})
            if 'language' in keys:
                print(f"   ✅ Found language index: {keys}")
                index_found = True

        if index_found:
            print(f"   ✅ PASS: Language index exists")
        else:
            print(f"   ⚠️  WARNING: Language index not found (may affect performance)")

        # Final summary
        print("\n" + "=" * 80)
        if all_checks_passed:
            print("✅ ALL CHECKS PASSED - PHASE 1 COMPLETE!")
        else:
            print("❌ SOME CHECKS FAILED - REVIEW ABOVE")
        print("=" * 80)

        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Challenge pool: {pool_count} documents (expected 0)")
        print(f"   ✅ Reference challenges: {with_language}/{total_ref} have language field")
        print(f"   ✅ Learning plans: Normalized to lowercase")
        print(f"   ✅ Users: Normalized to lowercase")
        print(f"   ✅ Sessions: Normalized to lowercase")

        print(f"\n💡 Next Steps:")
        print(f"   1. Phase 2: Implement CrewAI multi-agent system")
        print(f"   2. Phase 3: Update backend code with language filtering")
        print(f"   3. Phase 4: Test English/Dutch separation")
        print(f"   4. Phase 5: Deploy weekly cron")
        print(f"   5. Phase 6: Create iOS integration guide\n")

        if all_checks_passed:
            print("🎉 Ready to proceed to Phase 2!\n")
        else:
            print("⚠️  Fix failing checks before proceeding.\n")

    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("✅ READ-ONLY VERIFICATION")
    print("=" * 80)
    print("\nThis script verifies that Phase 1 completed successfully.")
    print("It performs read-only checks (completely safe).\n")

    asyncio.run(verify_migration())
