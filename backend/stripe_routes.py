from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
import stripe
import os
from auth import get_current_user
from models import UserResponse
from database import database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe with API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Create router
router = APIRouter(prefix="/api/stripe", tags=["stripe"])

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
    try:
        # Check if user has a Stripe customer ID
        customer_id = getattr(current_user, 'stripe_customer_id', None)
        if not customer_id:
            return {
                "status": None,
                "plan": None,
                "period": None,
                "price_id": None
            }

        # Get customer's active subscriptions first
        active_subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            expand=["data.default_payment_method"],
            limit=1
        )
        
        logger.info(f"Active subscriptions found: {len(active_subscriptions.data)}")

        # If no active subscriptions, check for any subscription
        if not active_subscriptions.data:
            all_subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status="all",
                expand=["data.default_payment_method"],
                limit=1
            )
            
            if not all_subscriptions.data:
                return {
                    "status": None,
                    "plan": None,
                    "period": None,
                    "price_id": None
                }
            
            subscription = all_subscriptions.data[0]
        else:
            subscription = active_subscriptions.data[0]

        logger.info(f"Subscription object type: {type(subscription)}")
        
        # Access subscription items correctly - it's an attribute, not a method
        subscription_items = subscription['items']['data'][0]
        price = subscription_items['price']
        
        logger.info(f"Price retrieved: {price['id']}")
        
        product = stripe.Product.retrieve(price['product'])
        logger.info(f"Product retrieved: {product.name}")

        # Determine if monthly or annual
        period = "monthly" if price['recurring']['interval'] == "month" else "annual"

        return {
            "status": subscription['status'],
            "plan": product.name.lower().replace(" ", "_").replace("-", "_"),
            "period": period,
            "price_id": price['id']
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
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
                update_data["subscription_plan"] = product.name.lower().replace(" ", "_")
                
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
                update_data["subscription_plan"] = product.name.lower().replace(" ", "_")
                
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
