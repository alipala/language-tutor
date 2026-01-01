"""
Generate Sample Story Builder Challenges
Generates 5 sample challenges for each CEFR level to test quality
"""

import asyncio
import json
from datetime import datetime
from database import database
from challenge_generator_ai import generate_challenges_with_ai

async def generate_samples_for_level(level: str, num_samples: int = 5) -> list:
    """
    Generate sample story_builder challenges for a specific level

    Args:
        level: CEFR level (A1-C2)
        num_samples: Number of samples to generate (default: 5)

    Returns:
        List of story_builder challenges
    """
    try:
        print(f"\n{'='*60}")
        print(f"[SAMPLE] 📖 Generating Story Builder samples for {level}")
        print(f"{'='*60}\n")

        story_builder_challenges = []

        # Generate challenges in batches
        for i in range(num_samples):
            print(f"[SAMPLE] 🤖 Generating sample {i+1}/{num_samples}...")

            # Use dummy user for generic challenges
            challenges = await generate_challenges_with_ai(
                user_id="reference_user",
                user_level=level,
                language="english"
            )

            # Extract story_builder challenge
            story_builder = next(
                (c for c in challenges if c.get("type") == "story_builder"),
                None
            )

            if story_builder:
                story_builder_challenges.append(story_builder)
                print(f"[SAMPLE] ✅ Generated: {story_builder.get('storyText', '')[:50]}...")
            else:
                print(f"[SAMPLE] ⚠️ No story_builder challenge in batch")

        return story_builder_challenges

    except Exception as e:
        print(f"[SAMPLE] ❌ Error generating samples for {level}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

async def save_samples_to_mongodb(level: str, challenges: list):
    """Save sample challenges to MongoDB for review"""
    try:
        collection = database.story_builder_samples

        # Clear existing samples for this level
        await collection.delete_many({"cefr_level": level})

        # Insert new samples
        for challenge in challenges:
            doc = {
                "cefr_level": level,
                "challenge_data": challenge,
                "created_at": datetime.utcnow(),
                "reviewed": False,
                "quality_score": None,
                "reviewer_notes": None
            }
            await collection.insert_one(doc)

        print(f"[SAMPLE] 💾 Saved {len(challenges)} samples to MongoDB for level {level}")

    except Exception as e:
        print(f"[SAMPLE] ❌ Error saving samples: {str(e)}")

async def generate_all_samples():
    """Generate samples for all CEFR levels"""
    try:
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

        print(f"\n{'='*60}")
        print(f"[SAMPLE] 🚀 Story Builder Sample Generation")
        print(f"[SAMPLE] 📊 Generating 5 samples per level (30 total)")
        print(f"{'='*60}\n")

        all_samples = {}

        for idx, level in enumerate(levels, 1):
            print(f"\n[SAMPLE] 📚 Level {idx}/6: {level}")

            samples = await generate_samples_for_level(level, num_samples=5)
            all_samples[level] = samples

            # Save to MongoDB
            await save_samples_to_mongodb(level, samples)

            # Save to JSON file for easy review
            filename = f"story_builder_samples_{level}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(samples, f, indent=2, ensure_ascii=False)

            print(f"[SAMPLE] 📄 Saved to {filename}")

        print(f"\n{'='*60}")
        print(f"[SAMPLE] 🎉 Sample Generation Complete!")
        print(f"[SAMPLE] ✅ Total samples generated: {sum(len(s) for s in all_samples.values())}")
        print(f"{'='*60}\n")

        # Summary
        print(f"[SAMPLE] 📊 Summary by level:")
        for level, samples in all_samples.items():
            print(f"  {level}: {len(samples)} samples")

        print(f"\n[SAMPLE] 📝 Review samples:")
        print(f"  - JSON files: story_builder_samples_*.json")
        print(f"  - MongoDB: story_builder_samples collection")
        print(f"\n[SAMPLE] 💡 Next steps:")
        print(f"  1. Review the quality of generated challenges")
        print(f"  2. Check for proper gap placement and distractors")
        print(f"  3. Verify CEFR level appropriateness")
        print(f"  4. Test drag & drop UI with these samples")
        print(f"  5. Adjust AI prompt if needed")
        print(f"  6. Run full reference seeding (50+ per level)")

    except Exception as e:
        print(f"[SAMPLE] ❌ Error in sample generation: {str(e)}")
        import traceback
        print(traceback.format_exc())

async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        level = sys.argv[1].upper()
        if level not in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            print(f"Invalid level: {level}. Must be A1-C2")
            return

        print(f"\n[SAMPLE] Generating samples for level {level}...")
        samples = await generate_samples_for_level(level, num_samples=5)
        await save_samples_to_mongodb(level, samples)

        filename = f"story_builder_samples_{level}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)

        print(f"[SAMPLE] ✅ Done! Saved to {filename}")
    else:
        await generate_all_samples()

if __name__ == "__main__":
    asyncio.run(main())
