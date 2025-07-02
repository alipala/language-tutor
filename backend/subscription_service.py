from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import stripe
import os
from database import database
from models import (
    SubscriptionPlan, SubscriptionLimits, SubscriptionStatus, 
    UsageTrackingRequest, LearningPlanPreservation
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

class SubscriptionService:
    """Comprehensive subscription business logic service"""
    
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
        else:
            sessions_limit = plan.monthly_sessions
            assessments_limit = plan.monthly_assessments
        
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
        
        # Get current usage
        sessions_used = user_data.get("practice_sessions_used", 0)
        assessments_used = user_data.get("assessments_used", 0)
        
        # Calculate remaining
        sessions_remaining = sessions_limit - sessions_used if sessions_limit != -1 else -1
        assessments_remaining = assessments_limit - assessments_used if assessments_limit != -1 else -1
        
        return SubscriptionLimits(
            plan=plan_id,
            period=period,
            sessions_limit=sessions_limit,
            assessments_limit=assessments_limit,
            sessions_used=sessions_used,
            assessments_used=assessments_used,
            sessions_remaining=sessions_remaining,
            assessments_remaining=assessments_remaining,
            period_start=period_start,
            period_end=period_end,
            is_unlimited=(sessions_limit == -1 and assessments_limit == -1)
        )
    
    @classmethod
    async def track_usage(cls, request: UsageTrackingRequest) -> bool:
        """Track usage of practice sessions or assessments"""
        try:
            user_id = request.user_id
            usage_type = request.usage_type
            
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
            
            # Update usage counter
            update_field = "practice_sessions_used" if usage_type == "practice_session" else "assessments_used"
            
            await database["users"].update_one(
                get_user_query(user_id),
                {"$inc": {update_field: 1}}
            )
            
            logger.info(f"Tracked {usage_type} usage for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking usage for user {user_id}: {str(e)}")
            return False
    
    @classmethod
    async def can_access_feature(cls, user_id: str, feature_type: str) -> tuple[bool, str]:
        """Check if user can access a specific feature"""
        try:
            status = await cls.get_user_subscription_status(user_id)
            
            if feature_type == "practice_session":
                if status.limits and status.limits.sessions_remaining == 0:
                    return False, f"You've used all {status.limits.sessions_limit} practice sessions for this {status.period}. Upgrade to continue learning!"
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
                
                # Update user with preservation data
                await database["users"].update_one(
                    get_user_query(user_id),
                    {"$set": {
                        "learning_plan_preserved": True,
                        "learning_plan_data": preservation_data.plan_data,
                        "learning_plan_progress": preservation_data.progress_data,
                        "subscription_plan": "try_learn",  # Revert to free tier
                        "practice_sessions_used": 0,  # Reset usage for free tier
                        "assessments_used": 0
                    }}
                )
                
                logger.info(f"Learning plan preserved for user {user_id}")
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
        """Reset monthly usage counters (called by scheduled task)"""
        try:
            now = datetime.utcnow()
            next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                next_month = next_month.replace(year=now.year + 1, month=1)
            else:
                next_month = next_month.replace(month=now.month + 1)
            
            await database["users"].update_one(
                get_user_query(user_id),
                {"$set": {
                    "practice_sessions_used": 0,
                    "assessments_used": 0,
                    "current_period_start": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                    "current_period_end": next_month
                }}
            )
            
            logger.info(f"Reset monthly usage for user {user_id}")
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
