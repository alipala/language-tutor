"""
Semantic Reranker Service - Phase 2
====================================
Uses cross-encoder for post-retrieval reranking to improve precision.

Cross-encoders are more accurate than bi-encoders (used in vector search) because
they process query-document pairs jointly, not separately.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
- Size: 17MB (lightweight, fast inference)
- Trained on MS MARCO passage ranking dataset
- Scores: Higher = more relevant
"""
import logging
from typing import List, Dict, Any
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

# Lazy import - only load if needed
_cross_encoder = None


def _get_cross_encoder():
    """Lazy load cross-encoder model."""
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("✅ Cross-encoder model loaded (17MB)")
        except ImportError:
            logger.error("❌ sentence-transformers not installed. Install: pip install sentence-transformers")
            _cross_encoder = False  # Mark as unavailable
        except Exception as e:
            logger.error(f"❌ Failed to load cross-encoder: {e}")
            _cross_encoder = False
    return _cross_encoder if _cross_encoder is not False else None


class SemanticReranker:
    """
    Production-grade semantic reranker for TaalCoach.

    Features:
    - Cross-encoder rescoring for better relevance
    - Weighted combination of bi-encoder + cross-encoder scores
    - Async support for non-blocking inference
    - Graceful degradation if model unavailable
    """

    def __init__(self):
        self.model = None
        self.enabled = True
        self._initialize()

    def _initialize(self):
        """Initialize cross-encoder model."""
        self.model = _get_cross_encoder()
        if self.model is None:
            logger.warning("⚠️  Cross-encoder disabled - will use vector scores only")
            self.enabled = False
        else:
            logger.info("✅ Semantic reranker initialized")

    async def rerank(
        self,
        query: str,
        matches: List[Dict[str, Any]],
        top_k: int = 5,
        bi_encoder_weight: float = 0.6,
        cross_encoder_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Rerank semantic matches using cross-encoder.

        Args:
            query: User's query
            matches: List of matches from vector search
                Each match should have: score, text, metadata
            top_k: Number of results to return
            bi_encoder_weight: Weight for original vector similarity (0.0-1.0)
            cross_encoder_weight: Weight for cross-encoder score (0.0-1.0)

        Returns:
            Reranked matches with final_score field

        Example:
            matches = await vector_search(query, user_id)
            reranked = await reranker.rerank(query, matches, top_k=5)
            # reranked[0] has highest final_score (most relevant)
        """
        if not matches:
            return []

        # If cross-encoder disabled, return original matches
        if not self.enabled or self.model is None:
            logger.debug("⏭️  Reranking disabled - returning original matches")
            return matches[:top_k]

        try:
            logger.debug(f"🔄 Reranking {len(matches)} matches with cross-encoder")

            # Run in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            reranked = await loop.run_in_executor(
                None,
                self._rerank_sync,
                query,
                matches,
                top_k,
                bi_encoder_weight,
                cross_encoder_weight
            )

            logger.info(f"✅ Reranked {len(reranked)} results (top score: {reranked[0]['final_score']:.3f})")
            return reranked

        except Exception as e:
            logger.error(f"❌ Reranking failed: {e}")
            # Fallback to original matches
            return matches[:top_k]

    def _rerank_sync(
        self,
        query: str,
        matches: List[Dict],
        top_k: int,
        bi_encoder_weight: float,
        cross_encoder_weight: float
    ) -> List[Dict]:
        """Synchronous reranking (runs in thread pool)."""
        # Create query-document pairs
        pairs = []
        for match in matches:
            text = match.get('text', '')
            if not text:
                # Fallback to metadata text if available
                text = match.get('metadata', {}).get('text', '')
            pairs.append([query, text])

        # Score with cross-encoder
        cross_scores = self.model.predict(pairs)

        # Combine scores
        for match, cross_score in zip(matches, cross_scores):
            bi_encoder_score = match.get('hybrid_score', match.get('score', 0.0))

            # Weighted average
            final_score = (
                bi_encoder_weight * bi_encoder_score +
                cross_encoder_weight * float(cross_score)
            )

            match['cross_encoder_score'] = float(cross_score)
            match['final_score'] = final_score
            match['reranked'] = True

            logger.debug(
                f"  Match {match.get('id', '?')[:20]}: "
                f"bi={bi_encoder_score:.3f}, cross={cross_score:.3f}, "
                f"final={final_score:.3f}"
            )

        # Sort by final score
        ranked = sorted(matches, key=lambda x: x.get('final_score', 0), reverse=True)

        return ranked[:top_k]

    def rerank_sync(
        self,
        query: str,
        matches: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Synchronous version for non-async contexts.
        """
        if not self.enabled or self.model is None:
            return matches[:top_k]

        return self._rerank_sync(query, matches, top_k, 0.6, 0.4)


# Global singleton instance
semantic_reranker = SemanticReranker()
