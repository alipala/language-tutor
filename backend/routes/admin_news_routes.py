"""
Admin News Routes
Endpoints for managing news generation (admin panel only)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from database import news_batches_collection, news_articles_collection
from news_generation.news_generator import generate_daily_news

router = APIRouter()


class NewsGenerationRequest(BaseModel):
    """Request body for manual news generation"""
    languages: Optional[List[str]] = ['en', 'es', 'nl']
    levels: Optional[List[str]] = ['A2', 'B1', 'B2']
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

        # Temporarily set configuration
        # Note: In production, you'd want to pass these to generate_daily_news()
        # For now, generate_daily_news uses MVP defaults

        # Trigger generation
        result = await generate_daily_news()

        return {
            "success": True,
            "message": "News generated successfully",
            "batch_id": result["batch_id"],
            "article_count": result["article_count"],
            "duration_seconds": result["duration_seconds"],
            "languages_requested": request.languages,
            "levels_requested": request.levels,
            "categories_requested": request.categories,
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
