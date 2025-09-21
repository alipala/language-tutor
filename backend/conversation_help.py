from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client with error handling
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully in conversation_help")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        # Alternative initialization without proxies
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method in conversation_help")
    else:
        print(f"Error initializing OpenAI client in conversation_help: {str(e)}")
        raise

class ConversationHelpRequest(BaseModel):
    ai_response: str
    conversation_context: List[Dict[str, str]]  # Recent conversation messages
    target_language: str
    user_language: str  # User's native language for help content
    proficiency_level: str
    topic: Optional[str] = None

class SuggestedResponse(BaseModel):
    text: str
    pronunciation: str
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    explanation: str

class VocabularyItem(BaseModel):
    word: str
    definition: str
    pronunciation: str
    example_sentence: str
    difficulty_level: str

class GrammarTip(BaseModel):
    pattern: str
    explanation: str
    example: str
    difficulty_level: str

class CulturalNote(BaseModel):
    context: str
    explanation: str
    relevance: str

class ConversationHelpResponse(BaseModel):
    ai_response_summary: str
    suggested_responses: List[SuggestedResponse]
    vocabulary_highlights: List[VocabularyItem]
    grammar_tips: List[GrammarTip]
    cultural_context: Optional[CulturalNote] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class UserHelpSettings(BaseModel):
    user_id: str
    help_enabled: bool = True
    help_language: str = "english"  # Language for help content
    show_pronunciation: bool = True
    show_grammar_tips: bool = True
    show_cultural_notes: bool = True
    show_vocabulary: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Pre-computed response templates for instant fallbacks
INSTANT_RESPONSE_TEMPLATES = {
    "dutch": {
        "beginner": [
            {"text": "Ik begrijp het", "pronunciation": "ɪk bəˈɣrɛip ət", "explanation": "I understand"},
            {"text": "Kun je dat herhalen?", "pronunciation": "kʏn jə dɑt hərˈhaːlə", "explanation": "Can you repeat that?"},
            {"text": "Dat is interessant", "pronunciation": "dɑt ɪs ɪntərɛˈsɑnt", "explanation": "That's interesting"}
        ]
    },
    "spanish": {
        "beginner": [
            {"text": "Entiendo", "pronunciation": "en-tjen-do", "explanation": "I understand"},
            {"text": "¿Puedes repetir?", "pronunciation": "pwe-des re-pe-tir", "explanation": "Can you repeat?"},
            {"text": "Es interesante", "pronunciation": "es in-te-re-san-te", "explanation": "It's interesting"}
        ]
    },
    "french": {
        "beginner": [
            {"text": "Je comprends", "pronunciation": "zhuh kom-prahn", "explanation": "I understand"},
            {"text": "Pouvez-vous répéter?", "pronunciation": "poo-vay voo ray-pay-tay", "explanation": "Can you repeat?"},
            {"text": "C'est intéressant", "pronunciation": "say an-tay-ray-sahn", "explanation": "That's interesting"}
        ]
    },
    "german": {
        "beginner": [
            {"text": "Ich verstehe", "pronunciation": "ikh fer-shtay-uh", "explanation": "I understand"},
            {"text": "Können Sie das wiederholen?", "pronunciation": "kur-nen zee das vee-der-ho-len", "explanation": "Can you repeat that?"},
            {"text": "Das ist interessant", "pronunciation": "das ist in-ter-es-sant", "explanation": "That's interesting"}
        ]
    },
    "portuguese": {
        "beginner": [
            {"text": "Eu entendo", "pronunciation": "eh-oo en-ten-do", "explanation": "I understand"},
            {"text": "Pode repetir?", "pronunciation": "po-de re-pe-tir", "explanation": "Can you repeat?"},
            {"text": "É interessante", "pronunciation": "eh in-te-re-san-te", "explanation": "That's interesting"}
        ]
    },
    "italian": {
        "beginner": [
            {"text": "Capisco", "pronunciation": "ka-pee-sko", "explanation": "I understand"},
            {"text": "Puoi ripetere?", "pronunciation": "pwo-ee ri-pe-te-re", "explanation": "Can you repeat?"},
            {"text": "È interessante", "pronunciation": "eh in-te-res-san-te", "explanation": "That's interesting"}
        ]
    },
    "english": {
        "beginner": [
            {"text": "I understand", "pronunciation": "aɪ ˌʌndərˈstænd", "explanation": "Shows comprehension"},
            {"text": "Can you repeat that?", "pronunciation": "kæn ju rɪˈpit ðæt", "explanation": "Ask for repetition"},
            {"text": "That's interesting", "pronunciation": "ðæts ˈɪntrəstɪŋ", "explanation": "Show engagement"}
        ]
    }
}

