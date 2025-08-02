import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def fix_assessment_counter_bug():
    """
    Fix the assessment counter bug where assessments_used is not being incremented
    when users complete assessments and create learning plans.
    """
    
    # Connect to production MongoDB using the Railway production URL
    mongodb_url = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    try:
        print("=== FIXING ASSESSMENT COUNTER BUG ===")
        
        # Step 1: Find users who have learning plans with assessment data but assessments_used = 0
        print("Step 1: Finding users with assessment counter bug...")
        
        # Find all learning plans that have assessment data
        learning_plans_with_assessments = await db.learning_plans.find({
            "assessment_data": {"$exists": True, "$ne": None}
        }).to_list(length=None)
        
        print(f"Found {len(learning_plans_with_assessments)} learning plans with assessment data")
        
        users_to_fix = []
        
        for plan in learning_plans_with_assessments:
            user_id = plan.get('user_id')
            if not user_id:
                continue
                
            # Get the user
            user = await db.users.find_one({'_id': ObjectId(user_id)})
            if not user:
                continue
            
            assessments_used = user.get('assessments_used', 0)
            
            # Count how many learning plans with assessments this user has
            user_assessment_plans = await db.learning_plans.count_documents({
                "user_id": user_id,
                "assessment_data": {"$exists": True, "$ne": None}
            })
            
            # If assessments_used is less than the number of assessment plans, there's a bug
            if assessments_used < user_assessment_plans:
                users_to_fix.append({
                    'user_id': user_id,
                    'email': user.get('email'),
                    'current_assessments_used': assessments_used,
                    'expected_assessments_used': user_assessment_plans,
                    'learning_plans_count': user_assessment_plans
                })
        
        print(f"Found {len(users_to_fix)} users with assessment counter bug")
        
        # Step 2: Display users that need fixing
        if users_to_fix:
            print("\nUsers with assessment counter bug:")
            for user in users_to_fix:
                print(f"  - {user['email']} (ID: {user['user_id']})")
                print(f"    Current assessments_used: {user['current_assessments_used']}")
                print(f"    Should be: {user['expected_assessments_used']}")
                print(f"    Learning plans with assessments: {user['learning_plans_count']}")
                print()
        
        # Step 3: Fix the specific user mentioned in the bug report
        target_user_id = '686424d66c72bbc0837f8a58'
        target_user = next((u for u in users_to_fix if u['user_id'] == target_user_id), None)
        
        if target_user:
            print(f"Step 3: Fixing the specific user {target_user['email']}...")
            
            # Update the assessments_used counter
            result = await db.users.update_one(
                {'_id': ObjectId(target_user_id)},
                {'$set': {'assessments_used': target_user['expected_assessments_used']}}
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated assessments_used from {target_user['current_assessments_used']} to {target_user['expected_assessments_used']}")
                
                # Verify the fix
                updated_user = await db.users.find_one({'_id': ObjectId(target_user_id)})
                print(f"✅ Verification: assessments_used is now {updated_user.get('assessments_used', 0)}")
                
                # Calculate what the counter should show now
                # For annual fluency_builder plan: 24 assessments total
                assessments_limit = 24
                assessments_used = updated_user.get('assessments_used', 0)
                assessments_remaining = assessments_limit - assessments_used
                
                print(f"✅ Assessment counter should now show: {assessments_remaining}/{assessments_limit}")
                
            else:
                print("❌ Failed to update the user")
        else:
            print(f"Target user {target_user_id} not found in the list of users to fix")
        
        # Step 4: Identify the root cause
        print("\n=== ROOT CAUSE ANALYSIS ===")
        print("The bug occurs because when users complete assessments and create learning plans,")
        print("the system is not properly incrementing the 'assessments_used' counter.")
        print()
        print("This likely happens in one of these places:")
        print("1. When the assessment is completed (speaking_assessment.py)")
        print("2. When the learning plan is created (learning_routes.py)")
        print("3. When subscription usage is tracked (subscription_service.py)")
        print()
        print("The fix should ensure that every time an assessment is completed,")
        print("the assessments_used counter is incremented.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_assessment_counter_bug())
