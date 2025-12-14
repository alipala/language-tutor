"""
SMART Production Challenge Pool Seeding Script
Only seeds users who:
1. Have active subscriptions OR
2. Have practice sessions in last 30 days OR
3. Are explicitly requested by email

This avoids wasting resources on inactive/test users
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from bson import ObjectId
from challenge_generator_ai import generate_challenges_with_ai

# Load .env file (production MongoDB URL)
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

if not MONGODB_URL:
    print("❌ ERROR: MONGODB_URL not found in .env file")
    sys.exit(1)

# Mask URL for display
masked_url = MONGODB_URL
if '@' in masked_url:
    parts = masked_url.split('@')
    if '//' in parts[0]:
        protocol_user = parts[0].split('//')
        masked_url = f"{protocol_user[0]}//***:***@{parts[1]}"

print(f"\n{'='*70}")
print(f"SMART PRODUCTION CHALLENGE POOL SEEDING")
print(f"{'='*70}")
print(f"MongoDB URL: {masked_url}")
print(f"Database: {DATABASE_NAME}")
print(f"{'='*70}\n")

confirm = input("⚠️  You are about to seed PRODUCTION database. Continue? (yes/no): ")
if confirm.lower() != "yes":
    print("Aborted.")
    sys.exit(0)

prod_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
prod_database = prod_client[DATABASE_NAME]


async def verify_connection():
    """Verify production database connection"""
    try:
        print(f"[SMART_SEED] 🔌 Testing production database connection...")
        await prod_client.admin.command('ping')
        print(f"[SMART_SEED] ✅ Successfully connected to production MongoDB")
        return True
    except Exception as e:
        print(f"[SMART_SEED] ❌ Failed to connect: {str(e)}")
        return False


async def create_indexes():
    """Create indexes"""
    try:
        print(f"[SMART_SEED] 📇 Creating indexes...")
        pool_collection = prod_database.challenge_pool

        await pool_collection.create_index([
            ("user_id", 1),
            ("challenge_type", 1),
            ("status", 1)
        ], name="pool_query_index")

        await pool_collection.create_index([
            ("user_id", 1),
            ("challenge_data.id", 1)
        ], name="pool_challenge_id_index")

        await pool_collection.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="pool_expiry_index"
        )

        print(f"[SMART_SEED] ✅ Indexes created")
    except Exception as e:
        print(f"[SMART_SEED] ⚠️ Error creating indexes: {str(e)}")


async def get_active_users():
    """
    Get truly active users based on:
    1. Has active subscription (not expired/canceled)
    2. Has practice sessions in last 30 days
    3. Is not a test/demo account
    """
    users_collection = prod_database.users
    sessions_collection = prod_database.conversation_sessions

    print(f"[SMART_SEED] 🔍 Finding active users...")

    # Get all users
    all_users = await users_collection.find({
        "is_active": True
    }).to_list(length=None)

    print(f"[SMART_SEED] 📊 Found {len(all_users)} users with is_active=True")

    active_users = []
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    for user in all_users:
        user_id = str(user["_id"])
        user_email = user.get("email", "")

        # Skip test accounts
        if "test" in user_email.lower() or "demo" in user_email.lower():
            print(f"[SMART_SEED] ⏭️  Skipping test account: {user_email}")
            continue

        # Check subscription status
        subscription_status = user.get("subscription_status")
        has_active_sub = subscription_status in ["active", "trialing"]

        # Check recent activity
        session_count = await sessions_collection.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": thirty_days_ago}
        })

        has_recent_activity = session_count > 0

        # Include user if they have active sub OR recent activity
        if has_active_sub or has_recent_activity:
            active_users.append({
                "user": user,
                "has_subscription": has_active_sub,
                "session_count": session_count,
                "reason": "subscription" if has_active_sub else f"{session_count} sessions in 30d"
            })
            print(f"[SMART_SEED] ✅ Active: {user_email} ({active_users[-1]['reason']})")
        else:
            print(f"[SMART_SEED] ⏭️  Inactive: {user_email} (no sub, no activity)")

    print(f"\n[SMART_SEED] 📊 Active users: {len(active_users)}/{len(all_users)}")

    return active_users


async def generate_pool_for_user(user_id: str, user_level: str, challenges_per_type: int = 50):
    """Generate pool for one user"""
    try:
        pool_collection = prod_database.challenge_pool

        # Check existing
        existing_count = await pool_collection.count_documents({
            "user_id": user_id,
            "status": "available"
        })

        if existing_count >= (challenges_per_type * 6):
            print(f"[SMART_SEED]     Already has {existing_count} challenges ✓")
            return 0

        print(f"[SMART_SEED]     Current: {existing_count} challenges")
        print(f"[SMART_SEED]     Generating {challenges_per_type} batches...")

        # Generate challenges
        challenges_by_type = {
            "error_spotting": [],
            "swipe_fix": [],
            "micro_quiz": [],
            "smart_flashcard": [],
            "native_check": [],
            "brain_tickler": []
        }

        for batch_num in range(1, challenges_per_type + 1):
            if batch_num % 10 == 0:
                print(f"[SMART_SEED]     Progress: {batch_num}/{challenges_per_type}")

            batch = await generate_challenges_with_ai(user_id, user_level)

            if batch:
                for challenge in batch:
                    challenge_type = challenge.get("type")
                    if challenge_type in challenges_by_type:
                        challenges_by_type[challenge_type].append(challenge)

        # Insert into pool
        pool_items = []
        total = 0

        for challenge_type, challenges in challenges_by_type.items():
            for challenge in challenges:
                pool_items.append({
                    "user_id": user_id,
                    "cefr_level": user_level,
                    "challenge_type": challenge_type,
                    "challenge_data": challenge,
                    "status": "available",
                    "created_at": datetime.utcnow(),
                    "completed_at": None,
                    "expires_at": datetime.utcnow() + timedelta(days=30)
                })
                total += 1

        if pool_items:
            result = await pool_collection.insert_many(pool_items)
            print(f"[SMART_SEED]     ✅ Inserted {len(result.inserted_ids)} challenges")

        return total

    except Exception as e:
        print(f"[SMART_SEED]     ❌ Error: {str(e)}")
        return 0


async def seed_active_users(challenges_per_type: int = 50):
    """Seed only active users"""
    try:
        active_users = await get_active_users()

        if len(active_users) == 0:
            print("[SMART_SEED] No active users to seed")
            return

        print(f"\n[SMART_SEED] 📋 Will seed {len(active_users)} active users")
        print(f"[SMART_SEED] ⏱️  Estimated time: {int(len(active_users) * challenges_per_type * 0.5)} minutes")

        confirm = input(f"\nContinue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        total_generated = 0
        start_time = datetime.now()

        for idx, user_data in enumerate(active_users, 1):
            user = user_data["user"]
            user_id = str(user["_id"])
            user_email = user.get("email", "Unknown")
            user_level = user.get("preferred_level") or "B1"
            reason = user_data["reason"]

            print(f"\n[SMART_SEED] 👤 User {idx}/{len(active_users)}: {user_email}")
            print(f"[SMART_SEED]     Level: {user_level} | Reason: {reason}")

            generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)
            total_generated += generated

        duration = (datetime.now() - start_time).total_seconds() / 60

        print(f"\n{'='*70}")
        print(f"[SMART_SEED] 🎉 Complete!")
        print(f"[SMART_SEED] ✅ Seeded {len(active_users)} active users")
        print(f"[SMART_SEED] 📊 Total challenges: {total_generated}")
        print(f"[SMART_SEED] ⏱️  Time: {duration:.1f} minutes")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"[SMART_SEED] ❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def seed_single_user(user_email: str, challenges_per_type: int = 50):
    """Seed specific user by email"""
    try:
        print(f"[SMART_SEED] 🔍 Looking for: {user_email}")

        users_collection = prod_database.users
        user = await users_collection.find_one({"email": user_email})

        if not user:
            print(f"[SMART_SEED] ❌ User not found: {user_email}")
            return

        user_id = str(user["_id"])
        user_level = user.get("preferred_level") or "B1"

        print(f"[SMART_SEED] ✅ Found user: {user_email}")
        print(f"[SMART_SEED]    Level: {user_level}")

        confirm = input(f"\nContinue? (yes/no): ")
        if confirm.lower() != "yes":
            return

        generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)

        if generated > 0:
            print(f"\n[SMART_SEED] ✅ Generated {generated} challenges for {user_email}")

    except Exception as e:
        print(f"[SMART_SEED] ❌ Error: {str(e)}")


async def list_users_preview():
    """Show which users would be seeded"""
    try:
        active_users = await get_active_users()

        print(f"\n{'='*70}")
        print(f"USERS THAT WOULD BE SEEDED:")
        print(f"{'='*70}\n")

        for idx, user_data in enumerate(active_users, 1):
            user = user_data["user"]
            email = user.get("email", "Unknown")
            level = user.get("preferred_level", "B1")
            reason = user_data["reason"]

            print(f"{idx}. {email}")
            print(f"   Level: {level} | Reason: {reason}\n")

        print(f"{'='*70}")
        print(f"Total: {len(active_users)} active users")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"[SMART_SEED] ❌ Error: {str(e)}")


async def main():
    """Main entry point"""

    if not await verify_connection():
        print("❌ Cannot proceed without connection")
        return

    await create_indexes()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            # Preview which users would be seeded
            await list_users_preview()

        elif command == "active":
            # Seed only active users
            challenges_per_type = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            await seed_active_users(challenges_per_type)

        elif command == "user":
            # Seed specific user
            if len(sys.argv) < 3:
                print("Usage: python seed_production_smart.py user <email> [count]")
                return

            user_email = sys.argv[2]
            challenges_per_type = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            await seed_single_user(user_email, challenges_per_type)

        else:
            print("Unknown command")
    else:
        print("\n📖 SMART SEEDING - Usage:")
        print("=" * 70)
        print("\n1. Preview which users would be seeded:")
        print("   python seed_production_smart.py list")
        print("\n2. Seed only active users (has subscription OR recent activity):")
        print("   python seed_production_smart.py active 50")
        print("   python seed_production_smart.py active 25")
        print("   python seed_production_smart.py active 10")
        print("\n3. Seed specific user by email:")
        print("   python seed_production_smart.py user test@example.com 50")
        print("\n" + "=" * 70)
        print("\n🎯 Active user criteria:")
        print("   - Has active subscription (status: active or trialing)")
        print("   - OR has practice sessions in last 30 days")
        print("   - Excludes test/demo accounts")
        print("\n⏱️  Time estimates:")
        print("   - 50 per type: ~25 min per user")
        print("   - 25 per type: ~12 min per user")
        print("   - 10 per type: ~5 min per user")
        print()


if __name__ == "__main__":
    asyncio.run(main())
