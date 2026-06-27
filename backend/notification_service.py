"""
Notification Service
Handles sending push notifications via Expo Push Notifications
and WebSocket real-time updates
"""

from typing import List, Dict, Any, Optional

# ─── Localised push notification strings ────────────────────────────────────
# Keyed by ISO 639-1 language code. All 7 supported UI languages are covered.
# Falls back to 'en' for any unknown / None locale.

NOTIFICATION_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "first_session_title":   "Great First Session! 🎉",
        "first_session_body":    "You earned {xp} XP! Come back tomorrow to build your streak.",
        "analysis_title":        "Your {language} practice analysis is ready!",
        "analysis_body":         "I've analyzed {count} sentences from your practice session. Tap to see detailed feedback and tips!",
    },
    "tr": {
        "first_session_title":   "Harika İlk Oturum! 🎉",
        "first_session_body":    "{xp} XP kazandın! Serini sürdürmek için yarın geri gel.",
        "analysis_title":        "{language} pratik analizin hazır!",
        "analysis_body":         "Pratik oturumundan {count} cümle analiz ettim. Detaylı geri bildirim ve ipuçları için dokun!",
    },
    "es": {
        "first_session_title":   "¡Gran primera sesión! 🎉",
        "first_session_body":    "¡Ganaste {xp} XP! Vuelve mañana para mantener tu racha.",
        "analysis_title":        "¡Tu análisis de práctica de {language} está listo!",
        "analysis_body":         "Analicé {count} oraciones de tu sesión de práctica. ¡Toca para ver comentarios detallados y consejos!",
    },
    "fr": {
        "first_session_title":   "Excellente première session ! 🎉",
        "first_session_body":    "Tu as gagné {xp} XP ! Reviens demain pour maintenir ta série.",
        "analysis_title":        "Ton analyse de pratique en {language} est prête !",
        "analysis_body":         "J'ai analysé {count} phrases de ta session de pratique. Appuie pour voir les retours détaillés et les conseils !",
    },
    "de": {
        "first_session_title":   "Tolle erste Sitzung! 🎉",
        "first_session_body":    "Du hast {xp} XP verdient! Komm morgen wieder, um deine Serie zu verlängern.",
        "analysis_title":        "Deine {language}-Übungsanalyse ist fertig!",
        "analysis_body":         "Ich habe {count} Sätze aus deiner Übungssitzung analysiert. Tippe für detailliertes Feedback und Tipps!",
    },
    "nl": {
        "first_session_title":   "Geweldige eerste sessie! 🎉",
        "first_session_body":    "Je hebt {xp} XP verdiend! Kom morgen terug om je reeks voort te zetten.",
        "analysis_title":        "Je {language}-oefenanalyse is klaar!",
        "analysis_body":         "Ik heb {count} zinnen uit je oefensessie geanalyseerd. Tik voor gedetailleerde feedback en tips!",
    },
    "pt": {
        "first_session_title":   "Ótima primeira sessão! 🎉",
        "first_session_body":    "Você ganhou {xp} XP! Volte amanhã para manter sua sequência.",
        "analysis_title":        "Sua análise de prática de {language} está pronta!",
        "analysis_body":         "Analisei {count} frases da sua sessão de prática. Toque para ver feedback detalhado e dicas!",
    },
}

# Language names localised per UI language (used in analysis_title)
_LANGUAGE_NAMES: Dict[str, Dict[str, str]] = {
    "en": {"english": "English", "spanish": "Spanish", "french": "French", "german": "German", "dutch": "Dutch", "portuguese": "Portuguese", "turkish": "Turkish"},
    "tr": {"english": "İngilizce", "spanish": "İspanyolca", "french": "Fransızca", "german": "Almanca", "dutch": "Felemenkçe", "portuguese": "Portekizce", "turkish": "Türkçe"},
    "es": {"english": "inglés", "spanish": "español", "french": "francés", "german": "alemán", "dutch": "neerlandés", "portuguese": "portugués", "turkish": "turco"},
    "fr": {"english": "anglais", "spanish": "espagnol", "french": "français", "german": "allemand", "dutch": "néerlandais", "portuguese": "portugais", "turkish": "turc"},
    "de": {"english": "Englisch", "spanish": "Spanisch", "french": "Französisch", "german": "Deutsch", "dutch": "Niederländisch", "portuguese": "Portugiesisch", "turkish": "Türkisch"},
    "nl": {"english": "Engels", "spanish": "Spaans", "french": "Frans", "german": "Duits", "dutch": "Nederlands", "portuguese": "Portugees", "turkish": "Turks"},
    "pt": {"english": "inglês", "spanish": "espanhol", "french": "francês", "german": "alemão", "dutch": "holandês", "portuguese": "português", "turkish": "turco"},
}

def get_notification_strings(locale: Optional[str]) -> Dict[str, str]:
    """Return notification strings for the given locale (falls back to 'en')."""
    lang = (locale or "en").lower()[:2]
    return NOTIFICATION_STRINGS.get(lang, NOTIFICATION_STRINGS["en"])

def localise_language_name(practice_language: str, ui_locale: Optional[str]) -> str:
    """Translate a practice language name (e.g. 'english') into the UI locale."""
    lang = (ui_locale or "en").lower()[:2]
    names = _LANGUAGE_NAMES.get(lang, _LANGUAGE_NAMES["en"])
    return names.get(practice_language.lower(), practice_language.title())
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
        # Log notification attempt
        logger.info(f"[PUSH_NOTIFICATION] 📤 Attempting to send push notification")
        logger.info(f"[PUSH_NOTIFICATION] Title: {title}")
        logger.info(f"[PUSH_NOTIFICATION] Tokens: {len(push_tokens)}")

        if not push_tokens:
            logger.warning("[PUSH_NOTIFICATION] ❌ No push tokens provided")
            return {'success': False, 'message': 'No push tokens'}

        # Filter out invalid tokens
        valid_tokens = [token for token in push_tokens if self._is_valid_expo_token(token)]

        logger.info(f"[PUSH_NOTIFICATION] Valid tokens: {len(valid_tokens)}/{len(push_tokens)}")
        for i, token in enumerate(valid_tokens):
            logger.info(f"[PUSH_NOTIFICATION] Token {i+1}: {token[:30]}...")

        if not valid_tokens:
            logger.warning("[PUSH_NOTIFICATION] ❌ No valid Expo push tokens")
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
                channel_id='default',  # Android 8+: routes to MAX importance channel
            )
            messages.append(message)

        logger.info(f"[PUSH_NOTIFICATION] Built {len(messages)} messages")

        # Send notifications in chunks (Expo recommends chunks of 100)
        success_count = 0
        failure_count = 0
        errors = []

        try:
            # Send messages
            chunks = self._chunk_messages(messages, 100)

            for chunk_idx, chunk in enumerate(chunks):
                try:
                    logger.info(f"[PUSH_NOTIFICATION] 📡 Sending chunk {chunk_idx+1}/{len(chunks)} ({len(chunk)} messages)")

                    # Send chunk of notifications
                    tickets = self.expo_push_client.publish_multiple(chunk)

                    logger.info(f"[PUSH_NOTIFICATION] 📥 Received {len(tickets)} tickets from Expo")

                    # Check for errors in tickets
                    for ticket_idx, ticket in enumerate(tickets):
                        if ticket.status == 'ok':
                            success_count += 1
                            logger.info(f"[PUSH_NOTIFICATION] ✅ Ticket {ticket_idx+1}: OK (ID: {getattr(ticket, 'id', 'N/A')})")
                        else:
                            failure_count += 1
                            error_msg = getattr(ticket, 'message', 'Unknown error')
                            errors.append(error_msg)
                            logger.error(f"[PUSH_NOTIFICATION] ❌ Ticket {ticket_idx+1}: {error_msg}")
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

        # Log final results
        logger.info(f"[PUSH_NOTIFICATION] 📊 Final Results:")
        logger.info(f"[PUSH_NOTIFICATION] ✅ Success: {success_count}")
        logger.info(f"[PUSH_NOTIFICATION] ❌ Failed: {failure_count}")
        if errors:
            logger.error(f"[PUSH_NOTIFICATION] Errors: {errors[:5]}")

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


async def send_push_notification(
    push_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    user_id: str = None,
    priority: str = 'high',
    sound: str = 'default',
    badge: Optional[int] = None
) -> bool:
    """
    Send a push notification to a single user.

    Simple wrapper around notification_service.send_expo_push_notification
    for backwards compatibility with cron jobs and other scripts.

    Args:
        push_token: Expo push token
        title: Notification title
        body: Notification body/content
        data: Additional data to send with notification
        user_id: User ID (for logging purposes)
        priority: 'default' or 'high'
        sound: Sound to play ('default' or null for silent)
        badge: Badge count to display (iOS)

    Returns:
        bool: True if notification was sent successfully
    """
    try:
        result = notification_service.send_expo_push_notification(
            push_tokens=[push_token],
            title=title,
            body=body,
            data=data,
            priority=priority,
            sound=sound,
            badge=badge
        )

        return result.get('success', False)

    except Exception as e:
        logger.error(f"Error sending push notification to user {user_id}: {str(e)}")
        return False


