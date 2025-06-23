import asyncio
import sys
import os
from datetime import datetime
from database import users_collection, init_db
from auth import get_password_hash

async def create_test_users():
    """Create test users in the local database"""
    
    # Initialize database connection
    await init_db()
    
    test_users = [
        {
            "email": "testuser1@example.com",
            "name": "Test User 1",
            "hashed_password": get_password_hash("password123"),
            "is_active": True,
            "is_verified": True,
            "preferred_language": "english",
            "preferred_level": "beginner",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "testuser2@example.com", 
            "name": "Test User 2",
            "hashed_password": get_password_hash("password123"),
            "is_active": True,
            "is_verified": False,
            "preferred_language": "spanish",
            "preferred_level": "intermediate",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "testuser3@example.com",
            "name": "Test User 3", 
            "hashed_password": get_password_hash("password123"),
            "is_active": False,
            "is_verified": True,
            "preferred_language": "french",
            "preferred_level": "advanced",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    try:
        # Insert test users
        result = await users_collection.insert_many(test_users)
        print(f"✅ Successfully created {len(result.inserted_ids)} test users:")
        
        for i, user in enumerate(test_users):
            print(f"   {i+1}. {user['name']} ({user['email']}) - ID: {result.inserted_ids[i]}")
            
        print("\n🎯 You can now test the admin panel with these users!")
        print("📧 All users have password: password123")
        
    except Exception as e:
        print(f"❌ Error creating test users: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_test_users())
