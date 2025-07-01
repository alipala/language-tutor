import os
import sys
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# MongoDB connection - Production Railway MongoDB
MONGODB_URI = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
client = MongoClient(MONGODB_URI)
db = client.language_tutor

def investigate_user_learning_plans():
    """Investigate the specific user's learning plans and history"""
    user_id = "686400809bb1effaa5448dcc"
    email = "a90e619b-a0b0-4ee3-a3aa-fc62ce987bb3@mailslurp.biz"
    
    print(f"🔍 Investigating user: {user_id}")
    print(f"📧 Email: {email}")
    print("=" * 80)
    
    # 1. Check user document
    print("\n1. USER DOCUMENT:")
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        print(f"✅ User found")
        print(f"   - Subscription: {user.get('subscription_plan', 'N/A')}")
        print(f"   - Status: {user.get('subscription_status', 'N/A')}")
        print(f"   - Created: {user.get('created_at', 'N/A')}")
        print(f"   - Sessions used: {user.get('practice_sessions_used', 0)}")
        print(f"   - Assessments used: {user.get('assessments_used', 0)}")
    else:
        print("❌ User not found!")
        return
    
    # 2. Check current learning plans
    print("\n2. CURRENT LEARNING PLANS:")
    current_plans = list(db.learning_plans.find({"user_id": user_id}))
    print(f"📊 Found {len(current_plans)} learning plan(s)")
    
    for i, plan in enumerate(current_plans, 1):
        print(f"\n   Plan {i}:")
        print(f"   - ID: {plan['_id']}")
        print(f"   - Language: {plan.get('language', 'N/A')}")
        print(f"   - Duration: {plan.get('duration_months', 'N/A')} months")
        print(f"   - Level: {plan.get('level', 'N/A')}")
        print(f"   - Created: {plan.get('created_at', 'N/A')}")
        print(f"   - Current week: {plan.get('current_week', 'N/A')}")
        print(f"   - Weeks completed: {plan.get('weeks_completed', 0)}")
        print(f"   - Total sessions: {plan.get('total_sessions', 'N/A')}")
        print(f"   - Completed sessions: {plan.get('completed_sessions', 0)}")
    
    # 3. Check for any learning plans with ObjectId user_id
    print("\n3. CHECKING FOR PLANS WITH OBJECTID USER_ID:")
    objectid_plans = list(db.learning_plans.find({"user_id": ObjectId(user_id)}))
    print(f"📊 Found {len(objectid_plans)} learning plan(s) with ObjectId user_id")
    
    for i, plan in enumerate(objectid_plans, 1):
        print(f"\n   Plan {i}:")
        print(f"   - ID: {plan['_id']}")
        print(f"   - Language: {plan.get('language', 'N/A')}")
        print(f"   - Duration: {plan.get('duration_months', 'N/A')} months")
        print(f"   - Level: {plan.get('level', 'N/A')}")
        print(f"   - Created: {plan.get('created_at', 'N/A')}")
    
    # 4. Check conversation sessions
    print("\n4. CONVERSATION SESSIONS:")
    sessions = list(db.conversation_sessions.find({"user_id": user_id}).sort("created_at", -1).limit(10))
    print(f"📊 Found {len(sessions)} recent conversation session(s)")
    
    for i, session in enumerate(sessions, 1):
        print(f"\n   Session {i}:")
        print(f"   - ID: {session['_id']}")
        print(f"   - Language: {session.get('language', 'N/A')}")
        print(f"   - Level: {session.get('level', 'N/A')}")
        print(f"   - Topic: {session.get('topic', 'N/A')}")
        print(f"   - Created: {session.get('created_at', 'N/A')}")
        print(f"   - Duration: {session.get('duration_minutes', 'N/A')} minutes")
    
    # 5. Check for any plans that might have been soft-deleted or archived
    print("\n5. CHECKING FOR ARCHIVED/DELETED PLANS:")
    all_plans = list(db.learning_plans.find({
        "$or": [
            {"user_id": user_id},
            {"user_id": ObjectId(user_id)}
        ]
    }))
    print(f"📊 Found {len(all_plans)} total learning plan(s) for this user")
    
    # 6. Look for any plans that might have English language
    print("\n6. SEARCHING FOR ENGLISH PLANS:")
    english_plans = list(db.learning_plans.find({
        "$or": [
            {"user_id": user_id, "language": "english"},
            {"user_id": ObjectId(user_id), "language": "english"}
        ]
    }))
    print(f"📊 Found {len(english_plans)} English learning plan(s)")
    
    for i, plan in enumerate(english_plans, 1):
        print(f"\n   English Plan {i}:")
        print(f"   - ID: {plan['_id']}")
        print(f"   - Language: {plan.get('language', 'N/A')}")
        print(f"   - Duration: {plan.get('duration_months', 'N/A')} months")
        print(f"   - Level: {plan.get('proficiency_level', 'N/A')}")
        print(f"   - Created: {plan.get('created_at', 'N/A')}")
        print(f"   - User ID type: {type(plan.get('user_id'))}")
        print(f"   - User ID value: {plan.get('user_id')}")
    
    # 7. Check if there are any plans without user_id that might belong to this user
    print("\n7. CHECKING FOR ORPHANED PLANS:")
    orphaned_plans = list(db.learning_plans.find({"user_id": None}))
    print(f"📊 Found {len(orphaned_plans)} orphaned learning plan(s)")
    
    # 8. Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY:")
    print(f"   - User exists: ✅")
    print(f"   - Current plans (string user_id): {len(current_plans)}")
    print(f"   - Current plans (ObjectId user_id): {len(objectid_plans)}")
    print(f"   - Total plans for user: {len(all_plans)}")
    print(f"   - English plans: {len(english_plans)}")
    print(f"   - Recent conversation sessions: {len(sessions)}")
    print(f"   - Orphaned plans: {len(orphaned_plans)}")

if __name__ == "__main__":
    investigate_user_learning_plans()
