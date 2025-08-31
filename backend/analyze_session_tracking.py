#!/usr/bin/env python3
"""
Analyze where and how we track completed sessions for subscription periods
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

# Production MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def analyze_session_tracking():
    """Analyze session tracking across collections"""
    
    print("🔍 ANALYZING SESSION TRACKING FOR SUBSCRIPTION PERIODS")
    print("=" * 70)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    user_id = "688921c268819565ef1ce3dc"
    user_object_id = ObjectId(user_id)
    
    print(f"👤 User ID: {user_id}")
    print()
    
    # 1. Check user record - primary tracking location
    print("👤 PRIMARY TRACKING: USERS COLLECTION")
    print("-" * 50)
    user = await db.users.find_one({"_id": user_object_id})
    if user:
        print(f"   📧 Email: {user.get('email')}")
        print(f"   📊 SUBSCRIPTION TRACKING FIELDS:")
        print(f"      - practice_sessions_used: {user.get('practice_sessions_used', 0)} (PRIMARY)")
        print(f"      - practice_minutes_used: {user.get('practice_minutes_used', 0.0)} (PRIMARY)")
        print(f"      - assessments_used: {user.get('assessments_used', 0)}")
        print(f"   📅 SUBSCRIPTION PERIOD:")
        print(f"      - current_period_start: {user.get('current_period_start')}")
        print(f"      - current_period_end: {user.get('current_period_end')}")
        print(f"      - subscription_plan: {user.get('subscription_plan')}")
        print(f"      - subscription_period: {user.get('subscription_period')}")
        
        # Check for audit trails
        if 'duration_audit_trail' in user:
            print(f"   📋 Duration audit trail: {len(user['duration_audit_trail'])} entries")
        if 'speaking_time_audit_trail' in user:
            print(f"   📋 Speaking time audit trail: {len(user['speaking_time_audit_trail'])} entries")
        if 'usage_audit_trail' in user:
            print(f"   📋 Usage audit trail: {len(user['usage_audit_trail'])} entries")
    print()
    
    # 2. Check learning plans - session completion tracking
    print("📚 LEARNING PLAN SESSION TRACKING:")
    print("-" * 50)
    learning_plans = await db.learning_plans.find({"user_id": user_id}).to_list(None)
    
    total_completed_sessions = 0
    total_session_minutes = 0.0
    
    for i, plan in enumerate(learning_plans, 1):
        plan_name = plan.get('name', f'Plan {i}')
        language = plan.get('language', 'Unknown')
        sessions = plan.get('sessions', [])
        
        completed_sessions = 0
        plan_minutes = 0.0
        
        print(f"   📋 Plan {i}: {plan_name} ({language})")
        print(f"      Total sessions in plan: {len(sessions)}")
        
        for j, session in enumerate(sessions):
            if session.get('completed_at'):
                completed_sessions += 1
                total_completed_sessions += 1
                
                # Check for duration data
                duration = 0.0
                if 'conversation_duration' in session:
                    duration = float(session['conversation_duration'])
                elif 'duration' in session:
                    duration = float(session['duration'])
                elif 'conversation_data' in session and session['conversation_data']:
                    conv_data = session['conversation_data']
                    if isinstance(conv_data, dict) and 'duration' in conv_data:
                        duration = float(conv_data['duration'])
                
                plan_minutes += duration
                total_session_minutes += duration
                
                completed_at = session.get('completed_at')
                print(f"         ✅ Session {j+1}: {duration:.2f} min on {completed_at}")
        
        print(f"      Completed sessions: {completed_sessions}")
        print(f"      Total minutes: {plan_minutes:.2f}")
        print()
    
    print(f"   📊 LEARNING PLAN TOTALS:")
    print(f"      Total completed sessions: {total_completed_sessions}")
    print(f"      Total session minutes: {total_session_minutes:.2f}")
    print()
    
    # 3. Check conversation sessions - standalone practice
    print("💬 STANDALONE CONVERSATION SESSIONS:")
    print("-" * 50)
    conv_sessions = await db.conversation_sessions.find({"user_id": user_object_id}).to_list(None)
    if not conv_sessions:
        conv_sessions = await db.conversation_sessions.find({"user_id": user_id}).to_list(None)
    
    standalone_sessions = len(conv_sessions)
    standalone_minutes = 0.0
    
    for i, session in enumerate(conv_sessions):
        duration = session.get('duration', 0.0)
        created_at = session.get('created_at', 'Unknown')
        standalone_minutes += duration
        print(f"   Session {i+1}: {duration:.2f} min on {created_at}")
    
    print(f"   📊 STANDALONE TOTALS:")
    print(f"      Total standalone sessions: {standalone_sessions}")
    print(f"      Total standalone minutes: {standalone_minutes:.2f}")
    print()
    
    # 4. Check sessions collection
    print("📊 SESSIONS COLLECTION:")
    print("-" * 50)
    sessions_coll = await db.sessions.find({"user_id": user_object_id}).to_list(None)
    if not sessions_coll:
        sessions_coll = await db.sessions.find({"user_id": user_id}).to_list(None)
    
    sessions_coll_count = len(sessions_coll)
    sessions_coll_minutes = 0.0
    
    for i, session in enumerate(sessions_coll):
        duration = session.get('duration', 0.0)
        if duration > 0:
            sessions_coll_minutes += duration
            created_at = session.get('created_at', session.get('timestamp', 'Unknown'))
            print(f"   Session {i+1}: {duration:.2f} min on {created_at}")
    
    print(f"   📊 SESSIONS COLLECTION TOTALS:")
    print(f"      Total sessions: {sessions_coll_count}")
    print(f"      Total minutes: {sessions_coll_minutes:.2f}")
    print()
    
    # 5. Summary and analysis
    print("🎯 SESSION TRACKING ANALYSIS:")
    print("=" * 70)
    
    # Calculate totals from all sources
    all_sessions = total_completed_sessions + standalone_sessions
    all_minutes = total_session_minutes + standalone_minutes + sessions_coll_minutes
    
    print(f"📊 ACTUAL DATA FOUND:")
    print(f"   Learning plan sessions: {total_completed_sessions} ({total_session_minutes:.2f} min)")
    print(f"   Standalone conversations: {standalone_sessions} ({standalone_minutes:.2f} min)")
    print(f"   Sessions collection: {sessions_coll_count} ({sessions_coll_minutes:.2f} min)")
    print(f"   TOTAL FOUND: {all_sessions} sessions, {all_minutes:.2f} minutes")
    print()
    
    print(f"📋 USER RECORD TRACKING:")
    if user:
        recorded_sessions = user.get('practice_sessions_used', 0)
        recorded_minutes = user.get('practice_minutes_used', 0.0)
        print(f"   practice_sessions_used: {recorded_sessions}")
        print(f"   practice_minutes_used: {recorded_minutes:.2f}")
        print()
        
        print(f"🔍 COMPARISON:")
        print(f"   Sessions - Recorded: {recorded_sessions}, Found: {all_sessions}, Diff: {all_sessions - recorded_sessions}")
        print(f"   Minutes - Recorded: {recorded_minutes:.2f}, Found: {all_minutes:.2f}, Diff: {all_minutes - recorded_minutes:.2f}")
        
        if recorded_sessions == all_sessions and abs(recorded_minutes - all_minutes) < 0.01:
            print("   ✅ USER RECORD MATCHES ACTUAL DATA!")
        else:
            print("   ❌ USER RECORD DOES NOT MATCH ACTUAL DATA!")
    
    print()
    print("📝 TRACKING SYSTEM SUMMARY:")
    print("   🎯 PRIMARY: users.practice_sessions_used (subscription period tracking)")
    print("   🎯 PRIMARY: users.practice_minutes_used (subscription period tracking)")
    print("   📚 DETAIL: learning_plans.sessions[].completed_at (individual session data)")
    print("   💬 DETAIL: conversation_sessions (standalone practice sessions)")
    print("   📊 DETAIL: sessions collection (additional session data)")
    print()
    print("   ✨ The users collection is the authoritative source for subscription limits!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(analyze_session_tracking())
