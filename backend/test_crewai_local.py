#!/usr/bin/env python3
"""
Local Test Script for CrewAI Challenge Generation
=================================================

Tests the new CrewAI multi-agent system locally against production MongoDB.

Usage:
    python test_crewai_local.py

This will generate:
    - Language: English
    - Level: A2
    - Type: brain_tickler
    - Count: 3 challenges

You can modify the parameters below to test different configurations.
"""

import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the CrewAI generator
from challenge_generator_crew import generate_challenges_with_ai
from database import database


async def test_crewai_generation():
    """Test CrewAI challenge generation with specific parameters"""

    print("=" * 80)
    print("🧪 CREWAI CHALLENGE GENERATION - LOCAL TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Testing against: PRODUCTION MongoDB")
    print("=" * 80)
    print()

    # Test parameters (as requested)
    test_user_id = None  # Will find a real user
    test_language = "english"
    test_level = "A2"
    test_challenge_type = "brain_tickler"
    test_count = 3

    try:
        # Step 1: Find a real active user
        print("📡 Connecting to MongoDB...")

        # Test connection
        await database.client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        print()

        # Find an active user with English learning plan
        print("👤 Finding an active user with English learning plan...")

        users_collection = database.users
        learning_plans_collection = database.learning_plans

        # Find users with English learning plans
        english_plans = await learning_plans_collection.find({
            "language": test_language,
            "is_active": True
        }).limit(5).to_list(length=5)

        if not english_plans:
            print("⚠️  No active English learning plans found. Trying any English plan...")
            english_plans = await learning_plans_collection.find({
                "language": test_language
            }).limit(5).to_list(length=5)

        if not english_plans:
            print("❌ No English learning plans found in database!")
            print("💡 You can still test with a dummy user_id if you want")
            return

        # Get the user from the first plan
        test_user_id = english_plans[0].get("user_id")

        # Get user details
        from bson import ObjectId
        user = await users_collection.find_one({"_id": ObjectId(test_user_id)})

        if user:
            user_email = user.get("email", "Unknown")
            user_preferred_level = user.get("preferred_level", test_level)
            print(f"✅ Found user: {user_email}")
            print(f"   User ID: {test_user_id}")
            print(f"   Preferred Level: {user_preferred_level}")

            # Use user's preferred level if available
            if user_preferred_level:
                test_level = user_preferred_level
                print(f"   Using user's preferred level: {test_level}")
        else:
            print(f"✅ Using user ID: {test_user_id}")

        print()

        # Step 2: Display test configuration
        print("=" * 80)
        print("🎯 TEST CONFIGURATION")
        print("=" * 80)
        print(f"User ID:        {test_user_id}")
        print(f"Language:       {test_language}")
        print(f"CEFR Level:     {test_level}")
        print(f"Challenge Type: {test_challenge_type}")
        print(f"Count:          {test_count}")
        print("=" * 80)
        print()

        # Step 3: Generate challenges with CrewAI
        print("🚀 Starting CrewAI challenge generation...")
        print("⏰ This will take 30-60 seconds (3 agents working)...")
        print()

        start_time = datetime.utcnow()

        challenges = await generate_challenges_with_ai(
            user_id=test_user_id,
            user_level=test_level,
            language=test_language,
            challenge_type=test_challenge_type,
            count=test_count
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Step 4: Display results
        print()
        print("=" * 80)
        print("📊 GENERATION RESULTS")
        print("=" * 80)
        print(f"✅ Generated:     {len(challenges)} challenge(s)")
        print(f"⏱️  Time:          {duration:.2f} seconds")
        print(f"💰 Est. Cost:     ~$0.05 per generation (3 agents × 6 API calls)")
        print("=" * 80)
        print()

        if challenges:
            # Display first challenge as sample
            print("📝 SAMPLE CHALLENGE (First Generated)")
            print("=" * 80)
            print(json.dumps(challenges[0], indent=2, default=str))
            print("=" * 80)
            print()

            # Ask if user wants to save to database
            print("💾 Save to Database?")
            print()
            save = input("   Type 'yes' to save these challenges to challenge_pool: ").lower().strip()

            if save == 'yes':
                # Save to challenge_pool
                pool_collection = database.challenge_pool

                pool_docs = []
                for challenge in challenges:
                    pool_doc = {
                        "user_id": test_user_id,
                        "language": test_language,
                        "cefr_level": test_level,
                        "challenge_type": test_challenge_type,
                        "challenge_data": challenge,
                        "status": "available",
                        "created_at": datetime.utcnow(),
                        "completed_at": None,
                        "expires_at": datetime.utcnow()
                    }
                    pool_docs.append(pool_doc)

                result = await pool_collection.insert_many(pool_docs)
                print(f"   ✅ Saved {len(result.inserted_ids)} challenges to database")
                print()
            else:
                print("   ⏭️  Skipped saving to database")
                print()

        else:
            print("❌ No challenges generated!")
            print("Check the logs above for errors.")
            print()

        print("=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")

    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def main():
    """Main entry point"""
    await test_crewai_generation()


if __name__ == "__main__":
    print()
    print("🔧 IMPORTANT: Make sure you have:")
    print("   1. Activated your venv")
    print("   2. Installed crewai: pip install crewai==1.7.2 crewai-tools==1.7.2")
    print("   3. Set OPENAI_API_KEY in .env")
    print("   4. Set MONGODB_URL in .env")
    print()
    input("Press Enter to continue...")
    print()

    asyncio.run(main())
