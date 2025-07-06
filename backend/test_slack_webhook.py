"""
Quick Slack webhook test for MyTaco AI monitoring
Tests the webhook URL directly to verify connectivity
"""

import asyncio
import httpx
import json
from datetime import datetime

# Your Slack webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

async def test_slack_webhook():
    """Test the Slack webhook directly"""
    print("🧪 Testing Slack webhook connectivity...")
    print(f"📡 Webhook URL: {SLACK_WEBHOOK_URL[:50]}...")
    
    # Create a test message
    test_message = {
        "text": "🚀 *MyTaco AI Monitoring Test*",
        "attachments": [
            {
                "color": "#36a64f",  # Green
                "title": "✅ Monitoring System Test",
                "text": "This is a test message to verify Slack webhook integration is working correctly.",
                "fields": [
                    {
                        "title": "Test Time",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "short": True
                    },
                    {
                        "title": "Status",
                        "value": "Testing webhook connectivity",
                        "short": True
                    }
                ],
                "footer": "MyTaco AI Monitoring",
                "ts": int(datetime.now().timestamp())
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                SLACK_WEBHOOK_URL,
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ SUCCESS! Test message sent to Slack")
                print("📱 Check your #mytaco-alerts channel for the test message")
                return True
            else:
                print(f"❌ FAILED! HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

async def test_monitoring_alerts():
    """Test the actual monitoring system alerts"""
    print("\n🚨 Testing monitoring system alerts...")
    
    # Import the monitoring system
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    
    from monitoring import (
        AlertSeverity,
        AlertContext,
        send_error_alert,
        send_performance_alert,
        send_business_logic_alert
    )
    
    # Test context
    context = AlertContext(
        endpoint="/test",
        method="POST",
        user_email="test@mytacoai.com",
        environment="production-test"
    )
    
    # Test 1: Business logic alert (LOW severity)
    print("📤 Sending test business logic alert...")
    success1 = await send_business_logic_alert(
        operation="Monitoring System Test",
        issue="Testing Slack integration for MyTaco AI production monitoring",
        context=context,
        severity=AlertSeverity.LOW
    )
    
    if success1:
        print("✅ Business logic alert sent successfully")
    else:
        print("❌ Business logic alert failed")
    
    # Small delay
    await asyncio.sleep(2)
    
    # Test 2: Error alert (MEDIUM severity)
    print("📤 Sending test error alert...")
    test_error = Exception("Test error for monitoring system validation")
    success2 = await send_error_alert(
        error=test_error,
        context=context,
        severity=AlertSeverity.MEDIUM
    )
    
    if success2:
        print("✅ Error alert sent successfully")
    else:
        print("❌ Error alert failed")
    
    # Small delay
    await asyncio.sleep(2)
    
    # Test 3: Performance alert (HIGH severity)
    print("📤 Sending test performance alert...")
    success3 = await send_performance_alert(
        endpoint="/api/realtime/token",
        response_time=8.5,  # Slow response
        context=context
    )
    
    if success3:
        print("✅ Performance alert sent successfully")
    else:
        print("❌ Performance alert failed")
    
    return success1 and success2 and success3

async def main():
    """Run all tests"""
    print("🚀 MyTaco AI Slack Webhook Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Test 1: Direct webhook test
    webhook_works = await test_slack_webhook()
    
    if not webhook_works:
        print("\n❌ Webhook test failed. Check the URL and try again.")
        return
    
    print("\n⏳ Waiting 3 seconds before testing monitoring alerts...")
    await asyncio.sleep(3)
    
    # Test 2: Monitoring system alerts
    monitoring_works = await test_monitoring_alerts()
    
    print("\n" + "=" * 50)
    if webhook_works and monitoring_works:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Slack webhook is working correctly")
        print("✅ Monitoring system is sending alerts")
        print("📱 Check your #mytaco-alerts channel for test messages")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())
