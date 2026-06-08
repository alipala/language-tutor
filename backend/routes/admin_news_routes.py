"""
Admin News Routes
Endpoints for managing news generation (admin panel only)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from bson import ObjectId
from bson.errors import InvalidId

from database import news_batches_collection, news_articles_collection
from news_generation.news_generator import generate_daily_news

router = APIRouter()


def _serialize_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Common serializer for admin endpoints — ObjectIds and datetimes → strings."""
    out: Dict[str, Any] = {}
    for k, v in article.items():
        if k == "_id":
            out["_id"] = str(v)
        elif k == "batch_id":
            out["batch_id"] = str(v) if v is not None else None
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


class NewsGenerationRequest(BaseModel):
    """Request body for manual news generation"""
    languages: Optional[List[str]] = ['en', 'es', 'nl', 'pt', 'de', 'fr']
    levels: Optional[List[str]] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    categories: Optional[List[str]] = ['technology', 'science', 'culture', 'sports', 'environment', 'health', 'business']


@router.post("/api/admin/news/generate")
async def trigger_manual_news_generation(request: NewsGenerationRequest):
    """
    Manually trigger news generation on-demand
    Used by admin panel to generate fresh news

    NOTE: This temporarily overrides the MVP_LANGUAGES, MVP_LEVELS,
    and category settings in crew_agents.py
    """
    try:
        print(f"[ADMIN] Manual news generation requested")
        print(f"[ADMIN] Languages: {request.languages}")
        print(f"[ADMIN] Levels: {request.levels}")
        print(f"[ADMIN] Categories: {request.categories}")

        # Trigger generation with selected parameters
        result = await generate_daily_news(
            languages=request.languages,
            levels=request.levels,
            categories=request.categories
        )

        return {
            "success": True,
            "message": "News generated successfully",
            "batch_id": result["batch_id"],
            "article_count": result["article_count"],
            "duration_seconds": result["duration_seconds"],
            "languages_used": request.languages,
            "levels_used": request.levels,
            "categories_used": request.categories,
        }

    except Exception as e:
        print(f"[ADMIN] Error generating news: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"News generation failed: {str(e)}"
        )


@router.get("/api/admin/news/batches")
async def get_news_batches():
    """
    Get news generation batch history
    Shows all past news generation runs
    """
    try:
        # Fetch recent batches (last 30 days)
        batches = []
        async for batch in news_batches_collection.find({}).sort("date", -1).limit(30):
            batches.append({
                "_id": str(batch["_id"]),
                "date": batch["date"].isoformat() if isinstance(batch["date"], datetime) else batch["date"],
                "status": batch.get("status", "unknown"),
                "article_count": batch.get("article_count", 0),
                "generation_started_at": batch.get("generation_started_at").isoformat() if batch.get("generation_started_at") else None,
                "generation_completed_at": batch.get("generation_completed_at").isoformat() if batch.get("generation_completed_at") else None,
                "retry_count": batch.get("retry_count", 0),
            })

        return {
            "success": True,
            "batches": batches,
            "total": len(batches)
        }

    except Exception as e:
        print(f"[ADMIN] Error fetching batches: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch batches: {str(e)}"
        )


@router.delete("/api/admin/news/clear")
async def clear_all_news():
    """
    Clear all news articles and batches
    DANGER: This deletes all news data
    """
    try:
        print("[ADMIN] Clearing all news data...")

        # Delete all batches
        batch_result = await news_batches_collection.delete_many({})
        print(f"[ADMIN] Deleted {batch_result.deleted_count} batches")

        # Delete all articles
        article_result = await news_articles_collection.delete_many({})
        print(f"[ADMIN] Deleted {article_result.deleted_count} articles")

        return {
            "success": True,
            "message": "All news data cleared",
            "batches_deleted": batch_result.deleted_count,
            "articles_deleted": article_result.deleted_count,
        }

    except Exception as e:
        print(f"[ADMIN] Error clearing news: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear news: {str(e)}"
        )


