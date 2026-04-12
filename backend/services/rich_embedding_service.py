"""
Rich Embedding Service
======================
Production-grade embedding strategy for TaalCoach semantic search.

Architecture:
- Embeds ACTUAL conversation content, not just metadata
- Includes topics, vocabulary, highlights from enhanced analysis
- Optimized for cross-lingual semantic search
- Handles missing data gracefully
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RichEmbeddingBuilder:
    """
    Builds rich, semantically meaningful text for vector embedding.

    Design Principles:
    1. Include ACTUAL content (conversation excerpts, vocabulary)
    2. Structure for semantic search (topics, themes, patterns)
    3. Handle multilingual content appropriately
    4. Fail gracefully with degraded quality
    """

    MAX_CONVERSATION_CHARS = 400  # Optimal for embedding context
    MAX_VOCABULARY_ITEMS = 15
    MAX_HIGHLIGHTS = 3

    @classmethod
    def should_embed_session(cls, session: Dict[str, Any]) -> tuple[bool, str]:
        """
        PHASE 1 FIX: Filter out low-quality sessions BEFORE embedding.

        Returns:
            (should_embed: bool, reason: str)

        Filters:
        - Billing placeholders (1 message, no content)
        - Generic "Practice Session (X min)" without real topic
        - Sessions with no conversation data
        """
        # Filter 1: Skip 1-message billing placeholders
        message_count = session.get('message_count', 0)
        if message_count <= 1:
            return (False, "Billing placeholder (1 message)")

        # Filter 2: Skip if no actual messages or transcript
        messages = session.get('messages', [])
        transcript = session.get('transcript', '')
        if not messages and not transcript:
            return (False, "No conversation content (no messages/transcript)")

        # Filter 3: Skip generic "Practice Session (X min)" without real topic
        topic = session.get('topic', '')
        has_custom_topic = bool(session.get('custom_topic'))
        has_enhanced = 'enhanced_analysis' in session

        if topic.startswith('Practice Session') and not has_custom_topic and not has_enhanced:
            return (False, "Generic placeholder topic (no custom/enhanced data)")

        # Filter 4: Ensure minimum content quality
        # Check if messages array has real content (not just billing)
        if messages:
            real_messages = [
                msg for msg in messages
                if msg.get('content', '').strip()
                and not msg.get('content', '').startswith('Practice session tracked')
            ]
            if len(real_messages) < 2:  # Need at least user + AI exchange
                return (False, "Insufficient conversation (< 2 real messages)")

        # Passed all filters
        return (True, "Quality session")

    @classmethod
    def build_conversation_embedding(cls, session: Dict[str, Any]) -> str:
        """
        Build rich embedding text for a conversation session.

        Priority Order:
        1. Topic (most important for matching)
        2. Conversation excerpt (actual content)
        3. Enhanced analysis highlights
        4. Vocabulary learned
        5. Metadata (language, level, duration)

        Args:
            session: Conversation session document from MongoDB

        Returns:
            Rich text optimized for semantic search
        """
        parts = []

        # 1. TOPIC - Primary identifier
        topic = cls._extract_topic(session)
        if topic and topic != "unknown":
            parts.append(f"Topic: {topic}")

        # 2. LANGUAGE & LEVEL - Essential for filtering
        language = session.get('language', 'unknown')
        level = session.get('level', 'unknown')
        parts.append(f"Language: {language} | Level: {level}")

        # 3. CONVERSATION EXCERPT - Actual content!
        conversation_text = cls._extract_conversation_excerpt(session)
        if conversation_text:
            parts.append(f"Conversation: {conversation_text}")

        # 4. ENHANCED ANALYSIS HIGHLIGHTS - Key learnings
        highlights = cls._extract_highlights(session)
        if highlights:
            parts.append(f"Highlights: {' | '.join(highlights)}")

        # 5. VOCABULARY - Searchable terms
        vocabulary = cls._extract_vocabulary(session)
        if vocabulary:
            parts.append(f"Vocabulary: {', '.join(vocabulary)}")

        # 6. DURATION - Useful for filtering
        duration = session.get('duration_minutes', 0)
        if duration > 0:
            parts.append(f"Duration: {duration} minutes")

        # 7. SUMMARY - Fallback if no better content
        if not conversation_text and not highlights:
            summary = session.get('summary', '')
            if summary and len(summary) > 20:  # Avoid "Practice session - X min"
                parts.append(f"Summary: {summary}")

        return " | ".join(parts)

    @classmethod
    def _extract_topic(cls, session: Dict[str, Any]) -> str:
        """
        Extract meaningful topic from session.

        Filters out generic placeholders like "Practice Session (X min)"
        """
        topic = session.get('topic', '')

        # Filter out billing placeholders
        if not topic or topic.startswith('Practice Session'):
            # Try to extract from custom topic or summary
            if session.get('custom_topic'):
                return session['custom_topic']

            # Check enhanced analysis for actual topic
            enhanced = session.get('enhanced_analysis', {})
            if enhanced:
                ai_insights = enhanced.get('ai_insights', {})
                if ai_insights.get('topic_focus'):
                    return ai_insights['topic_focus']

            return "conversation"  # Generic but better than "unknown"

        return topic

    @classmethod
    def _extract_conversation_excerpt(cls, session: Dict[str, Any]) -> Optional[str]:
        """
        Extract meaningful conversation excerpt.

        Priority:
        1. First 400 chars of actual messages
        2. Transcript field
        3. None if no content
        """
        # Try messages array (most detailed)
        messages = session.get('messages', [])
        if messages and len(messages) > 1:  # Skip billing placeholders
            # Extract first few messages (user + AI back-and-forth)
            conversation_parts = []
            for msg in messages[:6]:  # First 3 exchanges
                content = msg.get('content', '').strip()
                if content and not content.startswith('Practice session tracked'):
                    # Clean emojis/formatting
                    content = content.replace('{{emoji:', '').replace('}}', '')
                    conversation_parts.append(content)

            if conversation_parts:
                excerpt = ' ... '.join(conversation_parts)
                return excerpt[:cls.MAX_CONVERSATION_CHARS]

        # Fallback to transcript field
        transcript = session.get('transcript', '')
        if transcript:
            return transcript[:cls.MAX_CONVERSATION_CHARS]

        return None

    @classmethod
    def _extract_highlights(cls, session: Dict[str, Any]) -> List[str]:
        """
        Extract key highlights from enhanced analysis.

        Sources:
        - Breakthrough moments
        - Key achievements
        - Focus areas
        """
        highlights = []

        enhanced = session.get('enhanced_analysis', {})
        if not enhanced:
            return highlights

        ai_insights = enhanced.get('ai_insights', {})

        # Breakthrough moments (most important)
        breakthroughs = ai_insights.get('breakthrough_moments', [])
        if breakthroughs:
            highlights.extend(breakthroughs[:cls.MAX_HIGHLIGHTS])

        # If no breakthroughs, use struggle points (still useful)
        if not highlights:
            struggles = ai_insights.get('struggle_points', [])
            if struggles:
                highlights.extend([f"Practiced: {s}" for s in struggles[:cls.MAX_HIGHLIGHTS]])

        return highlights

    @classmethod
    def _extract_vocabulary(cls, session: Dict[str, Any]) -> List[str]:
        """
        Extract vocabulary learned in session.

        Sources:
        - vocabulary_highlights from enhanced_analysis
        - key terms from summary
        """
        vocabulary = []

        enhanced = session.get('enhanced_analysis', {})
        if enhanced:
            ai_insights = enhanced.get('ai_insights', {})
            vocab_list = ai_insights.get('vocabulary_highlights', [])
            if vocab_list:
                # Clean and limit
                vocab_list = [v.strip() for v in vocab_list if v.strip()]
                vocabulary.extend(vocab_list[:cls.MAX_VOCABULARY_ITEMS])

        return vocabulary

    @classmethod
    def build_metadata(cls, session: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Build metadata for vector DB.

        Metadata enables:
        - Filtering by language, level, content_type
        - Recency-based ranking
        - Debugging and analytics
        """
        return {
            "user_id": user_id,
            "content_type": "conversation",
            "language": session.get("language", "unknown"),
            "level": session.get("level", "unknown"),
            "topic": cls._extract_topic(session),
            "duration_minutes": session.get("duration_minutes", 0),
            "message_count": session.get("message_count", 0),
            "has_enhanced_analysis": "enhanced_analysis" in session,
            "created_at": session.get("created_at", datetime.utcnow()).isoformat(),
            "session_id": str(session.get("_id", ""))
        }


