"""
IMPROVED AI-Powered Challenge Generator
========================================
High-quality challenge generation with:
1. Explicit answer randomization
2. Detailed CEFR level guidelines
3. Better quality validation
4. Support for GPT-4o and newer models
"""

import os
import json
import random
import uuid
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Model configuration - easily upgradeable
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")  # Can be changed to gpt-4.5 when available

# CEFR Level Guidelines
CEFR_GUIDELINES = {
    "A1": {
        "description": "Beginner - Basic words and simple phrases",
        "grammar": "Present simple, basic pronouns, singular/plural, common verbs (be, have, go)",
        "vocabulary": "Numbers, colors, family, food, daily activities (200-300 words)",
        "sentences": "Very short (3-6 words), simple structure",
        "examples": "I am happy. She has a cat. They go to school."
    },
    "A2": {
        "description": "Elementary - Simple everyday expressions",
        "grammar": "Past simple, future with 'going to', basic prepositions, comparatives",
        "vocabulary": "Personal info, shopping, work, hobbies (400-600 words)",
        "sentences": "Short (5-10 words), simple compound sentences",
        "examples": "I went to the park yesterday. She is going to study tomorrow."
    },
    "B1": {
        "description": "Intermediate - Clear standard speech on familiar matters",
        "grammar": "Present perfect, conditionals (type 1), passive voice (simple), relative clauses",
        "vocabulary": "Travel, current events, opinions, feelings (1000-1500 words)",
        "sentences": "Medium length (8-15 words), some complex structures",
        "examples": "I have lived here for five years. If it rains, we will stay home."
    },
    "B2": {
        "description": "Upper Intermediate - Detailed text on wide range of subjects",
        "grammar": "All tenses, conditionals (type 2, 3), reported speech, subjunctive",
        "vocabulary": "Abstract concepts, professional topics, idioms (2000-2500 words)",
        "sentences": "Longer (12-20 words), complex and compound-complex",
        "examples": "Having finished the project, she decided to celebrate. I wish I had known earlier."
    },
    "C1": {
        "description": "Advanced - Fluent and sophisticated language use",
        "grammar": "Advanced structures, inversion, cleft sentences, subtle tense nuances",
        "vocabulary": "Specialized terminology, nuanced expressions, colloquialisms (3000-4000 words)",
        "sentences": "Long and complex (15-25+ words), sophisticated",
        "examples": "Rarely had she encountered such a perplexing situation. Not only did he arrive late, but he also forgot the documents."
    },
    "C2": {
        "description": "Mastery - Near-native fluency and precision",
        "grammar": "All advanced structures, subtle semantic distinctions, stylistic variations",
        "vocabulary": "Extensive and precise, including rare and archaic terms (5000+ words)",
        "sentences": "Very complex, nuanced, with sophisticated rhetoric",
        "examples": "Notwithstanding the overwhelming evidence to the contrary, he persisted in his erroneous beliefs."
    }
}

# Challenge type specific instructions
CHALLENGE_TYPE_INSTRUCTIONS = {
    "error_spotting": """Create a sentence with ONE grammatical error that is appropriate for the level.
The error should be:
- Common for learners at this level
- Clear and unambiguous
- Related to grammar rules for this CEFR level
- Realistic (something a learner might actually write)

Provide exactly 3 options: the error, and 2 correct parts.
IMPORTANT: The correct answer should be placed RANDOMLY (not always first or second).""",

    "swipe_fix": """Show a common mistake vs the correct version.
- Use real mistakes learners make at this level
- Provide clear explanations for both versions
- Ensure the "incorrect" version is actually wrong (verify!)
- Focus on grammar, not style preferences
- Both examples should be at the appropriate CEFR level""",

    "micro_quiz": """Create a quick multiple-choice question about grammar or vocabulary.
- Question should test knowledge appropriate for the level
- Provide exactly 3 options (all plausible for learners)
- IMPORTANT: Randomize which position (1, 2, or 3) contains the correct answer
- Make all options similar enough to be challenging
- Clear, unambiguous correct answer""",

    "smart_flashcard": """Present a vocabulary word appropriate for the CEFR level.
- Choose words from the typical vocabulary range for this level
- Provide clear definition and context
- Example sentence should demonstrate natural usage
- Word should be useful and practical""",

    "native_check": """Present a sentence and ask if it sounds natural to native speakers.
- For natural sentences: use common, idiomatic expressions
- For unnatural sentences: show subtle errors or awkward phrasing (not grammar errors)
- The unnaturalness should be appropriate to detect at this level
- Provide the natural alternative if unnatural""",

    "brain_tickler": """Create a 10-second timed challenge.
- Quick to answer but requires recall
- Test practical knowledge for the level
- Provide exactly 3 options
- IMPORTANT: Randomize the position of the correct answer
- Should be answerable in 5-10 seconds"""
}


