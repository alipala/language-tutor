#!/usr/bin/env python3
"""
Fix the guest user who completed payment but didn't get subscription data
User ID: 685eaa4d1b2752485f544910
Email: cf857e02-2593-465e-9527-c12f30e26104@mailslurp.biz
"""

import asyncio
import os
import stripe
from bson import ObjectId
from database import init_db, database
from datetime import datetime, timezone

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def fix_guest_user():
    """Fix the guest user who completed payment"""
    
    print("🚀 Fixing guest user subscription...")
    
    # Initialize database
    await init_db()
    
    # User details from the test
    user_id = "685eaa4d1b2752485f544910"
    user_email = "cf857e02-2593-465e-9527-c12f30e26104@mailslurp.biz"
    
    print(f"🔧 Fixing user: {user_id}")
    print(f"🔧 User email: {user_email}")
    
    try:
        # Find user by ID
        user = await database["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"✅ Found user: {user.get('name')} - {user.get('email')}")
        print(f"   Current subscription status: {user.get('subscription_status')}")
        print(f"   Current stripe customer ID: {user.get('stripe_customer_id')}")
        
        # Find Stripe customer by email
        print(f"🔍 Looking for Stripe customer with email: {user_email}")
        customers = stripe.Customer.list(email=user_email, limit=5)
        
        if not customers.data:
            print(f"❌ No Stripe customer found with email: {user_email}")
            return
        
        print(f"✅ Found {len(customers.data)} Stripe customer(s)")
        
        # Get the most recent customer
        customer = customers.data[0]
        customer_id = customer.id
        print(f"✅ Using customer: {customer_id}")
        
        # Get active subscriptions for this customer
        print(f"🔍 Looking for active subscriptions for customer: {customer_id}")
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=5
        )
        
        if not subscriptions.data:
            print(f"❌ No active subscription found for customer: {customer_id}")
            # Try all subscriptions
            all_subscriptions = stripe.Subscription.list(customer=customer_id, limit=10)
            print(f"📋 Found {len(all_subscriptions.data)} total subscriptions:")
            for sub in all_subscriptions.data:
                print(f"   - {sub.id}: {sub.status}")
            return
        
        subscription = subscriptions.data[0]
        print(f"✅ Found active subscription: {subscription.id}")
        print(f"   Status: {subscription.status}")
        
        # Prepare update data
        update_data = {
            "stripe_customer_id": customer_id,
            "subscription_status": subscription.status,
            "subscription_id": subscription.id
        }
        
        # Get the plan details
        if subscription.items and len(subscription.items.data) > 0:
            price = subscription.items.data[0].price
            if price:
                update_data["subscription_price_id"] = price.id
                print(f"   Price ID: {price.id}")
                
                # Get product details
                product = stripe.Product.retrieve(price.product)
                plan_name = product.name.lower().replace(" ", "_").replace("-", "")
                if "fluency builder" in product.name.lower():
                    plan_name = "fluency_builder"
                elif "team mastery" in product.name.lower():
                    plan_name = "team_mastery"
                
                update_data["subscription_plan"] = plan_name
                print(f"   Plan: {plan_name}")
                
                # Determine if monthly or annual
                if price.recurring and price.recurring.interval:
                    period = "monthly" if price.recurring.interval == "month" else "annual"
                    update_data["subscription_period"] = period
                    print(f"   Period: {period}")
        
        # Add period dates
        if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
            update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
        
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
        
        # Reset usage counters
        update_data["practice_sessions_used"] = 0
        update_data["assessments_used"] = 0
        
        print(f"🔄 Updating user with subscription data:")
        for key, value in update_data.items():
            print(f"   {key}: {value}")
        
        # Update user
        result = await database["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated user {user_id}!")
            
            # Verify the update
            updated_user = await database["users"].find_one({"_id": ObjectId(user_id)})
            print(f"🔍 Verification:")
            print(f"   ✅ Subscription status: {updated_user.get('subscription_status')}")
            print(f"   ✅ Subscription plan: {updated_user.get('subscription_plan')}")
            print(f"   ✅ Stripe customer ID: {updated_user.get('stripe_customer_id')}")
            print(f"   ✅ Subscription ID: {updated_user.get('subscription_id')}")
            
            print(f"\n🎉 SUCCESS! Guest user should no longer see upgrade prompts.")
        else:
            print(f"❌ Failed to update user")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_guest_user())
