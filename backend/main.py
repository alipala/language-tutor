import os
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# Import MongoDB and authentication modules
from database import init_db, client, database, DATABASE_NAME
from auth import get_current_user
from models import UserResponse
from auth_routes import router as auth_router

# Import sentence assessment functionality
from sentence_assessment import SentenceAssessmentRequest, SentenceAssessmentResponse, GrammarIssue, \
    recognize_speech, analyze_sentence, generate_exercises

# Import speaking assessment functionality
from speaking_assessment import SpeakingAssessmentRequest, SpeakingAssessmentResponse, SkillScore, \
    evaluate_language_proficiency, generate_speaking_prompts

# Load environment variables
load_dotenv()

# Check if OpenAI API key is configured
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY is not configured in .env file")
    print("Please add OPENAI_API_KEY=your_api_key to your .env file")

app = FastAPI(title="Language Tutor Backend API")

# CORS configuration
# For Railway deployment, we need to ensure proper CORS settings
origins = ["*"]  # Start with permissive setting

# Check for Railway-specific environment
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true":
    print("Running in Railway environment, using permissive CORS settings")
    # The correct frontend URL based on previous memory
    frontend_url = "https://taco.up.railway.app"
    
    # In production Railway environment, we use wildcard origins for maximum compatibility
    # This is based on our previous deployment experience
    origins = ["*"]
elif os.getenv("ENVIRONMENT") == "production":
    # For other production environments
    frontend_url = os.getenv("FRONTEND_URL", "https://taco.up.railway.app")
    origins = [
        frontend_url,
        "https://taco.up.railway.app",
    ]
else:
    # For local development - explicitly include localhost:3000
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    frontend_url = "http://localhost:3000"

print(f"Configured CORS with origins: {origins}")

# CORS middleware must be added before any other middleware or route registration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Set to True to allow credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Include learning routes
from learning_routes import router as learning_router
app.include_router(learning_router)

# Include progress routes
from progress_routes import router as progress_router
app.include_router(progress_router)

# Include export routes
from export_routes import router as export_router
app.include_router(export_router)

# Initialize MongoDB on startup
@app.on_event("startup")
async def startup_db_client():
    try:
        # Check if we're in Railway environment
        if os.getenv("RAILWAY_ENVIRONMENT"):
            print(f"Starting in Railway environment")
            # Print available environment variables for MongoDB (with sensitive info masked)
            mongo_vars = {
                k: ("*****" if "PASSWORD" in k else v) 
                for k, v in os.environ.items() 
                if "MONGO" in k
            }
            print(f"Available MongoDB environment variables: {mongo_vars}")
        
        # Initialize database
        await init_db()
        print("MongoDB initialized successfully")
        
        # Log available collections and their document counts
        from database import database
        if database is not None:
            collections = await database.list_collection_names()
            print(f"Available database collections: {collections}")
            
            # Log document counts for each collection
            collection_stats = {}
            for collection_name in collections:
                count = await database[collection_name].count_documents({})
                collection_stats[collection_name] = count
            
            print(f"Collection document counts: {collection_stats}")
    except Exception as e:
        print(f"ERROR initializing MongoDB: {str(e)}")
        print("The application will continue, but database functionality may be limited")

# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    print(f"Requested path: {request.url.path}")
    print(f"Request headers: {request.headers}")
    return await call_next(request)

# Global error handler for better debugging in Railway
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        # Process the request and get the response
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the error with traceback
        error_detail = f"Error processing request: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        
        # Return a JSON response with error details
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(e),
                "path": request.url.path,
                "railway": os.getenv("RAILWAY") == "true",
                "environment": os.getenv("ENVIRONMENT", "development")
            }
        )

# Simple test endpoint to verify API connectivity
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Language Tutor API is running"}

