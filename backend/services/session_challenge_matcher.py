"""
Session-to-Challenge Matcher

Analyzes completed practice sessions and recommends specific challenges
that target the user's weak areas identified during the session.

This creates an intelligent bridge between practice sessions and challenge activities,
ensuring that challenges reinforce what the user just practiced.

Author: MyTacoAI Backend Team
Date: 2026-04-20
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from database import (
    challenge_pool_collection,
    reference_challenges_collection,
    recommended_actions_collection
)
from models import RecommendedAction, RecommendedActionType


class SessionChallengeMatcher:
    """
    Matches session analysis to relevant challenges.

    Analyzes grammar errors, vocabulary gaps, and pronunciation issues
    from a session and recommends 2-3 challenges that address these areas.
    """

    def __init__(self):
        """Initialize the session challenge matcher"""
        # Map error types to challenge types
        self.error_to_challenge_mapping = {
            # Grammar errors
            "verb_tense": ["error_spotting", "swipe_fix"],
            "article": ["error_spotting", "micro_quiz"],
            "preposition": ["error_spotting", "micro_quiz"],
            "subject_verb_agreement": ["error_spotting", "swipe_fix"],
            "word_order": ["swipe_fix", "story_builder"],
            "plural": ["error_spotting", "micro_quiz"],
            "gender": ["error_spotting", "micro_quiz"],

            # Vocabulary gaps
            "vocabulary": ["smart_flashcard", "story_builder"],
            "vocabulary_limited": ["smart_flashcard", "brain_tickler"],
            "new_words": ["smart_flashcard", "native_check"],

            # Pronunciation/fluency
            "pronunciation": ["native_check", "brain_tickler"],
            "fluency": ["native_check", "story_builder"],
            "hesitation": ["brain_tickler", "native_check"],

            # General
            "grammar": ["error_spotting", "micro_quiz"],
            "confidence": ["native_check", "brain_tickler"],
            "accuracy": ["error_spotting", "swipe_fix"]
        }

    async def generate_post_session_recommendations(
        self,
        user_id: str,
        session_id: str,
        session_analysis: Dict[str, Any],
        language: str,
        level: str,
        max_recommendations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate challenge recommendations based on session analysis.

        Args:
            user_id: User's ID
            session_id: Session that just completed
            session_analysis: Analysis results from the session
            language: Language practiced
            level: CEFR level
            max_recommendations: Maximum number of challenges to recommend

        Returns:
            List of recommended challenge data (for API response)
        """
        try:
            # Extract weak areas from session analysis
            weak_areas = self._extract_weak_areas(session_analysis)

            if not weak_areas:
                # No specific weak areas - return general practice
                return await self._get_general_challenges(user_id, language, level, max_recommendations)

            # Get challenge types for weak areas
            recommended_types = self._get_challenge_types_for_weak_areas(weak_areas)

            # Fetch available challenges from user's pool
            challenges = await self._fetch_matching_challenges(
                user_id,
                language,
                level,
                recommended_types,
                max_recommendations
            )

            # If not enough challenges in pool, get from reference
            if len(challenges) < max_recommendations:
                additional = await self._fetch_reference_challenges(
                    language,
                    level,
                    recommended_types,
                    max_recommendations - len(challenges)
                )
                challenges.extend(additional)

            # Create recommended actions for tracking
            await self._create_recommended_actions(
                user_id,
                session_id,
                challenges,
                weak_areas
            )

            return challenges[:max_recommendations]

        except Exception as e:
            print(f"Error generating post-session recommendations: {str(e)}")
            # Return general challenges on error
            return await self._get_general_challenges(user_id, language, level, max_recommendations)

    def _extract_weak_areas(self, session_analysis: Dict[str, Any]) -> List[str]:
        """
        Extract weak areas from session analysis.

        Looks for:
        - Grammar issues mentioned in analysis
        - Vocabulary gaps
        - Pronunciation/fluency issues
        - Accuracy scores below threshold
        """
        weak_areas = []

        # Check enhanced analysis
        enhanced = session_analysis.get("enhanced_analysis", {})

        # Grammar analysis
        grammar_text = enhanced.get("grammar_analysis", "").lower()
        if "verb" in grammar_text or "tense" in grammar_text:
            weak_areas.append("verb_tense")
        if "article" in grammar_text:
            weak_areas.append("article")
        if "preposition" in grammar_text:
            weak_areas.append("preposition")
        if "word order" in grammar_text:
            weak_areas.append("word_order")
        if "plural" in grammar_text:
            weak_areas.append("plural")

        # Vocabulary analysis
        new_vocab = enhanced.get("new_vocabulary", [])
        if len(new_vocab) > 3:
            weak_areas.append("vocabulary")

        # Confidence/fluency
        confidence_score = enhanced.get("confidence_score", 1.0)
        if confidence_score < 0.7:
            weak_areas.append("confidence")

        # Check improvements section
        improvements = enhanced.get("highlights_for_improvement", [])
        for improvement in improvements:
            improvement_lower = improvement.lower()
            if "pronunciation" in improvement_lower:
                weak_areas.append("pronunciation")
            if "fluency" in improvement_lower or "hesitat" in improvement_lower:
                weak_areas.append("fluency")
            if "vocabulary" in improvement_lower:
                weak_areas.append("vocabulary_limited")

        # Remove duplicates
        weak_areas = list(set(weak_areas))

        return weak_areas

    def _get_challenge_types_for_weak_areas(self, weak_areas: List[str]) -> List[str]:
        """
        Map weak areas to appropriate challenge types.

        Returns:
            List of challenge types, prioritized by relevance
        """
        challenge_types = []

        for weak_area in weak_areas:
            if weak_area in self.error_to_challenge_mapping:
                challenge_types.extend(self.error_to_challenge_mapping[weak_area])

        # Count frequency and prioritize
        from collections import Counter
        type_counts = Counter(challenge_types)

        # Return types sorted by frequency (most relevant first)
        sorted_types = [t for t, count in type_counts.most_common()]

        # If no specific types, default to general practice
        if not sorted_types:
            sorted_types = ["error_spotting", "micro_quiz", "smart_flashcard"]

        return sorted_types

    async def _fetch_matching_challenges(
        self,
        user_id: str,
        language: str,
        level: str,
        challenge_types: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch available challenges from user's pool that match the criteria.
        """
        try:
            # Build query for user's available challenges
            query = {
                "user_id": user_id,
                "available": True,
                "language": language,
                "cefr_level": level,
                "challenge_type": {"$in": challenge_types}
            }

            # Fetch challenges, prioritizing by type order
            challenges = []
            for challenge_type in challenge_types:
                type_query = query.copy()
                type_query["challenge_type"] = challenge_type

                type_challenges = await challenge_pool_collection.find(
                    type_query,
                    limit=1
                ).to_list(None)

                challenges.extend(type_challenges)

                if len(challenges) >= limit:
                    break

            return [self._format_challenge(c) for c in challenges[:limit]]

        except Exception as e:
            print(f"Error fetching matching challenges: {str(e)}")
            return []

    async def _fetch_reference_challenges(
        self,
        language: str,
        level: str,
        challenge_types: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch challenges from reference collection (fallback if pool empty).
        """
        try:
            query = {
                "language": language,
                "cefrLevel": level,
                "type": {"$in": challenge_types}
            }

            # Fetch challenges, prioritizing by type order
            challenges = []
            for challenge_type in challenge_types:
                type_query = query.copy()
                type_query["type"] = challenge_type

                type_challenges = await reference_challenges_collection.find(
                    type_query,
                    limit=1
                ).to_list(None)

                challenges.extend(type_challenges)

                if len(challenges) >= limit:
                    break

            return [self._format_challenge(c) for c in challenges[:limit]]

        except Exception as e:
            print(f"Error fetching reference challenges: {str(e)}")
            return []

    async def _get_general_challenges(
        self,
        user_id: str,
        language: str,
        level: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get general challenges when no specific weak areas identified.
        """
        try:
            # Try user's pool first
            challenges = await challenge_pool_collection.find(
                {
                    "user_id": user_id,
                    "available": True,
                    "language": language,
                    "cefr_level": level
                },
                limit=limit
            ).to_list(None)

            if len(challenges) < limit:
                # Fallback to reference
                additional = await reference_challenges_collection.find(
                    {
                        "language": language,
                        "cefrLevel": level
                    },
                    limit=limit - len(challenges)
                ).to_list(None)
                challenges.extend(additional)

            return [self._format_challenge(c) for c in challenges[:limit]]

        except Exception as e:
            print(f"Error fetching general challenges: {str(e)}")
            return []

    def _format_challenge(self, challenge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format challenge for API response.

        Normalizes differences between pool and reference challenges.
        """
        # Reference challenges use 'cefrLevel', pool uses 'cefr_level'
        level = challenge.get("cefrLevel") or challenge.get("cefr_level", "A2")

        return {
            "challenge_id": challenge.get("challenge_id") or str(challenge.get("_id")),
            "type": challenge.get("type") or challenge.get("challenge_type"),
            "title": challenge.get("title", "Practice Challenge"),
            "description": challenge.get("description", "Test your skills!"),
            "level": level,
            "estimated_seconds": challenge.get("estimatedSeconds", 60),
            "content": challenge.get("content", {})
        }

    async def _create_recommended_actions(
        self,
        user_id: str,
        session_id: str,
        challenges: List[Dict[str, Any]],
        weak_areas: List[str]
    ):
        """
        Create recommended action entries for tracking.

        This allows us to see if users follow through on recommendations.
        """
        try:
            if not challenges:
                return

            # Create rationale
            if weak_areas:
                areas_str = ", ".join(weak_areas[:3])
                rationale = f"Session showed challenges with: {areas_str}"
                description = f"Your session revealed areas to practice: {areas_str}. These challenges will help!"
            else:
                rationale = "Post-session general practice"
                description = "Great session! Continue practicing with these challenges."

            # Create recommended action
            action = RecommendedAction(
                user_id=user_id,
                action_type=RecommendedActionType.TRY_CHALLENGES,
                priority=1,
                title="Practice These Challenges",
                description=description,
                rationale=rationale,
                action_data={
                    "session_id": session_id,
                    "challenges": [c["challenge_id"] for c in challenges],
                    "weak_areas": weak_areas,
                    "challenge_count": len(challenges)
                },
                source="session_analysis",
                expires_at=datetime.utcnow() + timedelta(days=1)
            )

            # Save to database
            await recommended_actions_collection.insert_one(
                action.dict(by_alias=False, exclude={"id"})
            )

        except Exception as e:
            print(f"Error creating recommended actions: {str(e)}")
            # Non-critical, just log and continue


# Singleton instance
session_challenge_matcher = SessionChallengeMatcher()
