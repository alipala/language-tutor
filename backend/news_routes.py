"""
Daily News Tab Feature - API Routes
Provides endpoints for fetching daily news content adapted for language learners
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import pytz
from bson import ObjectId
import logging

from auth import get_current_user
from models import UserResponse
from database import (
    news_batches_collection,
    news_articles_collection,
    learning_plans_collection
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news", tags=["news"])

# Supported languages and levels
SUPPORTED_LANGUAGES = ["en", "es", "nl", "pt", "de", "fr"]  # English, Spanish, Dutch, Portuguese, German, French
SUPPORTED_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]  # All 6 CEFR levels

class NewsArticleMetadata(BaseModel):
    """Metadata for a news article (returned in list view)"""
    id: str
    title: str
    translated_title: Optional[str] = None
    image_url: Optional[str] = None
    category: str
    source: str
    article_index: int

class NewsList(BaseModel):
    """Response for today's news list"""
    date: str
    articles: List[NewsArticleMetadata]
    recommended_level: str
    fallback_used: bool
    available_languages: List[str]

class VocabularyItem(BaseModel):
    """A single vocabulary word with translation and example"""
    word: str
    translation: Optional[str] = None
    example: str
    ipa: Optional[str] = None

class NewsContent(BaseModel):
    """Full content for a specific article/language/level"""
    news_id: str
    language: str
    level: str
    original: Dict[str, Any]
    summary: str
    vocabulary: List[VocabularyItem]
    discussion_questions: List[str]
    ai_instructions: str
    word_count: int

