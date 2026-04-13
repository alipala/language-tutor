"""
Inline Stats Formatter - Duolingo-style Visual Statistics
==========================================================
Automatically detects and formats statistics in TaalCoach responses
as beautiful inline stat chips for the mobile app.

This is an ENHANCEMENT LAYER - does not replace or modify existing logic.
"""
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InlineStatsFormatter:
    """
    Formats TaalCoach responses with inline stat chips.

    Extracts statistics from user context and intelligently inserts
    visual stat chips into responses when appropriate.
    """

    def __init__(self):
        # Patterns that indicate stats should be shown
        self.stat_triggers = [
            # User queries
            r'\b(how many|how much|show me|what is|what\'s)\b',
            r'\b(progress|statistics|stats|streak|level|score)\b',
            r'\b(completed|done|finished|practiced)\b',

            # AI response patterns
            r'\b(you\'re|you are|your)\s+(A[12]|B[12]|C[12])',  # CEFR level
            r'\b\d+[\-\s]day\s+streak\b',  # Streak mention
            r'\b\d+\s+(challenge|session|minute)s?\b',  # Counts
        ]

    def should_show_stats(self, user_message: str, ai_response: str) -> bool:
        """
        Determine if inline stats should be displayed.

        Args:
            user_message: User's input
            ai_response: AI's response text

        Returns:
            True if stats should be shown
        """
        user_lower = user_message.lower()

        # ALWAYS show stats for greeting messages
        if 'greeting' in user_lower or 'welcome' in user_lower or 'start_' in user_lower:
            logger.info(f"[INLINE_STATS] Greeting message detected - showing stats")
            return True

        # Check other triggers
        combined_text = f"{user_message} {ai_response}".lower()

        for pattern in self.stat_triggers:
            if re.search(pattern, combined_text, re.IGNORECASE):
                logger.info(f"[INLINE_STATS] Trigger matched: {pattern}")
                return True

        return False

    def extract_stats(self, context: Dict[str, Any], user_message: str = "") -> List[Dict[str, Any]]:
        """
        Extract key statistics from TaalCoach context.

        Args:
            context: User context from cache_helpers.get_taalcoach_context_cached
            user_message: User's query to filter relevant stats

        Returns:
            List of stat objects for inline display (filtered by relevance)
        """
        all_stats = []

        try:
            # Build complete stat pool
            # CEFR Level
            if context.get('cefr_level'):
                all_stats.append({
                    "value": context['cefr_level'],
                    "label": "Level",
                    "icon": "school",
                    "type": "level",
                    "keywords": ["level", "cefr", "proficiency", "a1", "a2", "b1", "b2"]
                })

            # Progress Percentage
            if context.get('assessment_score', 0) > 0:
                all_stats.append({
                    "value": int(context['assessment_score']),
                    "label": "Progress",
                    "icon": "analytics",
                    "type": "percentage",
                    "keywords": ["progress", "score", "percentage", "%", "assessment"]
                })

            # Current Streak
            current_streak = context.get('current_streak', 0)
            if current_streak > 0:
                all_stats.append({
                    "value": current_streak,
                    "label": "Streak",
                    "icon": "flame",
                    "type": "streak",
                    "keywords": ["streak", "day", "days", "daily", "consecutive"]
                })

            # Total Sessions
            total_sessions = context.get('total_sessions', 0)
            if total_sessions > 0:
                all_stats.append({
                    "value": total_sessions,
                    "label": "Sessions",
                    "icon": "chatbubbles",
                    "type": "count",
                    "keywords": ["session", "sessions", "conversation"]
                })

            # Total Challenges
            total_challenges = context.get('total_challenges_lifetime', 0)
            if total_challenges > 0:
                all_stats.append({
                    "value": total_challenges,
                    "label": "Challenges",
                    "icon": "trophy",
                    "type": "count",
                    "keywords": ["challenge", "challenges", "completed", "done", "finished"]
                })

            # Practice Minutes
            total_minutes = context.get('total_minutes', 0)
            if total_minutes > 0:
                all_stats.append({
                    "value": total_minutes,
                    "label": "Minutes",
                    "icon": "time",
                    "type": "time",
                    "keywords": ["minute", "minutes", "time", "practice time", "duration"]
                })

            # Filter stats based on user query
            filtered_stats = self._filter_stats_by_relevance(all_stats, user_message)

            logger.info(f"[INLINE_STATS] Extracted {len(all_stats)} total stats, filtered to {len(filtered_stats)} relevant")

        except Exception as e:
            logger.error(f"[INLINE_STATS] Failed to extract stats: {str(e)}")
            filtered_stats = []

        return filtered_stats

    def _filter_stats_by_relevance(self, stats: List[Dict[str, Any]], user_message: str) -> List[Dict[str, Any]]:
        """
        Filter stats to show only what's relevant to user's query.

        Args:
            stats: All available stats
            user_message: User's query

        Returns:
            Filtered list of relevant stats
        """
        if not user_message:
            # No query, return all stats (up to 4)
            return [self._remove_keywords(s) for s in stats[:4]]

        user_lower = user_message.lower()

        # GREETING MESSAGES - always show stats!
        if 'greeting' in user_lower or 'welcome' in user_lower or 'start_' in user_lower:
            logger.info(f"[INLINE_STATS] Greeting message detected, showing all stats")
            return [self._remove_keywords(s) for s in stats[:4]]

        # Check for general progress/stats queries FIRST
        general_keywords = ['progress', 'stats', 'statistics', 'how am i', 'show me my', 'overview']
        if any(keyword in user_lower for keyword in general_keywords):
            # Show all stats (up to 4)
            logger.info(f"[INLINE_STATS] General progress query, showing all stats")
            return [self._remove_keywords(s) for s in stats[:4]]

        # Check for practice-related queries that might be about recommendations
        # EXPANDED: Include "what challenges" which is also a recommendation query
        if re.search(r'\b(what should|what to|should i|recommend|suggestion|what challenge|which challenge)\b', user_lower):
            # This is a recommendation query, not stats query
            logger.info(f"[INLINE_STATS] Recommendation query detected, skipping stats")
            return []

        # Match stats whose keywords appear in user message
        matched_stats = []
        for stat in stats:
            keywords = stat.get('keywords', [])
            if any(keyword in user_lower for keyword in keywords):
                matched_stats.append(stat)

        # If specific stats matched, use only those
        if matched_stats:
            logger.info(f"[INLINE_STATS] Matched {len(matched_stats)} stats based on query keywords")
            return [self._remove_keywords(s) for s in matched_stats[:4]]

        # Default: no stats (query not about statistics)
        logger.info(f"[INLINE_STATS] No stat keywords matched, skipping stats")
        return []

    def _remove_keywords(self, stat: Dict[str, Any]) -> Dict[str, Any]:
        """Remove keywords field from stat (internal use only)"""
        stat_copy = stat.copy()
        stat_copy.pop('keywords', None)
        return stat_copy

    def format_response_with_stats(
        self,
        ai_response: str,
        context: Dict[str, Any],
        user_message: str
    ) -> List[Dict[str, Any]]:
        """
        Format AI response to include inline stats when appropriate.

        Strategy:
        1. Check if stats should be shown
        2. Extract stats from context
        3. Split response into text + stats + continuation
        4. Return as list of messages

        Args:
            ai_response: AI's text response
            context: User context
            user_message: User's original message

        Returns:
            List of rich messages (text + inline_stats)
        """
        # Check if we should show stats
        if not self.should_show_stats(user_message, ai_response):
            logger.info(f"[INLINE_STATS] No stat triggers found, returning plain text")
            return [{
                "type": "text",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }]

        # Extract stats from context (filtered by user query)
        stats = self.extract_stats(context, user_message)

        if not stats:
            logger.info(f"[INLINE_STATS] No stats available in context")
            return [{
                "type": "text",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }]

        # Format response with inline stats
        messages = self._split_response_with_stats(ai_response, stats)

        logger.info(f"[INLINE_STATS] Formatted response: {len(messages)} messages ({len([m for m in messages if m['type'] == 'inline_stats'])} with stats)")

        return messages

    def _split_response_with_stats(
        self,
        response: str,
        stats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Split response into introduction + stats + continuation.

        Strategy (DUOLINGO-STYLE):
        - For GREETING messages: Show stats FIRST, then minimal text
        - For other messages: Find complete sentence before stats
        - NEVER cut mid-sentence (avoid "You started at A1 (")

        Args:
            response: AI response text
            stats: List of stat objects

        Returns:
            List of message objects
        """
        messages = []

        # Find first sentence boundary
        first_sentence_end = re.search(r'[.!?]+[\s—]+', response)

        if first_sentence_end:
            # We have at least one complete sentence
            intro = response[:first_sentence_end.end()].strip()
            rest = response[first_sentence_end.end():].strip()

            # Add intro text
            messages.append({
                "type": "text",
                "content": intro,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Add stats
            messages.append({
                "type": "inline_stats",
                "data": {"stats": stats[:4]},
                "timestamp": datetime.utcnow().isoformat()
            })

            # Add continuation if it exists
            if rest:
                messages.append({
                    "type": "text",
                    "content": rest,
                    "timestamp": datetime.utcnow().isoformat()
                })
        else:
            # No sentence boundary found - show stats AFTER complete response
            # This prevents cutting mid-sentence
            messages.append({
                "type": "text",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            messages.append({
                "type": "inline_stats",
                "data": {"stats": stats[:4]},
                "timestamp": datetime.utcnow().isoformat()
            })

        # Ensure we have at least one message
        if not messages:
            messages = [{
                "type": "text",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            }]

        return messages


# Singleton instance
inline_stats_formatter = InlineStatsFormatter()
