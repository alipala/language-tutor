from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from auth import get_current_user, get_optional_current_user_from_request
from models import UserResponse
from conversation_help import (
    ConversationHelpRequest,
    ConversationHelpResponse,
    UserHelpSettings,
    generate_conversation_help,
    get_user_help_settings,
    update_user_help_settings,
    track_help_usage
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
        
        # Generate help content using ultra-fast method
        print(f"[CONVERSATION_HELP] 🔄 Calling generate_conversation_help_fast...")
        from conversation_help import generate_conversation_help_fast
        help_response = await generate_conversation_help_fast(request)
        print(f"[CONVERSATION_HELP] 📥 Received response from generate_conversation_help_fast: {help_response is not None}")
        
        # 🚀 NEW STRATEGY: Only return contextual responses, never generic fallbacks
        if help_response is None:
            print(f"[CONVERSATION_HELP] ✅ No contextual help generated, returning 204 No Content")
            # Return 204 No Content - frontend will not show modal
            from fastapi import Response
            return Response(status_code=204)
        
        # Track usage analytics if user is authenticated
        if current_user:
            print(f"[CONVERSATION_HELP] 📊 Tracking usage for user: {current_user.id}")
            try:
                await track_help_usage(
                    user_id=current_user.id,
                    help_type="help_generated",
                    language=request.target_language
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
        
        # Return fallback response instead of 500 error
        print(f"[CONVERSATION_HELP] 🔄 Generating fallback response...")
        fallback_response = ConversationHelpResponse(
            ai_response_summary=f"The AI tutor just spoke in {request.target_language}. They provided guidance to help you practice.",
            suggested_responses=[
                {
                    "text": "I understand" if request.target_language == "english" else "Ik begrijp het" if request.target_language == "dutch" else "Entiendo",
                    "pronunciation": "aɪ ˌʌndərˈstænd" if request.target_language == "english" else "ɪk bəˈɣrɛip ət" if request.target_language == "dutch" else "en-tjen-do",
                    "difficulty_level": "beginner",
                    "explanation": "A simple way to show you understand"
                },
                {
                    "text": "Can you repeat that?" if request.target_language == "english" else "Kun je dat herhalen?" if request.target_language == "dutch" else "¿Puedes repetir eso?",
                    "pronunciation": "kæn ju rɪˈpit ðæt" if request.target_language == "english" else "kʏn jə dɑt hərˈhaːlə" if request.target_language == "dutch" else "pwe-des re-pe-tir e-so",
                    "difficulty_level": "beginner",
                    "explanation": "Ask for repetition if you didn't catch everything"
                }
            ],
            vocabulary_highlights=[],
            grammar_tips=[]
        )
        
        print(f"[CONVERSATION_HELP] ✅ Returning fallback response")
        return fallback_response

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
        
        success = await track_help_usage(user_id, help_type, language)
        
        return {"success": success}
        
    except Exception as e:
        print(f"[CONVERSATION_HELP] Error tracking usage: {str(e)}")
        # Don't raise an error for analytics tracking failures
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
