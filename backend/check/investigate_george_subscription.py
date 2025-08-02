#!/usr/bin/env python3
"""
Investigation script for George's subscription issue
User ID: 6867a7e6e6c0452d1a92a35f
Stripe Customer ID: cus_ScLEmYviBW6lal
Subscription ID: sub_1Rh6YOJcquSiYwWNTOhUyBnQ
"""

import os
import stripe
from datetime import datetime, timezone
import pymongo
from bson import ObjectId

# Set up Stripe
stripe.api_key = "sk_test_51Mzx41JcquSiYwWNGndzlyBDtf249jC4H0bjboX2GxHJS2SHb2SXxlZmbt8ObCruGg5KKSTnHgnthxnZknF5F4R300MGsRy0aK"

# MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"

def investigate_george_subscription():
    """Investigate George's subscription status in both MongoDB and Stripe"""
    
    print("🔍 INVESTIGATING GEORGE'S SUBSCRIPTION")
    print("=" * 50)
    
    # User details from the provided data
    user_id = "6867a7e6e6c0452d1a92a35f"
    stripe_customer_id = "cus_ScLEmYviBW6lal"
    subscription_id = "sub_1Rh6YOJcquSiYwWNTOhUyBnQ"
    
    print(f"User ID: {user_id}")
    print(f"Stripe Customer ID: {stripe_customer_id}")
    print(f"Subscription ID: {subscription_id}")
    print()
    
    # 1. Check MongoDB current status
    print("📊 MONGODB STATUS:")
    print("-" * 20)
    try:
        client = pymongo.MongoClient(MONGODB_URL)
        db = client["language_tutor"]
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        
        if user:
            print(f"✅ User found in MongoDB")
            print(f"   Subscription Status: {user.get('subscription_status')}")
            print(f"   Subscription Plan: {user.get('subscription_plan')}")
            print(f"   Subscription Period: {user.get('subscription_period')}")
            print(f"   Is In Trial: {user.get('is_in_trial')}")
            print(f"   Trial End Date: {user.get('trial_end_date')}")
            print(f"   Subscription Started: {user.get('subscription_started_at')}")
            print(f"   Subscription Expires: {user.get('subscription_expires_at')}")
            print(f"   Current Period Start: {user.get('current_period_start')}")
            print(f"   Current Period End: {user.get('current_period_end')}")
            print(f"   Practice Sessions Used: {user.get('practice_sessions_used', 0)}")
            print(f"   Assessments Used: {user.get('assessments_used', 0)}")
        else:
            print("❌ User not found in MongoDB")
            
    except Exception as e:
        print(f"❌ MongoDB Error: {str(e)}")
    
    print()
    
    # 2. Check Stripe subscription status
    print("💳 STRIPE SUBSCRIPTION STATUS:")
    print("-" * 30)
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        print(f"✅ Subscription found in Stripe")
        print(f"   Status: {subscription.status}")
        
        # Safely access timestamp fields
        if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
            print(f"   Current Period Start: {datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)}")
        else:
            print(f"   Current Period Start: None")
            
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            print(f"   Current Period End: {datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)}")
        else:
            print(f"   Current Period End: None")
            
        if hasattr(subscription, 'trial_start') and subscription.trial_start:
            print(f"   Trial Start: {datetime.fromtimestamp(subscription.trial_start, tz=timezone.utc)}")
        else:
            print(f"   Trial Start: None")
            
        if hasattr(subscription, 'trial_end') and subscription.trial_end:
            print(f"   Trial End: {datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc)}")
        else:
            print(f"   Trial End: None")
            
        if hasattr(subscription, 'cancel_at_period_end'):
            print(f"   Cancel At Period End: {subscription.cancel_at_period_end}")
        else:
            print(f"   Cancel At Period End: None")
            
        if hasattr(subscription, 'created') and subscription.created:
            print(f"   Created: {datetime.fromtimestamp(subscription.created, tz=timezone.utc)}")
        else:
            print(f"   Created: None")
        
        # Get the price details
        try:
            if hasattr(subscription, 'items') and subscription.items:
                items_list = subscription.items.list()
                if items_list and len(items_list.data) > 0:
                    price = items_list.data[0].price
                    print(f"   Price ID: {price.id}")
                    print(f"   Amount: ${price.unit_amount / 100}")
                    print(f"   Currency: {price.currency}")
                    if hasattr(price, 'recurring') and price.recurring:
                        print(f"   Interval: {price.recurring.interval}")
                    
                    # Get product details
                    try:
                        product = stripe.Product.retrieve(price.product)
                        print(f"   Product: {product.name}")
                    except Exception as prod_e:
                        print(f"   Product: Error retrieving - {str(prod_e)}")
                else:
                    print(f"   No subscription items found")
            else:
                print(f"   No items attribute found")
        except Exception as items_e:
            print(f"   Items Error: {str(items_e)}")
        
        # Print raw subscription object for debugging
        try:
            print(f"   Raw Subscription Keys: {list(subscription.keys())}")
        except:
            print(f"   Could not list subscription keys")
        
    except Exception as e:
        print(f"❌ Stripe Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. Check Stripe customer
    print("👤 STRIPE CUSTOMER STATUS:")
    print("-" * 25)
    try:
        customer = stripe.Customer.retrieve(stripe_customer_id)
        print(f"✅ Customer found in Stripe")
        print(f"   Email: {customer.email}")
        print(f"   Name: {customer.name}")
        print(f"   Created: {datetime.fromtimestamp(customer.created, tz=timezone.utc)}")
        
    except Exception as e:
        print(f"❌ Stripe Customer Error: {str(e)}")
    
    print()
    
    # 4. Check recent invoices
    print("🧾 RECENT INVOICES:")
    print("-" * 18)
    try:
        invoices = stripe.Invoice.list(customer=stripe_customer_id, limit=5)
        
        if invoices.data:
            for i, invoice in enumerate(invoices.data):
                print(f"   Invoice {i+1}:")
                print(f"     ID: {invoice.id}")
                print(f"     Status: {invoice.status}")
                print(f"     Amount: ${invoice.amount_paid / 100}")
                print(f"     Created: {datetime.fromtimestamp(invoice.created, tz=timezone.utc)}")
                print(f"     Period Start: {datetime.fromtimestamp(invoice.period_start, tz=timezone.utc) if invoice.period_start else 'None'}")
                print(f"     Period End: {datetime.fromtimestamp(invoice.period_end, tz=timezone.utc) if invoice.period_end else 'None'}")
                print()
        else:
            print("   No invoices found")
            
    except Exception as e:
        print(f"❌ Invoice Error: {str(e)}")
    
    print()
    
    # 5. Analysis and recommendations
    print("🔬 ANALYSIS:")
    print("-" * 12)
    
    now = datetime.now(timezone.utc)
    trial_end = datetime(2025, 7, 11, 10, 9, 12, tzinfo=timezone.utc)
    
    print(f"   Current Time: {now}")
    print(f"   Trial End Time: {trial_end}")
    print(f"   Days Since Trial End: {(now - trial_end).days}")
    
    if now > trial_end:
        print("   ⚠️  TRIAL HAS ENDED - User should be on active monthly subscription")
        print("   🔧 EXPECTED FIXES NEEDED:")
        print("      - subscription_status should be 'active'")
        print("      - is_in_trial should be False")
        print("      - subscription_expires_at should be ~1 month from trial end")
        print("      - trial_end_date should be cleared or kept for reference")
    else:
        print("   ✅ Trial is still active")

if __name__ == "__main__":
    investigate_george_subscription()
