"""
Apple In-App Purchase API Routes
Handles receipt verification and subscription management for iOS
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from auth import get_current_user
from models import UserResponse
from database import database
from apple_iap_config import AppleIAPVerifier, get_plan_for_product, APPLE_IAP_PRODUCTS
from subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/apple-iap", tags=["Apple IAP"])


class VerifyReceiptRequest(BaseModel):
    """Request model for receipt verification"""
    receipt_data: str
    product_id: str


class VerifyReceiptResponse(BaseModel):
    """Response model for receipt verification"""
    success: bool
    subscription_active: bool
    plan_id: str
    period: str
    expires_at: Optional[datetime] = None
    is_trial: bool
    transaction_id: str


@router.post("/verify-receipt", response_model=VerifyReceiptResponse)
async def verify_receipt(
    request: VerifyReceiptRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Verify Apple IAP receipt and activate subscription

    Flow:
    1. Verify receipt with Apple
    2. Check if product ID is valid
    3. Create/update subscription in database
    4. Return subscription status
    """
    try:
        logger.info(f"[APPLE_IAP] Receipt verification requested by user {current_user.id}")
        logger.info(f"[APPLE_IAP] Product ID: {request.product_id}")

        # Validate product ID
        plan_config = get_plan_for_product(request.product_id)
        if not plan_config:
            logger.error(f"[APPLE_IAP] Invalid product ID: {request.product_id}")
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {request.product_id}")

        # 🔥 PROVIDER CONFLICT PROTECTION: Check for active subscription from different provider
        user = await database.get_collection("users").find_one({"_id": str(current_user.id)})
        if user:
            current_provider = user.get("subscription_provider")
            current_status = user.get("subscription_status")
            current_expires = user.get("subscription_expires_at")

            # Prevent overwriting active subscription from different provider
            if (current_provider in ["stripe", "google_play"] and
                current_status == "active" and
                current_expires and current_expires > datetime.utcnow()):

                logger.warning(f"[APPLE_IAP] User {current_user.id} has active {current_provider} subscription")
                raise HTTPException(
                    status_code=409,
                    detail=f"You have an active {current_provider} subscription until {current_expires.strftime('%Y-%m-%d')}. Please cancel it before subscribing via Apple."
                )

        # Verify receipt with Apple
        verification_result = await AppleIAPVerifier.verify_receipt(
            receipt_data=request.receipt_data,
            product_id=request.product_id
        )

        if not verification_result.get("valid"):
            logger.error(f"[APPLE_IAP] Receipt verification failed for user {current_user.id}")
            raise HTTPException(status_code=400, detail="Receipt verification failed")

        logger.info(f"[APPLE_IAP] Receipt verified successfully for user {current_user.id}")
        logger.info(f"[APPLE_IAP] Transaction ID: {verification_result.get('transaction_id')}")

        # Create or update subscription
        await _create_or_update_subscription(
            user_id=str(current_user.id),
            plan_config=plan_config,
            verification_result=verification_result
        )

        logger.info(f"[APPLE_IAP] Subscription activated for user {current_user.id}")

        return VerifyReceiptResponse(
            success=True,
            subscription_active=True,
            plan_id=plan_config["plan_id"],
            period=plan_config["period"],
            expires_at=verification_result.get("expires_date"),
            is_trial=verification_result.get("is_trial_period", False),
            transaction_id=verification_result["transaction_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[APPLE_IAP] Error verifying receipt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Receipt verification error: {str(e)}")


async def _create_or_update_subscription(
    user_id: str,
    plan_config: dict,
    verification_result: dict
):
    """Create or update user subscription based on Apple IAP"""

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
        "subscription_provider": "apple",
        "subscription_expires_at": expires_at,

        # Apple-specific fields
        "apple_product_id": verification_result["product_id"],
        "apple_transaction_id": verification_result["transaction_id"],
        "apple_original_transaction_id": verification_result["original_transaction_id"],
        "apple_is_trial": verification_result.get("is_trial_period", False),

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
        "google_purchase_token": 1,
        "google_order_id": 1
    }

    result = await users_collection.update_one(
        {"_id": user_id},
        {
            "$set": update_data,
            "$unset": unset_data
        }
    )

    if result.matched_count == 0:
        logger.error(f"[APPLE_IAP] User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"[APPLE_IAP] ✅ Subscription updated for user {user_id} - Apple IAP {plan_config['period']}")


@router.get("/products")
async def get_products():
    """
    Get list of available Apple IAP products
    Useful for displaying pricing in the app
    """
    try:
        products = []
        for product_id, config in APPLE_IAP_PRODUCTS.items():
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
        logger.error(f"[APPLE_IAP] Error getting products: {str(e)}")
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
        logger.error(f"[APPLE_IAP] Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving subscription status")
