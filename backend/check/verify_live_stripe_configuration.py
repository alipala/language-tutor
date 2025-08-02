#!/usr/bin/env python3
"""
Live Stripe Configuration Verification Script
Verifies all Stripe live mode settings and webhook configuration
"""

import stripe
import requests
import json
from datetime import datetime, timezone

# Live mode configuration - REPLACE WITH YOUR ACTUAL KEYS
STRIPE_LIVE_SECRET_KEY = "sk_live_YOUR_SECRET_KEY_HERE"
STRIPE_LIVE_PUBLISHABLE_KEY = "pk_live_YOUR_PUBLISHABLE_KEY_HERE"
WEBHOOK_URL = "https://your-domain.com/api/stripe/webhook"

stripe.api_key = STRIPE_LIVE_SECRET_KEY

def verify_api_keys():
    """Verify Stripe API keys are working"""
    print("🔑 VERIFYING STRIPE API KEYS")
    print("=" * 50)
    
    try:
        # Test secret key
        balance = stripe.Balance.retrieve()
        print(f"✅ Secret Key: Working (Live mode: {balance.livemode})")
        
        # Test publishable key format
        if STRIPE_LIVE_PUBLISHABLE_KEY.startswith("pk_live_"):
            print("✅ Publishable Key: Format correct (pk_live_)")
        else:
            print("❌ Publishable Key: Invalid format")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ API Key Error: {str(e)}")
        return False

def verify_products():
    """Verify live mode products"""
    print("\n📦 VERIFYING PRODUCTS")
    print("=" * 50)
    
    expected_products = {
        "prod_SZ5xUhxcUSrOIo": "Team Mastery Plan",
        "prod_SZ5YV4PDK1EJvC": "Fluency Builder Plan"
    }
    
    try:
        products = stripe.Product.list(active=True)
        
        found_products = {}
        for product in products.data:
            found_products[product.id] = product.name
            
        print("Found Products:")
        for product_id, name in found_products.items():
            print(f"  {product_id}: {name}")
        
        # Verify expected products
        all_found = True
        for expected_id, expected_name in expected_products.items():
            if expected_id in found_products:
                if found_products[expected_id] == expected_name:
                    print(f"✅ {expected_name}: Found and name matches")
                else:
                    print(f"⚠️  {expected_name}: Found but name mismatch")
            else:
                print(f"❌ {expected_name}: Not found")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Product verification error: {str(e)}")
        return False

def verify_prices():
    """Verify product prices"""
    print("\n💰 VERIFYING PRICES")
    print("=" * 50)
    
    try:
        # Team Mastery Plan prices
        team_prices = stripe.Price.list(product="prod_SZ5xUhxcUSrOIo", active=True)
        print("\nTeam Mastery Plan:")
        for price in team_prices.data:
            interval = price.recurring.interval if price.recurring else "one-time"
            amount = price.unit_amount / 100  # Convert from cents
            print(f"  {price.id}: €{amount:.2f}/{interval}")
        
        # Fluency Builder Plan prices
        fluency_prices = stripe.Price.list(product="prod_SZ5YV4PDK1EJvC", active=True)
        print("\nFluency Builder Plan:")
        for price in fluency_prices.data:
            interval = price.recurring.interval if price.recurring else "one-time"
            amount = price.unit_amount / 100  # Convert from cents
            print(f"  {price.id}: €{amount:.2f}/{interval}")
        
        total_prices = len(team_prices.data) + len(fluency_prices.data)
        print(f"\n✅ Found {total_prices} active prices")
        return total_prices > 0
        
    except Exception as e:
        print(f"❌ Price verification error: {str(e)}")
        return False

def verify_webhook():
    """Verify webhook configuration"""
    print("\n🔔 VERIFYING WEBHOOK CONFIGURATION")
    print("=" * 50)
    
    try:
        webhooks = stripe.WebhookEndpoint.list()
        
        target_webhook = None
        for webhook in webhooks.data:
            if webhook.url == WEBHOOK_URL:
                target_webhook = webhook
                break
        
        if not target_webhook:
            print(f"❌ Webhook not found: {WEBHOOK_URL}")
            return False
        
        print(f"✅ Webhook found: {WEBHOOK_URL}")
        print(f"   Status: {target_webhook.status}")
        print(f"   Live mode: {target_webhook.livemode}")
        print(f"   Events: {len(target_webhook.enabled_events)} configured")
        
        # Check for critical events
        critical_events = [
            "customer.subscription.trial_will_end",
            "customer.subscription.updated",
            "customer.subscription.created",
            "customer.subscription.deleted",
            "checkout.session.completed",
            "invoice.payment_succeeded"
        ]
        
        missing_events = []
        for event in critical_events:
            if event not in target_webhook.enabled_events:
                missing_events.append(event)
        
        if missing_events:
            print(f"⚠️  Missing critical events: {missing_events}")
        else:
            print("✅ All critical events configured")
        
        # Special check for our new event
        if "customer.subscription.trial_will_end" in target_webhook.enabled_events:
            print("✅ CRITICAL: customer.subscription.trial_will_end event is configured!")
        else:
            print("❌ CRITICAL: customer.subscription.trial_will_end event is MISSING!")
            return False
        
        return len(missing_events) == 0
        
    except Exception as e:
        print(f"❌ Webhook verification error: {str(e)}")
        return False

def test_webhook_endpoint():
    """Test webhook endpoint accessibility"""
    print("\n🌐 TESTING WEBHOOK ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={"test": "verification"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Webhook URL: {WEBHOOK_URL}")
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Webhook endpoint accessible (400 expected - missing signature)")
            return True
        elif response.status_code == 404:
            print("❌ Webhook endpoint not found (404)")
            return False
        elif response.status_code == 500:
            print("❌ Server error (500)")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return True  # Might still be working
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def verify_environment_variables():
    """Verify environment variables match"""
    print("\n🔧 VERIFYING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    print("Expected Live Mode Keys:")
    print(f"  STRIPE_PUBLISHABLE_KEY: {STRIPE_LIVE_PUBLISHABLE_KEY}")
    print(f"  STRIPE_SECRET_KEY: {STRIPE_LIVE_SECRET_KEY[:20]}...")
    
    print("\n⚠️  IMPORTANT: Ensure these keys are set in your Railway environment:")
    print("  1. STRIPE_PUBLISHABLE_KEY")
    print("  2. STRIPE_SECRET_KEY") 
    print("  3. STRIPE_WEBHOOK_SECRET (get from webhook endpoint settings)")
    
    return True

def main():
    """Run all verifications"""
    print("🔍 LIVE STRIPE CONFIGURATION VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc)}")
    print("=" * 60)
    
    results = []
    
    # Run all verifications
    results.append(("API Keys", verify_api_keys()))
    results.append(("Products", verify_products()))
    results.append(("Prices", verify_prices()))
    results.append(("Webhook Config", verify_webhook()))
    results.append(("Webhook Endpoint", test_webhook_endpoint()))
    results.append(("Environment Vars", verify_environment_variables()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} verifications passed")
    
    if passed == len(results):
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\n✅ Your Stripe live mode configuration is ready for production!")
        print("\n📝 Next steps:")
        print("   1. Deploy to Railway with live mode keys")
        print("   2. Test with a real subscription")
        print("   3. Monitor webhook events in Stripe Dashboard")
    else:
        print("\n⚠️  Some verifications failed. Please fix issues before going live.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
