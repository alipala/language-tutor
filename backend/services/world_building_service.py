import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from database import database
from models.world_building_models import (
    StoryWorldInDB, StoryWorldCreate, StoryWorldUpdate, StoryWorldResponse,
    StoryContributionInDB, StoryContributionCreate, StoryContributionResponse,
    WorldInvitationInDB, WorldInvitationCreate, WorldInvitationResponse,
    CollaborationQueueInDB, CollaborationQueueCreate, CollaborationQueueResponse,
    WorldCheckpointInDB, WorldCheckpointCreate, WorldCheckpointResponse,
    WorldListRequest, WorldListResponse, ContributionListRequest, ContributionListResponse,
    WorldStatusEnum, InvitationStatusEnum, QueueStatusEnum, ContributionOrderEnum,
    WorldState, LearningObjectives, CollaborationSettings, Statistics
)

class WorldBuildingService:
    """Service class for managing collaborative world building functionality"""
    
    def __init__(self):
        # Initialize collections
        self.story_worlds: AsyncIOMotorCollection = database.story_worlds
        self.story_contributions: AsyncIOMotorCollection = database.story_contributions
        self.world_invitations: AsyncIOMotorCollection = database.world_invitations
        self.collaboration_queue: AsyncIOMotorCollection = database.collaboration_queue
        self.world_checkpoints: AsyncIOMotorCollection = database.world_checkpoints
        
    async def initialize_indexes(self):
        """Create all required indexes for world building collections"""
        try:
            print("🔧 [WORLD_BUILDING] Creating database indexes...")
            
            # Story worlds indexes
            await self.story_worlds.create_index([
                ("language", 1),
                ("target_level", 1),
                ("status", 1),
                ("created_at", -1)
            ], name="language_level_status_created")
            
            await self.story_worlds.create_index([
                ("creator_id", 1),
                ("status", 1)
            ], name="creator_status")
            
            await self.story_worlds.create_index([
                ("featured", 1),
                ("status", 1),
                ("created_at", -1)
            ], name="featured_status_created")
            
            await self.story_worlds.create_index([
                ("genre", 1),
                ("language", 1)
            ], name="genre_language")
            
            # Story contributions indexes
            await self.story_contributions.create_index([
                ("world_id", 1),
                ("created_at", -1)
            ], name="world_created")
            
            await self.story_contributions.create_index([
                ("contributor_id", 1),
                ("created_at", -1)
            ], name="contributor_created")
            
            await self.story_contributions.create_index([
                ("world_id", 1),
                ("session_number", 1)
            ], name="world_session", unique=True)
            
            # World invitations indexes with TTL
            await self.world_invitations.create_index(
                "expires_at", 
                expireAfterSeconds=0,
                name="invitation_ttl"
            )
            
            await self.world_invitations.create_index([
                ("invitation_code", 1)
            ], name="invitation_code", unique=True)
            
            await self.world_invitations.create_index([
                ("world_id", 1),
                ("status", 1)
            ], name="world_invitation_status")
            
            # Collaboration queue indexes
            await self.collaboration_queue.create_index([
                ("world_id", 1),
                ("scheduled_start", 1)
            ], name="world_scheduled")
            
            await self.collaboration_queue.create_index([
                ("scheduled_contributor_id", 1),
                ("status", 1)
            ], name="contributor_status")
            
            # World checkpoints indexes
            await self.world_checkpoints.create_index([
                ("world_id", 1),
                ("checkpoint_number", 1)
            ], name="world_checkpoint", unique=True)
            
            print("✅ [WORLD_BUILDING] Database indexes created successfully")
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error creating indexes: {str(e)}")
            raise
    
    def generate_invitation_code(self) -> str:
        """Generate a unique 8-character invitation code"""
        # Use uppercase letters and numbers for readability
        alphabet = string.ascii_uppercase + string.digits
        # Exclude confusing characters
        alphabet = alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
        return ''.join(secrets.choice(alphabet) for _ in range(8))
    
    async def create_world(self, world_data: StoryWorldCreate) -> StoryWorldResponse:
        """Create a new story world"""
        try:
            # Convert creator_id to ObjectId (it's already set in world_data by the route)
            creator_object_id = ObjectId(world_data.creator_id)
            
            # Convert flattened structure to nested structure for database
            world_state = WorldState(
                current_plot_point=world_data.current_plot_point,
                active_characters=world_data.characters,
                locations=world_data.locations,
                important_items=world_data.important_items
            )
            
            learning_objectives = LearningObjectives(
                primary_focus=world_data.primary_focus,
                target_structures=world_data.target_structures,
                vocabulary_themes=world_data.vocabulary_themes
            )
            
            collaboration_settings = CollaborationSettings(
                max_contributors=world_data.max_contributors,
                session_duration_minutes=world_data.session_duration_minutes,
                requires_approval=world_data.requires_approval,
                contribution_order=ContributionOrderEnum.SEQUENTIAL
            )
            
            # Create world document with nested structure
            world_doc = StoryWorldInDB(
                title=world_data.title,
                description=world_data.description,
                creator_id=creator_object_id,
                language=world_data.language,
                target_level=world_data.target_level,
                genre=world_data.genre,
                privacy_setting=world_data.privacy_setting,
                world_state=world_state,
                learning_objectives=learning_objectives,
                collaboration_settings=collaboration_settings,
                statistics=Statistics(),
                contributors=[creator_object_id],  # Creator is automatically a contributor
                status=world_data.status,
                tags=world_data.tags,
                featured=False
            )
            
            # Insert into database
            result = await self.story_worlds.insert_one(world_doc.dict())
            
            # Retrieve the created world
            created_world = await self.story_worlds.find_one({"_id": result.inserted_id})
            
            # Convert ObjectId to string for response model while preserving nested structures
            world_dict = dict(created_world)
            # Convert _id to id since StoryWorldResponse now expects id field
            world_dict["id"] = str(world_dict["_id"])
            del world_dict["_id"]  # Remove the original _id
            world_dict["creator_id"] = str(world_dict["creator_id"])
            world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
            
            print(f"✅ [WORLD_BUILDING] Created world '{world_data.title}' with ID: {result.inserted_id}")
            
            return StoryWorldResponse(**world_dict)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error creating world: {str(e)}")
            raise
    
    async def get_world(self, world_id: str, user_id: Optional[str] = None) -> Optional[StoryWorldResponse]:
        """Get a story world by ID with privacy checks"""
        try:
            world = await self.story_worlds.find_one({"_id": ObjectId(world_id)})
            
            if not world:
                return None
            
            # Check privacy settings
            if world.get("privacy_setting") == "private":
                # Only creator and contributors can view private worlds
                if not user_id:
                    return None
                
                user_object_id = ObjectId(user_id)
                if (world.get("creator_id") != user_object_id and 
                    user_object_id not in world.get("contributors", [])):
                    return None
            
            # Convert ObjectId to string for response model while preserving nested structures
            world_dict = dict(world)
            world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
            del world_dict["_id"]  # Remove the original _id
            world_dict["creator_id"] = str(world_dict["creator_id"])
            world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
            
            return StoryWorldResponse(**world_dict)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting world: {str(e)}")
            raise
    
    async def list_worlds(self, request: WorldListRequest, user_id: Optional[str] = None) -> WorldListResponse:
        """List story worlds with filtering and pagination"""
        try:
            # Build query filter
            query_filter = {}
            
            if request.language:
                query_filter["language"] = request.language.value
            
            if request.target_level:
                query_filter["target_level"] = request.target_level.value
            
            if request.genre:
                query_filter["genre"] = request.genre.value
            
            if request.status:
                query_filter["status"] = request.status.value
            else:
                # Default to active worlds only
                query_filter["status"] = WorldStatusEnum.ACTIVE.value
            
            if request.featured_only:
                query_filter["featured"] = True
            
            # Privacy filter - exclude private worlds unless user is creator/contributor
            if user_id:
                user_object_id = ObjectId(user_id)
                query_filter["$or"] = [
                    {"privacy_setting": {"$ne": "private"}},
                    {"creator_id": user_object_id},
                    {"contributors": user_object_id}
                ]
            else:
                query_filter["privacy_setting"] = {"$ne": "private"}
            
            # Get total count
            total_count = await self.story_worlds.count_documents(query_filter)
            
            # Get worlds with pagination
            cursor = self.story_worlds.find(query_filter).sort("created_at", -1)
            cursor = cursor.skip(request.offset).limit(request.limit)
            
            worlds = await cursor.to_list(request.limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                # Convert ObjectId to string for response model while preserving nested structures
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
                del world_dict["_id"]  # Remove the original _id
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                
                # Add creator name by looking up the user
                creator_id = world_dict["creator_id"]
                try:
                    # Try to find user by string ID first, then ObjectId
                    user = await database.users.find_one({"_id": creator_id})
                    if not user:
                        user = await database.users.find_one({"_id": ObjectId(creator_id)})
                    
                    world_dict["creator_name"] = user.get("name", "Anonymous") if user else "Anonymous"
                except Exception as e:
                    print(f"⚠️ [WORLD_BUILDING] Error getting creator name: {str(e)}")
                    world_dict["creator_name"] = "Anonymous"
                
                world_responses.append(StoryWorldResponse(**world_dict))
            
            has_more = (request.offset + len(worlds)) < total_count
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error listing worlds: {str(e)}")
            raise
    
    
    async def create_invitation(self, invitation_data: WorldInvitationCreate, inviter_id: str) -> WorldInvitationResponse:
        """Create a world invitation"""
        try:
            # Check if world exists and user has permission to invite
            world = await self.story_worlds.find_one({
                "_id": ObjectId(invitation_data.world_id),
                "$or": [
                    {"creator_id": ObjectId(inviter_id)},
                    {"contributors": ObjectId(inviter_id)}
                ]
            })
            
            if not world:
                raise ValueError("World not found or no permission to invite")
            
            # Generate unique invitation code
            invitation_code = self.generate_invitation_code()
            
            # Ensure code is unique
            while await self.world_invitations.find_one({"invitation_code": invitation_code}):
                invitation_code = self.generate_invitation_code()
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(hours=invitation_data.expires_in_hours)
            
            # Create invitation document
            invitation_doc = WorldInvitationInDB(
                world_id=ObjectId(invitation_data.world_id),
                inviter_id=ObjectId(inviter_id),
                invitee_email=invitation_data.invitee_email,
                invitee_id=ObjectId(invitation_data.invitee_id) if invitation_data.invitee_id else None,
                invitation_code=invitation_code,
                invitation_type=invitation_data.invitation_type,
                message=invitation_data.message,
                expires_at=expires_at
            )
            
            # Insert invitation
            result = await self.world_invitations.insert_one(invitation_doc.dict())
            
            # Return created invitation
            created_invitation = await self.world_invitations.find_one({"_id": result.inserted_id})
            
            print(f"✅ [WORLD_BUILDING] Created invitation with code: {invitation_code}")
            
            return WorldInvitationResponse(**created_invitation)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error creating invitation: {str(e)}")
            raise
    
    async def accept_invitation(self, invitation_code: str, user_id: str) -> Tuple[bool, str]:
        """Accept a world invitation"""
        try:
            # Find the invitation
            invitation = await self.world_invitations.find_one({
                "invitation_code": invitation_code,
                "status": InvitationStatusEnum.PENDING.value,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not invitation:
                return False, "Invalid or expired invitation code"
            
            # Check if user is already a contributor
            world = await self.story_worlds.find_one({"_id": invitation["world_id"]})
            if not world:
                return False, "World no longer exists"
            
            user_object_id = ObjectId(user_id)
            if user_object_id in world.get("contributors", []):
                return False, "You are already a contributor to this world"
            
            # Check if world has reached max contributors
            max_contributors = world.get("collaboration_settings", {}).get("max_contributors", 10)
            current_contributors = len(world.get("contributors", []))
            
            if current_contributors >= max_contributors:
                return False, "World has reached maximum number of contributors"
            
            # Add user to contributors
            await self.story_worlds.update_one(
                {"_id": invitation["world_id"]},
                {
                    "$addToSet": {"contributors": user_object_id},
                    "$inc": {"statistics.total_contributors": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Mark invitation as accepted
            await self.world_invitations.update_one(
                {"_id": invitation["_id"]},
                {
                    "$set": {
                        "status": InvitationStatusEnum.ACCEPTED.value,
                        "accepted_at": datetime.utcnow()
                    }
                }
            )
            
            print(f"✅ [WORLD_BUILDING] User {user_id} accepted invitation to world {invitation['world_id']}")
            
            return True, "Successfully joined the world!"
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error accepting invitation: {str(e)}")
            return False, f"Error accepting invitation: {str(e)}"
    
    async def create_contribution(self, contribution_data: StoryContributionCreate, contributor_id: str) -> StoryContributionResponse:
        """Create a new story contribution"""
        try:
            # Verify user is a contributor to the world
            world = await self.story_worlds.find_one({
                "_id": ObjectId(contribution_data.world_id),
                "contributors": ObjectId(contributor_id)
            })
            
            if not world:
                raise ValueError("World not found or user is not a contributor")
            
            # Get next session number
            last_contribution = await self.story_contributions.find_one(
                {"world_id": ObjectId(contribution_data.world_id)},
                sort=[("session_number", -1)]
            )
            
            session_number = (last_contribution.get("session_number", 0) + 1) if last_contribution else 1
            
            # Create contribution document
            contribution_doc = StoryContributionInDB(
                **contribution_data.dict(),
                world_id=ObjectId(contribution_data.world_id),
                contributor_id=ObjectId(contributor_id),
                session_number=session_number
            )
            
            # Insert contribution
            result = await self.story_contributions.insert_one(contribution_doc.dict())
            
            # Update world statistics and last contribution time
            await self.story_worlds.update_one(
                {"_id": ObjectId(contribution_data.world_id)},
                {
                    "$inc": {"statistics.total_sessions": 1},
                    "$set": {
                        "last_contribution_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Return created contribution
            created_contribution = await self.story_contributions.find_one({"_id": result.inserted_id})
            
            print(f"✅ [WORLD_BUILDING] Created contribution #{session_number} for world {contribution_data.world_id}")
            
            return StoryContributionResponse(**created_contribution)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error creating contribution: {str(e)}")
            raise
    
    async def list_contributions(self, request: ContributionListRequest, user_id: Optional[str] = None) -> ContributionListResponse:
        """List contributions for a world"""
        try:
            # Check if user has access to the world
            if user_id:
                world = await self.get_world(request.world_id, user_id)
                if not world:
                    raise ValueError("World not found or access denied")
            
            # Build query
            query_filter = {"world_id": ObjectId(request.world_id)}
            
            # Get total count
            total_count = await self.story_contributions.count_documents(query_filter)
            
            # Get contributions with pagination
            cursor = self.story_contributions.find(query_filter).sort("created_at", -1)
            cursor = cursor.skip(request.offset).limit(request.limit)
            
            contributions = await cursor.to_list(request.limit)
            
            # Convert to response models
            contribution_responses = [StoryContributionResponse(**contrib) for contrib in contributions]
            
            has_more = (request.offset + len(contributions)) < total_count
            
            return ContributionListResponse(
                contributions=contribution_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error listing contributions: {str(e)}")
            raise
    
    async def create_checkpoint(self, checkpoint_data: WorldCheckpointCreate, user_id: str) -> WorldCheckpointResponse:
        """Create a world checkpoint (only by creator)"""
        try:
            # Verify user is the creator
            world = await self.story_worlds.find_one({
                "_id": ObjectId(checkpoint_data.world_id),
                "creator_id": ObjectId(user_id)
            })
            
            if not world:
                raise ValueError("World not found or user is not the creator")
            
            # Create checkpoint document
            checkpoint_doc = WorldCheckpointInDB(
                world_id=ObjectId(checkpoint_data.world_id),
                checkpoint_number=checkpoint_data.checkpoint_number,
                world_state_snapshot=checkpoint_data.world_state_snapshot,
                contribution_count=checkpoint_data.contribution_count
            )
            
            # Insert checkpoint
            result = await self.world_checkpoints.insert_one(checkpoint_doc.dict())
            
            # Return created checkpoint
            created_checkpoint = await self.world_checkpoints.find_one({"_id": result.inserted_id})
            
            print(f"✅ [WORLD_BUILDING] Created checkpoint #{checkpoint_data.checkpoint_number} for world {checkpoint_data.world_id}")
            
            return WorldCheckpointResponse(**created_checkpoint)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error creating checkpoint: {str(e)}")
            raise
    
    async def get_user_worlds(self, user_id: str, created_only: bool = False) -> List[StoryWorldResponse]:
        """Get worlds associated with a user"""
        try:
            user_object_id = ObjectId(user_id)
            
            if created_only:
                # Only worlds created by the user
                query_filter = {"creator_id": user_object_id}
            else:
                # All worlds where user is creator or contributor
                query_filter = {
                    "$or": [
                        {"creator_id": user_object_id},
                        {"contributors": user_object_id}
                    ]
                }
            
            worlds = await self.story_worlds.find(query_filter).sort("updated_at", -1).to_list(100)
            
            return [StoryWorldResponse(**world) for world in worlds]
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting user worlds: {str(e)}")
            raise
    
    async def get_world_analytics(self, world_id: str, user_id: str) -> Dict[str, Any]:
        """Get analytics for a world (creator only)"""
        try:
            # Verify user is the creator
            world = await self.story_worlds.find_one({
                "_id": ObjectId(world_id),
                "creator_id": ObjectId(user_id)
            })
            
            if not world:
                raise ValueError("World not found or user is not the creator")
            
            # Get contribution statistics
            contributions = await self.story_contributions.find({"world_id": ObjectId(world_id)}).to_list(1000)
            
            # Calculate analytics
            total_contributions = len(contributions)
            unique_contributors = len(set(str(contrib["contributor_id"]) for contrib in contributions))
            
            if contributions:
                avg_duration = sum(contrib.get("duration_seconds", 0) for contrib in contributions) / total_contributions
                total_words = sum(contrib.get("learning_metrics", {}).get("words_spoken", 0) for contrib in contributions)
            else:
                avg_duration = 0
                total_words = 0
            
            # Get contributor breakdown
            contributor_stats = {}
            for contrib in contributions:
                contributor_id = str(contrib["contributor_id"])
                if contributor_id not in contributor_stats:
                    contributor_stats[contributor_id] = {
                        "contributions": 0,
                        "total_words": 0,
                        "total_duration": 0
                    }
                
                contributor_stats[contributor_id]["contributions"] += 1
                contributor_stats[contributor_id]["total_words"] += contrib.get("learning_metrics", {}).get("words_spoken", 0)
                contributor_stats[contributor_id]["total_duration"] += contrib.get("duration_seconds", 0)
            
            return {
                "world_id": world_id,
                "total_contributions": total_contributions,
                "unique_contributors": unique_contributors,
                "average_contribution_duration": avg_duration,
                "total_words_spoken": total_words,
                "contributor_breakdown": contributor_stats,
                "world_statistics": world.get("statistics", {}),
                "created_at": world.get("created_at"),
                "last_contribution_at": world.get("last_contribution_at")
            }
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting world analytics: {str(e)}")
            raise

    # Missing methods that routes are calling
    async def list_public_worlds(self, request: WorldListRequest) -> WorldListResponse:
        """List public worlds for discovery"""
        try:
            # Build query filter for public worlds only
            query_filter = {"privacy_setting": {"$ne": "private"}}
            
            if request.language:
                query_filter["language"] = request.language
            
            if request.target_level:
                query_filter["target_level"] = request.target_level
            
            if request.genre:
                query_filter["genre"] = request.genre
            
            # Default to active worlds only
            query_filter["status"] = "active"
            
            # Get total count
            total_count = await self.story_worlds.count_documents(query_filter)
            
            # Get worlds with pagination
            cursor = self.story_worlds.find(query_filter).sort("created_at", -1)
            cursor = cursor.skip(request.offset).limit(request.limit)
            
            worlds = await cursor.to_list(request.limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                # Convert ObjectId to string for response model while preserving nested structures
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
                del world_dict["_id"]  # Remove the original _id
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                
                # Add creator name by looking up the user
                creator_id = world_dict["creator_id"]
                try:
                    # Try to find user by ObjectId first (most common), then string
                    user = None
                    try:
                        user = await database.users.find_one({"_id": ObjectId(creator_id)})
                    except:
                        pass
                    
                    if not user:
                        user = await database.users.find_one({"_id": creator_id})
                    
                    world_dict["creator_name"] = user.get("name", "Anonymous") if user else "Anonymous"
                except Exception as e:
                    print(f"⚠️ [WORLD_BUILDING] Error getting creator name: {str(e)}")
                    world_dict["creator_name"] = "Anonymous"
                
                world_responses.append(StoryWorldResponse(**world_dict))
            
            has_more = (request.offset + len(worlds)) < total_count
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error listing public worlds: {str(e)}")
            raise

    async def search_worlds(self, query: str, language: Optional[str] = None, 
                          target_level: Optional[str] = None, genre: Optional[str] = None,
                          limit: int = 20, offset: int = 0) -> WorldListResponse:
        """Search worlds with text query"""
        try:
            # Build search filter
            search_filter = {
                "privacy_setting": {"$ne": "private"},
                "status": "active",
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"tags": {"$regex": query, "$options": "i"}}
                ]
            }
            
            if language:
                search_filter["language"] = language
            
            if target_level:
                search_filter["target_level"] = target_level
            
            if genre:
                search_filter["genre"] = genre
            
            # Get total count
            total_count = await self.story_worlds.count_documents(search_filter)
            
            # Get worlds with pagination
            cursor = self.story_worlds.find(search_filter).sort("created_at", -1)
            cursor = cursor.skip(offset).limit(limit)
            
            worlds = await cursor.to_list(limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                # Convert ObjectId to string for response model while preserving nested structures
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
                del world_dict["_id"]  # Remove the original _id
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                world_responses.append(StoryWorldResponse(**world_dict))
            
            has_more = (offset + len(worlds)) < total_count
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error searching worlds: {str(e)}")
            raise

    async def get_featured_worlds(self, limit: int = 10) -> WorldListResponse:
        """Get featured worlds"""
        try:
            query_filter = {
                "featured": True,
                "status": "active",
                "privacy_setting": {"$ne": "private"}
            }
            
            # Get total count
            total_count = await self.story_worlds.count_documents(query_filter)
            
            # Get featured worlds
            cursor = self.story_worlds.find(query_filter).sort("created_at", -1).limit(limit)
            worlds = await cursor.to_list(limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                # Convert ObjectId to string for response model while preserving nested structures
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
                del world_dict["_id"]  # Remove the original _id
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                world_responses.append(StoryWorldResponse(**world_dict))
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=len(worlds) < total_count
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting featured worlds: {str(e)}")
            raise

    async def get_trending_worlds(self, limit: int = 10) -> WorldListResponse:
        """Get trending worlds based on recent activity"""
        try:
            # Get worlds with recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            query_filter = {
                "status": "active",
                "privacy_setting": {"$ne": "private"},
                "last_contribution_at": {"$gte": seven_days_ago}
            }
            
            # Get total count
            total_count = await self.story_worlds.count_documents(query_filter)
            
            # Get trending worlds sorted by recent activity
            cursor = self.story_worlds.find(query_filter).sort("last_contribution_at", -1).limit(limit)
            worlds = await cursor.to_list(limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                # Convert ObjectId to string for response model while preserving nested structures
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
                del world_dict["_id"]  # Remove the original _id
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                world_responses.append(StoryWorldResponse(**world_dict))
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=len(worlds) < total_count
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting trending worlds: {str(e)}")
            raise

    # Additional missing methods that routes are calling
    async def update_world(self, world_id: str, update_data: StoryWorldUpdate) -> Optional[StoryWorldResponse]:
        """Update a story world - simplified version for route compatibility"""
        try:
            # Prepare update data
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update the world
            result = await self.story_worlds.update_one(
                {"_id": ObjectId(world_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count == 0:
                return None
            
            # Return updated world
            updated_world = await self.story_worlds.find_one({"_id": ObjectId(world_id)})
            if not updated_world:
                return None
                
            # Convert ObjectId to string for response model while preserving nested structures
            world_dict = dict(updated_world)
            world_dict["id"] = str(world_dict["_id"])  # Use 'id' instead of '_id'
            del world_dict["_id"]  # Remove the original _id
            world_dict["creator_id"] = str(world_dict["creator_id"])
            world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
            
            return StoryWorldResponse(**world_dict)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error updating world: {str(e)}")
            raise

    async def delete_world(self, world_id: str) -> bool:
        """Delete a story world"""
        try:
            result = await self.story_worlds.delete_one({"_id": ObjectId(world_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error deleting world: {str(e)}")
            raise

    async def get_user_created_worlds(self, user_id: str, status: Optional[str] = None, 
                                    limit: int = 20, offset: int = 0) -> WorldListResponse:
        """Get worlds created by a specific user"""
        try:
            from bson import ObjectId
            
            # Handle both string and ObjectId formats for creator_id
            query_filter = {
                "$or": [
                    {"creator_id": user_id},  # String format
                    {"creator_id": ObjectId(user_id)}  # ObjectId format
                ]
            }
            
            if status:
                query_filter["status"] = status
            
            # Get total count
            total_count = await self.story_worlds.count_documents(query_filter)
            
            # Get worlds with pagination
            cursor = self.story_worlds.find(query_filter).sort("created_at", -1)
            cursor = cursor.skip(offset).limit(limit)
            
            worlds = await cursor.to_list(limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])
                del world_dict["_id"]
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                
                # Add creator name by looking up the user
                creator_id = world_dict["creator_id"]
                try:
                    from database import database
                    from bson import ObjectId
                    
                    # Try to find user by ObjectId first (most common), then string
                    user = None
                    try:
                        user = await database.users.find_one({"_id": ObjectId(creator_id)})
                    except:
                        pass
                    
                    if not user:
                        user = await database.users.find_one({"_id": creator_id})
                    
                    world_dict["creator_name"] = user.get("name", "Anonymous") if user else "Anonymous"
                except Exception as e:
                    print(f"⚠️ [WORLD_BUILDING] Error getting creator name: {str(e)}")
                    world_dict["creator_name"] = "Anonymous"
                
                world_responses.append(StoryWorldResponse(**world_dict))
            
            has_more = (offset + len(worlds)) < total_count
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting user created worlds: {str(e)}")
            raise

    async def get_user_contributing_worlds(self, user_id: str, limit: int = 20, offset: int = 0) -> WorldListResponse:
        """Get worlds the user is contributing to"""
        try:
            query_filter = {
                "contributors": ObjectId(user_id),
                "creator_id": {"$ne": ObjectId(user_id)}  # Exclude worlds they created
            }
            
            # Get total count
            total_count = await self.story_worlds.count_documents(query_filter)
            
            # Get worlds with pagination
            cursor = self.story_worlds.find(query_filter).sort("updated_at", -1)
            cursor = cursor.skip(offset).limit(limit)
            
            worlds = await cursor.to_list(limit)
            
            # Convert to response models with proper ObjectId handling
            world_responses = []
            for world in worlds:
                world_dict = dict(world)
                world_dict["id"] = str(world_dict["_id"])
                del world_dict["_id"]
                world_dict["creator_id"] = str(world_dict["creator_id"])
                world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
                world_responses.append(StoryWorldResponse(**world_dict))
            
            has_more = (offset + len(worlds)) < total_count
            
            return WorldListResponse(
                worlds=world_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting user contributing worlds: {str(e)}")
            raise

    async def get_user_bookmarked_worlds(self, user_id: str, limit: int = 20, offset: int = 0) -> WorldListResponse:
        """Get worlds bookmarked by the user - placeholder implementation"""
        try:
            # This would require a bookmarks collection/field - returning empty for now
            return WorldListResponse(
                worlds=[],
                total_count=0,
                has_more=False
            )
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting user bookmarked worlds: {str(e)}")
            raise

    async def join_world(self, world_id: str, user_id: str, invitation_code: Optional[str] = None) -> Optional[StoryWorldResponse]:
        """Join a world as a contributor"""
        try:
            # Check if world exists
            world = await self.story_worlds.find_one({"_id": ObjectId(world_id)})
            if not world:
                return None
            
            user_object_id = ObjectId(user_id)
            
            # Check if user is already a contributor
            if user_object_id in world.get("contributors", []):
                return None  # Already a contributor
            
            # Check if world has reached max contributors
            max_contributors = world.get("max_contributors", 10)
            current_contributors = len(world.get("contributors", []))
            
            if current_contributors >= max_contributors:
                return None  # World is full
            
            # Add user to contributors
            await self.story_worlds.update_one(
                {"_id": ObjectId(world_id)},
                {
                    "$addToSet": {"contributors": user_object_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Return updated world
            updated_world = await self.story_worlds.find_one({"_id": ObjectId(world_id)})
            
            # Convert ObjectId to string for response model
            world_dict = dict(updated_world)
            world_dict["id"] = str(world_dict["_id"])
            del world_dict["_id"]
            world_dict["creator_id"] = str(world_dict["creator_id"])
            world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
            
            return StoryWorldResponse(**world_dict)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error joining world: {str(e)}")
            raise

    async def leave_world(self, world_id: str, user_id: str) -> Optional[StoryWorldResponse]:
        """Leave a world (contributors only, not creator)"""
        try:
            # Check if world exists and user is not the creator
            world = await self.story_worlds.find_one({
                "_id": ObjectId(world_id),
                "creator_id": {"$ne": ObjectId(user_id)}
            })
            
            if not world:
                return None
            
            # Remove user from contributors
            await self.story_worlds.update_one(
                {"_id": ObjectId(world_id)},
                {
                    "$pull": {"contributors": ObjectId(user_id)},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Return updated world
            updated_world = await self.story_worlds.find_one({"_id": ObjectId(world_id)})
            
            # Convert ObjectId to string for response model
            world_dict = dict(updated_world)
            world_dict["id"] = str(world_dict["_id"])
            del world_dict["_id"]
            world_dict["creator_id"] = str(world_dict["creator_id"])
            world_dict["contributors"] = [str(contrib_id) for contrib_id in world_dict.get("contributors", [])]
            
            return StoryWorldResponse(**world_dict)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error leaving world: {str(e)}")
            raise

    async def get_collaboration_queue(self, world_id: str) -> Dict[str, Any]:
        """Get collaboration queue for a world - placeholder implementation"""
        try:
            # This would require proper queue implementation - returning basic structure for now
            return {
                "world_id": world_id,
                "queue": [],
                "current_contributor": None,
                "next_scheduled": None
            }
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting collaboration queue: {str(e)}")
            raise

    async def reserve_collaboration_slot(self, world_id: str, user_id: str, slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reserve a collaboration slot - placeholder implementation"""
        try:
            # This would require proper queue implementation - returning basic structure for now
            return {
                "world_id": world_id,
                "user_id": user_id,
                "slot_data": slot_data,
                "reserved_at": datetime.utcnow().isoformat(),
                "status": "reserved"
            }
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error reserving collaboration slot: {str(e)}")
            raise


    async def get_invitation_by_code(self, code: str) -> Optional[WorldInvitationResponse]:
        """Get invitation by code"""
        try:
            invitation = await self.world_invitations.find_one({
                "invitation_code": code,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not invitation:
                return None
            
            # Convert ObjectId to string for response
            invitation_dict = dict(invitation)
            invitation_dict["id"] = str(invitation_dict["_id"])
            del invitation_dict["_id"]
            invitation_dict["world_id"] = str(invitation_dict["world_id"])
            invitation_dict["inviter_id"] = str(invitation_dict["inviter_id"])
            
            return WorldInvitationResponse(**invitation_dict)
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting invitation by code: {str(e)}")
            raise


    async def get_user_invitations(self, user_id: str, status: Optional[str] = None, 
                                 limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get invitations for a user - placeholder implementation"""
        try:
            # This would require proper invitation implementation - returning basic structure for now
            return {
                "invitations": [],
                "total_count": 0,
                "has_more": False
            }
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting user invitations: {str(e)}")
            raise

# Global service instance
world_building_service = WorldBuildingService()