@router.get("/api/admin/news/stats")
async def get_news_statistics():
    """
    Get news generation statistics
    """
    try:
        # Count total batches
        total_batches = await news_batches_collection.count_documents({})

        # Count total articles
        total_articles = await news_articles_collection.count_documents({})

        # Get latest batch
        latest_batch = await news_batches_collection.find_one({}, sort=[("date", -1)])

        # Get successful generation count
        successful_generations = await news_batches_collection.count_documents({"status": "completed"})

        return {
            "success": True,
            "statistics": {
                "total_batches": total_batches,
                "total_articles": total_articles,
                "successful_generations": successful_generations,
                "latest_batch_date": latest_batch["date"].isoformat() if latest_batch else None,
                "latest_batch_status": latest_batch.get("status") if latest_batch else None,
                "latest_batch_article_count": latest_batch.get("article_count", 0) if latest_batch else 0,
            }
        }

    except Exception as e:
        print(f"[ADMIN] Error fetching stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


@router.get("/api/admin/news/today")
async def get_todays_news_admin():
    """
    Get today's news articles (admin endpoint - no auth required)
    Returns all articles for today without authentication
    """
    try:
        from datetime import datetime
        import pytz

        # Get today's date in CET
        cet = pytz.timezone('CET')
        today = datetime.now(cet).date()
        today_start = datetime.combine(today, datetime.min.time())
        today_start = cet.localize(today_start)

        # Convert to UTC naive datetime (MongoDB stores dates as UTC naive)
        today_start_utc = today_start.astimezone(pytz.utc).replace(tzinfo=None)

        # Find articles for today
        articles = []
        async for article in news_articles_collection.find({"date": today_start_utc}).sort("article_index", 1):
            articles.append({
                "_id": str(article["_id"]),
                "article_index": article.get("article_index", 0),
                "date": article["date"].isoformat() if isinstance(article["date"], datetime) else article["date"],
                "original": article.get("original", {}),
                "variations": article.get("variations", {}),
            })

        return {
            "success": True,
            "articles": articles,
            "count": len(articles),
            "date": today_start.isoformat()
        }

    except Exception as e:
        print(f"[ADMIN] Error fetching today's news: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch today's news: {str(e)}"
        )


# ===========================================================================
# Article CRUD endpoints (Phase 4 — admin panel B integration)
#
# These endpoints let the admin panel browse the news_articles collection,
# inspect a single article with all 6×6 variations, edit individual fields,
# and delete a single article. No new collection, no schema change — they
# operate on the existing news_articles documents the news generator writes.
#
# Endpoints:
#   GET    /api/admin/news/articles                 — paginated list
#   GET    /api/admin/news/articles/{id}            — full document
#   PATCH  /api/admin/news/articles/{id}            — edit original.* + variations[lang][level].*
#   DELETE /api/admin/news/articles/{id}            — delete one
# ===========================================================================


def _parse_object_id(id_str: str) -> ObjectId:
    """Parse a hex string into ObjectId; raise 400 on bad input."""
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid article id: {id_str}")


class OriginalPatch(BaseModel):
    """Editable fields inside ``original``. All optional — only sent fields update."""
    title: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    image_url: Optional[str] = None  # explicit "" to clear; None means "don't change"
    category: Optional[str] = None
    published_at: Optional[str] = None
    summary: Optional[str] = None


class VocabularyItemPatch(BaseModel):
    word: str
    translation: Optional[str] = None
    example: str
    ipa: Optional[str] = None


class VariationPatch(BaseModel):
    """Editable fields inside a single ``variations[lang][level]`` cell."""
    summary: Optional[str] = None
    vocabulary: Optional[List[VocabularyItemPatch]] = None
    discussion_questions: Optional[List[str]] = None
    ai_instructions: Optional[str] = None
    word_count: Optional[int] = None


class VariationKey(BaseModel):
    """Composite key for targeted variation edit."""
    language: str = Field(..., description="One of: en, es, nl, pt, de, fr")
    level: str = Field(..., description="One of: A1, A2, B1, B2, C1, C2")


class ArticlePatchRequest(BaseModel):
    """
    Patch payload. Use ``original`` to edit the article's top-level metadata.
    Use ``variation`` + ``variation_key`` to edit one (lang, level) cell at a time.
    Both blocks are optional; sending neither is a 400.
    """
    original: Optional[OriginalPatch] = None
    variation_key: Optional[VariationKey] = None
    variation: Optional[VariationPatch] = None


@router.get("/api/admin/news/articles")
async def list_articles(
    category: Optional[str] = Query(None, description="Filter by original.category (slot_id)"),
    batch_id: Optional[str] = Query(None, description="Filter by batch_id"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    skip: int = Query(0, ge=0, description="Offset"),
    sort: str = Query("-date", description="Sort field: '-date', 'date', 'article_index'"),
):
    """
    Paginated browsable list of articles. Returns the list view metadata
    (no full variations payload — use the detail endpoint for that).
    """
    try:
        query: Dict[str, Any] = {}
        if category:
            query["original.category"] = category
        if batch_id:
            try:
                query["batch_id"] = ObjectId(batch_id)
            except (InvalidId, TypeError):
                raise HTTPException(status_code=400, detail=f"Invalid batch_id: {batch_id}")

        # Sort key parsing — '-field' means descending.
        if sort.startswith("-"):
            sort_field, direction = sort[1:], -1
        else:
            sort_field, direction = sort, 1
        if sort_field not in {"date", "article_index", "created_at"}:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_field}")

        total = await news_articles_collection.count_documents(query)

        cursor = news_articles_collection.find(
            query,
            {
                "_id": 1,
                "batch_id": 1,
                "date": 1,
                "article_index": 1,
                "original": 1,
                "safety": 1,
                "created_at": 1,
            },
        ).sort(sort_field, direction).skip(skip).limit(limit)

        articles = [_serialize_article(a) async for a in cursor]

        return {
            "success": True,
            "articles": articles,
            "count": len(articles),
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN] Error listing articles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list articles: {e}")


@router.get("/api/admin/news/articles/{article_id}")
async def get_article(article_id: str):
    """Full single-article document including all 6×6 variations."""
    oid = _parse_object_id(article_id)
    article = await news_articles_collection.find_one({"_id": oid})
    if article is None:
        raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")
    return {"success": True, "article": _serialize_article(article)}


@router.patch("/api/admin/news/articles/{article_id}")
async def patch_article(article_id: str, body: ArticlePatchRequest):
    """
    Edit an article. Two independent edit modes:

      - ``original``: any subset of original.* fields. Only sent fields
        overwrite; omitted fields are untouched.
      - ``variation`` + ``variation_key``: edit a single (lang, level) cell.
        Same partial-update rule.

    At least one of the two must be supplied; otherwise 400.
    """
    if body.original is None and body.variation is None:
        raise HTTPException(
            status_code=400,
            detail="Patch must include 'original' and/or 'variation' (with variation_key).",
        )
    if (body.variation is None) != (body.variation_key is None):
        raise HTTPException(
            status_code=400,
            detail="'variation' and 'variation_key' must both be present or both absent.",
        )

    oid = _parse_object_id(article_id)

    # Confirm the article exists before constructing the update — Mongo's
    # update_one with no match would silently no-op.
    existing = await news_articles_collection.find_one({"_id": oid}, {"_id": 1})
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")

    set_ops: Dict[str, Any] = {}

    if body.original is not None:
        for field, value in body.original.model_dump(exclude_unset=True).items():
            set_ops[f"original.{field}"] = value

    if body.variation is not None and body.variation_key is not None:
        lang = body.variation_key.language
        level = body.variation_key.level
        if lang not in {"en", "es", "nl", "pt", "de", "fr"}:
            raise HTTPException(status_code=400, detail=f"Invalid language: {lang}")
        if level not in {"A1", "A2", "B1", "B2", "C1", "C2"}:
            raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
        for field, value in body.variation.model_dump(exclude_unset=True).items():
            # vocabulary is a list of pydantic objects — dump to dicts.
            if field == "vocabulary" and value is not None:
                value = [v if isinstance(v, dict) else v for v in value]
            set_ops[f"variations.{lang}.{level}.{field}"] = value

    if not set_ops:
        # Empty patch (both blocks were present but everything was unset).
        raise HTTPException(status_code=400, detail="No fields to update.")

    set_ops["updated_at"] = datetime.utcnow()

    result = await news_articles_collection.update_one({"_id": oid}, {"$set": set_ops})

    updated = await news_articles_collection.find_one({"_id": oid})
    return {
        "success": True,
        "modified_count": result.modified_count,
        "fields_set": list(set_ops.keys()),
        "article": _serialize_article(updated) if updated else None,
    }


@router.delete("/api/admin/news/articles/{article_id}")
async def delete_article(article_id: str):
    """Delete one article. The batch row is NOT decremented — batch.article_count remains as the historical count."""
    oid = _parse_object_id(article_id)
    result = await news_articles_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")
    return {"success": True, "deleted_count": result.deleted_count, "article_id": article_id}


@router.get("/api/admin/news/categories")
async def list_categories():
    """
    Distinct ``original.category`` values currently in the collection, with
    counts. Helps the admin filter UI populate a dropdown with the
    real-world distribution rather than a hardcoded list.
    """
    try:
        pipeline = [
            {"$group": {"_id": "$original.category", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        results = []
        async for row in news_articles_collection.aggregate(pipeline):
            results.append({"category": row["_id"], "count": row["count"]})
        return {"success": True, "categories": results}
    except Exception as e:
        print(f"[ADMIN] Error listing categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {e}")
