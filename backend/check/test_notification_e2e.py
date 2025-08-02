#!/usr/bin/env python3
"""
End-to-End Notification System API Test
Tests the complete notification flow from admin creation to user consumption
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://mytacoai.com"
ADMIN_EMAIL = "admin@languagetutor.com"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "e74709d6-1ad0-45a7-af51-d97780f875c2@mailslurp.biz"
USER_PASSWORD = "040050803"

def print_step(step_num, description):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def print_result(success, message, data=None):
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{status}: {message}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")

def test_admin_login():
    """Test admin login and get token"""
    print_step(1, "Testing Admin Login")
    
    response = requests.post(f"{BASE_URL}/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print_result(True, "Admin login successful", {"token_preview": token[:20] + "..." if token else None})
        return token
    else:
        print_result(False, f"Admin login failed: {response.text}")
        return None

def test_user_login():
    """Test user login and get token"""
    print_step(2, "Testing User Login")
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print_result(True, "User login successful", {"token_preview": token[:20] + "..." if token else None})
        return token
    else:
        print_result(False, f"User login failed: {response.text}")
        return None

def test_create_notification(admin_token):
    """Test creating a notification via admin API"""
    print_step(3, "Testing Notification Creation")
    
    if not admin_token:
        print_result(False, "No admin token available")
        return None
    
    notification_data = {
        "title": "Test Notification - E2E API Test",
        "content": "<p>This is a <strong>test notification</strong> created via API testing.</p><p>It includes <em>rich text formatting</em> to verify the system works correctly.</p>",
        "notification_type": "Information",
        "target_user_ids": None,  # Send to all users
        "send_immediately": True,
        "scheduled_send_time": None
    }
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.post(f"{BASE_URL}/api/admin/notifications", 
                           json=notification_data, 
                           headers=headers)
    
    if response.status_code in [200, 201]:
        data = response.json()
        notification_id = data.get('id')
        print_result(True, "Notification created successfully", {"notification_id": notification_id})
        return notification_id
    else:
        print_result(False, f"Notification creation failed: {response.text}")
        return None

def test_user_unread_count(user_token):
    """Test getting user's unread notification count"""
    print_step(4, "Testing User Unread Count")
    
    if not user_token:
        print_result(False, "No user token available")
        return 0
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/api/unread-count", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('unread_count', 0)
        print_result(True, f"Unread count retrieved: {count}", data)
        return count
    else:
        print_result(False, f"Failed to get unread count: {response.text}")
        return 0

def test_user_notifications(user_token):
    """Test getting user's notifications"""
    print_step(5, "Testing User Notifications List")
    
    if not user_token:
        print_result(False, "No user token available")
        return []
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/api/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        notifications = data.get('notifications', [])
        print_result(True, f"Retrieved {len(notifications)} notifications", {
            "total_count": data.get('total_count'),
            "unread_count": data.get('unread_count'),
            "notifications_preview": [n.get('notification', {}).get('title') for n in notifications[:3]]
        })
        return notifications
    else:
        print_result(False, f"Failed to get notifications: {response.text}")
        return []

def test_mark_notification_read(user_token, notification_id):
    """Test marking a notification as read"""
    print_step(6, "Testing Mark Notification as Read")
    
    if not user_token or not notification_id:
        print_result(False, "Missing user token or notification ID")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.post(f"{BASE_URL}/api/mark-read", 
                           json={"notification_id": notification_id}, 
                           headers=headers)
    
    if response.status_code == 200:
        print_result(True, "Notification marked as read successfully")
        return True
    else:
        print_result(False, f"Failed to mark notification as read: {response.text}")
        return False

def test_user_unread_count_after_read(user_token, initial_count):
    """Test that unread count decreased after marking as read"""
    print_step(7, "Testing Unread Count After Marking as Read")
    
    if not user_token:
        print_result(False, "No user token available")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/api/unread-count", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        new_count = data.get('unread_count', 0)
        success = new_count < initial_count
        print_result(success, f"Unread count changed from {initial_count} to {new_count}", data)
        return success
    else:
        print_result(False, f"Failed to get updated unread count: {response.text}")
        return False

def main():
    """Run the complete end-to-end test"""
    print("🚀 Starting End-to-End Notification System API Test")
    print(f"Testing against: {BASE_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    print(f"User: {USER_EMAIL}")
    
    # Test admin login
    admin_token = test_admin_login()
    
    # Test user login
    user_token = test_user_login()
    
    # Get initial unread count
    initial_unread_count = test_user_unread_count(user_token)
    
    # Create notification
    notification_id = test_create_notification(admin_token)
    
    # Wait a moment for notification to be processed
    time.sleep(2)
    
    # Get user notifications
    notifications = test_user_notifications(user_token)
    
    # Find our test notification
    test_notification = None
    for notif in notifications:
        if notif.get('notification', {}).get('title') == "Test Notification - E2E API Test":
            test_notification = notif
            break
    
    if test_notification:
        notification_id = test_notification.get('notification_id')
        print(f"\n📧 Found our test notification with ID: {notification_id}")
        
        # Mark as read
        mark_success = test_mark_notification_read(user_token, notification_id)
        
        # Check unread count decreased
        if mark_success:
            test_user_unread_count_after_read(user_token, initial_unread_count)
    else:
        print_result(False, "Could not find our test notification in user's notifications")
    
    print("\n" + "="*60)
    print("🎯 END-TO-END TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()