async def generate_conversation_help_fast(request: ConversationHelpRequest) -> Optional[ConversationHelpResponse]:
    """
    ULTRA-OPTIMIZED conversation help generation - 2-5 second target
    """
    try:
        print(f"[CONVERSATION_HELP] 🚀 Starting ultra-fast help generation...")
        print(f"[CONVERSATION_HELP] AI response: {request.ai_response[:100]}...")
        
        # Validate input
        if not request.ai_response or not request.ai_response.strip():
            print(f"[CONVERSATION_HELP] ❌ Empty AI response")
            return None
        
        # Smart truncation for speed
        def smart_truncate(text: str, max_length: int = 100) -> str:
            if len(text) <= max_length:
                return text
            
            # Try to cut at sentence boundary
            truncated = text[:max_length]
            last_period = truncated.rfind('.')
            last_question = truncated.rfind('?')
            last_exclamation = truncated.rfind('!')
            
            best_cut = max(last_period, last_question, last_exclamation)
            if best_cut > max_length * 0.6:
                return text[:best_cut + 1]
            
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.7:
                return text[:last_space] + "..."
            
            return text[:max_length] + "..."

        # Ultra-minimal prompt for maximum speed
        truncated_response = smart_truncate(request.ai_response, 100)
        
        prompt = f"""AI tutor said: "{truncated_response}"
Target language: {request.target_language}
Student level: {request.proficiency_level}
Help language: {request.user_language}

Generate 2 contextual responses in JSON:
{{"summary": "brief summary in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this response fits"}}]}}"""

        print(f"[CONVERSATION_HELP] 📤 Sending optimized prompt to OpenAI...")
        
        # Maximum speed OpenAI call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
            timeout=10,
            stream=False
        )
        
        print(f"[CONVERSATION_HELP] ✅ OpenAI response received")
        
        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            print(f"[CONVERSATION_HELP] ❌ Invalid OpenAI response structure")
            return None

        content = response.choices[0].message.content.strip()
        print(f"[CONVERSATION_HELP] Raw content: {content}")
        
        # Clean JSON content
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        
        if content.endswith('```'):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        try:
            help_data = json.loads(content)
            print(f"[CONVERSATION_HELP] ✅ JSON parsed successfully")
            
            # Extract responses
            responses_key = "responses" if "responses" in help_data else "suggested_responses"
            raw_responses = help_data.get(responses_key, [])
            
            if not raw_responses:
                print(f"[CONVERSATION_HELP] ❌ No responses in parsed data")
                return None
            
            # Build response objects
            suggested_responses = []
            for resp in raw_responses[:2]:  # Limit to 2 responses
                if isinstance(resp, dict) and resp.get("text"):
                    suggested_responses.append(SuggestedResponse(
                        text=resp.get("text", ""),
                        pronunciation=resp.get("pronunciation", ""),
                        difficulty_level=resp.get("difficulty_level", "beginner"),
                        explanation=resp.get("explanation", "")
                    ))
            
            if not suggested_responses:
                print(f"[CONVERSATION_HELP] ❌ No valid responses created")
                return None
            
            print(f"[CONVERSATION_HELP] ✅ Generated {len(suggested_responses)} contextual responses")
            
            return ConversationHelpResponse(
                ai_response_summary=help_data.get("summary", "The AI provided guidance."),
                suggested_responses=suggested_responses,
                vocabulary_highlights=[],
                grammar_tips=[]
            )
            
        except json.JSONDecodeError as e:
            print(f"[CONVERSATION_HELP] ❌ JSON parsing failed: {e}")
            print(f"[CONVERSATION_HELP] Content that failed: {content}")
            return None
            
    except Exception as e:
        print(f"[CONVERSATION_HELP] ❌ Fast generation failed: {e}")
        return None

