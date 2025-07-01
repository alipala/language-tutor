#!/usr/bin/env python3
"""
Fix Subscription Counter Calculation

This script fixes the subscription counter calculation issue where learning plan sessions
are not being properly counted towards subscription usage.

The issue is that learning plan sessions are being skipped in the auto-save process
and not counted in subscription usage tracking.
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def get_mongo_client():
    """Get MongoDB client"""
    try:
        # Force connection to Railway production database
        mongo_url = os.getenv('MONGODB_URL')  # Changed from MONGO_URL to MONGODB_URL
        if not mongo_url:
            # If MONGODB_URL is not set, we need to connect to Railway
            print("❌ MONGODB_URL environment variable not set!")
            print("💡 Please run: railway login && railway link")
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

def fix_specific_user(user_id_str):
    """Fix subscription counter for a specific user"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client['language_tutor']
        
        # Find the specific user
        user = db.users.find_one({"_id": ObjectId(user_id_str)})
        if not user:
            print(f"❌ User with ID {user_id_str} not found!")
            return False
        
        email = user.get('email', 'Unknown')
        name = user.get('name', 'Unknown')
        
        print(f"\n👤 Processing specific user: {name} ({email})")
        print(f"   🆔 User ID: {user_id_str}")
        
        # Count all conversation sessions for this user
        conversation_count = db.conversations.count_documents({
            "user_id": user_id_str
        })
        
        # Count all learning plan sessions for this user
        learning_plan_sessions = list(db.learning_plan_sessions.find({
            "user_id": user_id_str
        }))
        
        learning_plan_count = len(learning_plan_sessions)
        
        # Total sessions should be conversation + learning plan sessions
        total_actual_sessions = conversation_count + learning_plan_count
        
        # Get current subscription usage
        current_usage = user.get('subscription_usage', 0)
        
        print(f"   📈 Conversation sessions: {conversation_count}")
        print(f"   📚 Learning plan sessions: {learning_plan_count}")
        print(f"   🔢 Total actual sessions: {total_actual_sessions}")
        print(f"   📊 Current recorded usage: {current_usage}")
        
        # Show learning plan sessions details
        if learning_plan_sessions:
            print(f"   📋 Learning plan session details:")
            for session in learning_plan_sessions:
                session_date = session.get('created_at', 'Unknown date')
                duration = session.get('duration', 'Unknown')
                print(f"      • {session_date} - Duration: {duration}")
        
        # Update subscription usage if there's a discrepancy
        if total_actual_sessions != current_usage:
            print(f"   ⚠️  Discrepancy found! Updating usage from {current_usage} to {total_actual_sessions}")
            
            # Update user's subscription usage
            result = db.users.update_one(
                {"_id": ObjectId(user_id_str)},
                {
                    "$set": {
                        "subscription_usage": total_actual_sessions,
                        "last_usage_update": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Successfully updated subscription usage")
                
                # Also update learning plan progress if there's a learning plan
                learning_plan = db.learning_plans.find_one({"user_id": user_id_str})
                if learning_plan:
                    total_sessions = learning_plan.get('total_sessions', 16)
                    progress_percentage = (learning_plan_count / total_sessions) * 100 if total_sessions > 0 else 0
                    
                    db.learning_plans.update_one(
                        {"user_id": user_id_str},
                        {
                            "$set": {
                                "completed_sessions": learning_plan_count,
                                "progress_percentage": progress_percentage
                            }
                        }
                    )
                    print(f"   ✅ Updated learning plan progress: {learning_plan_count}/{total_sessions} sessions ({progress_percentage:.1f}%)")
                
            else:
                print(f"   ❌ Failed to update subscription usage")
        else:
            print(f"   ✅ Usage count is correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing specific user: {e}")
        return False
    finally:
        client.close()

def fix_subscription_counter():
    """Fix subscription counter calculation"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client['language_tutor']
        
        # Get all users with active subscriptions
        users = list(db.users.find({
            "subscription_status": "active",
            "subscription_type": {"$in": ["monthly", "yearly"]}
        }))
        
        print(f"📊 Found {len(users)} users with active subscriptions")
        
        for user in users:
            user_id = user['_id']
            email = user.get('email', 'Unknown')
            
            print(f"\n👤 Processing user: {email}")
            
            # Count all conversation sessions for this user
            conversation_count = db.conversations.count_documents({
                "user_id": str(user_id)
            })
            
            # Count all learning plan sessions for this user
            learning_plan_sessions = list(db.learning_plan_sessions.find({
                "user_id": str(user_id)
            }))
            
            learning_plan_count = len(learning_plan_sessions)
            
            # Total sessions should be conversation + learning plan sessions
            total_actual_sessions = conversation_count + learning_plan_count
            
            # Get current subscription usage
            current_usage = user.get('subscription_usage', 0)
            
            print(f"   📈 Conversation sessions: {conversation_count}")
            print(f"   📚 Learning plan sessions: {learning_plan_count}")
            print(f"   🔢 Total actual sessions: {total_actual_sessions}")
            print(f"   📊 Current recorded usage: {current_usage}")
            
            # Update subscription usage if there's a discrepancy
            if total_actual_sessions != current_usage:
                print(f"   ⚠️  Discrepancy found! Updating usage from {current_usage} to {total_actual_sessions}")
                
                # Update user's subscription usage
                result = db.users.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            "subscription_usage": total_actual_sessions,
                            "last_usage_update": datetime.now(timezone.utc)
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f"   ✅ Successfully updated subscription usage")
                else:
                    print(f"   ❌ Failed to update subscription usage")
            else:
                print(f"   ✅ Usage count is correct")
        
        print(f"\n🎉 Subscription counter fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing subscription counter: {e}")
        return False
    finally:
        client.close()

def verify_fix():
    """Verify the fix worked correctly"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client['language_tutor']
        
        # Check a few users to verify the fix
        users = list(db.users.find({
            "subscription_status": "active"
        }).limit(5))
        
        print(f"\n🔍 Verifying fix for {len(users)} sample users:")
        
        for user in users:
            user_id = user['_id']
            email = user.get('email', 'Unknown')
            
            conversation_count = db.conversations.count_documents({
                "user_id": str(user_id)
            })
            
            learning_plan_count = db.learning_plan_sessions.count_documents({
                "user_id": str(user_id)
            })
            
            total_sessions = conversation_count + learning_plan_count
            recorded_usage = user.get('subscription_usage', 0)
            
            status = "✅" if total_sessions == recorded_usage else "❌"
            print(f"   {status} {email}: {recorded_usage} recorded vs {total_sessions} actual")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying fix: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    print("🔧 Starting subscription counter fix...")
    
    # Specific user ID for Kamile
    kamile_user_id = "6863ba8450b8c0aa0d78de51"
    
    print(f"🎯 Targeting specific user: {kamile_user_id}")
    
    if fix_specific_user(kamile_user_id):
        print("✅ Kamile's data fixed successfully!")
        
        # Also run general fix for all users
        print("\n🔄 Running general fix for all users...")
        if fix_subscription_counter():
            verify_fix()
    else:
        print("❌ Fix failed!")
        sys.exit(1)
