"""
Capability Cards Formatter - TaalCoach Feature Showcase
=======================================================
Displays TaalCoach's capabilities as interactive cards in greeting messages.

Shows users what they can do with TaalCoach through beautiful visual cards.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CapabilityCardsFormatter:
    """
    Formats TaalCoach greeting with capability showcase cards.

    Displays 6 core capabilities as visual cards to guide users.
    """

    def __init__(self):
        # TaalCoach's core capabilities
        self.capabilities = [
            {
                "id": "progress",
                "icon": "analytics",
                "title": "Track Progress",
                "description": "View stats & achievements",
                "color": "#9333EA",  # Purple
                "query": "Show me my progress"
            },
            {
                "id": "practice",
                "icon": "chatbubbles",
                "title": "Get Recommendations",
                "description": "Personalized practice tips",
                "color": "#3B82F6",  # Blue
                "query": "What should I practice?"
            },
            {
                "id": "challenges",
                "icon": "trophy",
                "title": "Challenge Tips",
                "description": "Improve your skills",
                "color": "#EC4899",  # Pink
                "query": "Help me with challenges"
            },
            {
                "id": "voice",
                "icon": "mic",
                "title": "Voice Tutor",
                "description": "Choose AI voice style",
                "color": "#14B8A6",  # Turquoise
                "query": "Tell me about AI voices"
            },
            {
                "id": "learning",
                "icon": "school",
                "title": "Learning Plan",
                "description": "Structured path to fluency",
                "color": "#F59E0B",  # Amber
                "query": "How do learning plans work?"
            },
            {
                "id": "help",
                "icon": "help-circle",
                "title": "Ask Anything",
                "description": "I'm here to help!",
                "color": "#10B981",  # Green
                "query": "What can you help me with?"
            }
        ]

    def should_show_capability_cards(self, user_message: str) -> bool:
        """
        Determine if capability cards should be shown.

        Show on greeting messages for new or returning users.
        """
        # Greeting patterns
        greeting_patterns = [
            'start_greeting',
            'greeting',
            'welcome'
        ]

        user_lower = user_message.lower()
        return any(pattern in user_lower for pattern in greeting_patterns)

    def format_greeting_with_capabilities(
        self,
        ai_response: str,
        user_message: str,
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format greeting message with capability cards.

        Returns:
            List of messages: [text, inline_stats, capability_cards]
        """
        if not self.should_show_capability_cards(user_message):
            return [{
                "type": "text",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }]

        logger.info(f"[CAPABILITY_CARDS] Showing capability showcase for greeting")

        # Build messages
        messages = []

        # 1. Greeting text (keep it short)
        messages.append({
            "type": "text",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # 2. Capability cards
        messages.append({
            "type": "capability_cards",
            "data": {
                "cards": self.capabilities
            },
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"[CAPABILITY_CARDS] Added {len(self.capabilities)} capability cards to greeting")

        return messages


# Singleton instance
capability_cards_formatter = CapabilityCardsFormatter()
