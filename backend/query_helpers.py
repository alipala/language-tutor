"""
Database Query Helpers for Reference Challenges and Challenge Pool
Provides reusable query functions to count and analyze documents by language and CEFR level
"""

import asyncio
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
database = client[DATABASE_NAME]


# ==================== REFERENCE CHALLENGES QUERIES ====================

async def count_reference_challenges_by_language_and_level(
    language: str,
    cefr_level: str
) -> int:
    """
    Count reference challenges for a specific language and CEFR level

    Args:
        language: Language name (e.g., "french", "dutch", "spanish", "english")
        cefr_level: CEFR level (e.g., "A1", "A2", "B1", "B2", "C1", "C2")

    Returns:
        int: Number of matching documents

    Example:
        count = await count_reference_challenges_by_language_and_level("french", "A1")
        print(f"French A1 challenges: {count}")
    """
    collection = database.reference_challenges
    query = {
        "language": language.lower(),
        "cefr_level": cefr_level.upper()
    }
    count = await collection.count_documents(query)
    return count


async def count_reference_challenges_by_language(language: str) -> int:
    """
    Count all reference challenges for a specific language (all levels)

    Args:
        language: Language name (e.g., "french", "dutch", "spanish")

    Returns:
        int: Total number of challenges for this language

    Example:
        count = await count_reference_challenges_by_language("french")
        print(f"Total French challenges: {count}")
    """
    collection = database.reference_challenges
    query = {"language": language.lower()}
    count = await collection.count_documents(query)
    return count


async def count_reference_challenges_by_level(cefr_level: str) -> int:
    """
    Count all reference challenges for a specific CEFR level (all languages)

    Args:
        cefr_level: CEFR level (e.g., "A1", "B1", "C2")

    Returns:
        int: Total number of challenges for this level

    Example:
        count = await count_reference_challenges_by_level("B1")
        print(f"Total B1 challenges across all languages: {count}")
    """
    collection = database.reference_challenges
    query = {"cefr_level": cefr_level.upper()}
    count = await collection.count_documents(query)
    return count


