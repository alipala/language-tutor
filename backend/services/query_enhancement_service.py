"""
Query Enhancement Service
=========================
Enhances user queries with semantic expansion, synonyms, and context injection
for improved vector search retrieval accuracy.

PRODUCTION-GRADE IMPLEMENTATION - Phase 1
"""
import logging
from typing import Dict, List, Set, Optional
import re

logger = logging.getLogger(__name__)


class QueryEnhancementService:
    """
    Enhances user queries for better semantic search results.

    Transforms queries by:
    1. Adding multilingual synonyms
    2. Injecting user context (language, level, goals)
    3. Expanding domain-specific terms
    4. Removing noise words
    """

    # Multilingual synonym maps for common language learning topics
    SYNONYM_MAPS = {
        # Travel & Tourism
        'travel': ['vacation', 'trip', 'holiday', 'journey', 'tourism', 'sightseeing', 'voyage', 'traveling'],
        'reizen': ['vakantie', 'reis', 'toerisme'],  # Dutch
        'viajar': ['vacaciones', 'viaje', 'turismo'],  # Spanish
        'voyage': ['vacances', 'tourisme'],  # French

        # Food & Dining
        'restaurant': ['dining', 'food', 'eating', 'cafe', 'meal', 'dinner', 'lunch'],
        'eten': ['restaurant', 'voedsel', 'maaltijd'],  # Dutch
        'comer': ['restaurante', 'comida', 'almuerzo'],  # Spanish
        'manger': ['repas', 'nourriture', 'dîner'],  # French

        # Grammar & Language Structure
        'grammar': ['syntax', 'structure', 'rules', 'conjugation', 'tense', 'verb'],
        'grammatica': ['werkwoord', 'zinsstructuur', 'vervoeging'],  # Dutch
        'gramática': ['verbo', 'tiempo', 'conjugación'],  # Spanish
        'grammaire': ['verbe', 'temps', 'conjugaison'],  # French

        # Speaking & Pronunciation
        'speaking': ['pronunciation', 'accent', 'fluency', 'conversation', 'dialogue', 'talk'],
        'spreken': ['uitspraak', 'accent', 'vloeiendheid'],  # Dutch
        'hablar': ['pronunciación', 'acento', 'fluidez'],  # Spanish
        'parler': ['prononciation', 'accent', 'fluidité'],  # French

        # Practice & Learning
        'practice': ['exercise', 'training', 'drill', 'session', 'study'],
        'oefenen': ['trainen', 'studeren', 'leren'],  # Dutch
        'practicar': ['entrenar', 'estudiar', 'ejercicio'],  # Spanish
        'pratiquer': ['entraîner', 'étudier', 'exercice'],  # French

        # Common locations
        'hotel': ['accommodation', 'lodging', 'hostel', 'motel'],
        'airport': ['flight', 'plane', 'airplane', 'terminal'],
        'station': ['train', 'railway', 'metro', 'subway'],

        # Common activities
        'shopping': ['buying', 'purchasing', 'store', 'market'],
        'directions': ['navigation', 'way', 'route', 'location', 'address'],

        # Learning concepts
        'vocabulary': ['words', 'terms', 'lexicon', 'phrases'],
        'challenge': ['quiz', 'game', 'exercise', 'test'],
        'flashcard': ['vocabulary', 'memorization', 'review'],
    }

    # Noise words to remove (don't add semantic value)
    NOISE_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'about', 'as', 'is', 'was', 'are', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'what', 'which', 'who', 'when', 'where', 'why', 'how',
        'my', 'me', 'i', 'you', 'your', 'their', 'his', 'her'
    }

    def __init__(self):
        logger.info("[QUERY_ENHANCE] Query Enhancement Service initialized")

    async def enhance_query(
        self,
        query: str,
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Enhance a user query for better semantic search.

        Args:
            query: Original user query
            user_context: Dict with:
                - target_language: Learning language (e.g., 'dutch', 'spanish')
                - current_level: CEFR level (e.g., 'A2', 'B1')
                - learning_goals: User's learning objectives

        Returns:
            Enhanced query string

        Example:
            Input:  "What did I practice about travel?"
            Output: "practice conversation travel vacation trip journey tourism
                     dutch A2 B1 booking transport accommodation"
        """
        try:
            logger.debug(f"[QUERY_ENHANCE] Original query: '{query}'")

            # 1. Extract keywords (remove noise words)
            keywords = self._extract_keywords(query)
            logger.debug(f"[QUERY_ENHANCE] Keywords: {keywords}")

            # 2. Expand with synonyms
            expanded = self._add_synonyms(keywords)
            logger.debug(f"[QUERY_ENHANCE] After synonyms: {len(expanded)} terms")

            # 3. Add user context
            if user_context:
                expanded = self._add_user_context(expanded, user_context)
                logger.debug(f"[QUERY_ENHANCE] After context: {len(expanded)} terms")

            # 4. Rebuild enhanced query
            enhanced_query = ' '.join(sorted(expanded))

            logger.info(f"[QUERY_ENHANCE] Enhanced: '{query[:50]}...' → {len(expanded)} terms")

            return enhanced_query

        except Exception as e:
            logger.error(f"[QUERY_ENHANCE] Enhancement failed: {e}")
            # Fallback to original query
            return query

    def _extract_keywords(self, query: str) -> Set[str]:
        """
        Extract meaningful keywords from query.

        Removes noise words, normalizes case, handles punctuation.
        """
        # Lowercase and remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', query.lower())

        # Split into words
        words = normalized.split()

        # Filter noise words and short words (< 3 chars)
        keywords = {
            word for word in words
            if word not in self.NOISE_WORDS and len(word) >= 3
        }

        return keywords

    def _add_synonyms(self, keywords: Set[str]) -> Set[str]:
        """
        Expand keywords with synonyms from SYNONYM_MAPS.
        """
        expanded = set(keywords)  # Start with original keywords

        for keyword in keywords:
            if keyword in self.SYNONYM_MAPS:
                synonyms = self.SYNONYM_MAPS[keyword]
                expanded.update(synonyms)
                logger.debug(f"[QUERY_ENHANCE] '{keyword}' → +{len(synonyms)} synonyms")

        return expanded

    def _add_user_context(
        self,
        keywords: Set[str],
        user_context: Dict
    ) -> Set[str]:
        """
        Inject user context into keywords.

        Adds:
        - Target language
        - Current CEFR level
        - Learning goals (if present)
        """
        enhanced = set(keywords)

        # Add target language
        target_lang = user_context.get('target_language', '')
        if target_lang:
            target_lang = target_lang.lower()
        if target_lang and target_lang not in ['all', 'english', '']:
            enhanced.add(target_lang)
            logger.debug(f"[QUERY_ENHANCE] Added language: {target_lang}")

        # Add current level
        current_level = user_context.get('current_level', '')
        if current_level:
            current_level = current_level.upper()
        if current_level and current_level not in ['', 'NONE']:
            enhanced.add(current_level)
            # Also add adjacent levels for better coverage
            if current_level in ['A1', 'A2']:
                enhanced.add('beginner')
            elif current_level in ['B1', 'B2']:
                enhanced.add('intermediate')
            elif current_level in ['C1', 'C2']:
                enhanced.add('advanced')
            logger.debug(f"[QUERY_ENHANCE] Added level: {current_level}")

        # Add learning goals (extract keywords)
        learning_goals = user_context.get('learning_goals', '')
        if learning_goals:
            goal_keywords = self._extract_keywords(learning_goals)
            enhanced.update(goal_keywords)
            logger.debug(f"[QUERY_ENHANCE] Added {len(goal_keywords)} goal keywords")

        return enhanced

    def enhance_query_sync(
        self,
        query: str,
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Synchronous version for non-async contexts.
        """
        import asyncio

        # Check if we're in an async context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in async context, create new task
                return asyncio.create_task(self.enhance_query(query, user_context))
            else:
                # Run in sync
                return loop.run_until_complete(self.enhance_query(query, user_context))
        except RuntimeError:
            # No event loop, run sync
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.enhance_query(query, user_context))
            finally:
                loop.close()


# Global singleton instance
query_enhancer = QueryEnhancementService()
