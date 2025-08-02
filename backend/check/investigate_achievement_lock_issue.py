#!/usr/bin/env python3

import pymongo
from pymongo import MongoClient
from bson import ObjectId
import json
from datetime import datetime
import pprint

# MongoDB connection details from the provided environment
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

# User details to investigate
USER_EMAIL = "ea375861-ffae-41df-be08-ef309b3738fa@mailslurp.biz"
USER_ID = "6871ac37b3da13a7e9f1c1bb"

def connect_to_mongodb():
    """Connect to MongoDB and return database instance"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        # Test connection
        db.command('ping')
        print(f"✅ Successfully connected to MongoDB database: {DATABASE_NAME}")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def get_all_collections(db):
    """Get list of all collections in the database"""
    try:
        collections = db.list_collection_names()
        print(f"\n📋 Found {len(collections)} collections in database:")
        for i, collection in enumerate(collections, 1):
            print(f"  {i}. {collection}")
        return collections
    except Exception as e:
        print(f"❌ Error getting collections: {e}")
        return []

def find_user_data(db, user_email, user_id):
    """Find user data across all collections"""
    print(f"\n🔍 Searching for user data:")
    print(f"   Email: {user_email}")
    print(f"   User ID: {user_id}")
    
    user_data = {}
    collections = get_all_collections(db)
    
    for collection_name in collections:
        try:
            collection = db[collection_name]
            
            # Search by email
            email_results = list(collection.find({"email": user_email}))
            
            # Search by user_id (both string and ObjectId)
            user_id_results = []
            try:
                # Try as ObjectId
                user_id_results.extend(list(collection.find({"_id": ObjectId(user_id)})))
                user_id_results.extend(list(collection.find({"user_id": ObjectId(user_id)})))
                user_id_results.extend(list(collection.find({"userId": ObjectId(user_id)})))
            except:
                pass
            
            # Try as string
            user_id_results.extend(list(collection.find({"user_id": user_id})))
            user_id_results.extend(list(collection.find({"userId": user_id})))
            
            # Combine results and remove duplicates
            all_results = email_results + user_id_results
            unique_results = []
            seen_ids = set()
            
            for result in all_results:
                result_id = str(result.get('_id', ''))
                if result_id not in seen_ids:
                    unique_results.append(result)
                    seen_ids.add(result_id)
            
            if unique_results:
                user_data[collection_name] = unique_results
                print(f"   ✅ Found {len(unique_results)} records in '{collection_name}'")
            
        except Exception as e:
            print(f"   ❌ Error searching collection '{collection_name}': {e}")
    
    return user_data

def analyze_achievement_system(db):
    """Analyze the achievement system structure"""
    print(f"\n🏆 Analyzing Achievement System Structure:")
    
    # Look for achievement-related collections
    collections = get_all_collections(db)
    achievement_collections = [c for c in collections if 'achievement' in c.lower() or 'badge' in c.lower() or 'progress' in c.lower()]
    
    print(f"   Achievement-related collections: {achievement_collections}")
    
    # Sample documents from key collections to understand structure
    key_collections = ['users', 'learning_plans', 'user_progress', 'achievements', 'badges', 'sessions']
    
    for collection_name in key_collections:
        if collection_name in collections:
            try:
                collection = db[collection_name]
                sample_doc = collection.find_one()
                if sample_doc:
                    print(f"\n   📄 Sample document from '{collection_name}':")
                    # Convert ObjectId to string for JSON serialization
                    sample_doc_str = json.dumps(sample_doc, default=str, indent=2)
                    print(f"   {sample_doc_str[:500]}..." if len(sample_doc_str) > 500 else f"   {sample_doc_str}")
            except Exception as e:
                print(f"   ❌ Error sampling collection '{collection_name}': {e}")

def deep_dive_user_investigation(db, user_data):
    """Perform deep dive investigation of user data"""
    print(f"\n🔬 DEEP DIVE INVESTIGATION:")
    print("=" * 80)
    
    for collection_name, records in user_data.items():
        print(f"\n📊 Collection: {collection_name}")
        print("-" * 40)
        
        for i, record in enumerate(records):
            print(f"\n   Record {i+1}:")
            # Convert to JSON for better readability
            record_json = json.dumps(record, default=str, indent=4)
            print(f"   {record_json}")
            
            # Special analysis for specific collections
            if collection_name == 'learning_plans':
                analyze_learning_plan(record)
            elif collection_name == 'user_progress':
                analyze_user_progress(record)
            elif collection_name == 'users':
                analyze_user_profile(record)

def analyze_learning_plan(plan):
    """Analyze learning plan data"""
    print(f"\n   🎯 Learning Plan Analysis:")
    print(f"      Language: {plan.get('language', 'N/A')}")
    print(f"      Level: {plan.get('level', 'N/A')}")
    print(f"      Created: {plan.get('created_at', 'N/A')}")
    print(f"      Status: {plan.get('status', 'N/A')}")
    print(f"      Current Week: {plan.get('current_week', 'N/A')}")
    
    # Check for achievement-related fields
    achievement_fields = ['achievements', 'badges', 'progress', 'completed_weeks', 'unlocked_achievements']
    for field in achievement_fields:
        if field in plan:
            print(f"      {field}: {plan[field]}")

def analyze_user_progress(progress):
    """Analyze user progress data"""
    print(f"\n   📈 User Progress Analysis:")
    print(f"      Learning Plan ID: {progress.get('learning_plan_id', 'N/A')}")
    print(f"      Week: {progress.get('week', 'N/A')}")
    print(f"      Completed: {progress.get('completed', 'N/A')}")
    print(f"      Progress: {progress.get('progress', 'N/A')}")
    print(f"      Last Updated: {progress.get('updated_at', 'N/A')}")
    
    # Check for achievement-related fields
    achievement_fields = ['achievements', 'badges', 'unlocked', 'eligible_for_badge']
    for field in achievement_fields:
        if field in progress:
            print(f"      {field}: {progress[field]}")

def analyze_user_profile(user):
    """Analyze user profile data"""
    print(f"\n   👤 User Profile Analysis:")
    print(f"      Email: {user.get('email', 'N/A')}")
    print(f"      Created: {user.get('created_at', 'N/A')}")
    print(f"      Last Login: {user.get('last_login', 'N/A')}")
    
    # Check for achievement-related fields
    achievement_fields = ['achievements', 'badges', 'completed_weeks', 'learning_plans', 'progress']
    for field in achievement_fields:
        if field in user:
            print(f"      {field}: {user[field]}")

def investigate_timeline(db, user_data):
    """Investigate timeline of events"""
    print(f"\n⏰ TIMELINE INVESTIGATION:")
    print("=" * 80)
    
    timeline_events = []
    
    # Collect all timestamped events
    for collection_name, records in user_data.items():
        for record in records:
            # Look for timestamp fields
            timestamp_fields = ['created_at', 'updated_at', 'completed_at', 'last_login']
            for field in timestamp_fields:
                if field in record:
                    timeline_events.append({
                        'collection': collection_name,
                        'event': field,
                        'timestamp': record[field],
                        'data': record
                    })
    
    # Sort by timestamp - handle mixed datetime and string types
    def sort_key(event):
        timestamp = event['timestamp']
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                # Try to parse string as datetime
                from dateutil import parser
                return parser.parse(timestamp)
            except:
                return datetime.min
        else:
            return datetime.min
    
    timeline_events.sort(key=sort_key)
    
    print(f"\n📅 Chronological Events ({len(timeline_events)} total):")
    for event in timeline_events:
        print(f"   {event['timestamp']} | {event['collection']} | {event['event']}")
        
        # Show relevant data for learning plans and progress
        if event['collection'] in ['learning_plans', 'user_progress']:
            data = event['data']
            if 'language' in data:
                print(f"      → Language: {data['language']}")
            if 'week' in data:
                print(f"      → Week: {data['week']}")
            if 'completed' in data:
                print(f"      → Completed: {data['completed']}")

def main():
    print("🚀 Starting Achievement Lock Investigation")
    print("=" * 80)
    
    # Connect to database
    db = connect_to_mongodb()
    if db is None:
        return
    
    # Get all collections
    collections = get_all_collections(db)
    
    # Analyze achievement system structure
    analyze_achievement_system(db)
    
    # Find user data
    user_data = find_user_data(db, USER_EMAIL, USER_ID)
    
    if not user_data:
        print(f"\n❌ No data found for user {USER_EMAIL} (ID: {USER_ID})")
        return
    
    print(f"\n✅ Found user data in {len(user_data)} collections")
    
    # Deep dive investigation
    deep_dive_user_investigation(db, user_data)
    
    # Timeline investigation
    investigate_timeline(db, user_data)
    
    # Summary and hypothesis
    print(f"\n🎯 INVESTIGATION SUMMARY:")
    print("=" * 80)
    print("Based on the data analysis, investigating why achievements got locked...")
    
    # Look for patterns that might cause achievement locking
    learning_plans = user_data.get('learning_plans', [])
    if len(learning_plans) > 1:
        print(f"\n🔍 Found {len(learning_plans)} learning plans - this might be the issue!")
        for i, plan in enumerate(learning_plans):
            print(f"   Plan {i+1}: {plan.get('language', 'Unknown')} - Created: {plan.get('created_at', 'Unknown')}")
    
    print(f"\n📋 Next steps for investigation:")
    print("   1. Check if achievement system is tied to specific learning plans")
    print("   2. Verify if creating new learning plan resets achievement state")
    print("   3. Look for achievement logic in backend code")
    print("   4. Check for any global vs plan-specific achievement tracking")

if __name__ == "__main__":
    main()
