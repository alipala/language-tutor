"""
Main News Generation Orchestrator
Coordinates all CrewAI agents to generate daily news content
Runs at 1:00 AM CET daily via scheduler
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz
from bson import ObjectId
import logging

from database import news_batches_collection, news_articles_collection
from news_generation.crew_agents import (
    create_search_agent,
    create_safety_agent,
    create_summarization_agent,
    create_vocabulary_agent,
    create_search_task,
    create_safety_task,
    create_summarization_task,
    create_vocabulary_task,
    MVP_ARTICLE_COUNT,
    MVP_LANGUAGES,
    MVP_LEVELS
)
from news_generation.news_tools import get_diverse_news

logger = logging.getLogger(__name__)

# Configuration
MAX_RETRY_COUNT = 3
GENERATION_TIMEOUT = 7200  # 2 hours


class NewsGenerationError(Exception):
    """Custom exception for news generation failures"""
    pass


async def generate_daily_news(retry_count: int = 0) -> Dict[str, Any]:
    """
    Main function to generate daily news content
    Orchestrates all agents and saves to MongoDB

    Args:
        retry_count: Current retry attempt (0-indexed)

    Returns:
        Generation statistics and status

    Raises:
        NewsGenerationError: If generation fails after all retries
    """
    logger.info(f"[NEWS_GEN] Starting daily news generation (attempt {retry_count + 1}/{MAX_RETRY_COUNT})")

    # Get current date in CET
    cet = pytz.timezone('CET')
    generation_start = datetime.now(cet)
    today = generation_start.date()
    today_start = datetime.combine(today, datetime.min.time())
    today_start = cet.localize(today_start)

    # Convert to UTC naive datetime for MongoDB storage (Motor stores datetimes as UTC naive)
    today_start_utc = today_start.astimezone(pytz.utc).replace(tzinfo=None)

    try:
        # Step 1: Create or update batch record (upsert to avoid duplicate key errors)
        batch_id = ObjectId()

        # Use upsert with $setOnInsert for _id (only set on insert, not update)
        # This prevents "immutable field '_id'" error when updating existing batch
        result = await news_batches_collection.update_one(
            {"date": today_start_utc},
            {
                "$set": {
                    "status": "in_progress",
                    "generation_started_at": generation_start,
                    "retry_count": retry_count,
                    "article_count": 0
                },
                "$setOnInsert": {
                    "_id": batch_id,
                    "date": today_start_utc
                }
            },
            upsert=True
        )

        # If we updated an existing batch, get its _id
        if result.upserted_id:
            batch_id = result.upserted_id
        else:
            # Find the existing batch to get its _id
            existing_batch = await news_batches_collection.find_one({"date": today_start_utc})
            if existing_batch:
                batch_id = existing_batch["_id"]

        logger.info(f"[NEWS_GEN] Created/updated batch record: {batch_id}")

        # Step 2: AGENT 1 - Search for news articles
        logger.info("[NEWS_GEN] STEP 1: Searching for news articles...")
        # Note: Agent creation may return None if CrewAI not available (MVP mode)
        search_agent = create_search_agent()

        # Get previously used article URLs (last 7 days) to avoid duplicates
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        used_urls = []
        async for article in news_articles_collection.find(
            {"created_at": {"$gte": week_ago}},
            {"original.url": 1}
        ):
            url = article.get("original", {}).get("url")
            if url:
                used_urls.append(url)

        if used_urls:
            logger.info(f"[NEWS_GEN] Excluding {len(used_urls)} previously used articles from last 7 days")

        # Use our news tools to get articles (works without CrewAI)
        candidate_articles = get_diverse_news(exclude_urls=used_urls)

        if not candidate_articles:
            raise NewsGenerationError("No articles found in search")

        logger.info(f"[NEWS_GEN] Found {len(candidate_articles)} candidate articles")

        # Step 3: AGENT 2 - Safety evaluation
        logger.info("[NEWS_GEN] STEP 2: Evaluating article safety...")
        # Note: Agent creation may return None if CrewAI not available (MVP mode)
        safety_agent = create_safety_agent()

        # MVP uses simple rule-based safety (no LLM calls needed)
        safe_articles = await evaluate_safety_simple(candidate_articles)

        if len(safe_articles) < MVP_ARTICLE_COUNT:
            logger.warning(f"[NEWS_GEN] Only {len(safe_articles)} safe articles found (target: {MVP_ARTICLE_COUNT})")

        logger.info(f"[NEWS_GEN] {len(safe_articles)} articles passed safety evaluation")

        # Limit to MVP_ARTICLE_COUNT
        safe_articles = safe_articles[:MVP_ARTICLE_COUNT]

        # Step 4: AGENTS 3 & 4 - Parallel generation for all variations
        logger.info("[NEWS_GEN] STEP 3: Generating adaptations (parallel processing)...")

        # Calculate total variations
        total_variations = len(safe_articles) * len(MVP_LANGUAGES) * len(MVP_LEVELS)
        logger.info(f"[NEWS_GEN] Generating {total_variations} variations ({len(safe_articles)} articles × {len(MVP_LANGUAGES)} langs × {len(MVP_LEVELS)} levels)")

        # Generate all variations in parallel
        article_docs = await generate_all_variations_parallel(
            safe_articles,
            batch_id,
            today_start_utc
        )

        # Step 5: Save to MongoDB
        logger.info("[NEWS_GEN] STEP 4: Saving to MongoDB...")

        if article_docs:
            await news_articles_collection.insert_many(article_docs)
            logger.info(f"[NEWS_GEN] Saved {len(article_docs)} articles to database")

        # Step 6: Update batch status
        generation_end = datetime.now(cet)
        duration = (generation_end - generation_start).total_seconds()

        await news_batches_collection.update_one(
            {"_id": batch_id},
            {
                "$set": {
                    "status": "completed",
                    "article_count": len(article_docs),
                    "generation_completed_at": generation_end,
                    "generation_duration_seconds": duration
                }
            }
        )

        logger.info(f"[NEWS_GEN] ✅ Generation completed successfully in {duration:.1f} seconds")

        return {
            "success": True,
            "batch_id": str(batch_id),
            "article_count": len(article_docs),
            "duration_seconds": duration,
            "retry_count": retry_count
        }

    except Exception as e:
        logger.error(f"[NEWS_GEN] ❌ Generation failed: {str(e)}")

        # Update batch status to failed
        if 'batch_id' in locals():
            await news_batches_collection.update_one(
                {"_id": batch_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "generation_completed_at": datetime.now(cet)
                    }
                }
            )

        # Retry if we haven't exceeded max retries
        if retry_count < MAX_RETRY_COUNT - 1:
            logger.info(f"[NEWS_GEN] Retrying... (attempt {retry_count + 2}/{MAX_RETRY_COUNT})")
            await asyncio.sleep(60)  # Wait 1 minute before retry
            return await generate_daily_news(retry_count + 1)
        else:
            raise NewsGenerationError(f"Failed after {MAX_RETRY_COUNT} attempts: {str(e)}")


async def evaluate_safety_simple(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simple rule-based safety evaluation
    Avoids expensive LLM calls for MVP

    Args:
        articles: List of articles to evaluate

    Returns:
        List of safe articles with safety scores
    """
    # Keywords to avoid (violence, controversy)
    avoid_keywords = [
        "war", "conflict", "attack", "violence", "shooting", "bombing",
        "election", "political", "scandal", "controversy", "protest",
        "crash", "disaster", "death", "killed", "murder", "crime"
    ]

    safe_articles = []

    for article in articles:
        title_lower = article.get("title", "").lower()
        summary_lower = article.get("summary", "").lower()

        # Check for avoid keywords
        has_bad_keywords = any(
            keyword in title_lower or keyword in summary_lower
            for keyword in avoid_keywords
        )

        if not has_bad_keywords:
            # Assign safety scores
            article["safety"] = {
                "violence_score": 1,
                "controversy_score": 2,
                "educational_value": 8,
                "approved": True
            }
            safe_articles.append(article)
        else:
            logger.info(f"[SAFETY] Filtered out: {article.get('title', '')}")

    return safe_articles