# Enhanced health check endpoint with detailed status information
@app.get("/health")
@app.get("/api/health")  # Add an additional route to match frontend expectations
async def health_check():
    import platform
    import sys
    import time
    
    # Current timestamp for uptime calculation
    current_time = time.time()
    
    # Get environment information
    environment = os.getenv("ENVIRONMENT", "development")
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("RAILWAY") == "true"
    
    # Get all registered routes dynamically
    registered_routes = [route.path for route in app.routes if isinstance(route.path, str)]
    
    # Filter to only include API routes
    api_routes = [route for route in registered_routes if route.startswith('/api')]
    
    # Base health status that matches the frontend's expected format
    health_status = {
        "status": "ok",
        "version": os.getenv("VERSION", "development"),
        "uptime": current_time,
        "system_info": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "timestamp": current_time,
            "environment": environment,
            "railway": is_railway
        },
        "api_routes": api_routes,
        "database": {
            "connected": False,
            "name": DATABASE_NAME
        },
        "openai": {
            "configured": os.getenv("OPENAI_API_KEY") is not None
        }
    }
    
    # Check database connection
    try:
        # Import the client directly from database module to avoid confusion with OpenAI client
        from database import client as mongo_client
        
        if mongo_client is not None:
            await mongo_client.admin.command('ping')
            health_status["database"]["connected"] = True
            
            # Add collection stats
            collections = await database.list_collection_names()
            collection_stats = {}
            for collection_name in collections:
                count = await database[collection_name].count_documents({})
                collection_stats[collection_name] = count
            
            health_status["database"]["collections"] = collection_stats
    except Exception as e:
        health_status["database"]["error"] = str(e)
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        health_status["openai"]["error"] = "API key not configured"
    
    # Set overall status based on checks
    if not health_status["database"]["connected"] or not health_status["openai"]["configured"]:
        health_status["status"] = "degraded"
    
    return health_status

# Define models for request validation
class TutorSessionRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: Optional[str] = None  # User prompt for custom topics
    assessment_data: Optional[Dict[str, Any]] = None  # Assessment data from speaking assessment
    research_data: Optional[str] = None  # Pre-researched data for custom topics

# Define a new model for custom topic prompts
class CustomTopicRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: str  # The custom prompt from the user

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client with error handling
try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        # Alternative initialization without proxies
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method")
    else:
        print(f"Error initializing OpenAI client: {str(e)}")
        raise

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
    
    # Convert to lowercase and get the ISO code
    language_lower = language.lower().strip()
    iso_code = language_map.get(language_lower, "en")  # Default to English if not found
    
    print(f"Language mapping: '{language}' -> '{iso_code}'")
    return iso_code

# Endpoint to generate ephemeral keys for OpenAI Realtime API with language tutor instructions
# main.py - Universal backend approach

