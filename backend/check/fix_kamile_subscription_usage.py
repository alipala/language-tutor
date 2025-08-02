#!/usr/bin/env python3
"""
Fix Kamile's Subscription Usage Counter

This script fixes Kamile's subscription usage by properly counting the learning plan sessions
that are stored within the learning plan document structure.
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId

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

def fix_kamile_subscription_usage():
    """Fix Kamile's subscription usage counter"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client['language_tutor']
        kamile_user_id = "6863ba8450b8c0aa0d78de51"
        
        print(f"🎯 Fixing subscription usage for Kamile: {kamile_user_id}")
        
        # Get Kamile's user document
        user = db.users.find_one({"_id": ObjectId(kamile_user_id)})
        if not user:
            print(f"❌ User not found!")
            return False
        
        # Get Kamile's learning plan
        learning_plan = db.learning_plans.find_one({"user_id": kamile_user_id})
        if not learning_plan:
            print(f"❌ Learning plan not found!")
            return False
        
        print(f"\n👤 User: {user.get('name')} ({user.get('email')})")
        print(f"📊 Current subscription status: {user.get('subscription_status')}")
        print(f"📈 Current practice_sessions_used: {user.get('practice_sessions_used', 0)}")
        print(f"📚 Learning plan completed_sessions: {learning_plan.get('completed_sessions', 0)}")
        
        # Count actual sessions from learning plan
        total_actual_sessions = 0
        weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
        
        for week in weekly_schedule:
            session_details = week.get('session_details', [])
            completed_sessions = len([s for s in session_details if s.get('status') == 'completed'])
            total_actual_sessions += completed_sessions
            
            if completed_sessions > 0:
                print(f"   Week {week.get('week')}: {completed_sessions} completed sessions")
        
        print(f"\n🔢 Total actual completed sessions: {total_actual_sessions}")
        
        # Update user's practice_sessions_used to match actual sessions
        if total_actual_sessions != user.get('practice_sessions_used', 0):
            print(f"⚠️  Discrepancy found! Updating practice_sessions_used from {user.get('practice_sessions_used', 0)} to {total_actual_sessions}")
            
            # Update user document
            result = db.users.update_one(
                {"_id": ObjectId(kamile_user_id)},
                {
                    "$set": {
                        "practice_sessions_used": total_actual_sessions,
                        "subscription_usage": total_actual_sessions,  # Also set subscription_usage
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated subscription usage")
                
                # Also verify learning plan progress is correct
                total_sessions = learning_plan.get('total_sessions', 48)
                expected_progress = (total_actual_sessions / total_sessions) * 100 if total_sessions > 0 else 0
                current_progress = learning_plan.get('progress_percentage', 0)
                
                if abs(expected_progress - current_progress) > 0.1:  # Allow small floating point differences
                    print(f"📊 Updating learning plan progress: {current_progress:.1f}% → {expected_progress:.1f}%")
                    
                    db.learning_plans.update_one(
                        {"user_id": kamile_user_id},
                        {
                            "$set": {
                                "completed_sessions": total_actual_sessions,
                                "progress_percentage": expected_progress,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    print(f"✅ Learning plan progress updated")
                else:
                    print(f"✅ Learning plan progress is already correct: {current_progress:.1f}%")
                
            else:
                print(f"❌ Failed to update subscription usage")
        else:
            print(f"✅ Subscription usage is already correct")
        
        # Show final status
        updated_user = db.users.find_one({"_id": ObjectId(kamile_user_id)})
        updated_plan = db.learning_plans.find_one({"user_id": kamile_user_id})
        
        print(f"\n📋 Final Status:")
        print(f"   practice_sessions_used: {updated_user.get('practice_sessions_used', 0)}")
        print(f"   subscription_usage: {updated_user.get('subscription_usage', 0)}")
        print(f"   learning_plan completed_sessions: {updated_plan.get('completed_sessions', 0)}")
        print(f"   learning_plan progress_percentage: {updated_plan.get('progress_percentage', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing subscription usage: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    print("🔧 Starting Kamile's subscription usage fix...")
    
    if fix_kamile_subscription_usage():
        print("✅ Kamile's subscription usage fixed successfully!")
    else:
        print("❌ Fix failed!")
        sys.exit(1)
