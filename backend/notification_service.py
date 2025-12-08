"""
Notification Service
Handles sending push notifications via Expo Push Notifications
and WebSocket real-time updates
"""

from typing import List, Dict, Any, Optional
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
import requests
from requests.exceptions import ConnectionError, HTTPError
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.expo_push_client = PushClient()

    def send_expo_push_notification(
        self,
        push_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = 'high',
        sound: str = 'default',
        badge: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send push notifications via Expo Push Service

        Args:
            push_tokens: List of Expo push tokens
            title: Notification title
            body: Notification body/content
            data: Additional data to send with notification
            priority: 'default' or 'high'
            sound: Sound to play ('default' or null for silent)
            badge: Badge count to display (iOS)

        Returns:
            Dict with success/failure information
        """
        if not push_tokens:
            logger.warning("No push tokens provided")
            return {'success': False, 'message': 'No push tokens'}

        # Filter out invalid tokens
        valid_tokens = [token for token in push_tokens if self._is_valid_expo_token(token)]

        if not valid_tokens:
            logger.warning("No valid Expo push tokens")
            return {'success': False, 'message': 'No valid tokens'}

        # Build messages
        messages = []
        for token in valid_tokens:
            message = PushMessage(
                to=token,
                title=title,
                body=body,
                data=data or {},
                sound=sound,
                priority=priority,
                badge=badge,
                # Note: category_id is not a valid Expo parameter
                # Use channelId for Android channels if needed
            )
            messages.append(message)

        # Send notifications in chunks (Expo recommends chunks of 100)
        success_count = 0
        failure_count = 0
        errors = []

        try:
            # Send messages
            chunks = self._chunk_messages(messages, 100)

            for chunk in chunks:
                try:
                    # Send chunk of notifications
                    tickets = self.expo_push_client.publish_multiple(chunk)

                    # Check for errors in tickets
                    for ticket in tickets:
                        if ticket.status == 'ok':
                            success_count += 1
                        else:
                            failure_count += 1
                            error_msg = getattr(ticket, 'message', 'Unknown error')
                            errors.append(error_msg)
                            logger.error(f"Push notification error: {error_msg}")

                except PushServerError as exc:
                    # Server error
                    failure_count += len(chunk)
                    errors.append(str(exc))
                    logger.error(f"Expo push server error: {exc}")

                except (ConnectionError, HTTPError) as exc:
                    # Network error
                    failure_count += len(chunk)
                    errors.append(str(exc))
                    logger.error(f"Network error sending push: {exc}")

        except Exception as exc:
            logger.error(f"Unexpected error sending push notifications: {exc}")
            return {
                'success': False,
                'message': str(exc),
                'sent': 0,
                'failed': len(valid_tokens)
            }

        # Return results
        return {
            'success': success_count > 0,
            'sent': success_count,
            'failed': failure_count,
            'errors': errors[:10] if errors else [],  # Limit error messages
            'message': f'Sent {success_count}/{len(valid_tokens)} notifications'
        }

    def _is_valid_expo_token(self, token: str) -> bool:
        """Check if a token is a valid Expo push token"""
        if not token:
            return False
        # Expo push tokens start with ExponentPushToken[
        return token.startswith('ExponentPushToken[') or token.startswith('ExpoPushToken[')

    def _chunk_messages(self, messages: List[PushMessage], chunk_size: int) -> List[List[PushMessage]]:
        """Split messages into chunks"""
        return [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]


# Global notification service instance
notification_service = NotificationService()


async def send_notification_to_users(
    user_ids: List[str],
    title: str,
    content: str,
    notification_type: str,
    users_collection,
    priority: str = 'high'
) -> Dict[str, Any]:
    """
    Send push notifications to specific users

    Args:
        user_ids: List of user IDs to send to
        title: Notification title
        content: Notification content/body
        notification_type: Type of notification (for icon/color)
        users_collection: MongoDB users collection
        priority: Notification priority

    Returns:
        Dict with send results
    """
    try:
        # Get push tokens for these users
        push_tokens = []

        async for user in users_collection.find(
            {"_id": {"$in": user_ids}, "push_token": {"$exists": True, "$ne": None}}
        ):
            if user.get('push_token'):
                push_tokens.append(user['push_token'])

        if not push_tokens:
            logger.info(f"No push tokens found for {len(user_ids)} users")
            return {'success': False, 'message': 'No push tokens found'}

        # Prepare notification data
        data = {
            'type': 'notification',
            'notification_type': notification_type,
            'screen': 'Main',  # Navigate to Main (Profile tab)
            'params': {
                'screen': 'Profile',
                'params': {'tab': 'notifications'}
            }
        }

        # Send notifications
        result = notification_service.send_expo_push_notification(
            push_tokens=push_tokens,
            title=title,
            body=content,
            data=data,
            priority=priority,
            sound='default',
            badge=1  # Increment badge count
        )

        logger.info(f"Push notification result: {result}")
        return result

    except Exception as exc:
        logger.error(f"Error sending notifications to users: {exc}")
        return {'success': False, 'message': str(exc)}


async def send_notification_to_all_users(
    title: str,
    content: str,
    notification_type: str,
    users_collection,
    priority: str = 'high'
) -> Dict[str, Any]:
    """
    Send push notifications to all active users

    Args:
        title: Notification title
        content: Notification content/body
        notification_type: Type of notification
        users_collection: MongoDB users collection
        priority: Notification priority

    Returns:
        Dict with send results
    """
    try:
        # Get all push tokens for active users
        push_tokens = []

        async for user in users_collection.find(
            {"is_active": True, "push_token": {"$exists": True, "$ne": None}}
        ):
            if user.get('push_token'):
                push_tokens.append(user['push_token'])

        if not push_tokens:
            logger.info("No push tokens found for active users")
            return {'success': False, 'message': 'No push tokens found'}

        # Prepare notification data
        data = {
            'type': 'notification',
            'notification_type': notification_type,
            'screen': 'Main',
            'params': {
                'screen': 'Profile',
                'params': {'tab': 'notifications'}
            }
        }

        # Send notifications
        result = notification_service.send_expo_push_notification(
            push_tokens=push_tokens,
            title=title,
            body=content,
            data=data,
            priority=priority,
            sound='default',
            badge=1
        )

        logger.info(f"Push notification result (all users): {result}")
        return result

    except Exception as exc:
        logger.error(f"Error sending notifications to all users: {exc}")
        return {'success': False, 'message': str(exc)}
