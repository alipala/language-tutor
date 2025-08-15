"""
World Building API Routes - Phase 2
RESTful API endpoints for collaborative world building feature
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.security import HTTPBearer
from typing import Optional, List
from datetime import datetime

# Import existing auth dependencies
from auth import get_current_user
from models import UserResponse

# Import world building components
from models.world_building_models import (
    StoryWorldCreate, StoryWorldResponse, StoryWorldUpdate,
    WorldListRequest, WorldListResponse,
    WorldInvitationCreate, WorldInvitationResponse,
    InvitationAcceptRequest, WorldJoinRequest,
    ContributionListRequest, ContributionListResponse
)
from services.world_building_service import world_building_service
from services.user_integration_service import user_integration_service
from utils.feature_flags import feature_flags

# Create router with v2 prefix to isolate from existing endpoints
router = APIRouter(prefix="/api/v2/worlds", tags=["World Building"])
security = HTTPBearer()

# Feature flag dependency
async def check_world_building_enabled():
    """Dependency to check if world building feature is enabled"""
    if not feature_flags.is_world_building_enabled():
        raise HTTPException(
            status_code=404, 
            detail="World building feature is not available"
        )

# Authorization dependencies
async def get_verified_user(current_user: UserResponse = Depends(get_current_user)):
    """Get current user and verify they're authenticated"""
    await check_world_building_enabled()
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user

async def check_subscription_access(current_user: UserResponse = Depends(get_verified_user)):
    """Check if user has subscription access for world building"""
    subscription_check = await user_integration_service.check_subscription_limits(current_user.id)
    
    if not subscription_check.get("has_access", False):
        raise HTTPException(
            status_code=403,
            detail=f"Subscription required: {subscription_check.get('reason', 'Access denied')}"
        )
    
    return current_user

