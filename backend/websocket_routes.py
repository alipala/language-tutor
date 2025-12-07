"""
WebSocket Routes
Real-time notification WebSocket endpoints
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer
from typing import Optional
import logging
from websocket_manager import manager
from auth import get_current_user, get_current_admin
from admin_routes import get_current_admin as verify_admin
import jwt
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time notifications

    Clients should connect with:
    ws://host/api/ws/notifications?token=<jwt_token>

    Messages received:
    {
        "type": "new_notification",
        "data": { notification object }
    }
    """
    client_id = None

    try:
        # Authenticate the WebSocket connection
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Verify token and get user/admin info
        try:
            from jose import JWTError, jwt as jose_jwt
            from dotenv import load_dotenv
            import os

            load_dotenv()
            SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
            ALGORITHM = "HS256"

            # Decode token
            payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            user_type = payload.get("type", "user")  # "user" or "admin"

            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return

            client_id = f"{user_type}_{user_id}"
            logger.info(f"🔐 WebSocket authenticated: {client_id}")

        except JWTError as e:
            logger.error(f"JWT Error: {e}")
            await websocket.close(code=1008, reason="Invalid authentication token")
            return

        # Accept connection
        await manager.connect(websocket, client_id)

        # Send initial connection success message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected successfully",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and listen for messages
        try:
            while True:
                # Wait for messages from client (ping/pong, etc.)
                data = await websocket.receive_text()
                logger.debug(f"Received from {client_id}: {data}")

                # Echo back (for debugging)
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })

        except WebSocketDisconnect:
            logger.info(f"🔌 Client disconnected: {client_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        # Cleanup connection
        if client_id:
            manager.disconnect(websocket, client_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status (for debugging)"""
    return {
        "active_connections": manager.get_connection_count(),
        "clients": list(manager.active_connections.keys())
    }
