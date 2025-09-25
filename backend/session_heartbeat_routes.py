from fastapi import APIRouter, Request, HTTPException
import logging
from datetime import datetime

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
    """
    try:
        # Get the request body
        body = await request.body()
        
        if body:
            import json
            heartbeat_data = json.loads(body.decode('utf-8'))
            
            logger.info(f"[HEARTBEAT] Received heartbeat: {heartbeat_data.get('session_id', 'unknown')} - {heartbeat_data.get('duration_minutes', 0):.1f}min")
            
            # For now, just log the heartbeat - we could store this in database for monitoring
            return {
                "success": True,
                "message": "Heartbeat received",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.warning("[HEARTBEAT] Empty heartbeat received")
            return {
                "success": True,
                "message": "Empty heartbeat received",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"[HEARTBEAT] Error processing heartbeat: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
