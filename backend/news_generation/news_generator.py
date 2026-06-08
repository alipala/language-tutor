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
from news_generation.config import is_multi_provider_enabled
from news_generation.providers import NewsApiProvider
from news_generation.providers._common import backfill_images_for_articles
from news_generation.orchestrator import (
    fetch_candidates_multi_provider,
    NEWS_VARIATION_CONCURRENCY,
)
from news_generation.catalog import CATALOG


def _filter_catalog(slot_ids):
    """
    Return the subset of the 20-slot CATALOG whose ``slot_id`` is in
    ``slot_ids``. Preserves catalog order (specific → general) so
    claiming-order semantics still hold. Returns an empty list if no
    slot_id matches — caller decides what to do with that.
    """
    if not slot_ids:
        return None
    requested = {s.strip().lower() for s in slot_ids if isinstance(s, str)}
    return [d for d in CATALOG if d.slot_id.lower() in requested]

logger = logging.getLogger(__name__)

# Configuration
MAX_RETRY_COUNT = 3
GENERATION_TIMEOUT = 7200  # 2 hours


class NewsGenerationError(Exception):
    """Custom exception for news generation failures"""
    pass


async def generate_daily_news(
    retry_count: int = 0,
    languages: List[str] = None,
    levels: List[str] = None,
    categories: List[str] = None
) -> Dict[str, Any]:
    """
    Main function to generate daily news content
    Orchestrates all agents and saves to MongoDB

    Args:
        retry_count: Current retry attempt (0-indexed)
        languages: List of language codes to generate (defaults to MVP_LANGUAGES)
        levels: List of CEFR levels to generate (defaults to MVP_LEVELS)
        categories: List of news categories to search (defaults to MVP categories)

    Returns:
        Generation statistics and status

    Raises:
        NewsGenerationError: If generation fails after all retries
    """
    # Use provided parameters or defaults
    if languages is None:
        languages = MVP_LANGUAGES
    if levels is None:
        levels = MVP_LEVELS

    logger.info(f"[NEWS_GEN] Starting daily news generation (attempt {retry_count + 1}/{MAX_RETRY_COUNT})")
    logger.info(f"[NEWS_GEN] Languages: {languages}")
    logger.info(f"[NEWS_GEN] Levels: {levels}")
    logger.info(f"[NEWS_GEN] Categories: {categories or 'default MVP categories'}")

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
        # Provider seam:
        #   Flag OFF: NewsApiProvider — wraps get_diverse_news() verbatim;
        #             keeps the live pipeline byte-identical to pre-Phase-1.
        #   Flag ON:  multi-provider orchestrator (NewsData → Google News RSS →
        #             GDELT fallback chain across the 20-category catalog).
        #             Returns the same 8-key shape as get_diverse_news, drops
        #             into the existing safety + variation pipeline unchanged.
        # The flag-ON path treats the ``categories`` argument as an optional
        # **subset filter** over the 20-slot catalog: if the admin supplied
        # specific slot_ids (e.g. ['technology', 'science', 'ai']) we honor
        # that — only those categories are fetched and variations are
        # generated for them. If categories is None/empty, the full
        # 20-catalog runs (default cron behavior).
        if is_multi_provider_enabled():
            sub_catalog = _filter_catalog(categories) if categories else None
            if sub_catalog is not None and len(sub_catalog) == 0:
                # Admin sent ``categories`` but none matched the catalog —
                # fall back to the full catalog rather than producing zero
                # articles. Log loudly so the admin notices the typo.
                logger.warning(
                    f"[NEWS_GEN] Flag-ON requested categories={categories!r} but none "
                    f"matched the catalog; running the full 20-category catalog instead."
                )
                sub_catalog = None
            if sub_catalog is not None:
                logger.info(f"[NEWS_GEN] Flag-ON catalog filter: {[d.slot_id for d in sub_catalog]}")
            candidate_articles = await fetch_candidates_multi_provider(catalog=sub_catalog)
        else:
            candidate_articles = NewsApiProvider().fetch(exclude_urls=used_urls, categories=categories)

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

        # Phase 4 bug fix: the MVP_ARTICLE_COUNT=5 cap was originally written for
        # the flag-OFF NewsAPI path (which targets 5 articles/day). When the flag
        # is ON, the multi-provider orchestrator deliberately produces ~120
        # articles via the 20-category catalog (Phase 3). Capping at 5 here
        # silently discards 115 of them. The cap is now only applied on the
        # flag-OFF path; flag-ON keeps whatever the orchestrator returned.
        if not is_multi_provider_enabled():
            safe_articles = safe_articles[:MVP_ARTICLE_COUNT]

        # Step 4: AGENTS 3 & 4 - Parallel generation for all variations
        logger.info("[NEWS_GEN] STEP 3: Generating adaptations (parallel processing)...")

        # Calculate total variations
        total_variations = len(safe_articles) * len(languages) * len(levels)
        logger.info(f"[NEWS_GEN] Generating {total_variations} variations ({len(safe_articles)} articles × {len(languages)} langs × {len(levels)} levels)")

        if is_multi_provider_enabled():
            # ----------------------------------------------------------------
            # Phase 4 Task 6 — production-grade progressive per-category write.
            # ----------------------------------------------------------------
            # Instead of one big all-or-nothing 4,320-call fan-out followed by
            # one giant insert_many at the end (the original MVP design), we
            # process the safe articles **category by category** in catalog
            # order:
            #
            #   for each category:
            #     generate that category's 6 article × 36 cell variations
            #     insert_many ONLY this category's ~6 docs
            #     $inc batch.article_count and $addToSet batch.completed_categories
            #
            # Benefits:
            #   • User starts seeing news ~1-2 min after run begins (the first
            #     category's batch lands), not 15 min later as before.
            #   • One category's variation failure does not abort the others.
            #   • The batch row's article_count grows monotonically — anyone
            #     reading /api/news/today during the run gets the partial set
            #     they're entitled to.
            #   • The 8-key article doc shape and the news_articles collection
            #     schema are unchanged — only batch row gets two operational
            #     metadata fields (completed_categories, failed_categories)
            #     that are never surfaced via /api/news/today.
            article_docs = await _progressive_write_by_category(
                safe_articles,
                batch_id,
                today_start_utc,
                languages=languages,
                levels=levels,
            )
        else:
            # Flag-OFF: original all-or-nothing path. Byte-identical to Phase 1
            # baseline (snapshot tests still green).
            article_docs = await generate_all_variations_parallel(
                safe_articles,
                batch_id,
                today_start_utc,
                languages=languages,
                levels=levels
            )

            # Step 5: Save to MongoDB (flag-OFF only — progressive path inserts
            # per-category during generation).
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
            return await generate_daily_news(retry_count + 1, languages=languages, levels=levels, categories=categories)
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
        # Handle None values explicitly
        title = article.get("title") or ""
        summary = article.get("summary") or ""
        title_lower = title.lower()
        summary_lower = summary.lower()

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


