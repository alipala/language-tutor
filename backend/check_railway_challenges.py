"""
Check Railway Database for Reference Challenges
Quick verification script to see what's in the reference_challenges collection
"""

import asyncio
import os
from database import database


async def check_reference_challenges():
    """Check reference challenges in the database"""
    try:
        print("\n" + "="*70)
        print("REFERENCE CHALLENGES VERIFICATION")
        print("="*70 + "\n")

        # Check which database we're connected to
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        if "localhost" in mongo_url:
            print("⚠️  Connected to LOCALHOST database")
        else:
            print("✅ Connected to RAILWAY database")

        print(f"Database name: {os.getenv('DATABASE_NAME', 'language_tutor')}\n")

        reference_collection = database.reference_challenges

        # Total count
        total = await reference_collection.count_documents({})
        print(f"📊 Total reference challenges: {total}\n")

        if total == 0:
            print("❌ NO REFERENCE CHALLENGES FOUND!")
            print("\nYou need to seed the database. Run:")
            print("  python seed_reference_challenges.py all 50")
            print("\n⚠️  This will take ~2.5 hours for all levels")
            print("OR seed just B1 level (most common):")
            print("  python seed_reference_challenges.py level B1 50")
            return

        # Breakdown by language
        print("Breakdown by language:")
        languages = ["english", "spanish", "dutch", "german", "french", "portuguese"]

        for lang in languages:
            count = await reference_collection.count_documents({"language": lang})
            if count > 0:
                print(f"  {lang}: {count} challenges")

        print()

        # Breakdown by CEFR level
        print("Breakdown by CEFR level:")
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

        for level in levels:
            count = await reference_collection.count_documents({"cefr_level": level})
            status = "✅" if count >= 300 else "⚠️ " if count > 0 else "❌"
            print(f"  {status} {level}: {count} challenges")

        print()

        # Breakdown by challenge type for English B1 (most common)
        print("Breakdown for English B1 (most common):")
        challenge_types = [
            "error_spotting", "swipe_fix", "micro_quiz",
            "smart_flashcard", "native_check", "brain_tickler"
        ]

        for ctype in challenge_types:
            count = await reference_collection.count_documents({
                "language": "english",
                "cefr_level": "B1",
                "challenge_type": ctype
            })
            status = "✅" if count >= 50 else "⚠️ " if count > 0 else "❌"
            print(f"  {status} {ctype}: {count} challenges")

        print("\n" + "="*70)

        if total < 1800:  # 300 per level * 6 levels
            print("\n⚠️  WARNING: Not enough reference challenges!")
            print("Recommended: 300 per level (50 per type)")
            print("You have:", total, "challenges")
            print("\nTo seed more challenges, run:")
            print("  python seed_reference_challenges.py all 50")
        else:
            print("\n✅ Reference challenges look good!")

    except Exception as e:
        print(f"❌ Error checking reference challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def main():
    await check_reference_challenges()


if __name__ == "__main__":
    asyncio.run(main())
