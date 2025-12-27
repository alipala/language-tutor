"""
Check if previous_plan_id is being saved in learning plans
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print("Loaded .env for production")
else:
    print("No .env file found, using environment variables")

# Get MongoDB connection details
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

print(f"Using MongoDB URL from MONGODB_URL")
print(f"Connecting to MongoDB at: {MONGODB_URL[:50]}...")
print(f"Using database: {DATABASE_NAME}")

# User email to check
USER_EMAIL = "alipala.ist@gmail.com"


async def check_plans():
    """Check if previous_plan_id is saved in plans"""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print("MongoDB client initialized successfully\n")

    # Get user ID
    user = await db.users.find_one({"email": USER_EMAIL})
    if not user:
        print(f"❌ User not found: {USER_EMAIL}")
        return

    user_id = str(user["_id"])
    print(f"Found user: {USER_EMAIL}")
    print(f"User ID: {user_id}\n")

    print("=" * 80)
    print("CHECKING LEARNING PLANS")
    print("=" * 80)

    # Get all learning plans for this user
    plans = await db.learning_plans.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(None)

    print(f"\nFound {len(plans)} learning plans\n")

    for i, plan in enumerate(plans, 1):
        print(f"\n[{i}] Plan ID: {plan.get('id')}")
        print(f"    Language: {plan.get('language')}")
        print(f"    Level: {plan.get('proficiency_level')}")
        print(f"    Status: {plan.get('status')}")
        print(f"    Previous Plan ID: {plan.get('previous_plan_id', '❌ NOT SET')}")
        print(f"    From Final Assessment: {plan.get('from_final_assessment', False)}")
        print(f"    Completed Sessions: {plan.get('completed_sessions', 0)}/{plan.get('total_sessions', 0)}")

        # Check if this is a next-level plan
        if plan.get('previous_plan_id'):
            print(f"    ✅ This is a next-level plan (created from: {plan.get('previous_plan_id')})")
        elif plan.get('from_final_assessment'):
            print(f"    ⚠️  Marked as from_final_assessment but no previous_plan_id!")

    print("\n" + "=" * 80)
    print("CHECKING FOR NEXT-LEVEL PLAN RELATIONSHIPS")
    print("=" * 80)

    # Check which plans have next-level plans created
    for plan in plans:
        plan_id = plan.get('id')
        next_level_plans = [p for p in plans if p.get('previous_plan_id') == plan_id]

        if next_level_plans:
            print(f"\n✅ Plan {plan_id} ({plan.get('proficiency_level')}) has next-level plan:")
            for nlp in next_level_plans:
                print(f"   → {nlp.get('id')} ({nlp.get('proficiency_level')})")

    client.close()


if __name__ == "__main__":
    asyncio.run(check_plans())