@router.get("/today", response_model=NewsList)
async def get_todays_news(
    language: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get today's news list (metadata only) - FAST <100ms
    Returns list of news articles with basic metadata
    Includes user's recommended level based on learning plan
    """
    try:
        logger.info(f"[NEWS] Fetching today's news for user {current_user.id}")

        # Get current date in CET (Central European Time)
        cet = pytz.timezone('CET')
        now = datetime.now(cet)
        today = now.date()
        today_start = datetime.combine(today, datetime.min.time())
        today_start = cet.localize(today_start)

        logger.info(f"[NEWS] Query date: {today} (CET)")

        # Check if today's news batch exists.
        # Phase 4 progressive write: a batch starts at status=in_progress and
        # ticks article_count up category-by-category as ~120 articles land.
        # We serve as soon as ANY articles are written for the day, not only
        # after the full batch completes — otherwise the user sees nothing
        # for 15-50 min after the cron starts, defeating the progressive
        # design's whole point. ``completed`` is still the happy path, but
        # ``in_progress`` with article_count > 0 is also served.
        batch = await news_batches_collection.find_one(
            {"date": {"$gte": today_start}}
        )

        fallback_used = False
        query_date = today_start

        def _batch_has_visible_articles(b):
            if not b:
                return False
            status = b.get("status")
            if status == "completed":
                return True
            if status == "in_progress" and (b.get("article_count") or 0) > 0:
                return True
            return False

        if not _batch_has_visible_articles(batch):
            # Try yesterday's news as fallback
            logger.warning(f"[NEWS] Today's news not available, falling back to yesterday")
            yesterday_start = today_start - timedelta(days=1)
            batch = await news_batches_collection.find_one(
                {"date": {"$gte": yesterday_start}, "status": "completed"}
            )
            if batch:
                fallback_used = True
                query_date = yesterday_start
            else:
                logger.error(f"[NEWS] No news available for today or yesterday")
                return NewsList(
                    date=today.isoformat(),
                    articles=[],
                    recommended_level="B1",
                    fallback_used=False,
                    available_languages=SUPPORTED_LANGUAGES
                )

        # Query today's articles (or yesterday's if fallback)
        # Include variations so we can surface translated_title when language param is given
        projection = {
            "_id": 1,
            "original.title": 1,
            "original.image_url": 1,
            "original.category": 1,
            "original.source": 1,
            "article_index": 1,
        }
        if language:
            projection[f"variations.{language}"] = 1

        articles_cursor = news_articles_collection.find(
            {"date": {"$gte": query_date}},
            projection
        ).sort("article_index", 1)

        # Phase 4 Task 2A: raised from 20 → 200 so the flag-ON multi-provider
        # path (≤120 articles/day) surfaces in full. Flag-safe: flag-OFF still
        # writes ≤5 articles/day, so the same find().to_list(200) returns ≤5.
        articles_raw = await articles_cursor.to_list(200)

        # Transform to response format
        articles = []
        for article in articles_raw:
            translated_title = None
            if language:
                lang_variations = (article.get("variations") or {}).get(language, {})
                # translated_title is stored per-level; pick any available level
                for lvl_data in lang_variations.values():
                    if isinstance(lvl_data, dict) and lvl_data.get("translated_title"):
                        translated_title = lvl_data["translated_title"]
                        break
            articles.append(NewsArticleMetadata(
                id=str(article["_id"]),
                title=article["original"]["title"],
                translated_title=translated_title,
                image_url=article["original"].get("image_url"),
                category=article["original"]["category"],
                source=article["original"]["source"],
                article_index=article["article_index"]
            ))

        # Get user's recommended level from their learning plan
        learning_plan = await learning_plans_collection.find_one(
            {"user_id": str(current_user.id)},
            sort=[("created_at", -1)]
        )

        recommended_level = "B1"  # Default
        if learning_plan and learning_plan.get("proficiency_level"):
            level = learning_plan["proficiency_level"]
            # Map to MVP levels if needed
            if level in SUPPORTED_LEVELS:
                recommended_level = level
            elif level == "A1":
                recommended_level = "A2"  # Upgrade A1 to A2
            elif level in ["C1", "C2"]:
                recommended_level = "B2"  # Downgrade C1/C2 to B2

        logger.info(f"[NEWS] Returning {len(articles)} articles, recommended level: {recommended_level}")

        return NewsList(
            date=today.isoformat(),
            articles=articles,
            recommended_level=recommended_level,
            fallback_used=fallback_used,
            available_languages=SUPPORTED_LANGUAGES
        )

    except Exception as e:
        logger.error(f"[NEWS] Error fetching today's news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}"
        )

@router.get("/{news_id}/content", response_model=NewsContent)
async def get_news_content(
    news_id: str,
    language: str,
    level: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get full content for specific article, language, and level
    Returns adapted summary, vocabulary, discussion questions, and AI instructions
    Target: <200ms (single MongoDB query)
    """
    try:
        logger.info(f"[NEWS] Fetching content for news_id={news_id}, language={language}, level={level}")

        # Validate parameters
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid language. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )

        if level not in SUPPORTED_LEVELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid level. Supported: {', '.join(SUPPORTED_LEVELS)}"
            )

        # Convert news_id to ObjectId
        try:
            news_object_id = ObjectId(news_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid news ID format"
            )

        # Query specific variation (efficient single-doc query)
        article = await news_articles_collection.find_one(
            {"_id": news_object_id},
            {
                f"variations.{language}.{level}": 1,
                "original": 1
            }
        )

        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Extract the specific variation
        try:
            variation = article["variations"][language][level]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content not available for {language}/{level}"
            )

        logger.info(f"[NEWS] Content fetched successfully")

        # Build vocabulary defensively. The news generator occasionally emits
        # a malformed variation where non-dict junk (e.g. leaked
        # discussion_questions strings) ends up in the vocabulary list. A raw
        # `VocabularyItem(**vocab)` then throws "argument after ** must be a
        # mapping, not str" and 500s the WHOLE article for that language/level.
        # We instead skip any element that isn't a well-formed dict, so a bad
        # word never takes down the article — the user just sees fewer words.
        vocabulary_items = []
        for vocab in (variation.get("vocabulary") or []):
            if not isinstance(vocab, dict):
                logger.warning(
                    f"[NEWS] Skipping malformed vocab item in {news_id} {language}/{level}: "
                    f"{type(vocab).__name__} {str(vocab)[:60]!r}"
                )
                continue
            try:
                vocabulary_items.append(VocabularyItem(**vocab))
            except Exception as ve:
                logger.warning(
                    f"[NEWS] Skipping unparseable vocab item in {news_id} {language}/{level}: {ve}"
                )

        # Inject translated_title into original dict so mobile can use it.
        # Falls back to original.title for articles generated before this field existed.
        original_with_translation = dict(article["original"])
        if variation.get("translated_title"):
            original_with_translation["translated_title"] = variation["translated_title"]

        return NewsContent(
            news_id=news_id,
            language=language,
            level=level,
            original=original_with_translation,
            summary=variation["summary"],
            vocabulary=vocabulary_items,
            discussion_questions=variation["discussion_questions"],
            ai_instructions=variation["ai_instructions"],
            word_count=variation.get("word_count", 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NEWS] Error fetching news content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news content: {str(e)}"
        )

