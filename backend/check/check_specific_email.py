#!/usr/bin/env python3
"""
Script to check for a specific email in newsletter subscriptions
"""

import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv("backend/.env")

async def check_specific_email(email_to_check):
    """Check if a specific email is in the newsletter_subscriptions collection"""
    try:
        # Get MongoDB connection string
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("❌ MONGODB_URL not found in environment variables")
            return
        
        print(f"🔗 Connecting to MongoDB...")
        print(f"🔍 Searching for email: {email_to_check}")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        database = client["language_tutor"]
        collection = database["newsletter_subscriptions"]
        
        # Search for the specific email
        subscription = await collection.find_one({"email": email_to_check})
        
        if subscription:
            print(f"✅ EMAIL FOUND!")
            print("-" * 60)
            
            email = subscription.get("email", "N/A")
            subscribed_at = subscription.get("subscribed_at", "N/A")
            status = subscription.get("status", "N/A")
            source = subscription.get("source", "N/A")
            
            # Format timestamp
            if isinstance(subscribed_at, datetime):
                formatted_time = subscribed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                formatted_time = str(subscribed_at)
            
            print(f"📧 Email: {email}")
            print(f"⏰ Subscribed: {formatted_time}")
            print(f"📍 Status: {status}")
            print(f"🔗 Source: {source}")
            print("-" * 60)
        else:
            print(f"❌ EMAIL NOT FOUND")
            print(f"The email '{email_to_check}' is not in the newsletter subscriptions.")
        
        # Also show total count for context
        total_count = await collection.count_documents({})
        print(f"\n📊 Total newsletter subscriptions in database: {total_count}")
        
        # Show all emails for reference
        if total_count > 0:
            print(f"\n📋 All subscribed emails:")
            cursor = collection.find({}, {"email": 1, "subscribed_at": 1}).sort("subscribed_at", -1)
            
            async for doc in cursor:
                email = doc.get("email", "N/A")
                subscribed_at = doc.get("subscribed_at", "N/A")
                
                if isinstance(subscribed_at, datetime):
                    formatted_time = subscribed_at.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_time = str(subscribed_at)
                
                print(f"  • {email} ({formatted_time})")
        
        # Close connection
        client.close()
        print(f"\n✅ Database check completed successfully")
        
    except Exception as e:
        print(f"❌ Error checking email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    email_to_search = "starfish84itu@gmail.com"
    asyncio.run(check_specific_email(email_to_search))
