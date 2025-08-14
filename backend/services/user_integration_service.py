from typing import Optional, Dict, Any
from bson import ObjectId
from database import database, users_collection

# Import UserResponse from main models file
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from models import UserResponse
except ImportError:
    # Fallback if import fails
    UserResponse = None

class UserIntegrationService:
    """Service for integrating world building with existing user systems"""
    
    @staticmethod
    async def get_user_proficiency(user_id: str) -> Optional[str]:
        """
        Get user's CEFR proficiency level from last assessment data
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            CEFR level (A1, A2, B1, B2, C1, C2) or None if not available
        """
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                print(f"⚠️ [USER_INTEGRATION] User {user_id} not found")
                return None
            
            # Check last assessment data for recommended level
            last_assessment = user.get("last_assessment_data")
            if last_assessment and "recommended_level" in last_assessment:
                proficiency_level = last_assessment["recommended_level"]
                print(f"✅ [USER_INTEGRATION] User {user_id} proficiency from assessment: {proficiency_level}")
                return proficiency_level
            
            # Fallback to preferred level if no assessment data
            preferred_level = user.get("preferred_level")
            if preferred_level:
                print(f"✅ [USER_INTEGRATION] User {user_id} proficiency from preference: {preferred_level}")
                return preferred_level
            
            print(f"⚠️ [USER_INTEGRATION] No proficiency data found for user {user_id}")
            return None
            
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error getting user proficiency: {str(e)}")
            return None
    
    @staticmethod
    async def update_practice_metrics(user_id: str, minutes: float) -> bool:
        """
        Update user's practice minutes used for subscription tracking
        
        Args:
            user_id: User's ObjectId as string
            minutes: Minutes to add to practice_minutes_used
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"practice_minutes_used": minutes}}
            )
            
            if result.modified_count > 0:
                print(f"✅ [USER_INTEGRATION] Updated practice minutes for user {user_id}: +{minutes} minutes")
                return True
            else:
                print(f"⚠️ [USER_INTEGRATION] No update made for user {user_id} practice minutes")
                return False
                
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error updating practice metrics: {str(e)}")
            return False
    
    @staticmethod
    async def check_subscription_limits(user_id: str) -> Dict[str, Any]:
        """
        Check user's subscription limits and current usage
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Dictionary with subscription status and limits information
        """
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {
                    "has_access": False,
                    "reason": "User not found",
                    "subscription_status": None
                }
            
            subscription_status = user.get("subscription_status")
            subscription_plan = user.get("subscription_plan")
            
            # Check if user has active subscription
            if subscription_status not in ["active", "trialing"]:
                return {
                    "has_access": False,
                    "reason": "No active subscription",
                    "subscription_status": subscription_status,
                    "subscription_plan": subscription_plan
                }
            
            # Get usage metrics
            practice_sessions_used = user.get("practice_sessions_used", 0)
            practice_minutes_used = user.get("practice_minutes_used", 0.0)
            
            # Define plan limits (these should match subscription_service.py)
            plan_limits = {
                "try_learn": {
                    "monthly_sessions": 10,
                    "monthly_minutes": 50
                },
                "fluency_builder": {
                    "monthly_sessions": 50,
                    "monthly_minutes": 250
                },
                "team_mastery": {
                    "monthly_sessions": -1,  # Unlimited
                    "monthly_minutes": -1    # Unlimited
                }
            }
            
            current_plan_limits = plan_limits.get(subscription_plan, plan_limits["try_learn"])
            
            # Check session limits
            session_limit = current_plan_limits["monthly_sessions"]
            sessions_available = session_limit == -1 or practice_sessions_used < session_limit
            
            # Check minute limits
            minute_limit = current_plan_limits["monthly_minutes"]
            minutes_available = minute_limit == -1 or practice_minutes_used < minute_limit
            
            has_access = sessions_available and minutes_available
            
            result = {
                "has_access": has_access,
                "subscription_status": subscription_status,
                "subscription_plan": subscription_plan,
                "usage": {
                    "sessions_used": practice_sessions_used,
                    "sessions_limit": session_limit,
                    "sessions_available": sessions_available,
                    "minutes_used": practice_minutes_used,
                    "minutes_limit": minute_limit,
                    "minutes_available": minutes_available
                }
            }
            
            if not has_access:
                if not sessions_available:
                    result["reason"] = f"Session limit reached ({practice_sessions_used}/{session_limit})"
                elif not minutes_available:
                    result["reason"] = f"Minute limit reached ({practice_minutes_used:.1f}/{minute_limit})"
            
            print(f"✅ [USER_INTEGRATION] Subscription check for user {user_id}: {result}")
            return result
            
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error checking subscription limits: {str(e)}")
            return {
                "has_access": False,
                "reason": f"Error checking subscription: {str(e)}",
                "subscription_status": None
            }
    
    @staticmethod
    async def get_user_display_info(user_id: str) -> Dict[str, Any]:
        """
        Get user's display information (name, avatar, etc.) for world building UI
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Dictionary with user display information
        """
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {
                    "user_id": user_id,
                    "name": "Unknown User",
                    "email": None,
                    "avatar_url": None,
                    "preferred_language": None,
                    "preferred_level": None,
                    "found": False
                }
            
            # Extract display information
            display_info = {
                "user_id": user_id,
                "name": user.get("name", "Anonymous User"),
                "email": user.get("email"),
                "avatar_url": user.get("avatar_url"),  # If we add avatar support later
                "preferred_language": user.get("preferred_language"),
                "preferred_level": user.get("preferred_level"),
                "found": True,
                "is_verified": user.get("is_verified", False),
                "subscription_plan": user.get("subscription_plan"),
                "subscription_status": user.get("subscription_status")
            }
            
            print(f"✅ [USER_INTEGRATION] Retrieved display info for user {user_id}: {user.get('name')}")
            return display_info
            
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error getting user display info: {str(e)}")
            return {
                "user_id": user_id,
                "name": "Error Loading User",
                "email": None,
                "avatar_url": None,
                "preferred_language": None,
                "preferred_level": None,
                "found": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_user_language_preferences(user_id: str) -> Dict[str, Any]:
        """
        Get user's language learning preferences and history
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Dictionary with language preferences and learning history
        """
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {
                    "preferred_language": None,
                    "preferred_level": None,
                    "assessment_history": [],
                    "languages_practiced": []
                }
            
            # Get assessment history if available
            assessment_history = []
            if "assessment_history" in user:
                assessment_history = [user["assessment_history"]]  # Single assessment format
            
            # Extract languages from assessment history
            languages_practiced = []
            for assessment in assessment_history:
                if "language" in assessment:
                    lang = assessment["language"]
                    if lang not in languages_practiced:
                        languages_practiced.append(lang)
            
            # Add preferred language if not in practiced list
            preferred_lang = user.get("preferred_language")
            if preferred_lang and preferred_lang not in languages_practiced:
                languages_practiced.append(preferred_lang)
            
            preferences = {
                "preferred_language": preferred_lang,
                "preferred_level": user.get("preferred_level"),
                "assessment_history": assessment_history,
                "languages_practiced": languages_practiced,
                "last_assessment_data": user.get("last_assessment_data")
            }
            
            print(f"✅ [USER_INTEGRATION] Retrieved language preferences for user {user_id}")
            return preferences
            
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error getting language preferences: {str(e)}")
            return {
                "preferred_language": None,
                "preferred_level": None,
                "assessment_history": [],
                "languages_practiced": [],
                "error": str(e)
            }
    
    @staticmethod
    async def increment_session_usage(user_id: str) -> bool:
        """
        Increment user's session usage counter for subscription tracking
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"practice_sessions_used": 1}}
            )
            
            if result.modified_count > 0:
                print(f"✅ [USER_INTEGRATION] Incremented session usage for user {user_id}")
                return True
            else:
                print(f"⚠️ [USER_INTEGRATION] No update made for user {user_id} session usage")
                return False
                
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error incrementing session usage: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_stats_for_world_building(user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics relevant to world building features
        
        Args:
            user_id: User's ObjectId as string
            
        Returns:
            Dictionary with user statistics for world building
        """
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {"error": "User not found"}
            
            # Get conversation sessions for additional stats
            conversation_sessions = database.conversation_sessions
            user_sessions = await conversation_sessions.find({"user_id": user_id}).to_list(1000)
            
            # Calculate speaking time from sessions
            total_speaking_minutes = sum(session.get("duration_minutes", 0) for session in user_sessions)
            
            # Get unique languages and topics from sessions
            languages_used = set()
            topics_practiced = set()
            
            for session in user_sessions:
                if session.get("language"):
                    languages_used.add(session["language"])
                if session.get("topic"):
                    topics_practiced.add(session["topic"])
            
            stats = {
                "user_id": user_id,
                "name": user.get("name", "Anonymous"),
                "total_sessions": len(user_sessions),
                "total_speaking_minutes": total_speaking_minutes,
                "languages_practiced": list(languages_used),
                "topics_practiced": list(topics_practiced),
                "preferred_language": user.get("preferred_language"),
                "preferred_level": user.get("preferred_level"),
                "subscription_plan": user.get("subscription_plan"),
                "subscription_status": user.get("subscription_status"),
                "account_created": user.get("created_at"),
                "last_login": user.get("last_login"),
                "is_verified": user.get("is_verified", False),
                "assessment_completed": user.get("last_assessment_data") is not None
            }
            
            # Add proficiency level from assessment if available
            if user.get("last_assessment_data"):
                assessment = user["last_assessment_data"]
                stats["assessed_level"] = assessment.get("recommended_level")
                stats["overall_score"] = assessment.get("overall_score")
            
            print(f"✅ [USER_INTEGRATION] Retrieved comprehensive stats for user {user_id}")
            return stats
            
        except Exception as e:
            print(f"❌ [USER_INTEGRATION] Error getting user stats: {str(e)}")
            return {"error": str(e)}

# Global service instance
user_integration_service = UserIntegrationService()
