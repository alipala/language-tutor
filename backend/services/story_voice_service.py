from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import logging
from bson import ObjectId
from database import database
from services.world_building_service import WorldBuildingService
from services.contribution_service import ContributionService
from subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class StoryVoiceService:
    """Service for integrating voice conversations with story worlds"""
    
    @classmethod
    async def get_story_context_for_voice_session(
        cls, 
        world_id: str, 
        user_id: str,
        session_type: str = "contribution"  # "practice", "contribution", "review"
    ) -> Dict[str, Any]:
        """Get story context to enhance voice conversation prompts"""
        try:
            # Get world details
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return {"error": "World not found"}
            
            # Check if user is a contributor
            if ObjectId(user_id) not in world.get("contributors", []):
                return {"error": "User is not a contributor to this world"}
            
            # Get the last contribution for context
            last_contribution = await database["story_contributions"].find_one(
                {"world_id": ObjectId(world_id), "status": "active"},
                sort=[("created_at", -1)]
            )
            
            # Get contributor info for the last contribution
            previous_contributor_name = "Unknown"
            if last_contribution:
                contributor = await database["users"].find_one(
                    {"_id": last_contribution.get("contributor_id")}
                )
                if contributor:
                    previous_contributor_name = contributor.get("name", "Unknown")
            
            # Build story context
            world_state = world.get("world_state", {})
            learning_objectives = world.get("learning_objectives", {})
            
            story_context = {
                "world_id": world_id,
                "world_title": world.get("title", "Untitled Story"),
                "genre": world.get("genre", "adventure"),
                "language": world.get("language", "en"),
                "target_level": world.get("target_level", "B1"),
                "session_type": session_type,
                
                # Story state
                "current_plot_point": world_state.get("current_plot_point", "The story begins..."),
                "active_characters": world_state.get("active_characters", []),
                "locations": world_state.get("locations", []),
                "important_items": world_state.get("important_items", []),
                
                # Learning context
                "primary_focus": learning_objectives.get("primary_focus", "vocabulary"),
                "target_structures": learning_objectives.get("target_structures", []),
                "vocabulary_themes": learning_objectives.get("vocabulary_themes", []),
                
                # Previous contribution context
                "previous_contribution": {
                    "transcript": last_contribution.get("transcript", "") if last_contribution else "",
                    "contributor_name": previous_contributor_name,
                    "session_number": last_contribution.get("session_number", 0) if last_contribution else 0
                },
                
                # Session configuration
                "session_limits": cls._get_session_limits(session_type),
                "collaboration_settings": world.get("collaboration_settings", {}),
                
                # Story statistics
                "total_contributions": await database["story_contributions"].count_documents({
                    "world_id": ObjectId(world_id),
                    "status": "active"
                })
            }
            
            return story_context
            
        except Exception as e:
            logger.error(f"Error getting story context: {str(e)}")
            return {"error": "Failed to get story context"}
    
    @classmethod
    def _get_session_limits(cls, session_type: str) -> Dict[str, int]:
        """Get session limits based on type"""
        limits = {
            "practice": {
                "min_duration": 30,    # 30 seconds
                "max_duration": 120,   # 2 minutes
                "saves_to_story": False
            },
            "contribution": {
                "min_duration": 30,    # 30 seconds
                "max_duration": 300,   # 5 minutes
                "saves_to_story": True
            },
            "review": {
                "min_duration": 0,     # No minimum for review
                "max_duration": 600,   # 10 minutes for review
                "saves_to_story": False
            }
        }
        return limits.get(session_type, limits["contribution"])
    
    @classmethod
    def build_story_enhanced_prompt(
        cls, 
        base_language: str, 
        base_level: str, 
        story_context: Dict[str, Any]
    ) -> str:
        """Build enhanced AI prompt with story context"""
        
        # Extract story details
        world_title = story_context.get("world_title", "Untitled Story")
        genre = story_context.get("genre", "adventure")
        current_plot = story_context.get("current_plot_point", "The story begins...")
        previous_contribution = story_context.get("previous_contribution", {})
        active_characters = story_context.get("active_characters", [])
        locations = story_context.get("locations", [])
        primary_focus = story_context.get("primary_focus", "vocabulary")
        vocabulary_themes = story_context.get("vocabulary_themes", [])
        session_type = story_context.get("session_type", "contribution")
        session_limits = story_context.get("session_limits", {})
        
        # Build character list
        character_names = [char.get("name", "") for char in active_characters if char.get("name")]
        character_list = ", ".join(character_names) if character_names else "No established characters yet"
        
        # Build location list
        location_names = [loc.get("name", "") for loc in locations if loc.get("name")]
        location_list = ", ".join(location_names) if location_names else "No established locations yet"
        
        # Build vocabulary themes
        vocab_themes = ", ".join(vocabulary_themes) if vocabulary_themes else "general vocabulary"
        
        # Session-specific instructions
        session_instructions = {
            "practice": f"""
🎭 PRACTICE MODE - Story Exploration:
- This is a {session_limits.get('max_duration', 120)}-second practice session
- Help the user explore story ideas and practice language
- Focus on {primary_focus} within the story context
- This session will NOT be saved to the story
- Encourage creativity and experimentation""",
            
            "contribution": f"""
🎬 CONTRIBUTION MODE - Active Storytelling:
- This is a {session_limits.get('max_duration', 300)}-second contribution session
- Help the user create their actual story contribution
- This contribution WILL be saved to the collaborative story
- Ensure story continuity and quality
- Focus on {primary_focus} and vocabulary themes: {vocab_themes}""",
            
            "review": f"""
📖 REVIEW MODE - Story Analysis:
- This is a review session for existing contributions
- Help the user understand and analyze the story
- Provide feedback on language use and story development
- Focus on learning from the collaborative narrative"""
        }
        
        # Build the enhanced prompt
        story_prompt_addition = f"""
🌍 COLLABORATIVE STORY CONTEXT:

📚 Story Details:
- Title: "{world_title}"
- Genre: {genre.title()}
- Language: {base_language.title()}
- Level: {base_level}

📖 Current Story State:
- Plot Point: {current_plot}
- Characters: {character_list}
- Locations: {location_list}

{session_instructions.get(session_type, session_instructions["contribution"])}

📝 Previous Contribution Context:
{f'Last contribution by {previous_contribution.get("contributor_name", "Unknown")}: "{previous_contribution.get("transcript", "No previous contributions yet")}"' if previous_contribution.get("transcript") else "This is the beginning of the story!"}

🎯 Learning Objectives:
- Primary Focus: {primary_focus.title()}
- Vocabulary Themes: {vocab_themes}
- Story Integration: Help user practice language through storytelling

🚨 CRITICAL STORY CONTINUITY RULES:
1. MAINTAIN STORY CONSISTENCY: Ensure the user's contribution flows naturally from the previous contribution
2. CHARACTER CONSISTENCY: Reference established characters appropriately
3. PLOT COHERENCE: Help advance the story logically
4. GENRE ADHERENCE: Keep contributions appropriate for the {genre} genre
5. LEARNING BALANCE: 70% language learning, 30% story development

🎭 STORY GUIDANCE APPROACH:
- Ask about the user's story ideas FIRST
- Help them develop their contribution while practicing {base_language}
- Correct language errors within the story context
- Suggest vocabulary from themes: {vocab_themes}
- Encourage creativity while maintaining continuity
- Reference characters and locations when relevant

EXAMPLE STORY INTEGRATION:
Instead of generic corrections, provide story-contextual feedback:
❌ "You should say 'went' not 'goed'"
✅ "When describing how the character moved through the forest, we say 'went' - 'The hero went deeper into the mysterious woods...'"

Remember: You are helping create a collaborative story while teaching {base_language} at {base_level} level. Make language learning feel natural within the storytelling experience.
"""
        
        return story_prompt_addition
    
    @classmethod
    async def validate_story_voice_session(
        cls, 
        world_id: str, 
        user_id: str, 
        session_type: str = "contribution"
    ) -> Tuple[bool, str]:
        """Validate if user can start a story voice session"""
        try:
            # Check if it's a contribution session and validate turn
            if session_type == "contribution":
                can_contribute, error_msg = await ContributionService.validate_user_turn(world_id, user_id)
                if not can_contribute:
                    return False, error_msg
            
            # Check subscription limits for all session types
            can_access, limit_msg = await SubscriptionService.can_access_feature(user_id, "practice_session")
            if not can_access:
                return False, limit_msg
            
            # Get world to verify access
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return False, "Story world not found"
            
            # Check if user is a contributor
            if ObjectId(user_id) not in world.get("contributors", []):
                return False, "You are not a contributor to this story world"
            
            # Check world status
            if world.get("status") != "active":
                return False, f"Story world is not active (status: {world.get('status')})"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating story voice session: {str(e)}")
            return False, "Error validating session access"
    
    @classmethod
    async def process_story_voice_session_completion(
        cls,
        world_id: str,
        user_id: str,
        session_type: str,
        transcript: str,
        audio_base64: Optional[str] = None,
        duration_seconds: int = 0
    ) -> Tuple[bool, str, Optional[str]]:
        """Process completed story voice session"""
        try:
            session_limits = cls._get_session_limits(session_type)
            
            # For contribution sessions, save to story
            if session_type == "contribution" and session_limits.get("saves_to_story", False):
                # Check if we have meaningful content to save
                if transcript and transcript.strip() and len(transcript.strip()) > 10:
                    # If we have good content, save it regardless of duration
                    # This allows users to complete sessions early if they have something valuable
                    logger.info(f"Processing story contribution with {duration_seconds}s duration and {len(transcript)} characters")
                    
                    # Process as a story contribution
                    success, message, contribution_id = await ContributionService.process_contribution(
                        world_id=world_id,
                        user_id=user_id,
                        transcript=transcript,
                        audio_base64=audio_base64,
                        duration_seconds=duration_seconds
                    )
                    
                    return success, message, contribution_id
                
                elif duration_seconds < session_limits.get("min_duration", 30):
                    # If no meaningful content and too short, treat as practice session
                    logger.info(f"Short session ({duration_seconds}s) with minimal content - treating as practice")
                    speaking_minutes = duration_seconds / 60.0
                    await SubscriptionService.track_speaking_time({
                        "user_id": user_id,
                        "speaking_minutes": speaking_minutes,
                        "session_completed": False  # Mark as incomplete due to short duration
                    })
                    
                    return True, f"Practice session completed! Added {speaking_minutes:.1f} minutes of conversation practice.", None
                
                else:
                    # Duration is good but no meaningful content
                    logger.info(f"Session duration OK ({duration_seconds}s) but no meaningful transcript content")
                    speaking_minutes = duration_seconds / 60.0
                    await SubscriptionService.track_speaking_time({
                        "user_id": user_id,
                        "speaking_minutes": speaking_minutes,
                        "session_completed": True
                    })
                    
                    return True, f"Conversation practice completed! Added {speaking_minutes:.1f} minutes of speaking practice.", None
            
            else:
                # For practice/review sessions, just track usage without saving to story
                speaking_minutes = duration_seconds / 60.0
                await SubscriptionService.track_speaking_time({
                    "user_id": user_id,
                    "speaking_minutes": speaking_minutes,
                    "session_completed": duration_seconds >= session_limits.get("min_duration", 30)
                })
                
                return True, f"{session_type.title()} session completed successfully", None
                
        except Exception as e:
            logger.error(f"Error processing story voice session: {str(e)}")
            return False, "Error processing session", None
    
    @classmethod
    async def get_story_voice_session_config(
        cls,
        world_id: str,
        user_id: str,
        session_type: str = "contribution"
    ) -> Dict[str, Any]:
        """Get complete configuration for story voice session"""
        try:
            # Validate session access
            can_access, error_msg = await cls.validate_story_voice_session(world_id, user_id, session_type)
            if not can_access:
                return {"error": error_msg}
            
            # Get story context
            story_context = await cls.get_story_context_for_voice_session(world_id, user_id, session_type)
            if "error" in story_context:
                return story_context
            
            # Get session limits
            session_limits = cls._get_session_limits(session_type)
            
            # Build enhanced prompt
            enhanced_prompt = cls.build_story_enhanced_prompt(
                story_context.get("language", "english"),
                story_context.get("target_level", "B1"),
                story_context
            )
            
            return {
                "success": True,
                "story_context": story_context,
                "session_limits": session_limits,
                "enhanced_prompt": enhanced_prompt,
                "session_type": session_type,
                "world_id": world_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting story voice session config: {str(e)}")
            return {"error": "Failed to get session configuration"}
