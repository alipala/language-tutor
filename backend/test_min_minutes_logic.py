#!/usr/bin/env python3
"""
Test script to verify the 3-minute minimum requirement logic
"""

def can_start_session_logic(minutes_remaining: float, minutes_limit: int, minimum_minutes_required: int = 3) -> tuple[bool, str]:
    """
    Replicate the can_start_session logic to test it
    """
    if minutes_limit == -1:
        # Unlimited plan
        return True, f"✨ Unlimited speaking time remaining"
    elif minutes_remaining < minimum_minutes_required:
        # Not enough minutes to start a session
        if minutes_remaining <= 0:
            return False, f"🚫 No speaking time remaining. Upgrade to continue learning!"
        else:
            return False, f"🚫 You need at least {minimum_minutes_required} minutes to start a session. You have {minutes_remaining:.0f} minutes left. Upgrade to continue learning!"
    else:
        return True, f"You have {minutes_remaining:.0f} minutes remaining this period"


# Test cases
test_cases = [
    # (minutes_remaining, minutes_limit, expected_can_start, description)
    (15, 15, True, "Full 15 minutes available (free tier)"),
    (10, 15, True, "10 minutes remaining (enough)"),
    (5, 15, True, "5 minutes remaining (enough)"),
    (3, 15, True, "Exactly 3 minutes remaining (minimum)"),
    (2.5, 15, False, "2.5 minutes remaining (not enough)"),
    (2, 15, False, "2 minutes remaining (not enough)"),
    (1, 15, False, "1 minute remaining (not enough)"),
    (0, 15, False, "0 minutes remaining (exhausted)"),
    (-1, 15, False, "Negative minutes (over quota)"),
    (-134, 15, False, "Heavily negative minutes (-134)"),
    (100, -1, True, "Unlimited plan"),
]

print("Testing 3-minute minimum requirement logic:\n")
print("=" * 80)

for minutes_remaining, minutes_limit, expected_can_start, description in test_cases:
    can_start, message = can_start_session_logic(minutes_remaining, minutes_limit)
    status = "✅ PASS" if can_start == expected_can_start else "❌ FAIL"

    print(f"{status} | {description}")
    print(f"   Minutes: {minutes_remaining}/{minutes_limit}")
    print(f"   Can start: {can_start}")
    print(f"   Message: {message}")
    print("-" * 80)

print("\n✅ All test cases executed!")
