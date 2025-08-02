import requests
import json

def fix_production_user():
    """Fix the production user's subscription dates via admin API"""
    
    # Admin login
    admin_login_data = {
        "email": "admin@languagetutor.com",
        "password": "admin123"
    }

    print("🔐 Logging in as admin...")
    login_response = requests.post(
        "https://mytacoai.com/api/admin/login",
        json=admin_login_data
    )

    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        print(login_response.text)
        return

    admin_token = login_response.json()["access_token"]
    print("✅ Admin login successful")
    
    # User to fix
    user_id = "685fe4b2acdf4f770e24345e"
    
    print(f"\n📋 Current user data (from your message):")
    print(f"  - ID: {user_id}")
    print(f"  - Email: 430c7b01-706d-4a13-a466-7b5c2ee0ef00@mailslurp.biz")
    print(f"  - Current period: 2025-06-01 to 2025-07-01 (WRONG - monthly)")
    print(f"  - Should be: 2025-06-28 to 2026-06-28 (CORRECT - annual)")
    
    # Prepare the correct subscription data from Stripe
    update_data = {
        "current_period_start": "2025-06-28T22:37:34.000Z",
        "current_period_end": "2026-06-28T22:37:34.000Z",
        "subscription_period": "annual",
        "subscription_status": "active",
        "subscription_started_at": "2025-06-28T22:37:34.000Z",
        "subscription_expires_at": "2026-06-28T22:37:34.000Z"
    }
    
    print(f"\n🔧 Updating user {user_id} with correct subscription dates...")
    print(f"  - New start: {update_data['current_period_start']}")
    print(f"  - New end: {update_data['current_period_end']}")
    print(f"  - Period: {update_data['subscription_period']}")
    
    # Update via admin API
    update_response = requests.put(
        f"https://mytacoai.com/api/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    if update_response.status_code == 200:
        result = update_response.json()
        print("✅ User subscription dates updated successfully!")
        print("\n📊 Update result:")
        print(json.dumps(result, indent=2))
        
        print(f"\n🎉 SUCCESS! User {user_id} now has correct subscription dates:")
        print(f"  ✅ Start: June 28, 2025 at 10:37 PM UTC")
        print(f"  ✅ End: June 28, 2026 at 10:37 PM UTC")
        print(f"  ✅ Period: Annual (exactly 1 year)")
        print(f"\n🔗 Check admin panel: https://mytacoai.com/_admin#/users/{user_id}/show")
        
    else:
        print(f"❌ Failed to update user: {update_response.status_code}")
        print("Response:", update_response.text)

if __name__ == "__main__":
    fix_production_user()
