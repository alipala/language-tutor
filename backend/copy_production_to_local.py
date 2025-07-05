#!/usr/bin/env python3
"""
Copy production MongoDB data to local database for testing
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# Production MongoDB connection
PROD_MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"

# Local MongoDB connection (from .env.local)
LOCAL_MONGODB_URL = "mongodb://localhost:27017/language_tutor_local"

async def copy_production_to_local():
    """Copy all production data to local database"""
    
    print("🚀 Starting Production → Local Database Copy")
    print("=" * 60)
    
    # Connect to production database
    print("📡 Connecting to production database...")
    prod_client = AsyncIOMotorClient(PROD_MONGODB_URL)
    prod_db = prod_client.language_tutor
    
    # Connect to local database
    print("💻 Connecting to local database...")
    local_client = AsyncIOMotorClient(LOCAL_MONGODB_URL)
    local_db = local_client.language_tutor_local
    
    try:
        # Test connections
        await prod_client.admin.command('ping')
        await local_client.admin.command('ping')
        print("✅ Both database connections successful")
        
        # Get list of collections from production
        prod_collections = await prod_db.list_collection_names()
        print(f"\n📊 Found {len(prod_collections)} collections in production:")
        for collection in prod_collections:
            count = await prod_db[collection].count_documents({})
            print(f"   - {collection}: {count} documents")
        
        # Copy each collection
        print(f"\n🔄 Starting data copy process...")
        
        total_docs_copied = 0
        
        for collection_name in prod_collections:
            print(f"\n📋 Processing collection: {collection_name}")
            
            # Get all documents from production collection
            prod_collection = prod_db[collection_name]
            local_collection = local_db[collection_name]
            
            # Clear local collection first
            delete_result = await local_collection.delete_many({})
            print(f"   🗑️  Cleared {delete_result.deleted_count} existing local documents")
            
            # Get all documents from production
            documents = []
            async for doc in prod_collection.find({}):
                documents.append(doc)
            
            if documents:
                # Insert into local database
                insert_result = await local_collection.insert_many(documents)
                docs_copied = len(insert_result.inserted_ids)
                total_docs_copied += docs_copied
                print(f"   ✅ Copied {docs_copied} documents")
            else:
                print(f"   ⚪ No documents to copy")
        
        print(f"\n🎉 Copy completed successfully!")
        print(f"   📊 Total documents copied: {total_docs_copied}")
        
        # Verify the copy by checking some key collections
        print(f"\n🔍 Verification - Local database contents:")
        local_collections = await local_db.list_collection_names()
        
        for collection in ['users', 'learning_plans', 'conversation_sessions']:
            if collection in local_collections:
                count = await local_db[collection].count_documents({})
                print(f"   - {collection}: {count} documents")
                
                # Show sample user data
                if collection == 'users' and count > 0:
                    print(f"\n👥 Sample users in local database:")
                    async for user in local_db.users.find({}).limit(5):
                        email = user.get('email', 'N/A')
                        name = user.get('name', 'N/A')
                        user_id = str(user.get('_id', 'N/A'))
                        print(f"      - {name} ({email}) - ID: {user_id}")
                
                # Show learning plans
                if collection == 'learning_plans' and count > 0:
                    print(f"\n📚 Sample learning plans:")
                    async for plan in local_db.learning_plans.find({'user_id': {'$ne': None}}).limit(3):
                        user_id = plan.get('user_id', 'N/A')
                        language = plan.get('language', 'N/A')
                        level = plan.get('proficiency_level', 'N/A')
                        progress = plan.get('progress_percentage', 0)
                        completed = plan.get('completed_sessions', 0)
                        total = plan.get('total_sessions', 0)
                        print(f"      - User {user_id}: {language} {level} - {completed}/{total} sessions ({progress}%)")
        
        print(f"\n✅ Production data successfully copied to local database!")
        print(f"🎯 You can now test with real user data at http://localhost:3000")
        
    except Exception as e:
        print(f"❌ Error during copy process: {e}")
        raise
    
    finally:
        # Close connections
        prod_client.close()
        local_client.close()

async def main():
    await copy_production_to_local()

if __name__ == "__main__":
    asyncio.run(main())
