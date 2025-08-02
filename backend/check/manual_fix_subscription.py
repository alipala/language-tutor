import requests
import json
from datetime import datetime, timezone

# We know from Stripe that the correct dates are:
# Period start: 2025-06-28 22:37:34+00:00
# Period end: 2026-06-28 22:37:34+00:00

# Admin login
admin_login_data = {
    "email": "admin@languagetutor.com",
    "password": "admin123"
}

# Login to get admin token
print("Logging in as admin...")
login_response = requests.post(
    "https://mytacoai.com/api/admin/login",
    json=admin_login_data
)

if login_response.status_code == 200:
    admin_token = login_response.json()["access_token"]
    print("✅ Admin login successful")
    
    # Update user directly with correct dates
    user_id = "685fe4b2acdf4f770e24345e"
    
    # Prepare the correct subscription data
    update_data = {
        "current_period_start": "2025-06-28T22:37:34.000Z",
        "current_period_end": "2026-06-28T22:37:34.000Z",
        "subscription_period": "annual",
        "subscription_status": "active",
        "subscription_started_at": "2025-06-28T22:37:34.000Z",
        "subscription_expires_at": "2026-06-28T22:37:34.000Z"
    }
    
    print(f"Updating user {user_id} with correct subscription dates...")
    print(f"Period: {update_data['current_period_start']} to {update_data['current_period_end']}")
    
    update_response = requests.put(
        f"https://mytacoai.com/api/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    if update_response.status_code == 200:
        result = update_response.json()
        print("✅ User subscription dates updated successfully!")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Failed to update user: {update_response.status_code}")
        print(update_response.text)
else:
    print(f"❌ Admin login failed: {login_response.status_code}")
    print(login_response.text)
