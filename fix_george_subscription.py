#!/usr/bin/env python3
"""
Fix George's subscription data to demonstrate the trial-to-monthly transition fix
User ID: 6867a7e6e6c0452d1a92a35f
Email: bc0e874a-64c4-4419-8f48-d0c4bae5cc23@mailslurp.biz
"""

import os
import stripe
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import pymongo
from bson import ObjectId

# Set up Stripe
stripe.api_key = "sk_test_51Mzx41JcquSiYwWNGndzlyBDtf249jC4H0bjboX2GxHJS2SHb2SXxlZmbt8ObCruGg5KKSTnHgnthxnZknF5F4R300MGsRy0aK"

# MongoDB connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"

def fix_george_subscription():
    """Fix George's subscription to demonstrate proper trial-to-monthly transition"""
    
    print("🔧 FIXING GEORGE'S SUBSCRIPTION")
    print("=" * 50)
    
    # User details
    user_id = "6867a7e6e6c0452d1a92a35f"
    stripe_customer_id = "cus_ScLEmYviBW6lal"
    subscription_id = "sub_1Rh6YOJcquSiYwWNTOhUyBnQ"
    
    print(f"User ID: {user_id}")
    print(f"Stripe Customer ID: {stripe_customer_id}")
    print(f"Subscription ID: {subscription_id}")
    print()
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URL)
        db = client["language_tutor"]
        
        # Get current user data
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            print("❌ User not found in MongoDB")
            return
        
        print("📊 CURRENT USER DATA:")
        print(f"   Subscription Status: {user.get('subscription_status')}")
        print(f"   Is In Trial: {user.get('is_in_trial')}")
        print(f"   Trial End Date: {user.get('trial_end_date')}")
        print(f"   Subscription Expires: {user.get('subscription_expires_at')}")
        print(f"   Current Period End: {user.get('current_period_end')}")
        print()
        
        # Get current subscription from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        print("💳 CURRENT STRIPE DATA:")
        print(f"   Status: {subscription.status}")
        print(f"   Trial Start: {datetime.fromtimestamp(subscription.trial_start, tz=timezone.utc) if subscription.trial_start else 'None'}")
        print(f"   Trial End: {datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc) if subscription.trial_end else 'None'}")
        print(f"   Current Period Start: {datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc) if subscription.current_period_start else 'None'}")
        print(f"   Current Period End: {datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc) if subscription.current_period_end else 'None'}")
        print()
        
        # Determine what needs to be fixed
        now = datetime.now(timezone.utc)
        trial_end_date = datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc) if subscription.trial_end else None
        
        print("🔍 ANALYSIS:")
        print(f"   Current Time: {now}")
        print(f"   Trial End Time: {trial_end_date}")
        
        if trial_end_date and now > trial_end_date:
            print("   ⚠️  TRIAL HAS ENDED - User should be on active monthly subscription")
            
            # Calculate correct monthly expiry (1 month from trial end)
            monthly_expiry = trial_end_date + relativedelta(months=1)
            
            print(f"   📅 Correct monthly expiry should be: {monthly_expiry}")
            print()
            
            # Prepare update data
            update_data = {
                "subscription_status": "active",  # Should be active, not trialing
                "is_in_trial": False,  # Trial has ended
                "subscription_expires_at": monthly_expiry,  # 1 month from trial end
                "trial_end_date": trial_end_date,  # Keep for reference
                "practice_sessions_used": 0,  # Reset for new billing period
                "assessments_used": 0,  # Reset for new billing period
            }
            
            # Update current period info from Stripe
            if subscription.current_period_start:
                update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
            
            if subscription.current_period_end:
                update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
            
            print("🔧 APPLYING FIXES:")
            for key, value in update_data.items():
                print(f"   {key}: {value}")
            print()
            
            # Apply the fix
            result = db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print("✅ SUCCESS: George's subscription has been fixed!")
                print()
                
                # Verify the fix
                updated_user = db["users"].find_one({"_id": ObjectId(user_id)})
                print("📊 UPDATED USER DATA:")
                print(f"   Subscription Status: {updated_user.get('subscription_status')}")
                print(f"   Is In Trial: {updated_user.get('is_in_trial')}")
                print(f"   Trial End Date: {updated_user.get('trial_end_date')}")
                print(f"   Subscription Expires: {updated_user.get('subscription_expires_at')}")
                print(f"   Current Period End: {updated_user.get('current_period_end')}")
                print(f"   Practice Sessions Used: {updated_user.get('practice_sessions_used')}")
                print(f"   Assessments Used: {updated_user.get('assessments_used')}")
                print()
                
                print("🎉 SUMMARY:")
                print("   - Status changed from 'trialing' to 'active'")
                print("   - Trial flag set to False")
                print(f"   - Expiry date updated to {monthly_expiry} (1 month from trial end)")
                print("   - Usage counters reset for new billing period")
                print("   - Trial end date preserved for reference")
                
            else:
                print("❌ No changes were made to the user record")
                
        else:
            print("   ✅ Trial is still active - no fix needed yet")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_george_subscription()
