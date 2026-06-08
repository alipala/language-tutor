"""
NewsDataProvider — Phase 2 primary structured source.

Endpoint:  https://newsdata.io/api/1/latest
Auth:      ?apikey=...  (env: NEWSDATA_API_KEY)
Free tier: 200 credits/day · 10 articles per credit · 30 credits / 15 min · 12-hour news delay
Docs:      https://newsdata.io/docs

Response shape (relevant fields, free tier only):

    {
      "status": "success",
      "totalResults": <int>,
      "results": [
        {
          "article_id": "...",
          "title": "...",
          "link": "https://...",            # → 8-key url
          "source_id": "bbc",               # → 8-key source
          "description": "...",             # → 8-key summary
          "image_url": "https://..." | null,
          "pubDate": "2026-06-07 09:00:00", # → 8-key published_at
          "category": ["technology", ...],
          "duplicate": false,
          "content": "ONLY_AVAILABLE_IN_PAID_PLANS"  # IGNORED on purpose
        }, ...
      ]
    }

The paid ``content`` field is deliberately NOT used and NOT required:
the existing pipeline expands ``description`` into leveled summaries via
``gpt-4o-mini`` (see ``news_generator.generate_variation_simple``).

Hard rule: this adapter NEVER raises. Every failure path returns a
``ProviderResult`` with the appropriate ``FetchReason`` and ``articles=[]``.
"""

from __future__ import annotations

import logging
import os
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

NEWSDATA_URL = "https://newsdata.io/api/1/latest"
NEWSDATA_TIMEOUT_SECONDS = 10.0
NEWSDATA_PAGE_SIZE = 10  # free tier returns up to 10 per credit


