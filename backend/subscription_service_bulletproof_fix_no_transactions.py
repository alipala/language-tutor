"""
🔥 BULLETPROOF FIX: Subscription Service Speaking Time Deduction (No Transactions)
This version works without MongoDB transactions for Railway deployment.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from database import database, daily_stats_collection
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

        # Guard: if the session rounded to 0 minutes, treat as 1 minute minimum so
        # the $set update actually changes the document and isn't a silent no-op.
        # This prevents the modified_count == 0 false-positive race-condition path.
        if speaking_minutes == 0:
            logger.info(f"[BULLETPROOF_TRACKING] speaking_minutes rounded to 0 — enforcing 1-minute minimum")
            speaking_minutes = 1
        
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
            if subscription_plan in ("team_mastery", "language_mastery"):
                # Unlimited plans — sentinel `-1` for both limit and remaining
                # so the value is JSON/BSON-serializable in tracking records.
                minutes_limit = -1
                current_remaining = -1
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
            if subscription_plan == "team_mastery" or subscription_plan == "language_mastery":
                # Unlimited plans - don't deduct
                new_practice_minutes_used = practice_minutes_used
                deducted_amount = 0
                # Mirror current_remaining (sentinel -1 for unlimited) so the
                # tracking record below has a consistent before/after.
                new_remaining = current_remaining
                logger.info(f"[BULLETPROOF_TRACKING] Unlimited plan ({subscription_plan}) - no deduction needed")
            else:
                # ALL OTHER PLANS (including active fluency_builder) need minute deduction
                # 🔥 FIX: Prevent minutes from going negative - cap at minutes_limit
                if current_remaining <= 0:
                    logger.warning(f"[BULLETPROOF_TRACKING] ⚠️ No minutes remaining: {current_remaining}")
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
                        "reason": "no_minutes_remaining",
                        "timestamp": datetime.now(timezone.utc),
                        "user_object_id": str(user_object_id)
                    })
                    return False

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

                # 🔥 FIX: Enforce hard limit - never allow practice_minutes_used to exceed minutes_limit
                if new_practice_minutes_used > minutes_limit and minutes_limit != -1:
                    logger.error(f"[BULLETPROOF_TRACKING] ❌ HARD LIMIT VIOLATION PREVENTED: Would exceed limit ({new_practice_minutes_used} > {minutes_limit})")
                    await tracking_collection.insert_one({
                        "user_id": user_id,
                        "session_id": session_id,
                        "speaking_minutes": speaking_minutes,
                        "session_completed": session_completed,
                        "deducted_amount": 0,
                        "remaining_before": current_remaining,
                        "remaining_after": current_remaining,
                        "successfully_deducted": False,
                        "reason": "would_exceed_hard_limit",
                        "timestamp": datetime.now(timezone.utc),
                        "user_object_id": str(user_object_id)
                    })
                    return False

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
            
            # Step 7: Update user's practice minutes atomically
            # Use $inc so the update is always a real document change (avoids the
            # modified_count == 0 false-positive when new_value == old_value).
            # The conditional check on practice_minutes_used is kept to guard
            # against concurrent double-deductions.
            if subscription_plan in ("team_mastery", "language_mastery"):
                # For unlimited plans, just create tracking record without updating user
                user_update_result = type('MockResult', (), {'modified_count': 1})()  # Mock success
            else:
                user_update_result = await users_collection.update_one(
                    {
                        "_id": user_object_id,
                        "practice_minutes_used": practice_minutes_used  # Only update if usage hasn't changed
                    },
                    {
                        "$inc": {
                            "practice_minutes_used": deducted_amount
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
            
            # Step 9: 🔥 CRITICAL FIX: Increment session counter for completed sessions
            if session_completed and deducted_amount > 0:
                try:
                    session_counter_result = await users_collection.update_one(
                        {"_id": user_object_id},
                        {"$inc": {"practice_sessions_used": 1}}
                    )
                    
                    if session_counter_result.modified_count > 0:
                        logger.info(f"[BULLETPROOF_TRACKING] ✅ Session counter incremented for completed session")
                    else:
                        logger.warning(f"[BULLETPROOF_TRACKING] ⚠️ Failed to increment session counter")
                        
                except Exception as session_error:
                    logger.error(f"[BULLETPROOF_TRACKING] ❌ Error incrementing session counter: {str(session_error)}")
                    # Don't fail the entire operation if session counting fails
            else:
                logger.info(f"[BULLETPROOF_TRACKING] ℹ️ Session not completed or no deduction - not counting session")
            
            # Step 10: 🔥 NEW FIX: Create conversation_session for frontend display
            if session_completed and deducted_amount > 0:
                await BulletproofTracker.create_conversation_session_for_billing(
                    user_id, session_id, speaking_minutes, session_completed
                )

            # Step 11: Bust the recent_performance cache so next profile load recalculates fresh.
            # NOTE: daily_stats time/session counters are written by the session endpoints
            # (session_summary_routes.py for LP sessions, progress_routes.py for practice/news).
            # BulletproofTracker must NOT write to daily_stats — doing so causes double-counting
            # since every session endpoint already writes the correct time before calling the tracker.
            try:
                recent_performance_collection = database["recent_performance"]
                await recent_performance_collection.delete_one({'user_id': user_id})
                logger.info(f"[BULLETPROOF_TRACKING] 🗑️ recent_performance cache cleared for user {user_id}")
            except Exception as ds_err:
                logger.error(f"[BULLETPROOF_TRACKING] ⚠️ cache clear failed: {ds_err}")

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
    
    @staticmethod
    async def create_conversation_session_for_billing(user_id: str, session_id: str, minutes: float, session_completed: bool):
        """🔥 BILLING BRIDGE: Create conversation_session record when billing tracking occurs"""
        try:
            from bson import ObjectId
            from datetime import datetime
            
            # Only create conversation sessions for completed sessions (>=2 minutes)
            if not session_completed or minutes < 2.0:
                logger.info(f"[BILLING_BRIDGE] Skipping conversation session - not completed or too short: {minutes} min")
                return
            
            # Convert user_id to ObjectId (use same logic as main tracking)
            user_object_id = None
            users_collection = database["users"]
            
            # Try ObjectId first
            try:
                user_object_id = ObjectId(user_id)
                user_doc = await users_collection.find_one({"_id": user_object_id})
                if not user_doc:
                    user_object_id = None
            except:
                user_object_id = None
            
            # Fallback to string ID
            if not user_object_id:
                user_doc = await users_collection.find_one({"_id": user_id})
                if user_doc:
                    user_object_id = user_id
            
            if not user_object_id:
                logger.error(f"[BILLING_BRIDGE] ❌ User not found for conversation session: {user_id}")
                return
            
            # Check if conversation session already exists for this session_id
            conversation_sessions_collection = database["conversation_sessions"]
            existing_session = await conversation_sessions_collection.find_one({
                "user_id": user_object_id,
                "session_id": session_id
            })
            
            if existing_session:
                logger.info(f"[BILLING_BRIDGE] Conversation session already exists for {session_id}")
                return
            
            # Create conversation session document
            integer_minutes = min(5, max(1, int(round(minutes))))  # Enforce 1-5 minute range
            
            session_doc = {
                "user_id": user_object_id,
                "session_id": session_id,  # Link to billing session
                "language": "english",  # Default - could be enhanced later
                "level": "B1",  # Default - could be enhanced later  
                "topic": f"Practice Session ({integer_minutes} min)",
                "messages": [
                    {
                        "role": "user",
                        "content": "Practice session tracked by billing system",
                        "timestamp": datetime.utcnow()
                    }
                ],
                "duration_minutes": integer_minutes,
                "message_count": 1,
                "summary": f"Practice session - {integer_minutes} minutes",
                "enhanced_analysis": None,
                "is_streak_eligible": integer_minutes >= 5,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "source": "billing_tracker"  # Mark as created by billing system
            }
            
            # Insert the conversation session
            result = await conversation_sessions_collection.insert_one(session_doc)
            logger.info(f"[BILLING_BRIDGE] ✅ Created conversation session {result.inserted_id} for billing session {session_id}")
            
        except Exception as e:
            logger.error(f"[BILLING_BRIDGE] ❌ Error creating conversation session: {str(e)}")
            # Don't raise - this is supplementary functionality

# Export the fixed service
BulletproofTracker = BulletproofSubscriptionServiceNoTransactions
