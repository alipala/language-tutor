#!/usr/bin/env python3
"""
Clear all institutional data (for testing/reset)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "language_tutor")

async def clear_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("🗑️  Clearing institutional data...")

    collections = [
        "institutions",
        "tutors",
        "institutional_learners",
        "invitations",
        "consent_records"
    ]

    total_deleted = 0
    for collection_name in collections:
        result = await db[collection_name].delete_many({})
        deleted_count = result.deleted_count
        total_deleted += deleted_count
        print(f"✅ Deleted {deleted_count} documents from {collection_name}")

    print(f"\n📊 Total documents deleted: {total_deleted}")
    print("✅ All institutional data cleared!")

    client.close()

if __name__ == "__main__":
    asyncio.run(clear_data())
