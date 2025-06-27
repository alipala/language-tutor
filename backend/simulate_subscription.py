import asyncio
import os
from database import database
from bson import ObjectId

async def simulate_subscription_creation():
    """Simulate a successful subscription creation for testing"""
    
    # John Monthly - Monthly Fluency Builder subscription
    john_update = {
        "subscription_status": "active",
        "subscription_id": "sub_test_john_monthly_fluency",
        "subscription_plan": "fluency_builder",
        "subscription_period": "monthly",
        "subscription_price_id": "price_1Re01yJcquSiYwWNJRg7nyce",
        "stripe_customer_id": "cus_SZ9XawU9BEMA9a"
    }
    
    # Jane Yearly - Yearly Fluency Builder subscription  
    jane_update = {
        "subscription_status": "active",
        "subscription_id": "sub_test_jane_yearly_fluency",
        "subscription_plan": "fluency_builder", 
        "subscription_period": "annual",
        "subscription_price_id": "price_1Re06kJcquSiYwWN89Ra57wC",
        "stripe_customer_id": "cus_SZ9YpIsvjT8eYJ"
    }
    
    # Update John Monthly
    result1 = await database["users"].update_one(
        {"_id": ObjectId("685c6d8aa3412c0964ef47d0")},
        {"$set": john_update}
    )
    
    # Update Jane Yearly
    result2 = await database["users"].update_one(
        {"_id": ObjectId("685c6dd2a3412c0964ef47d3")},
        {"$set": jane_update}
    )
    
    print(f"✅ John Monthly subscription simulated: {result1.modified_count} record updated")
    print(f"✅ Jane Yearly subscription simulated: {result2.modified_count} record updated")
    
    # Verify updates
    john = await database["users"].find_one({"_id": ObjectId("685c6d8aa3412c0964ef47d0")})
    jane = await database["users"].find_one({"_id": ObjectId("685c6dd2a3412c0964ef47d3")})
    
    print(f"\n📊 John Monthly Status:")
    print(f"   - Subscription Status: {john.get('subscription_status')}")
    print(f"   - Plan: {john.get('subscription_plan')}")
    print(f"   - Period: {john.get('subscription_period')}")
    print(f"   - Stripe Customer: {john.get('stripe_customer_id')}")
    
    print(f"\n📊 Jane Yearly Status:")
    print(f"   - Subscription Status: {jane.get('subscription_status')}")
    print(f"   - Plan: {jane.get('subscription_plan')}")
    print(f"   - Period: {jane.get('subscription_period')}")
    print(f"   - Stripe Customer: {jane.get('stripe_customer_id')}")

if __name__ == "__main__":
    asyncio.run(simulate_subscription_creation())
