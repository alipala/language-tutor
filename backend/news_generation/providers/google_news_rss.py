"""
GoogleNewsRssProvider — Phase 2 keyless backfill / fallback-primary.

Endpoint:  https://news.google.com/rss/search
Params:    ?q=<query>&hl=en&gl=US&ceid=US:en
Auth:      none

Topic-section feeds (https://news.google.com/rss/headlines/section/topic/<TOPIC>)
work the same way and are addressable via the same QUERY descriptor (caller
provides the full URL or the topic slug). Phase 2 implements the search feed
only; the topic-section variant is a one-line change Phase 3 can decide on.

RSS shape we consume (only the fields we use):

    <rss>
      <channel>
        <item>
          <title>The headline</title>
          <link>https://...</link>
          <pubDate>Tue, 03 Jun 2026 09:00:00 GMT</pubDate>
          <description>HTML fragment with snippet + source link</description>
          <source url="https://www.bbc.co.uk">BBC News</source>
          <media:content url="..." />        <!-- sometimes -->
          <enclosure url="..." />            <!-- sometimes -->
        </item>
      </channel>
    </rss>

Never raises. Returns ProviderResult with a typed FetchReason on every path.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from xml.etree import ElementTree as ET

import httpx

from news_generation.providers.base import BaseNewsProvider
from news_generation.providers._common import build_article, html_strip
from news_generation.providers.types import (
    CategoryDescriptor,
    DescriptorKind,
    FetchReason,
    ProviderResult,
)

logger = logging.getLogger(__name__)

GOOGLE_NEWS_SEARCH_BASE = "https://news.google.com/rss/search"
GOOGLE_NEWS_TIMEOUT_SECONDS = 10.0

# Default audience (matches Phase 0 + simplified plan: English source pool).
GOOGLE_NEWS_LOCALE = {"hl": "en", "gl": "US", "ceid": "US:en"}

# XML namespace used for <media:content> in some Google News items.
_MEDIA_NS = "{http://search.yahoo.com/mrss/}"


class GoogleNewsRssProvider(BaseNewsProvider):
    """Async Google News RSS adapter — keyless backfill."""

    name = "gnews_rss"

    def __init__(self, *, client: Optional[httpx.AsyncClient] = None) -> None:
        self._injected_client = client

    # ------------------------------------------------------------------ public

    async def afetch_for(self, descriptor: CategoryDescriptor) -> ProviderResult:
        if descriptor.kind == DescriptorKind.QUERY:
            query = descriptor.value
        elif descriptor.kind == DescriptorKind.CATEGORY:
            # Translate a category-slot id into a free-text search.
            # Phase 3 may override with topic-section URLs per category.
            query = descriptor.value
        else:  # pragma: no cover
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=f"unknown kind={descriptor.kind!r}")

        url = GOOGLE_NEWS_SEARCH_BASE
        params = {"q": query, **GOOGLE_NEWS_LOCALE}

        # ---- transport ----
        try:
            async with self._client_ctx() as client:
                resp = await client.get(url, params=params, timeout=GOOGLE_NEWS_TIMEOUT_SECONDS)
        except httpx.TimeoutException as e:
            logger.warning("[GNEWS_RSS] timeout for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.TIMEOUT, error_detail=type(e).__name__)
        except httpx.ConnectError as e:
            logger.warning("[GNEWS_RSS] connection error for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.CONNECTION_ERROR, error_detail=type(e).__name__)
        except httpx.HTTPError as e:
            logger.warning("[GNEWS_RSS] httpx error for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=type(e).__name__)
        except Exception as e:
            logger.exception("[GNEWS_RSS] unexpected error for slot=%s", descriptor.slot_id)
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

        # ---- decode + parse RSS ----
        body = resp.content
        if not body:
            return ProviderResult(reason=FetchReason.EMPTY, error_detail="empty_body")
        try:
            root = ET.fromstring(body)
        except ET.ParseError as e:
            logger.warning("[GNEWS_RSS] RSS parse failed for slot=%s: %s", descriptor.slot_id, e)
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail=type(e).__name__)

        # rss/channel/item*
        channel = root.find("channel")
        if channel is None:
            return ProviderResult(reason=FetchReason.PARSE_ERROR, error_detail="no_channel")

        items = channel.findall("item")
        if not items:
            return ProviderResult(reason=FetchReason.EMPTY)

        # ---- normalize ----
        articles: List[Dict[str, Any]] = []
        cap = descriptor.target_count or 10
        for idx, item in enumerate(items):
            if len(articles) >= cap:
                break
            normalized = self._normalize_item(item, descriptor=descriptor, article_index=idx)
            if normalized is not None:
                articles.append(normalized)

        if not articles:
            return ProviderResult(reason=FetchReason.EMPTY)
        return ProviderResult(articles=articles, reason=FetchReason.OK)

    # ----------------------------------------------------------------- helpers

    def _client_ctx(self):
        if self._injected_client is not None:
            return _NoCloseClient(self._injected_client)
        # Google News RSS responds with a 302 redirect to the actual feed URL.
        # Without follow_redirects the provider sees status=302 → UNEXPECTED, and
        # the orchestrator silently loses RSS as a primary/fallback source.
        # Discovered during Phase 3 §4.1 smoke validation.
        return httpx.AsyncClient(timeout=GOOGLE_NEWS_TIMEOUT_SECONDS, follow_redirects=True)

    @staticmethod
    def _text(el: Optional[ET.Element]) -> str:
        return (el.text or "") if el is not None and el.text else ""

    def _normalize_item(self, item: ET.Element, *, descriptor: CategoryDescriptor, article_index: int) -> Optional[Dict[str, Any]]:
        title = self._text(item.find("title"))
        link = self._text(item.find("link"))
        if not title and not link:
            return None

        # description is HTML — strip to plain text.
        description = html_strip(self._text(item.find("description")))

        # Source: <source url="...">Display Name</source>; sometimes only one is present.
        source_el = item.find("source")
        source = self._text(source_el) or None

        # Image hunt: <media:content url="..."> first, then <enclosure url="...">.
        image_url: Optional[str] = None
        media = item.find(f"{_MEDIA_NS}content")
        if media is not None:
            image_url = media.get("url") or None
        if not image_url:
            enclosure = item.find("enclosure")
            if enclosure is not None:
                image_url = enclosure.get("url") or None

        pub_date = self._text(item.find("pubDate"))

        return build_article(
            title=title or None,
            url=link or None,
            source=source,
            category=descriptor.slot_id,
            summary=description or None,
            image_url=image_url,
            published_at=pub_date or None,
            article_index=article_index,
        )


class _NoCloseClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


# Module-level helper for callers building a topic-section URL by hand.
def google_news_topic_url(topic_slug: str) -> str:
    """Build a Google News topic-section RSS URL (Phase 3 may use this)."""
    return (
        f"https://news.google.com/rss/headlines/section/topic/{quote(topic_slug)}"
        f"?hl=en&gl=US&ceid=US:en"
    )
