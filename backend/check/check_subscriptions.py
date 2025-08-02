#!/usr/bin/env python3
"""
Script to check newsletter subscriptions in MongoDB
"""

import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend directory - prioritize .env.local for development
load_dotenv("backend/.env.local")

async def check_subscriptions():
    """Check the newsletter_subscriptions collection"""
    try:
        # Get MongoDB connection string
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("❌ MONGODB_URL not found in environment variables")
            return
        
        print(f"🔗 Connecting to MongoDB...")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        database = client["language_tutor_local"]  # Use local database
        collection = database["newsletter_subscriptions"]
        
        # Get total count
        total_count = await collection.count_documents({})
        print(f"📊 Total newsletter subscriptions: {total_count}")
        
        if total_count == 0:
            print("📭 No subscriptions found in the collection")
            return
        
        # Get all subscriptions
        print(f"\n📋 Recent subscriptions:")
        print("-" * 80)
        
        cursor = collection.find({}).sort("subscribed_at", -1).limit(10)
        
        async for doc in cursor:
            email = doc.get("email", "N/A")
            subscribed_at = doc.get("subscribed_at", "N/A")
            status = doc.get("status", "N/A")
            source = doc.get("source", "N/A")
            
            # Format timestamp
            if isinstance(subscribed_at, datetime):
                formatted_time = subscribed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                formatted_time = str(subscribed_at)
            
            print(f"📧 Email: {email}")
            print(f"⏰ Subscribed: {formatted_time}")
            print(f"📍 Status: {status}")
            print(f"🔗 Source: {source}")
            print("-" * 40)
        
        # Get subscription stats by source
        print(f"\n📈 Subscription sources:")
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        async for result in collection.aggregate(pipeline):
            source = result.get("_id", "Unknown")
            count = result.get("count", 0)
            print(f"  {source}: {count} subscriptions")
        
        # Close connection
        client.close()
        print(f"\n✅ Database check completed successfully")
        
    except Exception as e:
        print(f"❌ Error checking subscriptions: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_subscriptions())
