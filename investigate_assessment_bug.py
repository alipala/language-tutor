import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def investigate_bug():
    # Connect to production MongoDB using the Railway production URL
    mongodb_url = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    try:
        # Check the specific user from the bug report
        user_id = '686424d66c72bbc0837f8a58'
        user = await db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            print(f"User {user_id} not found")
            return
        
        print("=== USER SUBSCRIPTION DATA ===")
        print(f"User ID: {user_id}")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Name: {user.get('name', 'N/A')}")
        print(f"Subscription Plan: {user.get('subscription_plan', 'not set')}")
        print(f"Subscription Period: {user.get('subscription_period', 'not set')}")
        print(f"Subscription Status: {user.get('subscription_status', 'not set')}")
        print(f"Practice Sessions Used: {user.get('practice_sessions_used', 0)}")
        print(f"Assessments Used: {user.get('assessments_used', 0)}")
        print()
        
        # Check subscription limits calculation
        print("=== SUBSCRIPTION LIMITS CALCULATION ===")
        
        # Import subscription service logic
        import sys
        sys.path.append('./backend')
        from subscription_service import SubscriptionService
        
        # Get subscription status
        status = await SubscriptionService.get_user_subscription_status(user_id)
        print(f"Plan: {status.plan}")
        print(f"Period: {status.period}")
        print(f"Status: {status.status}")
        
        if status.limits:
            print(f"Sessions Limit: {status.limits.sessions_limit}")
            print(f"Sessions Used: {status.limits.sessions_used}")
            print(f"Sessions Remaining: {status.limits.sessions_remaining}")
            print(f"Assessments Limit: {status.limits.assessments_limit}")
            print(f"Assessments Used: {status.limits.assessments_used}")
            print(f"Assessments Remaining: {status.limits.assessments_remaining}")
            print(f"Is Unlimited: {status.limits.is_unlimited}")
        else:
            print("No limits calculated")
        
        print()
        
        # Check the subscription plans configuration
        print("=== SUBSCRIPTION PLANS CONFIGURATION ===")
        plans = SubscriptionService.get_all_plans()
        for plan_id, plan in plans.items():
            print(f"{plan_id}:")
            print(f"  Monthly Assessments: {plan.monthly_assessments}")
            print(f"  Annual Assessments: {plan.annual_assessments}")
            print(f"  Monthly Sessions: {plan.monthly_sessions}")
            print(f"  Annual Sessions: {plan.annual_sessions}")
        
        print()
        
        # Check learning plans for this user
        print("=== USER LEARNING PLANS ===")
        learning_plans = await db.learning_plans.find({'user_id': user_id}).to_list(length=None)
        print(f"Number of learning plans: {len(learning_plans)}")
        
        for i, plan in enumerate(learning_plans):
            print(f"Plan {i+1}:")
            print(f"  ID: {plan.get('id')}")
            print(f"  Language: {plan.get('language')}")
            print(f"  Level: {plan.get('proficiency_level')}")
            print(f"  Created: {plan.get('created_at')}")
            print(f"  Has Assessment Data: {bool(plan.get('assessment_data'))}")
        
        print()
        
        # Analyze the bug
        print("=== BUG ANALYSIS ===")
        expected_assessments_used = 1  # User completed 1 assessment
        actual_assessments_used = user.get('assessments_used', 0)
        
        print(f"Expected assessments_used: {expected_assessments_used}")
        print(f"Actual assessments_used: {actual_assessments_used}")
        
        if status.limits:
            expected_remaining = status.limits.assessments_limit - expected_assessments_used
            actual_remaining = status.limits.assessments_remaining
            
            print(f"Expected assessments remaining: {expected_remaining}")
            print(f"Actual assessments remaining: {actual_remaining}")
            
            if actual_remaining != expected_remaining:
                print("🐛 BUG CONFIRMED: Assessment counter is incorrect!")
                print(f"The counter should show {expected_remaining}/{status.limits.assessments_limit}")
                print(f"But it shows {actual_remaining}/{status.limits.assessments_limit}")
            else:
                print("✅ Assessment counter appears correct")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(investigate_bug())
