#!/usr/bin/env python3
"""
Script to clean users' speaking assessment and practice mode conversation data from MongoDB
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Get MongoDB connection details
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

async def connect_to_database():
    """Connect to MongoDB database"""
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        database = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB at: {MONGODB_URL}")
        print(f"📁 Using database: {DATABASE_NAME}")
        
        return client, database
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {str(e)}")
        return None, None

async def list_all_users(database):
    """List all users with their basic information"""
    try:
        users_collection = database.users
        users = await users_collection.find({}).to_list(length=None)
        
        print(f"\n📊 Found {len(users)} users in the database:")
        print("=" * 80)
        
        for i, user in enumerate(users, 1):
            print(f"\n{i}. User ID: {user.get('_id')}")
            print(f"   📧 Email: {user.get('email')}")
            print(f"   👤 Name: {user.get('name')}")
            print(f"   ✅ Active: {user.get('is_active', False)}")
            print(f"   📅 Created: {user.get('created_at')}")
            print(f"   🌐 Preferred Language: {user.get('preferred_language', 'Not set')}")
            print(f"   📈 Preferred Level: {user.get('preferred_level', 'Not set')}")
            
            # Check if user has assessment data
            if user.get('last_assessment_data'):
                print(f"   🎯 Has Assessment Data: Yes")
            else:
                print(f"   🎯 Has Assessment Data: No")
        
        return users
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
        return []

async def list_conversation_sessions(database):
    """List all conversation sessions"""
    try:
        sessions_collection = database.conversation_sessions
        sessions = await sessions_collection.find({}).to_list(length=None)
        
        print(f"\n💬 Found {len(sessions)} conversation sessions:")
        print("=" * 80)
        
        user_session_count = {}
        
        for i, session in enumerate(sessions, 1):
            user_id = session.get('user_id')
            if user_id not in user_session_count:
                user_session_count[user_id] = 0
            user_session_count[user_id] += 1
            
            print(f"\n{i}. Session ID: {session.get('_id')}")
            print(f"   👤 User ID: {user_id}")
            print(f"   🌐 Language: {session.get('language')}")
            print(f"   📈 Level: {session.get('level')}")
            print(f"   📝 Topic: {session.get('topic', 'Not specified')}")
            print(f"   💬 Messages: {len(session.get('messages', []))}")
            print(f"   ⏱️  Duration: {session.get('duration_minutes', 0)} minutes")
            print(f"   📅 Created: {session.get('created_at')}")
            
            # Show enhanced analysis if present
            if session.get('enhanced_analysis'):
                print(f"   🔍 Has Enhanced Analysis: Yes")
            else:
                print(f"   🔍 Has Enhanced Analysis: No")
        
        print(f"\n📊 Sessions per user:")
        for user_id, count in user_session_count.items():
            print(f"   User {user_id}: {count} sessions")
        
        return sessions
    except Exception as e:
        print(f"❌ Error listing conversation sessions: {str(e)}")
        return []

async def list_learning_plans(database):
    """List all learning plans if they exist"""
    try:
        plans_collection = database.learning_plans
        plans = await plans_collection.find({}).to_list(length=None)
        
        print(f"\n📚 Found {len(plans)} learning plans:")
        print("=" * 80)
        
        for i, plan in enumerate(plans, 1):
            print(f"\n{i}. Plan ID: {plan.get('_id')}")
            print(f"   👤 User ID: {plan.get('user_id')}")
            print(f"   🌐 Language: {plan.get('language', 'Not specified')}")
            print(f"   📈 Level: {plan.get('level', 'Not specified')}")
            print(f"   📅 Created: {plan.get('created_at')}")
        
        return plans
    except Exception as e:
        print(f"❌ Error listing learning plans: {str(e)}")
        return []

async def check_other_collections(database):
    """Check for other collections that might contain user data"""
    try:
        collection_names = await database.list_collection_names()
        print(f"\n📁 All collections in database:")
        print("=" * 80)
        
        for name in collection_names:
            collection = database[name]
            count = await collection.count_documents({})
            print(f"   📂 {name}: {count} documents")
        
        return collection_names
    except Exception as e:
        print(f"❌ Error listing collections: {str(e)}")
        return []

async def clean_user_assessment_data(database, users):
    """Clean speaking assessment data from users"""
    try:
        users_collection = database.users
        cleaned_count = 0
        
        print(f"\n🧹 Cleaning speaking assessment data from users...")
        print("=" * 80)
        
        for user in users:
            user_id = user.get('_id')
            if user.get('last_assessment_data'):
                # Remove the assessment data
                result = await users_collection.update_one(
                    {"_id": user_id},
                    {"$unset": {"last_assessment_data": ""}}
                )
                
                if result.modified_count > 0:
                    print(f"   ✅ Cleaned assessment data for user: {user.get('email')}")
                    cleaned_count += 1
                else:
                    print(f"   ⚠️  Failed to clean assessment data for user: {user.get('email')}")
        
        print(f"\n📊 Cleaned assessment data from {cleaned_count} users")
        return cleaned_count
    except Exception as e:
        print(f"❌ Error cleaning user assessment data: {str(e)}")
        return 0

async def clean_conversation_sessions(database):
    """Clean all conversation sessions (practice mode conversations)"""
    try:
        sessions_collection = database.conversation_sessions
        
        print(f"\n🧹 Cleaning all conversation sessions...")
        print("=" * 80)
        
        # Count documents before deletion
        count_before = await sessions_collection.count_documents({})
        print(f"   📊 Found {count_before} conversation sessions to delete")
        
        if count_before > 0:
            # Delete all conversation sessions
            result = await sessions_collection.delete_many({})
            print(f"   ✅ Deleted {result.deleted_count} conversation sessions")
            return result.deleted_count
        else:
            print(f"   ℹ️  No conversation sessions to delete")
            return 0
    except Exception as e:
        print(f"❌ Error cleaning conversation sessions: {str(e)}")
        return 0

async def clean_learning_plans(database):
    """Clean all learning plans"""
    try:
        plans_collection = database.learning_plans
        
        print(f"\n🧹 Cleaning all learning plans...")
        print("=" * 80)
        
        # Count documents before deletion
        count_before = await plans_collection.count_documents({})
        print(f"   📊 Found {count_before} learning plans to delete")
        
        if count_before > 0:
            # Delete all learning plans
            result = await plans_collection.delete_many({})
            print(f"   ✅ Deleted {result.deleted_count} learning plans")
            return result.deleted_count
        else:
            print(f"   ℹ️  No learning plans to delete")
            return 0
    except Exception as e:
        print(f"❌ Error cleaning learning plans: {str(e)}")
        return 0

async def main():
    """Main function to list and clean user data"""
    print("🚀 Starting MongoDB User Data Cleanup")
    print("=" * 80)
    
    # Connect to database
    client, database = await connect_to_database()
    if client is None or database is None:
        print("❌ Failed to connect to database. Exiting.")
        return
    
    try:
        # Step 1: List all collections
        print("\n📋 STEP 1: Examining database structure")
        await check_other_collections(database)
        
        # Step 2: List all users
        print("\n📋 STEP 2: Listing all users")
        users = await list_all_users(database)
        
        # Step 3: List conversation sessions
        print("\n📋 STEP 3: Listing conversation sessions")
        sessions = await list_conversation_sessions(database)
        
        # Step 4: List learning plans
        print("\n📋 STEP 4: Listing learning plans")
        plans = await list_learning_plans(database)
        
        # Ask for confirmation before cleaning
        print("\n" + "=" * 80)
        print("⚠️  WARNING: This will permanently delete the following data:")
        print("   • All speaking assessment data from user profiles")
        print("   • All conversation sessions (practice mode conversations)")
        print("   • All learning plans")
        print("=" * 80)
        
        confirm = input("\n❓ Do you want to proceed with cleaning? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            print("\n🧹 STARTING CLEANUP PROCESS")
            print("=" * 80)
            
            # Clean user assessment data
            assessment_cleaned = await clean_user_assessment_data(database, users)
            
            # Clean conversation sessions
            sessions_cleaned = await clean_conversation_sessions(database)
            
            # Clean learning plans
            plans_cleaned = await clean_learning_plans(database)
            
            # Summary
            print("\n" + "=" * 80)
            print("✅ CLEANUP COMPLETED")
            print("=" * 80)
            print(f"   📊 Users with assessment data cleaned: {assessment_cleaned}")
            print(f"   💬 Conversation sessions deleted: {sessions_cleaned}")
            print(f"   📚 Learning plans deleted: {plans_cleaned}")
            print("=" * 80)
            
        else:
            print("\n❌ Cleanup cancelled by user")
    
    except Exception as e:
        print(f"❌ Error in main process: {str(e)}")
    
    finally:
        # Close database connection
        if client:
            client.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
