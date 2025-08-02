import asyncio
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Add the backend directory to the path so we can import auth functions
sys.path.append('backend')

# Import the password hashing function
try:
    from auth import get_password_hash
except ImportError:
    # Fallback if we can't import from auth
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

async def create_test_user():
    # Connect to local MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["language_tutor_local"]
    users_collection = db["users"]
    
    # User details
    email = "430c7b01-706d-4a13-a466-7b5c2ee0ef00@mailslurp.biz"
    name = "Cemil Cem"
    password = "040050803"
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        print(f"User with email {email} already exists!")
        print(f"User ID: {existing_user['_id']}")
        
        # Update to verified status
        await users_collection.update_one(
            {"email": email},
            {"$set": {"is_verified": True, "is_active": True}}
        )
        print("✅ User updated to verified status")
        return
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Create user document
    user_doc = {
        "email": email,
        "name": name,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_verified": True,  # Set as verified
        "created_at": datetime.utcnow(),
        "last_login": None,
        "preferred_language": None,
        "preferred_level": None,
        # Subscription fields (default to free tier)
        "stripe_customer_id": None,
        "subscription_status": None,
        "subscription_plan": "try_learn",
        "subscription_period": None,
        "subscription_price_id": None,
        "subscription_expires_at": None,
        "subscription_started_at": None,
        "current_period_start": None,
        "current_period_end": None,
        "practice_sessions_used": 0,
        "assessments_used": 0,
        "learning_plan_preserved": False,
        "learning_plan_data": None,
        "learning_plan_progress": None
    }
    
    # Insert the user
    result = await users_collection.insert_one(user_doc)
    
    print("✅ Test user created successfully!")
    print(f"📧 Email: {email}")
    print(f"👤 Name: {name}")
    print(f"🔑 Password: {password}")
    print(f"🆔 User ID: {result.inserted_id}")
    print(f"✅ Verified: True")
    print(f"📱 Plan: Try & Learn (Free)")
    
    # Close the connection
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
