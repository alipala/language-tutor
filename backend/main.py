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

# Define a new model for custom topic prompts
class CustomTopicRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: str  # The custom prompt from the user

# Endpoint to generate ephemeral keys for OpenAI Realtime API with language tutor instructions
@app.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest):
    try:
        # Log the request data for debugging
        print(f"Received token request with language: {request.language}, level: {request.level}, voice: {request.voice}, topic: {request.topic}")
        
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
        
        if language not in tutor_data.get("languages", {}):
            raise HTTPException(status_code=400, detail=f"Language '{language}' not supported")
        
        language_data = tutor_data["languages"][language]
        
        if level not in language_data.get("levels", {}):
            raise HTTPException(status_code=400, detail=f"Level '{level}' not supported for language '{language}'")
        
        # Get the instructions for the selected language and level
        instructions = language_data["levels"][level].get("instructions", "")
        
        # Add enhanced language detection and enforcement instructions
        language_detection_instructions = f"\n\nCRITICAL LANGUAGE DETECTION ENHANCEMENT: You have advanced language detection capabilities. Before responding to any user input, carefully analyze the language being spoken. Listen for pronunciation patterns, vocabulary, grammar structures, and accent characteristics. If the user is speaking in the target language ({language}), respond normally. If they are speaking in a different language, use the standard language reminder response. Pay special attention to pronunciation, accent, and context clues to accurately identify the language being spoken. Do not assume a language based on a single unclear word - analyze the overall speech pattern."
        
        # Add language-specific enforcement to ensure the tutor always speaks the correct language
        if language == "english":
            # Enhanced enforcement for English language with better language detection
            extra_instructions = "\n\nEXTREMELY IMPORTANT INSTRUCTION: You MUST ONLY respond in English. Your FIRST message MUST be in English. Always start with an English greeting appropriate for the level. For A1 level, start with: 'Hello! I am your English language tutor. How are you today?'"
            
            # Add enhanced language detection and enforcement instructions
            language_enforcement = "\n\nMOST IMPORTANT INSTRUCTION ON LANGUAGE ENFORCEMENT: If the student is NOT speaking in English, but in another language such as Dutch, Spanish, German, French, Turkish, Arabic, or any other language, you must EXCLUSIVELY respond with: 'I understand you're speaking in another language, but let's practice English. Try to say it in English.' and then provide a simple English sentence they can use as an example.\n\nYou must ABSOLUTELY NOT respond to the CONTENT of what the student says in another language. COMPLETELY IGNORE what the student has said in another language. Do NOT attempt to understand, translate, or respond to the meaning of their message. Respond ONLY with the standard language reminder phrase. Do NOT continue the conversation or topic until the student speaks in English.\n\nExample of what NOT to do: If the student says in Turkish 'My favorite color is red', do NOT respond with 'You say your favorite color is red. Let's practice English.' This is INCORRECT because you are responding to the content.\n\nExample of what TO do: If the student speaks in Turkish, German, or any other language, respond ONLY with: 'I understand you're speaking in another language, but let's practice English. Try to say it in English. For example, you could say: My favorite color is...'\n\nIf the student CONTINUES to speak in another language, continue repeating this instruction and NEVER respond to the content of their messages until they speak in English. This is an ABSOLUTE RULE with no exceptions."
            
            instructions = instructions + extra_instructions + language_enforcement
            print("Added enhanced English-only enforcement to instructions")
        
        # Add universal formatting and speech instructions
        formatting_instructions = "\n\nFORMATTING INSTRUCTIONS: Always use proper spacing between words and sentences. Ensure there is a space after punctuation marks like periods, commas, question marks, and exclamation points. Maintain proper paragraph structure with line breaks between paragraphs. Use proper capitalization at the beginning of sentences."
        
        speech_instructions = "\n\nSPEECH CLARITY: When speaking, maintain a natural pace with slight pauses between sentences. Articulate words clearly and avoid running words together. Use proper intonation to indicate questions, statements, and emphasis."
        
        # Combine all instructions
        instructions = instructions + language_detection_instructions + formatting_instructions + speech_instructions
        
        print(f"Generating ephemeral key with OpenAI API for {language} at level {level}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-realtime-preview",
                    "voice": request.voice,
                    "instructions": instructions,
                    "modalities": ["audio", "text"]
                },
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

# Endpoint to handle custom topic prompts
@app.post("/api/custom-topic")
async def custom_topic(request: CustomTopicRequest):
    try:
        # Extract user input from request
        user_prompt = request.user_prompt
        language = request.language.lower()
        level = request.level.upper()
        
        # Log the request for debugging
        print(f"Processing custom topic request: language={language}, level={level}, prompt={user_prompt[:50]}...")
        
        # Prepare system prompt based on language learning context
        system_prompt = f"You are a helpful language tutor for {language.capitalize()} at {level} level. "
        system_prompt += "When answering questions, search for current information to provide accurate, up-to-date responses. "
        system_prompt += "Include relevant vocabulary and phrases in your response when appropriate. "
        system_prompt += "Adapt your language complexity to the {level} proficiency level and make the response educational for language learning."
        
        # Note: OpenAI's web search is not yet available for gpt-4o-mini in the standard API
        # Using enhanced prompting to provide the best possible response with available knowledge
        print("Using enhanced language tutor response (web search not available for gpt-4o-mini)")
        
        # Enhanced fallback with better prompting
        enhanced_system_prompt = f"You are a helpful language tutor for {language.capitalize()} at {level} level. "
        enhanced_system_prompt += "While you don't have access to real-time information, provide the most comprehensive and educational response possible based on your training data. "
        enhanced_system_prompt += "Include relevant vocabulary and phrases in your response when appropriate. "
        enhanced_system_prompt += f"Adapt your language complexity to the {level} proficiency level. "
        enhanced_system_prompt += "If the topic might have recent developments, acknowledge this and suggest where users might find more current information."
        
        # Call OpenAI API to generate response using the standard chat completions endpoint
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        # Extract the response content
        if response and hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            return {"response": content}
        
        # Final fallback if response structure is unexpected
        return {"response": "I apologize, but I'm having trouble processing your request right now. Please try again later."}
    
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
