import os
import sys
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# MongoDB connection - Production Railway MongoDB
MONGODB_URI = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
client = MongoClient(MONGODB_URI)
db = client.language_tutor

def fix_user_session_tracking():
    """Fix the session tracking for the specific user"""
    user_id = "686400809bb1effaa5448dcc"
    email = "a90e619b-a0b0-4ee3-a3aa-fc62ce987bb3@mailslurp.biz"
    
    print(f"🔧 Fixing session tracking for user: {user_id}")
    print(f"📧 Email: {email}")
    print("=" * 80)
    
    # 1. Get user document
    print("\n1. CURRENT USER STATUS:")
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        print("❌ User not found!")
        return
    
    print(f"✅ User found")
    print(f"   - Current practice_sessions_used: {user.get('practice_sessions_used', 0)}")
    print(f"   - Current assessments_used: {user.get('assessments_used', 0)}")
    
    # 2. Get learning plans and their actual progress
    print("\n2. LEARNING PLANS PROGRESS:")
    learning_plans = list(db.learning_plans.find({"user_id": user_id}))
    
    total_sessions_completed = 0
    for i, plan in enumerate(learning_plans, 1):
        completed = plan.get("completed_sessions", 0)
        total_sessions_completed += completed
        print(f"   Plan {i} ({plan.get('language')}): {completed} sessions completed")
    
    print(f"\n📊 Total sessions completed across all plans: {total_sessions_completed}")
    
    # 3. Check if we need to update
    current_tracked = user.get('practice_sessions_used', 0)
    
    if current_tracked != total_sessions_completed:
        print(f"\n⚠️ MISMATCH DETECTED!")
        print(f"   - User document shows: {current_tracked} sessions")
        print(f"   - Learning plans show: {total_sessions_completed} sessions")
        print(f"   - Difference: {total_sessions_completed - current_tracked}")
        
        # 4. Fix the tracking
        print(f"\n🔧 FIXING SESSION TRACKING...")
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "practice_sessions_used": total_sessions_completed,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated practice_sessions_used to {total_sessions_completed}")
            
            # Verify the fix
            updated_user = db.users.find_one({"_id": ObjectId(user_id)})
            print(f"✅ Verification: practice_sessions_used is now {updated_user.get('practice_sessions_used', 0)}")
        else:
            print(f"❌ Failed to update session tracking")
    else:
        print(f"\n✅ Session tracking is already correct!")
        print(f"   - Both user document and learning plans show: {total_sessions_completed} sessions")
    
    # 5. Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY:")
    print(f"   - User ID: {user_id}")
    print(f"   - Email: {email}")
    print(f"   - Learning plans: {len(learning_plans)}")
    print(f"   - Total sessions completed: {total_sessions_completed}")
    print(f"   - Session tracking: {'✅ Fixed' if current_tracked != total_sessions_completed else '✅ Already correct'}")

if __name__ == "__main__":
    fix_user_session_tracking()
