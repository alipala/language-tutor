"""
Hybrid Search Service - Phase 3 (Week 1-2)
==========================================
Combines BM25 (keyword/lexical) + Semantic (vector) search using Reciprocal Rank Fusion (RRF).

Improves retrieval by catching both:
- Semantic matches (similar meaning)
- Exact keyword matches (names, dates, specific terms)

Author: TaalCoach RAG Team
Date: April 2026
"""

import logging
from typing import List, Dict, Any, Optional
from database import get_database
from services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Hybrid search combining BM25 (MongoDB text search) + Semantic (Pinecone vector search).

    Uses Reciprocal Rank Fusion (RRF) to combine rankings from both methods.
    """

    def __init__(self):
        """Initialize hybrid search service."""
        self.vector_db = VectorDBService()
        self.rrf_k = 60  # RRF constant (recommended: 60)

        logger.info("[HYBRID] Hybrid Search Service initialized")

    async def hybrid_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 10,
        semantic_weight: float = 0.6,
        bm25_weight: float = 0.4,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining semantic + BM25 keyword search.

        Args:
            query: User's search query
            user_id: User ID to filter results
            top_k: Number of results to return
            semantic_weight: Weight for semantic scores (0.0-1.0)
            bm25_weight: Weight for BM25 scores (0.0-1.0)
            filters: Optional metadata filters

        Returns:
            Dict with matches, scores, and search metadata
        """
        logger.info(f"[HYBRID] Starting hybrid search for user {user_id}: '{query[:50]}...'")

        # Run both searches in parallel (would use asyncio.gather in production)
        # For now, sequential for simplicity

        # 1. Semantic search (Pinecone)
        semantic_results = await self._semantic_search(query, user_id, top_k=20, filters=filters)

        # 2. BM25 search (MongoDB text search)
        bm25_results = await self._bm25_search(query, user_id, top_k=20, filters=filters)

        logger.info(f"[HYBRID] Semantic: {len(semantic_results)} results, BM25: {len(bm25_results)} results")

        # 3. Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            bm25_results=bm25_results,
            semantic_weight=semantic_weight,
            bm25_weight=bm25_weight
        )

        # 4. Return top-k results
        final_results = fused_results[:top_k]

        logger.info(f"[HYBRID] Returned {len(final_results)} fused results (top score: {final_results[0]['hybrid_score']:.3f})")

        return {
            "matches": final_results,
            "total": len(final_results),
            "semantic_count": len(semantic_results),
            "bm25_count": len(bm25_results),
            "fusion_method": "reciprocal_rank_fusion",
            "weights": {"semantic": semantic_weight, "bm25": bm25_weight}
        }

    async def _semantic_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector DB.

        Returns:
            List of matches with semantic_score
        """
        try:
            # Use existing vector DB service
            results = await self.vector_db.semantic_search(
                query=query,
                user_id=user_id,
                top_k=top_k,
                filters=filters
            )

            # Normalize to standard format
            matches = []
            for r in results:
                matches.append({
                    "id": r.get("id", ""),
                    "text": r.get("text", ""),
                    "metadata": r.get("metadata", {}),
                    "semantic_score": r.get("score", 0.0),
                    "source": "semantic"
                })

            return matches

        except Exception as e:
            logger.error(f"[HYBRID] Semantic search failed: {e}")
            return []

    async def _bm25_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search using MongoDB text search.

        MongoDB text search uses BM25-like scoring algorithm.
        Requires text index on conversation_sessions collection.

        Returns:
            List of matches with bm25_score
        """
        try:
            db = await get_database()

            # Build text search query
            search_filter = {
                "user_id": user_id,
                "$text": {"$search": query}
            }

            # Add additional filters if provided
            if filters:
                if filters.get('language'):
                    search_filter['language'] = filters['language']
                if filters.get('topic'):
                    search_filter['$or'] = [
                        {'topic': {'$regex': filters['topic'], '$options': 'i'}},
                        {'custom_topic': {'$regex': filters['topic'], '$options': 'i'}}
                    ]

            # Execute text search with score projection
            cursor = db.conversation_sessions.find(
                search_filter,
                {
                    'score': {'$meta': 'textScore'},
                    'topic': 1,
                    'custom_topic': 1,
                    'language': 1,
                    'created_at': 1,
                    'duration_minutes': 1,
                    'messages': 1
                }
            ).sort([('score', {'$meta': 'textScore'})]).limit(top_k)

            results = await cursor.to_list(None)

            # Normalize to standard format
            matches = []
            for r in results:
                # Build text representation
                topic = r.get('custom_topic') or r.get('topic', 'Practice Session')
                text = f"{topic} | Language: {r.get('language', 'unknown')} | Duration: {r.get('duration_minutes', 0)} min"

                # Add message excerpts if available
                messages = r.get('messages', [])
                if messages and len(messages) > 1:
                    excerpts = [m.get('content', '')[:100] for m in messages[:3] if m.get('content')]
                    if excerpts:
                        text += " | Conversation: " + " ... ".join(excerpts)

                matches.append({
                    "id": str(r.get('_id', '')),
                    "text": text,
                    "metadata": {
                        "session_id": str(r.get('_id', '')),
                        "topic": topic,
                        "language": r.get('language', ''),
                        "created_at": r.get('created_at', ''),
                        "duration_minutes": r.get('duration_minutes', 0)
                    },
                    "bm25_score": r.get('score', 0.0),
                    "source": "bm25"
                })

            logger.info(f"[HYBRID] BM25 search returned {len(matches)} results")
            return matches

        except Exception as e:
            logger.error(f"[HYBRID] BM25 search failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        semantic_weight: float = 0.6,
        bm25_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and BM25 results using Reciprocal Rank Fusion (RRF).

        RRF formula: score(d) = sum over all rankings r: 1 / (k + rank_r(d))
        where k is a constant (typically 60)

        Args:
            semantic_results: Results from semantic search
            bm25_results: Results from BM25 search
            semantic_weight: Weight for semantic scores
            bm25_weight: Weight for BM25 scores

        Returns:
            List of fused results sorted by hybrid score
        """
        # Create combined result map
        result_map = {}

        # Process semantic results
        for rank, result in enumerate(semantic_results, start=1):
            doc_id = result['id']
            rrf_score = 1.0 / (self.rrf_k + rank)

            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
                result_map[doc_id]['semantic_rank'] = rank
                result_map[doc_id]['bm25_rank'] = None
                result_map[doc_id]['rrf_semantic'] = rrf_score
                result_map[doc_id]['rrf_bm25'] = 0.0
            else:
                result_map[doc_id]['semantic_rank'] = rank
                result_map[doc_id]['rrf_semantic'] = rrf_score

        # Process BM25 results
        for rank, result in enumerate(bm25_results, start=1):
            doc_id = result['id']
            rrf_score = 1.0 / (self.rrf_k + rank)

            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
                result_map[doc_id]['semantic_rank'] = None
                result_map[doc_id]['bm25_rank'] = rank
                result_map[doc_id]['rrf_semantic'] = 0.0
                result_map[doc_id]['rrf_bm25'] = rrf_score
            else:
                result_map[doc_id]['bm25_rank'] = rank
                result_map[doc_id]['rrf_bm25'] = rrf_score

        # Calculate weighted hybrid scores
        for doc_id, result in result_map.items():
            # Weighted RRF score
            hybrid_score = (
                semantic_weight * result['rrf_semantic'] +
                bm25_weight * result['rrf_bm25']
            )

            result['hybrid_score'] = hybrid_score

            # Add interpretability metadata
            result['fusion_details'] = {
                "semantic_contribution": semantic_weight * result['rrf_semantic'],
                "bm25_contribution": bm25_weight * result['rrf_bm25'],
                "found_in": []
            }

            if result['semantic_rank']:
                result['fusion_details']['found_in'].append(f"semantic(rank={result['semantic_rank']})")
            if result['bm25_rank']:
                result['fusion_details']['found_in'].append(f"bm25(rank={result['bm25_rank']})")

        # Sort by hybrid score (descending)
        fused_results = sorted(
            result_map.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )

        logger.info(f"[HYBRID] Fused {len(fused_results)} unique results via RRF")

        return fused_results


# Singleton instance
hybrid_search_service = HybridSearchService()
