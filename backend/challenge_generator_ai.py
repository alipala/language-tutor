"""
AI-Powered Challenge Generator
100% dynamically generated challenges based on user's actual learning data
Uses GPT-4 to create personalized challenges every 24 hours
"""

import os
import json
import random
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from database import database

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def analyze_user_learning_data(user_id: str, language: str = "english") -> Dict[str, Any]:
    """
    Deep analysis of user's learning history to extract:
    - Common mistakes and error patterns
    - Weak vocabulary areas
    - Grammar struggles
    - Learning plan focus areas

    Args:
        user_id: User ID
        language: Target language (default: "english")

    Returns comprehensive analysis for AI prompt
    """
    analysis = {
        "user_id": user_id,
        "language": language,
        "level": "B1",
        "common_mistakes": [],
        "weak_vocabulary": [],
        "grammar_struggles": [],
        "learning_plan_topics": [],
        "session_summaries": []
    }

    try:
        # 1. Get user's CEFR level
        from bson import ObjectId

        # Handle special case: reference_user (for generating generic challenges)
        if user_id == "reference_user":
            # Skip user lookup, use provided level
            pass
        else:
            # Normal user lookup
            user = await database.users.find_one({"_id": ObjectId(user_id)})
            if user:
                analysis["level"] = user.get("preferred_level", "B1") or "B1"

        # 2. Extract mistakes from recent practice sessions (filter by language!)
        sessions_collection = database.conversation_sessions
        recent_sessions = await sessions_collection.find({
            "user_id": user_id,
            "language": language,
            "enhanced_analysis": {"$exists": True}
        }).sort("created_at", -1).limit(10).to_list(length=10)

        for session in recent_sessions:
            enhanced = session.get("enhanced_analysis") or {}
            insights = enhanced.get("insights", {})

            # Grammar issues
            grammar_points = insights.get("grammar_to_review", [])
            for point in grammar_points:
                analysis["common_mistakes"].append({
                    "type": "grammar",
                    "category": point.get("category", "general"),
                    "example": point.get("example", ""),
                    "explanation": point.get("explanation", "")
                })

            # Vocabulary suggestions
            vocab_suggestions = insights.get("vocabulary_to_learn", [])
            for vocab in vocab_suggestions:
                analysis["weak_vocabulary"].append({
                    "word": vocab.get("word", ""),
                    "context": vocab.get("context", ""),
                    "definition": vocab.get("definition", "")
                })

            # Session summary for context
            summary = session.get("summary", "")
            if summary:
                analysis["session_summaries"].append(summary)

        # 3. Get weak flashcards (filter by language!)
        flashcards_collection = database.flashcards
        weak_cards = await flashcards_collection.find({
            "user_id": user_id,
            "language": language,
            "mastery_level": {"$lt": 0.5},
            "is_active": True
        }).limit(10).to_list(length=10)

        for card in weak_cards:
            analysis["weak_vocabulary"].append({
                "word": card.get("front", ""),
                "context": card.get("category", ""),
                "definition": card.get("back", "")
            })

        # 4. Get learning plan focus areas (filter by language!)
        learning_plans_collection = database.learning_plans
        learning_plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "language": language
        }, sort=[("updated_at", -1)])

        if learning_plan:
            plan_content = learning_plan.get("plan_content", {})
            weekly_schedule = plan_content.get("weekly_schedule", [])

            # Get last 3 weeks of topics
            for week in weekly_schedule[-3:]:
                focus = week.get("focus", "")
                if focus:
                    analysis["learning_plan_topics"].append(focus)

        # Deduplicate and limit
        analysis["common_mistakes"] = analysis["common_mistakes"][:10]
        analysis["weak_vocabulary"] = analysis["weak_vocabulary"][:10]
        analysis["learning_plan_topics"] = list(set(analysis["learning_plan_topics"]))[:5]

        print(f"[AI_CHALLENGE] 📊 User analysis complete:")
        print(f"  - Mistakes: {len(analysis['common_mistakes'])}")
        print(f"  - Weak vocab: {len(analysis['weak_vocabulary'])}")
        print(f"  - Learning topics: {len(analysis['learning_plan_topics'])}")
        print(f"  - Recent sessions: {len(analysis['session_summaries'])}")

        return analysis

    except Exception as e:
        print(f"[AI_CHALLENGE] ❌ Error analyzing user data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return analysis


def build_challenge_generation_prompt(user_analysis: Dict[str, Any]) -> str:
    """
    Build GPT-4 prompt to generate 6 personalized challenges
    Based on user's actual learning data
    """

    level = user_analysis.get("level", "B1")
    language = user_analysis.get("language", "english")
    mistakes = user_analysis.get("common_mistakes", [])
    vocab = user_analysis.get("weak_vocabulary", [])
    topics = user_analysis.get("learning_plan_topics", [])

    # Capitalize language name for prompt
    language_display = language.capitalize()

    prompt = f"""You are an expert language learning AI. Generate 6 personalized daily challenges for a {level} level {language_display} learner.

**User's Learning Data:**

Common Mistakes:
{json.dumps(mistakes[:5], indent=2) if mistakes else "No data yet"}

Weak Vocabulary:
{json.dumps(vocab[:5], indent=2) if vocab else "No data yet"}

Learning Plan Topics:
{json.dumps(topics, indent=2) if topics else "No data yet"}

**Required Output:**
Generate exactly 6 challenges (one of each type below). Base them on the user's actual mistakes and weak areas above.

**Challenge Types:**

1. **error_spotting**: Create a sentence with a grammar mistake the user commonly makes. Provide 3 options to identify the error.

2. **swipe_fix**: Show the user's typical mistake vs the correct version. Use their actual error patterns.

3. **micro_quiz**: Quick multiple choice about grammar/vocabulary they struggle with.

4. **smart_flashcard**: Review a word they found difficult (from weak vocabulary list).

5. **native_check**: Test if a sentence sounds natural. Use patterns from their mistakes.

6. **brain_tickler**: Timed challenge (10 seconds) on a concept they need to practice.

**JSON Output Format:**
Return ONLY valid JSON array (no markdown, no extra text):

[
  {{
    "id": "unique_id_1",
    "type": "error_spotting",
    "title": "Spot the Mistake",
    "emoji": "🧩",
    "description": "From your recent practice",
    "cefrLevel": "{level}",
    "estimatedSeconds": 12,
    "sentence": "The actual sentence with error",
    "options": [
      {{"id": "opt1", "text": "error part", "isCorrect": true}},
      {{"id": "opt2", "text": "correct part", "isCorrect": false}},
      {{"id": "opt3", "text": "another correct part", "isCorrect": false}}
    ],
    "explanation": "Why this is wrong and how to fix it",
    "correctedSentence": "The correct version",
    "tags": ["relevant", "tags"],
    "completed": false
  }},
  {{
    "id": "unique_id_2",
    "type": "swipe_fix",
    "title": "You Struggled With This",
    "emoji": "🔄",
    "description": "Compare and learn",
    "cefrLevel": "{level}",
    "estimatedSeconds": 15,
    "concept": "The concept being taught",
    "examples": [
      {{"text": "Your typical mistake", "isCorrect": false, "explanation": "Why it's wrong"}},
      {{"text": "The correct version", "isCorrect": true, "explanation": "Why it's right"}}
    ],
    "tags": ["relevant", "tags"],
    "completed": false
  }},
  {{
    "id": "unique_id_3",
    "type": "micro_quiz",
    "title": "Quick Quiz",
    "emoji": "⚡",
    "description": "Fast decision",
    "cefrLevel": "{level}",
    "estimatedSeconds": 10,
    "question": "The question text",
    "options": [
      {{"id": "opt1", "text": "option 1", "isCorrect": false}},
      {{"id": "opt2", "text": "option 2", "isCorrect": true}},
      {{"id": "opt3", "text": "option 3", "isCorrect": false}}
    ],
    "explanation": "Why option 2 is correct",
    "tags": ["relevant", "tags"],
    "completed": false
  }},
  {{
    "id": "unique_id_4",
    "type": "smart_flashcard",
    "title": "Smart Flashcard",
    "emoji": "📚",
    "description": "Review this word",
    "cefrLevel": "{level}",
    "estimatedSeconds": 12,
    "word": "word from weak vocabulary",
    "context": "where it's used",
    "explanation": "clear definition",
    "exampleSentence": "Example using the word naturally",
    "tags": ["vocabulary"],
    "completed": false
  }},
  {{
    "id": "unique_id_5",
    "type": "native_check",
    "title": "Would a Native Say This?",
    "emoji": "🧠",
    "description": "Natural or not?",
    "cefrLevel": "{level}",
    "estimatedSeconds": 12,
    "sentence": "A sentence that may or may not be natural",
    "isNatural": false,
    "correctedVersion": "The natural version if not natural",
    "explanation": "Why it sounds unnatural or why it's perfect",
    "tags": ["naturalness"],
    "completed": false
  }},
  {{
    "id": "unique_id_6",
    "type": "brain_tickler",
    "title": "10-Second Challenge",
    "emoji": "⏱️",
    "description": "Beat the clock!",
    "cefrLevel": "{level}",
    "estimatedSeconds": 10,
    "timeLimit": 10,
    "question": "Quick question on a weak area",
    "options": [
      {{"id": "opt1", "text": "option 1", "isCorrect": false}},
      {{"id": "opt2", "text": "option 2", "isCorrect": true}},
      {{"id": "opt3", "text": "option 3", "isCorrect": false}}
    ],
    "explanation": "Brief explanation",
    "tags": ["speed", "recall"],
    "completed": false
  }}
]

**IMPORTANT:**
- Use unique IDs (e.g., "ai_es_123", "ai_sf_456")
- Base challenges on the user's ACTUAL mistakes and weak vocabulary above
- Make them personalized and relevant to their learning journey
- If no user data, create level-appropriate generic challenges
- Return ONLY the JSON array, nothing else
"""

    return prompt


async def generate_challenges_with_ai(user_id: str, user_level: str, language: str = "english") -> List[Dict[str, Any]]:
    """
    Use GPT-4 to generate 6 personalized challenges based on user's learning data

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        language: Target language (default: "english")

    Returns:
        List of 6 AI-generated challenges
    """
    try:
        print(f"[AI_CHALLENGE] 🤖 Generating AI challenges for user {user_id} (language: {language}, level: {user_level})")

        # Step 1: Analyze user's learning data
        user_analysis = await analyze_user_learning_data(user_id, language)
        user_analysis["level"] = user_level
        user_analysis["language"] = language

        # Step 2: Build prompt
        prompt = build_challenge_generation_prompt(user_analysis)

        # Step 3: Call GPT-4 to generate challenges
        print(f"[AI_CHALLENGE] 📡 Calling GPT-4 for challenge generation...")

        response = client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4o for better JSON output
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert language learning content creator. Generate personalized challenges. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Some creativity for variety
            max_tokens=4000
        )

        # Parse response
        content = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        print(f"[AI_CHALLENGE] Raw response length: {len(content)} chars")

        # Handle both wrapped and unwrapped JSON
        if content.startswith('['):
            challenges = json.loads(content)
        elif content.startswith('{'):
            # If GPT wrapped it in an object, extract the array
            parsed = json.loads(content)
            # Try multiple possible keys
            challenges = (parsed.get("challenges") or
                         parsed.get("daily_challenges") or
                         parsed.get("data") or
                         list(parsed.values())[0] if parsed.values() else [])
        else:
            print(f"[AI_CHALLENGE] ⚠️ Unexpected response format: {content[:100]}")
            challenges = []

        if not isinstance(challenges, list) or len(challenges) != 6:
            print(f"[AI_CHALLENGE] ⚠️ Expected 6 challenges, got {len(challenges) if isinstance(challenges, list) else 'invalid'}")
            # Ensure we have exactly 6
            if isinstance(challenges, list):
                challenges = challenges[:6]  # Truncate if too many

        print(f"[AI_CHALLENGE] ✅ Generated {len(challenges)} AI challenges")

        # Add metadata and ensure unique IDs
        for challenge in challenges:
            # Generate globally unique ID by appending UUID
            # Keep original ID as base, add unique suffix
            original_id = challenge.get("id", "challenge")
            unique_id = f"{original_id}_{uuid.uuid4().hex[:8]}"
            challenge["id"] = unique_id

            challenge["language"] = language
            challenge["generated_at"] = datetime.utcnow().isoformat()
            challenge["source"] = "ai_generated"

        return challenges

    except Exception as e:
        print(f"[AI_CHALLENGE] ❌ Error generating AI challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())

        # Fallback: Return empty list (will be handled by caller)
        return []


async def get_or_generate_daily_challenges(user_id: str, user_level: str, language: str = "english") -> List[Dict[str, Any]]:
    """
    Main function: Get cached challenges or generate new ones with AI

    - Checks 24h cache first
    - If no cache, generates 6 new AI challenges
    - Caches for 24 hours

    Args:
        user_id: User ID
        user_level: CEFR level
        language: Target language (default: "english")

    Returns:
        List of 6 challenges (cached or freshly generated)
    """
    try:
        # Check cache first (filter by language!)
        cache_collection = database.daily_challenges_cache
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        cached = await cache_collection.find_one({
            "user_id": user_id,
            "language": language,
            "date": today_start
        })

        if cached:
            print(f"[AI_CHALLENGE] ✅ Found cached challenges for today")
            return cached.get("challenges", [])

        # No cache - generate new AI challenges
        print(f"[AI_CHALLENGE] 🆕 Generating new daily challenges with AI for language: {language}...")

        challenges = await generate_challenges_with_ai(user_id, user_level, language)

        if not challenges or len(challenges) == 0:
            print(f"[AI_CHALLENGE] ⚠️ AI generation failed, returning empty")
            return []

        # Cache for 24 hours
        cache_doc = {
            "user_id": user_id,
            "language": language,
            "date": today_start,
            "challenges": challenges,
            "created_at": datetime.utcnow(),
            "generation_method": "ai",
            "level": user_level
        }

        # Create TTL index if not exists
        await cache_collection.create_index("created_at", expireAfterSeconds=24*60*60)

        # Insert cache
        await cache_collection.insert_one(cache_doc)

        print(f"[AI_CHALLENGE] ✅ Cached {len(challenges)} challenges for 24h")

        return challenges

    except Exception as e:
        print(f"[AI_CHALLENGE] ❌ Error in get_or_generate_daily_challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []
