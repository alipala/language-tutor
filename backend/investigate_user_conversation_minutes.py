#!/usr/bin/env python3
"""
Investigate user conversation minutes across all collections
User ID: 688921c268819565ef1ce3dc
Learning Plan IDs provided by user
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def investigate_user_conversation_minutes():
    """Investigate conversation minutes for specific user and learning plans"""
    
    print("🔍 INVESTIGATING USER CONVERSATION MINUTES")
    print("=" * 70)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    # Learning plan IDs provided by user
    learning_plan_ids = [
        "688b531449449925afb0d481",
        "68976d2223991d68793118ad", 
        "68a03c210b308d5557da1664"
    ]
    
    print(f"👤 User ID: {user_id}")
    print(f"📚 Learning Plan IDs to investigate:")
    for i, plan_id in enumerate(learning_plan_ids, 1):
        print(f"   {i}. {plan_id}")
    print()
    
    total_conversation_minutes = 0.0
    total_sessions = 0
    
    # 1. Check user record first
    print("👤 USER RECORD:")
    print("-" * 50)
    user = await db.users.find_one({"_id": user_object_id})
    if user:
        print(f"   📧 Email: {user.get('email')}")
        print(f"   📊 Current recorded usage:")
        print(f"      - practice_minutes_used: {user.get('practice_minutes_used', 0)}")
        print(f"      - practice_sessions_used: {user.get('practice_sessions_used', 0)}")
        print(f"   📅 Subscription period:")
        print(f"      - Start: {user.get('current_period_start')}")
        print(f"      - End: {user.get('current_period_end')}")
    else:
        print("   ❌ User not found!")
    print()
    
    # 2. Check each learning plan
    print("📚 LEARNING PLANS INVESTIGATION:")
    print("-" * 50)
    
    for i, plan_id in enumerate(learning_plan_ids, 1):
        plan_object_id = ObjectId(plan_id)
        plan = await db.learning_plans.find_one({"_id": plan_object_id})
        
        if not plan:
            print(f"   ❌ Plan {i} ({plan_id}) not found!")
            continue
            
        print(f"   📋 Plan {i}: {plan.get('name', 'Unnamed')}")
        print(f"      ID: {plan_id}")
        print(f"      Language: {plan.get('language', 'Unknown')}")
        print(f"      Level: {plan.get('level', 'Unknown')}")
        print(f"      User ID: {plan.get('user_id')}")
        
        sessions = plan.get('sessions', [])
        print(f"      Total sessions in plan: {len(sessions)}")
        
        plan_minutes = 0.0
        plan_completed_sessions = 0
        
        for j, session in enumerate(sessions):
            if session.get('completed_at'):
                plan_completed_sessions += 1
                
                # Look for conversation duration
                duration = 0.0
                duration_source = ""
                
                # Check various duration fields
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
                    total_conversation_minutes += duration
                    total_sessions += 1
                    
                    completed_at = session.get('completed_at')
                    print(f"         ✅ Session {j+1}: {duration:.2f} min on {completed_at}")
                    print(f"            Source: {duration_source}")
                    
                    # Show message count if available
                    if 'messages' in session:
                        msg_count = len(session['messages'])
                        print(f"            Messages: {msg_count}")
                else:
                    completed_at = session.get('completed_at')
                    print(f"         ⚠️  Session {j+1}: 0.00 min on {completed_at} (no duration data)")
        
        print(f"      📊 Completed sessions: {plan_completed_sessions}")
        print(f"      ⏱️  Total conversation minutes: {plan_minutes:.2f}")
        print()
    
    # 3. Check conversation_sessions collection
    print("💬 CONVERSATION_SESSIONS COLLECTION:")
    print("-" * 50)
    
    # Try both user_id formats
    conv_sessions = await db.conversation_sessions.find({"user_id": user_object_id}).to_list(None)
    if not conv_sessions:
        conv_sessions = await db.conversation_sessions.find({"user_id": user_id}).to_list(None)
    
    print(f"   Found {len(conv_sessions)} standalone conversation sessions")
    
    for i, session in enumerate(conv_sessions):
        duration = session.get('duration', 0.0)
        created_at = session.get('created_at', 'Unknown')
        total_conversation_minutes += duration
        total_sessions += 1
        print(f"      Session {i+1}: {duration:.2f} min on {created_at}")
        
        # Show additional session details
        if 'messages' in session:
            msg_count = len(session.get('messages', []))
            print(f"         Messages: {msg_count}")
    print()
    
    # 4. Check sessions collection (if exists)
    print("📊 SESSIONS COLLECTION:")
    print("-" * 50)
    
    sessions_coll = await db.sessions.find({"user_id": user_object_id}).to_list(None)
    if not sessions_coll:
        sessions_coll = await db.sessions.find({"user_id": user_id}).to_list(None)
    
    print(f"   Found {len(sessions_coll)} sessions in sessions collection")
    
    for i, session in enumerate(sessions_coll):
        duration = session.get('duration', 0.0)
        if duration > 0:
            total_conversation_minutes += duration
            total_sessions += 1
            created_at = session.get('created_at', session.get('timestamp', 'Unknown'))
            print(f"      Session {i+1}: {duration:.2f} min on {created_at}")
    print()
    
    # 5. Final summary
    print("🎯 FINAL INVESTIGATION RESULTS:")
    print("=" * 70)
    print(f"🎯 TOTAL CONVERSATION MINUTES FOUND: {total_conversation_minutes:.2f}")
    print(f"📊 TOTAL CONVERSATION SESSIONS FOUND: {total_sessions}")
    print()
    
    # Compare with user record
    if user:
        recorded_minutes = user.get('practice_minutes_used', 0.0)
        recorded_sessions = user.get('practice_sessions_used', 0)
        
        print("🔍 COMPARISON WITH USER RECORD:")
        print(f"   User record minutes: {recorded_minutes}")
        print(f"   User record sessions: {recorded_sessions}")
        print(f"   Actual found minutes: {total_conversation_minutes:.2f}")
        print(f"   Actual found sessions: {total_sessions}")
        print(f"   Minutes difference: {abs(recorded_minutes - total_conversation_minutes):.2f}")
        print(f"   Sessions difference: {abs(recorded_sessions - total_sessions)}")
        
        if abs(recorded_minutes - total_conversation_minutes) < 0.01:
            print("   ✅ MINUTES MATCH!")
        else:
            print("   ❌ MINUTES MISMATCH!")
        
        if recorded_sessions == total_sessions:
            print("   ✅ SESSIONS MATCH!")
        else:
            print("   ❌ SESSIONS MISMATCH!")
    
    # 6. Check subscription period alignment
    if user and user.get('current_period_start') and user.get('current_period_end'):
        period_start = datetime.fromisoformat(user['current_period_start'].replace('Z', '+00:00'))
        period_end = datetime.fromisoformat(user['current_period_end'].replace('Z', '+00:00'))
        
        print(f"\n📅 SUBSCRIPTION PERIOD ANALYSIS:")
        print(f"   Current period: {period_start.date()} to {period_end.date()}")
        print(f"   Period duration: {(period_end - period_start).days} days")
        
        # Check if sessions fall within current period
        sessions_in_period = 0
        minutes_in_period = 0.0
        
        # This would require checking each session's timestamp against the period
        # For now, just show the period info
        print(f"   Sessions in current period: {sessions_in_period}")
        print(f"   Minutes in current period: {minutes_in_period:.2f}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(investigate_user_conversation_minutes())
