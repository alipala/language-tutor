#!/usr/bin/env python3
"""
MongoDB Text Index Setup - Phase 3 (Week 1-2)
==============================================
Creates text indexes on conversation_sessions for BM25 search.

Required for hybrid search to work efficiently.

Run once to set up indexes:
    python3 setup_text_indexes.py

Author: TaalCoach RAG Team
Date: April 2026
"""

import asyncio
import logging
from database import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_text_indexes():
    """Create text indexes for BM25 search on conversation_sessions."""

    db = await get_database()

    logger.info("="*80)
    logger.info("MONGODB TEXT INDEX SETUP - Phase 3 Hybrid Search")
    logger.info("="*80)

    # Drop existing text index if exists (to recreate)
    try:
        existing_indexes = await db.conversation_sessions.index_information()

        for index_name, index_info in existing_indexes.items():
            if 'text' in str(index_info):
                logger.info(f"Dropping existing text index: {index_name}")
                await db.conversation_sessions.drop_index(index_name)

    except Exception as e:
        logger.info(f"No existing text indexes to drop: {e}")

    # Create comprehensive text index
    # Weights determine importance (higher = more important)
    logger.info("\nCreating text index on conversation_sessions...")

    index_result = await db.conversation_sessions.create_index(
        [
            ("topic", "text"),              # Weight 10
            ("custom_topic", "text"),       # Weight 10
            ("messages.content", "text"),   # Weight 5
            ("language", "text"),           # Weight 3
        ],
        weights={
            "topic": 10,
            "custom_topic": 10,
            "messages.content": 5,
            "language": 3
        },
        name="conversation_text_search_idx",
        default_language="english"
    )

    logger.info(f"✅ Text index created: {index_result}")

    # Verify index creation
    indexes = await db.conversation_sessions.index_information()
    logger.info("\nCurrent indexes on conversation_sessions:")
    for idx_name, idx_info in indexes.items():
        logger.info(f"  - {idx_name}: {idx_info.get('key', {})}")

    # Test the text search
    logger.info("\n" + "="*80)
    logger.info("TESTING TEXT SEARCH")
    logger.info("="*80)

    test_queries = [
        "travel",
        "restaurant",
        "grammar",
        "dutch"
    ]

    for query in test_queries:
        count = await db.conversation_sessions.count_documents({
            "$text": {"$search": query}
        })
        logger.info(f"Query '{query}': {count} results")

    logger.info("\n✅ Text index setup complete!")
    logger.info("Hybrid search (BM25 + Semantic) is now ready to use.")


if __name__ == "__main__":
    asyncio.run(setup_text_indexes())
