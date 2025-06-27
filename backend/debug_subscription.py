import asyncio
import os
import stripe
from database import database
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def debug_subscription_status():
    """Debug subscription status for John Monthly"""
    
    print("🔍 Debugging subscription status for John Monthly...")
    
    # Get John's user record from database
    john_user = await database["users"].find_one({"_id": ObjectId("685c6d8aa3412c0964ef47d0")})
    
    if not john_user:
        print("❌ John's user record not found in database")
        return
    
    print(f"\n📊 John's Database Record:")
    print(f"   - ID: {john_user.get('_id')}")
    print(f"   - Email: {john_user.get('email')}")
    print(f"   - Name: {john_user.get('name')}")
    print(f"   - Stripe Customer ID: {john_user.get('stripe_customer_id')}")
    print(f"   - Subscription Status: {john_user.get('subscription_status')}")
    print(f"   - Subscription ID: {john_user.get('subscription_id')}")
    print(f"   - Subscription Plan: {john_user.get('subscription_plan')}")
    print(f"   - Subscription Period: {john_user.get('subscription_period')}")
    print(f"   - Subscription Price ID: {john_user.get('subscription_price_id')}")
    
    customer_id = john_user.get('stripe_customer_id')
    if not customer_id:
        print("❌ No Stripe customer ID found in database")
        return
    
    print(f"\n🔍 Checking Stripe subscriptions for customer: {customer_id}")
    
    try:
        # Check active subscriptions
        active_subs = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=10
        )
        
        print(f"\n✅ Active Subscriptions ({len(active_subs['data'])}):")
        for sub in active_subs['data']:
            price = sub.items.data[0].price
            product = stripe.Product.retrieve(price.product)
            period = "monthly" if price.recurring.interval == "month" else "annual"
            
            print(f"   - ID: {sub.id}")
            print(f"   - Status: {sub.status}")
            print(f"   - Product: {product.name}")
            print(f"   - Period: {period}")
            print(f"   - Price ID: {price.id}")
            print(f"   - Amount: {price.unit_amount/100} {price.currency.upper()}")
            print()
        
        # Check all subscriptions
        all_subs = stripe.Subscription.list(
            customer=customer_id,
            status="all",
            limit=10
        )
        
        print(f"📋 All Subscriptions ({len(all_subs.data)}):")
        for sub in all_subs.data:
            price = sub.items.data[0].price
            product = stripe.Product.retrieve(price.product)
            period = "monthly" if price.recurring.interval == "month" else "annual"
            
            print(f"   - ID: {sub.id}")
            print(f"   - Status: {sub.status}")
            print(f"   - Product: {product.name}")
            print(f"   - Period: {period}")
            print(f"   - Price ID: {price.id}")
            print()
            
    except Exception as e:
        print(f"❌ Error checking Stripe subscriptions: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_subscription_status())