async def generate_all_variations_parallel(
    articles: List[Dict[str, Any]],
    batch_id: ObjectId,
    date: datetime
) -> List[Dict[str, Any]]:
    """
    Generate all article variations in parallel
    Uses asyncio.gather for maximum speed

    Args:
        articles: List of safe articles
        batch_id: Batch ID
        date: Generation date

    Returns:
        List of article documents ready for MongoDB
    """
    tasks = []

    for article in articles:
        task = generate_single_article_all_variations(article, batch_id, date)
        tasks.append(task)

    # Run all article generations in parallel
    article_docs = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failed generations
    successful_docs = [
        doc for doc in article_docs
        if not isinstance(doc, Exception)
    ]

    logger.info(f"[NEWS_GEN] Successfully generated {len(successful_docs)}/{len(articles)} articles")

    return successful_docs


async def generate_single_article_all_variations(
    article: Dict[str, Any],
    batch_id: ObjectId,
    date: datetime
) -> Dict[str, Any]:
    """
    Generate all language/level variations for a single article

    Args:
        article: Article metadata
        batch_id: Batch ID
        date: Generation date

    Returns:
        MongoDB document with all variations
    """
    logger.info(f"[NEWS_GEN] Generating variations for: {article.get('title', '')}")

    # Create base document
    doc = {
        "_id": ObjectId(),
        "batch_id": batch_id,
        "date": date,
        "article_index": article.get("article_index", 0),
        "original": {
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "image_url": article.get("image_url"),
            "category": article.get("category", "general"),
            "published_at": article.get("published_at", ""),
            "summary": article.get("summary", "")
        },
        "safety": article.get("safety", {}),
        "variations": {},
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=2)  # TTL: 2 days
    }

    # Generate all variations
    for language in MVP_LANGUAGES:
        doc["variations"][language] = {}

        for level in MVP_LEVELS:
            logger.info(f"[NEWS_GEN]   → {language}/{level}")

            # Generate adaptation (using simple templates for MVP to reduce costs)
            variation = await generate_variation_simple(
                article,
                language,
                level
            )

            doc["variations"][language][level] = variation

    return doc


