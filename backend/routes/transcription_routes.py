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
        # Realtime (streaming) transcription — gpt-realtime-whisper, consistent with
        # the gpt-realtime-mini voice model. See routes/realtime_routes.py.
        realtime_model = os.getenv("REALTIME_TRANSCRIBE_MODEL", "gpt-realtime-whisper")
        realtime_delay = os.getenv("REALTIME_TRANSCRIBE_DELAY", "high")

        # File-based (non-realtime) transcription — gpt-4o-transcribe-diarize,
        # retirement-safe until 2027-04-16. See sentence_assessment.py.
        file_primary = os.getenv("FILE_TRANSCRIBE_MODEL", "gpt-4o-transcribe-diarize")
        file_fallback = os.getenv("FILE_TRANSCRIBE_FALLBACK_MODEL", "gpt-4o-transcribe-diarize")

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "REALTIME_TRANSCRIBE_MODEL": realtime_model,
                "REALTIME_TRANSCRIBE_DELAY": realtime_delay,
                "FILE_TRANSCRIBE_MODEL": file_primary,
                "FILE_TRANSCRIBE_FALLBACK_MODEL": file_fallback,
            },
            "models": {
                "realtime_api": realtime_model,
                "sentence_assessment": file_primary,
                "sentence_assessment_fallback": file_fallback,
            },
            "features": {
                "realtime_streaming_native": realtime_model == "gpt-realtime-whisper",
                "retirement_safe": file_primary == "gpt-4o-transcribe-diarize",
                "automatic_fallback": file_fallback != file_primary,
            },
            "supported_languages": [
                "English", "Dutch", "Spanish", "German", "French", "Portuguese"
            ],
            "instructions": {
                "rollback_realtime": "Set REALTIME_TRANSCRIBE_MODEL=gpt-4o-transcribe to revert",
                "rollback_file": "Set FILE_TRANSCRIBE_MODEL=gpt-4o-transcribe to revert",
                "restart_required": "Changes require application restart to take effect"
            }
        }

    except Exception as e:
        print(f"Error getting transcription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transcription status: {str(e)}")
