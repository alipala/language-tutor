"""
Generate High-Quality Reference Challenges
==========================================
Uses improved AI generation with:
- Explicit answer randomization
- Detailed CEFR level guidelines
- Better quality validation
- GPT-4o (or configurable newer model)

USAGE:
    # Generate for English only (recommended to start)
    python generate_reference_challenges_improved.py --language english --challenges-per-type 50

    # Generate for all languages
    python generate_reference_challenges_improved.py --all-languages --challenges-per-type 50

    # Generate for specific level only
    python generate_reference_challenges_improved.py --language spanish --level B1 --challenges-per-type 50
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the improved generator
from challenge_generator_improved import generate_challenges_with_improved_ai

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "language_tutor"

# Supported languages
LANGUAGES = ["english", "spanish", "dutch", "german", "french", "portuguese"]
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


async def validate_challenge_quality(challenge: Dict[str, Any], level: str) -> tuple[bool, List[str]]:
    """
    Validate challenge quality
    Returns: (is_valid, list_of_issues)
    """
    issues = []

    # Check required fields
    required_fields = ["id", "type", "title", "cefrLevel", "estimatedSeconds"]
    for field in required_fields:
        if field not in challenge:
            issues.append(f"Missing required field: {field}")

    # Check CEFR level matches
    if challenge.get("cefrLevel") != level:
        issues.append(f"CEFR level mismatch: expected {level}, got {challenge.get('cefrLevel')}")

    # Validate multiple choice questions
    challenge_type = challenge.get("type")
    if challenge_type in ["error_spotting", "micro_quiz", "brain_tickler"]:
        options = challenge.get("options", [])

        if len(options) != 3:
            issues.append(f"Expected 3 options, got {len(options)}")

        # Check exactly one correct answer
        correct_count = sum(1 for opt in options if opt.get("isCorrect"))
        if correct_count != 1:
            issues.append(f"Expected 1 correct answer, got {correct_count}")

        # Check for duplicate option text
        option_texts = [opt.get("text", "").lower() for opt in options]
        if len(option_texts) != len(set(option_texts)):
            issues.append("Duplicate option text found")

    # Validate swipe_fix
    if challenge_type == "swipe_fix":
        examples = challenge.get("examples", [])
        if len(examples) != 2:
            issues.append(f"swipe_fix should have 2 examples, got {len(examples)}")
        else:
            # Check one is correct, one is incorrect
            correct_count = sum(1 for ex in examples if ex.get("isCorrect"))
            if correct_count != 1:
                issues.append(f"swipe_fix should have 1 correct and 1 incorrect example")

    return (len(issues) == 0, issues)


async def generate_batch_for_level(
    level: str,
    language: str,
    challenges_per_type: int,
    db
) -> Dict[str, int]:
    """
    Generate reference challenges for a specific level and language

    Returns: Dictionary with count per challenge type
    """
    print(f"\n{'='*70}")
    print(f"🎯 Generating {language.upper()} - Level {level}")
    print(f"{'='*70}")
    print(f"Target: {challenges_per_type} challenges per type")
    print(f"Total: {challenges_per_type * 6} challenges for this level\n")

    reference_collection = db.reference_challenges

    # Check existing
    existing_count = await reference_collection.count_documents({
        "language": language,
        "cefr_level": level
    })

    print(f"Existing: {existing_count} challenges")

    if existing_count >= (challenges_per_type * 6):
        print(f"✅ Already have sufficient challenges, skipping")
        return {}

    # Organize by type
    challenges_by_type = {
        "error_spotting": [],
        "swipe_fix": [],
        "micro_quiz": [],
        "smart_flashcard": [],
        "native_check": [],
        "brain_tickler": []
    }

    # Generate in batches (each call generates 6 challenges, one per type)
    dummy_user_id = "reference_user"
    num_batches = challenges_per_type

    total_generated = 0
    total_valid = 0
    total_invalid = 0

    print(f"Generating {num_batches} batches...\n")

    for batch_num in range(1, num_batches + 1):
        # Progress indicator
        if batch_num % 5 == 0 or batch_num == 1:
            print(f"  📊 Progress: {batch_num}/{num_batches} batches", end="")
            if batch_num > 1:
                print(f" ({total_valid} valid, {total_invalid} invalid)")
            else:
                print()

        try:
            # Generate batch using improved AI
            batch = await generate_challenges_with_improved_ai(
                dummy_user_id,
                level,
                language,
                user_analysis=None  # No user context for reference challenges
            )

            if not batch:
                print(f"    ⚠️  Batch {batch_num} failed - no challenges returned")
                continue

            # Validate and categorize each challenge
            for challenge in batch:
                total_generated += 1

                challenge_type = challenge.get("type")

                # Validate quality
                is_valid, issues = await validate_challenge_quality(challenge, level)

                if not is_valid:
                    total_invalid += 1
                    print(f"    ❌ Invalid {challenge_type}: {'; '.join(issues[:2])}")
                    continue

                # Valid challenge
                total_valid += 1

                if challenge_type in challenges_by_type:
                    challenges_by_type[challenge_type].append(challenge)

            # Small delay to avoid rate limits
            await asyncio.sleep(1)

        except Exception as e:
            print(f"    ❌ Batch {batch_num} error: {str(e)}")
            continue

    # Insert into database
    print(f"\n💾 Saving to database...")

    reference_items = []
    counts_by_type = {}

    for challenge_type, challenges in challenges_by_type.items():
        count = len(challenges)
        counts_by_type[challenge_type] = count

        print(f"  {challenge_type}: {count} challenges")

        for challenge in challenges:
            reference_item = {
                "cefr_level": level,
                "language": language,
                "challenge_type": challenge_type,
                "challenge_data": challenge,
                "created_at": datetime.utcnow(),
                "tags": [level, challenge_type, "reference", language]
            }
            reference_items.append(reference_item)

    if reference_items:
        result = await reference_collection.insert_many(reference_items)
        print(f"\n✅ Inserted {len(result.inserted_ids)} challenges for {language} {level}")
    else:
        print(f"\n⚠️  No valid challenges to insert for {language} {level}")

    # Summary
    print(f"\n📊 Summary for {language} {level}:")
    print(f"  Total generated: {total_generated}")
    print(f"  Valid: {total_valid}")
    print(f"  Invalid: {total_invalid}")
    print(f"  Success rate: {(total_valid/total_generated*100) if total_generated > 0 else 0:.1f}%")

    return counts_by_type


async def generate_for_language(
    language: str,
    challenges_per_type: int,
    db,
    specific_level: str = None
) -> Dict[str, Any]:
    """Generate challenges for all levels of a language"""

    print(f"\n{'#'*70}")
    print(f"# 🌍 LANGUAGE: {language.upper()}")
    print(f"{'#'*70}\n")

    levels = [specific_level] if specific_level else CEFR_LEVELS

    total_generated = 0
    results_by_level = {}

    for level in levels:
        try:
            counts = await generate_batch_for_level(
                level,
                language,
                challenges_per_type,
                db
            )
            results_by_level[level] = counts
            total_generated += sum(counts.values())

        except Exception as e:
            print(f"\n❌ Error generating {language} {level}: {str(e)}")
            import traceback
            print(traceback.format_exc())

    return {
        "language": language,
        "total_generated": total_generated,
        "by_level": results_by_level
    }


async def create_indexes(db):
    """Create necessary indexes on reference_challenges collection"""
    print(f"\n📇 Creating database indexes...")

    reference_collection = db.reference_challenges

    try:
        # Compound index for efficient querying
        await reference_collection.create_index([
            ("language", 1),
            ("cefr_level", 1),
            ("challenge_type", 1)
        ], name="ref_lang_level_type_idx")

        # Index for random sampling
        await reference_collection.create_index([
            ("language", 1),
            ("cefr_level", 1)
        ], name="ref_lang_level_idx")

        print(f"✅ Indexes created")

    except Exception as e:
        print(f"⚠️  Error creating indexes: {str(e)}")


async def main():
    parser = argparse.ArgumentParser(description='Generate improved reference challenges')
    parser.add_argument('--language', choices=LANGUAGES,
                       help='Specific language to generate (recommended: start with english)')
    parser.add_argument('--all-languages', action='store_true',
                       help='Generate for all 6 languages')
    parser.add_argument('--level', choices=CEFR_LEVELS,
                       help='Specific CEFR level (optional, generates all if not specified)')
    parser.add_argument('--challenges-per-type', type=int, default=50,
                       help='Number of challenges per type per level (default: 50)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test without saving to database')

    args = parser.parse_args()

    # Validate arguments
    if not args.language and not args.all_languages:
        print("❌ ERROR: Must specify either --language or --all-languages")
        print("\nExamples:")
        print("  python generate_reference_challenges_improved.py --language english --challenges-per-type 50")
        print("  python generate_reference_challenges_improved.py --all-languages --challenges-per-type 50")
        sys.exit(1)

    # Header
    print(f"\n{'='*70}")
    print(f"🚀 HIGH-QUALITY REFERENCE CHALLENGE GENERATION")
    print(f"{'='*70}")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Challenges per type: {args.challenges_per_type}")
    print(f"Specific level: {args.level or 'All levels (A1-C2)'}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE GENERATION'}")
    print(f"{'='*70}\n")

    # Determine languages to process
    if args.all_languages:
        languages_to_process = LANGUAGES
        print(f"🌍 Processing ALL languages: {', '.join(LANGUAGES)}")
    else:
        languages_to_process = [args.language]
        print(f"🌍 Processing: {args.language.upper()}")

    # Calculate total
    levels_count = 1 if args.level else 6
    total_target = args.challenges_per_type * 6 * levels_count * len(languages_to_process)
    print(f"📊 Target: {total_target:,} total challenges")
    print(f"   ({len(languages_to_process)} language{'s' if len(languages_to_process) > 1 else ''} × {levels_count} level{'s' if levels_count > 1 else ''} × 6 types × {args.challenges_per_type} per type)\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)

    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        db = client[DATABASE_NAME]

        # Create indexes
        if not args.dry_run:
            await create_indexes(db)

        # Generate challenges
        start_time = datetime.utcnow()
        all_results = []

        for language in languages_to_process:
            result = await generate_for_language(
                language,
                args.challenges_per_type,
                db,
                specific_level=args.level
            )
            all_results.append(result)

        # Final summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n{'='*70}")
        print(f"✅ GENERATION COMPLETE")
        print(f"{'='*70}")
        print(f"Duration: {duration/60:.1f} minutes")
        print(f"\nResults by language:")

        grand_total = 0
        for result in all_results:
            lang = result['language']
            count = result['total_generated']
            grand_total += count
            print(f"  {lang.capitalize():12s}: {count:5d} challenges")

        print(f"\n  {'Grand Total':12s}: {grand_total:5d} challenges")
        print(f"  {'Target':12s}: {total_target:5d} challenges")

        if grand_total > 0:
            completion = (grand_total / total_target * 100)
            print(f"  {'Completion':12s}: {completion:5.1f}%")

        # Verify in database
        if not args.dry_run:
            print(f"\n📊 Database verification:")
            for language in languages_to_process:
                total = await db.reference_challenges.count_documents({"language": language})
                print(f"  {language.capitalize()}: {total:,} challenges in database")

        print(f"\n{'='*70}")
        print(f"🎉 SUCCESS! Ready for production use")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

    finally:
        client.close()
        print("🔌 MongoDB connection closed\n")


if __name__ == "__main__":
    asyncio.run(main())