# ============================================================================
# 0. HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/health")
async def world_building_health():
    """Health check endpoint for world building feature"""
    try:
        # Check if feature is enabled
        feature_enabled = feature_flags.is_world_building_enabled()
        
        return {
            "feature_enabled": feature_enabled,
            "status": "ok" if feature_enabled else "disabled",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "feature_enabled": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# 1. DISCOVERY ENDPOINTS (MUST BE BEFORE /{world_id} ROUTES)
# ============================================================================

@router.get("/discover", response_model=WorldListResponse)
async def discover_worlds(
    language: Optional[str] = Query(None, description="Filter by language"),
    target_level: Optional[str] = Query(None, description="Filter by CEFR level"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """Browse public worlds with filtering - accessible to all users"""
    try:
        # Check if feature is enabled
        await check_world_building_enabled()
        
        request = WorldListRequest(
            language=language,
            target_level=target_level,
            genre=genre,
            limit=limit,
            offset=offset
        )
        
        # Only show public worlds in discovery
        worlds = await world_building_service.list_public_worlds(request)
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering worlds: {str(e)}")

@router.get("/search", response_model=WorldListResponse)
async def search_worlds(
    q: str = Query(..., description="Search query"),
    language: Optional[str] = Query(None, description="Filter by language"),
    target_level: Optional[str] = Query(None, description="Filter by CEFR level"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Search worlds with text query and filters"""
    try:
        worlds = await world_building_service.search_worlds(
            query=q,
            language=language,
            target_level=target_level,
            genre=genre,
            limit=limit,
            offset=offset
        )
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching worlds: {str(e)}")

@router.get("/featured", response_model=WorldListResponse)
async def get_featured_worlds(
    limit: int = Query(10, ge=1, le=50, description="Number of results")
):
    """Get featured worlds - accessible to all users"""
    try:
        # Check if feature is enabled
        await check_world_building_enabled()
        
        worlds = await world_building_service.get_featured_worlds(limit)
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting featured worlds: {str(e)}")

@router.get("/trending", response_model=WorldListResponse)
async def get_trending_worlds(
    limit: int = Query(10, ge=1, le=50, description="Number of results")
):
    """Get trending worlds based on recent activity - accessible to all users"""
    try:
        # Check if feature is enabled
        await check_world_building_enabled()
        
        worlds = await world_building_service.get_trending_worlds(limit)
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending worlds: {str(e)}")

# ============================================================================
# 2. WORLD MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("", response_model=StoryWorldResponse, status_code=201)
async def create_world(
    world_data: StoryWorldCreate,
    current_user: UserResponse = Depends(check_subscription_access)
):
    """Create a new collaborative story world"""
    try:
        # Set creator_id from authenticated user
        world_data.creator_id = current_user.id
        
        # Create the world
        world = await world_building_service.create_world(world_data)
        
        if not world:
            raise HTTPException(status_code=400, detail="Failed to create world")
        
        # Increment user's session usage
        await user_integration_service.increment_session_usage(current_user.id)
        
        return world
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating world: {str(e)}")

# Add optional authentication for world details - allows guest access to public worlds
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Union

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """Get current user if authenticated, otherwise return None"""
    await check_world_building_enabled()
    
    if not credentials:
        return None
    
    try:
        # Try to get user from token
        from auth import verify_token
        user_data = verify_token(credentials.credentials)
        if user_data:
            return UserResponse(**user_data)
    except:
        pass
    
    return None

@router.get("/{world_id}", response_model=StoryWorldResponse)
async def get_world(
    world_id: str = Path(..., description="World ID"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get details of a specific world - public worlds accessible to all users"""
    try:
        world = await world_building_service.get_world(world_id)
        
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        
        # Check privacy permissions
        if world.privacy_setting == "private":
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required for private worlds")
            
            if world.creator_id != current_user.id and current_user.id not in world.contributors:
                raise HTTPException(status_code=403, detail="Access denied to private world")
        
        return world
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving world: {str(e)}")

@router.put("/{world_id}", response_model=StoryWorldResponse)
async def update_world(
    world_update: StoryWorldUpdate,
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Update a world (creator only)"""
    try:
        # Get existing world to check permissions
        existing_world = await world_building_service.get_world(world_id)
        
        if not existing_world:
            raise HTTPException(status_code=404, detail="World not found")
        
        # Only creator can update
        if existing_world.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can update this world")
        
        # Update the world
        updated_world = await world_building_service.update_world(world_id, world_update)
        
        if not updated_world:
            raise HTTPException(status_code=400, detail="Failed to update world")
        
        return updated_world
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating world: {str(e)}")

@router.delete("/{world_id}", status_code=204)
async def delete_world(
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Delete a world (creator only)"""
    try:
        # Get existing world to check permissions
        existing_world = await world_building_service.get_world(world_id)
        
        if not existing_world:
            raise HTTPException(status_code=404, detail="World not found")
        
        # Only creator can delete
        if existing_world.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can delete this world")
        
        # Delete the world
        success = await world_building_service.delete_world(world_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete world")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting world: {str(e)}")

@router.post("/{world_id}/archive", response_model=StoryWorldResponse)
async def archive_world(
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Archive a world (creator only)"""
    try:
        # Get existing world to check permissions
        existing_world = await world_building_service.get_world(world_id)
        
        if not existing_world:
            raise HTTPException(status_code=404, detail="World not found")
        
        # Only creator can archive
        if existing_world.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can archive this world")
        
        # Archive the world
        archived_world = await world_building_service.update_world(
            world_id, 
            StoryWorldUpdate(status="archived")
        )
        
        if not archived_world:
            raise HTTPException(status_code=400, detail="Failed to archive world")
        
        return archived_world
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error archiving world: {str(e)}")

# ============================================================================
# 3. USER'S WORLDS ENDPOINTS
# ============================================================================

@router.get("/my-worlds", response_model=WorldListResponse)
async def get_my_worlds(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Get worlds created by the current user"""
    try:
        worlds = await world_building_service.get_user_created_worlds(
            user_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset
        )
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user worlds: {str(e)}")

@router.get("/contributing", response_model=WorldListResponse)
async def get_contributing_worlds(
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Get worlds the user is contributing to"""
    try:
        worlds = await world_building_service.get_user_contributing_worlds(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting contributing worlds: {str(e)}")

@router.get("/bookmarked", response_model=WorldListResponse)
async def get_bookmarked_worlds(
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Get worlds bookmarked by the user"""
    try:
        # This would require a bookmarks collection/field - placeholder for now
        worlds = await world_building_service.get_user_bookmarked_worlds(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return worlds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bookmarked worlds: {str(e)}")

# ============================================================================
# 4. COLLABORATION ENDPOINTS
# ============================================================================

@router.post("/{world_id}/join", response_model=StoryWorldResponse)
async def join_world(
    join_request: WorldJoinRequest,
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(check_subscription_access)
):
    """Join a world as a contributor"""
    try:
        world = await world_building_service.join_world(
            world_id=world_id,
            user_id=current_user.id,
            invitation_code=join_request.invitation_code
        )
        
        if not world:
            raise HTTPException(status_code=400, detail="Failed to join world")
        
        return world
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining world: {str(e)}")

@router.post("/{world_id}/leave", response_model=StoryWorldResponse)
async def leave_world(
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Leave a world (contributors only, not creator)"""
    try:
        world = await world_building_service.leave_world(
            world_id=world_id,
            user_id=current_user.id
        )
        
        if not world:
            raise HTTPException(status_code=400, detail="Failed to leave world")
        
        return world
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leaving world: {str(e)}")

@router.get("/{world_id}/queue")
async def get_collaboration_queue(
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Get collaboration queue for a world"""
    try:
        # Check if user has access to this world
        world = await world_building_service.get_world(world_id)
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        
        if (world.privacy_setting == "private" and 
            world.creator_id != current_user.id and 
            current_user.id not in world.contributors):
            raise HTTPException(status_code=403, detail="Access denied")
        
        queue = await world_building_service.get_collaboration_queue(world_id)
        return queue
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting queue: {str(e)}")

@router.post("/{world_id}/reserve-slot")
async def reserve_time_slot(
    slot_data: dict,  # Would need proper model for time slot reservation
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Reserve a time slot for contribution"""
    try:
        # Check if user is a contributor
        world = await world_building_service.get_world(world_id)
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        
        if (current_user.id != world.creator_id and 
            current_user.id not in world.contributors):
            raise HTTPException(status_code=403, detail="Must be a contributor to reserve slots")
        
        reservation = await world_building_service.reserve_collaboration_slot(
            world_id=world_id,
            user_id=current_user.id,
            slot_data=slot_data
        )
        
        return reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reserving slot: {str(e)}")

# ============================================================================
# 5. INVITATION ENDPOINTS
# ============================================================================

@router.post("/{world_id}/invite", response_model=WorldInvitationResponse)
async def create_invitation(
    invitation_data: WorldInvitationCreate,
    world_id: str = Path(..., description="World ID"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Create an invitation to join a world"""
    try:
        # Check if user can invite (creator or contributor with permission)
        world = await world_building_service.get_world(world_id)
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        
        if (current_user.id != world.creator_id and 
            current_user.id not in world.contributors):
            raise HTTPException(status_code=403, detail="Only contributors can create invitations")
        
        # Set the world_id and inviter_id
        invitation_data.world_id = world_id
        
        invitation = await world_building_service.create_invitation(
            invitation_data=invitation_data,
            inviter_id=current_user.id
        )
        
        if not invitation:
            raise HTTPException(status_code=400, detail="Failed to create invitation")
        
        return invitation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invitation: {str(e)}")

# Create separate router for invitation endpoints (different prefix)
invitation_router = APIRouter(prefix="/api/v2/invitations", tags=["World Building - Invitations"])

@invitation_router.get("/{code}", response_model=WorldInvitationResponse)
async def get_invitation_details(
    code: str = Path(..., description="Invitation code"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Get invitation details by code"""
    try:
        invitation = await world_building_service.get_invitation_by_code(code)
        
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found or expired")
        
        return invitation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting invitation: {str(e)}")

@invitation_router.post("/{code}/accept", response_model=StoryWorldResponse)
async def accept_invitation(
    code: str = Path(..., description="Invitation code"),
    current_user: UserResponse = Depends(check_subscription_access)
):
    """Accept an invitation to join a world"""
    try:
        world = await world_building_service.accept_invitation(
            invitation_code=code,
            user_id=current_user.id
        )
        
        if not world:
            raise HTTPException(status_code=400, detail="Failed to accept invitation")
        
        return world
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accepting invitation: {str(e)}")

@invitation_router.get("/my-invitations")
async def get_my_invitations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: UserResponse = Depends(get_verified_user)
):
    """Get invitations for the current user"""
    try:
        invitations = await world_building_service.get_user_invitations(
            user_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset
        )
        return invitations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting invitations: {str(e)}")

# Export both routers
__all__ = ["router", "invitation_router"]
