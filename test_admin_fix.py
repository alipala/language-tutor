import requests
import json

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
    
    # Fix subscription dates for the specific user
    user_id = "685fe4b2acdf4f770e24345e"
    
    print(f"Fixing subscription dates for user {user_id}...")
    fix_response = requests.post(
        f"https://mytacoai.com/api/admin/fix-subscription-dates/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if fix_response.status_code == 200:
        result = fix_response.json()
        print("✅ Subscription dates fixed successfully!")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Failed to fix subscription dates: {fix_response.status_code}")
        print(fix_response.text)
else:
    print(f"❌ Admin login failed: {login_response.status_code}")
    print(login_response.text)
