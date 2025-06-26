from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
import stripe
import os
from auth import get_current_user
from models import UserResponse, UsageTrackingRequest
from database import database
from subscription_service import SubscriptionService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe with API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Create router
router = APIRouter(prefix="/api/stripe", tags=["stripe"])

def map_stripe_product_to_plan_id(product_name: str) -> str:
    """Map Stripe product names to internal plan IDs"""
    plan_name = product_name.lower()
    if "fluency builder" in plan_name:
        return "fluency_builder"
    elif "team mastery" in plan_name:
        return "team_mastery"
    elif "try learn" in plan_name:
        return "try_learn"
    else:
        # Fallback to the old method
        return product_name.lower().replace(" ", "_").replace("-", "")

@router.post("/create-guest-checkout-session")
async def create_guest_checkout_session(request: Request):
    """Create a checkout session for guest users (no authentication required)"""
    try:
        data = await request.json()
        price_id = data.get("price_id")
        success_url = data.get("success_url", "http://localhost:3000/auth/signup?checkout=success")
        cancel_url = data.get("cancel_url", "http://localhost:3000/#pricing")

        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID is required")

        # Create checkout session without a customer (guest checkout)
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            # Store the price_id in metadata for later linking to user account
            metadata={
                "price_id": price_id,
                "guest_checkout": "true"
            }
        )

        return {"url": checkout_session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating guest checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        data = await request.json()
        price_id = data.get("price_id")
        success_url = data.get("success_url", "http://localhost:3000/profile?checkout=success")
        cancel_url = data.get("cancel_url", "http://localhost:3000/profile?checkout=canceled")

        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID is required")

        # Check if user already has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)

        # If not, create a new customer in Stripe
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": str(current_user.id)}
            )
            customer_id = customer.id

            # Update user with Stripe customer ID in MongoDB
            await database["users"].update_one(
                {"_id": current_user.id},
                {"$set": {"stripe_customer_id": customer_id}}
            )

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(current_user.id),
        )

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
    """Get comprehensive subscription status using SubscriptionService"""
    try:
        status = await SubscriptionService.get_user_subscription_status(current_user.id)
        return status.dict()
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
    """Cancel user's active subscription"""
    try:
        # Check if user has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)
        if not customer_id:
            raise HTTPException(status_code=400, detail="No subscription found for this user")

        # Get user's active subscription
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1
        )

        if not subscriptions.data:
            raise HTTPException(status_code=400, detail="No active subscription found")

        subscription = subscriptions.data[0]

        # Cancel the subscription at period end
        updated_subscription = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True
        )

        # Update user's subscription status in MongoDB
        await database["users"].update_one(
            {"_id": current_user.id},
            {"$set": {"subscription_status": "canceled"}}
        )

        logger.info(f"Subscription canceled for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Subscription canceled successfully. Access will continue until the end of your billing period.",
            "subscription_id": subscription.id,
            "cancel_at_period_end": updated_subscription.cancel_at_period_end,
            "current_period_end": int(updated_subscription.current_period_end) if hasattr(updated_subscription, 'current_period_end') and updated_subscription.current_period_end else None
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

        # Update user's subscription status in MongoDB
        await database["users"].update_one(
            {"_id": current_user.id},
            {"$set": {"subscription_status": "active"}}
        )

        logger.info(f"Subscription reactivated for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Subscription reactivated successfully.",
            "subscription_id": subscription.id,
            "cancel_at_period_end": updated_subscription.cancel_at_period_end,
            "current_period_end": int(updated_subscription.current_period_end) if hasattr(updated_subscription, 'current_period_end') and updated_subscription.current_period_end else None
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
        
        # Find Stripe customer by email
        customers = stripe.Customer.list(email=customer_email, limit=1)
        
        if not customers.data:
            raise HTTPException(status_code=404, detail="No Stripe customer found with this email")
        
        customer = customers.data[0]
        customer_id = customer.id
        
        # Get active subscriptions for this customer
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1
        )
        
        if not subscriptions.data:
            raise HTTPException(status_code=404, detail="No active subscription found for this customer")
        
        subscription = subscriptions.data[0]
        
        # Prepare update data
        update_data = {
            "stripe_customer_id": customer_id,
            "subscription_status": subscription.status,
            "subscription_id": subscription.id
        }
        
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
        except Exception as e:
            logger.error(f"Error processing subscription items: {str(e)}")
            # Continue without plan details
        
        # Update user in MongoDB
        from bson import ObjectId
        result = await database["users"].update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Successfully linked subscription {subscription.id} to user {current_user.id}")
            return {
                "success": True,
                "message": "Subscription linked successfully",
                "subscription_id": subscription.id,
                "plan": update_data.get("subscription_plan"),
                "status": subscription.status
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update user subscription")
            
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error linking subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error linking guest subscription: {str(e)}")
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
        elif event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])

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

        # Find user by Stripe customer ID
        user = await database["users"].find_one({"stripe_customer_id": customer_id})
        if not user:
            logger.warning(f"No user found for Stripe customer ID: {customer_id}")
            return

        # Prepare update data
        update_data = {
            "subscription_status": subscription.get("status"),
            "subscription_id": subscription.get("id")
        }
        
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
        
        logger.info(f"Subscription created for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")

async def handle_subscription_updated(subscription):
    """Handle subscription updated event"""
    try:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("No customer ID in subscription updated event")
            return

        # Find user by Stripe customer ID
        user = await database["users"].find_one({"stripe_customer_id": customer_id})
        if not user:
            logger.warning(f"No user found for Stripe customer ID: {customer_id}")
            return

        # Prepare update data
        update_data = {
            "subscription_status": subscription.get("status")
        }
        
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
        
        logger.info(f"Subscription updated for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")

async def handle_subscription_deleted(subscription):
    """Handle subscription deleted event"""
    try:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("No customer ID in subscription deleted event")
            return

        # Find user by Stripe customer ID
        user = await database["users"].find_one({"stripe_customer_id": customer_id})
        if not user:
            logger.warning(f"No user found for Stripe customer ID: {customer_id}")
            return

        # Update user's subscription status
        await database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"subscription_status": "canceled"}}
        )
        
        logger.info(f"Subscription deleted for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")

async def handle_checkout_completed(checkout_session):
    """Handle checkout session completed event"""
    try:
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
        if not user.get("stripe_customer_id"):
            await database["users"].update_one(
                {"_id": user["_id"]},
                {"$set": {"stripe_customer_id": customer_id}}
            )
            logger.info(f"Updated Stripe customer ID for user {user['_id']}")
    except Exception as e:
        logger.error(f"Error handling checkout completed: {str(e)}")
