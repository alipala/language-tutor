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

async def generate_conversation_help_fast(request: ConversationHelpRequest) -> ConversationHelpResponse:
    """
    ULTRA-OPTIMIZED conversation help generation - 2-5 second target
    """
    try:
        # 🚀 STRATEGY 1: Smart Input Truncation (preserves context, speeds processing)
        def smart_truncate(text: str, max_length: int = 50) -> str:
            """Intelligently truncate while preserving key information"""
            if len(text) <= max_length:
                return text
            
            # Try to cut at sentence boundary
            truncated = text[:max_length]
            last_period = truncated.rfind('.')
            last_question = truncated.rfind('?')
            last_exclamation = truncated.rfind('!')
            
            # Find the best cut point
            best_cut = max(last_period, last_question, last_exclamation)
            if best_cut > max_length * 0.6:  # If we can preserve 60%+ of content
                return text[:best_cut + 1]
            
            # Otherwise, cut at word boundary
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.7:
                return text[:last_space] + "..."
            
            return text[:max_length] + "..."

        # 🚀 STRATEGY 2: Ultra-Minimal Prompt (50% size reduction)
        truncated_response = smart_truncate(request.ai_response, 75)
        
        ultra_minimal_prompt = f"""AI: "{truncated_response}"
Lang: {request.target_language}
Level: {request.proficiency_level}

JSON (2 responses):
{{"summary": "what AI said in {request.user_language}", "responses": [{{"text": "{request.target_language} response", "pronunciation": "guide", "explanation": "why"}}]}}"""

        # 🚀 STRATEGY 3: Maximum Speed OpenAI Call
        print(f"[CONVERSATION_HELP] Ultra-fast generation for: {truncated_response[:30]}...")
        print(f"[CONVERSATION_HELP] 📤 Sending prompt to OpenAI: {ultra_minimal_prompt[:100]}...")
        
        try:
            print(f"[CONVERSATION_HELP] 🔄 Making OpenAI API call...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": ultra_minimal_prompt}],
                temperature=0,      # Zero temperature for maximum speed
                max_tokens=300,     # 🚀 Increased to prevent truncation
                timeout=5,          # 🚀 5 seconds for more reliable completion
                stream=False,
                top_p=0.1,         # 🚀 Slightly more flexible for complete responses
                frequency_penalty=0,
                presence_penalty=0
            )
            print(f"[CONVERSATION_HELP] ✅ OpenAI API call completed successfully")

            if not response.choices:
                print(f"[CONVERSATION_HELP] ❌ No response choices in OpenAI response, returning None")
                return None
            
            if not response.choices[0].message:
                print(f"[CONVERSATION_HELP] ❌ No message in first choice, returning None")
                return None
            
            if not response.choices[0].message.content:
                print(f"[CONVERSATION_HELP] ❌ No content in message, returning None")
                return None

            # 🚀 STRATEGY 4: Ultra-Fast JSON parsing
            try:
                content = response.choices[0].message.content
                print(f"[CONVERSATION_HELP] Full raw response: {content}")
                
                # Try to parse the new format first - handle markdown code blocks
                try:
                    # Remove markdown code blocks if present
                    clean_content = content.strip()
                    print(f"[CONVERSATION_HELP] Content after strip: '{clean_content[:50]}...'")
                    
                    if clean_content.startswith('```json'):
                        clean_content = clean_content[7:]  # Remove ```json
                        print(f"[CONVERSATION_HELP] Removed ```json prefix")
                    elif clean_content.startswith('```'):
                        clean_content = clean_content[3:]   # Remove ```
                        print(f"[CONVERSATION_HELP] Removed ``` prefix")
                    
                    if clean_content.endswith('```'):
                        clean_content = clean_content[:-3]  # Remove closing ```
                        print(f"[CONVERSATION_HELP] Removed ``` suffix")
                    
                    clean_content = clean_content.strip()
                    print(f"[CONVERSATION_HELP] Final clean content: {clean_content}")
                    
                    help_content = json.loads(clean_content)
                    print(f"[CONVERSATION_HELP] ✅ JSON parsed successfully")
                    responses_key = "responses" if "responses" in help_content else "suggested_responses"
                    
                    suggested_responses = []
                    for resp in help_content.get(responses_key, [])[:2]:
                        suggested_responses.append(SuggestedResponse(
                            text=resp.get("text", ""),
                            pronunciation=resp.get("pronunciation", ""),
                            difficulty_level="beginner",
                            explanation=resp.get("explanation", "")
                        ))

                    if len(suggested_responses) > 0:
                        print(f"[CONVERSATION_HELP] ✅ Generated {len(suggested_responses)} contextual responses")
                        return ConversationHelpResponse(
                            ai_response_summary=help_content.get("summary", help_content.get("ai_response_summary", "The AI provided guidance.")),
                            suggested_responses=suggested_responses,
                            vocabulary_highlights=[],
                            grammar_tips=[]
                        )
                    else:
                        print(f"[CONVERSATION_HELP] ❌ No valid responses, returning None")
                        return None
                        
                except json.JSONDecodeError as e:
                    print(f"[CONVERSATION_HELP] ❌ JSON parsing failed: {e}")
                    print(f"[CONVERSATION_HELP] Attempting to fix malformed JSON...")
                    
                    # Try to fix common JSON issues
                    try:
                        # If JSON is incomplete, try to complete it
                        if not clean_content.endswith('}'):
                            # Find the last complete object
                            last_brace = clean_content.rfind('}')
                            if last_brace > 0:
                                clean_content = clean_content[:last_brace + 1]
                                print(f"[CONVERSATION_HELP] Truncated to last complete brace")
                        
                        # Try parsing again
                        help_content = json.loads(clean_content)
                        print(f"[CONVERSATION_HELP] ✅ JSON fixed and parsed successfully")
                        
                        # Continue with the parsing logic
                        responses_key = "responses" if "responses" in help_content else "suggested_responses"
                        
                        suggested_responses = []
                        for resp in help_content.get(responses_key, [])[:2]:
                            suggested_responses.append(SuggestedResponse(
                                text=resp.get("text", ""),
                                pronunciation=resp.get("pronunciation", ""),
                                difficulty_level="beginner",
                                explanation=resp.get("explanation", "")
                            ))

                        if len(suggested_responses) > 0:
                            print(f"[CONVERSATION_HELP] ✅ Generated {len(suggested_responses)} contextual responses from fixed JSON")
                            return ConversationHelpResponse(
                                ai_response_summary=help_content.get("summary", help_content.get("ai_response_summary", "The AI provided guidance.")),
                                suggested_responses=suggested_responses,
                                vocabulary_highlights=[],
                                grammar_tips=[]
                            )
                        else:
                            print(f"[CONVERSATION_HELP] ❌ No valid responses in fixed JSON, returning None")
                            return None
                        
                    except json.JSONDecodeError:
                        print(f"[CONVERSATION_HELP] ❌ Could not fix JSON, returning None")
                        return None
                
            except Exception as e:
                print(f"[CONVERSATION_HELP] ❌ Processing failed: {e}, returning None")
                return None
                
        except Exception as e:
            print(f"[CONVERSATION_HELP] ❌ OpenAI call failed: {e}, returning None")
            return None

    except Exception as e:
        print(f"Fast help generation failed: {e}")
        # Always return instant fallback on any error
        templates = INSTANT_RESPONSE_TEMPLATES.get(request.target_language, INSTANT_RESPONSE_TEMPLATES["english"])
        level_templates = templates.get(request.proficiency_level, templates.get("beginner", templates[list(templates.keys())[0]]))
        
        return ConversationHelpResponse(
            ai_response_summary=f"The AI tutor provided guidance in {request.target_language}.",
            suggested_responses=[
                SuggestedResponse(
                    text=template["text"],
                    pronunciation=template["pronunciation"],
                    difficulty_level="beginner",
                    explanation=template["explanation"]
                ) for template in level_templates[:2]
            ],
            vocabulary_highlights=[],
            grammar_tips=[]
        )

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

async def track_help_usage(user_id: str, help_type: str, language: str) -> bool:
    """
    Track help system usage for analytics
    """
    try:
        from database import database
        
        analytics_collection = database.conversation_help_analytics
        
        usage_doc = {
            "user_id": user_id,
            "help_type": help_type,  # "modal_opened", "response_used", "vocabulary_clicked", etc.
            "language": language,
            "timestamp": datetime.utcnow()
        }
        
        result = await analytics_collection.insert_one(usage_doc)
        return result.acknowledged
    
    except Exception as e:
        print(f"Error tracking help usage: {e}")
        return False
