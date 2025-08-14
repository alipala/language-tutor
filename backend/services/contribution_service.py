from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import logging
from bson import ObjectId
from database import database
from models.world_building_models import (
    StoryContributionCreate, StoryContributionInDB, StoryContributionResponse,
    ContributionStatusEnum, ContributionTypeEnum, LearningMetrics, StoryImpact,
    AIFeedback, Correction, PeerReactions
)
from sentence_assessment import recognize_speech
from subscription_service import SubscriptionService
import openai
import os

logger = logging.getLogger(__name__)

class ContributionService:
    """Service for managing story contributions and learning metrics"""
    
    @classmethod
    async def validate_user_turn(cls, world_id: str, user_id: str) -> Tuple[bool, str]:
        """Validate if it's the user's turn to contribute"""
        try:
            # Get world details
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return False, "World not found"
            
            # Check if user is a contributor, if not add them automatically for public worlds
            contributors = world.get("contributors", [])
            user_obj_id = ObjectId(user_id)
            
            if user_obj_id not in contributors:
                # For public worlds, automatically add user as contributor
                privacy_setting = world.get("privacy_setting", "public")
                if privacy_setting == "public":
                    # Add user as contributor
                    await database["story_worlds"].update_one(
                        {"_id": ObjectId(world_id)},
                        {"$addToSet": {"contributors": user_obj_id}}
                    )
                    contributors.append(user_obj_id)
                    logger.info(f"Added user {user_id} as contributor to public world {world_id}")
                else:
                    return False, "You are not a contributor to this private world"
            
            # Check world status
            if world.get("status") != "active":
                return False, f"World is not active (status: {world.get('status')})"
            
            # For voice sessions, we're more permissive with turn-based restrictions
            # The real-time conversation flow is more important than strict turn order
            
            # Get collaboration settings
            collaboration_settings = world.get("collaboration_settings", {})
            contribution_order = collaboration_settings.get("contribution_order", "sequential")
            
            # For voice sessions, we allow more flexible participation
            # Users can join conversations and practice even if it's not strictly "their turn"
            if contribution_order == "sequential":
                # For voice sessions, we'll be more lenient - allow anyone to participate
                # The AI tutor will guide the conversation appropriately
                contributors = world.get("contributors", [])
                if not contributors:
                    return False, "No contributors found"
                
                # Allow participation - the voice session is more about practice than strict story progression
                pass
            
            elif contribution_order == "random":
                # Random order - anyone can contribute
                pass
            
            elif contribution_order == "scheduled":
                # For voice sessions, we'll be more flexible with scheduling
                # Check if user has a scheduled slot, but don't be too strict
                queue_entry = await database["collaboration_queue"].find_one({
                    "world_id": ObjectId(world_id),
                    "scheduled_contributor_id": ObjectId(user_id),
                    "status": "active",
                    "scheduled_start": {"$lte": datetime.utcnow()},
                    "scheduled_end": {"$gte": datetime.utcnow()}
                })
                
                # If no scheduled slot, still allow for voice practice sessions
                if not queue_entry:
                    logger.info(f"User {user_id} joining voice session without scheduled slot - allowing for practice")
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating user turn: {str(e)}")
            return False, "Error validating turn"
    
    @classmethod
    async def process_contribution(
        cls, 
        world_id: str, 
        user_id: str, 
        transcript: Optional[str] = None,
        audio_base64: Optional[str] = None,
        audio_url: Optional[str] = None,
        duration_seconds: int = 0
    ) -> Tuple[bool, str, Optional[str]]:
        """Process a new contribution to a story world"""
        try:
            # Validate user's turn
            can_contribute, error_msg = await cls.validate_user_turn(world_id, user_id)
            if not can_contribute:
                return False, error_msg, None
            
            # Check subscription limits
            can_access, limit_msg = await SubscriptionService.can_access_feature(user_id, "practice_session")
            if not can_access:
                return False, limit_msg, None
            
            # Get world details
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return False, "World not found", None
            
            # Transcribe audio if provided and no transcript
            final_transcript = transcript
            if not final_transcript and audio_base64:
                try:
                    language = world.get("language", "en")
                    final_transcript = await recognize_speech(audio_base64, language)
                    logger.info(f"Transcribed audio for contribution: '{final_transcript}'")
                except Exception as e:
                    logger.error(f"Error transcribing audio: {str(e)}")
                    return False, "Failed to transcribe audio", None
            
            if not final_transcript:
                return False, "No transcript or audio provided", None
            
            # Flexible validation for voice sessions
            word_count = len(final_transcript.split())
            
            # For voice sessions, be more flexible with content length
            # Allow shorter contributions if they have meaningful content
            if len(final_transcript.strip()) < 10:
                return False, "Contribution must contain meaningful content", None
            
            # Still enforce maximum limits
            if word_count > 500:
                return False, "Contribution cannot exceed 500 words", None
            
            # Flexible duration validation - allow shorter sessions for practice
            if duration_seconds < 5:  # Minimum 5 seconds instead of 30
                return False, "Audio contribution must be at least 5 seconds", None
            if duration_seconds > 300:  # 5 minutes
                return False, "Audio contribution cannot exceed 5 minutes", None
            
            # Get session number
            contribution_count = await database["story_contributions"].count_documents({
                "world_id": ObjectId(world_id)
            })
            session_number = contribution_count + 1
            
            # Calculate learning metrics
            learning_metrics = await cls.calculate_learning_metrics(
                final_transcript, audio_base64, world.get("language", "en")
            )
            
            # Analyze story impact
            story_impact = await cls.analyze_story_impact(
                final_transcript, world, session_number
            )
            
            # Generate AI feedback
            ai_feedback = await cls.generate_ai_feedback(
                final_transcript, world.get("language", "en"), world.get("target_level", "B1")
            )
            
            # Determine contribution type
            contribution_type = ContributionTypeEnum.MIXED if audio_base64 else ContributionTypeEnum.TEXT
            
            # Create contribution
            contribution_data = StoryContributionCreate(
                world_id=ObjectId(world_id),
                contributor_id=ObjectId(user_id),
                session_number=session_number,
                contribution_type=contribution_type,
                audio_url=audio_url,
                transcript=final_transcript,
                duration_seconds=duration_seconds,
                learning_metrics=learning_metrics,
                story_impact=story_impact,
                ai_feedback=ai_feedback,
                peer_reactions=PeerReactions(),
                status=ContributionStatusEnum.ACTIVE
            )
            
            # Insert contribution
            contribution_dict = contribution_data.dict()
            contribution_dict["created_at"] = datetime.utcnow()
            
            result = await database["story_contributions"].insert_one(contribution_dict)
            contribution_id = str(result.inserted_id)
            
            # Update world state
            await cls.update_world_state(world_id, story_impact, final_transcript)
            
            # Track usage
            speaking_minutes = duration_seconds / 60.0
            await SubscriptionService.track_speaking_time({
                "user_id": user_id,
                "speaking_minutes": speaking_minutes,
                "session_completed": True  # Contribution counts as completed session
            })
            
            logger.info(f"Processed contribution {contribution_id} for world {world_id}")
            return True, "Contribution processed successfully", contribution_id
            
        except Exception as e:
            logger.error(f"Error processing contribution: {str(e)}")
            return False, "Error processing contribution", None
    
    @classmethod
    async def calculate_learning_metrics(
        cls, 
        transcript: str, 
        audio_base64: Optional[str], 
        language: str
    ) -> LearningMetrics:
        """Calculate learning metrics from contribution"""
        try:
            words = transcript.split()
            word_count = len(words)
            
            # Calculate unique vocabulary
            unique_words = list(set(word.lower().strip('.,!?;:"()[]{}') for word in words))
            
            # Basic grammar structure detection (simplified)
            grammar_structures = []
            transcript_lower = transcript.lower()
            
            # Common structures to detect
            if any(word in transcript_lower for word in ['because', 'since', 'as']):
                grammar_structures.append('causal_clauses')
            if any(word in transcript_lower for word in ['although', 'however', 'but']):
                grammar_structures.append('contrast_clauses')
            if any(word in transcript_lower for word in ['if', 'unless', 'provided']):
                grammar_structures.append('conditional_clauses')
            if any(word in transcript_lower for word in ['who', 'which', 'that', 'where']):
                grammar_structures.append('relative_clauses')
            
            # Pronunciation and fluency scores (simplified - would use actual audio analysis)
            pronunciation_score = 75.0  # Default score
            fluency_score = 70.0  # Default score
            
            if audio_base64:
                # In a real implementation, this would analyze the audio
                # For now, we'll use word count as a proxy for fluency
                if word_count > 100:
                    fluency_score = min(90.0, fluency_score + 15.0)
                elif word_count > 75:
                    fluency_score = min(85.0, fluency_score + 10.0)
                elif word_count > 50:
                    fluency_score = min(80.0, fluency_score + 5.0)
            
            return LearningMetrics(
                words_spoken=word_count,
                unique_vocabulary=unique_words[:50],  # Limit to 50 for storage
                grammar_structures_used=grammar_structures,
                pronunciation_score=pronunciation_score,
                fluency_score=fluency_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating learning metrics: {str(e)}")
            return LearningMetrics()
    
    @classmethod
    async def analyze_story_impact(
        cls, 
        transcript: str, 
        world: Dict[str, Any], 
        session_number: int
    ) -> StoryImpact:
        """Analyze how the contribution impacts the story"""
        try:
            # Use OpenAI to analyze story impact
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            world_state = world.get("world_state", {})
            current_plot = world_state.get("current_plot_point", "")
            active_characters = [char.get("name", "") for char in world_state.get("active_characters", [])]
            locations = [loc.get("name", "") for loc in world_state.get("locations", [])]
            
            prompt = f"""
Analyze this story contribution and determine its impact:

Current Plot: {current_plot}
Active Characters: {', '.join(active_characters)}
Known Locations: {', '.join(locations)}

New Contribution: "{transcript}"

Please analyze:
1. How does this advance the plot? (1-2 sentences)
2. Are any new characters introduced? (list names only)
3. Are any new locations mentioned? (list names only)

Respond in JSON format:
{{
    "plot_advancement": "description of how plot advances",
    "characters_introduced": ["character1", "character2"],
    "locations_visited": ["location1", "location2"]
}}
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            return StoryImpact(
                plot_advancement=analysis.get("plot_advancement", "The story continues to develop."),
                characters_introduced=analysis.get("characters_introduced", []),
                locations_visited=analysis.get("locations_visited", [])
            )
            
        except Exception as e:
            logger.error(f"Error analyzing story impact: {str(e)}")
            return StoryImpact(
                plot_advancement="The story continues to develop.",
                characters_introduced=[],
                locations_visited=[]
            )
    
    @classmethod
    async def generate_ai_feedback(
        cls, 
        transcript: str, 
        language: str, 
        target_level: str
    ) -> AIFeedback:
        """Generate AI feedback for the contribution"""
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""
Analyze this {language} language contribution from a {target_level} level learner:

"{transcript}"

Provide feedback in JSON format:
{{
    "corrections": [
        {{"error": "original text", "correction": "corrected text", "type": "grammar/vocabulary/spelling"}}
    ],
    "suggestions": [
        "suggestion 1",
        "suggestion 2"
    ],
    "praise_points": [
        "positive aspect 1",
        "positive aspect 2"
    ]
}}

Focus on:
- Grammar corrections appropriate for {target_level} level
- Vocabulary improvements
- Positive reinforcement
- Constructive suggestions for improvement
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            feedback_data = json.loads(response.choices[0].message.content)
            
            corrections = [
                Correction(
                    error=corr.get("error", ""),
                    correction=corr.get("correction", ""),
                    type=corr.get("type", "grammar")
                )
                for corr in feedback_data.get("corrections", [])
            ]
            
            return AIFeedback(
                corrections=corrections,
                suggestions=feedback_data.get("suggestions", []),
                praise_points=feedback_data.get("praise_points", [])
            )
            
        except Exception as e:
            logger.error(f"Error generating AI feedback: {str(e)}")
            return AIFeedback(
                corrections=[],
                suggestions=["Keep practicing! Your contribution adds to the story."],
                praise_points=["Great job participating in the collaborative story!"]
            )
    
    @classmethod
    async def update_world_state(
        cls, 
        world_id: str, 
        story_impact: StoryImpact, 
        transcript: str
    ) -> bool:
        """Update world state based on contribution"""
        try:
            world = await database["story_worlds"].find_one({"_id": ObjectId(world_id)})
            if not world:
                return False
            
            world_state = world.get("world_state", {})
            
            # Update plot point
            world_state["current_plot_point"] = story_impact.plot_advancement
            
            # Add new characters
            active_characters = world_state.get("active_characters", [])
            for char_name in story_impact.characters_introduced:
                if not any(char.get("name") == char_name for char in active_characters):
                    active_characters.append({
                        "name": char_name,
                        "role": "Character",
                        "description": f"Introduced in recent contribution"
                    })
            
            # Add new locations
            locations = world_state.get("locations", [])
            for loc_name in story_impact.locations_visited:
                if not any(loc.get("name") == loc_name for loc in locations):
                    locations.append({
                        "name": loc_name,
                        "description": f"Visited in recent contribution"
                    })
            
            # Update world
            await database["story_worlds"].update_one(
                {"_id": ObjectId(world_id)},
                {
                    "$set": {
                        "world_state": world_state,
                        "updated_at": datetime.utcnow(),
                        "last_contribution_at": datetime.utcnow()
                    },
                    "$inc": {
                        "statistics.total_sessions": 1
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating world state: {str(e)}")
            return False
    
    @classmethod
    async def get_contributions(
        cls, 
        world_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> Tuple[List[StoryContributionResponse], int]:
        """Get contributions for a world"""
        try:
            # Get contributions with pagination
            contributions_cursor = database["story_contributions"].find(
                {"world_id": ObjectId(world_id), "status": ContributionStatusEnum.ACTIVE}
            ).sort("created_at", -1).skip(offset).limit(limit)
            
            contributions = await contributions_cursor.to_list(length=limit)
            
            # Get total count
            total_count = await database["story_contributions"].count_documents({
                "world_id": ObjectId(world_id),
                "status": ContributionStatusEnum.ACTIVE
            })
            
            # Convert to response models
            response_contributions = []
            for contrib in contributions:
                contrib["id"] = str(contrib["_id"])
                contrib["world_id"] = str(contrib["world_id"])
                contrib["contributor_id"] = str(contrib["contributor_id"])
                response_contributions.append(StoryContributionResponse(**contrib))
            
            return response_contributions, total_count
            
        except Exception as e:
            logger.error(f"Error getting contributions: {str(e)}")
            return [], 0
    
    @classmethod
    async def update_contribution(
        cls, 
        contribution_id: str, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update a contribution (only by the contributor)"""
        try:
            # Get contribution
            contribution = await database["story_contributions"].find_one({
                "_id": ObjectId(contribution_id)
            })
            
            if not contribution:
                return False, "Contribution not found"
            
            # Check if user is the contributor
            if str(contribution.get("contributor_id")) != user_id:
                return False, "You can only edit your own contributions"
            
            # Only allow certain fields to be updated
            allowed_updates = {}
            if "transcript" in updates:
                allowed_updates["transcript"] = updates["transcript"]
                # Recalculate learning metrics if transcript changes
                world = await database["story_worlds"].find_one({
                    "_id": contribution.get("world_id")
                })
                if world:
                    learning_metrics = await cls.calculate_learning_metrics(
                        updates["transcript"], None, world.get("language", "en")
                    )
                    allowed_updates["learning_metrics"] = learning_metrics.dict()
            
            if allowed_updates:
                await database["story_contributions"].update_one(
                    {"_id": ObjectId(contribution_id)},
                    {"$set": allowed_updates}
                )
                return True, "Contribution updated successfully"
            
            return False, "No valid updates provided"
            
        except Exception as e:
            logger.error(f"Error updating contribution: {str(e)}")
            return False, "Error updating contribution"
    
    @classmethod
    async def delete_contribution(
        cls, 
        contribution_id: str, 
        user_id: str
    ) -> Tuple[bool, str]:
        """Delete a contribution (only by the contributor)"""
        try:
            # Get contribution
            contribution = await database["story_contributions"].find_one({
                "_id": ObjectId(contribution_id)
            })
            
            if not contribution:
                return False, "Contribution not found"
            
            # Check if user is the contributor
            if str(contribution.get("contributor_id")) != user_id:
                return False, "You can only delete your own contributions"
            
            # Mark as removed instead of deleting
            await database["story_contributions"].update_one(
                {"_id": ObjectId(contribution_id)},
                {"$set": {"status": ContributionStatusEnum.REMOVED}}
            )
            
            return True, "Contribution removed successfully"
            
        except Exception as e:
            logger.error(f"Error deleting contribution: {str(e)}")
            return False, "Error deleting contribution"