def get_level_appropriate_prompt_enhancement(level: str) -> str:
    """Get detailed CEFR level guidelines for the prompt"""
    if level not in CEFR_GUIDELINES:
        level = "B1"  # Default fallback

    guide = CEFR_GUIDELINES[level]

    return f"""
**CEFR {level} LEVEL REQUIREMENTS:**

{guide['description']}

Grammar scope: {guide['grammar']}
Vocabulary scope: {guide['vocabulary']}
Sentence complexity: {guide['sentences']}

Example sentences for {level}:
{guide['examples']}

CRITICAL: All content MUST match {level} level. Do not use grammar or vocabulary from higher levels.
"""


def build_improved_challenge_prompt(
    level: str,
    language: str,
    user_analysis: Dict[str, Any] = None
) -> str:
    """Build improved GPT prompt with quality guidelines"""

    language_display = language.capitalize()
    level_guidelines = get_level_appropriate_prompt_enhancement(level)

    # User context (if available)
    user_context = ""
    if user_analysis:
        mistakes = user_analysis.get("common_mistakes", [])
        vocab = user_analysis.get("weak_vocabulary", [])
        topics = user_analysis.get("learning_plan_topics", [])

        if mistakes or vocab or topics:
            user_context = f"""
**USER'S LEARNING CONTEXT:**

Common Mistakes:
{json.dumps(mistakes[:5], indent=2) if mistakes else "No specific data - create general challenges"}

Weak Vocabulary:
{json.dumps(vocab[:5], indent=2) if vocab else "No specific data - create general challenges"}

Recent Topics:
{json.dumps(topics, indent=2) if topics else "No specific data - create general challenges"}

Use this context to personalize challenges when possible, but prioritize quality and accuracy.
"""

    prompt = f"""You are an expert {language_display} language teacher creating high-quality learning challenges.

{level_guidelines}

{user_context}

**YOUR TASK:**
Generate exactly 6 challenges (one of each type below) for {level} level {language_display} learners.

**CRITICAL QUALITY REQUIREMENTS:**

1. **ACCURACY**: All content must be 100% grammatically correct in {language_display}
2. **LEVEL APPROPRIATENESS**: Strictly adhere to {level} level vocabulary and grammar
3. **ANSWER RANDOMIZATION**: For multiple choice, randomly vary which option (1, 2, or 3) is correct
4. **NATURAL LANGUAGE**: Use authentic, natural {language_display} that native speakers actually use
5. **CLEAR EXPLANATIONS**: Provide educational explanations that help learners understand
6. **CULTURAL APPROPRIATENESS**: Avoid cultural stereotypes or inappropriate content

**CHALLENGE TYPES:**

1. **error_spotting**
{CHALLENGE_TYPE_INSTRUCTIONS["error_spotting"]}

2. **swipe_fix**
{CHALLENGE_TYPE_INSTRUCTIONS["swipe_fix"]}

3. **micro_quiz**
{CHALLENGE_TYPE_INSTRUCTIONS["micro_quiz"]}

4. **smart_flashcard**
{CHALLENGE_TYPE_INSTRUCTIONS["smart_flashcard"]}

5. **native_check**
{CHALLENGE_TYPE_INSTRUCTIONS["native_check"]}

6. **brain_tickler**
{CHALLENGE_TYPE_INSTRUCTIONS["brain_tickler"]}

**JSON OUTPUT FORMAT:**

Return ONLY a valid JSON array (no markdown, no extra text). Each challenge must match this schema:

[
  {{
    "id": "unique_id_1",
    "type": "error_spotting",
    "title": "Spot the Mistake",
    "emoji": "🧩",
    "description": "Find the error",
    "cefrLevel": "{level}",
    "estimatedSeconds": 12,
    "sentence": "The sentence with an error",
    "options": [
      {{"id": "opt1", "text": "part A", "isCorrect": false}},
      {{"id": "opt2", "text": "part B (error)", "isCorrect": true}},
      {{"id": "opt3", "text": "part C", "isCorrect": false}}
    ],
    "explanation": "Why this is wrong and how to fix it",
    "correctedSentence": "The correct version",
    "tags": ["relevant", "tags"],
    "completed": false
  }},
  {{
    "id": "unique_id_2",
    "type": "swipe_fix",
    "title": "Compare & Learn",
    "emoji": "🔄",
    "description": "Which is correct?",
    "cefrLevel": "{level}",
    "estimatedSeconds": 15,
    "concept": "The grammar concept",
    "examples": [
      {{"text": "Incorrect version", "isCorrect": false, "explanation": "Why it's wrong"}},
      {{"text": "Correct version", "isCorrect": true, "explanation": "Why it's right"}}
    ],
    "tags": ["relevant", "tags"],
    "completed": false
  }},
  {{
    "id": "unique_id_3",
    "type": "micro_quiz",
    "title": "Quick Quiz",
    "emoji": "⚡",
    "description": "Test your knowledge",
    "cefrLevel": "{level}",
    "estimatedSeconds": 10,
    "question": "The question",
    "options": [
      {{"id": "opt1", "text": "option 1", "isCorrect": false}},
      {{"id": "opt2", "text": "option 2", "isCorrect": false}},
      {{"id": "opt3", "text": "option 3", "isCorrect": true}}
    ],
    "explanation": "Why option 3 is correct",
    "tags": ["relevant", "tags"],
    "completed": false
  }},
  {{
    "id": "unique_id_4",
    "type": "smart_flashcard",
    "title": "Vocabulary Review",
    "emoji": "📚",
    "description": "Learn this word",
    "cefrLevel": "{level}",
    "estimatedSeconds": 12,
    "word": "vocabulary word for {level} level",
    "context": "where/how it's used",
    "explanation": "clear definition",
    "exampleSentence": "Natural example sentence",
    "tags": ["vocabulary"],
    "completed": false
  }},
  {{
    "id": "unique_id_5",
    "type": "native_check",
    "title": "Sounds Natural?",
    "emoji": "🧠",
    "description": "Native speaker test",
    "cefrLevel": "{level}",
    "estimatedSeconds": 12,
    "sentence": "A sentence to evaluate",
    "isNatural": true,
    "correctedVersion": "Only if isNatural is false",
    "explanation": "Why it is or isn't natural",
    "tags": ["naturalness"],
    "completed": false
  }},
  {{
    "id": "unique_id_6",
    "type": "brain_tickler",
    "title": "Quick Challenge",
    "emoji": "⏱️",
    "description": "10 seconds!",
    "cefrLevel": "{level}",
    "estimatedSeconds": 10,
    "timeLimit": 10,
    "question": "Quick question",
    "options": [
      {{"id": "opt1", "text": "option 1", "isCorrect": true}},
      {{"id": "opt2", "text": "option 2", "isCorrect": false}},
      {{"id": "opt3", "text": "option 3", "isCorrect": false}}
    ],
    "explanation": "Brief explanation",
    "tags": ["speed", "recall"],
    "completed": false
  }}
]

**REMEMBER:**
- Vary the position of correct answers in multiple choice
- Double-check all {language_display} grammar and spelling
- Match {level} level precisely
- Return ONLY the JSON array
"""

    return prompt


