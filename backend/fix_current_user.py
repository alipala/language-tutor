#!/usr/bin/env python3
"""
Fix the current problematic user in production
User ID: 685ea1e1e2723b27de523837
Customer ID: cus_SZmGjgeevLADlv
"""

import asyncio
import os
from bson import ObjectId
from database import init_db, database
from datetime import datetime, timezone

async def fix_current_user():
    """Fix the current problematic user"""
    
    print("🚀 Fixing current problematic user...")
    
    # Initialize database
    await init_db()
    
    # User details from the test
    user_id = "685ea1e1e2723b27de523837"
    stripe_customer_id = "cus_SZmGjgeevLADlv"
    user_email = "9dc06a44-aeea-4e17-a6e9-4fb002cdd037@mailslurp.biz"
    
    print(f"🔧 Fixing user: {user_id}")
    print(f"🔧 Stripe customer ID: {stripe_customer_id}")
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
        
        # Update with subscription data based on Stripe
        update_data = {
            "stripe_customer_id": stripe_customer_id,
            "subscription_status": "active",
            "subscription_id": "sub_1RechrJcquSiYwWNaIMmQmzL",  # From the webhook data
            "subscription_plan": "fluency_builder",
            "subscription_period": "monthly",
            "subscription_price_id": "price_1Re01yJcquSiYwWNJRg7nyce",
            "current_period_start": datetime(2025, 6, 27, 13, 52, 44, tzinfo=timezone.utc),
            "current_period_end": datetime(2025, 7, 27, 13, 52, 44, tzinfo=timezone.utc),
            "practice_sessions_used": 0,
            "assessments_used": 0,
            "subscription_tier": "fluency_builder"
        }
        
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
            
            print(f"\n🎉 SUCCESS! User should no longer see upgrade prompts.")
        else:
            print(f"❌ Failed to update user")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_current_user())
