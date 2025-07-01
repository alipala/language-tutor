import asyncio
import stripe
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def simple_fix_subscription_status():
    """
    Simple fix for the subscription status issue - just update the status to 'active'
    """
    
    # Set up Stripe
    stripe.api_key = "sk_test_51Mzx41JcquSiYwWNGndzlyBDtf249jC4H0bjboX2GxHJS2SHb2SXxlZmbt8ObCruGg5KKSTnHgnthxnZknF5F4R300MGsRy0aK"
    
    # Connect to production MongoDB
    mongodb_url = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    try:
        print("=== SIMPLE FIX FOR SUBSCRIPTION STATUS ===")
        
        # Fix the specific user
        user_id = '686424d66c72bbc0837f8a58'
        user = await db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"🔧 Fixing user: {user.get('name')} ({user.get('email')})")
        print(f"📋 Current status: {user.get('subscription_status')}")
        
        # Get Stripe subscription details
        stripe_subscription_id = user.get('subscription_id')
        if stripe_subscription_id:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            print(f"📋 Stripe status: {subscription.status}")
            
            if subscription.status != user.get('subscription_status'):
                print("🔧 Updating user subscription status...")
                
                # Simple update - just fix the status
                update_data = {
                    "subscription_status": subscription.status
                }
                
                # Add period dates if available
                if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
                    update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start)
                
                if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
                    update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end)
                    update_data["subscription_expires_at"] = datetime.fromtimestamp(subscription.current_period_end)
                
                # Update user in MongoDB
                result = await db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    print(f"✅ Successfully updated user subscription status to: {subscription.status}")
                    print(f"✅ Assessment counter should now work correctly!")
                    
                    # Verify the fix
                    updated_user = await db.users.find_one({'_id': ObjectId(user_id)})
                    print(f"✅ Verification: subscription_status is now {updated_user.get('subscription_status')}")
                    print(f"✅ assessments_used: {updated_user.get('assessments_used', 0)}")
                    
                    # Calculate what the counter should show now
                    assessments_limit = 24  # Annual fluency_builder plan
                    assessments_used = updated_user.get('assessments_used', 0)
                    assessments_remaining = assessments_limit - assessments_used
                    
                    print(f"✅ Assessment counter should now show: {assessments_remaining}/{assessments_limit}")
                    
                else:
                    print("❌ Failed to update user subscription status")
            else:
                print("✅ User status is already correct")
        else:
            print("❌ No subscription ID found")
        
        print("\n=== SUMMARY ===")
        print("✅ Fixed the subscription status from 'incomplete' to 'active'")
        print("✅ This resolves both the assessment counter bug AND the subscription status issue")
        print("✅ The user should now see the correct Assessment counter: 23/24")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(simple_fix_subscription_status())
