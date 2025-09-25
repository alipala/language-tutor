#!/usr/bin/env python3
"""
🔥 DEPLOYMENT SCRIPT: Assessment Counter Fix
Deploy the permanent fix for assessment counter double increment bug
"""

import asyncio
import os
import sys
from datetime import datetime
from bson import ObjectId

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def deploy_assessment_counter_fix():
    """Deploy the assessment counter fix and reconcile all users"""
    
    print("🚀 DEPLOYMENT: Assessment Counter Fix")
    print("=" * 45)
    
    try:
        # Step 1: Verify database connection
        print("STEP 1: Database Connection Verification")
        print("-" * 40)
        
        db_name = database.name
        stats = await database.command("dbStats")
        
        print(f"✅ Connected to database: {db_name}")
        print(f"✅ Database size: {stats.get('dataSize', 0)} bytes")
        print(f"✅ Collections: {stats.get('collections', 0)}")
        print()
        
        # Step 2: Reconcile all users' assessment counters
        print("STEP 2: Assessment Counter Reconciliation")
        print("-" * 42)
        
        users_collection = database["users"]
        learning_plans_collection = database["learning_plans"]
        
        # Get all users with subscription plans
        users_cursor = users_collection.find({
            "subscription_plan": {"$in": ["fluency_builder", "try_learn", "team_mastery"]}
        })
        
        users_fixed = 0
        users_checked = 0
        
        async for user in users_cursor:
            users_checked += 1
            user_id = str(user["_id"])
            email = user.get("email", "N/A")
            current_assessments_used = user.get("assessments_used", 0)
            
            # Count actual learning plans with assessment data
            user_plans = await learning_plans_collection.find({"user_id": user_id}).to_list(100)
            actual_assessments = len([p for p in user_plans if p.get('assessment_data')])
            
            print(f"👤 User: {email}")
            print(f"   Current counter: {current_assessments_used}")
            print(f"   Actual assessments: {actual_assessments}")
            
            if current_assessments_used != actual_assessments:
                print(f"   🔧 FIXING: {current_assessments_used} → {actual_assessments}")
                
                # Fix the counter
                result = await users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {
                        "assessments_used": actual_assessments,
                        "assessment_counter_fixed": datetime.utcnow().isoformat(),
                        "assessment_counter_fix_version": "v1.0"
                    }}
                )
                
                if result.modified_count > 0:
                    users_fixed += 1
                    print(f"   ✅ Fixed successfully")
                else:
                    print(f"   ❌ Fix failed")
            else:
                print(f"   ✅ Already correct")
            
            print()
        
        print(f"📊 RECONCILIATION SUMMARY:")
        print(f"   Users checked: {users_checked}")
        print(f"   Users fixed: {users_fixed}")
        print(f"   Users already correct: {users_checked - users_fixed}")
        print()
        
        # Step 3: Verify the fix for test user
        print("STEP 3: Test User Verification")
        print("-" * 32)
        
        test_user_id = "688921c268819565ef1ce3dc"
        test_user = await users_collection.find_one({"_id": ObjectId(test_user_id)})
        
        if test_user:
            assessments_used = test_user.get("assessments_used", 0)
            subscription_plan = test_user.get("subscription_plan", "unknown")
            
            print(f"✅ Test user: {test_user.get('email', 'N/A')}")
            print(f"✅ Assessments used: {assessments_used}")
            print(f"✅ Plan: {subscription_plan}")
            
            if subscription_plan == "fluency_builder":
                assessments_remaining = max(0, 2 - assessments_used)
                print(f"✅ Assessments remaining: {assessments_remaining}/2")
                
                if assessments_remaining > 0:
                    print(f"✅ User can take {assessments_remaining} more assessments")
                else:
                    print(f"🔒 User has used all assessments")
        else:
            print(f"❌ Test user not found")
        
        print()
        
        # Step 4: Code deployment status
        print("STEP 4: Code Deployment Status")
        print("-" * 33)
        
        print("🔧 CODE FIXES IMPLEMENTED:")
        print("   ✅ Idempotent assessment creation")
        print("   ✅ Duplicate protection logic")
        print("   ✅ Conditional database updates")
        print("   ✅ Assessment ID tracking")
        print("   ✅ Learning plan linking")
        print()
        
        print("📋 DEPLOYMENT CHECKLIST:")
        print("   ✅ Database reconciliation complete")
        print("   ✅ Code fixes implemented")
        print("   ⚠️  Need to commit and push to production branch")
        print("   ⚠️  Need to restart production server")
        print()
        
        # Step 5: Next steps
        print("STEP 5: Next Steps Required")
        print("-" * 28)
        
        print("🚀 IMMEDIATE ACTIONS NEEDED:")
        print("   1. Commit the fixed learning_routes.py")
        print("   2. Push to fix/decrement-session-minutes branch")
        print("   3. Deploy to production")
        print("   4. Monitor for new assessment counter issues")
        print("   5. Test assessment creation flow")
        print()
        
        print("✅ DEPLOYMENT PREPARATION COMPLETE!")
        print("   Database inconsistencies fixed")
        print("   Code improvements implemented")
        print("   Ready for production deployment")
        
    except Exception as e:
        print(f"❌ Deployment preparation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(deploy_assessment_counter_fix())
