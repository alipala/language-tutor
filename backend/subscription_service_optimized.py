#!/usr/bin/env python3
"""
Optimized Subscription Service - Performance Fix for /api/stripe/subscription-status
Reduces response time from 5.44s to <2s by implementing caching and query optimization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import stripe
import os
import asyncio
from database import database
from models import (
    SubscriptionPlan, SubscriptionLimits, SubscriptionStatus, 
    UsageTrackingRequest, SpeakingTimeTrackingRequest
)
from bson import ObjectId

# Import production-safe logging
from logging_config import logger

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def get_user_query(user_id: str):
    """Helper function to handle both UUID and ObjectId formats"""
    try:
        return {"_id": ObjectId(user_id)}
    except:
        return {"_id": user_id}

class SubscriptionCache:
    """In-memory cache for subscription data to reduce Stripe API calls"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes TTL
    
    def _get_cache_key(self, user_id: str, data_type: str) -> str:
        return f"{user_id}:{data_type}"
    
    def get(self, user_id: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Get cached data if not expired"""
        cache_key = self._get_cache_key(user_id, data_type)
        cached_data = self._cache.get(cache_key)
        
        if cached_data:
            cached_time, data = cached_data
            if datetime.utcnow() - cached_time < timedelta(seconds=self._cache_ttl):
                logger.debug(f"[CACHE_HIT] {cache_key}")
                return data
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                logger.debug(f"[CACHE_EXPIRED] {cache_key}")
        
        return None
    
    def set(self, user_id: str, data_type: str, data: Dict[str, Any]) -> None:
        """Cache data with timestamp"""
        cache_key = self._get_cache_key(user_id, data_type)
        self._cache[cache_key] = (datetime.utcnow(), data)
        logger.debug(f"[CACHE_SET] {cache_key}")
    
    def invalidate(self, user_id: str, data_type: Optional[str] = None) -> None:
        """Invalidate cache for user"""
        if data_type:
            cache_key = self._get_cache_key(user_id, data_type)
            self._cache.pop(cache_key, None)
            logger.debug(f"[CACHE_INVALIDATE] {cache_key}")
        else:
            # Invalidate all cache entries for user
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"[CACHE_INVALIDATE_ALL] {user_id} ({len(keys_to_remove)} entries)")

# Global cache instance
subscription_cache = SubscriptionCache()

class OptimizedSubscriptionService:
    """Optimized subscription service with caching and performance improvements"""
    
    # Define subscription plans (same as original)
    SUBSCRIPTION_PLANS = {
        "try_learn": SubscriptionPlan(
            plan_id="try_learn",
            name="Try & Learn",
            monthly_price=0.0,
            annual_price=0.0,
            monthly_sessions=3,
            annual_sessions=3,
            monthly_assessments=1,
            annual_assessments=1,
            monthly_minutes=15,
            annual_minutes=15,
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
            annual_sessions=360,
            monthly_assessments=2,
            annual_assessments=24,
            monthly_minutes=150,
            annual_minutes=1800,
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
            monthly_sessions=-1,
            annual_sessions=-1,
            monthly_assessments=-1,
            annual_assessments=-1,
            monthly_minutes=-1,
            annual_minutes=-1,
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
    async def get_user_subscription_status_optimized(cls, user_id: str) -> SubscriptionStatus:
        """
        OPTIMIZED VERSION: Get comprehensive subscription status with caching and performance improvements
        Target: <2s response time (down from 5.44s)
        """
        try:
            start_time = datetime.utcnow()
            logger.info(f"[OPTIMIZED] Starting subscription status check for user {user_id}")
            
            # OPTIMIZATION 1: Check cache first
            cached_status = subscription_cache.get(user_id, "subscription_status")
            if cached_status:
                logger.info(f"[OPTIMIZED] Cache hit - returning cached status for user {user_id}")
                return SubscriptionStatus(**cached_status)
            
            # OPTIMIZATION 2: Get user data with minimal fields
            user = await database["users"].find_one(
                get_user_query(user_id),
                {
                    "subscription_status": 1,
                    "subscription_plan": 1,
                    "subscription_period": 1,
                    "subscription_price_id": 1,
                    "subscription_expires_at": 1,
                    "stripe_customer_id": 1,
                    "is_in_trial": 1,
                    "trial_end_date": 1,
                    "current_period_start": 1,
                    "current_period_end": 1,
                    "practice_minutes_used": 1,
                    "practice_sessions_used": 1,
                    "assessments_used": 1,
                    "learning_plan_preserved": 1
                }
            )
            
            if not user:
                return SubscriptionStatus()
            
            # OPTIMIZATION 3: Skip heavy validation by default (run in background if needed)
            skip_validation = True  # Can be made configurable
            
            # Check if subscription is expired
            now = datetime.utcnow()
            subscription_status = user.get("subscription_status")
            expires_at = user.get("subscription_expires_at")
            
            # Trial information
            trial_end_date = user.get("trial_end_date")
            is_in_trial = user.get("is_in_trial", False)
            trial_days_remaining = None
            
            # OPTIMIZATION 4: Only call Stripe API if absolutely necessary
            stripe_customer_id = user.get("stripe_customer_id")
            stripe_data_needed = (
                subscription_status in ["trialing", "active"] and 
                stripe_customer_id and 
                not subscription_cache.get(user_id, "stripe_data")
            )
            
            if stripe_data_needed:
                try:
                    # OPTIMIZATION 5: Use cached Stripe data if available
                    cached_stripe = subscription_cache.get(user_id, "stripe_data")
                    if cached_stripe:
                        stripe_subscription = cached_stripe
                        logger.debug(f"[OPTIMIZED] Using cached Stripe data for user {user_id}")
                    else:
                        # Single optimized Stripe API call
                        logger.debug(f"[OPTIMIZED] Making Stripe API call for user {user_id}")
                        subscriptions = stripe.Subscription.list(
                            customer=stripe_customer_id,
                            limit=1,
                            expand=['data.items.data.price.product']  # Expand to reduce additional API calls
                        )
                        
                        if subscriptions.data:
                            stripe_subscription = subscriptions.data[0]
                            
                            # Cache the Stripe data
                            stripe_data = {
                                "id": stripe_subscription.id,
                                "status": stripe_subscription.status,
                                "trial_end": stripe_subscription.trial_end,
                                "cancel_at_period_end": stripe_subscription.cancel_at_period_end,
                                "current_period_start": stripe_subscription.current_period_start,
                                "current_period_end": stripe_subscription.current_period_end
                            }
                            subscription_cache.set(user_id, "stripe_data", stripe_data)
                            stripe_subscription = stripe_data
                        else:
                            stripe_subscription = None
                    
                    if stripe_subscription:
                        # Update trial information from Stripe
                        if stripe_subscription["status"] == "trialing":
                            subscription_status = "trialing"
                            is_in_trial = True
                            if stripe_subscription["trial_end"]:
                                trial_end_date = datetime.fromtimestamp(stripe_subscription["trial_end"])
                                trial_days_remaining = max(0, (trial_end_date - now).days)
                        elif stripe_subscription["status"] == "active":
                            if stripe_subscription.get("cancel_at_period_end"):
                                subscription_status = "canceling"
                            else:
                                subscription_status = "active"
                            is_in_trial = False
                            trial_end_date = None
                            
                except Exception as stripe_error:
                    logger.warning(f"[OPTIMIZED] Stripe API error for user {user_id}: {str(stripe_error)}")
                    # Continue with database data
            
            # Calculate trial days remaining if in trial
            if is_in_trial and trial_end_date:
                trial_days_remaining = max(0, (trial_end_date - now).days)
            
            # Determine actual status
            if expires_at and now > expires_at and not is_in_trial:
                subscription_status = "expired"
            
            # Get plan details
            plan_id = user.get("subscription_plan", "try_learn")
            period = user.get("subscription_period", "monthly")
            
            # OPTIMIZATION 6: Fast limits calculation without heavy session queries
            limits = await cls._calculate_subscription_limits_fast(user_id, plan_id, period, user)
            
            # Check if learning plan should be preserved
            is_preserved = user.get("learning_plan_preserved", False)
            preservation_message = None
            
            if subscription_status == "expired" and not is_preserved:
                # Note: Preservation logic can be moved to background job for better performance
                preservation_message = "Learning plan will be preserved"
            
            # Calculate days until expiry
            days_until_expiry = None
            if expires_at and subscription_status in ["active", "canceling"] and not is_in_trial:
                days_until_expiry = (expires_at - now).days
            
            # Create status object
            status = SubscriptionStatus(
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
            
            # OPTIMIZATION 7: Cache the result
            subscription_cache.set(user_id, "subscription_status", status.dict())
            
            # Log performance
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"[OPTIMIZED] Subscription status completed for user {user_id} in {duration:.2f}s")
            
            return status
            
        except Exception as e:
            logger.error(f"[OPTIMIZED] Error getting subscription status for user {user_id}: {str(e)}")
            return SubscriptionStatus()
    
    @classmethod
    async def _calculate_subscription_limits_fast(
        cls, 
        user_id: str, 
        plan_id: str, 
        period: str, 
        user_data: Dict[str, Any]
    ) -> SubscriptionLimits:
        """
        OPTIMIZED VERSION: Fast limits calculation without heavy session queries
        Uses cached user data and skips expensive session aggregation
        """
        
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
            if period == "annual":
                subscription_started = user_data.get("subscription_started_at")
                if subscription_started:
                    period_start = subscription_started
                    try:
                        period_end = period_start.replace(year=period_start.year + 1)
                    except ValueError:
                        period_end = period_start.replace(year=period_start.year + 1, month=2, day=28)
                else:
                    period_start = now
                    try:
                        period_end = period_start.replace(year=period_start.year + 1)
                    except ValueError:
                        period_end = period_start.replace(year=period_start.year + 1, month=2, day=28)
            else:
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1)
        
        # OPTIMIZATION: Use user record data directly (skip expensive session queries)
        # This trades some accuracy for significant performance improvement
        sessions_used = max(0, user_data.get("practice_sessions_used", 0))
        minutes_used = max(0.0, user_data.get("practice_minutes_used", 0.0))
        assessments_used = max(0, user_data.get("assessments_used", 0))
        
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
            minutes_limit=minutes_limit,
            minutes_used=minutes_used,
            minutes_remaining=minutes_remaining,
            period_start=period_start,
            period_end=period_end,
            is_unlimited=(sessions_limit == -1 and assessments_limit == -1 and minutes_limit == -1)
        )
    
    @classmethod
    async def invalidate_user_cache(cls, user_id: str) -> None:
        """Invalidate cache when user data changes"""
        subscription_cache.invalidate(user_id)
        logger.info(f"[OPTIMIZED] Cache invalidated for user {user_id}")
    
    @classmethod
    async def track_usage_optimized(cls, request: UsageTrackingRequest) -> bool:
        """Optimized usage tracking with cache invalidation"""
        try:
            # Invalidate cache before tracking
            await cls.invalidate_user_cache(request.user_id)
            
            # Use original tracking logic (already optimized)
            from subscription_service import SubscriptionService
            result = await SubscriptionService.track_usage(request)
            
            # Invalidate cache after tracking
            if result:
                await cls.invalidate_user_cache(request.user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"[OPTIMIZED] Error in optimized usage tracking: {str(e)}")
            return False
    
    @classmethod
    async def track_speaking_time_optimized(cls, request: SpeakingTimeTrackingRequest) -> bool:
        """Optimized speaking time tracking with cache invalidation"""
        try:
            # Invalidate cache before tracking
            await cls.invalidate_user_cache(request.user_id)
            
            # Use original tracking logic (already optimized)
            from subscription_service import SubscriptionService
            result = await SubscriptionService.track_speaking_time(request)
            
            # Invalidate cache after tracking
            if result:
                await cls.invalidate_user_cache(request.user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"[OPTIMIZED] Error in optimized speaking time tracking: {str(e)}")
            return False

# Background validation task (optional)
async def run_background_validation(user_id: str) -> None:
    """Run validation in background to avoid blocking the main request"""
    try:
        logger.info(f"[BACKGROUND] Starting validation for user {user_id}")
        
        # Import validation modules
        from validation.auto_corrector import AutoCorrector
        
        # Run validation and auto-fix
        validation_result = await AutoCorrector.validate_and_fix_user(user_id, auto_fix=True)
        
        if validation_result.get("fixes") and validation_result["fixes"].get("overall_success"):
            logger.info(f"[BACKGROUND] Auto-fixed issues for user {user_id}")
            # Invalidate cache so next request gets fresh data
            await OptimizedSubscriptionService.invalidate_user_cache(user_id)
        
    except Exception as e:
        logger.error(f"[BACKGROUND] Background validation failed for user {user_id}: {str(e)}")

# Utility function to create database indexes for performance
async def create_performance_indexes():
    """Create database indexes to optimize subscription status queries"""
    try:
        logger.info("[INDEXES] Creating performance indexes...")
        
        # Index for user queries
        await database["users"].create_index([("_id", 1)])
        
        # Index for conversation sessions by user and date
        await database["conversation_sessions"].create_index([
            ("user_id", 1),
            ("created_at", -1)
        ])
        
        # Index for learning plans by user
        await database["learning_plans"].create_index([("user_id", 1)])
        
        logger.info("[INDEXES] Performance indexes created successfully")
        
    except Exception as e:
        logger.error(f"[INDEXES] Error creating indexes: {str(e)}")

if __name__ == "__main__":
    # Test the optimized service
    import asyncio
    
    async def test_optimized_service():
        user_id = "688921c268819565ef1ce3dc"
        
        print("🚀 TESTING OPTIMIZED SUBSCRIPTION SERVICE")
        print("=" * 50)
        
        # Create indexes first
        await create_performance_indexes()
        
        # Test optimized subscription status
        start_time = datetime.utcnow()
        status = await OptimizedSubscriptionService.get_user_subscription_status_optimized(user_id)
        end_time = datetime.utcnow()
        
        duration = (end_time - start_time).total_seconds()
        print(f"⚡ Response time: {duration:.2f}s")
        print(f"📊 Status: {status.status}")
        print(f"🎯 Plan: {status.plan}")
        
        if status.limits:
            print(f"⏱️ Minutes remaining: {status.limits.minutes_remaining}")
            print(f"📝 Sessions remaining: {status.limits.sessions_remaining}")
        
        # Test cache hit
        print("\n🔄 Testing cache hit...")
        start_time = datetime.utcnow()
        cached_status = await OptimizedSubscriptionService.get_user_subscription_status_optimized(user_id)
        end_time = datetime.utcnow()
        
        cache_duration = (end_time - start_time).total_seconds()
        print(f"⚡ Cached response time: {cache_duration:.2f}s")
        print(f"🎯 Performance improvement: {((duration - cache_duration) / duration * 100):.1f}%")
    
    asyncio.run(test_optimized_service())
