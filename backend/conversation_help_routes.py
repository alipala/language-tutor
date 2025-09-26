from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
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
from smart_response_generator import smart_response_generator
from learning_plan_context_provider import LearningPlanContextProvider, UserContextProvider

router = APIRouter(prefix="/api/conversation-help", tags=["conversation-help"])

@router.post("/generate", response_model=ConversationHelpResponse)
async def generate_help_content(
    request: ConversationHelpRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    🚀 ENHANCED: Generate contextually intelligent conversation help content.
    
    Handles ALL conversation types:
    - Custom learning plan sessions (rich context)
    - Practice conversations (standard context) 
    - Guest users (minimal context)
    - All edge cases with graceful fallbacks
    
    Uses smart model selection and intent detection for relevant suggestions.
    """
    try:
        print(f"[CONVERSATION_HELP_V2] 🚀 Starting ENHANCED help generation...")
        print(f"[CONVERSATION_HELP_V2] AI response: {request.ai_response[:100]}...")
        print(f"[CONVERSATION_HELP_V2] Target language: {request.target_language}")
        print(f"[CONVERSATION_HELP_V2] User language: {request.user_language}")
        print(f"[CONVERSATION_HELP_V2] Proficiency level: {request.proficiency_level}")
        print(f"[CONVERSATION_HELP_V2] User authenticated: {current_user is not None}")
        
        # Validate required fields
        if not request.ai_response or not request.ai_response.strip():
            print(f"[CONVERSATION_HELP_V2] ❌ Empty AI response, returning 204")
            from fastapi import Response
            return Response(status_code=204)
        
        if not request.target_language or not request.user_language:
            print(f"[CONVERSATION_HELP_V2] ❌ Missing language parameters")
            raise HTTPException(status_code=400, detail="Missing required language parameters")
        
        # Create user context (works for both registered and guest users)
        user_context = UserContextProvider.create_user_context(
            target_language=request.target_language,
            proficiency_level=request.proficiency_level,
            user_language=request.user_language,
            is_guest=(current_user is None)
        )
        
        print(f"[CONVERSATION_HELP_V2] User context: {user_context['context_type']}")
        
        # Generate help using smart response generator
        # NOTE: No learning plan context for practice conversations - this is intentional
        help_response = await smart_response_generator.generate_smart_response(
            request=request,
            learning_plan_context=None,  # Practice conversations have no learning plan context
            user_context=user_context,
            time_budget=7.0
        )
        
        # Track usage analytics if user is authenticated
        if current_user:
            print(f"[CONVERSATION_HELP_V2] 📊 Tracking usage for user: {current_user.id}")
            try:
                await track_help_usage(
                    user_id=current_user.id,
                    help_type="help_generated_v2",
                    language=request.target_language,
                    duration_minutes=0.0
                )
                print(f"[CONVERSATION_HELP_V2] ✅ Usage tracked successfully")
            except Exception as track_error:
                print(f"[CONVERSATION_HELP_V2] ⚠️ Failed to track usage: {track_error}")
        
        print(f"[CONVERSATION_HELP_V2] ✅ Successfully generated ENHANCED contextual help")
        print(f"[CONVERSATION_HELP_V2] 📤 Returning response with {len(help_response.suggested_responses)} suggestions")
        return help_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CONVERSATION_HELP_V2] ❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback to original system
        print(f"[CONVERSATION_HELP_V2] 🔄 Falling back to original system...")
        try:
            fallback_response = await generate_conversation_help_fast(request)
            if fallback_response:
                return fallback_response
        except Exception as fallback_error:
            print(f"[CONVERSATION_HELP_V2] ❌ Fallback also failed: {str(fallback_error)}")
        
        # Ultimate emergency fallback
        templates = INSTANT_RESPONSE_TEMPLATES.get(request.target_language, INSTANT_RESPONSE_TEMPLATES["english"])
        level_templates = templates.get(request.proficiency_level, templates.get("beginner", templates[list(templates.keys())[0]]))
        
        return ConversationHelpResponse(
            ai_response_summary=f"The AI tutor provided guidance in {request.target_language}.",
            suggested_responses=[
                SuggestedResponse(
                    text=template["text"],
                    pronunciation=template["pronunciation"],
                    difficulty_level="beginner",
                    explanation=template["explanation"]
                ) for template in level_templates[:2]
            ],
            vocabulary_highlights=[],
            grammar_tips=[]
        )

@router.post("/generate-with-learning-plan", response_model=ConversationHelpResponse)
async def generate_help_with_learning_plan_context(
    request: ConversationHelpRequest,
    plan_id: Optional[str] = None,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """
    🎯 NEW: Generate conversation help with learning plan context integration.
    
    This endpoint is specifically for custom learning plan sessions where we have
    rich context about the user's learning objectives, current focus, and progress.
    
    For practice conversations without learning plans, use the standard /generate endpoint.
    """
    try:
        print(f"[LEARNING_PLAN_HELP] 🎯 Starting learning plan enhanced help generation...")
        print(f"[LEARNING_PLAN_HELP] Plan ID: {plan_id}")
        print(f"[LEARNING_PLAN_HELP] User authenticated: {current_user is not None}")
        
        # Validate required fields
        if not request.ai_response or not request.ai_response.strip():
            print(f"[LEARNING_PLAN_HELP] ❌ Empty AI response, returning 204")
            from fastapi import Response
            return Response(status_code=204)
        
        if not request.target_language or not request.user_language:
            print(f"[LEARNING_PLAN_HELP] ❌ Missing language parameters")
            raise HTTPException(status_code=400, detail="Missing required language parameters")
        
        # Create user context
        user_context = UserContextProvider.create_user_context(
            target_language=request.target_language,
            proficiency_level=request.proficiency_level,
            user_language=request.user_language,
            is_guest=(current_user is None)
        )
        
        # Get learning plan context if available
        learning_plan_context = None
        if current_user and plan_id:
            learning_plan_context = await LearningPlanContextProvider.get_session_context(
                user_id=current_user.id,
                plan_id=plan_id
            )
            
            if learning_plan_context:
                print(f"[LEARNING_PLAN_HELP] ✅ Learning plan context loaded")
                print(f"[LEARNING_PLAN_HELP] Current focus: {learning_plan_context.get('current_focus', 'N/A')}")
            else:
                print(f"[LEARNING_PLAN_HELP] ⚠️ No learning plan context available")
        else:
            print(f"[LEARNING_PLAN_HELP] ⚠️ Missing user or plan_id for learning plan context")
        
        # Generate help using smart response generator with learning plan context
        help_response = await smart_response_generator.generate_smart_response(
            request=request,
            learning_plan_context=learning_plan_context,
            user_context=user_context,
            time_budget=7.0
        )
        
        # Track usage analytics
        if current_user:
            try:
                await track_help_usage(
                    user_id=current_user.id,
                    help_type="learning_plan_help_generated",
                    language=request.target_language,
                    duration_minutes=0.0
                )
                print(f"[LEARNING_PLAN_HELP] ✅ Usage tracked successfully")
            except Exception as track_error:
                print(f"[LEARNING_PLAN_HELP] ⚠️ Failed to track usage: {track_error}")
        
        print(f"[LEARNING_PLAN_HELP] ✅ Successfully generated learning plan enhanced help")
        return help_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LEARNING_PLAN_HELP] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback to standard generation without learning plan context
        print(f"[LEARNING_PLAN_HELP] 🔄 Falling back to standard generation...")
        return await generate_help_content(request, current_user)

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
