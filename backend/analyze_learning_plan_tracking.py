#!/usr/bin/env python3
"""
Deep analysis of learning plan session tracking vs conversation session tracking
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection details from Railway
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

# Target user details
TARGET_USER_EMAIL = "alipala.ist@gmail.com"
TARGET_USER_ID = "688921c268819565ef1ce3dc"

async def analyze_learning_plan_tracking():
    """Analyze the learning plan session tracking mechanism"""
    
    print("=" * 80)
    print("🔍 DEEP ANALYSIS: LEARNING PLAN SESSION TRACKING")
    print("=" * 80)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        database = client[DATABASE_NAME]
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Get collections
        users_collection = database.users
        conversation_sessions_collection = database.conversation_sessions
        learning_plans_collection = database.learning_plans
        
        # Get user
        user = await users_collection.find_one({"_id": ObjectId(TARGET_USER_ID)})
        if not user:
            print("❌ User not found")
            return
        
        print(f"👤 User: {user.get('email')} ({user.get('name')})")
        print()
        
        # Get learning plan
        learning_plan = await learning_plans_collection.find_one({"user_id": TARGET_USER_ID})
        if not learning_plan:
            print("❌ No learning plan found")
            return
        
        print("📚 LEARNING PLAN DETAILS")
        print("-" * 40)
        print(f"Plan ID: {learning_plan.get('id')}")
        print(f"Language: {learning_plan.get('language')}")
        print(f"Level: {learning_plan.get('proficiency_level')}")
        print(f"Completed Sessions: {learning_plan.get('completed_sessions', 0)}")
        print(f"Total Sessions: {learning_plan.get('total_sessions', 0)}")
        print(f"Progress: {learning_plan.get('progress_percentage', 0):.1f}%")
        print()
        
        # Analyze session summaries
        session_summaries = learning_plan.get('session_summaries', [])
        print(f"📝 SESSION SUMMARIES ({len(session_summaries)} found)")
        print("-" * 40)
        
        total_learning_plan_minutes = 0
        for i, summary in enumerate(session_summaries, 1):
            print(f"Session {i}:")
            if isinstance(summary, dict):
                completed_at = summary.get('completed_at', 'N/A')
                summary_text = summary.get('summary', 'No summary')[:50] + "..."
                duration = summary.get('duration_minutes', 0)
                total_learning_plan_minutes += duration
                
                print(f"  Date: {completed_at}")
                print(f"  Duration: {duration} minutes")
                print(f"  Summary: {summary_text}")
            else:
                # Handle string summaries
                print(f"  Summary (string): {str(summary)[:50]}...")
                print(f"  Duration: Unknown (string format)")
            print()
        
        print(f"Total Learning Plan Minutes: {total_learning_plan_minutes}")
        print()
        
        # Analyze weekly schedule
        weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
        print(f"📅 WEEKLY SCHEDULE ({len(weekly_schedule)} weeks)")
        print("-" * 40)
        
        total_weekly_sessions = 0
        for i, week in enumerate(weekly_schedule, 1):
            sessions_completed = week.get('sessions_completed', 0)
            total_weekly_sessions += sessions_completed
            session_details = week.get('session_details', [])
            
            print(f"Week {i}: {sessions_completed}/2 sessions completed")
            if session_details:
                for detail in session_details:
                    session_num = detail.get('session_number', 'N/A')
                    duration = detail.get('duration_minutes', 0)
                    completed_at = detail.get('completed_at', 'N/A')
                    print(f"  Session {session_num}: {duration}min at {completed_at}")
            print()
        
        print(f"Total Weekly Schedule Sessions: {total_weekly_sessions}")
        print()
        
        # Compare with conversation sessions
        conversation_sessions = await conversation_sessions_collection.find({"user_id": TARGET_USER_ID}).to_list(length=None)
        print(f"💬 CONVERSATION SESSIONS ({len(conversation_sessions)} found)")
        print("-" * 40)
        
        total_conversation_minutes = 0
        for session in conversation_sessions:
            duration = session.get('duration_minutes', 0)
            total_conversation_minutes += duration
            created_at = session.get('created_at', 'N/A')
            language = session.get('language', 'N/A')
            level = session.get('level', 'N/A')
            topic = session.get('topic', 'N/A')
            
            print(f"Session: {duration}min - {language}/{level}/{topic} at {created_at}")
        
        print(f"Total Conversation Minutes: {total_conversation_minutes}")
        print()
        
        # ANALYSIS SUMMARY
        print("🔍 ROOT CAUSE ANALYSIS")
        print("=" * 80)
        
        print("FINDINGS:")
        print(f"1. Learning Plan Sessions: {learning_plan.get('completed_sessions', 0)} sessions")
        print(f"2. Session Summaries: {len(session_summaries)} summaries")
        print(f"3. Weekly Schedule Sessions: {total_weekly_sessions} sessions")
        print(f"4. Conversation Sessions: {len(conversation_sessions)} sessions")
        print(f"5. User DB Sessions Used: {user.get('practice_sessions_used', 0)}")
        print(f"6. User DB Minutes Used: {user.get('practice_minutes_used', 0.0):.1f}")
        print()
        
        print("MINUTE TRACKING BREAKDOWN:")
        print(f"- Learning Plan Minutes: {total_learning_plan_minutes}")
        print(f"- Conversation Minutes: {total_conversation_minutes}")
        print(f"- Total Expected: {total_learning_plan_minutes + total_conversation_minutes}")
        print(f"- DB Tracked Minutes: {user.get('practice_minutes_used', 0.0):.1f}")
        print()
        
        print("ROOT CAUSE IDENTIFIED:")
        print("🎯 The issue is that LEARNING PLAN SESSIONS are tracked separately!")
        print()
        print("EXPLANATION:")
        print("1. User completed 6 learning plan sessions (stored in learning_plans collection)")
        print("2. User completed 1 regular conversation session (stored in conversation_sessions collection)")
        print("3. The system shows 7 sessions used (6 learning + 1 conversation)")
        print("4. But only ~13 minutes are tracked, which suggests:")
        print("   - Learning plan sessions may not be properly tracking minutes")
        print("   - OR there's a bug in the minute tracking logic")
        print("   - OR learning plan sessions are shorter than expected")
        print()
        
        print("VERIFICATION:")
        if total_learning_plan_minutes + total_conversation_minutes > user.get('practice_minutes_used', 0.0):
            print("❌ CONFIRMED BUG: Total session minutes exceed tracked minutes")
            print(f"   Expected: {total_learning_plan_minutes + total_conversation_minutes:.1f} minutes")
            print(f"   Tracked: {user.get('practice_minutes_used', 0.0):.1f} minutes")
            print(f"   Missing: {(total_learning_plan_minutes + total_conversation_minutes) - user.get('practice_minutes_used', 0.0):.1f} minutes")
        else:
            print("✅ Minutes tracking appears consistent")
        
        print()
        print("NEXT STEPS:")
        print("1. Check learning_routes.py for learning plan session saving logic")
        print("2. Verify if learning plan sessions call track_speaking_time()")
        print("3. Check if there's double-counting or missing tracking")
        print("4. Look for timing issues in the session completion flow")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(analyze_learning_plan_tracking())
