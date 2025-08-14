from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import logging
from bson import ObjectId
from database import database
from models.world_building_models import (
    CollaborationQueueCreate, CollaborationQueueInDB, CollaborationQueueResponse,
    QueueStatusEnum
)

logger = logging.getLogger(__name__)

class QueueService:
    """Service for managing collaboration queue and turn scheduling"""
    
    @classmethod
    async def get_queue_status(cls, world_id: str, user_id: str) -> Dict[str, Any]:
        """Get user's queue position and status for a world"""
        try:
            # Get world details
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return {"error": "World not found"}
            
            collaboration_settings = world.get("collaboration_settings", {})
            contribution_order = collaboration_settings.get("contribution_order", "sequential")
            
            if contribution_order == "sequential":
                return await cls._get_sequential_queue_status(world_id, user_id, world)
            elif contribution_order == "scheduled":
                return await cls._get_scheduled_queue_status(world_id, user_id)
            else:  # random
                return {
                    "queue_type": "random",
                    "can_contribute": True,
                    "message": "Anyone can contribute at any time",
                    "your_turn": True,
                    "position": 0,
                    "estimated_wait_minutes": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {"error": "Error getting queue status"}
    
    @classmethod
    async def _get_sequential_queue_status(
        cls, 
        world_id: str, 
        user_id: str, 
        world: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get queue status for sequential contribution order"""
        try:
            contributors = world.get("contributors", [])
            if ObjectId(user_id) not in contributors:
                return {"error": "You are not a contributor to this world"}
            
            # Get the last contribution to determine current turn
            last_contribution = await database["story_contributions"].find_one(
                {"world_id": ObjectId(world_id)},
                sort=[("created_at", -1)]
            )
            
            current_contributor_index = 0
            if last_contribution:
                last_contributor_id = last_contribution.get("contributor_id")
                try:
                    current_index = contributors.index(last_contributor_id)
                    current_contributor_index = (current_index + 1) % len(contributors)
                except (ValueError, IndexError):
                    current_contributor_index = 0
            
            current_contributor = contributors[current_contributor_index]
            user_index = contributors.index(ObjectId(user_id))
            
            # Calculate position in queue
            if current_contributor == ObjectId(user_id):
                position = 0
                your_turn = True
                message = "It's your turn to contribute!"
            else:
                if user_index > current_contributor_index:
                    position = user_index - current_contributor_index
                else:
                    position = len(contributors) - current_contributor_index + user_index
                
                your_turn = False
                message = f"You are #{position} in the queue"
            
            # Estimate wait time based on session duration
            session_duration = world.get("collaboration_settings", {}).get("session_duration_minutes", 10)
            estimated_wait_minutes = position * session_duration
            
            # Get current contributor info
            current_contributor_info = None
            if current_contributor != ObjectId(user_id):
                contributor_user = await database["users"].find_one({"_id": current_contributor})
                if contributor_user:
                    current_contributor_info = {
                        "id": str(current_contributor),
                        "name": contributor_user.get("name", "Unknown"),
                        "email": contributor_user.get("email", "")
                    }
            
            return {
                "queue_type": "sequential",
                "can_contribute": your_turn,
                "your_turn": your_turn,
                "position": position,
                "total_contributors": len(contributors),
                "estimated_wait_minutes": estimated_wait_minutes,
                "message": message,
                "current_contributor": current_contributor_info,
                "session_duration_minutes": session_duration
            }
            
        except Exception as e:
            logger.error(f"Error getting sequential queue status: {str(e)}")
            return {"error": "Error getting queue status"}
    
    @classmethod
    async def _get_scheduled_queue_status(cls, world_id: str, user_id: str) -> Dict[str, Any]:
        """Get queue status for scheduled contribution order"""
        try:
            now = datetime.utcnow()
            
            # Check if user has an active slot
            active_slot = await database["collaboration_queue"].find_one({
                "world_id": ObjectId(world_id),
                "scheduled_contributor_id": ObjectId(user_id),
                "status": QueueStatusEnum.ACTIVE,
                "scheduled_start": {"$lte": now},
                "scheduled_end": {"$gte": now}
            })
            
            if active_slot:
                remaining_minutes = int((active_slot["scheduled_end"] - now).total_seconds() / 60)
                return {
                    "queue_type": "scheduled",
                    "can_contribute": True,
                    "your_turn": True,
                    "position": 0,
                    "message": f"Your scheduled slot is active! {remaining_minutes} minutes remaining",
                    "slot_end": active_slot["scheduled_end"],
                    "remaining_minutes": remaining_minutes
                }
            
            # Check for upcoming slots
            upcoming_slot = await database["collaboration_queue"].find_one({
                "world_id": ObjectId(world_id),
                "scheduled_contributor_id": ObjectId(user_id),
                "status": QueueStatusEnum.UPCOMING,
                "scheduled_start": {"$gt": now}
            }, sort=[("scheduled_start", 1)])
            
            if upcoming_slot:
                wait_minutes = int((upcoming_slot["scheduled_start"] - now).total_seconds() / 60)
                return {
                    "queue_type": "scheduled",
                    "can_contribute": False,
                    "your_turn": False,
                    "position": 1,
                    "message": f"Your next slot starts in {wait_minutes} minutes",
                    "next_slot_start": upcoming_slot["scheduled_start"],
                    "wait_minutes": wait_minutes
                }
            
            # No scheduled slots
            return {
                "queue_type": "scheduled",
                "can_contribute": False,
                "your_turn": False,
                "position": -1,
                "message": "You don't have any scheduled slots",
                "next_slot_start": None
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduled queue status: {str(e)}")
            return {"error": "Error getting queue status"}
    
    @classmethod
    async def skip_turn(cls, world_id: str, user_id: str) -> Tuple[bool, str]:
        """Allow user to skip their turn in sequential mode"""
        try:
            # Get world details
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return False, "World not found"
            
            collaboration_settings = world.get("collaboration_settings", {})
            contribution_order = collaboration_settings.get("contribution_order", "sequential")
            
            if contribution_order != "sequential":
                return False, "Turn skipping is only available for sequential worlds"
            
            # Check if it's actually the user's turn
            queue_status = await cls._get_sequential_queue_status(world_id, user_id, world)
            if not queue_status.get("your_turn", False):
                return False, "It's not your turn to contribute"
            
            # Create a "skip" contribution to advance the queue
            skip_contribution = {
                "world_id": ObjectId(world_id),
                "contributor_id": ObjectId(user_id),
                "session_number": await cls._get_next_session_number(world_id),
                "contribution_type": "text",
                "transcript": "[User skipped their turn]",
                "duration_seconds": 0,
                "learning_metrics": {
                    "words_spoken": 0,
                    "unique_vocabulary": [],
                    "grammar_structures_used": [],
                    "pronunciation_score": 0.0,
                    "fluency_score": 0.0
                },
                "story_impact": {
                    "plot_advancement": "The story pauses momentarily.",
                    "characters_introduced": [],
                    "locations_visited": []
                },
                "ai_feedback": {
                    "corrections": [],
                    "suggestions": [],
                    "praise_points": []
                },
                "peer_reactions": {
                    "likes": 0,
                    "helpful_votes": 0,
                    "creative_votes": 0
                },
                "status": "removed",  # Mark as removed so it doesn't show in story
                "created_at": datetime.utcnow()
            }
            
            await database["story_contributions"].insert_one(skip_contribution)
            
            logger.info(f"User {user_id} skipped turn in world {world_id}")
            return True, "Turn skipped successfully"
            
        except Exception as e:
            logger.error(f"Error skipping turn: {str(e)}")
            return False, "Error skipping turn"
    
    @classmethod
    async def get_next_contributor(cls, world_id: str) -> Optional[str]:
        """Get the next contributor in the queue"""
        try:
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return None
            
            collaboration_settings = world.get("collaboration_settings", {})
            contribution_order = collaboration_settings.get("contribution_order", "sequential")
            
            if contribution_order == "sequential":
                queue_status = await cls._get_sequential_queue_status(world_id, "", world)
                current_contributor = queue_status.get("current_contributor")
                if current_contributor:
                    return current_contributor.get("id")
            
            elif contribution_order == "scheduled":
                now = datetime.utcnow()
                active_slot = await database["collaboration_queue"].find_one({
                    "world_id": ObjectId(world_id),
                    "status": QueueStatusEnum.ACTIVE,
                    "scheduled_start": {"$lte": now},
                    "scheduled_end": {"$gte": now}
                })
                
                if active_slot:
                    return str(active_slot["scheduled_contributor_id"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next contributor: {str(e)}")
            return None
    
    @classmethod
    async def handle_turn_timeout(cls, world_id: str, user_id: str) -> bool:
        """Handle when a user's turn times out"""
        try:
            # For scheduled mode, mark slot as missed
            collaboration_settings = await cls._get_world_collaboration_settings(world_id)
            if not collaboration_settings:
                return False
            
            if collaboration_settings.get("contribution_order") == "scheduled":
                await database["collaboration_queue"].update_one(
                    {
                        "world_id": ObjectId(world_id),
                        "scheduled_contributor_id": ObjectId(user_id),
                        "status": QueueStatusEnum.ACTIVE
                    },
                    {"$set": {"status": QueueStatusEnum.MISSED}}
                )
            
            # For sequential mode, automatically skip the turn
            elif collaboration_settings.get("contribution_order") == "sequential":
                await cls.skip_turn(world_id, user_id)
            
            logger.info(f"Handled turn timeout for user {user_id} in world {world_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling turn timeout: {str(e)}")
            return False
    
    @classmethod
    async def notify_next_contributor(cls, world_id: str, current_user_id: str) -> bool:
        """Notify the next contributor that it's their turn"""
        try:
            # This would integrate with a notification system
            # For now, we'll just log the notification
            next_contributor_id = await cls.get_next_contributor(world_id)
            
            if next_contributor_id and next_contributor_id != current_user_id:
                # Get user details for notification
                next_user = await database["users"].find_one({"_id": ObjectId(next_contributor_id)})
                world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
                
                if next_user and world:
                    logger.info(f"Would notify {next_user.get('email')} that it's their turn in '{world.get('title')}'")
                    
                    # Here you would integrate with:
                    # - Email notifications
                    # - Push notifications
                    # - In-app notifications
                    # - WebSocket real-time updates
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error notifying next contributor: {str(e)}")
            return False
    
    @classmethod
    async def create_scheduled_slots(
        cls, 
        world_id: str, 
        schedule: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """Create scheduled contribution slots"""
        try:
            slots_to_insert = []
            
            for slot_data in schedule:
                slot = CollaborationQueueCreate(
                    world_id=world_id,
                    scheduled_contributor_id=slot_data["contributor_id"],
                    scheduled_start=slot_data["start_time"],
                    scheduled_end=slot_data["end_time"]
                )
                
                slot_dict = slot.dict()
                slot_dict["world_id"] = ObjectId(slot_dict["world_id"])
                slot_dict["scheduled_contributor_id"] = ObjectId(slot_dict["scheduled_contributor_id"])
                slot_dict["created_at"] = datetime.utcnow()
                slot_dict["status"] = QueueStatusEnum.UPCOMING
                
                slots_to_insert.append(slot_dict)
            
            if slots_to_insert:
                await database["collaboration_queue"].insert_many(slots_to_insert)
                return True, f"Created {len(slots_to_insert)} scheduled slots"
            
            return False, "No slots to create"
            
        except Exception as e:
            logger.error(f"Error creating scheduled slots: {str(e)}")
            return False, "Error creating scheduled slots"
    
    @classmethod
    async def _get_next_session_number(cls, world_id: str) -> int:
        """Get the next session number for a world"""
        try:
            count = await database["story_contributions"].count_documents({
                "world_id": ObjectId(world_id)
            })
            return count + 1
        except:
            return 1
    
    @classmethod
    async def _get_world_collaboration_settings(cls, world_id: str) -> Optional[Dict[str, Any]]:
        """Get collaboration settings for a world"""
        try:
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if world:
                return world.get("collaboration_settings", {})
            return None
        except:
            return None
    
    @classmethod
    async def get_world_queue_overview(cls, world_id: str) -> Dict[str, Any]:
        """Get overview of queue status for a world"""
        try:
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return {"error": "World not found"}
            
            collaboration_settings = world.get("collaboration_settings", {})
            contribution_order = collaboration_settings.get("contribution_order", "sequential")
            contributors = world.get("contributors", [])
            
            # Get contributor details
            contributor_details = []
            for contributor_id in contributors:
                user = await database["users"].find_one({"_id": contributor_id})
                if user:
                    contributor_details.append({
                        "id": str(contributor_id),
                        "name": user.get("name", "Unknown"),
                        "email": user.get("email", "")
                    })
            
            # Get recent contributions
            recent_contributions = await database["story_contributions"].find(
                {"world_id": ObjectId(world_id), "status": "active"}
            ).sort("created_at", -1).limit(5).to_list(length=5)
            
            contribution_summary = []
            for contrib in recent_contributions:
                contributor = await database["users"].find_one({"_id": contrib["contributor_id"]})
                contribution_summary.append({
                    "contributor_name": contributor.get("name", "Unknown") if contributor else "Unknown",
                    "created_at": contrib["created_at"],
                    "word_count": len(contrib["transcript"].split()),
                    "session_number": contrib["session_number"]
                })
            
            return {
                "world_id": world_id,
                "title": world.get("title", ""),
                "contribution_order": contribution_order,
                "total_contributors": len(contributors),
                "contributors": contributor_details,
                "recent_contributions": contribution_summary,
                "session_duration_minutes": collaboration_settings.get("session_duration_minutes", 10),
                "total_contributions": len(recent_contributions)
            }
            
        except Exception as e:
            logger.error(f"Error getting world queue overview: {str(e)}")
            return {"error": "Error getting queue overview"}
