"""
Feedback Routes
Handles sentence analysis feedback functionality
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from bson import ObjectId

from auth import get_optional_current_user_from_request
from models import UserResponse

# Initialize router
router = APIRouter()

# Pydantic Models
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

# Route Handlers
@router.post("/api/feedback/sentence-analysis")
async def submit_sentence_analysis_feedback(
    request: Request,
    feedback: SentenceAnalysisFeedback,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """Store user feedback about sentence analysis decisions"""
    try:
        from database import database

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

        print(f"[FEEDBACK] Stored feedback: {feedback.feedback_type} for sentence: '{feedback.sentence_text[:30]}...'")

        return {
            "success": True,
            "feedback_id": str(result.inserted_id),
            "message": "Feedback submitted successfully"
        }

    except Exception as e:
        print(f"[FEEDBACK] Error storing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {str(e)}")
