import os
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# Import production-safe logging
from logging_config import logger, get_logger

# Import MongoDB and authentication modules
from database import init_db, client, database, DATABASE_NAME
from auth import get_current_user, get_optional_current_user_from_request
from models import UserResponse
from auth_routes import router as auth_router
from bson import ObjectId

# Import sentence assessment functionality
from sentence_assessment import SentenceAssessmentRequest, SentenceAssessmentResponse, GrammarIssue, \
    recognize_speech, analyze_sentence, generate_exercises

# Import background sentence analysis functionality
from background_sentence_analysis import (
    SentenceEvaluationRequest, SentenceEvaluationResponse,
    BackgroundAnalysisRequest, BackgroundAnalysisResponse,
    evaluate_sentence_worthiness, perform_background_analysis,
    process_sentence_for_background_analysis
)

# Import speaking assessment functionality
from speaking_assessment import SpeakingAssessmentRequest, SpeakingAssessmentResponse, SkillScore, \
    evaluate_language_proficiency, generate_speaking_prompts

# Load environment variables
load_dotenv()


# Check if OpenAI API key is configured
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY is not configured in environment")
    logger.error("Please configure OPENAI_API_KEY in environment variables")

app = FastAPI(title="Language Tutor Backend API")

# 🚀 PERFORMANCE: Enable GZip compression for all responses
# This reduces payload sizes by 60-80% (e.g., 15KB → 3KB)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6     # Balance between speed and compression ratio (1-9)
)

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
# from enhanced_export_routes import router as enhanced_export_router  # Temporarily disabled due to plotly dependency
app.include_router(export_router)
# app.include_router(enhanced_export_router)  # Temporarily disabled due to plotly dependency

# Include chat routes
from chat_routes import router as chat_router
from vector_chatbot import router as vector_chat_router
from contextual_chatbot import router as contextual_chat_router
app.include_router(chat_router)
app.include_router(vector_chat_router)
app.include_router(contextual_chat_router)

# Include admin routes
from admin_routes import router as admin_router
app.include_router(admin_router)

# Include stripe routes
from stripe_routes import router as stripe_router
app.include_router(stripe_router)


# Include notification routes
from notification_routes import router as notification_router
app.include_router(notification_router, prefix="/api")

# Include low minutes alert routes
from low_minutes_alert import router as low_minutes_router
app.include_router(low_minutes_router)

# Include health ping routes
from health_ping_routes import router as health_ping_router
app.include_router(health_ping_router)

# Include share routes
from share_routes import router as share_router
app.include_router(share_router)

# Include URL redirect routes
from url_redirect_routes import router as url_redirect_router
app.include_router(url_redirect_router)

# Include voice sample routes
from voice_sample_routes import router as voice_sample_router
app.include_router(voice_sample_router)

# Include conversation help routes
from conversation_help_routes import router as conversation_help_router
app.include_router(conversation_help_router)

# Include session heartbeat routes
from session_heartbeat_routes import router as session_heartbeat_router
app.include_router(session_heartbeat_router)

# Include consent routes
from app.consent.routes import router as consent_router
app.include_router(consent_router)

# Include institution routes
from app.institution.routes import router as institution_router
from app.institution.dashboard_routes import router as dashboard_router
app.include_router(institution_router)
app.include_router(dashboard_router)

# Include tutor routes
from app.tutor.routes import router as tutor_router
app.include_router(tutor_router)

# Include tutor dashboard routes (NEW: Authentication & Dashboard endpoints)
from app.tutor.tutor_routes import router as tutor_dashboard_router
app.include_router(tutor_dashboard_router)

# Include learner routes
from app.learner.routes import router as learner_router
app.include_router(learner_router)

# Include activation codes routes
from activation_codes_routes import router as activation_codes_router
app.include_router(activation_codes_router)

# Create images directory for URL shortener
os.makedirs("static/images", exist_ok=True)

# Image URL shortener endpoints
import hashlib
from datetime import datetime
from fastapi.responses import FileResponse

