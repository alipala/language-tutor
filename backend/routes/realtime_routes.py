"""
Realtime API Routes
Handles OpenAI Realtime API token generation, usage logging, and model configuration
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import httpx
from openai import OpenAI

from auth import get_optional_current_user_from_request
from models import UserResponse

# Initialize router
router = APIRouter()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client with error handling
try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully (realtime_routes)")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method (realtime_routes)")
    else:
        print(f"Error initializing OpenAI client: {str(e)}")
        raise

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
    iso_code = language_map.get(language_lower, "en")

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

def build_universal_instructions(request: TutorSessionRequest) -> str:
    """
    Build instructions that work reliably on all browsers.

    PHASE 0 OPTIMIZATION: Now includes personality/tone section with 2-sentence limit
    and uses compressed session summaries for 93% token reduction.
    """

    language = request.language.lower()
    level = request.level.upper()

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
        build_optimized_assessment_context
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

        print(f"Assessment context integrated: {len(assessment_context)} characters")

    # Extract learning plan data if available
    if request.assessment_data and 'learning_plan_data' in request.assessment_data:
        print(f"[LEARNING_PLAN] Integrating learning plan data into instructions")

        learning_plan_data = request.assessment_data.get('learning_plan_data', {})
        plan_content = learning_plan_data.get('plan_content', {})

        if plan_content:
            completed_sessions = learning_plan_data.get('completed_sessions', 0)
            total_sessions = learning_plan_data.get('total_sessions', 8)

            # Detect if this is a FINAL ASSESSMENT
            is_final_assessment = completed_sessions >= total_sessions
            if is_final_assessment:
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
                print(f"[FINAL_ASSESSMENT] Special assessment instructions created: {len(learning_plan_context)} characters")
                print(f"[FINAL_ASSESSMENT] Current level: {current_level}, Next level: {next_level}")

            else:
                # Regular learning plan session (not final assessment)
                sessions_per_week = 2
                current_week_number = min((completed_sessions // sessions_per_week) + 1, len(plan_content.get('weekly_schedule', [])))
                current_session_in_week = (completed_sessions % sessions_per_week) + 1

                weekly_schedule = plan_content.get('weekly_schedule', [])
                current_week = weekly_schedule[current_week_number - 1] if current_week_number <= len(weekly_schedule) else weekly_schedule[0] if weekly_schedule else None

                if current_week:
                    week_focus = current_week.get('focus', 'Building foundational skills')
                    week_activities = current_week.get('activities', [])

                    previous_sessions_context = ""
                    session_summaries = learning_plan_data.get('session_summaries', [])
                    if session_summaries:
                        previous_sessions_context = build_compressed_session_context(session_summaries, max_summaries=3)

                        previous_sessions_context += """
LEARNING PROGRESSION:
- Build upon insights from previous sessions
- Reference progress made in earlier conversations
- Continue developing skills identified in previous summaries"""

                    learning_plan_context = f"""
📚 LEARNING PLAN CONTEXT:
- Plan Title: {plan_content.get('title', 'Personalized Learning Plan')}
- Plan Overview: {plan_content.get('overview', 'Customized based on assessment results')}

CURRENT WEEK FOCUS (Week {current_week_number}, Session {current_session_in_week}):
- Focus Area: {week_focus}
- Key Activities: {', '.join(week_activities[:3]) if week_activities else 'Practice conversation skills'}
{previous_sessions_context}

CONVERSATION GUIDANCE:
- Center the conversation around this week's focus: "{week_focus}"
- Incorporate activities from the learning plan: {', '.join(week_activities[:2]) if week_activities else 'speaking practice'}
- Reference the student's learning journey and progress
- Connect speaking practice to their personalized learning objectives
- Encourage practice of specific skills mentioned in the weekly activities
- Build upon previous session insights and maintain learning continuity"""

                    print(f"Learning plan context integrated: {len(learning_plan_context)} characters")
                    print(f"Current week {current_week_number} focus: {week_focus}")
                    print(f"Current week activities: {week_activities}")
                    print(f"Session {current_session_in_week} of week {current_week_number}")

    # Handle custom topic
    if request.topic == "custom" and request.user_prompt:
        print(f"[CUSTOM_TOPIC] Creating universal custom topic instructions")

        research_content = ""
        if request.research_data:
            research_content = request.research_data
            print(f"Using provided research data: {len(research_content)} chars")
        else:
            # Fallback research
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Educational research assistant for language learners."},
                        {"role": "user", "content": f"Educational info about: {request.user_prompt}"}
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
                if response and response.choices:
                    research_content = response.choices[0].message.content
                    print(f"Fallback research completed")
            except Exception as e:
                print(f"Research failed: {str(e)}")

        # Add all optimization sections
        personality_section = build_personality_tone_section(language, level)
        pronunciations = build_reference_pronunciations()
        sample_phrases = build_sample_phrases(language)
        conversation_flow = build_conversation_flow_section(language, level, request.user_prompt)
        safety_escalation = build_safety_escalation_section(language)
        speed_instructions = build_speed_instructions()

        instructions = f"""{personality_section}

