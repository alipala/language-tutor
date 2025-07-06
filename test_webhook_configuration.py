#!/usr/bin/env python3
"""
Test script to validate webhook configuration and basic functionality
Run this after deploying to Railway to ensure everything is working
"""

import os
import stripe
import requests
import json
from datetime import datetime, timezone

# Configuration
STRIPE_SECRET_KEY = "sk_test_51Mzx41JcquSiYwWNGndzlyBDtf249jC4H0bjboX2GxHJS2SHb2SXxlZmbt8ObCruGg5KKSTnHgnthxnZknF5F4R300MGsRy0aK"
RAILWAY_WEBHOOK_URL = "https://your-railway-app.railway.app/api/stripe/webhook"  # Update this!

stripe.api_key = STRIPE_SECRET_KEY

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    print("🔗 Testing webhook endpoint accessibility...")
    
    try:
        response = requests.post(
            RAILWAY_WEBHOOK_URL,
            json={"test": "ping"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Webhook endpoint is accessible (400 expected - missing signature)")
            return True
        elif response.status_code == 404:
            print("❌ Webhook endpoint not found (404)")
            return False
        elif response.status_code == 500:
            print("❌ Server error (500)")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to webhook endpoint: {str(e)}")
        return False

def test_stripe_connection():
    """Test Stripe API connection"""
    print("\n💳 Testing Stripe API connection...")
    
    try:
        # Try to list a few customers
        customers = stripe.Customer.list(limit=1)
        print("✅ Stripe API connection successful")
        return True
    except Exception as e:
        print(f"❌ Stripe API connection failed: {str(e)}")
        return False

def check_webhook_events():
    """Check configured webhook events"""
    print("\n🔔 Checking webhook configuration...")
    
    try:
        # List webhook endpoints
        webhooks = stripe.WebhookEndpoint.list()
        
        if not webhooks.data:
            print("❌ No webhook endpoints configured")
            return False
        
        for webhook in webhooks.data:
            print(f"\n📍 Webhook: {webhook.url}")
            print(f"   Status: {webhook.status}")
            print(f"   Events: {len(webhook.enabled_events)} configured")
            
            # Check for our required events
            required_events = [
                "customer.subscription.trial_will_end",
                "customer.subscription.updated",
                "customer.subscription.created",
                "customer.subscription.deleted"
            ]
            
            missing_events = []
            for event in required_events:
                if event not in webhook.enabled_events:
                    missing_events.append(event)
            
            if missing_events:
                print(f"⚠️  Missing events: {missing_events}")
                print("   Please add these events in Stripe Dashboard")
            else:
                print("✅ All required events are configured")
        
        return len(webhooks.data) > 0
        
    except Exception as e:
        print(f"❌ Failed to check webhook configuration: {str(e)}")
        return False

def test_date_calculations():
    """Test date calculation functionality"""
    print("\n📅 Testing date calculations...")
    
    try:
        from dateutil.relativedelta import relativedelta
        from datetime import datetime, timezone
        
        # Test basic calculation
        trial_end = datetime(2025, 7, 11, 10, 9, 12, tzinfo=timezone.utc)
        monthly_expiry = trial_end + relativedelta(months=1)
        expected = datetime(2025, 8, 11, 10, 9, 12, tzinfo=timezone.utc)
        
        if monthly_expiry == expected:
            print("✅ Date calculations working correctly")
            print(f"   Trial end: {trial_end}")
            print(f"   Monthly expiry: {monthly_expiry}")
            return True
        else:
            print(f"❌ Date calculation error: {monthly_expiry} != {expected}")
            return False
            
    except ImportError as e:
        print(f"❌ Missing dependency: {str(e)}")
        print("   Please install python-dateutil")
        return False
    except Exception as e:
        print(f"❌ Date calculation error: {str(e)}")
        return False

def create_test_webhook_event():
    """Create a test webhook event for validation"""
    print("\n🧪 Creating test webhook event...")
    
    try:
        # Find George's subscription for testing
        subscription = stripe.Subscription.retrieve("sub_1Rh6YOJcquSiYwWNTOhUyBnQ")
        
        print(f"📊 George's subscription status: {subscription.status}")
        print(f"   Trial end: {datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc) if subscription.trial_end else 'None'}")
        
        # Note: We can't actually trigger webhooks programmatically
        # This would need to be done via Stripe CLI or dashboard
        print("\n💡 To test webhooks, use Stripe CLI:")
        print("   stripe trigger customer.subscription.trial_will_end")
        print("   stripe trigger customer.subscription.updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing test subscription: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🔧 WEBHOOK CONFIGURATION VALIDATION")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(("Webhook Endpoint", test_webhook_endpoint()))
    results.append(("Stripe Connection", test_stripe_connection()))
    results.append(("Webhook Events", check_webhook_events()))
    results.append(("Date Calculations", test_date_calculations()))
    results.append(("Test Data Access", create_test_webhook_event()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Ready for webhook testing.")
        print("\nNext steps:")
        print("1. Update RAILWAY_WEBHOOK_URL in this script")
        print("2. Deploy to Railway")
        print("3. Configure webhook in Stripe Dashboard")
        print("4. Test with Stripe CLI")
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deployment.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
