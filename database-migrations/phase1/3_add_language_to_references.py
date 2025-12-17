"""
Phase 1 - Step 3: Add Language Field to Reference Challenges
=============================================================
✅ SAFE: Only ADDING a field, not removing or changing existing data
✅ REVERSIBLE: Can remove field if needed

This script adds a 'language' field to all reference_challenges documents.
All existing challenges are tagged as "english".
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

async def add_language_field():
    """Add language field to reference_challenges"""

    print("=" * 80)
    print("🔧 PHASE 1 - STEP 3: ADD LANGUAGE FIELD TO REFERENCE CHALLENGES")
    print("=" * 80)
    print(f"\n📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📂 Database: {DATABASE_NAME}\n")

    # Connect
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    db = client[DATABASE_NAME]

    try:
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        reference_challenges = db.reference_challenges

        # Count documents without language field
        without_language = await reference_challenges.count_documents({
            "language": {"$exists": False}
        })

        with_language = await reference_challenges.count_documents({
            "language": {"$exists": True}
        })

        total = await reference_challenges.count_documents({})

        print(f"📊 Current state:")
        print(f"   - Total documents: {total}")
        print(f"   - With language field: {with_language}")
        print(f"   - Without language field: {without_language}\n")

        if without_language == 0:
            print("✅ All reference challenges already have language field!")
            print("   Nothing to update.\n")
            return

        print(f"🔧 Will add language='english' to {without_language} documents")
        print("   (All existing challenges are English)\n")

        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("\n❌ Operation cancelled.")
            return

        # Add language field
        print("\n🔄 Updating documents...")
        result = await reference_challenges.update_many(
            {"language": {"$exists": False}},
            {"$set": {"language": "english"}}
        )

        print(f"   ✅ Updated {result.modified_count} documents")

        # Verify update
        without_language_after = await reference_challenges.count_documents({
            "language": {"$exists": False}
        })

        with_language_after = await reference_challenges.count_documents({
            "language": {"$exists": True}
        })

        print(f"\n📊 After update:")
        print(f"   - With language field: {with_language_after}")
        print(f"   - Without language field: {without_language_after}")

        # Create index
        print(f"\n🔍 Creating index for efficient language queries...")
        await reference_challenges.create_index([
            ("language", 1),
            ("cefr_level", 1),
            ("challenge_type", 1)
        ])
        print(f"   ✅ Index created: language + cefr_level + challenge_type")

        print("\n" + "=" * 80)
        print("✅ LANGUAGE FIELD ADDED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"   - Documents updated: {result.modified_count}")
        print(f"   - All challenges now have language='english'")
        print(f"   - Index created for performance")
        print(f"\n💡 Next step:")
        print(f"   - Can now generate Dutch/Spanish challenges separately")
        print(f"   - System will filter by language when copying to user pools\n")

    except Exception as e:
        print(f"\n❌ Error during update: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("✅ SAFE OPERATION - READ ONLY ADDS NEW FIELD")
    print("=" * 80)
    print("\nThis script will ADD 'language' field to reference challenges.")
    print("\n✅ Safety:")
    print("   - Only adds new field (non-destructive)")
    print("   - Doesn't change existing data")
    print("   - Reversible (can remove field later)")
    print("   - Creates index for performance")
    print("\n")

    asyncio.run(add_language_field())
