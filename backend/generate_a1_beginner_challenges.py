"""
Generate TRUE A1 Beginner Challenges
=====================================
This script generates proper beginner-level A1 challenges using gpt-5.5-2026-04-23
based on research from Duolingo, Babbel, and CEFR A1 standards.

Key Features:
- Uses gpt-5.5-2026-04-23 for high-quality content
- TRUE beginner level (absolute basics)
- Randomized correct answer positions
- Based on Duolingo/Babbel beginner patterns
- Covers all 6 languages and 7 challenge types

Languages: English, Spanish, Dutch, German, French, Portuguese
Challenge Types: brain_tickler, micro_quiz, native_check, error_spotting, swipe_fix, story_builder, smart_flashcard
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from openai import OpenAI

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@66.33.22.252:44437/language_tutor?authSource=admin&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&socketTimeoutMS=60000&retryWrites=true&retryReads=true")
DATABASE_NAME = os.getenv("DATABASE_NAME", "language_tutor")

# OpenAI client
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("\n❌ ERROR: OPENAI_API_KEY not found in environment variables!")
    exit(1)

client = OpenAI(api_key=openai_key)
print(f"✅ OpenAI API key loaded")

# Configuration
LANGUAGES = {
    "english": {"native": "English", "english": "English"},
    "spanish": {"native": "Español", "english": "Spanish"},
    "dutch": {"native": "Nederlands", "english": "Dutch"},
    "german": {"native": "Deutsch", "english": "German"},
    "french": {"native": "Français", "english": "French"},
    "portuguese": {"native": "Português", "english": "Portuguese"}
}

CHALLENGE_TYPES = [
    "brain_tickler",
    "micro_quiz",
    "native_check",
    "error_spotting",
    "swipe_fix",
    "story_builder",
    "smart_flashcard"
]

# Generate more challenges per type to match the migrated A1 count
# We migrated ~400-500 per type, so let's generate similar amounts
CHALLENGES_PER_TYPE_LANGUAGE = 80  # 80 per (type, language) = ~480 total per type

# Progress tracking
progress = {
    "total_generated": 0,
    "total_cost": 0.0,
    "by_language": {},
    "errors": []
}


def generate_a1_challenge_prompt(language: str, language_native: str, challenge_type: str, batch_size: int = 20) -> str:
    """
    Generate GPT-5.5 prompt for creating TRUE BEGINNER A1 challenges

    CRITICAL: Emphasizes randomization and proper A1 difficulty
    """

    # A1 vocabulary topics (based on CEFR and Duolingo/Babbel research)
    a1_topics = """
    - Greetings and introductions (hello, goodbye, my name is)
    - Numbers 1-100
    - Colors (red, blue, green, yellow, etc.)
    - Family members (mother, father, sister, brother)
    - Basic objects (book, pen, table, chair, door, window)
    - Days of the week and months
    - Simple verbs (to be, to have, to go, to eat, to drink, to sleep)
    - Food and drinks (water, bread, apple, coffee, tea)
    - Time expressions (today, tomorrow, yesterday, now)
    - Weather (sun, rain, hot, cold)
    - Basic adjectives (big, small, good, bad, happy, sad)
    - Countries and nationalities
    - Simple prepositions (in, on, under, next to)
    - Common phrases (please, thank you, excuse me)
    """

    # A1 grammar topics
    a1_grammar = """
    - Present tense of basic verbs (I am, you are, he/she is)
    - Simple articles (a, an, the)
    - Basic plurals (book → books)
    - Subject pronouns (I, you, he, she, it, we, they)
    - Possessive adjectives (my, your, his, her)
    - Simple yes/no questions
    - Basic negation (I am not, he does not have)
    - Simple word order (Subject + Verb + Object)
    """

    # Challenge type specifications
    type_specs = {
        "error_spotting": {
            "description": "Find the grammatical error in a very simple sentence",
            "a1_examples": [
                "I am happy → I am happies (wrong plural)",
                "She have a book → She has a book (verb agreement)",
                "He is a doctor → He is doctor (missing article)"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "error_spotting",
  "title": "Spot the Mistake",
  "emoji": "🧩",
  "description": "Find the error",
  "cefrLevel": "A1",
  "estimatedSeconds": 12,
  "sentence": "Very simple sentence with ONE basic error in [LANGUAGE]",
  "options": [
    {"id": "opt1", "text": "word 1", "isCorrect": false},
    {"id": "opt2", "text": "word 2", "isCorrect": true},
    {"id": "opt3", "text": "word 3", "isCorrect": false}
  ],
  "explanation": "Brief explanation why it's wrong in [LANGUAGE]",
  "correctedSentence": "The correct version",
  "tags": ["basic_grammar"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Use ONLY A1 vocabulary and grammar
2. Sentences must be 4-8 words maximum
3. ONE obvious error only (article, verb form, basic plural, etc.)
4. RANDOMIZE which option is correct - NOT always option 1 or 2!
5. Each challenge should have the correct answer in different positions
6. Use present tense only
7. Avoid complex grammar - focus on basics
"""
        },

        "swipe_fix": {
            "description": "Compare wrong vs right usage of basic grammar/vocabulary",
            "a1_examples": [
                "Wrong: I am go → Right: I go",
                "Wrong: She have book → Right: She has a book"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "swipe_fix",
  "title": "Compare & Learn",
  "emoji": "🔄",
  "description": "Which is correct?",
  "cefrLevel": "A1",
  "estimatedSeconds": 15,
  "concept": "The basic grammar concept (e.g., 'verb to be', 'articles')",
  "examples": [
    {"text": "Wrong usage in [LANGUAGE]", "isCorrect": false, "explanation": "Why wrong"},
    {"text": "Correct usage in [LANGUAGE]", "isCorrect": true, "explanation": "Why right"}
  ],
  "tags": ["concept_tag"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Focus on ONE basic grammar concept per challenge
2. Use simple 3-6 word sentences
3. RANDOMIZE the order - sometimes correct is first, sometimes second
4. Don't always put the wrong answer first!
5. Clear contrast between wrong and right
6. Use only A1 vocabulary
"""
        },

        "micro_quiz": {
            "description": "Quick multiple choice question with basic vocabulary/grammar",
            "a1_examples": [
                "What color is the sun? (yellow/blue/green)",
                "I ___ a student. (am/is/are)"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "micro_quiz",
  "title": "Quick Quiz",
  "emoji": "⚡",
  "description": "Fast decision",
  "cefrLevel": "A1",
  "estimatedSeconds": 10,
  "question": "Simple question in [LANGUAGE]",
  "options": [
    {"id": "opt1", "text": "option 1", "isCorrect": false},
    {"id": "opt2", "text": "option 2", "isCorrect": true},
    {"id": "opt3", "text": "option 3", "isCorrect": false}
  ],
  "explanation": "Brief explanation",
  "tags": ["topic_tag"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Questions must be VERY simple (A1 level)
2. Use fill-in-the-blank OR simple comprehension questions
3. RANDOMIZE correct answer position - distribute across opt1, opt2, opt3
4. NEVER make opt2 always correct! Mix it up!
5. Use only basic vocabulary (numbers, colors, family, common objects)
6. Options should be clearly different
7. Avoid tricky questions - keep it straightforward for beginners
"""
        },

        "smart_flashcard": {
            "description": "Vocabulary flashcard with very basic words",
            "a1_examples": [
                "book (with example: I read a book)",
                "water (with example: I drink water)"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "smart_flashcard",
  "title": "Smart Flashcard",
  "emoji": "📚",
  "description": "Learn this word",
  "cefrLevel": "A1",
  "estimatedSeconds": 12,
  "word": "basic word in [LANGUAGE]",
  "context": "where/how it's used",
  "explanation": "clear, simple definition",
  "exampleSentence": "Very simple example sentence (3-6 words) in [LANGUAGE]",
  "tags": ["vocabulary"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Select ONLY the most basic, common A1 words
2. Words should be concrete (book, water, cat) not abstract
3. Example sentences must be 3-6 words, present tense
4. Use words from A1 core vocabulary (see list above)
5. Vary the word types: nouns, verbs, adjectives
6. No advanced vocabulary whatsoever
"""
        },

        "native_check": {
            "description": "Does this sound natural to a native speaker?",
            "a1_examples": [
                "Natural: Hello, my name is Maria",
                "Unnatural: Hello, name my is Maria"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "native_check",
  "title": "Natural or Not?",
  "emoji": "🧠",
  "description": "Would a native say this?",
  "cefrLevel": "A1",
  "estimatedSeconds": 12,
  "sentence": "A very simple sentence in [LANGUAGE]",
  "isNatural": false,
  "correctedVersion": "The natural version (if not natural)",
  "explanation": "Brief explanation in [LANGUAGE]",
  "tags": ["naturalness"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Use only basic A1 sentences (4-8 words)
2. RANDOMIZE isNatural - roughly 50% true, 50% false
3. Don't make all sentences unnatural!
4. Errors should be obvious (wrong word order, missing article)
5. Use common phrases beginners would encounter
6. Keep explanations very simple
"""
        },

        "brain_tickler": {
            "description": "Timed challenge - 10 seconds to answer basic question",
            "a1_examples": [
                "How many days in a week? (7/5/10)",
                "I ___ happy. (am/is/are)"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "brain_tickler",
  "title": "10-Second Challenge",
  "emoji": "⏱️",
  "description": "Beat the clock!",
  "cefrLevel": "A1",
  "estimatedSeconds": 10,
  "timeLimit": 10,
  "question": "Very simple quick question in [LANGUAGE]",
  "options": [
    {"id": "opt1", "text": "option 1", "isCorrect": false},
    {"id": "opt2", "text": "option 2", "isCorrect": true},
    {"id": "opt3", "text": "option 3", "isCorrect": false}
  ],
  "explanation": "Brief explanation",
  "tags": ["speed", "recall"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Questions must be INSTANT recall (numbers, colors, basic facts)
2. Answerable in 10 seconds even for absolute beginners
3. RANDOMIZE correct answer position - spread across opt1, opt2, opt3
4. Mix up the correct position in EVERY challenge
5. Use basic vocabulary only
6. Clear, unambiguous questions
7. Obvious correct answer (no tricks)
"""
        },

        "story_builder": {
            "description": "Fill-in-the-gaps story exercise where learners complete a short story by selecting words from a word bank",
            "a1_examples": [
                "Story: 'My name is Tom. I ___ a student. I have a ___ cat.' (Gaps: 'am', 'black')",
                "Story: 'Hello! I ___ Maria. I am from Spain. I like ___.' (Gaps: 'am', 'coffee')"
            ],
            "schema": """{
  "id": "unique_id",
  "type": "story_builder",
  "title": "Story Builder",
  "emoji": "📖",
  "description": "Complete the story",
  "cefrLevel": "A1",
  "estimatedSeconds": 45,
  "storyText": "Short story with ___ gaps for missing words",
  "gaps": [
    {
      "id": "gap1",
      "correctWord": "word1",
      "positionIndex": 0,
      "alternativeCorrectWords": []
    },
    {
      "id": "gap2",
      "correctWord": "word2",
      "positionIndex": 1,
      "alternativeCorrectWords": []
    }
  ],
  "wordBank": [
    "word1",
    "word2",
    "distractor1",
    "distractor2",
    "distractor3",
    "distractor4"
  ],
  "explanation": "Brief explanation of the story and grammar in [LANGUAGE]",
  "tags": ["story_builder"],
  "completed": false
}""",
            "instructions": """
CRITICAL INSTRUCTIONS:
1. Stories must be 2-4 sentences (20-40 words total)
2. Use only present tense
3. Only basic A1 vocabulary (hello, I am, my name is, I have, colors, numbers, family, food)
4. Each story has EXACTLY 2 gaps marked with ___
5. Word bank should have 6-8 words total (2 correct + 4-6 distractors)
6. Stories about simple topics: greetings, family, daily life, food, colors
7. Very simple grammar (verb to be, basic present tense, articles)
8. storyText must have exactly 2 gaps marked with ___
9. gaps array must have exactly 2 gap objects
10. Each gap must have: id, correctWord, positionIndex (0 or 1), alternativeCorrectWords (empty array for A1)
11. wordBank must include ALL correct words + distractors
12. Distractors should be similar words but grammatically wrong
13. Keep stories VERY simple - absolute beginner level
"""
        }
    }

    spec = type_specs[challenge_type]

    prompt = f"""You are an expert {language} language teacher creating ABSOLUTE BEGINNER (A1 CEFR level) learning challenges.

**CRITICAL: TRUE BEGINNER LEVEL**
This is for students who know ZERO or almost ZERO {language}. Think Duolingo Lesson 1-5.

**Target Language:** {language_native} ({language})
**CEFR Level:** A1 (Absolute Beginner)
**Challenge Type:** {challenge_type}

**Task:** Create {batch_size} diverse, high-quality {challenge_type} challenges for TRUE A1 beginners.

**A1 VOCABULARY TOPICS YOU MUST USE:**
{a1_topics}

**A1 GRAMMAR TOPICS YOU MUST USE:**
{a1_grammar}

**Challenge Description:** {spec['description']}

**A1 Examples:**
{chr(10).join(f"- {ex}" for ex in spec['a1_examples'])}

**CRITICAL REQUIREMENTS - READ CAREFULLY:**

{spec['instructions']}

**RANDOMIZATION REQUIREMENTS (VERY IMPORTANT):**
- For multiple choice questions: Distribute correct answers randomly across all options
- Challenge 1 might have correct answer at position 1
- Challenge 2 might have correct answer at position 2
- Challenge 3 might have correct answer at position 3
- DO NOT make a pattern (like always option 2)
- For story_builder: Randomize the word array order completely - don't use alphabetical or logical order
- For native_check: Mix true/false roughly 50/50
- For swipe_fix: Sometimes correct example first, sometimes second

**A1 DIFFICULTY CHECKLIST:**
✓ Sentences are 3-8 words maximum
✓ Only present tense (avoid past/future)
✓ Only core A1 vocabulary (see lists above)
✓ Only basic grammar (articles, verb to be, simple plurals, basic negation)
✓ No idioms, no slang, no complex structures
✓ Clear and obvious (no tricks)

**JSON Schema per challenge:**
{spec['schema'].replace('[LANGUAGE]', language_native)}

**Output Format:**
Return ONLY a valid JSON array with {batch_size} challenges. No markdown, no extra text.

[
  {{challenge_1}},
  {{challenge_2}},
  ...
  {{challenge_{batch_size}}}
]

**FINAL REMINDERS:**
1. TRUE BEGINNER level - think "Day 1 learner"
2. RANDOMIZE correct answer positions
3. Use ONLY {language_native} for all content
4. Keep it SIMPLE and CLEAR
5. Vary topics within A1 scope
6. Return ONLY JSON array
"""

    return prompt


async def generate_challenges_batch(
    language: str,
    language_native: str,
    challenge_type: str,
    batch_size: int = 20
) -> list:
    """Generate a batch of A1 challenges using gpt-5.5-2026-04-23"""

    try:
        print(f"      🤖 Calling gpt-5.5-2026-04-23 for {batch_size} {challenge_type} challenges...")

        prompt = generate_a1_challenge_prompt(language, language_native, challenge_type, batch_size)

        # GPT-5.5 with minimal parameters (uses default temperature=1)
        response = client.chat.completions.create(
            model="gpt-5.5-2026-04-23",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {language} language teacher specializing in absolute beginner (A1 CEFR) content. You create challenges similar to Duolingo and Babbel beginner lessons. You ALWAYS randomize correct answer positions. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
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

        # Calculate cost (GPT-5.5 pricing: $5/1M input, $30/1M output)
        usage = response.usage
        input_cost = (usage.prompt_tokens / 1_000_000) * 5.0  # $5 per 1M input tokens
        output_cost = (usage.completion_tokens / 1_000_000) * 30.0  # $30 per 1M output tokens
        total_cost = input_cost + output_cost

        progress["total_cost"] += total_cost

        print(f"      ✅ Generated {len(challenges)} challenges (cost: ${total_cost:.4f})")

        return challenges

    except json.JSONDecodeError as e:
        error_msg = f"JSON parse error for {language} {challenge_type}: {str(e)}"
        print(f"      ❌ {error_msg}")
        progress["errors"].append(error_msg)
        return []

    except Exception as e:
        error_msg = f"Error generating {language} {challenge_type}: {str(e)}"
        print(f"      ❌ {error_msg}")
        progress["errors"].append(error_msg)
        return []


async def generate_all_a1_challenges():
    """Generate all A1 challenges for all languages and types"""

    print("=" * 80)
    print("🌟 GENERATE TRUE A1 BEGINNER CHALLENGES")
    print("=" * 80)
    print(f"\n📅 Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"\n🤖 Model: gpt-5.5-2026-04-23")
    print(f"\n📋 Configuration:")
    print(f"   Languages: {len(LANGUAGES)} ({', '.join(LANGUAGES.keys())})")
    print(f"   Challenge Types: {len(CHALLENGE_TYPES)}")
    print(f"   Per (type, language): {CHALLENGES_PER_TYPE_LANGUAGE} challenges")

    total_expected = len(LANGUAGES) * len(CHALLENGE_TYPES) * CHALLENGES_PER_TYPE_LANGUAGE
    print(f"\n📊 Expected Output:")
    print(f"   Total challenges: ~{total_expected}")
    print(f"   Per language: ~{len(CHALLENGE_TYPES) * CHALLENGES_PER_TYPE_LANGUAGE}")
    print(f"\n💰 Estimated Cost: $15-25 (GPT-5.5 pricing)")
    print(f"⏱️  Estimated Time: 2-3 hours\n")

    confirm = input("Continue with generation? (yes/no): ")
    if confirm.lower() != 'yes':
        print("\n❌ Generation cancelled.")
        return

    # Connect to MongoDB
    print("\n🔌 Connecting to MongoDB...")
    client_db = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
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

            # Generate in batches of 20
            num_batches = (CHALLENGES_PER_TYPE_LANGUAGE + 19) // 20  # Round up

            for batch_num in range(num_batches):
                batch_size = min(20, CHALLENGES_PER_TYPE_LANGUAGE - len(type_challenges))
                if batch_size <= 0:
                    break

                print(f"    📦 Batch {batch_num + 1}/{num_batches} (size: {batch_size})")

                batch = await generate_challenges_batch(
                    lang_code,
                    lang_native,
                    challenge_type,
                    batch_size
                )

                if batch:
                    type_challenges.extend(batch)
                    await asyncio.sleep(2)  # Rate limiting

            # Insert batch into database
            if type_challenges:
                print(f"\n    💾 Inserting {len(type_challenges)} {challenge_type} challenges...")

                # Prepare documents
                documents = []
                for challenge in type_challenges:
                    doc = {
                        "language": lang_code,
                        "cefr_level": "A1",
                        "challenge_type": challenge_type,
                        "challenge_data": challenge,
                        "created_at": datetime.utcnow(),
                        "generated_by": "gpt-5.5-2026-04-23",
                        "is_true_beginner": True,
                        "tags": challenge.get("tags", []) + ["A1", challenge_type, "reference", "true_beginner"]
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
        for ctype, count in stats['by_type'].items():
            print(f"      {ctype}: {count}")

    if progress["errors"]:
        print(f"\n⚠️  Errors encountered: {len(progress['errors'])}")
        for error in progress["errors"][:10]:
            print(f"   - {error}")

    # Save progress report
    report_file = f"a1_generation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(progress, f, indent=2, default=str)

    print(f"\n💾 Report saved: {report_file}")

    # Verify database
    print(f"\n🔍 Verifying database...")
    total_a1 = await reference_challenges.count_documents({"cefr_level": "A1"})
    print(f"   Total A1 challenges in database: {total_a1}")

    for lang_code in LANGUAGES.keys():
        count = await reference_challenges.count_documents({
            "language": lang_code,
            "cefr_level": "A1"
        })
        print(f"   {LANGUAGES[lang_code]['english']} A1: {count} challenges")

    print(f"\n✅ TRUE A1 beginner challenges ready!")
    print(f"🎯 A1 learners now have proper beginner-level content!\n")

    client_db.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🌟 GENERATE TRUE A1 BEGINNER CHALLENGES")
    print("=" * 80)
    print("\nThis script generates proper beginner-level A1 challenges")
    print("using gpt-5.5-2026-04-23 based on Duolingo/Babbel patterns.")
    print("\n✨ Key Features:")
    print("   - TRUE beginner level (absolute basics)")
    print("   - Randomized correct answer positions")
    print("   - Based on CEFR A1 standards")
    print("   - Similar to Duolingo/Babbel beginner content")
    print(f"\n📊 Will generate:")
    print(f"   - {len(LANGUAGES)} languages")
    print(f"   - {len(CHALLENGE_TYPES)} challenge types")
    print(f"   - {CHALLENGES_PER_TYPE_LANGUAGE} per (type, language)")
    print(f"   - Total: ~{len(LANGUAGES) * len(CHALLENGE_TYPES) * CHALLENGES_PER_TYPE_LANGUAGE} challenges")
    print(f"\n💰 Cost: $15-25")
    print(f"⏱️  Time: 2-3 hours")
    print(f"🤖 Model: gpt-5.5-2026-04-23\n")

    asyncio.run(generate_all_a1_challenges())
