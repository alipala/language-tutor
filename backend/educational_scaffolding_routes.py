from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging

from auth import get_current_user
from models import UserResponse
from models.educational_scaffolding_models import (
    LearningGateResult, StoryProgressUpdate, StoryLearningAnalytics
)
from services.educational_scaffolding_service import EducationalScaffoldingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/educational-scaffolding", tags=["educational-scaffolding"])

@router.get("/learning-gates/{world_id}")
async def check_learning_gates(
    world_id: str,
    language: str,
    current_user: UserResponse = Depends(get_current_user)
) -> LearningGateResult:
    """
    Check if user meets all learning gates before allowing story contribution
    
    Gates checked:
    1. User has completed assessment in the language
    2. User's level matches world ±1 level
    3. User has practiced recently (last 7 days)
    4. User has sessions remaining in subscription
    """
    try:
        logger.info(f"[LEARNING_GATES_API] Checking gates for user {current_user.id} in world {world_id}")
        
        result = await EducationalScaffoldingService.check_learning_gates(
            user_id=current_user.id,
            world_id=world_id,
            language=language
        )
        
        logger.info(f"[LEARNING_GATES_API] Gate check result: can_contribute={result.can_contribute}")
        return result
        
    except Exception as e:
        logger.error(f"[LEARNING_GATES_API] Error checking learning gates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check learning gates: {str(e)}"
        )

