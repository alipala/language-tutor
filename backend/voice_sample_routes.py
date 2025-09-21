import os
import json
import asyncio
import tempfile
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
from openai import OpenAI
from auth import get_optional_current_user_from_request
from models import UserResponse

router = APIRouter()

# Initialize OpenAI client with error handling (same pattern as other files)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables for voice_sample_routes")

try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully in voice_sample_routes")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        # Alternative initialization without proxies
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method in voice_sample_routes")
    else:
        print(f"Error initializing OpenAI client in voice_sample_routes: {str(e)}")
        raise

class VoiceSampleRequest(BaseModel):
    voice_id: str
    language: Optional[str] = "english"
    level: Optional[str] = "intermediate"

# Voice character descriptions for generating appropriate sample text
VOICE_CHARACTERS = {
    'alloy': {
        'personality': 'Professional and encouraging',
        'style': 'Clear, balanced, and supportive',
        'sample_text': "Hello! I'm your AI language tutor. I'm here to help you practice and improve your speaking skills in a supportive environment."
    },
    'ash': {
        'personality': 'Warm and approachable',
        'style': 'Friendly, conversational, and welcoming',
        'sample_text': "Hi there! I'm excited to be your language learning companion. Let's have some fun while we practice together!"
    },
    'ballad': {
        'personality': 'Expressive and articulate',
        'style': 'Melodic, clear pronunciation, and engaging',
        'sample_text': "Welcome to your language journey! I love helping students discover the beauty and rhythm of language through practice."
    },
    'coral': {
        'personality': 'Energetic and motivating',
        'style': 'Upbeat, enthusiastic, and inspiring',
        'sample_text': "Hey! Ready to boost your language skills? I'm here to keep you motivated and make learning an exciting adventure!"
    },
    'echo': {
        'personality': 'Patient and supportive',
        'style': 'Calm, gentle, and reassuring',
        'sample_text': "Hello, and welcome. I'm here to support you at your own pace. Take your time, and remember that every step forward is progress."
    },
    'sage': {
        'personality': 'Engaging storyteller',
        'style': 'Wise, narrative, and captivating',
        'sample_text': "Greetings, fellow learner. Language is like a story waiting to be told. Let me guide you through this fascinating journey of discovery."
    },
    'shimmer': {
        'personality': 'Confident and authoritative',
        'style': 'Strong, clear, and professional',
        'sample_text': "Welcome to your language training. I'm here to challenge you and help you achieve excellence in your communication skills."
    },
    'verse': {
        'personality': 'Dynamic and modern',
        'style': 'Contemporary, energetic, and fresh',
        'sample_text': "What's up! Ready to level up your language game? I'm here to make learning feel fresh, relevant, and totally engaging!"
    }
}

@router.post("/api/voice/sample")
async def generate_voice_sample(
    request: VoiceSampleRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    Generate a voice sample using OpenAI's realtime API
    """
    try:
        print(f"🎤 [VOICE_SAMPLE] Generating sample for voice: {request.voice_id}")
        
        # Validate voice ID
        if request.voice_id not in VOICE_CHARACTERS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid voice ID: {request.voice_id}"
            )
        
        # Get voice character info
        voice_info = VOICE_CHARACTERS[request.voice_id]
        sample_text = voice_info['sample_text']
        
        print(f"🎤 [VOICE_SAMPLE] Using sample text: {sample_text}")
        
        # Create a temporary session with OpenAI Realtime API
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Generate instructions for the voice sample
        instructions = f"""You are an AI language tutor with the following characteristics:
- Personality: {voice_info['personality']}
- Speaking style: {voice_info['style']}
- Voice: {request.voice_id}

When the user asks you to say something, speak the COMPLETE text they provide without cutting it short. 
Make sure to say the entire greeting from beginning to end.
Use your natural {request.voice_id} voice with your {voice_info['personality']} personality.
"""
        # Create ephemeral token for voice sample generation
        payload = {
            "type": "realtime",
            "model": "gpt-realtime",
            "voice": request.voice_id,
            "instructions": instructions,
            "modalities": ["audio", "text"],
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 1000
            }
        }
        
        print(f"🎤 [VOICE_SAMPLE] Creating ephemeral session...")
        
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
            print(f"❌ [VOICE_SAMPLE] OpenAI API error: {error_text}")
            raise HTTPException(status_code=response.status_code, detail=error_text)
        
        session_data = response.json()
        ephemeral_key = session_data.get("client_secret", {}).get("value") or session_data.get("ephemeral_key")
        
        if not ephemeral_key:
            raise HTTPException(status_code=500, detail="Failed to get ephemeral key")
        
        print(f"✅ [VOICE_SAMPLE] Ephemeral session created successfully")
        
        # Return the ephemeral key and sample text for the frontend to use
        return {
            "success": True,
            "voice_id": request.voice_id,
            "ephemeral_key": ephemeral_key,
            "sample_text": sample_text,
            "voice_info": voice_info,
            "session_data": session_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [VOICE_SAMPLE] Error generating voice sample: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating voice sample: {str(e)}"
        )

@router.get("/api/voice/characters")
async def get_voice_characters():
    """
    Get all available voice characters with their descriptions
    """
    try:
        return {
            "success": True,
            "voices": VOICE_CHARACTERS
        }
    except Exception as e:
        print(f"❌ [VOICE_CHARACTERS] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching voice characters: {str(e)}"
        )
