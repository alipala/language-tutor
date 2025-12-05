"""
Transcription Routes
Handles transcription model configuration and monitoring
"""

import os
from datetime import datetime
from fastapi import APIRouter, HTTPException

# Initialize router
router = APIRouter()

# Route Handlers
@router.get("/api/transcription/status")
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
        print(f"Error getting transcription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transcription status: {str(e)}")