@router.post("/progress-update")
async def update_story_progress(
    progress_update: StoryProgressUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update user's story learning progress after each contribution
    
    Updates:
    - Subscription usage (minutes and sessions)
    - Story learning metrics
    - Main progress integration
    - Achievement checking
    - Level advancement checking
    """
    try:
        logger.info(f"[PROGRESS_UPDATE_API] Updating progress for user {current_user.id}")
        
        # Ensure the progress update is for the current user
        if progress_update.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Cannot update progress for another user"
            )
        
        success = await EducationalScaffoldingService.update_story_progress(progress_update)
        
        if success:
            logger.info(f"[PROGRESS_UPDATE_API] ✅ Progress updated successfully")
            return {
                "success": True,
                "message": "Story progress updated successfully",
                "user_id": current_user.id,
                "world_id": progress_update.world_id,
                "session_duration": progress_update.session_duration_minutes
            }
        else:
            logger.error(f"[PROGRESS_UPDATE_API] ❌ Failed to update progress")
            raise HTTPException(
                status_code=500,
                detail="Failed to update story progress"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PROGRESS_UPDATE_API] Error updating story progress: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update story progress: {str(e)}"
        )

@router.get("/analytics/{language}")
async def get_story_learning_analytics(
    language: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Optional[StoryLearningAnalytics]:
    """
    Get comprehensive story learning analytics for the user in a specific language
    
    Returns:
    - Total story sessions, minutes, contributions
    - Learning progress rates
    - Engagement metrics
    - Level progression history
    """
    try:
        logger.info(f"[ANALYTICS_API] Getting story analytics for user {current_user.id} in {language}")
        
        analytics = await EducationalScaffoldingService.get_story_learning_analytics(
            user_id=current_user.id,
            language=language
        )
        
        if analytics:
            logger.info(f"[ANALYTICS_API] ✅ Analytics retrieved: {analytics.total_story_sessions} sessions")
        else:
            logger.info(f"[ANALYTICS_API] No analytics found for user in {language}")
        
        return analytics
        
    except Exception as e:
        logger.error(f"[ANALYTICS_API] Error getting story analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get story analytics: {str(e)}"
        )

@router.get("/achievements")
async def get_story_achievements(
    current_user: UserResponse = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all story-specific achievements for the user
    
    Returns list of achievements with:
    - Achievement details (name, description, icon)
    - Earned status and date
    - Reward points
    - Category
    """
    try:
        logger.info(f"[ACHIEVEMENTS_API] Getting story achievements for user {current_user.id}")
        
        achievements = await EducationalScaffoldingService.get_user_story_achievements(current_user.id)
        
        logger.info(f"[ACHIEVEMENTS_API] ✅ Retrieved {len(achievements)} story achievements")
        return achievements
        
    except Exception as e:
        logger.error(f"[ACHIEVEMENTS_API] Error getting story achievements: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get story achievements: {str(e)}"
        )

@router.get("/achievements/available")
async def get_available_story_achievements() -> List[Dict[str, Any]]:
    """
    Get all available story achievements (for display purposes)
    
    Returns list of all possible story achievements with their requirements
    """
    try:
        logger.info(f"[ACHIEVEMENTS_API] Getting available story achievements")
        
        available_achievements = []
        for achievement_id, achievement in EducationalScaffoldingService.STORY_ACHIEVEMENTS.items():
            available_achievements.append({
                "id": achievement_id,
                "name": achievement.name,
                "description": achievement.description,
                "icon": achievement.icon,
                "category": achievement.category,
                "requirements": achievement.requirements,
                "reward_points": achievement.reward_points,
                "is_hidden": achievement.is_hidden
            })
        
        logger.info(f"[ACHIEVEMENTS_API] ✅ Retrieved {len(available_achievements)} available achievements")
        return available_achievements
        
    except Exception as e:
        logger.error(f"[ACHIEVEMENTS_API] Error getting available achievements: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available achievements: {str(e)}"
        )

@router.get("/level-compatibility/{world_id}")
async def check_level_compatibility(
    world_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if user's level is compatible with a specific world
    
    Returns compatibility status and level information
    """
    try:
        logger.info(f"[LEVEL_COMPATIBILITY_API] Checking compatibility for user {current_user.id} and world {world_id}")
        
        # Get user's assessment data
        from database import database
        user = await database.users.find_one(EducationalScaffoldingService.get_user_query(current_user.id))
        world = await database.story_worlds.find_one({"id": world_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        
        user_assessment = user.get("last_assessment_data")
        world_level = world.get("target_level", "B1")
        
        if not user_assessment:
            return {
                "compatible": False,
                "user_level": None,
                "world_level": world_level,
                "reason": "No assessment completed",
                "recommendation": "Complete a speaking assessment first"
            }
        
        user_level = user_assessment.get("level", "A1")
        compatible = EducationalScaffoldingService._check_level_compatibility(user_level, world_level)
        
        result = {
            "compatible": compatible,
            "user_level": user_level,
            "world_level": world_level,
            "reason": "Level match" if compatible else "Level mismatch",
            "recommendation": "You can join this world" if compatible else f"Find a world suitable for {user_level} level"
        }
        
        logger.info(f"[LEVEL_COMPATIBILITY_API] ✅ Compatibility check: {compatible}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LEVEL_COMPATIBILITY_API] Error checking level compatibility: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check level compatibility: {str(e)}"
        )

@router.get("/learning-metrics/{world_id}")
async def get_world_learning_metrics(
    world_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Get user's learning metrics for a specific world
    
    Returns detailed learning metrics including:
    - Vocabulary acquired
    - Grammar improvements
    - Pronunciation progress
    - Cultural insights
    - Engagement scores
    """
    try:
        logger.info(f"[LEARNING_METRICS_API] Getting metrics for user {current_user.id} in world {world_id}")
        
        from database import database
        metrics = await database.story_learning_metrics.find_one({
            "user_id": current_user.id,
            "world_id": world_id
        })
        
        if not metrics:
            logger.info(f"[LEARNING_METRICS_API] No metrics found for user in world {world_id}")
            return None
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in metrics:
            metrics["_id"] = str(metrics["_id"])
        
        # Format dates for JSON serialization
        if "created_at" in metrics:
            metrics["created_at"] = metrics["created_at"].isoformat()
        if "updated_at" in metrics:
            metrics["updated_at"] = metrics["updated_at"].isoformat()
        
        logger.info(f"[LEARNING_METRICS_API] ✅ Retrieved metrics: {metrics.get('contribution_count', 0)} contributions")
        return metrics
        
    except Exception as e:
        logger.error(f"[LEARNING_METRICS_API] Error getting learning metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning metrics: {str(e)}"
        )

@router.get("/dashboard-stats")
async def get_story_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get story-related statistics for the user's dashboard
    
    Returns:
    - Total story contributions
    - Worlds participated in
    - Story achievements earned
    - Recent story activity
    """
    try:
        logger.info(f"[DASHBOARD_STATS_API] Getting dashboard stats for user {current_user.id}")
        
        from database import database
        
        # Get story statistics
        story_stats = await EducationalScaffoldingService._get_user_story_statistics(current_user.id)
        
        # Get recent story activity (last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_contributions = await database.story_contributions.count_documents({
            "user_id": current_user.id,
            "created_at": {"$gte": seven_days_ago}
        })
        
        # Get story achievements count
        achievements_count = await database.user_story_achievements.count_documents({
            "user_id": current_user.id
        })
        
        # Get total story minutes
        metrics_pipeline = [
            {"$match": {"user_id": current_user.id}},
            {"$group": {
                "_id": None,
                "total_minutes": {"$sum": "$session_duration_minutes"},
                "total_sessions": {"$sum": 1}
            }}
        ]
        
        metrics_result = await database.story_learning_metrics.aggregate(metrics_pipeline).to_list(1)
        total_story_minutes = metrics_result[0]["total_minutes"] if metrics_result else 0.0
        total_story_sessions = metrics_result[0]["total_sessions"] if metrics_result else 0
        
        dashboard_stats = {
            "total_contributions": story_stats.get("contributions", 0),
            "worlds_participated": story_stats.get("total_worlds_participated", 0),
            "worlds_created": story_stats.get("worlds_created", 0),
            "completed_stories": story_stats.get("completed_stories", 0),
            "story_achievements": achievements_count,
            "recent_contributions": recent_contributions,
            "total_story_minutes": total_story_minutes,
            "total_story_sessions": total_story_sessions,
            "vocabulary_learned": story_stats.get("vocabulary_learned", 0),
            "cultural_references": story_stats.get("cultural_references", 0)
        }
        
        logger.info(f"[DASHBOARD_STATS_API] ✅ Dashboard stats retrieved")
        return dashboard_stats
        
    except Exception as e:
        logger.error(f"[DASHBOARD_STATS_API] Error getting dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )
