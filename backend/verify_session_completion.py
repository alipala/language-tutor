#!/usr/bin/env python3
"""
Verify that the completed session was properly tracked in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def verify_session_completion():
    """Verify the completed session tracking"""
    
    print("🔍 VERIFYING COMPLETED SESSION TRACKING")
    print("=" * 60)
    print("📊 Expected: Dutch A1 session, 5:57 duration, 41 messages")
    print("👤 User ID: 688921c268819565ef1ce3dc")
    print("📋 Plan ID: e45effa0-38be-4666-8588-fd1d1ce183f0")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    plan_id = "e45effa0-38be-4666-8588-fd1d1ce183f0"
    user_object_id = ObjectId(user_id)
    
    # 1. Check user record for updated usage
    print("👤 CHECKING USER RECORD UPDATES:")
    print("-" * 40)
    user = await db.users.find_one({"_id": user_object_id})
    if user:
        print(f"   📧 Email: {user.get('email')}")
        print(f"   📊 CURRENT USAGE:")
        print(f"      - practice_sessions_used: {user.get('practice_sessions_used', 0)}")
        print(f"      - practice_minutes_used: {user.get('practice_minutes_used', 0.0):.2f}")
        print(f"      - assessments_used: {user.get('assessments_used', 0)}")
        
        # Check for recent audit trails
        if 'duration_audit_trail' in user:
            print(f"   📋 Duration audit trail: {len(user['duration_audit_trail'])} entries")
            if user['duration_audit_trail']:
                latest = user['duration_audit_trail'][-1]
                print(f"      Latest entry: {latest.get('timestamp', 'N/A')}")
                print(f"      Reason: {latest.get('reason', 'N/A')}")
                print(f"      Minutes diff: {latest.get('minutes_diff', 0):.2f}")
                print(f"      Sessions diff: {latest.get('sessions_diff', 0)}")
        
        if 'speaking_time_audit_trail' in user:
            print(f"   📋 Speaking time audit trail: {len(user['speaking_time_audit_trail'])} entries")
            if user['speaking_time_audit_trail']:
                latest = user['speaking_time_audit_trail'][-1]
                print(f"      Latest entry: {latest.get('timestamp', 'N/A')}")
                print(f"      Reason: {latest.get('reason', 'N/A')}")
    print()
    
    # 2. Check learning plan for the completed session
    print("📚 CHECKING LEARNING PLAN SESSION:")
    print("-" * 40)
    
    # Find the learning plan by the plan ID (which is stored as 'id' field)
    learning_plan = await db.learning_plans.find_one({"id": plan_id})
    if not learning_plan:
        # Try finding by user_id and check all plans
        learning_plans = await db.learning_plans.find({"user_id": user_id}).to_list(None)
        print(f"   Found {len(learning_plans)} learning plans for user")
        
        for i, plan in enumerate(learning_plans, 1):
            plan_plan_id = plan.get('id', 'N/A')
            plan_name = plan.get('name', f'Plan {i}')
            language = plan.get('language', 'Unknown')
            sessions = plan.get('sessions', [])
            
            print(f"   📋 Plan {i}: {plan_name} ({language})")
            print(f"      Plan ID: {plan_plan_id}")
            print(f"      MongoDB _id: {plan['_id']}")
            print(f"      Total sessions: {len(sessions)}")
            
            # Check for recently completed sessions
            completed_sessions = 0
            recent_sessions = []
            
            for j, session in enumerate(sessions):
                if session.get('completed_at'):
                    completed_sessions += 1
                    completed_at = session.get('completed_at')
                    
                    # Check if this is a recent session (within last hour)
                    try:
                        if isinstance(completed_at, str):
                            session_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        else:
                            session_time = completed_at
                        
                        time_diff = datetime.utcnow() - session_time.replace(tzinfo=None)
                        if time_diff.total_seconds() < 3600:  # Within last hour
                            recent_sessions.append({
                                'index': j + 1,
                                'completed_at': completed_at,
                                'duration': session.get('conversation_duration', session.get('duration', 0)),
                                'messages': len(session.get('messages', [])),
                                'time_ago': f"{time_diff.total_seconds():.0f} seconds ago"
                            })
                    except Exception as e:
                        pass
            
            print(f"      Completed sessions: {completed_sessions}")
            
            if recent_sessions:
                print(f"      🆕 RECENT SESSIONS (last hour):")
                for session in recent_sessions:
                    print(f"         Session {session['index']}: {session['duration']:.2f} min, {session['messages']} messages")
                    print(f"            Completed: {session['completed_at']}")
                    print(f"            Time ago: {session['time_ago']}")
            else:
                print(f"      ⚠️  No recent sessions found")
            
            print()
    else:
        print(f"   ✅ Found learning plan by ID: {plan_id}")
        sessions = learning_plan.get('sessions', [])
        print(f"   Total sessions: {len(sessions)}")
        
        # Check for the most recent session
        completed_sessions = [s for s in sessions if s.get('completed_at')]
        if completed_sessions:
            latest_session = completed_sessions[-1]
            print(f"   🆕 Latest completed session:")
            print(f"      Duration: {latest_session.get('conversation_duration', latest_session.get('duration', 0)):.2f} min")
            print(f"      Messages: {len(latest_session.get('messages', []))}")
            print(f"      Completed at: {latest_session.get('completed_at')}")
    
    # 3. Check conversation sessions
    print("💬 CHECKING CONVERSATION SESSIONS:")
    print("-" * 40)
    conv_sessions = await db.conversation_sessions.find({"user_id": user_object_id}).to_list(None)
    if not conv_sessions:
        conv_sessions = await db.conversation_sessions.find({"user_id": user_id}).to_list(None)
    
    print(f"   Found {len(conv_sessions)} conversation sessions")
    
    # Check for recent sessions
    recent_conv_sessions = []
    for session in conv_sessions:
        created_at = session.get('created_at')
        if created_at:
            try:
                if isinstance(created_at, str):
                    session_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    session_time = created_at
                
                time_diff = datetime.utcnow() - session_time.replace(tzinfo=None)
                if time_diff.total_seconds() < 3600:  # Within last hour
                    recent_conv_sessions.append({
                        'duration': session.get('duration', 0),
                        'created_at': created_at,
                        'messages': len(session.get('messages', [])),
                        'time_ago': f"{time_diff.total_seconds():.0f} seconds ago"
                    })
            except Exception as e:
                pass
    
    if recent_conv_sessions:
        print(f"   🆕 RECENT CONVERSATION SESSIONS:")
        for session in recent_conv_sessions:
            print(f"      Duration: {session['duration']:.2f} min, Messages: {session['messages']}")
            print(f"      Created: {session['created_at']}")
            print(f"      Time ago: {session['time_ago']}")
    else:
        print(f"   ⚠️  No recent conversation sessions found")
    
    print()
    
    # 4. Summary
    print("🎯 VERIFICATION SUMMARY:")
    print("=" * 60)
    
    expected_duration = 5.95  # 5:57 = 5.95 minutes
    expected_messages = 41
    
    if user:
        current_sessions = user.get('practice_sessions_used', 0)
        current_minutes = user.get('practice_minutes_used', 0.0)
        
        print(f"📊 EXPECTED vs ACTUAL:")
        print(f"   Expected duration: ~{expected_duration:.2f} minutes")
        print(f"   Expected messages: {expected_messages}")
        print(f"   Expected session increment: +1")
        print()
        print(f"   Current sessions used: {current_sessions}")
        print(f"   Current minutes used: {current_minutes:.2f}")
        
        if current_sessions > 0 and current_minutes > 0:
            print("   ✅ SESSION TRACKING APPEARS TO BE WORKING!")
            print(f"   Average per session: {current_minutes/current_sessions:.2f} min")
        else:
            print("   ❌ NO USAGE RECORDED - SESSION TRACKING MAY NOT BE WORKING")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(verify_session_completion())
