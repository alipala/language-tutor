"""
Test script for MyTaco AI monitoring system
Tests Slack notifications and error handling
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from monitoring import (
    AlertSeverity,
    AlertContext,
    send_error_alert,
    send_performance_alert,
    send_business_logic_alert,
    send_health_alert,
    slack_notifier
)

async def test_slack_connection():
    """Test basic Slack webhook connectivity"""
    print("🔧 Testing Slack webhook connectivity...")
    
    if not slack_notifier.is_enabled():
        print("❌ Slack webhook not configured. Please set SLACK_WEBHOOK_URL in .env")
        return False
    
    try:
        context = AlertContext(
            endpoint="/test",
            method="GET",
            environment="testing"
        )
        
        success = await send_business_logic_alert(
            operation="Monitoring System Test",
            issue="Testing Slack integration for MyTaco AI monitoring",
            context=context,
            severity=AlertSeverity.LOW
        )
        
        if success:
            print("✅ Slack webhook test successful!")
            return True
        else:
            print("❌ Slack webhook test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Slack webhook: {str(e)}")
        return False

async def test_error_alerts():
    """Test error alert functionality"""
    print("\n🚨 Testing error alerts...")
    
    context = AlertContext(
        endpoint="/api/realtime/token",
        method="POST",
        user_email="test@example.com",
        environment="testing"
    )
    
    # Test different error types
    test_errors = [
        (Exception("OpenAI API rate limit exceeded"), AlertSeverity.CRITICAL),
        (Exception("Database connection timeout"), AlertSeverity.CRITICAL),
        (Exception("Stripe payment processing failed"), AlertSeverity.HIGH),
        (Exception("Authentication token expired"), AlertSeverity.HIGH),
        (Exception("General application error"), AlertSeverity.MEDIUM)
    ]
    
    for error, expected_severity in test_errors:
        try:
            success = await send_error_alert(
                error=error,
                context=context,
                additional_data={
                    "test_case": True,
                    "expected_severity": expected_severity.value
                }
            )
            
            if success:
                print(f"✅ Error alert sent: {str(error)[:50]}...")
            else:
                print(f"❌ Failed to send error alert: {str(error)[:50]}...")
                
        except Exception as e:
            print(f"❌ Exception testing error alert: {str(e)}")

async def test_performance_alerts():
    """Test performance alert functionality"""
    print("\n⚡ Testing performance alerts...")
    
    context = AlertContext(
        endpoint="/api/realtime/token",
        method="POST",
        user_email="test@example.com",
        environment="testing"
    )
    
    # Test different response times
    test_times = [6.0, 10.0, 15.0]  # Above threshold
    
    for response_time in test_times:
        try:
            success = await send_performance_alert(
                endpoint="/api/realtime/token",
                response_time=response_time,
                context=context,
                additional_data={
                    "test_case": True,
                    "simulated_time": response_time
                }
            )
            
            if success:
                print(f"✅ Performance alert sent for {response_time}s response time")
            else:
                print(f"❌ Failed to send performance alert for {response_time}s")
                
        except Exception as e:
            print(f"❌ Exception testing performance alert: {str(e)}")

async def test_business_logic_alerts():
    """Test business logic alert functionality"""
    print("\n💼 Testing business logic alerts...")
    
    context = AlertContext(
        endpoint="/api/learning/session-summary",
        method="POST",
        user_email="test@example.com",
        environment="testing"
    )
    
    test_cases = [
        ("Session Summary Generation", "Failed to generate AI-powered session summary", AlertSeverity.MEDIUM),
        ("Learning Plan Update", "Unable to update user learning plan progress", AlertSeverity.HIGH),
        ("Subscription Tracking", "Failed to track subscription usage", AlertSeverity.HIGH)
    ]
    
    for operation, issue, severity in test_cases:
        try:
            success = await send_business_logic_alert(
                operation=operation,
                issue=issue,
                context=context,
                severity=severity,
                additional_data={
                    "test_case": True,
                    "operation_type": operation
                }
            )
            
            if success:
                print(f"✅ Business logic alert sent: {operation}")
            else:
                print(f"❌ Failed to send business logic alert: {operation}")
                
        except Exception as e:
            print(f"❌ Exception testing business logic alert: {str(e)}")

async def test_health_alerts():
    """Test health check alert functionality"""
    print("\n🏥 Testing health alerts...")
    
    test_services = [
        ("MongoDB", "disconnected", "Database connection lost"),
        ("OpenAI API", "rate_limited", "API rate limit exceeded"),
        ("Stripe API", "timeout", "Payment service timeout")
    ]
    
    for service, status, details in test_services:
        try:
            success = await send_health_alert(
                service=service,
                status=status,
                details=details,
                severity=AlertSeverity.HIGH
            )
            
            if success:
                print(f"✅ Health alert sent: {service} - {status}")
            else:
                print(f"❌ Failed to send health alert: {service}")
                
        except Exception as e:
            print(f"❌ Exception testing health alert: {str(e)}")

async def test_alert_deduplication():
    """Test alert deduplication functionality"""
    print("\n🔄 Testing alert deduplication...")
    
    context = AlertContext(
        endpoint="/api/test",
        method="GET",
        environment="testing"
    )
    
    # Send the same alert multiple times
    error = Exception("Duplicate test error")
    
    print("Sending 3 identical alerts (should only send 1)...")
    
    results = []
    for i in range(3):
        success = await send_error_alert(
            error=error,
            context=context,
            additional_data={
                "test_case": True,
                "duplicate_test": True,
                "attempt": i + 1
            }
        )
        results.append(success)
        
        # Small delay between attempts
        await asyncio.sleep(0.1)
    
    sent_count = sum(results)
    print(f"✅ Deduplication test: {sent_count}/3 alerts sent (expected: 1)")

async def test_monitoring_configuration():
    """Test monitoring configuration"""
    print("\n⚙️ Testing monitoring configuration...")
    
    print(f"Slack webhook configured: {slack_notifier.is_enabled()}")
    print(f"Environment: {slack_notifier.environment}")
    print(f"Performance threshold: {slack_notifier.performance_threshold}s")
    print(f"Error rate threshold: {slack_notifier.error_rate_threshold}%")
    print(f"Cache duration: {slack_notifier.cache_duration}")

async def main():
    """Run all monitoring tests"""
    print("🚀 MyTaco AI Monitoring System Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test configuration
    await test_monitoring_configuration()
    
    # Test Slack connectivity first
    slack_works = await test_slack_connection()
    
    if not slack_works:
        print("\n❌ Slack webhook not working. Skipping alert tests.")
        print("\nTo enable Slack alerts:")
        print("1. Create a Slack webhook URL")
        print("2. Add SLACK_WEBHOOK_URL=your_webhook_url to your .env file")
        print("3. Run this test again")
        return
    
    # Run all alert tests
    await test_error_alerts()
    await test_performance_alerts()
    await test_business_logic_alerts()
    await test_health_alerts()
    await test_alert_deduplication()
    
    print("\n" + "=" * 60)
    print("✅ Monitoring system test suite completed!")
    print(f"Test finished at: {datetime.now().isoformat()}")
    print("\nCheck your Slack channel for test alerts.")

if __name__ == "__main__":
    asyncio.run(main())