class RichEmbeddingQualityValidator:
    """
    Validates embedding quality to ensure semantic search effectiveness.

    Quality Metrics:
    - Content richness (has actual conversation vs just metadata)
    - Semantic value (topic + content vs generic placeholders)
    - Length appropriateness (not too short, not too long)
    """

    MIN_LENGTH = 50  # Too short = poor semantic value
    MAX_LENGTH = 2000  # Too long = diluted semantics
    MIN_QUALITY_SCORE = 0.5  # Below this = warn

    @classmethod
    def validate(cls, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate embedding quality.

        Returns:
            {
                "is_valid": bool,
                "quality_score": float (0.0-1.0),
                "warnings": List[str],
                "metrics": Dict
            }
        """
        warnings = []
        metrics = {
            "length": len(text),
            "has_conversation": "Conversation:" in text,
            "has_vocabulary": "Vocabulary:" in text,
            "has_highlights": "Highlights:" in text,
            "has_real_topic": metadata.get("topic", "conversation") not in ["conversation", "unknown"],
            "message_count": metadata.get("message_count", 0)
        }

        # Length checks
        if len(text) < cls.MIN_LENGTH:
            warnings.append(f"Text too short ({len(text)} chars) - poor semantic value")

        if len(text) > cls.MAX_LENGTH:
            warnings.append(f"Text too long ({len(text)} chars) - may dilute semantics")

        # Content quality checks
        if not metrics["has_conversation"]:
            warnings.append("No conversation content - only metadata")

        if not metrics["has_real_topic"]:
            warnings.append("Generic topic - may affect search relevance")

        if metadata.get("message_count", 0) <= 1:
            warnings.append("Billing placeholder session - minimal content")

        # Calculate quality score
        quality_score = cls._calculate_quality_score(metrics)

        metrics["quality_score"] = quality_score

        return {
            "is_valid": len(text) >= cls.MIN_LENGTH and quality_score >= cls.MIN_QUALITY_SCORE,
            "quality_score": quality_score,
            "warnings": warnings,
            "metrics": metrics
        }

    @classmethod
    def _calculate_quality_score(cls, metrics: Dict[str, Any]) -> float:
        """
        Calculate embedding quality score (0.0-1.0).

        Scoring:
        - Has conversation: +0.4
        - Has vocabulary: +0.2
        - Has highlights: +0.2
        - Has real topic: +0.2
        """
        score = 0.0

        if metrics["has_conversation"]:
            score += 0.4

        if metrics["has_vocabulary"]:
            score += 0.2

        if metrics["has_highlights"]:
            score += 0.2

        if metrics["has_real_topic"]:
            score += 0.2

        return min(score, 1.0)
