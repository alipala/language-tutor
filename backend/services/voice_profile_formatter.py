"""
Voice Profile Formatter - AI Voice Character Display
=====================================================
Displays AI voice characters inline in TaalCoach chat when users ask about voices.

Shows voice profiles with avatars, personality traits, and recommendations.
"""
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VoiceProfileFormatter:
    """
    Formats TaalCoach responses with AI voice profile cards.

    Shows voice character information when users ask about:
    - "What voice do I have?"
    - "What voices are available?"
    - "Which voice is best for beginners?"
    - "How do I change my voice?"
    """

    def __init__(self):
        # Voice database with complete information
        self.voices = {
            "alloy": {
                "voice_id": "alloy",
                "name": "Alloy",
                "emoji": "🎯",
                "personality": "Balanced & Neutral",
                "description": "A balanced, neutral voice suitable for all learning contexts",
                "characteristics": ["Even-toned", "Professional", "Clear", "Gender-neutral"],
                "teaching_style": "Straightforward, factual, and objective",
                "best_for": ["All levels", "Professional/business contexts", "Those who prefer minimal personality"],
                "recommended_levels": ["A1", "A2", "B1", "B2", "C1", "C2"],
                "avatar_url": "/assets/tutor/alloy.png",
            },
            "ash": {
                "voice_id": "ash",
                "name": "Ash",
                "emoji": "🌟",
                "personality": "Warm & Encouraging",
                "description": "A warm, encouraging voice that provides gentle guidance",
                "characteristics": ["Soft", "Reassuring", "Patient", "Friendly"],
                "teaching_style": "Supportive, celebrates small wins",
                "best_for": ["Beginners (A1-A2)", "Anxious learners", "Building confidence"],
                "recommended_levels": ["A1", "A2"],
                "is_default": True,
                "avatar_url": "/assets/tutor/ash.png",
            },
            "ballad": {
                "voice_id": "ballad",
                "name": "Ballad",
                "emoji": "🎵",
                "personality": "Melodic & Expressive",
                "description": "A melodic, expressive voice that makes learning musical",
                "characteristics": ["Lyrical", "Rhythmic", "Musical", "Engaging"],
                "teaching_style": "Uses rhythm and melody to aid memory",
                "best_for": ["Creative learners", "Musicians", "Pronunciation practice (A2-B2)"],
                "recommended_levels": ["A2", "B1", "B2"],
                "avatar_url": "/assets/tutor/ballad.png",
            },
            "coral": {
                "voice_id": "coral",
                "name": "Coral",
                "emoji": "🌺",
                "personality": "Bright & Friendly",
                "description": "A bright, friendly voice that energizes your practice",
                "characteristics": ["Upbeat", "Cheerful", "Energetic", "Enthusiastic"],
                "teaching_style": "Energetic, fun, makes learning feel like play",
                "best_for": ["Young learners", "Morning practice", "Conversational practice (A2-B2)"],
                "recommended_levels": ["A2", "B1", "B2"],
                "avatar_url": "/assets/tutor/coral.png",
            },
            "echo": {
                "voice_id": "echo",
                "name": "Echo",
                "emoji": "🔊",
                "personality": "Clear & Articulate",
                "description": "A clear, articulate voice perfect for pronunciation practice",
                "characteristics": ["Crystal-clear", "Precise", "Deliberate", "Excellent phonetics"],
                "teaching_style": "Focus on accuracy, pronunciation, and proper form",
                "best_for": ["Pronunciation work (ALL levels)", "Perfecting accent", "Listening practice"],
                "recommended_levels": ["A1", "A2", "C1", "C2"],
                "special_tag": "PRONUNCIATION SPECIALIST",
                "avatar_url": "/assets/tutor/echo.png",
            },
            "sage": {
                "voice_id": "sage",
                "name": "Sage",
                "emoji": "🧘",
                "personality": "Wise & Patient",
                "description": "A wise, patient voice that provides thoughtful feedback",
                "characteristics": ["Calm", "Measured", "Thoughtful", "Contemplative"],
                "teaching_style": "Reflective, encourages critical thinking",
                "best_for": ["Advanced learners (B2-C2)", "Deep conversations", "Mature learners (40+)"],
                "recommended_levels": ["B2", "C1", "C2"],
                "avatar_url": "/assets/tutor/sage.png",
            },
            "shimmer": {
                "voice_id": "shimmer",
                "name": "Shimmer",
                "emoji": "✨",
                "personality": "Dynamic & Energetic",
                "description": "A dynamic, energetic voice that keeps you motivated",
                "characteristics": ["High energy", "Enthusiastic", "Animated", "Motivational"],
                "teaching_style": "High-energy, motivational, gamified approach",
                "best_for": ["Maintaining motivation during plateaus", "Competitive learners", "Short intense sessions"],
                "recommended_levels": ["B1", "B2"],
                "special_tag": "MOTIVATION BOOSTER",
                "avatar_url": "/assets/tutor/shimmer.png",
            },
            "verse": {
                "voice_id": "verse",
                "name": "Verse",
                "emoji": "📜",
                "personality": "Poetic & Smooth",
                "description": "A poetic, smooth voice that makes learning elegant",
                "characteristics": ["Smooth", "Flowing", "Elegant", "Literary"],
                "teaching_style": "Literary, focuses on beauty of language",
                "best_for": ["Literature enthusiasts", "Advanced learners (B2-C2)", "Reading/storytelling"],
                "recommended_levels": ["B2", "C1", "C2"],
                "avatar_url": "/assets/tutor/verse.png",
            },
        }

        # Patterns that indicate voice-related queries
        self.voice_triggers = [
            r'\b(voice|voices|tutor voice|ai voice|coach voice)\b',
            r'\b(what voice|which voice|current voice|my voice)\b',
            r'\b(change voice|select voice|switch voice|choose voice)\b',
            r'\b(available voice|voice option|voice character)\b',
            r'\b(voice.*recommend|recommend.*voice|best voice)\b',
            r'\b(ai tutor|tutor of me|my tutor|which tutor|what tutor)\b',  # "What is AI tutor of me"
            r'\b(alloy|ash|ballad|coral|echo|sage|shimmer|verse)\b',  # Specific voice names
        ]

    def should_show_voice_profile(
        self,
        user_message: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if voice profile should be displayed.

        Returns:
            {
                "show": bool,
                "trigger": str,  # "current_voice", "all_voices", "recommendation", etc.
                "display_mode": str,  # "single" or "list"
                "voice_ids": List[str]  # Which voices to show
            }
        """
        result = {
            "show": False,
            "trigger": None,
            "display_mode": "single",
            "voice_ids": []
        }

        user_lower = user_message.lower()

        # Check for voice triggers
        has_voice_trigger = any(re.search(pattern, user_lower, re.IGNORECASE) for pattern in self.voice_triggers)

        if not has_voice_trigger:
            logger.info(f"[VOICE_PROFILE] No voice trigger matched for: '{user_message}'")
            return result

        logger.info(f"[VOICE_PROFILE] Voice trigger detected for: '{user_message}'")

        # Determine what kind of voice query this is
        current_voice = user_context.get("user_profile", {}).get("selected_voice", "ash")

        # "What voice do I have?" / "My current voice" / "What is ai tutor of me"
        if (re.search(r'\b(current|my|what).*voice', user_lower) or
            re.search(r'\b(ai tutor|tutor of me|my tutor|what tutor)\b', user_lower)) and \
           not re.search(r'\b(all|available|list)\b', user_lower):
            logger.info(f"[VOICE_PROFILE] Showing current voice: {current_voice}")
            result["show"] = True
            result["trigger"] = "current_voice"
            result["display_mode"] = "single"
            result["voice_ids"] = [current_voice]
            return result

        # "What voices are available?" / "List all voices"
        if re.search(r'\b(available|all|list|what are).*voice', user_lower):
            logger.info(f"[VOICE_PROFILE] Showing all voices")
            result["show"] = True
            result["trigger"] = "all_voices"
            result["display_mode"] = "list"
            result["voice_ids"] = list(self.voices.keys())
            return result

        # "Which voice is best for beginners?" / "Recommend a voice"
        if re.search(r'\b(best|recommend|which|suggest).*voice', user_lower):
            user_level = user_context.get("user_profile", {}).get("cefr_level", "A1")
            recommended = self._get_recommended_voices(user_level, user_lower)
            logger.info(f"[VOICE_PROFILE] Recommending voices for level {user_level}: {recommended}")
            result["show"] = True
            result["trigger"] = "recommendation"
            result["display_mode"] = "list"
            result["voice_ids"] = recommended[:3]  # Show top 3 recommendations
            return result

        # Specific voice query (e.g., "Tell me about Echo")
        for voice_id in self.voices.keys():
            if voice_id in user_lower:
                logger.info(f"[VOICE_PROFILE] Showing specific voice: {voice_id}")
                result["show"] = True
                result["trigger"] = "specific_voice"
                result["display_mode"] = "single"
                result["voice_ids"] = [voice_id]
                return result

        # FALLBACK: If we matched a voice trigger but no specific pattern,
        # assume they're asking about their current voice
        logger.info(f"[VOICE_PROFILE] Fallback - showing current voice: {current_voice}")
        result["show"] = True
        result["trigger"] = "current_voice"
        result["display_mode"] = "single"
        result["voice_ids"] = [current_voice]
        return result

    def _get_recommended_voices(self, user_level: str, query: str) -> List[str]:
        """Get recommended voices based on user level and query context"""

        # Special recommendations based on query keywords
        if re.search(r'\b(pronunciation|speak|accent)\b', query, re.IGNORECASE):
            return ["echo", "ash", "alloy"]

        if re.search(r'\b(confidence|beginner|new)\b', query, re.IGNORECASE):
            return ["ash", "coral", "echo"]

        if re.search(r'\b(motivation|plateau|stuck)\b', query, re.IGNORECASE):
            return ["shimmer", "coral", "ballad"]

        if re.search(r'\b(professional|business|work)\b', query, re.IGNORECASE):
            return ["alloy", "sage", "echo"]

        if re.search(r'\b(creative|poetry|literature)\b', query, re.IGNORECASE):
            return ["verse", "ballad", "sage"]

        # Default recommendations by level
        level_recommendations = {
            "A1": ["ash", "echo", "coral"],
            "A2": ["ash", "echo", "ballad"],
            "B1": ["coral", "ballad", "alloy"],
            "B2": ["sage", "verse", "shimmer"],
            "C1": ["sage", "verse", "echo"],
            "C2": ["verse", "sage", "alloy"],
        }

        return level_recommendations.get(user_level, ["ash", "echo", "coral"])

    def format_voice_profile(
        self,
        voice_ids: List[str],
        trigger: str,
        display_mode: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format voice profile data for display.

        Returns:
            {
                "type": "voice_profile",
                "data": {
                    "display_mode": "single" or "list",
                    "trigger": str,
                    "voices": [voice_data...],
                    "current_voice": str,
                    "navigation_hint": str
                }
            }
        """
        current_voice = user_context.get("user_profile", {}).get("selected_voice", "ash")

        voices_data = []
        for voice_id in voice_ids:
            if voice_id in self.voices:
                voice_data = self.voices[voice_id].copy()
                voice_data["is_current"] = (voice_id == current_voice)
                voices_data.append(voice_data)

        return {
            "type": "voice_profile",
            "data": {
                "display_mode": display_mode,
                "trigger": trigger,
                "voices": voices_data,
                "current_voice": current_voice,
                "navigation_hint": "Profile → AI Tutor Voice",
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def format_response_with_voice_profile(
        self,
        ai_response: str,
        user_message: str,
        user_context: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Format AI response to include voice profile when appropriate.

        Args:
            ai_response: AI's text response
            user_message: User's original message
            user_context: User context data

        Returns:
            Tuple of (messages, tracking_data)
            - messages: List of message objects (text + voice_profile)
            - tracking_data: Optional tracking data for analytics
        """
        # Check if we should show voice profile
        profile_decision = self.should_show_voice_profile(
            user_message,
            user_context
        )

        if not profile_decision["show"]:
            logger.info(f"[VOICE_PROFILE] Not showing voice profile")
            return ([{
                "type": "text",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }], None)

        # Build messages
        messages = []

        # Add text response
        messages.append({
            "type": "text",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Add voice profile
        voice_profile = self.format_voice_profile(
            voice_ids=profile_decision["voice_ids"],
            trigger=profile_decision["trigger"],
            display_mode=profile_decision["display_mode"],
            user_context=user_context
        )
        messages.append(voice_profile)

        # Tracking data for analytics
        tracking_data = {
            "trigger": profile_decision["trigger"],
            "display_mode": profile_decision["display_mode"],
            "voice_ids": profile_decision["voice_ids"],
            "num_voices": len(profile_decision["voice_ids"]),
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"[VOICE_PROFILE] Showing {len(profile_decision['voice_ids'])} voice(s) (trigger: {profile_decision['trigger']}, mode: {profile_decision['display_mode']})")

        return (messages, tracking_data)


# Singleton instance
voice_profile_formatter = VoiceProfileFormatter()
