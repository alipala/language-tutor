#!/usr/bin/env python3
"""
Investigation script for user minute calculation issue
User: alipala.ist@gmail.com (UserId: 688921c268819565ef1ce3dc)
Issue: Shows 137/150 minutes remaining despite completing 6 sessions + practice
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

async def investigate_user_minutes():
    """Deep dive analysis of user's session tracking and minute calculation"""
    
    print("=" * 80)
    print("🔍 INVESTIGATING USER MINUTE CALCULATION ISSUE")
    print("=" * 80)
    print(f"Target User: {TARGET_USER_EMAIL}")
    print(f"User ID: {TARGET_USER_ID}")
    print(f"Expected Issue: Shows 137/150 minutes remaining despite 6 sessions + practice")
    print()
    
    try:
        # Connect to MongoDB
        print("📡 Connecting to production MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        database = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        print()
        
        # Get collections
        users_collection = database.users
        conversation_sessions_collection = database.conversation_sessions
        learning_plans_collection = database.learning_plans
        
        # 1. FIND USER DATA
        print("👤 STEP 1: RETRIEVING USER DATA")
        print("-" * 40)
        
        # Try both ObjectId and string formats
        user = None
        try:
            user = await users_collection.find_one({"_id": ObjectId(TARGET_USER_ID)})
            print(f"✅ Found user by ObjectId: {TARGET_USER_ID}")
        except:
            user = await users_collection.find_one({"_id": TARGET_USER_ID})
            if user:
                print(f"✅ Found user by string ID: {TARGET_USER_ID}")
        
        if not user:
            # Try by email as fallback
            user = await users_collection.find_one({"email": TARGET_USER_EMAIL})
            if user:
                print(f"✅ Found user by email: {TARGET_USER_EMAIL}")
                print(f"   Actual User ID: {user['_id']}")
            else:
                print(f"❌ User not found with ID {TARGET_USER_ID} or email {TARGET_USER_EMAIL}")
                return
        
        print(f"📧 Email: {user.get('email', 'N/A')}")
        print(f"👤 Name: {user.get('name', 'N/A')}")
        print(f"📅 Created: {user.get('created_at', 'N/A')}")
        print()
        
        # 2. SUBSCRIPTION STATUS
        print("💳 STEP 2: SUBSCRIPTION STATUS")
        print("-" * 40)
        print(f"Plan: {user.get('subscription_plan', 'N/A')}")
        print(f"Status: {user.get('subscription_status', 'N/A')}")
        print(f"Period: {user.get('subscription_period', 'N/A')}")
        print(f"Expires: {user.get('subscription_expires_at', 'N/A')}")
        print(f"Started: {user.get('subscription_started_at', 'N/A')}")
        print()
        
        # 3. USAGE TRACKING FIELDS
        print("📊 STEP 3: USAGE TRACKING FIELDS")
        print("-" * 40)
        print(f"Practice Sessions Used: {user.get('practice_sessions_used', 0)}")
        print(f"Assessments Used: {user.get('assessments_used', 0)}")
        print(f"Practice Minutes Used: {user.get('practice_minutes_used', 0.0)}")
        print(f"Current Period Start: {user.get('current_period_start', 'N/A')}")
        print(f"Current Period End: {user.get('current_period_end', 'N/A')}")
        print()
        
        # 4. CALCULATE EXPECTED LIMITS
        print("🎯 STEP 4: SUBSCRIPTION LIMITS CALCULATION")
        print("-" * 40)
        
        plan = user.get('subscription_plan', 'try_learn')
        period = user.get('subscription_period', 'monthly')
        
        # Define limits based on subscription_service.py
        SUBSCRIPTION_PLANS = {
            "try_learn": {
                "monthly_sessions": 3, "monthly_minutes": 15,
                "annual_sessions": 3, "annual_minutes": 15
            },
            "fluency_builder": {
                "monthly_sessions": 30, "monthly_minutes": 150,
                "annual_sessions": 360, "annual_minutes": 1800
            },
            "team_mastery": {
                "monthly_sessions": -1, "monthly_minutes": -1,
                "annual_sessions": -1, "annual_minutes": -1
            }
        }
        
        plan_limits = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["try_learn"])
        
        if period == "annual":
            sessions_limit = plan_limits["annual_sessions"]
            minutes_limit = plan_limits["annual_minutes"]
        else:
            sessions_limit = plan_limits["monthly_sessions"]
            minutes_limit = plan_limits["monthly_minutes"]
        
        sessions_used = user.get('practice_sessions_used', 0)
        minutes_used = user.get('practice_minutes_used', 0.0)
        
        sessions_remaining = sessions_limit - sessions_used if sessions_limit != -1 else -1
        minutes_remaining = minutes_limit - minutes_used if minutes_limit != -1 else -1
        
        print(f"Plan: {plan} ({period})")
        print(f"Sessions Limit: {sessions_limit}")
        print(f"Minutes Limit: {minutes_limit}")
        print(f"Sessions Used: {sessions_used}")
        print(f"Minutes Used: {minutes_used}")
        print(f"Sessions Remaining: {sessions_remaining}")
        print(f"Minutes Remaining: {minutes_remaining}")
        print()
        
        # 5. CONVERSATION SESSIONS ANALYSIS
        print("💬 STEP 5: CONVERSATION SESSIONS ANALYSIS")
        print("-" * 40)
        
        # Get all conversation sessions for this user
        sessions_cursor = conversation_sessions_collection.find({"user_id": str(user['_id'])})
        sessions = await sessions_cursor.to_list(length=None)
        
        print(f"Total Conversation Sessions Found: {len(sessions)}")
        
        if sessions:
            total_duration = 0
            streak_eligible_count = 0
            
            print("\nSession Details:")
            print("Date       | Duration | Messages | Streak | Language | Level | Topic")
            print("-" * 75)
            
            for i, session in enumerate(sessions, 1):
                created_at = session.get('created_at', datetime.min)
                duration = session.get('duration_minutes', 0)
                message_count = session.get('message_count', 0)
                is_streak = session.get('is_streak_eligible', False)
                language = session.get('language', 'N/A')
                level = session.get('level', 'N/A')
                topic = session.get('topic', 'N/A')
                
                total_duration += duration
                if is_streak:
                    streak_eligible_count += 1
                
                date_str = created_at.strftime("%Y-%m-%d") if isinstance(created_at, datetime) else str(created_at)[:10]
                print(f"{date_str} | {duration:8.1f} | {message_count:8d} | {str(is_streak):6s} | {language:8s} | {level:5s} | {topic}")
            
            print("-" * 75)
            print(f"Total Duration from Sessions: {total_duration:.1f} minutes")
            print(f"Streak Eligible Sessions: {streak_eligible_count}")
            print(f"Average Duration per Session: {total_duration/len(sessions):.1f} minutes")
        
        print()
        
        # 6. LEARNING PLAN SESSIONS
        print("📚 STEP 6: LEARNING PLAN SESSIONS")
        print("-" * 40)
        
        learning_plans_cursor = learning_plans_collection.find({"user_id": str(user['_id'])})
        learning_plans = await learning_plans_cursor.to_list(length=None)
        
        print(f"Learning Plans Found: {len(learning_plans)}")
        
        for plan in learning_plans:
            print(f"\nLearning Plan ID: {plan.get('id', 'N/A')}")
            print(f"Language: {plan.get('language', 'N/A')}")
            print(f"Level: {plan.get('proficiency_level', 'N/A')}")
            print(f"Completed Sessions: {plan.get('completed_sessions', 0)}")
            print(f"Total Sessions: {plan.get('total_sessions', 0)}")
            print(f"Progress: {plan.get('progress_percentage', 0):.1f}%")
            
            # Check for session summaries
            session_summaries = plan.get('session_summaries', [])
            print(f"Session Summaries: {len(session_summaries)}")
            
            # Check weekly schedule
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            if weekly_schedule:
                completed_weeks = sum(1 for week in weekly_schedule if week.get('sessions_completed', 0) >= 2)
                print(f"Weekly Schedule: {len(weekly_schedule)} weeks, {completed_weeks} completed")
        
        print()
        
        # 7. DISCREPANCY ANALYSIS
        print("🚨 STEP 7: DISCREPANCY ANALYSIS")
        print("-" * 40)
        
        print("EXPECTED vs ACTUAL:")
        print(f"User reported: 6 sessions + practice = should consume ~30-35 minutes")
        print(f"System shows: {minutes_used:.1f} minutes used, {minutes_remaining:.1f} remaining")
        print(f"Conversation sessions found: {len(sessions)} sessions")
        print(f"Total duration from sessions: {sum(s.get('duration_minutes', 0) for s in sessions):.1f} minutes")
        print(f"Streak eligible sessions: {sum(1 for s in sessions if s.get('is_streak_eligible', False))}")
        
        # Check for potential issues
        print("\nPOTENTIAL ISSUES:")
        
        # Issue 1: Sessions not being tracked properly
        if len(sessions) < 6:
            print(f"❌ ISSUE 1: Only {len(sessions)} conversation sessions found, but user claims 6 sessions")
        
        # Issue 2: Minutes not being tracked properly
        total_session_minutes = sum(s.get('duration_minutes', 0) for s in sessions)
        if abs(total_session_minutes - minutes_used) > 1.0:
            print(f"❌ ISSUE 2: Mismatch between session minutes ({total_session_minutes:.1f}) and tracked minutes ({minutes_used:.1f})")
        
        # Issue 3: Learning plan sessions not appearing in conversation history
        learning_plan_sessions = sum(plan.get('completed_sessions', 0) for plan in learning_plans)
        if learning_plan_sessions > 0:
            print(f"⚠️  ISSUE 3: {learning_plan_sessions} learning plan sessions completed but may not appear in conversation history")
        
        # Issue 4: Session tracking logic issues
        if sessions_used != len(sessions) and sessions_used != streak_eligible_count:
            print(f"❌ ISSUE 4: Session count mismatch - DB shows {sessions_used} used, but found {len(sessions)} sessions ({streak_eligible_count} streak eligible)")
        
        print()
        
        # 8. RECOMMENDATIONS
        print("💡 STEP 8: RECOMMENDATIONS")
        print("-" * 40)
        
        print("Based on the analysis, here are the potential root causes:")
        print()
        print("1. LEARNING PLAN SESSIONS vs CONVERSATION SESSIONS:")
        print("   - Learning plan sessions may be tracked separately")
        print("   - They might not appear in conversation_sessions collection")
        print("   - But they still consume minutes and session counts")
        print()
        print("2. MINUTE TRACKING LOGIC:")
        print("   - Check if learning plan sessions update practice_minutes_used")
        print("   - Verify if session completion triggers minute tracking")
        print("   - Look for double-counting or missing tracking")
        print()
        print("3. SESSION COUNTING LOGIC:")
        print("   - Verify if practice_sessions_used is incremented correctly")
        print("   - Check if both conversation and learning plan sessions count")
        print("   - Look for timing issues in tracking")
        
        print()
        print("=" * 80)
        print("🔍 INVESTIGATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during investigation: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
    
    finally:
        if 'client' in locals():
            client.close()
            print("📡 MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(investigate_user_minutes())
