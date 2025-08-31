#!/usr/bin/env python3
"""
Focused search for conversation sessions in learning_plans collection
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def focused_session_search():
    """Focus on learning_plans collection to find the 11 sessions"""
    
    print("🔍 FOCUSED SEARCH: LEARNING_PLANS COLLECTION")
    print("=" * 60)
    
    # Railway production MongoDB URL for Taco DB
    MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    DATABASE_NAME = "language_tutor"
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print(f"📧 Email: alipala.ist@gmail.com")
    print()
    
    total_minutes = 0.0
    total_sessions = 0
    dutch_sessions = 0
    english_sessions = 0
    
    # Focus on learning_plans collection
    print("🎓 SEARCHING LEARNING_PLANS COLLECTION:")
    print("-" * 50)
    
    # Try both user_id formats
    learning_plans = []
    
    # Try string user_id first
    plans_string = await db.learning_plans.find({"user_id": user_id}).to_list(None)
    if plans_string:
        learning_plans = plans_string
        print(f"✅ Found {len(plans_string)} learning plans with string user_id")
    else:
        # Try ObjectId user_id
        plans_object = await db.learning_plans.find({"user_id": user_object_id}).to_list(None)
        if plans_object:
            learning_plans = plans_object
            print(f"✅ Found {len(plans_object)} learning plans with ObjectId user_id")
        else:
            print("❌ No learning plans found with either user_id format")
    
    if not learning_plans:
        print("❌ NO LEARNING PLANS FOUND!")
        client.close()
        return
    
    print(f"\n📚 ANALYZING {len(learning_plans)} LEARNING PLANS:")
    print("=" * 60)
    
    for i, plan in enumerate(learning_plans, 1):
        plan_id = plan.get('_id')
        plan_name = plan.get('name', f'Plan {i}')
        language = plan.get('language', 'Unknown')
        level = plan.get('level', 'Unknown')
        sessions = plan.get('sessions', [])
        
        print(f"\n📋 Plan {i}: {plan_name}")
        print(f"   ID: {plan_id}")
        print(f"   Language: {language}")
        print(f"   Level: {level}")
        print(f"   Total sessions in plan: {len(sessions)}")
        
        completed_sessions = 0
        plan_minutes = 0.0
        
        for j, session in enumerate(sessions):
            if session.get('completed_at'):
                completed_sessions += 1
                
                # Calculate session duration
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
                
                # Calculate from messages if no duration
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
                
                # Count session
                total_sessions += 1
                plan_minutes += duration
                total_minutes += duration
                
                # Count by language
                if 'dutch' in language.lower():
                    dutch_sessions += 1
                elif 'english' in language.lower():
                    english_sessions += 1
                
                completed_at = session.get('completed_at')
                print(f"      ✅ Session {j+1}: {duration:.2f} min on {completed_at}")
                if duration_source:
                    print(f"         Duration source: {duration_source}")
                
                # Show some message info if available
                if 'messages' in session:
                    msg_count = len(session['messages'])
                    print(f"         Messages: {msg_count}")
        
        print(f"   📊 Completed sessions: {completed_sessions}")
        print(f"   ⏱️  Total minutes: {plan_minutes:.2f}")
    
    # Also check conversation_sessions collection
    print(f"\n💬 CHECKING CONVERSATION_SESSIONS COLLECTION:")
    print("-" * 50)
    
    conv_sessions = await db.conversation_sessions.find({"user_id": user_object_id}).to_list(None)
    if not conv_sessions:
        conv_sessions = await db.conversation_sessions.find({"user_id": user_id}).to_list(None)
    
    print(f"Found {len(conv_sessions)} standalone conversation sessions")
    for i, session in enumerate(conv_sessions):
        duration = session.get('duration', 0.0)
        created_at = session.get('created_at', 'Unknown')
        total_minutes += duration
        total_sessions += 1
        print(f"   Session {i+1}: {duration:.2f} min on {created_at}")
    
    print(f"\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print("=" * 60)
    print(f"🎯 TOTAL CONVERSATION MINUTES: {total_minutes:.2f}")
    print(f"📊 TOTAL CONVERSATION SESSIONS: {total_sessions}")
    print(f"🇳🇱 Dutch sessions: {dutch_sessions}")
    print(f"🇬🇧 English sessions: {english_sessions}")
    print()
    
    # Compare with expected
    expected_sessions = 11  # 10 Dutch + 1 English B2
    print("🔍 COMPARISON WITH SCREENSHOT:")
    print(f"   Expected: {expected_sessions} sessions (10 Dutch + 1 English B2)")
    print(f"   Found: {total_sessions} sessions")
    print(f"   Dutch found: {dutch_sessions} (expected: 10)")
    print(f"   English found: {english_sessions} (expected: 1)")
    
    if total_sessions == expected_sessions:
        print("   ✅ SESSION COUNT MATCHES SCREENSHOT!")
    else:
        print("   ❌ SESSION COUNT MISMATCH!")
        print(f"   Difference: {expected_sessions - total_sessions} sessions")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(focused_session_search())
