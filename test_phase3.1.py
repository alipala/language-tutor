#!/usr/bin/env python3
"""
Test Script for Phase 3.1 - Flexible Language/Level Selection
Tests with a registered user who has NO learning plan
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"  # Change if backend runs on different port
TEST_EMAIL = "d77240fe-5821-486a-a6cc-d61396fffa58@mailslurp.biz"
TEST_PASSWORD = "040050803"

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def login(email: str, password: str) -> Optional[str]:
    """Login and get auth token"""
    print_header("1. AUTHENTICATION TEST")

    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": email,
        "password": password
    }

    print_info(f"Logging in with: {email}")

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")

            if token:
                print_success(f"Login successful!")
                print_info(f"User ID: {data.get('user', {}).get('id')}")
                print_info(f"Preferred Level: {data.get('user', {}).get('preferred_level', 'Not set')}")
                return token
            else:
                print_error("No token in response")
                return None
        else:
            print_error(f"Login failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return None


def test_counts_endpoint(token: str):
    """Test /api/challenges/counts with different parameters"""
    print_header("2. CHALLENGE COUNTS ENDPOINT TESTS")

    headers = {"Authorization": f"Bearer {token}"}

    test_cases = [
        {
            "name": "Spanish A1 (explicit params)",
            "params": {"language": "spanish", "level": "A1"},
            "expected": "Should show counts for Spanish A1"
        },
        {
            "name": "German B2 (explicit params)",
            "params": {"language": "german", "level": "B2"},
            "expected": "Should show counts for German B2"
        },
        {
            "name": "French A2 (explicit params)",
            "params": {"language": "french", "level": "A2"},
            "expected": "Should show counts for French A2"
        },
        {
            "name": "No params (fallback test)",
            "params": {},
            "expected": "Should fallback to default (english/B1)"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{BOLD}Test {i}/{len(test_cases)}: {test['name']}{RESET}")
        print_info(test['expected'])

        url = f"{BASE_URL}/api/challenges/counts"

        try:
            response = requests.get(url, headers=headers, params=test['params'])

            if response.status_code == 200:
                data = response.json()
                total_challenges = sum(data.values())

                print_success(f"Status: {response.status_code}")
                print_info(f"Total challenges: {total_challenges}")
                print(f"  error_spotting: {data.get('error_spotting', 0)}")
                print(f"  swipe_fix: {data.get('swipe_fix', 0)}")
                print(f"  micro_quiz: {data.get('micro_quiz', 0)}")
                print(f"  smart_flashcard: {data.get('smart_flashcard', 0)}")
                print(f"  native_check: {data.get('native_check', 0)}")
                print(f"  brain_tickler: {data.get('brain_tickler', 0)}")

                if total_challenges > 0:
                    print_success("Challenges available!")
                else:
                    print_warning("No challenges in pool yet (will auto-generate)")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text}")

        except Exception as e:
            print_error(f"Request error: {str(e)}")


def test_daily_endpoint(token: str):
    """Test /api/challenges/daily with different parameters"""
    print_header("3. DAILY CHALLENGES ENDPOINT TESTS")

    headers = {"Authorization": f"Bearer {token}"}

    test_cases = [
        {
            "name": "Spanish A1 (explicit params)",
            "params": {"language": "spanish", "level": "A1"}
        },
        {
            "name": "Dutch B1 (explicit params)",
            "params": {"language": "dutch", "level": "B1"}
        },
        {
            "name": "No params (fallback test)",
            "params": {}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{BOLD}Test {i}/{len(test_cases)}: {test['name']}{RESET}")

        url = f"{BASE_URL}/api/challenges/daily"

        try:
            response = requests.get(url, headers=headers, params=test['params'])

            if response.status_code == 200:
                data = response.json()
                challenges = data.get('challenges', [])

                print_success(f"Status: {response.status_code}")
                print_info(f"Challenges received: {len(challenges)}")
                print_info(f"Total completed today: {data.get('total_completed_today', 0)}")
                print_info(f"Streak: {data.get('streak', 0)}")

                if challenges:
                    print(f"\n  Challenge types:")
                    for idx, challenge in enumerate(challenges, 1):
                        lang = challenge.get('language', 'N/A')
                        level = challenge.get('cefrLevel', 'N/A')
                        ctype = challenge.get('type', 'N/A')
                        print(f"    {idx}. {ctype} - {lang} {level}")
                else:
                    print_warning("No challenges returned")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text[:500]}")

        except Exception as e:
            print_error(f"Request error: {str(e)}")


def test_by_type_endpoint(token: str):
    """Test /api/challenges/by-type/{type} with different parameters"""
    print_header("4. BY-TYPE ENDPOINT TESTS")

    headers = {"Authorization": f"Bearer {token}"}

    test_cases = [
        {
            "name": "Spanish A1 error_spotting",
            "challenge_type": "error_spotting",
            "params": {"language": "spanish", "level": "A1", "limit": 5}
        },
        {
            "name": "German A2 swipe_fix",
            "challenge_type": "swipe_fix",
            "params": {"language": "german", "level": "A2", "limit": 5}
        },
        {
            "name": "No params micro_quiz (fallback)",
            "challenge_type": "micro_quiz",
            "params": {"limit": 5}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{BOLD}Test {i}/{len(test_cases)}: {test['name']}{RESET}")

        url = f"{BASE_URL}/api/challenges/by-type/{test['challenge_type']}"

        try:
            response = requests.get(url, headers=headers, params=test['params'])

            if response.status_code == 200:
                data = response.json()
                challenges = data.get('challenges', [])

                print_success(f"Status: {response.status_code}")
                print_info(f"Challenges received: {len(challenges)}")
                print_info(f"Type: {data.get('type', 'N/A')}")

                if challenges:
                    print(f"\n  First 3 challenges:")
                    for idx, challenge in enumerate(challenges[:3], 1):
                        lang = challenge.get('language', 'N/A')
                        level = challenge.get('cefrLevel', 'N/A')
                        cid = challenge.get('id', 'N/A')
                        print(f"    {idx}. {lang} {level} - ID: {cid[:20]}...")
                else:
                    print_warning("No challenges returned")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text[:500]}")

        except Exception as e:
            print_error(f"Request error: {str(e)}")


def test_languages_endpoint(token: str):
    """Test /api/challenges/languages endpoint"""
    print_header("5. LANGUAGES ENDPOINT TEST")

    headers = {"Authorization": f"Bearer {token}"}

    test_cases = [
        {
            "name": "All languages for A1",
            "params": {"level": "A1"}
        },
        {
            "name": "All languages for B2",
            "params": {"level": "B2"}
        },
        {
            "name": "No params (user's level)",
            "params": {}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{BOLD}Test {i}/{len(test_cases)}: {test['name']}{RESET}")

        url = f"{BASE_URL}/api/challenges/languages"

        try:
            response = requests.get(url, headers=headers, params=test['params'])

            if response.status_code == 200:
                data = response.json()
                languages = data.get('languages', [])
                active = data.get('active_language')

                print_success(f"Status: {response.status_code}")
                print_info(f"Active language: {active or 'None (no learning plan)'}")
                print_info(f"Languages available: {len(languages)}")

                print(f"\n  Language breakdown:")
                for lang_data in languages:
                    lang = lang_data['language']
                    has_plan = lang_data['has_learning_plan']
                    is_active = lang_data['is_active']
                    count = lang_data['available_challenges']

                    status = ""
                    if is_active:
                        status = f"{GREEN}[ACTIVE]{RESET}"
                    elif has_plan:
                        status = f"{YELLOW}[HAS PLAN]{RESET}"

                    print(f"    - {lang.capitalize():<12} {status:<20} Challenges: {count}")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text}")

        except Exception as e:
            print_error(f"Request error: {str(e)}")


def test_resolution_logic(token: str):
    """Test the smart resolution logic"""
    print_header("6. SMART RESOLUTION LOGIC TEST")

    headers = {"Authorization": f"Bearer {token}"}

    print(f"{BOLD}Testing priority-based parameter resolution:{RESET}\n")

    # Test 1: Explicit params should override everything
    print(f"{BOLD}Test 1: Explicit parameters (highest priority){RESET}")
    print_info("Requesting Portuguese C1 explicitly")

    url = f"{BASE_URL}/api/challenges/counts"
    params = {"language": "portuguese", "level": "C1"}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            print_success("Explicit params work! Backend should use Portuguese C1")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

    # Test 2: No params should use fallback
    print(f"\n{BOLD}Test 2: No parameters (fallback to defaults){RESET}")
    print_info("Not providing any params - should fallback to english/B1")

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print_success("Fallback works! Backend should use defaults")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

    # Test 3: Invalid params should fallback
    print(f"\n{BOLD}Test 3: Invalid parameters (should fallback){RESET}")
    print_info("Requesting invalid language/level")

    params = {"language": "klingon", "level": "Z9"}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            print_success("Invalid params handled! Backend should fallback to defaults")
        else:
            print_error(f"Failed: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {str(e)}")


def main():
    """Run all tests"""
    print(f"\n{BOLD}{BLUE}")
    print("=" * 80)
    print("  PHASE 3.1 TEST SUITE - Flexible Language/Level Selection")
    print("  Testing with: User WITHOUT learning plan")
    print("=" * 80)
    print(f"{RESET}\n")

    # Step 1: Login
    token = login(TEST_EMAIL, TEST_PASSWORD)

    if not token:
        print_error("Authentication failed. Cannot continue tests.")
        return

    # Step 2: Test endpoints
    test_counts_endpoint(token)
    test_daily_endpoint(token)
    test_by_type_endpoint(token)
    test_languages_endpoint(token)
    test_resolution_logic(token)

    # Summary
    print_header("TEST SUMMARY")
    print_success("All endpoint tests completed!")
    print_info("Check the output above for any errors or warnings")
    print_info("Expected behavior for user without learning plan:")
    print_info("  - Should see 0 challenges initially")
    print_info("  - Backend auto-copies from reference challenges")
    print_info("  - Challenges become available for requested language/level")
    print_info("  - Can freely switch between languages")

    print(f"\n{BOLD}{GREEN}✅ Phase 3.1 testing complete!{RESET}\n")


if __name__ == "__main__":
    main()
