"""
Test Enhanced TaalCoach with App Features Knowledge
====================================================
Validates that coach can answer questions about:
- App features (challenges, learning plans, Speaking DNA, etc.)
- External recommendations (movies, music, podcasts, books)
- Level-appropriate content
- Subscription-aware responses

Usage:
    python test_coach_enhanced.py
"""

import asyncio
import sys
from services.coach_service_optimized import coach_service_optimized as coach_service

# Test user ID (real user from MongoDB)
TEST_USER_ID = "69937ade7d780583ed65ea31"  # Real user for testing

# Test scenarios
TEST_SCENARIOS = [
    # App features questions
    {
        "name": "Challenge types inquiry",
        "message": "What types of challenges are available?",
        "expected_keywords": ["error spotting", "swipe fix", "micro quiz", "brain tickler", "story builder"],
        "intent": "app_help"
    },
    {
        "name": "Speaking DNA inquiry (premium feature)",
        "message": "What is Speaking DNA?",
        "expected_keywords": ["confidence", "fluency", "vocabulary", "accuracy", "premium"],
        "intent": "app_help"
    },
    {
        "name": "Learning plan inquiry",
        "message": "How do learning plans work?",
        "expected_keywords": ["session", "curriculum", "goal", "plan"],
        "intent": "app_help"
    },
    {
        "name": "Heart system inquiry (free users)",
        "message": "What are hearts and how do they work?",
        "expected_keywords": ["heart", "refill", "free", "wrong answer"],
        "intent": "app_help"
    },
    {
        "name": "Subscription benefits inquiry",
        "message": "What's the difference between free and premium?",
        "expected_keywords": ["unlimited", "speaking dna", "heart", "premium"],
        "intent": "app_help"
    },

    # External recommendations (level-appropriate)
    {
        "name": "Movie recommendation for B1 Spanish learner",
        "message": "Can you recommend a Spanish movie for my B1 level?",
        "expected_keywords": ["netflix", "spanish", "b1"],
        "intent": "general",
        "expected_specific": ["Money Heist", "Narcos", "La Casa de Papel"]
    },
    {
        "name": "Podcast recommendation for French learner",
        "message": "What podcasts should I listen to for learning French?",
        "expected_keywords": ["podcast", "french"],
        "intent": "general",
        "expected_specific": ["Coffee Break", "News in Slow", "Easy French"]
    },
    {
        "name": "Music recommendation for German",
        "message": "Suggest some German music for language learning",
        "expected_keywords": ["german", "music"],
        "intent": "general",
        "expected_specific": ["Rammstein", "Nena", "Mark Forster"]
    },
    {
        "name": "Book recommendation for A2 level",
        "message": "What books should I read at A2 level?",
        "expected_keywords": ["book", "a2", "read"],
        "intent": "general",
        "expected_specific": ["children", "graded reader", "simple"]
    },

    # Progress and motivation
    {
        "name": "Progress inquiry",
        "message": "How am I doing with my learning?",
        "expected_keywords": ["streak", "session", "progress"],
        "intent": "progress"
    },
    {
        "name": "DNA strand inquiry",
        "message": "Tell me about my Speaking DNA",
        "expected_keywords": ["confidence", "fluency", "strand"],
        "intent": "dna"
    },
    {
        "name": "Challenge performance inquiry",
        "message": "How's my challenge accuracy?",
        "expected_keywords": ["accuracy", "challenge", "correct"],
        "intent": "challenges"
    },
]


async def test_coach_response(scenario: dict):
    """Test a single scenario"""
    print(f"\n{'='*80}")
    print(f"TEST: {scenario['name']}")
    print(f"{'='*80}")
    print(f"Message: \"{scenario['message']}\"")
    print(f"Expected Intent: {scenario['intent']}")

    try:
        # Call coach service
        response = await coach_service.chat(
            user_id=TEST_USER_ID,
            language="en",  # English interface
            user_message=scenario['message'],
            conversation_history=[]
        )

        # Parse response
        ai_message = response['raw_response']
        messages = response['messages']

        print(f"\n✅ COACH RESPONSE:")
        print(f"   {ai_message}")

        # Check for expected keywords
        message_lower = ai_message.lower()
        found_keywords = []
        missing_keywords = []

        for keyword in scenario.get('expected_keywords', []):
            if keyword.lower() in message_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        # Check for specific recommendations
        found_specific = []
        if 'expected_specific' in scenario:
            for specific in scenario['expected_specific']:
                if specific.lower() in message_lower:
                    found_specific.append(specific)

        # Print analysis
        print(f"\n📊 ANALYSIS:")
        if found_keywords:
            print(f"   ✅ Found keywords: {', '.join(found_keywords)}")
        if missing_keywords:
            print(f"   ⚠️  Missing keywords: {', '.join(missing_keywords)}")
        if found_specific:
            print(f"   🎯 Specific recommendations: {', '.join(found_specific)}")

        # Evaluate response
        keyword_score = len(found_keywords) / len(scenario['expected_keywords']) if scenario.get('expected_keywords') else 1.0

        if keyword_score >= 0.5:  # At least 50% keywords found
            print(f"   ✅ PASS (Score: {keyword_score:.1%})")
            return True
        else:
            print(f"   ❌ FAIL (Score: {keyword_score:.1%})")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("🧪 ENHANCED TAALCOACH TEST SUITE")
    print("="*80)
    print(f"Testing with user: {TEST_USER_ID}")
    print(f"Total scenarios: {len(TEST_SCENARIOS)}")

    # Check if user ID is placeholder
    if TEST_USER_ID == "65c9e9f4b8e8f2a1c0000001":
        print("\n⚠️  WARNING: Using placeholder TEST_USER_ID")
        print("   Please replace with actual user ID from MongoDB")
        print("   Example: TEST_USER_ID = \"your_actual_user_id_here\"")
        print("\n   Continuing with placeholder for demo purposes...")

    results = []

    # Run each scenario
    for scenario in TEST_SCENARIOS:
        passed = await test_coach_response(scenario)
        results.append(passed)

        # Small delay between tests
        await asyncio.sleep(0.5)

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed_count = sum(results)
    total_count = len(results)
    pass_rate = (passed_count / total_count) * 100 if total_count > 0 else 0

    print(f"Passed: {passed_count}/{total_count} ({pass_rate:.1f}%)")
    print(f"Failed: {total_count - passed_count}/{total_count}")

    # Categorize results
    print(f"\n📋 DETAILED RESULTS:")
    for i, (scenario, passed) in enumerate(zip(TEST_SCENARIOS, results), 1):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {i}. {status} - {scenario['name']}")

    # Recommendations
    print(f"\n💡 OBSERVATIONS:")
    if pass_rate >= 80:
        print("   ✅ Excellent! Coach has comprehensive app knowledge")
    elif pass_rate >= 60:
        print("   ⚠️  Good, but some gaps in knowledge detected")
    else:
        print("   ❌ Needs improvement - missing key app knowledge")

    if passed_count < total_count:
        print(f"\n   Review failed tests above to identify knowledge gaps")

    print("\n" + "="*80)
    print("✅ TESTING COMPLETE")
    print("="*80)
    print()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7+ required")
        sys.exit(1)

    # Run tests
    asyncio.run(main())
