import asyncio
import stripe
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def fix_stripe_webhook_sync_issue():
    """
    Fix the Stripe webhook synchronization issue by updating user subscription status
    and improving webhook handling robustness.
    """
    
    # Set up Stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return
    
    # Connect to production MongoDB
    mongodb_url = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    try:
        print("=== FIXING STRIPE WEBHOOK SYNC ISSUE ===")
        
        # Fix the specific user first
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
                
                update_data = {
                    "subscription_status": subscription.status,
                    "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                    "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                    "subscription_expires_at": datetime.fromtimestamp(subscription.current_period_end)
                }
                
                # Get plan details - handle Stripe API response properly
                try:
                    if hasattr(subscription, 'items') and subscription.items and hasattr(subscription.items, 'data') and len(subscription.items.data) > 0:
                        price = subscription.items.data[0].price
                        if price:
                            update_data["subscription_price_id"] = price.id
                            
                            # Get product details
                            product = stripe.Product.retrieve(price.product)
                            plan_id = product.name.lower().replace(" ", "_").replace("-", "")
                            if "fluency builder" in product.name.lower():
                                plan_id = "fluency_builder"
                            elif "team mastery" in product.name.lower():
                                plan_id = "team_mastery"
                            elif "try learn" in product.name.lower():
                                plan_id = "try_learn"
                            
                            update_data["subscription_plan"] = plan_id
                            
                            # Determine if monthly or annual
                            if hasattr(price, 'recurring') and price.recurring and hasattr(price.recurring, 'interval'):
                                update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"
                except Exception as e:
                    print(f"   ⚠️ Warning: Could not get plan details: {str(e)}")
                
                # Update user in MongoDB
                result = await db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    print(f"✅ Successfully updated user subscription status to: {subscription.status}")
                    print(f"✅ Assessment counter should now work correctly!")
                else:
                    print("❌ Failed to update user subscription status")
            else:
                print("✅ User status is already correct")
        
        # Now find and fix other users with similar issues
        print("\n=== FINDING OTHER USERS WITH SYNC ISSUES ===")
        
        # Find users with incomplete status but active Stripe subscriptions
        users_with_incomplete = await db.users.find({
            "subscription_status": "incomplete",
            "stripe_customer_id": {"$exists": True, "$ne": None}
        }).to_list(length=50)
        
        print(f"📋 Found {len(users_with_incomplete)} users with 'incomplete' status")
        
        fixed_count = 0
        for user in users_with_incomplete:
            try:
                customer_id = user.get('stripe_customer_id')
                if not customer_id:
                    continue
                
                # Get active subscriptions for this customer
                subscriptions = stripe.Subscription.list(
                    customer=customer_id,
                    status="active",
                    limit=1
                )
                
                if subscriptions.data:
                    subscription = subscriptions.data[0]
                    print(f"🔧 Fixing user {user.get('email')}: {user.get('subscription_status')} -> {subscription.status}")
                    
                    update_data = {
                        "subscription_status": subscription.status,
                        "subscription_id": subscription.id,
                        "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                        "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                        "subscription_expires_at": datetime.fromtimestamp(subscription.current_period_end)
                    }
                    
                    # Get plan details
                    if subscription.items and len(subscription.items.data) > 0:
                        price = subscription.items.data[0].price
                        if price:
                            update_data["subscription_price_id"] = price.id
                            
                            # Get product details
                            product = stripe.Product.retrieve(price.product)
                            plan_id = product.name.lower().replace(" ", "_").replace("-", "")
                            if "fluency builder" in product.name.lower():
                                plan_id = "fluency_builder"
                            elif "team mastery" in product.name.lower():
                                plan_id = "team_mastery"
                            elif "try learn" in product.name.lower():
                                plan_id = "try_learn"
                            
                            update_data["subscription_plan"] = plan_id
                            
                            # Determine if monthly or annual
                            if price.recurring and price.recurring.interval:
                                update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"
                    
                    # Update user in MongoDB
                    result = await db.users.update_one(
                        {'_id': user['_id']},
                        {'$set': update_data}
                    )
                    
                    if result.modified_count > 0:
                        fixed_count += 1
                        print(f"   ✅ Fixed!")
                    else:
                        print(f"   ❌ Failed to update")
                        
            except Exception as e:
                print(f"   ❌ Error fixing user {user.get('email')}: {str(e)}")
        
        print(f"\n✅ Fixed {fixed_count} users with subscription sync issues")
        
        print("\n=== WEBHOOK IMPROVEMENT RECOMMENDATIONS ===")
        print("1. ✅ Fixed immediate sync issues")
        print("2. 🔧 Consider adding webhook retry mechanism")
        print("3. 🔧 Add webhook event logging for debugging")
        print("4. 🔧 Implement periodic sync check (daily/weekly)")
        print("5. 🔧 Add webhook endpoint health monitoring")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_stripe_webhook_sync_issue())
