"""
Production Error Testing Script for MyTaco AI
Triggers real errors in production to test monitoring system
"""

import asyncio
import httpx
import json
from datetime import datetime

# Replace with your actual Railway production URL
PRODUCTION_URL = "https://mytacoai.com"  # or your Railway URL

async def test_production_errors():
    """Test real production errors to verify monitoring alerts"""
    print("🚨 MyTaco AI Production Error Testing")
    print("=" * 60)
    print(f"Testing against: {PRODUCTION_URL}")
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    print("⚠️  This will trigger real errors in production to test monitoring")
    print("📱 Watch your #mytaco-alerts Slack channel for alerts")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: 404 Error (Should NOT trigger alert - by design)
        print("1️⃣ Testing 404 Error (should NOT alert)...")
        try:
            response = await client.get(f"{PRODUCTION_URL}/api/nonexistent-endpoint")
            print(f"   Status: {response.status_code} (Expected: 404)")
            print("   ✅ This should NOT generate a Slack alert (4xx errors filtered)")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        await asyncio.sleep(3)
        
        # Test 2: OpenAI Token Error (Should trigger CRITICAL alert)
        print("\n2️⃣ Testing OpenAI Token Error (should alert CRITICAL)...")
        try:
            response = await client.post(
                f"{PRODUCTION_URL}/api/realtime/token",
                json={
                    "language": "english",
                    "level": "B1",
                    "topic": "travel"
                },
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code >= 500:
                print("   🚨 This should generate a CRITICAL Slack alert (5xx error)")
            elif response.status_code == 401 or response.status_code == 403:
                print("   ⚠️  This might generate a HIGH Slack alert (auth error)")
            else:
                print("   ℹ️  Unexpected response - check what happened")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        await asyncio.sleep(3)
        
        # Test 3: Authentication Error (Should trigger HIGH alert)
        print("\n3️⃣ Testing Authentication Error (should alert HIGH)...")
        try:
            response = await client.get(
                f"{PRODUCTION_URL}/auth/me",
                headers={"Authorization": "Bearer invalid_token_12345"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code >= 500:
                print("   🚨 This should generate a HIGH Slack alert (auth error)")
            elif response.status_code == 401:
                print("   ⚠️  401 Unauthorized - might trigger auth monitoring")
            else:
                print("   ℹ️  Check response details")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        await asyncio.sleep(3)
        
        # Test 4: Performance Test (Try to trigger slow response)
        print("\n4️⃣ Testing Performance (looking for slow responses)...")
        try:
            start_time = datetime.now()
            response = await client.get(f"{PRODUCTION_URL}/health")
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"   Status: {response.status_code}")
            print(f"   Response time: {response_time:.2f}s")
            
            if response_time > 5.0:
                print("   ⚡ This should generate a MEDIUM performance alert (>5s)")
            else:
                print("   ✅ Fast response - no performance alert expected")
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        await asyncio.sleep(3)
        
        # Test 5: Try to trigger a 500 error
        print("\n5️⃣ Testing 500 Error (should alert HIGH)...")
        try:
            # Try to access an endpoint that might cause a server error
            response = await client.post(
                f"{PRODUCTION_URL}/api/learning/session-summary",
                json={"invalid": "data", "plan_id": "nonexistent"},
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code >= 500:
                print("   🚨 This should generate a HIGH Slack alert (5xx error)")
            elif response.status_code == 401 or response.status_code == 403:
                print("   ⚠️  Auth required - might trigger auth alert")
            else:
                print("   ℹ️  No server error triggered")
        except Exception as e:
            print(f"   Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Production Error Testing Complete!")
    print()
    print("📱 Check your #mytaco-alerts Slack channel for:")
    print("   🚨 CRITICAL alerts (red) - OpenAI/Database errors")
    print("   ⚠️ HIGH alerts (orange) - Auth/5xx errors")
    print("   ⚡ MEDIUM alerts (yellow) - Performance issues")
    print()
    print("⏰ Alerts should appear within 10-30 seconds")
    print("🔄 If no alerts appear, the errors might not be triggering 5xx responses")

async def test_railway_console():
    """Test monitoring from Railway console"""
    print("🚀 Railway Console Monitoring Test")
    print("=" * 50)
    print("Run this in Railway Console to test monitoring:")
    print()
    print("cd backend")
    print("python test_production_monitoring.py")
    print()
    print("This will send test alerts directly from production environment")

if __name__ == "__main__":
    print("Choose testing method:")
    print("1. Test production errors (triggers real errors)")
    print("2. Show Railway console commands")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_production_errors())
    elif choice == "2":
        asyncio.run(test_railway_console())
    else:
        print("Invalid choice. Run script again with 1 or 2.")
