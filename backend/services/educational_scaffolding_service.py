import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId

from database import database
from models.educational_scaffolding_models import (
    StoryLearningMetrics, LearningGateResult, StoryProgressUpdate,
    StoryAchievement, UserStoryAchievement, LevelAssessmentResult,
    StoryLearningAnalytics, StoryProgressIntegration
)
from subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class EducationalScaffoldingService:
    """Service for educational scaffolding and learning effectiveness in story worlds"""
    
    # Define story-specific achievements
    STORY_ACHIEVEMENTS = {
        "story_pioneer": StoryAchievement(
            achievement_id="story_pioneer",
            name="Story Pioneer",
            description="Make your first story contribution",
            icon="🌟",
            category="story",
            requirements={"contributions": 1},
            reward_points=50
        ),
        "world_builder": StoryAchievement(
            achievement_id="world_builder",
            name="World Builder",
            description="Create your first story world",
            icon="🏗️",
            category="creation",
            requirements={"worlds_created": 1},
            reward_points=100
        ),
        "collaborator": StoryAchievement(
            achievement_id="collaborator",
            name="Collaborator",
            description="Make 10 story contributions",
            icon="🤝",
            category="collaboration",
            requirements={"contributions": 10},
            reward_points=200
        ),
        "narrative_master": StoryAchievement(
            achievement_id="narrative_master",
            name="Narrative Master",
            description="Complete 5 story worlds",
            icon="📚",
            category="mastery",
            requirements={"completed_stories": 5},
            reward_points=500
        ),
        "cultural_explorer": StoryAchievement(
            achievement_id="cultural_explorer",
            name="Cultural Explorer",
            description="Learn 25 cultural references through stories",
            icon="🌍",
            category="learning",
            requirements={"cultural_references": 25},
            reward_points=150
        ),
        "vocabulary_collector": StoryAchievement(
            achievement_id="vocabulary_collector",
            name="Vocabulary Collector",
            description="Learn 100 new words through stories",
            icon="📖",
            category="learning",
            requirements={"vocabulary_learned": 100},
            reward_points=300
        )
    }
    
    # Level compatibility matrix (user level can join world ±1 level)
    LEVEL_HIERARCHY = ["A1", "A2", "B1", "B2", "C1", "C2"]
    
    @classmethod
    def get_user_query(cls, user_id: str):
        """Helper function to handle both UUID and ObjectId formats"""
        try:
            return {"_id": ObjectId(user_id)}
        except:
            return {"_id": user_id}
    
    @classmethod
    async def check_learning_gates(cls, user_id: str, world_id: str, language: str) -> LearningGateResult:
        """
        Check if user meets all learning gates before allowing contribution
        
        Gates:
        1. User has completed at least 1 assessment with the language
        2. User's level matches world ±1 level
        3. User has practiced recently (last 7 days)
        4. User has sessions remaining in subscription
        """
        try:
            logger.info(f"[LEARNING_GATES] Checking learning gates for user {user_id} in world {world_id}")
            
            # Get user data
            user = await database.users.find_one(cls.get_user_query(user_id))
            if not user:
                return LearningGateResult(
                    can_contribute=False,
                    gate_checks={},
                    blocking_reasons=["User not found"],
                    recommendations=["Please log in again"]
                )
            
            # Get world data
            world = await database.story_worlds.find_one({"id": world_id})
            if not world:
                return LearningGateResult(
                    can_contribute=False,
                    gate_checks={},
                    blocking_reasons=["Story world not found"],
                    recommendations=["Please select a valid story world"]
                )
            
            gate_checks = {}
            blocking_reasons = []
            recommendations = []
            
            # Gate 1: Assessment completed for this language
            last_assessment = user.get("last_assessment_data")
            assessment_completed = False
            user_level = None
            
            if last_assessment and last_assessment.get("language") == language:
                assessment_completed = True
                user_level = last_assessment.get("level", "A1")
                logger.info(f"[LEARNING_GATES] ✅ Assessment completed: {user_level} level in {language}")
            else:
                logger.info(f"[LEARNING_GATES] ❌ No assessment found for {language}")
                blocking_reasons.append(f"Complete a speaking assessment in {language} first")
                recommendations.append(f"Take a speaking assessment to determine your {language} level")
            
            gate_checks["assessment_completed"] = assessment_completed
            
            # Gate 2: Level compatibility (±1 level)
            world_level = world.get("target_level", "B1")
            level_match = False
            
            if assessment_completed and user_level:
                level_match = cls._check_level_compatibility(user_level, world_level)
                if level_match:
                    logger.info(f"[LEARNING_GATES] ✅ Level match: User {user_level} can join {world_level} world")
                else:
                    logger.info(f"[LEARNING_GATES] ❌ Level mismatch: User {user_level} cannot join {world_level} world")
                    blocking_reasons.append(f"Your {user_level} level doesn't match this {world_level} story world")
                    recommendations.append(f"Find a story world suitable for {user_level} level, or improve to {world_level} level")
            else:
                logger.info(f"[LEARNING_GATES] ❌ Cannot check level compatibility without assessment")
            
            gate_checks["level_match"] = level_match
            
            # Gate 3: Recent practice (last 7 days)
            recent_practice = False
            days_since_practice = None
            
            # Check conversation sessions in last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_session = await database.conversation_sessions.find_one({
                "user_id": user_id,
                "language": language,
                "created_at": {"$gte": seven_days_ago}
            })
            
            if recent_session:
                recent_practice = True
                days_since_practice = 0  # Practiced recently
                logger.info(f"[LEARNING_GATES] ✅ Recent practice found in {language}")
            else:
                # Find last practice session to calculate days
                last_session = await database.conversation_sessions.find_one(
                    {"user_id": user_id, "language": language},
                    sort=[("created_at", -1)]
                )
                
                if last_session:
                    days_since_practice = (datetime.utcnow() - last_session.get("created_at", datetime.utcnow())).days
                    logger.info(f"[LEARNING_GATES] ❌ Last practice was {days_since_practice} days ago")
                    blocking_reasons.append(f"Practice {language} more recently (last practice: {days_since_practice} days ago)")
                    recommendations.append(f"Complete a practice session in {language} to refresh your skills")
                else:
                    days_since_practice = 999  # Never practiced
                    logger.info(f"[LEARNING_GATES] ❌ No practice history found in {language}")
                    blocking_reasons.append(f"Practice {language} first before joining story worlds")
                    recommendations.append(f"Complete at least one practice session in {language}")
            
            gate_checks["recent_practice"] = recent_practice
            
            # Gate 4: Subscription sessions remaining
            subscription_status = await SubscriptionService.get_user_subscription_status(user_id)
            sessions_remaining = True
            sessions_remaining_count = None
            
            if subscription_status.limits:
                if subscription_status.limits.sessions_remaining == 0:
                    sessions_remaining = False
                    sessions_remaining_count = 0
                    logger.info(f"[LEARNING_GATES] ❌ No sessions remaining")
                    blocking_reasons.append("No practice sessions remaining in your subscription")
                    recommendations.append("Upgrade your subscription to continue learning")
                else:
                    sessions_remaining_count = subscription_status.limits.sessions_remaining
                    logger.info(f"[LEARNING_GATES] ✅ {sessions_remaining_count} sessions remaining")
            else:
                logger.info(f"[LEARNING_GATES] ✅ Unlimited sessions")
                sessions_remaining_count = -1  # Unlimited
            
            gate_checks["sessions_remaining"] = sessions_remaining
            
            # Determine if user can contribute
            can_contribute = all([
                assessment_completed,
                level_match,
                recent_practice,
                sessions_remaining
            ])
            
            logger.info(f"[LEARNING_GATES] Final result: can_contribute={can_contribute}")
            
            return LearningGateResult(
                can_contribute=can_contribute,
                gate_checks=gate_checks,
                blocking_reasons=blocking_reasons,
                recommendations=recommendations,
                user_level=user_level,
                world_level=world_level,
                days_since_practice=days_since_practice,
                sessions_remaining=sessions_remaining_count
            )
            
        except Exception as e:
            logger.error(f"[LEARNING_GATES] Error checking learning gates: {str(e)}")
            return LearningGateResult(
                can_contribute=False,
                gate_checks={},
                blocking_reasons=["System error occurred"],
                recommendations=["Please try again later"]
            )
    
    @classmethod
    def _check_level_compatibility(cls, user_level: str, world_level: str) -> bool:
        """Check if user level is compatible with world level (±1 level)"""
        try:
            if user_level not in cls.LEVEL_HIERARCHY or world_level not in cls.LEVEL_HIERARCHY:
                return False
            
            user_index = cls.LEVEL_HIERARCHY.index(user_level)
            world_index = cls.LEVEL_HIERARCHY.index(world_level)
            
            # Allow ±1 level difference
            return abs(user_index - world_index) <= 1
            
        except (ValueError, IndexError):
            return False
    
    @classmethod
    async def update_story_progress(cls, progress_update: StoryProgressUpdate) -> bool:
        """
        Update user's story learning progress after each contribution
        
        Updates:
        - Add minutes to practice_minutes_used
        - Increment practice_sessions_used
        - Update vocabulary learned
        - Track grammar improvements
        - Check for level advancement
        """
        try:
            logger.info(f"[STORY_PROGRESS] Updating progress for user {progress_update.user_id}")
            
            # 1. Update subscription usage (minutes and sessions)
            await cls._update_subscription_usage(
                progress_update.user_id,
                progress_update.session_duration_minutes
            )
            
            # 2. Create or update story learning metrics
            await cls._update_story_learning_metrics(progress_update)
            
            # 3. Integrate with main progress tracking
            await cls._integrate_with_main_progress(progress_update)
            
            # 4. Check and award achievements
            await cls._check_story_achievements(progress_update.user_id)
            
            # 5. Check for level advancement
            await cls._check_level_advancement(progress_update.user_id, progress_update.world_id)
            
            logger.info(f"[STORY_PROGRESS] ✅ Progress updated successfully for user {progress_update.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[STORY_PROGRESS] Error updating story progress: {str(e)}")
            return False
    
    @classmethod
    async def _update_subscription_usage(cls, user_id: str, duration_minutes: float) -> None:
        """Update subscription usage for story contributions"""
        try:
            # Track speaking time and increment session count
            from models import SpeakingTimeTrackingRequest
            
            tracking_request = SpeakingTimeTrackingRequest(
                user_id=user_id,
                speaking_minutes=duration_minutes,
                session_completed=True  # Story contributions count as completed sessions
            )
            
            await SubscriptionService.track_speaking_time(tracking_request)
            logger.info(f"[STORY_PROGRESS] Updated subscription usage: +{duration_minutes} minutes, +1 session")
            
        except Exception as e:
            logger.error(f"[STORY_PROGRESS] Error updating subscription usage: {str(e)}")
    
    @classmethod
    async def _update_story_learning_metrics(cls, progress_update: StoryProgressUpdate) -> None:
        """Create or update story learning metrics"""
        try:
            # Find existing metrics for this user and world
            existing_metrics = await database.story_learning_metrics.find_one({
                "user_id": progress_update.user_id,
                "world_id": progress_update.world_id
            })
            
            if existing_metrics:
                # Update existing metrics
                update_data = {
                    "$inc": {
                        "session_duration_minutes": progress_update.session_duration_minutes,
                        "contribution_count": 1
                    },
                    "$push": {
                        "vocabulary_acquired": {"$each": progress_update.vocabulary_learned},
                        "grammar_improvements": {"$each": progress_update.grammar_improvements},
                        "pronunciation_improvements": {"$each": progress_update.pronunciation_improvements},
                        "cultural_learning_moments": {"$each": progress_update.cultural_insights}
                    },
                    "$set": {
                        "story_engagement_score": progress_update.engagement_score,
                        "narrative_contribution_quality": progress_update.contribution_quality,
                        "collaborative_skills_score": progress_update.collaboration_score,
                        "updated_at": datetime.utcnow()
                    }
                }
                
                await database.story_learning_metrics.update_one(
                    {"_id": existing_metrics["_id"]},
                    update_data
                )
                
                logger.info(f"[STORY_PROGRESS] Updated existing learning metrics")
                
            else:
                # Create new metrics
                # Get user and world info for context
                user = await database.users.find_one(cls.get_user_query(progress_update.user_id))
                world = await database.story_worlds.find_one({"id": progress_update.world_id})
                
                new_metrics = StoryLearningMetrics(
                    user_id=progress_update.user_id,
                    world_id=progress_update.world_id,
                    contribution_id=progress_update.contribution_id,
                    vocabulary_acquired=progress_update.vocabulary_learned,
                    grammar_improvements=progress_update.grammar_improvements,
                    pronunciation_improvements=progress_update.pronunciation_improvements,
                    cultural_learning_moments=progress_update.cultural_insights,
                    story_engagement_score=progress_update.engagement_score,
                    narrative_contribution_quality=progress_update.contribution_quality,
                    collaborative_skills_score=progress_update.collaboration_score,
                    session_duration_minutes=progress_update.session_duration_minutes,
                    contribution_count=1,
                    language=world.get("language", "english") if world else "english",
                    proficiency_level=user.get("last_assessment_data", {}).get("level", "B1") if user else "B1"
                )
                
                await database.story_learning_metrics.insert_one(new_metrics.dict(by_alias=True))
                logger.info(f"[STORY_PROGRESS] Created new learning metrics")
                
        except Exception as e:
            logger.error(f"[STORY_PROGRESS] Error updating story learning metrics: {str(e)}")
    
    @classmethod
    async def _integrate_with_main_progress(cls, progress_update: StoryProgressUpdate) -> None:
        """Integrate story progress with main progress tracking system"""
        try:
            # Add story vocabulary to user's main vocabulary list
            if progress_update.vocabulary_learned:
                # Get user's current vocabulary or initialize
                user = await database.users.find_one(cls.get_user_query(progress_update.user_id))
                if user:
                    current_vocab = user.get("vocabulary_learned", [])
                    
                    # Add new vocabulary with story context
                    for vocab_item in progress_update.vocabulary_learned:
                        vocab_entry = {
                            **vocab_item,
                            "source": "story_world",
                            "world_id": progress_update.world_id,
                            "learned_at": datetime.utcnow()
                        }
                        current_vocab.append(vocab_entry)
                    
                    # Update user's vocabulary
                    await database.users.update_one(
                        cls.get_user_query(progress_update.user_id),
                        {"$set": {"vocabulary_learned": current_vocab}}
                    )
                    
                    logger.info(f"[STORY_PROGRESS] Added {len(progress_update.vocabulary_learned)} vocabulary items to main progress")
            
            # Add grammar improvements to user's main progress
            if progress_update.grammar_improvements:
                user = await database.users.find_one(cls.get_user_query(progress_update.user_id))
                if user:
                    current_grammar = user.get("grammar_improvements", [])
                    
                    for grammar_item in progress_update.grammar_improvements:
                        grammar_entry = {
                            **grammar_item,
                            "source": "story_world",
                            "world_id": progress_update.world_id,
                            "improved_at": datetime.utcnow()
                        }
                        current_grammar.append(grammar_entry)
                    
                    await database.users.update_one(
                        cls.get_user_query(progress_update.user_id),
                        {"$set": {"grammar_improvements": current_grammar}}
                    )
                    
                    logger.info(f"[STORY_PROGRESS] Added {len(progress_update.grammar_improvements)} grammar improvements to main progress")
            
        except Exception as e:
            logger.error(f"[STORY_PROGRESS] Error integrating with main progress: {str(e)}")
    
    @classmethod
    async def _check_story_achievements(cls, user_id: str) -> None:
        """Check and award story-specific achievements"""
        try:
            # Get user's story statistics
            story_stats = await cls._get_user_story_statistics(user_id)
            
            # Check each achievement
            for achievement_id, achievement in cls.STORY_ACHIEVEMENTS.items():
                # Check if user already has this achievement
                existing_achievement = await database.user_story_achievements.find_one({
                    "user_id": user_id,
                    "achievement_id": achievement_id
                })
                
                if existing_achievement:
                    continue  # Already earned
                
                # Check if requirements are met
                if cls._check_achievement_requirements(achievement, story_stats):
                    # Award achievement
                    new_achievement = UserStoryAchievement(
                        user_id=user_id,
                        achievement_id=achievement_id,
                        progress_data=story_stats
                    )
                    
                    await database.user_story_achievements.insert_one(new_achievement.dict(by_alias=True))
                    logger.info(f"[ACHIEVEMENTS] ✅ Awarded '{achievement.name}' to user {user_id}")
                    
                    # TODO: Send notification to user about new achievement
            
        except Exception as e:
            logger.error(f"[ACHIEVEMENTS] Error checking story achievements: {str(e)}")
    
    @classmethod
    async def _get_user_story_statistics(cls, user_id: str) -> Dict[str, Any]:
        """Get user's story-related statistics for achievement checking"""
        try:
            # Count contributions
            contributions_count = await database.story_contributions.count_documents({"user_id": user_id})
            
            # Count worlds created
            worlds_created_count = await database.story_worlds.count_documents({"creator_id": user_id})
            
            # Count completed stories (worlds where user contributed and story is completed)
            completed_stories_count = await database.story_worlds.count_documents({
                "status": "completed",
                "contributors": user_id
            })
            
            # Count cultural references learned
            cultural_refs_pipeline = [
                {"$match": {"user_id": user_id}},
                {"$unwind": "$cultural_learning_moments"},
                {"$count": "total"}
            ]
            cultural_refs_result = await database.story_learning_metrics.aggregate(cultural_refs_pipeline).to_list(1)
            cultural_references_count = cultural_refs_result[0]["total"] if cultural_refs_result else 0
            
            # Count vocabulary learned through stories
            vocab_pipeline = [
                {"$match": {"user_id": user_id}},
                {"$unwind": "$vocabulary_acquired"},
                {"$count": "total"}
            ]
            vocab_result = await database.story_learning_metrics.aggregate(vocab_pipeline).to_list(1)
            vocabulary_learned_count = vocab_result[0]["total"] if vocab_result else 0
            
            return {
                "contributions": contributions_count,
                "worlds_created": worlds_created_count,
                "completed_stories": completed_stories_count,
                "cultural_references": cultural_references_count,
                "vocabulary_learned": vocabulary_learned_count
            }
            
        except Exception as e:
            logger.error(f"[ACHIEVEMENTS] Error getting user story statistics: {str(e)}")
            return {}
    
    @classmethod
    def _check_achievement_requirements(cls, achievement: StoryAchievement, stats: Dict[str, Any]) -> bool:
        """Check if user meets achievement requirements"""
        try:
            requirements = achievement.requirements
            
            for req_key, req_value in requirements.items():
                user_value = stats.get(req_key, 0)
                if user_value < req_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"[ACHIEVEMENTS] Error checking achievement requirements: {str(e)}")
            return False
    
    @classmethod
    async def _check_level_advancement(cls, user_id: str, world_id: str) -> None:
        """Check if user should advance to next level based on story performance"""
        try:
            # Get user's story learning metrics
            metrics = await database.story_learning_metrics.find_one({
                "user_id": user_id,
                "world_id": world_id
            })
            
            if not metrics:
                return
            
            # Calculate performance scores
            engagement_score = metrics.get("story_engagement_score", 0.0)
            contribution_quality = metrics.get("narrative_contribution_quality", 0.0)
            collaboration_score = metrics.get("collaborative_skills_score", 0.0)
            
            # Average performance score
            avg_performance = (engagement_score + contribution_quality + collaboration_score) / 3
            
            # If performance is consistently high (>0.8), recommend level advancement
            if avg_performance > 0.8 and metrics.get("contribution_count", 0) >= 3:
                user = await database.users.find_one(cls.get_user_query(user_id))
                if user and user.get("last_assessment_data"):
                    current_level = user["last_assessment_data"].get("level", "A1")
                    next_level = cls._get_next_level(current_level)
                    
                    if next_level:
                        # Create level advancement recommendation
                        recommendation = {
                            "current_level": current_level,
                            "recommended_level": next_level,
                            "reason": "Excellent performance in story contributions",
                            "performance_score": avg_performance,
                            "contributions_count": metrics.get("contribution_count", 0),
                            "recommended_at": datetime.utcnow()
                        }
                        
                        # Store recommendation (could be used by assessment system)
                        await database.users.update_one(
                            cls.get_user_query(user_id),
                            {"$set": {"level_advancement_recommendation": recommendation}}
                        )
                        
                        logger.info(f"[LEVEL_ADVANCEMENT] Recommended {current_level} → {next_level} for user {user_id}")
            
        except Exception as e:
            logger.error(f"[LEVEL_ADVANCEMENT] Error checking level advancement: {str(e)}")
    
    @classmethod
    def _get_next_level(cls, current_level: str) -> Optional[str]:
        """Get the next level in the hierarchy"""
        try:
            current_index = cls.LEVEL_HIERARCHY.index(current_level)
            if current_index < len(cls.LEVEL_HIERARCHY) - 1:
                return cls.LEVEL_HIERARCHY[current_index + 1]
            return None
        except (ValueError, IndexError):
            return None
    
    @classmethod
    async def get_story_learning_analytics(cls, user_id: str, language: str) -> Optional[StoryLearningAnalytics]:
        """Get comprehensive story learning analytics for a user"""
        try:
            # Aggregate story metrics
            pipeline = [
                {"$match": {"user_id": user_id, "language": language}},
                {"$group": {
                    "_id": None,
                    "total_sessions": {"$sum": 1},
                    "total_minutes": {"$sum": "$session_duration_minutes"},
                    "total_contributions": {"$sum": "$contribution_count"},
                    "avg_engagement": {"$avg": "$story_engagement_score"},
                    "avg_quality": {"$avg": "$narrative_contribution_quality"},
                    "avg_collaboration": {"$avg": "$collaborative_skills_score"},
                    "worlds": {"$addToSet": "$world_id"}
                }}
            ]
            
            result = await database.story_learning_metrics.aggregate(pipeline).to_list(1)
            
            if not result:
                return None
            
            data = result[0]
            
            # Calculate learning rates (simplified)
            vocab_growth_rate = 0.0  # Could be calculated from vocabulary_acquired arrays
            grammar_improvement_rate = 0.0  # Could be calculated from grammar_improvements
            pronunciation_improvement_rate = 0.0  # Could be calculated from pronunciation_improvements
            
            # Get user's current effective level from assessment
            user = await database.users.find_one(cls.get_user_query(user_id))
            current_level = "A1"
            if user and user.get("last_assessment_data"):
                current_level = user["last_assessment_data"].get("level", "A1")
            
            analytics = StoryLearningAnalytics(
                user_id=user_id,
                language=language,
                total_story_sessions=data.get("total_sessions", 0),
                total_story_minutes=data.get("total_minutes", 0.0),
                total_contributions=data.get("total_contributions", 0),
                total_worlds_participated=len(data.get("worlds", [])),
                vocabulary_growth_rate=vocab_growth_rate,
                grammar_improvement_rate=grammar_improvement_rate,
                pronunciation_improvement_rate=pronunciation_improvement_rate,
                average_engagement_score=data.get("avg_engagement", 0.0),
                average_contribution_quality=data.get("avg_quality", 0.0),
                average_collaboration_score=data.get("avg_collaboration", 0.0),
                current_effective_level=current_level
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"[ANALYTICS] Error getting story learning analytics: {str(e)}")
            return None
    
    @classmethod
    async def get_user_story_achievements(cls, user_id: str) -> List[Dict[str, Any]]:
        """Get all story achievements for a user"""
        try:
            # Get earned achievements
            earned_achievements = await database.user_story_achievements.find(
                {"user_id": user_id}
            ).to_list(None)
            
            # Format achievements with details
            achievements = []
            for earned in earned_achievements:
                achievement_def = cls.STORY_ACHIEVEMENTS.get(earned["achievement_id"])
                if achievement_def:
                    achievements.append({
                        "id": earned["achievement_id"],
                        "name": achievement_def.name,
                        "description": achievement_def.description,
                        "icon": achievement_def.icon,
                        "category": achievement_def.category,
                        "earned_at": earned["earned_at"],
                        "reward_points": achievement_def.reward_points,
                        "earned": True
                    })
            
            return achievements
            
        except Exception as e:
            logger.error(f"[ACHIEVEMENTS] Error getting user story achievements: {str(e)}")
            return []
