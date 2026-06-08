"""
Shared helpers used by every Phase-2 provider adapter.

The 8-key article dict is the parity contract (see providers/base.py).
``build_article`` is the only place in the new providers where that dict
is constructed — if it stays the only place, no adapter can drift the
shape by accident.

``make_stable_id`` produces the dedup key Phase 3 will use across providers.
Prefers the article ``url``; falls back to a hash of ``title+source+published_at``
so URL-less or unstable-URL items (some RSS sources) still dedup correctly.

``html_strip`` removes tags + decodes entities from RSS ``<description>`` blocks.
Uses only stdlib (``html.parser`` + ``html.unescape``). No new runtime dep.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical 8-key shape — keep aligned with news_tools.py:99-109.
# ---------------------------------------------------------------------------

ARTICLE_KEYS = (
    "title", "url", "source", "category",
    "summary", "image_url", "published_at", "article_index",
)


def build_article(
    *,
    title: Optional[str],
    url: Optional[str],
    source: Optional[str],
    category: Optional[str],
    summary: Optional[str],
    image_url: Optional[str],
    published_at: Optional[str],
    article_index: int,
) -> Dict[str, Any]:
    """
    Return a canonical 8-key article dict.

    Defaults mirror the existing NewsAPI normalization at news_tools.py:99-109:
      - ``title``/``url``/``summary`` default to ``""`` when None.
      - ``source`` defaults to ``"Unknown"``.
      - ``category`` defaults to ``"general"`` when neither caller-supplied
        nor provider-supplied (matches NewsAPI's ``category or "general"`` fallback).
      - ``image_url`` defaults to ``None`` (not empty string).
      - ``published_at`` (Phase 3.5 Fix 3) is normalized to ISO-8601 UTC
        ``YYYY-MM-DDTHH:MM:SSZ`` via ``normalize_published_at``. NewsAPI
        already supplies this exact format, so the existing flag-OFF behavior
        is preserved (the value passes through normalize unchanged).
        Unparseable / missing values become ``""``.
    """
    return {
        "title": title if isinstance(title, str) else "",
        "url": url if isinstance(url, str) else "",
        "source": source if (isinstance(source, str) and source) else "Unknown",
        "category": category if (isinstance(category, str) and category) else "general",
        "summary": summary if isinstance(summary, str) else "",
        "image_url": image_url if isinstance(image_url, str) and image_url else None,
        "published_at": normalize_published_at(published_at),
        "article_index": int(article_index),
    }


# ---------------------------------------------------------------------------
# Dedup id
# ---------------------------------------------------------------------------

def make_stable_id(article: Dict[str, Any]) -> str:
    """
    Stable dedup key. Prefers url; otherwise hashes title+source+published_at.

    Two different providers returning the same story produce the same id when
    they share the url (the common case). When url is missing or differs only
    in trailing query params, callers may want a normalized-url version — out
    of scope for Phase 2; Phase 3 can add a normalization helper if needed.
    """
    url = (article.get("url") or "").strip()
    if url:
        return f"url:{url}"
    fallback = "|".join([
        (article.get("title") or "").strip().lower(),
        (article.get("source") or "").strip().lower(),
        (article.get("published_at") or "").strip(),
    ])
    return "hash:" + hashlib.sha1(fallback.encode("utf-8", errors="replace")).hexdigest()


# ---------------------------------------------------------------------------
# published_at normalization (Phase 3.5 Fix 3)
# ---------------------------------------------------------------------------

# Canonical output format. Matches the existing production news_articles
# documents (confirmed by a read-only sample of prod data, 2026-06-07):
#   '2026-06-04T20:07:31Z'
# This is what NewsAPI's `publishedAt` already produces unchanged, so flag-OFF
# behavior is preserved (the NewsAPI path passes the field through verbatim,
# and that verbatim value already matches this format).
ISO_8601_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Compact ISO-8601 used by GDELT DOC API (no separators).
_GDELT_COMPACT_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z?$")


def normalize_published_at(value: Optional[str]) -> str:
    """
    Best-effort parse of a publication timestamp into the canonical
    ISO-8601 UTC string ``YYYY-MM-DDTHH:MM:SSZ``.

    Accepted inputs (covering every Phase 2 provider):
      - Already-canonical: ``"2026-06-04T20:07:31Z"`` (NewsAPI, prod data)
      - Already ISO with microseconds: ``"2026-06-04T20:07:31.123Z"``
      - ISO with explicit offset: ``"2026-06-04T20:07:31+00:00"``
      - NewsData free tier: ``"2026-06-07 08:00:00"`` (space separator, no TZ — treated as UTC per NewsData docs)
      - RSS RFC-2822: ``"Sat, 07 Jun 2026 08:00:00 GMT"``
      - GDELT compact: ``"20260607T080000Z"`` or ``"20260607T080000"``

    Unparseable or missing input → ``""`` (empty string). The orchestrator's
    deterministic-select treats empty strings as least-recent, so articles
    with missing dates sort last under DESC, which matches the existing
    behavior in Phase 3.
    """
    if not value or not isinstance(value, str):
        return ""
    raw = value.strip()
    if not raw:
        return ""

    parsed: Optional[datetime] = None

    # 1. GDELT compact form first — fast and unambiguous.
    m = _GDELT_COMPACT_RE.match(raw)
    if m:
        y, mo, d, h, mi, s = (int(g) for g in m.groups())
        try:
            parsed = datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc)
        except ValueError:
            parsed = None

    # 2. ISO-8601-ish: replace trailing 'Z' with '+00:00' so datetime.fromisoformat
    #    (3.9-compatible) accepts it. Python 3.11+ handles 'Z' directly; we
    #    support older runtimes by normalizing.
    #    NOTE: Python 3.9's fromisoformat also accepts the NewsData-style
    #    space-separated form ``"YYYY-MM-DD HH:MM:SS"`` and returns it naive.
    #    A subsequent ``.astimezone(utc)`` on a naive datetime would assume
    #    system local time — wrong. We force UTC on any naive result here
    #    so ISO parsing and the explicit NewsData branch behave identically.
    if parsed is None:
        candidate = raw
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            parsed = None

    # 3. NewsData free-tier form: ``YYYY-MM-DD HH:MM:SS`` (space, no TZ).
    #    Kept as a defensive fallback in case fromisoformat ever stops
    #    accepting the space separator (Python 3.10+ explicitly tightens
    #    fromisoformat; this branch covers that future).
    if parsed is None:
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            parsed = parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            parsed = None

    # 4. RFC-2822 (RSS).
    if parsed is None:
        try:
            parsed = parsedate_to_datetime(raw)
            if parsed is not None and parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            parsed = None

    if parsed is None:
        return ""

    # Convert to UTC and emit canonical form. Drop sub-second precision to
    # match prod (existing docs have second-level precision).
    parsed_utc = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return parsed_utc.strftime(ISO_8601_UTC_FORMAT)


# ---------------------------------------------------------------------------
# Fuzzy title dedup (Phase 3.5 Fix 2)
# ---------------------------------------------------------------------------

# A small, conservative English stopword set. Kept intentionally short so the
# fuzzy key still discriminates well — over-aggressive stopword stripping
# starts merging genuinely different stories. Tune via FUZZY_TOKEN_LIMIT
# rather than adding more stopwords if collisions appear.
_FUZZY_STOPWORDS = frozenset({
    "a", "an", "the",
    "of", "to", "in", "on", "for", "at", "by", "from", "with",
    "and", "or", "but", "as",
    "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those",
    "it", "its",
})

# How many content tokens to take from the normalized title. Set deliberately
# generous so that "Congo Ebola outbreak labor with little pay" doesn't
# collide with "Congo Ebola outbreak detected in capital" (different stories
# despite shared first 4 tokens). Phase 3.5 dry-run will tune this if real
# data shows over-merging.
FUZZY_TOKEN_LIMIT: int = 8

# Tokenizer: keep alphanumerics + spaces, strip everything else.
_TOKEN_KEEP = re.compile(r"[^a-z0-9\s]+")


def make_fuzzy_title_key(article: Dict[str, Any]) -> str:
    """
    Build a deterministic fuzzy dedup key from an article's title.

    Pipeline:
      lowercase → strip punctuation → collapse whitespace → drop stopwords
      → take the first FUZZY_TOKEN_LIMIT content tokens → join with spaces.

    Empty/missing title yields the empty string. Callers can treat an empty
    fuzzy key as "no fuzzy match available" (don't dedup on it).

    This is intentionally deterministic and stdlib-only — no LLM, no
    embeddings, no external libraries. The same article always produces the
    same key.
    """
    title = (article.get("title") or "").lower()
    if not title.strip():
        return ""
    # Replace punctuation with spaces so token boundaries are preserved.
    cleaned = _TOKEN_KEEP.sub(" ", title)
    tokens = [t for t in cleaned.split() if t and t not in _FUZZY_STOPWORDS]
    if not tokens:
        return ""
    head = tokens[:FUZZY_TOKEN_LIMIT]
    return " ".join(head)


# ---------------------------------------------------------------------------
# HTML stripping for RSS <description>
# ---------------------------------------------------------------------------

class _TagStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def html_strip(raw: Optional[str]) -> str:
    """
    Convert an HTML fragment (RSS description) to plain text.

    - Returns ``""`` for None / empty.
    - Decodes HTML entities (``&amp;`` → ``&``, etc.).
    - Removes tags but preserves their text content.
    - Collapses runs of whitespace to single spaces and strips edges.

    Stdlib-only; no bs4/lxml dependency.
    """
    if not raw:
        return ""
    text = unescape(raw)
    parser = _TagStripper()
    try:
        parser.feed(text)
        parser.close()
        text = parser.get_text()
    except Exception:
        # HTMLParser is permissive but treat any explosion as best-effort.
        # Falling through to the raw entity-decoded text is safer than raising.
        pass
    # Whitespace normalize.
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Image backfill — fetch og:image / twitter:image from article URLs when the
# provider didn't supply one. Best-effort, time-bounded, fully concurrent.
# ---------------------------------------------------------------------------

# Match <meta property="og:image" content="..."> in either attribute order,
# either quote style. Also matches <meta name="twitter:image" content="...">
# as a fallback. Case-insensitive, dot-matches-newline so attributes can span.
#
# Phase 4 image-backfill helper: when Google News RSS / GDELT / NewsData return
# an article with no image_url, the orchestrator can pull the source URL and
# parse <head> for the standard social-share image meta. This gives the mobile
# app a real article image instead of a "No image available" placeholder.
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)\s*=\s*["\'](?:og:image|og:image:url|twitter:image|twitter:image:src)["\'][^>]*?'
    r'\s+content\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE | re.DOTALL,
)
_OG_IMAGE_RE_REVERSED = re.compile(
    r'<meta[^>]+content\s*=\s*["\']([^"\']+)["\'][^>]*?'
    r'\s+(?:property|name)\s*=\s*["\'](?:og:image|og:image:url|twitter:image|twitter:image:src)["\']',
    re.IGNORECASE | re.DOTALL,
)

# Only download a few hundred KB of <head> bytes; we don't need the whole page
# and many news sites are heavy.
_IMG_FETCH_BYTE_LIMIT = 256 * 1024  # 256 KB
_IMG_FETCH_TIMEOUT_SECONDS = 6.0


def _extract_og_image_from_html(html: str) -> Optional[str]:
    """
    Find the first og:image / twitter:image URL in the given HTML.
    Returns None if no match. Stdlib + regex only — no bs4/lxml.
    """
    if not html:
        return None
    m = _OG_IMAGE_RE.search(html)
    if not m:
        m = _OG_IMAGE_RE_REVERSED.search(html)
    if not m:
        return None
    url = m.group(1).strip()
    # Decode HTML entities in URL attribute values (e.g. &amp; → &).
    url = unescape(url)
    # Sanity: must look like a URL.
    if not url.startswith(("http://", "https://", "//")):
        return None
    if url.startswith("//"):
        url = "https:" + url
    return url


async def _fetch_og_image_for_url(
    client: httpx.AsyncClient,
    page_url: str,
) -> Optional[str]:
    """
    Visit ``page_url``, read the first ~256 KB, extract og:image. Returns
    None if anything goes wrong (timeout, non-2xx, no meta, etc.). Never
    raises out.
    """
    if not page_url:
        return None
    try:
        # GET with size cap: we ask the server for the head bytes via Range,
        # but many news CDNs ignore Range — fall through to standard GET and
        # rely on the response.aread() limit via .read(N).
        async with client.stream(
            "GET",
            page_url,
            headers={
                # Some sites cloak content from headless UAs; pretend to be a
                # standard browser. This is the same UA news aggregators use.
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=_IMG_FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as resp:
            if resp.status_code != 200:
                return None
            # Read up to the byte limit.
            chunks: list[bytes] = []
            total = 0
            async for chunk in resp.aiter_bytes(chunk_size=8192):
                chunks.append(chunk)
                total += len(chunk)
                if total >= _IMG_FETCH_BYTE_LIMIT:
                    break
            body = b"".join(chunks)
        # Best-effort decode — most news pages are UTF-8.
        try:
            html = body.decode("utf-8", errors="replace")
        except Exception:
            return None
        return _extract_og_image_from_html(html)
    except (httpx.TimeoutException, httpx.HTTPError, httpx.RequestError):
        return None
    except Exception:
        # Last-resort catch — never break the orchestrator.
        return None


async def backfill_images_for_articles(
    articles: List[Dict[str, Any]],
    *,
    max_concurrency: int = 8,
    client: Optional[httpx.AsyncClient] = None,
) -> None:
    """
    For each article in ``articles`` where ``image_url`` is missing AND ``url``
    is present, fetch the page and extract og:image. Mutates the articles in
    place — sets ``article["image_url"]`` only if a real image URL is found,
    leaves it as-is otherwise.

    Bounded by ``max_concurrency`` to avoid hitting many news sites at once.
    Total time roughly = (count_needing_image / max_concurrency) * timeout.
    With 60 missing images and concurrency 8 + 6s timeout, worst case = ~45s.
    """
    targets = [a for a in articles if not a.get("image_url") and a.get("url")]
    if not targets:
        return

    logger.info(
        f"[IMG_BACKFILL] {len(targets)} article(s) need images "
        f"(concurrency={max_concurrency}, timeout={_IMG_FETCH_TIMEOUT_SECONDS}s)"
    )

    sem = asyncio.Semaphore(max_concurrency)
    owns_client = client is None

    if owns_client:
        client = httpx.AsyncClient(timeout=_IMG_FETCH_TIMEOUT_SECONDS)

    async def _one(article: Dict[str, Any]) -> None:
        async with sem:
            url = article.get("url") or ""
            img = await _fetch_og_image_for_url(client, url)
            if img:
                article["image_url"] = img

    try:
        await asyncio.gather(*[_one(a) for a in targets], return_exceptions=True)
    finally:
        if owns_client:
            await client.aclose()

    found = sum(1 for a in targets if a.get("image_url"))
    logger.info(f"[IMG_BACKFILL] recovered {found}/{len(targets)} images")
