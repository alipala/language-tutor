import os
import sys
import stripe
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL') or 'mongodb://localhost:27017'
DATABASE_NAME = os.getenv('DATABASE_NAME') or 'language_tutor'

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

def fix_user_subscription_dates(user_id, stripe_customer_id):
    """Fix subscription dates by fetching from Stripe"""
    try:
        print(f"Fixing subscription dates for user {user_id}")
        print(f"Stripe customer ID: {stripe_customer_id}")
        
        # Get active subscriptions from Stripe
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="active",
            limit=5
        )
        
        if not subscriptions.data:
            print("No active subscriptions found")
            return False
        
        subscription = subscriptions.data[0]
        print(f"Found subscription: {subscription.id}")
        print(f"Status: {subscription.status}")
        print(f"Current period start: {subscription.current_period_start}")
        print(f"Current period end: {subscription.current_period_end}")
        
        # Convert timestamps to datetime
        period_start = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
        period_end = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
        
        print(f"Period start: {period_start}")
        print(f"Period end: {period_end}")
        
        # Get subscription details
        price = subscription.items.data[0].price if subscription.items and subscription.items.data else None
        period_type = "annual" if price and price.recurring and price.recurring.interval == "year" else "monthly"
        
        print(f"Billing period: {period_type}")
        
        # Update user in database
        update_data = {
            "current_period_start": period_start,
            "current_period_end": period_end,
            "subscription_period": period_type,
            "subscription_status": subscription.status,
            "subscription_id": subscription.id
        }
        
        # Add subscription_started_at if not exists
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user.get("subscription_started_at"):
            update_data["subscription_started_at"] = period_start
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated user {user_id}")
            print(f"New period: {period_start} to {period_end}")
            return True
        else:
            print(f"❌ No changes made to user {user_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing subscription dates: {str(e)}")
        return False

if __name__ == "__main__":
    # Fix the specific user mentioned
    user_id = "685fe4b2acdf4f770e24345e"
    stripe_customer_id = "cus_SaHw3oXyZFueFK"
    
    print("=== FIXING SUBSCRIPTION DATES FROM STRIPE ===")
    success = fix_user_subscription_dates(user_id, stripe_customer_id)
    
    if success:
        print("\n✅ Subscription dates fixed successfully!")
        
        # Verify the fix
        user = db.users.find_one({"_id": ObjectId(user_id)})
        print("\n=== VERIFICATION ===")
        print(f"current_period_start: {user.get('current_period_start')}")
        print(f"current_period_end: {user.get('current_period_end')}")
        print(f"subscription_period: {user.get('subscription_period')}")
        print(f"subscription_status: {user.get('subscription_status')}")
    else:
        print("\n❌ Failed to fix subscription dates")
