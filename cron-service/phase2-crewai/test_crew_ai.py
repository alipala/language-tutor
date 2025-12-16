#!/usr/bin/env python3
"""
CrewAI Challenge Generation Testing Script
==========================================

Test the CrewAI multi-agent system with a single user before running
the full weekly cron. This helps verify:

1. API keys and configuration are correct
2. CrewAI agents are working properly
3. Challenge generation quality is acceptable
4. Cost estimates are accurate
5. Database integration works correctly

Usage:
    python test_crew_ai.py
    python test_crew_ai.py --user-id <user_id>
    python test_crew_ai.py --language spanish --level B2
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from challenge_crew_ai import (
    ChallengeCrew,
    UsageStatistics,
    OPENAI_API_KEY,
    MONGODB_URL,
    DATABASE_NAME,
    GPT_MODEL,
    LLM_PROVIDER,
    CHALLENGE_TYPES,
    logger
)


async def test_single_user_generation(
    user_id: str = None,
    language: str = "english",
    level: str = "B1",
    challenge_type: str = "error_spotting",
    count: int = 3
):
    """Test challenge generation for a single user

    Args:
        user_id: User ID to test (if None, finds first active user)
        language: Language to test
        level: CEFR level to test
        challenge_type: Challenge type to test
        count: Number of challenges to generate
    """
    print("=" * 80)
    print("🧪 CREWAI CHALLENGE GENERATION - TEST MODE")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"LLM Model: {GPT_MODEL}")
    print(f"LLM Provider: {LLM_PROVIDER}")
    print("=" * 80)
    print()

    # Validate configuration
    if not OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not set!")
        print("Set it in environment: export OPENAI_API_KEY='sk-...'")
        return

    if not MONGODB_URL:
        print("❌ ERROR: MONGODB_URL not set!")
        print("Set it in environment: export MONGODB_URL='mongodb://...'")
        return

    # Connect to MongoDB
    print("📡 Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)

    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        db = client[DATABASE_NAME]
        stats = UsageStatistics()

        # Get or find user
        if user_id:
            user = await db.users.find_one({"_id": user_id})
            if not user:
                print(f"❌ User {user_id} not found!")
                return
        else:
            # Find first active user
            print("🔍 Finding an active user to test with...")
            user = await db.users.find_one({})
            if not user:
                print("❌ No users found in database!")
                return
            user_id = str(user["_id"])

        print(f"👤 Test User: {user_id}")
        print(f"📧 Email: {user.get('email', 'N/A')}")
        print()

        # Check if user has learning plans
        learning_plans = await db.learning_plans.find({
            "user_id": user_id
        }).to_list(length=10)

        if learning_plans:
            print(f"📚 User has {len(learning_plans)} learning plan(s):")
            for i, plan in enumerate(learning_plans, 1):
                active = "✅ ACTIVE" if plan.get("is_active") else "⏸️  INACTIVE"
                print(f"   {i}. {plan.get('language', 'unknown')} - {plan.get('level', 'unknown')} {active}")
            print()

            # Use first active plan if no language specified
            if language == "english" and learning_plans:
                active_plan = next((p for p in learning_plans if p.get("is_active")), learning_plans[0])
                language = active_plan.get("language", "english")
                level = active_plan.get("level", "B1")
                print(f"📌 Using learning plan: {language} - {level}")
                print()

        # Check reference challenges availability
        ref_count = await db.reference_challenges.count_documents({
            "language": language,
            "cefr_level": level,
            "challenge_type": challenge_type
        })

        print(f"📊 Reference Challenges Available:")
        print(f"   Language: {language}")
        print(f"   Level: {level}")
        print(f"   Type: {challenge_type}")
        print(f"   Count: {ref_count}")
        print()

        if ref_count == 0:
            print(f"⚠️  WARNING: No reference challenges found for {language}/{level}/{challenge_type}")
            print(f"   The system may not generate challenges correctly.")
            print()

        # Initialize CrewAI system
        print("🤖 Initializing CrewAI system...")
        crew_system = ChallengeCrew(client, stats)
        print("✅ CrewAI system initialized\n")

        # Test challenge generation
        print("=" * 80)
        print(f"🎯 GENERATING {count} TEST CHALLENGE(S)")
        print("=" * 80)
        print(f"User: {user_id}")
        print(f"Language: {language}")
        print(f"Level: {level}")
        print(f"Type: {challenge_type}")
        print("=" * 80)
        print()

        start_time = datetime.utcnow()

        challenges = await crew_system.generate_challenges_for_user(
            user_id=user_id,
            language=language,
            cefr_level=level,
            challenge_type=challenge_type,
            count=count
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Display results
        print()
        print("=" * 80)
        print("📊 GENERATION RESULTS")
        print("=" * 80)
        print(f"✅ Generated: {len(challenges)} challenge(s)")
        print(f"⏱️  Time: {duration:.2f} seconds")
        print(f"🤖 API Calls: {stats.total_api_calls} (estimated)")
        print(f"🪙 Input Tokens: {stats.total_input_tokens:,}")
        print(f"🪙 Output Tokens: {stats.total_output_tokens:,}")
        print(f"💰 Cost: ${stats.total_cost_usd:.4f}")
        print()

        if challenges:
            # Show first challenge
            print("=" * 80)
            print("📝 SAMPLE CHALLENGE (First Generated)")
            print("=" * 80)
            first_challenge = challenges[0]
            print(f"Language: {first_challenge['language']}")
            print(f"Level: {first_challenge['cefr_level']}")
            print(f"Type: {first_challenge['challenge_type']}")
            print(f"Created: {first_challenge['created_at']}")
            print(f"Expires: {first_challenge['expires_at']}")
            print()
            print("Challenge Data:")
            import json
            print(json.dumps(first_challenge['challenge_data'], indent=2, ensure_ascii=False))
            print("=" * 80)
            print()

            # Ask if we should save to database
            print("💾 Save Challenges to Database?")
            save = input("   Type 'yes' to save these challenges to challenge_pool: ").lower().strip()

            if save == 'yes':
                result = await db.challenge_pool.insert_many(challenges)
                print(f"   ✅ Saved {len(result.inserted_ids)} challenges to database")
            else:
                print(f"   ⏭️  Skipped saving (test only)")

        else:
            print("❌ No challenges generated!")
            print("Check logs above for errors.")

        # Display any errors
        if stats.errors:
            print()
            print("=" * 80)
            print("❌ ERRORS ENCOUNTERED")
            print("=" * 80)
            for error in stats.errors:
                print(f"   - {error['message']}")
            print()

        print()
        print("=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)
        print()
        print("💡 Next Steps:")
        print("   1. Review the generated challenge quality")
        print("   2. Check the cost estimates")
        print("   3. If satisfied, deploy to weekly cron")
        print("   4. Monitor logs in production")
        print()

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()
        print("🔌 MongoDB connection closed")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Test CrewAI challenge generation system"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Specific user ID to test (optional, will find one if not provided)"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="english",
        help="Language to test (default: english)"
    )
    parser.add_argument(
        "--level",
        type=str,
        default="B1",
        help="CEFR level to test (default: B1)"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="error_spotting",
        choices=CHALLENGE_TYPES,
        help="Challenge type to test (default: error_spotting)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of challenges to generate (default: 3)"
    )

    args = parser.parse_args()

    # Run test
    asyncio.run(test_single_user_generation(
        user_id=args.user_id,
        language=args.language,
        level=args.level,
        challenge_type=args.type,
        count=args.count
    ))


if __name__ == "__main__":
    main()
