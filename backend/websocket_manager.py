"""
WebSocket Manager
Handles WebSocket connections for real-time notifications
"""

from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Store active connections by user/admin ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()

        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()

        self.active_connections[client_id].add(websocket)
        logger.info(f"🔌 WebSocket connected: {client_id} (total: {len(self.active_connections[client_id])} connections)")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)

            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

            logger.info(f"🔌 WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            disconnected = set()

            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {client_id}: {e}")
                    disconnected.add(connection)

            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[client_id].discard(connection)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = []

        for client_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append((client_id, connection))

        # Remove disconnected connections
        for client_id, connection in disconnected:
            if client_id in self.active_connections:
                self.active_connections[client_id].discard(connection)

    async def send_notification_update(self, notification_data: dict, target_user_ids: list = None):
        """
        Send notification update to specific users or all connected admins

        Args:
            notification_data: The notification data to send
            target_user_ids: List of user IDs to send to (None = broadcast to all admins)
        """
        message = {
            "type": "new_notification",
            "data": notification_data
        }

        if target_user_ids:
            # Send to specific users
            for user_id in target_user_ids:
                await self.send_personal_message(message, str(user_id))
        else:
            # Broadcast to all connected clients (admins)
            await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()
