#!/usr/bin/env python3
"""
Investigate Kamile's Data Structure

This script investigates the actual data structure for Kamile to understand
why the learning plan sessions aren't being found.
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def get_mongo_client():
    """Get MongoDB client"""
    try:
        mongo_url = os.getenv('MONGODB_URL')
        if not mongo_url:
            print("❌ MONGODB_URL environment variable not set!")
            return None
            
        client = MongoClient(mongo_url)
        print(f"✅ Connected to Railway Production MongoDB")
        
        # Test the connection
        client.admin.command('ping')
        print(f"✅ Database connection verified")
        return client
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def investigate_kamile_data():
    """Investigate Kamile's data structure"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client['language_tutor']
        kamile_user_id = "6863ba8450b8c0aa0d78de51"
        
        print(f"🔍 Investigating data for user ID: {kamile_user_id}")
        
        # 1. Check user document
        user = db.users.find_one({"_id": ObjectId(kamile_user_id)})
        if user:
            print(f"\n👤 User Document:")
            print(f"   Name: {user.get('name', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Subscription Status: {user.get('subscription_status', 'N/A')}")
            print(f"   Subscription Type: {user.get('subscription_type', 'N/A')}")
            print(f"   Subscription Usage: {user.get('subscription_usage', 'N/A')}")
            print(f"   Created At: {user.get('created_at', 'N/A')}")
        else:
            print(f"❌ User not found!")
            return False
        
        # 2. Check all collections for this user
        collections_to_check = [
            'conversations',
            'learning_plan_sessions', 
            'learning_plans',
            'assessments',
            'user_progress'
        ]
        
        for collection_name in collections_to_check:
            if collection_name in db.list_collection_names():
                # Try different user ID formats
                count_str = db[collection_name].count_documents({"user_id": kamile_user_id})
                count_obj = db[collection_name].count_documents({"user_id": ObjectId(kamile_user_id)})
                
                print(f"\n📊 Collection '{collection_name}':")
                print(f"   Documents with user_id as string: {count_str}")
                print(f"   Documents with user_id as ObjectId: {count_obj}")
                
                # Show sample documents
                sample_str = list(db[collection_name].find({"user_id": kamile_user_id}).limit(2))
                sample_obj = list(db[collection_name].find({"user_id": ObjectId(kamile_user_id)}).limit(2))
                
                if sample_str:
                    print(f"   Sample documents (string user_id):")
                    for doc in sample_str:
                        doc_id = str(doc.get('_id', 'N/A'))
                        created_at = doc.get('created_at', 'N/A')
                        print(f"     • ID: {doc_id}, Created: {created_at}")
                
                if sample_obj:
                    print(f"   Sample documents (ObjectId user_id):")
                    for doc in sample_obj:
                        doc_id = str(doc.get('_id', 'N/A'))
                        created_at = doc.get('created_at', 'N/A')
                        print(f"     • ID: {doc_id}, Created: {created_at}")
            else:
                print(f"\n📊 Collection '{collection_name}': Does not exist")
        
        # 3. Check for any documents that might reference this user
        print(f"\n🔍 Searching for any references to user ID across all collections...")
        
        for collection_name in db.list_collection_names():
            try:
                # Search for the user ID in any field
                count = db[collection_name].count_documents({
                    "$or": [
                        {"user_id": kamile_user_id},
                        {"user_id": ObjectId(kamile_user_id)},
                        {"_id": ObjectId(kamile_user_id)}
                    ]
                })
                if count > 0:
                    print(f"   Found {count} documents in '{collection_name}'")
                    
                    # Show sample
                    sample = db[collection_name].find_one({
                        "$or": [
                            {"user_id": kamile_user_id},
                            {"user_id": ObjectId(kamile_user_id)},
                            {"_id": ObjectId(kamile_user_id)}
                        ]
                    })
                    if sample:
                        print(f"     Sample: {list(sample.keys())}")
            except Exception as e:
                print(f"   Error checking {collection_name}: {e}")
        
        # 4. Check the original user data from the task description
        original_user_id = "68611de8d21ce7f1f731063c"
        print(f"\n🔍 Checking original user ID from task: {original_user_id}")
        
        try:
            original_user = db.users.find_one({"_id": ObjectId(original_user_id)})
            if original_user:
                print(f"   Found original user: {original_user.get('email', 'N/A')}")
            else:
                print(f"   Original user not found")
        except Exception as e:
            print(f"   Error checking original user: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error investigating data: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    print("🔍 Starting Kamile data investigation...")
    investigate_kamile_data()
