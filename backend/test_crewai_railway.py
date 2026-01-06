#!/usr/bin/env python3
"""
Railway Test Script for CrewAI Challenge Generation
===================================================

This script tests the CrewAI implementation on Railway's Python 3.11 environment.

Usage (on Railway or any Python 3.11+ environment):
    python test_crewai_railway.py

Configuration:
    - Language: english
    - Level: A2
    - Type: brain_tickler
    - Count: 3 challenges
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


async def test_crewai():
    """Test CrewAI challenge generation"""

    print("\n" + "=" * 80)
    print("🧪 CREWAI CHALLENGE GENERATION TEST - RAILWAY/PRODUCTION")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Python Environment: Railway (Python 3.11+)")
    print("=" * 80)
    print()

    # Test configuration
    test_language = "english"
    test_level = "A2"
    test_challenge_type = "brain_tickler"
    test_count = 3

    try:
        # Connect to database
        print("📡 Connecting to MongoDB...")
        await database.client.admin.command('ping')
        print("✅ Connected successfully")
        print()

        # Find a test user
        print("👤 Finding test user with English learning plan...")
        learning_plans = await database.learning_plans.find({
            "language": test_language
        }).limit(1).to_list(length=1)

        if not learning_plans:
            print("❌ No English learning plans found!")
            return

        test_user_id = learning_plans[0].get("user_id")
        print(f"✅ Using user: {test_user_id}")
        print()

        # Display test configuration
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

        # Generate challenges
        print("🚀 Starting CrewAI generation (30-60 seconds)...")
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

        # Display results
        print()
        print("=" * 80)
        print("📊 RESULTS")
        print("=" * 80)
        print(f"✅ Generated: {len(challenges)} challenges")
        print(f"⏱️  Duration:  {duration:.2f} seconds")
        print(f"💰 Est. Cost: ~$0.05 (3 agents)")
        print("=" * 80)
        print()

        if challenges:
            print("📝 SAMPLE CHALLENGE")
            print("=" * 80)
            print(json.dumps(challenges[0], indent=2, default=str))
            print("=" * 80)
            print()
            print("✅ TEST PASSED - CrewAI is working correctly!")
        else:
            print("❌ TEST FAILED - No challenges generated")
            print("Check logs above for errors")

        print()
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_crewai())
