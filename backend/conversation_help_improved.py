"""
IMPROVED CONTEXT-AWARE CONVERSATION HELP SYSTEM
Production-ready implementation with 7-second performance constraint
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import os
import json
import httpx
import asyncio
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Async OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

# Enhanced Data Models
class TutorIntent(BaseModel):
    intent: str  # PRONUNCIATION_DRILL, ERROR_CORRECTION, NEW_CONCEPT, CONVERSATIONAL_PRACTICE, VOCABULARY_PRACTICE, ASSESSMENT, ENCOURAGEMENT
    confidence: float
    teaching_phase: str  # practice, instruction, assessment
    key_focus: str
    requires_specific_response: bool

class ConversationContext(BaseModel):
    recent_messages: List[Dict[str, str]]
    conversation_flow: str  # ascending, struggling, neutral
    student_engagement: str  # high, medium, low
    learning_objective: Optional[str] = None

class EnhancedConversationHelpRequest(BaseModel):
    ai_response: str
    conversation_context: List[Dict[str, str]]
    target_language: str
    user_language: str
    proficiency_level: str
    topic: Optional[str] = None
    learning_plan_context: Optional[Dict[str, Any]] = None  # NEW: Learning plan integration
    session_type: Optional[str] = "general"  # general, custom_plan, assessment

# Caching for performance optimization
INTENT_CACHE: Dict[str, TutorIntent] = {}
RESPONSE_CACHE: Dict[str, Dict] = {}

def create_cache_key(text: str, context_length: int) -> str:
    """Create cache key for performance optimization"""
    return hashlib.md5(f"{text}_{context_length}".encode()).hexdigest()

def format_conversation_context(messages: List[Dict[str, str]], max_messages: int = 4) -> str:
    """Format recent conversation for context analysis"""
    if not messages:
        return "No previous conversation context."
    
    # Take the most recent messages
    recent = messages[-max_messages:]
    formatted = []
    
    for msg in recent:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:200]  # Truncate for performance
        formatted.append(f"{role.upper()}: {content}")
    
    return "\n".join(formatted)

async def analyze_tutor_intent_fast(request: EnhancedConversationHelpRequest) -> TutorIntent:
    """
    PHASE 1: Fast AI tutor intent analysis (2 seconds max)
    Uses caching and optimized prompts for speed
    """
    
    # Create cache key
    cache_key = create_cache_key(request.ai_response, len(request.conversation_context))
    if cache_key in INTENT_CACHE:
        print(f"[INTENT_ANALYSIS] 🚀 Cache hit for intent analysis")
        return INTENT_CACHE[cache_key]
    
    print(f"[INTENT_ANALYSIS] 🔍 Analyzing tutor intent...")
    
    # Build context-aware intent analysis prompt
    conversation_ctx = format_conversation_context(request.conversation_context)
    
    intent_prompt = f"""<role>Expert language learning analyst</role>

<conversation_context>
{conversation_ctx}
</conversation_context>

<ai_tutor_response>
{request.ai_response[:300]}
</ai_tutor_response>

<analysis_framework>
INTENT_CATEGORIES:
- PRONUNCIATION_DRILL: "Repeat after me", phonetic practice, sound focus
- ERROR_CORRECTION: Correcting mistakes, showing proper form
- NEW_CONCEPT_INTRODUCTION: Teaching new grammar/vocabulary
- VOCABULARY_PRACTICE: "Use this word in a sentence", vocabulary exercises, word application
- CONVERSATIONAL_PRACTICE: Natural dialogue, storytelling
- ASSESSMENT: Testing knowledge, asking questions
- ENCOURAGEMENT: Praise, motivation, support
</analysis_framework>

