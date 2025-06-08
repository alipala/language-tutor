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

# Endpoint to generate ephemeral keys for OpenAI Realtime API with language tutor instructions
@app.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest):
    try:
        # Enhanced logging for debugging
        print("="*80)
        print(f"[REALTIME_TOKEN] Starting token generation request")
        print(f"[REALTIME_TOKEN] Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        print(f"[REALTIME_TOKEN] Language: {request.language}")
        print(f"[REALTIME_TOKEN] Level: {request.level}")
        print(f"[REALTIME_TOKEN] Voice: {request.voice}")
        print(f"[REALTIME_TOKEN] Topic: {request.topic}")
        print(f"[REALTIME_TOKEN] User prompt length: {len(request.user_prompt) if request.user_prompt else 0}")
        print(f"[REALTIME_TOKEN] User prompt preview: {request.user_prompt[:100] if request.user_prompt else 'None'}...")
        print(f"[REALTIME_TOKEN] Assessment data provided: {bool(request.assessment_data)}")
        print(f"[REALTIME_TOKEN] Full request data: {request.dict()}")
        print("="*80)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("ERROR: OPENAI_API_KEY is not configured in .env file")
            raise HTTPException(status_code=500, detail="OpenAI API key is not configured")
        
        # Load the tutor instructions from the JSON file
        instructions_path = Path(__file__).parent / "tutor_instructions.json"
        if not instructions_path.exists():
            raise HTTPException(status_code=404, detail="Tutor instructions not found")
        
        with open(instructions_path, "r") as f:
            tutor_data = json.load(f)
        
        # Get the instructions for the selected language and level
        language = request.language.lower()
        level = request.level.upper()
        topic = request.topic
        
        # CRITICAL DEBUGGING - Log exactly what language is being processed
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] CRITICAL LANGUAGE PROCESSING:")
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Raw request.language: '{request.language}'")
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Processed language: '{language}'")
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Level: '{level}'")
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Available languages in tutor_data: {list(tutor_data.get('languages', {}).keys())}")
        
        if language not in tutor_data.get("languages", {}):
            print(f"🚨🚨🚨 [LANGUAGE_DEBUG] ERROR: Language '{language}' not found in supported languages!")
            raise HTTPException(status_code=400, detail=f"Language '{language}' not supported")
        
        language_data = tutor_data["languages"][language]
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Successfully found language data for '{language}'")
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Available levels for {language}: {list(language_data.get('levels', {}).keys())}")
        
        if level not in language_data.get("levels", {}):
            print(f"🚨🚨🚨 [LANGUAGE_DEBUG] ERROR: Level '{level}' not found for language '{language}'!")
            raise HTTPException(status_code=400, detail=f"Level '{level}' not supported for language '{language}'")
        
        print(f"🚨🚨🚨 [LANGUAGE_DEBUG] Successfully found level data for '{language}' at level '{level}'")
        
        # Get the base instructions for the selected language and level
        base_instructions = language_data["levels"][level].get("instructions", "")
        
        # Create concise, focused instructions following the analysis recommendations
        print(f"[REALTIME_TOKEN] Creating concise instructions for {language} at level {level}")
        
        # Create simplified language enforcement based on language
        if language == "dutch":
            language_rule = "Spreek alleen Nederlands. Als de student een andere taal gebruikt, zeg: 'Laten we Nederlands oefenen. Probeer het in het Nederlands te zeggen.'"
            greeting = "Hallo! Ik ben je Nederlandse taaldocent."
        elif language == "english":
            language_rule = "Respond only in English. If the student speaks another language, say: 'Let's practice in English. Try saying that in English.'"
            greeting = "Hello! I am your English language tutor."
        elif language == "spanish":
            language_rule = "Responde solo en español. Si el estudiante habla otro idioma, di: 'Practiquemos español. Intenta decirlo en español.'"
            greeting = "¡Hola! Soy tu profesor de español."
        elif language == "german":
            language_rule = "Antworte nur auf Deutsch. Wenn der Schüler eine andere Sprache spricht, sage: 'Lass uns Deutsch üben. Versuche es auf Deutsch zu sagen.'"
            greeting = "Hallo! Ich bin dein Deutschlehrer."
        elif language == "french":
            language_rule = "Réponds uniquement en français. Si l'étudiant parle une autre langue, dis: 'Pratiquons le français. Essaie de le dire en français.'"
            greeting = "Bonjour! Je suis ton professeur de français."
        elif language == "portuguese":
            language_rule = "Responda apenas em português. Se o aluno falar outro idioma, diga: 'Vamos praticar português. Tente dizer isso em português.'"
            greeting = "Olá! Eu sou seu professor de português."
        else:
            language_rule = f"Respond only in {language}. If the student speaks another language, redirect them to practice in {language}."
            greeting = f"Hello! I am your {language} language tutor."
        
        # Create concise instructions (following the 80% reduction recommendation)
        instructions = f"""You are a {language} language tutor for {level} level students.

LANGUAGE RULE: {language_rule}

Start with: "{greeting}"

{base_instructions}

Be engaging and encourage conversation."""
        
        print(f"[REALTIME_TOKEN] Simplified instructions length: {len(instructions)} characters (reduced from ~5000)")
        
        # Add custom topic instructions with research data if provided
        if request.topic == "custom" and request.user_prompt:
            print(f"[REALTIME_TOKEN] Processing custom topic: {request.user_prompt}")
            
            # Check if we have pre-researched data (from the new research endpoint)
            web_search_results = ""
            research_source = "none"
            
            # First, check if research data was provided in the request
            if request.research_data:
                web_search_results = request.research_data
                research_source = "request_data"
                print(f"[REALTIME_TOKEN] ✅ Using research data from request: {len(web_search_results)} characters")
            else:
                # Fallback: perform research here (for backward compatibility)
                try:
                    print(f"[REALTIME_TOKEN] No pre-researched data found, performing research now")
                    print(f"[REALTIME_TOKEN] Using enhanced GPT-4o for topic research")
                    enhanced_prompt = f"""Provide comprehensive, educational information about: {request.user_prompt}
                    
Please include:
                    - Key facts and context
                    - Recent developments (if applicable)
                    - Background information
                    - Relevant vocabulary for language learners
                    - Educational insights
                    
Make this informative and suitable for {level} level {language} language learners."""
                    
                    search_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an educational research assistant. Provide comprehensive, factual information about topics in a way that's educational for language learners. Include context, key vocabulary, and relevant details."},
                            {"role": "user", "content": enhanced_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1500
                    )
                    
                    if search_response and search_response.choices:
                        web_search_results = search_response.choices[0].message.content
                        research_source = "realtime_fallback"
                        print(f"[REALTIME_TOKEN] ✅ Fallback research successful - got {len(web_search_results)} characters")
                    else:
                        print(f"[REALTIME_TOKEN] ❌ Fallback research returned no results")
                        
                except Exception as search_error:
                    print(f"[REALTIME_TOKEN] ❌ Fallback research failed: {str(search_error)}")
                    web_search_results = ""
                    research_source = "failed"
            
            # Create enhanced custom topic instructions with research results
            custom_topic_instructions = f"\n\n🎯 CRITICAL CUSTOM TOPIC INSTRUCTION - HIGHEST PRIORITY:\n\nThe user has specifically chosen to discuss: '{request.user_prompt}'\n\n"
            
            if web_search_results:
                custom_topic_instructions += f"📚 CURRENT INFORMATION ABOUT THE TOPIC:\n{web_search_results}\n\n"
                print(f"[REALTIME_TOKEN] ✅ Added {len(web_search_results)} characters of research results to AI instructions (source: {research_source})")
            else:
                print(f"[REALTIME_TOKEN] ⚠️ No research results available, using base knowledge only")
            
            custom_topic_instructions += f"YOU MUST START YOUR VERY FIRST MESSAGE by discussing this exact topic using the current information provided above. Do NOT greet with generic phrases like 'Hello! How can I help you today?' Instead, immediately begin with content about '{request.user_prompt}' in a way that's appropriate for {level} level {language} learners.\n\nExample first message structure:\n'Let's talk about {request.user_prompt}. [Use the current information provided to give interesting facts]. What do you think about [specific current aspect of the topic]?'\n\nIMPORTANT RULES:\n- Your FIRST message must be about '{request.user_prompt}' - no generic greetings\n- Use the current information provided above to give accurate, up-to-date content\n- Provide educational content about this specific topic\n- Ask engaging questions related to '{request.user_prompt}' and current developments\n- Keep the entire conversation focused on this chosen topic\n- Adapt the complexity to {level} level\n- Help the user practice {language} while exploring '{request.user_prompt}' with current context"
            
            instructions = custom_topic_instructions + "\n\n" + instructions
            print(f"[REALTIME_TOKEN] 📝 Final instructions length: {len(instructions)} characters")
            print(f"[REALTIME_TOKEN] 🎯 Custom topic setup complete with {'research-enhanced' if web_search_results else 'basic'} knowledge (source: {research_source})")
        
        # Add regular topic instructions for predefined topics
        elif request.topic and request.topic != "custom":
            print(f"[REALTIME_TOKEN] Processing regular topic: {request.topic}")
            
            # Define topic-specific conversation starters and focus areas
            topic_details = {
                "travel": {
                    "name": "Travel & Tourism",
                    "focus_areas": ["destinations", "transportation", "accommodation", "cultural experiences", "travel planning", "local customs"],
                    "starter_questions": [
                        "What's your favorite travel destination and why?",
                        "Tell me about a memorable trip you've taken.",
                        "What type of accommodation do you prefer when traveling?",
                        "How do you usually plan your trips?"
                    ]
                },
                "food": {
                    "name": "Food & Cooking",
                    "focus_areas": ["cuisines", "cooking techniques", "recipes", "restaurants", "food culture", "dietary preferences"],
                    "starter_questions": [
                        "What's your favorite cuisine and why?",
                        "Do you enjoy cooking? What's your specialty?",
                        "Tell me about a traditional dish from your country.",
                        "What's the most interesting food you've ever tried?"
                    ]
                },
                "hobbies": {
                    "name": "Hobbies & Interests",
                    "focus_areas": ["sports", "arts", "music", "reading", "games", "outdoor activities", "creative pursuits"],
                    "starter_questions": [
                        "What hobbies do you enjoy in your free time?",
                        "How did you get started with your favorite hobby?",
                        "Do you prefer indoor or outdoor activities?",
                        "What new hobby would you like to try?"
                    ]
                },
                "culture": {
                    "name": "Culture & Traditions",
                    "focus_areas": ["festivals", "customs", "traditions", "art", "history", "social norms", "celebrations"],
                    "starter_questions": [
                        "What's an important tradition in your culture?",
                        "How do you celebrate holidays in your country?",
                        "What cultural differences have you noticed when traveling?",
                        "Tell me about a festival or celebration you enjoy."
                    ]
                },
                "movies": {
                    "name": "Movies & TV Shows",
                    "focus_areas": ["genres", "actors", "directors", "streaming", "cinema", "entertainment", "storytelling"],
                    "starter_questions": [
                        "What's your favorite movie genre and why?",
                        "Tell me about a movie or TV show you recently watched.",
                        "Do you prefer watching at home or in the cinema?",
                        "Who's your favorite actor or actress?"
                    ]
                },
                "music": {
                    "name": "Music",
                    "focus_areas": ["genres", "instruments", "concerts", "artists", "streaming", "live performances", "music culture"],
                    "starter_questions": [
                        "What type of music do you enjoy listening to?",
                        "Do you play any musical instruments?",
                        "Tell me about a concert or live performance you've attended.",
                        "How do you usually discover new music?"
                    ]
                },
                "technology": {
                    "name": "Technology",
                    "focus_areas": ["gadgets", "apps", "social media", "innovation", "digital trends", "artificial intelligence", "smartphones"],
                    "starter_questions": [
                        "What's your favorite piece of technology and why?",
                        "How has technology changed your daily life?",
                        "What apps do you use most frequently?",
                        "What do you think about artificial intelligence?"
                    ]
                },
                "environment": {
                    "name": "Environment & Nature",
                    "focus_areas": ["climate change", "sustainability", "wildlife", "conservation", "renewable energy", "recycling", "nature"],
                    "starter_questions": [
                        "What do you do to help protect the environment?",
                        "Tell me about your favorite place in nature.",
                        "How concerned are you about climate change?",
                        "What environmental changes have you noticed in your area?"
                    ]
                }
            }
            
            # Get topic details or use generic fallback
            topic_info = topic_details.get(request.topic, {
                "name": request.topic.title(),
                "focus_areas": [request.topic],
                "starter_questions": [f"What interests you about {request.topic}?"]
            })
            
            # Create simple, direct topic-specific instructions
            regular_topic_instructions = f"\n\nIMPORTANT: The user has chosen to discuss {topic_info['name']}.\n\n"
            regular_topic_instructions += f"You must start your first message by introducing {topic_info['name']} and asking a question about it.\n\n"
            regular_topic_instructions += f"If the user asks what topic you are discussing, respond: 'We are discussing {topic_info['name']}'.\n\n"
            regular_topic_instructions += f"Keep the conversation focused on {topic_info['name']} and related topics like: {', '.join(topic_info['focus_areas'])}.\n\n"
            regular_topic_instructions += f"Example first message: 'Let's talk about {topic_info['name']}! {topic_info['starter_questions'][0]}'\n\n"
            
            instructions = regular_topic_instructions + "\n\n" + instructions
            print(f"[REALTIME_TOKEN] ✅ Added regular topic instructions for '{topic_info['name']}'")
            print(f"[REALTIME_TOKEN] 📝 Topic focus areas: {', '.join(topic_info['focus_areas'])}")
            print(f"[REALTIME_TOKEN] 📝 Final instructions length: {len(instructions)} characters")
        
        # Add universal formatting and speech instructions
        formatting_instructions = "\n\nFORMATTING INSTRUCTIONS: Always use proper spacing between words and sentences. Ensure there is a space after punctuation marks like periods, commas, question marks, and exclamation points. Maintain proper paragraph structure with line breaks between paragraphs. Use proper capitalization at the beginning of sentences."
        
        speech_instructions = "\n\nSPEECH CLARITY: When speaking, maintain a natural pace with slight pauses between sentences. Articulate words clearly and avoid running words together. Use proper intonation to indicate questions, statements, and emphasis."
        
        # Add enhanced language detection and enforcement instructions
        language_detection_instructions = f"\n\nCRITICAL LANGUAGE DETECTION ENHANCEMENT: You have advanced language detection capabilities. Before responding to any user input, carefully analyze the language being spoken. Listen for pronunciation patterns, vocabulary, grammar structures, and accent characteristics. If the user is speaking in the target language ({language}), respond normally. If they are speaking in a different language, use the standard language reminder response. Pay special attention to pronunciation, accent, and context clues to accurately identify the language being spoken. Do not assume a language based on a single unclear word - analyze the overall speech pattern."
        
        # The simplified language rules are already included in the base instructions above
        # No additional verbose enforcement needed - this was the main issue!
        print(f"[REALTIME_TOKEN] Using simplified language rules only (no verbose enforcement)")
        
        # Combine all instructions
        instructions = instructions + language_detection_instructions + formatting_instructions + speech_instructions
        
        print(f"Generating ephemeral key with OpenAI API for {language} at level {level}...")
        
        # CRITICAL DEBUGGING - Log the exact instructions being sent to OpenAI
        print("🚨🚨🚨 [INSTRUCTIONS_DEBUG] CRITICAL: Logging exact instructions sent to OpenAI:")
        print("🚨🚨🚨 [INSTRUCTIONS_DEBUG] Instructions length:", len(instructions))
        print("🚨🚨🚨 [INSTRUCTIONS_DEBUG] First 500 characters:")
        print(instructions[:500])
        print("🚨🚨🚨 [INSTRUCTIONS_DEBUG] Last 500 characters:")
        print(instructions[-500:])
        print("🚨🚨🚨 [INSTRUCTIONS_DEBUG] Full instructions:")
        print(instructions)
        print("🚨🚨🚨 [INSTRUCTIONS_DEBUG] End of instructions")
        
        # Log the exact JSON payload being sent
        payload = {
            "model": "gpt-4o-mini-realtime-preview-2024-12-17",
            "voice": request.voice,
            "instructions": instructions,
            "modalities": ["audio", "text"]
        }
        print("🚨🚨🚨 [PAYLOAD_DEBUG] Full JSON payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
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
            raise HTTPException(
                status_code=response.status_code,
                detail={"error": "Error from OpenAI API", "details": error_text}
            )
        
        return response.json()
    except httpx.RequestError as e:
        print(f"Error generating ephemeral key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate ephemeral key: {str(e)}")

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
