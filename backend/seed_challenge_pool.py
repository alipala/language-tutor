"""
Challenge Pool Seed Script
Generates 300 challenges per user (50 per type) using AI
Run this script to populate the challenge pool for existing users
"""

import asyncio
import sys
from datetime import datetime, timedelta
from bson import ObjectId
from database import database
from challenge_generator_ai import generate_challenges_with_ai


async def generate_pool_for_user(user_id: str, user_level: str, challenges_per_type: int = 50):
    """
    Generate challenge pool for a single user

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        challenges_per_type: Number of challenges to generate per type (default 50)

    Returns:
        Number of challenges generated
    """
    try:
        print(f"\n[POOL_SEED] 🎯 Generating pool for user {user_id} (level: {user_level})")

        pool_collection = database.challenge_pool

        # Check if user already has challenges
        existing_count = await pool_collection.count_documents({
            "user_id": user_id,
            "status": "available"
        })

        if existing_count >= 300:
            print(f"[POOL_SEED] ✅ User already has {existing_count} challenges, skipping")
            return 0

        print(f"[POOL_SEED] 📊 User has {existing_count} existing challenges")

        # Generate challenges in batches (50 AI calls, each returns 6 challenges)
        # We'll extract one of each type from each batch
        total_generated = 0
        challenges_by_type = {
            "error_spotting": [],
            "swipe_fix": [],
            "micro_quiz": [],
            "smart_flashcard": [],
            "native_check": [],
            "brain_tickler": []
        }

        # Generate enough batches to get 50 of each type
        # Each AI call generates 6 challenges (1 of each type)
        # So we need 50 AI calls to get 50 of each type
        num_batches = challenges_per_type

        print(f"[POOL_SEED] 🤖 Generating {num_batches} batches (6 challenges each)...")

        for batch_num in range(1, num_batches + 1):
            print(f"[POOL_SEED] 🔄 Batch {batch_num}/{num_batches}...")

            # Generate 6 challenges with AI
            batch_challenges = await generate_challenges_with_ai(user_id, user_level)

            if not batch_challenges or len(batch_challenges) == 0:
                print(f"[POOL_SEED] ⚠️ Batch {batch_num} failed, skipping")
                continue

            # Group by type
            for challenge in batch_challenges:
                challenge_type = challenge.get("type")
                if challenge_type in challenges_by_type:
                    challenges_by_type[challenge_type].append(challenge)

            # Show progress every 10 batches
            if batch_num % 10 == 0:
                print(f"[POOL_SEED] 📈 Progress: {batch_num}/{num_batches} batches completed")

        # Insert all challenges into pool
        pool_items = []

        for challenge_type, challenges in challenges_by_type.items():
            print(f"[POOL_SEED] 💾 Inserting {len(challenges)} {challenge_type} challenges")

            for challenge in challenges:
                pool_item = {
                    "user_id": user_id,
                    "cefr_level": user_level,
                    "challenge_type": challenge_type,
                    "challenge_data": challenge,
                    "status": "available",
                    "created_at": datetime.utcnow(),
                    "completed_at": None,
                    "expires_at": datetime.utcnow() + timedelta(days=30)
                }
                pool_items.append(pool_item)
                total_generated += 1

        # Bulk insert
        if pool_items:
            result = await pool_collection.insert_many(pool_items)
            print(f"[POOL_SEED] ✅ Inserted {len(result.inserted_ids)} challenges into pool")

        # Show final counts by type
        print(f"\n[POOL_SEED] 📊 Final counts by type:")
        for challenge_type in challenges_by_type.keys():
            count = len(challenges_by_type[challenge_type])
            print(f"  - {challenge_type}: {count}")

        print(f"[POOL_SEED] ✅ Generated {total_generated} total challenges for user {user_id}")

        return total_generated

    except Exception as e:
        print(f"[POOL_SEED] ❌ Error generating pool for user {user_id}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 0


async def seed_all_users(challenges_per_type: int = 50):
    """
    Generate challenge pools for all active users

    Args:
        challenges_per_type: Number of challenges per type (default 50, total 300)
    """
    try:
        print(f"\n{'='*60}")
        print(f"[POOL_SEED] 🚀 Starting Challenge Pool Generation")
        print(f"[POOL_SEED] 📋 Target: {challenges_per_type} challenges per type (300 total)")
        print(f"{'='*60}\n")

        users_collection = database.users

        # Get all active users
        users = await users_collection.find({
            "is_active": True
        }).to_list(length=None)

        print(f"[POOL_SEED] 👥 Found {len(users)} active users")

        total_challenges = 0
        successful_users = 0

        for idx, user in enumerate(users, 1):
            user_id = str(user["_id"])
            user_level = user.get("preferred_level") or "B1"

            print(f"\n[POOL_SEED] 👤 User {idx}/{len(users)}: {user.get('email', 'Unknown')}")

            generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)

            if generated > 0:
                total_challenges += generated
                successful_users += 1

        print(f"\n{'='*60}")
        print(f"[POOL_SEED] 🎉 Pool Generation Complete!")
        print(f"[POOL_SEED] ✅ Successfully generated pools for {successful_users}/{len(users)} users")
        print(f"[POOL_SEED] 📊 Total challenges generated: {total_challenges}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"[POOL_SEED] ❌ Error seeding all users: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def seed_single_user(user_email: str, challenges_per_type: int = 50):
    """
    Generate challenge pool for a single user by email

    Args:
        user_email: User email address
        challenges_per_type: Number of challenges per type (default 50)
    """
    try:
        print(f"\n[POOL_SEED] 🔍 Looking for user: {user_email}")

        users_collection = database.users
        user = await users_collection.find_one({"email": user_email})

        if not user:
            print(f"[POOL_SEED] ❌ User not found: {user_email}")
            return

        user_id = str(user["_id"])
        user_level = user.get("preferred_level") or "B1"

        generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)

        if generated > 0:
            print(f"\n[POOL_SEED] ✅ Successfully generated {generated} challenges for {user_email}")
        else:
            print(f"\n[POOL_SEED] ⚠️ No new challenges generated for {user_email}")

    except Exception as e:
        print(f"[POOL_SEED] ❌ Error seeding user {user_email}: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def create_indexes():
    """Create necessary indexes on challenge_pool collection"""
    try:
        print(f"[POOL_SEED] 📇 Creating indexes...")

        pool_collection = database.challenge_pool

        # Index for querying available challenges by type
        await pool_collection.create_index([
            ("user_id", 1),
            ("challenge_type", 1),
            ("status", 1)
        ], name="pool_query_index")

        # Index for finding challenges by challenge ID
        await pool_collection.create_index([
            ("user_id", 1),
            ("challenge_data.id", 1)
        ], name="pool_challenge_id_index")

        # TTL index for auto-expiring old challenges
        await pool_collection.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="pool_expiry_index"
        )

        print(f"[POOL_SEED] ✅ Indexes created successfully")

    except Exception as e:
        print(f"[POOL_SEED] ⚠️ Error creating indexes: {str(e)}")


async def main():
    """Main entry point"""

    # Create indexes first
    await create_indexes()

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            # Seed all users
            challenges_per_type = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            await seed_all_users(challenges_per_type)

        elif command == "user":
            # Seed single user by email
            if len(sys.argv) < 3:
                print("Usage: python seed_challenge_pool.py user <email> [challenges_per_type]")
                return

            user_email = sys.argv[2]
            challenges_per_type = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            await seed_single_user(user_email, challenges_per_type)

        else:
            print("Unknown command. Use 'all' or 'user'")
    else:
        print("Usage:")
        print("  python seed_challenge_pool.py all [challenges_per_type]")
        print("  python seed_challenge_pool.py user <email> [challenges_per_type]")
        print("\nExamples:")
        print("  python seed_challenge_pool.py all 50")
        print("  python seed_challenge_pool.py user test@example.com 50")


if __name__ == "__main__":
    asyncio.run(main())
