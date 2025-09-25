#!/usr/bin/env python3

"""
Test script to verify early exit session saving functionality.

This script tests the critical fix for early exit sessions where users click
"Your Dashboard" menu item and confirm to leave the session modal.
"""

import asyncio
import json
import sys
from datetime import datetime
import requests
from typing import Dict, Any

# Test configuration
API_BASE_URL = "https://mytacoai.com"
TEST_USER_EMAIL = "alipala.ist@gmail.com"

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_step(step: str):
    """Print a formatted step"""
    print(f"\n📋 {step}")
    print("-" * 50)

def print_result(success: bool, message: str):
    """Print a formatted result"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def get_auth_token() -> str:
    """Get authentication token for the test user"""
    print_step("Getting authentication token")
    
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": "testpassword123"  # Use actual test password
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print_result(True, f"Authentication successful")
            return token
        else:
            print_result(False, f"Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print_result(False, f"Authentication error: {e}")
        return None

def test_session_save_endpoint(token: str) -> bool:
    """Test the session save endpoint directly"""
    print_step("Testing session save endpoint")
    
    # Create mock session data
    session_data = {
        "language": "dutch",
        "level": "beginner",
        "topic": "daily_life",
        "messages": [
            {
                "role": "assistant",
                "content": "Hallo! Hoe gaat het met je?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user", 
                "content": "Hallo, het gaat goed met mij!",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "duration_minutes": 2.5,
        "learning_plan_id": None,
        "conversation_type": "practice",
        "exit_type": "modal_confirmation"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/progress/save-conversation",
            json=session_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Session saved successfully: {result}")
            return True
        else:
            print_result(False, f"Session save failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Session save error: {e}")
        return False

def test_speaking_time_tracking(token: str) -> bool:
    """Test the speaking time tracking endpoint"""
    print_step("Testing speaking time tracking")
    
    # Create mock speaking time data
    speaking_data = {
        "user_id": "688921c268819565ef1ce3dc",  # Test user ID
        "session_id": f"688921c268819565ef1ce3dc_{int(datetime.now().timestamp())}",
        "speaking_minutes": 2.5,
        "session_completed": False,
        "exit_type": "modal_confirmation"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/stripe/track-speaking-time",
            json=speaking_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Speaking time tracked successfully: {result}")
            return True
        else:
            print_result(False, f"Speaking time tracking failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Speaking time tracking error: {e}")
        return False

def test_subscription_status(token: str) -> Dict[str, Any]:
    """Test subscription status endpoint to verify current state"""
    print_step("Checking subscription status")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/stripe/subscription-status",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Subscription status retrieved")
            
            # Print key metrics
            if 'limits' in result:
                limits = result['limits']
                print(f"   📊 Minutes used: {limits.get('minutes_used', 0)}")
                print(f"   📊 Minutes limit: {limits.get('minutes_limit', 0)}")
                print(f"   📊 Sessions used: {limits.get('sessions_used', 0)}")
                print(f"   📊 Sessions limit: {limits.get('sessions_limit', 0)}")
                print(f"   📊 Plan: {result.get('plan', 'unknown')}")
            
            return result
        else:
            print_result(False, f"Subscription status failed: {response.status_code}")
            return {}
            
    except Exception as e:
        print_result(False, f"Subscription status error: {e}")
        return {}

def simulate_early_exit_scenario(token: str) -> bool:
    """Simulate the complete early exit scenario"""
    print_step("Simulating complete early exit scenario")
    
    print("🎯 Scenario: User starts session, has conversation, clicks 'Your Dashboard', confirms leave")
    
    # Step 1: Save conversation (simulating modal confirmation)
    session_success = test_session_save_endpoint(token)
    
    # Step 2: Track speaking time (simulating subscription tracking)
    speaking_success = test_speaking_time_tracking(token)
    
    # Step 3: Verify both operations succeeded
    if session_success and speaking_success:
        print_result(True, "Complete early exit scenario successful")
        return True
    else:
        print_result(False, "Early exit scenario failed - some operations did not complete")
        return False

def main():
    """Main test function"""
    print_header("EARLY EXIT SESSION SAVING - VERIFICATION TEST")
    
    print("🎯 Testing the critical fix for early exit sessions")
    print("📋 This verifies that sessions are saved when users:")
    print("   1. Click 'Your Dashboard' menu item")
    print("   2. Confirm 'End Session' in the modal")
    print("   3. Session data is properly saved before navigation")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print_result(False, "Cannot proceed without authentication token")
        sys.exit(1)
    
    # Check initial subscription status
    initial_status = test_subscription_status(token)
    initial_minutes = initial_status.get('limits', {}).get('minutes_used', 0)
    
    # Run the complete early exit scenario test
    scenario_success = simulate_early_exit_scenario(token)
    
    # Check final subscription status
    print_step("Verifying changes after early exit simulation")
    final_status = test_subscription_status(token)
    final_minutes = final_status.get('limits', {}).get('minutes_used', 0)
    
    # Verify that minutes were properly tracked
    minutes_increased = final_minutes > initial_minutes
    if minutes_increased:
        print_result(True, f"Minutes properly tracked: {initial_minutes} → {final_minutes}")
    else:
        print_result(False, f"Minutes not tracked: {initial_minutes} → {final_minutes}")
    
    # Final assessment
    print_header("TEST RESULTS SUMMARY")
    
    if scenario_success and minutes_increased:
        print_result(True, "🎉 EARLY EXIT SESSION SAVING FIX VERIFIED!")
        print("✅ Sessions are now properly saved when users leave via modal")
        print("✅ Speaking time is correctly tracked for subscription limits")
        print("✅ Users will see their conversation data in history")
        print("✅ Minutes are properly deducted from their subscription")
        return True
    else:
        print_result(False, "❌ EARLY EXIT SESSION SAVING STILL HAS ISSUES")
        print("❌ Some operations failed - further investigation needed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
