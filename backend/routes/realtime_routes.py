"""
Realtime API Routes
Handles OpenAI Realtime API token generation, usage logging, and model configuration
"""

import traceback
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import httpx
from openai_client import get_async_openai

from auth import get_optional_current_user_from_request
from models import UserResponse

# Debug flag — set DEBUG_REALTIME=true in Railway env to re-enable verbose prints.
# Off by default to keep Railway log rate below the 500/s cap under load.
DEBUG_REALTIME = os.getenv("DEBUG_REALTIME", "false").lower() == "true"

# Shared httpx client for OpenAI Realtime API calls.
# One pool per worker process; reuses TLS connections across requests, eliminating
# the 100-150ms per-request TLS handshake cost that existed when AsyncClient()
# was instantiated fresh on every call.
_openai_http_client: Optional[httpx.AsyncClient] = None


def get_openai_http_client() -> httpx.AsyncClient:
    """Return the shared httpx client, creating it on first call."""
    global _openai_http_client
    if _openai_http_client is None:
        _openai_http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=3.0, read=10.0, write=5.0, pool=2.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _openai_http_client


async def close_openai_http_client() -> None:
    """Close the shared client on application shutdown."""
    global _openai_http_client
    if _openai_http_client is not None:
        await _openai_http_client.aclose()
        _openai_http_client = None


# Initialize router
router = APIRouter()


# Pydantic Models
class TutorSessionRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"
    topic: Optional[str] = None
    user_prompt: Optional[str] = None
    assessment_data: Optional[Dict[str, Any]] = None
    research_data: Optional[str] = None
    conversation_history: Optional[str] = None
    news_context: Optional[str] = None  # News article context for news conversations
    learning_plan_data: Optional[Dict[str, Any]] = None  # Learning plan session context
    selected_duration: Optional[int] = 5  # Session duration in minutes (1, 3, or 5)
    disable_corrections: Optional[bool] = False  # Disable real-time grammar corrections (all levels)
    session_mode: Optional[str] = "conversation"  # "conversation" | "roleplay"

class RealtimeUsageData(BaseModel):
    user_id: Optional[str] = None
    session_id: str
    language: str
    level: str
    topic: Optional[str] = None
    audio_input_tokens: int = 0
    audio_output_tokens: int = 0
    text_input_tokens: int = 0
    text_output_tokens: int = 0
    cached_input_audio_tokens: int = 0
    cached_input_text_tokens: int = 0
    total_tokens: int = 0
    session_start: str
    session_end: Optional[str] = None
    session_duration_seconds: Optional[int] = None
    estimated_cost: float = 0.0
    model: str = "gpt-realtime-mini"
    start_time: Optional[int] = None
    end_time: Optional[int] = None

# Helper Functions
def get_language_iso_code(language: str) -> str:
    """Convert language name to ISO 639-1 code for Whisper transcription"""
    language_map = {
        "english": "en",
        "dutch": "nl",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "italian": "it",
        "portuguese": "pt",
        "russian": "ru",
        "japanese": "ja",
        "korean": "ko",
        "chinese": "zh",
        "arabic": "ar",
        "hindi": "hi",
        "turkish": "tr",
        "polish": "pl",
        "swedish": "sv",
        "norwegian": "no",
        "danish": "da",
        "finnish": "fi",
        "czech": "cs",
        "hungarian": "hu",
        "romanian": "ro",
        "bulgarian": "bg",
        "croatian": "hr",
        "slovak": "sk",
        "slovenian": "sl",
        "lithuanian": "lt",
        "latvian": "lv",
        "estonian": "et",
        "greek": "el",
        "hebrew": "he",
        "thai": "th",
        "vietnamese": "vi",
        "indonesian": "id",
        "malay": "ms",
        "filipino": "tl",
        "ukrainian": "uk",
        "bengali": "bn",
        "tamil": "ta",
        "telugu": "te",
        "marathi": "mr",
        "gujarati": "gu",
        "kannada": "kn",
        "malayalam": "ml",
        "punjabi": "pa",
        "urdu": "ur",
        "persian": "fa",
        "swahili": "sw",
        "afrikaans": "af",
        "amharic": "am",
        "azerbaijani": "az",
        "belarusian": "be",
        "bosnian": "bs",
        "catalan": "ca",
        "welsh": "cy",
        "basque": "eu",
        "galician": "gl",
        "georgian": "ka",
        "icelandic": "is",
        "irish": "ga",
        "kazakh": "kk",
        "kyrgyz": "ky",
        "luxembourgish": "lb",
        "macedonian": "mk",
        "maltese": "mt",
        "mongolian": "mn",
        "nepali": "ne",
        "serbian": "sr",
        "sinhala": "si",
        "albanian": "sq",
        "tajik": "tg",
        "turkmen": "tk",
        "uzbek": "uz",
        "yiddish": "yi"
    }

    language_lower = language.lower().strip()

    # If already an ISO code (e.g. "nl", "de"), pass it through directly
    known_iso_codes = {"en", "nl", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
                       "zh", "ar", "hi", "tr", "pl", "sv", "no", "da", "fi", "cs",
                       "hu", "ro", "bg", "hr", "sk", "sl", "lt", "lv", "et", "el",
                       "he", "th", "vi", "id", "ms", "tl", "uk", "bn", "ta", "te",
                       "mr", "gu", "kn", "ml", "pa", "ur", "fa", "sw", "af", "am",
                       "az", "be", "bs", "ca", "cy", "eu", "gl", "ka", "is", "ga",
                       "kk", "ky", "lb", "mk", "mt", "mn", "ne", "sr", "si", "sq",
                       "tg", "tk", "uz", "yi"}
    if language_lower in known_iso_codes:
        if DEBUG_REALTIME:
            print(f"Language mapping: '{language}' -> '{language_lower}' (ISO passthrough)")
        return language_lower

    iso_code = language_map.get(language_lower, "en")

    if DEBUG_REALTIME:
        print(f"Language mapping: '{language}' -> '{iso_code}'")
    return iso_code

def get_next_cefr_level(current_level: str) -> str:
    """Get the next CEFR level after the current one"""
    level_progression = {
        'A1': 'A2',
        'A2': 'B1',
        'B1': 'B2',
        'B2': 'C1',
        'C1': 'C2',
        'C2': 'C2'  # C2 is the highest level
    }
    return level_progression.get(current_level.upper(), 'B1')

def get_assessment_duration(level: str) -> str:
    """Get the minimum assessment duration for a CEFR level"""
    duration_map = {
        'A1': '2',
        'A2': '3',
        'B1': '4',
        'B2': '5',
        'C1': '5',
        'C2': '5'
    }
    return duration_map.get(level.upper(), '4')

def get_level_appropriate_topics(level: str) -> str:
    """Get conversation topics appropriate for a CEFR level"""
    topics_by_level = {
        'A1': 'daily routines, family, hobbies, simple descriptions, basic needs',
        'A2': 'shopping, local geography, work, past experiences, future plans',
        'B1': 'current events, travel experiences, personal opinions, problems and solutions',
        'B2': 'abstract ideas, cultural topics, detailed arguments, hypothetical situations',
        'C1': 'complex academic topics, nuanced opinions, abstract concepts, socio-political issues',
        'C2': 'specialized topics, sophisticated argumentation, subtle meanings, expert-level discourse'
    }
    return topics_by_level.get(level.upper(), topics_by_level['B1'])

