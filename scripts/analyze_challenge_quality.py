"""
Analyze Challenge Quality Issues
=================================
This script analyzes existing challenges to identify quality problems:
1. Answer position bias (correct answer always in same position)
2. CEFR level appropriateness
3. Missing language fields
4. Collection statistics

USAGE:
    python analyze_challenge_quality.py

    # Analyze specific collection only
    python analyze_challenge_quality.py --collection reference_challenges

    # Save analysis report
    python analyze_challenge_quality.py --save-report
"""

import asyncio
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend to path for database import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "language_tutor"


async def analyze_answer_position_bias(collection_name: str, db):
    """Analyze if correct answers are biased towards certain positions"""
    print(f"\n{'='*70}")
    print(f"📊 ANSWER POSITION ANALYSIS - {collection_name}")
    print(f"{'='*70}")

    collection = db[collection_name]

    # Challenge types with multiple choice options
    challenge_types_with_options = ["error_spotting", "micro_quiz", "brain_tickler"]

    position_stats = defaultdict(lambda: Counter())
    total_by_type = defaultdict(int)

    for challenge_type in challenge_types_with_options:
        cursor = collection.find({"challenge_type": challenge_type})

        async for doc in cursor:
            challenge_data = doc.get("challenge_data", {})
            options = challenge_data.get("options", [])

            if not options:
                continue

            total_by_type[challenge_type] += 1

            # Find position of correct answer
            for idx, option in enumerate(options):
                if option.get("isCorrect"):
                    position_stats[challenge_type][idx] += 1
                    break

    # Print results
    bias_detected = False

    for challenge_type in challenge_types_with_options:
        total = total_by_type[challenge_type]
        if total == 0:
            print(f"\n❌ {challenge_type}: No challenges found")
            continue

        print(f"\n{challenge_type.upper()}: {total} challenges analyzed")
        print(f"   Correct answer position distribution:")

        positions = position_stats[challenge_type]
        max_pos = max(positions.keys()) + 1 if positions else 3

        for pos in range(max_pos):
            count = positions[pos]
            percentage = (count / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 2)

            # Flag if heavily biased (should be ~33% for 3 options)
            is_biased = percentage > 40 or percentage < 25
            warning = " ⚠️  BIAS!" if is_biased else ""

            if is_biased:
                bias_detected = True

            label = f"Option {pos + 1} (Position {pos})"
            print(f"   {label:25s}: {count:4d} ({percentage:5.1f}%) {bar}{warning}")

        # Expected distribution
        expected_pct = 100 / max_pos if max_pos > 0 else 33.3
        print(f"\n   Expected (random): ~{expected_pct:.1f}% per position")

    if bias_detected:
        print(f"\n⚠️  WARNING: Answer position bias detected!")
        print(f"   Correct answers are not evenly distributed across positions.")
        print(f"   This makes challenges predictable and reduces learning effectiveness.")
    else:
        print(f"\n✅ Answer positions appear well-distributed")

    return position_stats, total_by_type


async def analyze_language_field(collection_name: str, db):
    """Check for missing language fields"""
    print(f"\n{'='*70}")
    print(f"🌍 LANGUAGE FIELD ANALYSIS - {collection_name}")
    print(f"{'='*70}")

    collection = db[collection_name]

    total = await collection.count_documents({})
    with_language = await collection.count_documents({"language": {"$exists": True}})
    without_language = total - with_language

    print(f"\nTotal challenges: {total:,}")
    print(f"With language field: {with_language:,}")
    print(f"Missing language field: {without_language:,}")

    if without_language > 0:
        print(f"\n⚠️  WARNING: {without_language:,} challenges missing language field!")
        print(f"   Missing language data can cause incorrect challenge selection.")

    # Count by language
    pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    language_counts = await collection.aggregate(pipeline).to_list(length=100)

    print(f"\nChallenges by language:")
    for item in language_counts:
        lang = item["_id"] or "MISSING"
        count = item["count"]
        print(f"  {lang:12s}: {count:6,}")

    return {"total": total, "with_language": with_language, "without_language": without_language}


async def analyze_cefr_levels(collection_name: str, db):
    """Analyze CEFR level distribution"""
    print(f"\n{'='*70}")
    print(f"📚 CEFR LEVEL DISTRIBUTION - {collection_name}")
    print(f"{'='*70}")

    collection = db[collection_name]

    pipeline = [
        {"$group": {"_id": {"level": "$cefr_level", "type": "$challenge_type"}, "count": {"$sum": 1}}},
        {"$sort": {"_id.level": 1, "_id.type": 1}}
    ]

    results = await collection.aggregate(pipeline).to_list(length=1000)

    # Organize by level
    by_level = defaultdict(lambda: defaultdict(int))
    for item in results:
        level = item["_id"]["level"]
        ctype = item["_id"]["type"]
        count = item["count"]
        by_level[level][ctype] = count

    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    challenge_types = ["error_spotting", "swipe_fix", "micro_quiz", "smart_flashcard", "native_check", "brain_tickler"]

    print(f"\nChallenges per level and type:\n")
    print(f"{'Level':<8}", end="")
    for ctype in challenge_types:
        # Abbreviate for display
        abbrev = ctype.replace("_", "")[:8]
        print(f"{abbrev:<10}", end="")
    print("TOTAL")
    print("-" * 70)

    for level in levels:
        print(f"{level:<8}", end="")
        total_for_level = 0
        for ctype in challenge_types:
            count = by_level[level][ctype]
            total_for_level += count
            print(f"{count:<10}", end="")
        print(f"{total_for_level}")

    # Check for imbalances
    print(f"\n📊 Balance Analysis:")
    for level in levels:
        counts = [by_level[level][ct] for ct in challenge_types]
        if counts:
            min_count = min(counts)
            max_count = max(counts)
            imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')

            if imbalance_ratio > 2:
                print(f"  ⚠️  {level}: Imbalanced (min={min_count}, max={max_count}, ratio={imbalance_ratio:.1f}x)")
            else:
                print(f"  ✅ {level}: Well balanced (min={min_count}, max={max_count})")

    return by_level


