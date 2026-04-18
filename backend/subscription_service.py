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

# Import performance cache
from performance_cache import perf_cache

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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
            annual_price=119.00,  # UPDATED: Was 199.99
            monthly_sessions=30,
            annual_sessions=360,  # 30 sessions × 12 months
            monthly_assessments=2,
            annual_assessments=24,  # 2 assessments × 12 months
            # NEW: Minute limits for duration-based tracking
            monthly_minutes=150,  # 150 minutes monthly
            annual_minutes=1800,  # 1800 minutes annually
            features=[
                "150 minutes speaking monthly",
                "2 speaking assessments monthly",
                "10 hearts for challenges",
                "Hearts refill every 1 hour",
                "Advanced progress tracking",
                "All conversation topics"
            ]
        ),
        "language_mastery": SubscriptionPlan(
            plan_id="language_mastery",
            name="Language Mastery",
            monthly_price=39.99,
            annual_price=239.00,  # UPDATED: Was 399.99
            monthly_sessions=-1,  # Unlimited
            annual_sessions=-1,   # Unlimited
            monthly_assessments=-1,  # Unlimited
            annual_assessments=-1,   # Unlimited
            # NEW: Minute limits for duration-based tracking
            monthly_minutes=-1,  # Unlimited
            annual_minutes=-1,   # Unlimited
            features=[
                "UNLIMITED speaking practice",
                "UNLIMITED assessments",
                "UNLIMITED hearts for challenges",
                "Instant heart refills",
                "Premium learning plans",
                "Advanced analytics"
            ]
        ),
        # Backward compatibility for old plan ID
        "team_mastery": SubscriptionPlan(
            plan_id="team_mastery",
            name="Language Mastery",  # Display new name
            monthly_price=39.99,
            annual_price=239.00,  # UPDATED: Was 399.99
            monthly_sessions=-1,  # Unlimited
            annual_sessions=-1,   # Unlimited
            monthly_assessments=-1,  # Unlimited
            annual_assessments=-1,   # Unlimited
            monthly_minutes=-1,  # Unlimited
            annual_minutes=-1,   # Unlimited
            features=[
                "UNLIMITED speaking practice",
                "UNLIMITED assessments",
                "UNLIMITED hearts for challenges",
                "Instant heart refills",
                "Premium learning plans",
                "Advanced analytics"
            ]
        )
    }
    
    @classmethod
    async def get_user_subscription_status(cls, user_id: str) -> SubscriptionStatus:
        """Get comprehensive subscription status for a user with integrated validation"""
        try:
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                return SubscriptionStatus()
            
            # Skip validation for now - focus on core functionality
            logger.info(f"Getting subscription status for user {user_id}")

            # Check if subscription is expired
            from datetime import timezone
            now = datetime.now(timezone.utc)
            subscription_status = user.get("subscription_status")
            expires_at = user.get("subscription_expires_at")

            # Make expires_at timezone-aware if needed
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            # 🎁 GRACE PERIOD: Check if grace period has expired
            if subscription_status == "payment_pending_grace":
                grace_period_end = user.get("grace_period_end_date")
                # Make timezone-aware if needed
                if grace_period_end and grace_period_end.tzinfo is None:
                    grace_period_end = grace_period_end.replace(tzinfo=timezone.utc)
                if grace_period_end and now > grace_period_end:
                    # Grace period expired - downgrade to free tier
                    logger.warning(f"[GRACE_PERIOD_EXPIRED] Grace period ended for user {user_id} - downgrading to free tier")
                    logger.info(f"[GRACE_PERIOD_EXPIRED] Grace period end: {grace_period_end}, Current time: {now}")

                    # Downgrade user to free tier
                    await database["users"].update_one(
                        get_user_query(user_id),
                        {
                            "$set": {
                                "subscription_status": "free",
                                "subscription_plan": "try_learn"
                            },
                            "$unset": {
                                "grace_period_end_date": 1,
                                "pending_subscription_plan": 1,
                                "pending_subscription_id": 1
                            }
                        }
                    )

                    # Update local variables
                    subscription_status = "free"
                    logger.info(f"[GRACE_PERIOD_EXPIRED] User {user_id} downgraded to free tier")
                else:
                    # Grace period still active
                    if grace_period_end:
                        days_remaining = (grace_period_end - now).days
                        logger.info(f"[GRACE_PERIOD_ACTIVE] User {user_id} in grace period - {days_remaining} days remaining")

            # Trial information
            trial_end_date = user.get("trial_end_date")
            is_in_trial = user.get("is_in_trial", False)
            trial_days_remaining = None
            
            # Check Stripe for trial and cancellation status
            stripe_customer_id = user.get("stripe_customer_id")
            if stripe_customer_id:
                try:
                    # 🚀 OPTIMIZED: Cache Stripe API call for 30 seconds
                    cache_key = f"stripe_subscription:{stripe_customer_id}"
                    
                    async def fetch_stripe_subscription():
                        """Fetch subscription from Stripe (cached)"""
                        return stripe.Subscription.list(
                            customer=stripe_customer_id,
                            limit=1
                        )
                    
                    # Get subscription from Stripe with caching
                    subscriptions = await perf_cache.fetch_with_cache_and_dedup(
                        cache_key,
                        fetch_stripe_subscription,
                        ttl_seconds=30
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
                        elif stripe_subscription.status == "canceled":
                            # Subscription was canceled — clear all trial/subscription state
                            subscription_status = "free"
                            is_in_trial = False
                            trial_end_date = None
                            trial_days_remaining = None
                            await database["users"].update_one(
                                get_user_query(user_id),
                                {
                                    "$set": {
                                        "is_in_trial": False,
                                        "subscription_status": "free",
                                        "subscription_plan": "try_learn",
                                    },
                                    "$unset": {
                                        "trial_end_date": 1,
                                        "current_period_start": 1,
                                        "current_period_end": 1,
                                    }
                                }
                            )
                            logger.info(f"[SUBSCRIPTION_STATUS] Cleared stale trial data for canceled user {user_id}")

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
            provider = user.get("subscription_provider")  # stripe, apple, google_play

            # 🔥 FIX: For free users, check if current_period_end has expired
            # This handles the case where cron job hasn't run yet
            if plan_id == "try_learn":
                current_period_end = user.get("current_period_end")
                if current_period_end:
                    # Make timezone-aware if needed
                    if current_period_end.tzinfo is None:
                        from datetime import timezone
                        current_period_end = current_period_end.replace(tzinfo=timezone.utc)

                    if now > current_period_end:
                        logger.warning(f"Free user {user_id} period expired at {current_period_end}, current time {now}")
                        logger.warning(f"This should have been reset by cron job. Auto-resetting as fallback.")
                        # Auto-reset the period as a fallback (cron job should have done this)
                        await cls.reset_monthly_usage(user_id)
                        # Re-fetch user data after reset
                        user = await database["users"].find_one(get_user_query(user_id))
                        if not user:
                            return SubscriptionStatus()

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
            # 🎁 GRACE PERIOD: Include payment_pending_grace in active status check
            if expires_at and subscription_status in ["active", "canceling", "payment_pending_grace"] and not is_in_trial:
                days_until_expiry = (expires_at - now).days
            
            return SubscriptionStatus(
                status=subscription_status,
                plan=plan_id,
                period=period,
                provider=provider,  # stripe, apple, google_play
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
        """Calculate subscription limits and current usage with dashboard fix validation"""
        
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
        
        # 🔥 FIX: Count lifetime conversation sessions for "Sessions Completed" display
        sessions_completed = await database["conversation_sessions"].count_documents({
            "user_id": user_id
        })
        logger.info(f"User {user_id} has {sessions_completed} lifetime conversation sessions")
        
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
        
        # SIMPLE APPROACH: Use user record data directly (no auto-correction)
        # Auto-correction was causing bugs by incorrectly resetting user minutes
        user_record_minutes = user_data.get("practice_minutes_used", 0.0)
        user_record_sessions = user_data.get("practice_sessions_used", 0)
        
        # Check if auto-correction is disabled for this user
        auto_correction_disabled = user_data.get("auto_correction_disabled", False)
        
        if auto_correction_disabled:
            logger.info(f"Auto-correction disabled for user {user_id} - using user record data directly")
            sessions_used = max(0, user_record_sessions)
            minutes_used = max(0.0, user_record_minutes)
        else:
            # For users without auto-correction disabled, still use user record but log a warning
            logger.warning(f"Using user record data for user {user_id} (auto-correction not explicitly disabled)")
            sessions_used = max(0, user_record_sessions)
            minutes_used = max(0.0, user_record_minutes)
        
        # Get assessments usage (not affected by dashboard fix)
        assessments_used = max(0, user_data.get("assessments_used", 0))  # Ensure non-negative
        
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
            # 🔥 FIX: Add lifetime sessions count for Profile display
            sessions_completed=sessions_completed,
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
    async def can_access_feature(cls, user_id: str, feature_type: str, minimum_minutes_required: int = 3) -> tuple[bool, str]:
        """
        Check if user can access a specific feature

        Args:
            user_id: User ID to check
            feature_type: Type of feature ("practice_session", "assessment", "learning_plan_progression")
            minimum_minutes_required: Minimum minutes required for practice sessions (default: 3)

        Returns:
            Tuple of (can_access: bool, message: str)
        """
        try:
            status = await cls.get_user_subscription_status(user_id)

            if feature_type == "practice_session":
                # Check minute limits with minimum requirement
                # We give users "150 minutes speaking regardless of practice session OR learning plan session"
                if status.limits and status.limits.minutes_remaining is not None:
                    if status.limits.minutes_limit == -1:
                        # Unlimited plan
                        return True, ""

                    # Require minimum minutes to start a session
                    if status.limits.minutes_remaining < minimum_minutes_required:
                        if status.limits.minutes_remaining <= 0:
                            return False, f"No speaking time remaining this {status.period}. You have used {status.limits.minutes_used:.1f} of {status.limits.minutes_limit} minutes. Upgrade to continue learning!"
                        else:
                            return False, f"You need at least {minimum_minutes_required} minutes to start a session. You have {status.limits.minutes_remaining:.0f} minutes left. Upgrade to continue learning!"

                # Has enough minutes to start
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
    async def can_start_session(cls, user_id: str, selected_duration_minutes: Optional[int] = None) -> tuple[bool, str]:
        """
        Check if user can start a new session based on minute limits and selected duration

        Args:
            user_id: User ID to check
            selected_duration_minutes: Duration user wants to practice (3 or 5 minutes)
                                      If None, checks for minimum 3 minutes

        Returns:
            Tuple of (can_start: bool, message: str)
        """
        try:
            status = await cls.get_user_subscription_status(user_id)

            # Determine minimum minutes required based on selected duration
            # If no duration selected, require at least 3 minutes (A1/A2 minimum)
            minimum_required = selected_duration_minutes if selected_duration_minutes else 3

            # Check minute limit first
            if status.limits and status.limits.minutes_remaining is not None:
                if status.limits.minutes_limit == -1:
                    # Unlimited plan
                    return True, f"✨ Unlimited speaking time remaining"
                elif status.limits.minutes_remaining < minimum_required:
                    # Not enough minutes to start a session
                    if status.limits.minutes_remaining <= 0:
                        return False, f"🚫 No speaking time remaining. Upgrade to continue learning!"
                    else:
                        return False, f"🚫 You need at least {minimum_required} minutes to start a {minimum_required}-minute session. You have {status.limits.minutes_remaining:.0f} minute{'s' if status.limits.minutes_remaining != 1 else ''} left. Upgrade to continue learning!"
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
    async def track_speaking_time(cls, request: SpeakingTimeTrackingRequest) -> bool:
        """
        🔥 BULLETPROOF: Track speaking time with atomic deduction and proper limit enforcement
        """
        try:
            from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker
            
            # Use the bulletproof implementation
            return await BulletproofTracker.track_speaking_time_atomic(request)
            
        except Exception as e:
            logger.error(f"Error in track_speaking_time: {str(e)}")
            return False
