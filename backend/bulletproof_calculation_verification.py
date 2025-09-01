#!/usr/bin/env python3
"""
BULLETPROOF CALCULATION VERIFICATION
Deep dive technical investigation to verify all subscription calculations are correct
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from bson import ObjectId
import json

async def bulletproof_verification():
    """Comprehensive verification of all subscription calculations"""
    
    # Get MongoDB URL
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable is required")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    user_id = "688921c268819565ef1ce3dc"
    
    print("🔍 BULLETPROOF CALCULATION VERIFICATION")
    print("=" * 60)
    print(f"🎯 Target User: {user_id}")
    print(f"📅 Verification Time: {datetime.utcnow().isoformat()}")
    print()
    
    # ========================================
    # 1. USER RECORD ANALYSIS
    # ========================================
    print("1️⃣ USER RECORD ANALYSIS")
    print("-" * 30)
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        print("❌ User not found!")
        return
    
    print(f"📧 Email: {user.get('email', 'N/A')}")
    print(f"📊 Subscription Plan: {user.get('subscription_plan', 'N/A')}")
    print(f"📅 Subscription Period: {user.get('subscription_period', 'N/A')}")
    print(f"📅 Current Period Start: {user.get('current_period_start', 'N/A')}")
    print(f"📅 Current Period End: {user.get('current_period_end', 'N/A')}")
    print()
    
    # User record usage
    user_minutes = user.get('practice_minutes_used', 0.0)
    user_sessions = user.get('practice_sessions_used', 0)
    user_assessments = user.get('assessments_used', 0)
    
    print("📊 USER RECORD USAGE:")
    print(f"   - Minutes Used: {user_minutes}")
    print(f"   - Sessions Used: {user_sessions}")
    print(f"   - Assessments Used: {user_assessments}")
    print()
    
    # ========================================
    # 2. SUBSCRIPTION PERIOD VALIDATION
    # ========================================
    print("2️⃣ SUBSCRIPTION PERIOD VALIDATION")
    print("-" * 35)
    
    period_start = user.get('current_period_start')
    period_end = user.get('current_period_end')
    now = datetime.utcnow()
    
    if not period_start or not period_end:
        print("⚠️ Missing subscription period dates!")
        # Calculate expected period for monthly subscription
        expected_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if expected_start.month == 12:
            expected_end = expected_start.replace(year=expected_start.year + 1, month=1)
        else:
            expected_end = expected_start.replace(month=expected_start.month + 1)
        
        print(f"📅 Expected Period: {expected_start} to {expected_end}")
        period_start = expected_start
        period_end = expected_end
    else:
        print(f"📅 Current Period: {period_start} to {period_end}")
        
        # Validate period makes sense
        period_duration = (period_end - period_start).days
        print(f"📊 Period Duration: {period_duration} days")
        
        if period_duration < 28 or period_duration > 32:
            print(f"⚠️ Unusual period duration: {period_duration} days")
        else:
            print("✅ Period duration looks correct")
    
    # Check if we're in the current period
    in_current_period = period_start <= now < period_end
    print(f"📍 Currently in period: {in_current_period}")
    if not in_current_period:
        days_until_reset = (period_end - now).days
        print(f"📅 Days until period reset: {days_until_reset}")
    print()
    
    # ========================================
    # 3. ACTUAL SESSION DATA ANALYSIS
    # ========================================
    print("3️⃣ ACTUAL SESSION DATA ANALYSIS")
    print("-" * 35)
    
    # Query conversation sessions in current period
    conversation_sessions = await db.conversation_sessions.find({
        "user_id": user_id,
        "created_at": {
            "$gte": period_start,
            "$lt": period_end
        }
    }).to_list(length=None)
    
    print(f"💬 CONVERSATION SESSIONS IN PERIOD:")
    print(f"   - Count: {len(conversation_sessions)}")
    
    conv_total_minutes = 0.0
    for i, session in enumerate(conversation_sessions, 1):
        duration = session.get('duration_minutes', 0.0)
        created = session.get('created_at', 'N/A')
        conv_total_minutes += duration
        print(f"   - Session {i}: {duration:.2f} min at {created}")
    
    print(f"   - Total Minutes: {conv_total_minutes:.2f}")
    print()
    
    # Query learning plan sessions in current period
    learning_plans = await db.learning_plans.find({
        "user_id": user_id
    }).to_list(length=None)
    
    print(f"🎓 LEARNING PLAN SESSIONS IN PERIOD:")
    learning_total_minutes = 0.0
    learning_total_sessions = 0
    
    for plan_idx, plan in enumerate(learning_plans, 1):
        plan_name = plan.get('name', f'Plan {plan_idx}')
        sessions = plan.get('sessions', [])
        plan_minutes = 0.0
        plan_sessions_in_period = 0
        
        print(f"   📋 {plan_name}:")
        print(f"      - Total sessions in plan: {len(sessions)}")
        
        for session in sessions:
            completed_at = session.get('completed_at')
            if completed_at:
                # Handle both string and datetime
                if isinstance(completed_at, str):
                    try:
                        completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    except:
                        continue
                
                if period_start <= completed_at < period_end:
                    duration = session.get('duration_minutes', 0.0)
                    plan_minutes += duration
                    plan_sessions_in_period += 1
                    learning_total_minutes += duration
                    learning_total_sessions += 1
                    print(f"      - Session: {duration:.2f} min at {completed_at}")
        
        print(f"      - Sessions in period: {plan_sessions_in_period}")
        print(f"      - Minutes in period: {plan_minutes:.2f}")
    
    print(f"   - Total Learning Sessions: {learning_total_sessions}")
    print(f"   - Total Learning Minutes: {learning_total_minutes:.2f}")
    print()
    
    # ========================================
    # 4. CALCULATION VERIFICATION
    # ========================================
    print("4️⃣ CALCULATION VERIFICATION")
    print("-" * 30)
    
    # Calculate actual totals
    actual_total_minutes = conv_total_minutes + learning_total_minutes
    actual_total_sessions = len(conversation_sessions) + learning_total_sessions
    
    print("📊 ACTUAL USAGE (SOURCE OF TRUTH):")
    print(f"   - Total Minutes: {actual_total_minutes:.2f}")
    print(f"   - Total Sessions: {actual_total_sessions}")
    print(f"   - Conversation: {conv_total_minutes:.2f} min, {len(conversation_sessions)} sessions")
    print(f"   - Learning Plans: {learning_total_minutes:.2f} min, {learning_total_sessions} sessions")
    print()
    
    print("📝 USER RECORD vs ACTUAL:")
    minutes_diff = abs(user_minutes - actual_total_minutes)
    sessions_diff = abs(user_sessions - actual_total_sessions)
    
    print(f"   - Minutes: Record={user_minutes:.2f}, Actual={actual_total_minutes:.2f}, Diff={minutes_diff:.2f}")
    print(f"   - Sessions: Record={user_sessions}, Actual={actual_total_sessions}, Diff={sessions_diff}")
    
    if minutes_diff > 0.1:
        print(f"   ⚠️ MINUTES DISCREPANCY: {minutes_diff:.2f} minutes")
    else:
        print("   ✅ Minutes match")
    
    if sessions_diff > 0:
        print(f"   ⚠️ SESSIONS DISCREPANCY: {sessions_diff} sessions")
    else:
        print("   ✅ Sessions match")
    print()
    
    # ========================================
    # 5. SUBSCRIPTION LIMITS VERIFICATION
    # ========================================
    print("5️⃣ SUBSCRIPTION LIMITS VERIFICATION")
    print("-" * 38)
    
    plan_id = user.get('subscription_plan', 'try_learn')
    period = user.get('subscription_period', 'monthly')
    
    # Define limits based on plan
    if plan_id == "try_learn":
        if period == "annual":
            minutes_limit = 15
            sessions_limit = 3
            assessments_limit = 1
        else:
            minutes_limit = 15
            sessions_limit = 3
            assessments_limit = 1
    elif plan_id == "fluency_builder":
        if period == "annual":
            minutes_limit = 1800  # 150 * 12
            sessions_limit = 360  # 30 * 12
            assessments_limit = 24  # 2 * 12
        else:
            minutes_limit = 150
            sessions_limit = 30
            assessments_limit = 2
    elif plan_id == "team_mastery":
        minutes_limit = -1  # Unlimited
        sessions_limit = -1  # Unlimited
        assessments_limit = -1  # Unlimited
    else:
        # Default to free tier
        minutes_limit = 15
        sessions_limit = 3
        assessments_limit = 1
    
    print(f"📋 PLAN: {plan_id} ({period})")
    print(f"📊 LIMITS:")
    print(f"   - Minutes: {minutes_limit if minutes_limit != -1 else 'Unlimited'}")
    print(f"   - Sessions: {sessions_limit if sessions_limit != -1 else 'Unlimited'}")
    print(f"   - Assessments: {assessments_limit if assessments_limit != -1 else 'Unlimited'}")
    print()
    
    # ========================================
    # 6. REMAINING CALCULATIONS
    # ========================================
    print("6️⃣ REMAINING CALCULATIONS")
    print("-" * 28)
    
    # Calculate remaining using ACTUAL data (not user record)
    if minutes_limit == -1:
        minutes_remaining = -1
        minutes_remaining_display = "Unlimited"
    else:
        minutes_remaining = max(0, minutes_limit - actual_total_minutes)
        minutes_remaining_display = f"{minutes_remaining:.0f} min left"
    
    if sessions_limit == -1:
        sessions_remaining = -1
    else:
        sessions_remaining = max(0, sessions_limit - actual_total_sessions)
    
    if assessments_limit == -1:
        assessments_remaining = -1
    else:
        assessments_remaining = max(0, assessments_limit - user_assessments)
    
    print("📊 REMAINING (USING ACTUAL DATA):")
    print(f"   - Minutes: {minutes_remaining_display}")
    print(f"   - Sessions: {sessions_remaining if sessions_remaining != -1 else 'Unlimited'}")
    print(f"   - Assessments: {assessments_remaining if assessments_remaining != -1 else 'Unlimited'}")
    print()
    
    # Compare with user record calculations
    if minutes_limit != -1:
        user_record_remaining = max(0, minutes_limit - user_minutes)
        print("📝 REMAINING (USING USER RECORD):")
        print(f"   - Minutes: {user_record_remaining:.0f} min left")
        
        if abs(minutes_remaining - user_record_remaining) > 0.1:
            print(f"   ⚠️ DASHBOARD DISCREPANCY: {abs(minutes_remaining - user_record_remaining):.2f} minutes")
            print(f"   📊 Dashboard would show: '{user_record_remaining:.0f} min left' (WRONG)")
            print(f"   ✅ Should show: '{minutes_remaining:.0f} min left' (CORRECT)")
        else:
            print("   ✅ Dashboard calculation matches actual usage")
    print()
    
    # ========================================
    # 7. EDGE CASE TESTING
    # ========================================
    print("7️⃣ EDGE CASE TESTING")
    print("-" * 22)
    
    # Test negative scenarios
    print("🧪 TESTING EDGE CASES:")
    
    # What if user goes over limit?
    if minutes_limit != -1 and actual_total_minutes > minutes_limit:
        overage = actual_total_minutes - minutes_limit
        print(f"   ⚠️ User is {overage:.2f} minutes over limit!")
        print(f"   📊 Remaining should be: 0 min left")
    else:
        print("   ✅ User is within limits")
    
    # What if period dates are wrong?
    if not in_current_period:
        print("   ⚠️ User is not in current subscription period!")
        print("   📊 Usage calculations may be incorrect")
    else:
        print("   ✅ User is in correct subscription period")
    
    # What if there are sessions outside the period?
    all_conversations = await db.conversation_sessions.find({
        "user_id": user_id
    }).to_list(length=None)
    
    outside_period_sessions = []
    for session in all_conversations:
        created = session.get('created_at')
        if created and (created < period_start or created >= period_end):
            outside_period_sessions.append(session)
    
    if outside_period_sessions:
        outside_minutes = sum(s.get('duration_minutes', 0) for s in outside_period_sessions)
        print(f"   📊 Sessions outside period: {len(outside_period_sessions)} ({outside_minutes:.2f} min)")
        print("   ✅ These are correctly excluded from current period calculations")
    else:
        print("   ✅ All sessions are within current period")
    print()
    
    # ========================================
    # 8. SUBSCRIPTION SERVICE VALIDATION
    # ========================================
    print("8️⃣ SUBSCRIPTION SERVICE VALIDATION")
    print("-" * 37)
    
    # Test the actual subscription service calculation
    try:
        from subscription_service import SubscriptionService
        
        # Get subscription status using the service
        status = await SubscriptionService.get_user_subscription_status(user_id)
        
        print("📊 SUBSCRIPTION SERVICE RESULTS:")
        print(f"   - Status: {status.status}")
        print(f"   - Plan: {status.plan}")
        print(f"   - Period: {status.period}")
        
        if status.limits:
            print(f"   - Minutes Used: {status.limits.minutes_used:.2f}")
            print(f"   - Minutes Remaining: {status.limits.minutes_remaining if status.limits.minutes_remaining != -1 else 'Unlimited'}")
            print(f"   - Sessions Used: {status.limits.sessions_used}")
            print(f"   - Sessions Remaining: {status.limits.sessions_remaining if status.limits.sessions_remaining != -1 else 'Unlimited'}")
            print(f"   - Assessments Used: {status.limits.assessments_used}")
            print(f"   - Assessments Remaining: {status.limits.assessments_remaining if status.limits.assessments_remaining != -1 else 'Unlimited'}")
            
            # Verify service calculations match our manual calculations
            service_minutes_used = status.limits.minutes_used
            service_minutes_remaining = status.limits.minutes_remaining
            
            if abs(service_minutes_used - actual_total_minutes) > 0.1:
                print(f"   ❌ SERVICE CALCULATION ERROR!")
                print(f"      Service: {service_minutes_used:.2f}, Actual: {actual_total_minutes:.2f}")
            else:
                print("   ✅ Service minutes calculation is correct")
            
            if service_minutes_remaining != -1 and abs(service_minutes_remaining - minutes_remaining) > 0.1:
                print(f"   ❌ SERVICE REMAINING CALCULATION ERROR!")
                print(f"      Service: {service_minutes_remaining:.2f}, Expected: {minutes_remaining:.2f}")
            else:
                print("   ✅ Service remaining calculation is correct")
        
    except Exception as e:
        print(f"   ❌ Error testing subscription service: {e}")
    print()
    
    # ========================================
    # 9. FINAL VERIFICATION SUMMARY
    # ========================================
    print("9️⃣ FINAL VERIFICATION SUMMARY")
    print("-" * 32)
    
    issues_found = []
    
    # Check for data discrepancies
    if minutes_diff > 0.1:
        issues_found.append(f"Minutes discrepancy: {minutes_diff:.2f} minutes")
    
    if sessions_diff > 0:
        issues_found.append(f"Sessions discrepancy: {sessions_diff} sessions")
    
    # Check for period issues
    if not in_current_period:
        issues_found.append("User not in current subscription period")
    
    # Check for over-limit usage
    if minutes_limit != -1 and actual_total_minutes > minutes_limit:
        issues_found.append(f"User over minutes limit by {actual_total_minutes - minutes_limit:.2f}")
    
    if sessions_limit != -1 and actual_total_sessions > sessions_limit:
        issues_found.append(f"User over sessions limit by {actual_total_sessions - sessions_limit}")
    
    print("🎯 VERIFICATION RESULTS:")
    if issues_found:
        print("   ❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"      - {issue}")
    else:
        print("   ✅ ALL CALCULATIONS ARE BULLETPROOF!")
    
    print()
    print("📊 DASHBOARD SHOULD DISPLAY:")
    print(f"   - Speaking Time: {minutes_remaining_display}")
    print(f"   - Sessions Used: {actual_total_sessions}/{sessions_limit if sessions_limit != -1 else '∞'}")
    print(f"   - Assessments Used: {user_assessments}/{assessments_limit if assessments_limit != -1 else '∞'}")
    
    # Create verification report
    verification_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "user_email": user.get('email'),
        "subscription_plan": plan_id,
        "subscription_period": period,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "user_record": {
            "minutes_used": user_minutes,
            "sessions_used": user_sessions,
            "assessments_used": user_assessments
        },
        "actual_usage": {
            "total_minutes": actual_total_minutes,
            "total_sessions": actual_total_sessions,
            "conversation_minutes": conv_total_minutes,
            "conversation_sessions": len(conversation_sessions),
            "learning_minutes": learning_total_minutes,
            "learning_sessions": learning_total_sessions
        },
        "subscription_limits": {
            "minutes_limit": minutes_limit,
            "sessions_limit": sessions_limit,
            "assessments_limit": assessments_limit
        },
        "calculated_remaining": {
            "minutes_remaining": minutes_remaining,
            "sessions_remaining": sessions_remaining,
            "assessments_remaining": assessments_remaining
        },
        "discrepancies": {
            "minutes_diff": minutes_diff,
            "sessions_diff": sessions_diff
        },
        "issues_found": issues_found,
        "is_bulletproof": len(issues_found) == 0
    }
    
    # Save report
    report_filename = f"bulletproof_verification_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(verification_report, f, indent=2, default=str)
    
    print(f"\n📄 Verification report saved: {report_filename}")
    
    await client.close()
    
    return verification_report

if __name__ == "__main__":
    asyncio.run(bulletproof_verification())