async def build_universal_instructions(request: TutorSessionRequest) -> str:
    """
    Build instructions that work reliably on all browsers.

    PHASE 0 OPTIMIZATION: Now includes personality/tone section with 2-sentence limit
    and uses compressed session summaries for 93% token reduction.

    BEGINNER OPTIMIZATION: Routes A1/A2 levels to specialized beginner prompts
    with vocabulary control, question scaffolding, and simplified structure.
    """

    language = request.language.lower()
    level = request.level.upper()

    # Roleplay mode bypasses all specialized paths — handled at end of this function
    _session_mode = getattr(request, 'session_mode', 'conversation') or 'conversation'

    # ── PROMPT_V3 (guide-aligned short prompt for gpt-realtime-mini) ──────
    # Returns None for unsupported modes (roleplay, learning-plan final
    # assessment, unparseable context) → falls through to legacy builders.
    # Flag off = byte-identical legacy behavior.
    if os.getenv("PROMPT_V3", "false").lower() == "true":
        from prompt_v3 import build_instructions_v3
        _v3 = build_instructions_v3(request, language, level)
        if _v3:
            if DEBUG_REALTIME:
                print(f"[PROMPT_V3] Using V3 instructions: {len(_v3)} characters")
            return _v3
        if DEBUG_REALTIME:
            print("[PROMPT_V3] Mode unsupported by V3 — falling back to legacy builder")

    # ROUTE BEGINNER/INTERMEDIATE/ADVANCED TO build_beginner_instructions.
    # When BEGINNER_PROMPT_V2 is on, that builder serves ALL CEFR levels (A1–C2)
    # via per-level profiles, so freestyle/news/custom stays consistent across
    # levels. When the flag is off, only A1/A2 route here (legacy behaviour);
    # B1–C2 fall through to build_universal_instructions below.
    _v2_on = os.getenv("BEGINNER_PROMPT_V2", "false").lower() == "true"
    _levels_for_beginner_builder = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] if _v2_on else ['A1', 'A2']
    if level in _levels_for_beginner_builder and _session_mode != 'roleplay':
        if DEBUG_REALTIME:
            print(f"[BEGINNER_MODE] Routing {level} to specialized beginner instructions")
        from prompt_optimization_helpers import build_beginner_instructions

        # Extract assessment and learning plan data if available
        assessment_data = request.assessment_data if hasattr(request, 'assessment_data') else None
        learning_plan_data = request.learning_plan_data if hasattr(request, 'learning_plan_data') else None

        # Log if learning plan data is present
        if learning_plan_data:
            if DEBUG_REALTIME:
                print(f"[BEGINNER_MODE] ✅ Learning plan data available")
            completed_sessions = learning_plan_data.get('completed_sessions', 0)
            total_sessions = learning_plan_data.get('total_sessions', 0)
            if DEBUG_REALTIME:
                print(f"[BEGINNER_MODE] 📚 Progress: {completed_sessions}/{total_sessions} sessions")
        else:
            if DEBUG_REALTIME:
                print(f"[BEGINNER_MODE] ⚠️ NO learning plan data")

        # Build beginner-optimized instructions
        research_context = request.research_data if hasattr(request, 'research_data') and request.research_data else None
        if research_context:
            if DEBUG_REALTIME:
                print(f"[BEGINNER_MODE] ✅ Research context available: {len(research_context)} characters")
            if DEBUG_REALTIME:
                print(f"[BEGINNER_MODE] Research preview: {research_context[:200]}...")
        else:
            if DEBUG_REALTIME:
                print(f"[BEGINNER_MODE] ⚠️ NO research context available")

        beginner_instructions = build_beginner_instructions(
            language=language,
            level=level,
            topic=request.topic if hasattr(request, 'topic') else None,
            user_prompt=request.user_prompt if hasattr(request, 'user_prompt') else None,
            assessment_data=assessment_data,
            learning_plan_data=learning_plan_data,
            conversation_history=request.conversation_history if hasattr(request, 'conversation_history') else None,
            news_context=request.news_context if hasattr(request, 'news_context') else None,
            research_context=research_context,
            selected_duration=getattr(request, 'selected_duration', 5) or 5,
        )

        if DEBUG_REALTIME:
            print(f"[BEGINNER_MODE] Created beginner instructions: {len(beginner_instructions)} characters")
        return beginner_instructions

    # ============================================================================
    # INTERMEDIATE/ADVANCED (B1-C2) INSTRUCTION BUILDING
    # Continue with existing optimized prompts for B1+ levels
    # ============================================================================

    # Import optimization helpers
    from prompt_optimization_helpers import (
        build_personality_tone_section,
        build_compressed_session_context,
        build_reference_pronunciations,
        build_sample_phrases,
        build_conversation_flow_section,
        build_safety_escalation_section,
        build_state_specific_sample_phrases,
        build_speed_instructions,
        build_optimized_assessment_context,
        build_universal_correction_style
    )

    # Language configurations
    language_configs = {
        "english": {
            "rule": "Respond only in English. If the student speaks another language, say: 'Let's practice in English. Try saying that in English.'",
            "greeting": "Hello! I am your English language tutor."
        },
        "dutch": {
            "rule": "Spreek alleen Nederlands. Als de student een andere taal gebruikt, zeg: 'Laten we Nederlands oefenen. Probeer het in het Nederlands te zeggen.'",
            "greeting": "Hallo! Ik ben je Nederlandse taaldocent."
        },
        "spanish": {
            "rule": "Responde solo en español. Si el estudiante habla otro idioma, di: 'Practiquemos español. Intenta decirlo en español.'",
            "greeting": "¡Hola! Soy tu profesor de español."
        },
        "french": {
            "rule": "Réponds uniquement en français. Si l'étudiant parle une autre langue, dis: 'Pratiquons le français. Essaie de le dire en français.'",
            "greeting": "Bonjour! Je suis ton professeur de français."
        },
        "german": {
            "rule": "Antworte nur auf Deutsch. Wenn der Schüler eine andere Sprache spricht, sage: 'Lass uns Deutsch üben. Versuche es auf Deutsch zu sagen.'",
            "greeting": "Hallo! Ich bin dein Deutschlehrer."
        }
    }

    config = language_configs.get(language, {
        "rule": f"Respond only in {language}.",
        "greeting": f"Hello! I am your {language} language tutor."
    })

    # Build conversation context summary for reconnections
    conversation_context = ""
    if hasattr(request, 'conversation_history') and request.conversation_history:
        conversation_context = f"""
📝 CONVERSATION CONTEXT (MAINTAIN CONTINUITY):
Previous conversation history:
{request.conversation_history}

CRITICAL INSTRUCTIONS FOR RECONNECTION:
- This is a CONTINUATION of an existing conversation, NOT a new session
- DO NOT greet the user again or restart the conversation
- IMMEDIATELY continue from where the conversation left off
- MAINTAIN the same learning focus and objectives established earlier
- Reference previous topics and corrections made in the conversation
- Keep the same energy and teaching approach as before the interruption
"""

    # Build assessment-aware instructions
    assessment_context = ""
    learning_plan_context = ""

    if request.assessment_data:
        if DEBUG_REALTIME:
            print(f"[ASSESSMENT] Integrating assessment data into instructions")

        overall_score = request.assessment_data.get('overall_score', 0)
        recommended_level = request.assessment_data.get('recommended_level', level)
        strengths = request.assessment_data.get('strengths', [])
        areas_for_improvement = request.assessment_data.get('areas_for_improvement', [])

        pronunciation_score = request.assessment_data.get('pronunciation', {}).get('score', 0)
        grammar_score = request.assessment_data.get('grammar', {}).get('score', 0)
        vocabulary_score = request.assessment_data.get('vocabulary', {}).get('score', 0)
        fluency_score = request.assessment_data.get('fluency', {}).get('score', 0)
        coherence_score = request.assessment_data.get('coherence', {}).get('score', 0)

        assessment_context = f"""
📊 STUDENT ASSESSMENT PROFILE:
- Overall Score: {overall_score}/100
- Recommended Level: {recommended_level}
- Pronunciation: {pronunciation_score}/100
- Grammar: {grammar_score}/100
- Vocabulary: {vocabulary_score}/100
- Fluency: {fluency_score}/100
- Coherence: {coherence_score}/100

STRENGTHS: {', '.join(strengths) if strengths else 'General communication'}
FOCUS AREAS: {', '.join(areas_for_improvement) if areas_for_improvement else 'Overall improvement'}

PERSONALIZED APPROACH:
- Acknowledge their strengths in {', '.join(strengths[:2]) if strengths else 'communication'}
- Focus on improving {', '.join(areas_for_improvement[:2]) if areas_for_improvement else 'speaking skills'}
- Adapt difficulty to their {recommended_level} level capabilities
- Provide targeted feedback based on their assessment results"""

        if DEBUG_REALTIME:
            print(f"Assessment context integrated: {len(assessment_context)} characters")

    # Extract learning plan data if available
    if request.assessment_data and 'learning_plan_data' in request.assessment_data:
        if DEBUG_REALTIME:
            print(f"[LEARNING_PLAN] Integrating learning plan data into instructions")

        learning_plan_data = request.assessment_data.get('learning_plan_data', {})
        plan_content = learning_plan_data.get('plan_content', {})

        if plan_content:
            completed_sessions = learning_plan_data.get('completed_sessions', 0)
            total_sessions = learning_plan_data.get('total_sessions', 8)

            # Detect if this is a FINAL ASSESSMENT
            is_final_assessment = completed_sessions >= total_sessions
            if is_final_assessment:
                if DEBUG_REALTIME:
                    print(f"[FINAL_ASSESSMENT] Detected final assessment mode - {completed_sessions}/{total_sessions} sessions completed")

                # Get current and next level for assessment
                current_level = level
                next_level = get_next_cefr_level(current_level)
                target_language = language

                # Build comprehensive final assessment instructions
                learning_plan_context = f"""
🎓 FINAL ASSESSMENT MODE - ACTIVE

You are conducting a FINAL SPEAKING ASSESSMENT for a {current_level} level {target_language} learning plan.

ASSESSMENT OBJECTIVE:
Evaluate the student's readiness to advance from {current_level} to {next_level} level through natural conversation.

DUAL-CRITERIA EVALUATION (explained to user at the END):
1. CURRENT LEVEL MASTERY ({current_level}): Student should demonstrate strong command of {current_level} skills
2. NEXT LEVEL READINESS ({next_level}): Student should show potential for {next_level} level work

ASSESSMENT STRUCTURE:
Duration: {get_assessment_duration(current_level)} minutes minimum
Format: Natural conversation that progressively increases in complexity

🎬 HOW TO START THE ASSESSMENT:
Begin with a warm, natural greeting that immediately establishes the assessment context:
"Hi! Congratulations on completing all your {current_level} sessions! Today is your final speaking assessment. Don't worry - this will be just like a friendly conversation. I'd love to hear about your learning journey. What topics did you enjoy most during your {target_language} plan?"

PHASE 1 - WARM-UP (First 1-2 minutes):
- Start with {current_level} level topics to build confidence
- Use familiar vocabulary and grammar structures
- Create a comfortable, encouraging atmosphere
- Example: "Let's talk about your experience with this {current_level} learning plan. What topics did you enjoy most?"

PHASE 2 - CURRENT LEVEL ASSESSMENT (Next 2-3 minutes):
- Test mastery of {current_level} competencies through natural dialogue
- Evaluate: grammar accuracy, vocabulary range, fluency, coherence, pronunciation
- Ask questions that require {current_level} skills
- Gradually increase complexity within {current_level}
- Listen for: consistent accuracy, natural expression, appropriate vocabulary

PHASE 3 - NEXT LEVEL CHALLENGE (Final 1-2 minutes):
- Introduce {next_level} topics and complexity
- Test potential for next level work
- Use some {next_level} vocabulary and structures
- Assess: adaptability, comprehension, willingness to tackle challenges
- Example topics at {next_level}: more abstract concepts, nuanced opinions, complex situations

NATURAL CONVERSATION GUIDELINES:
✅ DO:
- Keep it conversational and engaging - NOT a formal test
- Build topics naturally from student's responses
- Provide appropriate scaffolding when needed
- Encourage elaboration: "Tell me more about...", "How did that make you feel?"
- Maintain positive, supportive tone throughout
- Mix different skills naturally (describing, narrating, expressing opinions, explaining)

❌ DO NOT:
- Say "This is a test" or make it feel like an exam
- Ask drill questions or vocabulary lists
- Make student repeat phrases
- Announce phase transitions
- Make student anxious or uncomfortable
- Give corrective feedback during the assessment

CONVERSATION TOPICS (vary complexity):
For {current_level}: {get_level_appropriate_topics(current_level)}
For {next_level} stretch: {get_level_appropriate_topics(next_level)}

ENDING THE ASSESSMENT:
After the target duration, NATURALLY conclude the conversation:
- Thank the student warmly
- Provide encouraging summary
- Explain the dual-criteria evaluation system
- Mention they will receive detailed feedback shortly

Example closing: "Thank you for this great conversation! You've completed your {current_level} final assessment. Our system evaluates based on two criteria: your mastery of {current_level} skills and your readiness for {next_level} level. You'll receive detailed results soon showing your performance in grammar, vocabulary, fluency, coherence, and pronunciation. Great job!"

REMEMBER:
- This is an ASSESSMENT but should feel like a FRIENDLY CONVERSATION
- Your role is to ELICIT language, not teach during the assessment
- Focus on LISTENING and EVALUATING, not correcting
- Create a SAFE space for the student to demonstrate their best abilities
- The conversation should flow NATURALLY while covering required competencies

Previous Learning Journey:
{build_compressed_session_context(learning_plan_data.get('session_summaries', []), max_summaries=5)}

Plan Details:
- Title: {plan_content.get('title', 'Learning Plan')}
- Overview: {plan_content.get('overview', 'Comprehensive language learning')}
"""
                if DEBUG_REALTIME:
                    print(f"[FINAL_ASSESSMENT] Special assessment instructions created: {len(learning_plan_context)} characters")
                if DEBUG_REALTIME:
                    print(f"[FINAL_ASSESSMENT] Current level: {current_level}, Next level: {next_level}")

            else:
                # Regular learning plan session (not final assessment)
                sessions_per_week = 4
                current_week_number = min((completed_sessions // sessions_per_week) + 1, len(plan_content.get('weekly_schedule', [])))
                current_session_in_week = (completed_sessions % sessions_per_week) + 1

                weekly_schedule = plan_content.get('weekly_schedule', [])
                current_week = weekly_schedule[current_week_number - 1] if current_week_number <= len(weekly_schedule) else weekly_schedule[0] if weekly_schedule else None

                if current_week:
                    week_focus = current_week.get('focus', 'Building foundational skills')
                    week_activities = current_week.get('activities', [])

                    # ── Vocabulary & phrases from enriched schedule ───────────
                    key_vocabulary = current_week.get('key_vocabulary', [])
                    key_phrases = current_week.get('key_phrases', [])

                    # ── Previous session structured summaries ─────────────────
                    # Build context from both compressed strings AND structured objects
                    previous_sessions_context = ""
                    session_summaries = learning_plan_data.get('session_summaries', [])
                    session_history = learning_plan_data.get('session_history', [])

                    if session_summaries:
                        previous_sessions_context = build_compressed_session_context(
                            session_summaries, max_summaries=3
                        )

                    # Enrich with last structured summary if available
                    _structured_context_lines = []
                    for _hist in reversed(session_history[-3:]):
                        _ss = _hist.get('structured_summary') or {}
                        if not _ss:
                            continue
                        _vocab = _ss.get('vocabulary_practiced', [])
                        _focus_next = _ss.get('focus_next_session', '')
                        _confidence = _ss.get('student_confidence', '')
                        _breakthrough = _ss.get('breakthrough_moment', '')
                        _corrections = _ss.get('corrections_made', [])
                        _s_num = _hist.get('session_number', '?')

                        _lines = [f"  Session {_s_num} insights:"]
                        if _vocab:
                            _lines.append(f"    - Vocabulary practiced: {', '.join(_vocab[:6])}")
                        if _corrections:
                            _corr_str = '; '.join(
                                f"{c.get('wrong','?')} → {c.get('correct','?')}"
                                for c in _corrections[:3]
                            )
                            _lines.append(f"    - Corrections made: {_corr_str}")
                        if _confidence:
                            _lines.append(f"    - Student confidence: {_confidence}")
                        if _breakthrough:
                            _lines.append(f"    - Breakthrough: {_breakthrough}")
                        if _focus_next:
                            _lines.append(f"    - Carry forward: {_focus_next}")
                        _structured_context_lines.extend(_lines)

                    if _structured_context_lines:
                        previous_sessions_context += (
                            "\n\n📋 DETAILED PREVIOUS SESSION INSIGHTS:\n"
                            + "\n".join(_structured_context_lines)
                        )

                    if previous_sessions_context:
                        previous_sessions_context += """

LEARNING PROGRESSION:
- Build directly upon the vocabulary and corrections listed above
- If a correction was made in a previous session, watch for the same error and recast gently
- Reference previous breakthrough moments to boost confidence
- Start the session by continuing the area flagged in "Carry forward" """

                    # ── Vocabulary injection block ────────────────────────────
                    vocab_injection = ""
                    if key_vocabulary or key_phrases:
                        vocab_lines = []
                        if key_vocabulary:
                            vocab_lines.append(
                                f"Target vocabulary: {', '.join(key_vocabulary[:10])}"
                            )
                        if key_phrases:
                            vocab_lines.append(
                                f"Target phrases: {', '.join(key_phrases[:5])}"
                            )
                        vocab_injection = f"""

🎯 MANDATORY VOCABULARY FOR THIS SESSION:
{chr(10).join(vocab_lines)}

VOCABULARY RULES:
- Weave these words/phrases naturally into the conversation
- When the student uses one correctly, acknowledge it briefly
- If a target word fits the topic, use it yourself first so the student hears it in context
- Do NOT turn this into a vocabulary drill — integrate organically"""

                    learning_plan_context = f"""
🚨🚨🚨 CRITICAL FIRST MESSAGE INSTRUCTION - READ THIS FIRST 🚨🚨🚨

YOU ARE IN LEARNING PLAN MODE - DO NOT USE GENERIC GREETINGS!

Your FIRST message MUST follow this EXACT structure:
"Hello! Great to see you again! This week we're focusing on {week_focus}. Let's dive right in - {week_activities[0] if week_activities else 'I want to start by asking you about'} [immediate question or task]."

❌ FORBIDDEN FIRST MESSAGES:
- "Hello! I am your English language tutor—what would you like to practice today?"
- "What would you like to practice?"
- "How can I help you today?"
- ANY question asking what the user wants to practice

✅ REQUIRED FIRST MESSAGE EXAMPLE:
"Hello! Great to see you again! This week we're focusing on Email & Written Communication: Write professional emails and documents. Let's dive right in - I'd like you to imagine you need to write a business email to a colleague requesting a meeting. What would you say in that email?"

📚 LEARNING PLAN CONTEXT:
- Plan Title: {plan_content.get('title', 'Personalized Learning Plan')}
- Plan Overview: {plan_content.get('overview', 'Customized based on assessment results')}
- Current Session: Week {current_week_number}, Session {current_session_in_week}
- Focus Area: {week_focus}
- Key Activities: {', '.join(week_activities[:3]) if week_activities else 'Practice conversation skills'}
{previous_sessions_context}{vocab_injection}

CONVERSATION GUIDANCE:
- Center the conversation around this week's focus: "{week_focus}"
- Incorporate activities from the learning plan: {', '.join(week_activities[:2]) if week_activities else 'speaking practice'}
- Reference the student's learning journey and progress
- Connect speaking practice to their personalized learning objectives
- Encourage practice of specific skills mentioned in the weekly activities
- Build upon previous session insights and maintain learning continuity"""

                    if DEBUG_REALTIME:
                        print(f"Learning plan context integrated: {len(learning_plan_context)} characters")
                    if DEBUG_REALTIME:
                        print(f"Current week {current_week_number} focus: {week_focus}")
                    if DEBUG_REALTIME:
                        print(f"Current week activities: {week_activities}")
                    if DEBUG_REALTIME:
                        print(f"Session {current_session_in_week} of week {current_week_number}")
                    if key_vocabulary:
                        if DEBUG_REALTIME:
                            print(f"Key vocabulary injected: {key_vocabulary[:5]}")
                    if key_phrases:
                        if DEBUG_REALTIME:
                            print(f"Key phrases injected: {key_phrases[:3]}")

    # Handle news conversations FIRST (highest priority)
    if request.news_context:
        import json
        try:
            news_data = json.loads(request.news_context)
            if DEBUG_REALTIME:
                print(f"[NEWS] Building instructions for news conversation")
            if DEBUG_REALTIME:
                print(f"[NEWS] Raw news_data keys: {news_data.keys() if isinstance(news_data, dict) else 'not a dict'}")
            if DEBUG_REALTIME:
                print(f"[NEWS] News data preview: {str(news_data)[:500]}")

            # Extract news article details - FIXED: Use correct key names
            article_title = news_data.get('news_title', news_data.get('title', 'a news article'))
            article_summary = news_data.get('news_summary', news_data.get('summary', ''))
            vocabulary_items = news_data.get('vocabulary', [])
            discussion_questions = news_data.get('discussion_questions', [])
            ai_instructions = news_data.get('ai_instructions', '')

            # Format vocabulary list
            vocab_list = "\n".join([
                f"- **{item.get('word', '')}** ({item.get('translation', '')}): {item.get('example', '')}"
                for item in vocabulary_items[:10]  # Limit to 10 key words
            ])

            # Format discussion questions with level-appropriate framing
            if level in ("A1", "A2"):
                # Beginner: derive yes/no questions from the summary, not pre-generated ones
                questions_list = "(Do NOT use these pre-generated questions for beginners — derive simple yes/no questions directly from the Summary above instead)"
            else:
                questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(discussion_questions[:5])])

            # Normalize language code: "en" → "english", "nl" → "dutch", etc.
            _lang_code_map = {"en": "english", "nl": "dutch", "es": "spanish", "fr": "french", "de": "german", "pt": "portuguese", "it": "italian"}
            lang_key = _lang_code_map.get(language.lower(), language.lower())
            config = language_configs.get(lang_key, {
                "rule": f"Respond only in {language}.",
                "greeting": f"Hello! I am your {language} language tutor."
            })

            # Build level-specific constraints for all CEFR levels
            level_constraints_map = {
                "A1": """- Use ONLY the 500 most common words — no exceptions
- Present tense only — no past, future, or conditional
- Max 8 words per sentence, subject-verb-object structure only
- Rephrase immediately if learner shows confusion""",
                "A2": """- Basic familiar vocabulary only — no advanced words
- Simple present and simple past tense only
- Max 12 words per sentence, simple compound sentences OK (and, but, or)
- No subjunctive, passive voice, or complex conditionals""",
                "B1": """- Everyday vocabulary plus topic-specific words from the article
- Present, past, future and basic conditional tenses
- Compound and some complex sentences OK
- Introduce 2-3 new vocabulary words from the article naturally
- Check understanding when introducing new concepts""",
                "B2": """- Wider range of vocabulary including abstract and topic-specific terms
- Full range of tenses including perfect, passive, and conditionals
- Complex sentences with subordinate clauses
- Discuss nuance, implication, and different perspectives
- Encourage learner to paraphrase and explain in their own words""",
                "C1": """- Advanced vocabulary including idiomatic expressions and collocations
- All tenses and complex grammatical structures
- Push learner to express precise opinions with evidence and reasoning
- Explore subtle distinctions in meaning
- Encourage sophisticated argumentation and counterarguments""",
                "C2": """- Full unrestricted vocabulary including academic and technical register
- All grammatical structures at native-level complexity
- Engage with nuance, irony, subtext, and critical analysis
- Challenge assumptions and explore multiple interpretations
- Expect near-native fluency and precision in expression""",
            }
            level_constraints = level_constraints_map.get(level, f"- Stay strictly within {level} proficiency level throughout")

            # Build comprehensive news instructions
            instructions = f"""You are a {language} language tutor conducting a news discussion session with an {level} level student.

LANGUAGE RULE: {config['rule']}

📰 NEWS ARTICLE CONTEXT:
Title: {article_title}
Summary: {article_summary}

🎯 YOUR MISSION:
Guide an engaging discussion about this news article, helping the student:
1. Understand the key points of the article
2. Practice using the vocabulary in context
3. Express their opinions and thoughts
4. Develop critical thinking skills

📚 KEY VOCABULARY TO TEACH:
{vocab_list}

💬 DISCUSSION QUESTIONS TO EXPLORE:
{questions_list}

🎓 TEACHING APPROACH:
{ai_instructions}

CONVERSATION FLOW:
1. **Welcome & Introduction** (First message):
   - Greet the student warmly
   - Introduce the news topic with enthusiasm
   - Share 1-2 key facts from the summary
   - Ask an engaging opening question about the topic

2. **Vocabulary Practice** (MANDATORY):
   - YOU MUST teach and practice THE SPECIFIC VOCABULARY WORDS listed above
   - Naturally introduce each vocabulary word in context during the conversation
   - Ask students to use these new words in their own sentences
   - Provide examples when needed using the vocabulary from the list
   - Praise correct usage and gently correct when needed
   - Track which vocabulary words you've covered and ensure you teach all of them

3. **Content Discussion** (MANDATORY):
   - YOU MUST explore THE SPECIFIC DISCUSSION QUESTIONS listed above
   - Ask these discussion questions one by one throughout the conversation
   - Guide discussion through the key points of the article
   - Encourage students to share personal opinions and reactions
   - Connect the news to their own experiences or knowledge
   - Make sure to cover all the discussion questions before the session ends

4. **Critical Thinking**:
   - Ask "why" and "how" questions based on the discussion questions
   - Encourage students to analyze the implications
   - Discuss different perspectives on the topic
   - Use the vocabulary words while discussing these perspectives

🚨 STRICT LANGUAGE LEVEL CONSTRAINTS ({level}):
{level_constraints}
- Vocabulary and grammar MUST stay at {level} level throughout the conversation
- Do NOT drift into higher-level language as conversation progresses
- Simplify immediately if learner shows confusion
- Celebrate progress and correct gently within level constraints

CORRECTION STYLE:
- Use natural recasting (embed correct form in your response)
- Don't explicitly point out every error
- Focus on meaning first, form second
- Keep corrections conversational and encouraging

ENGAGEMENT RULES:
- Be enthusiastic and curious about the topic
- Share interesting facts from the article
- Ask for the student's opinions and reactions
- Make connections to real life
- Keep the conversation dynamic and interactive

🚨 CRITICAL: This is a NEWS DISCUSSION, not a reading comprehension test:
- DON'T quiz the student on article details
- DO have a natural conversation about the topic
- DON'T ask "Did you understand?" repeatedly
- DO check comprehension through discussion
- DON'T lecture - have a dialogue
- DO encourage the student to lead parts of the conversation

⚠️ MANDATORY REQUIREMENTS - YOU MUST COMPLETE THESE:
1. ✅ Teach and practice ALL the vocabulary words listed in "KEY VOCABULARY TO TEACH"
2. ✅ Ask and explore ALL the questions listed in "DISCUSSION QUESTIONS TO EXPLORE"
3. ✅ Stay strictly within the {level} proficiency level constraints at all times
4. ✅ Use the vocabulary words naturally throughout the discussion questions

These are not optional suggestions - they are REQUIRED elements of this news conversation session.
The learner expects to practice these specific vocabulary words and discuss these specific topics.

Remember: You're having an engaging conversation about news, using it as a vehicle for language practice and cultural learning!"""

            if DEBUG_REALTIME:
                print(f"[NEWS] News instructions created: {len(instructions)} characters")
            if DEBUG_REALTIME:
                print(f"[NEWS] Article: {article_title}")
            if DEBUG_REALTIME:
                print(f"[NEWS] Vocabulary items: {len(vocabulary_items)}")
            if DEBUG_REALTIME:
                print(f"[NEWS] Discussion questions: {len(discussion_questions)}")
            return instructions

        except Exception as e:
            if DEBUG_REALTIME:
                print(f"[NEWS] Error parsing news_context, falling back to default")
            if DEBUG_REALTIME:
                print(f"[NEWS] Error details: {str(e)}")
            # Fall through to default instructions

    # Handle custom topic
    if request.topic == "custom" and request.user_prompt:
        if DEBUG_REALTIME:
            print(f"[CUSTOM_TOPIC] Creating universal custom topic instructions")

        # Duration-aware pacing for custom topics
        from tutor_config import get_session_pacing as _gsp
        _dur = getattr(request, 'selected_duration', 5) or 5
        _cp  = _gsp(_dur)
        _custom_pacing = (
            f"\n⏱️ SESSION PACING — {_dur} MINUTE(S):\n"
            f"{_cp['pacing_note']}\n"
            f"Max {_cp['response_sentences']} sentence(s) per response. "
            f"Target ~{_cp['turns_target']} exchanges total.\n"
        )

        research_content = ""
        if request.research_data:
            research_content = request.research_data
            if DEBUG_REALTIME:
                print(f"Using provided research data: {len(research_content)} chars")
        else:
            # Fallback research — use gpt-4.1-mini with language+level context
            try:
                response = await get_async_openai().chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are an educational content assistant for a {language} language tutor. "
                                f"The student is at CEFR {level} level. "
                                f"Provide 5-7 interesting, factual points about the topic below. "
                                f"Keep vocabulary at {level} level. Respond in English (tutor will translate)."
                            )
                        },
                        {"role": "user", "content": f"Topic: {request.user_prompt}"}
                    ],
                    temperature=0.3,
                    max_tokens=600
                )
                if response and response.choices:
                    research_content = response.choices[0].message.content
                    if DEBUG_REALTIME:
                        print(f"Fallback research completed ({len(research_content)} chars)")
            except Exception as e:
                if DEBUG_REALTIME:
                    print(f"Research failed: {str(e)}")

        # Add all optimization sections
        personality_section = build_personality_tone_section(language, level)
        pronunciations = build_reference_pronunciations()
        sample_phrases = build_sample_phrases(language)
        conversation_flow = build_conversation_flow_section(language, level, request.user_prompt)
        safety_escalation = build_safety_escalation_section(language)
        speed_instructions = build_speed_instructions()
        correction_style = build_universal_correction_style(level) if not request.disable_corrections else ""

        instructions = f"""{personality_section}

{pronunciations}

{sample_phrases}

{speed_instructions}

{correction_style}

{conversation_flow}

{safety_escalation}

{_custom_pacing}

CUSTOM TOPIC CONVERSATION: '{request.user_prompt}'

You are a PROACTIVE {language} language coach for {level} level students who LEADS the conversation.

PROACTIVE TUTOR BEHAVIOR - CRITICAL:
- DO NOT ask questions like 'What would you like to practice?', 'Would you like to try something else?', 'Do you have any questions?', or 'How would you like to proceed?'
- YOU guide the conversation naturally toward learning objectives
- After addressing any issues, continue the conversation flow smoothly without explicit transitions
- Maintain conversational flow while working toward learning goals
- Be a conversation partner and guide, not a drill instructor

CONTENT GUARDRAILS - STRICTLY ENFORCE:
1. EDUCATIONAL FOCUS ONLY: Only discuss language learning and the specified topic
2. REFUSE HARMFUL CONTENT: Immediately decline discussions about:
   - Violence, weapons, illegal activities
   - Sexual content, adult themes, inappropriate relationships
   - Hate speech, discrimination, offensive language
   - Personal information requests (addresses, phone numbers, etc.)
   - Political extremism, conspiracy theories
   - Self-harm, dangerous activities, substance abuse
3. OFF-TOPIC REDIRECT: If user tries to discuss unrelated topics or avoid the topic, say:
   "I understand, but let's focus on practicing {language} with our topic: {request.user_prompt}. This helps improve your language skills and serves your learning objectives."
4. LEARNING PLAN ADHERENCE: ALWAYS redirect conversations back to the learning objectives. NEVER allow general conversation that doesn't serve the learning plan.

MANDATORY TOPIC FOCUS:
- You MUST keep the conversation focused on '{request.user_prompt}'
- If the user tries to change topics or avoid the subject, redirect them back to '{request.user_prompt}'
- Do NOT allow "general {language} practice" - stick to the specific topic
- The conversation must serve the learning objectives at all times

🚨 CRITICAL ANTI-DRILL REMINDER:
- You are a CONVERSATION PARTNER, not a drill instructor
- NEVER ask students to repeat phrases, words, or sentences
- NEVER create structured drills, pronunciation exercises, or repetition tasks
- NEVER say "Repeat after me", "Try saying", "Say this", or similar drilling phrases
- Correct errors through NATURAL RECASTING only (embed correct form in your response)
- Maintain natural conversation flow at ALL times - drilling kills engagement
- If student makes error: recast it naturally in your reply, then continue conversation
- Example: Student says "I go yesterday" → You respond "Oh, you went somewhere yesterday? Where?"

LANGUAGE RULE: {config['rule']}
{assessment_context}
{learning_plan_context}

🎯 TOPIC INFORMATION - YOU MUST DISCUSS THIS CONTENT:
{research_content if research_content else f'Use your knowledge about {request.user_prompt}.'}

🚨 CRITICAL INSTRUCTIONS FOR USING THE TOPIC INFORMATION:
1. READ the topic information above carefully
2. SHARE specific facts, details, and information from the research in your responses
3. ASK questions that engage with the ACTUAL CONTENT, not just generic questions
4. DISCUSS the real substance of the topic throughout the conversation
5. Make the conversation about the SPECIFIC DETAILS from the research, not vague/general questions

Examples:
❌ WRONG: "What do you think about this topic?" (too vague)
✅ RIGHT: "This topic involves [specific detail from research]. What's your opinion on that?"

❌ WRONG: "Do you know about {request.user_prompt}?" (too generic)
✅ RIGHT: "[Share 2-3 facts from research]. Have you heard about this before?"

❌ WRONG: "Is this interesting to you?" (meta question)
✅ RIGHT: "According to [research detail], [specific fact]. How do you feel about that?"

FIRST MESSAGE REQUIREMENT:
Your first message MUST:
1. Immediately introduce '{request.user_prompt}' with 1-2 SPECIFIC FACTS from the topic information above
2. NOT use generic greetings like "Hello! How can I help you?"
3. Engage with the ACTUAL CONTENT from the research

Example structure: "Let's talk about {request.user_prompt}! [Share 1-2 specific facts from the research]. [Ask question about those facts]."

ONGOING CONVERSATION REQUIREMENT:
- Throughout the conversation, continuously reference and discuss the specific information provided in the topic research
- Don't just ask "What do you think?" - share facts and details, THEN ask for reactions and opinions
- Keep bringing up new details from the research to maintain depth and engagement
- The user searched for this specific topic - they want to discuss the ACTUAL CONTENT, not generic questions

CRITICAL: Keep all conversation about '{request.user_prompt}' using the specific information provided.
- Use the topic information extensively - don't just mention it once
- Adapt language complexity to {level} level while maintaining content depth
- Be engaging and educational about the SPECIFIC topic content
- Apply personalized feedback based on assessment results
- If learning plan context is available, connect the topic to the student's learning objectives"""

        if DEBUG_REALTIME:
            print(f"Custom topic instructions: {len(instructions)} characters")
        return instructions

    # Handle regular topics — B1-C2 path (A1/A2 handled above via build_beginner_instructions)
    elif request.topic and request.topic != "custom":
        # Resolve topic from the universal catalogue (covers all aliases)
        from tutor_config import get_topic_config, get_session_pacing, get_topic_vocabulary, get_subtopic_arcs

        _selected_duration = getattr(request, 'selected_duration', 5) or 5
        _topic_cfg   = get_topic_config(request.topic)
        _pacing      = get_session_pacing(_selected_duration)
        _vocab_words = get_topic_vocabulary(request.topic, level) if _topic_cfg else []
        _arcs        = get_subtopic_arcs(request.topic, _pacing["subtopics_to_cover"]) if _topic_cfg else []

        if _topic_cfg:
            topic_name        = _topic_cfg["display_name"]
            topic_description = _topic_cfg["description"]
        else:
            # Unknown topic — build a graceful fallback so no TypeError occurs
            topic_details_fallback = {
                "travel": {"name": "Travel & Tourism", "description": "Discuss travel destinations, experiences, planning trips, transportation, accommodations, and cultural experiences."},
                "food": {"name": "Food & Cooking", "description": "Talk about cuisines, recipes, restaurants, cooking techniques, and food culture."},
                "work": {"name": "Work & Career", "description": "Discuss jobs, career goals, workplace situations, professional development, and work-life balance."
            },
            "education": {
                "name": "Education & Learning",
                "description": "Talk about school, university, learning experiences, educational goals, study methods, academic subjects, and lifelong learning. Practice vocabulary related to education systems, academic achievements, and learning strategies."
            },
            "daily-routine": {
                "name": "Daily Routines",
                "description": "Share your daily schedule, morning routines, everyday activities, time management, and lifestyle habits. Practice vocabulary for describing time, daily activities, schedules, and personal routines."
            },
            "family": {
                "name": "Family & Relationships",
                "description": "Discuss family members, relationships, friendships, social connections, family traditions, and personal relationships. Practice vocabulary for describing people, relationships, emotions, and social interactions."
            },
            "health": {
                "name": "Health & Fitness",
                "description": "Talk about exercise, healthy habits, medical topics, wellness, mental health, and lifestyle choices. Practice vocabulary related to body parts, symptoms, medical care, fitness activities, and healthy living."
            },
            "shopping": {
                "name": "Shopping & Money",
                "description": "Discuss shopping experiences, prices, budgeting, financial topics, consumer choices, and spending habits. Practice vocabulary for shopping, money, prices, payment methods, and financial planning."
            },
            "movies": {
                "name": "Movies & TV Shows",
                "description": "Discuss films, series, actors, directors, entertainment preferences, genres, and media consumption. Practice vocabulary for describing plots, characters, opinions, and entertainment experiences."
            },
            "music": {
                "name": "Music & Arts",
                "description": "Talk about music genres, artists, concerts, creative arts, cultural events, and artistic expression. Practice vocabulary for describing music, art forms, performances, and creative activities."
            },
            "sports": {
                "name": "Sports & Games",
                "description": "Discuss sports, games, competitions, physical activities, team sports, individual sports, and recreational activities. Practice vocabulary for sports equipment, rules, competitions, and athletic performance."
            },
            "hobbies": {
                "name": "Hobbies & Interests",
                "description": "Share your favorite activities, creative pursuits, personal interests, leisure time, and recreational activities. Practice vocabulary for describing interests, skills, pastimes, and personal preferences."
            },
            "technology": {
                "name": "Technology & Digital Life",
                "description": "Discuss gadgets, apps, social media, digital trends, internet usage, and technology's impact on daily life. Practice vocabulary for digital devices, online activities, and technological innovations."
            },
            "news": {
                "name": "News & Current Events",
                "description": "Talk about current events, news stories, global happenings, social issues, and world affairs. Practice vocabulary for discussing news, expressing opinions, and analyzing current topics."
            },
            "weather": {
                "name": "Weather & Seasons",
                "description": "Discuss weather conditions, seasons, climate, outdoor activities, and weather-related experiences. Practice vocabulary for describing weather, seasonal activities, and climate-related topics."
            },
            "transportation": {
                "name": "Transportation & Travel",
                "description": "Talk about vehicles, public transport, commuting, getting around, traffic, and transportation systems. Practice vocabulary for different modes of transport, directions, and travel logistics."
            },
            "culture": {
                "name": "Culture & Traditions",
                "description": "Explore cultural aspects, traditions, festivals, customs, cultural differences, and heritage. Practice vocabulary for describing cultural practices, celebrations, traditions, and cross-cultural experiences."
            },
            "environment": {
                "name": "Environment & Nature",
                "description": "Explore environmental issues, sustainability, the natural world, conservation, climate change, and eco-friendly practices. Practice vocabulary for environmental topics, nature, and green living."
            },
            "home": {
                "name": "Home & Living",
                "description": "Discuss housing, home decoration, household tasks, living spaces, furniture, and domestic life. Practice vocabulary for describing homes, rooms, furniture, household items, and living arrangements."
            },
            "pets": {
                "name": "Pets & Animals",
                "description": "Talk about pets, animals, wildlife, and animal care."
            }
        }
            _fb = topic_details_fallback.get(request.topic, {
                "name": request.topic.replace("-", " ").title(),
                "description": f"Discuss various aspects of {request.topic}."
            })
            topic_name        = _fb["name"]
            topic_description = _fb["description"]

        # ── Build topic vocabulary block ─────────────────────────────────────
        if _vocab_words:
            _vocab_block = (
                f"\n🎯 KEY VOCABULARY TO USE THIS SESSION:\n"
                f"  {', '.join(_vocab_words)}\n"
                f"Weave these words naturally into your questions and responses.\n"
                f"Do NOT drill them — introduce them organically in context.\n"
            )
        else:
            _vocab_block = ""

        # ── Build subtopic progression block ─────────────────────────────────
        if _arcs:
            _arc_lines = ["\n📋 SUBTOPIC PROGRESSION (cover in order, pace to session length):"]
            for i, arc in enumerate(_arcs, 1):
                _arc_lines.append(f"\n  {i}. {arc['name']}")
                for q in arc.get("questions", [])[:2]:
                    _arc_lines.append(f"     → \"{q}\"")
            _subtopic_block = "\n".join(_arc_lines) + "\n"
        else:
            _subtopic_block = ""

        # ── Build duration pacing block ───────────────────────────────────────
        _pacing_block = (
            f"\n⏱️ SESSION PACING — {_selected_duration} MINUTE(S):\n"
            f"{_pacing['pacing_note']}\n"
            f"Max {_pacing['response_sentences']} sentence(s) per response. "
            f"Target ~{_pacing['turns_target']} exchanges total.\n"
        )

        # Add all optimization sections
        personality_section = build_personality_tone_section(language, level)
        pronunciations      = build_reference_pronunciations()
        sample_phrases      = build_sample_phrases(language)
        conversation_flow   = build_conversation_flow_section(language, level, topic_name)
        safety_escalation   = build_safety_escalation_section(language)
        speed_instructions  = build_speed_instructions()
        correction_style    = build_universal_correction_style(level) if not request.disable_corrections else ""

        instructions = f"""{personality_section}

{pronunciations}

{sample_phrases}

{speed_instructions}

{correction_style}

{conversation_flow}

{safety_escalation}

{_pacing_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THIS SESSION: {topic_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Topic: {topic_name}
Description: {topic_description}

{_vocab_block}
{_subtopic_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TUTOR BEHAVIOUR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are a PROACTIVE {language} language coach who LEADS the conversation.

✅ DO:
- Open with ONE engaging question about {topic_name} — no generic greetings
- Progress through the subtopic arcs above in order
- Use the key vocabulary words naturally in your turns (not as drills)
- Correct errors through NATURAL RECASTING only — embed correct form, continue conversation
- Acknowledge the student's level and adapt complexity accordingly

❌ NEVER:
- Ask "What would you like to practise?" — YOU drive the conversation
- Ask students to repeat phrases (drilling kills engagement)
- Say "Repeat after me", "Try saying", "Say this"
- Deviate from {topic_name} without a clear reason
- Write more than {_pacing['response_sentences']} sentence(s) per response

LANGUAGE RULE: {config['rule']}

{assessment_context}
{learning_plan_context}

FIRST MESSAGE: Introduce {topic_name} with ONE specific question from subtopic 1 above.
Example: "Let's talk about {topic_name}! {_arcs[0]['questions'][0] if _arcs else 'What do you think about this topic?'}"

Keep the entire conversation focused on {topic_name}.
Apply personalised feedback based on assessment results if available."""

        # ── ROLEPLAY MODE — override with immersive scenario instructions ────
        session_mode = _session_mode  # already resolved at top of function
        if session_mode == 'roleplay':
            if DEBUG_REALTIME:
                print(f"[ROLEPLAY] ✅ Roleplay mode detected for topic={request.topic} level={level}")
            from tutor_config import get_roleplay_scenario
            scenario = get_roleplay_scenario(request.topic)
            if scenario:
                level_note = scenario.get('level_notes', {}).get(level, '')
                roleplay_vocab = f"\nUSE THESE WORDS naturally in your speech: {', '.join(_vocab_words[:6])}" if _vocab_words else ""

                # Level-aware complexity rules — placed at the very top so the model weights them first
                complexity_rules = {
                    'A1': (
                        "CRITICAL — learner is A1 (complete beginner):\n"
                        "- Use ONLY simple present tense: 'I go', 'you like', 'it is'\n"
                        "- Maximum 6 words per sentence\n"
                        "- Ask ONE yes/no question per turn, nothing more\n"
                        "- Use the same simple words repeatedly — do not introduce complex vocabulary\n"
                        "- Example good response: 'Hoi! Ben je nieuw? Leuk!'\n"
                        "- Example bad response: 'Wat maakte dat je geïnteresseerd bent?' (TOO COMPLEX)"
                    ),
                    'A2': (
                        "IMPORTANT — learner is A2 (elementary):\n"
                        "- Use simple present and simple past tense only\n"
                        "- Keep sentences short: maximum 8-10 words\n"
                        "- Ask simple direct questions: 'Do you like...?', 'How often...?'\n"
                        "- Avoid subordinate clauses, conditional tense, or abstract nouns"
                    ),
                    'B1': (
                        "Learner is B1 (intermediate) — use natural everyday language.\n"
                        "Mix tenses. Ask open questions. Keep it conversational."
                    ),
                    'B2': (
                        "Learner is B2 (upper intermediate) — use rich natural language.\n"
                        "Include idioms, varied tenses, nuanced questions."
                    ),
                    'C1': "Learner is C1 (advanced) — use sophisticated register, complex structures, idiomatic language.",
                    'C2': "Learner is C2 (mastery) — use expert-level language, subtle nuance, full idiomatic range.",
                }.get(level, '')

                # Use level-specific opening line if available, fall back to default
                opening = scenario.get('opening_line_by_level', {}).get(level, scenario['opening_line'])

                instructions = f"""LANGUAGE LEVEL: {level} — READ THIS FIRST
{complexity_rules}

## YOUR CHARACTER
You are {scenario['character']}.
Location: {scenario['location']}.
The learner has just arrived: {scenario['entry_action']}.
{roleplay_vocab}

## STRICT RULES
- You are {scenario['character'].split(',')[0]}. Stay in character. You are NOT a teacher.
- Speak ONLY in {language.capitalize()}. Never use English mid-scene.
- {_pacing['response_sentences']} sentence(s) maximum per response.
- ONE question per turn — never ask two things at once.
- If learner makes a grammar error: restate correctly in your reply naturally, without commenting.

## OPENING LINE — say this exactly, then wait:
"{opening}"

Never say you are a language tutor. Never explain grammar. Just be {scenario['character'].split(',')[0]}."""

                if DEBUG_REALTIME:
                    print(f"[ROLEPLAY] Scenario: {scenario['character']} | Topic: {request.topic} | Level: {level}")
                return instructions

        # ── CONVERSATION MODE (default) ──────────────────────────────────────
        if DEBUG_REALTIME:
            print(f"Regular topic instructions ({_selected_duration}min, {level}): {len(instructions)} characters")
        if _vocab_words:
            if DEBUG_REALTIME:
                print(f"  Topic vocab injected: {_vocab_words[:5]}")
        if _arcs:
            if DEBUG_REALTIME:
                print(f"  Subtopic arcs: {[a['name'] for a in _arcs]}")
        return instructions

    # Default conversation instructions (no specific topic)
    else:
        # Add all optimization sections
        personality_section = build_personality_tone_section(language, level)
        pronunciations = build_reference_pronunciations()
        sample_phrases = build_sample_phrases(language)
        conversation_flow = build_conversation_flow_section(language, level, "general conversation")
        safety_escalation = build_safety_escalation_section(language)
        speed_instructions = build_speed_instructions()
        correction_style = build_universal_correction_style(level) if not request.disable_corrections else ""

        instructions = f"""{personality_section}

{pronunciations}

{sample_phrases}

{speed_instructions}

{correction_style}

{conversation_flow}

{safety_escalation}

You are a PROACTIVE {language} language tutor for {level} level students who MANAGES the conversation flow.

PROACTIVE TUTOR BEHAVIOR - CRITICAL:
- DO NOT ask questions like 'What would you like to practice?', 'Would you like to try something else?', 'Do you have any questions?', or 'How would you like to proceed?'
- YOU guide the conversation naturally toward learning objectives
- After addressing any issues, continue the conversation flow smoothly without explicit transitions
- Maintain conversational flow while working toward learning goals
- Be a conversation partner and guide, not a drill instructor

CONTENT GUARDRAILS - STRICTLY ENFORCE:
1. EDUCATIONAL FOCUS ONLY: Only discuss language learning and educational topics
2. REFUSE HARMFUL CONTENT: Immediately decline discussions about:
   - Violence, weapons, illegal activities
   - Sexual content, adult themes, inappropriate relationships
   - Hate speech, discrimination, offensive language
   - Personal information requests (addresses, phone numbers, etc.)
   - Political extremism, conspiracy theories
   - Self-harm, dangerous activities, substance abuse
3. OFF-TOPIC REDIRECT: If user tries to discuss unrelated topics, redirect them to language learning
4. LEARNING PLAN ADHERENCE: If learning plan context is available, you MUST focus on the specified objectives. Do not allow the user to change topics or avoid the learning plan.

MANDATORY LEARNING PLAN FOCUS (if applicable):
- If learning plan context is provided above, you MUST keep the conversation focused on those objectives
- If the user tries to change topics, redirect them back to the learning plan
- Do NOT allow "general English practice" - stick to the specific areas identified in the assessment
- The conversation must serve the learning objectives at all times

🚨 CRITICAL ANTI-DRILL REMINDER:
- You are a CONVERSATION PARTNER, not a drill instructor
- NEVER ask students to repeat phrases, words, or sentences
- NEVER create structured drills, pronunciation exercises, or repetition tasks
- NEVER say "Repeat after me", "Try saying", "Say this", or similar drilling phrases
- Correct errors through NATURAL RECASTING only (embed correct form in your response)
- Maintain natural conversation flow at ALL times - drilling kills engagement
- If student makes error: recast it naturally in your reply, then continue conversation
- Example: Student says "I go yesterday" → You respond "Oh, you went somewhere yesterday? Where?"

LANGUAGE RULE: {config['rule']}
{assessment_context}
{learning_plan_context}

FIRST MESSAGE INSTRUCTIONS:
- If FINAL ASSESSMENT MODE is active (check above): Use the specific opening greeting provided in the "🎬 HOW TO START THE ASSESSMENT" section. Congratulate them on completing all sessions and immediately begin the assessment conversation.
- If learning plan context is provided (but NOT final assessment): Follow the "🎬 CRITICAL FIRST MESSAGE INSTRUCTION FOR LEARNING PLANS" section EXACTLY. Start immediately with the week's focus and first activity. DO NOT ask "What would you like to practice?" or any similar question.
- If NO learning plan context: Start with a brief greeting, then IMMEDIATELY begin a conversation about a relevant topic at the student's level. DO NOT ask "What would you like to practice?" - instead, start with an engaging question or statement about a topic appropriate for their level.

CRITICAL:
- If FINAL ASSESSMENT MODE is active, follow the assessment structure and opening greeting EXACTLY as specified above.
- If learning plan context is available (non-assessment), you MUST follow the opening format in the "🎬 CRITICAL FIRST MESSAGE INSTRUCTION FOR LEARNING PLANS" section and focus the entire conversation on the current week's learning objectives.
- NEVER start with generic questions like "What would you like to practice?" - YOU drive the conversation based on the context provided."""

        return instructions

