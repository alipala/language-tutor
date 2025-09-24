"""
🔥 BULLETPROOF FIX: Subscription Service Speaking Time Deduction
This fixes the race condition and silent failures in speaking time tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from database import database
from models import SpeakingTimeTrackingRequest

logger = logging.getLogger(__name__)

class BulletproofSubscriptionService:
    """Fixed subscription service that ensures atomic speaking time deduction"""
    
    @staticmethod
    async def track_speaking_time_atomic(request: SpeakingTimeTrackingRequest) -> bool:
        """
        🔥 BULLETPROOF: Atomic speaking time tracking that ensures both tracking and deduction succeed together
        """
        user_id = request.user_id
        session_id = request.session_id
        speaking_minutes = int(round(request.speaking_minutes))  # Always use integers
        session_completed = request.session_completed
        
        logger.info(f"[BULLETPROOF_TRACKING] Starting atomic tracking for user {user_id}")
        logger.info(f"[BULLETPROOF_TRACKING] Session: {session_id}, Minutes: {speaking_minutes}, Completed: {session_completed}")
        
        try:
            # 🔥 CRITICAL: Use MongoDB transaction to ensure atomicity
            async with await database.client.start_session() as session:
                async with session.start_transaction():
                    
                    # Step 1: Check if already processed (with transaction safety)
                    tracking_collection = database["speaking_time_tracking"]
                    already_tracked = await tracking_collection.find_one(
                        {
                            "user_id": user_id,
                            "session_id": session_id,
                            "successfully_deducted": True  # 🔥 Only consider it tracked if deduction succeeded
                        },
                        session=session
                    )
                    
                    if already_tracked:
                        logger.info(f"[BULLETPROOF_TRACKING] Session {session_id} already successfully processed")
                        return True
                    
                    # Step 2: Convert user_id to ObjectId with multiple fallback strategies
                    user_object_id = None
                    users_collection = database["users"]
                    
                    # Strategy 1: Try as ObjectId
                    try:
                        user_object_id = ObjectId(user_id)
                        user_doc = await users_collection.find_one({"_id": user_object_id}, session=session)
                        if user_doc:
                            logger.info(f"[BULLETPROOF_TRACKING] Found user with ObjectId: {user_object_id}")
                        else:
                            user_object_id = None
                    except Exception as e:
                        logger.warning(f"[BULLETPROOF_TRACKING] ObjectId conversion failed: {str(e)}")
                        user_object_id = None
                    
                    # Strategy 2: Try as string ID
                    if not user_object_id:
                        user_doc = await users_collection.find_one({"_id": user_id}, session=session)
                        if user_doc:
                            logger.info(f"[BULLETPROOF_TRACKING] Found user with string ID: {user_id}")
                            user_object_id = user_id
                    
                    # Strategy 3: Search by field values
                    if not user_object_id:
                        user_doc = await users_collection.find_one({"id": user_id}, session=session)
                        if user_doc:
                            logger.info(f"[BULLETPROOF_TRACKING] Found user by 'id' field: {user_id}")
                            user_object_id = user_doc["_id"]
                    
                    if not user_object_id:
                        logger.error(f"[BULLETPROOF_TRACKING] ❌ User not found: {user_id}")
                        return False
                    
                    # Step 3: Get current user data
                    user_doc = await users_collection.find_one({"_id": user_object_id}, session=session)
                    if not user_doc:
                        logger.error(f"[BULLETPROOF_TRACKING] ❌ User document not found: {user_object_id}")
                        return False
                    
                    # Step 4: Check subscription limits
                    current_remaining = user_doc.get("speaking_time_remaining", 150)  # Default 150 minutes
                    subscription_status = user_doc.get("subscription_status", "free")
                    
                    logger.info(f"[BULLETPROOF_TRACKING] Current remaining: {current_remaining} minutes")
                    logger.info(f"[BULLETPROOF_TRACKING] Subscription: {subscription_status}")
                    
                    # Step 5: Deduct speaking time (only if user has enough)
                    if subscription_status != "active" and current_remaining < speaking_minutes:
                        logger.warning(f"[BULLETPROOF_TRACKING] ⚠️ Not enough minutes remaining: {current_remaining} < {speaking_minutes}")
                        # Still track the attempt but don't deduct
                        await tracking_collection.insert_one({
                            "user_id": user_id,
                            "session_id": session_id,
                            "speaking_minutes": speaking_minutes,
                            "session_completed": session_completed,
                            "deducted_amount": 0,  # No deduction due to insufficient balance
                            "remaining_before": current_remaining,
                            "remaining_after": current_remaining,
                            "successfully_deducted": False,
                            "reason": "insufficient_balance",
                            "timestamp": datetime.now(timezone.utc),
                            "user_object_id": str(user_object_id)
                        }, session=session)
                        return False
                    
                    # Step 6: Calculate new remaining time
                    if subscription_status == "active":
                        # Unlimited for active subscribers - don't deduct
                        new_remaining = current_remaining
                        deducted_amount = 0
                        logger.info(f"[BULLETPROOF_TRACKING] Active subscriber - no deduction needed")
                    else:
                        # Deduct for free users
                        new_remaining = max(0, current_remaining - speaking_minutes)
                        deducted_amount = current_remaining - new_remaining
                        logger.info(f"[BULLETPROOF_TRACKING] Deducting {deducted_amount} minutes: {current_remaining} → {new_remaining}")
                    
                    # Step 7: Update user's speaking time atomically
                    user_update_result = await users_collection.update_one(
                        {"_id": user_object_id},
                        {
                            "$set": {
                                "speaking_time_remaining": new_remaining
                            },
                            "$inc": {
                                "speaking_minutes_used": deducted_amount
                            }
                        },
                        session=session
                    )
                    
                    if user_update_result.modified_count == 0:
                        logger.error(f"[BULLETPROOF_TRACKING] ❌ Failed to update user document")
                        return False
                    
                    # Step 8: Record successful tracking
                    await tracking_collection.insert_one({
                        "user_id": user_id,
                        "session_id": session_id,
                        "speaking_minutes": speaking_minutes,
                        "session_completed": session_completed,
                        "deducted_amount": deducted_amount,
                        "remaining_before": current_remaining,
                        "remaining_after": new_remaining,
                        "successfully_deducted": True,
                        "reason": "success",
                        "timestamp": datetime.now(timezone.utc),
                        "user_object_id": str(user_object_id),
                        "subscription_status": subscription_status
                    }, session=session)
                    
                    logger.info(f"[BULLETPROOF_TRACKING] ✅ SUCCESS: Deducted {deducted_amount} minutes")
                    logger.info(f"[BULLETPROOF_TRACKING] ✅ User {user_id}: {current_remaining} → {new_remaining} minutes")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"[BULLETPROOF_TRACKING] ❌ TRANSACTION FAILED: {str(e)}")
            import traceback
            logger.error(f"[BULLETPROOF_TRACKING] Full traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    async def get_user_remaining_time(user_id: str) -> Optional[int]:
        """Get user's remaining speaking time with robust ID handling"""
        try:
            users_collection = database["users"]
            
            # Try multiple ID formats
            for query in [{"_id": ObjectId(user_id)}, {"_id": user_id}, {"id": user_id}]:
                try:
                    user_doc = await users_collection.find_one(query)
                    if user_doc:
                        remaining = user_doc.get("speaking_time_remaining", 150)
                        logger.info(f"[BULLETPROOF_TRACKING] User {user_id} has {remaining} minutes remaining")
                        return remaining
                except Exception as e:
                    continue
            
            logger.warning(f"[BULLETPROOF_TRACKING] User not found: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"[BULLETPROOF_TRACKING] Error getting remaining time: {str(e)}")
            return None

# Export the fixed service
BulletproofTracker = BulletproofSubscriptionService
