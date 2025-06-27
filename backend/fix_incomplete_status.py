#!/usr/bin/env python3
"""
Fix users with 'incomplete' subscription status when they should be 'active'
This happens when the webhook doesn't properly update the status after payment completion.
"""

import asyncio
import os
import stripe
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def fix_incomplete_subscriptions():
    """Fix users with incomplete subscription status"""
    
    print("🚀 Fixing incomplete subscription statuses...")
    
    # Connect to production MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("❌ MONGODB_URL environment variable not set")
        return
    
    print(f"🔗 Connecting to production MongoDB...")
    client = AsyncIOMotorClient(mongodb_url)
    database = client.get_default_database()
    
    try:
        # Find users with incomplete subscription status but have subscription_id
        users_cursor = database["users"].find({
            "subscription_status": "incomplete",
            "subscription_id": {"$exists": True, "$ne": None}
        })
        
        users = await users_cursor.to_list(length=None)
        print(f"🔍 Found {len(users)} users with incomplete status but have subscription_id")
        
        for user in users:
            user_id = user["_id"]
            subscription_id = user.get("subscription_id")
            user_email = user.get("email")
            
            print(f"\n🔧 Checking user: {user_id}")
            print(f"   Email: {user_email}")
            print(f"   Subscription ID: {subscription_id}")
            
            if not subscription_id:
                print(f"   ❌ No subscription ID found")
                continue
            
            try:
                # Get subscription from Stripe
                subscription = stripe.Subscription.retrieve(subscription_id)
                print(f"   ✅ Stripe subscription status: {subscription.status}")
                
                if subscription.status == "active":
                    # Update user status to active
                    update_data = {
                        "subscription_status": "active"
                    }
                    
                    # Also update period dates if missing
                    if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
                        update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
                    
                    if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
                        update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                    
                    # Reset usage counters if they don't exist
                    if "practice_sessions_used" not in user:
                        update_data["practice_sessions_used"] = 0
                    if "assessments_used" not in user:
                        update_data["assessments_used"] = 0
                    
                    result = await database["users"].update_one(
                        {"_id": user_id},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        print(f"   ✅ Updated user status to active!")
                    else:
                        print(f"   ⚠️ No changes made")
                        
                elif subscription.status in ["past_due", "canceled", "unpaid"]:
                    print(f"   ⚠️ Subscription is {subscription.status} - keeping as incomplete")
                else:
                    print(f"   ⚠️ Subscription status is {subscription.status} - no action needed")
                    
            except stripe.error.StripeError as e:
                print(f"   ❌ Stripe error: {str(e)}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        print(f"\n🎉 Completed checking {len(users)} users")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_incomplete_subscriptions())
