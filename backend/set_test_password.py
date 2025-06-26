#!/usr/bin/env python3
"""
Set a test password for a user to enable login testing.
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import bcrypt

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

def set_user_password(email, password):
    """Set password for a user"""
    try:
        db = get_database()
        users_collection = db.users
        
        # Find the user
        user = users_collection.find_one({"email": email})
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        print(f"📧 Found user: {user['name']} ({user['email']})")
        
        # Hash the password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        # Update the user with hashed password and verify email
        update_data = {
            "password": hashed_password.decode('utf-8'),
            "email_verified": True,  # Also verify email for testing
            "updated_at": datetime.utcnow()
        }
        
        # Update the user
        result = users_collection.update_one(
            {"email": email},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully set password and verified email!")
            print(f"🔐 Password: {password}")
            print("📧 Email verified: True")
            print("🧪 Ready for login testing!")
            return True
        else:
            print("⚠️  No changes made")
            return False
            
    except Exception as e:
        print(f"❌ Error setting password: {str(e)}")
        return False

def main():
    """Main function"""
    print("🔐 Test User Password Setup Tool")
    print("=" * 50)
    
    # Default test user email and password
    email = "testuser@example.com"
    password = "testpassword123"
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    
    print(f"🎯 Setting password for: {email}")
    print(f"🔐 Password: {password}")
    print()
    
    success = set_user_password(email, password)
    
    if success:
        print()
        print("✅ PASSWORD SET SUCCESSFULLY!")
        print("📝 Login Credentials:")
        print(f"   • Email: {email}")
        print(f"   • Password: {password}")
        print()
        print("🧪 You can now login and test the checkout flow!")
    else:
        print("❌ Failed to set password!")
        sys.exit(1)

if __name__ == "__main__":
    main()