class StartConversationRequest(BaseModel):
    """Request to start a news conversation"""
    news_id: str
    language: str
    level: str

class ConversationContext(BaseModel):
    """Context data for news conversation"""
    type: str = "news_discussion"
    news_id: str
    language: str
    level: str
    vocabulary: List[VocabularyItem]
    discussion_questions: List[str]
    ai_instructions: str
    news_title: str
    news_summary: str
    word_count: int

@router.post("/start-conversation")
async def start_news_conversation(
    request: StartConversationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Start a news conversation
    Integrates with existing realtime conversation system
    Returns session_id and conversation context for frontend
    """
    try:
        logger.info(f"[NEWS] Starting conversation for news_id={request.news_id}")

        # Get news content
        content = await get_news_content(
            request.news_id,
            request.language,
            request.level,
            current_user
        )

        # Generate unique session ID for news conversation
        import uuid
        session_id = f"news_{request.news_id}_{uuid.uuid4()}"

        # Create conversation context
        conversation_context = ConversationContext(
            type="news_discussion",
            news_id=request.news_id,
            language=request.language,
            level=request.level,
            vocabulary=content.vocabulary,
            discussion_questions=content.discussion_questions,
            ai_instructions=content.ai_instructions,
            news_title=content.original["title"],
            news_summary=content.summary,
            word_count=content.word_count
        )

        logger.info(f"[NEWS] Conversation session created: {session_id}")

        # TODO: Integrate with existing /api/realtime/token endpoint
        # For now, return the context and session_id
        # Frontend will use these to initialize the conversation

        return {
            "session_id": session_id,
            "conversation_context": conversation_context.dict(),
            "news_content": content.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NEWS] Error starting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )

@router.get("/generation-status")
async def get_generation_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get status of today's news generation
    Used for monitoring and debugging
    """
    try:
        cet = pytz.timezone('CET')
        today_start = datetime.combine(datetime.now(cet).date(), datetime.min.time())
        today_start = cet.localize(today_start)

        batch = await news_batches_collection.find_one(
            {"date": {"$gte": today_start}}
        )

        if not batch:
            return {
                "status": "not_started",
                "date": today_start.isoformat(),
                "message": "Today's news generation has not started"
            }

        return {
            "status": batch.get("status", "unknown"),
            "date": batch["date"].isoformat() if isinstance(batch["date"], datetime) else batch["date"],
            "article_count": batch.get("article_count", 0),
            "generation_started_at": batch.get("generation_started_at"),
            "generation_completed_at": batch.get("generation_completed_at"),
            "generation_duration_seconds": batch.get("generation_duration_seconds"),
            "retry_count": batch.get("retry_count", 0)
        }

    except Exception as e:
        logger.error(f"[NEWS] Error fetching generation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch generation status: {str(e)}"
        )