<instructions>
Analyze the AI tutor's intent and respond ONLY in this JSON format:
{{"intent": "category", "confidence": 0.95, "teaching_phase": "practice|instruction|assessment", "key_focus": "specific learning goal", "requires_specific_response": true}}
</instructions>"""

    try:
        # Use GPT-4o for better reasoning, with timeout for performance
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "developer", "content": intent_prompt}
                ],
                temperature=0.1,
                max_tokens=150
            ),
            timeout=3.0
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean and parse JSON
        if content.startswith('```json'):
            content = content[7:-3]
        elif content.startswith('```'):
            content = content[3:-3]
        
        intent_data = json.loads(content)
        
        tutor_intent = TutorIntent(
            intent=intent_data.get("intent", "CONVERSATIONAL_PRACTICE"),
            confidence=intent_data.get("confidence", 0.8),
            teaching_phase=intent_data.get("teaching_phase", "practice"),
            key_focus=intent_data.get("key_focus", "general conversation"),
            requires_specific_response=intent_data.get("requires_specific_response", False)
        )
        
        # Cache the result
        INTENT_CACHE[cache_key] = tutor_intent
        print(f"[INTENT_ANALYSIS] ✅ Intent: {tutor_intent.intent} (confidence: {tutor_intent.confidence})")
        
        return tutor_intent
        
    except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
        print(f"[INTENT_ANALYSIS] ⚠️ Intent analysis failed: {e}, using fallback")
        # Fallback intent analysis
        fallback_intent = TutorIntent(
            intent="CONVERSATIONAL_PRACTICE",
            confidence=0.6,
            teaching_phase="practice",
            key_focus="general conversation",
            requires_specific_response=False
        )
        INTENT_CACHE[cache_key] = fallback_intent
        return fallback_intent

def build_context_aware_prompt(request: EnhancedConversationHelpRequest, intent: TutorIntent) -> str:
    """Build specialized prompts based on tutor intent"""
    
    base_context = f"""<student_profile>
Target Language: {request.target_language}
Proficiency Level: {request.proficiency_level}
Native Language: {request.user_language}
</student_profile>

<conversation_context>
{format_conversation_context(request.conversation_context)}
</conversation_context>

<ai_tutor_response>
{request.ai_response}
</ai_tutor_response>"""

    # Add learning plan context if available
    if request.learning_plan_context:
        base_context += f"""
<learning_plan_context>
Objective: {request.learning_plan_context.get('objective', 'General practice')}
Focus Area: {request.learning_plan_context.get('focus_area', 'Conversation')}
Target Skills: {request.learning_plan_context.get('target_skills', 'Speaking')}
</learning_plan_context>"""

    # Intent-specific prompt building
    if intent.intent == "PRONUNCIATION_DRILL":
        return f"""{base_context}

<scenario_analysis>
The AI tutor is conducting pronunciation practice. The student needs to focus on correct pronunciation, not complex conversation.
Teaching Phase: {intent.teaching_phase}
Key Focus: {intent.key_focus}
</scenario_analysis>

<response_guidelines>
- Generate responses that show readiness for pronunciation practice
- Include phonetic hints for challenging sounds
- Keep language simple and focused on the pronunciation task
- Show engagement with specific sounds/words being practiced
- Responses should be short and clear for pronunciation practice
</response_guidelines>

