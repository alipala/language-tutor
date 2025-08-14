from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import logging
from datetime import datetime
import base64
import tempfile
import os

from auth import get_current_user
from services.contribution_service import ContributionService
from services.queue_service import QueueService
from services.story_voice_service import StoryVoiceService
from models.world_building_models import (
    StoryContributionResponse, ContributionListResponse,
    ContributionUpdate
)
from utils.feature_flags import feature_flags

router = APIRouter(prefix="/api/v2/worlds", tags=["World Building - Contributions"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

@router.post("/{world_id}/contribute")
async def submit_contribution(
    world_id: str,
    transcript: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    duration_seconds: int = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Submit a contribution to a story world"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Validate input
        if not transcript and not audio_file:
            raise HTTPException(status_code=400, detail="Either transcript or audio file is required")
        
        if duration_seconds < 30:
            raise HTTPException(status_code=400, detail="Contribution must be at least 30 seconds")
        
        if duration_seconds > 300:  # 5 minutes
            raise HTTPException(status_code=400, detail="Contribution cannot exceed 5 minutes")
        
        # Process audio file if provided
        audio_base64 = None
        audio_url = None
        
        if audio_file:
            # Validate audio file
            if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Invalid audio file format")
            
            # Read and encode audio
            audio_content = await audio_file.read()
            if len(audio_content) > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")
            
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            
            # In a production environment, you would upload to cloud storage
            # For now, we'll just indicate that audio was provided
            audio_url = f"audio/contributions/{world_id}/{user_id}_{datetime.utcnow().timestamp()}.wav"
        
        # Validate transcript length if provided
        if transcript:
            word_count = len(transcript.split())
            if word_count < 50:
                raise HTTPException(status_code=400, detail="Transcript must be at least 50 words")
            if word_count > 500:
                raise HTTPException(status_code=400, detail="Transcript cannot exceed 500 words")
        
        # Process the contribution
        success, message, contribution_id = await ContributionService.process_contribution(
            world_id=world_id,
            user_id=user_id,
            transcript=transcript,
            audio_base64=audio_base64,
            audio_url=audio_url,
            duration_seconds=duration_seconds
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Notify next contributor
        await QueueService.notify_next_contributor(world_id, user_id)
        
        return {
            "success": True,
            "message": message,
            "contribution_id": contribution_id,
            "speaking_minutes": duration_seconds / 60.0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting contribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Error submitting contribution")

@router.get("/{world_id}/contributions", response_model=ContributionListResponse)
async def get_contributions(
    world_id: str,
    limit: int = 20,
    offset: int = 0,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get contributions for a story world"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user (for access control)
        current_user = await get_current_user(credentials.credentials)
        
        # Validate pagination
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        # Get contributions
        contributions, total_count = await ContributionService.get_contributions(
            world_id=world_id,
            limit=limit,
            offset=offset
        )
        
        return ContributionListResponse(
            contributions=contributions,
            total_count=total_count,
            has_more=offset + len(contributions) < total_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contributions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting contributions")

@router.put("/contributions/{contribution_id}")
async def update_contribution(
    contribution_id: str,
    updates: ContributionUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a contribution (only by the contributor)"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Update contribution
        success, message = await ContributionService.update_contribution(
            contribution_id=contribution_id,
            user_id=user_id,
            updates=updates.dict(exclude_unset=True)
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating contribution")

@router.delete("/contributions/{contribution_id}")
async def delete_contribution(
    contribution_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a contribution (only by the contributor)"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Delete contribution
        success, message = await ContributionService.delete_contribution(
            contribution_id=contribution_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting contribution")

@router.get("/{world_id}/queue/status")
async def get_queue_status(
    world_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's queue position and status"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Get queue status
        status = await QueueService.get_queue_status(world_id, user_id)
        
        if "error" in status:
            raise HTTPException(status_code=400, detail=status["error"])
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting queue status")

@router.post("/{world_id}/queue/skip")
async def skip_turn(
    world_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Skip your turn in the contribution queue"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Skip turn
        success, message = await QueueService.skip_turn(world_id, user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Notify next contributor
        await QueueService.notify_next_contributor(world_id, user_id)
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping turn: {str(e)}")
        raise HTTPException(status_code=500, detail="Error skipping turn")

@router.get("/{world_id}/queue/overview")
async def get_queue_overview(
    world_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get overview of queue status for a world (for world creators/admins)"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        
        # Get queue overview
        overview = await QueueService.get_world_queue_overview(world_id)
        
        if "error" in overview:
            raise HTTPException(status_code=400, detail=overview["error"])
        
        return overview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting queue overview")

@router.post("/{world_id}/validate-turn")
async def validate_user_turn(
    world_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validate if it's the user's turn to contribute"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Validate turn
        can_contribute, message = await ContributionService.validate_user_turn(world_id, user_id)
        
        return {
            "can_contribute": can_contribute,
            "message": message,
            "user_id": user_id,
            "world_id": world_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating user turn: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating turn")

# Health check endpoint for contribution system
@router.get("/contributions/health")
async def contribution_system_health():
    """Health check for contribution management system"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Basic health checks
        from database import database
        
        # Check database connectivity
        await database.command("ping")
        
        # Check if required collections exist
        collections = await database.list_collection_names()
        required_collections = ["story_worlds", "story_contributions", "collaboration_queue", "users"]
        missing_collections = [col for col in required_collections if col not in collections]
        
        if missing_collections:
            return {
                "status": "degraded",
                "message": f"Missing collections: {', '.join(missing_collections)}",
                "timestamp": datetime.utcnow()
            }
        
        return {
            "status": "healthy",
            "message": "Contribution management system is operational",
            "features": {
                "contribution_processing": True,
                "queue_management": True,
                "turn_validation": True,
                "audio_transcription": True,
                "learning_metrics": True,
                "ai_feedback": True
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"System error: {str(e)}",
            "timestamp": datetime.utcnow()
        }

# ============================================================================
# VOICE INTEGRATION ENDPOINTS
# ============================================================================

@router.get("/{world_id}/voice/session-config")
async def get_story_voice_session_config(
    world_id: str,
    session_type: str = "contribution",  # practice, contribution, review
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get configuration for story voice session"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Validate session type
        valid_session_types = ["practice", "contribution", "review"]
        if session_type not in valid_session_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid session type. Must be one of: {', '.join(valid_session_types)}"
            )
        
        # Get session configuration
        config = await StoryVoiceService.get_story_voice_session_config(
            world_id=world_id,
            user_id=user_id,
            session_type=session_type
        )
        
        if "error" in config:
            raise HTTPException(status_code=400, detail=config["error"])
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting story voice session config: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting session configuration")

@router.post("/{world_id}/voice/validate-session")
async def validate_story_voice_session(
    world_id: str,
    session_type: str = "contribution",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validate if user can start a story voice session"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Validate session
        can_access, error_msg = await StoryVoiceService.validate_story_voice_session(
            world_id=world_id,
            user_id=user_id,
            session_type=session_type
        )
        
        return {
            "can_access": can_access,
            "message": error_msg if not can_access else "Session access validated",
            "session_type": session_type,
            "world_id": world_id,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating story voice session: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating session")

@router.post("/{world_id}/voice/complete-session")
async def complete_story_voice_session(
    world_id: str,
    session_type: str = Form(...),
    transcript: str = Form(...),
    duration_seconds: int = Form(...),
    audio_base64: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Complete a story voice session and process the result"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Validate inputs
        if not transcript or not transcript.strip():
            raise HTTPException(status_code=400, detail="Transcript is required")
        
        if duration_seconds < 1:
            raise HTTPException(status_code=400, detail="Duration must be at least 1 second")
        
        # Validate session type
        valid_session_types = ["practice", "contribution", "review"]
        if session_type not in valid_session_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid session type. Must be one of: {', '.join(valid_session_types)}"
            )
        
        # Process the completed session
        success, message, contribution_id = await StoryVoiceService.process_story_voice_session_completion(
            world_id=world_id,
            user_id=user_id,
            session_type=session_type,
            transcript=transcript.strip(),
            audio_base64=audio_base64,
            duration_seconds=duration_seconds
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # For contribution sessions, notify next contributor
        if session_type == "contribution" and contribution_id:
            await QueueService.notify_next_contributor(world_id, user_id)
        
        response_data = {
            "success": True,
            "message": message,
            "session_type": session_type,
            "duration_seconds": duration_seconds,
            "speaking_minutes": duration_seconds / 60.0
        }
        
        # Add contribution ID if this was a contribution session
        if contribution_id:
            response_data["contribution_id"] = contribution_id
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing story voice session: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing session")

@router.get("/{world_id}/voice/story-context")
async def get_story_context_for_voice(
    world_id: str,
    session_type: str = "contribution",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get story context for voice session (for debugging/testing)"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(status_code=404, detail="World Building feature is not enabled")
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials)
        user_id = str(current_user.id)
        
        # Get story context
        context = await StoryVoiceService.get_story_context_for_voice_session(
            world_id=world_id,
            user_id=user_id,
            session_type=session_type
        )
        
        if "error" in context:
            raise HTTPException(status_code=400, detail=context["error"])
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting story context: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting story context")
