"""
NewsApiProvider — flag-OFF / production provider.

This wrapper delegates to the existing `get_diverse_news()` function in
`news_tools.py` verbatim. No logic change, no rewriting of the inner
NewsAPI fetch, no different normalization. The whole point of Phase 1
is the seam — the wrapper exists so Phase 2 can introduce sibling
providers without altering this code path at all.

Parity guarantee: with NEWS_MULTI_PROVIDER_V1 OFF, the orchestrator
constructs only this provider, and this provider returns exactly what
the previous direct call would have returned.
"""

from typing import Any, Dict, List, Optional

from news_generation.providers.base import BaseNewsProvider
from news_generation.news_tools import get_diverse_news


class NewsApiProvider(BaseNewsProvider):
    """Thin wrapper over the existing NewsAPI fetch path."""

    name = "newsapi"

    def fetch(
        self,
        exclude_urls: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        # Verbatim delegation. Argument names are aligned with the existing
        # callee so this is a pure forwarding call.
        return get_diverse_news(exclude_urls=exclude_urls, categories=categories)
