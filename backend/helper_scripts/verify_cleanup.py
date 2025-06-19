#!/usr/bin/env python3
"""
Script to verify that the cleanup was successful
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB connection details
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

async def verify_cleanup():
    """Verify that the cleanup was successful"""
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        database = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB at: {MONGODB_URL}")
        print(f"📁 Using database: {DATABASE_NAME}")
        
        print("\n🔍 VERIFICATION RESULTS")
        print("=" * 80)
        
        # Check users for assessment data
        users_collection = database.users
        users_with_assessment = await users_collection.count_documents({"last_assessment_data": {"$exists": True}})
        print(f"👥 Users with assessment data remaining: {users_with_assessment}")
        
        # Check conversation sessions
        sessions_collection = database.conversation_sessions
        session_count = await sessions_collection.count_documents({})
        print(f"💬 Conversation sessions remaining: {session_count}")
        
        # Check learning plans
        plans_collection = database.learning_plans
        plans_count = await plans_collection.count_documents({})
        print(f"📚 Learning plans remaining: {plans_count}")
        
        # Summary
        print("\n" + "=" * 80)
        if users_with_assessment == 0 and session_count == 0 and plans_count == 0:
            print("✅ CLEANUP VERIFICATION: SUCCESS")
            print("All speaking assessment data and practice mode conversations have been cleaned!")
        else:
            print("⚠️  CLEANUP VERIFICATION: INCOMPLETE")
            print("Some data may still remain in the database.")
        print("=" * 80)
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_cleanup())