{pronunciations}

{sample_phrases}

{speed_instructions}

{conversation_flow}

{safety_escalation}

CUSTOM TOPIC CONVERSATION: '{request.user_prompt}'

You are a PROACTIVE {language} language tutor for {level} level students who MANAGES the conversation flow.

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

TOPIC INFORMATION:
{research_content if research_content else f'Use your knowledge about {request.user_prompt}.'}

FIRST MESSAGE REQUIREMENT:
Your first message MUST immediately discuss '{request.user_prompt}'.
Do NOT say generic greetings like "Hello! How can I help you?"

Start like: "Let's talk about {request.user_prompt}! [Share interesting facts]. What interests you about this topic?"

CRITICAL: Keep all conversation about '{request.user_prompt}'. Do not deviate from this topic regardless of what the user requests.
- Use the topic information provided
- Adapt language complexity to {level} level
- Be engaging and educational
- Apply personalized feedback based on assessment results
- If learning plan context is available, connect the topic to the student's learning objectives"""

        print(f"Custom topic instructions: {len(instructions)} characters")
        return instructions

    # Handle regular topics
    elif request.topic and request.topic != "custom":
        # Enhanced topic mapping with detailed descriptions
        topic_details = {
            "travel": {
                "name": "Travel & Tourism",
                "description": "Discuss travel destinations, experiences, planning trips, transportation, accommodations, cultural experiences, and travel tips. Practice vocabulary related to airports, hotels, restaurants, sightseeing, and navigation."
            },
            "food": {
                "name": "Food & Cooking",
                "description": "Talk about cuisines, recipes, restaurants, cooking techniques, ingredients, dietary preferences, and food culture. Practice vocabulary for ordering food, describing flavors, cooking methods, and dining experiences."
            },
            "work": {
                "name": "Work & Career",
                "description": "Discuss jobs, career goals, workplace situations, professional development, job interviews, office culture, and work-life balance. Practice business vocabulary, professional communication, and workplace scenarios."
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
                "description": "Talk about pets, animals, wildlife, animal care, pet ownership, and animal behavior. Practice vocabulary for different animals, pet care, animal characteristics, and human-animal relationships."
            }
        }

        topic_info = topic_details.get(request.topic, {
            "name": request.topic.title(),
            "description": f"Discuss various aspects of {request.topic} and related topics."
        })

        topic_name = topic_info["name"]
        topic_description = topic_info["description"]

        # Add all optimization sections
        personality_section = build_personality_tone_section(language, level)
        pronunciations = build_reference_pronunciations()
        sample_phrases = build_sample_phrases(language)
        conversation_flow = build_conversation_flow_section(language, level, topic_name)
        safety_escalation = build_safety_escalation_section(language)
        speed_instructions = build_speed_instructions()

        instructions = f"""{personality_section}

{pronunciations}

{sample_phrases}

{speed_instructions}

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
1. EDUCATIONAL FOCUS ONLY: Only discuss language learning and the specified topic
2. REFUSE HARMFUL CONTENT: Immediately decline discussions about:
   - Violence, weapons, illegal activities
   - Sexual content, adult themes, inappropriate relationships
   - Hate speech, discrimination, offensive language
   - Personal information requests (addresses, phone numbers, etc.)
   - Political extremism, conspiracy theories
   - Self-harm, dangerous activities, substance abuse
3. OFF-TOPIC REDIRECT: If user tries to discuss unrelated topics or avoid the topic, say:
   "I understand, but let's focus on practicing {language} with our topic: {topic_name}. This helps improve your language skills and serves your learning objectives."
4. LEARNING PLAN ADHERENCE: ALWAYS redirect conversations back to the learning objectives. NEVER allow general conversation that doesn't serve the learning plan.

MANDATORY TOPIC FOCUS:
- You MUST keep the conversation focused on {topic_name}
- If the user tries to change topics or avoid the subject, redirect them back to {topic_name}
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

TOPIC DETAILS:
Topic: {topic_name}
Description: {topic_description}

CONVERSATION GUIDANCE:
- Use the topic description to guide conversation areas and vocabulary
- Focus on the specific aspects mentioned in the description
- Incorporate relevant vocabulary and scenarios from the topic description
- Create exercises and activities based on the topic's scope

Start your first message by introducing {topic_name} and asking an engaging question about it.

Example: "Let's talk about {topic_name}! What interests you most about this topic?"

CRITICAL: Keep the conversation focused on {topic_name}. Do not deviate from this topic regardless of what the user requests.
Apply personalized feedback based on assessment results.
If learning plan context is available, connect the topic to the student's learning objectives."""

        print(f"Regular topic instructions: {len(instructions)} characters")
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

        instructions = f"""{personality_section}

{pronunciations}

{sample_phrases}

{speed_instructions}

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
- If learning plan context is provided (but NOT final assessment): Start by referencing the current week's focus and immediately begin practicing the specified activities. Example: "Great to see you! This week we're focusing on [week focus]. Let's start by [first activity]. Tell me about..."
- If NO learning plan context: Start with "{config['greeting']}" and ask what the student wants to practice today

CRITICAL:
- If FINAL ASSESSMENT MODE is active, follow the assessment structure and opening greeting EXACTLY as specified above.
- If learning plan context is available (non-assessment), you MUST focus the entire conversation on the current week's learning objectives."""

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
                "cached_text": 0.30 / 1_000_000
            }
        }

        # Always use environment variable model for cost calculation
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")

        print(f"[USAGE_LOG] Using model from environment: {model}")

        if hasattr(usage_data, 'model') and usage_data.model and usage_data.model != model:
            print(f"[USAGE_LOG] Note: usage_data.model was '{usage_data.model}' but using environment model '{model}' for cost calculation")

        if model not in PRICING:
            print(f"[USAGE_LOG] Unknown model '{model}', defaulting to gpt-realtime-mini pricing")
            model = "gpt-realtime-mini"

        pricing = PRICING[model]

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
        print("="*80)
        print(f"[USAGE_LOG] SESSION COMPLETED")
        print(f"Session ID: {usage_data.session_id}")
        print(f"User ID: {current_user.id if current_user else usage_data.user_id or 'guest'}")
        print(f"Language: {usage_data.language}")
        print(f"Level: {usage_data.level}")
        print(f"Duration: {usage_data.session_duration_seconds}s ({duration_str})")
        print(f"Model: {usage_data.model}")
        print("-"*80)
        print(f"TOKEN USAGE:")
        print(f"  Audio Input: {usage_data.audio_input_tokens:,} tokens")
        print(f"  Audio Input (cached): {usage_data.cached_input_audio_tokens:,} tokens")
        print(f"  Audio Output: {usage_data.audio_output_tokens:,} tokens")
        print(f"  Text Input: {usage_data.text_input_tokens:,} tokens")
        print(f"  Text Input (cached): {usage_data.cached_input_text_tokens:,} tokens")
        print(f"  Text Output: {usage_data.text_output_tokens:,} tokens")
        print(f"  TOTAL: {usage_data.total_tokens:,} tokens")
        print("-"*80)
        print(f"COST BREAKDOWN:")
        print(f"  Audio Input: ${audio_input_cost:.4f}")
        print(f"  Audio Input (cached): ${cached_audio_input_cost:.4f}")
        print(f"  Audio Output: ${audio_output_cost:.4f}")
        print(f"  Text Input: ${text_input_cost:.4f}")
        print(f"  Text Input (cached): ${cached_text_input_cost:.4f}")
        print(f"  Text Output: ${text_output_cost:.4f}")
        print(f"  TOTAL COST: ${total_cost:.4f}")
        print("-"*80)
        print(f"Cost per minute: ${cost_per_minute:.4f}")
        print(f"Tokens per minute: {tokens_per_minute:,.0f}")
        print("="*80)

        # Fetch organization costs from OpenAI API
        organization_cost = None
        organization_cost_data = None

        if usage_data.start_time:
            import time
            current_time = int(time.time())

            start_time = usage_data.start_time

            if start_time > current_time:
                print(f"[ORG_COSTS] Start timestamp is in the future! start={start_time}, current={current_time}")
                print(f"[ORG_COSTS] Skipping organization cost fetch - invalid timestamp")
            else:
                try:
                    print(f"[ORG_COSTS] Fetching organization costs for session {usage_data.session_id}")
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
                                    print(f"[ORG_COSTS] Organization cost for bucket {aggregation_timestamp}: ${organization_cost:.4f}")
                                    break

                            if organization_cost is not None:
                                break

                        if organization_cost is not None:
                            print(f"[ORG_COSTS] Final organization cost: ${organization_cost:.4f}")
                            print(f"[ORG_COSTS] Calculated cost: ${total_cost:.4f}")
                            print(f"[ORG_COSTS] Difference: ${abs(organization_cost - total_cost):.4f}")
                        else:
                            print(f"[ORG_COSTS] No cost data found in API response")
                    else:
                        print(f"[ORG_COSTS] No data in organization costs response")

                except Exception as org_error:
                    print(f"[ORG_COSTS] Error fetching organization costs: {str(org_error)}")
                    import traceback
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
        print(f"[USAGE_LOG] Stored in MongoDB with ID: {result.inserted_id}")

        return True

    except Exception as e:
        print(f"[USAGE_LOG] Background processing error: {str(e)}")
        return False

