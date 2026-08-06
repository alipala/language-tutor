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
# get_user_query resolves a user id to the right _id type. Users are stored under
# ObjectId, so querying with the raw string matched nothing: the conflict check
# below silently passed and the update matched 0 documents, returning 404 to a
# user Apple had already charged. It falls back to the string form for any
# legacy UUID-keyed document.
from subscription_service import get_user_query
from cache_helpers import invalidate_user_cache, invalidate_subscription_cache

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
        user = await database.get_collection("users").find_one(get_user_query(str(current_user.id)))
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

        # If the transaction carries an appAccountToken, it names the account
        # that started the purchase, and that is authoritative. Enforced only
        # when present: purchases made before the client began sending it, and
        # legacy receipts, have no token and still fall through to the
        # ownership check below.
        app_account_token = verification_result.get("app_account_token")
        if not app_account_token:
            # Expected for purchases started before the client began sending
            # the token, and for legacy receipts. Logged because it is the
            # difference between "the buyer is proven" and "we are relying on
            # the ownership check below" — worth seeing in production.
            logger.info(
                "[APPLE_IAP] Transaction carries no appAccountToken; "
                "falling back to the ownership check"
            )
        if app_account_token:
            # The client encodes a 24-hex ObjectId as a UUID by right-padding
            # with zeros, so stripping hyphens and taking the first 24 chars
            # recovers the original id.
            claimed_user_id = str(app_account_token).replace("-", "")[:24].lower()
            if claimed_user_id != str(current_user.id).lower():
                logger.warning(
                    f"[APPLE_IAP] Transaction was purchased by {claimed_user_id} "
                    f"but user {current_user.id} is trying to claim it"
                )
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "This purchase was made by a different account. "
                        "Please sign in with the account that made the purchase."
                    ),
                )

        # An Apple subscription belongs to an Apple ID, not to an app account.
        # Nothing in a verified receipt says which of our users paid, so without
        # this check the same transaction can be claimed by every app account
        # that signs in on the device — observed in production: one transaction
        # (2000001216903849) granted Fluency Builder to three separate users,
        # two of whom paid nothing. Restore Purchases replays every transaction
        # the Apple ID owns, so a manual restore reproduces it just as easily.
        #
        # original_transaction_id is the stable identity of a subscription
        # across renewals, so it is the right key to claim.
        original_transaction_id = verification_result.get("original_transaction_id")
        if original_transaction_id:
            existing_owner = await database.get_collection("users").find_one(
                {
                    "apple_original_transaction_id": original_transaction_id,
                    "_id": {"$ne": get_user_query(str(current_user.id))["_id"]},
                },
                {"_id": 1, "email": 1},
            )
            if existing_owner:
                logger.warning(
                    f"[APPLE_IAP] User {current_user.id} tried to claim transaction "
                    f"{original_transaction_id}, already owned by {existing_owner['_id']}"
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

        # Offer / campaign attribution. Without these a customer who redeemed a
        # discounted offer code is indistinguishable from one who paid list
        # price, so campaign performance cannot be measured after the fact.
        # apple_offer_identifier names the offer configured in App Store
        # Connect; it identifies the offer, not the individual code.
        "apple_offer_type": verification_result.get("offer_type"),
        "apple_offer_identifier": verification_result.get("offer_identifier"),
        "apple_offer_discount_type": verification_result.get("offer_discount_type"),
        "apple_is_discounted": verification_result.get("is_discounted", False),
        # What Apple charged, in milli-units (9990 = 9.99), so revenue is not
        # inferred from our own price table when an offer was applied.
        "apple_price": verification_result.get("price"),
        "apple_currency": verification_result.get("currency"),

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
        "google_play_product_id": 1,
        "google_play_purchase_token": 1,
        "google_play_order_id": 1,
        "google_play_is_trial": 1,
        "google_play_auto_renewing": 1,
    }

    result = await users_collection.update_one(
        get_user_query(user_id),
        {
            "$set": update_data,
            "$unset": unset_data
        }
    )

    if result.matched_count == 0:
        logger.error(f"[APPLE_IAP] User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    # The user doc is Redis-cached (auth.get_user_by_id), so without this the
    # buyer keeps seeing free-tier limits until the TTL expires. Stripe does the
    # same after every subscription write. Errors are swallowed deliberately: the
    # paid subscription is already committed to MongoDB, and a stale cache entry
    # is recoverable — failing here would 500 a request Apple has already charged.
    for _invalidate in (invalidate_user_cache, invalidate_subscription_cache):
        try:
            await _invalidate(user_id)
        except Exception as _cache_err:
            logger.warning(f"[APPLE_IAP] {_invalidate.__name__} failed for {user_id}: {_cache_err}")

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
            "is_trial": user.get("apple_is_trial", False)
        }

    except Exception as e:
        logger.error(f"[APPLE_IAP] Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving subscription status")
