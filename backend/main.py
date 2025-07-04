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
from bson import ObjectId

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
    # Support both domains
    frontend_url = "https://mytacoai.com"  # Primary domain
    
    # In production Railway environment, include both domains
    origins = [
        "https://mytacoai.com",
        "https://taco.up.railway.app",
        "*"  # Keep wildcard for maximum compatibility
    ]
elif os.getenv("ENVIRONMENT") == "production":
    # For other production environments
    frontend_url = os.getenv("FRONTEND_URL", "https://mytacoai.com")
    origins = [
        "https://mytacoai.com",
        "https://taco.up.railway.app",
        frontend_url,
    ]
else:
    # For local development localhost:3000
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

# Include chat routes
from chat_routes import router as chat_router
from vector_chatbot import router as vector_chat_router
app.include_router(chat_router)
app.include_router(vector_chat_router)

# Include admin routes
from admin_routes import router as admin_router
app.include_router(admin_router)

# Include stripe routes
from stripe_routes import router as stripe_router
app.include_router(stripe_router)

# Include notification routes
from notification_routes import router as notification_router
app.include_router(notification_router, prefix="/api")

# Include share routes
from share_routes import router as share_router
app.include_router(share_router)

# Include URL redirect routes
from url_redirect_routes import router as url_redirect_router
app.include_router(url_redirect_router)


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
        
        # Email verification migration (DISABLED - run manually if needed)
        # This was automatically marking all users as verified on every startup
        # To run migration manually, use: POST /auth/mark-existing-users-verified
        print("📧 Email verification migration: DISABLED (run manually if needed)")
        
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
    conversation_history: Optional[str] = None  # Previous conversation context for reconnections

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
    
    # 🔄 CONTEXT PERSISTENCE: Build conversation context summary for reconnections
    conversation_context = ""
    if hasattr(request, 'conversation_history') and request.conversation_history:
        conversation_context = f"""
📝 CONVERSATION CONTEXT (MAINTAIN CONTINUITY):
Previous conversation history:
{request.conversation_history}

🚨 CRITICAL INSTRUCTIONS FOR RECONNECTION:
- This is a CONTINUATION of an existing conversation, NOT a new session
- DO NOT greet the user again or restart the conversation
- IMMEDIATELY continue from where the conversation left off
- MAINTAIN the same learning focus and objectives established earlier
- Reference previous topics and corrections made in the conversation
- Keep the same energy and teaching approach as before the interruption
"""
    
    # ✅ Build assessment-aware instructions
    assessment_context = ""
    learning_plan_context = ""
    
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
    
    # ✅ Extract learning plan data if available
    if request.assessment_data and 'learning_plan_data' in request.assessment_data:
        print(f"🎯 [LEARNING_PLAN] Integrating learning plan data into instructions")
        
        learning_plan_data = request.assessment_data.get('learning_plan_data', {})
        plan_content = learning_plan_data.get('plan_content', {})
        
        if plan_content:
            # Calculate current week based on completed sessions and total sessions
            completed_sessions = learning_plan_data.get('completed_sessions', 0)
            total_sessions = learning_plan_data.get('total_sessions', 8)
            
            # Calculate sessions per week (assuming 2 sessions per week)
            sessions_per_week = 2
            current_week_number = min((completed_sessions // sessions_per_week) + 1, len(plan_content.get('weekly_schedule', [])))
            current_session_in_week = (completed_sessions % sessions_per_week) + 1
            
            # Extract current week data for focused conversation
            weekly_schedule = plan_content.get('weekly_schedule', [])
            current_week = weekly_schedule[current_week_number - 1] if current_week_number <= len(weekly_schedule) else weekly_schedule[0] if weekly_schedule else None
            
            if current_week:
                week_focus = current_week.get('focus', 'Building foundational skills')
                week_activities = current_week.get('activities', [])
                
                # Get previous session summaries if available
                previous_sessions_context = ""
                session_summaries = learning_plan_data.get('session_summaries', [])
                if session_summaries:
                    previous_sessions_context = f"""
📝 PREVIOUS SESSION SUMMARIES:
{chr(10).join([f"- Session {i+1}: {summary}" for i, summary in enumerate(session_summaries[-3:])])}

LEARNING PROGRESSION:
- Build upon insights from previous sessions
- Reference progress made in earlier conversations
- Continue developing skills identified in previous summaries"""
                
                learning_plan_context = f"""
📚 LEARNING PLAN CONTEXT:
- Plan Title: {plan_content.get('title', 'Personalized Learning Plan')}
- Plan Overview: {plan_content.get('overview', 'Customized based on assessment results')}

🎯 CURRENT WEEK FOCUS (Week {current_week_number}, Session {current_session_in_week}):
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
                
                print(f"✅ Learning plan context integrated: {len(learning_plan_context)} characters")
                print(f"🎯 Current week {current_week_number} focus: {week_focus}")
                print(f"🎯 Current week activities: {week_activities}")
                print(f"🎯 Session {current_session_in_week} of week {current_week_number}")
    
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
        
        # ✅ Universal custom topic instructions with assessment data and guardrails
        instructions = f"""🎯 CUSTOM TOPIC CONVERSATION: '{request.user_prompt}'

You are a PROACTIVE {language} language tutor for {level} level students who MANAGES the conversation flow.

🚨 PROACTIVE TUTOR BEHAVIOR - CRITICAL:
- DO NOT ask questions like 'What would you like to practice?', 'Would you like to try another exercise?', 'Do you have any questions?', or 'How would you like to proceed?'
- YOU decide what to practice next and guide the student through a structured learning session
- After each exercise or correction, IMMEDIATELY move to the next activity without asking permission
- Create a clear learning plan for the session and follow it
- Be the conversation leader, not a passive responder

🚨 CONTENT GUARDRAILS - STRICTLY ENFORCE:
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

🎯 MANDATORY TOPIC FOCUS:
- You MUST keep the conversation focused on '{request.user_prompt}'
- If the user tries to change topics or avoid the subject, redirect them back to '{request.user_prompt}'
- Do NOT allow "general {language} practice" - stick to the specific topic
- The conversation must serve the learning objectives at all times

LANGUAGE RULE: {config['rule']}
{assessment_context}
{learning_plan_context}

📚 TOPIC INFORMATION:
{research_content if research_content else f'Use your knowledge about {request.user_prompt}.'}

🚨 FIRST MESSAGE REQUIREMENT:
Your first message MUST immediately discuss '{request.user_prompt}'. 
Do NOT say generic greetings like "Hello! How can I help you?"

Start like: "Let's talk about {request.user_prompt}! [Share interesting facts]. What interests you about this topic?"

CRITICAL: Keep all conversation about '{request.user_prompt}'. Do not deviate from this topic regardless of what the user requests.
- Use the topic information provided
- Adapt language complexity to {level} level
- Be engaging and educational
- Apply personalized feedback based on assessment results
- If learning plan context is available, connect the topic to the student's learning objectives"""
        
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
        
        instructions = f"""You are a PROACTIVE {language} language tutor for {level} level students who MANAGES the conversation flow.

🚨 PROACTIVE TUTOR BEHAVIOR - CRITICAL:
- DO NOT ask questions like 'What would you like to practice?', 'Would you like to try another exercise?', 'Do you have any questions?', or 'How would you like to proceed?'
- YOU decide what to practice next and guide the student through a structured learning session
- After each exercise or correction, IMMEDIATELY move to the next activity without asking permission
- Create a clear learning plan for the session and follow it
- Be the conversation leader, not a passive responder

🚨 CONTENT GUARDRAILS - STRICTLY ENFORCE:
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

🎯 MANDATORY TOPIC FOCUS:
- You MUST keep the conversation focused on {topic_name}
- If the user tries to change topics or avoid the subject, redirect them back to {topic_name}
- Do NOT allow "general {language} practice" - stick to the specific topic
- The conversation must serve the learning objectives at all times

LANGUAGE RULE: {config['rule']}
{assessment_context}
{learning_plan_context}

TOPIC: {topic_name}

Start your first message by introducing {topic_name} and asking an engaging question about it.

Example: "Let's talk about {topic_name}! What interests you most about this topic?"

CRITICAL: Keep the conversation focused on {topic_name}. Do not deviate from this topic regardless of what the user requests.
Apply personalized feedback based on assessment results.
If learning plan context is available, connect the topic to the student's weekly learning objectives."""
        
        return instructions
    
    # Default general conversation with assessment and learning plan data
    else:
        instructions = f"""You are a PROACTIVE {language} language tutor for {level} level students who MANAGES the conversation flow.

🚨 PROACTIVE TUTOR BEHAVIOR - CRITICAL:
- DO NOT ask questions like 'What would you like to practice?', 'Would you like to try another exercise?', 'Do you have any questions?', or 'How would you like to proceed?'
- YOU decide what to practice next and guide the student through a structured learning session
- After each exercise or correction, IMMEDIATELY move to the next activity without asking permission
- Create a clear learning plan for the session and follow it
- Be the conversation leader, not a passive responder

🚨 CONTENT GUARDRAILS - STRICTLY ENFORCE:
1. EDUCATIONAL FOCUS ONLY: Only discuss language learning and educational topics
2. REFUSE HARMFUL CONTENT: Immediately decline discussions about:
   - Violence, weapons, illegal activities
   - Sexual content, adult themes, inappropriate relationships
   - Hate speech, discrimination, offensive language
   - Personal information requests (addresses, phone numbers, etc.)
   - Political extremism, conspiracy theories
   - Self-harm, dangerous activities, substance abuse
3. OFF-TOPIC REDIRECT: If user tries to discuss unrelated topics or avoid learning objectives, say:
   "I understand, but let's focus on your {language} learning goals. Based on your assessment, we need to work on [specific areas from learning plan]. Let's practice that now."
4. LEARNING PLAN ADHERENCE: ALWAYS redirect conversations back to the learning objectives. NEVER allow general conversation that doesn't serve the learning plan.

🎯 MANDATORY LEARNING FOCUS:
- You MUST keep the conversation focused on the specific learning objectives
- If the user tries to change topics, redirect them back to the learning plan
- Do NOT allow "general English practice" - stick to the specific areas identified in the assessment
- The conversation must serve the learning objectives at all times

LANGUAGE RULE: {config['rule']}
{assessment_context}
{learning_plan_context}

Start with: "{config['greeting']}"

CRITICAL: If learning plan context is available, you MUST focus the entire conversation on the current week's learning objectives. Do not deviate from this focus regardless of what the user requests."""
        
        return instructions

# Add endpoint for custom topic research using web search
@app.post("/api/custom-topic/research")
async def research_custom_topic(request: CustomTopicRequest):
    """
    Research a custom topic using OpenAI's web search capabilities with gpt-4o-search-preview
    """
    try:
        print(f"🔍 [RESEARCH] Starting REAL web search for custom topic: '{request.user_prompt}'")
        print(f"🔍 [RESEARCH] Language: {request.language}, Level: {request.level}")
        
        # Try gpt-4o-search-preview first, fallback to gpt-4o if not available
        try:
            search_response = client.chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": f"""You are a research assistant with web search capabilities. You MUST search the web for current, accurate information about the topic provided.

CRITICAL: Use your web search capabilities to find the most recent and accurate information available online about the topic.

Your research should include:
1. Current facts and recent developments (search for latest news and updates)
2. Key details like dates, locations, participants, and outcomes
3. Important vocabulary and terminology related to the topic
4. Recent news articles, official announcements, or press releases
5. Any upcoming events or scheduled activities

Format your response for {request.level} level {request.language} language learners with:
- Clear, factual information suitable for educational discussion
- Important vocabulary highlighted
- Discussion points and questions
- Cultural or political context if relevant

IMPORTANT: Always search for the most current information available online. Do not rely solely on training data."""
                    },
                    {
                        "role": "user", 
                        "content": f"Search the web for current information about: {request.user_prompt}. Find the latest news, official announcements, dates, locations, and any recent developments. This is for {request.language} language learning at {request.level} level."
                    }
                ],
                max_tokens=1500
            )
            print(f"✅ [RESEARCH] Successfully used gpt-4o-search-preview model")
            
        except Exception as search_error:
            print(f"⚠️ [RESEARCH] gpt-4o-search-preview failed: {str(search_error)}")
            print(f"🔄 [RESEARCH] Falling back to gpt-4o model for research")
            
            # Fallback to regular gpt-4o model
            search_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": f"""You are a knowledgeable research assistant helping with language learning. Provide comprehensive information about the topic for educational discussion.

Your research should include:
1. Key facts and background information about the topic
2. Important details like dates, locations, participants, and outcomes (if known)
3. Important vocabulary and terminology related to the topic
4. Historical context and significance
5. Discussion points and questions for language practice

Format your response for {request.level} level {request.language} language learners with:
- Clear, factual information suitable for educational discussion
- Important vocabulary highlighted
- Discussion points and questions
- Cultural or political context if relevant

Note: Provide the best information available from your training data, and acknowledge any limitations about current events."""
                    },
                    {
                        "role": "user", 
                        "content": f"Provide comprehensive information about: {request.user_prompt}. Include background, key facts, important vocabulary, and discussion points. This is for {request.language} language learning at {request.level} level."
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            print(f"✅ [RESEARCH] Successfully used fallback gpt-4o model")
        
        if not search_response or not search_response.choices:
            raise HTTPException(status_code=500, detail="Failed to get research results from OpenAI")
        
        research_content = search_response.choices[0].message.content
        
        print(f"✅ [RESEARCH] Real web search completed successfully")
        print(f"✅ [RESEARCH] Research content length: {len(research_content)} characters")
        print(f"🔍 [RESEARCH] Research preview: {research_content[:200]}...")
        
        # Validate that we got actual research content, not a generic response
        if len(research_content) < 100 or "I'll help you discuss" in research_content:
            print(f"⚠️ [RESEARCH] Detected generic response, attempting fallback search...")
            
            # Try a more direct search approach
            fallback_response = client.chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[
                    {
                        "role": "user", 
                        "content": f"Search the internet for current information about '{request.user_prompt}'. Find recent news, official announcements, dates, locations, and key facts. Provide specific, factual information."
                    }
                ],
                max_tokens=1200  # Removed temperature parameter for gpt-4o-search-preview
            )
            
            if fallback_response and fallback_response.choices:
                research_content = fallback_response.choices[0].message.content
                print(f"✅ [RESEARCH] Fallback search completed: {len(research_content)} characters")
        
        # Return the research data in the format expected by the frontend
        return {
            "success": True,
            "topic": request.user_prompt,
            "language": request.language,
            "level": request.level,
            "research": research_content,  # Frontend expects 'research' not 'research_content'
            "research_content": research_content,  # Keep both for compatibility
            "timestamp": "2025-06-24T19:27:03.202Z"  # Current timestamp
        }
        
    except Exception as e:
        print(f"❌ [RESEARCH] Error during web search: {str(e)}")
        print(f"❌ [RESEARCH] Full error details: {traceback.format_exc()}")
        
        # Return a fallback response so the flow doesn't break
        fallback_content = f"""I'll help you discuss {request.user_prompt}. 

This is an interesting topic that we can explore together during our conversation. I'll provide relevant information and help you practice {request.language} while discussing various aspects of this subject.

Let's have an engaging conversation about {request.user_prompt} and improve your {request.language} skills at the same time!"""
        
        return {
            "success": False,
            "topic": request.user_prompt,
            "language": request.language,
            "level": request.level,
            "research_content": fallback_content,
            "error": str(e),
            "timestamp": "2025-06-24T19:27:03.202Z"
        }

# Subscription model
class SubscriptionRequest(BaseModel):
    email: str

# Add endpoint for newsletter subscription
@app.post("/api/subscribe")
async def subscribe_to_newsletter(request: SubscriptionRequest):
    """
    Subscribe user to newsletter - stores email in MongoDB
    """
    try:
        from database import database
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, request.email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        # Check if email already exists
        subscriptions_collection = database["newsletter_subscriptions"]
        existing_subscription = await subscriptions_collection.find_one({"email": request.email})
        
        if existing_subscription:
            return {
                "success": True,
                "message": "Email already subscribed",
                "already_subscribed": True
            }
        
        # Create subscription document
        from datetime import datetime, timezone
        subscription_doc = {
            "email": request.email,
            "subscribed_at": datetime.now(timezone.utc),
            "status": "active",
            "source": "landing_page"
        }
        
        # Insert into database
        result = await subscriptions_collection.insert_one(subscription_doc)
        
        if result.inserted_id:
            print(f"✅ New newsletter subscription: {request.email}")
            return {
                "success": True,
                "message": "Successfully subscribed to newsletter",
                "already_subscribed": False
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save subscription"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Error in newsletter subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing subscription: {str(e)}"
        )

# Add endpoint for session summary storage
@app.post("/api/learning/session-summary")
async def store_session_summary(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Store comprehensive conversation analysis summary for a learning plan session
    """
    # Get parameters from query string and request body
    plan_id = request.query_params.get('plan_id')
    basic_summary = request.query_params.get('session_summary')
    
    # Try to get conversation data from request body for comprehensive analysis
    conversation_data = None
    try:
        body = await request.body()
        if body:
            conversation_data = json.loads(body)
    except:
        conversation_data = None
    
    if not plan_id:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameter: plan_id"
        )
    
    print(f"[SESSION_SUMMARY] Processing session summary for plan {plan_id}")
    print(f"[SESSION_SUMMARY] Basic summary: {basic_summary[:100] if basic_summary else 'None'}...")
    print(f"[SESSION_SUMMARY] Conversation data available: {conversation_data is not None}")
    
    try:
        from database import database
        learning_plans_collection = database.learning_plans
        
        # Find the plan
        plan = await learning_plans_collection.find_one({"id": plan_id})
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Learning plan not found"
            )
        
        # Check if the plan belongs to the current user
        if plan.get("user_id") and plan.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this learning plan"
            )
        
        # Generate comprehensive session summary
        comprehensive_summary = await generate_comprehensive_session_summary(
            plan, conversation_data, basic_summary, current_user.id
        )
        
        # Get existing session summaries or initialize empty list
        session_summaries = plan.get("session_summaries", [])
        
        # Add new comprehensive session summary
        session_summaries.append(comprehensive_summary)
        
        # Update completed sessions count and weekly schedule
        completed_sessions = plan.get("completed_sessions", 0) + 1
        total_sessions = plan.get("total_sessions", 48)
        progress_percentage = min((completed_sessions / total_sessions) * 100, 100.0)
        
        # Calculate which week this session belongs to
        sessions_per_week = 2
        new_week = ((completed_sessions - 1) // sessions_per_week) + 1
        sessions_in_week = ((completed_sessions - 1) % sessions_per_week) + 1
        
        # Update weekly schedule progress
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        if weekly_schedule:
            week_index = new_week - 1  # Convert to 0-based index
            if week_index < len(weekly_schedule):
                weekly_schedule[week_index]["sessions_completed"] = sessions_in_week
                print(f"[SESSION_SUMMARY] Updated week {new_week} sessions_completed to {sessions_in_week}")
        
        # 🔥 CRITICAL FIX: Track subscription usage when session is completed
        # This ensures subscription counter stays synchronized with learning plan progress
        try:
            users_collection = database.users
            user_result = await users_collection.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$inc": {"practice_sessions_used": 1}}
            )
            
            if user_result.modified_count > 0:
                print(f"[SESSION_SUMMARY] ✅ Incremented subscription usage for user {current_user.id}")
            else:
                print(f"[SESSION_SUMMARY] ⚠️ Failed to increment subscription usage for user {current_user.id}")
        except Exception as subscription_error:
            print(f"[SESSION_SUMMARY] ❌ Error tracking subscription usage: {str(subscription_error)}")
            # Don't fail the session saving if subscription tracking fails
            pass
        
        # Update the plan
        update_data = {
            "session_summaries": session_summaries,
            "completed_sessions": completed_sessions,
            "progress_percentage": progress_percentage
        }
        
        # Update weekly schedule if modified
        if weekly_schedule:
            update_data["plan_content.weekly_schedule"] = weekly_schedule
        
        result = await learning_plans_collection.update_one(
            {"id": plan_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to update learning plan with session summary"
            )
        
        print(f"✅ Comprehensive session summary stored for plan {plan_id}")
        print(f"✅ Session {completed_sessions}/{total_sessions} completed ({progress_percentage:.1f}%)")
        print(f"✅ Week {new_week}, session {sessions_in_week} of {sessions_per_week}")
        
        return {
            "success": True,
            "completed_sessions": completed_sessions,
            "progress_percentage": progress_percentage,
            "total_summaries": len(session_summaries),
            "current_week": new_week,
            "sessions_in_week": sessions_in_week,
            "comprehensive_summary": comprehensive_summary
        }
        
    except Exception as e:
        print(f"❌ Error storing session summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error storing session summary: {str(e)}"
        )

async def generate_comprehensive_session_summary(plan, conversation_data, basic_summary, user_id):
    """Generate a comprehensive session summary with AI analysis"""
    try:
        # Get plan details
        language = plan.get("language", "english")
        level = plan.get("proficiency_level", "B1")
        completed_sessions = plan.get("completed_sessions", 0) + 1
        
        # Get current week focus
        sessions_per_week = 2
        current_week = ((completed_sessions - 1) // sessions_per_week) + 1
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])
        current_week_data = weekly_schedule[current_week - 1] if current_week <= len(weekly_schedule) else None
        week_focus = current_week_data.get("focus", "General language practice") if current_week_data else "General language practice"
        
        print(f"[SESSION_SUMMARY] Generating summary for session {completed_sessions}, week {current_week}")
        print(f"[SESSION_SUMMARY] Week focus: {week_focus}")
        print(f"[SESSION_SUMMARY] Basic summary: {basic_summary}")
        print(f"[SESSION_SUMMARY] Conversation data available: {conversation_data is not None}")
        
        # Extract conversation content if available
        conversation_content = ""
        if conversation_data and "messages" in conversation_data:
            messages = conversation_data["messages"]
            print(f"[SESSION_SUMMARY] Found {len(messages)} messages in conversation data")
            for msg in messages[-10:]:  # Last 10 messages for context
                role = "Student" if msg.get("role") == "user" else "Tutor"
                content = msg.get("content", "")
                conversation_content += f"{role}: {content}\n"
        else:
            print(f"[SESSION_SUMMARY] No conversation messages found, using basic summary only")
        
        # Always generate a comprehensive summary, even without conversation data
        if conversation_content:
            # Full analysis with conversation data
            prompt = f"""Analyze this {language} language learning session and create a comprehensive summary.

STUDENT PROFILE:
- Language: {language}
- Level: {level}
- Session: {completed_sessions}
- Current Week Focus: {week_focus}

CONVERSATION EXCERPT:
{conversation_content}

BASIC SESSION INFO:
{basic_summary if basic_summary else "5-minute conversation session completed"}

Create a comprehensive summary that includes:
1. Session overview (duration, topics covered)
2. Language skills demonstrated (pronunciation, grammar, vocabulary, fluency)
3. Progress towards weekly learning objectives
4. Key achievements and improvements observed
5. Areas for continued focus
6. Specific examples from the conversation

Format as a detailed but concise summary suitable for tracking learning progress."""
        else:
            # Generate comprehensive summary based on basic info and learning objectives
            prompt = f"""Create a comprehensive learning session summary based on the available information.

STUDENT PROFILE:
- Language: {language}
- Level: {level}
- Session: {completed_sessions}
- Current Week Focus: {week_focus}

SESSION INFORMATION:
{basic_summary if basic_summary else "5-minute conversation session completed"}

Even without detailed conversation data, create a comprehensive summary that includes:
1. Session overview based on available information
2. Expected language skills practice for {level} level {language}
3. Progress towards weekly learning objectives: "{week_focus}"
4. Likely achievements and improvements for this session type
5. Areas for continued focus based on the weekly objectives
6. Encouragement and next steps

Make it detailed and educational, focusing on the learning objectives and expected outcomes for a {level} level {language} student working on: {week_focus}."""

        print(f"[SESSION_SUMMARY] Sending prompt to OpenAI (length: {len(prompt)} chars)")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert language learning analyst. Create detailed, insightful summaries of student progress that are educational and encouraging."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,  # Increased for more comprehensive summaries
            temperature=0.3
        )
        
        if response and response.choices:
            comprehensive_summary = response.choices[0].message.content.strip()
            print(f"[SESSION_SUMMARY] ✅ Generated comprehensive summary: {len(comprehensive_summary)} characters")
            return comprehensive_summary
        else:
            print(f"[SESSION_SUMMARY] ❌ No response from OpenAI")
            # Enhanced fallback summary
            return f"""**Session {completed_sessions} Summary**

**Session Overview:**
Completed a {basic_summary if basic_summary else '5-minute conversation session'} focusing on {language} language practice at {level} level.

**Weekly Learning Focus:**
This session addressed the current week's objective: {week_focus}

**Progress Made:**
- Continued development of {language} communication skills
- Practice aligned with {level} proficiency level expectations
- Engagement with weekly learning objectives

**Areas for Continued Focus:**
- Further practice with {week_focus.lower()}
- Continued application of {level} level language structures
- Building confidence in {language} communication

**Next Steps:**
Continue practicing the weekly focus areas and maintain consistent engagement with the learning plan objectives."""
            
    except Exception as e:
        print(f"[SESSION_SUMMARY] ❌ Error generating comprehensive summary: {str(e)}")
        import traceback
        print(f"[SESSION_SUMMARY] Full traceback: {traceback.format_exc()}")
        
        # Enhanced fallback summary with error handling
        return f"""**Session {completed_sessions} Summary**

**Session Overview:**
Completed a {basic_summary if basic_summary else 'conversation session'} in {language} at {level} level.

**Weekly Learning Focus:**
{week_focus}

**Progress Made:**
- Continued {language} language practice
- Engagement with {level} level content
- Progress towards weekly learning objectives

**Areas for Continued Focus:**
- {week_focus.lower()}
- Consistent practice and application
- Building fluency and confidence

This session contributed to the overall learning journey and weekly objectives."""

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
            exercise_type=request.exercise_type
        )
        
        return assessment
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in sentence assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing sentence: {str(e)}")

# Add endpoint for speaking assessment
@app.post("/api/speaking/assess", response_model=SpeakingAssessmentResponse)
async def assess_speaking(request: SpeakingAssessmentRequest):
    try:
        # Transcribe audio if provided
        recognized_text = None
        if request.audio_base64:
            try:
                print("Transcribing audio for speaking assessment...")
                recognized_text = await recognize_speech(request.audio_base64, request.language)
                print(f"Transcribed text: '{recognized_text}'")
            except Exception as e:
                print(f"Error transcribing audio: {str(e)}")
                raise HTTPException(status_code=400, detail="Failed to transcribe audio")
        
        if not recognized_text or recognized_text.strip() == "":
            raise HTTPException(status_code=400, detail="No speech detected")
        
        # Evaluate language proficiency
        assessment = await evaluate_language_proficiency(
            text=recognized_text,
            language=request.language,
            duration=request.duration or 60,
            prompt=request.prompt
        )
        
        return assessment
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in speaking assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assessing speaking: {str(e)}")

# Add endpoint for generating speaking prompts
@app.get("/api/speaking/prompts")
async def get_speaking_prompts(language: str, level: str, count: int = 3):
    try:
        prompts = await generate_speaking_prompts(language, level, count)
        return {"prompts": prompts}
    except Exception as e:
        print(f"Error generating speaking prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating prompts: {str(e)}")

# Add mock token endpoint for testing
@app.post("/api/mock-token")
async def generate_mock_token(request: TutorSessionRequest):
    """
    Mock endpoint for testing when OpenAI API is not available
    """
    try:
        print("🧪 [MOCK] Creating mock ephemeral token for testing")
        
        # Return a mock response that matches the expected format
        mock_response = {
            "id": "sess_mock_test_session",
            "object": "realtime.session",
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "expires_at": 1234567890,
            "client_secret": {
                "value": "ek_mock_test_key_for_development",
                "expires_at": 1234567890
            },
            "ephemeral_key": "ek_mock_test_key_for_development"
        }
        
        print("✅ [MOCK] Mock token created successfully")
        return mock_response
        
    except Exception as e:
        print(f"❌ [MOCK] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files from frontend build - MUST be at the end after all API routes
print("="*80)
print("🔧 STATIC FILE MOUNTING DEBUG")
print("="*80)

# Get the path to the frontend build directory
# In Docker, we're running from /app/backend, so frontend/out is at /app/frontend/out
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production":
    # In production (Railway), use absolute path from app root
    frontend_build_path = Path("/app/frontend/out")
    print("🚀 PRODUCTION MODE DETECTED")
else:
    # In development, use relative path
    frontend_build_path = Path(__file__).parent.parent / "frontend" / "out"
    print("🛠️ DEVELOPMENT MODE DETECTED")

print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
print(f"Railway: {os.getenv('RAILWAY_ENVIRONMENT', 'false')}")
print(f"NODE_ENV: {os.getenv('NODE_ENV', 'not_set')}")
print(f"Current working directory: {os.getcwd()}")
print(f"__file__ location: {Path(__file__).parent}")
print(f"Calculated frontend build path: {frontend_build_path}")
print(f"Frontend build path exists: {frontend_build_path.exists()}")

# Additional debugging - check if files exist
if frontend_build_path.exists():
    try:
        all_files = list(frontend_build_path.iterdir())
        print(f"Total files/dirs in build path: {len(all_files)}")
        html_files = list(frontend_build_path.glob("*.html"))
        print(f"HTML files found: {len(html_files)}")
        print(f"First 5 HTML files: {[f.name for f in html_files[:5]]}")
        
        # Check specific files
        for page in ["privacy.html", "terms.html", "cookies.html", "about.html"]:
            page_path = frontend_build_path / page
            print(f"  {page}: {'✅ EXISTS' if page_path.exists() else '❌ MISSING'}")
    except Exception as e:
        print(f"❌ Error listing files: {e}")
else:
    print("❌ Frontend build path does not exist!")

# Only mount static files if the build directory exists
if frontend_build_path.exists():
    print(f"Mounting static files from: {frontend_build_path}")
    
    # List some files for debugging
    html_files = list(frontend_build_path.glob("*.html"))
    print(f"Found {len(html_files)} HTML files: {[f.name for f in html_files[:10]]}")
    
    # Check for specific files
    for page in ["privacy.html", "terms.html", "cookies.html", "gdpr.html"]:
        page_path = frontend_build_path / page
        print(f"  {page}: {'EXISTS' if page_path.exists() else 'MISSING'}")
    
    # 🔧 FIX: Add explicit route handlers for static pages
    # FastAPI's StaticFiles html=True is not working reliably, so we'll handle these explicitly
    
    @app.get("/privacy")
    async def serve_privacy():
        privacy_file = frontend_build_path / "privacy.html"
        if privacy_file.exists():
            return FileResponse(privacy_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Privacy page not found")
    
    @app.get("/terms")
    async def serve_terms():
        terms_file = frontend_build_path / "terms.html"
        if terms_file.exists():
            return FileResponse(terms_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Terms page not found")
    
    @app.get("/cookies")
    async def serve_cookies():
        cookies_file = frontend_build_path / "cookies.html"
        if cookies_file.exists():
            return FileResponse(cookies_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Cookies page not found")
    
    @app.get("/gdpr")
    async def serve_gdpr():
        gdpr_file = frontend_build_path / "gdpr.html"
        if gdpr_file.exists():
            return FileResponse(gdpr_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="GDPR page not found")
    
    @app.get("/about")
    async def serve_about():
        about_file = frontend_build_path / "about.html"
        if about_file.exists():
            return FileResponse(about_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="About page not found")
    
    @app.get("/help")
    async def serve_help():
        help_file = frontend_build_path / "help.html"
        if help_file.exists():
            return FileResponse(help_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Help page not found")
    
    @app.get("/careers")
    async def serve_careers():
        careers_file = frontend_build_path / "careers.html"
        if careers_file.exists():
            return FileResponse(careers_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Careers page not found")
    
    @app.get("/press")
    async def serve_press():
        press_file = frontend_build_path / "press.html"
        if press_file.exists():
            return FileResponse(press_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Press page not found")
    
    @app.get("/blog")
    async def serve_blog():
        blog_file = frontend_build_path / "blog.html"
        if blog_file.exists():
            return FileResponse(blog_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Blog page not found")
    
    @app.get("/research")
    async def serve_research():
        research_file = frontend_build_path / "research.html"
        if research_file.exists():
            return FileResponse(research_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Research page not found")
    
    @app.get("/community")
    async def serve_community():
        community_file = frontend_build_path / "community.html"
        if community_file.exists():
            return FileResponse(community_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Community page not found")
    
    @app.get("/status")
    async def serve_status():
        status_file = frontend_build_path / "status.html"
        if status_file.exists():
            return FileResponse(status_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Status page not found")
    
    # Add admin panel route
    @app.get("/_admin")
    async def serve_admin_panel():
        admin_file = frontend_build_path / "_admin" / "index.html"
        if admin_file.exists():
            return FileResponse(admin_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Admin panel not found")
    
    @app.get("/_admin/{path:path}")
    async def serve_admin_assets(path: str):
        admin_asset = frontend_build_path / "_admin" / path
        if admin_asset.exists():
            # Determine media type based on file extension
            if path.endswith('.js'):
                media_type = "application/javascript"
            elif path.endswith('.css'):
                media_type = "text/css"
            elif path.endswith('.html'):
                media_type = "text/html"
            elif path.endswith('.ico'):
                media_type = "image/x-icon"
            elif path.endswith('.json'):
                media_type = "application/json"
            else:
                media_type = "application/octet-stream"
            
            return FileResponse(admin_asset, media_type=media_type)
        raise HTTPException(status_code=404, detail="Admin asset not found")
    
    # Add explicit handlers for auth routes
    @app.get("/auth/login")
    async def serve_auth_login():
        login_file = frontend_build_path / "auth" / "login.html"
        if login_file.exists():
            return FileResponse(login_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Login page not found")
    
    @app.get("/auth/signup")
    async def serve_auth_signup():
        signup_file = frontend_build_path / "auth" / "signup.html"
        if signup_file.exists():
            return FileResponse(signup_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Signup page not found")
    
    @app.get("/auth/forgot-password")
    async def serve_auth_forgot_password():
        forgot_file = frontend_build_path / "auth" / "forgot-password.html"
        if forgot_file.exists():
            return FileResponse(forgot_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Forgot password page not found")
    
    @app.get("/auth/reset-password")
    async def serve_auth_reset_password():
        reset_file = frontend_build_path / "auth" / "reset-password.html"
        if reset_file.exists():
            return FileResponse(reset_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Reset password page not found")
    
    # Add explicit handlers for main application routes
    @app.get("/language-selection")
    async def serve_language_selection():
        file_path = frontend_build_path / "language-selection.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Language selection page not found")
    
    @app.get("/level-selection")
    async def serve_level_selection():
        file_path = frontend_build_path / "level-selection.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Level selection page not found")
    
    @app.get("/topic-selection")
    async def serve_topic_selection():
        file_path = frontend_build_path / "topic-selection.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Topic selection page not found")
    
    @app.get("/speech")
    async def serve_speech():
        file_path = frontend_build_path / "speech.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Speech page not found")
    
    @app.get("/assessment/speaking")
    async def serve_assessment_speaking():
        file_path = frontend_build_path / "assessment" / "speaking.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Speaking assessment page not found")
    
    @app.get("/profile")
    async def serve_profile():
        file_path = frontend_build_path / "profile.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Profile page not found")
    
    @app.get("/loading-modal-demo")
    async def serve_loading_modal_demo():
        file_path = frontend_build_path / "loading-modal-demo.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Loading modal demo page not found")
    
    @app.get("/flow")
    async def serve_flow():
        file_path = frontend_build_path / "flow.html"
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Flow page not found")
    
    print("✅ Added explicit route handlers for static pages, auth routes, and main application routes")
    
    # Still mount StaticFiles for other assets like _next, images, etc.
    app.mount("/", StaticFiles(directory=str(frontend_build_path), html=True), name="static")
else:
    print(f"Warning: Frontend build directory not found at {frontend_build_path}")
    
    # Add a fallback route for the root path
    @app.get("/")
    async def root():
        return {"message": "Language Tutor API is running", "frontend_build": "not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
