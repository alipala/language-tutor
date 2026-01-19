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

    # Update user document with Google Play subscription
    update_data = {
        "subscription.plan": plan_config["plan_id"],
        "subscription.status": "active",
        "subscription.provider": "google_play",
        "subscription.google_play_product_id": verification_result["product_id"],
        "subscription.google_play_purchase_token": verification_result["purchase_token"],
        "subscription.google_play_order_id": verification_result["order_id"],
        "subscription.current_period_end": expires_at,
        "subscription.is_trial": verification_result.get("is_trial_period", False),
        "subscription.updated_at": datetime.utcnow()
    }

    result = await users_collection.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        logger.error(f"[GOOGLE_PLAY] User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"[GOOGLE_PLAY] Subscription updated for user {user_id}")


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
    Returns subscription details from database
    """
    try:
        users_collection = database.get_collection("users")
        user = await users_collection.find_one({"_id": str(current_user.id)})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        subscription = user.get("subscription", {})

        return {
            "plan": subscription.get("plan", "try_learn"),
            "status": subscription.get("status", "inactive"),
            "provider": subscription.get("provider"),
            "current_period_end": subscription.get("current_period_end"),
            "is_trial": subscription.get("is_trial", False)
        }

    except Exception as e:
        logger.error(f"[GOOGLE_PLAY] Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving subscription status")
