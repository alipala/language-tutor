"""
News Generation Service Entry Point
Runs news generation on Railway as a separate service
"""

import asyncio
import sys
from news_generation.news_generator import generate_daily_news

async def main():
    """
    Main entry point for Railway news generation service
    """
    print("[NEWS_SERVICE] 🚀 Starting news generation service...")

    try:
        result = await generate_daily_news()

        print(f"[NEWS_SERVICE] ✅ News generation completed successfully!")
        print(f"[NEWS_SERVICE] Batch ID: {result['batch_id']}")
        print(f"[NEWS_SERVICE] Articles: {result['article_count']}")
        print(f"[NEWS_SERVICE] Duration: {result['duration_seconds']}s")

        sys.exit(0)  # Success

    except Exception as e:
        print(f"[NEWS_SERVICE] ❌ News generation failed: {str(e)}")
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())
