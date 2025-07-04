from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from database import database, notifications_collection, user_notifications_collection, users_collection
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
    result = await notifications_collection.insert_one(notification_doc.dict(by_alias=True))
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
    total_count = await notifications_collection.count_documents({})
    
    # Get notifications with pagination
    cursor = notifications_collection.find().sort(sort_field, sort_direction).skip(skip).limit(per_page)
    notifications = []
    
    async for doc in cursor:
        # Convert ObjectId to string for frontend
        doc["id"] = str(doc["_id"])
        notifications.append(doc)
    
    return {
        "data": notifications,
        "total": total_count
    }

@router.get("/admin/notifications/{notification_id}")
async def get_notification_admin(
    notification_id: str,
    current_admin = Depends(get_current_admin)
):
    """Get a specific notification (Admin only)"""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    print(f"DEBUG: Getting notification with ID: {notification_id}")
    print(f"DEBUG: ID type: {type(notification_id)}, length: {len(notification_id)}")
    
    try:
        # Try to find notification by string ID first (since our notifications are stored as strings)
        notification = await notifications_collection.find_one({"_id": notification_id})
        print(f"DEBUG: String ID query result: {notification is not None}")
        
        # If not found by string, try ObjectId conversion
        if not notification and ObjectId.is_valid(notification_id):
            object_id = ObjectId(notification_id)
            print(f"DEBUG: Trying ObjectId: {object_id}")
            notification = await notifications_collection.find_one({"_id": object_id})
            print(f"DEBUG: ObjectId query result: {notification is not None}")
        
        if not notification:
            # Debug: show available notification IDs
            all_notifications = []
            async for doc in notifications_collection.find().limit(5):
                all_notifications.append({
                    "id": str(doc["_id"]),
                    "type": type(doc["_id"]).__name__,
                    "title": doc.get("title", "No title")
                })
            print(f"DEBUG: Available notifications: {all_notifications}")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification not found with ID: {notification_id}"
            )
        
        # Ensure the notification has an 'id' field for the frontend
        notification["id"] = str(notification["_id"])
        print(f"DEBUG: Successfully found notification: {notification.get('title', 'No title')}")
        
        return {"data": notification}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"DEBUG: Unexpected error getting notification {notification_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification: {str(e)}"
        )

@router.put("/admin/notifications/{notification_id}")
async def update_notification_admin(
    notification_id: str,
    notification_data: NotificationCreate,
    current_admin = Depends(get_current_admin)
):
    """Update a notification (Admin only)"""
    from bson import ObjectId
    
    try:
        # Check if notification exists (try string ID first, then ObjectId)
        existing = await notifications_collection.find_one({"_id": notification_id})
        if not existing and ObjectId.is_valid(notification_id):
            existing = await notifications_collection.find_one({"_id": ObjectId(notification_id)})
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Prepare update data
        update_data = notification_data.dict()
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the notification using the same ID format as found
        result = await notifications_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes made to notification"
            )
        
        # Get updated notification
        updated_notification = await notifications_collection.find_one({"_id": existing["_id"]})
        updated_notification["id"] = str(updated_notification["_id"])
        
        return {"data": updated_notification}
    except Exception as e:
        print(f"Error updating notification {notification_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}"
        )

@router.delete("/admin/notifications/{notification_id}")
async def delete_notification_admin(
    notification_id: str,
    current_admin = Depends(get_current_admin)
):
    """Delete a notification (Admin only)"""
    from bson import ObjectId
    
    try:
        # Try string ID first, then ObjectId
        result = await notifications_collection.delete_one({"_id": notification_id})
        if result.deleted_count == 0 and ObjectId.is_valid(notification_id):
            result = await notifications_collection.delete_one({"_id": ObjectId(notification_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Also delete all user notifications for this notification
        await user_notifications_collection.delete_many({"notification_id": notification_id})
        
        return {"data": {"id": notification_id, "message": "Notification deleted successfully"}}
    except Exception as e:
        print(f"Error deleting notification {notification_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

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
    
    cursor = user_notifications_collection.aggregate(pipeline)
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
    total_count = await user_notifications_collection.count_documents({"user_id": current_user.id})
    unread_count = await user_notifications_collection.count_documents({
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
    
    count = await user_notifications_collection.count_documents({
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
    
    result = await user_notifications_collection.update_one(
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
    
    result = await user_notifications_collection.update_many(
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
    from database import notifications_collection, user_notifications_collection, users_collection
    
    print(f"DEBUG: Processing notification {notification_id}")
    
    try:
        # Get notification - try string ID first, then ObjectId
        notification = await notifications_collection.find_one({"_id": notification_id})
        if not notification and ObjectId.is_valid(notification_id):
            notification = await notifications_collection.find_one({"_id": ObjectId(notification_id)})
        
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
            cursor = users_collection.find({"is_active": True}, {"_id": 1})
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
            result = await user_notifications_collection.insert_many(user_notifications)
            print(f"DEBUG: Inserted {len(result.inserted_ids)} user notifications")
        
        # Mark notification as sent - use the same ID format as found
        update_result = await notifications_collection.update_one(
            {"_id": notification["_id"]},
            {
                "$set": {
                    "is_sent": True,
                    "sent_at": datetime.utcnow()
                }
            }
        )
        print(f"DEBUG: Marked notification as sent: {update_result.modified_count} documents updated")
        
    except Exception as e:
        print(f"ERROR: Failed to process notification {notification_id}: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

async def schedule_notification(notification_id: str):
    """Schedule notification for later sending"""
    from bson import ObjectId
    
    # Get notification - try string ID first, then ObjectId
    notification = await notifications_collection.find_one({"_id": notification_id})
    if not notification and ObjectId.is_valid(notification_id):
        notification = await notifications_collection.find_one({"_id": ObjectId(notification_id)})
    
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
    
    # Check if notification still exists and hasn't been sent - use same ID handling
    notification = await notifications_collection.find_one({"_id": notification_id})
    if not notification and ObjectId.is_valid(notification_id):
        notification = await notifications_collection.find_one({"_id": ObjectId(notification_id)})
    
    if notification and not notification.get("is_sent"):
        await process_notification(notification_id)

# Utility endpoint to get all users for admin interface
@router.get("/admin/notifications/admin/users", response_model=List[dict])
async def get_users_for_notifications(
    current_admin = Depends(get_current_admin)
):
    """Get list of users for notification targeting (Admin only)"""
    
    cursor = users_collection.find(
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
