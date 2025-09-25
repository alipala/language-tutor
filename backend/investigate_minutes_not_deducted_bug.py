#!/usr/bin/env python3

"""
🚨 CRITICAL BUG INVESTIGATION: Minutes Not Being Deducted

User completed 5-minute session but logs show:
- "Minutes used: 0.0" 
- Frontend shows 150/150 minutes (should be 145/150)
- Session count incremented correctly (1 session)
- But minutes not deducted

This suggests the session duration tracking is broken.
"""

import os
import sys
sys.path.append('/Users/alipala/CascadeProjects/language-tutor/backend')

import asyncio
from database import database
from bson import ObjectId
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def investigate_minutes_bug():
    """Investigate why minutes are not being deducted from user account"""
    
    print("🚨 INVESTIGATING MINUTES NOT DEDUCTED BUG")
    print("=" * 60)
    
    # User ID from logs
    user_id = "688921c268819565ef1ce3dc"
    
    try:
        if database is None:
            print("❌ Database connection not available!")
            return
            
        print(f"\n1. 👤 USER ACCOUNT STATUS")
        print("-" * 40)
        
        # Check user account
        user = await database.users.find_one({"_id": ObjectId(user_id)})
        if user:
            print(f"✅ User found: {user.get('email', 'No email')}")
            print(f"📊 Plan: {user.get('subscription_plan', 'No plan')}")
            print(f"⏱️  Minutes used: {user.get('minutes_used', 'Not set')}")
            print(f"🎯 Sessions used: {user.get('sessions_used', 'Not set')}")
            print(f"📝 Assessments used: {user.get('assessments_used', 'Not set')}")
        else:
            print(f"❌ User not found!")
            return
            
        print(f"\n2. 📚 LEARNING PLAN SESSIONS")
        print("-" * 40)
        
        # Check learning plan sessions (most recent first)
        learning_plans = []
        async for plan in database.learning_plans.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5):
            learning_plans.append(plan)
        
        print(f"📊 Found {len(learning_plans)} learning plans")
        
        for i, plan in enumerate(learning_plans):
            print(f"\n📋 Learning Plan {i+1}:")
            print(f"   ID: {plan['_id']}")
            print(f"   Language: {plan.get('language', 'Unknown')}")
            print(f"   Level: {plan.get('level', 'Unknown')}")
            print(f"   Created: {plan.get('created_at', 'Unknown')}")
            print(f"   Status: {plan.get('status', 'Unknown')}")
            print(f"   Duration: {plan.get('duration_minutes', 'Not set')} minutes")
            print(f"   Completed: {plan.get('completed_at', 'Not completed')}")
            
            # Check if this plan has sessions
            sessions = []
            async for session in database.learning_plan_sessions.find(
                {"learning_plan_id": str(plan['_id'])}
            ).sort("created_at", -1):
                sessions.append(session)
            
            print(f"   🎯 Sessions: {len(sessions)}")
            
            for j, session in enumerate(sessions):
                print(f"      Session {j+1}:")
                print(f"         ID: {session['_id']}")
                print(f"         Created: {session.get('created_at', 'Unknown')}")
                print(f"         Duration: {session.get('duration_minutes', 'Not set')} minutes")
                print(f"         Status: {session.get('status', 'Unknown')}")
                print(f"         Completed: {session.get('completed_at', 'Not completed')}")
        
        print(f"\n3. 💬 CONVERSATION SESSIONS")
        print("-" * 40)
        
        # Check conversation sessions
        conversations = []
        async for conv in database.conversations.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5):
            conversations.append(conv)
        
        print(f"📊 Found {len(conversations)} conversations")
        
        for i, conv in enumerate(conversations):
            print(f"\n💬 Conversation {i+1}:")
            print(f"   ID: {conv['_id']}")
            print(f"   Language: {conv.get('language', 'Unknown')}")
            print(f"   Created: {conv.get('created_at', 'Unknown')}")
            print(f"   Duration: {conv.get('duration_minutes', 'Not set')} minutes")
            print(f"   Status: {conv.get('status', 'Unknown')}")
            print(f"   Completed: {conv.get('completed_at', 'Not completed')}")
        
        print(f"\n4. 🔍 RECENT DATABASE ACTIVITY")
        print("-" * 40)
        
        # Check for any recent updates to user account
        recent_time = datetime.utcnow() - timedelta(hours=1)
        
        # This is a simplified check - in production you'd need to check oplog
        print(f"⏰ Checking activity since: {recent_time}")
        print(f"📊 Current user minutes_used: {user.get('minutes_used', 0)}")
        print(f"🎯 Current user sessions_used: {user.get('sessions_used', 0)}")
        
        print(f"\n5. 🚨 ROOT CAUSE ANALYSIS")
        print("-" * 40)
        
        # Analyze the issue
        total_learning_plan_minutes = 0
        total_conversation_minutes = 0
        
        for plan in learning_plans:
            sessions = []
            async for session in database.learning_plan_sessions.find(
                {"learning_plan_id": str(plan['_id'])}
            ):
                sessions.append(session)
            for session in sessions:
                duration = session.get('duration_minutes', 0)
                if duration:
                    total_learning_plan_minutes += duration
        
        for conv in conversations:
            duration = conv.get('duration_minutes', 0)
            if duration:
                total_conversation_minutes += duration
        
        total_calculated_minutes = total_learning_plan_minutes + total_conversation_minutes
        stored_minutes_used = user.get('minutes_used', 0)
        
        print(f"📊 CALCULATION SUMMARY:")
        print(f"   Learning plan minutes: {total_learning_plan_minutes}")
        print(f"   Conversation minutes: {total_conversation_minutes}")
        print(f"   Total calculated: {total_calculated_minutes}")
        print(f"   Stored in user account: {stored_minutes_used}")
        print(f"   DISCREPANCY: {total_calculated_minutes - stored_minutes_used} minutes")
        
        if total_calculated_minutes != stored_minutes_used:
            print(f"\n🚨 BUG CONFIRMED: Minutes calculation is incorrect!")
            print(f"   Expected: {total_calculated_minutes} minutes used")
            print(f"   Actual: {stored_minutes_used} minutes used")
            print(f"   Frontend shows: 150 - {stored_minutes_used} = {150 - stored_minutes_used} remaining")
            print(f"   Should show: 150 - {total_calculated_minutes} = {150 - total_calculated_minutes} remaining")
        else:
            print(f"\n✅ Minutes calculation appears correct in database")
            print(f"   Issue might be in the subscription status calculation logic")
        
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_minutes_bug())
