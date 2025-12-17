"""
Populate challenge pools for existing users with learning plans
Run this once to ensure all existing users have challenges
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.language_tutor

# Import the helper function
import sys
sys.path.append('/home/user/language-tutor/backend')
from challenge_pool_helpers import ensure_pool_has_challenges


async def populate_challenges_for_users():
    """
    Populate challenges for all users with active learning plans
    """
    print("=" * 80)
    print("POPULATING CHALLENGES FOR USERS WITH LEARNING PLANS")
    print("=" * 80)

    # Get all active learning plans
    learning_plans = await db.learning_plans.find({"is_active": True}).to_list(length=None)

    print(f"\n📊 Found {len(learning_plans)} active learning plans")

    populated_count = 0
    error_count = 0

    for plan in learning_plans:
        user_id = plan.get("user_id")
        language = plan.get("language", "english").lower()

        # Get user's preferred level
        user = await db.users.find_one({"_id": user_id})
        if not user:
            print(f"⚠️  User {user_id} not found, skipping...")
            continue

        user_level = user.get("preferred_level", "B1")

        print(f"\n👤 User: {user_id}")
        print(f"   Language: {language}")
        print(f"   Level: {user_level}")

        try:
            # Check if user already has challenges
            pool_collection = db.challenge_pool
            existing_count = await pool_collection.count_documents({
                "user_id": user_id,
                "language": language,
                "cefr_level": user_level,
                "status": "available"
            })

            if existing_count > 0:
                print(f"   ✅ Already has {existing_count} challenges - skipping")
                continue

            # Populate challenges
            print(f"   🔄 Populating challenges...")
            counts = await ensure_pool_has_challenges(
                user_id=user_id,
                user_level=user_level,
                language=language,
                is_new_user=True  # Force copy from reference
            )

            total = counts.get("total", 0)
            print(f"   ✅ Populated {total} challenges!")
            print(f"      - error_spotting: {counts.get('error_spotting', 0)}")
            print(f"      - swipe_fix: {counts.get('swipe_fix', 0)}")
            print(f"      - micro_quiz: {counts.get('micro_quiz', 0)}")
            print(f"      - smart_flashcard: {counts.get('smart_flashcard', 0)}")
            print(f"      - native_check: {counts.get('native_check', 0)}")
            print(f"      - brain_tickler: {counts.get('brain_tickler', 0)}")

            populated_count += 1

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            error_count += 1
            continue

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully populated: {populated_count} users")
    print(f"❌ Errors: {error_count} users")
    print(f"📊 Total learning plans: {len(learning_plans)}")
    print("=" * 80)


async def populate_challenges_for_all_levels():
    """
    Alternative: Populate challenges for all 6 levels for users with learning plans
    This gives users full flexibility to explore any level
    """
    print("=" * 80)
    print("POPULATING CHALLENGES FOR ALL LEVELS (A1-C2)")
    print("=" * 80)

    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    # Get all active learning plans
    learning_plans = await db.learning_plans.find({"is_active": True}).to_list(length=None)

    print(f"\n📊 Found {len(learning_plans)} active learning plans")
    print(f"📊 Will populate {len(levels)} levels per user")

    for plan in learning_plans:
        user_id = plan.get("user_id")
        language = plan.get("language", "english").lower()

        print(f"\n👤 User: {user_id}")
        print(f"   Language: {language}")

        for level in levels:
            try:
                # Check if already exists
                pool_collection = db.challenge_pool
                existing_count = await pool_collection.count_documents({
                    "user_id": user_id,
                    "language": language,
                    "cefr_level": level,
                    "status": "available"
                })

                if existing_count > 0:
                    print(f"   ✅ {level}: Already has {existing_count} challenges")
                    continue

                # Populate
                print(f"   🔄 {level}: Populating...")
                counts = await ensure_pool_has_challenges(
                    user_id=user_id,
                    user_level=level,
                    language=language,
                    is_new_user=True
                )

                total = counts.get("total", 0)
                print(f"   ✅ {level}: Populated {total} challenges")

            except Exception as e:
                print(f"   ❌ {level}: Error - {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Challenge Population Script")
    print("\nChoose an option:")
    print("1. Populate challenges for user's current level only (faster)")
    print("2. Populate challenges for ALL levels A1-C2 (gives full flexibility)")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(populate_challenges_for_users())
    elif choice == "2":
        asyncio.run(populate_challenges_for_all_levels())
    else:
        print("Invalid choice. Exiting.")