@app.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest):
    try:
        print("="*80)
        print(f"🌐 [UNIVERSAL] Creating ephemeral token for all browsers")
        print(f"🌐 [UNIVERSAL] Language: {request.language}")
        print(f"🌐 [UNIVERSAL] Level: {request.level}")
        print(f"🌐 [UNIVERSAL] Topic: {request.topic}")
        print("="*80)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # ✅ Build universal instructions that work on all browsers
        instructions = build_universal_instructions(request)
        
        print(f"✅ [UNIVERSAL] Instructions created: {len(instructions)} characters")
        
        # ✅ Create ephemeral token with complete configuration
        # This approach works reliably on desktop AND mobile browsers
        payload = {
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "voice": request.voice or "alloy",
            "instructions": instructions,  # ✅ All instructions here
            "modalities": ["audio", "text"],
            "input_audio_transcription": {
                "model": "whisper-1",
                "language": get_language_iso_code(request.language) if request.language else "en"
            },
            "turn_detection": {
                "type": "semantic_vad",
                "eagerness": "low",
                "create_response": True,
                "interrupt_response": True
            }
        }
        
        print("✅ [UNIVERSAL] Sending ephemeral token request to OpenAI...")
        
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
            print(f"❌ OpenAI API error: {error_text}")
            raise HTTPException(status_code=response.status_code, detail=error_text)
        
        result = response.json()
        print(f"✅ [UNIVERSAL] Ephemeral token created successfully")
        return result
        
    except Exception as e:
        print(f"❌ [UNIVERSAL] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def build_universal_instructions(request: TutorSessionRequest) -> str:
    """Build instructions that work reliably on all browsers"""
    
    language = request.language.lower()
    level = request.level.upper()
    
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
    
    # ✅ Build assessment-aware instructions
    assessment_context = ""
    if request.assessment_data:
        print(f"🎯 [ASSESSMENT] Integrating assessment data into instructions")
        
        # Extract assessment information
        overall_score = request.assessment_data.get('overall_score', 0)
        recommended_level = request.assessment_data.get('recommended_level', level)
        strengths = request.assessment_data.get('strengths', [])
        areas_for_improvement = request.assessment_data.get('areas_for_improvement', [])
        
        # Extract skill scores
        pronunciation_score = request.assessment_data.get('pronunciation', {}).get('score', 0)
        grammar_score = request.assessment_data.get('grammar', {}).get('score', 0)
        vocabulary_score = request.assessment_data.get('vocabulary', {}).get('score', 0)
        fluency_score = request.assessment_data.get('fluency', {}).get('score', 0)
        coherence_score = request.assessment_data.get('coherence', {}).get('score', 0)
        
        # Build personalized context
        assessment_context = f"""
📊 STUDENT ASSESSMENT PROFILE:
- Overall Score: {overall_score}/100
- Recommended Level: {recommended_level}
- Pronunciation: {pronunciation_score}/100
- Grammar: {grammar_score}/100  
- Vocabulary: {vocabulary_score}/100
- Fluency: {fluency_score}/100
- Coherence: {coherence_score}/100

💪 STRENGTHS: {', '.join(strengths) if strengths else 'General communication'}
🎯 FOCUS AREAS: {', '.join(areas_for_improvement) if areas_for_improvement else 'Overall improvement'}

PERSONALIZED APPROACH:
- Acknowledge their strengths in {', '.join(strengths[:2]) if strengths else 'communication'}
- Focus on improving {', '.join(areas_for_improvement[:2]) if areas_for_improvement else 'speaking skills'}
- Adapt difficulty to their {recommended_level} level capabilities
- Provide targeted feedback based on their assessment results"""
        
        print(f"✅ Assessment context integrated: {len(assessment_context)} characters")
    
    # ✅ Handle custom topic (works on all browsers)
    if request.topic == "custom" and request.user_prompt:
        print(f"🎯 [CUSTOM_TOPIC] Creating universal custom topic instructions")
        
        # Get research data
        research_content = ""
        if request.research_data:
            research_content = request.research_data
            print(f"✅ Using provided research data: {len(research_content)} chars")
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
                    print(f"✅ Fallback research completed")
            except Exception as e:
                print(f"⚠️ Research failed: {str(e)}")
        
        # ✅ Universal custom topic instructions with assessment data
        instructions = f"""🎯 CUSTOM TOPIC CONVERSATION: '{request.user_prompt}'

You are a {language} language tutor for {level} level students.

LANGUAGE RULE: {config['rule']}
{assessment_context}

📚 TOPIC INFORMATION:
{research_content if research_content else f'Use your knowledge about {request.user_prompt}.'}

🚨 FIRST MESSAGE REQUIREMENT:
Your first message MUST immediately discuss '{request.user_prompt}'. 
Do NOT say generic greetings like "Hello! How can I help you?"

Start like: "Let's talk about {request.user_prompt}! [Share interesting facts]. What interests you about this topic?"

CONVERSATION FOCUS:
- Keep all conversation about '{request.user_prompt}'
- Use the topic information provided
- Adapt language complexity to {level} level
- Be engaging and educational
- Apply personalized feedback based on assessment results"""
        
        print(f"✅ Custom topic instructions: {len(instructions)} characters")
        return instructions
    
    # Handle regular topics
    elif request.topic and request.topic != "custom":
        topic_map = {
            "travel": "Travel & Tourism",
            "food": "Food & Cooking", 
            "hobbies": "Hobbies & Interests",
            "culture": "Culture & Traditions",
            "movies": "Movies & TV Shows",
            "music": "Music",
            "technology": "Technology",
            "environment": "Environment & Nature"
        }
        
        topic_name = topic_map.get(request.topic, request.topic.title())
        
        instructions = f"""You are a {language} language tutor for {level} level students.

LANGUAGE RULE: {config['rule']}
{assessment_context}

TOPIC: {topic_name}

Start your first message by introducing {topic_name} and asking an engaging question about it.

Example: "Let's talk about {topic_name}! What interests you most about this topic?"

Keep the conversation focused on {topic_name}.
Apply personalized feedback based on assessment results."""
        
        return instructions
    
    # Default general conversation with assessment data
    else:
        instructions = f"""You are a {language} language tutor for {level} level students.

LANGUAGE RULE: {config['rule']}
{assessment_context}

Start with: "{config['greeting']}"

Be engaging and encourage conversation.
Apply personalized feedback based on assessment results."""
        
        return instructions
# Add endpoint for sentence construction assessment
@app.post("/api/sentence/assess", response_model=SentenceAssessmentResponse)
async def assess_sentence_construction(request: SentenceAssessmentRequest):
    try:
        # Determine the text to analyze - prioritize transcript over audio
        recognized_text = None
        
        # First check if a transcript is provided - prioritize this
        if request.transcript and request.transcript.strip():
            print(f"Using provided transcript: '{request.transcript}'")
            recognized_text = request.transcript
        # If no transcript, try to transcribe audio if provided
        elif request.audio_base64:
            try:
                print("Attempting to transcribe audio...")
                recognized_text = await recognize_speech(request.audio_base64, request.language)
                print(f"Successfully transcribed audio: '{recognized_text}'")
            except Exception as audio_err:
                print(f"Error transcribing audio: {str(audio_err)}")
                # No need to fall back to transcript as we already checked it
        # Use context as last resort if provided
        elif request.context:
            print(f"Using context as fallback: '{request.context}'")
            recognized_text = request.context
        
        if not recognized_text or recognized_text.strip() == "":
            print("No valid text found for analysis")
            raise HTTPException(status_code=400, detail="No speech detected or text provided for analysis")
        
        print(f"Proceeding with analysis of: '{recognized_text}'")
        
        # Analyze sentence
        assessment = await analyze_sentence(
            text=recognized_text,
            language=request.language,
            level=request.level,
            exercise_type=request.exercise_type,
            target_grammar=request.target_grammar
        )
        
        # Combine the recognized text with the assessment results
        result = SentenceAssessmentResponse(
            recognized_text=recognized_text,
            **assessment
        )
        
        return result
    
    except Exception as e:
        print(f"Error in sentence assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentence assessment failed: {str(e)}")

# New endpoint to handle custom topic research (called when user clicks Submit)
@app.post("/api/custom-topic/research")
async def research_custom_topic(request: CustomTopicRequest):
    try:
        # Extract user input from request
        user_prompt = request.user_prompt
        language = request.language.lower()
        level = request.level.upper()
        
        # Enhanced logging for debugging
        print("="*80)
        print(f"[TOPIC_RESEARCH] Starting topic research request")
        print(f"[TOPIC_RESEARCH] Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        print(f"[TOPIC_RESEARCH] Language: {language}")
        print(f"[TOPIC_RESEARCH] Level: {level}")
        print(f"[TOPIC_RESEARCH] User prompt: {user_prompt}")
        print("="*80)
        
        # Perform topic research using GPT-4o
        try:
            print(f"[TOPIC_RESEARCH] Using GPT-4o for comprehensive topic research")
            research_prompt = f"""Provide comprehensive, educational information about: {user_prompt}
            
Please include:
            - Key facts and context
            - Recent developments (if applicable)
            - Background information
            - Relevant vocabulary for language learners
            - Educational insights
            
Make this informative and suitable for {level} level {language} language learners."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an educational research assistant. Provide comprehensive, factual information about topics in a way that's educational for language learners. Include context, key vocabulary, and relevant details."},
                    {"role": "user", "content": research_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            if response and response.choices:
                research_results = response.choices[0].message.content
                print(f"[TOPIC_RESEARCH] ✅ Research successful - got {len(research_results)} characters")
                print(f"[TOPIC_RESEARCH] Research preview: {research_results[:200]}...")
                
                return {
                    "success": True,
                    "topic": user_prompt,
                    "research": research_results,
                    "message": "Topic research completed successfully. You can now start speaking!"
                }
            else:
                print(f"[TOPIC_RESEARCH] ❌ No research results returned")
                return {
                    "success": False,
                    "topic": user_prompt,
                    "research": "",
                    "message": "Research failed, but you can still practice with this topic."
                }
                
        except Exception as research_error:
            print(f"[TOPIC_RESEARCH] ❌ Research failed: {str(research_error)}")
            return {
                "success": False,
                "topic": user_prompt,
                "research": "",
                "message": "Research failed, but you can still practice with this topic."
            }
    
    except Exception as e:
        print(f"[TOPIC_RESEARCH] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to research topic: {str(e)}")

# Endpoint to handle custom topic prompts
@app.post("/api/custom-topic")
async def custom_topic(request: CustomTopicRequest):
    try:
        # Extract user input from request
        user_prompt = request.user_prompt
        language = request.language.lower()
        level = request.level.upper()
        
        # Enhanced logging for debugging
        print("="*80)
        print(f"[CUSTOM_TOPIC] Starting custom topic request processing")
        print(f"[CUSTOM_TOPIC] Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        print(f"[CUSTOM_TOPIC] Language: {language}")
        print(f"[CUSTOM_TOPIC] Level: {level}")
        print(f"[CUSTOM_TOPIC] Voice: {request.voice}")
        print(f"[CUSTOM_TOPIC] Topic: {request.topic}")
        print(f"[CUSTOM_TOPIC] User prompt length: {len(user_prompt)} characters")
        print(f"[CUSTOM_TOPIC] User prompt preview: {user_prompt[:100]}...")
        print(f"[CUSTOM_TOPIC] Full request data: {request.dict()}")
        print("="*80)
        
        # Prepare system prompt based on language learning context
        system_prompt = f"You are a helpful language tutor for {language.capitalize()} at {level} level. "
        system_prompt += "When answering questions, search for current information to provide accurate, up-to-date responses. "
        system_prompt += "Include relevant vocabulary and phrases in your response when appropriate. "
        system_prompt += "Adapt your language complexity to the {level} proficiency level and make the response educational for language learning."
        
        # Note: OpenAI's web search is not yet available for gpt-4o-mini in the standard API
        # Using enhanced prompting to provide the best possible response with available knowledge
        print(f"[CUSTOM_TOPIC] Using enhanced language tutor response (web search not available for gpt-4o-mini)")
        
        # Enhanced fallback with better prompting
        enhanced_system_prompt = f"You are a helpful language tutor for {language.capitalize()} at {level} level. "
        enhanced_system_prompt += "While you don't have access to real-time information, provide the most comprehensive and educational response possible based on your training data. "
        enhanced_system_prompt += "Include relevant vocabulary and phrases in your response when appropriate. "
        enhanced_system_prompt += f"Adapt your language complexity to the {level} proficiency level. "
        enhanced_system_prompt += "If the topic might have recent developments, acknowledge this and suggest where users might find more current information."
        
        print(f"[CUSTOM_TOPIC] System prompt length: {len(enhanced_system_prompt)} characters")
        print(f"[CUSTOM_TOPIC] System prompt preview: {enhanced_system_prompt[:200]}...")
        print(f"[CUSTOM_TOPIC] Calling OpenAI API with model: gpt-4o-mini")
        
        # Call OpenAI API to generate response using the standard chat completions endpoint
        start_time = __import__('time').time()
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            end_time = __import__('time').time()
            print(f"[CUSTOM_TOPIC] OpenAI API call completed in {end_time - start_time:.2f} seconds")
            
            # Log response details
            print(f"[CUSTOM_TOPIC] Response object type: {type(response)}")
            print(f"[CUSTOM_TOPIC] Response has choices: {hasattr(response, 'choices')}")
            if hasattr(response, 'choices'):
                print(f"[CUSTOM_TOPIC] Number of choices: {len(response.choices)}")
                if response.choices:
                    print(f"[CUSTOM_TOPIC] First choice type: {type(response.choices[0])}")
                    print(f"[CUSTOM_TOPIC] First choice has message: {hasattr(response.choices[0], 'message')}")
                    if hasattr(response.choices[0], 'message'):
                        message = response.choices[0].message
                        print(f"[CUSTOM_TOPIC] Message has content: {hasattr(message, 'content')}")
                        if hasattr(message, 'content'):
                            content = message.content
                            print(f"[CUSTOM_TOPIC] Content length: {len(content) if content else 0} characters")
                            print(f"[CUSTOM_TOPIC] Content preview: {content[:200] if content else 'None'}...")
            
            # Extract the response content
            if response and hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                print(f"[CUSTOM_TOPIC] Successfully extracted content, returning response")
                print(f"[CUSTOM_TOPIC] Final response length: {len(content)} characters")
                print("="*80)
                return {"response": content}
            else:
                print(f"[CUSTOM_TOPIC] ERROR: Unexpected response structure")
                print(f"[CUSTOM_TOPIC] Response: {response}")
                print("="*80)
                return {"response": "I apologize, but I received an unexpected response format. Please try again later."}
                
        except Exception as api_error:
            end_time = __import__('time').time()
            print(f"[CUSTOM_TOPIC] ERROR: OpenAI API call failed after {end_time - start_time:.2f} seconds")
            print(f"[CUSTOM_TOPIC] API Error: {str(api_error)}")
            print(f"[CUSTOM_TOPIC] API Error type: {type(api_error)}")
            print("="*80)
            raise api_error
    
    except Exception as e:
        print(f"Error processing custom topic request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process custom topic request: {str(e)}")

# Add endpoint for speaking assessment
@app.post("/api/assessment/speaking", response_model=SpeakingAssessmentResponse)
async def assess_speaking_proficiency(request: SpeakingAssessmentRequest):
    try:
        # First, transcribe the audio if provided
        if not request.transcript and request.audio_base64:
            try:
                print("Transcribing audio for speaking assessment...")
                request.transcript = await recognize_speech(request.audio_base64, request.language)
                print(f"Transcribed text: '{request.transcript}'")
            except Exception as audio_err:
                print(f"Error transcribing assessment audio: {str(audio_err)}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to transcribe audio for assessment"
                )
        
        if not request.transcript or request.transcript.strip() == "":
            raise HTTPException(
                status_code=400, 
                detail="No speech detected or text provided for assessment"
            )
        
        # Perform comprehensive language proficiency assessment
        assessment_result = await evaluate_language_proficiency(
            text=request.transcript,
            language=request.language,
            duration=request.duration
        )
        
        return assessment_result
    
    except Exception as e:
        print(f"Error in speaking assessment: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Speaking assessment failed: {str(e)}"
        )

# Setup static file serving for the frontend
# Check if we're in Railway environment and frontend build exists
# Handle different working directory scenarios (local vs Railway)
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY") == "true":
    # In Railway, the working directory is 'backend' but we need to access the parent directory
    frontend_build_path = Path("/app/frontend/out")
else:
    # Local development - relative path from backend directory
    frontend_build_path = Path(__file__).parent.parent / "frontend" / "out"

frontend_next_static_path = frontend_build_path / "_next" / "static"

print(f"Checking for frontend build at: {frontend_build_path}")
print(f"Frontend build exists: {frontend_build_path.exists()}")
print(f"Frontend Next.js static exists: {frontend_next_static_path.exists()}")

# Mount Next.js static files if they exist
if frontend_next_static_path.exists():
    print("Mounting Next.js static files")
    app.mount("/_next/static", StaticFiles(directory=str(frontend_next_static_path)), name="nextstatic")

# Mount other static assets from the out directory
if frontend_build_path.exists():
    # Mount images and other assets
    frontend_images_path = frontend_build_path / "images"
    frontend_sounds_path = frontend_build_path / "sounds"
    
    if frontend_images_path.exists():
        print("Mounting frontend images")
        app.mount("/images", StaticFiles(directory=str(frontend_images_path)), name="images")
    
    if frontend_sounds_path.exists():
        print("Mounting frontend sounds")
        app.mount("/sounds", StaticFiles(directory=str(frontend_sounds_path)), name="sounds")

# Catch-all route to serve the frontend application
@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    """
    Catch-all route to serve the Next.js frontend application.
    This should be the last route defined.
    """
    # Don't serve frontend for API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Try to serve static files from the Next.js out directory
    if frontend_build_path.exists():
        try:
            # Handle root path - serve index.html
            if full_path == "" or full_path == "/":
                index_path = frontend_build_path / "index.html"
                if index_path.exists():
                    print(f"Serving index.html from: {index_path}")
                    return FileResponse(str(index_path), media_type="text/html")
            
            # Handle other paths - try to serve the corresponding HTML file
            else:
                # Clean the path
                clean_path = full_path.strip("/")
                
                # Try to serve the exact file if it exists
                file_path = frontend_build_path / clean_path
                if file_path.exists() and file_path.is_file():
                    print(f"Serving file: {file_path}")
                    return FileResponse(str(file_path))
                
                # Try to serve as HTML file
                html_path = frontend_build_path / f"{clean_path}.html"
                if html_path.exists():
                    print(f"Serving HTML file: {html_path}")
                    return FileResponse(str(html_path), media_type="text/html")
                
                # Try to serve index.html from subdirectory
                dir_index_path = frontend_build_path / clean_path / "index.html"
                if dir_index_path.exists():
                    print(f"Serving directory index: {dir_index_path}")
                    return FileResponse(str(dir_index_path), media_type="text/html")
                
                # If nothing found, serve the main index.html (SPA fallback)
                index_path = frontend_build_path / "index.html"
                if index_path.exists():
                    print(f"Serving SPA fallback index.html for path: {full_path}")
                    return FileResponse(str(index_path), media_type="text/html")
                    
        except Exception as e:
            print(f"Error serving static frontend file: {str(e)}")
    
    # Fallback: serve a basic HTML page that explains the issue
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Language Tutor - Setup Required</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; }
                .error { background: #f8f9fa; border: 1px solid #dee2e6; padding: 20px; border-radius: 5px; }
                .api-link { background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 20px 0; }
                code { background: #f1f3f4; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Language Tutor Backend</h1>
                <div class="error">
                    <h2>Frontend Not Found</h2>
                    <p>The frontend application build was not found. This usually means:</p>
                    <ul>
                        <li>The frontend hasn't been built yet</li>
                        <li>The build process failed during deployment</li>
                        <li>The frontend files are in a different location</li>
                    </ul>
                </div>
                
                <div class="api-link">
                    <h3>API Status</h3>
                    <p>The backend API is running. You can check the health status:</p>
                    <p><a href="/api/health">API Health Check</a></p>
                    <p><a href="/api/test">API Test Endpoint</a></p>
                </div>
                
                <h3>Deployment Information</h3>
                <p><strong>Environment:</strong> Railway</p>
                <p><strong>Frontend Build Path:</strong> <code>frontend/.next</code></p>
                <p><strong>Expected Files:</strong> Next.js standalone build</p>
            </div>
        </body>
        </html>
        """,
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
