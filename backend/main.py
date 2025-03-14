import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if OpenAI API key is configured
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY is not configured in .env file")
    print("Please add OPENAI_API_KEY=your_api_key to your .env file")

app = FastAPI(title="Language Tutor Backend API")

# CORS configuration
origins = []
if os.getenv("NODE_ENV") == "production":
    frontend_url = os.getenv("FRONTEND_URL", "https://taco.up.railway.app")
    origins = [frontend_url]
else:
    # Allow all origins during development
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple test endpoint to verify API connectivity
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Backend API is working correctly"}

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Serve static files in production
if os.getenv("NODE_ENV") == "production":
    # Check for Docker environment first
    docker_frontend_path = Path("/app/frontend")
    local_frontend_path = Path(__file__).parent.parent / "frontend"
    
    # Determine which path to use
    frontend_path = docker_frontend_path if docker_frontend_path.exists() else local_frontend_path
    out_path = frontend_path / "out"
    
    print(f"Serving Next.js files from: {frontend_path}")
    
    # Mount static files only if the directories exist
    # Check if the out directory exists (for export mode)
    if out_path.exists():
        # Check and mount _next directory if it exists
        next_static_path = out_path / "_next"
        if next_static_path.exists():
            print(f"Mounting /_next from {next_static_path}")
            app.mount("/_next", StaticFiles(directory=str(next_static_path)), name="next-static")
        
        # Check and mount static directory if it exists
        static_path = out_path / "static"
        if static_path.exists():
            print(f"Mounting /static from {static_path}")
            app.mount("/static", StaticFiles(directory=str(static_path)), name="static-files")
    
    # Fallback to .next directory (for standalone mode)
    next_path = frontend_path / ".next"
    if next_path.exists():
        print(f"Mounting /_next from {next_path}")
        app.mount("/_next", StaticFiles(directory=str(next_path)), name="next-static")
        
        # Check and mount public directory if it exists
        public_path = frontend_path / "public"
        if public_path.exists():
            print(f"Mounting /static from {public_path}")
            app.mount("/static", StaticFiles(directory=str(public_path)), name="public")

# Define models for request validation
class TutorSessionRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer

# Simple endpoint for testing connection
@app.get("/api/test")
async def test_connection():
    return {"message": "Backend connection successful"}

# Mock ephemeral key endpoint for testing when OpenAI API key is not available
@app.post("/api/mock-token")
async def mock_token(request: TutorSessionRequest):
    # Log the request data for debugging
    print(f"Providing mock ephemeral key for testing with language: {request.language}, level: {request.level}, voice: {request.voice}")
    print(f"Request body received: language={request.language}, level={request.level}, voice={request.voice}")
    
    from datetime import datetime, timedelta
    
    expiry = datetime.now() + timedelta(hours=1)
    return {
        "ephemeral_key": "mock_ephemeral_key_for_testing",
        "expires_at": expiry.isoformat()
    }

# Endpoint to get available languages and levels
@app.get("/api/languages")
async def get_languages():
    try:
        # Load the tutor instructions from the JSON file
        instructions_path = Path(__file__).parent / "tutor_instructions.json"
        if not instructions_path.exists():
            raise HTTPException(status_code=404, detail="Tutor instructions not found")
        
        with open(instructions_path, "r") as f:
            tutor_data = json.load(f)
        
        # Extract just the languages and levels structure (without the full instructions)
        languages_data = {}
        for lang_code, lang_data in tutor_data.get("languages", {}).items():
            languages_data[lang_code] = {
                "name": lang_data.get("name", ""),
                "levels": {level: data.get("description", "") for level, data in lang_data.get("levels", {}).items()}
            }
        
        return languages_data
    except Exception as e:
        print(f"Error retrieving languages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve languages: {str(e)}")

# Endpoint to generate ephemeral keys for OpenAI Realtime API with language tutor instructions
@app.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest):
    try:
        # Log the request data for debugging
        print(f"Received token request with language: {request.language}, level: {request.level}, voice: {request.voice}")
        
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
        
        if language not in tutor_data.get("languages", {}):
            raise HTTPException(status_code=400, detail=f"Language '{language}' not supported")
        
        language_data = tutor_data["languages"][language]
        
        if level not in language_data.get("levels", {}):
            raise HTTPException(status_code=400, detail=f"Level '{level}' not supported for language '{language}'")
        
        # Get the instructions for the selected language and level
        instructions = language_data["levels"][level].get("instructions", "")
        
        print(f"Generating ephemeral key with OpenAI API for {language} at level {level}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
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

# Fallback route for serving the index.html in production
@app.get("/", response_class=HTMLResponse)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str = "", request: Request = None):
    # Skip API routes
    if full_path and full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    if os.getenv("NODE_ENV") == "production":
        # Check for Docker environment first
        docker_frontend_path = Path("/app/frontend")
        local_frontend_path = Path(__file__).parent.parent / "frontend"
        
        # Determine which path to use
        frontend_path = docker_frontend_path if docker_frontend_path.exists() else local_frontend_path
        print(f"Looking for index.html in: {frontend_path}")
        
        # Try different possible paths for the index.html file
        possible_paths = [
            # Standalone output paths
            frontend_path / ".next/standalone/frontend/app/index.html",
            frontend_path / ".next/standalone/index.html",
            frontend_path / ".next/standalone/frontend/index.html",
            # Static export paths
            frontend_path / "out/index.html",
            # Server component paths
            frontend_path / ".next/server/app/index.html",
            frontend_path / ".next/server/pages/index.html",
            # Other possible paths
            frontend_path / ".next/static/index.html",
            frontend_path / ".next/index.html",
            frontend_path / "public/index.html",
        ]
        
        for path in possible_paths:
            try:
                if path.exists():
                    print(f"Serving index.html from: {path}")
                    return FileResponse(str(path))
            except Exception as e:
                print(f"Error checking path {path}: {str(e)}")
                continue
        
        # If no index.html is found, send a basic HTML response
        html_content = """
        <!DOCTYPE html>
        <html>
          <head>
            <title>Tutor App</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
          </head>
          <body>
            <h1>Welcome to Tutor App</h1>
            <p>The application is running, but the frontend build was not found.</p>
          </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    # In development, return a 404 for non-API routes
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
