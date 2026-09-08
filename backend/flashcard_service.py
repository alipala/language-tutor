"""
Flashcard Service for AI-generated flashcards from speaking sessions
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai_client import get_async_openai
from models import Flashcard, FlashcardSet, FlashcardGenerationRequest


def _session_flashcards_enabled() -> bool:
    """Whether ending a session should auto-generate a flashcard set.

    Off by default: the generated sets were not being used, and each one costs an
    LLM call on every completed session. The manual /api/flashcards/generate
    endpoint stays available regardless of this flag.
    """
    return (os.getenv("SESSION_FLASHCARDS_ENABLED", "false") or "").strip().lower() == "true"


class FlashcardService:
    """Service for generating and managing AI-powered flashcards"""

    @staticmethod
    async def generate_flashcards(request: FlashcardGenerationRequest, user_id: str) -> FlashcardSet:
        """
        Generate flashcards from a speaking session using GPT-4o
        """
        try:
            # Prepare context for flashcard generation
            context = FlashcardService._build_generation_context(request)

            # Generate flashcards using GPT-4o
            prompt = FlashcardService._build_flashcard_prompt(request, context)

            print(f"[FLASHCARD_GEN] Generating {request.count} flashcards for session {request.session_id}")
            print(f"[FLASHCARD_GEN] Language: {request.language}, Level: {request.level}")

            response = await get_async_openai().chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for cost optimization (94% cheaper)
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert language learning flashcard creator. Generate high-quality, educational flashcards that help students practice and reinforce language skills from their speaking sessions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )

            if not response or not response.choices:
                raise Exception("Failed to generate flashcards from OpenAI")

            # Parse the response and create flashcard objects
            flashcards_data = FlashcardService._parse_flashcard_response(
                response.choices[0].message.content,
                request,
                user_id
            )

            # Create flashcard set
            flashcard_set = FlashcardSet(
                id=str(uuid.uuid4()),
                session_id=request.session_id,
                user_id=user_id,
                language=request.language,
                level=request.level,
                topic=request.topic,
                title=f"{request.language.capitalize()} Practice - Session {request.session_id[:8]}",
                description=f"AI-generated flashcards from your {request.language} speaking session",
                flashcards=flashcards_data,
                total_cards=len(flashcards_data),
                created_at=datetime.utcnow()
            )

            print(f"[FLASHCARD_GEN] ✅ Generated {len(flashcards_data)} flashcards successfully")

            return flashcard_set

        except Exception as e:
            print(f"[FLASHCARD_GEN] ❌ Error generating flashcards: {str(e)}")
            raise Exception(f"Failed to generate flashcards: {str(e)}")

    @staticmethod
    def _build_generation_context(request: FlashcardGenerationRequest) -> str:
        """Build context information for flashcard generation"""
        context_parts = []

        if request.conversation_content:
            context_parts.append(f"CONVERSATION CONTENT:\n{request.conversation_content[:1000]}...")

        if request.session_summary:
            context_parts.append(f"SESSION SUMMARY:\n{request.session_summary}")

        if request.topic:
            context_parts.append(f"TOPIC: {request.topic}")

        context_parts.extend([
            f"LANGUAGE: {request.language}",
            f"PROFICIENCY LEVEL: {request.level}",
            f"FLASHCARDS REQUESTED: {request.count}"
        ])

        return "\n\n".join(context_parts)

    @staticmethod
    def _build_flashcard_prompt(request: FlashcardGenerationRequest, context: str) -> str:
        """Build the prompt for flashcard generation"""

        level_descriptions = {
            "A1": "beginner - basic vocabulary, simple sentences, present tense",
            "A2": "elementary - common phrases, past/future tenses, basic communication",
            "B1": "intermediate - complex sentences, opinions, detailed descriptions",
            "B2": "upper intermediate - nuanced language, formal/informal registers",
            "C1": "advanced - sophisticated vocabulary, complex structures",
            "C2": "proficient - native-like fluency, idiomatic expressions"
        }

        level_desc = level_descriptions.get(request.level, f"{request.level} level")

        prompt = f"""Generate {request.count} high-quality flashcards for a {request.language} language learner at {level_desc} proficiency level.

CONTEXT INFORMATION:
{context}

REQUIREMENTS:
1. Create flashcards that reinforce key language skills from the session
2. Each flashcard must have a clear FRONT (question/prompt) and BACK (answer/explanation)
3. Categorize each flashcard by type: grammar, vocabulary, pronunciation, fluency, or comprehension
4. Assign difficulty level: easy, medium, or hard based on complexity
5. Focus on practical, conversational language that the student actually used or should practice
6. Include pronunciation tips where relevant
7. Make flashcards educational and spaced repetition friendly

FLASHCARD FORMAT:
Return a JSON array of flashcard objects with this exact structure:
[
  {{
    "front": "Question or prompt for the student",
    "back": "Answer, explanation, or correct response",
    "category": "grammar|vocabulary|pronunciation|fluency|comprehension",
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"]
  }}
]

GUIDELINES:
- FRONT should be a question, incomplete sentence, or prompt that tests knowledge
- BACK should provide the complete answer with explanation
- Category should reflect the primary language skill being practiced
- Difficulty should match the {request.level} proficiency level
- Tags should include relevant keywords like verb tenses, vocabulary themes, etc.
- Ensure variety across different language skills
- Make flashcards directly relevant to the conversation content when available