@app.post("/api/shorten-image")
async def shorten_openai_image(request: dict):
    """Download OpenAI image and return short URL"""
    try:
        openai_url = request.get('url')
        if not openai_url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # For testing, allow any image URL, but prioritize OpenAI URLs
        if 'oaidalleapiprodscus.blob.core.windows.net' not in openai_url:
            print(f"[IMAGE_SHORTENER] ⚠️ Non-OpenAI URL detected: {openai_url}")
        
        # Generate unique ID from URL
        url_hash = hashlib.md5(openai_url.encode()).hexdigest()
        image_id = url_hash[:12]  # Use first 12 characters
        image_path = f"static/images/{image_id}.png"
        
        print(f"[IMAGE_SHORTENER] Processing URL: {openai_url}")
        print(f"[IMAGE_SHORTENER] Generated image_id: {image_id}")
        print(f"[IMAGE_SHORTENER] Image path: {image_path}")
        
        # Check if image already exists
        if not os.path.exists(image_path):
            print(f"[IMAGE_SHORTENER] Image not cached, downloading...")
            
            # Download image from OpenAI using requests (same as share_routes.py)
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/png,image/jpeg,image/*;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(openai_url, headers=headers, timeout=30, allow_redirects=True)
            print(f"[IMAGE_SHORTENER] Download response status: {response.status_code}")
            
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                print(f"[IMAGE_SHORTENER] ✅ Image saved successfully: {len(response.content)} bytes")
            else:
                print(f"[IMAGE_SHORTENER] ❌ Failed to download image: HTTP {response.status_code}")
                raise HTTPException(status_code=400, detail="Failed to download image")
        else:
            print(f"[IMAGE_SHORTENER] ✅ Image already cached")
        
        # Return short URL
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        short_url = f"{base_url}/api/img/{image_id}"
        
        print(f"[IMAGE_SHORTENER] ✅ Short URL created: {short_url}")
        
        return {
            "short_url": short_url,
            "image_id": image_id,
            "original_url": openai_url
        }
        
    except Exception as e:
        print(f"[IMAGE_SHORTENER] ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error shortening image URL: {str(e)}")

@app.get("/api/img/{image_id}")
async def serve_image(image_id: str):
    """Serve shortened image"""
    try:
        # Validate image_id (alphanumeric only)
        if not image_id.isalnum() or len(image_id) != 12:
            raise HTTPException(status_code=400, detail="Invalid image ID")
        
        image_path = f"static/images/{image_id}.png"
        
        print(f"[IMAGE_SHORTENER] Serving image: {image_id}")
        print(f"[IMAGE_SHORTENER] Image path: {image_path}")
        print(f"[IMAGE_SHORTENER] File exists: {os.path.exists(image_path)}")
        
        if os.path.exists(image_path):
            return FileResponse(
                image_path, 
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
            )
        else:
            print(f"[IMAGE_SHORTENER] ❌ Image not found: {image_path}")
            raise HTTPException(status_code=404, detail="Image not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[IMAGE_SHORTENER] ❌ Error serving image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")

@app.post("/api/cleanup-images")
async def cleanup_old_images():
    """Remove images older than 24 hours"""
    try:
        if not os.path.exists("static/images"):
            return {"message": "No images directory"}
        
        now = datetime.now()
        deleted_count = 0
        
        for filename in os.listdir("static/images"):
            file_path = os.path.join("static/images", filename)
            if os.path.isfile(file_path):
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if (now - file_time).days > 1:  # Older than 1 day
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"[IMAGE_SHORTENER] Deleted old image: {filename}")
        
        print(f"[IMAGE_SHORTENER] Cleanup completed: {deleted_count} files deleted")
        return {"message": f"Deleted {deleted_count} old images"}
        
    except Exception as e:
        print(f"[IMAGE_SHORTENER] ❌ Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


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

# Enhanced monitoring middleware with Slack integration
from monitoring import MonitoringMiddleware, RequestLoggingMiddleware

# Add monitoring middleware (replaces basic error handling)
app.add_middleware(MonitoringMiddleware, performance_threshold=5.0)

# Add request logging middleware for development
if os.getenv("ENVIRONMENT") == "development":
    app.add_middleware(RequestLoggingMiddleware)

# Simple test endpoint to verify API connectivity
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Language Tutor API is running"}

# Enhanced health check endpoint with comprehensive error handling
@app.get("/health")
@app.get("/api/health")  # Add an additional route to match frontend expectations
async def health_check():
    import time
    import platform
    
    try:
        # Current timestamp
        current_time = time.time()
        
        # Get environment information
        environment = os.getenv("ENVIRONMENT", "production")
        is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("RAILWAY") == "true"
        
        # Quick configuration checks (no network calls)
        openai_configured = os.getenv("OPENAI_API_KEY") is not None
        
        # Check if MongoDB URL is configured (don't test connection)
        mongodb_configured = False
        for var_name in ["MONGODB_URL", "MONGO_URL", "MONGO_PUBLIC_URL"]:
            if os.getenv(var_name):
                mongodb_configured = True
                break
        
        # Enhanced health status with both flat and nested structure for compatibility
        health_status = {
            "status": "ok",
            "timestamp": current_time,
            "environment": environment,
            "railway": is_railway,
            "port": os.getenv("PORT", "3001"),
            "service": "language-tutor-backend",
            "python_version": "3.11",
            "openai_configured": openai_configured,
            "mongodb_configured": mongodb_configured,
            "frontend_mode": "nextjs_server",  # Using Next.js server, not static export
            "version": "1.0.0",
            "uptime": current_time,
            # Add nested system_info for backward compatibility with legacy frontend code
            "system_info": {
                "python_version": "3.11",
                "platform": platform.system(),
                "timestamp": current_time,
                "environment": environment,
                "railway": is_railway
            },
            "api_routes": [
                "/api/health",
                "/api/test",
                "/api/realtime/token",
                "/api/speaking/assess",
                "/api/sentence/assess",
                "/auth/login",
                "/auth/signup"
            ]
        }
        
        print(f"[HEALTH_CHECK] ✅ Health check successful: {health_status['status']}")
        return health_status
        
    except Exception as e:
        error_message = str(e)
        print(f"[HEALTH_CHECK] ❌ Health check error: {error_message}")
        
        # Even if there's an error, return a 200 status so Railway doesn't think the service is down
        # But provide both flat and nested error information
        error_response = {
            "status": "error",
            "error": error_message,
            "timestamp": time.time(),
            "service": "language-tutor-backend",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "railway": os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("RAILWAY") == "true",
            "port": os.getenv("PORT", "3001"),
            "python_version": "3.11",
            "openai_configured": False,
            "mongodb_configured": False,
            # Add nested system_info for backward compatibility
            "system_info": {
                "python_version": "3.11",
                "platform": "unknown",
                "timestamp": time.time(),
                "environment": os.getenv("ENVIRONMENT", "production"),
                "railway": os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("RAILWAY") == "true"
            }
        }
        
        return error_response

# Define models for request validation
class TutorSessionRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, ash, ballad, coral, echo, sage, shimmer, verse
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: Optional[str] = None  # User prompt for custom topics
    assessment_data: Optional[Dict[str, Any]] = None  # Assessment data from speaking assessment
    research_data: Optional[str] = None  # Pre-researched data for custom topics
    conversation_history: Optional[str] = None  # Previous conversation context for reconnections

# Define a new model for custom topic prompts
class CustomTopicRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, ash, ballad, coral, echo, sage, shimmer, verse
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: str  # The custom prompt from the user

# Realtime Usage Data model
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
    start_time: Optional[int] = None  # Unix timestamp for session start
    end_time: Optional[int] = None    # Unix timestamp for session end

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
async def generate_token(request: TutorSessionRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    from monitoring import send_error_alert, send_business_logic_alert, AlertContext, AlertSeverity
    
    try:
        print("="*80)
        print(f"🌐 [UNIVERSAL] Creating ephemeral token for all browsers")
        print(f"🌐 [UNIVERSAL] Language: {request.language}")
        print(f"🌐 [UNIVERSAL] Level: {request.level}")
        print(f"🌐 [UNIVERSAL] Topic: {request.topic}")
        print("="*80)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            # Send alert for missing API key
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
        
        # ✅ Build universal instructions that work on all browsers
        instructions = build_universal_instructions(request)
        
        print(f"✅ [UNIVERSAL] Instructions created: {len(instructions)} characters")
        
        # 🎤 Get user's preferred voice fresh from database to ensure latest selection
        preferred_voice = "alloy"  # Default voice
        if current_user:
            try:
                from database import users_collection
                from bson import ObjectId
                
                # Get fresh user data from database to ensure we have the latest voice preference
                user_doc = await users_collection.find_one({"_id": ObjectId(current_user.id)})
                if user_doc and "preferred_voice" in user_doc:
                    preferred_voice = user_doc["preferred_voice"]
                    print(f"🎤 [VOICE] Fresh voice preference from DB: {preferred_voice}")
                else:
                    print(f"🎤 [VOICE] No voice preference found in DB, using default: {preferred_voice}")
            except Exception as e:
                print(f"🎤 [VOICE] Error fetching voice preference: {str(e)}")
                preferred_voice = "alloy"
        
        # Use request voice if provided, otherwise use user's preferred voice
        selected_voice = request.voice or preferred_voice
        
        print(f"🎤 [VOICE] User preferred voice: {preferred_voice}")
        print(f"🎤 [VOICE] Request voice: {request.voice}")
        print(f"🎤 [VOICE] Selected voice: {selected_voice}")
        
        # ✅ Create ephemeral token with complete configuration
        # This approach works reliably on desktop AND mobile browsers
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")
        payload = {
            "model": model,
            "voice": selected_voice,
            "instructions": instructions,  # ✅ All instructions here
            "modalities": ["audio", "text"],
            "input_audio_transcription": {
                "model": "gpt-4o-transcribe" if os.getenv("USE_GPT4O_TRANSCRIBE", "true").lower() == "true" else "whisper-1",  # 🚀 CONFIGURABLE: Use environment variable to control model
                "language": get_language_iso_code(request.language) if request.language else "en"
            },
            "turn_detection": {
                "type": "semantic_vad",
                "eagerness": "low",
                "create_response": True,
                "interrupt_response": True
            },
            "input_audio_noise_reduction": {
                "type": "near_field"  # Focus on learner's voice for semantic analysis
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
        
        # Log session creation
        session_id = result.get('id', 'unknown')
        print("="*80)
        print(f"💰 [USAGE_LOG] SESSION CREATED")
        print(f"Session ID: {session_id}")
        print(f"User ID: {current_user.id if current_user else 'guest'}")
        print(f"Language: {request.language}")
        print(f"Level: {request.level}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*80)
        
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
        # Enhanced topic mapping with detailed descriptions
        topic_details = {
            # Core Topics
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
            
            # Daily Life Topics
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
            
            # Entertainment & Culture
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
            
            # Modern Life Topics
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
            
            # Lifestyle & Personal Topics
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

📚 TOPIC DETAILS:
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

# 🎯 STRATEGY 2: Add summarization endpoint for token optimization
class SummarizeRequest(BaseModel):
    transcript: str

@app.post("/api/summarize")
async def summarize_conversation(request: SummarizeRequest):
    """
    Summarize conversation transcript using gpt-4o-mini for cost efficiency.
    Used to reduce cached token usage in OpenAI Realtime API.
    """
    try:
        print(f"📝 [SUMMARIZATION] Received transcript: {len(request.transcript)} characters")
        
        if not request.transcript or len(request.transcript.strip()) < 10:
            raise HTTPException(status_code=400, detail="Transcript too short for summarization")
        
        # Use gpt-4o-mini for cost-effective summarization
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize this language learning conversation in 2-3 sentences. 
Focus on topics discussed and any corrections made. Ignore grammar details.

Conversation:
{request.transcript}

Summary:"""
                }
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        if not response or not response.choices:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        summary = response.choices[0].message.content.strip()
        
        print(f"✅ [SUMMARIZATION] Generated summary: {len(summary)} characters")
        print(f"📝 [SUMMARIZATION] Summary: {summary}")
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(request.transcript),
            "summary_length": len(summary),
            "compression_ratio": f"{(len(summary) / len(request.transcript) * 100):.1f}%"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [SUMMARIZATION] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

# Add endpoint for realtime usage logging
@app.post("/api/realtime/usage-log")
async def log_realtime_usage(
    usage_data: RealtimeUsageData,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """Store realtime API usage data and calculate costs"""
    try:
        from database import usage_logs_collection
        from datetime import datetime, timezone
        from openai_organization_costs import fetch_organization_costs, datetime_to_unix_timestamp
        
        # OpenAI Realtime API Pricing Configuration
        # Reference: https://platform.openai.com/docs/pricing
        PRICING = {
            "gpt-realtime": {
                "audio_input": 32.0 / 1_000_000,      # $32/1M
                "audio_output": 64.0 / 1_000_000,     # $64/1M
                "text_input": 4.0 / 1_000_000,        # $4/1M
                "text_output": 16.0 / 1_000_000,      # $16/1M
                "cached_audio": 0.40 / 1_000_000,     # $0.40/1M
                "cached_text": 2.0 / 1_000_000        # $2/1M (estimated)
            },
            "gpt-realtime-mini": {
                "audio_input": 10.0 / 1_000_000,      # $10/1M
                "audio_output": 20.0 / 1_000_000,     # $20/1M
                "text_input": 0.6 / 1_000_000,        # $0.60/1M
                "text_output": 2.4 / 1_000_000,       # $2.40/1M
                "cached_audio": 0.30 / 1_000_000,     # $0.30/1M
                "cached_text": 0.30 / 1_000_000       # $0.30/1M (estimated)
            }
        }
        
        # 🔥 FIX: Always use environment variable model for cost calculation
        # The usage_data.model might be outdated or incorrect
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")
        
        print(f"💰 [USAGE_LOG] Using model from environment: {model}")
        
        # Log if usage_data has a different model (for debugging)
        if hasattr(usage_data, 'model') and usage_data.model and usage_data.model != model:
            print(f"ℹ️ [USAGE_LOG] Note: usage_data.model was '{usage_data.model}' but using environment model '{model}' for cost calculation")
        
        # Get pricing for the specific model
        if model not in PRICING:
            print(f"⚠️ [USAGE_LOG] Unknown model '{model}', defaulting to gpt-realtime-mini pricing")
            model = "gpt-realtime-mini"
        
        pricing = PRICING[model]
        
        print(f"💰 [USAGE_LOG] Using pricing for model: {model}")
        
        # Calculate costs based on the selected model's pricing
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
        print(f"💰 [USAGE_LOG] SESSION COMPLETED")
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
        
        # 🔥 NEW: Fetch organization costs from OpenAI API
        organization_cost = None
        organization_cost_data = None
        
        # Convert session timestamps to Unix timestamps if provided
        if usage_data.start_time:
            # 🔥 SIMPLIFIED FIX: Only use start_time, let API handle daily bucketing
            # The OpenAI API works best with just start_time and returns daily buckets
            import time
            current_time = int(time.time())
            
            start_time = usage_data.start_time
            
            # Validate timestamp is in the past
            if start_time > current_time:
                print(f"[ORG_COSTS] ⚠️ Start timestamp is in the future! start={start_time}, current={current_time}")
                print(f"[ORG_COSTS] ⚠️ Skipping organization cost fetch - invalid timestamp")
            else:
                print(f"[ORG_COSTS] Fetching organization costs for start_time: {start_time}")
                
                try:
                    # Only pass start_time, let API return daily bucket
                    org_cost_result = await fetch_organization_costs(
                        start_time=start_time,
                        end_time=None,  # Let API handle bucketing
                        limit=1
                    )
                
                    if org_cost_result:
                        organization_cost = org_cost_result.get("cost", 0.0)
                        organization_cost_data = org_cost_result
                        print(f"[ORG_COSTS] ✅ Organization cost fetched: ${organization_cost:.4f}")
                        print(f"[ORG_COSTS] Currency: {org_cost_result.get('currency', 'usd').upper()}")
                    else:
                        print(f"[ORG_COSTS] ⚠️ No organization cost data available")
                except Exception as org_cost_error:
                    print(f"[ORG_COSTS] ❌ Error fetching organization costs: {str(org_cost_error)}")
        else:
            # If timestamps not provided, try to parse from session_start string only
            try:
                if usage_data.session_start:
                    from dateutil import parser
                    import time
                    
                    start_dt = parser.parse(usage_data.session_start)
                    start_timestamp = datetime_to_unix_timestamp(start_dt)
                    current_time = int(time.time())
                    
                    # Validate timestamp is in the past
                    if start_timestamp > current_time:
                        print(f"[ORG_COSTS] ⚠️ Parsed start timestamp is in the future! start={start_timestamp}, current={current_time}")
                        print(f"[ORG_COSTS] ⚠️ Skipping organization cost fetch - invalid timestamp")
                    else:
                        # 🔥 FIX: Only use start_time, let API handle daily bucketing
                        print(f"[ORG_COSTS] Parsed start timestamp from session string: {start_timestamp}")
                        
                        # Only pass start_time, let API return daily bucket
                        org_cost_result = await fetch_organization_costs(
                            start_time=start_timestamp,
                            end_time=None,  # 🔥 FIX: Don't send end_time, let API handle bucketing
                            limit=1
                        )
                        
                        if org_cost_result:
                            organization_cost = org_cost_result.get("cost", 0.0)
                            organization_cost_data = org_cost_result
                            print(f"[ORG_COSTS] ✅ Organization cost fetched: ${organization_cost:.4f}")
                        else:
                            print(f"[ORG_COSTS] ⚠️ No organization cost data available")
            except Exception as parse_error:
                print(f"[ORG_COSTS] ⚠️ Could not parse session timestamp: {str(parse_error)}")
        
        # Log organization cost comparison if available
        if organization_cost is not None:
            cost_difference = abs(total_cost - organization_cost)
            cost_difference_pct = (cost_difference / total_cost * 100) if total_cost > 0 else 0
            
            print("-"*80)
            print(f"COST COMPARISON:")
            print(f"  Calculated Cost: ${total_cost:.4f}")
            print(f"  Organization Cost: ${organization_cost:.4f}")
            print(f"  Difference: ${cost_difference:.4f} ({cost_difference_pct:.2f}%)")
            print("="*80)
        
        # Save to database
        usage_log_doc = {
            "user_id": current_user.id if current_user else usage_data.user_id,
            "session_id": usage_data.session_id,
            "language": usage_data.language,
            "level": usage_data.level,
            "topic": usage_data.topic,
            "audio_input_tokens": usage_data.audio_input_tokens,
            "audio_output_tokens": usage_data.audio_output_tokens,
            "text_input_tokens": usage_data.text_input_tokens,
            "text_output_tokens": usage_data.text_output_tokens,
            "cached_input_audio_tokens": usage_data.cached_input_audio_tokens,
            "cached_input_text_tokens": usage_data.cached_input_text_tokens,
            "total_tokens": usage_data.total_tokens,
            "session_start": usage_data.session_start,
            "session_end": usage_data.session_end,
            "session_duration_seconds": usage_data.session_duration_seconds,
            "total_cost": total_cost,
            "model": usage_data.model,
            "logged_at": datetime.now(timezone.utc).isoformat(),
            # 🔥 NEW: Add organization cost fields
            "start_time": usage_data.start_time,  # Unix timestamp
            "end_time": usage_data.end_time,      # Unix timestamp
            "organization_cost": organization_cost,  # Actual cost from OpenAI API
            "organization_cost_data": organization_cost_data  # Full response data
        }
        
        result = await usage_logs_collection.insert_one(usage_log_doc)
        
        print(f"✅ [USAGE_LOG] Saved to database with ID: {result.inserted_id}")
        
        return {
            "success": True,
            "total_cost": total_cost,
            "log_id": str(result.inserted_id)
        }
        
    except Exception as e:
        print(f"❌ [USAGE_LOG] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging usage: {str(e)}")

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

# Sentence Analysis Feedback Models
class SentenceAnalysisFeedback(BaseModel):
    session_id: str
    feedback_type: str  # "analysis_rejection", "stuck_state", "quality_rating"
    sentence_text: str
    language: str
    level: str
    analysis_decision: Dict[str, Any]
    user_rating: Optional[int] = None  # 1-5 stars
    user_comment: Optional[str] = None
    expected_outcome: Optional[str] = None
    session_duration: Optional[int] = None
    retry_count: Optional[int] = None
    conversation_context: Optional[List[str]] = None

# Add endpoint for sentence analysis feedback
@app.post("/api/feedback/sentence-analysis")
async def submit_sentence_analysis_feedback(
    request: Request,
    feedback: SentenceAnalysisFeedback,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """Store user feedback about sentence analysis decisions"""
    try:
        from database import database
        from datetime import datetime, timezone
        
        # Create feedback collection if it doesn't exist
        feedback_collection = database.sentence_analysis_feedback
        
        # Build feedback document
        feedback_doc = {
            "user_id": ObjectId(current_user.id) if current_user else None,
            "session_id": feedback.session_id,
            "feedback_type": feedback.feedback_type,
            "sentence_text": feedback.sentence_text,
            "language": feedback.language,
            "level": feedback.level,
            "analysis_decision": feedback.analysis_decision,
            "user_rating": feedback.user_rating,
            "user_comment": feedback.user_comment,
            "expected_outcome": feedback.expected_outcome,
            "timestamp": datetime.now(timezone.utc),
            "ip_address": request.client.host if hasattr(request, 'client') else None,
            "user_agent": request.headers.get("user-agent"),
            "session_duration": feedback.session_duration,
            "retry_count": feedback.retry_count,
            "conversation_context": feedback.conversation_context,
            "resolved": False  # Will be updated when issues are addressed
        }
        
        # Insert feedback document
        result = await feedback_collection.insert_one(feedback_doc)
        
        print(f"✅ [FEEDBACK] Stored feedback: {feedback.feedback_type} for sentence: '{feedback.sentence_text[:30]}...'")
        
        return {
            "success": True,
            "feedback_id": str(result.inserted_id),
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        print(f"❌ [FEEDBACK] Error storing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {str(e)}")

# Add semantic VAD monitoring endpoint
@app.get("/api/realtime/semantic-feedback")
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
                for feedback in recent_feedback[:20]  # Return only the 20 most recent
            ]
        }
        
    except Exception as e:
        print(f"❌ Error getting semantic feedback monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting semantic feedback monitoring: {str(e)}")

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
async def assess_speaking(request: SpeakingAssessmentRequest, current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)):
    try:
        # 🔥 CRITICAL FIX: Check assessment limits BEFORE processing the assessment
        if current_user:
            try:
                print(f"[ASSESSMENT_LIMIT_CHECK] 🔍 Checking assessment limits for user {current_user.id}")
                
                from subscription_service import SubscriptionService
                can_access, access_message = await SubscriptionService.can_access_feature(current_user.id, "assessment")
                
                if not can_access:
                    print(f"[ASSESSMENT_LIMIT_CHECK] ❌ Assessment blocked: {access_message}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=access_message
                    )
                
                print(f"[ASSESSMENT_LIMIT_CHECK] ✅ Assessment limit check passed")
                
            except HTTPException:
                # Re-raise HTTP exceptions (limit exceeded)
                raise
            except Exception as limit_error:
                print(f"[ASSESSMENT_LIMIT_CHECK] ❌ Error checking limits: {str(limit_error)}")
                # Continue with assessment if limit check fails (don't block user)
                pass
        
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
        
        # 🔥 CRITICAL FIX: Track assessment usage AND save assessment data for authenticated users
        # NOTE: We already checked limits above, so this should succeed
        if current_user:
            try:
                print(f"[ASSESSMENT_TRACKING] Tracking assessment usage for user {current_user.id}")
                
                # Import the subscription service to track usage
                from subscription_service import SubscriptionService
                from models import UsageTrackingRequest
                from database import users_collection
                from bson import ObjectId
                
                # Create usage tracking request
                usage_request = UsageTrackingRequest(
                    user_id=current_user.id,
                    usage_type="assessment",
                    duration_minutes=None  # Assessments don't have duration tracking
                )
                
                # Track the usage
                success = await SubscriptionService.track_usage(usage_request)
                if success:
                    print(f"[ASSESSMENT_TRACKING] ✅ Successfully tracked assessment usage for user {current_user.id}")
                else:
                    print(f"[ASSESSMENT_TRACKING] ⚠️ Usage tracking returned false for user {current_user.id}")
                
                # 🔥 CRITICAL FIX 2: Save assessment data to user record for learning plan creation
                try:
                    print(f"[ASSESSMENT_TRACKING] Saving assessment data to user record")
                    
                    result = await users_collection.update_one(
                        {"_id": ObjectId(current_user.id)},
                        {"$set": {"last_assessment_data": assessment}}
                    )
                    
                    if result.modified_count > 0:
                        print(f"[ASSESSMENT_TRACKING] ✅ Assessment data saved to user record")
                    else:
                        print(f"[ASSESSMENT_TRACKING] ⚠️ Failed to save assessment data to user record")
                        
                except Exception as save_error:
                    print(f"[ASSESSMENT_TRACKING] ❌ Error saving assessment data: {str(save_error)}")
                    
            except Exception as tracking_error:
                print(f"[ASSESSMENT_TRACKING] ❌ Error tracking assessment usage: {str(tracking_error)}")
                # Don't fail the assessment if usage tracking fails
                pass
        else:
            print(f"[ASSESSMENT_TRACKING] ℹ️ No authenticated user - skipping usage tracking")
        
        print(f"Successfully analyzed speaking proficiency")
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

# Add background sentence analysis endpoints
@app.post("/api/sentence/evaluate", response_model=SentenceEvaluationResponse)
async def evaluate_sentence_for_analysis(request: SentenceEvaluationRequest):
    """
    Evaluate whether a sentence is substantial enough for analysis.
    This endpoint is used by the frontend to determine if background analysis should be triggered.
    """
    try:
        print(f"🔍 [EVALUATION] Evaluating sentence: '{request.text}'")
        
        evaluation = await evaluate_sentence_worthiness(
            text=request.text,
            language=request.language,
            level=request.level,
            conversation_context=request.conversation_context
        )
        
        print(f"✅ [EVALUATION] Result: {evaluation['should_analyze']} - {evaluation['reason']}")
        
        return SentenceEvaluationResponse(
            should_analyze=evaluation["should_analyze"],
            reason=evaluation["reason"],
            confidence=evaluation["confidence"]
        )
        
    except Exception as e:
        print(f"❌ [EVALUATION] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating sentence: {str(e)}")

@app.post("/api/sentence/background-analyze", response_model=BackgroundAnalysisResponse)
async def perform_background_sentence_analysis(request: BackgroundAnalysisRequest):
    """
    Perform background sentence analysis without interrupting the conversation.
    This endpoint analyzes the sentence and returns detailed assessment results.
    """
    try:
        print(f"🔬 [BACKGROUND_ANALYSIS] Analyzing sentence: '{request.text}'")
        
        analysis = await perform_background_analysis(
            text=request.text,
            language=request.language,
            level=request.level,
            exercise_type=request.exercise_type,
            conversation_context=request.conversation_context
        )
        
        print(f"✅ [BACKGROUND_ANALYSIS] Analysis completed for: '{request.text}'")
        
        return BackgroundAnalysisResponse(
            analysis_id=analysis["analysis_id"],
            recognized_text=analysis["recognized_text"],
            grammatical_score=analysis["grammatical_score"],
            vocabulary_score=analysis["vocabulary_score"],
            complexity_score=analysis["complexity_score"],
            appropriateness_score=analysis["appropriateness_score"],
            overall_score=analysis["overall_score"],
            grammar_issues=analysis["grammar_issues"],
            improvement_suggestions=analysis["improvement_suggestions"],
            corrected_text=analysis.get("corrected_text"),
            level_appropriate_alternatives=analysis.get("level_appropriate_alternatives"),
            timestamp=analysis["timestamp"]
        )
        
    except Exception as e:
        print(f"❌ [BACKGROUND_ANALYSIS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing background analysis: {str(e)}")

@app.post("/api/sentence/process-background")
async def process_sentence_background(request: BackgroundAnalysisRequest):
    """
    Complete background sentence processing pipeline.
    Evaluates if sentence should be analyzed, and if so, performs the analysis.
    Returns None if sentence doesn't warrant analysis, otherwise returns analysis results.
    """
    try:
        print(f"🔄 [BACKGROUND_PROCESS] Processing sentence: '{request.text}'")
        
        result = await process_sentence_for_background_analysis(
            text=request.text,
            language=request.language,
            level=request.level,
            conversation_context=request.conversation_context
        )
        
        if not result or not result.get("analyzed"):
            reason = result.get("reason", "Sentence not substantial enough for analysis") if result else "Sentence not substantial enough for analysis"
            print(f"⏭️ [BACKGROUND_PROCESS] Sentence skipped - {reason}")
            return {"analyzed": False, "reason": reason}
        
        # Extract analysis data from the result
        analysis_data = result.get("analysis", {})
        if not analysis_data:
            print(f"❌ [BACKGROUND_PROCESS] No analysis data in result")
            return {"analyzed": False, "reason": "No analysis data available"}
        
        analysis_id = analysis_data.get("analysis_id", "unknown")
        print(f"✅ [BACKGROUND_PROCESS] Analysis completed with ID: {analysis_id}")
        
        return {
            "analyzed": True,
            "analysis": BackgroundAnalysisResponse(
                analysis_id=analysis_id,
                recognized_text=analysis_data.get("recognized_text", request.text),
                grammatical_score=analysis_data.get("grammatical_score", 50.0),
                vocabulary_score=analysis_data.get("vocabulary_score", 50.0),
                complexity_score=analysis_data.get("complexity_score", 50.0),
                appropriateness_score=analysis_data.get("appropriateness_score", 50.0),
                overall_score=analysis_data.get("overall_score", 50.0),
                grammar_issues=analysis_data.get("grammar_issues", []),
                improvement_suggestions=analysis_data.get("improvement_suggestions", []),
                corrected_text=analysis_data.get("corrected_text"),
                level_appropriate_alternatives=analysis_data.get("level_appropriate_alternatives"),
                timestamp=analysis_data.get("timestamp", "")
            ),
            "evaluation": result.get("evaluation", {})
        }
        
    except Exception as e:
        print(f"❌ [BACKGROUND_PROCESS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing sentence: {str(e)}")

# Add transcription model monitoring endpoint
@app.get("/api/transcription/status")
async def get_transcription_status():
    """
    Monitor transcription model configuration and usage
    """
    try:
        use_gpt4o = os.getenv("USE_GPT4O_TRANSCRIBE", "true").lower() == "true"
        
        # Get current model configuration
        realtime_model = "gpt-4o-transcribe" if use_gpt4o else "whisper-1"
        sentence_assessment_model = "gpt-4o-transcribe (with whisper-1 fallback)" if use_gpt4o else "whisper-1 only"
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "USE_GPT4O_TRANSCRIBE": use_gpt4o,
                "environment_variable": os.getenv("USE_GPT4O_TRANSCRIBE", "not_set"),
                "realtime_api_model": realtime_model,
                "sentence_assessment_model": sentence_assessment_model
            },
            "models": {
                "primary": "gpt-4o-transcribe" if use_gpt4o else "whisper-1",
                "fallback": "whisper-1" if use_gpt4o else "none",
                "realtime_api": realtime_model,
                "sentence_assessment": "gpt-4o-transcribe" if use_gpt4o else "whisper-1"
            },
            "features": {
                "enhanced_multilingual_accuracy": use_gpt4o,
                "advanced_prompting": use_gpt4o,
                "streaming_support": use_gpt4o,
                "automatic_fallback": use_gpt4o
            },
            "supported_languages": [
                "English", "Dutch", "Spanish", "German", "French", "Portuguese"
            ],
            "instructions": {
                "enable_gpt4o": "Set USE_GPT4O_TRANSCRIBE=true in environment variables",
                "disable_gpt4o": "Set USE_GPT4O_TRANSCRIBE=false in environment variables",
                "restart_required": "Changes require application restart to take effect"
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting transcription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transcription status: {str(e)}")

# Add endpoint to get current model configuration
@app.get("/api/realtime/model-config")
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
        print(f"❌ Error getting model config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model config: {str(e)}")

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
            "model": "gpt-realtime-mini",
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

# Frontend is served by Next.js server (npm start), not by FastAPI
# Backend only handles API routes
print("="*80)
print("🔧 FRONTEND SERVING MODE")
print("="*80)
print("✅ Using Next.js server mode (not static export)")
print("✅ Frontend will be served by Next.js on port 3001")
print("✅ Backend API only handles /api/* routes")
print("="*80)

# Note: We don't mount static files because Next.js server handles the frontend
# The following code is kept for reference but not executed:
if False:  # Disabled - Next.js server handles frontend now
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
    
    @app.get("/responsible-ai")
    async def serve_responsible_ai():
        responsible_ai_file = frontend_build_path / "responsible-ai.html"
        if responsible_ai_file.exists():
            return FileResponse(responsible_ai_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Responsible AI page not found")
    
    # Institution routes (App Router pages)
    @app.get("/institution/signup")
    async def serve_institution_signup():
        signup_file = frontend_build_path / "institution" / "signup.html"
        if signup_file.exists():
            return FileResponse(signup_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Institution signup page not found")
    
    @app.get("/institution/login")
    async def serve_institution_login():
        login_file = frontend_build_path / "institution" / "login.html"
        if login_file.exists():
            return FileResponse(login_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Institution login page not found")
    
    @app.get("/institution/signup-success")
    async def serve_institution_signup_success():
        success_file = frontend_build_path / "institution" / "signup-success.html"
        if success_file.exists():
            return FileResponse(success_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="Institution signup success page not found")
    
    print("✅ Added institution route handlers for App Router pages")
    
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
    
    # Note: StaticFiles mounting removed - using Next.js server mode instead

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
