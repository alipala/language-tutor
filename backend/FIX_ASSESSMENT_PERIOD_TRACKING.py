#!/usr/bin/env python3
"""
FIX ASSESSMENT PERIOD TRACKING

PROBLEM IDENTIFIED:
- Dashboard shows -2/2 assessments (negative remaining)
- System counts ALL assessments (4) instead of current period assessments (1)
- User completed Dutch assessment on Sept 23, 2025
- Current subscription period: Sept 9 - Oct 9, 2025
- Only 1 assessment should count, so user should have 1/2 remaining

ROOT CAUSE:
The assessment counter (assessments_used) tracks ALL assessments ever created,
but it should only track assessments in the CURRENT subscription period.

SOLUTION:
1. Fix the assessment counter to only count current period assessments
2. Update the dashboard calculation logic
3. Ensure new assessments check subscription period before incrementing
"""

import asyncio
from database import database, init_db
from datetime import datetime, timezone
from bson import ObjectId

async def fix_assessment_period_tracking():
    """Fix assessment tracking to only count current subscription period"""
    
    await init_db()
    
    print("🔧 FIXING ASSESSMENT PERIOD TRACKING")
    print("=" * 60)
    
    users_collection = database.users
    learning_plans_collection = database.learning_plans
    
    # Get all users with subscriptions
    users = await users_collection.find({
        "current_period_start": {"$exists": True}
    }).to_list(length=None)
    
    fixed_users = 0
    
    for user in users:
        user_id = str(user["_id"])
        email = user.get("email", "unknown")
        current_assessments_used = user.get("assessments_used", 0)
        
        # Get subscription period
        current_period_start = user.get("current_period_start")
        if not current_period_start:
            continue
            
        # Convert to naive datetime for comparison
        if current_period_start.tzinfo:
            period_start_naive = current_period_start.replace(tzinfo=None)
        else:
            period_start_naive = current_period_start
        
        # Get all learning plans with assessment data for this user
        learning_plans = await learning_plans_collection.find({"user_id": user_id}).to_list(length=None)
        
        # Count assessments in current period only
        assessments_in_current_period = 0
        total_assessments = 0
        
        for plan in learning_plans:
            if plan.get("assessment_data"):
                total_assessments += 1
                created_at = plan.get("created_at", "")
                
                try:
                    # Parse assessment date
                    assessment_date_str = created_at.replace('Z', '').replace('+00:00', '')
                    if 'T' in assessment_date_str:
                        assessment_date = datetime.fromisoformat(assessment_date_str)
                    else:
                        assessment_date = datetime.strptime(assessment_date_str, '%Y-%m-%d %H:%M:%S')
                    
                    # Check if in current period
                    if assessment_date >= period_start_naive:
                        assessments_in_current_period += 1
                        
                except Exception as e:
                    print(f"   ⚠️ Error parsing date for {email}: {str(e)}")
        
        # Update if there's a mismatch
        if assessments_in_current_period != current_assessments_used:
            print(f"👤 {email}")
            print(f"   Total assessments ever: {total_assessments}")
            print(f"   Assessments in current period: {assessments_in_current_period}")
            print(f"   Current counter: {current_assessments_used}")
            print(f"   Period start: {period_start_naive}")
            
            # Update the counter to reflect only current period
            result = await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"assessments_used": assessments_in_current_period}}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Fixed counter: {current_assessments_used} → {assessments_in_current_period}")
                fixed_users += 1
                
                # Calculate remaining
                assessments_limit = user.get("assessments_limit", 2)
                remaining = assessments_limit - assessments_in_current_period
                print(f"   📊 Dashboard will now show: {remaining}/{assessments_limit}")
            else:
                print(f"   ❌ Failed to update counter")
            print()
    
    print("📊 SUMMARY:")
    print(f"   Users processed: {len(users)}")
    print(f"   Users fixed: {fixed_users}")
    
    # Verify Ali's specific case
    print("\n🔍 VERIFYING ALI'S CASE:")
    print("-" * 40)
    
    ali_user = await users_collection.find_one({"email": "alipala.ist@gmail.com"})
    if ali_user:
        assessments_used = ali_user.get("assessments_used", 0)
        assessments_limit = ali_user.get("assessments_limit", 2)
        remaining = assessments_limit - assessments_used
        
        print(f"   assessments_used: {assessments_used}")
        print(f"   assessments_limit: {assessments_limit}")
        print(f"   Dashboard shows: {remaining}/{assessments_limit}")
        
        if remaining >= 0:
            print("   ✅ Dashboard now shows positive remaining assessments!")
        else:
            print("   ❌ Dashboard still shows negative remaining")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Update assessment increment logic to check subscription period")
    print("2. Test with a new assessment to verify period-based tracking")
    print("3. Deploy the fix to production")

if __name__ == "__main__":
    asyncio.run(fix_assessment_period_tracking())
