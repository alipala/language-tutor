#!/usr/bin/env python3
"""
Debug script to test subscription endpoint with detailed logging
"""

import os
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv("backend/.env")

async def test_subscription_directly():
    """Test subscription functionality directly with MongoDB"""
    try:
        # Get MongoDB connection string
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("❌ MONGODB_URL not found in environment variables")
            return
        
        print(f"🔗 Connecting to MongoDB...")
        print(f"📧 Testing direct subscription save...")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        database = client["language_tutor"]
        collection = database["newsletter_subscriptions"]
        
        # Test email
        test_email = "direct-test@example.com"
        
        # Check if email already exists
        existing_subscription = await collection.find_one({"email": test_email})
        
        if existing_subscription:
            print(f"⚠️ Email {test_email} already exists, deleting first...")
            await collection.delete_one({"email": test_email})
        
        # Create subscription document
        subscription_doc = {
            "email": test_email,
            "subscribed_at": datetime.now(timezone.utc),
            "status": "active",
            "source": "direct_test"
        }
        
        print(f"📝 Inserting subscription document: {subscription_doc}")
        
        # Insert into database
        result = await collection.insert_one(subscription_doc)
        
        if result.inserted_id:
            print(f"✅ Successfully inserted subscription with ID: {result.inserted_id}")
            
            # Verify it was saved
            saved_doc = await collection.find_one({"email": test_email})
            if saved_doc:
                print(f"✅ Verified: Document saved successfully")
                print(f"📧 Email: {saved_doc.get('email')}")
                print(f"⏰ Subscribed: {saved_doc.get('subscribed_at')}")
                print(f"📍 Status: {saved_doc.get('status')}")
                print(f"🔗 Source: {saved_doc.get('source')}")
            else:
                print(f"❌ Document not found after insertion!")
        else:
            print(f"❌ Failed to insert subscription")
        
        # Get total count
        total_count = await collection.count_documents({})
        print(f"\n📊 Total newsletter subscriptions: {total_count}")
        
        # Close connection
        client.close()
        print(f"\n✅ Direct database test completed successfully")
        
    except Exception as e:
        print(f"❌ Error in direct database test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_subscription_directly())
