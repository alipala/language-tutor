#!/usr/bin/env python3
"""
🔥 CRITICAL BUG FIX: Assessment Display Bug
Database shows assessments_used = 2, but frontend shows 0/2
The frontend is misinterpreting the API response.

ISSUE: Frontend shows "0/2" but this should mean "0 remaining out of 2" not "0 used out of 2"
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

async def fix_assessment_display_bug():
    """Fix the assessment display bug by correcting the user's assessment counter"""
    
    print("🔥 ASSESSMENT DISPLAY BUG FIX")
    print("=" * 35)
    
    # Test user details
    test_user_email = "alipala.ist@gmail.com"
    test_user_id = "688921c268819565ef1ce3dc"
    
    print(f"📋 Test User: {test_user_email}")
    print(f"📋 User ID: {test_user_id}")
    print()
    
    try:
        # Step 1: Analyze current state
        print("STEP 1: Current State Analysis")
        print("-" * 30)
        
        users_collection = database["users"]
        user_doc = await users_collection.find_one({"_id": ObjectId(test_user_id)})
        
        if not user_doc:
            print(f"❌ User not found with ID: {test_user_id}")
            return
        
        assessments_used = user_doc.get("assessments_used", 0)
        subscription_plan = user_doc.get("subscription_plan", "unknown")
        
        print(f"✅ Current assessments_used: {assessments_used}")
        print(f"✅ Subscription plan: {subscription_plan}")
        
        # Check learning plans
        learning_plans_collection = database["learning_plans"]
        user_plans = await learning_plans_collection.find({"user_id": test_user_id}).to_list(10)
        plans_with_assessment = len([p for p in user_plans if p.get('assessment_data')])
        
        print(f"✅ Learning plans with assessments: {plans_with_assessment}")
        print()
        
        # Step 2: Identify the problem
        print("STEP 2: Problem Identification")
        print("-" * 32)
        
        print("🔍 ANALYSIS:")
        print(f"   Database: assessments_used = {assessments_used}")
        print(f"   Learning plans: {plans_with_assessment} with assessment data")
        print(f"   Expected: assessments_used should equal learning plans with assessments")
        
        if assessments_used != plans_with_assessment:
            print(f"   ❌ INCONSISTENCY FOUND!")
            print(f"   The assessment counter ({assessments_used}) doesn't match actual assessments ({plans_with_assessment})")
            
            # Determine correct value
            correct_assessments_used = plans_with_assessment
            print(f"   ✅ Correct value should be: {correct_assessments_used}")
            
            # Step 3: Fix the counter
            print("\nSTEP 3: Fixing Assessment Counter")
            print("-" * 35)
            
            print(f"🔧 Updating assessments_used from {assessments_used} to {correct_assessments_used}")
            
            result = await users_collection.update_one(
                {"_id": ObjectId(test_user_id)},
                {"$set": {"assessments_used": correct_assessments_used}}
            )
            
            if result.modified_count > 0:
                print("✅ Assessment counter fixed successfully!")
                
                # Verify the fix
                updated_user = await users_collection.find_one({"_id": ObjectId(test_user_id)})
                new_assessments_used = updated_user.get("assessments_used", 0)
                
                print(f"✅ Verification: assessments_used = {new_assessments_used}")
                
                # Calculate what frontend should now show
                if subscription_plan == "fluency_builder":
                    assessments_limit = 2
                    assessments_remaining = max(0, assessments_limit - new_assessments_used)
                    
                    print(f"✅ Frontend should now show: {assessments_remaining}/{assessments_limit}")
                    
                    if assessments_remaining == 0:
                        print("✅ User should see upgrade prompt (no assessments left)")
                    else:
                        print(f"✅ User can take {assessments_remaining} more assessments")
                        
            else:
                print("❌ Failed to update assessment counter")
                
        else:
            print("✅ Assessment counter is already correct")
            
            # The issue might be in frontend interpretation
            print("\nSTEP 3: Frontend Display Analysis")
            print("-" * 36)
            
            if subscription_plan == "fluency_builder":
                assessments_limit = 2
                assessments_remaining = max(0, assessments_limit - assessments_used)
                
                print(f"📊 API should return:")
                print(f"   assessments_limit: {assessments_limit}")
                print(f"   assessments_used: {assessments_used}")
                print(f"   assessments_remaining: {assessments_remaining}")
                
                print(f"\n📱 Frontend should display:")
                print(f"   {assessments_remaining}/{assessments_limit} (remaining/total)")
                
                if assessments_remaining == 0:
                    print("   🔒 Should show upgrade prompt")
                    print("   🔒 Should disable assessment button")
                else:
                    print("   ✅ Should allow taking assessments")
                    
                print(f"\n🔍 Current frontend shows: 0/2")
                if assessments_remaining == 0:
                    print("   ✅ This is CORRECT if it means '0 remaining out of 2'")
                    print("   ❌ This is WRONG if it means '0 used out of 2'")
                    
                    print(f"\n🔧 FRONTEND FIX NEEDED:")
                    print(f"   The frontend should show that assessments are exhausted")
                    print(f"   It should display upgrade prompt or disable assessment button")
        
        print()
        
        # Step 4: Test the API response
        print("STEP 4: API Response Test")
        print("-" * 25)
        
        # Get fresh user data
        fresh_user = await users_collection.find_one({"_id": ObjectId(test_user_id)})
        fresh_assessments_used = fresh_user.get("assessments_used", 0)
        
        # Simulate API response
        if subscription_plan == "fluency_builder":
            limits = {
                "assessments_limit": 2,
                "assessments_used": fresh_assessments_used,
                "assessments_remaining": max(0, 2 - fresh_assessments_used)
            }
            
            print(f"📡 API Response:")
            print(f"   {limits}")
            
            print(f"\n🎯 Frontend should interpret this as:")
            print(f"   User has used {limits['assessments_used']} out of {limits['assessments_limit']} assessments")
            print(f"   User has {limits['assessments_remaining']} assessments remaining")
            
            if limits['assessments_remaining'] == 0:
                print(f"   🔒 Should show: 'You have used all your assessments. Upgrade to get more.'")
            else:
                print(f"   ✅ Should show: 'You have {limits['assessments_remaining']} assessments remaining'")
        
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_assessment_display_bug())
