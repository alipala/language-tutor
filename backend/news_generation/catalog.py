"""
News content engine — 20-category catalog (Phase 3).

The orchestrator iterates this list in order. Order is intentional:
**specific → general**. Niche categories (ai, space, gaming, world_cup,
etc.) claim their articles first; catch-all categories (business, world,
top_stories) come last so they only sweep up what's left. This is the
"claiming-order" rule documented in §4.3 of the Phase 3 prompt: global
dedup means an article claimed by `ai` is no longer available to
`technology` or `top_stories`, even if it would have matched both.

All entries use ``target_count=6`` (matches the simplified plan's
"20 categories × 6 articles = 120 articles/day" target). Tuning the
per-category target later is a one-line change.

Each descriptor's ``slot_id`` is what appears in the article's
``original.category`` field once selected — the canonical taxonomy
the mobile app and read endpoints already understand (Phase 0 §2.2).
``value`` is provider-fed (NewsData category slug or free-text query).
``kind`` chooses the provider call mode (CATEGORY vs QUERY).
"""

from __future__ import annotations

from typing import List, Tuple

from news_generation.providers.types import CategoryDescriptor, DescriptorKind

# Target articles per category. Tuning surface for Phase 4+.
DEFAULT_TARGET_COUNT = 6

# Catalog: ordered specific → general. **Do not reorder without re-reading
# §4.3** — claiming order materially affects which category gets a multi-
# match article. See module docstring.
#
# Format: (slot_id, kind, value)
_CATALOG_RAW: List[Tuple[str, DescriptorKind, str]] = [
    ("technology",   DescriptorKind.CATEGORY, "technology"),
    ("ai",           DescriptorKind.QUERY,    "artificial intelligence"),
    ("science",      DescriptorKind.CATEGORY, "science"),
    ("space",        DescriptorKind.QUERY,    "space astronomy"),
    ("health",       DescriptorKind.CATEGORY, "health"),
    ("environment",  DescriptorKind.CATEGORY, "environment"),
    ("sports",       DescriptorKind.CATEGORY, "sports"),
    # SEASONAL: world_cup is a temporary slot for the 2026 FIFA World Cup
    # (Jun 11 – Jul 19, 2026). After 2026-07-19 revert this slot to
    # ``("football", QUERY, "football leagues transfers")`` — one-line change.
    ("world_cup",    DescriptorKind.QUERY,    "FIFA World Cup 2026"),
    ("culture",      DescriptorKind.QUERY,    "arts culture"),
    ("film_tv",      DescriptorKind.CATEGORY, "entertainment"),
    ("music",        DescriptorKind.QUERY,    "music"),
    ("gaming",       DescriptorKind.QUERY,    "video games"),
    ("food",         DescriptorKind.CATEGORY, "food"),
    ("travel",       DescriptorKind.CATEGORY, "tourism"),
    ("lifestyle",    DescriptorKind.CATEGORY, "lifestyle"),
    ("education",    DescriptorKind.CATEGORY, "education"),
    ("money",        DescriptorKind.QUERY,    "personal finance money"),
    # Catch-alls — claim last so specific categories above keep their matches.
    ("business",     DescriptorKind.CATEGORY, "business"),
    ("world",        DescriptorKind.CATEGORY, "world"),
    ("top_stories",  DescriptorKind.CATEGORY, "top"),
]


def build_catalog(target_count: int = DEFAULT_TARGET_COUNT) -> List[CategoryDescriptor]:
    """Return the 20-category catalog as a list of CategoryDescriptor objects."""
    return [
        CategoryDescriptor(slot_id=slot_id, kind=kind, value=value, target_count=target_count)
        for slot_id, kind, value in _CATALOG_RAW
    ]


# Eagerly-built default. Most callers want this; rebuild via build_catalog()
# only if a non-default target_count is needed.
CATALOG: List[CategoryDescriptor] = build_catalog()

# Public expectation pinned by name so tests can assert it without rebuilding.
CATALOG_SIZE = 20
assert len(CATALOG) == CATALOG_SIZE, (
    f"CATALOG must contain exactly {CATALOG_SIZE} entries; found {len(CATALOG)}"
)