async def send_notification_to_users(
    user_ids: List[str],
    title: str,
    content: str,
    notification_type: str,
    users_collection,
    notification_id: str = None,  # CRITICAL: Include notification_id for banner tap!
    priority: str = 'high'
) -> Dict[str, Any]:
    """
    Send push notifications to specific users (respects user preferences)

    Args:
        user_ids: List of user IDs to send to
        title: Notification title
        content: Notification content/body
        notification_type: Type of notification (Maintenance, Special Offer, Information)
        users_collection: MongoDB users collection
        priority: Notification priority

    Returns:
        Dict with send results
    """
    try:
        from database import notification_preferences_collection

        # Get push tokens for these users
        push_tokens = []
        skipped_count = 0

        async for user in users_collection.find(
            {"_id": {"$in": user_ids}, "push_token": {"$exists": True, "$ne": None}}
        ):
            push_token = user.get('push_token')
            if not push_token:
                continue

            # ✅ CHECK NOTIFICATION PREFERENCES - Respect user's settings!
            # Maintenance notifications always send (critical)
            # Special Offer & Information respect product_updates_enabled
            if notification_type in ["Special Offer", "Information"]:
                prefs = await notification_preferences_collection.find_one({"user_id": str(user["_id"])})

                # Default to True if no preferences set (existing behavior)
                product_updates_enabled = True
                if prefs:
                    product_updates_enabled = prefs.get("product_updates_enabled", True)

                if not product_updates_enabled:
                    skipped_count += 1
                    logger.info(f"Skipping notification for user {user.get('name', 'Unknown')} - product updates disabled")
                    continue

            # User wants to receive this notification
            push_tokens.append(push_token)

        logger.info(f"Filtered users: {len(push_tokens)} will receive, {skipped_count} skipped (preferences)")

        if not push_tokens:
            logger.info(f"No push tokens found for {len(user_ids)} users (or all opted out)")
            return {'success': False, 'message': 'No push tokens found or all users opted out'}

        # Prepare notification data
        data = {
            'type': 'notification',
            'notification_type': notification_type,
            'notification_id': notification_id,  # CRITICAL: iOS needs this to identify notification!
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
    notification_id: str = None,  # CRITICAL: Include notification_id for banner tap!
    priority: str = 'high'
) -> Dict[str, Any]:
    """
    Send push notifications to all active users (respects user preferences)

    Args:
        title: Notification title
        content: Notification content/body
        notification_type: Type of notification (Maintenance, Special Offer, Information)
        users_collection: MongoDB users collection
        priority: Notification priority

    Returns:
        Dict with send results
    """
    try:
        from database import notification_preferences_collection

        # Get all push tokens for active users
        push_tokens = []
        skipped_count = 0

        async for user in users_collection.find(
            {"is_active": True, "push_token": {"$exists": True, "$ne": None}}
        ):
            push_token = user.get('push_token')
            if not push_token:
                continue

            # ✅ CHECK NOTIFICATION PREFERENCES - Respect user's settings!
            # Maintenance notifications always send (critical)
            # Special Offer & Information respect product_updates_enabled
            if notification_type in ["Special Offer", "Information"]:
                prefs = await notification_preferences_collection.find_one({"user_id": str(user["_id"])})

                # Default to True if no preferences set (existing behavior)
                product_updates_enabled = True
                if prefs:
                    product_updates_enabled = prefs.get("product_updates_enabled", True)

                if not product_updates_enabled:
                    skipped_count += 1
                    logger.info(f"Skipping notification for user {user.get('name', 'Unknown')} - product updates disabled")
                    continue

            # User wants to receive this notification
            push_tokens.append(push_token)

        logger.info(f"Filtered users: {len(push_tokens)} will receive, {skipped_count} skipped (preferences)")

        if not push_tokens:
            logger.info("No push tokens found for active users (or all opted out)")
            return {'success': False, 'message': 'No push tokens found or all users opted out'}

        # Prepare notification data
        data = {
            'type': 'notification',
            'notification_type': notification_type,
            'notification_id': notification_id,  # CRITICAL: iOS needs this to identify notification!
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