async def _progressive_write_by_category(
    safe_articles: List[Dict[str, Any]],
    batch_id: ObjectId,
    date: datetime,
    languages: List[str],
    levels: List[str],
) -> List[Dict[str, Any]]:
    """
    Phase 4 progressive writer (flag-ON only).

    Groups ``safe_articles`` by ``original['category']`` (which the orchestrator
    has already stamped with the canonical slot_id) and runs **all categories
    in parallel**. Inside each category task:
        1. generates that group's variations (wrapped in the shared
           NEWS_VARIATION_CONCURRENCY semaphore so total in-flight OpenAI
           calls across ALL categories stays bounded — this is the cap that
           protects us from rate-limit cascades),
        2. atomically claims the next block of article_index values from a
           single counter (so indexes are globally unique across the day),
        3. inserts only those ~6 docs into news_articles,
        4. increments batch.article_count and appends to
           batch.completed_categories.

    Parallel execution model (the v2 design after Ali's feedback):
        Sequential (v1, 35 min):   cat1 → cat2 → ... → cat20
        Parallel   (v2, ~5 min):   all 20 cats kicked off at once;
                                   semaphore=15 caps simultaneous variation
                                   loops across the whole batch.

    Returns the flat list of every doc that was successfully written.
    Failure isolation: each category is its own asyncio task wrapped in
    return_exceptions semantics — one task raising does not abort the others.
    """
    from collections import OrderedDict

    # Catalog-ordered grouping. The orchestrator already returns articles in
    # catalog order (specific → general) and the orchestrator stamps
    # article['category'] with the slot_id, so this groupby preserves that
    # order. Order matters here only for *deterministic article_index
    # assignment*: even though categories run in parallel, the index counter
    # is claimed atomically so the final indexes are stable.
    groups: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for art in safe_articles:
        slot_id = art.get("category") or "general"
        groups.setdefault(slot_id, []).append(art)

    # ONE shared semaphore across all parallel category tasks. This is the
    # global cap on simultaneous in-flight OpenAI calls regardless of how
    # many categories are running at once.
    sem = asyncio.Semaphore(NEWS_VARIATION_CONCURRENCY)

    # Shared index counter. asyncio is single-threaded so a list-index + lock
    # gives us a deterministic global counter without races.
    index_counter = [0]
    index_lock = asyncio.Lock()

    logger.info(
        f"[NEWS_GEN] Progressive write (PARALLEL): launching {len(groups)} category tasks, "
        f"{sum(len(g) for g in groups.values())} articles total, "
        f"variation semaphore cap={NEWS_VARIATION_CONCURRENCY}"
    )

    async def _run_one_category(slot_id: str, group_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """One category's full pipeline: variations → claim indexes → insert → batch tag."""
        if not group_articles:
            return []
        logger.info(f"[NEWS_GEN] → category '{slot_id}': starting (n={len(group_articles)})")
        try:
            docs = await generate_all_variations_parallel(
                group_articles,
                batch_id,
                date,
                languages=languages,
                levels=levels,
                semaphore=sem,  # shared cap across all parallel categories
            )
            if not docs:
                logger.warning(f"[NEWS_GEN] category '{slot_id}': 0 docs produced")
                await news_batches_collection.update_one(
                    {"_id": batch_id},
                    {"$addToSet": {"failed_categories": slot_id}},
                )
                return []

            # Atomically claim a block of N indexes so concurrent categories
            # don't collide. asyncio.Lock + bumping the counter is a tiny
            # critical section — no real contention.
            async with index_lock:
                base = index_counter[0]
                index_counter[0] += len(docs)
            for offset, d in enumerate(docs):
                d["article_index"] = base + offset

            # Phase 4 image backfill: for any doc whose provider didn't return
            # an image (typical for Google News RSS aggregator URLs and GDELT
            # rows), scrape og:image / twitter:image from the article URL.
            # Mutates docs in place; failure is silent (image stays None).
            # See providers/_common.backfill_images_for_articles for the
            # bounded-concurrency implementation.
            try:
                # Adapt the doc shape (has nested ``original``) to the helper's
                # 8-key flat shape by passing references to the ``original``
                # sub-dicts directly. The helper only reads url + image_url
                # and writes image_url, so the in-place mutation is sufficient.
                originals = [d.get("original") or {} for d in docs]
                await backfill_images_for_articles(originals, max_concurrency=8)
            except Exception as e:  # never block the insert on backfill issues
                logger.warning(f"[NEWS_GEN] image backfill skipped for '{slot_id}': {e}")

            await news_articles_collection.insert_many(docs)
            await news_batches_collection.update_one(
                {"_id": batch_id},
                {
                    "$inc": {"article_count": len(docs)},
                    "$addToSet": {"completed_categories": slot_id},
                },
            )
            logger.info(f"[NEWS_GEN] ✅ category '{slot_id}': wrote {len(docs)} docs")
            return docs
        except Exception as e:
            logger.exception(f"[NEWS_GEN] ❌ category '{slot_id}' failed: {type(e).__name__}: {e}")
            try:
                await news_batches_collection.update_one(
                    {"_id": batch_id},
                    {"$addToSet": {"failed_categories": slot_id}},
                )
            except Exception:
                pass
            return []

    # Launch one task per category, all in parallel. The shared semaphore
    # inside generate_all_variations_parallel keeps in-flight OpenAI calls
    # bounded — adding more categories doesn't multiply OpenAI concurrency,
    # only spreads the same 15 slots across more pipelines.
    tasks = [_run_one_category(slot_id, group) for slot_id, group in groups.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten and filter exceptions defensively (per-task try/except above
    # should catch everything; this is belt-and-braces).
    all_written: List[Dict[str, Any]] = []
    for r in results:
        if isinstance(r, list):
            all_written.extend(r)

    logger.info(
        f"[NEWS_GEN] Progressive write complete: {len(all_written)} docs across "
        f"{len(groups)} categories (parallel run)"
    )
    return all_written


async def generate_all_variations_parallel(
    articles: List[Dict[str, Any]],
    batch_id: ObjectId,
    date: datetime,
    languages: List[str] = None,
    levels: List[str] = None,
    semaphore: "asyncio.Semaphore" = None,
) -> List[Dict[str, Any]]:
    """
    Generate all article variations in parallel.

    Phase 4: a ``semaphore`` (default ``NEWS_VARIATION_CONCURRENCY=15``) bounds
    the number of articles whose variation loops are in flight simultaneously.
    Each article still runs its 6×6 cells sequentially inside
    ``generate_single_article_all_variations`` — so peak in-flight OpenAI
    calls ≈ semaphore capacity, not articles × langs × levels. This protects
    against OpenAI rate-limit cascades on the at-scale flag-ON run (~4,320
    total calls when the orchestrator delivers ~120 articles).

    Per-article failure isolation is preserved by the existing
    ``asyncio.gather(return_exceptions=True)`` + Exception-filter pattern:
    one article exploding does not abort the batch. Per-(lang, level) cell
    failure is absorbed inside ``generate_variation_simple`` via its own
    try/except → template fallback.

    Args:
        articles: List of safe articles
        batch_id: Batch ID
        date: Generation date
        languages: List of language codes (defaults to MVP_LANGUAGES)
        levels: List of CEFR levels (defaults to MVP_LEVELS)
        semaphore: optional bound on concurrent article variation loops.
            When ``None``, defaults to ``asyncio.Semaphore(NEWS_VARIATION_CONCURRENCY)``.

    Returns:
        List of article documents ready for MongoDB
    """
    if languages is None:
        languages = MVP_LANGUAGES
    if levels is None:
        levels = MVP_LEVELS
    if semaphore is None:
        semaphore = asyncio.Semaphore(NEWS_VARIATION_CONCURRENCY)

    tasks = []

    for article in articles:
        task = _generate_single_article_with_semaphore(
            article, batch_id, date, languages=languages, levels=levels,
            semaphore=semaphore,
        )
        tasks.append(task)

    # Run all article generations in parallel, semaphore-bounded.
    article_docs = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failed generations (per-article isolation).
    successful_docs = [
        doc for doc in article_docs
        if not isinstance(doc, Exception)
    ]
    failed_count = len(article_docs) - len(successful_docs)
    if failed_count:
        # Log per-article failures so the Phase-4 batch report can account
        # for them without losing the rest of the batch.
        for d in article_docs:
            if isinstance(d, Exception):
                logger.warning(f"[NEWS_GEN] Article variation failed: {type(d).__name__}: {d}")

    logger.info(
        f"[NEWS_GEN] Successfully generated {len(successful_docs)}/{len(articles)} articles "
        f"(failed: {failed_count})"
    )

    return successful_docs


async def _generate_single_article_with_semaphore(
    article: Dict[str, Any],
    batch_id: ObjectId,
    date: datetime,
    *,
    languages: List[str],
    levels: List[str],
    semaphore: "asyncio.Semaphore",
) -> Dict[str, Any]:
    """Wrap ``generate_single_article_all_variations`` with the concurrency cap."""
    async with semaphore:
        return await generate_single_article_all_variations(
            article, batch_id, date, languages=languages, levels=levels,
        )


async def generate_single_article_all_variations(
    article: Dict[str, Any],
    batch_id: ObjectId,
    date: datetime,
    languages: List[str] = None,
    levels: List[str] = None
) -> Dict[str, Any]:
    """
    Generate all language/level variations for a single article

    Args:
        article: Article metadata
        batch_id: Batch ID
        date: Generation date
        languages: List of language codes (defaults to MVP_LANGUAGES)
        levels: List of CEFR levels (defaults to MVP_LEVELS)

    Returns:
        MongoDB document with all variations
    """
    if languages is None:
        languages = MVP_LANGUAGES
    if levels is None:
        levels = MVP_LEVELS

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
    for language in languages:
        doc["variations"][language] = {}

        for level in levels:
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
        "nl": "Dutch",
        "pt": "Portuguese",
        "de": "German",
        "fr": "French"
    }

    # Level descriptions
    level_descriptions = {
        "A1": "beginner level (A1) - very basic vocabulary, very short sentences, present tense only",
        "A2": "elementary level (A2) - simple vocabulary, short sentences, present/past tense",
        "B1": "intermediate level (B1) - everyday vocabulary, varied sentences, common idioms",
        "B2": "upper-intermediate level (B2) - advanced vocabulary, complex sentences, nuanced language",
        "C1": "advanced level (C1) - sophisticated vocabulary, complex grammatical structures, nuanced expressions",
        "C2": "proficiency level (C2) - native-like vocabulary, highly complex sentences, subtle idiomatic language"
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
