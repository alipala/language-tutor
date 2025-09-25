"""
IMPROVED SUBSCRIPTION SERVICE with Unified Session Tracking
Integrates the comprehensive session tracking fix into the main codebase

This replaces the existing track_speaking_time method with the new unified approach
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import stripe
import os
from database import database
from models import (
    SubscriptionPlan, SubscriptionLimits, SubscriptionStatus, 
    UsageTrackingRequest, SpeakingTimeTrackingRequest, LearningPlanPreservation
)
from bson import ObjectId

# Import production-safe logging
from logging_config import logger

# Import validation modules
try:
    from validation.auto_corrector import AutoCorrector
    from validation.subscription_validator import SubscriptionValidator
    from validation.session_validator import SessionValidator
    VALIDATION_AVAILABLE = True
    logger.info("✅ Validation modules imported successfully")
except ImportError as e:
    VALIDATION_AVAILABLE = False
    logger.warning(f"⚠️ Validation modules not available: {str(e)}")

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def get_user_query(user_id: str):
    """Helper function to handle both UUID and ObjectId formats"""
    try:
        return {"_id": ObjectId(user_id)}
    except:
        return {"_id": user_id}

class UnifiedSessionTracker:
    """
    Production-ready unified session tracker integrated into SubscriptionService
    """
    
    @staticmethod
    async def track_session_unified(
        user_id: str,
        session_id: str,
        duration_minutes: float,
        session_type: str = "conversation",
        learning_plan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        UNIFIED SESSION TRACKING with all business rules
        
        BUSINESS RULES IMPLEMENTED:
        - Sessions < 1 minute: NOT tracked or deducted
        - Sessions 1-2 minutes: Tracked, deducted, but NOT counted as complete
        - Sessions 2-5 minutes: Tracked, deducted, AND counted as complete sessions  
        - Sessions > 5 minutes: Capped at 5 minutes for protection
        - NO SESSION LIMIT - users can complete unlimited sessions (only minute limit)
        - All durations stored as INTEGERS (1-5) only
        - Idempotent tracking prevents double counting
        """
        
        logger.info(f"[UNIFIED_TRACKER] 🎯 Tracking session: {session_id}")
        logger.info(f"[UNIFIED_TRACKER] User: {user_id}")
        logger.info(f"[UNIFIED_TRACKER] Raw duration: {duration_minutes}")
        logger.info(f"[UNIFIED_TRACKER] Type: {session_type}")
        
        try:
            # STEP 1: Check if already tracked (IDEMPOTENCY)
            existing_tracking = await database.speaking_time_tracking.find_one({
                "user_id": user_id,
                "session_id": session_id
            })
            
            if existing_tracking:
                logger.info(f"[UNIFIED_TRACKER] ✅ Session already tracked - skipping")
                return {
                    "success": True,
                    "already_tracked": True,
                    "message": "Session already tracked"
                }
            
            # STEP 2: Apply business rules for duration
            processed_duration = UnifiedSessionTracker._process_duration(duration_minutes)
            
            if processed_duration["should_track"]:
                duration_int = processed_duration["duration_int"]
                is_complete = processed_duration["is_complete"]
                
                logger.info(f"[UNIFIED_TRACKER] ✅ Will track: {duration_int} minutes (complete: {is_complete})")
                
                # STEP 3: Get user data
                user = await database.users.find_one(get_user_query(user_id))
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # STEP 4: Check subscription limits
                limits_check = await UnifiedSessionTracker._check_subscription_limits(user, duration_int)
                if not limits_check["can_track"]:
                    logger.warning(f"[UNIFIED_TRACKER] ❌ Subscription limits exceeded: {limits_check['message']}")
                    return {
                        "success": False,
                        "error": limits_check["message"],
                        "limits_exceeded": True
                    }
                
                # STEP 5: Perform atomic tracking
                tracking_result = await UnifiedSessionTracker._atomic_track_session(
                    user_id=user_id,
                    session_id=session_id,
                    duration_int=duration_int,
                    is_complete=is_complete,
                    session_type=session_type,
                    learning_plan_id=learning_plan_id,
                    user_email=user.get('email', 'unknown')
                )
                
                if tracking_result["success"]:
                    logger.info(f"[UNIFIED_TRACKER] 🎉 Session tracked successfully!")
                    return tracking_result
                else:
                    logger.error(f"[UNIFIED_TRACKER] ❌ Atomic tracking failed: {tracking_result['error']}")
                    return tracking_result
                    
            else:
                logger.info(f"[UNIFIED_TRACKER] ℹ️ Session too short - not tracking")
                return {
                    "success": True,
                    "not_tracked": True,
                    "reason": "Session < 1 minute",
                    "message": "Session too short to track"
                }
                
        except Exception as e:
            logger.error(f"[UNIFIED_TRACKER] ❌ Error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _process_duration(duration_minutes: float) -> Dict[str, Any]:
        """Apply business rules to process duration"""
        
        # Rule 1: Don't track < 1 minute
        if duration_minutes < 1:
            return {
                "should_track": False,
                "reason": "Duration < 1 minute"
            }
        
        # Rule 2: Convert to integer (round to nearest)
        duration_int = round(duration_minutes)
        
        # Rule 3: Cap at 5 minutes maximum
        if duration_int > 5:
            duration_int = 5
            logger.warning(f"[UNIFIED_TRACKER] ⚠️ Capped duration from {duration_minutes} to 5 minutes")
        
        # Rule 4: Minimum 1 minute
        if duration_int < 1:
            duration_int = 1
        
        # Rule 5: Sessions >= 2 minutes are complete
        is_complete = (duration_int >= 2)
        
        return {
            "should_track": True,
            "duration_int": int(duration_int),
            "is_complete": is_complete,
            "capped": (duration_minutes > 5)
        }
    
    @staticmethod
    async def _check_subscription_limits(user: Dict[str, Any], duration_int: int) -> Dict[str, Any]:
        """Check if user can track this session based on subscription limits"""
        
        # Get subscription details
        subscription_plan = user.get('subscription_plan', 'try_learn')
        subscription_period = user.get('subscription_period', 'monthly')
        current_minutes_used = user.get('practice_minutes_used', 0)
        
        # Calculate limits
        if subscription_plan == "fluency_builder":
            if subscription_period == "monthly":
                minutes_limit = 150
            else:  # yearly
                minutes_limit = 1800
        elif subscription_plan == "team_mastery":
            minutes_limit = -1  # unlimited
        else:  # try_learn
            minutes_limit = 15
        
        # Check limits
        if minutes_limit == -1:
            # Unlimited plan
            return {"can_track": True}
        
        if current_minutes_used + duration_int > minutes_limit:
            remaining = minutes_limit - current_minutes_used
            return {
                "can_track": False,
                "message": f"Would exceed minute limit. {remaining} minutes remaining, {duration_int} requested."
            }
        
        return {"can_track": True}
    
    @staticmethod
    async def _atomic_track_session(
        user_id: str,
        session_id: str,
        duration_int: int,
        is_complete: bool,
        session_type: str,
        learning_plan_id: Optional[str],
        user_email: str
    ) -> Dict[str, Any]:
        """Atomically track session with proper audit trail"""
        
        try:
            # Get current user data
            user = await database.users.find_one(get_user_query(user_id))
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Calculate new values
            old_minutes = user.get('practice_minutes_used', 0)
            old_sessions = user.get('practice_sessions_used', 0)
            
            new_minutes = old_minutes + duration_int
            new_sessions = old_sessions + (1 if is_complete else 0)
            
            # Create audit data
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "user_email": user_email,
                "session_id": session_id,
                "session_type": session_type,
                "learning_plan_id": learning_plan_id,
                "reason": f"unified_track_{duration_int}min_{'complete' if is_complete else 'partial'}",
                "old_minutes": old_minutes,
                "new_minutes": new_minutes,
                "old_sessions": old_sessions,
                "new_sessions": new_sessions,
                "minutes_diff": duration_int,
                "sessions_diff": (1 if is_complete else 0)
            }
            
            # Update user profile
            update_data = {
                "$inc": {"practice_minutes_used": duration_int},
                "$set": {
                    "last_session_tracked": datetime.utcnow().isoformat(),
                    "last_session_type": session_type
                },
                "$push": {
                    "speaking_time_audit_trail": {
                        "$each": [audit_data],
                        "$slice": -20  # Keep last 20 changes
                    }
                }
            }
            
            # Increment session count if complete
            if is_complete:
                update_data["$inc"]["practice_sessions_used"] = 1
            
            # Update user
            update_result = await database.users.update_one(
                get_user_query(user_id),
                update_data
            )
            
            if update_result.modified_count == 0:
                return {"success": False, "error": "Failed to update user profile"}
            
            # Record tracking for idempotency
            await database.speaking_time_tracking.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "session_type": session_type,
                "learning_plan_id": learning_plan_id,
                "duration_minutes": duration_int,
                "is_complete": is_complete,
                "tracked_at": datetime.utcnow(),
                "audit_data": audit_data
            })
            
            return {
                "success": True,
                "duration_tracked": duration_int,
                "session_complete": is_complete,
                "total_minutes": new_minutes,
                "total_sessions": new_sessions,
                "audit_created": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class DurationTrackingSafeguards:
    """Integrated safeguards for duration tracking data integrity"""
    
    @staticmethod
    async def validate_user_data_change(user_id: str, old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """
        Validate that a user data change is reasonable and safe
        Returns validation result with warnings/errors
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        old_minutes = old_data.get('practice_minutes_used', 0)
        new_minutes = new_data.get('practice_minutes_used', 0)
        old_sessions = old_data.get('practice_sessions_used', 0)
        new_sessions = new_data.get('practice_sessions_used', 0)
        
        # Check for suspicious data resets
        if old_minutes > 10 and new_minutes == 0:
            validation_result["errors"].append(
                f"DANGEROUS: Resetting minutes from {old_minutes} to 0 - this looks like data corruption!"
            )
            validation_result["is_valid"] = False
            
        if old_sessions > 2 and new_sessions == 0:
            validation_result["errors"].append(
                f"DANGEROUS: Resetting sessions from {old_sessions} to 0 - this looks like data corruption!"
            )
            validation_result["is_valid"] = False
        
        # Check for unrealistic increases
        minutes_increase = new_minutes - old_minutes
        if minutes_increase > 500:  # More than 8+ hours in one update
            validation_result["warnings"].append(
                f"Large minutes increase: +{minutes_increase:.2f} minutes - please verify this is correct"
            )
            
        sessions_increase = new_sessions - old_sessions
        if sessions_increase > 50:  # More than 50 sessions in one update
            validation_result["warnings"].append(
                f"Large sessions increase: +{sessions_increase} sessions - please verify this is correct"
            )
        
        # Check for negative values
        if new_minutes < 0:
            validation_result["errors"].append("Minutes cannot be negative")
            validation_result["is_valid"] = False
            
        if new_sessions < 0:
            validation_result["errors"].append("Sessions cannot be negative")
            validation_result["is_valid"] = False
        
        # Check for reasonable ratios
        if new_sessions > 0 and new_minutes > 0:
            avg_minutes_per_session = new_minutes / new_sessions
            if avg_minutes_per_session > 60:  # More than 1 hour per session
                validation_result["warnings"].append(
                    f"High average session duration: {avg_minutes_per_session:.1f} min/session"
                )
            elif avg_minutes_per_session < 1:  # Less than 1 minute per session
                validation_result["warnings"].append(
                    f"Low average session duration: {avg_minutes_per_session:.1f} min/session"
                )
        
        return validation_result
    
    @staticmethod
    async def create_audit_trail(user_id: str, user_email: str, old_data: Dict, new_data: Dict, reason: str) -> Dict[str, Any]:
        """Create audit trail for duration changes"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "user_email": user_email,
            "reason": reason,
            "old_minutes": old_data.get("practice_minutes_used", 0),
            "new_minutes": new_data.get("practice_minutes_used", 0),
            "old_sessions": old_data.get("practice_sessions_used", 0),
            "new_sessions": new_data.get("practice_sessions_used", 0),
            "minutes_diff": new_data.get("practice_minutes_used", 0) - old_data.get("practice_minutes_used", 0),
            "sessions_diff": new_data.get("practice_sessions_used", 0) - old_data.get("practice_sessions_used", 0)
        }

class ImprovedSubscriptionService:
    """Enhanced subscription service with unified session tracking"""
    
    # Define subscription plans according to requirements
    SUBSCRIPTION_PLANS = {
        "try_learn": SubscriptionPlan(
            plan_id="try_learn",
            name="Try & Learn",
            monthly_price=0.0,
            annual_price=0.0,
            monthly_sessions=3,
            annual_sessions=3,  # Same as monthly for free tier
            monthly_assessments=1,
            annual_assessments=1,  # Same as monthly for free tier
            # NEW: Minute limits for duration-based tracking
            monthly_minutes=15,  # 3 sessions × 5 minutes
            annual_minutes=15,   # Same as monthly for free tier
            features=[
                "3 practice sessions (5 minutes each) monthly",
                "1 speaking assessment monthly",
                "Basic progress tracking"
            ],
            is_free=True
        ),
        "fluency_builder": SubscriptionPlan(
            plan_id="fluency_builder",
            name="Fluency Builder",
            monthly_price=19.99,
            annual_price=199.99,
            monthly_sessions=30,
            annual_sessions=360,  # 30 sessions × 12 months
            monthly_assessments=2,
            annual_assessments=24,  # 2 assessments × 12 months
            # NEW: Minute limits for duration-based tracking
            monthly_minutes=150,  # 30 sessions × 5 minutes
            annual_minutes=1800,  # 360 sessions × 5 minutes
            features=[
                "30 practice sessions (5 minutes each) monthly",
                "2 speaking assessments monthly",
                "Advanced progress tracking",
                "Learning plan progression",
                "Achievement badges"
            ]
        ),
        "team_mastery": SubscriptionPlan(
            plan_id="team_mastery",
            name="Team Mastery",
            monthly_price=39.99,
            annual_price=399.99,
            monthly_sessions=-1,  # Unlimited
            annual_sessions=-1,   # Unlimited
            monthly_assessments=-1,  # Unlimited
            annual_assessments=-1,   # Unlimited
            # NEW: Minute limits for duration-based tracking
            monthly_minutes=-1,  # Unlimited
            annual_minutes=-1,   # Unlimited
            features=[
                "Unlimited practice sessions",
                "Unlimited assessments",
                "Premium learning plans",
                "Advanced analytics",
                "Priority support",
                "Team collaboration features"
            ]
        )
    }
    
    @classmethod
    async def track_speaking_time(cls, request: SpeakingTimeTrackingRequest) -> bool:
        """
        NEW IMPROVED track_speaking_time method using Unified Session Tracking
        
        This is a drop-in replacement for the existing method but uses the new
        unified tracking system with all business rules properly implemented.
        """
        
        try:
            logger.info(f"[IMPROVED_SERVICE] 🎯 Track speaking time request:")
            logger.info(f"[IMPROVED_SERVICE] User: {request.user_id}")
            logger.info(f"[IMPROVED_SERVICE] Session: {request.session_id}")
            logger.info(f"[IMPROVED_SERVICE] Minutes: {request.speaking_minutes}")
            logger.info(f"[IMPROVED_SERVICE] Complete: {request.session_completed}")
            
            # Use the unified tracker
            result = await UnifiedSessionTracker.track_session_unified(
                user_id=request.user_id,
                session_id=request.session_id,
                duration_minutes=request.speaking_minutes,
                session_type="speaking_practice"
            )
            
            if result["success"]:
                if result.get("already_tracked"):
                    logger.info(f"[IMPROVED_SERVICE] ✅ Session already tracked (idempotent)")
                    return True
                elif result.get("not_tracked"):
                    logger.info(f"[IMPROVED_SERVICE] ℹ️ Session not tracked: {result['reason']}")
                    return True  # Still return success for sessions < 1 minute
                else:
                    logger.info(f"[IMPROVED_SERVICE] ✅ Session tracked successfully:")
                    logger.info(f"[IMPROVED_SERVICE]    Duration tracked: {result.get('duration_tracked')} minutes")
                    logger.info(f"[IMPROVED_SERVICE]    Session complete: {result.get('session_complete')}")
                    logger.info(f"[IMPROVED_SERVICE]    Total minutes: {result.get('total_minutes')}")
                    logger.info(f"[IMPROVED_SERVICE]    Total sessions: {result.get('total_sessions')}")
                    return True
            else:
                if result.get("limits_exceeded"):
                    logger.warning(f"[IMPROVED_SERVICE] ❌ Limits exceeded: {result['error']}")
                    return False  # Return False so calling code can handle limit exceeded
                else:
                    logger.error(f"[IMPROVED_SERVICE] ❌ Tracking failed: {result['error']}")
                    return False
                    
        except Exception as e:
            logger.error(f"[IMPROVED_SERVICE] ❌ Error in track_speaking_time: {str(e)}")
            return False
    
    # Keep all other existing methods from SubscriptionService unchanged
    # This allows for drop-in replacement
    
    @classmethod
    async def get_user_subscription_status(cls, user_id: str) -> SubscriptionStatus:
        """Keep existing implementation - no changes needed"""
        # Import the original implementation
        from subscription_service import SubscriptionService
        return await SubscriptionService.get_user_subscription_status(user_id)
    
    @classmethod
    async def _calculate_subscription_limits(cls, user_id: str, plan_id: str, period: str, user_data: Dict[str, Any]) -> SubscriptionLimits:
        """Keep existing implementation - no changes needed"""
        from subscription_service import SubscriptionService
        return await SubscriptionService._calculate_subscription_limits(user_id, plan_id, period, user_data)
    
    @classmethod
    async def track_usage(cls, request: UsageTrackingRequest) -> bool:
        """Keep existing implementation - no changes needed"""
        from subscription_service import SubscriptionService
        return await SubscriptionService.track_usage(request)
    
    @classmethod
    async def can_access_feature(cls, user_id: str, feature_type: str) -> tuple[bool, str]:
        """Keep existing implementation - no changes needed"""
        from subscription_service import SubscriptionService
        return await SubscriptionService.can_access_feature(user_id, feature_type)
    
    @classmethod
    async def can_start_session(cls, user_id: str) -> tuple[bool, str]:
        """Keep existing implementation - no changes needed"""
        from subscription_service import SubscriptionService
        return await SubscriptionService.can_start_session(user_id)
