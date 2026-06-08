"""
GdeltProvider — Phase 2 optional trending / image backfill.

Endpoint:  https://api.gdeltproject.org/api/v2/doc/doc
Auth:      none
Default params:  mode=ArtList, format=json, sourcelang:english, sort=DateDesc

Response shape (relevant fields):

    {
      "articles": [
        {
          "url": "https://...",
          "url_mobile": "https://...",
          "title": "...",
          "seendate": "20260607T080000Z",    # → 8-key published_at
          "socialimage": "https://...",      # → 8-key image_url
          "domain": "bbc.com",               # → 8-key source
          "language": "English",
          "sourcecountry": "..."
        }, ...
      ]
    }

Phase 3 may use this as an image-backfill source when NewsData/RSS produce
articles with no image. Also useful for "trending" because GDELT sorts by
DateDesc by default. Never raises; typed reasons on failure.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from news_generation.providers.base import BaseNewsProvider
from news_generation.providers._common import build_article
from news_generation.providers.types import (
    CategoryDescriptor,
    DescriptorKind,
    FetchReason,
    ProviderResult,
)

logger = logging.getLogger(__name__)

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TIMEOUT_SECONDS = 10.0


class GdeltProvider(BaseNewsProvider):
    """Async GDELT DOC adapter — keyless trending/image backfill."""

    name = "gdelt"

    def __init__(self, *, client: Optional[httpx.AsyncClient] = None) -> None:
        self._injected_client = client

    # ------------------------------------------------------------------ public

    async def afetch_for(self, descriptor: CategoryDescriptor) -> ProviderResult:
        # GDELT only has free-text query — translate CATEGORY descriptors into a query.
        if descriptor.kind == DescriptorKind.QUERY:
            user_q = descriptor.value
        elif descriptor.kind == DescriptorKind.CATEGORY:
            user_q = descriptor.value
        else:  # pragma: no cover
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=f"unknown kind={descriptor.kind!r}")

        cap = descriptor.target_count or 20
        # Enforce the english source filter at the query level — keeps the
        # downstream English denylist (news_generator.evaluate_safety_simple)
        # valid for Phase 2 candidates.
        query_str = f"{user_q} sourcelang:english"

        params = {
            "query": query_str,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": str(max(1, min(cap * 2, 250))),  # GDELT cap is 250
            "sort": "DateDesc",
        }

        # ---- transport ----
        try:
            async with self._client_ctx() as client:
                resp = await client.get(GDELT_DOC_URL, params=params, timeout=GDELT_TIMEOUT_SECONDS)
        except httpx.TimeoutException as e:
            return ProviderResult(reason=FetchReason.TIMEOUT, error_detail=type(e).__name__)
        except httpx.ConnectError as e:
            return ProviderResult(reason=FetchReason.CONNECTION_ERROR, error_detail=type(e).__name__)
        except httpx.HTTPError as e:
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=type(e).__name__)
        except Exception as e:
            logger.exception("[GDELT] unexpected error for slot=%s", descriptor.slot_id)
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=type(e).__name__)

        # ---- HTTP status ----
        if resp.status_code == 429:
            return ProviderResult(reason=FetchReason.RATE_LIMITED, error_detail="429")
        if 400 <= resp.status_code < 500:
            return ProviderResult(reason=FetchReason.HTTP_4XX, error_detail=str(resp.status_code))
        if 500 <= resp.status_code < 600:
            return ProviderResult(reason=FetchReason.HTTP_5XX, error_detail=str(resp.status_code))
        if resp.status_code != 200:
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=f"status={resp.status_code}")

        # ---- decode ----
        try:
            payload = resp.json()
        except Exception as e:
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail=type(e).__name__)

        if not isinstance(payload, dict):
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail="root_not_object")

        raw = payload.get("articles") or []
        if not isinstance(raw, list):
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail="articles_not_list")

        # ---- normalize ----
        articles: List[Dict[str, Any]] = []
        for idx, item in enumerate(raw):
            if len(articles) >= cap:
                break
            normalized = self._normalize(item, descriptor=descriptor, article_index=idx)
            if normalized is not None:
                articles.append(normalized)

        if not articles:
            return ProviderResult(reason=FetchReason.EMPTY)
        return ProviderResult(articles=articles, reason=FetchReason.OK)

    # ----------------------------------------------------------------- helpers

    def _client_ctx(self):
        if self._injected_client is not None:
            return _NoCloseClient(self._injected_client)
        return httpx.AsyncClient(timeout=GDELT_TIMEOUT_SECONDS)

    @staticmethod
    def _normalize(item: Dict[str, Any], *, descriptor: CategoryDescriptor, article_index: int) -> Optional[Dict[str, Any]]:
        if not isinstance(item, dict):
            return None
        url = item.get("url") or item.get("url_mobile")
        title = item.get("title")
        if not url and not title:
            return None
        return build_article(
            title=title,
            url=url,
            source=item.get("domain"),
            category=descriptor.slot_id,
            summary=None,  # GDELT doesn't return a description in ArtList mode
            image_url=item.get("socialimage"),
            published_at=item.get("seendate"),
            article_index=article_index,
        )


class _NoCloseClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
