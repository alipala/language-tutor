import os
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
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
    # In Railway, we need to be more permissive with CORS
    # Use the correct Railway URL as the default
    frontend_url = os.getenv("FRONTEND_URL", "https://taaco.up.railway.app")
    
    # Add the Railway URL as the origin
    origins = [
        frontend_url,
        "https://taaco.up.railway.app",  # Correct URL
    ]
    
    print(f"Configured CORS with origins: {origins}")
    
    # If we're in Railway, also allow the request from any origin
    # This is more permissive but ensures the app works in Railway's environment
    if os.getenv("RAILWAY") == "true":
        origins = ["*"]
        print("Running in Railway environment, allowing all origins")
else:
    # Allow all origins during development
    origins = ["*"]

print(f"Configured CORS with origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                "environment": os.getenv("NODE_ENV", "development")
            }
        )

# Simple test endpoint to verify API connectivity
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Backend API is working correctly"}

# Enhanced health check endpoint with detailed status information
@app.get("/api/health")
async def health_check():
    import platform
    import sys
    import time
    
    # Get environment information
    is_production = os.getenv("NODE_ENV") == "production"
    environment = "production" if is_production else "development"
    
    # Get system information
    system_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "timestamp": time.time(),
        "environment": environment,
        "railway": os.getenv("RAILWAY") == "true"
    }
    
    # Return comprehensive health data
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": time.time(),  # You could track actual uptime if needed
        "system_info": system_info,
        "api_routes": [
            "/api/languages",
            "/api/realtime/token",
            "/api/test"
        ]
    }

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
    # Log request details for debugging Railway issues
    print(f"Requested path: {full_path}")
    if request:
        print(f"Request headers: {request.headers}")
    
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
        
        # Log the request headers for debugging
        print(f"Request headers: {request.headers if request else 'No request object'}")
        
        # First check for Next.js static files
        if full_path.startswith('_next/') or full_path.startswith('static/'):
            # Try to find the file in various locations
            possible_static_paths = [
                frontend_path / ".next" / full_path.replace('_next/', ''),
                frontend_path / ".next" / full_path,
                frontend_path / full_path,
                frontend_path / "public" / full_path,
            ]
            
            for path in possible_static_paths:
                if path.exists() and path.is_file():
                    print(f"Serving Next.js static file from: {path}")
                    return FileResponse(str(path))
        
        # Check if the request is for a static file (has extension)
        if '.' in full_path and not full_path.endswith('.html'):
            # Try to serve the static file directly
            static_file_paths = [
                frontend_path / "public" / full_path,
                frontend_path / full_path,
                frontend_path / ".next" / "static" / full_path,
            ]
            
            for path in static_file_paths:
                if path.exists() and path.is_file():
                    print(f"Serving static file from: {path}")
                    return FileResponse(str(path))
        
        # SPECIAL HANDLING FOR CLIENT-SIDE ROUTES
        # Check for specific client-side routes and serve appropriate content
        client_side_routes = ["language-selection", "level-selection", "speech"]
        
        # For client-side routes, we want to serve the specific HTML file if it exists
        # Otherwise, serve a version of index.html that has the correct meta tags for the route
        if full_path in client_side_routes:
            print(f"Detected client-side route: {full_path}, looking for specific HTML file")
            
            # Look for route-specific HTML
            route_specific_paths = [
                frontend_path / ".next/server/app" / full_path / "index.html",
                frontend_path / ".next/server/pages" / full_path / "index.html",
                frontend_path / "out" / full_path / "index.html",
                frontend_path / ".next/server/app" / f"{full_path}.html"
            ]
            
            for path in route_specific_paths:
                if path.exists():
                    print(f"Found route-specific file for {full_path} at {path}")
                    return FileResponse(str(path))
            
            # If we're in Railway and it's a known client-side route but no specific file exists,
            # we need to create a custom HTML that will properly redirect on the client side
            print(f"No specific HTML found for {full_path}, creating a special redirect page")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
              <head>
                <title>Language Tutor - {full_path.replace('-', ' ').title()}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <meta name="route" content="/{full_path}">
                <script>
                  // Handle client-side routing for Next.js
                  window.addEventListener('DOMContentLoaded', function() {{
                    // Force the browser to the correct route path
                    const targetPath = '{full_path}';
                    if (window.location.pathname.endsWith(targetPath)) {{
                      // We're on the right URL, let Next.js take over when loaded
                      console.log('Target route already in URL - waiting for Next.js');
                    }} else {{
                      // Redirect to the proper URL
                      window.location.href = window.location.origin + '/' + targetPath;
                    }}
                  }});
                </script>
                <!-- Pull in Next.js scripts -->
                <link rel="stylesheet" href="/_next/static/css/cc3ec16c3199f2fd.css" />
              </head>
              <body>
                <div id="__next">
                  <div style="display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column;">
                    <h1 style="color: #6466f1;">Language Tutor</h1>
                    <div style="margin-top: 20px;">
                      <div style="border: 4px solid #6466f1; border-radius: 50%; width: 40px; height: 40px; border-top-color: transparent; animation: spin 1s linear infinite;"></div>
                    </div>
                    <p style="margin-top: 20px;">Redirecting to {full_path.replace('-', ' ')}...</p>
                  </div>
                </div>
                <style>
                  @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                  }}
                </style>
                <script src="/_next/static/chunks/webpack-2e864253d8c6645c.js" defer></script>
                <script src="/_next/static/chunks/fd9d1056-bfe8cd6c9c7c7e45.js" defer></script>
                <script src="/_next/static/chunks/938-a9dc5eeaa9cbd612.js" defer></script>
                <script src="/_next/static/chunks/main-app-c5d0a9511a5ba1de.js" defer></script>
                <script src="/_next/static/chunks/app/page-5f60a265695a008d.js" defer></script>
              </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        # For all other paths, try standard Next.js file locations
        possible_paths = [
            # For root path
            frontend_path / ".next/server/app/index.html",  # Next.js 13+ app router
            frontend_path / ".next/server/pages/index.html", # Next.js pages router
            frontend_path / ".next/standalone/frontend/app/index.html",
            frontend_path / ".next/standalone/index.html",
            frontend_path / ".next/standalone/frontend/index.html",
            frontend_path / "out/index.html",
            frontend_path / ".next/static/index.html",
            frontend_path / ".next/index.html",
            frontend_path / "public/index.html",
            frontend_path / "index.html",
            frontend_path / ".next/standalone/frontend/out/index.html",
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
        html_content = f"""
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
            <p>Requested path: {full_path}</p>
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
