"""
Subscription Routes
Handles newsletter subscription functionality
"""

import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Initialize router
router = APIRouter()

# Pydantic Models
class SubscriptionRequest(BaseModel):
    email: str

# Route Handlers
@router.post("/api/subscribe")
async def subscribe_to_newsletter(request: SubscriptionRequest):
    """
    Subscribe user to newsletter - stores email in MongoDB
    """
    try:
        from database import database

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, request.email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )

        # Check if email already exists
        subscriptions_collection = database["newsletter_subscriptions"]
        existing_subscription = await subscriptions_collection.find_one({"email": request.email})

        if existing_subscription:
            return {
                "success": True,
                "message": "Email already subscribed",
                "already_subscribed": True
            }

        # Create subscription document
        subscription_doc = {
            "email": request.email,
            "subscribed_at": datetime.now(timezone.utc),
            "status": "active",
            "source": "landing_page"
        }

        # Insert into database
        result = await subscriptions_collection.insert_one(subscription_doc)

        if result.inserted_id:
            print(f"New newsletter subscription: {request.email}")
            return {
                "success": True,
                "message": "Successfully subscribed to newsletter",
                "already_subscribed": False
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save subscription"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in newsletter subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing subscription: {str(e)}"
        )
