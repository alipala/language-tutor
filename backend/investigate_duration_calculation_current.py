#!/usr/bin/env python3

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from bson import ObjectId

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from subscription_service import SubscriptionService

async def investigate_user_duration_calculation(user_id: str):
    """
    Comprehensive investigation of duration calculation issues for a specific user
    """
    print("=" * 80)
    print(f"🔍 DURATION CALCULATION INVESTIGATION")
    print(f"User ID: {user_id}")
    print(f"Investigation Date: {datetime.utcnow()}")
    print("=" * 80)
    
    try:
        # Convert user ID to proper format
        try:
            user_object_id = ObjectId(user_id)
            user_query = {"_id": user_object_id}
        except:
            user_query = {"_id": user_id}
        
        # 1. GET USER DATA
        print("\n📊 USER SUBSCRIPTION DATA:")
        print("-" * 40)
        
        user = await database.users.find_one(user_query)
        if not user:
            print(f"❌ User {user_id} not found!")
            return
        
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Subscription Plan: {user.get('subscription_plan', 'N/A')}")
        print(f"Subscription Period: {user.get('subscription_period', 'N/A')}")
        print(f"Subscription Status: {user.get('subscription_status', 'N/A')}")
        print(f"Period Start: {user.get('current_period_start', 'N/A')}")
        print(f"Period End: {user.get('current_period_end', 'N/A')}")
        print(f"Practice Sessions Used: {user.get('practice_sessions_used', 0)}")
        print(f"Practice Minutes Used: {user.get('practice_minutes_used', 0.0)}")
        print(f"Assessments Used: {user.get('assessments_used', 0)}")
        
        # 2. GET SUBSCRIPTION STATUS FROM SERVICE
        print("\n🎯 CALCULATED SUBSCRIPTION STATUS:")
        print("-" * 40)
        
        status = await SubscriptionService.get_user_subscription_status(user_id)
        if status.limits:
            print(f"Plan: {status.limits.plan}")
            print(f"Period: {status.limits.period}")
            print(f"Sessions - Used: {status.limits.sessions_used}, Limit: {status.limits.sessions_limit}, Remaining: {status.limits.sessions_remaining}")
            print(f"Minutes - Used: {status.limits.minutes_used:.2f}, Limit: {status.limits.minutes_limit}, Remaining: {status.limits.minutes_remaining:.2f}")
            print(f"Assessments - Used: {status.limits.assessments_used}, Limit: {status.limits.assessments_limit}, Remaining: {status.limits.assessments_remaining}")
            print(f"Period Start: {status.limits.period_start}")
            print(f"Period End: {status.limits.period_end}")
        
        # 3. ANALYZE CONVERSATION SESSIONS
        print("\n💬 CONVERSATION SESSIONS ANALYSIS:")
        print("-" * 40)
        
        conversation_sessions = await database.conversation_sessions.find({
            "user_id": user_id
        }).sort("created_at", 1).to_list(length=None)
        
        total_conversation_duration = 0.0
        current_period_start = user.get('current_period_start')
        current_period_end = user.get('current_period_end')
        current_period_conversation_sessions = []
        
        print(f"Total conversation sessions: {len(conversation_sessions)}")
        
        for i, session in enumerate(conversation_sessions):
            duration = session.get('duration_minutes', 0.0)
            total_conversation_duration += duration
            created_at = session.get('created_at', datetime.min)
            
            # Check if in current period
            if current_period_start and current_period_end and current_period_start <= created_at < current_period_end:
                current_period_conversation_sessions.append(session)
            
            print(f"  Session {i+1}: {created_at} - {duration:.2f} minutes - Topic: {session.get('topic', 'N/A')}")
        
        current_period_conversation_duration = sum(s.get('duration_minutes', 0.0) for s in current_period_conversation_sessions)
        print(f"\nConversation Sessions Summary:")
        print(f"  Total Duration (all time): {total_conversation_duration:.2f} minutes")
        print(f"  Current Period Sessions: {len(current_period_conversation_sessions)}")
        print(f"  Current Period Duration: {current_period_conversation_duration:.2f} minutes")
        
        # 4. ANALYZE LEARNING PLANS
        print("\n📚 LEARNING PLANS ANALYSIS:")
        print("-" * 40)
        
        learning_plans = await database.learning_plans.find({
            "user_id": user_id
        }).sort("created_at", 1).to_list(length=None)
        
        total_learning_plan_duration = 0.0
        total_learning_plan_sessions = 0
        current_period_learning_duration = 0.0
        current_period_learning_sessions = 0
        
        print(f"Total learning plans: {len(learning_plans)}")
        
        for i, plan in enumerate(learning_plans):
            plan_language = plan.get('language', 'N/A')
            plan_level = plan.get('proficiency_level', 'N/A')
            completed_sessions = plan.get('completed_sessions', 0)
            total_sessions = plan.get('total_sessions', 0)
            
            print(f"\nLearning Plan {i+1}: {plan_language} ({plan_level})")
            print(f"  ID: {plan.get('id', 'N/A')}")
            print(f"  Completed Sessions: {completed_sessions}/{total_sessions}")
            print(f"  Created: {plan.get('created_at', 'N/A')}")
            
            total_learning_plan_sessions += completed_sessions
            
            # Check session summaries for duration data
            session_summaries = plan.get('session_summaries', [])
            plan_duration = 0.0
            plan_sessions_in_period = 0
            plan_duration_in_period = 0.0
            
            print(f"  Session summaries: {len(session_summaries)}")
            
            # Also check weekly schedule for session details
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            print(f"  Weekly schedule weeks: {len(weekly_schedule)}")
            
            for week_idx, week in enumerate(weekly_schedule):
                session_details = week.get('session_details', [])
                print(f"    Week {week_idx + 1}: {len(session_details)} session details")
                
                for session_detail in session_details:
                    duration = session_detail.get('duration_minutes', 0.0)
                    completed_at_str = session_detail.get('completed_at')
                    
                    if duration > 0:
                        plan_duration += duration
                        total_learning_plan_duration += duration
                        
                        # Check if in current period
                        if completed_at_str and current_period_start and current_period_end:
                            try:
                                completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                if current_period_start <= completed_at < current_period_end:
                                    plan_sessions_in_period += 1
                                    plan_duration_in_period += duration
                                    current_period_learning_sessions += 1
                                    current_period_learning_duration += duration
                            except:
                                print(f"      ⚠️ Could not parse date: {completed_at_str}")
                    
                    print(f"      Session {session_detail.get('session_number', 'N/A')}: {duration:.2f}min at {completed_at_str}")
            
            print(f"  Plan Total Duration: {plan_duration:.2f} minutes")
            print(f"  Plan Sessions in Current Period: {plan_sessions_in_period}")
            print(f"  Plan Duration in Current Period: {plan_duration_in_period:.2f} minutes")
        
        print(f"\nLearning Plans Summary:")
        print(f"  Total Sessions (all time): {total_learning_plan_sessions}")
        print(f"  Total Duration (all time): {total_learning_plan_duration:.2f} minutes")
        print(f"  Current Period Sessions: {current_period_learning_sessions}")
        print(f"  Current Period Duration: {current_period_learning_duration:.2f} minutes")
        
        # 5. COMPREHENSIVE SUMMARY AND ISSUE DETECTION
        print("\n🎯 COMPREHENSIVE ANALYSIS:")
        print("=" * 40)
        
        # Calculate actual totals
        actual_total_sessions = len(current_period_conversation_sessions) + current_period_learning_sessions
        actual_total_duration = current_period_conversation_duration + current_period_learning_duration
        
        # Compare with stored values
        stored_sessions = user.get('practice_sessions_used', 0)
        stored_minutes = user.get('practice_minutes_used', 0.0)
        
        print(f"CURRENT PERIOD ANALYSIS ({current_period_start} to {current_period_end}):")
        print(f"  Actual Sessions: {actual_total_sessions} (Conversation: {len(current_period_conversation_sessions)}, Learning: {current_period_learning_sessions})")
        print(f"  Stored Sessions: {stored_sessions}")
        print(f"  Actual Duration: {actual_total_duration:.2f} minutes (Conversation: {current_period_conversation_duration:.2f}, Learning: {current_period_learning_duration:.2f})")
        print(f"  Stored Duration: {stored_minutes:.2f} minutes")
        
        # Identify discrepancies
        session_discrepancy = actual_total_sessions - stored_sessions
        duration_discrepancy = actual_total_duration - stored_minutes
        
        print(f"\nDISCREPANCY ANALYSIS:")
        print(f"  Session Discrepancy: {session_discrepancy} ({'✅ OK' if abs(session_discrepancy) <= 1 else '❌ ISSUE'})")
        print(f"  Duration Discrepancy: {duration_discrepancy:.2f} minutes ({'✅ OK' if abs(duration_discrepancy) <= 5 else '❌ ISSUE'})")
        
        # Calculate remaining based on plan
        if status.limits:
            print(f"\nREMAINING CALCULATION:")
            print(f"  Sessions Remaining: {status.limits.sessions_remaining} out of {status.limits.sessions_limit}")
            print(f"  Minutes Remaining: {status.limits.minutes_remaining:.2f} out of {status.limits.minutes_limit}")
            print(f"  Period End: {status.limits.period_end}")
            
            # Calculate days until period end
            if status.limits.period_end:
                days_remaining = (status.limits.period_end - datetime.utcnow()).days
                print(f"  Days Until Reset: {days_remaining}")
        
        # 6. ISSUE IDENTIFICATION AND RECOMMENDATIONS
        print("\n🔧 ISSUE IDENTIFICATION:")
        print("=" * 40)
        
        issues_found = []
        
        if abs(session_discrepancy) > 1:
            issues_found.append(f"Session count mismatch: Expected {actual_total_sessions}, but stored {stored_sessions}")
        
        if abs(duration_discrepancy) > 5:  # Allow 5-minute tolerance
            issues_found.append(f"Duration mismatch: Expected {actual_total_duration:.2f}, but stored {stored_minutes:.2f}")
        
        # Check if learning plan sessions have duration data
        learning_sessions_without_duration = 0
        for plan in learning_plans:
            weekly_schedule = plan.get('plan_content', {}).get('weekly_schedule', [])
            for week in weekly_schedule:
                for session_detail in week.get('session_details', []):
                    if session_detail.get('duration_minutes', 0.0) == 0:
                        learning_sessions_without_duration += 1
        
        if learning_sessions_without_duration > 0:
            issues_found.append(f"{learning_sessions_without_duration} learning plan sessions missing duration data")
        
        if not issues_found:
            print("✅ No major issues detected!")
        else:
            print("❌ Issues found:")
            for i, issue in enumerate(issues_found, 1):
                print(f"  {i}. {issue}")
        
        print(f"\n🎯 INVESTIGATION COMPLETE")
        print("=" * 80)
        
        return {
            "user_data": user,
            "subscription_status": status,
            "conversation_sessions": len(conversation_sessions),
            "learning_plan_sessions": total_learning_plan_sessions,
            "actual_sessions_current_period": actual_total_sessions,
            "actual_duration_current_period": actual_total_duration,
            "stored_sessions": stored_sessions,
            "stored_minutes": stored_minutes,
            "issues_found": issues_found
        }
        
    except Exception as e:
        print(f"❌ Error during investigation: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

async def main():
    """Main function to run the investigation"""
    
    # User ID from the provided data
    USER_ID = "688921c268819565ef1ce3dc"
    
    print("🚀 Starting Duration Calculation Investigation...")
    
    # Initialize database connection
    from database import init_db
    await init_db()
    
    # Run investigation
    result = await investigate_user_duration_calculation(USER_ID)
    
    if result and result.get('issues_found'):
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("-" * 40)
        print("1. Update user's stored session count and duration based on actual data")
        print("2. Ensure all learning plan sessions have duration tracking")
        print("3. Verify monthly reset functionality")
        print("4. Test duration tracking for new sessions")

if __name__ == "__main__":
    asyncio.run(main())
