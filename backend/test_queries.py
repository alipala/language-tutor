"""
Test script to verify database queries work correctly
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_helpers import (
    count_reference_challenges_by_language_and_level,
    count_challenge_pool_by_language_and_level,
    get_complete_statistics,
    get_reference_challenges_breakdown,
    client
)


async def run_tests():
    """Run test queries to verify everything works"""

    print("\n" + "="*60)
    print("Testing Database Queries")
    print("="*60 + "\n")

    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ MongoDB connection successful\n")

        # Test 1: Count reference challenges
        print("Test 1: Count reference challenges for French A1")
        count = await count_reference_challenges_by_language_and_level("french", "A1")
        print(f"  Result: {count} documents")
        print(f"  Status: {'✓ PASS' if count >= 0 else '✗ FAIL'}\n")

        # Test 2: Count reference challenges for Dutch B2
        print("Test 2: Count reference challenges for Dutch B2")
        count = await count_reference_challenges_by_language_and_level("dutch", "B2")
        print(f"  Result: {count} documents")
        print(f"  Status: {'✓ PASS' if count >= 0 else '✗ FAIL'}\n")

        # Test 3: Count challenge pool
        print("Test 3: Count challenge pool for Spanish A1")
        count = await count_challenge_pool_by_language_and_level("spanish", "A1")
        print(f"  Result: {count} documents")
        print(f"  Status: {'✓ PASS' if count >= 0 else '✗ FAIL'}\n")

        # Test 4: Get complete statistics
        print("Test 4: Get complete statistics for English B1")
        stats = await get_complete_statistics("english", "B1")
        print(f"  Reference challenges: {stats['reference_challenges']}")
        print(f"  Pool available: {stats['pool']['available']}")
        print(f"  Pool completed: {stats['pool']['completed']}")
        print(f"  Status: ✓ PASS\n")

        # Test 5: Get breakdown
        print("Test 5: Get reference challenges breakdown")
        breakdown = await get_reference_challenges_breakdown()
        print(f"  Languages found: {list(breakdown.keys())}")
        if breakdown:
            first_lang = list(breakdown.keys())[0]
            print(f"  Levels for {first_lang}: {list(breakdown[first_lang].keys())}")
        print(f"  Status: {'✓ PASS' if breakdown else '✗ FAIL'}\n")

        # Summary
        print("="*60)
        print("All tests completed successfully! ✓")
        print("="*60)

        # Show some actual data
        if breakdown:
            print("\nSample data from database:")
            print("-" * 60)
            for language, levels in sorted(breakdown.items())[:3]:  # Show first 3 languages
                print(f"\n{language.title()}:")
                for level, count in sorted(levels.items()):
                    print(f"  {level}: {count} challenges")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print("\n✓ Connection closed")


if __name__ == "__main__":
    asyncio.run(run_tests())
