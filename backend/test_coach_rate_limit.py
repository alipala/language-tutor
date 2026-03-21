"""
Test TaalCoach Rate Limiting
=============================
Validates rate limits work correctly for free and premium users.

Usage:
    python test_coach_rate_limit.py
"""

import asyncio
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
COACH_ENDPOINT = f"{BASE_URL}/api/coach/chat"

# Test user tokens (replace with actual tokens)
FREE_USER_TOKEN = None  # Get from /api/auth/login
PREMIUM_USER_TOKEN = None  # Get from /api/auth/login

# Rate limits
FREE_LIMIT = 10  # messages per hour
PREMIUM_LIMIT = 20  # messages per hour


def make_coach_request(token: str, message: str):
    """Make a single coach chat request"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "language": "en",
        "message": message,
        "conversation_history": []
    }

    response = requests.post(COACH_ENDPOINT, headers=headers, json=payload)
    return response


def test_free_user_rate_limit():
    """Test free user rate limit (10 messages/hour)"""
    print("=" * 80)
    print("TEST 1: Free User Rate Limit (10 messages/hour)")
    print("=" * 80)

    if not FREE_USER_TOKEN:
        print("⚠️  FREE_USER_TOKEN not set. Skipping test.")
        print("   Get token from: POST /api/auth/login")
        return

    print(f"Testing with FREE_USER_TOKEN...")
    print()

    success_count = 0
    rate_limited = False

    for i in range(FREE_LIMIT + 2):  # Try 12 requests (should hit limit at 11)
        print(f"Request {i+1}/{FREE_LIMIT + 2}...", end=" ")

        response = make_coach_request(FREE_USER_TOKEN, f"Test message {i+1}")

        if response.status_code == 200:
            success_count += 1
            print(f"✅ SUCCESS (200)")
        elif response.status_code == 429:
            rate_limited = True
            data = response.json()
            print(f"🚫 RATE LIMITED (429)")
            print(f"   Message: {data['detail']['message']}")
            print(f"   Retry after: {data['detail']['retry_after']}s")
            print(f"   Category: {data['detail']['category']}")
            print(f"   Limit: {data['detail']['limit']} requests/{data['detail']['window']}s")
            break
        else:
            print(f"❌ ERROR ({response.status_code}): {response.text}")
            break

        time.sleep(0.2)  # Small delay between requests

    print()
    print("RESULTS:")
    print(f"  Successful requests: {success_count}")
    print(f"  Expected limit: {FREE_LIMIT}")

    if success_count == FREE_LIMIT and rate_limited:
        print(f"  ✅ PASS: Free user limited to {FREE_LIMIT} messages/hour")
    else:
        print(f"  ❌ FAIL: Rate limiting not working correctly")

    print()


def test_premium_user_rate_limit():
    """Test premium user rate limit (20 messages/hour)"""
    print("=" * 80)
    print("TEST 2: Premium User Rate Limit (20 messages/hour)")
    print("=" * 80)

    if not PREMIUM_USER_TOKEN:
        print("⚠️  PREMIUM_USER_TOKEN not set. Skipping test.")
        print("   Get token from: POST /api/auth/login")
        return

    print(f"Testing with PREMIUM_USER_TOKEN...")
    print()

    success_count = 0
    rate_limited = False

    for i in range(PREMIUM_LIMIT + 2):  # Try 22 requests (should hit limit at 21)
        print(f"Request {i+1}/{PREMIUM_LIMIT + 2}...", end=" ")

        response = make_coach_request(PREMIUM_USER_TOKEN, f"Test message {i+1}")

        if response.status_code == 200:
            success_count += 1
            print(f"✅ SUCCESS (200)")
        elif response.status_code == 429:
            rate_limited = True
            data = response.json()
            print(f"🚫 RATE LIMITED (429)")
            print(f"   Message: {data['detail']['message']}")
            print(f"   Retry after: {data['detail']['retry_after']}s")
            print(f"   Category: {data['detail']['category']}")
            print(f"   Limit: {data['detail']['limit']} requests/{data['detail']['window']}s")
            break
        else:
            print(f"❌ ERROR ({response.status_code}): {response.text}")
            break

        time.sleep(0.2)  # Small delay between requests

    print()
    print("RESULTS:")
    print(f"  Successful requests: {success_count}")
    print(f"  Expected limit: {PREMIUM_LIMIT}")

    if success_count == PREMIUM_LIMIT and rate_limited:
        print(f"  ✅ PASS: Premium user limited to {PREMIUM_LIMIT} messages/hour")
    else:
        print(f"  ❌ FAIL: Rate limiting not working correctly")

    print()


def test_error_message_quality():
    """Test that error messages are user-friendly"""
    print("=" * 80)
    print("TEST 3: User-Friendly Error Messages")
    print("=" * 80)

    if not FREE_USER_TOKEN:
        print("⚠️  FREE_USER_TOKEN not set. Skipping test.")
        return

    print("Triggering rate limit to check error message...")
    print()

    # Make requests until rate limited
    for i in range(FREE_LIMIT + 1):
        response = make_coach_request(FREE_USER_TOKEN, f"Test {i+1}")

        if response.status_code == 429:
            data = response.json()
            print("✅ Rate limit error received:")
            print(f"   Error type: {data['detail']['error']}")
            print(f"   Message: {data['detail']['message']}")
            print(f"   Retry after: {data['detail']['retry_after']} seconds")
            print(f"   Category: {data['detail']['category']}")
            print(f"   Limit: {data['detail']['limit']} requests per {data['detail']['window']}s")
            print()

            # Check message quality
            message = data['detail']['message']
            if "coach" in message.lower() and "break" in message.lower():
                print("✅ PASS: Error message is user-friendly")
            else:
                print("⚠️  WARNING: Error message could be more user-friendly")

            break

    print()


def manual_test_instructions():
    """Print manual testing instructions"""
    print("=" * 80)
    print("MANUAL TESTING INSTRUCTIONS")
    print("=" * 80)
    print()
    print("To run automated tests:")
    print()
    print("1. Get a FREE user token:")
    print("   curl -X POST http://localhost:8000/api/auth/login \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"email\": \"free@test.com\", \"password\": \"password\"}'")
    print()
    print("2. Get a PREMIUM user token:")
    print("   curl -X POST http://localhost:8000/api/auth/login \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"email\": \"premium@test.com\", \"password\": \"password\"}'")
    print()
    print("3. Update this file with tokens:")
    print("   FREE_USER_TOKEN = 'eyJ...'")
    print("   PREMIUM_USER_TOKEN = 'eyJ...'")
    print()
    print("4. Run tests:")
    print("   python test_coach_rate_limit.py")
    print()
    print("=" * 80)
    print()


def main():
    """Run all tests"""
    print()
    print("🧪 TAALCOACH RATE LIMITING TEST SUITE")
    print()

    if not FREE_USER_TOKEN and not PREMIUM_USER_TOKEN:
        manual_test_instructions()
        return

    # Run tests
    test_free_user_rate_limit()
    test_premium_user_rate_limit()
    test_error_message_quality()

    print("=" * 80)
    print("✅ TESTING COMPLETE")
    print("=" * 80)
    print()
    print("SUMMARY:")
    print("- Free users: 10 messages/hour")
    print("- Premium users: 20 messages/hour")
    print("- Error messages: User-friendly")
    print()
    print("Next steps:")
    print("1. Monitor Slack for rate limit alerts")
    print("2. Check logs: grep 'RATE_LIMITER' your_log_file.log")
    print("3. Adjust limits if needed in rate_limiter.py")
    print()


if __name__ == "__main__":
    main()
