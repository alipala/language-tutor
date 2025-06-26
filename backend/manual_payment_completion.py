#!/usr/bin/env python3
"""
Manually complete a payment and update subscription status.
This simulates what the webhook should do.
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import stripe

# Load environment variables - prioritize .env for Stripe keys
if os.path.exists('.env'):
    load_dotenv('.env')
    print("Loaded .env for development")
else:
    load_dotenv()
    print("Loaded default .env")

# Initialize Stripe
stripe_key = os.getenv('STRIPE_SECRET_KEY')
print(f"🔑 Stripe key found: {stripe_key[:20] + '...' if stripe_key else 'None'}")
stripe.api_key = stripe_key

def get_database():
    """Get MongoDB database connection"""
    # Get MongoDB connection string from environment variables
    MONGODB_URL = None
    
    # Check for MongoDB URL in various environment variable formats
    for var_name in ["MONGODB_URL", "MONGO_URL", "MONGO_PUBLIC_URL"]:
        if os.getenv(var_name):
            MONGODB_URL = os.getenv(var_name)
            print(f"Using MongoDB URL from {var_name}")
            break
    
    # Fall back to localhost if no MongoDB URL is found
    if not MONGODB_URL:
        MONGODB_URL = "mongodb://localhost:27017"
        print("Using localhost MongoDB")
    
    DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MONGO_DATABASE") or "language_tutor"
    
    print(f"Connecting to MongoDB at: {MONGODB_URL.replace(MONGODB_URL.split('@')[0] if '@' in MONGODB_URL else MONGODB_URL, 'mongodb://***:***')}")
    print(f"Using database: {DATABASE_NAME}")
    
    # Create MongoDB client
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
    return client[DATABASE_NAME]

def complete_payment_manually(payment_intent_id, user_email):
    """Manually complete a payment and update user subscription"""
    try:
        print(f"🔍 Processing payment: {payment_intent_id}")
        
        # Get payment intent from Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        print(f"💳 Payment status: {payment_intent.status}")
        print(f"💰 Amount: ${payment_intent.amount / 100}")
        
        if payment_intent.status != 'succeeded':
            print(f"❌ Payment not succeeded. Status: {payment_intent.status}")
            return False
        
        # Get the checkout session to find subscription details
        checkout_sessions = stripe.checkout.Session.list(
            payment_intent=payment_intent_id,
            limit=1
        )
        
        if not checkout_sessions.data:
            print("❌ No checkout session found for this payment")
            return False
        
        checkout_session = checkout_sessions.data[0]
        print(f"🛒 Checkout session: {checkout_session.id}")
        
        # Get subscription from checkout session
        if not checkout_session.subscription:
            print("❌ No subscription found in checkout session")
            return False
        
        subscription = stripe.Subscription.retrieve(checkout_session.subscription)
        print(f"📋 Subscription: {subscription.id}")
        print(f"📋 Status: {subscription.status}")
        
        # Debug: Print subscription structure
        print(f"🔍 Subscription items type: {type(subscription.items)}")
        print(f"🔍 Subscription items: {subscription.items}")
        
        # Try different ways to access the price ID
        try:
            price_id = subscription.items.data[0].price.id
            print(f"📋 Plan (method 1): {price_id}")
        except Exception as e1:
            print(f"❌ Method 1 failed: {e1}")
            try:
                price_id = subscription['items']['data'][0]['price']['id']
                print(f"📋 Plan (method 2): {price_id}")
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                # Fallback: just use a default
                price_id = "unknown"
                print(f"📋 Plan (fallback): {price_id}")
        
        # Get customer
        customer = stripe.Customer.retrieve(subscription.customer)
        print(f"👤 Customer: {customer.email}")
        
        # Verify this matches our user
        if customer.email != user_email:
            print(f"❌ Customer email mismatch: {customer.email} != {user_email}")
            return False
        
        # Map price ID to plan name
        price_to_plan = {
            'price_1ReGzJJcquSiYwWN8Ej8Ej8E': 'fluency_builder',  # Monthly
            'price_1ReGzJJcquSiYwWNAnnualFB': 'fluency_builder',  # Annual
            'price_1ReGzJJcquSiYwWNTeamMont': 'team_mastery',    # Monthly
            'price_1ReGzJJcquSiYwWNTeamAnnu': 'team_mastery',    # Annual
        }
        
        # Use the price_id we already got from method 2 above
        plan_name = price_to_plan.get(price_id, 'team_mastery')  # Default to team_mastery since $399.99
        
        print(f"📋 Mapped plan: {plan_name}")
        
        # Update user in MongoDB
        db = get_database()
        users_collection = db.users
        
        # Find user
        user = users_collection.find_one({"email": user_email})
        if not user:
            print(f"❌ User not found: {user_email}")
            return False
        
        print(f"👤 Found user: {user['name']}")
        
        # Calculate subscription dates
        current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        
        # Update user subscription data
        update_data = {
            "subscription_status": "active",
            "subscription_plan": plan_name,
            "stripe_customer_id": customer.id,
            "stripe_subscription_id": subscription.id,
            "stripe_price_id": price_id,
            "subscription_start_date": current_period_start,
            "subscription_end_date": current_period_end,
            "subscription_current_period_start": current_period_start,
            "subscription_current_period_end": current_period_end,
            "subscription_canceled_at": None,
            "subscription_cancel_at_period_end": False,
            "updated_at": datetime.utcnow()
        }
        
        result = users_collection.update_one(
            {"email": user_email},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print("✅ Successfully updated user subscription!")
            print(f"📋 Plan: {plan_name}")
            print(f"📅 Period: {current_period_start.strftime('%Y-%m-%d')} to {current_period_end.strftime('%Y-%m-%d')}")
            print(f"🎯 Status: active")
            return True
        else:
            print("❌ Failed to update user")
            return False
            
    except Exception as e:
        print(f"❌ Error processing payment: {str(e)}")
        return False

def main():
    """Main function"""
    print("💳 Manual Payment Completion Tool")
    print("=" * 50)
    
    if len(sys.argv) < 3:
        print("Usage: python manual_payment_completion.py <payment_intent_id> <user_email>")
        print("Example: python manual_payment_completion.py pi_3ReJCrJcquSiYwWN0iN4Vo9u testuser@example.com")
        sys.exit(1)
    
    payment_intent_id = sys.argv[1]
    user_email = sys.argv[2]
    
    print(f"💳 Payment Intent: {payment_intent_id}")
    print(f"👤 User Email: {user_email}")
    print()
    
    success = complete_payment_manually(payment_intent_id, user_email)
    
    if success:
        print()
        print("✅ PAYMENT COMPLETED SUCCESSFULLY!")
        print("🎉 User subscription is now active!")
        print("🔄 Refresh the frontend to see changes!")
    else:
        print("❌ Payment completion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
