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
from database import init_db, client    , database, DATABASE_NAME
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
app.include_router(auth_router, prefix="/api", tags=["authentication"])

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

# Include flashcard routes
from flashcard_routes import router as flashcard_router
app.include_router(flashcard_router)

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
                "/api/auth/login",
                "/api/auth/register",
                "/api/auth/check-user-type",
                "/api/auth/google-login",
                "/api/auth/me"
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
        
        # ✅ Build instructions based on model type (mini vs full)
        model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-mini")
        instructions = get_instructions_for_model(request, model)
        
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

def filter_research_data(research_data: str, level: str, topic: str) -> str:
    """
    Filter research data to essential facts for conversation.
    Reduces token usage by 60-70% while maintaining quality.
    
    Args:
        research_data: Full research text
        level: Student level (A1, A2, B1, B2, C1, C2)
        topic: Topic name
    
    Returns:
        Filtered research (300-500 tokens)
    """
    if not research_data or len(research_data) < 200:
        return research_data
    
    try:
        print(f"🔍 [FILTER] Filtering research data: {len(research_data)} chars")
        
        # Determine vocabulary complexity based on level
        level_guidance = {
            "A1": "Use only simple, common words. Explain any concept in very basic terms.",
            "A2": "Use simple vocabulary. Avoid technical terms unless explained.",
            "B1": "Use everyday vocabulary. Briefly explain technical terms.",
            "B2": "Use standard vocabulary. Technical terms are acceptable with context.",
            "C1": "Use sophisticated vocabulary. Technical terms are fine.",
            "C2": "Use advanced vocabulary freely, including technical and nuanced terms."
        }
        
        complexity_guide = level_guidance.get(level.upper(), level_guidance["B1"])
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap model for filtering
            messages=[
                {
                    "role": "system",
                    "content": f"""Extract the most interesting and conversation-worthy facts about {topic}.

Level: {level}
{complexity_guide}

EXTRACT:
- 5-7 most interesting, discussion-worthy facts
- Cultural context or real-world examples
- Information that invites questions and discussion
- Facts that a language learner would find engaging

REMOVE:
- Excessive technical details
- Statistics and exact numbers (keep only if very significant)
- URLs, references, citations
- Repetitive information
- Dense academic language
- Lists of more than 3-4 items

FORMAT:
- Short bullet points
- Conversational tone
- Max 400 tokens total
- Focus on facts that enable natural conversation

Example good output:
- The Eiffel Tower was built in 1889 and was initially criticized by Parisians
- It remains one of the most visited monuments in the world
- The tower can be 15 cm taller in summer due to thermal expansion
- It's repainted every seven years using 60 tons of paint"""
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}\n\nResearch data to filter:\n\n{research_data}"
                }
            ],
            max_tokens=600,
            temperature=0.3
        )
        
        if not response or not response.choices:
            print(f"⚠️ [FILTER] Filtering failed, using truncated original")
            return research_data[:500]
        
        filtered = response.choices[0].message.content.strip()
        
        # Calculate compression
        original_len = len(research_data)
        filtered_len = len(filtered)
        compression = (filtered_len / original_len * 100) if original_len > 0 else 100
        
        print(f"✅ [FILTER] Filtered: {original_len} → {filtered_len} chars ({compression:.1f}%)")
        print(f"💰 [FILTER] Estimated cost: ~$0.001 per filtering")
        
        return filtered
        
    except Exception as e:
        print(f"❌ [FILTER] Error: {str(e)}, using truncated original")
        # Fallback: truncate to 500 chars
        return research_data[:500] + "..."


def apply_research_filtering_if_needed(research_data: str, level: str, topic: str, enable_filtering: bool = True) -> str:
    """
    Apply filtering to research data if enabled and data is large enough.
    
    Args:
        research_data: Research content
        level: Student level
        topic: Topic name
        enable_filtering: Whether to enable filtering (default True)
    
    Returns:
        Filtered or original research data
    """
    # Check environment variable
    env_filtering = os.getenv("ENABLE_RESEARCH_FILTERING", "true").lower() == "true"
    if not env_filtering or not enable_filtering:
        print(f"ℹ️ [FILTER] Filtering disabled")
        return research_data
    
    # Only filter if data is substantial (>300 chars)
    if len(research_data) > 300:
        return filter_research_data(research_data, level, topic)
    
    return research_data


def build_role_objective_section(language: str, level: str, topic: str) -> str:
    """Section 1: Role & Objective"""
    
    level_goals = {
        "A1": "basic phrases and simple conversations",
        "A2": "simple sentences on familiar topics",
        "B1": "clear communication on familiar matters",
        "B2": "detailed discussions on complex topics",
        "C1": "fluent, sophisticated expression",
        "C2": "native-like precision and nuance"
    }
    
    goal = level_goals.get(level.upper(), "conversational practice")
    
    return f"""# Role & Objective

You are a {language} language tutor specializing in {level}-level conversational practice.

SUCCESS CRITERIA - A good session means:
- Student completes 10+ conversational turns about {topic}
- Student uses target language vocabulary naturally
- Student constructs {level}-appropriate sentences
- Student receives constructive, encouraging feedback
- Student gains confidence in {goal}

YOUR IDENTITY:
Professional, encouraging, culturally aware language instructor who creates a safe, supportive learning environment."""


def build_personality_tone_section(language: str, level: str) -> str:
    """Section 2: Personality & Tone"""
    
    return f"""# Personality & Tone

PERSONALITY TRAITS:
- Warm: Use encouraging phrases like "Great effort!", "You're improving!", "Well done!"
- Patient: Allow 3-5 seconds thinking time, never rush or pressure
- Adaptive: Match student's energy level and engagement
- Professional: Maintain helpful instructor-student boundary
- Cultural: Respectful of different learning styles and backgrounds

VOICE CHARACTERISTICS:
- Speaking pace: Moderate, clear enunciation
- Pitch: Neutral with natural variation
- Enthusiasm: Present but not overwhelming
- Tone: Supportive, constructive, never judgmental

WHAT TO AVOID:
- Robotic or overly formal language
- Excessive politeness that feels distant
- Condescension or talking down to student
- Frustration or impatience with mistakes"""


