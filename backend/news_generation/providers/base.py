"""
News provider abstract base.

Every provider returns the same 8-key article dict that today's
news_tools.py:99-109 produces. This is the parity contract: nothing
downstream of the provider (orchestrator, doc shape, routes, mobile)
knows or cares which provider produced an article.

The 8 keys, with defaults matching the existing NewsAPI normalization:

    {
        "title":         str,           # default "" when source field missing
        "url":           str,           # default ""
        "source":        str,           # default "Unknown" (flattened from nested provider field)
        "category":      str,           # default "general" when the caller didn't supply one
        "summary":       str,           # default ""
        "image_url":     Optional[str], # default None
        "published_at":  str,           # default "" (ISO-8601 when present)
        "article_index": int,           # 0..N-1, set by the provider per-call
    }
"""

from abc import ABC
from typing import Any, Dict, List, Optional

from news_generation.providers.types import CategoryDescriptor, ProviderResult


class BaseNewsProvider(ABC):
    """
    Abstract base for news candidate-fetching providers.

    Two seams:

    - ``fetch(exclude_urls, categories)`` — Phase 1's sync seam. Used by
      ``NewsApiProvider`` to keep flag-OFF byte-identical. Returns the bare
      list of articles; on failure returns ``[]`` (no typed reason).

    - ``afetch_for(descriptor)`` — Phase 2's async seam. New providers
      implement this. Takes one ``CategoryDescriptor`` at a time so the
      orchestrator can fan out concurrently in Phase 3. Returns a
      ``ProviderResult`` with both the articles and a typed outcome reason.

    Subclasses override only the method they need. Phase 1's NewsApiProvider
    overrides ``fetch``; Phase 2's new providers override ``afetch_for``.
    Both have default ``NotImplementedError`` bodies so calling the wrong
    one fails loudly during development.
    """

    name: str = "base"  # subclasses override; used for logging only

    def fetch(
        self,
        exclude_urls: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sync seam. Phase 1 contract; returns the 8-key shape verbatim.

        Must not raise on transport errors — return [] with a log line instead.
        Phase 2+ providers should leave this NotImplementedError and use
        ``afetch_for`` for their async path. The orchestrator decides which
        seam to call.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.fetch() is not implemented; "
            "Phase 2 providers expose afetch_for() instead."
        )

    async def afetch_for(self, descriptor: CategoryDescriptor) -> ProviderResult:
        """
        Async seam. Phase 2 contract.

        Implementations MUST NOT raise. Catch every transport / parse failure
        and return a ProviderResult with the appropriate FetchReason. The
        orchestrator in Phase 3 will inspect ``result.reason`` to decide on
        fallback (e.g. switch primary to RSS when NewsData is RATE_LIMITED).
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.afetch_for() is not implemented."
        )