async def analyze_collection_stats(collection_name: str, db):
    """Get general collection statistics"""
    print(f"\n{'='*70}")
    print(f"📈 COLLECTION STATISTICS - {collection_name}")
    print(f"{'='*70}")

    collection = db[collection_name]

    total = await collection.count_documents({})

    print(f"\nTotal documents: {total:,}")

    if total == 0:
        print(f"⚠️  Collection is empty!")
        return 0

    # Get oldest and newest
    oldest = await collection.find_one({}, sort=[("created_at", 1)])
    newest = await collection.find_one({}, sort=[("created_at", -1)])

    if oldest and oldest.get("created_at"):
        oldest_date = oldest["created_at"]
        print(f"Oldest challenge: {oldest_date}")

    if newest and newest.get("created_at"):
        newest_date = newest["created_at"]
        print(f"Newest challenge: {newest_date}")

    # Check for model/source information
    has_source = await collection.count_documents({"challenge_data.source": {"$exists": True}})
    has_model = await collection.count_documents({"challenge_data.model": {"$exists": True}})

    print(f"\nGeneration metadata:")
    print(f"  With source info: {has_source:,}")
    print(f"  With model info: {has_model:,}")

    # Sample a few challenges to inspect quality
    samples = await collection.aggregate([{"$sample": {"size": 3}}]).to_list(length=3)

    print(f"\n📝 Sample challenges:")
    for idx, sample in enumerate(samples, 1):
        challenge_data = sample.get("challenge_data", {})
        print(f"\nSample {idx}:")
        print(f"  Type: {sample.get('challenge_type', 'Unknown')}")
        print(f"  Level: {sample.get('cefr_level', 'Unknown')}")
        print(f"  Language: {sample.get('language', 'MISSING')}")
        print(f"  Source: {challenge_data.get('source', 'Unknown')}")

        if challenge_data.get("question"):
            print(f"  Question: {challenge_data['question'][:80]}...")
        elif challenge_data.get("sentence"):
            print(f"  Sentence: {challenge_data['sentence'][:80]}...")

        options = challenge_data.get("options", [])
        if options:
            print(f"  Options ({len(options)} total):")
            for opt_idx, opt in enumerate(options):
                marker = "✓" if opt.get("isCorrect") else " "
                text = opt.get('text', 'N/A')[:50]
                print(f"    [{marker}] Option {opt_idx}: {text}")

    return total


async def generate_quality_report(analysis_results: Dict, collection_name: str) -> str:
    """Generate a formatted quality report"""

    report = f"""
{'='*70}
CHALLENGE QUALITY ANALYSIS REPORT
Collection: {collection_name}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
{'='*70}

1. COLLECTION SIZE:
   Total Challenges: {analysis_results.get('total', 0):,}

2. LANGUAGE COVERAGE:
   With Language Field: {analysis_results.get('with_language', 0):,}
   Missing Language: {analysis_results.get('without_language', 0):,}

3. ANSWER POSITION BIAS:
   Status: {analysis_results.get('bias_status', 'Unknown')}

4. CEFR LEVEL BALANCE:
   {analysis_results.get('level_balance', 'Not analyzed')}

5. QUALITY ISSUES FOUND:
   {chr(10).join('   - ' + issue for issue in analysis_results.get('issues', ['None']))}

6. RECOMMENDATIONS:
   {chr(10).join('   - ' + rec for rec in analysis_results.get('recommendations', ['No recommendations']))}

{'='*70}
"""

    return report


async def main():
    parser = argparse.ArgumentParser(description='Analyze challenge quality')
    parser.add_argument('--collection', choices=['reference_challenges', 'challenge_pool', 'both'],
                       default='both', help='Which collection(s) to analyze')
    parser.add_argument('--save-report', action='store_true',
                       help='Save analysis report to file')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"🔍 CHALLENGE QUALITY ANALYSIS TOOL")
    print(f"{'='*70}")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Target: {args.collection}")
    print(f"{'='*70}\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)

    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")

        db = client[DATABASE_NAME]

        # Determine collections to analyze
        collections = []
        if args.collection in ['reference_challenges', 'both']:
            collections.append('reference_challenges')
        if args.collection in ['challenge_pool', 'both']:
            collections.append('challenge_pool')

        # Analyze each collection
        for collection_name in collections:
            print(f"\n\n{'#'*70}")
            print(f"# ANALYZING: {collection_name.upper()}")
            print(f"{'#'*70}\n")

            # Run all analyses
            total = await analyze_collection_stats(collection_name, db)

            if total > 0:
                await analyze_language_field(collection_name, db)
                await analyze_cefr_levels(collection_name, db)
                await analyze_answer_position_bias(collection_name, db)

        print(f"\n{'='*70}")
        print(f"✅ ANALYSIS COMPLETE")
        print(f"{'='*70}\n")

        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. If answer position bias detected:")
        print(f"      → Delete and regenerate with improved generator")
        print(f"   2. If language fields missing:")
        print(f"      → Run migration script to add language fields")
        print(f"   3. If CEFR levels imbalanced:")
        print(f"      → Generate more challenges for under-represented levels")
        print(f"\n   Use delete_all_challenges.py and generate_reference_challenges_improved.py")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

    finally:
        client.close()
        print("🔌 MongoDB connection closed\n")


if __name__ == "__main__":
    asyncio.run(main())
