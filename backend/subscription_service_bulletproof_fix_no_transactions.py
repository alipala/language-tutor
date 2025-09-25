"""
🔥 BULLETPROOF FIX: Subscription Service Speaking Time Deduction (No Transactions)
This version works without MongoDB transactions for Railway deployment.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from database import database
from models import SpeakingTimeTrackingRequest

logger = logging.getLogger(__name__)

class BulletproofSubscriptionServiceNoTransactions:
    """Fixed subscription service that ensures atomic speaking time deduction without transactions"""
    
    @staticmethod
    async def track_speaking_time_atomic(request: SpeakingTimeTrackingRequest) -> bool:
        """
        🔥 BULLETPROOF: Atomic speaking time tracking without MongoDB transactions
        Uses careful ordering and validation to prevent race conditions
        """
        user_id = request.user_id
        session_id = request.session_id
        speaking_minutes = int(round(request.speaking_minutes))  # Always use integers
        session_completed = request.session_completed
        
        logger.info(f"[BULLETPROOF_TRACKING] Starting atomic tracking for user {user_id}")
        logger.info(f"[BULLETPROOF_TRACKING] Session: {session_id}, Minutes: {speaking_minutes}, Completed: {session_completed}")
        
        try:
            # Step 1: Check if already processed (with success validation)
            tracking_collection = database["speaking_time_tracking"]
            already_tracked = await tracking_collection.find_one({
                "user_id": user_id,
                "session_id": session_id,
                "successfully_deducted": True  # 🔥 Only consider it tracked if deduction succeeded
            })
            
            if already_tracked:
                logger.info(f"[BULLETPROOF_TRACKING] Session {session_id} already successfully processed")
                return True
            
            # Step 2: Convert user_id to ObjectId with multiple fallback strategies
            user_object_id = None
            users_collection = database["users"]
            
            # Strategy 1: Try as ObjectId
            try:
                user_object_id = ObjectId(user_id)
                user_doc = await users_collection.find_one({"_id": user_object_id})
                if user_doc:
                    logger.info(f"[BULLETPROOF_TRACKING] Found user with ObjectId: {user_object_id}")
                else:
                    user_object_id = None
            except Exception as e:
                logger.warning(f"[BULLETPROOF_TRACKING] ObjectId conversion failed: {str(e)}")
                user_object_id = None
            
            # Strategy 2: Try as string ID
            if not user_object_id:
                user_doc = await users_collection.find_one({"_id": user_id})
                if user_doc:
                    logger.info(f"[BULLETPROOF_TRACKING] Found user with string ID: {user_id}")
                    user_object_id = user_id
            
            # Strategy 3: Search by field values
            if not user_object_id:
                user_doc = await users_collection.find_one({"id": user_id})
                if user_doc:
                    logger.info(f"[BULLETPROOF_TRACKING] Found user by 'id' field: {user_id}")
                    user_object_id = user_doc["_id"]
            
            if not user_object_id:
                logger.error(f"[BULLETPROOF_TRACKING] ❌ User not found: {user_id}")
                return False
            
            # Step 3: Get current user data with fresh query
            user_doc = await users_collection.find_one({"_id": user_object_id})
            if not user_doc:
                logger.error(f"[BULLETPROOF_TRACKING] ❌ User document not found: {user_object_id}")
                return False
            
            # Step 4: Get subscription details and calculate remaining minutes
            subscription_status = user_doc.get("subscription_status", "free")
            subscription_plan = user_doc.get("subscription_plan", "try_learn")
            subscription_period = user_doc.get("subscription_period", "monthly")
            practice_minutes_used = user_doc.get("practice_minutes_used", 0.0)
            
            # Calculate subscription limits based on plan
            if subscription_plan == "team_mastery":
                minutes_limit = -1  # Unlimited
                current_remaining = float('inf')  # Infinite remaining
            elif subscription_plan == "fluency_builder":
                if subscription_period == "annual":
                    minutes_limit = 1800  # 1800 minutes annually
                else:
                    minutes_limit = 150   # 150 minutes monthly
                current_remaining = max(0, minutes_limit - practice_minutes_used)
            else:  # try_learn
                minutes_limit = 15    # 15 minutes monthly
                current_remaining = max(0, minutes_limit - practice_minutes_used)
            
            logger.info(f"[BULLETPROOF_TRACKING] Plan: {subscription_plan} ({subscription_period})")
            logger.info(f"[BULLETPROOF_TRACKING] Limit: {minutes_limit}, Used: {practice_minutes_used}")
            logger.info(f"[BULLETPROOF_TRACKING] Current remaining: {current_remaining} minutes")
            logger.info(f"[BULLETPROOF_TRACKING] Subscription: {subscription_status}")
            
            # Step 5: Calculate deduction based on correct business rules
            if subscription_plan == "team_mastery":
                # Team Mastery has unlimited minutes - don't deduct
                new_practice_minutes_used = practice_minutes_used
                deducted_amount = 0
                logger.info(f"[BULLETPROOF_TRACKING] Team Mastery (unlimited) - no deduction needed")
            else:
                # ALL OTHER PLANS (including active fluency_builder) need minute deduction
                if current_remaining < speaking_minutes:
                    logger.warning(f"[BULLETPROOF_TRACKING] ⚠️ Not enough minutes remaining: {current_remaining} < {speaking_minutes}")
                    # Record failed attempt
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
                    })
                    return False
                
                # Deduct minutes for all limited plans (try_learn, fluency_builder monthly/annual)
                new_practice_minutes_used = practice_minutes_used + speaking_minutes
                deducted_amount = speaking_minutes
                new_remaining = max(0, current_remaining - speaking_minutes)
                logger.info(f"[BULLETPROOF_TRACKING] Deducting {deducted_amount} minutes")
                logger.info(f"[BULLETPROOF_TRACKING] Minutes used: {practice_minutes_used} → {new_practice_minutes_used}")
                logger.info(f"[BULLETPROOF_TRACKING] Remaining: {current_remaining} → {new_remaining}")
            
            # Step 6: Create tracking record FIRST (before user update for better safety)
            tracking_record = {
                "user_id": user_id,
                "session_id": session_id,
                "speaking_minutes": speaking_minutes,
                "session_completed": session_completed,
                "deducted_amount": deducted_amount,
                "remaining_before": current_remaining,
                "remaining_after": new_remaining,
                "successfully_deducted": False,  # Will be updated after user update succeeds
                "reason": "processing",
                "timestamp": datetime.now(timezone.utc),
                "user_object_id": str(user_object_id),
                "subscription_status": subscription_status
            }
            
            tracking_result = await tracking_collection.insert_one(tracking_record)
            tracking_id = tracking_result.inserted_id
            logger.info(f"[BULLETPROOF_TRACKING] Created tracking record: {tracking_id}")
            
            # Step 7: Update user's practice minutes with conditional update to prevent race conditions
            if subscription_plan == "team_mastery":
                # For unlimited plans, just create tracking record without updating user
                user_update_result = type('MockResult', (), {'modified_count': 1})()  # Mock success
            else:
                user_update_result = await users_collection.update_one(
                    {
                        "_id": user_object_id,
                        "practice_minutes_used": practice_minutes_used  # 🔥 Only update if usage hasn't changed
                    },
                    {
                        "$set": {
                            "practice_minutes_used": new_practice_minutes_used
                        }
                    }
                )
            
            if user_update_result.modified_count == 0:
                logger.warning(f"[BULLETPROOF_TRACKING] ⚠️ User update failed - balance may have changed concurrently")
                # Mark tracking record as failed
                await tracking_collection.update_one(
                    {"_id": tracking_id},
                    {"$set": {
                        "successfully_deducted": False,
                        "reason": "concurrent_modification"
                    }}
                )
                return False
            
            # Step 8: Mark tracking record as successful
            await tracking_collection.update_one(
                {"_id": tracking_id},
                {"$set": {
                    "successfully_deducted": True,
                    "reason": "success"
                }}
            )
            
            logger.info(f"[BULLETPROOF_TRACKING] ✅ SUCCESS: Deducted {deducted_amount} minutes")
            logger.info(f"[BULLETPROOF_TRACKING] ✅ User {user_id}: {current_remaining} → {new_remaining} minutes")
            
            return True
                    
        except Exception as e:
            logger.error(f"[BULLETPROOF_TRACKING] ❌ OPERATION FAILED: {str(e)}")
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
BulletproofTracker = BulletproofSubscriptionServiceNoTransactions
