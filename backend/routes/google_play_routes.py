"""
Google Play Billing API Routes
Handles purchase verification and subscription management for Android
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from auth import get_current_user
from models import UserResponse
from database import database
from google_play_config import GooglePlayVerifier, get_plan_for_product, GOOGLE_PLAY_PRODUCTS
# See the note in apple_iap_routes.py: users are stored under ObjectId, so a raw
# string _id matched nothing — the conflict check passed silently and the update
# 404'd after Google had already charged the user.
from subscription_service import get_user_query
from cache_helpers import invalidate_user_cache, invalidate_subscription_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google-play", tags=["Google Play Billing"])


class VerifyPurchaseRequest(BaseModel):
    """Request model for purchase verification"""
    purchase_token: str
    product_id: str


class VerifyPurchaseResponse(BaseModel):
    """Response model for purchase verification"""
    success: bool
    subscription_active: bool
    plan_id: str
    period: str
    expires_at: Optional[datetime] = None
    is_trial: bool
    order_id: str


@router.post("/verify-purchase", response_model=VerifyPurchaseResponse)
async def verify_purchase(
    request: VerifyPurchaseRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Verify Google Play purchase and activate subscription

    Flow:
    1. Verify purchase with Google Play Developer API
    2. Check if product ID is valid
    3. Create/update subscription in database
    4. Return subscription status
    """
    try:
        logger.info(f"[GOOGLE_PLAY] Purchase verification requested by user {current_user.id}")
        logger.info(f"[GOOGLE_PLAY] Product ID: {request.product_id}")

        # Validate product ID
        plan_config = get_plan_for_product(request.product_id)
        if not plan_config:
            logger.error(f"[GOOGLE_PLAY] Invalid product ID: {request.product_id}")
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {request.product_id}")

        # 🔥 PROVIDER CONFLICT PROTECTION: Check for active subscription from different provider
        user = await database.get_collection("users").find_one(get_user_query(str(current_user.id)))
        if user:
            current_provider = user.get("subscription_provider")
            current_status = user.get("subscription_status")
            current_expires = user.get("subscription_expires_at")

            # Prevent overwriting active subscription from different provider
            if (current_provider in ["stripe", "apple"] and
                current_status == "active" and
                current_expires and current_expires > datetime.utcnow()):

                logger.warning(f"[GOOGLE_PLAY] User {current_user.id} has active {current_provider} subscription")
                raise HTTPException(
                    status_code=409,
                    detail=f"You have an active {current_provider} subscription until {current_expires.strftime('%Y-%m-%d')}. Please cancel it before subscribing via Google Play."
                )

        # Verify purchase with Google Play
        verification_result = await GooglePlayVerifier.verify_purchase(
            purchase_token=request.purchase_token,
            product_id=request.product_id
        )

        if not verification_result.get("valid"):
            logger.error(f"[GOOGLE_PLAY] Purchase verification failed for user {current_user.id}")
            raise HTTPException(status_code=400, detail="Purchase verification failed")

        logger.info(f"[GOOGLE_PLAY] Purchase verified successfully for user {current_user.id}")
        logger.info(f"[GOOGLE_PLAY] Order ID: {verification_result.get('order_id')}")

        # Same ownership gap as Apple (see apple_iap_routes for the production
        # incident): a Play subscription belongs to a Google account, and a
        # verified purchase token says nothing about which of our users paid.
        # Without this, every app account signing in on the device can claim it.
        # The purchase token is the stable identity of a Play subscription.
        if request.purchase_token:
            existing_owner = await database.get_collection("users").find_one(
                {
                    "google_play_purchase_token": request.purchase_token,
                    "_id": {"$ne": get_user_query(str(current_user.id))["_id"]},
                },
                {"_id": 1},
            )
            if existing_owner:
                logger.warning(
                    f"[GOOGLE_PLAY] User {current_user.id} tried to claim a purchase "
                    f"token already owned by {existing_owner['_id']}"
                )
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This subscription is already linked to another account. "
                        "Please sign in with the account that made the purchase, "
                        "or contact support."
                    ),
                )

        # Create or update subscription
        await _create_or_update_subscription(
            user_id=str(current_user.id),
            plan_config=plan_config,
            verification_result=verification_result
        )

        logger.info(f"[GOOGLE_PLAY] Subscription activated for user {current_user.id}")

        return VerifyPurchaseResponse(
            success=True,
            subscription_active=True,
            plan_id=plan_config["plan_id"],
            period=plan_config["period"],
            expires_at=verification_result.get("expires_date"),
            is_trial=verification_result.get("is_trial_period", False),
            order_id=verification_result["order_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GOOGLE_PLAY] Error verifying purchase: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Purchase verification error: {str(e)}")


async def _create_or_update_subscription(
    user_id: str,
    plan_config: dict,
    verification_result: dict
):
    """Create or update user subscription based on Google Play purchase"""

    users_collection = database.get_collection("users")

    # Calculate period end based on plan period
    expires_at = verification_result.get("expires_date")
    now = datetime.utcnow()

    # 🔥 FIX: Use top-level format (consistent with Stripe)
    update_data = {
        # Subscription metadata (top-level)
        "subscription_plan": plan_config["plan_id"],
        "subscription_status": "active",
        "subscription_period": plan_config["period"],
        "subscription_provider": "google_play",
        "subscription_expires_at": expires_at,

        # Google Play-specific fields
        "google_play_product_id": verification_result["product_id"],
        "google_play_purchase_token": verification_result["purchase_token"],
        "google_play_order_id": verification_result["order_id"],
        "google_play_is_trial": verification_result.get("is_trial_period", False),
        "google_play_auto_renewing": verification_result.get("auto_renewing", False),

        # Period tracking
        "current_period_start": now,
        "current_period_end": expires_at,

        # 🔥 RESET usage on new subscription
        "practice_minutes_used": 0.0,
        "practice_sessions_used": 0,
        "assessments_used": 0,

        # Metadata
        "subscription_updated_at": now
    }

    # 🔥 REMOVE old provider data and nested subscription object
    unset_data = {
        "subscription": 1,  # Remove nested object
        "stripe_customer_id": 1,
        "stripe_subscription_id": 1,
        "apple_transaction_id": 1,
        "apple_product_id": 1,
        "apple_original_transaction_id": 1,
        "apple_is_trial": 1,
    }

    result = await users_collection.update_one(
        get_user_query(user_id),
        {
            "$set": update_data,
            "$unset": unset_data
        }
    )

    if result.matched_count == 0:
        logger.error(f"[GOOGLE_PLAY] User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    # See apple_iap_routes: drop the cached user/subscription docs so the buyer
    # does not keep seeing free-tier limits until the Redis TTL expires. Errors
    # are swallowed — the subscription is already committed.
    for _invalidate in (invalidate_user_cache, invalidate_subscription_cache):
        try:
            await _invalidate(user_id)
        except Exception as _cache_err:
            logger.warning(f"[GOOGLE_PLAY] {_invalidate.__name__} failed for {user_id}: {_cache_err}")

    logger.info(f"[GOOGLE_PLAY] ✅ Subscription updated for user {user_id} - Google Play {plan_config['period']}")


@router.get("/products")
async def get_products():
    """
    Get list of available Google Play products
    Useful for displaying pricing in the app
    """
    try:
        products = []
        for product_id, config in GOOGLE_PLAY_PRODUCTS.items():
            products.append({
                "product_id": product_id,
                "plan_id": config["plan_id"],
                "period": config["period"],
                "price": config["price"],
                "minutes": config["minutes"],
                "assessments": config["assessments"]
            })

        return {"products": products}

    except Exception as e:
        logger.error(f"[GOOGLE_PLAY] Error getting products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving products")


@router.get("/subscription-status")
async def get_subscription_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current subscription status for user
    🔥 FIXED: Use top-level fields (consistent with standardized format)
    """
    try:
        users_collection = database.get_collection("users")
        user = await users_collection.find_one(get_user_query(str(current_user.id)))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 🔥 Read from top-level fields (standardized format)
        return {
            "plan": user.get("subscription_plan", "try_learn"),
            "status": user.get("subscription_status", "inactive"),
            "provider": user.get("subscription_provider"),
            "current_period_end": user.get("current_period_end"),
            "is_trial": user.get("google_play_is_trial", False)
        }

    except Exception as e:
        logger.error(f"[GOOGLE_PLAY] Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving subscription status")
