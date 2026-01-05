#!/usr/bin/env python3
"""
Test CrewAI with Ali's User Account
===================================

Tests challenge generation specifically for Ali Pala's account.
This user has real learning data, so challenges should be highly personalized!

Usage:
    python test_crewai_ali.py
"""

import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

from challenge_generator_crew import generate_challenges_with_ai
from database import database

# Load environment
load_dotenv()

# Ali's user info
ALI_USER_ID = "688921c268819565ef1ce3dc"
ALI_EMAIL = "alipala.ist@gmail.com"


async def test_ali_personalized_challenges():
    """Generate personalized challenges for Ali"""

    print("\n" + "="*80)
    print("🧪 CREWAI TEST - ALI PALA'S ACCOUNT")
    print("="*80)
    print(f"User: {ALI_EMAIL}")
    print(f"User ID: {ALI_USER_ID}")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)
    print()

    # Connect to database
    print("📡 Connecting to MongoDB...")
    await database.client.admin.command('ping')
    print("✅ Connected")
    print()

    # Get user details
    from bson import ObjectId
    user = await database.users.find_one({"_id": ObjectId(ALI_USER_ID)})

    if not user:
        print(f"❌ User not found: {ALI_USER_ID}")
        return

    user_level = user.get("preferred_level", "B1")
    print(f"👤 User: {user.get('name', 'Unknown')}")
    print(f"📧 Email: {user.get('email', 'Unknown')}")
    print(f"📚 Level: {user_level}")
    print()

    # Get user's learning plans
    learning_plans = await database.learning_plans.find({
        "user_id": ALI_USER_ID
    }).to_list(length=10)

    print(f"📋 Learning Plans: {len(learning_plans)}")
    for plan in learning_plans:
        language = plan.get("language", "unknown")
        level = plan.get("level", "unknown")
        is_active = plan.get("is_active", False)
        status = "✅ ACTIVE" if is_active else "⏸️  INACTIVE"
        print(f"   - {language} ({level}) {status}")
    print()

    # Choose language and type to test
    test_language = "english"
    test_level = user_level
    test_type = "brain_tickler"
    test_count = 3

    print("="*80)
    print("🎯 GENERATING PERSONALIZED CHALLENGES")
    print("="*80)
    print(f"Language: {test_language}")
    print(f"Level: {test_level}")
    print(f"Type: {test_type}")
    print(f"Count: {test_count}")
    print("="*80)
    print()
    print("⏰ This will take 30-60 seconds (3 agents analyzing your real data)...")
    print()

    # Generate challenges
    start_time = datetime.utcnow()

    challenges = await generate_challenges_with_ai(
        user_id=ALI_USER_ID,
        user_level=test_level,
        language=test_language,
        challenge_type=test_type,
        count=test_count
    )

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Show results
    print()
    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print(f"✅ Generated: {len(challenges)} challenges")
    print(f"⏱️  Duration:  {duration:.2f} seconds")
    print(f"💰 Est. Cost: ~$0.05 (3 agents)")
    print("="*80)
    print()

    if challenges:
        print("📝 SAMPLE CHALLENGE (First)")
        print("="*80)
        print(json.dumps(challenges[0], indent=2, default=str))
        print("="*80)
        print()

        if len(challenges) > 1:
            print("📝 ALL CHALLENGES SUMMARY")
            print("="*80)
            for i, challenge in enumerate(challenges, 1):
                title = challenge.get("title", "Unknown")
                question = challenge.get("question", "Unknown")
                print(f"{i}. {title}")
                print(f"   Q: {question[:80]}...")
                print()
            print("="*80)
            print()

        # Ask if user wants to save
        print("💾 Save to Database?")
        save = input("   Type 'yes' to save these challenges to challenge_pool: ").lower().strip()

        if save == 'yes':
            # Save to challenge_pool
            pool_collection = database.challenge_pool

            pool_docs = []
            for challenge in challenges:
                pool_doc = {
                    "user_id": ALI_USER_ID,
                    "language": test_language,
                    "cefr_level": test_level,
                    "challenge_type": test_type,
                    "challenge_data": challenge,
                    "status": "available",
                    "created_at": datetime.utcnow(),
                    "completed_at": None,
                    "expires_at": None  # No expiry for manual test
                }
                pool_docs.append(pool_doc)

            result = await pool_collection.insert_many(pool_docs)
            print(f"   ✅ Saved {len(result.inserted_ids)} challenges to database")
            print(f"   📍 Collection: challenge_pool")
            print(f"   🔍 User: {ALI_EMAIL}")
        else:
            print("   ⏭️  Skipped saving")

    else:
        print("❌ No challenges generated")

    print()
    print("="*80)
    print("✅ TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_ali_personalized_challenges())
