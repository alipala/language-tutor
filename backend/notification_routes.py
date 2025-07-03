from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from database import database
from auth import get_current_user
from models import (
    UserInDB, NotificationCreate, NotificationInDB, NotificationResponse,
    UserNotificationInDB, UserNotificationResponse, NotificationListResponse,
    NotificationMarkReadRequest, NotificationType
)

# Import admin authentication from admin_routes
from admin_routes import get_current_admin

router = APIRouter(tags=["notifications"])
security = HTTPBearer()

# Admin endpoints for managing notifications
@router.post("/admin/notifications", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_admin = Depends(get_current_admin)
):
    """Create a new notification (Admin only)"""
    
    # Debug logging
    print(f"DEBUG: Received notification data: {notification_data.dict()}")
    print(f"DEBUG: Notification type received: '{notification_data.notification_type}' (type: {type(notification_data.notification_type)})")
    
    # Validate notification type
    valid_types = ["Maintenance", "Special Offer", "Information"]
    print(f"DEBUG: Valid types: {valid_types}")
    print(f"DEBUG: Received type: '{notification_data.notification_type}' (type: {type(notification_data.notification_type)})")
    
    if notification_data.notification_type not in valid_types:
        print(f"DEBUG: Validation failed - '{notification_data.notification_type}' not in {valid_types}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid notification type '{notification_data.notification_type}'. Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate scheduled send time if not sending immediately
    if not notification_data.send_immediately and not notification_data.scheduled_send_time:
        print("DEBUG: Validation failed - scheduled send time required")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scheduled send time is required when not sending immediately"
        )
    
    if notification_data.scheduled_send_time and notification_data.scheduled_send_time <= datetime.utcnow():
        print("DEBUG: Validation failed - scheduled time in past")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scheduled send time must be in the future"
        )
    
    print("DEBUG: All validations passed, creating notification...")
    
    # Create notification document
    notification_doc = NotificationInDB(
        **notification_data.dict(),
        created_by=current_admin.id
    )
    
    print(f"DEBUG: Created notification doc: {notification_doc.dict()}")
    
    # Insert into database
    result = await database.notifications.insert_one(notification_doc.dict(by_alias=True))
    notification_doc.id = str(result.inserted_id)
    
    print(f"DEBUG: Inserted notification with ID: {notification_doc.id}")
    
    # If sending immediately, process in background
    if notification_data.send_immediately:
        background_tasks.add_task(process_notification, str(result.inserted_id))
    else:
        # Schedule for later processing
        background_tasks.add_task(schedule_notification, str(result.inserted_id))
    
    print("DEBUG: Notification created successfully")
    return NotificationResponse(**notification_doc.dict())

@router.get("/admin/notifications")
async def list_notifications_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin = Depends(get_current_admin)
):
    """List all notifications (Admin only)"""
    from bson import ObjectId
    
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    # Set sort direction
    sort_direction = -1 if sort_order.lower() == "desc" else 1
    
    # Get total count
    total_count = await database.notifications.count_documents({})
    
    # Get notifications with pagination
    cursor = database.notifications.find().sort(sort_field, sort_direction).skip(skip).limit(per_page)
    notifications = []
    
    async for doc in cursor:
        # Convert ObjectId to string for frontend
        doc["id"] = str(doc["_id"])
        notifications.append(doc)
    
    return {
        "data": notifications,
        "total": total_count
    }

@router.get("/admin/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification_admin(
    notification_id: str,
    current_admin = Depends(get_current_admin)
):
    """Get a specific notification (Admin only)"""
    
    notification = await database.notifications.find_one({"_id": notification_id})
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return NotificationResponse(**notification)

