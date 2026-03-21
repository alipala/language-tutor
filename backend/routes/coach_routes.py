"""
Taal Coach API Routes
=====================
REST endpoints for AI-powered language learning coach.

Endpoints:
- GET /api/coach/context/{language} - Get aggregated user context
- POST /api/coach/chat - Chat with AI coach
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from auth import get_current_user
from models import UserResponse
# OPTIMIZED: Using coach_service_optimized for 8.75x speedup
from services.coach_service_optimized import coach_service_optimized as coach_service
from rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/coach", tags=["Taal Coach"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Request for coach chat"""
    language: str  # Interface language (English, Turkish, etc.)
    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    target_language: Optional[str] = None  # User's learning language (optional)


class RichMessage(BaseModel):
    """Rich message with type and content"""
    type: str  # 'text', 'progress_card', 'dna_card', 'learning_plans_table', 'challenge_stats_table', 'celebration'
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class QuickReply(BaseModel):
    """Quick reply suggestion"""
    label: str
    value: str


class ChatResponse(BaseModel):
    """Response from coach chat"""
    messages: List[RichMessage]
    quick_replies: List[QuickReply]
    raw_response: str


class ContextResponse(BaseModel):
    """User context response"""
    user_profile: Dict[str, Any]
    is_new_user: bool
    has_learning_plan: bool
    has_dna_profile: bool
    learning_plan: Optional[Dict[str, Any]]
    speaking_dna: Optional[Dict[str, Any]]
    breakthroughs: List[Dict[str, Any]]
    stats: Dict[str, Any]
    recent_sessions: List[Dict[str, Any]]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/context/{language}", response_model=ContextResponse)
async def get_user_context(
    language: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get aggregated user context for coach AI.

    This endpoint aggregates all relevant user data:
    - User profile and subscription
    - Learning plan progress
    - Speaking DNA profile and evolution
    - Recent breakthroughs
    - Daily stats and streaks
    - Recent sessions

    This data is used to provide personalized, context-aware coaching.

    Args:
        language: Target language code (e.g., 'dutch', 'spanish')
        current_user: Authenticated user from JWT token

    Returns:
        ContextResponse with all user context

    Raises:
        500: Server error during context aggregation
    """
    try:
        logger.info(f"[COACH API] Getting context for user {current_user.id}, language {language}")

        context = await coach_service.get_user_context(
            user_id=str(current_user.id),
            language=language
        )

        return ContextResponse(**context)

    except Exception as e:
        logger.error(f"[COACH API] Error getting context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user context: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_coach(
    http_request: Request,
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Chat with AI coach.

    RATE LIMITED:
    - Free users: 10 messages per hour
    - Premium users: 20 messages per hour

    The coach provides:
    - Personalized learning guidance
    - Progress insights and celebration
    - Feature explanations and app guidance
    - Motivational support
    - Actionable tips and strategies

    IMPORTANT: Responses are in the user's INTERFACE language (English, Turkish, etc.),
    NOT in the target learning language. This ensures users can understand the guidance clearly.

    Args:
        http_request: FastAPI Request object (for rate limiting)
        request: Chat request with message and conversation history
        current_user: Authenticated user from JWT token

    Returns:
        ChatResponse with AI messages and quick reply suggestions

    Raises:
        400: Invalid request
        429: Rate limit exceeded
        500: Server error during chat generation
    """
    # Apply rate limiting FIRST (before any processing)
    await check_rate_limit(
        request=http_request,
        user_id=str(current_user.id),
        subscription_status=current_user.subscription_status
    )

    try:
        logger.info(f"[COACH API] Chat request from user {current_user.id}: '{request.message}'")

        # Convert conversation history to dict
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Generate coach response
        response = await coach_service.chat(
            user_id=str(current_user.id),
            language=request.language,  # Interface language
            user_message=request.message,
            conversation_history=history,
            target_language=request.target_language  # Learning language
        )

        # Convert to response models
        messages = [RichMessage(**msg) for msg in response["messages"]]
        quick_replies = [QuickReply(**qr) for qr in response["quick_replies"]]

        return ChatResponse(
            messages=messages,
            quick_replies=quick_replies,
            raw_response=response["raw_response"]
        )

    except Exception as e:
        logger.error(f"[COACH API] Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate coach response: {str(e)}"
        )
