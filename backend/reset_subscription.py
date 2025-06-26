#!/usr/bin/env python3
"""
Reset subscription data for a user while keeping them registered and verified.
This allows testing the complete checkout flow from a clean state.
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
    print("Loaded .env.local for local development")
else:
    load_dotenv()
    print("Loaded .env for production")

def get_database():
    """Get MongoDB database connection"""
    # Get MongoDB connection string from environment variables
    MONGODB_URL = None
    
    # Check for MongoDB URL in various environment variable formats
    for var_name in ["MONGODB_URL", "MONGO_URL", "MONGO_PUBLIC_URL"]:
        if os.getenv(var_name):
            MONGODB_URL = os.getenv(var_name)
            print(f"Using MongoDB URL from {var_name}")
            break
    
    # Fall back to localhost if no MongoDB URL is found
    if not MONGODB_URL:
        MONGODB_URL = "mongodb://localhost:27017"
        print("Using localhost MongoDB")
    
    DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MONGO_DATABASE") or "language_tutor"
    
    print(f"Connecting to MongoDB at: {MONGODB_URL.replace(MONGODB_URL.split('@')[0] if '@' in MONGODB_URL else MONGODB_URL, 'mongodb://***:***')}")
    print(f"Using database: {DATABASE_NAME}")
    
    # Create MongoDB client
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    return client[DATABASE_NAME]

def reset_user_subscription(email):
    """Reset subscription data for a specific user"""
    try:
        db = get_database()
        users_collection = db.users
        
        # Find the user
        user = users_collection.find_one({"email": email})
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        print(f"📧 Found user: {user['name']} ({user['email']})")
        print(f"🔍 Current subscription status: {user.get('subscription_status', 'None')}")
        print(f"📋 Current plan: {user.get('subscription_plan', 'None')}")
        
        # Reset subscription fields to default free tier
        update_data = {
            "subscription_status": "try_learn",
            "subscription_plan": "try_learn",
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
            "subscription_start_date": None,
            "subscription_end_date": None,
            "subscription_canceled_at": None,
            "subscription_cancel_at_period_end": False,
            "updated_at": datetime.utcnow()
        }
        
        # Remove any subscription-related fields that might exist
        unset_fields = {
            "stripe_price_id": "",
            "subscription_current_period_start": "",
            "subscription_current_period_end": "",
            "subscription_trial_start": "",
            "subscription_trial_end": "",
            "subscription_metadata": ""
        }
        
        # Update the user
        result = users_collection.update_one(
            {"email": email},
            {
                "$set": update_data,
                "$unset": unset_fields
            }
        )
        
        if result.modified_count > 0:
            print("✅ Successfully reset subscription data!")
            print("🔄 User is now on the free 'Try & Learn' plan")
            print("👤 User remains registered and verified")
            print("🧪 Ready for checkout testing!")
            return True
        else:
            print("⚠️  No changes made (user might already be on free plan)")
            return True
            
    except Exception as e:
        print(f"❌ Error resetting subscription: {str(e)}")
        return False

def main():
    """Main function"""
    print("🔄 MongoDB Subscription Reset Tool")
    print("=" * 50)
    
    # Default test user email
    email = "testuser@example.com"
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    print(f"🎯 Resetting subscription for: {email}")
    print()
    
    success = reset_user_subscription(email)
    
    if success:
        print()
        print("✅ RESET COMPLETE!")
        print("📝 What was reset:")
        print("   • Subscription status → 'try_learn'")
        print("   • Subscription plan → 'try_learn'")
        print("   • Stripe customer ID → None")
        print("   • Stripe subscription ID → None")
        print("   • All subscription dates → None")
        print()
        print("📝 What was preserved:")
        print("   • User account and login credentials")
        print("   • Email verification status")
        print("   • User profile data")
        print("   • Learning progress and history")
        print()
        print("🧪 Ready to test checkout flow!")
    else:
        print("❌ Reset failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
