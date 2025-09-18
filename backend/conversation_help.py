from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import json
import httpx
import traceback
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

# 1. Truncation
def smart_truncate(text: str, max_length: int = 100) -> str:
    """
    1. First checking if text is already short enough
    2. Trying to cut at natural sentence boundaries (periods, questions, exclamations)
    3. Falling back to word boundaries if sentence boundaries aren't optimal
    4. Using hard truncation only as a last resort

    Returns:
        Truncated text with semantic preservation
    """
    # Return immediately if text is already short
    if len(text) <= max_length:
        print(f" Text already short enough, no truncation needed")
        return text
    
    # Try to cut at natural sentence boundaries
    truncated = text[:max_length]
    last_period = truncated.rfind('.')      # Find last complete sentence
    last_question = truncated.rfind('?')    # Find last complete question
    last_exclamation = truncated.rfind('!') # Find last complete exclamation
    
    # BOUNDARY: Choose best cut point that preserves meaning
    best_cut = max(last_period, last_question, last_exclamation)
    if best_cut > max_length * 0.6:  # If we can preserve 60%+ of content
        print(f"Truncating at sentence boundary (position {best_cut})")
        return text[:best_cut + 1]
    
    # FALLBACK: Cut at word boundary to avoid mid-word truncation
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:  # If we can preserve 70%+ of content
        print(f"Truncating at word boundary (position {last_space})")
        return text[:last_space] + "..."
    
    # FALLBACK: Hard truncation with ellipsis
    print(f"Using hard truncation at {max_length} characters")
    return text[:max_length] + "..."


# 2. Input validation function
def validate_help_request(request: ConversationHelpRequest) -> bool:
    """
    Validate the conversation help request with early exit optimization. 
    Returns:
        True if valid, False otherwise
    """
    if not request.ai_response or not request.ai_response.strip():
        print(f"VALIDATION FAILED: Empty AI response - returning None")
        return False
    print(f"VALIDATION PASSED: AI response is valid")
    return True


# 3. Prompt generation function
def generate_help_prompt(truncated_response: str, request: ConversationHelpRequest) -> str:
    """
    Generate a compressed prompt that keeps the precision while redıucing tokens.
    It uses direct JSON specification with minimal context and clear instructions.
    
    Args:
        truncated_response: The truncated AI response
        request: The help request containing language and proficiency info
    """
    print(f"\n PHASE 5: Prompt engineering")
    
    # TECHNIQUE: Direct JSON specification + minimal context + clear instructions
    prompt = f"""AI tutor said: "{truncated_response}"
    Target language: {request.target_language}
    Student level: {request.proficiency_level}
    Help language: {request.user_language}

    Generate 2 contextual responses in JSON:
    {{"summary": "brief summary in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this response fits"}}]}}"""

    print(f"Prompt length: {len(prompt)} characters")
    print(f"Prompt template: {prompt[:100]}...")
    return prompt