async def generate_variation_simple(
    article: Dict[str, Any],
    language: str,
    level: str
) -> Dict[str, Any]:
    """
    Generate AI-powered variation using OpenAI (v1.0+ API)

    Args:
        article: Article data
        language: Target language code (en, es, nl)
        level: CEFR level (A2, B1, B2)

    Returns:
        Variation data with AI-generated summary, vocabulary, questions
    """
    from openai import AsyncOpenAI
    import os
    import json

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    title = article.get("title", "")
    summary = article.get("summary", "")

    # Language names for prompts
    language_names = {
        "en": "English",
        "es": "Spanish",
        "nl": "Dutch"
    }

    # Level descriptions
    level_descriptions = {
        "A2": "elementary level (A2) - simple vocabulary, short sentences, present/past tense",
        "B1": "intermediate level (B1) - everyday vocabulary, varied sentences, common idioms",
        "B2": "upper-intermediate level (B2) - advanced vocabulary, complex sentences, nuanced language"
    }

    lang_name = language_names.get(language, "English")
    level_desc = level_descriptions.get(level, level)

    try:
        # Generate adapted content with GPT-4o-mini
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=[
                {
                    "role": "system",
                    "content": f"You are a language learning content creator. Adapt news articles for {lang_name} learners at {level_desc}."
                },
                {
                    "role": "user",
                    "content": f"""Adapt this news article for language learners:

Title: {title}
Original Summary: {summary}

Create:
1. A clear, engaging summary (150-200 words) in {lang_name} appropriate for {level} level
2. Extract 8-10 key vocabulary words with:
   - The word in {lang_name}
   - Translation to English (if not English)
   - Example sentence using the word
   - IPA pronunciation
3. 5 discussion questions that encourage conversation
4. Teaching instructions for an AI tutor

Return as JSON:
{{
  "summary": "adapted summary text",
  "vocabulary": [
    {{"word": "word", "translation": "translation or null", "example": "sentence", "ipa": "/pronunciation/"}}
  ],
  "discussion_questions": ["question1", "question2", ...],
  "ai_instructions": "instructions for AI tutor"
}}"""
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        return {
            "summary": result.get("summary", f"{title}. {summary}"),
            "word_count": len(result.get("summary", "").split()),
            "vocabulary": result.get("vocabulary", []),
            "discussion_questions": result.get("discussion_questions", []),
            "ai_instructions": result.get("ai_instructions", f"Discuss this {level} level news article.")
        }

    except Exception as e:
        logger.error(f"[NEWS_GEN] Error generating AI variation: {str(e)}")
        # Fallback to template if AI fails
        adapted_summary = f"{title}. {summary}"
        return {
            "summary": adapted_summary,
            "word_count": len(adapted_summary.split()),
            "vocabulary": [
                {"word": "news", "translation": None, "example": "I read the news.", "ipa": "/njuːz/"}
            ],
            "discussion_questions": [
                f"What do you think about this news?",
                "Have you heard about this topic?"
            ],
            "ai_instructions": f"Discuss this {level} level news article."
        }


# For testing: Run generation manually
if __name__ == "__main__":
    import asyncio

    async def test_generation():
        result = await generate_daily_news()
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(test_generation())
