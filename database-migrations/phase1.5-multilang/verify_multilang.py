"""
Verification Script - Multi-Language Reference Challenges
==========================================================
Verifies that all languages have been generated correctly
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

EXPECTED_LANGUAGES = {
    "english": {"native": "English", "min": 580, "max": 650},
    "dutch": {"native": "Nederlands", "min": 580, "max": 650},
    "spanish": {"native": "Español", "min": 580, "max": 650},
    "german": {"native": "Deutsch", "min": 580, "max": 650},
    "french": {"native": "Français", "min": 580, "max": 650},
    "portuguese": {"native": "Português", "min": 580, "max": 650}
}

CHALLENGE_TYPES = [
    "error_spotting",
    "swipe_fix",
    "micro_quiz",
    "smart_flashcard",
    "native_check",
    "brain_tickler"
]

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


async def verify_challenges():
    """Verify all multi-language challenges"""

    print("=" * 80)
    print("🔍 MULTI-LANGUAGE REFERENCE CHALLENGE VERIFICATION")
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

        reference_challenges = db.reference_challenges

        all_checks_passed = True

        # Check 1: Overall counts
        print("🔍 Check 1: Language Coverage")
        print("-" * 80)

        total_count = await reference_challenges.count_documents({})
        print(f"Total reference challenges: {total_count}")

        # Get language distribution
        pipeline = [
            {"$group": {"_id": "$language", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        lang_counts = await reference_challenges.aggregate(pipeline).to_list(length=100)

        print(f"\nLanguage distribution:")
        for item in lang_counts:
            lang = item['_id']
            count = item['count']
            expected = EXPECTED_LANGUAGES.get(lang, {})
            native = expected.get("native", "Unknown")
            min_expected = expected.get("min", 0)
            max_expected = expected.get("max", 999999)

            if min_expected <= count <= max_expected:
                status = "✅"
            else:
                status = "❌"
                all_checks_passed = False

            print(f"  {status} {lang:12s} ({native:15s}): {count:4d} challenges (expected {min_expected}-{max_expected})")

        # Check for missing languages
        found_languages = {item['_id'] for item in lang_counts}
        missing_languages = set(EXPECTED_LANGUAGES.keys()) - found_languages

        if missing_languages:
            print(f"\n❌ Missing languages: {', '.join(missing_languages)}")
            all_checks_passed = False
        else:
            print(f"\n✅ All 6 languages present")

        # Check 2: Challenge type coverage
        print(f"\n🔍 Check 2: Challenge Type Coverage Per Language")
        print("-" * 80)

        for lang_code, lang_info in EXPECTED_LANGUAGES.items():
            lang_native = lang_info["native"]
            print(f"\n  {lang_native} ({lang_code}):")

            # Get type distribution for this language
            pipeline = [
                {"$match": {"language": lang_code}},
                {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            type_counts = await reference_challenges.aggregate(pipeline).to_list(length=100)

            types_found = {item['_id'] for item in type_counts}
            missing_types = set(CHALLENGE_TYPES) - types_found

            for item in type_counts:
                ctype = item['_id']
                count = item['count']
                # Expect ~100 per type (6 levels × 17 = 102)
                if 80 <= count <= 120:
                    status = "✅"
                else:
                    status = "⚠️"

                print(f"    {status} {ctype:20s}: {count:3d} challenges")

            if missing_types:
                print(f"    ❌ Missing types: {', '.join(missing_types)}")
                all_checks_passed = False

        # Check 3: CEFR level coverage
        print(f"\n🔍 Check 3: CEFR Level Coverage Per Language")
        print("-" * 80)

        for lang_code, lang_info in EXPECTED_LANGUAGES.items():
            lang_native = lang_info["native"]

            # Get level distribution for this language
            pipeline = [
                {"$match": {"language": lang_code}},
                {"$group": {"_id": "$cefr_level", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            level_counts = await reference_challenges.aggregate(pipeline).to_list(length=100)

            levels_found = {item['_id'] for item in level_counts}
            missing_levels = set(CEFR_LEVELS) - levels_found

            if missing_levels:
                print(f"  ❌ {lang_native}: Missing levels {', '.join(missing_levels)}")
                all_checks_passed = False
            else:
                level_str = ", ".join([f"{item['_id']}:{item['count']}" for item in level_counts])
                print(f"  ✅ {lang_native:15s}: {level_str}")

        # Check 4: Sample data quality
        print(f"\n🔍 Check 4: Sample Data Quality")
        print("-" * 80)

        for lang_code in ["dutch", "spanish", "german"]:
            sample = await reference_challenges.find_one({"language": lang_code})

            if sample:
                lang_native = EXPECTED_LANGUAGES[lang_code]["native"]
                challenge_data = sample.get("challenge_data", {})

                print(f"\n  {lang_native} ({lang_code}) sample:")
                print(f"    Type: {challenge_data.get('type', 'N/A')}")
                print(f"    Level: {challenge_data.get('cefrLevel', 'N/A')}")
                print(f"    Has ID: {'✅' if challenge_data.get('id') else '❌'}")
                print(f"    Has content: {'✅' if len(str(challenge_data)) > 100 else '❌'}")

                # Check if content is in target language (basic check)
                content_str = str(challenge_data)
                if len(content_str) > 200:
                    print(f"    Content length: ✅ {len(content_str)} chars")
                else:
                    print(f"    Content length: ⚠️  {len(content_str)} chars (seems short)")

        # Check 5: Index verification
        print(f"\n🔍 Check 5: Database Indexes")
        print("-" * 80)

        indexes = await reference_challenges.list_indexes().to_list(length=None)

        language_index_found = False
        for index in indexes:
            keys = index.get('key', {})
            if 'language' in keys:
                print(f"  ✅ Found language index: {keys}")
                language_index_found = True

        if not language_index_found:
            print(f"  ⚠️  No language index found (may affect performance)")

        # Final summary
        print("\n" + "=" * 80)
        if all_checks_passed:
            print("✅ ALL VERIFICATION CHECKS PASSED!")
        else:
            print("❌ SOME CHECKS FAILED - REVIEW ABOVE")
        print("=" * 80)

        print(f"\n📊 Summary:")
        print(f"   Total challenges: {total_count}")
        print(f"   Languages: {len(found_languages)}/6")
        print(f"   Expected total: ~3,660 (600 English + 3,060 new)")

        if all_checks_passed:
            print(f"\n🎉 Multi-language reference challenges verified!")
            print(f"✅ Ready to proceed to Phase 2 (CrewAI)\n")
        else:
            print(f"\n⚠️  Some issues found. Review output above.\n")

    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🔍 MULTI-LANGUAGE VERIFICATION")
    print("=" * 80)
    print("\nThis script verifies all 6 languages have reference challenges.")
    print("It performs read-only checks (completely safe).\n")

    asyncio.run(verify_challenges())
