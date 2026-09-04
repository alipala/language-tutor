"""
News Content Engine — configuration.

Module-level os.getenv per the Phase 0 decision (no pydantic-settings refactor).

When NEWS_MULTI_PROVIDER_V1 is OFF (the default and the production state),
news generation is byte-identical to today's NewsAPI-only pipeline. The flag
gates only the additive multi-provider behavior added in Phase 2 onward.

Generation cadence
------------------
``NEWS_GENERATION_INTERVAL_DAYS`` is the single knob that decides how often the
``news`` cron actually produces a batch. It does NOT schedule anything — the
Railway cron does that — but every *consumer-side* window is derived from it so
the three settings can never drift apart:

    interval → how far /api/news/today looks back for a servable batch
    interval → how long articles live before Mongo's TTL index reaps them

Getting that wrong is silent and total: articles carry ``expires_at`` and the
``news_articles`` collection has a TTL index on it (``expireAfterSeconds: 0``),
so a batch that outlives its retention is *physically deleted*, not merely
stale. A weekly cron with the old 2-day retention would leave the news tab
empty from day 3 onward. Deriving both windows from one number is what stops
that.

The default of 1 reproduces the historical daily behaviour exactly:
lookback = 1 day (yesterday) and retention = 2 days, which is what the
hard-coded values were before this became configurable.
"""

import os
from typing import List

# Canonical generation matrix. ``crew_agents`` re-exports these as
# MVP_LANGUAGES / MVP_LEVELS so there is exactly one definition; this module is
# a leaf (stdlib only), so importing it never drags in crewai/openai the way
# importing crew_agents does — which matters because news_routes.py runs inside
# the web process and must stay cheap to import.
DEFAULT_LANGUAGES = ["en", "es", "nl", "pt", "de", "fr"]
DEFAULT_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _truthy(value: str) -> bool:
    """Conservative truthy parser: only 'true'/'1'/'yes' (case-insensitive) count as ON."""
    return (value or "").strip().lower() in {"true", "1", "yes"}


def is_multi_provider_enabled() -> bool:
    """
    Read NEWS_MULTI_PROVIDER_V1 at call time (not import time).

    Reading on every call lets tests flip the env var without needing to reload
    the module. The cost is one env-var lookup per news generation run, which
    is negligible.
    """
    return _truthy(os.getenv("NEWS_MULTI_PROVIDER_V1", ""))


def _positive_int(env_name: str, default: int) -> int:
    """
    Read a positive int from the environment, falling back on anything odd.

    Cadence values are read from operator-set env vars, so a typo must degrade
    to the safe default rather than crash the cron or — worse — produce a
    zero/negative retention that would make Mongo reap every article the
    instant it is written.
    """
    raw = (os.getenv(env_name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 1 else default


def _csv_list(env_name: str, default: List[str]) -> List[str]:
    """
    Read a comma-separated override list, preserving the default's ordering.

    Only values already present in ``default`` are honoured: the matrix drives
    prompt construction and Mongo document shape, so an unknown language or
    CEFR code would create variations nothing can ever read. An override that
    filters everything out falls back to the full default rather than
    generating an empty batch.
    """
    raw = (os.getenv(env_name) or "").strip()
    if not raw:
        return list(default)
    wanted = {item.strip() for item in raw.split(",") if item.strip()}
    filtered = [item for item in default if item in wanted]
    return filtered or list(default)


def get_generation_interval_days() -> int:
    """
    How many days a generated batch is expected to serve. 1 = daily (default).

    Set to 7 alongside a weekly Railway cron. This value must match the cron;
    nothing verifies that, so changing one without the other either wastes
    generation (interval longer than the cron) or empties the feed (cron
    longer than the interval).
    """
    return _positive_int("NEWS_GENERATION_INTERVAL_DAYS", 1)


def get_lookback_days() -> int:
    """
    How far /api/news/today may reach back for a servable batch.

    Equal to the interval: with the default of 1 this is "yesterday", which is
    exactly the fallback the endpoint hard-coded before.
    """
    return _positive_int("NEWS_LOOKBACK_DAYS", get_generation_interval_days())


def get_retention_days() -> int:
    """
    Article TTL in days — what goes into each document's ``expires_at``.

    One day of grace beyond the lookback window so a batch never disappears
    while it is still the newest thing available. Default 2 reproduces the
    previous hard-coded ``timedelta(days=2)``.
    """
    return _positive_int("NEWS_RETENTION_DAYS", get_lookback_days() + 1)


def get_languages() -> List[str]:
    """Languages to generate variations for. Override: NEWS_LANGUAGES=en,nl,es"""
    return _csv_list("NEWS_LANGUAGES", DEFAULT_LANGUAGES)


def get_levels() -> List[str]:
    """CEFR levels to generate variations for. Override: NEWS_LEVELS=A1,A2,B1,B2"""
    return _csv_list("NEWS_LEVELS", DEFAULT_LEVELS)
