import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

async def fix_subscription_dates():
    """Fix subscription dates directly in production MongoDB"""
    
    # Get MongoDB connection string
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment variables")
        return
    
    print(f"Connecting to MongoDB...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    users_collection = db.users
    
    # User details to fix
    user_id = "685fe4b2acdf4f770e24345e"
    user_email = "430c7b01-706d-4a13-a466-7b5c2ee0ef00@mailslurp.biz"
    
    print(f"Looking for user: {user_id} or email: {user_email}")
    
    # Try to find the user by ID first, then by email
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        print(f"User not found by ID, trying email...")
        user = await users_collection.find_one({"email": user_email})
    
    if not user:
        print(f"❌ User not found by ID or email")
        # Let's see what users exist
        print("Checking existing users...")
        users_count = await users_collection.count_documents({})
        print(f"Total users in database: {users_count}")
        
        # Show a few users for debugging
        sample_users = await users_collection.find({}).limit(3).to_list(length=3)
        for sample_user in sample_users:
            print(f"Sample user: {sample_user.get('_id')} - {sample_user.get('email')}")
        return
    
    print(f"✅ Found user: {user.get('email', 'unknown')}")
    print(f"Current subscription dates:")
    print(f"  - Start: {user.get('current_period_start')}")
    print(f"  - End: {user.get('current_period_end')}")
    
    # The correct dates from Stripe
    correct_start = datetime(2025, 6, 28, 22, 37, 34, tzinfo=timezone.utc)
    correct_end = datetime(2026, 6, 28, 22, 37, 34, tzinfo=timezone.utc)
    
    print(f"\nUpdating to correct dates:")
    print(f"  - Start: {correct_start}")
    print(f"  - End: {correct_end}")
    
    # Update the user with correct dates
    update_data = {
        "current_period_start": correct_start,
        "current_period_end": correct_end,
        "subscription_started_at": correct_start,
        "subscription_expires_at": correct_end,
        "subscription_period": "annual",
        "subscription_status": "active"
    }
    
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        print("✅ Successfully updated subscription dates!")
        
        # Verify the update
        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        print(f"\nVerification - Updated dates:")
        print(f"  - Start: {updated_user.get('current_period_start')}")
        print(f"  - End: {updated_user.get('current_period_end')}")
        print(f"  - Period: {updated_user.get('subscription_period')}")
        print(f"  - Status: {updated_user.get('subscription_status')}")
    else:
        print("❌ No changes were made to the user")
    
    # Close connection
    client.close()
    print("\n🎉 Database update completed!")

if __name__ == "__main__":
    asyncio.run(fix_subscription_dates())
