"""
Feedback Routes
Handles sentence analysis feedback and session feedback functionality
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from bson import ObjectId
import logging

from auth import get_optional_current_user_from_request
from models import UserResponse, SessionFeedbackRequest, SessionFeedbackResponse

logger = logging.getLogger(__name__)

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


# ============================================================================
# SESSION FEEDBACK (Thumbs Up/Down for Conversations & Challenges)
# ============================================================================

@router.post("/api/feedback/session", response_model=SessionFeedbackResponse)
async def submit_session_feedback(
    feedback_request: SessionFeedbackRequest,
    http_request: Request,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    Submit feedback for a completed session (conversation or challenge)

    - For guests: device_id is optional for tracking
    - For registered users: user_id from auth token (optional)
    - Rate limit: 1 feedback per session_id per user/device
    """
    try:
        from database import database

        # Get user_id from auth if available, otherwise use provided user_id
        user_id = None
        if current_user:
            user_id = current_user.id
            logger.info(f"📝 Authenticated user submitting feedback: {user_id}")
        elif feedback_request.user_id:
            user_id = feedback_request.user_id
            logger.info(f"📝 User ID provided in request: {user_id}")
        else:
            logger.info("📝 Guest user submitting feedback")

        # Validate challenge_type for challenge sessions
        if feedback_request.session_type == 'challenge' and not feedback_request.challenge_type:
            raise HTTPException(
                status_code=422,
                detail="challenge_type is required for challenge sessions"
            )

        # Check for duplicate feedback (prevent spam)
        query_conditions = []
        if user_id:
            query_conditions.append({"user_id": user_id})
        if feedback_request.device_id:
            query_conditions.append({"device_id": feedback_request.device_id})

        if query_conditions:
            existing_feedback = await database.session_feedback.find_one({
                "session_id": feedback_request.session_id,
                "$or": query_conditions
            })

            if existing_feedback:
                logger.warning(f"⚠️ Duplicate feedback attempt for session {feedback_request.session_id}")
                raise HTTPException(
                    status_code=409,
                    detail="Feedback already submitted for this session"
                )

        # Validate and clean comment
        comment = None
        if feedback_request.comment:
            comment = feedback_request.comment.strip()
            if comment == '':
                comment = None

        # Prepare feedback document
        feedback_doc = {
            "user_id": user_id,
            "is_guest": feedback_request.is_guest,
            "device_id": feedback_request.device_id,
            "session_id": feedback_request.session_id,
            "session_type": feedback_request.session_type,
            "challenge_type": feedback_request.challenge_type,
            "feedback_type": feedback_request.feedback_type,
            "comment": comment,
            "language": feedback_request.language,
            "level": feedback_request.level,
            "topic": feedback_request.topic,
            "session_duration_seconds": feedback_request.session_duration_seconds,
            "words_spoken": feedback_request.words_spoken,
            "accuracy": feedback_request.accuracy,
            "user_agent": feedback_request.user_agent or http_request.headers.get("User-Agent"),
            "app_version": feedback_request.app_version,
            "created_at": datetime.utcnow()
        }

        # Insert into database
        result = await database.session_feedback.insert_one(feedback_doc)

        logger.info(
            f"✅ Feedback submitted - Session: {feedback_request.session_id}, "
            f"Type: {feedback_request.feedback_type}, User: {user_id or 'guest'}, "
            f"Session Type: {feedback_request.session_type}, "
            f"Has Comment: {comment is not None}"
        )

        return SessionFeedbackResponse(
            success=True,
            message="Thank you for your feedback!",
            feedback_id=str(result.inserted_id)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback. Please try again."
        )
