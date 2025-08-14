from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from database import database
from services.world_building_service import world_building_service
from services.user_integration_service import user_integration_service
from utils.feature_flags import feature_flags

class WorldBuildingHelpers:
    """Helper functions for world building database operations and utilities"""
    
    @staticmethod
    async def initialize_world_building_system():
        """Initialize the world building system with indexes and seed data"""
        try:
            print("🚀 [WORLD_BUILDING] Initializing world building system...")
            
            # Check if feature is enabled
            if not feature_flags.is_world_building_enabled():
                print("⚠️ [WORLD_BUILDING] World building feature is disabled")
                return False
            
            # Initialize database indexes
            await world_building_service.initialize_indexes()
            
            # Seed database with sample data if empty
            from utils.world_building_seed_data import WorldBuildingSeedData
            await WorldBuildingSeedData.seed_database()
            
            print("✅ [WORLD_BUILDING] World building system initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error initializing system: {str(e)}")
            return False
    
    @staticmethod
    async def get_world_building_stats() -> Dict[str, Any]:
        """Get comprehensive statistics about the world building system"""
        try:
            # Get collection references
            story_worlds = database.story_worlds
            story_contributions = database.story_contributions
            world_invitations = database.world_invitations
            
            # Basic counts
            total_worlds = await story_worlds.count_documents({})
            active_worlds = await story_worlds.count_documents({"status": "active"})
            total_contributions = await story_contributions.count_documents({})
            pending_invitations = await world_invitations.count_documents({"status": "pending"})
            
            # Language distribution
            language_pipeline = [
                {"$group": {"_id": "$language", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            language_stats = await story_worlds.aggregate(language_pipeline).to_list(10)
            
            # Level distribution
            level_pipeline = [
                {"$group": {"_id": "$target_level", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            level_stats = await story_worlds.aggregate(level_pipeline).to_list(10)
            
            # Genre distribution
            genre_pipeline = [
                {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            genre_stats = await story_worlds.aggregate(genre_pipeline).to_list(10)
            
            # Most active worlds (by contribution count)
            active_worlds_pipeline = [
                {"$match": {"status": "active"}},
                {"$lookup": {
                    "from": "story_contributions",
                    "localField": "_id",
                    "foreignField": "world_id",
                    "as": "contributions"
                }},
                {"$addFields": {"contribution_count": {"$size": "$contributions"}}},
                {"$sort": {"contribution_count": -1}},
                {"$limit": 5},
                {"$project": {
                    "title": 1,
                    "language": 1,
                    "target_level": 1,
                    "contribution_count": 1,
                    "contributors": {"$size": "$contributors"}
                }}
            ]
            most_active_worlds = await story_worlds.aggregate(active_worlds_pipeline).to_list(5)
            
            # Recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_worlds = await story_worlds.count_documents({
                "created_at": {"$gte": seven_days_ago}
            })
            recent_contributions = await story_contributions.count_documents({
                "created_at": {"$gte": seven_days_ago}
            })
            
            return {
                "overview": {
                    "total_worlds": total_worlds,
                    "active_worlds": active_worlds,
                    "total_contributions": total_contributions,
                    "pending_invitations": pending_invitations
                },
                "distributions": {
                    "languages": [{"language": item["_id"], "count": item["count"]} for item in language_stats],
                    "levels": [{"level": item["_id"], "count": item["count"]} for item in level_stats],
                    "genres": [{"genre": item["_id"], "count": item["count"]} for item in genre_stats]
                },
                "most_active_worlds": most_active_worlds,
                "recent_activity": {
                    "new_worlds_last_7_days": recent_worlds,
                    "new_contributions_last_7_days": recent_contributions
                },
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting stats: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def cleanup_expired_invitations():
        """Clean up expired invitations from the database"""
        try:
            world_invitations = database.world_invitations
            
            # Count expired invitations
            expired_count = await world_invitations.count_documents({
                "status": "pending",
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            if expired_count > 0:
                # Update expired invitations
                result = await world_invitations.update_many(
                    {
                        "status": "pending",
                        "expires_at": {"$lt": datetime.utcnow()}
                    },
                    {"$set": {"status": "expired"}}
                )
                
                print(f"✅ [WORLD_BUILDING] Marked {result.modified_count} invitations as expired")
                return result.modified_count
            else:
                print("ℹ️ [WORLD_BUILDING] No expired invitations found")
                return 0
                
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error cleaning up invitations: {str(e)}")
            return 0
    
    @staticmethod
    async def validate_world_access(world_id: str, user_id: str) -> Tuple[bool, str]:
        """
        Validate if a user has access to a specific world
        
        Args:
            world_id: World's ObjectId as string
            user_id: User's ObjectId as string
            
        Returns:
            Tuple of (has_access: bool, reason: str)
        """
        try:
            # Check if world exists
            world = await world_building_service.get_world(world_id, user_id)
            if not world:
                return False, "World not found or access denied"
            
            # Check subscription limits
            subscription_check = await user_integration_service.check_subscription_limits(user_id)
            if not subscription_check.get("has_access", False):
                return False, subscription_check.get("reason", "Subscription limit reached")
            
            # Check if user is a contributor
            user_object_id = ObjectId(user_id)
            if user_object_id not in [ObjectId(contrib_id) for contrib_id in world.contributors]:
                return False, "User is not a contributor to this world"
            
            # Check world status
            if world.status not in ["active", "draft"]:
                return False, f"World is {world.status} and not available for contributions"
            
            return True, "Access granted"
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error validating world access: {str(e)}")
            return False, f"Error validating access: {str(e)}"
    
    @staticmethod
    async def get_user_world_summary(user_id: str) -> Dict[str, Any]:
        """
        Get a summary of worlds associated with a user
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Dictionary with user's world summary
        """
        try:
            # Get user's worlds
            user_worlds = await world_building_service.get_user_worlds(user_id)
            
            # Separate created vs contributed worlds
            created_worlds = []
            contributed_worlds = []
            
            user_object_id = ObjectId(user_id)
            
            for world in user_worlds:
                if ObjectId(world.creator_id) == user_object_id:
                    created_worlds.append(world)
                else:
                    contributed_worlds.append(world)
            
            # Get contribution statistics
            story_contributions = database.story_contributions
            user_contributions = await story_contributions.find({
                "contributor_id": user_object_id
            }).to_list(1000)
            
            # Calculate statistics
            total_contributions = len(user_contributions)
            total_speaking_time = sum(contrib.get("duration_seconds", 0) for contrib in user_contributions) / 60  # Convert to minutes
            
            # Get unique languages practiced
            languages_practiced = set()
            for world in user_worlds:
                languages_practiced.add(world.language)
            
            # Get favorite genres
            genre_counts = {}
            for world in user_worlds:
                genre = world.genre
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "user_id": user_id,
                "worlds_created": len(created_worlds),
                "worlds_contributed_to": len(contributed_worlds),
                "total_worlds": len(user_worlds),
                "total_contributions": total_contributions,
                "total_speaking_time_minutes": total_speaking_time,
                "languages_practiced": list(languages_practiced),
                "favorite_genres": [genre for genre, count in favorite_genres],
                "created_worlds": [
                    {
                        "id": str(world.id),
                        "title": world.title,
                        "language": world.language,
                        "target_level": world.target_level,
                        "status": world.status,
                        "contributors_count": len(world.contributors)
                    }
                    for world in created_worlds[:5]  # Limit to 5 most recent
                ],
                "contributed_worlds": [
                    {
                        "id": str(world.id),
                        "title": world.title,
                        "language": world.language,
                        "target_level": world.target_level,
                        "status": world.status,
                        "creator_id": str(world.creator_id)
                    }
                    for world in contributed_worlds[:5]  # Limit to 5 most recent
                ]
            }
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error getting user world summary: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def check_world_building_health() -> Dict[str, Any]:
        """
        Perform health checks on the world building system
        
        Returns:
            Dictionary with health check results
        """
        try:
            health_status = {
                "overall_status": "healthy",
                "checks": {},
                "warnings": [],
                "errors": [],
                "timestamp": datetime.utcnow()
            }
            
            # Check database connectivity
            try:
                await database.story_worlds.find_one({})
                health_status["checks"]["database_connectivity"] = "✅ Connected"
            except Exception as e:
                health_status["checks"]["database_connectivity"] = f"❌ Error: {str(e)}"
                health_status["errors"].append("Database connectivity failed")
                health_status["overall_status"] = "unhealthy"
            
            # Check indexes
            try:
                indexes = await database.story_worlds.list_indexes().to_list(20)
                required_indexes = ["language_level_status_created", "creator_status"]
                existing_index_names = [idx.get("name", "") for idx in indexes]
                
                missing_indexes = [idx for idx in required_indexes if idx not in existing_index_names]
                if missing_indexes:
                    health_status["warnings"].append(f"Missing indexes: {missing_indexes}")
                    health_status["checks"]["indexes"] = f"⚠️ Missing: {missing_indexes}"
                else:
                    health_status["checks"]["indexes"] = "✅ All required indexes present"
            except Exception as e:
                health_status["checks"]["indexes"] = f"❌ Error checking indexes: {str(e)}"
                health_status["errors"].append("Index check failed")
            
            # Check feature flag
            if not feature_flags.is_world_building_enabled():
                health_status["warnings"].append("World building feature is disabled")
                health_status["checks"]["feature_flag"] = "⚠️ Disabled"
            else:
                health_status["checks"]["feature_flag"] = "✅ Enabled"
            
            # Check for orphaned data
            try:
                # Check for contributions without valid worlds
                contributions_pipeline = [
                    {
                        "$lookup": {
                            "from": "story_worlds",
                            "localField": "world_id",
                            "foreignField": "_id",
                            "as": "world"
                        }
                    },
                    {
                        "$match": {"world": {"$size": 0}}
                    },
                    {
                        "$count": "orphaned_contributions"
                    }
                ]
                
                orphaned_result = await database.story_contributions.aggregate(contributions_pipeline).to_list(1)
                orphaned_count = orphaned_result[0]["orphaned_contributions"] if orphaned_result else 0
                
                if orphaned_count > 0:
                    health_status["warnings"].append(f"Found {orphaned_count} orphaned contributions")
                    health_status["checks"]["data_integrity"] = f"⚠️ {orphaned_count} orphaned contributions"
                else:
                    health_status["checks"]["data_integrity"] = "✅ No orphaned data found"
                    
            except Exception as e:
                health_status["checks"]["data_integrity"] = f"❌ Error checking data integrity: {str(e)}"
            
            # Set overall status based on errors
            if health_status["errors"]:
                health_status["overall_status"] = "unhealthy"
            elif health_status["warnings"]:
                health_status["overall_status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    @staticmethod
    async def migrate_world_building_data():
        """
        Perform any necessary data migrations for world building collections
        """
        try:
            print("🔄 [WORLD_BUILDING] Starting data migration...")
            
            # Example migration: Add missing fields to existing worlds
            story_worlds = database.story_worlds
            
            # Find worlds missing the 'featured' field
            worlds_to_update = await story_worlds.find({"featured": {"$exists": False}}).to_list(1000)
            
            if worlds_to_update:
                # Update worlds with missing featured field
                result = await story_worlds.update_many(
                    {"featured": {"$exists": False}},
                    {"$set": {"featured": False}}
                )
                print(f"✅ [WORLD_BUILDING] Updated {result.modified_count} worlds with featured field")
            
            # Add any other migrations here as needed
            
            print("✅ [WORLD_BUILDING] Data migration completed")
            return True
            
        except Exception as e:
            print(f"❌ [WORLD_BUILDING] Error during migration: {str(e)}")
            return False

# Global helpers instance
world_building_helpers = WorldBuildingHelpers()