# Background task for usage log processing
async def process_usage_log_background(
    usage_data: RealtimeUsageData,
    current_user: Optional[UserResponse]
):
    """Process usage log in background to avoid blocking response"""
    try:
        user_id = current_user.id if current_user else None
        from database import usage_logs_collection
        from datetime import datetime, timezone
        from openai_organization_costs import fetch_organization_costs, datetime_to_unix_timestamp

        # OpenAI Realtime API Pricing Configuration
        #
        # NOTE: This dict prices only the gpt-realtime-mini *voice* model (audio/text
        # tokens). The input transcription model is billed SEPARATELY and is not
        # reflected here. gpt-realtime-whisper is billed per minute of *user-spoken*
        # audio (~$0.017/min), not per token — roughly +$0.83/user/month at 150 min
        # sessions with ~50% user-speech ratio. If precise per-session transcribe
        # cost is ever needed, capture spoken-audio seconds client-side and multiply
        # by REALTIME_TRANSCRIBE_RATE here.
        PRICING = {
            "gpt-realtime": {
                "audio_input": 32.0 / 1_000_000,
                "audio_output": 64.0 / 1_000_000,
                "text_input": 4.0 / 1_000_000,
                "text_output": 16.0 / 1_000_000,
                "cached_audio": 0.40 / 1_000_000,
                "cached_text": 2.0 / 1_000_000
            },
            "gpt-realtime-mini": {
                "audio_input": 10.0 / 1_000_000,
                "audio_output": 20.0 / 1_000_000,
                "text_input": 0.6 / 1_000_000,
                "text_output": 2.4 / 1_000_000,
                "cached_audio": 0.30 / 1_000_000,
                # Cached text input is 90% off uncached ($0.60 → $0.06). Was 0.30 here,
                # which over-reported cached-text cost ~5x (reporting only — billing
                # is OpenAI-side and unaffected).
                "cached_text": 0.06 / 1_000_000
            }
        }

        # Always use environment variable model for cost calculation
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")

        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] Using model from environment: {model}")

        if hasattr(usage_data, 'model') and usage_data.model and usage_data.model != model:
            if DEBUG_REALTIME:
                print(f"[USAGE_LOG] Note: usage_data.model was '{usage_data.model}' but using environment model '{model}' for cost calculation")

        if model not in PRICING:
            if DEBUG_REALTIME:
                print(f"[USAGE_LOG] Unknown model '{model}', defaulting to gpt-realtime-mini pricing")
            model = "gpt-realtime-mini"

        pricing = PRICING[model]

        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] Using pricing for model: {model}")

        # Calculate costs
        audio_input_cost = usage_data.audio_input_tokens * pricing["audio_input"]
        cached_audio_input_cost = usage_data.cached_input_audio_tokens * pricing["cached_audio"]
        audio_output_cost = usage_data.audio_output_tokens * pricing["audio_output"]
        text_input_cost = usage_data.text_input_tokens * pricing["text_input"]
        cached_text_input_cost = usage_data.cached_input_text_tokens * pricing["cached_text"]
        text_output_cost = usage_data.text_output_tokens * pricing["text_output"]

        total_cost = sum([
            audio_input_cost,
            cached_audio_input_cost,
            audio_output_cost,
            text_input_cost,
            cached_text_input_cost,
            text_output_cost
        ])

        # Calculate cost per minute and tokens per minute
        duration_minutes = usage_data.session_duration_seconds / 60 if usage_data.session_duration_seconds else 1
        cost_per_minute = total_cost / duration_minutes if duration_minutes > 0 else 0
        tokens_per_minute = usage_data.total_tokens / duration_minutes if duration_minutes > 0 else 0

        # Format duration
        duration_min = usage_data.session_duration_seconds // 60
        duration_sec = usage_data.session_duration_seconds % 60
        duration_str = f"{duration_min} min {duration_sec} sec" if duration_min > 0 else f"{duration_sec} sec"

        # Log to console with detailed breakdown
        if DEBUG_REALTIME:
            print("="*80)
        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] SESSION COMPLETED")
        if DEBUG_REALTIME:
            print(f"Session ID: {usage_data.session_id}")
        if DEBUG_REALTIME:
            print(f"User ID: {current_user.id if current_user else usage_data.user_id or 'guest'}")
        if DEBUG_REALTIME:
            print(f"Language: {usage_data.language}")
        if DEBUG_REALTIME:
            print(f"Level: {usage_data.level}")
        if DEBUG_REALTIME:
            print(f"Duration: {usage_data.session_duration_seconds}s ({duration_str})")
        if DEBUG_REALTIME:
            print(f"Model: {usage_data.model}")
        if DEBUG_REALTIME:
            print("-"*80)
        if DEBUG_REALTIME:
            print(f"TOKEN USAGE:")
        if DEBUG_REALTIME:
            print(f"  Audio Input: {usage_data.audio_input_tokens:,} tokens")
        if DEBUG_REALTIME:
            print(f"  Audio Input (cached): {usage_data.cached_input_audio_tokens:,} tokens")
        if DEBUG_REALTIME:
            print(f"  Audio Output: {usage_data.audio_output_tokens:,} tokens")
        if DEBUG_REALTIME:
            print(f"  Text Input: {usage_data.text_input_tokens:,} tokens")
        if DEBUG_REALTIME:
            print(f"  Text Input (cached): {usage_data.cached_input_text_tokens:,} tokens")
        if DEBUG_REALTIME:
            print(f"  Text Output: {usage_data.text_output_tokens:,} tokens")
        if DEBUG_REALTIME:
            print(f"  TOTAL: {usage_data.total_tokens:,} tokens")
        if DEBUG_REALTIME:
            print("-"*80)
        if DEBUG_REALTIME:
            print(f"COST BREAKDOWN:")
        if DEBUG_REALTIME:
            print(f"  Audio Input: ${audio_input_cost:.4f}")
        if DEBUG_REALTIME:
            print(f"  Audio Input (cached): ${cached_audio_input_cost:.4f}")
        if DEBUG_REALTIME:
            print(f"  Audio Output: ${audio_output_cost:.4f}")
        if DEBUG_REALTIME:
            print(f"  Text Input: ${text_input_cost:.4f}")
        if DEBUG_REALTIME:
            print(f"  Text Input (cached): ${cached_text_input_cost:.4f}")
        if DEBUG_REALTIME:
            print(f"  Text Output: ${text_output_cost:.4f}")
        if DEBUG_REALTIME:
            print(f"  TOTAL COST: ${total_cost:.4f}")
        if DEBUG_REALTIME:
            print("-"*80)
        if DEBUG_REALTIME:
            print(f"Cost per minute: ${cost_per_minute:.4f}")
        if DEBUG_REALTIME:
            print(f"Tokens per minute: {tokens_per_minute:,.0f}")
        if DEBUG_REALTIME:
            print("="*80)

        # Fetch organization costs from OpenAI API
        organization_cost = None
        organization_cost_data = None

        if usage_data.start_time:
            import time
            current_time = int(time.time())

            start_time = usage_data.start_time

            if start_time > current_time:
                if DEBUG_REALTIME:
                    print(f"[ORG_COSTS] Start timestamp is in the future! start={start_time}, current={current_time}")
                if DEBUG_REALTIME:
                    print(f"[ORG_COSTS] Skipping organization cost fetch - invalid timestamp")
            else:
                try:
                    if DEBUG_REALTIME:
                        print(f"[ORG_COSTS] Fetching organization costs for session {usage_data.session_id}")
                    if DEBUG_REALTIME:
                        print(f"[ORG_COSTS] Start time: {start_time} ({datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat()})")

                    org_costs = await fetch_organization_costs(
                        start_time=start_time,
                        end_time=None
                    )

                    if org_costs and "data" in org_costs:
                        organization_cost_data = org_costs

                        for bucket in org_costs["data"]:
                            aggregation_timestamp = bucket.get("aggregation_timestamp")
                            results = bucket.get("results", [])

                            for result in results:
                                if "amount" in result:
                                    organization_cost = result["amount"].get("value", 0)
                                    if DEBUG_REALTIME:
                                        print(f"[ORG_COSTS] Organization cost for bucket {aggregation_timestamp}: ${organization_cost:.4f}")
                                    break

                            if organization_cost is not None:
                                break

                        if organization_cost is not None:
                            if DEBUG_REALTIME:
                                print(f"[ORG_COSTS] Final organization cost: ${organization_cost:.4f}")
                            if DEBUG_REALTIME:
                                print(f"[ORG_COSTS] Calculated cost: ${total_cost:.4f}")
                            if DEBUG_REALTIME:
                                print(f"[ORG_COSTS] Difference: ${abs(organization_cost - total_cost):.4f}")
                        else:
                            if DEBUG_REALTIME:
                                print(f"[ORG_COSTS] No cost data found in API response")
                    else:
                        if DEBUG_REALTIME:
                            print(f"[ORG_COSTS] No data in organization costs response")

                except Exception as org_error:
                    if DEBUG_REALTIME:
                        print(f"[ORG_COSTS] Error fetching organization costs: {str(org_error)}")
                    if DEBUG_REALTIME:
                        print(f"[ORG_COSTS] Full traceback: {traceback.format_exc()}")

        # Store in MongoDB
        usage_log = {
            "user_id": user_id,
            "session_id": usage_data.session_id,
            "language": usage_data.language,
            "level": usage_data.level,
            "topic": usage_data.topic,
            "model": model,
            "audio_input_tokens": usage_data.audio_input_tokens,
            "audio_output_tokens": usage_data.audio_output_tokens,
            "text_input_tokens": usage_data.text_input_tokens,
            "text_output_tokens": usage_data.text_output_tokens,
            "cached_input_audio_tokens": usage_data.cached_input_audio_tokens,
            "cached_input_text_tokens": usage_data.cached_input_text_tokens,
            "total_tokens": usage_data.total_tokens,
            "audio_input_cost": audio_input_cost,
            "cached_audio_input_cost": cached_audio_input_cost,
            "audio_output_cost": audio_output_cost,
            "text_input_cost": text_input_cost,
            "cached_text_input_cost": cached_text_input_cost,
            "text_output_cost": text_output_cost,
            "total_cost": total_cost,
            "session_start": usage_data.session_start,
            "session_end": usage_data.session_end,
            "session_duration_seconds": usage_data.session_duration_seconds,
            "cost_per_minute": cost_per_minute,
            "tokens_per_minute": tokens_per_minute,
            "timestamp": datetime.now(timezone.utc),
            "start_time": usage_data.start_time,
            "end_time": usage_data.end_time,
            "organization_cost": organization_cost,
            "organization_cost_data": organization_cost_data
        }

        result = await usage_logs_collection.insert_one(usage_log)
        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] Stored in MongoDB with ID: {result.inserted_id}")

        return True

    except Exception as e:
        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] Background processing error: {str(e)}")
        return False

# Route Handlers

@router.get("/api/realtime/rate-limit-status")
async def check_rate_limit_status(current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    """
    Check rate limit status for realtime sessions WITHOUT consuming a token.
    Returns whether user is rate limited and how long to wait.

    This should be called BEFORE attempting to start a conversation session.
    """
    from rate_limiter import rate_limiter
    import time

    try:
        # Use user_id if authenticated, otherwise use "guest"
        identifier = str(current_user.id) if current_user else "guest"
        category = "realtime"  # Check realtime session limit

        # Get rate limit configuration
        config = rate_limiter.limits[category]
        window_seconds = config["window_seconds"]
        max_requests = config["max_requests"]

        # Check if rate limited (WITHOUT consuming a request)
        is_limited, retry_after = rate_limiter._is_rate_limited(identifier, category)

        if is_limited:
            # User is rate limited
            minutes_to_wait = max(1, int(retry_after / 60))

            return {
                "is_rate_limited": True,
                "retry_after_seconds": retry_after,
                "retry_after_minutes": minutes_to_wait,
                "message": f"You've practiced a lot! Take a {minutes_to_wait}-minute break to let your learning sink in. 🧘",
                "limit_info": {
                    "max_sessions": max_requests,
                    "window_hours": int(window_seconds / 3600),
                    "category": category
                }
            }
        else:
            # User is NOT rate limited
            # Calculate how many sessions they have left
            timestamps = rate_limiter.requests[identifier].get(category, [])
            cutoff = time.time() - window_seconds
            valid_requests = [ts for ts in timestamps if ts > cutoff]
            remaining_sessions = max_requests - len(valid_requests)

            return {
                "is_rate_limited": False,
                "remaining_sessions": remaining_sessions,
                "message": "You're good to go! Start your practice session.",
                "limit_info": {
                    "max_sessions": max_requests,
                    "window_hours": int(window_seconds / 3600),
                    "category": category
                }
            }

    except Exception as e:
        if DEBUG_REALTIME:
            print(f"[RATE_LIMIT_CHECK] Error checking rate limit: {str(e)}")
        # If there's an error, allow the session (fail open)
        return {
            "is_rate_limited": False,
            "message": "Rate limit check unavailable, proceeding...",
            "error": str(e)
        }

@router.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    from monitoring import send_error_alert, send_business_logic_alert, AlertContext, AlertSeverity
    import asyncio

    try:
        if DEBUG_REALTIME:
            print("="*80)
        if DEBUG_REALTIME:
            print(f"[PERFORMANCE] Creating ephemeral token with parallel optimization")
        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Language: {request.language}")
        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Level: {request.level}")
        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Topic: {request.topic}")
        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Session mode: {getattr(request, 'session_mode', 'NOT_SENT')}")
        if DEBUG_REALTIME:
            print(f"[DEBUG] news_context exists: {hasattr(request, 'news_context')}")
        if hasattr(request, 'news_context'):
            nc = request.news_context
            if DEBUG_REALTIME:
                print(f"[DEBUG] news_context is None: {nc is None}")
            if DEBUG_REALTIME:
                print(f"[DEBUG] news_context type: {type(nc)}")
            if nc is not None:
                if DEBUG_REALTIME:
                    print(f"[DEBUG] news_context length: {len(nc)}")
                if DEBUG_REALTIME:
                    print(f"[DEBUG] news_context preview: {nc[:200] if len(nc) > 200 else nc}")
            if DEBUG_REALTIME:
                print(f"[DEBUG] news_context is truthy: {bool(nc)}")
        if DEBUG_REALTIME:
            print("="*80)

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            context = AlertContext(
                endpoint="/api/realtime/token",
                method="POST",
                environment=os.getenv("ENVIRONMENT", "development")
            )
            await send_business_logic_alert(
                operation="OpenAI Token Generation",
                issue="OpenAI API key not configured",
                context=context,
                severity=AlertSeverity.CRITICAL
            )
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")

        # 🔥 CRITICAL FIX: Validate subscription and minutes before generating token
        if current_user:
            from subscription_service import SubscriptionService
            from database import database
            from bson import ObjectId

            if DEBUG_REALTIME:
                print(f"[SUBSCRIPTION_CHECK] Validating access for user {current_user.id}")

            # Get fresh user data from database
            user_doc = await database["users"].find_one({"_id": ObjectId(current_user.id)})

            if user_doc:
                # Check if free user's period has expired (should have been reset by cron job)
                subscription_plan = user_doc.get("subscription_plan", "try_learn")
                period_end = user_doc.get("current_period_end")

                if DEBUG_REALTIME:
                    print(f"[SUBSCRIPTION_CHECK] Plan: {subscription_plan}, Period end: {period_end}")

                # Auto-reset fallback for free users with expired periods (in case cron job missed it)
                if subscription_plan == "try_learn" and period_end:
                    now = datetime.now(timezone.utc)

                    # Make period_end timezone-aware if it isn't
                    if period_end.tzinfo is None:
                        period_end = period_end.replace(tzinfo=timezone.utc)

                    if now > period_end:
                        if DEBUG_REALTIME:
                            print(f"[SUBSCRIPTION_CHECK] ⚠️ Period expired {(now - period_end).days} days ago - auto-resetting as fallback")
                        await SubscriptionService.reset_monthly_usage(str(current_user.id))
                        if DEBUG_REALTIME:
                            print(f"[SUBSCRIPTION_CHECK] ✅ Period reset completed for user {current_user.id}")

            # Now validate if user can start a session with selected duration
            # Get selected duration from request (A1/A2 can select 3 or 5, others only 5)
            selected_duration = getattr(request, 'selected_duration', None) or 5

            can_start, message = await SubscriptionService.can_start_session(
                str(current_user.id),
                selected_duration_minutes=selected_duration
            )

            if DEBUG_REALTIME:
                print(f"[SUBSCRIPTION_CHECK] Can start: {can_start}, Message: {message}")
            if DEBUG_REALTIME:
                print(f"[SUBSCRIPTION_CHECK] Selected duration: {selected_duration} minutes")

            if not can_start:
                if DEBUG_REALTIME:
                    print(f"[SUBSCRIPTION_CHECK] ❌ Access denied for user {current_user.id}: {message}")
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_minutes",
                        "message": message,
                        "can_start": False,
                        "selected_duration": selected_duration
                    }
                )

            if DEBUG_REALTIME:
                print(f"[SUBSCRIPTION_CHECK] ✅ Access granted for user {current_user.id}")

        # PERFORMANCE OPTIMIZATION: Run voice fetch and instruction building in parallel
        async def fetch_voice_preference():
            """Fetch voice preference without blocking token generation"""
            if not current_user:
                return "alloy"

            try:
                from database import users_collection
                from bson import ObjectId

                user_doc = await users_collection.find_one(
                    {"_id": ObjectId(current_user.id)},
                    {"preferred_voice": 1}
                )

                if user_doc and "preferred_voice" in user_doc:
                    if DEBUG_REALTIME:
                        print(f"[VOICE] Fetched voice: {user_doc['preferred_voice']}")
                    return user_doc["preferred_voice"]

                if DEBUG_REALTIME:
                    print(f"[VOICE] No preference found, using default")
                return "alloy"
            except Exception as e:
                if DEBUG_REALTIME:
                    print(f"[VOICE] Error fetching voice: {str(e)}")
                return "alloy"

        async def fetch_active_learning_plan():
            """Fetch user's active learning plan if not provided"""
            # If learning_plan_data is already provided, use it
            if request.learning_plan_data:
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN] Using provided learning plan data")
                return request.learning_plan_data

            if not current_user:
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN] No current user, skipping")
                return None

            try:
                from database import database
                from bson import ObjectId

                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN] 🔍 Searching for learning plan:")
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN]    user_id: {current_user.id}")
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN]    language: {request.language.lower()}")
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN]    status: in_progress")

                # Fetch user's active learning plan
                plans_collection = database.learning_plans

                # First, check what learning plans exist for this user
                all_plans = await plans_collection.find({"user_id": current_user.id}).to_list(length=10)
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN] 📋 Found {len(all_plans)} total learning plans for user")
                for plan in all_plans:
                    if DEBUG_REALTIME:
                        print(f"[LEARNING_PLAN]    - Language: {plan.get('language')}, Status: {plan.get('status')}")

                # FIXED: Also match plans where status is missing/null (legacy plans)
                learning_plan = await plans_collection.find_one({
                    "user_id": current_user.id,
                    "$or": [
                        {"status": "in_progress"},  # New plans with explicit status
                        {"status": None},           # Legacy plans without status field
                        {"status": {"$exists": False}}  # Plans missing status entirely
                    ],
                    "language": request.language.lower()
                })

                if learning_plan:
                    if DEBUG_REALTIME:
                        print(f"[LEARNING_PLAN] ✅ Found active learning plan (status: {learning_plan.get('status', 'None')})")
                    if DEBUG_REALTIME:
                        print(f"[LEARNING_PLAN] 📚 Progress: {learning_plan.get('completed_sessions', 0)}/{learning_plan.get('total_sessions', 0)}")
                    return {
                        "plan_content": learning_plan.get("plan_content", {}),
                        "completed_sessions": learning_plan.get("completed_sessions", 0),
                        "total_sessions": learning_plan.get("total_sessions", 0),
                        # session_history carries structured_summary objects for continuity
                        "session_history": learning_plan.get("session_history", []),
                        "session_summaries": learning_plan.get("session_summaries", []),
                    }
                else:
                    if DEBUG_REALTIME:
                        print(f"[LEARNING_PLAN] ❌ No learning plan found for this language and user")
                    return None
            except Exception as e:
                if DEBUG_REALTIME:
                    print(f"[LEARNING_PLAN] ❌ Error fetching learning plan: {str(e)}")
                import traceback
                traceback.print_exc()
                return None

        # Run voice fetch and learning plan fetch in parallel
        voice_task = asyncio.create_task(fetch_voice_preference())
        learning_plan_task = asyncio.create_task(fetch_active_learning_plan())

        # Wait for learning plan data before building instructions (needed for context)
        learning_plan_data = await learning_plan_task
        if learning_plan_data:
            # Add learning plan data to request
            request.learning_plan_data = learning_plan_data

        # Build instructions (now with learning plan context if available)
        instructions = await build_universal_instructions(request)
        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Instructions created: {len(instructions)} characters")

        # DEBUG: Check if emoji instructions are included (for A1/A2)
        if request.level.upper() in ['A1', 'A2']:
            if '{{emoji:' in instructions:
                if DEBUG_REALTIME:
                    print(f"[DEBUG] ✅ Emoji markers found in instructions")
            else:
                if DEBUG_REALTIME:
                    print(f"[DEBUG] ❌ NO emoji markers in instructions!")

            # Show a snippet of the topic vocabulary section
            if 'TOPIC VOCABULARY' in instructions:
                start_idx = instructions.find('TOPIC VOCABULARY')
                snippet = instructions[start_idx:start_idx+500]
                if DEBUG_REALTIME:
                    print(f"[DEBUG] Topic vocab snippet:\n{snippet}")

        # NEW: Add Speaking DNA context for premium users
        if current_user and current_user.subscription_status in ["active", "trialing"]:
            try:
                from services.speaking_dna_service import speaking_dna_service

                # Determine session type
                session_type = "news" if request.news_context else "freestyle" if request.user_prompt else "learning"

                dna_context = await speaking_dna_service.build_coach_instructions(
                    user_id=str(current_user.id),
                    language=request.language.lower(),
                    session_type=session_type
                )

                if dna_context:
                    instructions += f"\n\n{dna_context}"
                    if DEBUG_REALTIME:
                        print(f"[DNA] Added Speaking DNA context: {len(dna_context)} characters")
            except Exception as e:
                if DEBUG_REALTIME:
                    print(f"[DNA] Error adding DNA context (non-fatal): {str(e)}")
                # Continue without DNA context - this is a premium feature

        # Wait for voice preference (should be done by now)
        preferred_voice = await voice_task

        # Use request voice if provided, otherwise use fetched preference
        selected_voice = request.voice or preferred_voice

        if DEBUG_REALTIME:
            print(f"[VOICE] User preferred voice: {preferred_voice}")
        if DEBUG_REALTIME:
            print(f"[VOICE] Request voice: {request.voice}")
        if DEBUG_REALTIME:
            print(f"[VOICE] Selected voice: {selected_voice}")

        # Create ephemeral token with complete configuration
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")

        # Import truncation config helper
        from prompt_optimization_helpers import build_truncation_config

        # Define function tools for grammar correction (all levels, unless disabled)
        # PROMPT_V3 lowers the reporting threshold: the V3 prompt tells the model
        # to correct explicitly and to report every fix, so the tool description
        # must match (guide: prompt/tool misalignment degrades tool calling).
        _prompt_v3_on = os.getenv("PROMPT_V3", "false").lower() == "true"
        _grammar_tool_desc = (
            "Show the student a correction card for a CLEAR grammar, verb-form, word-choice, or "
            "word-order mistake. This is the ONLY way corrections reach the student, so call it "
            "FIRST — before you speak — whenever there is a real error, then just acknowledge briefly "
            "out loud. Do NOT call it for a sentence that is already correct, and do NOT call it for "
            "minor pronunciation slips."
            if _prompt_v3_on else
            "Report a MAJOR grammar mistake made by the student. Only call this for significant errors in articles, verb conjugation, or word order. Do NOT call for minor pronunciation or vocabulary issues."
        )
        tools = []
        if not request.disable_corrections:
            tools = [
                {
                    "type": "function",
                    "name": "report_grammar_mistake",
                    "description": _grammar_tool_desc,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "wrong": {
                                "type": "string",
                                "description": "The incorrect word or phrase the student said"
                            },
                            "correct": {
                                "type": "string",
                                "description": "The correct word or phrase"
                            },
                            "tip": {
                                "type": "string",
                                "description": "Brief explanation (8-12 words) of why this is the correct form"
                            }
                        },
                        "required": ["wrong", "correct", "tip"]
                    }
                }
            ]

        # Strip {emoji:name} markers from the instructions text that goes to audio.
        # The model sometimes reads these aloud literally ("emoji book") which sounds
        # ridiculous. Markers are display-only and must never appear in spoken audio.
        import re as _re
        audio_safe_instructions = _re.sub(r'\{emoji:[^}]+\}', '', instructions)

        # Prepend a hard-stop rule at the very top of instructions where the model
        # is most likely to attend to it — before any other content.
        audio_safe_instructions = (
            "CRITICAL AUDIO RULE: Your responses will be spoken aloud. "
            "NEVER say the words 'emoji', 'bracket', '{', '}', or any emoji name. "
            "If you want to express emotion or illustrate a concept, use natural words only.\n\n"
            + audio_safe_instructions
        )

        # GA API shape: session config nested under "session" key.
        # Endpoint: /v1/realtime/client_secrets (GA, replaces beta /v1/realtime/sessions)
        # GA requires: type="realtime", audio.input/output nested structure, output_modalities
        #
        # TRANSCRIPTION MODEL: gpt-realtime-whisper is the only model in the
        # gpt-realtime-* family designed for *streaming* transcription, so it stays
        # consistent with the gpt-realtime-mini voice model. gpt-4o-transcribe is a
        # file/request-response model that mis-decodes short, accented A1/A2 speech
        # in the Realtime path (wrong-language output, garbled transcripts) even
        # though the voice model understood the user correctly — this breaks the
        # displayed transcript, grammar corrections, and Speaking DNA. It is also
        # retired (2026-06-01) along with whisper-1 / gpt-4o-mini-transcribe.
        #
        # Override via REALTIME_TRANSCRIBE_MODEL to roll back to gpt-4o-transcribe
        # if needed. delay=high trades ~200-400ms latency for higher accuracy,
        # which is the right call for non-native beginners.
        transcription_model = os.getenv("REALTIME_TRANSCRIBE_MODEL", "gpt-realtime-whisper")
        transcription_delay = os.getenv("REALTIME_TRANSCRIBE_DELAY", "high")
        session_config = {
            "type": "realtime",
            "model": model,
            "instructions": audio_safe_instructions,
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "transcription": {
                        "model": transcription_model,
                        "language": get_language_iso_code(request.language) if request.language else "en",
                        # delay tunes the latency/accuracy tradeoff (minimal|low|medium|high|xhigh).
                        # Only gpt-realtime-whisper supports it; omitted for other models.
                        **({"delay": transcription_delay} if transcription_model == "gpt-realtime-whisper" else {})
                    },
                    "turn_detection": {
                        "type": "semantic_vad",
                        "eagerness": "low",
                        "create_response": True,
                        "interrupt_response": True
                    },
                    "noise_reduction": {
                        "type": "near_field"
                    }
                },
                "output": {
                    "voice": selected_voice
                }
            },
            "truncation": build_truncation_config()
        }

        # Add tools if available
        if tools:
            session_config["tools"] = tools
            if DEBUG_REALTIME:
                print(f"[TOOLS] Added {len(tools)} function tools for {request.level} level")

        payload = {"session": session_config}

        if DEBUG_REALTIME:
            print(f"[TRUNCATION] Configured with retention_ratio=0.8, post_instructions limit=8000 tokens")

        # DEBUG: Check if news context is in instructions
        if request.news_context:
            if "NEWS CONVERSATION" in instructions or "NEWS DISCUSSION" in instructions or "📰" in instructions:
                if DEBUG_REALTIME:
                    print(f"[DEBUG] ✅ NEWS CONTEXT FOUND IN INSTRUCTIONS")
                # Check for vocabulary
                if "KEY VOCABULARY" in instructions:
                    if DEBUG_REALTIME:
                        print(f"[DEBUG] ✅ Vocabulary section included")
                else:
                    if DEBUG_REALTIME:
                        print(f"[DEBUG] ⚠️ Vocabulary section NOT found")
                # Check for discussion questions
                if "DISCUSSION QUESTIONS" in instructions:
                    if DEBUG_REALTIME:
                        print(f"[DEBUG] ✅ Discussion questions included")
                else:
                    if DEBUG_REALTIME:
                        print(f"[DEBUG] ⚠️ Discussion questions NOT found")
                # Find and print the news section
                if "📰" in instructions:
                    news_start = instructions.find("📰")
                    if DEBUG_REALTIME:
                        print(f"[DEBUG] News section preview: {instructions[news_start:news_start+500]}")
            else:
                if DEBUG_REALTIME:
                    print(f"[DEBUG] ❌ WARNING: news_context exists but NOT found in instructions!")
                if DEBUG_REALTIME:
                    print(f"[DEBUG] Instructions length: {len(instructions)}")
                if DEBUG_REALTIME:
                    print(f"[DEBUG] Instructions preview: {instructions[:500]}")

        if DEBUG_REALTIME:
            print("[UNIVERSAL] Sending ephemeral token request to OpenAI...")

        try:
            http_client = get_openai_http_client()
            response = await asyncio.wait_for(
                http_client.post(
                    "https://api.openai.com/v1/realtime/client_secrets",
                    headers={
                        "Authorization": f"Bearer {openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ),
                timeout=8.0,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "realtime_unavailable",
                    "message": "Voice session service temporarily unavailable. Please retry.",
                    "retry_after": 3,
                },
            )

        if response.status_code != 200:
            error_text = response.text
            if DEBUG_REALTIME:
                print(f"OpenAI API error: {error_text}")
            raise HTTPException(status_code=response.status_code, detail=error_text)

        result = response.json()

        # GA API returns {"value": "ek_...", "expires_at": ..., "session": {...}}
        # Mobile app expects beta shape: {"id": "...", "model": "...", "client_secret": {"value": "..."}, ...}
        # Transform GA response to beta-compatible shape so the mobile app doesn't break.
        if "value" in result and "client_secret" not in result:
            ga_session = result.get("session", {})
            result = {
                "id": ga_session.get("id", result.get("id", "unknown")),
                "model": ga_session.get("model", model),
                "client_secret": {
                    "value": result["value"],
                    "expires_at": result.get("expires_at")
                },
                "object": result.get("object", "realtime.client_secret"),
                "expires_at": result.get("expires_at"),
                "session": ga_session,
            }
            if DEBUG_REALTIME:
                print(f"[GA_COMPAT] Transformed GA response to beta shape, id={result['id']}")

        # Log session creation
        session_id = result.get('id', 'unknown')
        if DEBUG_REALTIME:
            print("="*80)
        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] SESSION CREATED")
        if DEBUG_REALTIME:
            print(f"Session ID: {session_id}")
        if DEBUG_REALTIME:
            print(f"User ID: {current_user.id if current_user else 'guest'}")
        if DEBUG_REALTIME:
            print(f"Language: {request.language}")
        if DEBUG_REALTIME:
            print(f"Level: {request.level}")
        if DEBUG_REALTIME:
            print(f"Timestamp: {datetime.now().isoformat()}")
        if DEBUG_REALTIME:
            print("="*80)

        # Add session configuration based on authentication status
        is_guest = current_user is None

        # Check if this is a final assessment to set appropriate duration
        is_final_assessment = False
        assessment_level = None
        if request.assessment_data and 'learning_plan_data' in request.assessment_data:
            learning_plan_data = request.assessment_data.get('learning_plan_data', {})
            completed_sessions = learning_plan_data.get('completed_sessions', 0)
            total_sessions = learning_plan_data.get('total_sessions', 8)
            is_final_assessment = completed_sessions >= total_sessions
            if is_final_assessment:
                assessment_level = request.level  # Use the level from the request

        # Set duration based on context
        if is_final_assessment and assessment_level:
            # Final assessment: duration based on CEFR level
            duration_map = {
                'A1': 120,  # 2 minutes
                'A2': 180,  # 3 minutes
                'B1': 240,  # 4 minutes
                'B2': 300,  # 5 minutes
                'C1': 300,  # 5 minutes
                'C2': 300   # 5 minutes
            }
            max_duration_seconds = duration_map.get(assessment_level.upper(), 300)
            if DEBUG_REALTIME:
                print(f"[SESSION_CONFIG] Final assessment mode - Level {assessment_level} - Duration: {max_duration_seconds}s")
        else:
            # Regular practice session - use selected_duration from request
            if is_guest:
                max_duration_seconds = 120  # 2 min for guests
            else:
                # Use selected_duration (3 or 5 minutes) for authenticated users
                selected_duration = getattr(request, 'selected_duration', None) or 5
                max_duration_seconds = selected_duration * 60
                if DEBUG_REALTIME:
                    print(f"[SESSION_CONFIG] Using selected_duration: {selected_duration} minutes ({max_duration_seconds}s)")

        if DEBUG_REALTIME:
            print(f"[SESSION_CONFIG] User type: {'guest' if is_guest else 'authenticated'}")
        if DEBUG_REALTIME:
            print(f"[SESSION_CONFIG] Max duration: {max_duration_seconds}s ({max_duration_seconds//60} minutes)")

        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Ephemeral token created successfully")

        # Return OpenAI result + session configuration
        return {
            **result,  # OpenAI session data (id, client_secret, etc.)
            "session_config": {
                "max_duration_seconds": max_duration_seconds,
                "is_guest": is_guest,
                "duration_minutes": max_duration_seconds / 60,
                "assessment_duration_seconds": 30 if is_guest else 60
            }
        }

    except HTTPException:
        # Re-raise HTTPExceptions (like 403 for insufficient minutes) without modification
        raise
    except Exception as e:
        if DEBUG_REALTIME:
            print(f"[UNIVERSAL] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/realtime/usage-log")
