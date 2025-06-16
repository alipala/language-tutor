#!/usr/bin/env python3
"""
Script to delete a specific user from the production database
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

async def delete_user_by_email(email: str):
    """Delete a user and all related data by email"""
    if not MONGODB_URL:
        print("❌ MONGODB_URL environment variable not set!")
        return False
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB database: {DATABASE_NAME}")
        
        # Collections
        users_collection = database.users
        sessions_collection = database.sessions
        email_verifications_collection = database.email_verifications
        conversation_sessions_collection = database.conversation_sessions
        learning_plans_collection = database.learning_plans
        password_resets_collection = database.password_resets
        
        # Find the user first
        user = await users_collection.find_one({"email": email})
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        user_id = user["_id"]
        print(f"📧 Found user: {user.get('name', 'Unknown')} ({email})")
        print(f"🆔 User ID: {user_id}")
        print(f"📅 Created: {user.get('created_at', 'Unknown')}")
        print(f"✅ Verified: {user.get('is_verified', False)}")
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will permanently delete the user and ALL related data!")
        print(f"📧 Email: {email}")
        print(f"🆔 User ID: {user_id}")
        
        # Delete related data
        print(f"\n🗑️  Deleting user data...")
        
        # Delete sessions
        sessions_result = await sessions_collection.delete_many({"user_id": str(user_id)})
        print(f"   Sessions deleted: {sessions_result.deleted_count}")
        
        # Delete email verifications
        email_verifications_result = await email_verifications_collection.delete_many({"email": email})
        print(f"   Email verifications deleted: {email_verifications_result.deleted_count}")
        
        # Delete conversation sessions
        conversation_sessions_result = await conversation_sessions_collection.delete_many({"user_id": str(user_id)})
        print(f"   Conversation sessions deleted: {conversation_sessions_result.deleted_count}")
        
        # Delete learning plans
        learning_plans_result = await learning_plans_collection.delete_many({"user_id": user_id})
        print(f"   Learning plans deleted: {learning_plans_result.deleted_count}")
        
        # Delete password resets
        password_resets_result = await password_resets_collection.delete_many({"email": email})
        print(f"   Password resets deleted: {password_resets_result.deleted_count}")
        
        # Finally, delete the user
        user_result = await users_collection.delete_one({"_id": user_id})
        print(f"   User deleted: {user_result.deleted_count}")
        
        if user_result.deleted_count > 0:
            print(f"\n✅ Successfully deleted user '{email}' and all related data!")
            return True
        else:
            print(f"\n❌ Failed to delete user '{email}'!")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting user: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()

async def main():
    """Main function"""
    email = "alipala@mail.com"
    
    print("🗑️  User Deletion Script")
    print("=" * 50)
    print(f"Target email: {email}")
    print("=" * 50)
    
    success = await delete_user_by_email(email)
    
    if success:
        print(f"\n🎉 User deletion completed successfully!")
        print(f"📧 You can now test signup again with: {email}")
    else:
        print(f"\n❌ User deletion failed!")

if __name__ == "__main__":
    asyncio.run(main())
