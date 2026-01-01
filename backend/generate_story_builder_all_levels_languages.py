"""
Generate Story Builder Challenges for All Levels and Languages
Generates high-quality, creative challenges using GPT-4o
Supports 6 CEFR levels (A1, A2, B1, B2, C1, C2) and 6 languages
"""

import asyncio
import json
from datetime import datetime
from database import database
from challenge_generator_ai import generate_challenges_with_ai
import sys

# Configuration
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
LANGUAGES = ["english", "spanish", "dutch", "german", "french", "portuguese"]
CHALLENGES_PER_LEVEL = 50  # Can be adjusted

# Language names for display
LANGUAGE_NAMES = {
    "english": "English",
    "spanish": "Spanish",
    "dutch": "Dutch",
    "german": "German",
    "french": "French",
    "portuguese": "Portuguese"
}


async def generate_for_level_and_language(
    level: str,
    language: str,
    count: int = 50
) -> list:
    """
    Generate story_builder challenges for a specific level and language

    Args:
        level: CEFR level (A1-C2)
        language: Target language
        count: Number of challenges to generate

    Returns:
        List of generated story_builder challenges
    """
    challenges = []

    try:
        print(f"\n[GEN] 🤖 Generating {count} challenges for {LANGUAGE_NAMES.get(language, language)} {level}")
        print(f"[GEN] Using GPT-4o for maximum quality...")

        batch_size = 5  # Generate 5 at a time (adjust based on rate limits)
        batches = count // batch_size
        remainder = count % batch_size

        for batch_num in range(batches):
            print(f"[GEN] 📦 Batch {batch_num + 1}/{batches + (1 if remainder > 0 else 0)} ({len(challenges)}/{count} generated)", end="\r")

            # Generate a batch
            result = await generate_challenges_with_ai(
                user_id="reference_user",
                user_level=level,
                language=language
            )

            # Extract story_builder challenges
            story_builder_challenges = [
                c for c in result
                if c.get("type") == "story_builder"
            ]

            challenges.extend(story_builder_challenges)

            # Add delay to respect rate limits
            await asyncio.sleep(1)

        # Generate remaining challenges
        if remainder > 0:
            print(f"[GEN] 📦 Final batch ({len(challenges)}/{count} generated)", end="\r")
            result = await generate_challenges_with_ai(
                user_id="reference_user",
                user_level=level,
                language=language
            )
            story_builder_challenges = [
                c for c in result
                if c.get("type") == "story_builder"
            ]
            challenges.extend(story_builder_challenges[:remainder])

        print(f"\n[GEN] ✅ Generated {len(challenges)} challenges for {LANGUAGE_NAMES.get(language, language)} {level}")

        return challenges[:count]  # Ensure we don't exceed count

    except Exception as e:
        print(f"\n[GEN] ❌ Error generating for {language} {level}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return challenges


async def save_to_reference_collection(
    level: str,
    language: str,
    challenges: list
):
    """Save generated challenges directly to reference_challenges collection"""
    try:
        collection = database.reference_challenges

        items = []
        for challenge in challenges:
            item = {
                "cefr_level": level,
                "challenge_type": "story_builder",
                "language": language,
                "challenge_data": challenge,
                "created_at": datetime.utcnow(),
                "tags": [level, "story_builder", language, "reference", "gpt4o"]
            }
            items.append(item)

        if items:
            await collection.insert_many(items)
            print(f"[SAVE] 💾 Saved {len(items)} challenges to reference_challenges")

    except Exception as e:
        print(f"[SAVE] ❌ Error saving: {str(e)}")


async def generate_all():
    """Generate challenges for all levels and languages"""
    try:
        print(f"\n{'='*80}")
        print(f"🚀 STORY BUILDER CHALLENGE GENERATION - ALL LEVELS & LANGUAGES")
        print(f"{'='*80}")
        print(f"\n📊 Configuration:")
        print(f"  Levels: {', '.join(LEVELS)} (6 levels)")
        print(f"  Languages: {', '.join(LANGUAGE_NAMES.values())} (6 languages)")
        print(f"  Challenges per level: {CHALLENGES_PER_LEVEL}")
        print(f"  Total challenges: {len(LEVELS) * len(LANGUAGES) * CHALLENGES_PER_LEVEL}")
        print(f"  Model: GPT-4o (highest quality)")
        print(f"\n{'='*80}\n")

        total_generated = 0

        for lang_idx, language in enumerate(LANGUAGES, 1):
            lang_name = LANGUAGE_NAMES.get(language, language)
            print(f"\n{'='*80}")
            print(f"🌍 LANGUAGE {lang_idx}/{len(LANGUAGES)}: {lang_name.upper()}")
            print(f"{'='*80}\n")

            for level_idx, level in enumerate(LEVELS, 1):
                print(f"\n[{lang_name}] 📚 Level {level_idx}/{len(LEVELS)}: {level}")

                # Generate challenges
                challenges = await generate_for_level_and_language(
                    level,
                    language,
                    CHALLENGES_PER_LEVEL
                )

                if challenges:
                    # Save to database
                    await save_to_reference_collection(level, language, challenges)

                    # Save to JSON file for backup/review
                    filename = f"story_builder_{language}_{level}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(challenges, f, indent=2, ensure_ascii=False)

                    print(f"[{lang_name}] 📄 Saved to {filename}")
                    total_generated += len(challenges)
                else:
                    print(f"[{lang_name}] ⚠️ No challenges generated for {level}")

                # Small delay between levels
                await asyncio.sleep(2)

        # Final summary
        print(f"\n{'='*80}")
        print(f"🎉 GENERATION COMPLETE!")
        print(f"{'='*80}\n")
        print(f"📊 Summary:")
        print(f"  Total generated: {total_generated} challenges")
        print(f"  Target: {len(LEVELS) * len(LANGUAGES) * CHALLENGES_PER_LEVEL} challenges")
        print(f"  Success rate: {(total_generated / (len(LEVELS) * len(LANGUAGES) * CHALLENGES_PER_LEVEL) * 100):.1f}%")

        # Database statistics
        print(f"\n📊 Database breakdown:")
        collection = database.reference_challenges

        for language in LANGUAGES:
            lang_name = LANGUAGE_NAMES.get(language, language)
            print(f"\n  {lang_name}:")
            for level in LEVELS:
                count = await collection.count_documents({
                    "language": language,
                    "cefr_level": level,
                    "challenge_type": "story_builder"
                })
                print(f"    {level}: {count} challenges")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Error in generation: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def generate_specific(language: str, level: str, count: int = 50):
    """Generate challenges for a specific language and level"""
    try:
        lang_name = LANGUAGE_NAMES.get(language, language)
        print(f"\n{'='*80}")
        print(f"🚀 GENERATING STORY BUILDER CHALLENGES")
        print(f"{'='*80}")
        print(f"\n  Language: {lang_name}")
        print(f"  Level: {level}")
        print(f"  Count: {count}")
        print(f"  Model: GPT-4o")
        print(f"\n{'='*80}\n")

        challenges = await generate_for_level_and_language(level, language, count)

        if challenges:
            await save_to_reference_collection(level, language, challenges)

            filename = f"story_builder_{language}_{level}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(challenges, f, indent=2, ensure_ascii=False)

            print(f"\n✅ Success! Generated {len(challenges)} challenges")
            print(f"📄 Saved to: {filename}")
            print(f"💾 Saved to database: reference_challenges collection")
        else:
            print(f"\n⚠️ No challenges generated")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Specific language/level mode
        if sys.argv[1] == "--all":
            await generate_all()
        elif len(sys.argv) >= 3:
            language = sys.argv[1].lower()
            level = sys.argv[2].upper()
            count = int(sys.argv[3]) if len(sys.argv) > 3 else 50

            if language not in LANGUAGES:
                print(f"❌ Invalid language: {language}")
                print(f"Valid languages: {', '.join(LANGUAGES)}")
                return

            if level not in LEVELS:
                print(f"❌ Invalid level: {level}")
                print(f"Valid levels: {', '.join(LEVELS)}")
                return

            await generate_specific(language, level, count)
        else:
            print("Usage:")
            print("  Generate all: python generate_story_builder_all_levels_languages.py --all")
            print("  Specific: python generate_story_builder_all_levels_languages.py <language> <level> [count]")
            print(f"\nLanguages: {', '.join(LANGUAGES)}")
            print(f"Levels: {', '.join(LEVELS)}")
            print("\nExamples:")
            print("  python generate_story_builder_all_levels_languages.py english B1 50")
            print("  python generate_story_builder_all_levels_languages.py spanish A2 30")
            print("  python generate_story_builder_all_levels_languages.py --all")
    else:
        # Default: generate all
        await generate_all()


if __name__ == "__main__":
    asyncio.run(main())
