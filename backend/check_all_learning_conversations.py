#!/usr/bin/env python3
"""
Check all conversation minutes from learning plan sessions for a specific user
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def check_all_learning_conversations():
    """Check all conversation minutes from learning plan sessions"""
    
    print("🔍 CHECKING ALL LEARNING PLAN CONVERSATION MINUTES")
    print("=" * 60)
    
    # Connect to production MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print()
    
    # Get user info
    user = await db.users.find_one({"_id": user_object_id})
    if user:
        print(f"📧 Email: {user.get('email', 'N/A')}")
        print(f"📊 Current recorded usage:")
        print(f"   - Sessions used: {user.get('practice_sessions_used', 0)}")
        print(f"   - Minutes used: {user.get('practice_minutes_used', 0.0):.2f}")
        print()
    
    # Get all learning plans for this user
    learning_plans = await db.learning_plans.find({"user_id": user_object_id}).to_list(None)
    
    total_conversation_minutes = 0.0
    total_sessions_with_conversations = 0
    
    print(f"🎓 FOUND {len(learning_plans)} LEARNING PLANS")
    print()
    
    for i, plan in enumerate(learning_plans, 1):
        plan_name = plan.get('name', f'Plan {i}')
        print(f"📋 Plan {i}: {plan_name}")
        print(f"   Plan ID: {plan['_id']}")
        
        # Get all sessions for this learning plan
        sessions = plan.get('sessions', [])
        plan_conversation_minutes = 0.0
        plan_sessions_with_conversations = 0
        
        print(f"   📊 Total sessions in plan: {len(sessions)}")
        
        for j, session in enumerate(sessions):
            session_date = session.get('completed_at')
            if session_date:
                # Check if this session has conversation data
                conversation_duration = 0.0
                
                # Check for conversation_duration field
                if 'conversation_duration' in session:
                    conversation_duration = float(session['conversation_duration'])
                
                # Check for duration field (might be total duration)
                elif 'duration' in session:
                    conversation_duration = float(session['duration'])
                
                # Check for conversation_data with duration
                elif 'conversation_data' in session and session['conversation_data']:
                    conv_data = session['conversation_data']
                    if isinstance(conv_data, dict) and 'duration' in conv_data:
                        conversation_duration = float(conv_data['duration'])
                
                # Check for messages and calculate duration from timestamps
                elif 'messages' in session and session['messages']:
                    messages = session['messages']
                    if len(messages) >= 2:
                        try:
                            first_msg_time = messages[0].get('timestamp')
                            last_msg_time = messages[-1].get('timestamp')
                            if first_msg_time and last_msg_time:
                                if isinstance(first_msg_time, str):
                                    first_time = datetime.fromisoformat(first_msg_time.replace('Z', '+00:00'))
                                else:
                                    first_time = first_msg_time
                                
                                if isinstance(last_msg_time, str):
                                    last_time = datetime.fromisoformat(last_msg_time.replace('Z', '+00:00'))
                                else:
                                    last_time = last_msg_time
                                
                                duration_seconds = (last_time - first_time).total_seconds()
                                conversation_duration = duration_seconds / 60.0  # Convert to minutes
                        except Exception as e:
                            print(f"      ⚠️  Error calculating duration from messages: {e}")
                
                if conversation_duration > 0:
                    plan_conversation_minutes += conversation_duration
                    plan_sessions_with_conversations += 1
                    
                    print(f"      Session {j+1}: {conversation_duration:.2f} min on {session_date}")
        
        print(f"   💬 Sessions with conversations: {plan_sessions_with_conversations}")
        print(f"   ⏱️  Total conversation minutes: {plan_conversation_minutes:.2f}")
        print()
        
        total_conversation_minutes += plan_conversation_minutes
        total_sessions_with_conversations += plan_sessions_with_conversations
    
    # Also check standalone conversation sessions
    print("💬 STANDALONE CONVERSATION SESSIONS:")
    conversation_sessions = await db.conversation_sessions.find({"user_id": user_object_id}).to_list(None)
    
    standalone_conversation_minutes = 0.0
    for session in conversation_sessions:
        duration = session.get('duration', 0.0)
        created_at = session.get('created_at', 'Unknown')
        standalone_conversation_minutes += duration
        print(f"   Session: {duration:.2f} min on {created_at}")
    
    print(f"   Total standalone conversations: {standalone_conversation_minutes:.2f} min")
    print()
    
    # Final totals
    grand_total_minutes = total_conversation_minutes + standalone_conversation_minutes
    
    print("🎯 FINAL TOTALS:")
    print("=" * 40)
    print(f"📚 Learning plan conversation minutes: {total_conversation_minutes:.2f}")
    print(f"💬 Standalone conversation minutes: {standalone_conversation_minutes:.2f}")
    print(f"🎯 GRAND TOTAL CONVERSATION MINUTES: {grand_total_minutes:.2f}")
    print(f"📊 Total sessions with conversations: {total_sessions_with_conversations + len(conversation_sessions)}")
    print()
    
    # Compare with user record
    recorded_minutes = user.get('practice_minutes_used', 0.0) if user else 0.0
    print("🔍 COMPARISON WITH USER RECORD:")
    print(f"   Recorded in user: {recorded_minutes:.2f} min")
    print(f"   Actual calculated: {grand_total_minutes:.2f} min")
    print(f"   Difference: {abs(recorded_minutes - grand_total_minutes):.2f} min")
    
    if abs(recorded_minutes - grand_total_minutes) < 0.01:
        print("   ✅ MATCH!")
    else:
        print("   ❌ MISMATCH!")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(check_all_learning_conversations())