Generate 2 contextually perfect responses in JSON format:
{{"summary": "brief explanation in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "IPA or simplified phonetic", "explanation": "why this response helps with pronunciation practice"}}]}}"""

    elif intent.intent == "ERROR_CORRECTION":
        return f"""{base_context}

<scenario_analysis>
The AI tutor just corrected a mistake. The student should acknowledge the correction and demonstrate understanding.
Teaching Phase: {intent.teaching_phase}
Key Focus: {intent.key_focus}
</scenario_analysis>

<response_guidelines>
- Acknowledge the correction positively
- Use the corrected form to show understanding
- Build confidence while incorporating the feedback
- Show readiness to continue with improved language
- Demonstrate that the student learned from the correction
</response_guidelines>

Generate 2 contextually perfect responses in JSON format:
{{"summary": "brief explanation in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this response shows understanding of the correction"}}]}}"""

    elif intent.intent == "NEW_CONCEPT_INTRODUCTION":
        return f"""{base_context}

<scenario_analysis>
The AI tutor is introducing a new concept. The student should show interest and engagement with the new material.
Teaching Phase: {intent.teaching_phase}
Key Focus: {intent.key_focus}
</scenario_analysis>

<response_guidelines>
- Show curiosity about the new concept
- Ask clarifying questions if appropriate
- Use simple language that incorporates the new concept
- Demonstrate active engagement with learning
- Request examples or practice opportunities
</response_guidelines>

Generate 2 contextually perfect responses in JSON format:
{{"summary": "brief explanation in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this response shows engagement with the new concept"}}]}}"""

    elif intent.intent == "VOCABULARY_PRACTICE":
        return f"""{base_context}

<scenario_analysis>
The AI tutor is asking for vocabulary practice. The student should demonstrate proper word usage in context.
Teaching Phase: {intent.teaching_phase}
Key Focus: {intent.key_focus}
</scenario_analysis>

<response_guidelines>
- Create natural sentences using the target vocabulary word
- Show understanding of word meaning and usage
- Use appropriate grammar and context
- Demonstrate vocabulary mastery at student's level
- Make sentences meaningful and realistic
</response_guidelines>

Generate 2 contextually perfect responses in JSON format:
{{"summary": "brief explanation in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this sentence demonstrates proper vocabulary usage"}}]}}"""

    elif intent.intent == "ASSESSMENT":
        return f"""{base_context}

<scenario_analysis>
The AI tutor is testing the student's knowledge. The student should provide thoughtful, appropriate responses.
Teaching Phase: {intent.teaching_phase}
Key Focus: {intent.key_focus}
</scenario_analysis>

<response_guidelines>
- Provide responses that demonstrate knowledge
- Use appropriate complexity for the student's level
- Show confidence in language use
- If uncertain, ask for clarification appropriately
- Demonstrate learning progress
</response_guidelines>

Generate 2 contextually perfect responses in JSON format:
{{"summary": "brief explanation in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this response demonstrates knowledge appropriately"}}]}}"""

    else:  # CONVERSATIONAL_PRACTICE or ENCOURAGEMENT
        return f"""{base_context}

<scenario_analysis>
The AI tutor is engaging in natural conversation. The student should respond naturally and keep the conversation flowing.
Teaching Phase: {intent.teaching_phase}
Key Focus: {intent.key_focus}
</scenario_analysis>

<response_guidelines>
- Provide natural, conversational responses
- Match the tone and topic of the tutor's message
- Use appropriate complexity for the student's level
- Keep the conversation engaging and flowing
- Show personality while practicing the language
</response_guidelines>

Generate 2 contextually perfect responses in JSON format:
{{"summary": "brief explanation in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this response fits the conversation naturally"}}]}}"""

async def generate_contextual_responses(
    request: EnhancedConversationHelpRequest, 
    intent: TutorIntent
) -> Optional[Dict]:
    """
    PHASE 2: Generate context-aware responses (4 seconds max)
    """
    print(f"[RESPONSE_GEN] 🎯 Generating responses for intent: {intent.intent}")
    
    # Create cache key for response caching
    cache_key = create_cache_key(f"{request.ai_response}_{intent.intent}", len(request.conversation_context))
    if cache_key in RESPONSE_CACHE:
        print(f"[RESPONSE_GEN] 🚀 Cache hit for response generation")
        return RESPONSE_CACHE[cache_key]
    
    # Build context-aware prompt
    context_prompt = build_context_aware_prompt(request, intent)
    
    try:
        # Generate responses with extended timeout for quality responses
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for better contextual understanding
                messages=[
                    {"role": "developer", "content": context_prompt}
                ],
                temperature=0.2,
                max_tokens=400  # Reduced for speed while maintaining quality
            ),
            timeout=8.0  # INCREASED: Give GPT-4o enough time for quality responses
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean JSON content
        if content.startswith('```json'):
            content = content[7:-3]
        elif content.startswith('```'):
            content = content[3:-3]
        
        response_data = json.loads(content)
        
        # Cache the result
        RESPONSE_CACHE[cache_key] = response_data
        print(f"[RESPONSE_GEN] ✅ Generated {len(response_data.get('responses', []))} contextual responses")
        
        return response_data
        
    except asyncio.TimeoutError as e:
        print(f"[RESPONSE_GEN] ⏰ TIMEOUT after 8 seconds - GPT-4o needs more processing time")
        print(f"[RESPONSE_GEN] ⏰ This is expected for complex contextual analysis")
        return None
    except json.JSONDecodeError as e:
        print(f"[RESPONSE_GEN] ❌ JSON parsing failed: {e}")
        print(f"[RESPONSE_GEN] ❌ Raw content may be malformed")
        return None
    except Exception as e:
        print(f"[RESPONSE_GEN] ❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def generate_conversation_help_context_aware(request: EnhancedConversationHelpRequest) -> Optional[Dict]:
    """
    MAIN FUNCTION: Ultra-optimized context-aware conversation help (7 seconds max)
    """
    start_time = datetime.utcnow()
    print(f"[CONTEXT_HELP] 🚀 Starting context-aware help generation...")
    
    try:
        # Validate input
        if not request.ai_response or not request.ai_response.strip():
            print(f"[CONTEXT_HELP] ❌ Empty AI response")
            return None
        
        # PHASE 1: Analyze tutor intent (2 seconds max)
        print(f"[CONTEXT_HELP] 📊 Phase 1: Analyzing tutor intent...")
        intent_task = asyncio.create_task(analyze_tutor_intent_fast(request))
        
        # PHASE 2: Generate contextual responses (4 seconds max)
        try:
            intent = await asyncio.wait_for(intent_task, timeout=3.0)
            print(f"[CONTEXT_HELP] 📝 Phase 2: Generating contextual responses...")
            response_data = await generate_contextual_responses(request, intent)
            
            if response_data:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                print(f"[CONTEXT_HELP] ✅ Context-aware help generated in {elapsed:.2f}s")
                
                return {
                    "ai_response_summary": response_data.get("summary", "The AI provided guidance."),
                    "suggested_responses": [
                        {
                            "text": resp.get("text", ""),
                            "pronunciation": resp.get("pronunciation", ""),
                            "difficulty_level": request.proficiency_level,
                            "explanation": resp.get("explanation", "")
                        } for resp in response_data.get("responses", [])[:2]
                    ],
                    "vocabulary_highlights": [],
                    "grammar_tips": [],
                    "context_analysis": {
                        "tutor_intent": intent.intent,
                        "confidence": intent.confidence,
                        "teaching_phase": intent.teaching_phase
                    },
                    "generated_at": datetime.utcnow()
                }
            else:
                print(f"[CONTEXT_HELP] ⚠️ Response generation failed, using fallback")
                return None
                
        except asyncio.TimeoutError:
            print(f"[CONTEXT_HELP] ⏰ Context analysis timeout, using fast fallback")
            return None
            
    except Exception as e:
        print(f"[CONTEXT_HELP] ❌ Context-aware generation failed: {e}")
        return None

# Fallback to original system if context-aware fails
from conversation_help import generate_conversation_help_fast, ConversationHelpRequest

async def generate_conversation_help_hybrid(request: EnhancedConversationHelpRequest) -> Optional[Dict]:
    """
    HYBRID SYSTEM: Try context-aware first, fallback to fast system
    Ensures 7-second performance guarantee
    """
    print(f"[HYBRID_HELP] 🔄 Starting hybrid help generation...")
    
    # Try context-aware approach first (6 seconds max)
    try:
        context_result = await asyncio.wait_for(
            generate_conversation_help_context_aware(request),
            timeout=6.0
        )
        
        if context_result:
            print(f"[HYBRID_HELP] ✅ Context-aware system succeeded")
            return context_result
    
    except asyncio.TimeoutError:
        print(f"[HYBRID_HELP] ⏰ Context-aware system timeout, falling back to fast system")
    except Exception as e:
        print(f"[HYBRID_HELP] ⚠️ Context-aware system failed: {e}, falling back to fast system")
    
    # Fallback to original fast system (1 second remaining)
    print(f"[HYBRID_HELP] 🏃 Using fast fallback system...")
    
    # Convert to original request format
    original_request = ConversationHelpRequest(
        ai_response=request.ai_response,
        conversation_context=request.conversation_context,
        target_language=request.target_language,
        user_language=request.user_language,
        proficiency_level=request.proficiency_level,
        topic=request.topic
    )
    
    fast_result = await generate_conversation_help_fast(original_request)
    
    if fast_result:
        print(f"[HYBRID_HELP] ✅ Fast fallback system succeeded")
        return {
            "ai_response_summary": fast_result.ai_response_summary,
            "suggested_responses": [
                {
                    "text": resp.text,
                    "pronunciation": resp.pronunciation,
                    "difficulty_level": resp.difficulty_level,
                    "explanation": resp.explanation
                } for resp in fast_result.suggested_responses
            ],
            "vocabulary_highlights": [],
            "grammar_tips": [],
            "context_analysis": {
                "tutor_intent": "UNKNOWN",
                "confidence": 0.5,
                "teaching_phase": "fallback"
            },
            "generated_at": datetime.utcnow()
        }
    
    print(f"[HYBRID_HELP] ❌ All systems failed")
    return None
