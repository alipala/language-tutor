from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from auth import get_current_user, get_optional_current_user_from_request
from models import UserResponse
from conversation_help import (
    ConversationHelpRequest,
    ConversationHelpResponse,
    SuggestedResponse,
    UserHelpSettings,
    generate_conversation_help,
    generate_conversation_help_fast,
    get_user_help_settings,
    update_user_help_settings,
    track_help_usage,
    INSTANT_RESPONSE_TEMPLATES
)

# Import the new context-aware system
from conversation_help_improved import (
    EnhancedConversationHelpRequest,
    generate_conversation_help_hybrid,
    generate_conversation_help_context_aware
)

router = APIRouter(prefix="/api/conversation-help", tags=["conversation-help"])

@router.post("/generate", response_model=ConversationHelpResponse)
async def generate_help_content(
    request: ConversationHelpRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    Generate conversation help content based on AI tutor's response
    """
    try:
        print(f"[CONVERSATION_HELP] 🚀 Starting help generation...")
        print(f"[CONVERSATION_HELP] AI response: {request.ai_response[:100]}...")
        print(f"[CONVERSATION_HELP] Target language: {request.target_language}")
        print(f"[CONVERSATION_HELP] User language: {request.user_language}")
        print(f"[CONVERSATION_HELP] Proficiency level: {request.proficiency_level}")
        print(f"[CONVERSATION_HELP] Topic: {request.topic}")
        print(f"[CONVERSATION_HELP] Conversation context length: {len(request.conversation_context)}")
        
        # Validate required fields
        if not request.ai_response or not request.ai_response.strip():
            print(f"[CONVERSATION_HELP] ❌ Empty AI response, returning 204")
            from fastapi import Response
            return Response(status_code=204)
        
        if not request.target_language or not request.user_language:
            print(f"[CONVERSATION_HELP] ❌ Missing language parameters")
            raise HTTPException(status_code=400, detail="Missing required language parameters")
        
        # 🚀 NEW: Use context-aware conversation help system
        print(f"[CONVERSATION_HELP] 🎯 Using CONTEXT-AWARE system - NO generic fallbacks!")
        
        # Create enhanced request with learning plan context (if available from session)
        learning_context = None
        if hasattr(request, 'learning_plan_context') and request.learning_plan_context:
            learning_context = request.learning_plan_context
        elif request.topic:
            # Extract learning context from topic if available
            learning_context = {
                'objective': f'Practice {request.topic}',
                'focus_area': request.topic,
                'target_skills': 'Conversation and comprehension'
            }
        
        enhanced_request = EnhancedConversationHelpRequest(
            ai_response=request.ai_response,
            conversation_context=request.conversation_context,
            target_language=request.target_language,
            user_language=request.user_language,
            proficiency_level=request.proficiency_level,
            topic=request.topic,
            learning_plan_context=learning_context,  # NOW IMPLEMENTED
            session_type="general"
        )
        
        # 🔄 Try context-aware system with robust fallback
        print(f"[CONVERSATION_HELP] 🔄 Calling context-aware generation system...")
        context_result = None
        
        try:
            context_result = await asyncio.wait_for(
                generate_conversation_help_context_aware(enhanced_request),
                timeout=10.0  # INCREASED: Give context-aware system 10 seconds for quality responses
            )
        except Exception as e:
            print(f"[CONVERSATION_HELP] ⚠️ Context-aware system failed: {e}")
            context_result = None
        
        # If context-aware fails, use the original fast system
        if context_result is None:
            print(f"[CONVERSATION_HELP] 🏃 Falling back to original fast system...")
            
            # Convert to original request format
            original_request = ConversationHelpRequest(
                ai_response=request.ai_response,
                conversation_context=request.conversation_context,
                target_language=request.target_language,
                user_language=request.user_language,
                proficiency_level=request.proficiency_level,
                topic=request.topic
            )
            
            # Use original fast system as fallback
            fast_result = await generate_conversation_help_fast(original_request)
            
            if fast_result:
                print(f"[CONVERSATION_HELP] ✅ Fast fallback system succeeded")
                help_response = fast_result
            else:
                print(f"[CONVERSATION_HELP] ❌ All systems failed - returning error")
                raise HTTPException(
                    status_code=503,
                    detail="Conversation help system temporarily unavailable. Please try again."
                )
        else:
            # Context-aware system succeeded - convert result
            help_response = ConversationHelpResponse(
                ai_response_summary=context_result.get("ai_response_summary", "The AI provided guidance."),
                suggested_responses=[
                    SuggestedResponse(
                        text=resp.get("text", ""),
                        pronunciation=resp.get("pronunciation", ""),
                        difficulty_level=resp.get("difficulty_level", request.proficiency_level),
                        explanation=resp.get("explanation", ""),
                        translation=resp.get("translation")  # CRITICAL FIX: Include translation field!
                    ) for resp in context_result.get("suggested_responses", [])
                ],
                vocabulary_highlights=context_result.get("vocabulary_highlights", []),
                grammar_tips=context_result.get("grammar_tips", []),
                generated_at=context_result.get("generated_at", datetime.utcnow())
            )
            print(f"[CONVERSATION_HELP] ✅ Context-aware system succeeded!")
            print(f"[CONVERSATION_HELP] 🎯 Intent detected: {context_result.get('context_analysis', {}).get('tutor_intent', 'UNKNOWN')}")
            print(f"[CONVERSATION_HELP]  Teaching phase: {context_result.get('context_analysis', {}).get('teaching_phase', 'unknown')}")
            print(f"[CONVERSATION_HELP] 🔍 Response includes translation: {help_response.suggested_responses[0].translation if help_response.suggested_responses else 'N/A'}")
        
        # Track usage analytics if user is authenticated
        if current_user:
            print(f"[CONVERSATION_HELP] 📊 Tracking usage for user: {current_user.id}")
            try:
                # CRITICAL FIX: Don't track duration for help generation - only for session completion
                await track_help_usage(
                    user_id=current_user.id,
                    help_type="help_generated",
                    language=request.target_language,
                    duration_minutes=0.0  # Help generation doesn't consume speaking time
                )
                print(f"[CONVERSATION_HELP] ✅ Usage tracked successfully")
            except Exception as track_error:
                print(f"[CONVERSATION_HELP] ⚠️ Failed to track usage: {track_error}")
                # Don't fail the request if tracking fails
        
        print(f"[CONVERSATION_HELP] ✅ Successfully generated contextual help content")
        print(f"[CONVERSATION_HELP] 📤 Returning response with {len(help_response.suggested_responses)} suggestions")
        return help_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"[CONVERSATION_HELP] ❌ CRITICAL ERROR generating help content:")
        print(f"[CONVERSATION_HELP] ❌ Error type: {type(e).__name__}")
        print(f"[CONVERSATION_HELP] ❌ Error message: {str(e)}")
        print(f"[CONVERSATION_HELP] ❌ Error details: {repr(e)}")
        
        # Import traceback for detailed error logging
        import traceback
        print(f"[CONVERSATION_HELP] ❌ Full traceback:")
        traceback.print_exc()
        
        # NO GENERIC FALLBACKS - Return service error instead
        print(f"[CONVERSATION_HELP] ❌ Critical system failure - no generic responses allowed")
        raise HTTPException(
            status_code=503,
            detail="Context-aware help system encountered an error. Please try again."
        )

from pydantic import BaseModel


class TutorTranslateRequest(BaseModel):
    text: str
    target_language: str  # language to translate INTO (the user's app/help language)
    source_language: Optional[str] = None  # the tutor's speaking language (optional hint)


class TutorTranslateResponse(BaseModel):
    translation: str


@router.post("/translate", response_model=TutorTranslateResponse)
async def translate_tutor_line(
    request: TutorTranslateRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request),
):
    """
    Fast, single-purpose translation of ONE AI-tutor line into the user's
    language. Used by the live conversation screen to show a subtitle-style
    translation under the tutor's message for beginner (A1/A2) sessions.

    Deliberately minimal: no suggested responses, no vocab, no context —
    just the translation, so it lands in ~300-700ms and never blocks the
    tutor's audio. Best-effort: on any failure returns the original text so
    the client never shows an empty subtitle.
    """
    from openai_client import get_async_openai

    text = (request.text or "").strip()
    if not text:
        return TutorTranslateResponse(translation="")

    target = (request.target_language or "english").strip()
    source_hint = f" The text is in {request.source_language}." if request.source_language else ""

    try:
        response = await asyncio.wait_for(
            get_async_openai().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a translation engine. Translate the user's message into {target}.{source_hint} "
                            f"Return ONLY the translation — no quotes, no notes, no explanation, "
                            f"no romanization. Preserve tone and punctuation."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=200,
            ),
            timeout=6.0,
        )
        translation = (response.choices[0].message.content or "").strip()
        return TutorTranslateResponse(translation=translation or text)
    except Exception as e:
        print(f"[TUTOR_TRANSLATE] ⚠️ Translation failed, returning source: {e}")
        # Fail open — never leave the client hanging on an empty subtitle.
        return TutorTranslateResponse(translation=text)


@router.get("/settings", response_model=UserHelpSettings)
async def get_help_settings(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's conversation help settings
    """
    try:
        settings = await get_user_help_settings(current_user.id)
        return settings
        
    except Exception as e:
        print(f"[CONVERSATION_HELP] Error getting help settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get help settings: {str(e)}"
        )

@router.put("/settings")
async def update_help_settings(
    settings: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user's conversation help settings
    """
    try:
        print(f"[CONVERSATION_HELP] Updating help settings for user {current_user.id}")
        print(f"[CONVERSATION_HELP] New settings: {settings}")
        
        success = await update_user_help_settings(current_user.id, settings)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update help settings"
            )
        
        # Track settings update
        await track_help_usage(
            user_id=current_user.id,
            help_type="settings_updated",
            language=settings.get("help_language", "english")
        )
        
        return {"success": True, "message": "Help settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CONVERSATION_HELP] Error updating help settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update help settings: {str(e)}"
        )

@router.post("/track-usage")
async def track_help_system_usage(
    usage_data: Dict[str, Any],
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    Track help system usage for analytics
    """
    try:
        if not current_user:
            # For guest users, we can still track anonymous usage
            user_id = "guest"
        else:
            user_id = current_user.id
        
        help_type = usage_data.get("help_type", "unknown")
        language = usage_data.get("language", "unknown")
        duration_minutes = usage_data.get("duration_minutes", 0.0)
        
        success = await track_help_usage(user_id, help_type, language, duration_minutes)
        
        return {"success": success}
        
    except Exception as e:
        print(f"[CONVERSATION_HELP] Error tracking usage: {str(e)}")
        # Don't raise an error for analytics tracking failures
        return {"success": False, "error": str(e)}

@router.post("/complete-session")
async def complete_conversation_session(
    session_data: Dict[str, Any],
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    CRITICAL FIX: Track session completion with proper duration and subscription usage
    This endpoint should be called when a conversation session ends
    """
    try:
        if not current_user:
            print(f"[CONVERSATION_HELP] ⚠️ Session completion called for guest user - no subscription tracking")
            return {"success": False, "message": "Guest users don't have subscription tracking"}
        
        user_id = current_user.id
        duration_minutes = session_data.get("duration_minutes", 0.0)
        language = session_data.get("language", "unknown")
        
        print(f"[CONVERSATION_HELP] 🎯 Session completion for user {user_id}")
        print(f"[CONVERSATION_HELP] 📊 Duration: {duration_minutes} minutes")
        print(f"[CONVERSATION_HELP] 🌍 Language: {language}")
        
        # Validate duration
        if duration_minutes <= 0:
            print(f"[CONVERSATION_HELP] ❌ Invalid duration: {duration_minutes}")
            return {"success": False, "message": "Invalid session duration"}
        
        # Track the session completion with duration
        success = await track_help_usage(
            user_id=user_id,
            help_type="session_completed",
            language=language,
            duration_minutes=duration_minutes
        )
        
        if success:
            print(f"[CONVERSATION_HELP] ✅ Session completion tracked successfully")
            return {
                "success": True,
                "message": f"Session completed: {duration_minutes} minutes tracked",
                "duration_minutes": duration_minutes
            }
        else:
            print(f"[CONVERSATION_HELP] ❌ Failed to track session completion")
            return {"success": False, "message": "Failed to track session completion"}
        
    except Exception as e:
        print(f"[CONVERSATION_HELP] ❌ Error completing session: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.get("/analytics")
async def get_help_analytics(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get help system usage analytics for the current user
    """
    try:
        from database import database
        
        analytics_collection = database.conversation_help_analytics
        
        # Get user's help usage statistics
        pipeline = [
            {"$match": {"user_id": current_user.id}},
            {"$group": {
                "_id": "$help_type",
                "count": {"$sum": 1},
                "last_used": {"$max": "$timestamp"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        usage_stats = []
        async for doc in analytics_collection.aggregate(pipeline):
            usage_stats.append({
                "help_type": doc["_id"],
                "count": doc["count"],
                "last_used": doc["last_used"]
            })
        
        # Get total usage count
        total_usage = await analytics_collection.count_documents({"user_id": current_user.id})
        
        return {
            "total_usage": total_usage,
            "usage_breakdown": usage_stats
        }
        
    except Exception as e:
        print(f"[CONVERSATION_HELP] Error getting analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )

# Language options for help content
SUPPORTED_HELP_LANGUAGES = [
    {"code": "english", "name": "English", "native_name": "English"},
    {"code": "spanish", "name": "Spanish", "native_name": "Español"},
    {"code": "french", "name": "French", "native_name": "Français"},
    {"code": "german", "name": "German", "native_name": "Deutsch"},
    {"code": "italian", "name": "Italian", "native_name": "Italiano"},
    {"code": "portuguese", "name": "Portuguese", "native_name": "Português"},
    {"code": "dutch", "name": "Dutch", "native_name": "Nederlands"},
    {"code": "russian", "name": "Russian", "native_name": "Русский"},
    {"code": "chinese", "name": "Chinese", "native_name": "中文"},
    {"code": "japanese", "name": "Japanese", "native_name": "日本語"},
    {"code": "korean", "name": "Korean", "native_name": "한국어"},
    {"code": "arabic", "name": "Arabic", "native_name": "العربية"},
    {"code": "hindi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "turkish", "name": "Turkish", "native_name": "Türkçe"},
]

@router.get("/languages")
async def get_supported_help_languages():
    """
    Get list of supported languages for help content
    """
    return {
        "languages": SUPPORTED_HELP_LANGUAGES,
        "default": "english"
    }
