#!/usr/bin/env python3
"""
Test Slack webhook URL
"""

import requests
import json

# Your NEW webhook URL
WEBHOOK_URL = "https://hooks.slack.com/services/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"

def test_slack_webhook():
    """Test the Slack webhook"""
    print(f"🔗 Testing Slack webhook: {WEBHOOK_URL}")
    
    # Simple test message
    test_message = {
        "text": "🧪 Test message from Railway deployment",
        "username": "My Taco AI Bot",
        "icon_emoji": ":taco:"
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Slack webhook is working!")
            return True
        else:
            print(f"❌ Slack webhook failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")
        return False

def check_webhook_format():
    """Check if webhook URL format is correct"""
    print("\n🔍 Checking webhook URL format...")
    
    if not WEBHOOK_URL.startswith("https://hooks.slack.com/services/"):
        print("❌ Webhook URL doesn't start with correct prefix")
        return False
    
    parts = WEBHOOK_URL.replace("https://hooks.slack.com/services/", "").split("/")
    if len(parts) != 3:
        print(f"❌ Webhook URL should have 3 parts after /services/, found {len(parts)}")
        return False
    
    print(f"✅ Webhook format looks correct:")
    print(f"   Team ID: {parts[0]}")
    print(f"   Channel ID: {parts[1]}")
    print(f"   Token: {parts[2]}")
    
    return True

if __name__ == "__main__":
    print("🧪 SLACK WEBHOOK TESTING")
    print("=" * 50)
    
    # Check format first
    if check_webhook_format():
        # Test the webhook
        test_slack_webhook()
    
    print("\n📋 TROUBLESHOOTING STEPS:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Find your app and click on it")
    print("3. Go to 'Incoming Webhooks' in left sidebar")
    print("4. Make sure 'Activate Incoming Webhooks' is ON")
    print("5. Copy the webhook URL and compare with Railway env var")
    print("6. If URL is different, update SLACK_WEBHOOK_URL in Railway")
