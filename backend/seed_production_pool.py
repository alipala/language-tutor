"""
Production Challenge Pool Seeding Script
Run this locally to seed challenges into PRODUCTION MongoDB

Usage:
    python seed_production_pool.py all 50          # Seed all users with 50 per type
    python seed_production_pool.py all 25          # Seed all users with 25 per type
    python seed_production_pool.py user email@example.com 50  # Seed specific user
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from bson import ObjectId
from challenge_generator_ai import generate_challenges_with_ai

# Load .env file (which should have production MongoDB URL)
load_dotenv()

# Get production MongoDB URL
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

if not MONGODB_URL:
    print("❌ ERROR: MONGODB_URL not found in .env file")
    print("Make sure your .env file has the production MongoDB URL")
    sys.exit(1)

# Mask the URL for display (hide password)
masked_url = MONGODB_URL
if '@' in masked_url:
    parts = masked_url.split('@')
    if '//' in parts[0]:
        protocol_user = parts[0].split('//')
        masked_url = f"{protocol_user[0]}//***:***@{parts[1]}"

print(f"\n{'='*70}")
print(f"PRODUCTION CHALLENGE POOL SEEDING")
print(f"{'='*70}")
print(f"MongoDB URL: {masked_url}")
print(f"Database: {DATABASE_NAME}")
print(f"{'='*70}\n")

# Confirm with user
confirm = input("⚠️  You are about to seed PRODUCTION database. Continue? (yes/no): ")
if confirm.lower() != "yes":
    print("Aborted.")
    sys.exit(0)

# Create production client
prod_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
prod_database = prod_client[DATABASE_NAME]


async def create_indexes():
    """Create necessary indexes on challenge_pool collection"""
    try:
        print(f"[PROD_SEED] 📇 Creating indexes on production...")

        pool_collection = prod_database.challenge_pool

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

        print(f"[PROD_SEED] ✅ Indexes created successfully")

    except Exception as e:
        print(f"[PROD_SEED] ⚠️ Error creating indexes: {str(e)}")


async def generate_pool_for_user(user_id: str, user_level: str, challenges_per_type: int = 50):
    """
    Generate challenge pool for a single user in PRODUCTION

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        challenges_per_type: Number of challenges to generate per type (default 50)

    Returns:
        Number of challenges generated
    """
    try:
        print(f"\n[PROD_SEED] 🎯 Generating pool for user {user_id} (level: {user_level})")

        pool_collection = prod_database.challenge_pool

        # Check if user already has challenges
        existing_count = await pool_collection.count_documents({
            "user_id": user_id,
            "status": "available"
        })

        if existing_count >= 300:
            print(f"[PROD_SEED] ✅ User already has {existing_count} challenges, skipping")
            return 0

        print(f"[PROD_SEED] 📊 User has {existing_count} existing challenges")

        # Generate challenges in batches
        total_generated = 0
        challenges_by_type = {
            "error_spotting": [],
            "swipe_fix": [],
            "micro_quiz": [],
            "smart_flashcard": [],
            "native_check": [],
            "brain_tickler": []
        }

        num_batches = challenges_per_type

        print(f"[PROD_SEED] 🤖 Generating {num_batches} batches (6 challenges each)...")
        print(f"[PROD_SEED] ⏱️  Estimated time: {int(num_batches * 0.5)} minutes")

        for batch_num in range(1, num_batches + 1):
            print(f"[PROD_SEED] 🔄 Batch {batch_num}/{num_batches}...", end=" ", flush=True)

            # Generate 6 challenges with AI
            batch_challenges = await generate_challenges_with_ai(user_id, user_level)

            if not batch_challenges or len(batch_challenges) == 0:
                print(f"❌ FAILED")
                continue

            print(f"✅")

            # Group by type
            for challenge in batch_challenges:
                challenge_type = challenge.get("type")
                if challenge_type in challenges_by_type:
                    challenges_by_type[challenge_type].append(challenge)

            # Show progress every 10 batches
            if batch_num % 10 == 0:
                print(f"[PROD_SEED] 📈 Progress: {batch_num}/{num_batches} batches completed")

        # Insert all challenges into production pool
        pool_items = []

        for challenge_type, challenges in challenges_by_type.items():
            print(f"[PROD_SEED] 💾 Preparing {len(challenges)} {challenge_type} challenges")

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

        # Bulk insert into PRODUCTION
        if pool_items:
            print(f"[PROD_SEED] 🚀 Inserting {len(pool_items)} challenges into PRODUCTION...")
            result = await pool_collection.insert_many(pool_items)
            print(f"[PROD_SEED] ✅ Inserted {len(result.inserted_ids)} challenges")

        # Show final counts by type
        print(f"\n[PROD_SEED] 📊 Final counts by type:")
        for challenge_type in challenges_by_type.keys():
            count = len(challenges_by_type[challenge_type])
            print(f"  - {challenge_type}: {count}")

        print(f"[PROD_SEED] ✅ Generated {total_generated} total challenges for user {user_id}")

        return total_generated

    except Exception as e:
        print(f"[PROD_SEED] ❌ Error generating pool for user {user_id}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 0


async def seed_all_users(challenges_per_type: int = 50):
    """
    Generate challenge pools for all active users in PRODUCTION

    Args:
        challenges_per_type: Number of challenges per type (default 50, total 300)
    """
    try:
        print(f"\n{'='*70}")
        print(f"[PROD_SEED] 🚀 Starting Production Pool Generation")
        print(f"[PROD_SEED] 📋 Target: {challenges_per_type} challenges per type (300 total)")
        print(f"{'='*70}\n")

        users_collection = prod_database.users

        # Get all active users from PRODUCTION
        users = await users_collection.find({
            "is_active": True
        }).to_list(length=None)

        print(f"[PROD_SEED] 👥 Found {len(users)} active users in PRODUCTION")
        print(f"[PROD_SEED] ⏱️  Estimated total time: {int(len(users) * challenges_per_type * 0.5)} minutes\n")

        confirm = input(f"Continue with seeding {len(users)} users? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        total_challenges = 0
        successful_users = 0
        start_time = datetime.now()

        for idx, user in enumerate(users, 1):
            user_id = str(user["_id"])
            user_level = user.get("preferred_level") or "B1"
            user_email = user.get("email", "Unknown")

            print(f"\n[PROD_SEED] 👤 User {idx}/{len(users)}: {user_email}")

            generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)

            if generated > 0:
                total_challenges += generated
                successful_users += 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60

        print(f"\n{'='*70}")
        print(f"[PROD_SEED] 🎉 Production Pool Generation Complete!")
        print(f"[PROD_SEED] ✅ Successfully seeded {successful_users}/{len(users)} users")
        print(f"[PROD_SEED] 📊 Total challenges generated: {total_challenges}")
        print(f"[PROD_SEED] ⏱️  Total time: {duration:.1f} minutes")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"[PROD_SEED] ❌ Error seeding production: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def seed_single_user(user_email: str, challenges_per_type: int = 50):
    """
    Generate challenge pool for a single user by email in PRODUCTION

    Args:
        user_email: User email address
        challenges_per_type: Number of challenges per type (default 50)
    """
    try:
        print(f"\n[PROD_SEED] 🔍 Looking for user in PRODUCTION: {user_email}")

        users_collection = prod_database.users
        user = await users_collection.find_one({"email": user_email})

        if not user:
            print(f"[PROD_SEED] ❌ User not found in PRODUCTION: {user_email}")
            return

        user_id = str(user["_id"])
        user_level = user.get("preferred_level") or "B1"

        print(f"[PROD_SEED] ✅ Found user:")
        print(f"  - Email: {user_email}")
        print(f"  - User ID: {user_id}")
        print(f"  - Level: {user_level}")

        confirm = input(f"\nContinue with seeding this user? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)

        if generated > 0:
            print(f"\n[PROD_SEED] ✅ Successfully generated {generated} challenges in PRODUCTION for {user_email}")
        else:
            print(f"\n[PROD_SEED] ⚠️ No new challenges generated for {user_email}")

    except Exception as e:
        print(f"[PROD_SEED] ❌ Error seeding user {user_email}: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def verify_connection():
    """Verify production database connection"""
    try:
        print(f"[PROD_SEED] 🔌 Testing production database connection...")
        await prod_client.admin.command('ping')
        print(f"[PROD_SEED] ✅ Successfully connected to production MongoDB")
        return True
    except Exception as e:
        print(f"[PROD_SEED] ❌ Failed to connect to production MongoDB: {str(e)}")
        return False


async def main():
    """Main entry point"""

    # Verify connection first
    if not await verify_connection():
        print("\n❌ Cannot proceed without database connection")
        print("Check your MONGODB_URL in .env file")
        return

    # Create indexes
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
                print("Usage: python seed_production_pool.py user <email> [challenges_per_type]")
                return

            user_email = sys.argv[2]
            challenges_per_type = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            await seed_single_user(user_email, challenges_per_type)

        else:
            print("Unknown command. Use 'all' or 'user'")
    else:
        print("\n📖 Usage:")
        print("  python seed_production_pool.py all [challenges_per_type]")
        print("  python seed_production_pool.py user <email> [challenges_per_type]")
        print("\n📝 Examples:")
        print("  python seed_production_pool.py all 50           # Seed all users")
        print("  python seed_production_pool.py all 25           # Seed all users (faster)")
        print("  python seed_production_pool.py user test@example.com 50")
        print("\n⏱️  Time estimates:")
        print("  - 50 per type: ~25 minutes per user")
        print("  - 25 per type: ~12 minutes per user")
        print("  - 10 per type: ~5 minutes per user")


if __name__ == "__main__":
    asyncio.run(main())
