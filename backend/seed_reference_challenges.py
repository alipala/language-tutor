"""
Seed Reference Challenges
Generate generic, reusable challenges for all CEFR levels
These are used for new users who need instant challenges
"""

import asyncio
from datetime import datetime
from database import database
from challenge_generator_ai import generate_challenges_with_ai


async def generate_reference_challenges_for_level(
    level: str,
    language: str = "english",
    challenges_per_type: int = 50
) -> int:
    """
    Generate reference challenges for a specific CEFR level and language

    Args:
        level: CEFR level (A1-C2)
        language: Target language (default: "english")
        challenges_per_type: Number per type (default 50)

    Returns:
        Number of challenges generated
    """
    try:
        print(f"\n[REF_SEED] 🎯 Generating reference challenges for {language} {level}")

        reference_collection = database.reference_challenges

        # Check existing
        existing_count = await reference_collection.count_documents({
            "language": language,
            "cefr_level": level
        })

        if existing_count >= (challenges_per_type * 7):
            print(f"[REF_SEED] ✅ {language} {level} already has {existing_count} challenges, skipping")
            return 0

        print(f"[REF_SEED] 📊 Current: {existing_count} challenges for {language} {level}")

        challenges_by_type = {
            "error_spotting": [],
            "swipe_fix": [],
            "micro_quiz": [],
            "smart_flashcard": [],
            "native_check": [],
            "brain_tickler": [],
            "story_builder": []
        }

        # Generate batches (use dummy user ID for generic challenges)
        dummy_user_id = "reference_user"
        num_batches = challenges_per_type

        print(f"[REF_SEED] 🤖 Generating {num_batches} batches...")

        for batch_num in range(1, num_batches + 1):
            if batch_num % 10 == 0:
                print(f"[REF_SEED] 📈 Progress: {batch_num}/{num_batches}")

            batch = await generate_challenges_with_ai(dummy_user_id, level)

            if batch:
                for challenge in batch:
                    challenge_type = challenge.get("type")
                    if challenge_type in challenges_by_type:
                        challenges_by_type[challenge_type].append(challenge)

        # Insert into reference collection
        reference_items = []
        total = 0

        for challenge_type, challenges in challenges_by_type.items():
            print(f"[REF_SEED] 💾 Preparing {len(challenges)} {challenge_type} challenges")

            for challenge in challenges:
                reference_item = {
                    "cefr_level": level,
                    "challenge_type": challenge_type,
                    "challenge_data": challenge,
                    "created_at": datetime.utcnow(),
                    "tags": [level, challenge_type, "reference"]
                }
                reference_items.append(reference_item)
                total += 1

        if reference_items:
            result = await reference_collection.insert_many(reference_items)
            print(f"[REF_SEED] ✅ Inserted {len(result.inserted_ids)} reference challenges for level {level}")

        return total

    except Exception as e:
        print(f"[REF_SEED] ❌ Error generating for level {level}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 0


async def seed_all_levels(challenges_per_type: int = 50):
    """
    Generate reference challenges for all CEFR levels

    Args:
        challenges_per_type: Number per type per level (default 50)
    """
    try:
        print(f"\n{'='*70}")
        print(f"[REF_SEED] 🚀 Seeding Reference Challenges")
        print(f"[REF_SEED] 📋 Target: {challenges_per_type} per type per level")
        print(f"[REF_SEED] 📊 Total: {challenges_per_type * 7 * 6} challenges (7 types × 6 levels)")
        print(f"{'='*70}\n")

        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

        total_generated = 0
        start_time = datetime.now()

        for idx, level in enumerate(levels, 1):
            print(f"\n[REF_SEED] 📚 Level {idx}/6: {level}")

            generated = await generate_reference_challenges_for_level(
                level,
                challenges_per_type
            )

            total_generated += generated

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60

        print(f"\n{'='*70}")
        print(f"[REF_SEED] 🎉 Reference Seeding Complete!")
        print(f"[REF_SEED] ✅ Total challenges generated: {total_generated}")
        print(f"[REF_SEED] ⏱️  Total time: {duration:.1f} minutes")
        print(f"{'='*70}\n")

        # Show breakdown
        reference_collection = database.reference_challenges

        print(f"[REF_SEED] 📊 Breakdown by level:")
        for level in levels:
            count = await reference_collection.count_documents({"cefr_level": level})
            print(f"  {level}: {count} challenges")

        print()

    except Exception as e:
        print(f"[REF_SEED] ❌ Error seeding all levels: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def create_indexes():
    """Create indexes on reference_challenges collection"""
    try:
        print(f"[REF_SEED] 📇 Creating indexes...")

        reference_collection = database.reference_challenges

        # Index for querying by level and type
        await reference_collection.create_index([
            ("cefr_level", 1),
            ("challenge_type", 1)
        ], name="ref_level_type_index")

        # Index for random sampling
        await reference_collection.create_index("cefr_level", name="ref_level_index")

        print(f"[REF_SEED] ✅ Indexes created")

    except Exception as e:
        print(f"[REF_SEED] ⚠️ Error creating indexes: {str(e)}")


async def main():
    """Main entry point"""
    import sys

    # Create indexes first
    await create_indexes()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            # Seed all levels
            challenges_per_type = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            await seed_all_levels(challenges_per_type)

        elif command == "level":
            # Seed specific level
            if len(sys.argv) < 3:
                print("Usage: python seed_reference_challenges.py level <A1-C2> [count]")
                return

            level = sys.argv[2].upper()
            challenges_per_type = int(sys.argv[3]) if len(sys.argv) > 3 else 50

            if level not in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                print(f"Invalid level: {level}. Must be A1-C2")
                return

            await generate_reference_challenges_for_level(level, challenges_per_type)

        else:
            print("Unknown command")
    else:
        print("\n📖 Usage:")
        print("  python seed_reference_challenges.py all [count_per_type]")
        print("  python seed_reference_challenges.py level <A1-C2> [count_per_type]")
        print("\nExamples:")
        print("  python seed_reference_challenges.py all 50")
        print("  python seed_reference_challenges.py level B1 50")
        print("\n⏱️  Time estimates (50 per type):")
        print("  - Single level: ~25 minutes")
        print("  - All 6 levels: ~2.5 hours")
        print()


if __name__ == "__main__":
    asyncio.run(main())
