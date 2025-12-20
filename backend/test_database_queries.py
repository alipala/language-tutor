"""
Test script to verify database queries work correctly
Uses existing database.py module
"""

import asyncio
import os
import sys

# Set up environment
os.chdir('/home/user/language-tutor/backend')
sys.path.insert(0, '/home/user/language-tutor/backend')

# Load environment for MongoDB connection
from dotenv import load_dotenv
load_dotenv('/home/user/language-tutor/backend/.env.local', override=True)

from motor.motor_asyncio import AsyncIOMotorClient


async def test_queries():
    """Test the database queries"""

    # Get connection details from environment
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=60000&retryWrites=true&retryReads=true")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

    print("\n" + "="*60)
    print("Testing Database Queries")
    print("="*60)

    # Create client
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    database = client[DATABASE_NAME]

    try:
        # Test connection
        await client.admin.command('ping')
        print("\n✓ MongoDB connection successful\n")

        # Get collections
        ref_collection = database.reference_challenges
        pool_collection = database.challenge_pool

        # Test 1: Count French A1 reference challenges
        print("Test 1: Count French A1 reference challenges")
        count = await ref_collection.count_documents({
            "language": "french",
            "cefr_level": "A1"
        })
        print(f"  Result: {count} documents ✓\n")

        # Test 2: Count Dutch B2 reference challenges
        print("Test 2: Count Dutch B2 reference challenges")
        count = await ref_collection.count_documents({
            "language": "dutch",
            "cefr_level": "B2"
        })
        print(f"  Result: {count} documents ✓\n")

        # Test 3: Count English B1 reference challenges
        print("Test 3: Count English B1 reference challenges")
        count = await ref_collection.count_documents({
            "language": "english",
            "cefr_level": "B1"
        })
        print(f"  Result: {count} documents ✓\n")

        # Test 4: Get breakdown of all reference challenges
        print("Test 4: Get reference challenges breakdown")
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "language": "$language",
                        "level": "$cefr_level"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {
                    "_id.language": 1,
                    "_id.level": 1
                }
            }
        ]

        results = await ref_collection.aggregate(pipeline).to_list(None)

        if results:
            print("  Results:")
            breakdown = {}
            for result in results:
                language = result["_id"]["language"]
                level = result["_id"]["level"]
                count = result["count"]

                if language not in breakdown:
                    breakdown[language] = {}
                breakdown[language][level] = count

            for language, levels in sorted(breakdown.items()):
                print(f"\n  {language.title()}:")
                for level, count in sorted(levels.items()):
                    print(f"    {level}: {count}")
        else:
            print("  No documents found")

        print("\n" + "="*60)
        print("All tests completed successfully! ✓")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(test_queries())