class NewsDataProvider(BaseNewsProvider):
    """Async NewsData.io adapter for the 8-key article shape."""

    name = "newsdata"

    def __init__(self, *, api_key: Optional[str] = None, client: Optional[httpx.AsyncClient] = None) -> None:
        # api_key resolved at construction so callers can inject in tests;
        # falls back to env so production wiring stays a one-liner.
        self._api_key = api_key if api_key is not None else os.getenv("NEWSDATA_API_KEY")
        # The httpx client is optional; if not supplied we build per-call and
        # close cleanly. Phase 3 may want a long-lived shared client for the
        # 20-category fan-out, but Phase 2 keeps lifecycle simple.
        self._injected_client = client

    # ------------------------------------------------------------------ public

    async def afetch_for(self, descriptor: CategoryDescriptor) -> ProviderResult:
        if not self._api_key:
            logger.info("[NEWSDATA] NEWSDATA_API_KEY not configured — provider disabled")
            return ProviderResult(reason=FetchReason.AUTH_MISSING)

        params: Dict[str, Any] = {
            "apikey": self._api_key,
            "language": "en",
            "size": NEWSDATA_PAGE_SIZE,
        }
        if descriptor.kind == DescriptorKind.CATEGORY:
            params["category"] = descriptor.value
        elif descriptor.kind == DescriptorKind.QUERY:
            # NewsData enforces a 100-char limit on q.
            params["q"] = descriptor.value[:100]
        else:  # pragma: no cover — DescriptorKind is a closed enum
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=f"unknown kind={descriptor.kind!r}")

        # ---- transport ----
        try:
            async with self._client_ctx() as client:
                resp = await client.get(NEWSDATA_URL, params=params, timeout=NEWSDATA_TIMEOUT_SECONDS)
        except httpx.TimeoutException as e:
            logger.warning("[NEWSDATA] timeout for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.TIMEOUT, error_detail=type(e).__name__)
        except httpx.ConnectError as e:
            logger.warning("[NEWSDATA] connection error for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.CONNECTION_ERROR, error_detail=type(e).__name__)
        except httpx.HTTPError as e:
            logger.warning("[NEWSDATA] httpx error for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=type(e).__name__)
        except Exception as e:  # last-resort catch-all — must never raise out
            logger.exception("[NEWSDATA] unexpected error for slot=%s", descriptor.slot_id)
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=type(e).__name__)

        # ---- HTTP status ----
        if resp.status_code == 429:
            logger.warning("[NEWSDATA] rate-limited for slot=%s (429)", descriptor.slot_id)
            return ProviderResult(reason=FetchReason.RATE_LIMITED, error_detail="429")
        if 400 <= resp.status_code < 500:
            logger.warning("[NEWSDATA] HTTP %s for slot=%s body=%r",
                           resp.status_code, descriptor.slot_id, resp.text[:200])
            return ProviderResult(reason=FetchReason.HTTP_4XX, error_detail=str(resp.status_code))
        if 500 <= resp.status_code < 600:
            logger.warning("[NEWSDATA] HTTP %s for slot=%s", resp.status_code, descriptor.slot_id)
            return ProviderResult(reason=FetchReason.HTTP_5XX, error_detail=str(resp.status_code))
        if resp.status_code != 200:
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=f"status={resp.status_code}")

        # ---- decode + envelope ----
        try:
            payload = resp.json()
        except Exception as e:
            logger.warning("[NEWSDATA] JSON parse failed for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail=type(e).__name__)

        if not isinstance(payload, dict):
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail="root_not_object")

        status = payload.get("status")
        if status not in ("success", "ok"):
            # NewsData sets status="error" with message on bad input/quota; treat as parse-ish.
            msg = payload.get("message") or payload.get("results") or ""
            logger.warning("[NEWSDATA] non-success status=%r message=%r", status, msg)
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail=f"status={status!r}")

        raw_results = payload.get("results") or []
        if not isinstance(raw_results, list):
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail="results_not_list")

        # ---- normalize ----
        articles: List[Dict[str, Any]] = []
        cap = descriptor.target_count or NEWSDATA_PAGE_SIZE
        for idx, item in enumerate(raw_results):
            if len(articles) >= cap:
                break
            normalized = self._normalize(item, descriptor=descriptor, article_index=idx)
            if normalized is None:
                continue  # item too malformed to keep
            articles.append(normalized)

        if not articles:
            return ProviderResult(reason=FetchReason.EMPTY)

        return ProviderResult(articles=articles, reason=FetchReason.OK)

    # ----------------------------------------------------------------- helpers

    def _client_ctx(self):
        """
        Return an httpx async client context manager.

        If the caller injected one, reuse it without closing it (the caller owns
        the lifecycle). Otherwise build a one-shot client.
        """
        if self._injected_client is not None:
            return _NoCloseClient(self._injected_client)
        return httpx.AsyncClient(timeout=NEWSDATA_TIMEOUT_SECONDS)

    @staticmethod
    def _normalize(item: Dict[str, Any], *, descriptor: CategoryDescriptor, article_index: int) -> Optional[Dict[str, Any]]:
        """
        Map a NewsData ``result`` row into the canonical 8-key shape.

        Returns None if the row is missing both title and url (unusable).
        Skips the paid-only ``content`` field entirely.
        """
        if not isinstance(item, dict):
            return None

        title = item.get("title")
        link = item.get("link") or item.get("url")
        if not title and not link:
            return None

        # NewsData category is a list; pick the first; fall back to descriptor slot_id
        # so dedup / display still know what bucket the article came from.
        cat_field = item.get("category")
        if isinstance(cat_field, list) and cat_field:
            category = str(cat_field[0])
        elif isinstance(cat_field, str) and cat_field:
            category = cat_field
        else:
            category = descriptor.slot_id

        # source_id (e.g. "bbc"). NewsData also has source_name in some plans;
        # use whichever is present, fall back to "Unknown" via build_article.
        source = item.get("source_name") or item.get("source_id")

        return build_article(
            title=title,
            url=link,
            source=source,
            category=category,
            summary=item.get("description"),
            image_url=item.get("image_url"),
            published_at=item.get("pubDate"),
            article_index=article_index,
        )


class _NoCloseClient:
    """Wrap an injected httpx.AsyncClient so 'async with' doesn't close it."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
