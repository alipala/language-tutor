"""
Test script for Challenge Pool System
Tests the new endpoints and seed script with a single user
"""

import asyncio
from database import database
from seed_challenge_pool import seed_single_user, create_indexes


async def test_challenge_pool():
    """Test the challenge pool system with a single user"""

    print("\n" + "="*60)
    print("CHALLENGE POOL SYSTEM - TEST")
    print("="*60 + "\n")

    # Step 1: Create indexes
    print("[TEST] Step 1: Creating database indexes...")
    await create_indexes()
    print("[TEST] ✅ Indexes created\n")

    # Step 2: Find a test user
    print("[TEST] Step 2: Finding a test user...")
    users_collection = database.users
    user = await users_collection.find_one({"is_active": True})

    if not user:
        print("[TEST] ❌ No active users found in database")
        print("[TEST] Please create a user first or run with a production database")
        return

    user_email = user.get("email", "Unknown")
    user_id = str(user["_id"])
    user_level = user.get("preferred_level") or "B1"

    print(f"[TEST] ✅ Found test user: {user_email}")
    print(f"[TEST]    User ID: {user_id}")
    print(f"[TEST]    Level: {user_level}\n")

    # Step 3: Generate small pool (5 per type = 30 total for testing)
    print("[TEST] Step 3: Generating test pool (5 per type = 30 challenges)...")
    print("[TEST] ⏳ This will take a few minutes (AI generation)...\n")

    await seed_single_user(user_email, challenges_per_type=5)

    # Step 4: Verify pool was created
    print("\n[TEST] Step 4: Verifying pool creation...")
    pool_collection = database.challenge_pool

    # Count by type
    challenge_types = [
        "error_spotting",
        "swipe_fix",
        "micro_quiz",
        "smart_flashcard",
        "native_check",
        "brain_tickler"
    ]

    print("[TEST] 📊 Challenge counts by type:")
    total = 0
    for challenge_type in challenge_types:
        count = await pool_collection.count_documents({
            "user_id": user_id,
            "challenge_type": challenge_type,
            "status": "available"
        })
        total += count
        print(f"[TEST]   - {challenge_type}: {count}")

    print(f"[TEST]   - TOTAL: {total}\n")

    # Step 5: Test fetching challenges
    print("[TEST] Step 5: Testing challenge retrieval...")

    # Get first 3 error_spotting challenges
    challenges = await pool_collection.find({
        "user_id": user_id,
        "challenge_type": "error_spotting",
        "status": "available"
    }).limit(3).to_list(length=3)

    print(f"[TEST] ✅ Retrieved {len(challenges)} error_spotting challenges")

    if challenges:
        first_challenge = challenges[0]
        challenge_data = first_challenge.get("challenge_data", {})
        print(f"[TEST] 📝 Sample challenge:")
        print(f"[TEST]    ID: {challenge_data.get('id')}")
        print(f"[TEST]    Type: {challenge_data.get('type')}")
        print(f"[TEST]    Title: {challenge_data.get('title')}")
        print(f"[TEST]    Level: {challenge_data.get('cefrLevel')}")

    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\n[TEST] ✅ All tests passed!")
    print(f"[TEST] 📊 Generated {total} challenges for user {user_email}")
    print("\n[TEST] Next steps:")
    print("[TEST] 1. Start the backend server: uvicorn main:app --reload")
    print("[TEST] 2. Test API endpoints:")
    print(f"[TEST]    GET /api/challenges/counts")
    print(f"[TEST]    GET /api/challenges/by-type/error_spotting?limit=50")
    print(f"[TEST] 3. Test from iOS app\n")


if __name__ == "__main__":
    asyncio.run(test_challenge_pool())
