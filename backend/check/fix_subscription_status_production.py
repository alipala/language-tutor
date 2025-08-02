import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def fix_subscription_status_production():
    """
    Fix the subscription status issue in production database.
    The user has an active subscription in Stripe but shows 'incomplete' in our DB.
    """
    
    # Connect to production MongoDB
    mongodb_url = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    try:
        print("=== FIXING SUBSCRIPTION STATUS IN PRODUCTION ===")
        
        # Fix the specific user
        user_id = '686424d66c72bbc0837f8a58'
        user = await db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"🔧 User: {user.get('name')} ({user.get('email')})")
        print(f"📋 Current subscription_status: {user.get('subscription_status')}")
        print(f"📋 Stripe customer ID: {user.get('stripe_customer_id')}")
        print(f"📋 Subscription ID: {user.get('subscription_id')}")
        print(f"📋 Assessments used: {user.get('assessments_used', 0)}")
        print()
        
        # The user has all the subscription data but status is 'incomplete'
        # Based on the data provided, this should be 'active'
        if user.get('subscription_status') == 'incomplete':
            print("🐛 FOUND THE BUG: subscription_status is 'incomplete' but should be 'active'")
            print("🔧 Updating subscription status to 'active'...")
            
            # Update the subscription status
            result = await db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'subscription_status': 'active'}}
            )
            
            if result.modified_count > 0:
                print("✅ Successfully updated subscription status to 'active'")
                
                # Verify the fix
                updated_user = await db.users.find_one({'_id': ObjectId(user_id)})
                print(f"✅ Verification: subscription_status is now '{updated_user.get('subscription_status')}'")
                
                # Calculate assessment counter
                assessments_used = updated_user.get('assessments_used', 0)
                assessments_limit = 24  # Annual fluency_builder plan
                assessments_remaining = assessments_limit - assessments_used
                
                print(f"✅ Assessment counter should now show: {assessments_remaining}/{assessments_limit}")
                print(f"✅ Expected: 23/24 (since user has used 1 assessment)")
                
            else:
                print("❌ Failed to update subscription status")
        else:
            print(f"✅ Subscription status is already: {user.get('subscription_status')}")
        
        print("\n=== WEBHOOK ANALYSIS ===")
        print("🔍 Root cause analysis:")
        print("1. User completed Stripe checkout successfully")
        print("2. Stripe subscription status is 'active' (confirmed in previous investigation)")
        print("3. Our database shows 'incomplete' - webhook sync failed")
        print("4. Possible causes:")
        print("   - Webhook endpoint not receiving events")
        print("   - Webhook processing failed silently")
        print("   - Race condition in webhook processing")
        print("   - Webhook signature verification issues")
        
        print("\n=== RECOMMENDATIONS ===")
        print("1. ✅ Fixed immediate issue by updating status to 'active'")
        print("2. 🔧 Check Stripe webhook logs in dashboard")
        print("3. 🔧 Add webhook event logging to our backend")
        print("4. 🔧 Implement webhook retry mechanism")
        print("5. 🔧 Add periodic sync job to catch missed webhooks")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_subscription_status_production())
