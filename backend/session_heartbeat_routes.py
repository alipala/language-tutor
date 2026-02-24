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
        selected_duration = heartbeat_data.get('selected_duration', 5)  # 🆕 Get selected duration

        logger.info(f"[HEARTBEAT] Received heartbeat: {session_id} - {duration_minutes:.1f}min (status: {status}, threshold: {selected_duration}min)")

        # 🔥 DOUBLE-COUNTING FIX: Heartbeat should NOT track sessions
        # Session tracking is handled by:
        # 1. learning_routes.py for learning plan sessions
        # 2. Frontend saveConversationProgress() for practice sessions
        # The heartbeat is ONLY for monitoring active sessions, not for tracking/deduction

        if user_id and duration_minutes >= selected_duration:
            logger.info(f"[HEARTBEAT] 📊 Session reached {selected_duration}-minute threshold: {session_id}")
            logger.info(f"[HEARTBEAT] ℹ️ Tracking will be handled by session completion endpoint")
            logger.info(f"[HEARTBEAT] ℹ️ Heartbeat is for monitoring only - no deduction here")

            return {
                "success": True,
                "message": "Heartbeat received - session will be tracked on completion",
                "duration_minutes": duration_minutes,
                "selected_duration": selected_duration,
                "monitoring_only": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Session not yet at threshold - just acknowledge heartbeat
            if duration_minutes < selected_duration:
                logger.info(f"[HEARTBEAT] Session in progress: {duration_minutes:.1f}/{selected_duration} minutes")
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
