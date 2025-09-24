#!/usr/bin/env python3
"""
🔥 TEST SCRIPT: Bulletproof Speaking Time Deduction Fix
This script tests the atomic speaking time tracking for Ali Pala's account.
"""

import asyncio
import logging
from datetime import datetime, timezone
from bson import ObjectId
from database import init_db, database
from models import SpeakingTimeTrackingRequest
from subscription_service_bulletproof_fix import BulletproofTracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ali Pala's user ID from MongoDB
ALI_PALA_USER_ID = "688921c268819565ef1ce3dc"

async def test_bulletproof_fix():
    """Test the bulletproof speaking time tracking fix"""
    
    print("🔥 TESTING BULLETPROOF SPEAKING TIME DEDUCTION FIX")
    print("=" * 80)
    
    try:
        # Initialize database connection
        print("🔌 Initializing database connection...")
        await init_db()
        print("✅ Database connected successfully")
        
        # Step 1: Get Ali Pala's current state
        print("\n📊 STEP 1: Getting Ali Pala's current subscription state")
        users_collection = database["users"]
        
        user = await users_collection.find_one({"_id": ObjectId(ALI_PALA_USER_ID)})
        if not user:
            print(f"❌ User not found: {ALI_PALA_USER_ID}")
            return False
            
        current_remaining = user.get("speaking_time_remaining", 150)
        subscription_status = user.get("subscription_status", "free")
        
        print(f"👤 User: {user.get('name', 'Ali Pala')} ({user.get('email', 'N/A')})")
        print(f"💰 Subscription: {subscription_status}")
        print(f"🕒 Current remaining time: {current_remaining} minutes")
        print(f"📊 Minutes used: {user.get('speaking_minutes_used', 0)}")
        
        # Step 2: Test the bulletproof tracker with a 5-minute session
        print("\n🧪 STEP 2: Testing 5-minute session deduction")
        
        # Create a test session ID
        session_id = f"test_session_{ALI_PALA_USER_ID}_{int(datetime.now().timestamp())}"
        
        # Create speaking time tracking request
        request = SpeakingTimeTrackingRequest(
            user_id=ALI_PALA_USER_ID,
            session_id=session_id,
            speaking_minutes=5.0,  # 5 minutes
            session_completed=True
        )
        
        print(f"📝 Test request:")
        print(f"   - User ID: {request.user_id}")
        print(f"   - Session ID: {request.session_id}")
        print(f"   - Minutes: {request.speaking_minutes}")
        print(f"   - Completed: {request.session_completed}")
        
        # Execute the bulletproof tracker
        print("\n🚀 Executing bulletproof atomic tracking...")
        success = await BulletproofTracker.track_speaking_time_atomic(request)
        
        if success:
            print("✅ Bulletproof tracking succeeded!")
        else:
            print("❌ Bulletproof tracking failed!")
            return False
        
        # Step 3: Verify the results
        print("\n🔍 STEP 3: Verifying deduction results")
        
        # Get updated user state
        updated_user = await users_collection.find_one({"_id": ObjectId(ALI_PALA_USER_ID)})
        new_remaining = updated_user.get("speaking_time_remaining", 150)
        new_used = updated_user.get("speaking_minutes_used", 0)
        
        print(f"🕒 Previous remaining: {current_remaining} minutes")
        print(f"🕒 New remaining: {new_remaining} minutes")
        print(f"📊 Previous used: {user.get('speaking_minutes_used', 0)} minutes")
        print(f"📊 New used: {new_used} minutes")
        
        # Check if deduction worked correctly
        expected_remaining = max(0, current_remaining - 5) if subscription_status != "active" else current_remaining
        expected_deduction = current_remaining - expected_remaining
        
        if new_remaining == expected_remaining:
            print(f"✅ Deduction correct! {expected_deduction} minutes deducted")
            
            # Step 4: Check tracking record
            print("\n📋 STEP 4: Verifying tracking record")
            tracking_collection = database["speaking_time_tracking"]
            tracking_record = await tracking_collection.find_one({
                "user_id": ALI_PALA_USER_ID,
                "session_id": session_id
            })
            
            if tracking_record:
                print("✅ Tracking record created successfully:")
                print(f"   - Successfully deducted: {tracking_record.get('successfully_deducted')}")
                print(f"   - Deducted amount: {tracking_record.get('deducted_amount')} minutes")
                print(f"   - Reason: {tracking_record.get('reason')}")
                print(f"   - Timestamp: {tracking_record.get('timestamp')}")
                
                if tracking_record.get('successfully_deducted') and tracking_record.get('deducted_amount') == expected_deduction:
                    print("✅ ALL TESTS PASSED! The bulletproof fix is working correctly.")
                    return True
                else:
                    print("❌ Tracking record shows issues")
                    return False
            else:
                print("❌ No tracking record found")
                return False
        else:
            print(f"❌ Deduction incorrect! Expected {expected_remaining}, got {new_remaining}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

async def test_idempotency():
    """Test that the idempotency protection works correctly"""
    
    print("\n🔄 TESTING IDEMPOTENCY PROTECTION")
    print("=" * 50)
    
    try:
        # Create a test session ID
        session_id = f"idempotency_test_{ALI_PALA_USER_ID}_{int(datetime.now().timestamp())}"
        
        # Create speaking time tracking request
        request = SpeakingTimeTrackingRequest(
            user_id=ALI_PALA_USER_ID,
            session_id=session_id,
            speaking_minutes=3.0,  # 3 minutes
            session_completed=True
        )
        
        # Get current state
        users_collection = database["users"]
        user = await users_collection.find_one({"_id": ObjectId(ALI_PALA_USER_ID)})
        current_remaining = user.get("speaking_time_remaining", 150)
        
        print(f"🕒 Current remaining: {current_remaining} minutes")
        print(f"📝 Testing session: {session_id}")
        
        # First call - should succeed
        print("\n🚀 First call (should succeed)...")
        success1 = await BulletproofTracker.track_speaking_time_atomic(request)
        print(f"Result: {'✅ SUCCESS' if success1 else '❌ FAILED'}")
        
        # Second call - should be idempotent (return success but no deduction)
        print("\n🚀 Second call (should be idempotent)...")
        success2 = await BulletproofTracker.track_speaking_time_atomic(request)
        print(f"Result: {'✅ SUCCESS' if success2 else '❌ FAILED'}")
        
        # Verify only one deduction occurred
        updated_user = await users_collection.find_one({"_id": ObjectId(ALI_PALA_USER_ID)})
        new_remaining = updated_user.get("speaking_time_remaining", 150)
        
        subscription_status = user.get("subscription_status", "free")
        expected_deduction = 3 if subscription_status != "active" else 0
        expected_remaining = current_remaining - expected_deduction
        
        if new_remaining == expected_remaining:
            print(f"✅ Idempotency test passed! Only one deduction of {expected_deduction} minutes occurred")
            return True
        else:
            print(f"❌ Idempotency test failed! Expected {expected_remaining}, got {new_remaining}")
            return False
            
    except Exception as e:
        print(f"❌ Idempotency test failed: {str(e)}")
        return False

async def cleanup_test_data():
    """Clean up test tracking records"""
    print("\n🧹 CLEANING UP TEST DATA")
    print("=" * 30)
    
    try:
        tracking_collection = database["speaking_time_tracking"]
        
        # Remove test tracking records
        result = await tracking_collection.delete_many({
            "user_id": ALI_PALA_USER_ID,
            "session_id": {"$regex": "^(test_session_|idempotency_test_)"}
        })
        
        print(f"🗑️ Removed {result.deleted_count} test tracking records")
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")

async def main():
    """Run all tests"""
    print("🎯 BULLETPROOF SPEAKING TIME FIX - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"🔍 Testing with Ali Pala's account: {ALI_PALA_USER_ID}")
    print(f"⏰ Test started at: {datetime.now(timezone.utc)}")
    print()
    
    # Test 1: Basic functionality
    test1_passed = await test_bulletproof_fix()
    
    # Test 2: Idempotency protection  
    test2_passed = await test_idempotency()
    
    # Cleanup
    await cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"🧪 Basic functionality test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"🔄 Idempotency protection test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🔥 The bulletproof speaking time fix is working correctly!")
        print("✅ Ali Pala's account will now properly deduct speaking time.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 The bulletproof fix needs additional work.")
        return False

if __name__ == "__main__":
    asyncio.run(main())
