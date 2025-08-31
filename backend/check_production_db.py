#!/usr/bin/env python3
"""
Check the ACTUAL Railway production MongoDB (Taco App service)
"""

import asyncio
import sys
import os
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId

async def check_production_data():
    print('🔍 CHECKING ACTUAL RAILWAY PRODUCTION MONGODB')
    print('=' * 55)
    
    # Use the actual production MongoDB URL from Railway
    MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    print(f'🚀 Connecting to Railway Production MongoDB...')
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    db = client.language_tutor
    
    user_id = '688921c268819565ef1ce3dc'
    
    # Define current subscription period
    period_start = datetime(2025, 8, 9, 7, 32, 19)
    period_end = datetime(2025, 9, 9, 7, 32, 19)
    
    print(f'📅 Current Subscription Period: Aug 9 - Sep 9, 2025')
    print(f'👤 User ID: {user_id}')
    
    # 1. Check user record first
    print(f'\n👤 USER RECORD IN PRODUCTION:')
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        print('❌ User not found in production database!')
        return
    
    print(f'   📧 Email: {user.get("email")}')
    print(f'   📊 Current usage:')
    print(f'      - Sessions used: {user.get("practice_sessions_used", 0)}')
    print(f'      - Minutes used: {user.get("practice_minutes_used", 0):.2f}')
    print(f'   📅 Subscription period:')
    print(f'      - Start: {user.get("current_period_start")}')
    print(f'      - End: {user.get("current_period_end")}')
    print(f'   💳 Plan: {user.get("subscription_plan")}')
    
    # 2. Check conversation sessions in production
    print(f'\n💬 CONVERSATION SESSIONS IN PRODUCTION:')
    conversations = await db.conversation_sessions.find({'user_id': user_id}).to_list(length=None)
    
    conv_sessions_in_period = 0
    conv_minutes_in_period = 0.0
    
    print(f'   Found {len(conversations)} total conversation sessions')
    
    for conv in conversations:
        created_at = conv.get('created_at')
        duration = conv.get('duration_minutes', 0)
        
        if isinstance(created_at, str):
            session_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            session_date = created_at
        
        print(f'   - {duration:.2f} min at {session_date}', end='')
        
        if period_start <= session_date <= period_end:
            print(' ✅ IN CURRENT PERIOD')
            conv_sessions_in_period += 1
            conv_minutes_in_period += duration
        else:
            print(' ❌ OUTSIDE CURRENT PERIOD')
    
    print(f'   📊 Conversations in current period: {conv_sessions_in_period} ({conv_minutes_in_period:.2f} min)')
    
    # 3. Check learning plans in production
    print(f'\n🎓 LEARNING PLANS IN PRODUCTION:')
    learning_plans = await db.learning_plans.find({'user_id': user_id}).to_list(length=None)
    
    learning_sessions_in_period = 0
    learning_minutes_in_period = 0.0
    
    print(f'   Found {len(learning_plans)} learning plans')
    
    for i, plan in enumerate(learning_plans, 1):
        plan_name = plan.get('plan_name', f'Plan {i}')
        sessions_completed = plan.get('sessions_completed', [])
        
        print(f'\n   📋 Plan {i}: {plan_name}')
        print(f'      Total sessions in plan: {len(sessions_completed)}')
        
        plan_sessions_in_period = 0
        plan_minutes_in_period = 0.0
        
        for session in sessions_completed:
            completed_at = session.get('completed_at')
            duration = session.get('duration_minutes', 0)
            session_name = session.get('session_name', 'Unknown')
            
            if completed_at:
                if isinstance(completed_at, str):
                    session_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                else:
                    session_date = completed_at
                
                print(f'      - {session_name}: {duration:.2f} min at {session_date}', end='')
                
                if period_start <= session_date <= period_end:
                    print(' ✅ IN CURRENT PERIOD')
                    plan_sessions_in_period += 1
                    plan_minutes_in_period += duration
                    learning_sessions_in_period += 1
                    learning_minutes_in_period += duration
                else:
                    print(' ❌ OUTSIDE CURRENT PERIOD')
            else:
                print(f'      - {session_name}: {duration:.2f} min (no completion date)')
        
        print(f'      📊 Sessions in current period: {plan_sessions_in_period} ({plan_minutes_in_period:.2f} min)')
    
    print(f'\n   📊 Total learning sessions in current period: {learning_sessions_in_period} ({learning_minutes_in_period:.2f} min)')
    
    # 4. Calculate totals
    total_sessions_in_period = conv_sessions_in_period + learning_sessions_in_period
    total_minutes_in_period = conv_minutes_in_period + learning_minutes_in_period
    
    print(f'\n🎯 ACTUAL PRODUCTION DATA FOR CURRENT PERIOD:')
    print(f'   - Conversation sessions: {conv_sessions_in_period} ({conv_minutes_in_period:.2f} min)')
    print(f'   - Learning plan sessions: {learning_sessions_in_period} ({learning_minutes_in_period:.2f} min)')
    print(f'   - TOTAL SESSIONS: {total_sessions_in_period}')
    print(f'   - TOTAL MINUTES: {total_minutes_in_period:.2f}')
    
    # 5. Compare with user record
    user_sessions = user.get('practice_sessions_used', 0)
    user_minutes = user.get('practice_minutes_used', 0)
    
    print(f'\n🔍 COMPARISON:')
    print(f'   - User record sessions: {user_sessions}')
    print(f'   - Actual sessions in period: {total_sessions_in_period}')
    print(f'   - User record minutes: {user_minutes:.2f}')
    print(f'   - Actual minutes in period: {total_minutes_in_period:.2f}')
    
    if total_sessions_in_period == user_sessions and abs(total_minutes_in_period - user_minutes) < 1:
        print(f'\n✅ USER RECORD MATCHES ACTUAL PRODUCTION DATA!')
        
        # Calculate remaining time
        plan_limit = 150 if user.get('subscription_plan') == 'fluency_builder' else 15
        sessions_limit = 30 if user.get('subscription_plan') == 'fluency_builder' else 3
        
        minutes_remaining = plan_limit - user_minutes
        sessions_remaining = sessions_limit - user_sessions
        
        print(f'\n📊 REMAINING TIME:')
        print(f'   - Minutes remaining: {minutes_remaining:.2f}')
        print(f'   - Sessions remaining: {sessions_remaining}')
        
    else:
        print(f'\n❌ DISCREPANCY IN PRODUCTION DATA!')
        print(f'💡 User record should be: {total_sessions_in_period} sessions, {total_minutes_in_period:.2f} minutes')
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(check_production_data())
