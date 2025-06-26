#!/usr/bin/env python3
"""
Get user information for testing purposes.
"""

import os
import sys
from pymongo import MongoClient
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

def get_user_info(email):
    """Get user information"""
    try:
        db = get_database()
        users_collection = db.users
        
        # Find the user
        user = users_collection.find_one({"email": email})
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        print(f"📧 User Email: {user['email']}")
        print(f"👤 User Name: {user['name']}")
        print(f"✅ Email Verified: {user.get('email_verified', False)}")
        print(f"🔐 Password Hash: {user.get('password', 'Not set')[:20]}...")
        print(f"📅 Created: {user.get('created_at', 'Unknown')}")
        print(f"🔄 Subscription Status: {user.get('subscription_status', 'None')}")
        print(f"📋 Subscription Plan: {user.get('subscription_plan', 'None')}")
        
        # Note: We can't retrieve the actual password as it's hashed
        print("\n⚠️  Note: Password is hashed and cannot be retrieved.")
        print("💡 Common test passwords to try:")
        print("   • password123")
        print("   • testpassword")
        print("   • 123456")
        print("   • test123")
        
        return True
            
    except Exception as e:
        print(f"❌ Error getting user info: {str(e)}")
        return False

def main():
    """Main function"""
    print("👤 User Information Retrieval Tool")
    print("=" * 50)
    
    # Default test user email
    email = "testuser@example.com"
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    print(f"🎯 Getting info for: {email}")
    print()
    
    success = get_user_info(email)
    
    if not success:
        print("❌ Failed to get user info!")
        sys.exit(1)

if __name__ == "__main__":
    main()
