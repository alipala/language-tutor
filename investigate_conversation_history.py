#!/usr/bin/env python3
"""
Investigation script for conversation history saving issue
"""

import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend directory - prioritize .env.local for development
load_dotenv("backend/.env.local")

async def investigate_conversation_history():
    """Investigate conversation history for starfish84itu@gmail.com"""
    try:
        # Get MongoDB connection string
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("❌ MONGODB_URL not found in environment variables")
            return
        
        print(f"🔗 Connecting to MongoDB...")
        print(f"🔍 Investigating conversation history for: starfish84itu@gmail.com")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        database = client["language_tutor_local"]
        
        # Get collections
        users_collection = database["users"]
        conversation_sessions_collection = database["conversation_sessions"]
        learning_plans_collection = database["learning_plans"]
        
        # Find the user
        user = await users_collection.find_one({"email": "starfish84itu@gmail.com"})
        
        if not user:
            print("❌ User not found in database")
            return
        
        user_id = str(user.get("_id"))
        print(f"✅ Found user: {user.get('name', 'Unknown')} (ID: {user_id})")
        
        # Check conversation sessions for this user
        print(f"\n📋 CONVERSATION SESSIONS:")
        print("-" * 80)
        
        cursor = conversation_sessions_collection.find({"user_id": user_id}).sort("created_at", -1)
        session_count = 0
        
        async for session in cursor:
            session_count += 1
            session_id = session.get("session_id", "N/A")
            created_at = session.get("created_at", "N/A")
            conversation_type = session.get("conversation_type", "N/A")
            source = session.get("source", "N/A")
            language = session.get("language", "N/A")
            level = session.get("level", "N/A")
            topic = session.get("topic", "N/A")
            learning_plan_id = session.get("learning_plan_id", None)
            
            # Format timestamp
            if isinstance(created_at, datetime):
                formatted_time = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                formatted_time = str(created_at)
            
            print(f"📝 Session {session_count}:")
            print(f"   ID: {session_id}")
            print(f"   Created: {formatted_time}")
            print(f"   Type: {conversation_type}")
            print(f"   Source: {source}")
            print(f"   Language: {language}")
            print(f"   Level: {level}")
            print(f"   Topic: {topic}")
            print(f"   Learning Plan ID: {learning_plan_id}")
            print(f"   Has Learning Plan: {'YES' if learning_plan_id else 'NO'}")
            print("-" * 40)
        
        print(f"\n📊 Total conversation sessions: {session_count}")
        
        # Check learning plans for this user
        print(f"\n📚 LEARNING PLANS:")
        print("-" * 80)
        
        cursor = learning_plans_collection.find({"user_id": user_id}).sort("created_at", -1)
        plan_count = 0
        
        async for plan in cursor:
            plan_count += 1
            plan_id = plan.get("id", "N/A")
            title = plan.get("title", "N/A")
            created_at = plan.get("created_at", "N/A")
            completed_sessions = plan.get("completed_sessions", 0)
            total_sessions = plan.get("total_sessions", 0)
            
            # Format timestamp
            if isinstance(created_at, datetime):
                formatted_time = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                formatted_time = str(created_at)
            
            print(f"📚 Learning Plan {plan_count}:")
            print(f"   ID: {plan_id}")
            print(f"   Title: {title}")
            print(f"   Created: {formatted_time}")
            print(f"   Progress: {completed_sessions}/{total_sessions} sessions")
            print("-" * 40)
        
        print(f"\n📊 Total learning plans: {plan_count}")
        
        # Analyze the issue
        print(f"\n🔍 ANALYSIS:")
        print("-" * 80)
        
        # Count sessions by type
        practice_sessions = await conversation_sessions_collection.count_documents({
            "user_id": user_id,
            "learning_plan_id": {"$exists": False}
        })
        
        learning_plan_sessions = await conversation_sessions_collection.count_documents({
            "user_id": user_id,
            "learning_plan_id": {"$exists": True, "$ne": None}
        })
        
        print(f"📈 Practice Mode Sessions (should be in history): {practice_sessions}")
        print(f"📈 Learning Plan Sessions (should NOT be in history): {learning_plan_sessions}")
        
        if learning_plan_sessions > 0:
            print(f"⚠️  ISSUE FOUND: {learning_plan_sessions} learning plan sessions are being saved!")
            print(f"   These should NOT appear in conversation history.")
        else:
            print(f"✅ No learning plan sessions found in conversation history.")
        
        # Close connection
        client.close()
        print(f"\n✅ Investigation completed successfully")
        
    except Exception as e:
        print(f"❌ Error during investigation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_conversation_history())
