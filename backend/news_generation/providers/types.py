"""
Shared types for Phase 2+ news providers.

Two small primitives, deliberately data-only:

1. CategoryDescriptor — what the orchestrator hands to a provider when it
   wants articles for some semantic category. The shape is generic enough
   that Phase 3 can finalize a 20-category catalog (config-driven) without
   changing any provider's signature.

2. ProviderResult / FetchReason — every provider's fetch returns ``[]`` on
   failure (never raises), and *also* records a typed reason for that empty
   result so unit tests can assert on it and Phase 3 can implement smart
   fallback chains (e.g. "NewsData said RATE_LIMITED → switch to Google News
   RSS for this category").

Both are intentionally not Pydantic models: keep providers usable from sync
unit-test code without extra deps, and avoid serialization confusion with
the 8-key article dict (which stays a plain dict, see ``providers/base.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DescriptorKind(str, Enum):
    """How to query the provider for a CategoryDescriptor."""

    CATEGORY = "category"  # provider-native taxonomy slot (e.g. NewsData category=technology)
    QUERY = "q"            # free-text search (e.g. q="space" for the SPACE category)


@dataclass(frozen=True)
class CategoryDescriptor:
    """
    Generic instruction set: "give me articles for THIS slot."

    Examples (Phase 3 will produce these from config; Phase 2 just consumes them):
        CategoryDescriptor(slot_id="technology",  kind=CATEGORY, value="technology")
        CategoryDescriptor(slot_id="ai",          kind=QUERY,    value="artificial intelligence")
        CategoryDescriptor(slot_id="football",    kind=QUERY,    value="football OR soccer")

    target_count is advisory — providers may return fewer (Phase 3 falls back).
    """

    slot_id: str          # internal id used by orchestrator/dedup (e.g. "ai")
    kind: DescriptorKind  # how to translate this into a provider request
    value: str            # category slug OR free-text query, depending on kind
    target_count: int = 6  # default per Phase-3 plan; provider may cap lower


class FetchReason(str, Enum):
    """Typed outcome reason for a provider fetch. Drives logs + tests + Phase 3 fallback policy."""

    OK = "ok"
    EMPTY = "empty"                 # provider responded fine, just no articles
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_4XX = "http_4xx"           # non-429 client error
    HTTP_5XX = "http_5xx"
    RATE_LIMITED = "rate_limited"   # 429 specifically
    PARSE_ERROR = "parse_error"     # JSON or RSS-XML couldn't be decoded
    AUTH_MISSING = "auth_missing"   # required API key not configured
    UNEXPECTED = "unexpected"       # anything else; the catch-all that must never raise out


@dataclass
class ProviderResult:
    """
    What a Phase-2 provider returns from fetch().

    ``articles`` is always a list (possibly empty) of 8-key dicts.
    ``reason`` is the typed outcome — providers MUST set this even on success.
    ``error_detail`` is an optional short string for log/test inspection
    (e.g. the HTTP status code, the exception type name). Never include
    sensitive data (api keys, full response bodies).
    """

    articles: List[Dict[str, Any]] = field(default_factory=list)
    reason: FetchReason = FetchReason.OK
    error_detail: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.reason == FetchReason.OK

    def __bool__(self) -> bool:  # truthy iff we got something usable
        return bool(self.articles)
