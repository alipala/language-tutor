#!/usr/bin/env python3
"""
Find all conversation data for user based on backfill and session count fix details
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def find_conversation_data():
    """Find conversation data based on user record details"""
    
    print("🔍 FINDING CONVERSATION DATA BASED ON USER RECORD")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print()
    
    # Get user record first
    user = await db.users.find_one({"_id": user_object_id})
    if not user:
        print("❌ User not found!")
        return
    
    print("📋 USER RECORD DETAILS:")
    print(f"   Email: {user.get('email')}")
    print(f"   Current usage: {user.get('practice_minutes_used', 0)} min, {user.get('practice_sessions_used', 0)} sessions")
    
    # Show backfill details
    if 'backfill_details' in user:
        backfill = user['backfill_details']
        print(f"\n📊 BACKFILL DETAILS (what should exist):")
        print(f"   Learning plan sessions: {backfill.get('learning_plan_sessions', 0)}")
        print(f"   Conversation minutes: {backfill.get('conversation_minutes', 0)}")
        print(f"   Total minutes: {backfill.get('total_minutes', 0)}")
    
    # Show session count fix details
    if 'session_count_fix_details' in user:
        fix_details = user['session_count_fix_details']
        print(f"\n🔧 SESSION COUNT FIX DETAILS (what should exist):")
        print(f"   Learning plan sessions: {fix_details.get('learning_plan_sessions', 0)}")
        print(f"   Conversation sessions: {fix_details.get('conversation_sessions', 0)}")
        print(f"   Conversation minutes: {fix_details.get('conversation_minutes', 0)}")
        print(f"   Total sessions: {fix_details.get('total_sessions', 0)}")
        print(f"   Total minutes: {fix_details.get('total_minutes', 0)}")
    
    print("\n" + "="*60)
    print("🔍 SEARCHING FOR ACTUAL DATA IN DATABASE:")
    print("="*60)
    
    total_found_minutes = 0.0
    total_found_sessions = 0
    
    # 1. Check conversation_sessions collection
    print("\n💬 CONVERSATION_SESSIONS COLLECTION:")
    conv_sessions = await db.conversation_sessions.find({"user_id": user_object_id}).to_list(None)
    if not conv_sessions:
        # Try string user_id
        conv_sessions = await db.conversation_sessions.find({"user_id": user_id}).to_list(None)
    
    print(f"   Found {len(conv_sessions)} conversation sessions")
    for i, session in enumerate(conv_sessions):
        duration = session.get('duration', 0.0)
        created_at = session.get('created_at', 'Unknown')
        total_found_minutes += duration
        total_found_sessions += 1
        print(f"      Session {i+1}: {duration:.2f} min on {created_at}")
    
    # 2. Check learning_plans collection with string user_id
    print("\n🎓 LEARNING_PLANS COLLECTION:")
    learning_plans = await db.learning_plans.find({"user_id": user_id}).to_list(None)
    print(f"   Found {len(learning_plans)} learning plans")
    
    for i, plan in enumerate(learning_plans):
        plan_name = plan.get('name', f'Plan {i+1}')
        sessions = plan.get('sessions', [])
        print(f"\n   📋 Plan {i+1}: {plan_name}")
        print(f"      Plan ID: {plan['_id']}")
        print(f"      Total sessions: {len(sessions)}")
        
        plan_minutes = 0.0
        plan_sessions = 0
        
        for j, session in enumerate(sessions):
            if session.get('completed_at'):
                # Look for duration in various places
                duration = 0.0
                duration_source = ""
                
                if 'conversation_duration' in session:
                    duration = float(session['conversation_duration'])
                    duration_source = "conversation_duration"
                elif 'duration' in session:
                    duration = float(session['duration'])
                    duration_source = "duration"
                elif 'conversation_data' in session and session['conversation_data']:
                    conv_data = session['conversation_data']
                    if isinstance(conv_data, dict) and 'duration' in conv_data:
                        duration = float(conv_data['duration'])
                        duration_source = "conversation_data.duration"
                
                # Calculate from messages if no duration found
                if duration == 0 and 'messages' in session and len(session['messages']) >= 2:
                    try:
                        messages = session['messages']
                        first_time = messages[0].get('timestamp')
                        last_time = messages[-1].get('timestamp')
                        if first_time and last_time:
                            if isinstance(first_time, str):
                                first_dt = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                            else:
                                first_dt = first_time
                            
                            if isinstance(last_time, str):
                                last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                            else:
                                last_dt = last_time
                            
                            duration = (last_dt - first_dt).total_seconds() / 60.0
                            duration_source = "calculated_from_messages"
                    except Exception as e:
                        pass
                
                if duration > 0:
                    plan_minutes += duration
                    plan_sessions += 1
                    total_found_minutes += duration
                    total_found_sessions += 1
                    print(f"         Session {j+1}: {duration:.2f} min on {session.get('completed_at')} ({duration_source})")
        
        print(f"      Plan total: {plan_sessions} sessions, {plan_minutes:.2f} minutes")
    
    # 3. Check sessions collection (might be separate)
    print("\n📊 SESSIONS COLLECTION:")
    sessions_coll = await db.sessions.find({"user_id": user_object_id}).to_list(None)
    if not sessions_coll:
        sessions_coll = await db.sessions.find({"user_id": user_id}).to_list(None)
    
    print(f"   Found {len(sessions_coll)} sessions")
    for i, session in enumerate(sessions_coll):
        duration = session.get('duration', 0.0)
        if duration > 0:
            total_found_minutes += duration
            total_found_sessions += 1
            created_at = session.get('created_at', session.get('timestamp', 'Unknown'))
            print(f"      Session {i+1}: {duration:.2f} min on {created_at}")
    
    print("\n" + "="*60)
    print("🎯 FINAL RESULTS:")
    print("="*60)
    print(f"🎯 TOTAL CONVERSATION MINUTES FOUND: {total_found_minutes:.2f}")
    print(f"📊 TOTAL CONVERSATION SESSIONS FOUND: {total_found_sessions}")
    
    # Compare with expected from user record
    expected_minutes = 0.0
    expected_sessions = 0
    
    if 'session_count_fix_details' in user:
        fix_details = user['session_count_fix_details']
        expected_minutes = fix_details.get('total_minutes', 0)
        expected_sessions = fix_details.get('total_sessions', 0)
    elif 'backfill_details' in user:
        backfill = user['backfill_details']
        expected_minutes = backfill.get('total_minutes', 0)
        expected_sessions = backfill.get('learning_plan_sessions', 0) + 1  # +1 for conversation
    
    print(f"\n🔍 COMPARISON:")
    print(f"   Expected minutes: {expected_minutes}")
    print(f"   Expected sessions: {expected_sessions}")
    print(f"   Found minutes: {total_found_minutes:.2f}")
    print(f"   Found sessions: {total_found_sessions}")
    print(f"   Minutes difference: {abs(expected_minutes - total_found_minutes):.2f}")
    print(f"   Sessions difference: {abs(expected_sessions - total_found_sessions)}")
    
    if abs(expected_minutes - total_found_minutes) < 0.1:
        print("   ✅ MINUTES MATCH!")
    else:
        print("   ❌ MINUTES MISMATCH!")
    
    if expected_sessions == total_found_sessions:
        print("   ✅ SESSIONS MATCH!")
    else:
        print("   ❌ SESSIONS MISMATCH!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(find_conversation_data())
