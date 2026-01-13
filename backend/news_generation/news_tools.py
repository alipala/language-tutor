"""
Tools for News Search Agent
Provides web search and news API capabilities
"""

import os
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# MVP: We'll use NewsAPI.org (free tier: 100 requests/day)
# You need to get a free API key from: https://newsapi.org/register
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def search_news_api(query: str = None, category: str = None, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Search for news using NewsAPI.org
    Free tier: 100 requests/day, last 1 month of articles

    Args:
        query: Search keywords (optional)
        category: News category (business, technology, science, health, sports, entertainment)
        page_size: Number of articles to return (max 100)

    Returns:
        List of news articles with metadata
    """
    if not NEWS_API_KEY:
        logger.warning("[NEWS_TOOLS] NEWS_API_KEY not configured, using mock data")
        return get_mock_news_articles()

    try:
        # Use top-headlines endpoint (better for free tier)
        # Free tier has limitations on /everything endpoint
        if category:
            url = "https://newsapi.org/v2/top-headlines"

            # Map our categories to NewsAPI categories
            category_mapping = {
                "technology": "technology",
                "science": "science",
                "health": "health",
                "culture": "entertainment",
                "sports": "sports",
                "environment": "science",  # Environment news often categorized under science
                "business": "business",
                "politics": "general",
                "finance": "business",
                "entertainment": "entertainment"
            }

            params = {
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "pageSize": page_size,
                "category": category_mapping.get(category, "general")
            }
        else:
            # Fallback to /everything for custom queries (with date restrictions)
            today = datetime.utcnow()
            yesterday = today - timedelta(days=7)  # Extend to 7 days for better results

            url = "https://newsapi.org/v2/everything"

            params = {
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "from": yesterday.isoformat(),
                "to": today.isoformat()
            }

            if query:
                params["q"] = query

        # Make request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Debug logging to see what NewsAPI returns
        logger.info(f"[NEWS_TOOLS] NewsAPI response status: {data.get('status')}")
        logger.info(f"[NEWS_TOOLS] NewsAPI totalResults: {data.get('totalResults', 0)}")
        if data.get("status") != "ok":
            logger.error(f"[NEWS_TOOLS] NewsAPI error: {data.get('message')}")
            logger.error(f"[NEWS_TOOLS] Full response: {data}")
            return []

        articles = data.get("articles", [])

        # Transform to our format
        formatted_articles = []
        for idx, article in enumerate(articles):
            formatted_articles.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "category": category or "general",
                "summary": article.get("description", ""),
                "image_url": article.get("urlToImage"),
                "published_at": article.get("publishedAt", ""),
                "article_index": idx
            })

        logger.info(f"[NEWS_TOOLS] Found {len(formatted_articles)} articles from NewsAPI")
        return formatted_articles

    except Exception as e:
        logger.error(f"[NEWS_TOOLS] Error searching NewsAPI: {str(e)}")
        return []


def search_multiple_categories(categories: List[str], articles_per_category: int = 2) -> List[Dict[str, Any]]:
    """
    Search for articles across multiple categories
    Ensures diversity in news topics

    Args:
        categories: List of categories to search
        articles_per_category: Number of articles per category

    Returns:
        Combined list of articles from all categories
    """
    all_articles = []

    for category in categories:
        logger.info(f"[NEWS_TOOLS] Searching category: {category}")
        articles = search_news_api(category=category, page_size=articles_per_category)
        all_articles.extend(articles)

    logger.info(f"[NEWS_TOOLS] Total articles found: {len(all_articles)}")
    return all_articles


def get_mock_news_articles() -> List[Dict[str, Any]]:
    """
    Mock news articles for testing when NEWS_API_KEY is not available
    Returns 5 sample articles
    """
    logger.info("[NEWS_TOOLS] Using mock news articles for testing")

    return [
        {
            "title": "AI Breakthrough Revolutionizes Language Learning",
            "url": "https://techcrunch.com/ai-language-learning",
            "source": "TechCrunch",
            "category": "Technology",
            "summary": "Researchers develop new AI system that adapts to individual learning styles, making language acquisition faster and more effective.",
            "image_url": "https://via.placeholder.com/800x400?text=AI+Learning",
            "published_at": datetime.utcnow().isoformat(),
            "article_index": 0
        },
        {
            "title": "Scientists Discover New Species in Amazon Rainforest",
            "url": "https://nature.com/amazon-discovery",
            "source": "Nature",
            "category": "Science",
            "summary": "International team of biologists identifies over 400 new species during expedition to unexplored regions of the Amazon.",
            "image_url": "https://via.placeholder.com/800x400?text=Amazon+Discovery",
            "published_at": datetime.utcnow().isoformat(),
            "article_index": 1
        },
        {
            "title": "Virtual Reality Museums Open Doors to Global Audiences",
            "url": "https://culturenews.com/vr-museums",
            "source": "Culture News",
            "category": "Culture",
            "summary": "Major museums launch VR experiences allowing people worldwide to explore art collections and historical artifacts from home.",
            "image_url": "https://via.placeholder.com/800x400?text=VR+Museums",
            "published_at": datetime.utcnow().isoformat(),
            "article_index": 2
        },
        {
            "title": "Olympic Champion Announces Retirement After Record-Breaking Career",
            "url": "https://sports.com/olympic-retirement",
            "source": "Sports Today",
            "category": "Sports",
            "summary": "Legendary athlete retires with 8 Olympic gold medals and multiple world records, inspiring next generation of competitors.",
            "image_url": "https://via.placeholder.com/800x400?text=Olympic+Champion",
            "published_at": datetime.utcnow().isoformat(),
            "article_index": 3
        },
        {
            "title": "Sustainable Architecture: Building the Green Cities of Tomorrow",
            "url": "https://environment.com/green-cities",
            "source": "Environment Today",
            "category": "Environment",
            "summary": "Innovative architects design eco-friendly buildings that generate their own energy and purify air in urban centers.",
            "image_url": "https://via.placeholder.com/800x400?text=Green+Architecture",
            "published_at": datetime.utcnow().isoformat(),
            "article_index": 4
        }
    ]


def get_diverse_news(exclude_urls: List[str] = None) -> List[Dict[str, Any]]:
    """
    Main function to get diverse news articles
    Searches across multiple categories to ensure variety

    Args:
        exclude_urls: List of article URLs to exclude (previously used)

    Returns:
        List of 5-8 diverse news articles
    """
    if exclude_urls is None:
        exclude_urls = []

    # MVP: Search these categories
    categories = [
        "technology",
        "science",
        "health",
        "culture",
        "sports",
        "environment"
    ]

    # Try to get more articles per category to allow for filtering
    articles_per_cat = 3 if exclude_urls else 1
    articles = search_multiple_categories(categories, articles_per_category=articles_per_cat)

    # Filter out previously used articles
    if exclude_urls:
        original_count = len(articles)
        articles = [a for a in articles if a.get('url') not in exclude_urls]
        filtered_count = original_count - len(articles)
        if filtered_count > 0:
            logger.info(f"[NEWS_TOOLS] Filtered out {filtered_count} previously used articles")

    # If we got enough articles, return them
    if len(articles) >= 5:
        return articles[:8]  # Max 8 articles

    # Otherwise, fall back to mock data
    logger.warning(f"[NEWS_TOOLS] Only {len(articles)} new articles found, using mock data")
    return get_mock_news_articles()