async def get_reference_challenges_breakdown() -> Dict:
    """
    Get a complete breakdown of reference challenges by language and level

    Returns:
        Dict: Nested dictionary with counts by language and level

    Example:
        breakdown = await get_reference_challenges_breakdown()
        # Result: {"french": {"A1": 50, "A2": 45, "B1": 40}, "dutch": {...}}
    """
    collection = database.reference_challenges

    pipeline = [
        {
            "$group": {
                "_id": {
                    "language": "$language",
                    "level": "$cefr_level"
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id.language": 1,
                "_id.level": 1
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(None)

    # Convert to nested dictionary
    breakdown = {}
    for result in results:
        language = result["_id"]["language"]
        level = result["_id"]["level"]
        count = result["count"]

        if language not in breakdown:
            breakdown[language] = {}
        breakdown[language][level] = count

    return breakdown


async def get_reference_challenges_by_type(
    language: str,
    cefr_level: str,
    challenge_type: Optional[str] = None
) -> int:
    """
    Count reference challenges by language, level, and optionally by type

    Args:
        language: Language name
        cefr_level: CEFR level
        challenge_type: Optional challenge type (e.g., "error_spotting", "fill_blank", "multiple_choice")

    Returns:
        int: Count of matching challenges

    Example:
        count = await get_reference_challenges_by_type("french", "A1", "error_spotting")
        print(f"French A1 error spotting challenges: {count}")
    """
    collection = database.reference_challenges
    query = {
        "language": language.lower(),
        "cefr_level": cefr_level.upper()
    }

    if challenge_type:
        query["challenge_type"] = challenge_type

    count = await collection.count_documents(query)
    return count


# ==================== CHALLENGE POOL QUERIES ====================

async def count_challenge_pool_by_language_and_level(
    language: str,
    cefr_level: str,
    user_id: Optional[str] = None,
    status: Optional[str] = None
) -> int:
    """
    Count challenge pool items for a specific language and CEFR level

    Args:
        language: Language name (e.g., "french", "dutch", "spanish")
        cefr_level: CEFR level (e.g., "A1", "B1")
        user_id: Optional user ID to filter by specific user
        status: Optional status filter ("available", "completed", "expired")

    Returns:
        int: Number of matching documents

    Example:
        count = await count_challenge_pool_by_language_and_level("french", "A1")
        count_user = await count_challenge_pool_by_language_and_level(
            "french", "A1", user_id="123", status="available"
        )
    """
    collection = database.challenge_pool
    query = {
        "language": language.lower(),
        "cefr_level": cefr_level.upper()
    }

    if user_id:
        query["user_id"] = user_id

    if status:
        query["status"] = status

    count = await collection.count_documents(query)
    return count


async def get_challenge_pool_breakdown(user_id: Optional[str] = None) -> Dict:
    """
    Get a complete breakdown of challenge pool by language, level, and status

    Args:
        user_id: Optional user ID to filter by specific user

    Returns:
        Dict: Nested dictionary with counts

    Example:
        breakdown = await get_challenge_pool_breakdown()
        # Result: {"french": {"A1": {"available": 10, "completed": 5}}}
    """
    collection = database.challenge_pool

    match_stage = {}
    if user_id:
        match_stage["user_id"] = user_id

    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": {
                    "language": "$language",
                    "level": "$cefr_level",
                    "status": "$status"
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id.language": 1,
                "_id.level": 1,
                "_id.status": 1
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(None)

    # Convert to nested dictionary
    breakdown = {}
    for result in results:
        language = result["_id"]["language"]
        level = result["_id"]["level"]
        status = result["_id"]["status"]
        count = result["count"]

        if language not in breakdown:
            breakdown[language] = {}
        if level not in breakdown[language]:
            breakdown[language][level] = {}
        breakdown[language][level][status] = count

    return breakdown


# ==================== COMBINED STATISTICS ====================

async def get_complete_statistics(language: str, cefr_level: str) -> Dict:
    """
    Get complete statistics for a language/level combination across both collections

    Args:
        language: Language name
        cefr_level: CEFR level

    Returns:
        Dict: Complete statistics including reference and pool counts

    Example:
        stats = await get_complete_statistics("french", "A1")
        print(f"Reference: {stats['reference_challenges']}")
        print(f"Pool Available: {stats['pool']['available']}")
    """
    ref_count = await count_reference_challenges_by_language_and_level(language, cefr_level)
    pool_available = await count_challenge_pool_by_language_and_level(
        language, cefr_level, status="available"
    )
    pool_completed = await count_challenge_pool_by_language_and_level(
        language, cefr_level, status="completed"
    )
    pool_expired = await count_challenge_pool_by_language_and_level(
        language, cefr_level, status="expired"
    )

    return {
        "language": language,
        "cefr_level": cefr_level,
        "reference_challenges": ref_count,
        "pool": {
            "available": pool_available,
            "completed": pool_completed,
            "expired": pool_expired,
            "total": pool_available + pool_completed + pool_expired
        }
    }


# ==================== INTERACTIVE CLI ====================

async def interactive_query():
    """
    Interactive command-line interface for running queries
    """
    print("\n" + "="*60)
    print("Language Tutor Database Query Helper")
    print("="*60)

    print("\nSelect a query type:")
    print("1. Count reference challenges by language and level")
    print("2. Count challenge pool by language and level")
    print("3. Get complete statistics for language/level")
    print("4. Get full breakdown of reference challenges")
    print("5. Get full breakdown of challenge pool")
    print("6. Exit")

    choice = input("\nEnter choice (1-6): ").strip()

    if choice == "1":
        language = input("Enter language (e.g., french, dutch, spanish): ").strip()
        level = input("Enter CEFR level (e.g., A1, B1, B2): ").strip()
        count = await count_reference_challenges_by_language_and_level(language, level)
        print(f"\n✓ {language.title()} {level.upper()} reference challenges: {count}")

    elif choice == "2":
        language = input("Enter language: ").strip()
        level = input("Enter CEFR level: ").strip()
        status = input("Enter status (available/completed/expired) or press Enter for all: ").strip() or None
        count = await count_challenge_pool_by_language_and_level(language, level, status=status)
        status_str = f" ({status})" if status else ""
        print(f"\n✓ {language.title()} {level.upper()} challenge pool{status_str}: {count}")

    elif choice == "3":
        language = input("Enter language: ").strip()
        level = input("Enter CEFR level: ").strip()
        stats = await get_complete_statistics(language, level)
        print(f"\n✓ Complete statistics for {language.title()} {level.upper()}:")
        print(f"  Reference challenges: {stats['reference_challenges']}")
        print(f"  Challenge Pool:")
        print(f"    - Available: {stats['pool']['available']}")
        print(f"    - Completed: {stats['pool']['completed']}")
        print(f"    - Expired: {stats['pool']['expired']}")
        print(f"    - Total: {stats['pool']['total']}")

    elif choice == "4":
        breakdown = await get_reference_challenges_breakdown()
        print("\n✓ Reference Challenges Breakdown:")
        for language, levels in sorted(breakdown.items()):
            print(f"\n  {language.title()}:")
            for level, count in sorted(levels.items()):
                print(f"    {level}: {count}")

    elif choice == "5":
        breakdown = await get_challenge_pool_breakdown()
        print("\n✓ Challenge Pool Breakdown:")
        for language, levels in sorted(breakdown.items()):
            print(f"\n  {language.title()}:")
            for level, statuses in sorted(levels.items()):
                print(f"    {level}:")
                for status, count in sorted(statuses.items()):
                    print(f"      {status}: {count}")

    elif choice == "6":
        print("\nGoodbye!")
        return False

    else:
        print("\n✗ Invalid choice")

    print("\n" + "="*60)
    return True


async def main():
    """Main function to run interactive queries"""
    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")

        # Run interactive queries
        while True:
            should_continue = await interactive_query()
            if not should_continue:
                break

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