# 4. API call function
async def call_openai_api(prompt: str) -> tuple:
    """
    Sending request to OpenAI with the settings.
    """
    
    # PHASE 6: Maximum speed OpenAI API call with cost optimization
    # MODEL: GPT-4o-mini for 80% cost reduction vs GPT-4    
    start_time = datetime.utcnow()
    print(f"API call started at: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",        # 80% cheaper than GPT-4
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,            # Low temperature for consistent, fast responses
        max_tokens=400,             # Limit tokens for speed and cost control
        timeout=10,                 # 10-second timeout for user experience
        stream=False                # No streaming for faster processing
    )
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    print(f"   - API call completed at: {end_time.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"   - Duration: {duration:.2f} seconds")
    
    return response, duration, start_time

# 5. Response validation function
def validate_api_response(response) -> bool:
    """
    Validate the OpenAI API response.

    Check if the response has choices, message, and content.
    It implements early exit patterns to avoid processing invalid responses.
        
    """    
    # PHASE 7: Response validation with early exit patterns
    if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
        print(f" VALIDATION FAILED: Invalid OpenAI response structure")
        return False
    print(f" VALIDATION PASSED: Response structure is valid")
    return True


# 6. Response cleaning function
def clean_json_response(content: str) -> str:
    """
    Clean the JSON response from OpenAI for parsing.
    
    This function handles various JSON formatting from OpenAI responses by:
    1. Removing code block markers (```json, ```)
    2. Stripping whitespace
    3. Tracking content length changes for debugging
        
    Returns:
        Cleaned JSON ready for parsing
    """
    print(f"\  PHASE 9: JSON cleaning")
    # PURPOSE: Handle various JSON formatting from OpenAI responses
    original_length = len(content)
    if content.startswith('```json'):
        content = content[7:]       # Remove ```json prefix
        print(f"   - Removed ```json prefix")
    elif content.startswith('```'):
        content = content[3:]       # Remove ``` prefix
        print(f"   - Removed ``` prefix")
    
    if content.endswith('```'):
        content = content[:-3]      # Remove ``` suffix
        print(f"   - Removed ``` suffix")
    
    content = content.strip()       # Clean whitespace
    print(f"   - Cleaned content length: {len(content)} (was {original_length})")
    return content


# 7. Response parsing function
def parse_and_build_response(content: str, start_time: datetime) -> Optional[ConversationHelpResponse]:
    """
    Parse the JSON content and build the response object with error handling.
    
    This function:
    1. Parses the JSON with error handling
    2. Extracts responses with flexible key handling
    3. Builds structured response objects
    4. Limits to 2 responses for optimal UX
    5. Creates the final ConversationHelpResponse
    """
    print(f"\n PHASE 10: JSON parsing")
    try:
        help_data = json.loads(content)
        print(f" JSON parsed successfully")
        print(f"   - JSON structure: {list(help_data.keys())}")
        
        # PHASE 11: Extract responses with flexible key handling
        print(f"\n PHASE 11: Extract responses")
        responses_key = "responses" if "responses" in help_data else "suggested_responses"
        print(f"   - Using key: '{responses_key}' for responses")
        raw_responses = help_data.get(responses_key, [])
        print(f"   - Found {len(raw_responses)} raw responses")
        
        if not raw_responses:
            print(f" No responses in parsed data")
            return None
        
        # PHASE 12: Build structured response objects
        print(f"\n PHASE 12: Building response objects")
        # OPTIMIZATION: Limit to 2 responses for speed and user experience
        suggested_responses = []
        for i, resp in enumerate(raw_responses[:2]):  # Limit to 2 responses for optimal UX
            if isinstance(resp, dict) and resp.get("text"):
                print(f"   - Response {i+1}: \"{resp.get('text', '')[:30]}...\"")
                print(f"     Pronunciation: \"{resp.get('pronunciation', '')[:20]}...\"")
                suggested_responses.append(SuggestedResponse(
                    text=resp.get("text", ""),
                    pronunciation=resp.get("pronunciation", ""),
                    difficulty_level=resp.get("difficulty_level", "beginner"),
                    explanation=resp.get("explanation", "")
                ))
            else:
                print(f"   - Response {i+1}: Invalid format, skipping")
        
        if not suggested_responses:
            print(f" No valid responses created")
            return None
        
        print(f" Generated {len(suggested_responses)} contextual responses")
        
        # PHASE 13: Return optimized conversation help response
        print(f"\n PHASE 13: Creating final response")
        # RESULT: Ultra-fast, cost-effective, contextually relevant help
        summary = help_data.get("summary", "The AI provided guidance.")
        print(f"   - Summary: \"{summary[:50]}...\"")
        print(f"   - Responses: {len(suggested_responses)}")
        print(f"   - Vocabulary items: 0 (minimal for speed)")
        print(f"   - Grammar tips: 0 (minimal for speed)")
        
        final_response = ConversationHelpResponse(
            ai_response_summary=summary,
            suggested_responses=suggested_responses,
            vocabulary_highlights=[],  # Minimal for speed
            grammar_tips=[]           # Minimal for speed
        )
        
        print(f"\n CONVERSATION HELP GENERATION COMPLETE")
        print(f"   - Total time: {(datetime.utcnow() - start_time).total_seconds():.2f} seconds")
        print(f"========== END DEBUGGING ==========\n\n")
        
        return final_response
        
    except json.JSONDecodeError as e:
        print(f"\n JSON parsing failed: {e}")
        print(f"   - Content that failed: {content[:100]}...")
        print(f"========== END DEBUGGING (ERROR) ==========\n\n")
        return None


# 8. Main function for help generation
async def generate_conversation_help_fast(request: ConversationHelpRequest) -> Optional[ConversationHelpResponse]:
    try:
        # PHASE 2: Validate input
        if not validate_help_request(request):
            return None
        
        # PHASE 3-4: Truncate AI response
        print(f"\n PHASE 3: Truncation of AI response")
        print(f"   - Original AI response length: {len(request.ai_response)} characters")
        truncated_response = smart_truncate(request.ai_response, 100)
        print(f"   - Truncated response: \"{truncated_response}\"")
        print(f"   - Truncated length: {len(truncated_response)} characters")
        print(f"   - Reduction: {(1 - len(truncated_response)/len(request.ai_response))*100:.1f}%")
        
        # PHASE 5: Generate prompt
        prompt = generate_help_prompt(truncated_response, request)
        
        # PHASE 6: Call OpenAI API
        response, duration, start_time = await call_openai_api(prompt)
        
        # PHASE 7: Validate API response
        if not validate_api_response(response):
            return None
        
        # PHASE 8: Extract content
        content = response.choices[0].message.content.strip()
        print(f"   - Raw content (first 100 chars): {content[:100]}...")
        
        # PHASE 9: Clean JSON response
        cleaned_content = clean_json_response(content)
        
        # PHASE 10-13: Parse and build response
        return parse_and_build_response(cleaned_content, start_time)
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        print(f"type: {type(e).__name__}")
        print(f"Stack trace: {traceback.format_exc()}")
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
