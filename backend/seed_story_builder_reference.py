"""
Seed Story Builder challenges into reference_challenges collection
Takes samples from story_builder_samples and moves them to reference_challenges
"""

import asyncio
from datetime import datetime
from database import database

async def seed_story_builder_to_reference():
    """Move story_builder samples to reference_challenges"""
    try:
        print(f"\n{'='*60}")
        print(f"[SEED] 📖 Seeding Story Builder to Reference Challenges")
        print(f"{'='*60}\n")

        samples_collection = database.story_builder_samples
        reference_collection = database.reference_challenges

        # Check current counts
        sample_count = await samples_collection.count_documents({})
        ref_sb_count = await reference_collection.count_documents({"challenge_type": "story_builder"})

        print(f"[SEED] 📊 Current status:")
        print(f"  - Samples: {sample_count}")
        print(f"  - Reference story_builder: {ref_sb_count}")

        if sample_count == 0:
            print(f"[SEED] ⚠️ No samples found! Run generate_story_builder_samples.py first")
            return

        # Get all samples
        samples = await samples_collection.find({}).to_list(length=None)
        print(f"[SEED] 📥 Found {len(samples)} samples to seed")

        # Transform samples to reference format
        reference_items = []
        for sample in samples:
            level = sample.get("cefr_level")
            challenge_data = sample.get("challenge_data")

            if not level or not challenge_data:
                print(f"[SEED] ⚠️ Skipping invalid sample: {sample.get('_id')}")
                continue

            reference_item = {
                "cefr_level": level,
                "challenge_type": "story_builder",
                "language": "english",  # Default to english
                "challenge_data": challenge_data,
                "created_at": datetime.utcnow(),
                "tags": [level, "story_builder", "reference"]
            }
            reference_items.append(reference_item)

        if not reference_items:
            print(f"[SEED] ❌ No valid items to insert")
            return

        # Insert into reference_challenges
        result = await reference_collection.insert_many(reference_items)
        print(f"[SEED] ✅ Inserted {len(result.inserted_ids)} story_builder challenges")

        # Show breakdown by level
        print(f"\n[SEED] 📊 Breakdown by level:")
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            count = await reference_collection.count_documents({
                "cefr_level": level,
                "challenge_type": "story_builder"
            })
            print(f"  {level}: {count} challenges")

        # Show total reference counts
        print(f"\n[SEED] 📊 Total reference challenges by type:")
        pipeline = [
            {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        async for doc in reference_collection.aggregate(pipeline):
            print(f"  {doc['_id']}: {doc['count']}")

        print(f"\n{'='*60}")
        print(f"[SEED] 🎉 Story Builder seeding complete!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"[SEED] ❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def main():
    await seed_story_builder_to_reference()


if __name__ == "__main__":
    asyncio.run(main())
