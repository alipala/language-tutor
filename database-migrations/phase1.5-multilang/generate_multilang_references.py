"""
Phase 1.5: Multi-Language Reference Challenge Generator
========================================================
Generates reference challenges for 6 languages × 6 CEFR levels × 6 types

Languages: Dutch, Spanish, German, French, Portuguese (English already exists)
CEFR Levels: A1, A2, B1, B2, C1, C2
Challenge Types: error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler

Total to generate: ~3,000 challenges (600 per language × 5 languages)
Estimated cost: $1.50
Estimated time: 1-2 hours
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import uuid
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin")
DATABASE_NAME = "language_tutor"

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
LANGUAGES = {
    "dutch": {"native": "Nederlands", "english": "Dutch"},
    "spanish": {"native": "Español", "english": "Spanish"},
    "german": {"native": "Deutsch", "english": "German"},
    "french": {"native": "Français", "english": "French"},
    "portuguese": {"native": "Português", "english": "Portuguese"}
}

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

CHALLENGE_TYPES = [
    "error_spotting",
    "swipe_fix",
    "micro_quiz",
    "smart_flashcard",
    "native_check",
    "brain_tickler"
]

# Generate ~17 challenges per (type, level) combination = ~100 per type
CHALLENGES_PER_TYPE_LEVEL = 17

# Progress tracking
progress = {
    "total_generated": 0,
    "total_cost": 0.0,
    "by_language": {},
    "errors": []
}


def generate_challenge_prompt(language: str, language_native: str, cefr_level: str, challenge_type: str, batch_size: int = 17) -> str:
    """Generate GPT-4o prompt for creating reference challenges"""

    level_descriptions = {
        "A1": "Complete beginner - basic words and phrases",
        "A2": "Elementary - simple sentences and everyday topics",
        "B1": "Intermediate - can handle most situations while traveling",
        "B2": "Upper intermediate - can interact fluently with native speakers",
        "C1": "Advanced - can express ideas fluently and spontaneously",
        "C2": "Proficient - near-native level, nuanced understanding"
    }

    type_specs = {
        "error_spotting": {
            "description": "Find the grammatical error in a sentence",
            "schema": """{{
  "id": "unique_id",
  "type": "error_spotting",
  "title": "Spot the Mistake",
  "emoji": "🧩",
  "description": "Find the error",
  "cefrLevel": "{level}",
  "estimatedSeconds": 12,
  "sentence": "Sentence with an error in {language}",
  "options": [
    {{"id": "opt1", "text": "error part", "isCorrect": true}},
    {{"id": "opt2", "text": "correct part", "isCorrect": false}},
    {{"id": "opt3", "text": "another correct part", "isCorrect": false}}
  ],
  "explanation": "Why it's wrong and how to fix it in {language}",
  "correctedSentence": "The correct version",
  "tags": ["grammar_category"],
  "completed": false
}}"""
        },
        "swipe_fix": {
            "description": "Compare wrong vs right usage",
            "schema": """{{
  "id": "unique_id",
  "type": "swipe_fix",
  "title": "Compare & Learn",
  "emoji": "🔄",
  "description": "Which is correct?",
  "cefrLevel": "{level}",
  "estimatedSeconds": 15,
  "concept": "The grammar/vocabulary concept being taught",
  "examples": [
    {{"text": "Wrong usage in {language}", "isCorrect": false, "explanation": "Why wrong"}},
    {{"text": "Correct usage in {language}", "isCorrect": true, "explanation": "Why right"}}
  ],
  "tags": ["concept_tag"],
  "completed": false
}}"""
        },
        "micro_quiz": {
            "description": "Quick multiple choice question",
            "schema": """{{
  "id": "unique_id",
  "type": "micro_quiz",
  "title": "Quick Quiz",
  "emoji": "⚡",
  "description": "Fast decision",
  "cefrLevel": "{level}",
  "estimatedSeconds": 10,
  "question": "Question in {language}",
  "options": [
    {{"id": "opt1", "text": "option 1", "isCorrect": false}},
    {{"id": "opt2", "text": "option 2", "isCorrect": true}},
    {{"id": "opt3", "text": "option 3", "isCorrect": false}}
  ],
  "explanation": "Why option 2 is correct",
  "tags": ["topic_tag"],
  "completed": false
}}"""
        },
        "smart_flashcard": {
            "description": "Vocabulary flashcard with context",
            "schema": """{{
  "id": "unique_id",
  "type": "smart_flashcard",
  "title": "Smart Flashcard",
  "emoji": "📚",
  "description": "Learn this word",
  "cefrLevel": "{level}",
  "estimatedSeconds": 12,
  "word": "word in {language}",
  "context": "where/how it's used",
  "explanation": "clear definition",
  "exampleSentence": "Example sentence in {language}",
  "tags": ["vocabulary"],
  "completed": false
}}"""
        },
        "native_check": {
            "description": "Does this sound natural to a native speaker?",
            "schema": """{{
  "id": "unique_id",
  "type": "native_check",
  "title": "Natural or Not?",
  "emoji": "🧠",
  "description": "Would a native say this?",
  "cefrLevel": "{level}",
  "estimatedSeconds": 12,
  "sentence": "A sentence in {language}",
  "isNatural": false,
  "correctedVersion": "The natural version (if not natural)",
  "explanation": "Why it sounds unnatural or why it's perfect",
  "tags": ["naturalness"],
  "completed": false
}}"""
        },
        "brain_tickler": {
            "description": "Timed challenge - 10 seconds to answer",
            "schema": """{{
  "id": "unique_id",
  "type": "brain_tickler",
  "title": "10-Second Challenge",
  "emoji": "⏱️",
  "description": "Beat the clock!",
  "cefrLevel": "{level}",
  "estimatedSeconds": 10,
  "timeLimit": 10,
  "question": "Quick question in {language}",
  "options": [
    {{"id": "opt1", "text": "option 1", "isCorrect": false}},
    {{"id": "opt2", "text": "option 2", "isCorrect": true}},
    {{"id": "opt3", "text": "option 3", "isCorrect": false}}
  ],
  "explanation": "Brief explanation",
  "tags": ["speed", "recall"],
  "completed": false
}}"""
        }
    }

    spec = type_specs[challenge_type]
    level_desc = level_descriptions[cefr_level]

    prompt = f"""You are an expert {language} language teacher creating learning challenges.

