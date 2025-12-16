#!/usr/bin/env python3
"""
Weekly Challenge Generation Cron Entry Point
============================================

Simple entry point for Railway cron job to run weekly challenge generation
using the CrewAI multi-agent system.

Schedule: Weekly (every Monday at 00:00 UTC)
Railway Cron: 0 0 * * 1

Environment Variables Required:
- OPENAI_API_KEY
- MONGODB_URL
- GPT_MODEL (optional, default: gpt-4o)
- LLM_PROVIDER (optional, default: openai)
- LOG_LEVEL (optional, default: INFO)
"""

import sys
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/home/user/language-tutor/cron-service/phase2-crewai')

from challenge_crew_ai import run_weekly_challenge_generation


def main():
    """Main entry point for weekly cron"""
    print("=" * 80)
    print("🗓️  WEEKLY CHALLENGE GENERATION CRON")
    print("=" * 80)
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)
    print()

    try:
        # Run the async challenge generation
        asyncio.run(run_weekly_challenge_generation())

        print()
        print("=" * 80)
        print("✅ Weekly cron completed successfully!")
        print("=" * 80)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
