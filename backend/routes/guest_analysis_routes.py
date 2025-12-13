"""
Guest Analysis Routes
Provides session analysis for guest users WITHOUT authentication or database persistence
Designed for mobile app to show analysis results before signup
"""

import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
import httpx

# Initialize router
router = APIRouter()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully (guest_analysis_routes)")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method (guest_analysis_routes)")
    else:
        print(f"Error initializing OpenAI client: {str(e)}")
        raise

# Pydantic Models
class GuestMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class GuestSentence(BaseModel):
    text: str
    timestamp: Optional[str] = None
    messageIndex: Optional[int] = None

class GuestSessionAnalysisRequest(BaseModel):
    messages: List[GuestMessage]
    duration_minutes: float
    sentences_for_analysis: List[GuestSentence]
    language: str
    level: str
    topic: Optional[str] = None

# Helper Functions
def calculate_guest_session_stats(messages: List[GuestMessage], duration_minutes: float) -> Dict[str, Any]:
    """Calculate basic session statistics for guest users"""
    user_messages = [m for m in messages if m.role == "user"]
    tutor_messages = [m for m in messages if m.role in ["assistant", "system"]]

    # Calculate word counts
    user_words = sum(len(m.content.split()) for m in user_messages)
    tutor_words = sum(len(m.content.split()) for m in tutor_messages)
    total_words = user_words + tutor_words

    # Calculate message statistics
    user_message_count = len(user_messages)
    tutor_message_count = len(tutor_messages)
    total_messages = user_message_count + tutor_message_count

    # Calculate averages
    avg_user_message_length = user_words / user_message_count if user_message_count > 0 else 0
    avg_tutor_message_length = tutor_words / tutor_message_count if tutor_message_count > 0 else 0

    # Calculate speaking speed (words per minute)
    speaking_speed_wpm = round(user_words / duration_minutes) if duration_minutes > 0 else 0

    return {
        "total_words": total_words,
        "user_words": user_words,
        "tutor_words": tutor_words,
        "user_message_count": user_message_count,
        "tutor_message_count": tutor_message_count,
        "total_messages": total_messages,
        "average_user_message_length": round(avg_user_message_length, 1),
        "average_tutor_message_length": round(avg_tutor_message_length, 1),
        "conversation_turns": total_messages,
        "speaking_speed_wpm": speaking_speed_wpm,
        "duration_minutes": duration_minutes
    }

async def generate_guest_session_summary(
    messages: List[GuestMessage],
    language: str,
    level: str,
    topic: Optional[str],
    stats: Dict[str, Any]
) -> str:
    """Generate AI summary for guest user session"""
    try:
        # Build conversation excerpt (last 10 messages)
        conversation_content = ""
        for msg in messages[-10:]:
            role = "Student" if msg.role == "user" else "Tutor"
            conversation_content += f"{role}: {msg.content}\n"

        prompt = f"""Analyze this {language} language learning session and create an encouraging summary for a guest user.

STUDENT PROFILE:
- Language: {language}
- Level: {level}
- Topic: {topic or "General conversation"}
- Duration: {stats['duration_minutes']} minutes

SESSION STATS:
- Words spoken: {stats['user_words']}
- Messages: {stats['user_message_count']}
- Speaking speed: {stats['speaking_speed_wpm']} words/minute

CONVERSATION EXCERPT:
{conversation_content}

Create a brief, encouraging summary (max 150 words) that includes:
1. What they practiced well
2. One key achievement
3. One area to improve
4. Motivation to sign up and continue learning

Be positive and specific. This is their first session as a guest."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini model for cost efficiency
            messages=[
                {"role": "system", "content": "You are an encouraging language learning coach. Create brief, motivating summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )

        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            # Fallback summary
            return f"""Great job completing your first {language} practice session! You spoke {stats['user_words']} words in {stats['duration_minutes']} minutes at {level} level.

Your conversation showed good engagement with the {topic or 'topic'}. Keep practicing to build fluency and confidence!

Sign up to save your progress and unlock unlimited practice time."""

    except Exception as e:
        print(f"[GUEST_SUMMARY] Error generating summary: {str(e)}")
        # Return fallback summary
        return f"""Great job completing your {language} practice session! You practiced at {level} level for {stats['duration_minutes']} minutes.

