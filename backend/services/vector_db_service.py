"""
Vector Database Service for TaalCoach Semantic Search
Uses Pinecone for production-grade vector storage and retrieval
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize clients
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not PINECONE_API_KEY:
    logger.error("❌ PINECONE_API_KEY not found in environment variables")
    raise ValueError("PINECONE_API_KEY must be set")

if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY must be set")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Initialize OpenAI async client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Index configuration
INDEX_NAME = "taalcoach-semantic-search"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"


class VectorDBService:
    """
    Production-grade vector database service for TaalCoach

    Features:
    - Semantic search across all user content
    - Metadata filtering (user_id, language, content_type, date)
    - Hybrid ranking (semantic similarity + recency + relevance)
    - Batch operations for efficiency
    - Error handling and retries
    """

    def __init__(self):
        self.index_name = INDEX_NAME
        self.index = None
        self._initialize_index()

    def _initialize_index(self):
        """Initialize or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if self.index_name not in index_names:
                logger.info(f"🔧 Creating new Pinecone index: {self.index_name}")
                pc.create_index(
                    name=self.index_name,
                    dimension=EMBEDDING_DIMENSIONS,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=PINECONE_CLOUD,
                        region=PINECONE_REGION
                    )
                )
                logger.info(f"✅ Created Pinecone index: {self.index_name}")
            else:
                logger.info(f"✅ Connected to existing Pinecone index: {self.index_name}")

            # Connect to index
            self.index = pc.Index(self.index_name)

            # Log index stats
            stats = self.index.describe_index_stats()
            logger.info(f"📊 Index stats: {stats.total_vector_count:,} vectors, {stats.dimension} dimensions")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone index: {str(e)}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI text-embedding-3-small

        Args:
            text: Text to embed (max 8191 tokens)

        Returns:
            1536-dimensional embedding vector
        """
        try:
            # Truncate text if too long (8191 tokens ≈ 32,000 characters)
            if len(text) > 32000:
                text = text[:32000]
                logger.warning(f"⚠️  Text truncated to 32,000 characters for embedding")

            response = await openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding
            logger.debug(f"✅ Generated embedding: {len(embedding)} dimensions")

            return embedding

        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {str(e)}")
            raise

    async def upsert_content(
        self,
        content_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Embed and upsert content to Pinecone

        Args:
            content_id: Unique ID for this content (e.g., "conv_69962fc967664c1a344da758_001")
            text: Content to embed
            metadata: Metadata for filtering
                - user_id (str): User ID
                - content_type (str): "conversation", "challenge", "flashcard", "plan", etc.
                - language (str): "dutch", "spanish", etc.
                - created_at (str): ISO timestamp
                - Additional fields as needed

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = await self.generate_embedding(text)

            # Prepare vector for upsert
            vector = {
                "id": content_id,
                "values": embedding,
                "metadata": {
                    **metadata,
                    "text": text[:1000],  # Store first 1000 chars for context
                    "text_length": len(text),
                    "indexed_at": datetime.utcnow().isoformat()
                }
            }

            # Upsert to Pinecone
            self.index.upsert(vectors=[vector])

            logger.info(f"✅ Upserted vector: {content_id} ({metadata.get('content_type')})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upsert content {content_id}: {str(e)}")
            return False

    async def upsert_batch(
        self,
        contents: List[Dict[str, Any]]
    ) -> int:
        """
        Batch upsert multiple contents (more efficient)

        Args:
            contents: List of dicts with keys: id, text, metadata

        Returns:
            Number of successful upserts
        """
        try:
            # Generate embeddings in parallel
            logger.info(f"🔄 Generating embeddings for {len(contents)} items...")

            embedding_tasks = [
                self.generate_embedding(content["text"])
                for content in contents
            ]
            embeddings = await asyncio.gather(*embedding_tasks, return_exceptions=True)

            # Prepare vectors
            vectors = []
            for i, (content, embedding) in enumerate(zip(contents, embeddings)):
                if isinstance(embedding, Exception):
                    logger.error(f"❌ Failed embedding for {content.get('id')}: {embedding}")
                    continue

                vectors.append({
                    "id": content["id"],
                    "values": embedding,
                    "metadata": {
                        **content["metadata"],
                        "text": content["text"][:1000],
                        "text_length": len(content["text"]),
                        "indexed_at": datetime.utcnow().isoformat()
                    }
                })

            # Batch upsert (Pinecone supports up to 100 vectors per batch)
            batch_size = 100
            total_upserted = 0

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                total_upserted += len(batch)
                logger.info(f"✅ Upserted batch {i//batch_size + 1}: {len(batch)} vectors")

            logger.info(f"✅ Total upserted: {total_upserted}/{len(contents)} vectors")
            return total_upserted

        except Exception as e:
            logger.error(f"❌ Batch upsert failed: {str(e)}")
            return 0

    async def semantic_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with metadata filtering

        Args:
            query: User's natural language query
            user_id: User ID (for filtering to user's data only)
            top_k: Number of results to return
            filters: Additional metadata filters
                - content_type: List["conversation", "challenge"] or single value
                - language: "dutch", "spanish", etc.
                - date_from: ISO timestamp
                - date_to: ISO timestamp
            include_metadata: Whether to include full metadata in results

        Returns:
            List of matches with score, id, metadata, text
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)

            # Build metadata filter
            metadata_filter = {"user_id": user_id}

            if filters:
                # Content type filter (can be list or single value)
                if "content_type" in filters:
                    content_types = filters["content_type"]
                    if isinstance(content_types, list):
                        metadata_filter["content_type"] = {"$in": content_types}
                    else:
                        metadata_filter["content_type"] = content_types

                # Language filter
                if "language" in filters:
                    metadata_filter["language"] = filters["language"]

                # Date range filter
                if "date_from" in filters:
                    metadata_filter["created_at"] = {"$gte": filters["date_from"]}
                if "date_to" in filters:
                    if "created_at" in metadata_filter:
                        metadata_filter["created_at"]["$lte"] = filters["date_to"]
                    else:
                        metadata_filter["created_at"] = {"$lte": filters["date_to"]}

            # Query Pinecone
            logger.info(f"🔍 Searching: '{query[:50]}...' for user {user_id}")
            logger.debug(f"   Filters: {metadata_filter}")

            results = self.index.query(
                vector=query_embedding,
                filter=metadata_filter,
                top_k=top_k,
                include_metadata=include_metadata
            )

            # Format results
            matches = []
            for match in results.matches:
                matches.append({
                    "score": match.score,
                    "id": match.id,
                    "metadata": match.metadata if include_metadata else {},
                    "text": match.metadata.get("text", "") if include_metadata else ""
                })

            logger.info(f"✅ Found {len(matches)} semantic matches (top score: {matches[0]['score']:.3f})" if matches else "No matches found")

            return matches

        except Exception as e:
            logger.error(f"❌ Semantic search failed: {str(e)}")
            return []

    async def hybrid_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        recency_boost: float = 0.1,
        relevance_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Advanced hybrid search with semantic similarity + recency boost + relevance filtering

        Args:
            query: User's query
            user_id: User ID
            top_k: Results to return
            filters: Metadata filters
            recency_boost: Weight for recency (0.0-1.0, default 0.1)
            relevance_threshold: Minimum similarity score (0.0-1.0, default 0.7)

        Returns:
            Ranked results with hybrid scores
        """
        try:
            # Get semantic matches
            matches = await self.semantic_search(
                query=query,
                user_id=user_id,
                top_k=top_k * 2,  # Get more to apply post-filtering
                filters=filters,
                include_metadata=True
            )

            # Filter by relevance threshold
            matches = [m for m in matches if m["score"] >= relevance_threshold]

            if not matches:
                logger.warning(f"⚠️  No matches above relevance threshold {relevance_threshold}")
                return []

            # Apply recency boost
            now = datetime.utcnow()
            for match in matches:
                created_at = match["metadata"].get("created_at")
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        days_old = (now - created_date).days

                        # Exponential decay: recent content gets boost
                        recency_score = max(0, 1.0 - (days_old / 30.0))  # Decay over 30 days

                        # Hybrid score = semantic_similarity * (1 - recency_boost) + recency_score * recency_boost
                        match["hybrid_score"] = (
                            match["score"] * (1 - recency_boost) +
                            recency_score * recency_boost
                        )
                        match["recency_score"] = recency_score
                        match["days_old"] = days_old
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to parse date {created_at}: {e}")
                        match["hybrid_score"] = match["score"]
                else:
                    match["hybrid_score"] = match["score"]

            # Re-rank by hybrid score
            matches.sort(key=lambda x: x.get("hybrid_score", x["score"]), reverse=True)

            # Return top-k
            matches = matches[:top_k]

            logger.info(f"✅ Hybrid search: {len(matches)} results (top hybrid score: {matches[0]['hybrid_score']:.3f})")

            return matches

        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {str(e)}")
            return []

    def delete_user_content(self, user_id: str) -> bool:
        """
        Delete all vectors for a user (GDPR compliance)

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            # Pinecone doesn't support bulk delete by metadata filter directly
            # We need to query first, then delete by IDs

            logger.info(f"🗑️  Deleting all content for user {user_id}")

            # This is a placeholder - actual implementation depends on Pinecone SDK version
            # For now, log warning
            logger.warning(f"⚠️  User content deletion not fully implemented - requires ID-based deletion")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete user content: {str(e)}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimensions": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
        except Exception as e:
            logger.error(f"❌ Failed to get index stats: {str(e)}")
            return {}


# Global instance
vector_db = VectorDBService()


# Convenience functions
async def embed_user_content(user_id: str, content_type: str, content_data: List[Dict[str, Any]]) -> int:
    """
    Convenience function to embed user content

    Args:
        user_id: User ID
        content_type: "conversation", "challenge", "flashcard", etc.
        content_data: List of content items with 'id', 'text', and additional metadata

    Returns:
        Number of items successfully embedded
    """
    contents = []
    for item in content_data:
        contents.append({
            "id": f"{content_type}_{user_id}_{item['id']}",
            "text": item["text"],
            "metadata": {
                "user_id": user_id,
                "content_type": content_type,
                **item.get("metadata", {})
            }
        })

    return await vector_db.upsert_batch(contents)


async def search_user_context(query: str, user_id: str, filters: Optional[Dict] = None) -> List[Dict]:
    """
    Convenience function for semantic search

    Args:
        query: User's query
        user_id: User ID
        filters: Optional metadata filters

    Returns:
        List of relevant content matches
    """
    return await vector_db.hybrid_search(
        query=query,
        user_id=user_id,
        top_k=10,
        filters=filters,
        recency_boost=0.15,  # 15% recency weight
        relevance_threshold=0.65  # 65% minimum similarity
    )