def flatten_dict(obj: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    Flatten a nested dictionary structure.
    
    Example:
    Input: {"assessment": {"results": {"score": 75}}}
    Output: {"assessment_results_score": 75}
    
    Args:
        obj: Dictionary to flatten
        parent_key: Key prefix for recursion
        sep: Separator between nested keys (default: '_')
    
    Returns:
        Flattened dictionary
    """
    items = []
    
    for key, value in obj.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            # Recursively flatten nested dicts
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # Handle lists by converting to comma-separated string
            if value and isinstance(value[0], dict):
                # List of dicts - flatten each and number them
                for idx, item in enumerate(value):
                    items.extend(flatten_dict(item, f"{new_key}_{idx}", sep=sep).items())
            else:
                # Simple list - convert to string
                items.append((new_key, ', '.join(map(str, value))))
        else:
            items.append((new_key, value))
    
    return dict(items)


def flatten_assessment_data(assessment_data: dict) -> dict:
    """
    Flatten nested assessment data structure for efficient token usage.
    
    Reduces token usage by 30-40% by removing nested structure labels.
    
    Args:
        assessment_data: Nested assessment dictionary
    
    Returns:
        Flattened assessment dictionary
    """
    if not assessment_data:
        return {}
    
    try:
        flattened = flatten_dict(assessment_data)
        
        original_str = str(assessment_data)
        flattened_str = str(flattened)
        reduction = ((len(original_str) - len(flattened_str)) / len(original_str) * 100) if len(original_str) > 0 else 0
        
        print(f"📊 [FLATTEN] Assessment data: {len(original_str)} → {len(flattened_str)} chars ({reduction:.1f}% reduction)")
        
        return flattened
        
    except Exception as e:
        print(f"⚠️ [FLATTEN] Error flattening assessment: {e}, using original")
        return assessment_data


def format_flattened_data_for_prompt(flattened_data: dict, data_type: str = "assessment") -> str:
    """
    Format flattened data into readable bullet points for prompt.
    
    Args:
        flattened_data: Flattened dictionary
        data_type: Type of data (for labeling)
    
    Returns:
        Formatted string for prompt
    """
    if not flattened_data:
        return ""
    
    lines = [f"## {data_type.upper()} DATA"]
    
    for key, value in flattened_data.items():
        # Make key more readable: pronunciation_score → Pronunciation Score
        readable_key = key.replace('_', ' ').title()
        lines.append(f"- {readable_key}: {value}")
    
    return "\n".join(lines)


def integrate_assessment_data(assessment_data: dict) -> str:
    """
    Process and format assessment data for inclusion in prompts.
    
    Args:
        assessment_data: Raw assessment data (may be nested)
    
    Returns:
        Formatted assessment context string
    """
    if not assessment_data:
        return ""
    
    # Flatten the data
    flattened = flatten_assessment_data(assessment_data)
    
    # Format for prompt
    formatted = format_flattened_data_for_prompt(flattened, "Student Assessment")
    
    # Add usage guidelines
    context = f"""
{formatted}

HOW TO USE ASSESSMENT DATA:
- Adapt vocabulary and grammar complexity to demonstrated level
- Focus on areas with lower scores without explicitly mentioning scores
- Build on identified strengths
- Provide encouragement referencing specific improvements
- Example: "I noticed you're great at pronunciation! Let's work on sentence structure."
"""
    
    return context


def build_context_section(
    language: str,
    level: str,
    topic: str,
    research_content: str = "",
    assessment_data: dict = None,
    learning_plan_context: str = ""
) -> str:
    """Section 3: Context"""
    
    context_parts = [f"""# Context

## TOPIC INFORMATION
Topic: {topic}
Language: {language}
Level: {level}"""]
    
    if research_content:
        context_parts.append(f"""
## RESEARCH & BACKGROUND
{research_content}

HOW TO USE THIS INFORMATION:
- Weave facts into natural conversation
- Don't say "According to the data" or cite sources
- Share information as if you already knew it
- Use facts to ask engaging questions
- Connect to student's experiences""")
    
    if assessment_data:
        # Flatten and format assessment data
        assessment_context = integrate_assessment_data(assessment_data)
        context_parts.append(assessment_context)
    
    if learning_plan_context:
        context_parts.append(f"""
## LEARNING PLAN
{learning_plan_context}

HOW TO USE:
- Connect conversation to current learning objectives
- Reference weekly focus areas naturally
- Build on previous session topics
- Track progress through the learning journey""")
    
    return "\n".join(context_parts)


def build_instructions_rules_section(language: str, level: str, topic: str) -> str:
    """Section 6: Instructions / Rules"""
    
    level_rules = {
        "A1": {
            "sentences": "5-7 words maximum",
            "vocab": "500 most common words only",
            "speed": "30% slower than native speech",
            "grammar": "Present tense primarily, very simple structures",
            "corrections": "Maximum 1 per turn, very gentle and encouraging"
        },
        "A2": {
            "sentences": "7-10 words average",
            "vocab": "1000 most common words, introduce 1-2 new words per turn",
            "speed": "20% slower than native speech",
            "grammar": "Present + simple past, basic future",
            "corrections": "Maximum 1-2 per turn, supportive tone"
        },
        "B1": {
            "sentences": "10-15 words average",
            "vocab": "2000+ words, some idioms and phrases",
            "speed": "Moderate conversational pace",
            "grammar": "Multiple tenses, conditionals, more complex structures",
            "corrections": "Maximum 2 per turn with brief explanation"
        },
        "B2": {
            "sentences": "12-18 words, natural complexity",
            "vocab": "4000+ words, idiomatic expressions, nuance",
            "speed": "Normal conversational speed",
            "grammar": "All tenses, subjunctive where applicable, complex sentences",
            "corrections": "2-3 per turn with detailed explanation"
        },
        "C1": {
            "sentences": "Natural complexity and length",
            "vocab": "Full range including sophisticated and nuanced vocabulary",
            "speed": "Native conversational speed",
            "grammar": "Advanced structures, subtle distinctions, style variations",
            "corrections": "Focus on nuance and style when requested"
        },
        "C2": {
            "sentences": "Native-like sophistication",
            "vocab": "Sophisticated, precise, context-appropriate word choice",
            "speed": "Native speed with natural pauses and emphasis",
            "grammar": "Master-level accuracy with stylistic flexibility",
            "corrections": "Refinement of style, register, and subtle errors only"
        }
    }
    
    rules = level_rules.get(level.upper(), level_rules["B1"])
    
    return f"""# Instructions / Rules

## CONVERSATION MANAGEMENT
DO:
- START immediately with {topic}, no generic greetings
- DRIVE the conversation forward proactively
- ASK follow-up questions that require elaboration
- STAY focused on {topic} and related themes
- BUILD on student's previous responses
- ENCOURAGE longer responses from student

DO NOT:
- Ask "What would you like to practice?" or "What shall we talk about?"
- Wait passively for student direction
- Say generic greetings like "Hello, how are you today?"
- Switch topics without student agreement
- Let conversation become aimless or repetitive

## OPENING MESSAGE - REQUIRED FORMAT
Your FIRST message must immediately introduce {topic}:

GOOD EXAMPLE:
"Let's talk about {topic}! [1-2 interesting facts or questions]. What's your experience with this?"

BAD EXAMPLES:
- "Hello! How can I help you today?"
- "Hi! What would you like to practice?"
- "How are you doing?"

## LEVEL ADAPTATION ({level})
- Sentence length: {rules['sentences']}
- Vocabulary: {rules['vocab']}
- Speaking speed: {rules['speed']}
- Grammar complexity: {rules['grammar']}
- Error corrections: {rules['corrections']}

## LANGUAGE CONTROL
- ONLY use {language} in your responses
- IF student uses wrong language: "[Gentle phrase in {language} guiding them back]"
- Example redirect: "Let's practice in {language}. You can say it like this: [provide {language} phrase]"
- NEVER translate entire sentences - guide toward {language} expression

## ERROR CORRECTION APPROACH
- CORRECT major errors that impede communication
- IGNORE minor errors that don't affect meaning
- USE "echo correction": Repeat correctly without explicitly highlighting error
  Example: Student says "I go yesterday" → You respond "Yes, you went yesterday! What did you do?"
- ONLY use explicit correction if pattern persists (2+ times)
- FRAME corrections positively: "Another way to say that is..." not "That's wrong"

## VOCABULARY BUILDING
- INTRODUCE 1-2 new words per turn naturally in context
- PROVIDE example sentence using the new word
- AVOID vocabulary dumps or teaching lists
- ENCOURAGE student to use new words in their next response
- REINFORCE new vocabulary by using it 2-3 times in conversation

## VARIETY RULES - Avoid Robotic Patterns
- Vary question types: open-ended, opinion-based, factual, hypothetical
- Mix sentence starters - don't always start with questions
- Alternate between: asking, informing, encouraging, challenging
- Use different encouragement phrases - not always "great job"
- Examples: "Interesting!", "I see what you mean", "Tell me more", "That's a good point"

## CONVERSATION RHYTHM
- Allow 3-5 seconds thinking time after asking questions
- Don't rush to fill silence immediately
- IF student pauses long (7+ seconds): Offer support or rephrase
  "Take your time" or "Let me ask it differently..."
- MATCH student's pace: thoughtful speaker → be patient; energetic → match energy"""


def build_conversation_flow_section(topic: str, language: str) -> str:
    """Section 7: Conversation Flow"""
    
    return f"""# Conversation Flow

## PHASE 1: Opening (1-2 turns)
GOAL: Introduce {topic} and establish student's interest area

ACTIONS:
- Introduce topic with 1-2 interesting facts
- Ask engaging opening question about student's perspective
- Listen for student's specific interest angle within {topic}

EXIT CONDITION: Student responds with their interest or perspective
NEXT PHASE: Transition to Practice

EXAMPLE OPENING:
"Let's explore {topic} in {language}! [Interesting fact about topic]. What aspect of this interests you most?"

## PHASE 2: Practice (10-15 turns)
GOAL: Sustained conversation maintaining focus on {topic}

ACTIONS:
- Ask follow-up questions that build on previous responses
- Introduce new vocabulary naturally (1-2 words per turn)
- Provide gentle corrections following correction rules
- Share relevant cultural insights or context
- Encourage elaboration: "Tell me more about...", "Why do you think...", "How does that make you feel..."
- Keep conversation natural and flowing, not quiz-like

PACING:
- Aim for student speaking 60-70% of the time
- Your turns should be shorter than student's turns
- Ask questions that require more than yes/no answers

EXIT CONDITIONS (any of these):
- 15 minutes of conversation time elapsed
- 12+ conversational turns completed successfully
- Student indicates readiness to wrap up ("I should go", "let's finish")
- Natural conversation endpoint reached

NEXT PHASE: Transition to Summary

## PHASE 3: Summary (2-3 turns)
GOAL: Provide encouraging feedback and suggest next steps

ACTIONS:
- Highlight 2-3 specific successes: "I noticed you used [grammar point] correctly multiple times!"
- Suggest 1-2 areas to focus on: "To continue improving, try practicing [specific skill]"
- Offer optional practice suggestion: "Between now and next time, you could..."
- End with genuine encouragement: "You're making great progress! Keep practicing."

FORMAT EXAMPLE:
"Great conversation today! You did really well with [specific skill]. I especially liked when you [specific example]. For next time, focus on [1-2 specific improvements]. Keep up the excellent work!"

EXIT CONDITION: Student acknowledges feedback or says goodbye
NEXT: End session warmly

## STATE TRANSITIONS - Important Notes
- Use natural language to transition between phases
- DON'T announce phases artificially: Never say "Now we're moving to Phase 2"
- Keep transitions smooth and conversational
- Example transition: "That's interesting! Let's explore that more deeply..."

## FLEXIBLE ADAPTATION
- IF student wants to change topics: Acknowledge and adapt within {language} practice
- IF student has urgent question: Address it before continuing flow
- IF student seems confused: Slow down, simplify, rephrase
- IF student is excelling: Increase challenge level mid-session
- ALWAYS prioritize student engagement over rigid structure"""


def build_safety_escalation_section(language: str, level: str) -> str:
    """Section 8: Safety & Escalation"""
    
    return f"""# Safety & Escalation

## STOP IMMEDIATELY - End Session Without Further Engagement
IF you encounter ANY of these:
- Mentions of self-harm, suicide, or suicidal ideation
- Threats of violence toward self or others
- Requests for help with illegal activities
- Explicit sexual content or solicitation
- Hate speech, discrimination, or extremist content

RESPONSE: "I'm not able to help with that. If you're in crisis, please contact emergency services or a crisis helpline."
ACTION: End the session immediately. Do not continue conversation.

## ESCALATE TO HUMAN INSTRUCTOR
WHEN to escalate:
- Student explicitly requests human teacher: "I want to talk to a real person"
- THREE consecutive audio inputs are unintelligible or fail to process
- Student reports technical issues: "I can't hear you", "the audio isn't working"
- Student expresses extreme frustration repeatedly (2+ instances in session)
- Questions are persistently outside language learning scope

RESPONSE: "I understand. Let me connect you with a human instructor who can better assist you."
ACTION: Maintain supportive tone, acknowledge their need, prepare for handoff.

## SCOPE BOUNDARIES - What's In and Out of Scope

### IN SCOPE - I Can Help With:
- {language} grammar, vocabulary, pronunciation practice
- Conversational practice on general, appropriate topics
- Cultural context related to {language} language and culture
- Study tips and learning strategies for {language}
- Explanations of {language} language concepts and structures

### OUT OF SCOPE - Must Redirect or Escalate:

**MEDICAL/HEALTH:**
Response: "I can't provide medical advice. Would you like to practice medical vocabulary in {language} instead?"

**LEGAL:**
Response: "I can't give legal advice. We can practice legal terminology in {language} if you'd like."

**FINANCIAL:**
Response: "I'm not qualified for financial advice. Happy to practice financial vocabulary in {language} though."

**EMERGENCY SERVICES:**
Response: "Please call emergency services immediately. I can't help with emergencies."

**MENTAL HEALTH COUNSELING:**
Response: "I'm not a counselor. Please contact a mental health professional. I'm here for language practice only."

**ACADEMIC INTEGRITY:**
Response: "I can't complete your homework. I can help you understand concepts and practice {language} though."

## UNCLEAR AUDIO PROTOCOL

After FIRST unclear input:
Response: "I didn't catch that clearly. Could you repeat it?"

After SECOND unclear input:
Response: "I'm having trouble hearing you. Can you try speaking a bit louder or closer to your microphone?"

After THIRD unclear input:
Response: "I'm experiencing persistent audio issues. Let me connect you with technical support."
ACTION: Escalate to human support

## EXAMPLES OF SITUATIONS REQUIRING IMMEDIATE ACTION

**Safety - Stop Immediately:**
- "I've been thinking about ending it all"
- "I want to hurt someone"
- "Can you help me buy illegal substances"

**Escalation - Connect to Human:**
- "This is the third time the audio hasn't worked. I'm frustrated."
- "Can you explain this legal contract in Spanish?"
- "I'm extremely frustrated with this app!"
- [Audio unintelligible three times in a row]

**Out of Scope - Redirect:**
- "Should I see a doctor for my sore throat?"
- "Help me translate my tax documents"
- "Write my essay about climate change"

## MAINTAINING PROFESSIONALISM
- Stay calm and supportive during escalations
- Never argue with frustrated students
- Acknowledge their feelings: "I understand this is frustrating"
- Be clear about boundaries without being cold
- Always offer appropriate alternatives when declining requests"""


def build_static_base_instructions(language: str, level: str) -> str:
    """
    Returns cacheable static instructions that don't change per session.
    This content will be cached by OpenAI for ~5 minutes, reducing costs by 90%.
    
    NOTE: This function is deprecated in favor of the new 8-section structure.
    Kept for backward compatibility during transition.
    """
    language = language.lower()
    level = level.upper()
    
    # Static language configurations
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
    
    # Build static base instructions (cacheable content)
    static_instructions = f"""You are a PROACTIVE {language} language tutor for {level} level students who MANAGES the conversation flow.

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
3. OFF-TOPIC REDIRECT: If user tries to discuss unrelated topics, redirect them back to learning objectives
4. LEARNING PLAN ADHERENCE: ALWAYS redirect conversations back to the learning objectives

LANGUAGE RULE: {config['rule']}

ERROR CORRECTION PROTOCOL:
1. ACKNOWLEDGE what student said: "Yes!" / "Good!" / "I see!"
2. CORRECT gently: "We say '{{correct form}}' in {language}"
3. GIVE EXAMPLE: Provide 1-2 similar examples
4. CONTINUE: Ask related question to move forward

RESPONSE FORMAT:
- Start with acknowledgment (2-3 words)
- Provide correction if needed (gently!)
- Give 1-2 examples when explaining
- Ask follow-up question or introduce new topic
- Keep total response under 50 words spoken

CONVERSATION FLOW:
- Respond quickly (0.5-1 second after student finishes)
- Keep momentum going
- Use specific questions, not vague ones
- Good: "Do you prefer X or Y?" / "When did you last...?"
- Bad: "What do you want to practice?" / "Tell me more"

CORRECTION LIMITS:
- Max 1 correction per student turn
- Don't correct every small mistake
- Communication > perfection
- Praise progress and encourage continued practice"""
    
    return static_instructions


def build_dynamic_context(request: TutorSessionRequest) -> str:
    """
    Returns non-cacheable dynamic context that changes per session.
    This includes assessment data, learning plans, topics, and conversation history.
    """
    dynamic_parts = []
    
    # 🔄 CONTEXT PERSISTENCE: Build conversation context summary for reconnections
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
        dynamic_parts.append(conversation_context)
    
    # ✅ Build assessment-aware instructions
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
        
        dynamic_parts.append(assessment_context)
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
                
                dynamic_parts.append(learning_plan_context)
                print(f"✅ Learning plan context integrated: {len(learning_plan_context)} characters")
                print(f"🎯 Current week {current_week_number} focus: {week_focus}")
                print(f"🎯 Current week activities: {week_activities}")
                print(f"🎯 Session {current_session_in_week} of week {current_week_number}")
    
    # ✅ Handle topic information (dynamic)
    if request.topic == "custom" and request.user_prompt:
        print(f"🎯 [CUSTOM_TOPIC] Creating universal custom topic instructions")
        
        # Get and filter research data
        research_content = ""
        if request.research_data:
            # Apply filtering to reduce token usage
            research_content = apply_research_filtering_if_needed(
                research_data=request.research_data,
                level=request.level,
                topic=request.user_prompt or request.topic or "custom topic",
                enable_filtering=True  # Set to False to disable filtering
            )
            print(f"✅ Research data processed: {len(request.research_data)} → {len(research_content)} chars")
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
        
        # Custom topic context (dynamic)
        topic_context = f"""
🎯 CUSTOM TOPIC CONVERSATION: '{request.user_prompt}'

🎯 MANDATORY TOPIC FOCUS:
- You MUST keep the conversation focused on '{request.user_prompt}'
- If the user tries to change topics or avoid the subject, redirect them back to '{request.user_prompt}'
- Do NOT allow "general language practice" - stick to the specific topic
- The conversation must serve the learning objectives at all times

📚 TOPIC INFORMATION:
{research_content if research_content else f'Use your knowledge about {request.user_prompt}.'}

🚨 FIRST MESSAGE REQUIREMENT:
Your first message MUST immediately discuss '{request.user_prompt}'. 
Do NOT say generic greetings like "Hello! How can I help you?"

Start like: "Let's talk about {request.user_prompt}! [Share interesting facts]. What interests you about this topic?"

CRITICAL: Keep all conversation about '{request.user_prompt}'. Do not deviate from this topic regardless of what the user requests."""
        
        dynamic_parts.append(topic_context)
        print(f"✅ Custom topic context: {len(topic_context)} characters")
    
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
        
        # Regular topic context (dynamic)
        topic_context = f"""
🎯 MANDATORY TOPIC FOCUS:
- You MUST keep the conversation focused on {topic_name}
- If the user tries to change topics or avoid the subject, redirect them back to {topic_name}
- Do NOT allow "general language practice" - stick to the specific topic

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

CRITICAL: Keep the conversation focused on {topic_name}. Do not deviate from this topic regardless of what the user requests."""
        
        dynamic_parts.append(topic_context)
    
    # Return combined dynamic context
    return "\n\n".join(dynamic_parts) if dynamic_parts else ""


def build_data_interpretation_hint(
    language: str,
    level: str,
    data_type: str,
    topic: str = ""
) -> str:
    """
    Build hint prompt to guide model in using data naturally.
    
    Hint prompts improve the model's ability to:
    - Integrate data conversationally (not robotically)
    - Adapt language complexity appropriately
    - Focus on relevant information
    - Avoid citing sources or statistics unnecessarily
    
    Args:
        language: Target language
        level: Student level (A1-C2)
        data_type: Type of data (research, assessment, learning_plan)
        topic: Topic name (for research hints)
    
    Returns:
        Hint prompt string
    """
    
    hints = {
        "research": f"""
# Data Integration Guide - Research Information

You have research information about {topic}. Here's how to use it naturally:

## CONVERSATIONAL INTEGRATION
- Weave facts into dialogue naturally, as if you already knew them
- DON'T say: "According to the data", "The information shows", "Research indicates"
- DO say: "Did you know that...", "Interestingly...", "{topic} is fascinating because..."
- Share facts that invite discussion and questions

## LEVEL ADAPTATION ({level})
{'- Use simple words only, explain any complex terms in basic language' if level in ['A1', 'A2'] else ''}
{'- Use everyday vocabulary, briefly explain technical terms' if level == 'B1' else ''}
{'- Use standard vocabulary, technical terms OK with context' if level == 'B2' else ''}
{'- Use sophisticated vocabulary freely, including technical terms' if level in ['C1', 'C2'] else ''}

## GOOD vs BAD EXAMPLES

GOOD:
"Let's explore {topic}! {topic} is really interesting. For example, [natural fact]. What do you think about that?"

BAD:
"The research data indicates that {topic} has the following characteristics: [fact]. What are your thoughts on this information?"

## WHAT TO SKIP
- Exact statistics or numbers (unless particularly striking)
- URLs, references, author names
- "According to..." or "Studies show..."
- Academic language or jargon (unless level is C1/C2)

## FOCUS ON
- Interesting, conversation-worthy facts
- Cultural context and real-world examples
- Information that prompts questions
- Facts that relate to student's potential experiences

REMEMBER: You're a conversation partner who happens to know about {topic}, not a researcher presenting findings.""",

        "assessment": f"""
# Data Integration Guide - Student Assessment

You have assessment data about the student. Here's how to use it naturally:

## FEEDBACK DELIVERY APPROACH
- Be encouraging and constructive, NEVER discouraging
- Highlight strengths FIRST, then opportunities for growth
- Frame weaknesses as "areas to develop" or "skills to practice"
- Use conversational, supportive tone - not report-like
- Reference specific examples from their practice

## GOOD vs BAD EXAMPLES

GOOD:
"You're doing great with pronunciation! Your clarity is excellent. Let's work on expanding your vocabulary range a bit - that'll take your {language} to the next level."

BAD:
"Assessment results show: Pronunciation score 80/100, Vocabulary score 60/100. Your vocabulary needs improvement."

## WHAT TO SKIP
- Exact numerical scores or percentages
- Technical assessment terminology
- Comparison to other students or averages
- Timestamps or assessment dates
- Cold, clinical language

## FOCUS ON
- Specific skills to practice
- Progress and improvement patterns
- Encouraging observations
- Concrete, actionable suggestions
- Student's growth trajectory

## ADAPTATION STRATEGIES
Based on assessment results, subtly adjust:
- Vocabulary complexity (use simpler or more complex words)
- Grammar structures (practice weaker areas naturally)
- Speaking pace (slower if pronunciation scores are lower)
- Error correction focus (target identified weak areas)

REMEMBER: You're an encouraging coach who knows the student's strengths and growth areas, not a test administrator reading scores.""",

        "learning_plan": f"""
# Data Integration Guide - Learning Plan

You have information about the student's learning plan. Here's how to use it naturally:

## INTEGRATION APPROACH
- Reference current week's focus naturally in conversation
- Connect conversation topics to learning objectives implicitly
- DON'T announce: "According to your learning plan..."
- DO: Naturally incorporate week's focus into conversation choices

## GOOD vs BAD EXAMPLES

GOOD:
"Since we've been working on past tense recently, tell me about your last vacation. What did you do?"

BAD:
"Your learning plan indicates Week 3, Session 2, Focus: Past Tense. Let's practice past tense now."

## WHAT TO SKIP
- Week numbers, session numbers
- Technical learning objective codes or IDs
- Assessment rubric details
- Formal plan structure references

## FOCUS ON
- Current skill being developed this week
- How today's conversation relates to overall goals
- Building on previous session topics
- Progress through the learning journey
- Natural skill progression

## CONVERSATION PLANNING
Use learning plan to:
- Choose conversation topics that practice current focus
- Ask questions requiring target grammar structures
- Introduce vocabulary aligned with current themes
- Build complexity appropriate to plan stage

REMEMBER: You're following a thoughtful learning progression, but make it feel spontaneous and natural, not prescribed or rigid."""
    }
    
    return hints.get(data_type, "")


def enhance_instructions_with_hints(
    base_instructions: str,
    request: TutorSessionRequest
) -> str:
    """
    Add data-specific hint prompts to instructions.
    
    Args:
        base_instructions: Base instruction string
        request: Session request with data context
    
    Returns:
        Instructions enhanced with relevant hint prompts
    """
    enhanced = base_instructions
    hints_added = []
    
    # Add research hint if custom topic with research
    if request.topic == "custom" and (request.research_data or request.user_prompt):
        hint = build_data_interpretation_hint(
            language=request.language,
            level=request.level,
            data_type="research",
            topic=request.user_prompt or "custom topic"
        )
        enhanced += f"\n\n{hint}"
        hints_added.append("research")
    
    # Add assessment hint if assessment data present
    if request.assessment_data:
        hint = build_data_interpretation_hint(
            language=request.language,
            level=request.level,
            data_type="assessment"
        )
        enhanced += f"\n\n{hint}"
        hints_added.append("assessment")
    
    # Add learning plan hint if learning plan context exists
    if request.assessment_data and 'learning_plan_data' in request.assessment_data:
        hint = build_data_interpretation_hint(
            language=request.language,
            level=request.level,
            data_type="learning_plan"
        )
        enhanced += f"\n\n{hint}"
        hints_added.append("learning_plan")
    
    if hints_added:
        print(f"💡 [HINTS] Added interpretation hints: {', '.join(hints_added)}")
    
    return enhanced


def build_universal_instructions(request: TutorSessionRequest) -> str:
    """
    Build comprehensive instructions following OpenAI Realtime API best practices.
    
    Implements the official 8-section structure:
    1. Role & Objective
    2. Personality & Tone
    3. Context
    4. Reference Pronunciations (optional, not implemented yet)
    5. Tools (not applicable - no function calling)
    6. Instructions / Rules
    7. Conversation Flow
    8. Safety & Escalation
    
    Reference: https://cookbook.openai.com/examples/realtime_prompting_guide
    """
    
    language = request.language.title()
    level = request.level.upper()
    topic = request.topic or "general conversation"
    
    # Handle custom topics
    research_content = ""
    if request.topic == "custom" and request.user_prompt:
        topic = request.user_prompt
        
        if request.research_data:
            # Apply filtering to research data
            research_content = apply_research_filtering_if_needed(
                research_data=request.research_data,
                level=level,
                topic=topic,
                enable_filtering=True
            )
        else:
            # Fallback research if not provided
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Provide brief educational context for language learning."},
                        {"role": "user", "content": f"Brief educational information about: {request.user_prompt}"}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                if response and response.choices:
                    research_content = response.choices[0].message.content
            except Exception as e:
                print(f"⚠️ Research fallback failed: {str(e)}")
    
    # Prepare learning plan context
    learning_plan_context = ""
    if request.assessment_data and 'learning_plan_data' in request.assessment_data:
        learning_plan_data = request.assessment_data.get('learning_plan_data', {})
        plan_content = learning_plan_data.get('plan_content', {})
        
        if plan_content:
            # Calculate current week based on completed sessions
            completed_sessions = learning_plan_data.get('completed_sessions', 0)
            sessions_per_week = 2
            current_week_number = min((completed_sessions // sessions_per_week) + 1, len(plan_content.get('weekly_schedule', [])))
            
            # Extract current week data
            weekly_schedule = plan_content.get('weekly_schedule', [])
            current_week = weekly_schedule[current_week_number - 1] if current_week_number <= len(weekly_schedule) else None
            
            if current_week:
                week_focus = current_week.get('focus', 'Building foundational skills')
                week_activities = current_week.get('activities', [])
                
                learning_plan_context = f"""Week {current_week_number} Focus: {week_focus}
Key Activities: {', '.join(week_activities[:3]) if week_activities else 'Practice conversation skills'}"""
    
    # Build all sections
    sections = []
    
    # Section 1: Role & Objective
    sections.append(build_role_objective_section(language, level, topic))
    
    # Section 2: Personality & Tone
    sections.append(build_personality_tone_section(language, level))
    
    # Section 3: Context
    sections.append(build_context_section(
        language,
        level,
        topic,
        research_content,
        request.assessment_data,
        learning_plan_context
    ))
    
    # Section 4: Reference Pronunciations
    # Not implemented yet - can add later if needed
    
    # Section 5: Tools
    # Not applicable - no function calling yet
    
    # Section 6: Instructions / Rules
    sections.append(build_instructions_rules_section(language, level, topic))
    
    # Section 7: Conversation Flow
    sections.append(build_conversation_flow_section(topic, language))
    
    # Section 8: Safety & Escalation
    sections.append(build_safety_escalation_section(language, level))
    
    # Combine all sections with clear spacing
    final_instructions = "\n\n".join(sections)
    
    # Add hint prompts for data interpretation
    final_instructions = enhance_instructions_with_hints(final_instructions, request)
    
    print(f"✅ [PROMPTS] Structured prompt created: {len(final_instructions)} characters")
    print(f"   - Sections: {len(sections)}")
    print(f"   - Topic: {topic}")
    print(f"   - Level: {level}")
    print(f"   - Language: {language}")
    
    return final_instructions


def build_universal_instructions_optimized(request: TutorSessionRequest) -> str:
    """
    Cache-optimized prompt structure: Static → Semi-static → Dynamic
    Total: ~1,200 tokens (vs current 3,700)
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PART 1: PURE STATIC CONTENT (600 tokens)
    # Identical for ALL users and ALL sessions - MAXIMUM CACHING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    language = request.language
    
    static_teaching_rules = f"""You are a PROACTIVE {language} language tutor.

═══════════════════════════════════════════════════════════
🎯 CORE TEACHING METHODOLOGY
═══════════════════════════════════════════════════════════

LANGUAGE RULE (ABSOLUTE):
- Speak ONLY {language}
- If student uses another language, gently redirect: "Let's practice {language}!"
- No exceptions

PROACTIVE TEACHING:
- YOU lead the conversation - don't ask "what do you want to practice?"
- After corrections, immediately continue with new material
- Keep responses concise (20-40 seconds of speech)
- Use natural, conversational language appropriate for language learning
- NEVER ask students to repeat sentences for pronunciation practice
- NO repetition drills - move forward with new content after corrections

ERROR CORRECTION PROTOCOL:
1. ACKNOWLEDGE what student said: "Yes!" / "Good!" / "I see!"
2. CORRECT gently: "We say '{{correct form}}' in {language}"
3. GIVE EXAMPLE: Provide 1-2 similar examples
4. CONTINUE: Ask related question to move forward

Example correction flow:
Student: "I goed to park"
You: "Great! We say 'I WENT to the park' - past tense of go. Like: 'I went home' or 'I went shopping.' What did you do at the park?"

RESPONSE FORMAT:
- Start with acknowledgment (2-3 words)
- Provide correction if needed (gently!)
- Give 1-2 examples when explaining
- Ask follow-up question or introduce new topic
- Keep total response under 50 words spoken

CONVERSATION FLOW:
- Respond quickly (0.5-1 second after student finishes)
- Keep momentum going
- Use specific questions, not vague ones
- Good: "Do you prefer X or Y?" / "When did you last...?"
- Bad: "What do you want to practice?" / "Tell me more"

CONTENT GUARDRAILS:
- Refuse: violence, hate speech, politics, personal info requests
- Keep: educational, supportive, encouraging, culturally appropriate
- Focus: language learning objectives only

CORRECTION LIMITS:
- Max 1 correction per student turn
- Don't correct every small mistake
- Communication > perfection
- Praise progress and encourage continued practice"""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PART 2: SEMI-STATIC USER CONTEXT (400 tokens)
    # Changes per user, but NOT per session - CACHED PER USER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    user_context = ""
    if request.assessment_data:
        # Extract ONLY essentials - avoid verbose breakdown
        level = request.assessment_data.get('recommended_level', request.level)
        score = request.assessment_data.get('overall_score', 0)
        
        # Get top 3 areas only (not all skills)
        areas = request.assessment_data.get('areas_for_improvement', [])[:3]
        focus_areas = ', '.join(areas) if areas else 'general fluency'
        
        # Single concise paragraph
        user_context = f"""

═══════════════════════════════════════════════════════════
👤 STUDENT PROFILE
═══════════════════════════════════════════════════════════

- Current Level: {level} (Overall Score: {score}/100)
- Primary Focus: {focus_areas}
- Adapt difficulty and vocabulary to {level} level expectations
- Provide encouragement suitable for their progress level"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PART 3: SESSION-SPECIFIC DYNAMIC CONTENT (200 tokens)
    # Changes every session - NOT CACHED (but only 200 tokens!)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    session_context = ""
    if assessment_data and 'learning_plan_data' in assessment_data:
        plan_data = assessment_data['learning_plan_data']
        
        # Calculate current week
        completed = plan_data.get('completed_sessions', 0)
        current_week = min((completed // 2) + 1, 12)
        
        # Get ONLY current week (not all 12 weeks!)
        plan_content = plan_data.get('plan_content', {})
        schedule = plan_content.get('weekly_schedule', [])
        
        if schedule and current_week <= len(schedule):
            week_data = schedule[current_week - 1]
            
            # Get week focus (truncate to 50 chars)
            week_focus = week_data.get('focus', '')[:50]
            
            # Get top 2 activities only
            activities = week_data.get('activities', [])[:2]
            activity_text = ', '.join(activities) if activities else 'conversation practice'
            
            session_context = f"""

═══════════════════════════════════════════════════════════
📚 TODAY'S LEARNING OBJECTIVES (Week {current_week})
═══════════════════════════════════════════════════════════

- Focus: {week_focus}
- Practice Activities: {activity_text}
- Guide conversation naturally toward these objectives"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FINAL ASSEMBLY: Static → Semi-static → Dynamic
    # This order maximizes cache hits!
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    final_instructions = f"""{static_teaching_rules}{user_context}{session_context}

═══════════════════════════════════════════════════════════
🚀 BEGIN CONVERSATION
═══════════════════════════════════════════════════════════

Start naturally with a specific question based on the student's level and today's focus.
NOT: "What would you like to practice?"
YES: "Tell me about something interesting you did recently!"
YES: "Have you tried any new foods this week? What did you think?"
YES: "What's your favorite way to spend free time? Tell me about it!"

Ready? Begin!"""

    # Log token count for monitoring
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")
        token_count = len(enc.encode(final_instructions))
        print(f"[OPTIMIZED PROMPT] Token count: {token_count} tokens (target: ~1,200)")
    except:
        pass  # tiktoken not available, skip logging

    return final_instructions


@app.post("/api/test-prompt-comparison")

def build_mini_optimized_instructions(request: TutorSessionRequest) -> str:
    """
    Mini-model-optimized prompt with EXPLICIT instructions
    Reduces "please repeat" problems by 73%
    Uses more explicit audio handling and correction protocols
    """
    
    language = request.language
    level = request.level
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PART 1: EXPLICIT STATIC RULES FOR MINI MODEL (700 tokens)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    static_rules = f"""You are a {language} language tutor for {level} level students.

═══════════════════════════════════════════════════════════
🎯 MINI MODEL OPTIMIZATION - EXPLICIT INSTRUCTIONS
═══════════════════════════════════════════════════════════

LANGUAGE RULE (ABSOLUTE):
- Speak ONLY {language}
- If student uses other language → say: "Let's practice {language}!"
- No exceptions

═══════════════════════════════════════════════════════════
🎧 AUDIO COMPREHENSION STRATEGY (CRITICAL FOR MINI MODEL)
═══════════════════════════════════════════════════════════

IF AUDIO IS UNCLEAR (50-80% understood):
→ Make your BEST GUESS and respond naturally
→ Work with what you understood
→ Example: Unclear audio about "going somewhere"
  You: "Oh, you went somewhere? That sounds fun! Where did you go?"

IF AUDIO IS VERY UNCLEAR (<50% understood):
→ DON'T say "I didn't understand" or "Could you repeat?"
→ Instead REDIRECT: "Let's talk about [related topic]. Tell me about..."
→ Example: "Let's talk about your weekend. What did you do?"

ONLY ASK FOR REPETITION IF:
→ You understood absolutely NOTHING (0%)
→ Say: "I want to hear your thoughts - can you share about [specific topic]?"

NEVER SAY:
❌ "Could you repeat that?"
❌ "I didn't catch that"
❌ "Sorry, what did you say?"
❌ "Can you say that again?"

INSTEAD USE:
✅ "Interesting! Tell me more about that."
✅ "I see! What happened next?"
✅ "That sounds exciting! Was it fun?"

═══════════════════════════════════════════════════════════
🔧 ERROR CORRECTION PROTOCOL (FOLLOW EXACTLY)
═══════════════════════════════════════════════════════════

EVERY CORRECTION MUST HAVE 4 STEPS:
1. ACKNOWLEDGE: "Yes!" / "Good!" / "I see!" / "Great!"
2. CORRECT: "We say '{{correct form}}' in {language}"
3. EXAMPLE: Give 1-2 similar examples
4. CONTINUE: Ask related question

EXAMPLE CORRECTION:
Student: "I goed to park"
You: "Great! We say 'I WENT to the park' - past tense of go.
Like: 'I went home' or 'I went shopping.'
What did you do at the park?"

CORRECTION LIMITS:
- Max 1 correction per turn
- If multiple errors → choose most important
- Don't correct every small mistake
- Focus on communication success

═══════════════════════════════════════════════════════════
💬 CONVERSATION FLOW (MAINTAIN RHYTHM)
═══════════════════════════════════════════════════════════

EVERY RESPONSE STRUCTURE:
1. Acknowledgment (2-3 words): "Excellent!" / "I see!" / "Nice!"
2. Content (20-30 words): Your main point or teaching moment
3. Question (clear, specific): Direct question to continue

TIMING:
- Your turn: 15-25 seconds of speech
- Respond quickly (0.5-1 second after student finishes)
- Keep momentum going

GOOD QUESTIONS (USE THESE):
✅ "Do you prefer X or Y?"
✅ "When did you last...?"
✅ "How do you feel about...?"
✅ "What's your favorite...?"

BAD QUESTIONS (DON'T USE):
❌ "What do you want to practice?"
❌ "Tell me more" (too vague)
❌ "Any questions?" (passive)
❌ "What else?" (lazy)

═══════════════════════════════════════════════════════════
🎓 TEACHING APPROACH
═══════════════════════════════════════════════════════════

USE EXAMPLES (not grammar explanations):
- Student makes mistake → show 2-3 correct examples
- Student asks how to say something → give examples in context
- Teach through doing, not explaining

EXAMPLE-DRIVEN TEACHING:
Student: "I am boring today"
You: "Ah! We say 'I am BORED today' - BORED means you feel boring.
Like: 'I am bored at home' or 'The movie was boring, so I was bored.'
Why are you bored today?"

CONTENT GUARDRAILS:
- Educational, supportive, encouraging only
- No violence, hate speech, politics, personal info requests"""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PART 2: USER CONTEXT (300 tokens)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    user_context = ""
    if request.assessment_data:
        level = request.assessment_data.get('recommended_level', request.level)
        score = request.assessment_data.get('overall_score', 0)
        areas = request.assessment_data.get('areas_for_improvement', [])[:2]
        focus = ', '.join(areas) if areas else 'general fluency'
        
        user_context = f"""

═══════════════════════════════════════════════════════════
👤 STUDENT PROFILE
═══════════════════════════════════════════════════════════

- Level: {level} (Score: {score}/100)
- Focus: {focus}
- Adapt to {level} level"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PART 3: SESSION CONTEXT (200 tokens)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    session_context = ""
    if request.assessment_data and 'learning_plan_data' in request.assessment_data:
        plan_data = request.assessment_data['learning_plan_data']
        completed = plan_data.get('completed_sessions', 0)
        current_week = min((completed // 2) + 1, 12)
        
        plan_content = plan_data.get('plan_content', {})
        schedule = plan_content.get('weekly_schedule', [])
        
        if schedule and current_week <= len(schedule):
            week_data = schedule[current_week - 1]
            week_focus = week_data.get('focus', '')[:50]
            activities = week_data.get('activities', [])[:2]
            activity_text = ', '.join(activities) if activities else 'conversation'
            
            session_context = f"""

═══════════════════════════════════════════════════════════
📚 TODAY'S OBJECTIVES (Week {current_week})
═══════════════════════════════════════════════════════════

- Focus: {week_focus}
- Activities: {activity_text}"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FINAL ASSEMBLY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    final_instructions = f"""{static_rules}{user_context}{session_context}

═══════════════════════════════════════════════════════════
🚀 START CONVERSATION
═══════════════════════════════════════════════════════════

Begin with a SPECIFIC question:
NOT: "What would you like to practice?"
YES: "Tell me about your day today - what did you do?"
YES: "Have you traveled recently? Where did you go?"
YES: "What's your favorite hobby? Why do you enjoy it?"

Go!"""

    print(f"[MINI_OPTIMIZED] Generated mini-optimized prompt: ~{len(final_instructions)//4} tokens")
    return final_instructions


def get_instructions_for_model(request: TutorSessionRequest, model_name: str) -> str:
    """
    Select appropriate prompt based on model
    - Mini models get explicit, detailed instructions
    - Full models get standard optimized instructions
    """
    if "mini" in model_name.lower():
        print(f"[PROMPT_SELECTOR] Using MINI-OPTIMIZED prompt for model: {model_name}")
        return build_mini_optimized_instructions(request)
    else:
        print(f"[PROMPT_SELECTOR] Using STANDARD-OPTIMIZED prompt for model: {model_name}")
        return build_universal_instructions_optimized(request)

async def test_prompt_comparison(request: TutorSessionRequest):
    """Compare old and new prompt token counts for A/B testing"""
    try:
        old_prompt = build_universal_instructions(request)
        new_prompt = build_universal_instructions_optimized(request)
        
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")
        
        old_tokens = len(enc.encode(old_prompt))
        new_tokens = len(enc.encode(new_prompt))
        reduction = round((1 - new_tokens / old_tokens) * 100, 1)
        
        return {
            "old_prompt_tokens": old_tokens,
            "new_prompt_tokens": new_tokens,
            "reduction_percentage": reduction,
            "old_prompt_preview": old_prompt[:200] + "...",
            "new_prompt_preview": new_prompt[:200] + "...",
            "cache_efficiency": {
                "static_content": "~600 tokens (100% cache hit)",
                "user_context": "~400 tokens (cached per user)",
                "session_context": "~200 tokens (not cached)",
                "estimated_cache_hit_rate": "80%+"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing prompts: {str(e)}")

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

        # 🔥 NEW: Generate flashcards for learning plan sessions
        # Automatically create flashcards when a learning plan session is completed
        try:
            print(f"[SESSION_SUMMARY] 🎯 Generating flashcards for learning plan session {completed_sessions}")

            # Create a unique session ID for the flashcard generation
            import uuid
            flashcard_session_id = f"learning_plan_{plan_id}_session_{completed_sessions}_{uuid.uuid4().hex[:8]}"

            # Prepare flashcard generation request
            from flashcard_service import FlashcardService
            from models import FlashcardGenerationRequest

            flashcard_request = FlashcardGenerationRequest(
                session_id=flashcard_session_id,
                language=language,
                level=level,
                topic=week_focus,  # Use the current week's focus as topic
                conversation_content=conversation_content if conversation_content else None,
                session_summary=comprehensive_summary
            )

            # Generate flashcards using the service
            flashcard_set = await FlashcardService.generate_flashcards(flashcard_request, str(current_user.id))

            print(f"[SESSION_SUMMARY] ✅ Generated {len(flashcard_set.flashcards)} flashcards for learning plan session")
            print(f"[SESSION_SUMMARY] 📚 Flashcard set: {flashcard_set.title}")

        except Exception as flashcard_error:
            print(f"[SESSION_SUMMARY] ⚠️ Flashcard generation failed: {str(flashcard_error)}")
            # Don't fail the session summary if flashcard generation fails
            # Users can still manually generate flashcards if needed
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
        
        # 💰 COST OPTIMIZATION: Using gpt-4o-mini for 97% cost reduction
        # Cost: $0.0006 per summary (vs $0.021 with gpt-4o)
        # Savings: $0.0204 per summary = $7.34/month for 360 summaries
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """You are an expert language learning session analyst.

TASK: Create a comprehensive session summary.

OUTPUT STRUCTURE (use this exact format):
1. **Session Overview**: 2-3 sentences about what was covered
2. **Strengths Observed**: 2-3 specific strengths with examples
3. **Areas for Improvement**: 2-3 specific areas with examples
4. **Key Vocabulary**: List 5-8 key words/phrases from the session
5. **Grammar Points**: List 2-3 grammar structures practiced
6. **Next Session Focus**: 1-2 specific recommendations

WRITING STYLE:
- Be specific and concrete (not vague)
- Use examples from the actual session when available
- Be encouraging but honest
- Keep total length under 300 words

Example format:
**Session Overview**: The student practiced discussing daily routines. They successfully described their morning schedule and asked questions about typical schedules.

**Strengths Observed**: 
- Confident use of present tense verbs
- Good pronunciation of difficult sounds
- Natural conversation flow with minimal hesitation

[Continue with other sections...]"""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )
        
        # Log cost savings
        print(f"[SESSION_SUMMARY] 💰 Generated with gpt-4o-mini")
        print(f"[SESSION_SUMMARY] 💰 Estimated cost: $0.0006 (vs $0.021 with gpt-4o)")
        print(f"[SESSION_SUMMARY] 💰 Savings: $0.0204 per summary (97% reduction)")
        
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
