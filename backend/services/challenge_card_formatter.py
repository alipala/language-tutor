"""
Challenge Card Formatter - Smart Challenge Card Display
========================================================
Automatically detects when to show challenge cards in TaalCoach
and formats beautiful 3x2 grid of available challenges.

Displays the 6 challenge types when users ask about challenges.
"""
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ChallengeCardFormatter:
    """
    Formats TaalCoach responses with inline challenge cards.

    Shows beautiful 3×2 grid of available challenge types when users
    ask about challenges or want to know what they can practice.
    """

    def __init__(self):
        # Patterns that indicate challenge cards should be shown
        self.challenge_triggers = [
            r'\b(what|which|show|tell)\b.*\b(challenge|game|exercise|activity)\b',
            r'\b(challenge|game|exercise)\b.*\b(types?|available|have|offer)\b',
            r'\b(help|assist)\b.*\b(challenge|game)\b',
            r'\bwhat can i (practice|play|do)\b',
            r'\b(list|show) (all |the )?challenges?\b',
        ]

    def should_show_challenge_cards(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Determine if challenge cards should be displayed.

        Returns True if user is asking about available challenges.
        """
        if conversation_history is None:
            conversation_history = []

        # Check if already shown in this conversation
        if any(msg.get('type') == 'challenge_cards' for msg in conversation_history):
            logger.info(f"[CHALLENGE_CARDS] Already shown in conversation, skipping")
            return False

        user_lower = user_message.lower()

        # Check for challenge triggers
        for pattern in self.challenge_triggers:
            if re.search(pattern, user_lower, re.IGNORECASE):
                logger.info(f"[CHALLENGE_CARDS] Challenge trigger matched: {pattern}")
                return True

        return False

    def format_challenge_cards(self, user_language: str = "english") -> Dict[str, Any]:
        """
        Format the challenge cards data.

        Returns:
            {
                "type": "challenge_cards",
                "content": "",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "challenges": [
                        {
                            "id": "micro_quiz",
                            "icon": "help-circle",
                            "title": "Micro Quiz",
                            "description": "Quick knowledge checks",
                            "color": "#3B82F6",
                            "challenge_type": "micro_quiz"
                        },
                        ...
                    ]
                }
            }
        """
        from datetime import datetime
        # Define the 6 challenge types with their styling
        challenges = [
            {
                "id": "micro_quiz",
                "icon": "help-circle",
                "title": "Micro Quiz",
                "description": "Quick knowledge checks",
                "color": "#3B82F6",  # Blue
                "challenge_type": "micro_quiz"
            },
            {
                "id": "error_spotting",
                "icon": "search",
                "title": "Error Spotting",
                "description": "Find the mistakes",
                "color": "#EF4444",  # Red
                "challenge_type": "error_spotting"
            },
            {
                "id": "brain_tickler",
                "icon": "bulb",
                "title": "Brain Tickler",
                "description": "Think outside the box",
                "color": "#F59E0B",  # Orange
                "challenge_type": "brain_tickler"
            },
            {
                "id": "swipe_fix",
                "icon": "shuffle",
                "title": "Swipe & Fix",
                "description": "Rearrange the words",
                "color": "#10B981",  # Green
                "challenge_type": "swipe_fix"
            },
            {
                "id": "smart_flashcard",
                "icon": "card",
                "title": "Smart Flashcard",
                "description": "Learn with flashcards",
                "color": "#8B5CF6",  # Purple
                "challenge_type": "smart_flashcard"
            },
            {
                "id": "story_builder",
                "icon": "book",
                "title": "Story Builder",
                "description": "Build a story",
                "color": "#EC4899",  # Pink
                "challenge_type": "story_builder"
            },
        ]

        return {
            "type": "challenge_cards",
            "content": "",  # Empty content since this is a visual card
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "challenges": challenges
            }
        }


# Singleton instance
challenge_card_formatter = ChallengeCardFormatter()