# Keep the original function as backup
async def generate_conversation_help(request: ConversationHelpRequest) -> ConversationHelpResponse:
    """
    Original comprehensive help generation (now used as backup)
    """
    # Use the fast version by default
    return await generate_conversation_help_fast(request)

async def get_user_help_settings(user_id: str) -> UserHelpSettings:
    """
    Get user's help system settings from database
    """
    try:
        from database import database
        
        settings_collection = database.conversation_help_settings
        settings_doc = await settings_collection.find_one({"user_id": user_id})
        
        if settings_doc:
            return UserHelpSettings(**settings_doc)
        else:
            # Return default settings for new users
            return UserHelpSettings(user_id=user_id)
    
    except Exception as e:
        print(f"Error getting user help settings: {e}")
        # Return default settings on error
        return UserHelpSettings(user_id=user_id)

async def update_user_help_settings(user_id: str, settings: Dict[str, Any]) -> bool:
    """
    Update user's help system settings in database
    """
    try:
        from database import database
        
        settings_collection = database.conversation_help_settings
        
        # Update timestamp
        settings["updated_at"] = datetime.utcnow()
        
        result = await settings_collection.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
        
        return result.acknowledged
    
    except Exception as e:
        print(f"Error updating user help settings: {e}")
        return False

async def track_help_usage(user_id: str, help_type: str, language: str, duration_minutes: float = 0.0) -> bool:
    """
    Track help system usage for analytics with proper duration tracking
    """
    try:
        from database import database
        
        analytics_collection = database.conversation_help_analytics
        
        # VALIDATION: Prevent meaningless 0-duration sessions from cluttering the database
        if help_type in ["session_completed", "conversation_ended"] and duration_minutes <= 0:
            print(f"[CONVERSATION_HELP] ⚠️ Rejecting {help_type} with invalid duration: {duration_minutes}")
            return False
        
        usage_doc = {
            "user_id": user_id,
            "help_type": help_type,  # "modal_opened", "response_used", "vocabulary_clicked", etc.
            "language": language,
            "duration_minutes": duration_minutes,  # CRITICAL FIX: Add duration tracking
            "created_at": datetime.utcnow(),  # Use created_at for consistency
            "timestamp": datetime.utcnow()
        }
        
        result = await analytics_collection.insert_one(usage_doc)
        
        # CRITICAL FIX: If this is a completed session with duration > 0, update subscription usage
        if duration_minutes > 0 and help_type in ["session_completed", "conversation_ended"]:
            print(f"[CONVERSATION_HELP] 🔄 Session completed with {duration_minutes} minutes - updating subscription usage")
            
            try:
                from subscription_service import SubscriptionService
                from models import SpeakingTimeTrackingRequest
                
                # Track subscription usage for sessions with actual duration
                speaking_time_request = SpeakingTimeTrackingRequest(
                    user_id=user_id,
                    speaking_minutes=duration_minutes,
                    session_completed=True  # This will increment both minutes AND session count
                )
                
                tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)
                if tracking_success:
                    print(f"[CONVERSATION_HELP] ✅ Subscription usage updated: {duration_minutes} minutes for user {user_id}")
                else:
                    print(f"[CONVERSATION_HELP] ⚠️ Subscription tracking failed - user may have exceeded limits")
                    
            except Exception as subscription_error:
                print(f"[CONVERSATION_HELP] ⚠️ Failed to update subscription usage: {subscription_error}")
                # Don't fail the analytics tracking if subscription update fails
        
        return result.acknowledged
    
    except Exception as e:
        print(f"Error tracking help usage: {e}")
        return False
