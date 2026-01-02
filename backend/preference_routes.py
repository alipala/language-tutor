"""
Preference Routes
API endpoints for managing user preferences (notification settings, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime
from bson import ObjectId

from models import (
    NotificationPreferencesInDB,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    UserInDB
)
from database import notification_preferences_collection
from auth import get_current_user

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("/notifications", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get user's notification preferences.
    Creates default preferences if none exist.
    """
    # Try to find existing preferences
    preferences = await notification_preferences_collection.find_one(
        {"user_id": current_user.id}
    )

    # If no preferences exist, create default ones
    if not preferences:
        default_prefs = NotificationPreferencesInDB(
            user_id=current_user.id,
            practice_reminders_enabled=False,  # Default OFF - opt-in
            achievement_alerts_enabled=True,   # Default ON
            learning_plan_updates_enabled=True,  # Default ON
            product_updates_enabled=True,  # Default ON
            preferred_notification_time=18,  # 6 PM (works well globally: 10 AM PST, 1 PM EST, 6 PM London)
            timezone="UTC",  # Default to UTC, will work with user's local time when set properly
            quiet_hours_enabled=False,
            quiet_hours_start=22,  # 10 PM
            quiet_hours_end=8,  # 8 AM
            max_notifications_per_week=3,
        )

        # Save to database
        prefs_dict = default_prefs.model_dump(by_alias=True)
        await notification_preferences_collection.insert_one(prefs_dict)

        preferences = prefs_dict

    # Convert ObjectId to string for response
    preferences["_id"] = str(preferences["_id"])

    return NotificationPreferencesResponse(**preferences)


@router.put("/notifications", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update user's notification preferences.
    Only updates fields that are provided (partial update).
    """
    # Get existing preferences or create default
    existing_prefs = await notification_preferences_collection.find_one(
        {"user_id": current_user.id}
    )

    if not existing_prefs:
        # Create default preferences first
        default_prefs = NotificationPreferencesInDB(
            user_id=current_user.id,
            practice_reminders_enabled=False,
            achievement_alerts_enabled=True,
            learning_plan_updates_enabled=True,
            product_updates_enabled=True,
            preferred_notification_time=18,  # 6 PM (works well globally)
            timezone="UTC",  # Default to UTC
            quiet_hours_enabled=False,
            quiet_hours_start=22,
            quiet_hours_end=8,
            max_notifications_per_week=3,
        )

        prefs_dict = default_prefs.model_dump(by_alias=True)
        await notification_preferences_collection.insert_one(prefs_dict)
        existing_prefs = prefs_dict

    # Build update dict with only provided fields
    update_data = {}
    update_fields = preferences_update.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        # Validate hour fields
        if field == "preferred_notification_time" and value is not None:
            if not (0 <= value <= 23):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="preferred_notification_time must be between 0 and 23"
                )

        if field in ["quiet_hours_start", "quiet_hours_end"] and value is not None:
            if not (0 <= value <= 23):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{field} must be between 0 and 23"
                )

        if field == "max_notifications_per_week" and value is not None:
            if not (0 <= value <= 20):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="max_notifications_per_week must be between 0 and 20"
                )

        update_data[field] = value

    # Always update the updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()

    # Update in database
    result = await notification_preferences_collection.update_one(
        {"user_id": current_user.id},
        {"$set": update_data}
    )

    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

    # Fetch updated preferences
    updated_prefs = await notification_preferences_collection.find_one(
        {"user_id": current_user.id}
    )

    # Convert ObjectId to string for response
    updated_prefs["_id"] = str(updated_prefs["_id"])

    return NotificationPreferencesResponse(**updated_prefs)


@router.post("/notifications/reset", response_model=NotificationPreferencesResponse)
async def reset_notification_preferences(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Reset notification preferences to default values.
    """
    default_prefs = NotificationPreferencesInDB(
        user_id=current_user.id,
        practice_reminders_enabled=False,
        achievement_alerts_enabled=True,
        learning_plan_updates_enabled=True,
        product_updates_enabled=True,
        preferred_notification_time=10,
        timezone=None,
        quiet_hours_enabled=False,
        quiet_hours_start=22,
        quiet_hours_end=8,
        max_notifications_per_week=3,
    )

    # Delete existing preferences
    await notification_preferences_collection.delete_one({"user_id": current_user.id})

    # Insert default preferences
    prefs_dict = default_prefs.model_dump(by_alias=True)
    await notification_preferences_collection.insert_one(prefs_dict)

    # Convert ObjectId to string for response
    prefs_dict["_id"] = str(prefs_dict["_id"])

    return NotificationPreferencesResponse(**prefs_dict)
