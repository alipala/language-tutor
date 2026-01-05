#!/usr/bin/env python3
"""
Weekly Reference Challenge Generation with CrewAI
=================================================

Generates generic high-quality challenges for the reference_challenges collection.
These are used for freestyle practice mode (not personalized).

Runs weekly to keep a fresh pool of reference challenges for all:
- Languages: english, spanish, french, german, italian, portuguese
- Levels: A1, A2, B1, B2, C1, C2
- Types: error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler

Usage:
    python generate_reference_challenges_crew.py
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

from database import database
from challenge_generator_crew import (
    create_learning_analyzer_agent,
    create_challenge_generator_agent,
    create_quality_curator_agent,
    analyze_user_learning_data,
    generate_challenges_with_ai
)

# Load environment
load_dotenv()

# Configuration
LANGUAGES = ["english", "spanish", "french", "german", "italian", "portuguese"]
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
CHALLENGE_TYPES = [
    "error_spotting",
    "swipe_fix",
    "micro_quiz",
    "smart_flashcard",
    "native_check",
    "brain_tickler"
]

# How many reference challenges per language/level/type
CHALLENGES_PER_TYPE = 10


async def generate_reference_challenges(
    language: str,
    cefr_level: str,
    challenge_type: str,
    count: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate generic reference challenges (not user-specific)

    Args:
        language: Target language
        cefr_level: CEFR level (A1-C2)
        challenge_type: Type of challenge
        count: Number to generate

    Returns:
        List of challenge documents ready for reference_challenges collection
    """
    print(f"\n[REFERENCE] Generating {count} {challenge_type} challenges")
    print(f"[REFERENCE] Language: {language}, Level: {cefr_level}")

    # Use special "reference_user" ID for generic challenges
    challenges = await generate_challenges_with_ai(
        user_id="reference_user",
        user_level=cefr_level,
        language=language,
        challenge_type=challenge_type,
        count=count
    )

    if not challenges:
        print(f"[REFERENCE] ❌ Failed to generate challenges")
        return []

    # Convert to reference_challenges format
    reference_docs = []
    for challenge in challenges:
        ref_doc = {
            "language": language,
            "cefr_level": cefr_level,
            "challenge_type": challenge_type,
            "challenge_data": challenge,
            "created_at": datetime.utcnow(),
            "source": "crewai_reference_generator",
            "is_active": True
        }
        reference_docs.append(ref_doc)

    print(f"[REFERENCE] ✅ Generated {len(reference_docs)} reference challenges")
    return reference_docs


async def replenish_reference_challenges():
    """
    Weekly job to replenish reference_challenges collection

    For each language/level/type combination:
    - Check how many active reference challenges exist
    - Generate more if below target (50 per type)
    """
    print("\n" + "="*80)
    print("🔄 WEEKLY REFERENCE CHALLENGE GENERATION")
    print("="*80)
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)
    print()

    reference_collection = database.reference_challenges

    total_generated = 0

    for language in LANGUAGES:
        print(f"\n{'='*80}")
        print(f"🌍 Language: {language.upper()}")
        print(f"{'='*80}")

        for level in CEFR_LEVELS:
            print(f"\n📚 Level: {level}")

            for challenge_type in CHALLENGE_TYPES:
                # Count existing active reference challenges
                existing_count = await reference_collection.count_documents({
                    "language": language,
                    "cefr_level": level,
                    "challenge_type": challenge_type,
                    "is_active": True
                })

                target_count = 50  # Target pool size
                needed = target_count - existing_count

                if needed > 0:
                    print(f"  📝 {challenge_type}: {existing_count}/{target_count} (need {needed})")

                    # Generate in batches of 10
                    to_generate = min(needed, CHALLENGES_PER_TYPE)

                    new_challenges = await generate_reference_challenges(
                        language=language,
                        cefr_level=level,
                        challenge_type=challenge_type,
                        count=to_generate
                    )

                    if new_challenges:
                        # Insert to database
                        result = await reference_collection.insert_many(new_challenges)
                        inserted_count = len(result.inserted_ids)
                        total_generated += inserted_count
                        print(f"  ✅ Inserted {inserted_count} challenges")
                    else:
                        print(f"  ⚠️ Generation failed")
                else:
                    print(f"  ✓ {challenge_type}: {existing_count}/{target_count} (sufficient)")

    print("\n" + "="*80)
    print("✅ WEEKLY REFERENCE GENERATION COMPLETE")
    print("="*80)
    print(f"Total generated: {total_generated} challenges")
    print(f"Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)


async def generate_for_single_combo(language: str, level: str, challenge_type: str, count: int = 10):
    """
    Generate reference challenges for a single language/level/type combination
    Useful for testing

    Args:
        language: Target language
        level: CEFR level
        challenge_type: Type of challenge
        count: Number to generate (default: 10)
    """
    print(f"\n🧪 TEST MODE: Generating {count} reference challenges")
    print(f"Language: {language}, Level: {level}, Type: {challenge_type}")
    print()

    new_challenges = await generate_reference_challenges(
        language=language,
        cefr_level=level,
        challenge_type=challenge_type,
        count=count
    )

    if new_challenges:
        print(f"\n✅ Generated {len(new_challenges)} challenges")
        print("\n📝 Sample Challenge:")
        print("-" * 80)
        import json
        print(json.dumps(new_challenges[0], indent=2, default=str))
        print("-" * 80)

        # Ask if user wants to save
        save = input("\n💾 Save to reference_challenges? (yes/no): ").lower().strip()

        if save == 'yes':
            reference_collection = database.reference_challenges
            result = await reference_collection.insert_many(new_challenges)
            print(f"✅ Saved {len(result.inserted_ids)} challenges to database")
        else:
            print("⏭️  Skipped saving to database")
    else:
        print("❌ Generation failed")


async def main():
    """Main entry point"""
    import sys

    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode: generate for one combination
        language = sys.argv[2] if len(sys.argv) > 2 else "english"
        level = sys.argv[3] if len(sys.argv) > 3 else "A2"
        challenge_type = sys.argv[4] if len(sys.argv) > 4 else "brain_tickler"
        count = int(sys.argv[5]) if len(sys.argv) > 5 else 3

        await generate_for_single_combo(language, level, challenge_type, count)
    else:
        # Full weekly generation
        await replenish_reference_challenges()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🤖 CrewAI Reference Challenge Generator")
    print("="*80)
    print()
    print("Usage:")
    print("  Full generation:  python generate_reference_challenges_crew.py")
    print("  Test mode:        python generate_reference_challenges_crew.py test [lang] [level] [type] [count]")
    print()
    print("Example test:")
    print("  python generate_reference_challenges_crew.py test english A2 brain_tickler 3")
    print()
    print("="*80)
    print()

    asyncio.run(main())