def validate_and_randomize_options(challenge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-process challenge to ensure answer randomization
    This is a safety check in case the AI didn't randomize properly
    """
    challenge_type = challenge.get("type")

    # Only randomize for types with multiple choice options
    if challenge_type in ["error_spotting", "micro_quiz", "brain_tickler"]:
        options = challenge.get("options", [])

        if len(options) > 0:
            # Check if options are already randomized
            correct_indices = [i for i, opt in enumerate(options) if opt.get("isCorrect")]

            if len(correct_indices) == 1:
                # Shuffle the options
                random.shuffle(options)
                challenge["options"] = options

                # Regenerate option IDs to match new positions
                for i, option in enumerate(options):
                    option["id"] = f"opt{i+1}"

    return challenge


async def generate_challenges_with_improved_ai(
    user_id: str,
    user_level: str,
    language: str = "english",
    user_analysis: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Generate 6 high-quality challenges using improved prompts

    Args:
        user_id: User ID
        user_level: CEFR level (A1-C2)
        language: Target language
        user_analysis: Optional user learning analysis

    Returns:
        List of 6 AI-generated challenges
    """
    try:
        print(f"[IMPROVED_AI] 🤖 Generating challenges for {language} {user_level}")
        print(f"[IMPROVED_AI] 📡 Using model: {GPT_MODEL}")

        # Build improved prompt
        prompt = build_improved_challenge_prompt(user_level, language, user_analysis)

        # Call GPT
        # GPT-5.2 and o-series models use max_completion_tokens instead of max_tokens
        api_params = {
            "model": GPT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are an expert {language.capitalize()} language teacher. Generate high-quality, accurate challenges. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,  # Balance between consistency and variety
        }

        # Use correct parameter name based on model
        if GPT_MODEL.startswith(("gpt-5", "o3", "o1")):
            api_params["max_completion_tokens"] = 4000
        else:
            api_params["max_tokens"] = 4000

        response = client.chat.completions.create(**api_params)

        # Parse response
        content = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        # Parse JSON
        if content.startswith('['):
            challenges = json.loads(content)
        elif content.startswith('{'):
            parsed = json.loads(content)
            challenges = (parsed.get("challenges") or
                         parsed.get("daily_challenges") or
                         list(parsed.values())[0] if parsed.values() else [])
        else:
            print(f"[IMPROVED_AI] ⚠️ Unexpected format")
            challenges = []

        if not isinstance(challenges, list):
            print(f"[IMPROVED_AI] ❌ Response is not a list")
            return []

        # Validate and post-process each challenge
        processed_challenges = []

        for challenge in challenges[:6]:  # Ensure max 6
            # Validate and randomize options
            challenge = validate_and_randomize_options(challenge)

            # Add metadata
            original_id = challenge.get("id", f"challenge_{uuid.uuid4().hex[:8]}")
            challenge["id"] = f"{original_id}_{uuid.uuid4().hex[:8]}"
            challenge["language"] = language
            challenge["generated_at"] = datetime.utcnow().isoformat()
            challenge["source"] = "ai_improved"
            challenge["model"] = GPT_MODEL

            processed_challenges.append(challenge)

        print(f"[IMPROVED_AI] ✅ Generated {len(processed_challenges)} high-quality challenges")

        return processed_challenges

    except Exception as e:
        print(f"[IMPROVED_AI] ❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []


# Convenience function that matches the old API
async def generate_challenges_with_ai(
    user_id: str,
    user_level: str,
    language: str = "english"
) -> List[Dict[str, Any]]:
    """
    Wrapper function for backward compatibility
    """
    return await generate_challenges_with_improved_ai(
        user_id, user_level, language, user_analysis=None
    )