Generate exactly {request.count} flashcards that will help reinforce learning from this speaking session."""

        return prompt

    @staticmethod
    def _parse_flashcard_response(response_content: str, request: FlashcardGenerationRequest, user_id: str) -> List[Flashcard]:
        """Parse the OpenAI response and create Flashcard objects"""
        import json
        import re

        try:
            # 🔥 CRITICAL FIX: Strip markdown code fences if present
            # OpenAI sometimes wraps JSON in ```json ... ``` blocks
            cleaned_content = response_content.strip()
            
            # Remove markdown code fences
            if cleaned_content.startswith('```'):
                # Find the first newline after opening fence
                first_newline = cleaned_content.find('\n')
                if first_newline != -1:
                    cleaned_content = cleaned_content[first_newline + 1:]
                
                # Remove closing fence
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3].strip()
            
            print(f"[FLASHCARD_PARSE] Cleaned content length: {len(cleaned_content)}")
            
            # Try to extract JSON from the response
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', cleaned_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                flashcards_json = json.loads(json_str)
            else:
                # Try parsing the entire response as JSON
                flashcards_json = json.loads(cleaned_content)

            flashcards = []
            for i, card_data in enumerate(flashcards_json):
                # Create individual flashcard
                flashcard = Flashcard(
                    id=str(uuid.uuid4()),
                    session_id=request.session_id,
                    user_id=user_id,
                    language=request.language,
                    level=request.level,
                    topic=request.topic,
                    front=card_data.get("front", ""),
                    back=card_data.get("back", ""),
                    category=card_data.get("category", "vocabulary"),
                    difficulty=card_data.get("difficulty", "medium"),
                    tags=card_data.get("tags", []),
                    created_at=datetime.utcnow(),
                    next_review_date=datetime.utcnow()  # Due for review immediately
                )
                flashcards.append(flashcard)

            return flashcards

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[FLASHCARD_PARSE] ❌ Error parsing flashcard response: {str(e)}")
            print(f"[FLASHCARD_PARSE] Response content: {response_content[:500]}...")

            # Fallback: Create basic flashcards if parsing fails
            return FlashcardService._create_fallback_flashcards(request, user_id)

    @staticmethod
    def _create_fallback_flashcards(request: FlashcardGenerationRequest, user_id: str) -> List[Flashcard]:
        """Create basic fallback flashcards if parsing fails"""
        print("[FLASHCARD_FALLBACK] Creating fallback flashcards")

        fallback_cards = [
            {
                "front": f"What is the {request.language} word for 'hello'?",
                "back": "The greeting 'hello' in conversational contexts.",
                "category": "vocabulary",
                "difficulty": "easy",
                "tags": ["greetings", "basic"]
            },
            {
                "front": f"Complete: 'I ___ to the store yesterday.'",
                "back": "went - This uses the past tense of 'go'.",
                "category": "grammar",
                "difficulty": "medium",
                "tags": ["past tense", "irregular verbs"]
            },
            {
                "front": f"How do you pronounce '{request.language}' correctly?",
                "back": "Practice the native pronunciation focusing on accent and intonation.",
                "category": "pronunciation",
                "difficulty": "medium",
                "tags": ["pronunciation", "speaking"]
            }
        ]

        flashcards = []
        for card_data in fallback_cards[:request.count]:
            flashcard = Flashcard(
                id=str(uuid.uuid4()),
                session_id=request.session_id,
                user_id=user_id,
                language=request.language,
                level=request.level,
                topic=request.topic,
                front=card_data["front"],
                back=card_data["back"],
                category=card_data["category"],
                difficulty=card_data["difficulty"],
                tags=card_data["tags"],
                created_at=datetime.utcnow(),
                next_review_date=datetime.utcnow()
            )
            flashcards.append(flashcard)

        return flashcards

    @staticmethod
    def calculate_next_review_date(review_count: int, correct: bool, current_mastery: float) -> datetime:
        """
        Calculate next review date using spaced repetition algorithm
        Based on SM-2 algorithm principles
        """
        if correct:
            # Increase mastery level
            new_mastery = min(current_mastery + 0.1, 1.0)
            # Calculate interval based on review count
            if review_count == 0:
                days = 1
            elif review_count == 1:
                days = 3
            else:
                days = 6 * (2 ** (review_count - 2))
        else:
            # Decrease mastery level
            new_mastery = max(current_mastery - 0.2, 0.0)
            # Reset to 1 day for incorrect answers
            days = 1

        # Cap maximum interval at 30 days
        days = min(days, 30)

        return datetime.utcnow() + timedelta(days=days)

    @staticmethod
    def update_flashcard_progress(flashcard: Flashcard, correct: bool) -> Flashcard:
        """Update flashcard progress after review"""
        flashcard.review_count += 1
        flashcard.last_reviewed = datetime.utcnow()

        if correct:
            flashcard.correct_count += 1
            flashcard.mastery_level = min(flashcard.mastery_level + 0.1, 1.0)
        else:
            flashcard.incorrect_count += 1
            flashcard.mastery_level = max(flashcard.mastery_level - 0.2, 0.0)

        # Calculate next review date
        flashcard.next_review_date = FlashcardService.calculate_next_review_date(
            flashcard.review_count,
            correct,
            flashcard.mastery_level
        )

        return flashcard
