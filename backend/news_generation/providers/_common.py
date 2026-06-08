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

import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any, Dict, Optional


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