# Route Handlers
@router.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    from monitoring import send_error_alert, send_business_logic_alert, AlertContext, AlertSeverity
    import asyncio

    try:
        print("="*80)
        print(f"[PERFORMANCE] Creating ephemeral token with parallel optimization")
        print(f"[UNIVERSAL] Language: {request.language}")
        print(f"[UNIVERSAL] Level: {request.level}")
        print(f"[UNIVERSAL] Topic: {request.topic}")
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
                    print(f"[VOICE] Fetched voice: {user_doc['preferred_voice']}")
                    return user_doc["preferred_voice"]

                print(f"[VOICE] No preference found, using default")
                return "alloy"
            except Exception as e:
                print(f"[VOICE] Error fetching voice: {str(e)}")
                return "alloy"

        # Run voice fetch and instruction building in parallel
        voice_task = asyncio.create_task(fetch_voice_preference())

        # Build instructions (can run while voice is being fetched)
        instructions = build_universal_instructions(request)
        print(f"[UNIVERSAL] Instructions created: {len(instructions)} characters")

        # Wait for voice preference (should be done by now)
        preferred_voice = await voice_task

        # Use request voice if provided, otherwise use fetched preference
        selected_voice = request.voice or preferred_voice

        print(f"[VOICE] User preferred voice: {preferred_voice}")
        print(f"[VOICE] Request voice: {request.voice}")
        print(f"[VOICE] Selected voice: {selected_voice}")

        # Create ephemeral token with complete configuration
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")

        # Import truncation config helper
        from prompt_optimization_helpers import build_truncation_config

        payload = {
            "model": model,
            "voice": selected_voice,
            "instructions": instructions,
            "modalities": ["audio", "text"],
            "input_audio_transcription": {
                "model": "gpt-4o-transcribe" if os.getenv("USE_GPT4O_TRANSCRIBE", "true").lower() == "true" else "whisper-1",
                "language": get_language_iso_code(request.language) if request.language else "en"
            },
            "turn_detection": {
                "type": "semantic_vad",
                "eagerness": "low",
                "create_response": True,
                "interrupt_response": True
            },
            "input_audio_noise_reduction": {
                "type": "near_field"
            },
            "truncation": build_truncation_config()
        }

        print(f"[TRUNCATION] Configured with retention_ratio=0.8, post_instructions limit=8000 tokens")

        print("[UNIVERSAL] Sending ephemeral token request to OpenAI...")

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0
            )

        if response.status_code != 200:
            error_text = response.text
            print(f"OpenAI API error: {error_text}")
            raise HTTPException(status_code=response.status_code, detail=error_text)

        result = response.json()

        # Log session creation
        session_id = result.get('id', 'unknown')
        print("="*80)
        print(f"[USAGE_LOG] SESSION CREATED")
        print(f"Session ID: {session_id}")
        print(f"User ID: {current_user.id if current_user else 'guest'}")
        print(f"Language: {request.language}")
        print(f"Level: {request.level}")
        print(f"Timestamp: {datetime.now().isoformat()}")
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
            print(f"[SESSION_CONFIG] Final assessment mode - Level {assessment_level} - Duration: {max_duration_seconds}s")
        else:
            # Regular practice session
            max_duration_seconds = 120 if is_guest else 300  # 2 min for guests, 5 min for registered

        print(f"[SESSION_CONFIG] User type: {'guest' if is_guest else 'authenticated'}")
        print(f"[SESSION_CONFIG] Max duration: {max_duration_seconds}s ({max_duration_seconds//60} minutes)")

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

    except Exception as e:
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
        print("="*80)
        print(f"[USAGE_LOG] SESSION QUEUED FOR PROCESSING")
        print(f"Session ID: {usage_data.session_id}")
        print(f"User ID: {user_id or 'guest'}")
        print(f"Language: {usage_data.language}")
        print(f"Level: {usage_data.level}")
        print(f"Duration: {usage_data.session_duration_seconds}s")
        print(f"Total Tokens: {usage_data.total_tokens:,}")
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
            "available_models": ["gpt-realtime-mini", "gpt-realtime"],
            "default_model": "gpt-realtime-mini"
        }
    except Exception as e:
        print(f"Error getting model config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model config: {str(e)}")