**Target Language:** {language_native} ({language})
**CEFR Level:** {cefr_level} ({level_desc})
**Challenge Type:** {challenge_type}

**Task:** Create {batch_size} diverse, high-quality {challenge_type} challenges for {cefr_level} level {language} learners.

**Challenge Description:** {spec['description']}

**Requirements:**
1. All text (sentences, questions, options, explanations) must be in {language_native} ({language})
2. Appropriate difficulty for {cefr_level} level
3. Cover diverse grammar/vocabulary topics appropriate for this level
4. Educational and practical
5. Each challenge must have a unique ID (format: {challenge_type[:2]}_{cefr_level.lower()}_{language[:2]}_XXXXX)
6. Natural, authentic {language} usage
7. Clear, helpful explanations

**JSON Schema per challenge:**
{spec['schema'].format(level=cefr_level, language=language_native)}

**Output Format:**
Return ONLY a valid JSON array with {batch_size} challenges. No markdown, no extra text.
Example:
[
  {{challenge_1}},
  {{challenge_2}},
  ...
  {{challenge_{batch_size}}}
]

**IMPORTANT:**
- Use authentic {language_native} language
- Ensure all content is in {language_native}, not English
- Make challenges educational and practical
- Vary the topics and difficulty within {cefr_level} level
- Return ONLY the JSON array, nothing else
"""

    return prompt


async def generate_challenges_batch(
    language: str,
    language_native: str,
    cefr_level: str,
    challenge_type: str,
    batch_size: int = 17
) -> list:
    """Generate a batch of challenges using GPT-4o"""

    try:
        print(f"      🤖 Calling GPT-4o for {batch_size} {challenge_type} challenges...")

        prompt = generate_challenge_prompt(language, language_native, cefr_level, challenge_type, batch_size)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {language} language teacher. Generate reference learning challenges. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,  # More creativity for variety
            max_tokens=4000
        )

        # Parse response
        content = response.choices[0].message.content.strip()

        # Remove markdown if present
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        # Parse JSON
        challenges = json.loads(content)

        if not isinstance(challenges, list):
            print(f"      ⚠️  Expected array, got {type(challenges)}")
            return []

        # Calculate cost (approximate)
        usage = response.usage
        input_cost = (usage.prompt_tokens / 1000) * 0.0025  # $2.50 per 1M input tokens
        output_cost = (usage.completion_tokens / 1000) * 0.01  # $10 per 1M output tokens
        total_cost = input_cost + output_cost

        progress["total_cost"] += total_cost

        print(f"      ✅ Generated {len(challenges)} challenges (cost: ${total_cost:.4f})")

        return challenges

    except json.JSONDecodeError as e:
        error_msg = f"JSON parse error for {language} {cefr_level} {challenge_type}: {str(e)}"
        print(f"      ❌ {error_msg}")
        progress["errors"].append(error_msg)
        return []

    except Exception as e:
        error_msg = f"Error generating {language} {cefr_level} {challenge_type}: {str(e)}"
        print(f"      ❌ {error_msg}")
        progress["errors"].append(error_msg)
        return []


async def generate_all_challenges():
    """Generate all multi-language reference challenges"""

    print("=" * 80)
    print("🌍 MULTI-LANGUAGE REFERENCE CHALLENGE GENERATOR")
    print("=" * 80)
    print(f"\n📅 Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"\n📋 Configuration:")
    print(f"   Languages: {len(LANGUAGES)} (dutch, spanish, german, french, portuguese)")
    print(f"   CEFR Levels: {len(CEFR_LEVELS)} (A1, A2, B1, B2, C1, C2)")
    print(f"   Challenge Types: {len(CHALLENGE_TYPES)}")
    print(f"   Per (type, level): {CHALLENGES_PER_TYPE_LEVEL} challenges")
    print(f"\n📊 Expected Output:")
    total_expected = len(LANGUAGES) * len(CEFR_LEVELS) * len(CHALLENGE_TYPES) * CHALLENGES_PER_TYPE_LEVEL
    print(f"   Total challenges: ~{total_expected}")
    print(f"   Per language: ~{len(CEFR_LEVELS) * len(CHALLENGE_TYPES) * CHALLENGES_PER_TYPE_LEVEL}")
    print(f"\n💰 Estimated Cost: $1.50 - $2.00")
    print(f"⏱️  Estimated Time: 1-2 hours\n")

    confirm = input("Continue with generation? (yes/no): ")
    if confirm.lower() != 'yes':
        print("\n❌ Generation cancelled.")
        return

    # Connect to MongoDB
    print("\n🔌 Connecting to MongoDB...")
    client_db = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    db = client_db[DATABASE_NAME]

    try:
        await client_db.admin.command('ping')
        print("   ✅ Connected\n")
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return

    reference_challenges = db.reference_challenges

    # Start generation
    print("=" * 80)
    print("🚀 STARTING GENERATION")
    print("=" * 80)

    for lang_code, lang_info in LANGUAGES.items():
        lang_native = lang_info["native"]
        lang_english = lang_info["english"]

        print(f"\n\n{'='*80}")
        print(f"🌍 LANGUAGE: {lang_english} ({lang_native})")
        print(f"{'='*80}\n")

        progress["by_language"][lang_code] = {
            "total": 0,
            "by_type": {}
        }

        for challenge_type in CHALLENGE_TYPES:
            print(f"\n  📝 Challenge Type: {challenge_type}")
            print(f"  {'-'*70}")

            type_challenges = []

            for cefr_level in CEFR_LEVELS:
                print(f"    🎯 Level: {cefr_level}")

                # Generate batch
                batch = await generate_challenges_batch(
                    lang_code,
                    lang_native,
                    cefr_level,
                    challenge_type,
                    CHALLENGES_PER_TYPE_LEVEL
                )

                if batch:
                    type_challenges.extend(batch)
                    await asyncio.sleep(1)  # Rate limiting

            # Insert batch into database
            if type_challenges:
                print(f"\n    💾 Inserting {len(type_challenges)} {challenge_type} challenges...")

                # Prepare documents
                documents = []
                for challenge in type_challenges:
                    doc = {
                        "language": lang_code,
                        "cefr_level": challenge.get("cefrLevel"),
                        "challenge_type": challenge_type,
                        "challenge_data": challenge,
                        "created_at": datetime.utcnow(),
                        "tags": challenge.get("tags", []) + [cefr_level, challenge_type, "reference"]
                    }
                    documents.append(doc)

                # Insert
                result = await reference_challenges.insert_many(documents)
                inserted = len(result.inserted_ids)

                print(f"    ✅ Inserted {inserted} documents")

                progress["total_generated"] += inserted
                progress["by_language"][lang_code]["total"] += inserted
                progress["by_language"][lang_code]["by_type"][challenge_type] = inserted

    # Final summary
    print("\n\n" + "=" * 80)
    print("🎉 GENERATION COMPLETE!")
    print("=" * 80)

    print(f"\n📊 Summary:")
    print(f"   Total challenges generated: {progress['total_generated']}")
    print(f"   Total cost: ${progress['total_cost']:.2f}")

    print(f"\n📋 By Language:")
    for lang_code, stats in progress["by_language"].items():
        lang_name = LANGUAGES[lang_code]["english"]
        print(f"   {lang_name}: {stats['total']} challenges")

    if progress["errors"]:
        print(f"\n⚠️  Errors encountered: {len(progress['errors'])}")
        for error in progress["errors"][:5]:
            print(f"   - {error}")

    # Save progress report
    report_file = f"generation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(progress, f, indent=2, default=str)

    print(f"\n💾 Report saved: {report_file}")

    # Verify database
    print(f"\n🔍 Verifying database...")
    for lang_code in LANGUAGES.keys():
        count = await reference_challenges.count_documents({"language": lang_code})
        print(f"   {LANGUAGES[lang_code]['english']}: {count} challenges")

    total_refs = await reference_challenges.count_documents({})
    print(f"\n   Total reference challenges: {total_refs}")
    print(f"   (Including existing 600 English = {total_refs} total)")

    print(f"\n✅ Multi-language reference challenges ready!")
    print(f"🎯 Ready to proceed to Phase 2 (CrewAI)\n")

    client_db.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🌍 MULTI-LANGUAGE REFERENCE CHALLENGE GENERATOR")
    print("=" * 80)
    print("\nThis script generates reference challenges for 6 languages.")
    print("\n📋 Languages to generate:")
    for lang_code, lang_info in LANGUAGES.items():
        print(f"   - {lang_info['english']} ({lang_info['native']})")

    print(f"\n📊 Total to generate:")
    print(f"   - 5 languages × 6 levels × 6 types × 17 each")
    print(f"   - ≈ 3,060 challenges")
    print(f"\n💰 Cost: $1.50 - $2.00")
    print(f"⏱️  Time: 1-2 hours")
    print(f"\n⚠️  Requires: OpenAI API key\n")

    asyncio.run(generate_all_challenges())
