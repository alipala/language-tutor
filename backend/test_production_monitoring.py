"""
Production monitoring test for MyTaco AI
Tests the monitoring system with proper environment loading
"""

import os
import asyncio
from datetime import datetime

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Now import monitoring after env is loaded
from monitoring import (
    AlertSeverity,
    AlertContext,
    send_error_alert,
    send_performance_alert,
    send_business_logic_alert,
    send_health_alert,
    slack_notifier
)

async def test_production_monitoring():
    """Test the monitoring system with production-like scenarios"""
    print("🚀 MyTaco AI Production Monitoring Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Check configuration
    print("⚙️ Monitoring Configuration:")
    print(f"  Slack webhook configured: {slack_notifier.is_enabled()}")
    print(f"  Environment: {slack_notifier.environment}")
    print(f"  Performance threshold: {slack_notifier.performance_threshold}s")
    print(f"  Webhook URL: {os.getenv('SLACK_WEBHOOK_URL', 'Not set')[:50]}...")
    print()
    
    if not slack_notifier.is_enabled():
        print("❌ Slack webhook not configured properly")
        return False
    
    # Test context for production-like scenarios
    context = AlertContext(
        endpoint="/api/realtime/token",
        method="POST",
        user_email="customer@example.com",
        environment="production",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
        ip_address="203.0.113.1"
    )
    
    print("🧪 Testing different alert scenarios...")
    print()
    
    # Test 1: Critical OpenAI Error
    print("1️⃣ Testing CRITICAL OpenAI API Error...")
    openai_error = Exception("OpenAI API rate limit exceeded - too many requests")
    success1 = await send_error_alert(
        error=openai_error,
        context=context,
        additional_data={
            "api_endpoint": "realtime/sessions",
            "rate_limit": "exceeded",
            "retry_after": "60 seconds"
        }
    )
    print(f"   Result: {'✅ Sent' if success1 else '❌ Failed'}")
    await asyncio.sleep(2)
    
    # Test 2: High Priority Authentication Error
    print("2️⃣ Testing HIGH Authentication Error...")
    auth_context = AlertContext(
        endpoint="/auth/login",
        method="POST",
        user_email="suspicious@example.com",
        environment="production",
        ip_address="192.0.2.1"
    )
    auth_error = Exception("Authentication failed - invalid credentials")
    success2 = await send_error_alert(
        error=auth_error,
        context=auth_context,
        additional_data={
            "failed_attempts": 5,
            "account_locked": True,
            "suspicious_activity": True
        }
    )
    print(f"   Result: {'✅ Sent' if success2 else '❌ Failed'}")
    await asyncio.sleep(2)
    
    # Test 3: Performance Alert
    print("3️⃣ Testing MEDIUM Performance Alert...")
    perf_context = AlertContext(
        endpoint="/api/sentence/assess",
        method="POST",
        user_email="student@example.com",
        environment="production"
    )
    success3 = await send_performance_alert(
        endpoint="/api/sentence/assess",
        response_time=7.8,
        context=perf_context,
        additional_data={
            "database_query_time": "3.2s",
            "openai_api_time": "4.1s",
            "processing_time": "0.5s"
        }
    )
    print(f"   Result: {'✅ Sent' if success3 else '❌ Failed'}")
    await asyncio.sleep(2)
    
    # Test 4: Business Logic Alert
    print("4️⃣ Testing MEDIUM Business Logic Alert...")
    success4 = await send_business_logic_alert(
        operation="Session Summary Generation",
        issue="Failed to generate AI-powered session summary for learning plan",
        context=context,
        severity=AlertSeverity.MEDIUM,
        additional_data={
            "learning_plan_id": "plan_12345",
            "session_number": 8,
            "total_sessions": 24,
            "error_count": 3
        }
    )
    print(f"   Result: {'✅ Sent' if success4 else '❌ Failed'}")
    await asyncio.sleep(2)
    
    # Test 5: Health Check Alert
    print("5️⃣ Testing HIGH Health Check Alert...")
    success5 = await send_health_alert(
        service="MongoDB",
        status="connection_timeout",
        details="Database connection pool exhausted - unable to process user requests",
        severity=AlertSeverity.HIGH
    )
    print(f"   Result: {'✅ Sent' if success5 else '❌ Failed'}")
    await asyncio.sleep(2)
    
    # Test 6: Low Priority Info Alert
    print("6️⃣ Testing LOW Info Alert...")
    success6 = await send_business_logic_alert(
        operation="Monitoring System Health Check",
        issue="Daily monitoring system health verification completed successfully",
        context=AlertContext(environment="production", endpoint="/health"),
        severity=AlertSeverity.LOW,
        additional_data={
            "alerts_sent_today": 12,
            "system_uptime": "99.9%",
            "last_restart": "2025-07-06T10:00:00Z"
        }
    )
    print(f"   Result: {'✅ Sent' if success6 else '❌ Failed'}")
    
    print()
    print("=" * 60)
    
    # Summary
    total_tests = 6
    passed_tests = sum([success1, success2, success3, success4, success5, success6])
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Monitoring system is working perfectly")
        print("📱 Check your #mytaco-alerts channel for all test alerts")
        print()
        print("🔍 You should see alerts with different colors:")
        print("   🚨 Red (Critical): OpenAI API error")
        print("   ⚠️ Orange (High): Auth error, Health check")
        print("   ⚡ Yellow (Medium): Performance, Business logic")
        print("   ℹ️ Blue (Low): Info alert")
    else:
        print(f"❌ {total_tests - passed_tests} out of {total_tests} tests failed")
        print("Check the output above for details")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(test_production_monitoring())
