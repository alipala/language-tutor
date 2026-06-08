"""
News Content Engine — configuration.

Phase 1 scope (current): just the master feature flag.
Module-level os.getenv per the Phase 0 decision (no pydantic-settings refactor).

When NEWS_MULTI_PROVIDER_V1 is OFF (the default and the production state),
news generation is byte-identical to today's NewsAPI-only pipeline. The flag
gates only the additive multi-provider behavior added in Phase 2 onward.
"""

import os


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
