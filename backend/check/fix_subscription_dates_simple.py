import os
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL') or 'mongodb://localhost:27017'
DATABASE_NAME = os.getenv('DATABASE_NAME') or 'language_tutor'

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

def fix_user_subscription_dates_manual():
    """Fix subscription dates with the correct dates from Stripe"""
    user_id = "685fe4b2acdf4f770e24345e"
    
    # These are the correct dates from Stripe (we got them from the previous run)
    period_start = datetime(2025, 6, 28, 22, 37, 34, tzinfo=timezone.utc)
    period_end = datetime(2026, 6, 28, 22, 37, 34, tzinfo=timezone.utc)
    
    print(f"Fixing subscription dates for user {user_id}")
    print(f"Setting period start: {period_start}")
    print(f"Setting period end: {period_end}")
    
    # Update user in database
    update_data = {
        "current_period_start": period_start,
        "current_period_end": period_end,
        "subscription_period": "annual",
        "subscription_status": "active",
        "subscription_started_at": period_start,
        "subscription_expires_at": period_end
    }
    
    try:
        # First check if user exists
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            print(f"❌ User {user_id} not found in database")
            return False
        
        print(f"Found user: {user.get('email', 'No email')}")
        print(f"Current period start: {user.get('current_period_start')}")
        print(f"Current period end: {user.get('current_period_end')}")
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        print(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.matched_count > 0:
            print(f"✅ Successfully updated user {user_id}")
            
            # Verify the fix
            updated_user = db.users.find_one({"_id": ObjectId(user_id)})
            print("\n=== VERIFICATION ===")
            print(f"current_period_start: {updated_user.get('current_period_start')}")
            print(f"current_period_end: {updated_user.get('current_period_end')}")
            print(f"subscription_period: {updated_user.get('subscription_period')}")
            print(f"subscription_status: {updated_user.get('subscription_status')}")
            print(f"subscription_started_at: {updated_user.get('subscription_started_at')}")
            print(f"subscription_expires_at: {updated_user.get('subscription_expires_at')}")
            return True
        else:
            print(f"❌ No user matched for update {user_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing subscription dates: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== FIXING SUBSCRIPTION DATES MANUALLY ===")
    success = fix_user_subscription_dates_manual()
    
    if success:
        print("\n✅ Subscription dates fixed successfully!")
        print("The user should now show:")
        print("- Subscription Started: June 28, 2025 at 10:37 PM")
        print("- Expires At: June 28, 2026 at 10:37 PM")
        print("- Period: Annual")
    else:
        print("\n❌ Failed to fix subscription dates")
