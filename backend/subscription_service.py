from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import stripe
import os
from database import database
from models import (
    SubscriptionPlan, SubscriptionLimits, SubscriptionStatus, 
    UsageTrackingRequest, SpeakingTimeTrackingRequest, LearningPlanPreservation
)
from bson import ObjectId

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

logger = logging.getLogger(__name__)

def get_user_query(user_id: str):
    """Helper function to handle both UUID and ObjectId formats"""
    try:
        return {"_id": ObjectId(user_id)}
    except:
        return {"_id": user_id}

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

class SubscriptionService:
    """Enhanced subscription business logic service with integrated safeguards"""
    
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
    async def get_user_subscription_status(cls, user_id: str) -> SubscriptionStatus:
        """Get comprehensive subscription status for a user"""
        try:
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                return SubscriptionStatus()
            
            # Check if subscription is expired
            now = datetime.utcnow()
            subscription_status = user.get("subscription_status")
            expires_at = user.get("subscription_expires_at")
            
            # Trial information
            trial_end_date = user.get("trial_end_date")
            is_in_trial = user.get("is_in_trial", False)
            trial_days_remaining = None
            
            # Check Stripe for trial and cancellation status
            stripe_customer_id = user.get("stripe_customer_id")
            if stripe_customer_id:
                try:
                    # Get subscription from Stripe to check trial status
                    subscriptions = stripe.Subscription.list(
                        customer=stripe_customer_id,
                        limit=1
                    )
                    
                    if subscriptions.data:
                        stripe_subscription = subscriptions.data[0]
                        
                        # Update trial information from Stripe
                        if stripe_subscription.status == "trialing":
                            subscription_status = "trialing"
                            is_in_trial = True
                            if stripe_subscription.trial_end:
                                trial_end_date = datetime.fromtimestamp(stripe_subscription.trial_end)
                                trial_days_remaining = max(0, (trial_end_date - now).days)
                                
                                # Update user with trial info
                                await database["users"].update_one(
                                    get_user_query(user_id),
                                    {"$set": {
                                        "is_in_trial": True,
                                        "trial_end_date": trial_end_date,
                                        "subscription_status": "trialing"
                                    }}
                                )
                        elif stripe_subscription.status == "active":
                            # Check if subscription is scheduled for cancellation
                            if stripe_subscription.cancel_at_period_end:
                                subscription_status = "canceling"
                                logger.info(f"User {user_id} subscription is scheduled for cancellation")
                            else:
                                subscription_status = "active"
                            
                            # Clear trial status if subscription is now active
                            if is_in_trial:
                                await database["users"].update_one(
                                    get_user_query(user_id),
                                    {"$set": {
                                        "is_in_trial": False,
                                        "trial_end_date": None,
                                        "subscription_status": subscription_status
                                    }}
                                )
                                is_in_trial = False
                                trial_end_date = None
                                
                except Exception as stripe_error:
                    logger.warning(f"Could not check Stripe status for user {user_id}: {str(stripe_error)}")
            
            # Calculate trial days remaining if in trial
            if is_in_trial and trial_end_date:
                trial_days_remaining = max(0, (trial_end_date - now).days)
            
            # Determine actual status
            if expires_at and now > expires_at and not is_in_trial:
                subscription_status = "expired"
                # Update user status in database
                await database["users"].update_one(
                    get_user_query(user_id),
                    {"$set": {"subscription_status": "expired"}}
                )
            
            # Get plan details
            plan_id = user.get("subscription_plan", "try_learn")
            period = user.get("subscription_period", "monthly")
            
            # Calculate limits and usage
            limits = await cls._calculate_subscription_limits(user_id, plan_id, period, user)
            
            # Check if learning plan should be preserved
            is_preserved = user.get("learning_plan_preserved", False)
            preservation_message = None
            
            if subscription_status == "expired" and not is_preserved:
                # Preserve learning plan
                await cls._preserve_learning_plan(user_id)
                is_preserved = True
                preservation_message = cls._get_preservation_message(user)
            
            # Calculate days until expiry (for non-trial subscriptions)
            days_until_expiry = None
            if expires_at and subscription_status in ["active", "canceling"] and not is_in_trial:
                days_until_expiry = (expires_at - now).days
            
            return SubscriptionStatus(
                status=subscription_status,
                plan=plan_id,
                period=period,
                price_id=user.get("subscription_price_id"),
                expires_at=expires_at,
                limits=limits,
                is_preserved=is_preserved,
                preservation_message=preservation_message,
                days_until_expiry=days_until_expiry,
                is_in_trial=is_in_trial,
                trial_end_date=trial_end_date,
                trial_days_remaining=trial_days_remaining
            )
            
        except Exception as e:
            logger.error(f"Error getting subscription status for user {user_id}: {str(e)}")
            return SubscriptionStatus()
    
    @classmethod
    async def _calculate_subscription_limits(
        cls, 
        user_id: str, 
        plan_id: str, 
        period: str, 
        user_data: Dict[str, Any]
    ) -> SubscriptionLimits:
        """Calculate subscription limits and current usage"""
        
        plan = cls.SUBSCRIPTION_PLANS.get(plan_id, cls.SUBSCRIPTION_PLANS["try_learn"])
        
        # Get limits based on period
        if period == "annual":
            sessions_limit = plan.annual_sessions
            assessments_limit = plan.annual_assessments
            minutes_limit = plan.annual_minutes
        else:
            sessions_limit = plan.monthly_sessions
            assessments_limit = plan.monthly_assessments
            minutes_limit = plan.monthly_minutes
        
        # Get current period dates
        period_start = user_data.get("current_period_start")
        period_end = user_data.get("current_period_end")
        
        # If no period set, calculate based on subscription start or current month
        if not period_start or not period_end:
            now = datetime.utcnow()
            subscription_started = user_data.get("subscription_started_at")
            
            if period == "annual":
                # For annual subscriptions, use the actual subscription start date
                if subscription_started:
                    period_start = subscription_started
                    # Calculate exactly 1 year from start date
                    try:
                        period_end = period_start.replace(year=period_start.year + 1)
                    except ValueError:
                        # Handle leap year edge case (Feb 29)
                        period_end = period_start.replace(year=period_start.year + 1, month=2, day=28)
                else:
                    # Fallback if no start date
                    period_start = now
                    try:
                        period_end = period_start.replace(year=period_start.year + 1)
                    except ValueError:
                        period_end = period_start.replace(year=period_start.year + 1, month=2, day=28)
            else:
                # Monthly period - use current month boundaries
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1)
            
            # Update user with calculated periods
            await database["users"].update_one(
                get_user_query(user_id),
                {"$set": {
                    "current_period_start": period_start,
                    "current_period_end": period_end
                }}
            )
        
        # Get current usage with safeguards
        sessions_used = max(0, user_data.get("practice_sessions_used", 0))  # Ensure non-negative
        assessments_used = max(0, user_data.get("assessments_used", 0))  # Ensure non-negative
        minutes_used = max(0.0, user_data.get("practice_minutes_used", 0.0))  # Ensure non-negative
        
        # Calculate remaining
        sessions_remaining = sessions_limit - sessions_used if sessions_limit != -1 else -1
        assessments_remaining = assessments_limit - assessments_used if assessments_limit != -1 else -1
        minutes_remaining = minutes_limit - minutes_used if minutes_limit != -1 else -1
        
        return SubscriptionLimits(
            plan=plan_id,
            period=period,
            sessions_limit=sessions_limit,
            assessments_limit=assessments_limit,
            sessions_used=sessions_used,
            assessments_used=assessments_used,
            sessions_remaining=sessions_remaining,
            assessments_remaining=assessments_remaining,
            # NEW: Minute tracking fields
            minutes_limit=minutes_limit,
            minutes_used=minutes_used,
            minutes_remaining=minutes_remaining,
            period_start=period_start,
            period_end=period_end,
            is_unlimited=(sessions_limit == -1 and assessments_limit == -1 and minutes_limit == -1)
        )
    
    @classmethod
    async def track_usage(cls, request: UsageTrackingRequest) -> bool:
        """Track usage of practice sessions or assessments with enhanced safeguards"""
        try:
            user_id = request.user_id
            usage_type = request.usage_type
            
            # Get current user data for validation
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                logger.error(f"User {user_id} not found for usage tracking")
                return False
            
            # Get current subscription status
            status = await cls.get_user_subscription_status(user_id)
            
            # Check if user has remaining quota
            if usage_type == "practice_session":
                if status.limits and status.limits.sessions_remaining == 0:
                    logger.warning(f"User {user_id} exceeded practice session limit")
                    return False
            elif usage_type == "assessment":
                if status.limits and status.limits.assessments_remaining == 0:
                    logger.warning(f"User {user_id} exceeded assessment limit")
                    return False
            
            # Prepare data for validation
            old_data = {
                "practice_sessions_used": user.get("practice_sessions_used", 0),
                "assessments_used": user.get("assessments_used", 0)
            }
            
            # Calculate new values
            if usage_type == "practice_session":
                new_sessions = old_data["practice_sessions_used"] + 1
                new_assessments = old_data["assessments_used"]
            else:
                new_sessions = old_data["practice_sessions_used"]
                new_assessments = old_data["assessments_used"] + 1
            
            new_data = {
                "practice_sessions_used": new_sessions,
                "assessments_used": new_assessments
            }
            
            # Validate the change
            validation = await DurationTrackingSafeguards.validate_user_data_change(user_id, old_data, new_data)
            
            if not validation["is_valid"]:
                logger.error(f"❌ Usage tracking validation failed for user {user_id}: {validation['errors']}")
                return False
            
            if validation["warnings"]:
                logger.warning(f"⚠️ Usage tracking warnings for user {user_id}: {validation['warnings']}")
            
            # Create audit trail
            audit_data = await DurationTrackingSafeguards.create_audit_trail(
                user_id, user.get('email', 'unknown'), old_data, new_data, f"track_{usage_type}"
            )
            
            # Update usage counter with audit trail
            update_field = "practice_sessions_used" if usage_type == "practice_session" else "assessments_used"
            
            await database["users"].update_one(
                get_user_query(user_id),
                {
                    "$inc": {update_field: 1},
                    "$set": {
                        "last_usage_update": datetime.utcnow().isoformat(),
                        "last_usage_update_reason": f"track_{usage_type}"
                    },
                    "$push": {
                        "usage_audit_trail": {
                            "$each": [audit_data],
                            "$slice": -10  # Keep last 10 changes
                        }
                    }
                }
            )
            
            logger.info(f"✅ Tracked {usage_type} usage for user {user.get('email', user_id)}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking usage for user {user_id}: {str(e)}")
            return False
    
    @classmethod
    async def track_speaking_time(cls, request: SpeakingTimeTrackingRequest) -> bool:
        """Track speaking time and optionally increment session count with enhanced safeguards"""
        try:
            user_id = request.user_id
            speaking_minutes = request.speaking_minutes
            session_completed = request.session_completed
            
            # Get current user data for validation
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                logger.error(f"User {user_id} not found for speaking time tracking")
                return False
            
            # Validate speaking minutes input
            if speaking_minutes < 0:
                logger.error(f"❌ Invalid speaking minutes: {speaking_minutes} (cannot be negative)")
                return False
            
            if speaking_minutes > 120:  # More than 2 hours in one session
                logger.warning(f"⚠️ Very long session: {speaking_minutes} minutes for user {user.get('email', user_id)}")
            
            # Get current subscription status to check minute limits
            status = await cls.get_user_subscription_status(user_id)
            
            # Check if user has remaining minutes (allow current session to complete even if over limit)
            if status.limits and status.limits.minutes_remaining is not None and status.limits.minutes_remaining <= 0:
                logger.warning(f"User {user_id} has no speaking time remaining: {status.limits.minutes_remaining} minutes")
                # Still track the time but warn about limit
            
            # Prepare data for validation
            old_data = {
                "practice_minutes_used": user.get("practice_minutes_used", 0.0),
                "practice_sessions_used": user.get("practice_sessions_used", 0)
            }
            
            # Calculate new values
            new_minutes = old_data["practice_minutes_used"] + speaking_minutes
            new_sessions = old_data["practice_sessions_used"] + (1 if session_completed else 0)
            
            new_data = {
                "practice_minutes_used": new_minutes,
                "practice_sessions_used": new_sessions
            }
            
            # Validate the change
            validation = await DurationTrackingSafeguards.validate_user_data_change(user_id, old_data, new_data)
            
            if not validation["is_valid"]:
                logger.error(f"❌ Speaking time tracking validation failed for user {user_id}: {validation['errors']}")
                return False
            
            if validation["warnings"]:
                logger.warning(f"⚠️ Speaking time tracking warnings for user {user_id}: {validation['warnings']}")
            
            # Create audit trail
            reason = f"track_speaking_time_{speaking_minutes:.2f}min_session_{'completed' if session_completed else 'partial'}"
            audit_data = await DurationTrackingSafeguards.create_audit_trail(
                user_id, user.get('email', 'unknown'), old_data, new_data, reason
            )
            
            # Always track speaking minutes
            update_data = {
                "$inc": {"practice_minutes_used": speaking_minutes},
                "$set": {
                    "last_speaking_time_update": datetime.utcnow().isoformat(),
                    "last_speaking_time_update_reason": reason
                },
                "$push": {
                    "speaking_time_audit_trail": {
                        "$each": [audit_data],
                        "$slice": -10  # Keep last 10 changes
                    }
                }
            }
            
            # Only increment session count if session was completed (5+ minutes + saved)
            if session_completed:
                update_data["$inc"]["practice_sessions_used"] = 1
                logger.info(f"✅ Session completed for user {user.get('email', user_id)}: +1 session, +{speaking_minutes:.2f} minutes")
            else:
                logger.info(f"✅ Partial session for user {user.get('email', user_id)}: +0 sessions, +{speaking_minutes:.2f} minutes")
            
            await database["users"].update_one(
                get_user_query(user_id),
                update_data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking speaking time for user {user_id}: {str(e)}")
            return False
    
    @classmethod
    async def can_access_feature(cls, user_id: str, feature_type: str) -> tuple[bool, str]:
        """Check if user can access a specific feature"""
        try:
            status = await cls.get_user_subscription_status(user_id)
            
            if feature_type == "practice_session":
                # FIXED: Only check minute limits - session count is just for tracking
                # We give users "150 minutes speaking regardless of practice session OR learning plan session"
                if status.limits and status.limits.minutes_remaining is not None and status.limits.minutes_remaining <= 0:
                    if status.limits.minutes_limit == -1:
                        # Unlimited plan
                        return True, ""
                    return False, f"No speaking time remaining this {status.period}. You have used {status.limits.minutes_used:.1f} of {status.limits.minutes_limit} minutes. Upgrade to continue learning!"
                
                # Session count is tracked but doesn't block access - only minutes matter
                return True, ""
            
            elif feature_type == "assessment":
                if status.limits and status.limits.assessments_remaining == 0:
                    return False, f"You've used all {status.limits.assessments_limit} assessments for this {status.period}. Upgrade to unlock more!"
                return True, ""
            
            elif feature_type == "learning_plan_progression":
                if status.status == "expired" or status.is_preserved:
                    return False, "Your learning plan is in preservation mode. Resubscribe to continue your progress!"
                return True, ""
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking feature access for user {user_id}: {str(e)}")
            return False, "Unable to verify access. Please try again."
    
    @classmethod
    async def can_start_session(cls, user_id: str) -> tuple[bool, str]:
        """Check if user can start a new session based on minute limits"""
        try:
            status = await cls.get_user_subscription_status(user_id)
            
            # Check minute limit first
            if status.limits and status.limits.minutes_remaining is not None:
                if status.limits.minutes_limit == -1:
                    # Unlimited plan
                    return True, f"✨ Unlimited speaking time remaining"
                elif status.limits.minutes_remaining <= 0:
                    return False, f"🚫 No speaking time remaining. Upgrade to continue learning!"
                else:
                    return True, f"You have {status.limits.minutes_remaining:.0f} minutes remaining this {status.period}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking session access for user {user_id}: {str(e)}")
            return False, "Unable to verify access. Please try again."
    
    @classmethod
    async def _preserve_learning_plan(cls, user_id: str) -> bool:
        """Preserve user's learning plan when subscription expires"""
        try:
            # Get user's learning plan data
            learning_plan = await database["learning_plans"].find_one({"user_id": user_id})
            
            if learning_plan:
                # Get user's conversation history for progress tracking
                conversations = await database["conversation_sessions"].find(
                    {"user_id": user_id}
                ).to_list(length=None)
                
                # Calculate progress metrics
                total_sessions = len(conversations)
                total_minutes = sum(session.get("duration_minutes", 0) for session in conversations)
                
                # Create preservation data
                preservation_data = LearningPlanPreservation(
                    user_id=user_id,
                    plan_data=learning_plan,
                    progress_data={
                        "total_sessions": total_sessions,
                        "total_minutes": total_minutes,
                        "conversations": conversations[-10:]  # Keep last 10 sessions
                    },
                    weeks_completed=learning_plan.get("weeks_completed", 0),
                    current_week=learning_plan.get("current_week", 1),
                    achievements=learning_plan.get("achievements", []),
                    vocabulary_learned=learning_plan.get("vocabulary_learned", []),
                    grammar_improvements=learning_plan.get("grammar_improvements", [])
                )
                
                # Update user with preservation data (with safeguards)
                user = await database["users"].find_one(get_user_query(user_id))
                if user:
                    old_data = {
                        "practice_sessions_used": user.get("practice_sessions_used", 0),
                        "assessments_used": user.get("assessments_used", 0),
                        "practice_minutes_used": user.get("practice_minutes_used", 0.0)
                    }
                    
                    new_data = {
                        "practice_sessions_used": 0,  # Reset for free tier
                        "assessments_used": 0,  # Reset for free tier
                        "practice_minutes_used": 0.0  # Reset for free tier
                    }
                    
                    # Create audit trail for preservation
                    audit_data = await DurationTrackingSafeguards.create_audit_trail(
                        user_id, user.get('email', 'unknown'), old_data, new_data, "learning_plan_preservation"
                    )
                    
                    await database["users"].update_one(
                        get_user_query(user_id),
                        {
                            "$set": {
                                "learning_plan_preserved": True,
                                "learning_plan_data": preservation_data.plan_data,
                                "learning_plan_progress": preservation_data.progress_data,
                                "subscription_plan": "try_learn",  # Revert to free tier
                                "practice_sessions_used": 0,  # Reset usage for free tier
                                "assessments_used": 0,
                                "practice_minutes_used": 0.0,
                                "preservation_date": datetime.utcnow().isoformat()
                            },
                            "$push": {
                                "preservation_audit_trail": {
                                    "$each": [audit_data],
                                    "$slice": -5  # Keep last 5 preservation events
                                }
                            }
                        }
                    )
                
                logger.info(f"✅ Learning plan preserved for user {user.get('email', user_id)}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error preserving learning plan for user {user_id}: {str(e)}")
            return False
    
    @classmethod
    def _get_preservation_message(cls, user_data: Dict[str, Any]) -> str:
        """Get preservation mode message based on user data"""
        weeks_completed = user_data.get("learning_plan_progress", {}).get("weeks_completed", 0)
        
        return f"""
🎯 Your Learning Goals Are Safe!

Your learning plan progress is preserved:
✅ {weeks_completed} weeks completed
✅ Grammar improvements tracked  
✅ Vocabulary milestones saved

What you can do now:
• Continue with 3 free sessions monthly
• View all your progress and achievements
• Access your learning history anytime

Resubscribe to unlock:
• 30 practice sessions monthly
• 2 assessments monthly  
• Continue your learning plan progression
• Access new weekly content and goals
        """.strip()
    
    @classmethod
    def get_expiry_warning_message(cls, days_until_expiry: int) -> Optional[str]:
        """Get appropriate warning message based on days until expiry"""
        if days_until_expiry == 7:
            return "Your subscription expires in 7 days. Don't worry - your learning plan progress will be safely preserved! You can continue anytime by renewing your subscription."
        elif days_until_expiry == 3:
            return "Only 3 days left! Your learning journey doesn't have to stop. Renew now to keep progressing through your personalized learning plan without interruption."
        elif days_until_expiry == 1:
            return "Your subscription expires tomorrow! All your progress will be preserved. Resubscribe anytime to pick up exactly where you left off."
        elif days_until_expiry == 0:
            return "Your subscription has expired, but your learning plan is preserved! All your progress is saved. Resubscribe anytime to pick up exactly where you left off."
        
        return None
    
    @classmethod
    async def reset_monthly_usage(cls, user_id: str) -> bool:
        """Reset monthly usage counters with enhanced safeguards (called by scheduled task)"""
        try:
            # Get current user data for validation
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                logger.error(f"User {user_id} not found for monthly reset")
                return False
            
            # Prepare data for validation
            old_data = {
                "practice_sessions_used": user.get("practice_sessions_used", 0),
                "assessments_used": user.get("assessments_used", 0),
                "practice_minutes_used": user.get("practice_minutes_used", 0.0)
            }
            
            new_data = {
                "practice_sessions_used": 0,
                "assessments_used": 0,
                "practice_minutes_used": 0.0
            }
            
            # Create audit trail for monthly reset
            audit_data = await DurationTrackingSafeguards.create_audit_trail(
                user_id, user.get('email', 'unknown'), old_data, new_data, "monthly_usage_reset"
            )
            
            now = datetime.utcnow()
            next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                next_month = next_month.replace(year=now.year + 1, month=1)
            else:
                next_month = next_month.replace(month=now.month + 1)
            
            await database["users"].update_one(
                get_user_query(user_id),
                {
                    "$set": {
                        "practice_sessions_used": 0,
                        "assessments_used": 0,
                        "practice_minutes_used": 0.0,  # NEW: Reset minute usage
                        "current_period_start": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                        "current_period_end": next_month,
                        "last_monthly_reset": datetime.utcnow().isoformat()
                    },
                    "$push": {
                        "monthly_reset_audit_trail": {
                            "$each": [audit_data],
                            "$slice": -12  # Keep last 12 monthly resets
                        }
                    }
                }
            )
            
            logger.info(f"✅ Reset monthly usage for user {user.get('email', user_id)}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting monthly usage for user {user_id}: {str(e)}")
            return False
    
    @classmethod
    def get_plan_details(cls, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get details for a specific subscription plan"""
        return cls.SUBSCRIPTION_PLANS.get(plan_id)
    
    @classmethod
    def get_all_plans(cls) -> Dict[str, SubscriptionPlan]:
        """Get all available subscription plans"""
        return cls.SUBSCRIPTION_PLANS
    
    @classmethod
    async def safe_update_user_duration(cls, user_id: str, new_minutes: float, new_sessions: int, 
                                      reason: str, bypass_validation: bool = False) -> Dict[str, Any]:
        """
        Safely update user duration data with validation and logging
        This is the main entry point for any manual duration updates
        """
        try:
            # Get current user data
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                return {"success": False, "error": "User not found"}
            
            old_data = {
                "practice_minutes_used": user.get('practice_minutes_used', 0),
                "practice_sessions_used": user.get('practice_sessions_used', 0)
            }
            
            new_data = {
                "practice_minutes_used": new_minutes,
                "practice_sessions_used": new_sessions
            }
            
            # Validate the change
            if not bypass_validation:
                validation = await DurationTrackingSafeguards.validate_user_data_change(user_id, old_data, new_data)
                
                if not validation["is_valid"]:
                    logger.error(f"❌ Validation failed for user {user_id}: {validation['errors']}")
                    return {
                        "success": False, 
                        "error": "Validation failed", 
                        "validation": validation
                    }
                
                if validation["warnings"]:
                    logger.warning(f"⚠️ Validation warnings for user {user_id}: {validation['warnings']}")
            
            # Create audit trail
            audit_data = await DurationTrackingSafeguards.create_audit_trail(
                user_id, user.get('email', 'unknown'), old_data, new_data, reason
            )
            
            # Update user data
            update_result = await database["users"].update_one(
                get_user_query(user_id),
                {
                    "$set": {
                        "practice_minutes_used": new_minutes,
                        "practice_sessions_used": new_sessions,
                        "last_duration_update": datetime.utcnow().isoformat(),
                        "last_duration_update_reason": reason
                    },
                    "$push": {
                        "duration_audit_trail": {
                            "$each": [audit_data],
                            "$slice": -10  # Keep last 10 changes
                        }
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"✅ Successfully updated user {user.get('email', user_id)}: "
                          f"{old_data['practice_minutes_used']:.2f}→{new_minutes:.2f} min, "
                          f"{old_data['practice_sessions_used']}→{new_sessions} sessions")
                
                return {
                    "success": True,
                    "audit_data": audit_data,
                    "validation": validation if not bypass_validation else None
                }
            else:
                return {"success": False, "error": "Database update failed"}
                
        except Exception as e:
            logger.error(f"❌ Error updating user duration: {e}")
            return {"success": False, "error": str(e)}