async def log_realtime_usage(
    usage_data: RealtimeUsageData,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Store realtime API usage data and calculate costs.

    PERFORMANCE OPTIMIZATION: Returns immediately while processing happens in background.
    Response time reduced from 3,041ms to <100ms (97% faster).
    """
    try:
        # Get user ID
        user_id = current_user.id if current_user else usage_data.user_id

        # Log basic session info immediately
        if DEBUG_REALTIME:
            print("="*80)
        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] SESSION QUEUED FOR PROCESSING")
        if DEBUG_REALTIME:
            print(f"Session ID: {usage_data.session_id}")
        if DEBUG_REALTIME:
            print(f"User ID: {user_id or 'guest'}")
        if DEBUG_REALTIME:
            print(f"Language: {usage_data.language}")
        if DEBUG_REALTIME:
            print(f"Level: {usage_data.level}")
        if DEBUG_REALTIME:
            print(f"Duration: {usage_data.session_duration_seconds}s")
        if DEBUG_REALTIME:
            print(f"Total Tokens: {usage_data.total_tokens:,}")
        if DEBUG_REALTIME:
            print("="*80)

        # Add heavy processing to background tasks
        background_tasks.add_task(
            process_usage_log_background,
            usage_data,
            current_user
        )

        # Return immediately with success
        return {
            "success": True,
            "status": "queued",
            "session_id": usage_data.session_id,
            "message": "Usage data queued for processing"
        }

    except Exception as e:
        if DEBUG_REALTIME:
            print(f"[USAGE_LOG] Error queueing usage log: {str(e)}")
        # Still return success so frontend doesn't fail, but log the error
        return {
            "success": True,
            "status": "error",
            "session_id": usage_data.session_id,
            "message": "Usage data queued with errors"
        }

@router.get("/api/realtime/semantic-feedback")
async def get_semantic_feedback_monitoring():
    """
    Monitor semantic VAD feedback incidents and conversation quality metrics
    Provides debugging information for semantic VAD issues
    """
    try:
        from database import database
        from datetime import datetime, timezone, timedelta

        # Get feedback data from the last 24 hours
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        feedback_collection = database.sentence_analysis_feedback

        # Get recent feedback incidents
        recent_feedback = await feedback_collection.find({
            "timestamp": {"$gte": twenty_four_hours_ago}
        }).sort("timestamp", -1).limit(100).to_list(100)

        # Analyze feedback patterns
        feedback_stats = {
            "total_incidents": len(recent_feedback),
            "feedback_types": {},
            "languages": {},
            "levels": {},
            "common_issues": [],
            "quality_ratings": []
        }

        for feedback in recent_feedback:
            # Count feedback types
            feedback_type = feedback.get("feedback_type", "unknown")
            feedback_stats["feedback_types"][feedback_type] = feedback_stats["feedback_types"].get(feedback_type, 0) + 1

            # Count languages
            language = feedback.get("language", "unknown")
            feedback_stats["languages"][language] = feedback_stats["languages"].get(language, 0) + 1

            # Count levels
            level = feedback.get("level", "unknown")
            feedback_stats["levels"][level] = feedback_stats["levels"].get(level, 0) + 1

            # Collect quality ratings
            if feedback.get("user_rating"):
                feedback_stats["quality_ratings"].append(feedback.get("user_rating"))

        # Calculate average quality rating
        if feedback_stats["quality_ratings"]:
            feedback_stats["average_quality_rating"] = sum(feedback_stats["quality_ratings"]) / len(feedback_stats["quality_ratings"])
        else:
            feedback_stats["average_quality_rating"] = None

        # Identify common issues
        analysis_rejection_count = feedback_stats["feedback_types"].get("analysis_rejection", 0)
        stuck_state_count = feedback_stats["feedback_types"].get("stuck_state", 0)

        if analysis_rejection_count > 5:
            feedback_stats["common_issues"].append("High analysis rejection rate")
        if stuck_state_count > 3:
            feedback_stats["common_issues"].append("Users getting stuck in conversation state")

        # Get semantic VAD specific metrics
        semantic_vad_metrics = {
            "feedback_loops_detected": 0,
            "background_conversation_triggers": 0,
            "ai_self_hearing_incidents": 0
        }

        for feedback in recent_feedback:
            user_comment = feedback.get("user_comment", "").lower()
            if "feedback" in user_comment or "echo" in user_comment:
                semantic_vad_metrics["feedback_loops_detected"] += 1
            if "background" in user_comment or "other conversation" in user_comment:
                semantic_vad_metrics["background_conversation_triggers"] += 1
            if "ai hearing itself" in user_comment or "self hearing" in user_comment:
                semantic_vad_metrics["ai_self_hearing_incidents"] += 1

        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring_period": "24 hours",
            "feedback_stats": feedback_stats,
            "semantic_vad_metrics": semantic_vad_metrics,
            "recent_feedback": [
                {
                    "id": str(feedback["_id"]),
                    "timestamp": feedback.get("timestamp"),
                    "feedback_type": feedback.get("feedback_type"),
                    "language": feedback.get("language"),
                    "level": feedback.get("level"),
                    "user_rating": feedback.get("user_rating"),
                    "user_comment": feedback.get("user_comment", "")[:100] + "..." if len(feedback.get("user_comment", "")) > 100 else feedback.get("user_comment", ""),
                    "resolved": feedback.get("resolved", False)
                }
                for feedback in recent_feedback[:20]
            ]
        }

    except Exception as e:
        if DEBUG_REALTIME:
            print(f"Error getting semantic feedback monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting semantic feedback monitoring: {str(e)}")

@router.get("/api/realtime/model-config")
async def get_model_config():
    """
    Get the current OpenAI Realtime API model configuration
    """
    try:
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")

        return {
            "model": model,
            "configured_via": "environment_variable" if os.getenv("OPENAI_REALTIME_MODEL") else "default",
            "available_models": ["gpt-realtime-mini", "gpt-4o-mini-realtime-preview"],
            "default_model": "gpt-realtime-mini"
        }
    except Exception as e:
        if DEBUG_REALTIME:
            print(f"Error getting model config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model config: {str(e)}")