Sign up to save your progress and continue your learning journey!"""

async def generate_guest_insights(
    messages: List[GuestMessage],
    language: str,
    level: str,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate AI insights for guest users"""
    try:
        # Build conversation for analysis
        conversation_content = ""
        user_messages = [m for m in messages if m.role == "user"]
        for msg in user_messages[-5:]:  # Last 5 user messages
            conversation_content += f"{msg.content}\n"

        prompt = f"""Analyze this {language} language learner's conversation and provide insights.

LEVEL: {level}
WORDS SPOKEN: {stats['user_words']}
SPEAKING SPEED: {stats['speaking_speed_wpm']} wpm

USER MESSAGES:
{conversation_content}

Provide:
1. breakthrough_moments: 2 specific positive moments (array of strings)
2. struggle_points: 2 areas to improve (array of strings)
3. confidence_level: "Low", "Medium", or "High"
4. immediate_actions: 2 specific practice recommendations (array of strings)

Return ONLY valid JSON in this format:
{{
  "breakthrough_moments": ["...", "..."],
  "struggle_points": ["...", "..."],
  "confidence_level": "Medium",
  "immediate_actions": ["...", "..."]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a language learning analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        if response and response.choices:
            import json
            insights = json.loads(response.choices[0].message.content)
            return insights
        else:
            return _get_fallback_insights(level)

    except Exception as e:
        print(f"[GUEST_INSIGHTS] Error generating insights: {str(e)}")
        return _get_fallback_insights(level)

def _get_fallback_insights(level: str) -> Dict[str, Any]:
    """Fallback insights when AI generation fails"""
    return {
        "breakthrough_moments": [
            f"Maintained conversation flow at {level} level",
            "Engaged actively with the tutor"
        ],
        "struggle_points": [
            "Continue building vocabulary range",
            "Practice with more complex sentence structures"
        ],
        "confidence_level": "Medium",
        "immediate_actions": [
            "Practice daily for 5-10 minutes",
            "Review common phrases and expressions"
        ]
    }

# Route Handlers
@router.post("/api/guest/analyze-session")
async def analyze_guest_session(request: GuestSessionAnalysisRequest):
    """
    Analyze a guest user's practice session WITHOUT saving to database.
    Returns sentence analyses, summary, stats, and insights for mobile app display.
    """
    try:
        print(f"[GUEST_ANALYSIS] Processing guest session: {request.language} {request.level}")
        print(f"[GUEST_ANALYSIS] Messages: {len(request.messages)}, Duration: {request.duration_minutes}min")
        print(f"[GUEST_ANALYSIS] Sentences to analyze: {len(request.sentences_for_analysis)}")

        # 1. Analyze sentences (batch processing for efficiency)
        background_analyses = []
        if request.sentences_for_analysis:
            try:
                from background_sentence_analysis import batch_analyze_sentences

                sentence_texts = [s.text for s in request.sentences_for_analysis if s.text]

                if sentence_texts:
                    print(f"[GUEST_ANALYSIS] Analyzing {len(sentence_texts)} sentences...")
                    analyses = await batch_analyze_sentences(
                        sentences=sentence_texts,
                        language=request.language,
                        level=request.level
                    )
                    background_analyses = [a.dict() for a in analyses]
                    print(f"[GUEST_ANALYSIS] ✅ Sentence analysis complete: {len(background_analyses)} results")
            except Exception as e:
                print(f"[GUEST_ANALYSIS] ⚠️ Sentence analysis failed: {str(e)}")
                # Continue without sentence analysis

        # 2. Calculate session statistics
        session_stats = calculate_guest_session_stats(request.messages, request.duration_minutes)
        print(f"[GUEST_ANALYSIS] ✅ Stats calculated: {session_stats['user_words']} words, {session_stats['speaking_speed_wpm']} wpm")

        # 3. Generate AI summary
        session_summary = await generate_guest_session_summary(
            messages=request.messages,
            language=request.language,
            level=request.level,
            topic=request.topic,
            stats=session_stats
        )
        print(f"[GUEST_ANALYSIS] ✅ Summary generated: {len(session_summary)} chars")

        # 4. Generate AI insights
        insights = await generate_guest_insights(
            messages=request.messages,
            language=request.language,
            level=request.level,
            stats=session_stats
        )
        print(f"[GUEST_ANALYSIS] ✅ Insights generated")

        # 5. Generate simple flashcards from sentence analyses
        flashcards = []
        for idx, analysis in enumerate(background_analyses[:5]):  # Max 5 flashcards
            if analysis.get('is_worth_analyzing') and (
                analysis.get('grammar_issues') or
                analysis.get('vocabulary_suggestions')
            ):
                # Create flashcard from the analysis
                flashcard = {
                    "id": f"guest_flash_{idx}",
                    "front": f"How can you improve this sentence?\n\n\"{analysis['sentence']}\"",
                    "back": analysis.get('alternative_phrasings', [analysis['sentence']])[0] if analysis.get('alternative_phrasings') else analysis['sentence'],
                    "category": "grammar" if analysis.get('grammar_issues') else "vocabulary",
                    "difficulty": analysis.get('difficulty_level', request.level),
                    "hint": analysis.get('grammar_issues', [None])[0] if analysis.get('grammar_issues') else analysis.get('vocabulary_suggestions', [None])[0]
                }
                flashcards.append(flashcard)

        print(f"[GUEST_ANALYSIS] ✅ Generated {len(flashcards)} flashcards")

        # Return complete analysis
        return {
            "success": True,
            "is_guest": True,
            "session_stats": session_stats,
            "session_summary": session_summary,
            "background_analyses": background_analyses,
            "insights": insights,
            "flashcards": flashcards,
            "message": "Session analyzed successfully. Sign up to save your progress!"
        }

    except Exception as e:
        print(f"[GUEST_ANALYSIS] Error: {str(e)}")
        import traceback
        print(f"[GUEST_ANALYSIS] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing session: {str(e)}"
        )

@router.post("/api/guest/quick-stats")
async def get_guest_quick_stats(request: Request):
    """
    Quick endpoint to get just stats without full analysis.
    Useful for showing immediate feedback during/after session.
    """
    try:
        data = await request.json()
        messages = [GuestMessage(**m) for m in data.get('messages', [])]
        duration_minutes = data.get('duration_minutes', 2.0)

        stats = calculate_guest_session_stats(messages, duration_minutes)

        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        print(f"[GUEST_QUICK_STATS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
