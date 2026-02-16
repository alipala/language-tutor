from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import os
import logging

# Set up logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CRITICAL FIX: Initialize Stripe properly to avoid circular import issues
import stripe

# Load environment variables
stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Set Stripe API key immediately after import
if stripe_secret_key:
    stripe.api_key = stripe_secret_key
    logger.info(f"[STRIPE_INIT] ✅ Stripe API key set successfully")
else:
    logger.error(f"[STRIPE_INIT] ❌ STRIPE_SECRET_KEY not found in environment")

# Import other modules AFTER Stripe is properly initialized
from auth import get_current_user, get_optional_current_user_from_request
from models import UserResponse, UsageTrackingRequest, SpeakingTimeTrackingRequest
from database import database
from subscription_service import SubscriptionService
from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker
from performance_cache import perf_cache

# Create router
router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Feature flag for iDEAL payment method (can be disabled without code deployment)
ENABLE_IDEAL_PAYMENT = os.getenv("ENABLE_IDEAL_PAYMENT", "true").lower() == "true"
logger.info(f"[STRIPE_INIT] iDEAL payment support: {'ENABLED' if ENABLE_IDEAL_PAYMENT else 'DISABLED'}")

def map_stripe_product_to_plan_id(product_name: str) -> str:
    """Map Stripe product names to internal plan IDs"""
    plan_name = product_name.lower()
    if "fluency builder" in plan_name:
        return "fluency_builder"
    elif "language mastery" in plan_name:
        return "language_mastery"
    elif "team mastery" in plan_name:
        # Backward compatibility - map old name to new plan
        return "language_mastery"
    elif "try learn" in plan_name:
        return "try_learn"
    else:
        # Fallback to the old method
        return product_name.lower().replace(" ", "_").replace("-", "")


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    try:
        data = await request.json()
        price_id = data.get("price_id")
        success_url = data.get("success_url", "http://localhost:3000/profile?checkout=success")
        cancel_url = data.get("cancel_url", "http://localhost:3000/profile?checkout=canceled")

        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID is required")

        # Require authentication for all checkout sessions
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required for checkout")

        # Handle authenticated user checkout
        logger.info(f"[AUTH_CHECKOUT] Creating checkout session for user: {current_user.id}")
        
        # IMMEDIATE DEBUG - Check environment variables right at the start
        logger.info(f"[AUTH_CHECKOUT] IMMEDIATE DEBUG - Stripe API key: {bool(stripe.api_key)}")
        logger.info(f"[AUTH_CHECKOUT] IMMEDIATE DEBUG - Webhook secret: {bool(stripe_webhook_secret)}")
        
        # Check if user already has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)
        logger.info(f"[AUTH_CHECKOUT] User has existing customer ID: {bool(customer_id)}")

        # If not, create a new customer in Stripe
        if not customer_id:
            logger.info(f"[AUTH_CHECKOUT] Creating new Stripe customer...")
            logger.info(f"[AUTH_CHECKOUT] Customer data - email: {current_user.email}, name: {current_user.name}, user_id: {current_user.id}")
            
            try:
                logger.info(f"[AUTH_CHECKOUT] About to call stripe.Customer.create()...")
                customer = stripe.Customer.create(
                    email=current_user.email,
                    name=current_user.name,
                    metadata={"user_id": str(current_user.id)}
                )
                logger.info(f"[AUTH_CHECKOUT] ✅ stripe.Customer.create() completed successfully")
                
                logger.info(f"[AUTH_CHECKOUT] Customer object received: {type(customer)}")
                logger.info(f"[AUTH_CHECKOUT] Customer object: {customer}")
                
                if customer and hasattr(customer, 'id'):
                    customer_id = customer.id
                    logger.info(f"[AUTH_CHECKOUT] ✅ Stripe customer created: {customer_id}")
                else:
                    logger.error(f"[AUTH_CHECKOUT] ❌ Invalid customer object returned from Stripe: {customer}")
                    raise HTTPException(status_code=500, detail="Failed to create Stripe customer")
                    
            except Exception as stripe_customer_error:
                logger.error(f"[AUTH_CHECKOUT] ❌ stripe.Customer.create() failed: {str(stripe_customer_error)}")
                logger.error(f"[AUTH_CHECKOUT] Error type: {type(stripe_customer_error)}")
                import traceback
                logger.error(f"[AUTH_CHECKOUT] Full traceback: {traceback.format_exc()}")
                
                # Check if this is the 'Secret' attribute error
                if "'Secret'" in str(stripe_customer_error):
                    logger.error(f"[AUTH_CHECKOUT] 🔥 FOUND THE SECRET ATTRIBUTE ERROR!")
                    logger.error(f"[AUTH_CHECKOUT] This is likely a Stripe library or webhook configuration issue")
                
                raise HTTPException(status_code=500, detail=f"Stripe customer creation failed: {str(stripe_customer_error)}")

            # Update user with Stripe customer ID in MongoDB
            try:
                logger.info(f"[AUTH_CHECKOUT] About to update MongoDB for user: {current_user.id}")
                from bson import ObjectId
                logger.info(f"[AUTH_CHECKOUT] Converting user ID to ObjectId...")
                user_object_id = ObjectId(current_user.id)
                logger.info(f"[AUTH_CHECKOUT] ObjectId created successfully: {user_object_id}")
                
                logger.info(f"[AUTH_CHECKOUT] Updating user in MongoDB...")
                result = await database["users"].update_one(
                    {"_id": user_object_id},
                    {"$set": {"stripe_customer_id": customer_id}}
                )
                logger.info(f"[AUTH_CHECKOUT] MongoDB update result: {result.modified_count} documents modified")
                logger.info(f"[AUTH_CHECKOUT] Created Stripe customer: {customer_id}")
            except Exception as mongo_error:
                logger.error(f"[AUTH_CHECKOUT] MongoDB update failed: {str(mongo_error)}")
                logger.error(f"[AUTH_CHECKOUT] Error type: {type(mongo_error)}")
                import traceback
                logger.error(f"[AUTH_CHECKOUT] MongoDB traceback: {traceback.format_exc()}")
                # Continue without failing - we can still create checkout session
                pass

        # CRITICAL DEBUG: Add logging right after customer creation
        logger.info(f"[AUTH_CHECKOUT] Customer creation completed successfully: {customer_id}")
        logger.info(f"[AUTH_CHECKOUT] Current user ID: {current_user.id}")
        logger.info(f"[AUTH_CHECKOUT] Price ID: {price_id}")
        logger.info(f"[AUTH_CHECKOUT] Success URL: {success_url}")
        logger.info(f"[AUTH_CHECKOUT] Cancel URL: {cancel_url}")
        
        # Debug Stripe configuration
        logger.info(f"[AUTH_CHECKOUT] Stripe API key configured: {bool(stripe.api_key)}")
        logger.info(f"[AUTH_CHECKOUT] Stripe API key type: {type(stripe.api_key)}")
        if stripe.api_key:
            logger.info(f"[AUTH_CHECKOUT] Stripe API key starts with: {stripe.api_key[:15]}...")
        else:
            logger.error(f"[AUTH_CHECKOUT] ❌ STRIPE API KEY IS NONE!")
        
        # Debug webhook secret (this might be the issue)
        logger.info(f"[AUTH_CHECKOUT] Stripe webhook secret configured: {bool(stripe_webhook_secret)}")
        logger.info(f"[AUTH_CHECKOUT] Stripe webhook secret type: {type(stripe_webhook_secret)}")
        if stripe_webhook_secret:
            logger.info(f"[AUTH_CHECKOUT] Webhook secret starts with: {stripe_webhook_secret[:15]}...")
        else:
            logger.error(f"[AUTH_CHECKOUT] ❌ WEBHOOK SECRET IS NONE!")
        
        # Create checkout session with proper configuration
        try:
            logger.info(f"[AUTH_CHECKOUT] Creating Stripe checkout session...")
            
            # 🔥 FIX: Create checkout session with simplified configuration
            # The 400 error was caused by customer_update conflicting with promotion codes

            # Configure payment methods (card + iDEAL support)
            payment_methods = ["card"]
            if ENABLE_IDEAL_PAYMENT:
                payment_methods.append("ideal")
                logger.info(f"[AUTH_CHECKOUT] iDEAL payment method enabled")

            # Determine if user should get trial
            # Only NEW customers get trial (no current/previous subscription)
            user_plan = getattr(current_user, 'subscription_plan', 'try_learn')
            is_new_customer = user_plan in ['try_learn', 'free', None]

            # Build subscription data
            subscription_data = {
                "metadata": {
                    "user_id": str(current_user.id),
                    "user_email": current_user.email
                }
            }

            # Add 7-day trial ONLY for new customers
            if is_new_customer:
                subscription_data["trial_period_days"] = 7
                logger.info(f"[AUTH_CHECKOUT] New customer - adding 7-day free trial")
            else:
                logger.info(f"[AUTH_CHECKOUT] Existing customer ({user_plan}) - NO trial, immediate charge")

            checkout_session_data = {
                "customer": customer_id,
                "payment_method_types": payment_methods,
                "line_items": [
                    {
                        "price": price_id,
                        "quantity": 1,
                    },
                ],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                # 🔥 PROMO CODE FIX: Enable promotion codes (simplified config)
                "allow_promotion_codes": True,
                # Add metadata for tracking
                "metadata": {
                    "user_id": str(current_user.id),
                    "user_email": current_user.email
                },
                # Add subscription data (with trial for new customers only)
                "subscription_data": subscription_data
            }
            
            logger.info(f"[AUTH_CHECKOUT] Creating checkout session with full configuration...")
            checkout_session = stripe.checkout.Session.create(**checkout_session_data)
            logger.info(f"[AUTH_CHECKOUT] ✅ Checkout session created successfully: {checkout_session.id}")
            logger.info(f"[AUTH_CHECKOUT] ✅ Promotion codes enabled: {checkout_session.allow_promotion_codes}")
            
        except Exception as checkout_error:
            logger.error(f"[AUTH_CHECKOUT] ❌ Checkout session creation failed: {str(checkout_error)}")
            logger.error(f"[AUTH_CHECKOUT] Error type: {type(checkout_error)}")
            import traceback
            logger.error(f"[AUTH_CHECKOUT] Full traceback: {traceback.format_exc()}")
            
            # Try to identify the exact issue
            logger.error(f"[AUTH_CHECKOUT] Stripe API key configured: {bool(stripe.api_key)}")
            logger.error(f"[AUTH_CHECKOUT] Customer ID: {customer_id}")
            logger.error(f"[AUTH_CHECKOUT] Price ID: {price_id}")
            
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to create checkout session: {str(checkout_error)}"
            )

        logger.info(f"[AUTH_CHECKOUT] Created checkout session: {checkout_session.id}")
        return {"url": checkout_session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer-portal")
async def create_customer_portal_session(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        data = await request.json()
        return_url = data.get("return_url", "http://localhost:3000/profile")

        # Check if user has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)
        if not customer_id:
            raise HTTPException(status_code=400, detail="No subscription found for this user")

        # Create customer portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        return {"url": portal_session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer portal session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription-status")
async def get_subscription_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """🔥 FIXED: Use SubscriptionService for consistent data"""
    try:
        # Use the SubscriptionService which has the correct logic including sessions_completed
        status = await SubscriptionService.get_user_subscription_status(current_user.id)
        
        # Convert to dict for JSON response
        response = {
            "status": status.status,
            "plan": status.plan,
            "period": status.period,
            "provider": status.provider,  # stripe, apple, google_play (for mobile conflict detection)
            "limits": status.limits.dict() if status.limits else None,
            "is_in_trial": status.is_in_trial,
            "trial_end_date": status.trial_end_date.isoformat() if status.trial_end_date else None,
            "trial_days_remaining": status.trial_days_remaining
        }
        
        logger.info(f"[SUBSCRIPTION_STATUS] ✅ Response served for user {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription-limits")
async def get_subscription_limits(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's subscription limits and current usage"""
    try:
        status = await SubscriptionService.get_user_subscription_status(current_user.id)
        if status.limits:
            return status.limits.dict()
        else:
            return {"error": "No subscription limits found"}
    except Exception as e:
        logger.error(f"Error getting subscription limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-usage")
async def track_usage(
    request: UsageTrackingRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Track usage of practice sessions or assessments"""
    try:
        # Ensure the request is for the current user
        request.user_id = current_user.id
        
        success = await SubscriptionService.track_usage(request)
        if success:
            return {"success": True, "message": "Usage tracked successfully"}
        else:
            return {"success": False, "message": "Usage limit exceeded"}
    except Exception as e:
        logger.error(f"Error tracking usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-speaking-time")
async def track_speaking_time(
    http_request: Request,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user_from_request)
):
    """Track speaking time and optionally increment session count - supports both authenticated and beacon requests"""
    try:
        # Parse request body
        body = await http_request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is required")
        
        import json
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        # Handle case where user is not authenticated (e.g., sendBeacon from page unload)
        if not current_user:
            # Try to authenticate using token from request body (for sendBeacon)
            token = data.get('token')
            if token:
                try:
                    from auth import get_optional_current_user
                    current_user = await get_optional_current_user(token)
                    logger.info("[PARTIAL_SESSION] Successfully authenticated user from beacon token")
                except Exception as auth_error:
                    logger.warning(f"[PARTIAL_SESSION] Failed to authenticate from beacon token: {str(auth_error)}")
            
            if not current_user:
                logger.warning("[PARTIAL_SESSION] No authenticated user found - skipping speaking time tracking")
                return {"success": False, "message": "Authentication required"}
        
        # Create request object
        request = SpeakingTimeTrackingRequest(
            user_id=current_user.id,
            session_id=data.get('session_id', f"fallback_{current_user.id}_{int(data.get('speaking_minutes', 0) * 1000)}"),
            speaking_minutes=data.get('speaking_minutes', 0.0),
            session_completed=data.get('session_completed', False)
        )
        
        # Log the tracking request
        logger.info(f"[SPEAKING_TIME] Tracking {request.speaking_minutes:.1f} minutes for user {current_user.id}, session_completed: {request.session_completed}")
        
        # 🔥 BULLETPROOF FIX: Use atomic tracking to prevent race conditions
        success = await BulletproofTracker.track_speaking_time_atomic(request)
        if success:
            return {"success": True, "message": "Speaking time tracked successfully"}
        else:
            return {"success": False, "message": "Failed to track speaking time or insufficient balance"}
    except Exception as e:
        logger.error(f"Error tracking speaking time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/can-start-session")
async def can_start_session(
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if user can start a new session based on minute limits"""
    try:
        can_start, message = await SubscriptionService.can_start_session(current_user.id)
        return {
            "can_start": can_start,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error checking session access: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/can-access/{feature_type}")
async def can_access_feature(
    feature_type: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if user can access a specific feature"""
    try:
        can_access, message = await SubscriptionService.can_access_feature(current_user.id, feature_type)
        return {
            "can_access": can_access,
            "message": message,
            "feature_type": feature_type
        }
    except Exception as e:
        logger.error(f"Error checking feature access: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
async def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        plans = SubscriptionService.get_all_plans()
        return {"plans": {plan_id: plan.dict() for plan_id, plan in plans.items()}}
    except Exception as e:
        logger.error(f"Error getting subscription plans: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan/{plan_id}")
async def get_plan_details(plan_id: str):
    """Get details for a specific subscription plan"""
    try:
        plan = SubscriptionService.get_plan_details(plan_id)
        if plan:
            return plan.dict()
        else:
            raise HTTPException(status_code=404, detail="Plan not found")
    except Exception as e:
        logger.error(f"Error getting plan details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/expiry-warning")
async def get_expiry_warning(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get expiry warning message if applicable"""
    try:
        status = await SubscriptionService.get_user_subscription_status(current_user.id)
        
        if status.days_until_expiry is not None:
            warning_message = SubscriptionService.get_expiry_warning_message(status.days_until_expiry)
            return {
                "has_warning": warning_message is not None,
                "message": warning_message,
                "days_until_expiry": status.days_until_expiry
            }
        
        return {"has_warning": False, "message": None, "days_until_expiry": None}
    except Exception as e:
        logger.error(f"Error getting expiry warning: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: UserResponse = Depends(get_current_user)
):
    """Cancel user's active subscription or trial"""
    try:
        # Check if user has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)
        if not customer_id:
            raise HTTPException(status_code=400, detail="No subscription found for this user")

        # Get user's subscription (active or trialing)
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            limit=1
        )

        if not subscriptions.data:
            raise HTTPException(status_code=400, detail="No subscription found")

        subscription = subscriptions.data[0]

        # Handle trial cancellation differently
        if subscription.status == "trialing":
            # Cancel trial immediately in Stripe
            canceled_subscription = stripe.Subscription.cancel(subscription.id)

            # 🔥 COMPLETE RESET TO FREE TIER (match webhook behavior)
            old_plan = current_user.subscription_plan if hasattr(current_user, 'subscription_plan') else "try_learn"

            update_data = {
                "subscription_status": "free",
                "subscription_plan": "try_learn",
                "is_in_trial": False,
                "cancel_at_period_end": False,
            }

            # 🔥 CLEAR subscription fields (keep stripe_customer_id for future resubscriptions)
            unset_data = {
                "stripe_subscription_id": 1,
                "subscription_price_id": 1,
                "subscription_period": 1,
                "subscription_expires_at": 1,
                "subscription_started_at": 1,
                "current_period_start": 1,
                "current_period_end": 1,
                "trial_end_date": 1,
                "cancellation_date": 1,
            }

            # Update user in MongoDB
            from bson import ObjectId

            user_id_obj = ObjectId(current_user.id)
            logger.info(f"[CANCEL_TRIAL] Updating MongoDB for user {user_id_obj}")
            logger.info(f"[CANCEL_TRIAL] Set data: {update_data}")
            logger.info(f"[CANCEL_TRIAL] Unset fields: {list(unset_data.keys())}")

            result = await database["users"].update_one(
                {"_id": user_id_obj},
                {
                    "$set": update_data,
                    "$unset": unset_data
                }
            )

            logger.info(f"[CANCEL_TRIAL] MongoDB update result: matched={result.matched_count}, modified={result.modified_count}")

            if result.matched_count == 0:
                logger.error(f"[CANCEL_TRIAL] ❌ No user found with _id: {user_id_obj}")
                raise HTTPException(status_code=404, detail="User not found")

            if result.modified_count == 0:
                logger.warning(f"[CANCEL_TRIAL] ⚠️  User found but not modified (already in target state?)")

            logger.info(f"[CANCEL_TRIAL] ✅ User {current_user.id} reset to free tier")

            # 🔥 UPDATE HEART SYSTEM back to free tier
            try:
                from services.heart_service import HeartService
                heart_service = HeartService()

                logger.info(f"[CANCEL_TRIAL] Updating heart system: {old_plan} → try_learn")
                await heart_service.update_hearts_on_subscription_change(
                    user_id=str(current_user.id),
                    old_plan=old_plan,
                    new_plan="try_learn"
                )
                logger.info(f"[CANCEL_TRIAL] ✅ Heart system updated to free tier")
            except Exception as heart_error:
                logger.error(f"[CANCEL_TRIAL] ❌ Error updating heart system: {str(heart_error)}")
                import traceback
                logger.error(traceback.format_exc())

            return {
                "success": True,
                "message": "Trial canceled successfully. No charges have been applied.",
                "subscription_id": subscription.id,
                "was_trial": True
            }
        else:
            # Cancel regular subscription at period end
            updated_subscription = stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=True
            )

            # 🔥 FIX: Use "canceling" status instead of "canceled" to indicate active until period end
            await database["users"].update_one(
                {"_id": current_user.id},
                {"$set": {
                    "subscription_status": "canceling",
                    "cancel_at_period_end": True,
                    "cancellation_date": datetime.utcnow()
                }}
            )

            logger.info(f"Subscription scheduled for cancellation for user {current_user.id}")
            
            # Get period end date for better messaging
            period_end_timestamp = updated_subscription.current_period_end if hasattr(updated_subscription, 'current_period_end') and updated_subscription.current_period_end else None
            period_end_date = datetime.fromtimestamp(period_end_timestamp).strftime('%B %d, %Y') if period_end_timestamp else 'the end of your billing period'
            
            return {
                "success": True,
                "message": f"Cancellation scheduled. Your subscription will remain active until {period_end_date}. You can reactivate anytime before then.",
                "subscription_id": subscription.id,
                "cancel_at_period_end": updated_subscription.cancel_at_period_end,
                "current_period_end": int(period_end_timestamp) if period_end_timestamp else None,
                "period_end_date": period_end_date,
                "was_trial": False
            }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error canceling subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reactivate-subscription")
async def reactivate_subscription(
    current_user: UserResponse = Depends(get_current_user)
):
    """Reactivate user's canceled subscription"""
    try:
        # Check if user has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)
        if not customer_id:
            raise HTTPException(status_code=400, detail="No subscription found for this user")

        # Get user's canceled subscription
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1
        )

        if not subscriptions.data:
            raise HTTPException(status_code=400, detail="No subscription found to reactivate")

        subscription = subscriptions.data[0]

        # Check if subscription is set to cancel at period end
        if not subscription.cancel_at_period_end:
            raise HTTPException(status_code=400, detail="Subscription is not scheduled for cancellation")

        # Reactivate the subscription by removing cancel_at_period_end
        updated_subscription = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=False
        )

        # Update user's subscription status in MongoDB and clear cancellation fields
        await database["users"].update_one(
            {"_id": current_user.id},
            {
                "$set": {"subscription_status": "active"},
                "$unset": {
                    "cancel_at_period_end": "",
                    "cancellation_date": ""
                }
            }
        )

        # Clear the Stripe subscription cache to force fresh data
        stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
        if stripe_customer_id:
            cache_key = f"stripe_subscription:{stripe_customer_id}"
            try:
                await perf_cache.delete(cache_key)
                logger.info(f"Cleared Stripe subscription cache for user {current_user.id}")
            except Exception as cache_error:
                logger.warning(f"Could not clear cache: {str(cache_error)}")

        logger.info(f"Subscription reactivated for user {current_user.id}")
        
        # Get period end date for better messaging
        period_end_timestamp = updated_subscription.current_period_end if hasattr(updated_subscription, 'current_period_end') and updated_subscription.current_period_end else None
        period_end_date = datetime.fromtimestamp(period_end_timestamp).strftime('%B %d, %Y') if period_end_timestamp else None
        
        return {
            "success": True,
            "message": f"Subscription reactivated! Your subscription will continue and auto-renew on {period_end_date}." if period_end_date else "Subscription reactivated successfully!",
            "subscription_id": subscription.id,
            "cancel_at_period_end": updated_subscription.cancel_at_period_end,
            "current_period_end": int(period_end_timestamp) if period_end_timestamp else None,
            "period_end_date": period_end_date
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error reactivating subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link-guest-subscription")
async def link_guest_subscription(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Link a guest subscription to the user account after signup"""
    try:
        data = await request.json()
        customer_email = data.get("customer_email", current_user.email)
        session_id = data.get("session_id")
        
        logger.info(f"[LINK-GUEST] Attempting to link subscription for user {current_user.id}, email: {customer_email}")
        
        # Method 1: Try to find customer by session_id if provided
        customer_id = None
        if session_id:
            try:
                logger.info(f"[LINK-GUEST] Looking up checkout session: {session_id}")
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                if checkout_session.customer:
                    customer_id = checkout_session.customer
                    logger.info(f"[LINK-GUEST] Found customer from session: {customer_id}")
            except Exception as e:
                logger.warning(f"[LINK-GUEST] Could not retrieve session {session_id}: {str(e)}")
        
        # Method 2: Find Stripe customer by email if session method failed
        if not customer_id:
            logger.info(f"[LINK-GUEST] Looking up customer by email: {customer_email}")
            customers = stripe.Customer.list(email=customer_email, limit=5)
            
            if not customers.data:
                raise HTTPException(status_code=404, detail="No Stripe customer found with this email")
            
            # Get the most recent customer (in case there are multiple)
            customer = customers.data[0]
            customer_id = customer.id
            logger.info(f"[LINK-GUEST] Found customer by email: {customer_id}")
        
        # Get active subscriptions for this customer
        logger.info(f"[LINK-GUEST] Looking for active subscriptions for customer: {customer_id}")
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=5
        )
        
        if not subscriptions.data:
            # Try all subscriptions if no active ones found
            all_subscriptions = stripe.Subscription.list(customer=customer_id, limit=10)
            logger.warning(f"[LINK-GUEST] No active subscriptions found. Total subscriptions: {len(all_subscriptions.data)}")
            for sub in all_subscriptions.data:
                logger.info(f"[LINK-GUEST] Found subscription {sub.id} with status: {sub.status}")
            raise HTTPException(status_code=404, detail="No active subscription found for this customer")
        
        subscription = subscriptions.data[0]
        logger.info(f"[LINK-GUEST] Found active subscription: {subscription.id}")
        
        # Prepare update data
        update_data = {
            "stripe_customer_id": customer_id,
            "subscription_status": subscription.status,
            "subscription_id": subscription.id
        }
        
        # Add period dates
        from datetime import datetime, timezone
        if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
            update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
        
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
        
        # Reset usage counters for new subscription
        update_data["practice_sessions_used"] = 0
        update_data["assessments_used"] = 0
        
        # Get the plan details
        try:
            if subscription.items and len(subscription.items.data) > 0:
                price = subscription.items.data[0].price
                if price:
                    update_data["subscription_price_id"] = price.id
                    
                    # Get product details
                    product = stripe.Product.retrieve(price.product)
                    update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)
                    
                    # Determine if monthly or annual
                    if price.recurring and price.recurring.interval:
                        update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"
                    
                    logger.info(f"[LINK-GUEST] Plan details: {update_data['subscription_plan']} ({update_data.get('subscription_period', 'unknown')})")
        except Exception as e:
            logger.error(f"[LINK-GUEST] Error processing subscription items: {str(e)}")
            # Continue without plan details
        
        # Update user in MongoDB
        from bson import ObjectId
        logger.info(f"[LINK-GUEST] Updating user {current_user.id} with subscription data")
        result = await database["users"].update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"[LINK-GUEST] Successfully linked subscription {subscription.id} to user {current_user.id}")
            return {
                "success": True,
                "message": "Subscription linked successfully",
                "subscription_id": subscription.id,
                "plan": update_data.get("subscription_plan"),
                "status": subscription.status,
                "customer_id": customer_id
            }
        else:
            logger.warning(f"[LINK-GUEST] No changes made to user {current_user.id} - subscription may already be linked")
            return {
                "success": True,
                "message": "Subscription already linked",
                "subscription_id": subscription.id,
                "plan": update_data.get("subscription_plan"),
                "status": subscription.status,
                "customer_id": customer_id
            }
            
    except stripe.error.StripeError as e:
        logger.error(f"[LINK-GUEST] Stripe error linking subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[LINK-GUEST] Error linking guest subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    try:
        # Get the webhook data
        payload = await request.body()
        
        # Verify the webhook signature
        if not stripe_signature or not stripe_webhook_secret:
            logger.warning("Missing Stripe signature or webhook secret")
            return JSONResponse(status_code=400, content={"error": "Missing Stripe signature or webhook secret"})

        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, stripe_webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid Stripe signature")
            return JSONResponse(status_code=400, content={"error": "Invalid signature"})

        # Handle the event
        if event["type"] == "customer.subscription.created":
            await handle_subscription_created(event["data"]["object"])
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"])
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"])
        elif event["type"] == "customer.subscription.trial_will_end":
            await handle_subscription_trial_will_end(event["data"]["object"])
        elif event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "invoice.payment_succeeded":
            await handle_invoice_payment_succeeded(event["data"]["object"])
        elif event["type"] == "invoice_payment.paid":
            await handle_invoice_payment_paid(event["data"]["object"])
        elif event["type"] == "payment_intent.succeeded":
            await handle_payment_intent_succeeded(event["data"]["object"])

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

async def handle_subscription_created(subscription):
    """Handle subscription created event"""
    try:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("No customer ID in subscription created event")
            return

        # Find user by multiple methods
        user = await find_user_by_customer_id(customer_id)
        if not user:
            return

        # Prepare update data
        update_data = {
            "subscription_status": subscription.get("status"),
            "stripe_subscription_id": subscription.get("id"),  # 🔥 FIX: Standardized field name
            "subscription_provider": "stripe"  # 🔥 FIX: Required for mobile conflict detection
        }
        
        # 🔥 FIX ROOT CAUSE 1: PRESERVE remaining free minutes as a bonus!
        # Calculate remaining free minutes (15 - used)
        current_minutes_used = user.get("practice_minutes_used", 0.0)
        free_plan_limit = 15.0
        remaining_free_minutes = max(0, free_plan_limit - current_minutes_used)
        
        if remaining_free_minutes > 0:
            # User has unused free minutes - preserve them by resetting counter
            # The remaining minutes will be added to their new subscription limit
            update_data["practice_minutes_used"] = 0.0
            logger.info(f"[SUB_CREATED] 🎁 PRESERVING {remaining_free_minutes:.1f} free minutes for user {user['_id']}")
        else:
            # User used all free minutes - reset counter for new subscription
            update_data["practice_minutes_used"] = 0.0
            logger.info(f"[SUB_CREATED] ✅ Resetting counter for user {user['_id']} (no free minutes remaining)")
        
        # Always reset session and assessment counters for new subscription period
        update_data["practice_sessions_used"] = 0
        update_data["assessments_used"] = 0
        
        # Add period dates from Stripe
        from datetime import datetime, timezone
        if subscription.get("current_period_start"):
            update_data["current_period_start"] = datetime.fromtimestamp(subscription.get("current_period_start"), tz=timezone.utc)
            update_data["subscription_started_at"] = datetime.fromtimestamp(subscription.get("current_period_start"), tz=timezone.utc)
        
        if subscription.get("current_period_end"):
            update_data["current_period_end"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
            update_data["subscription_expires_at"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
        
        # Get the plan details
        if subscription.get("items") and subscription.get("items").get("data"):
            price = subscription.get("items").get("data")[0].get("price")
            if price:
                update_data["subscription_price_id"] = price.get("id")

                # Get product details
                product = stripe.Product.retrieve(price.get("product"))
                update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)

                # Determine if monthly or annual
                if price.get("recurring") and price.get("recurring").get("interval"):
                    update_data["subscription_period"] = "monthly" if price.get("recurring").get("interval") == "month" else "annual"

        # 🔥 REMOVE old provider data on Stripe subscription
        unset_data = {
            "subscription": 1,  # Remove nested object
            "subscription_id": 1,  # Remove old field name (now using stripe_subscription_id)
            "apple_transaction_id": 1,
            "apple_product_id": 1,
            "apple_original_transaction_id": 1,
            "apple_is_trial": 1,
            "google_play_product_id": 1,
            "google_play_purchase_token": 1,
            "google_play_order_id": 1,
            "google_play_is_trial": 1,
            "google_play_auto_renewing": 1,
        }

        # Update user in MongoDB
        await database["users"].update_one(
            {"_id": user["_id"]},
            {
                "$set": update_data,
                "$unset": unset_data
            }
        )

        logger.info(f"Subscription created for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")

async def handle_subscription_updated(subscription):
    """Handle subscription updated event - includes trial-to-active transitions"""
    try:
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        
        if not customer_id:
            logger.warning("No customer ID in subscription updated event")
            return

        # Find user by multiple methods
        user = await find_user_by_customer_id(customer_id)
        if not user:
            return

        current_status = user.get("subscription_status")
        new_status = subscription.get("status")
        
        logger.info(f"[SUB_UPDATED] User {user['_id']} subscription {subscription_id}: {current_status} → {new_status}")

        # Prepare update data
        update_data = {
            "subscription_status": new_status
        }

        # Handle cancellation status
        # NOTE: subscription.deleted webhook will do full cleanup, but we handle this
        # for immediate feedback in case there's a delay
        if new_status == "canceled":
            logger.info(f"[SUB_UPDATED] Subscription canceled for user {user['_id']}")
            logger.info(f"[SUB_UPDATED] Will wait for subscription.deleted webhook for full cleanup")
            # Just update status, subscription.deleted will do complete reset
            update_data["cancel_at_period_end"] = subscription.get("cancel_at_period_end", False)

        # Handle trial-to-active transition
        elif current_status == "trialing" and new_status == "active":
            logger.info(f"[SUB_UPDATED] Processing trial-to-active transition for user {user['_id']}")
            
            # Update trial status
            update_data["is_in_trial"] = False
            
            # Reset usage counters for new billing period
            update_data["practice_sessions_used"] = 0
            update_data["assessments_used"] = 0
            
            # Calculate proper monthly expiry date
            from datetime import datetime, timezone
            from dateutil.relativedelta import relativedelta
            
            # Get trial end date if available
            trial_end_date = None
            if subscription.get("trial_end"):
                trial_end_date = datetime.fromtimestamp(subscription.get("trial_end"), tz=timezone.utc)
                update_data["trial_end_date"] = trial_end_date
            
            # Calculate monthly expiry (1 month from trial end or current period start)
            if trial_end_date:
                monthly_expiry = trial_end_date + relativedelta(months=1)
                update_data["subscription_expires_at"] = monthly_expiry
                logger.info(f"[SUB_UPDATED] Set monthly expiry to {monthly_expiry} (1 month from trial end)")
            elif subscription.get("current_period_end"):
                # Fallback to current period end from Stripe
                update_data["subscription_expires_at"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
                logger.info(f"[SUB_UPDATED] Using Stripe current_period_end as expiry")
        
        # Add period dates from Stripe
        from datetime import datetime, timezone
        if subscription.get("current_period_start"):
            update_data["current_period_start"] = datetime.fromtimestamp(subscription.get("current_period_start"), tz=timezone.utc)
            # Only update subscription_started_at if not already set
            if not user.get("subscription_started_at"):
                update_data["subscription_started_at"] = datetime.fromtimestamp(subscription.get("current_period_start"), tz=timezone.utc)
        
        if subscription.get("current_period_end"):
            update_data["current_period_end"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
            # Only update subscription_expires_at if not already calculated above
            if "subscription_expires_at" not in update_data:
                update_data["subscription_expires_at"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
        
        # Get the plan details
        if subscription.get("items") and subscription.get("items").get("data"):
            price = subscription.get("items").get("data")[0].get("price")
            if price:
                update_data["subscription_price_id"] = price.get("id")
                
                # Get product details
                product = stripe.Product.retrieve(price.get("product"))
                update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)
                
                # Determine if monthly or annual
                if price.get("recurring") and price.get("recurring").get("interval"):
                    update_data["subscription_period"] = "monthly" if price.get("recurring").get("interval") == "month" else "annual"

        # Update user in MongoDB
        await database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )

        logger.info(f"[SUB_UPDATED] Successfully updated subscription for user {user['_id']}")

        # NEW: Update heart system when subscription plan changes
        if "subscription_plan" in update_data:
            try:
                from services.heart_service import HeartService
                heart_service = HeartService()

                old_plan = user.get("subscription_plan", "try_learn")
                new_plan = update_data["subscription_plan"]

                if old_plan != new_plan:
                    logger.info(f"[SUB_UPDATED] Updating heart system: {old_plan} → {new_plan}")
                    await heart_service.update_hearts_on_subscription_change(
                        user_id=str(user["_id"]),
                        old_plan=old_plan,
                        new_plan=new_plan
                    )
                    logger.info(f"[SUB_UPDATED] ✅ Heart system updated successfully")
            except Exception as heart_error:
                # Log error but don't fail the webhook
                logger.error(f"[SUB_UPDATED] Error updating heart system: {str(heart_error)}")
                import traceback
                logger.error(traceback.format_exc())

        # Log the transition details for debugging
        if current_status == "trialing" and new_status == "active":
            logger.info(f"[SUB_UPDATED] Trial-to-active transition completed:")
            logger.info(f"  - User: {user['_id']}")
            logger.info(f"  - Subscription: {subscription_id}")
            logger.info(f"  - New expiry: {update_data.get('subscription_expires_at')}")
            logger.info(f"  - Plan: {update_data.get('subscription_plan')}")
            logger.info(f"  - Period: {update_data.get('subscription_period')}")
        
    except Exception as e:
        logger.error(f"[SUB_UPDATED] Error handling subscription updated: {str(e)}")

async def handle_subscription_deleted(subscription):
    """
    Handle subscription deleted event - Reset user to free tier completely

    This fires when:
    1. User cancels during trial (immediate deletion)
    2. User cancels after trial (deletion at period end)
    3. Payment fails and subscription expires
    """
    try:
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")

        if not customer_id:
            logger.warning("[SUB_DELETED] No customer ID in subscription deleted event")
            return

        # Find user by Stripe customer ID
        user = await database["users"].find_one({"stripe_customer_id": customer_id})
        if not user:
            logger.warning(f"[SUB_DELETED] No user found for Stripe customer ID: {customer_id}")
            return

        old_plan = user.get("subscription_plan", "try_learn")
        old_status = user.get("subscription_status", "free")

        logger.info(f"[SUB_DELETED] Processing subscription deletion for user {user['_id']}")
        logger.info(f"[SUB_DELETED] Old plan: {old_plan}, Old status: {old_status}")
        logger.info(f"[SUB_DELETED] Subscription ID: {subscription_id}")

        # 🔥 COMPLETE RESET TO FREE TIER
        update_data = {
            "subscription_status": "free",
            "subscription_plan": "try_learn",
            "is_in_trial": False,
            "cancel_at_period_end": False,
        }

        # 🔥 CLEAR subscription fields (keep stripe_customer_id for future resubscriptions)
        unset_data = {
            "stripe_subscription_id": 1,
            "subscription_price_id": 1,
            "subscription_period": 1,
            "subscription_expires_at": 1,
            "subscription_started_at": 1,
            "current_period_start": 1,
            "current_period_end": 1,
            "trial_end_date": 1,
            "cancellation_date": 1,
        }

        # Update user in MongoDB
        await database["users"].update_one(
            {"_id": user["_id"]},
            {
                "$set": update_data,
                "$unset": unset_data
            }
        )

        logger.info(f"[SUB_DELETED] ✅ User {user['_id']} reset to free tier")
        logger.info(f"[SUB_DELETED] Kept stripe_customer_id for future resubscriptions")

        # 🔥 UPDATE HEART SYSTEM back to free tier
        try:
            from services.heart_service import HeartService
            heart_service = HeartService()

            logger.info(f"[SUB_DELETED] Updating heart system: {old_plan} → try_learn")
            await heart_service.update_hearts_on_subscription_change(
                user_id=str(user["_id"]),
                old_plan=old_plan,
                new_plan="try_learn"
            )
            logger.info(f"[SUB_DELETED] ✅ Heart system updated to free tier")
        except Exception as heart_error:
            # Log error but don't fail the webhook
            logger.error(f"[SUB_DELETED] ❌ Error updating heart system: {str(heart_error)}")
            import traceback
            logger.error(traceback.format_exc())

        logger.info(f"[SUB_DELETED] ✅ Subscription deletion complete for user {user['_id']}")

    except Exception as e:
        logger.error(f"[SUB_DELETED] ❌ Error handling subscription deleted: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

async def handle_subscription_trial_will_end(subscription):
    """Handle subscription trial_will_end event - prepare for trial-to-monthly transition"""
    try:
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        
        if not customer_id:
            logger.warning("No customer ID in subscription trial_will_end event")
            return

        # Find user by multiple methods
        user = await find_user_by_customer_id(customer_id)
        if not user:
            logger.warning(f"No user found for trial ending subscription: {subscription_id}")
            return

        logger.info(f"[TRIAL_WILL_END] Processing trial end for user {user['_id']}, subscription: {subscription_id}")

        # Get fresh subscription data from Stripe to ensure we have latest info
        fresh_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Prepare update data for trial ending
        update_data = {
            "subscription_status": fresh_subscription.status,
            "subscription_id": fresh_subscription.id
        }
        
        # Handle trial end date and future monthly billing
        from datetime import datetime, timezone
        if hasattr(fresh_subscription, 'trial_end') and fresh_subscription.trial_end:
            trial_end_date = datetime.fromtimestamp(fresh_subscription.trial_end, tz=timezone.utc)
            update_data["trial_end_date"] = trial_end_date
            
            # If trial is ending, prepare for monthly billing
            if fresh_subscription.status == "trialing":
                # Calculate when the monthly subscription will expire (1 month from trial end)
                from dateutil.relativedelta import relativedelta
                monthly_expiry = trial_end_date + relativedelta(months=1)
                update_data["subscription_expires_at"] = monthly_expiry
                
                logger.info(f"[TRIAL_WILL_END] Trial ends {trial_end_date}, monthly billing will expire {monthly_expiry}")
            
        # Update current period info
        if hasattr(fresh_subscription, 'current_period_start') and fresh_subscription.current_period_start:
            update_data["current_period_start"] = datetime.fromtimestamp(fresh_subscription.current_period_start, tz=timezone.utc)
        
        if hasattr(fresh_subscription, 'current_period_end') and fresh_subscription.current_period_end:
            update_data["current_period_end"] = datetime.fromtimestamp(fresh_subscription.current_period_end, tz=timezone.utc)
        
        # Get plan details if missing
        if fresh_subscription.items and len(fresh_subscription.items.data) > 0:
            price = fresh_subscription.items.data[0].price
            if price:
                update_data["subscription_price_id"] = price.id
                
                # Get product details
                product = stripe.Product.retrieve(price.product)
                update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)
                
                # Determine if monthly or annual
                if price.recurring and price.recurring.interval:
                    update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"

        # Update user in MongoDB
        await database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        logger.info(f"[TRIAL_WILL_END] Updated user {user['_id']} for upcoming trial end")
        
        # Optional: Send notification email to user about trial ending
        # This could be implemented here or handled by a separate notification service
        
    except Exception as e:
        logger.error(f"[TRIAL_WILL_END] Error handling subscription trial_will_end: {str(e)}")

async def handle_checkout_completed(checkout_session):
    """Handle checkout session completed event"""
    try:
        # Log payment method types used for analytics
        payment_method_types = checkout_session.get("payment_method_types", [])
        logger.info(f"[CHECKOUT_COMPLETED] Payment methods used: {payment_method_types}")
        if "ideal" in payment_method_types:
            logger.info(f"[CHECKOUT_COMPLETED] ✅ iDEAL payment completed successfully")

        # Only process subscription checkouts
        if checkout_session.get("mode") != "subscription":
            return

        customer_id = checkout_session.get("customer")
        client_reference_id = checkout_session.get("client_reference_id")
        
        if not customer_id:
            logger.warning("No customer ID in checkout completed event")
            return

        # Find user by client_reference_id or Stripe customer ID
        user = None
        if client_reference_id:
            user = await database["users"].find_one({"_id": client_reference_id})
        
        if not user:
            user = await database["users"].find_one({"stripe_customer_id": customer_id})
        
        if not user:
            logger.warning(f"No user found for checkout session: {checkout_session.get('id')}")
            return

        # Update user's Stripe customer ID if not already set
        # 🔥 FIX ROOT CAUSE 1: PRESERVE remaining free minutes as a bonus!
        update_data = {"stripe_customer_id": customer_id}
        
        if not user.get("stripe_customer_id"):
            # New subscription - preserve remaining free minutes
            current_minutes_used = user.get("practice_minutes_used", 0.0)
            free_plan_limit = 15.0
            remaining_free_minutes = max(0, free_plan_limit - current_minutes_used)
            
            if remaining_free_minutes > 0:
                # User has unused free minutes - preserve them by resetting counter
                update_data["practice_minutes_used"] = 0.0
                logger.info(f"[CHECKOUT_COMPLETED] 🎁 PRESERVING {remaining_free_minutes:.1f} free minutes for user {user['_id']}")
            else:
                # User used all free minutes - reset counter for new subscription
                update_data["practice_minutes_used"] = 0.0
                logger.info(f"[CHECKOUT_COMPLETED] ✅ Resetting counter for user {user['_id']} (no free minutes remaining)")
            
            # Always reset session and assessment counters
            update_data["practice_sessions_used"] = 0
            update_data["assessments_used"] = 0
        
        await database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        logger.info(f"Updated Stripe customer ID for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling checkout completed: {str(e)}")

async def handle_invoice_payment_succeeded(invoice):
    """Handle invoice payment succeeded event"""
    try:
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")
        
        if not customer_id or not subscription_id:
            logger.warning("Missing customer ID or subscription ID in invoice payment succeeded event")
            return

        # Find user by Stripe customer ID
        user = await database["users"].find_one({"stripe_customer_id": customer_id})
        if not user:
            logger.warning(f"No user found for Stripe customer ID: {customer_id}")
            return

        # Get subscription details from Stripe (expand items to get price/product data)
        subscription = stripe.Subscription.retrieve(
            subscription_id,
            expand=['items.data.price', 'items.data.price.product']
        )

        # 🔥 FIX: Check if this is a renewal (new billing period started)
        from datetime import timezone
        old_period_end = user.get("current_period_end")
        new_period_start = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
        new_period_end = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)

        # 🔥 FIX: Make old_period_end timezone-aware if it exists
        if old_period_end and old_period_end.tzinfo is None:
            old_period_end = old_period_end.replace(tzinfo=timezone.utc)

        is_renewal = False
        if old_period_end and new_period_start > old_period_end:
            is_renewal = True
            logger.info(f"[RENEWAL] Detected renewal for user {user['_id']} - new billing period started")

        # Prepare update data
        update_data = {
            "subscription_status": subscription.status,
            "stripe_subscription_id": subscription.id,  # 🔥 FIX: Standardized field name
            "subscription_provider": "stripe",
            "current_period_start": new_period_start,
            "current_period_end": new_period_end,
            "subscription_expires_at": new_period_end
        }

        # 🔥 RESET usage counters on renewal OR first subscription
        # (Apple/Google always reset, Stripe should too for consistency)
        if is_renewal or old_period_end is None:
            update_data["practice_minutes_used"] = 0.0
            update_data["practice_sessions_used"] = 0
            update_data["assessments_used"] = 0
            if is_renewal:
                logger.info(f"[RENEWAL] Reset usage counters for user {user['_id']}")
            else:
                logger.info(f"[FIRST_SUBSCRIPTION] Reset usage counters for user {user['_id']}")

        # Get the plan details
        if hasattr(subscription.items, 'data') and len(subscription.items.data) > 0:
            price = subscription.items.data[0].price
            if price:
                update_data["subscription_price_id"] = price.id

                # Get product details
                product = stripe.Product.retrieve(price.product)
                update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)

                # Determine if monthly or annual
                if price.recurring and price.recurring.interval:
                    update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"

        # 🔥 REMOVE old provider data on Stripe subscription
        unset_data = {
            "subscription": 1,  # Remove nested object
            "subscription_id": 1,  # Remove old field name (now using stripe_subscription_id)
            "apple_transaction_id": 1,
            "apple_product_id": 1,
            "apple_original_transaction_id": 1,
            "apple_is_trial": 1,
            "google_play_product_id": 1,
            "google_play_purchase_token": 1,
            "google_play_order_id": 1,
            "google_play_is_trial": 1,
            "google_play_auto_renewing": 1,
        }

        # Update user in MongoDB
        await database["users"].update_one(
            {"_id": user["_id"]},
            {
                "$set": update_data,
                "$unset": unset_data
            }
        )

        if is_renewal:
            logger.info(f"✅ [RENEWAL] Updated subscription for user {user['_id']} - usage reset")
        elif old_period_end is None:
            logger.info(f"✅ [FIRST_SUBSCRIPTION] Created subscription for user {user['_id']} - usage reset")
        else:
            logger.info(f"Invoice payment succeeded - updated subscription for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling invoice payment succeeded: {str(e)}")

async def find_user_by_customer_id(customer_id: str):
    """Find user by multiple methods: stripe_customer_id, email, or metadata"""
    # Method 1: Try by stripe_customer_id (existing users)
    user = await database["users"].find_one({"stripe_customer_id": customer_id})
    if user:
        logger.info(f"Found user by stripe_customer_id: {user['_id']}")
        return user
    
    # Method 2: Get customer from Stripe and try by email (new users)
    try:
        customer = stripe.Customer.retrieve(customer_id)
        if customer.email:
            user = await database["users"].find_one({"email": customer.email})
            if user:
                logger.info(f"Found user by email {customer.email}: {user['_id']}")
                # Update user with stripe_customer_id for future lookups
                await database["users"].update_one(
                    {"_id": user["_id"]},
                    {"$set": {"stripe_customer_id": customer_id}}
                )
                logger.info(f"Updated user {user['_id']} with stripe_customer_id: {customer_id}")
                return user
    except Exception as e:
        logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
    
    # Method 3: Try by customer metadata user_id
    try:
        customer = stripe.Customer.retrieve(customer_id)
        if customer.metadata and customer.metadata.get("user_id"):
            from bson import ObjectId
            user_id = customer.metadata.get("user_id")
            user = await database["users"].find_one({"_id": ObjectId(user_id)})
            if user:
                logger.info(f"Found user by metadata user_id: {user['_id']}")
                # Update user with stripe_customer_id for future lookups
                await database["users"].update_one(
                    {"_id": user["_id"]},
                    {"$set": {"stripe_customer_id": customer_id}}
                )
                logger.info(f"Updated user {user['_id']} with stripe_customer_id: {customer_id}")
                return user
    except Exception as e:
        logger.error(f"Error checking customer metadata for {customer_id}: {str(e)}")
    
    logger.warning(f"No user found for Stripe customer ID: {customer_id}")
    return None


async def handle_invoice_payment_paid(invoice_payment):
    """Handle invoice_payment.paid event"""
    try:
        invoice_id = invoice_payment.get("invoice")
        
        if not invoice_id:
            logger.warning("No invoice ID in invoice_payment.paid event")
            return

        logger.info(f"[INVOICE_PAYMENT] Processing invoice payment for invoice: {invoice_id}")

        # Get invoice details from Stripe
        invoice = stripe.Invoice.retrieve(invoice_id)
        customer_id = invoice.customer
        subscription_id = invoice.subscription
        
        if not customer_id or not subscription_id:
            logger.warning("Missing customer ID or subscription ID in invoice")
            return

        # Find user by multiple methods
        user = await find_user_by_customer_id(customer_id)
        if not user:
            return

        # Get subscription details from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Prepare update data
        update_data = {
            "subscription_status": subscription.status,
            "subscription_id": subscription.id
        }
        
        # Add period dates if missing
        from datetime import datetime, timezone
        if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
            update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
        
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
        
        # Get the plan details if missing
        if not user.get("subscription_plan") and subscription.items and len(subscription.items.data) > 0:
            price = subscription.items.data[0].price
            if price:
                update_data["subscription_price_id"] = price.id
                
                # Get product details
                product = stripe.Product.retrieve(price.product)
                update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)
                
                # Determine if monthly or annual
                if price.recurring and price.recurring.interval:
                    update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"

        # Update user in MongoDB
        await database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        logger.info(f"[INVOICE_PAYMENT] Successfully updated subscription for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling invoice_payment.paid: {str(e)}")

async def handle_payment_intent_succeeded(payment_intent):
    """Handle payment_intent.succeeded event - helps catch subscription status updates"""
    try:
        # Check if this payment intent is for a subscription
        if not payment_intent.get("invoice"):
            return
        
        invoice_id = payment_intent.get("invoice")
        logger.info(f"[PAYMENT_INTENT] Processing payment intent for invoice: {invoice_id}")
        
        # Get invoice details from Stripe
        invoice = stripe.Invoice.retrieve(invoice_id)
        customer_id = invoice.customer
        subscription_id = invoice.subscription
        
        if not customer_id or not subscription_id:
            logger.warning(f"[PAYMENT_INTENT] Missing customer ID or subscription ID in invoice {invoice_id}")
            return

        # Find user by multiple methods
        user = await find_user_by_customer_id(customer_id)
        if not user:
            logger.warning(f"[PAYMENT_INTENT] No user found for customer {customer_id}")
            return

        # Get subscription details from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        logger.info(f"[PAYMENT_INTENT] Found subscription {subscription_id} with status: {subscription.status}")
        
        # Check if user's subscription status needs updating
        current_status = user.get("subscription_status")
        if current_status != subscription.status:
            logger.info(f"[PAYMENT_INTENT] Updating user {user['_id']} status from '{current_status}' to '{subscription.status}'")
            
            # Prepare update data
            update_data = {
                "subscription_status": subscription.status,
                "subscription_id": subscription.id
            }
            
            # Add period dates if missing
            from datetime import datetime, timezone
            if hasattr(subscription, 'current_period_start') and subscription.current_period_start:
                update_data["current_period_start"] = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
            
            if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
                update_data["current_period_end"] = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
            
            # Reset usage counters if they don't exist
            if "practice_sessions_used" not in user:
                update_data["practice_sessions_used"] = 0
            if "assessments_used" not in user:
                update_data["assessments_used"] = 0
            
            # Get the plan details if missing
            if not user.get("subscription_plan") and subscription.items and len(subscription.items.data) > 0:
                price = subscription.items.data[0].price
                if price:
                    update_data["subscription_price_id"] = price.id
                    
                    # Get product details
                    product = stripe.Product.retrieve(price.product)
                    update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)
                    
                    # Determine if monthly or annual
                    if price.recurring and price.recurring.interval:
                        update_data["subscription_period"] = "monthly" if price.recurring.interval == "month" else "annual"

            # Update user in MongoDB
            await database["users"].update_one(
                {"_id": user["_id"]},
                {"$set": update_data}
            )
            
            logger.info(f"[PAYMENT_INTENT] Successfully updated subscription status for user {user['_id']}")
        else:
            logger.info(f"[PAYMENT_INTENT] User {user['_id']} already has correct status: {current_status}")
        
    except Exception as e:
        logger.error(f"[PAYMENT_INTENT] Error handling payment_intent.succeeded: {str(e)}")
