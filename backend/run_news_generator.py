"""
News Generation Service Entry Point
Runs news generation on Railway as a separate service.

CLI:
  python run_news_generator.py             # full daily generation run
  python run_news_generator.py --dry-run   # flag-ON fetch + select only.
                                           # NO Mongo writes, NO OpenAI calls.
                                           # Prints the 20-category inventory.

The ``--dry-run`` path forces ``NEWS_MULTI_PROVIDER_V1=true`` for the duration
of the process so reviewers can inspect what the multi-provider orchestrator
would feed into the variation pass before any real Phase-4 run.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Phase 4 fix: explicitly load .env so NEWSDATA_API_KEY (and any other
# Phase-3 provider keys) are visible to providers constructed lazily inside
# the orchestrator. Without this, ``--dry-run`` and the live run would see
# NEWSDATA_API_KEY only when crew_agents.py was imported transitively, which
# the orchestrator-only --dry-run path does not do.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is already a transitive dep via crew_agents; if it's
    # somehow missing the live cron still works (env injected by Railway).
    pass


async def _full_run() -> int:
    """Original behavior: full daily generation. Writes to Mongo, calls OpenAI."""
    from news_generation.news_generator import generate_daily_news

    print("[NEWS_SERVICE] 🚀 Starting news generation service...")
    try:
        result = await generate_daily_news()
        print("[NEWS_SERVICE] ✅ News generation completed successfully!")
        print(f"[NEWS_SERVICE] Batch ID: {result['batch_id']}")
        print(f"[NEWS_SERVICE] Articles: {result['article_count']}")
        print(f"[NEWS_SERVICE] Duration: {result['duration_seconds']}s")
        return 0
    except Exception as e:
        print(f"[NEWS_SERVICE] ❌ News generation failed: {str(e)}")
        return 1


async def _dry_run() -> int:
    """
    Flag-ON fetch + select path only. Prints the per-category inventory.
    Zero Mongo writes. Zero OpenAI calls. Safe to run against production
    upstreams; the only side effect is HTTP traffic to the news providers.
    """
    # Force flag ON for this process. config.is_multi_provider_enabled()
    # reads on every call so this takes effect immediately.
    os.environ["NEWS_MULTI_PROVIDER_V1"] = "true"

    from news_generation.orchestrator import (
        fetch_candidates_with_report,
        NEWS_FETCH_CONCURRENCY,
        NEWS_VARIATION_CONCURRENCY,
    )

    print("[DRY-RUN] 🔎 Phase 3 dry-run — flag-ON fetch + deterministic select only.")
    print(f"[DRY-RUN] Concurrency caps: fetch={NEWS_FETCH_CONCURRENCY}, variation={NEWS_VARIATION_CONCURRENCY}")
    print("[DRY-RUN] No Mongo writes. No OpenAI calls.")
    print()

    try:
        report = await fetch_candidates_with_report()
    except Exception as e:  # pragma: no cover — orchestrator is no-raise; defensive
        print(f"[DRY-RUN] ❌ Orchestrator raised unexpectedly: {type(e).__name__}: {e}")
        return 1

    print(f"[DRY-RUN] === Inventory: {len(report.articles)} article(s) across {len(report.per_category)} category slots ===")
    print()

    for cat in report.per_category:
        status = "OK" if not cat.fell_short else "SHORT"
        provider_summary = " · ".join(
            f"{name}={reason}" for name, reason in cat.provider_reasons.items()
        ) or "(no providers consulted)"
        print(f"[{status}] {cat.slot_id:<14} {cat.selected_count}/{cat.target_count}  "
              f"providers: {provider_summary}")
        for i, title in enumerate(cat.selected_titles, start=1):
            # Truncate long titles for readability.
            t = (title or "")[:80]
            ellipsis = "…" if len(title or "") > 80 else ""
            print(f"     {i}. {t}{ellipsis}")
        print()

    short_categories = [c.slot_id for c in report.per_category if c.fell_short]
    if short_categories:
        print(f"[DRY-RUN] ⚠️  Short categories ({len(short_categories)}): {', '.join(short_categories)}")
    else:
        print("[DRY-RUN] ✅ All categories hit their target_count.")

    print(f"[DRY-RUN] Total selected: {len(report.articles)} article(s).")
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="News generation service. Default is a full daily run. "
                    "Use --dry-run to exercise the flag-ON orchestrator without "
                    "writing to Mongo or calling OpenAI."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the flag-ON multi-provider fetch + selection only; "
             "print the 20-category inventory and exit. NO Mongo writes, "
             "NO OpenAI calls.",
    )
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.dry_run:
        return await _dry_run()
    return await _full_run()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
