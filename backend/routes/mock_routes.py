"""
Mock Routes for Testing
Provides mock endpoints for development and testing without OpenAI API dependency
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

router = APIRouter()

# Request model (shared with main.py for now)
class TutorSessionRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"
    topic: Optional[str] = None
    user_prompt: Optional[str] = None
    assessment_data: Optional[Dict[str, Any]] = None
    research_data: Optional[str] = None
    conversation_history: Optional[str] = None


@router.post("/api/mock-token")
async def generate_mock_token(request: TutorSessionRequest):
    """
    Mock endpoint for testing when OpenAI API is not available.
    Returns a mock ephemeral token response that matches OpenAI's format.
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
