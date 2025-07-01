import asyncio
import os
import stripe
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def investigate_stripe_webhook_issue():
    """
    Investigate why the user's subscription status is 'incomplete' instead of 'active'
    and fix the Stripe webhook synchronization issue.
    """
    
    # Set up Stripe using environment variables
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return
    
    # Connect to production MongoDB
    mongodb_url = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    try:
        print("=== INVESTIGATING STRIPE WEBHOOK ISSUE ===")
        
        # Check the specific user
        user_id = '686424d66c72bbc0837f8a58'
        user = await db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"📋 User: {user.get('name')} ({user.get('email')})")
        print(f"📋 Current subscription status: {user.get('subscription_status')}")
        print(f"📋 Stripe customer ID: {user.get('stripe_customer_id')}")
        print(f"📋 Subscription ID: {user.get('subscription_id')}")
        print()
        
        # Check Stripe customer and subscription status
        stripe_customer_id = user.get('stripe_customer_id')
        stripe_subscription_id = user.get('subscription_id')
        
        if not stripe_customer_id:
            print("❌ No Stripe customer ID found")
            return
        
        print("=== STRIPE CUSTOMER DETAILS ===")
        try:
            customer = stripe.Customer.retrieve(stripe_customer_id)
            print(f"✅ Customer found: {customer.id}")
            print(f"📧 Email: {customer.email}")
            print(f"👤 Name: {customer.name}")
            print()
        except Exception as e:
            print(f"❌ Error retrieving customer: {str(e)}")
            return
        
        print("=== STRIPE SUBSCRIPTION DETAILS ===")
        if stripe_subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                print(f"✅ Subscription found: {subscription.id}")
                print(f"📊 Status: {subscription.status}")
                print(f"📅 Current period start: {datetime.fromtimestamp(subscription.current_period_start)}")
                print(f"📅 Current period end: {datetime.fromtimestamp(subscription.current_period_end)}")
                print(f"💰 Amount: {subscription.items.data[0].price.unit_amount / 100} {subscription.items.data[0].price.currency.upper()}")
                
                # Check if status mismatch
                if subscription.status != user.get('subscription_status'):
                    print(f"🐛 STATUS MISMATCH DETECTED!")
                    print(f"   Stripe status: {subscription.status}")
                    print(f"   DB status: {user.get('subscription_status')}")
                    print()
                    
                    # Fix the status
                    print("🔧 FIXING STATUS MISMATCH...")
                    
                    update_data = {
                        "subscription_status": subscription.status,
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
                        {'_id': ObjectId(user_id)},
                        {'$set': update_data}
                    )
                    
                    if result.modified_count > 0:
                        print(f"✅ Successfully updated user subscription status to: {subscription.status}")
                        print(f"✅ Updated subscription details in database")
                    else:
                        print("❌ Failed to update user subscription status")
                else:
                    print(f"✅ Status is correct: {subscription.status}")
                
            except Exception as e:
                print(f"❌ Error retrieving subscription: {str(e)}")
        else:
            print("❌ No subscription ID found in user record")
            
            # Try to find subscriptions for this customer
            print("🔍 Searching for subscriptions for this customer...")
            try:
                subscriptions = stripe.Subscription.list(customer=stripe_customer_id, limit=10)
                print(f"📋 Found {len(subscriptions.data)} subscriptions:")
                
                for sub in subscriptions.data:
                    print(f"   - {sub.id}: {sub.status} (created: {datetime.fromtimestamp(sub.created)})")
                    
                    if sub.status in ['active', 'trialing']:
                        print(f"🔧 Found active subscription: {sub.id}")
                        print("🔧 Updating user with this subscription...")
                        
                        update_data = {
                            "subscription_id": sub.id,
                            "subscription_status": sub.status,
                            "current_period_start": datetime.fromtimestamp(sub.current_period_start),
                            "current_period_end": datetime.fromtimestamp(sub.current_period_end),
                            "subscription_expires_at": datetime.fromtimestamp(sub.current_period_end)
                        }
                        
                        # Get plan details
                        if sub.items and len(sub.items.data) > 0:
                            price = sub.items.data[0].price
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
                            {'_id': ObjectId(user_id)},
                            {'$set': update_data}
                        )
                        
                        if result.modified_count > 0:
                            print(f"✅ Successfully linked active subscription {sub.id}")
                            break
                        else:
                            print("❌ Failed to update user with active subscription")
                            
            except Exception as e:
                print(f"❌ Error searching for subscriptions: {str(e)}")
        
        print()
        print("=== WEBHOOK INVESTIGATION ===")
        print("Checking recent webhook events for this customer...")
        
        try:
            # Get recent events for this customer
            events = stripe.Event.list(
                limit=20,
                type='customer.subscription.*'
            )
            
            customer_events = []
            for event in events.data:
                if (event.data.object.get('customer') == stripe_customer_id or 
                    (event.data.object.get('object') == 'subscription' and 
                     event.data.object.get('customer') == stripe_customer_id)):
                    customer_events.append(event)
            
            print(f"📋 Found {len(customer_events)} subscription events for this customer:")
            for event in customer_events:
                print(f"   - {event.type}: {event.created} ({datetime.fromtimestamp(event.created)})")
                if hasattr(event.data.object, 'status'):
                    print(f"     Status: {event.data.object.status}")
            
            if not customer_events:
                print("⚠️  No recent subscription events found - this might indicate webhook delivery issues")
                
        except Exception as e:
            print(f"❌ Error checking webhook events: {str(e)}")
        
        print()
        print("=== RECOMMENDATIONS ===")
        print("1. Check Stripe webhook endpoint configuration")
        print("2. Verify webhook secret is correct")
        print("3. Check webhook delivery logs in Stripe dashboard")
        print("4. Ensure webhook endpoint is accessible from Stripe")
        print("5. Consider implementing webhook retry mechanism")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(investigate_stripe_webhook_issue())
