#!/usr/bin/env python3
"""
Setup script for institutional collections and indexes
Run this script to initialize the institutional database schema
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv(backend_dir / '.env')

from motor.motor_asyncio import AsyncIOMotorClient
from app.db.institutional_collections import setup_institutional_collections

async def main():
    """Main setup function"""
    print("🚀 Setting up institutional collections...")

    # Get MongoDB connection string
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("❌ MONGODB_URL environment variable not found")
        print("   Please set MONGODB_URL in your .env file")
        return 1

    # Get database name
    database_name = os.getenv("DATABASE_NAME", "language_tutor")

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        db = client[database_name]

        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB database: {database_name}")

        # Setup collections and indexes
        await setup_institutional_collections(db)

        # Verify collections were created
        collections = await db.list_collection_names()
        institutional_collections = [
            'institutions',
            'tutors',
            'institutional_learners',
            'invitations',
            'consent_records'
        ]

        missing_collections = []
        for collection in institutional_collections:
            if collection not in collections:
                missing_collections.append(collection)

        if missing_collections:
            print(f"⚠️  Warning: Collections not found: {missing_collections}")
            print("   This is normal if collections are empty (MongoDB creates them on first insert)")
        else:
            print("✅ All institutional collections exist")

        # Check indexes
        print("\n📊 Checking indexes...")
        for collection_name in institutional_collections:
            collection = db[collection_name]
            indexes = await collection.index_information()
            index_count = len(indexes) - 1  # Subtract 1 for the default _id index
            print(f"   {collection_name}: {index_count} custom indexes")

        print("\n🎉 Institutional database setup complete!")
        print("\n📋 Collections created:")
        print("   - institutions: Organization records")
        print("   - tutors: Instructor accounts")
        print("   - institutional_learners: Enrollment records")
        print("   - invitations: Enrollment invitations (with TTL)")
        print("   - consent_records: GDPR compliance audit trail")

        return 0

    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return 1

    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
