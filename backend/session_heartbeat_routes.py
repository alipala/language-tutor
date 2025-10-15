from fastapi import APIRouter, Request, HTTPException
import logging
from datetime import datetime
from models import SpeakingTimeTrackingRequest
from subscription_service_bulletproof_fix_no_transactions import BulletproofTracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["session"])

@router.post("/api/session-heartbeat")
async def session_heartbeat(request: Request):
    """
    Handle session heartbeat from frontend
    This endpoint receives periodic heartbeat signals from active sessions
    🔥 FIXED: Now properly saves sessions and deducts minutes when threshold is reached
    """
    try:
        # Get the request body
        body = await request.body()
        
        if not body:
            logger.warning("[HEARTBEAT] Empty heartbeat received")
            return {
                "success": True,
                "message": "Empty heartbeat received",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        import json
        heartbeat_data = json.loads(body.decode('utf-8'))
        
        session_id = heartbeat_data.get('session_id', 'unknown')
        duration_minutes = heartbeat_data.get('duration_minutes', 0)
        user_id = heartbeat_data.get('user_id')
        status = heartbeat_data.get('status', 'active')
        
        logger.info(f"[HEARTBEAT] Received heartbeat: {session_id} - {duration_minutes:.1f}min (status: {status})")
        
        # 🔥 CRITICAL FIX: Save session and deduct minutes when threshold is reached
        if user_id and duration_minutes >= 5.0:
            logger.info(f"[HEARTBEAT] 🎯 Session reached 5-minute threshold - processing deduction")
            
            try:
                # Create tracking request
                tracking_request = SpeakingTimeTrackingRequest(
                    user_id=user_id,
                    session_id=session_id,
                    speaking_minutes=duration_minutes,
                    session_completed=True  # 5+ minutes = completed session
                )
                
                # Call BulletproofTracker to deduct minutes atomically
                tracking_success = await BulletproofTracker.track_speaking_time_atomic(tracking_request)
                
                if tracking_success:
                    logger.info(f"[HEARTBEAT] ✅ Successfully tracked and deducted {duration_minutes:.1f} minutes for user {user_id}")
                    return {
                        "success": True,
                        "message": "Heartbeat received and session saved",
                        "minutes_deducted": duration_minutes,
                        "session_saved": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.warning(f"[HEARTBEAT] ⚠️ Failed to track speaking time for user {user_id}")
                    return {
                        "success": True,
                        "message": "Heartbeat received but tracking failed",
                        "minutes_deducted": 0,
                        "session_saved": False,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
            except Exception as tracking_error:
                logger.error(f"[HEARTBEAT] ❌ Error during tracking: {str(tracking_error)}")
                # Return success for heartbeat but indicate tracking failure
                return {
                    "success": True,
                    "message": "Heartbeat received but tracking error occurred",
                    "error": str(tracking_error),
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            # Session not yet at threshold - just acknowledge heartbeat
            if duration_minutes < 5.0:
                logger.info(f"[HEARTBEAT] Session in progress: {duration_minutes:.1f}/5.0 minutes")
            else:
                logger.warning(f"[HEARTBEAT] No user_id provided - cannot track session")
            
            return {
                "success": True,
                "message": "Heartbeat received",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"[HEARTBEAT] Error processing heartbeat: {str(e)}")
        import traceback
        logger.error(f"[HEARTBEAT] Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