@router.delete("/admin/notifications/{notification_id}")
async def delete_notification_admin(
    notification_id: str,
    current_admin = Depends(get_current_admin)
):
    """Delete a notification (Admin only)"""
    
    result = await database.notifications.delete_one({"_id": notification_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Also delete all user notifications for this notification
    await database.user_notifications.delete_many({"notification_id": notification_id})
    
    return {"message": "Notification deleted successfully"}

# User endpoints for viewing notifications
@router.get("/", response_model=NotificationListResponse)
async def get_user_notifications(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get notifications for the current user"""
    
    # Build query
    query = {"user_id": current_user.id}
    if unread_only:
        query["is_read"] = False
    
    # Get user notifications with notification details
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "notifications",
            "localField": "notification_id",
            "foreignField": "_id",
            "as": "notification"
        }},
        {"$unwind": "$notification"},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]
    
    cursor = database.user_notifications.aggregate(pipeline)
    notifications = []
    
    async for doc in cursor:
        notification_data = UserNotificationResponse(
            id=doc["_id"],
            user_id=doc["user_id"],
            notification_id=doc["notification_id"],
            is_read=doc["is_read"],
            read_at=doc.get("read_at"),
            created_at=doc["created_at"],
            notification=NotificationResponse(**doc["notification"])
        )
        notifications.append(notification_data)
    
    # Get counts
    total_count = await database.user_notifications.count_documents({"user_id": current_user.id})
    unread_count = await database.user_notifications.count_documents({
        "user_id": current_user.id,
        "is_read": False
    })
    
    return NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count,
        total_count=total_count
    )

@router.get("/unread-count")
async def get_unread_count(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get count of unread notifications for the current user"""
    
    count = await database.user_notifications.count_documents({
        "user_id": current_user.id,
        "is_read": False
    })
    
    return {"unread_count": count}

@router.post("/mark-read")
async def mark_notification_read(
    request: NotificationMarkReadRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Mark a notification as read"""
    
    result = await database.user_notifications.update_one(
        {
            "user_id": current_user.id,
            "notification_id": request.notification_id,
            "is_read": False
        },
        {
            "$set": {
                "is_read": True,
                "read_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read"
        )
    
    return {"message": "Notification marked as read"}

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: UserInDB = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    
    result = await database.user_notifications.update_many(
        {
            "user_id": current_user.id,
            "is_read": False
        },
        {
            "$set": {
                "is_read": True,
                "read_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": f"Marked {result.modified_count} notifications as read"}

# Background task functions
async def process_notification(notification_id: str):
    """Process and send notification to users"""
    from bson import ObjectId
    
    print(f"DEBUG: Processing notification {notification_id}")
    
    # Get notification
    notification = await database.notifications.find_one({"_id": ObjectId(notification_id)})
    if not notification:
        print(f"DEBUG: Notification {notification_id} not found")
        return
    
    print(f"DEBUG: Found notification: {notification.get('title')}")
    
    # Get target users
    if notification.get("target_user_ids"):
        # Send to specific users
        target_users = notification["target_user_ids"]
        print(f"DEBUG: Sending to specific users: {target_users}")
    else:
        # Send to all active users
        cursor = database.users.find({"is_active": True}, {"_id": 1})
        target_users = [str(doc["_id"]) async for doc in cursor]  # Convert ObjectId to string
        print(f"DEBUG: Sending to all active users: {len(target_users)} users")
    
    # Create user notifications
    user_notifications = []
    for user_id in target_users:
        user_notification = UserNotificationInDB(
            user_id=str(user_id),  # Ensure string format
            notification_id=notification_id
        )
        user_notifications.append(user_notification.dict(by_alias=True))
    
    print(f"DEBUG: Creating {len(user_notifications)} user notifications")
    
    if user_notifications:
        result = await database.user_notifications.insert_many(user_notifications)
        print(f"DEBUG: Inserted {len(result.inserted_ids)} user notifications")
    
    # Mark notification as sent
    update_result = await database.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {
            "$set": {
                "is_sent": True,
                "sent_at": datetime.utcnow()
            }
        }
    )
    print(f"DEBUG: Marked notification as sent: {update_result.modified_count} documents updated")

async def schedule_notification(notification_id: str):
    """Schedule notification for later sending"""
    
    # Get notification
    notification = await database.notifications.find_one({"_id": notification_id})
    if not notification or notification.get("is_sent"):
        return
    
    scheduled_time = notification.get("scheduled_send_time")
    if not scheduled_time:
        return
    
    # Calculate delay
    now = datetime.utcnow()
    if scheduled_time <= now:
        # Send immediately if scheduled time has passed
        await process_notification(notification_id)
        return
    
    delay_seconds = (scheduled_time - now).total_seconds()
    
    # Wait until scheduled time
    await asyncio.sleep(delay_seconds)
    
    # Check if notification still exists and hasn't been sent
    notification = await database.notifications.find_one({"_id": notification_id})
    if notification and not notification.get("is_sent"):
        await process_notification(notification_id)

# Utility endpoint to get all users for admin interface
@router.get("/admin/notifications/admin/users", response_model=List[dict])
async def get_users_for_notifications(
    current_admin = Depends(get_current_admin)
):
    """Get list of users for notification targeting (Admin only)"""
    
    cursor = database.users.find(
        {"is_active": True},
        {"_id": 1, "name": 1, "email": 1, "created_at": 1}
    ).sort("name", 1)
    
    users = []
    async for doc in cursor:
        users.append({
            "id": str(doc["_id"]),  # Convert ObjectId to string
            "name": doc["name"],
            "email": doc["email"],
            "created_at": doc["created_at"]
        })
    
    return users
