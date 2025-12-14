"""
Fix Duplicate Challenge IDs
Clears and regenerates challenges for users with duplicate IDs
"""

import asyncio
from database import database
from seed_production_smart import generate_pool_for_user


async def clear_and_regenerate_user(user_email: str, challenges_per_type: int = 10):
    """
    Clear existing challenges and regenerate with unique IDs

    Args:
        user_email: User email
        challenges_per_type: Number per type to generate (default 10)
    """
    try:
        print(f"\n[FIX] 🔧 Fixing duplicate IDs for: {user_email}")

        # Find user
        users_collection = database.users
        user = await users_collection.find_one({"email": user_email})

        if not user:
            print(f"[FIX] ❌ User not found: {user_email}")
            return

        user_id = str(user["_id"])
        user_level = user.get("preferred_level") or "B1"

        print(f"[FIX] 👤 User: {user_email}")
        print(f"[FIX] 📊 Level: {user_level}")

        # Clear existing challenges
        pool_collection = database.challenge_pool
        result = await pool_collection.delete_many({"user_id": user_id})

        print(f"[FIX] 🗑️  Deleted {result.deleted_count} old challenges")

        # Regenerate with unique IDs
        print(f"[FIX] 🔄 Regenerating {challenges_per_type} per type with unique IDs...")

        generated = await generate_pool_for_user(user_id, user_level, challenges_per_type)

        if generated > 0:
            print(f"[FIX] ✅ Generated {generated} new challenges with unique IDs")

            # Verify uniqueness
            all_challenges = await pool_collection.find({
                "user_id": user_id
            }).to_list(length=None)

            ids = [c.get("challenge_data", {}).get("id") for c in all_challenges]
            unique_ids = set(ids)

            print(f"[FIX] 📊 Total challenges: {len(ids)}")
            print(f"[FIX] 📊 Unique IDs: {len(unique_ids)}")

            if len(ids) == len(unique_ids):
                print(f"[FIX] ✅ All IDs are unique!")
            else:
                print(f"[FIX] ⚠️  Still have {len(ids) - len(unique_ids)} duplicates")
        else:
            print(f"[FIX] ❌ Generation failed")

    except Exception as e:
        print(f"[FIX] ❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def fix_all_users():
    """Clear and regenerate for all users who have challenges"""
    try:
        print(f"\n[FIX] 🔧 Fixing duplicate IDs for all users...")

        pool_collection = database.challenge_pool

        # Get unique user IDs that have challenges
        user_ids = await pool_collection.distinct("user_id")

        print(f"[FIX] 👥 Found {len(user_ids)} users with challenges")

        confirm = input(f"\nClear and regenerate for all {len(user_ids)} users? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        users_collection = database.users
        from bson import ObjectId

        for idx, user_id in enumerate(user_ids, 1):
            # Convert string to ObjectId
            try:
                user = await users_collection.find_one({"_id": ObjectId(user_id)})
            except:
                user = None

            if not user:
                print(f"[FIX] ⚠️  User {user_id} not found, skipping")
                continue

            user_email = user.get("email", "Unknown")
            user_level = user.get("preferred_level") or "B1"

            print(f"\n[FIX] 👤 User {idx}/{len(user_ids)}: {user_email}")

            # Check if already has unique IDs
            existing_challenges = await pool_collection.find({
                "user_id": user_id
            }).limit(10).to_list(length=10)

            if existing_challenges:
                ids = [c.get("challenge_data", {}).get("id", "") for c in existing_challenges]
                # Check if IDs have UUID suffix (format: xxx_xxxxxxxx)
                has_unique_ids = all("_" in id and len(id.split("_")[-1]) == 8 for id in ids if id)

                if has_unique_ids:
                    print(f"[FIX] ✓ Already has unique IDs, skipping")
                    continue

            # Clear existing
            result = await pool_collection.delete_many({"user_id": user_id})
            print(f"[FIX] 🗑️  Deleted {result.deleted_count} old challenges")

            # Regenerate
            generated = await generate_pool_for_user(user_id, user_level, 10)

            if generated > 0:
                print(f"[FIX] ✅ Generated {generated} new challenges")
            else:
                print(f"[FIX] ⚠️  Generation failed")

        print(f"\n[FIX] ✅ All users fixed!")

    except Exception as e:
        print(f"[FIX] ❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            # Fix all users
            await fix_all_users()
        elif command == "user":
            # Fix specific user
            if len(sys.argv) < 3:
                print("Usage: python fix_duplicate_ids.py user <email> [count]")
                return

            user_email = sys.argv[2]
            count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            await clear_and_regenerate_user(user_email, count)
        else:
            print("Unknown command")
    else:
        print("\n📖 Usage:")
        print("  python fix_duplicate_ids.py user <email> [count]")
        print("  python fix_duplicate_ids.py all")
        print("\nExamples:")
        print("  python fix_duplicate_ids.py user alipala.ist@gmail.com 10")
        print("  python fix_duplicate_ids.py all")


if __name__ == "__main__":
    asyncio.run(main())
