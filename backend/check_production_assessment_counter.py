#!/usr/bin/env python3
"""
🔥 CRITICAL BUG FIX: Check Production Assessment Counter
Frontend shows 0/2 assessments but backend investigation showed assessments_used: 2
Need to check the actual production MongoDB database state
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

async def check_production_assessment_counter():
    """Check the actual production database state for assessment counter"""
    
    print("🔥 PRODUCTION DATABASE CHECK: Assessment Counter")
    print("=" * 55)
    
    # Test user details
    test_user_email = "alipala.ist@gmail.com"
    test_user_id = "688921c268819565ef1ce3dc"
    
    print(f"📋 Test User: {test_user_email}")
    print(f"📋 User ID: {test_user_id}")
    print(f"📋 Frontend Display: 0/2 assessments (from screenshot)")
    print()
    
    try:
        # Step 1: Check production database connection
        print("STEP 1: Production Database Connection")
        print("-" * 38)
        
        # Verify we're connected to production
        db_name = database.name
        print(f"✅ Connected to database: {db_name}")
        
        # Get database stats
        stats = await database.command("dbStats")
        print(f"✅ Database size: {stats.get('dataSize', 0)} bytes")
        print(f"✅ Collections: {stats.get('collections', 0)}")
        print()
        
        # Step 2: Get user document from production
        print("STEP 2: Production User Document")
        print("-" * 33)
        
        users_collection = database["users"]
        user_doc = await users_collection.find_one({"_id": ObjectId(test_user_id)})
        
        if not user_doc:
            print(f"❌ User not found with ID: {test_user_id}")
            return
        
        # Extract all assessment-related fields
        assessments_used = user_doc.get("assessments_used", 0)
        subscription_plan = user_doc.get("subscription_plan", "unknown")
        subscription_status = user_doc.get("subscription_status", "unknown")
        last_assessment_data = user_doc.get("last_assessment_data")
        assessment_history = user_doc.get("assessment_history")
        
        print(f"✅ User found: {user_doc.get('email', 'N/A')}")
        print(f"📊 CRITICAL: assessments_used = {assessments_used}")
        print(f"📋 Subscription plan: {subscription_plan}")
        print(f"📋 Subscription status: {subscription_status}")
        print(f"📋 Has last_assessment_data: {bool(last_assessment_data)}")
        print(f"📋 Has assessment_history: {bool(assessment_history)}")
        print()
        
        # Step 3: Calculate expected frontend display
        print("STEP 3: Frontend Display Calculation")
        print("-" * 36)
        
        if subscription_plan == "fluency_builder":
            assessments_limit = 2
            assessments_remaining = max(0, assessments_limit - assessments_used)
            
            print(f"📊 Plan: Fluency Builder (limit: {assessments_limit})")
            print(f"📊 Used: {assessments_used}")
            print(f"📊 Remaining: {assessments_remaining}")
            print(f"📊 Frontend should show: {assessments_remaining}/{assessments_limit}")
            print()
            
            # Compare with actual frontend display
            print("🔍 FRONTEND vs DATABASE COMPARISON:")
            print(f"   Frontend shows: 0/2 (from screenshot)")
            print(f"   Database shows: {assessments_remaining}/{assessments_limit}")
            
            if assessments_remaining == 0 and assessments_used == 2:
                print("   ❌ MISMATCH: Frontend shows 0/2 but database shows 0/2")
                print("   This suggests frontend is not reading assessments_used correctly!")
            elif assessments_remaining != 0:
                print(f"   ❌ MISMATCH: Database shows {assessments_remaining} remaining but frontend shows 0")
                print("   This confirms the frontend-backend disconnect!")
        print()
        
        # Step 4: Check subscription status endpoint simulation
        print("STEP 4: Subscription Status Endpoint Simulation")
        print("-" * 48)
        
        # Simulate what /api/stripe/subscription-status should return
        practice_minutes_used = user_doc.get("practice_minutes_used", 0.0)
        practice_sessions_used = user_doc.get("practice_sessions_used", 0)
        
        if subscription_plan == "fluency_builder":
            subscription_period = user_doc.get("subscription_period", "monthly")
            if subscription_period == "annual":
                minutes_limit = 1800
            else:
                minutes_limit = 150
            
            limits = {
                "is_unlimited": False,
                "minutes_limit": minutes_limit,
                "minutes_used": practice_minutes_used,
                "minutes_remaining": max(0, minutes_limit - practice_minutes_used),
                "sessions_limit": -1,  # Unlimited sessions
                "sessions_used": practice_sessions_used,
                "sessions_remaining": -1,
                "assessments_limit": 2,  # 2 assessments per period
                "assessments_used": assessments_used,
                "assessments_remaining": max(0, 2 - assessments_used)
            }
            
            print("✅ Subscription Status API Response (simulated):")
            print(f"   assessments_limit: {limits['assessments_limit']}")
            print(f"   assessments_used: {limits['assessments_used']}")
            print(f"   assessments_remaining: {limits['assessments_remaining']}")
            print()
            
            print("🔍 WHAT FRONTEND SHOULD RECEIVE:")
            print(f"   subscriptionStatus.limits.assessments_remaining = {limits['assessments_remaining']}")
            print(f"   subscriptionStatus.limits.assessments_limit = {limits['assessments_limit']}")
            print(f"   Display: {limits['assessments_remaining']}/{limits['assessments_limit']}")
        
        print()
        
        # Step 5: Check learning plans for evidence
        print("STEP 5: Learning Plans Evidence")
        print("-" * 32)
        
        learning_plans_collection = database["learning_plans"]
        user_plans = await learning_plans_collection.find({"user_id": test_user_id}).to_list(10)
        
        print(f"📊 Found {len(user_plans)} learning plans for user")
        
        plans_with_assessment = 0
        for i, plan in enumerate(user_plans, 1):
            has_assessment = bool(plan.get('assessment_data'))
            if has_assessment:
                plans_with_assessment += 1
            print(f"   Plan {i}: {plan.get('language', 'N/A')} - Assessment: {has_assessment}")
        
        print(f"\n📊 Learning plans with assessment data: {plans_with_assessment}")
        print(f"📊 Database assessments_used: {assessments_used}")
        
        if plans_with_assessment != assessments_used:
            print(f"❌ INCONSISTENCY: {plans_with_assessment} plans vs {assessments_used} counter")
        else:
            print("✅ Learning plans consistent with counter")
        print()
        
        # Step 6: Root cause analysis
        print("STEP 6: Root Cause Analysis")
        print("-" * 28)
        
        print("🔍 POSSIBLE CAUSES:")
        
        if assessments_used == 0:
            print("   1. ✅ Database is correct - user hasn't done assessments")
            print("   2. ✅ Frontend is correct - showing 0/2")
            print("   3. ❌ Previous investigation was wrong or using wrong database")
        elif assessments_used > 0:
            print(f"   1. ❌ Database shows {assessments_used} assessments used")
            print("   2. ❌ Frontend shows 0 assessments used")
            print("   3. 🔍 Frontend not fetching/displaying data correctly")
            print("   4. 🔍 API endpoint returning wrong data")
            print("   5. 🔍 Frontend caching old data")
        
        print()
        
        # Step 7: Recommendations
        print("STEP 7: Fix Recommendations")
        print("-" * 28)
        
        if assessments_used == 0:
            print("✅ NO BUG: System is working correctly")
            print("   - Database: 0 assessments used")
            print("   - Frontend: 0/2 displayed")
            print("   - User can take 2 assessments")
        else:
            print("🔧 FRONTEND BUG CONFIRMED:")
            print("   1. Check frontend API call to /api/stripe/subscription-status")
            print("   2. Verify frontend is parsing assessments_remaining correctly")
            print("   3. Check for caching issues in frontend")
            print("   4. Test API endpoint directly")
            print("   5. Clear browser cache and test again")
        
    except Exception as e:
        print(f"❌ Investigation failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_api_endpoint_directly():
    """Test the subscription status API endpoint logic directly"""
    
    print("\n" + "=" * 55)
    print("🧪 API ENDPOINT DIRECT TEST")
    print("=" * 55)
    
    test_user_id = "688921c268819565ef1ce3dc"
    
    try:
        users_collection = database["users"]
        user_doc = await users_collection.find_one({"_id": ObjectId(test_user_id)})
        
        if not user_doc:
            print("❌ User not found")
            return
        
        # Simulate the exact logic from stripe_routes.py
        subscription_status = user_doc.get("subscription_status", "free")
        subscription_plan = user_doc.get("subscription_plan", "try_learn")
        subscription_period = user_doc.get("subscription_period", "monthly")
        practice_minutes_used = user_doc.get("practice_minutes_used", 0.0)
        practice_sessions_used = user_doc.get("practice_sessions_used", 0)
        assessments_used = user_doc.get("assessments_used", 0)
        
        print(f"📊 Raw database values:")
        print(f"   subscription_plan: {subscription_plan}")
        print(f"   subscription_period: {subscription_period}")
        print(f"   assessments_used: {assessments_used}")
        print()
        
        # Calculate limits (exact logic from stripe_routes.py)
        if subscription_plan == "fluency_builder":
            if subscription_period == "annual":
                minutes_limit = 1800
            else:
                minutes_limit = 150
            
            minutes_remaining = max(0, minutes_limit - practice_minutes_used)
            
            limits = {
                "is_unlimited": False,
                "minutes_limit": minutes_limit,
                "minutes_used": practice_minutes_used,
                "minutes_remaining": minutes_remaining,
                "sessions_limit": -1,  # Unlimited sessions
                "sessions_used": practice_sessions_used,
                "sessions_remaining": -1,
                "assessments_limit": 2,  # 2 assessments per period (CORRECTED!)
                "assessments_used": assessments_used,
                "assessments_remaining": max(0, 2 - assessments_used)
            }
            
            print(f"📊 API Response (exact stripe_routes.py logic):")
            print(f"   limits.assessments_limit: {limits['assessments_limit']}")
            print(f"   limits.assessments_used: {limits['assessments_used']}")
            print(f"   limits.assessments_remaining: {limits['assessments_remaining']}")
            print()
            
            print(f"🎯 FRONTEND SHOULD DISPLAY:")
            print(f"   {limits['assessments_remaining']}/{limits['assessments_limit']}")
            
            if limits['assessments_remaining'] == 0:
                print("   🔒 Should show upgrade prompt (no assessments left)")
            else:
                print("   ✅ Should allow taking assessments")
                
        else:
            print(f"⚠️ Unexpected plan: {subscription_plan}")
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_production_assessment_counter())
    asyncio.run(test_api_endpoint_directly())
