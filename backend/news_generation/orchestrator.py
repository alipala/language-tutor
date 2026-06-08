"""
News content engine — flag-ON multi-provider orchestrator (Phase 3).

The orchestrator's contract is identical in shape to what
``news_tools.get_diverse_news()`` returns today: a ``list[dict]`` of
8-key article dictionaries (see ``providers/_common.py``). Downstream
(safety eval, variation fan-out, batch insert) reuses Phase 1/2 code
unchanged.

PIPELINE (per category, in catalog order, with a global ``claimed_ids``
running across the whole catalog):

  1.  NewsData primary → afetch_for(descriptor).
      If NEWSDATA_API_KEY is missing, NewsData returns AUTH_MISSING.
  2.  Pool ← articles whose stable id is not in ``claimed_ids`` and
      not already in the in-category pool (dedup by stable id).
  3.  If pool < target_count → Google News RSS backfill, same exclusion.
  4.  If pool < target_count → GDELT tertiary backfill, same exclusion.
  5.  Deterministic selection of up to ``target_count`` from the pool
      (see ``_select_deterministic`` for the exact rule).
  6.  Stamp each selected article's ``category`` with ``descriptor.slot_id``
      and register its stable id in ``claimed_ids`` so later categories
      cannot re-claim it. Order = catalog order = specific-before-general.

The orchestrator never raises. Provider failures surface as typed
``FetchReason`` values and are recorded for the dry-run inventory.

Articles whose ``summary`` is empty or whose ``title`` is empty are
dropped during selection — they cannot drive a useful learning
adaptation downstream. **This is why GDELT alone rarely contributes
selected articles**: GDELT ArtList mode does not include descriptions.
GDELT remains in the chain because it gives us URL + image_url + title
that may later be merged with another provider's summary (Phase 4
enhancement; not done now per the prompt's "optional/best-effort"
authorization).

Concurrency: a single ``asyncio.Semaphore`` (default 10) caps the
number of in-flight provider HTTP calls. Categories are processed
**sequentially** (claiming order matters for dedup), but the three
provider calls inside a single category fall back **lazily** — only
the next provider is invoked when the previous one didn't fill the
target_count.

The orchestrator returns a list of 8-key dicts with ``article_index``
re-numbered 0..N-1 across the whole result set (matches the current
``get_diverse_news`` behavior).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from news_generation.catalog import CATALOG, DEFAULT_TARGET_COUNT
from news_generation.providers import (
    BaseNewsProvider,
    CategoryDescriptor,
    FetchReason,
    GdeltProvider,
    GoogleNewsRssProvider,
    NewsDataProvider,
    ProviderResult,
)
from news_generation.providers._common import (
    backfill_images_for_articles,
    make_fuzzy_title_key,
    make_stable_id,
)

logger = logging.getLogger(__name__)


# --- Concurrency caps -------------------------------------------------------

# Caps the number of in-flight provider HTTP requests. Provider fan-out is
# already category-serial; this guards against bursts when a single category
# triggers multiple fallback hops in quick succession.
NEWS_FETCH_CONCURRENCY: int = 10

# Plumbed for Phase 4's variation pass (4,320 OpenAI calls if all 120
# articles produce a full 6×6 matrix). Defined here so Phase 4 doesn't
# need to invent a name. **Not used in Phase 3.**
NEWS_VARIATION_CONCURRENCY: int = 15

# Phase 3.5 Fix 2: deterministic fuzzy-title dedup across categories.
# When enabled (default), the orchestrator builds a normalized-title key per
# candidate and folds it into the global claiming pass — a story claimed by
# an earlier (more specific) category cannot reappear under a later
# (catch-all) category even if it has a different URL.
#
# Set to False to disable if the heuristic over-merges in practice. The
# stopword set and token limit live in providers/_common.py.
NEWS_FUZZY_DEDUP: bool = True


# --- Per-category bookkeeping for the dry-run inventory --------------------

@dataclass
class CategoryReport:
    """Per-category diagnostics so the --dry-run inventory can explain shortfalls."""

    slot_id: str
    selected_count: int = 0
    target_count: int = 0
    provider_reasons: Dict[str, str] = field(default_factory=dict)
    fell_short: bool = False
    selected_titles: List[str] = field(default_factory=list)


@dataclass
class OrchestratorReport:
    articles: List[Dict[str, Any]]
    per_category: List[CategoryReport]

    @property
    def total_articles(self) -> int:
        return len(self.articles)


# --- Public entry point -----------------------------------------------------

async def fetch_candidates_multi_provider(
    *,
    catalog: Optional[Sequence[CategoryDescriptor]] = None,
    newsdata: Optional[BaseNewsProvider] = None,
    google_news: Optional[BaseNewsProvider] = None,
    gdelt: Optional[BaseNewsProvider] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> List[Dict[str, Any]]:
    """
    Flag-ON multi-provider fetch. Returns a list of 8-key article dicts
    with ``article_index`` renumbered 0..N-1.

    Callers wanting the per-category diagnostics (for ``--dry-run``)
    should use ``fetch_candidates_with_report`` instead.
    """
    report = await fetch_candidates_with_report(
        catalog=catalog,
        newsdata=newsdata,
        google_news=google_news,
        gdelt=gdelt,
        semaphore=semaphore,
    )
    return report.articles


async def fetch_candidates_with_report(
    *,
    catalog: Optional[Sequence[CategoryDescriptor]] = None,
    newsdata: Optional[BaseNewsProvider] = None,
    google_news: Optional[BaseNewsProvider] = None,
    gdelt: Optional[BaseNewsProvider] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> OrchestratorReport:
    """
    Same as ``fetch_candidates_multi_provider`` but also returns
    per-category diagnostics. Used by ``--dry-run``.
    """
    descriptors = list(catalog) if catalog is not None else list(CATALOG)
    nd = newsdata if newsdata is not None else NewsDataProvider()
    gn = google_news if google_news is not None else GoogleNewsRssProvider()
    gd = gdelt if gdelt is not None else GdeltProvider()
    sem = semaphore if semaphore is not None else asyncio.Semaphore(NEWS_FETCH_CONCURRENCY)

    claimed_ids: set[str] = set()
    # Phase 3.5 Fix 2: fuzzy-key set; populated alongside claimed_ids when
    # NEWS_FUZZY_DEDUP is on. Empty when disabled (treated as no-op exclusion).
    claimed_fuzzy_keys: set[str] = set()
    selected: List[Dict[str, Any]] = []
    per_category: List[CategoryReport] = []

    for descriptor in descriptors:
        report = CategoryReport(slot_id=descriptor.slot_id, target_count=descriptor.target_count)
        pool: List[Dict[str, Any]] = []
        pool_ids: set[str] = set()
        pool_fuzzy_keys: set[str] = set()  # per-category fuzzy dedup, paired with pool_ids

        # --- Step 1: NewsData primary ---
        nd_result = await _fetch_safely(nd, descriptor, sem)
        report.provider_reasons["newsdata"] = nd_result.reason.value
        _extend_pool(pool, pool_ids, claimed_ids, nd_result.articles,
                     pool_fuzzy_keys=pool_fuzzy_keys, claimed_fuzzy_keys=claimed_fuzzy_keys)

        # --- Step 2: Google News RSS backfill ---
        # Phase 3.5 Fix 1: the "do we need to backfill?" check now compares
        # against _selectable_ survivors (post-global-dedup, post-empty-filter),
        # not the raw pool size. The Phase 3 dry-run surfaced cases where
        # NewsData returned 6 raw articles but 2 had empty summaries; the raw
        # check said "enough", _select_deterministic later dropped the empties,
        # and the category shipped with 4/6. See forensic in §A of the report.
        if _count_selectable(pool) < descriptor.target_count:
            gn_result = await _fetch_safely(gn, descriptor, sem)
            report.provider_reasons["gnews_rss"] = gn_result.reason.value
            _extend_pool(pool, pool_ids, claimed_ids, gn_result.articles,
                         pool_fuzzy_keys=pool_fuzzy_keys, claimed_fuzzy_keys=claimed_fuzzy_keys)

        # --- Step 3: GDELT tertiary backfill ---
        if _count_selectable(pool) < descriptor.target_count:
            gd_result = await _fetch_safely(gd, descriptor, sem)
            report.provider_reasons["gdelt"] = gd_result.reason.value
            _extend_pool(pool, pool_ids, claimed_ids, gd_result.articles,
                         pool_fuzzy_keys=pool_fuzzy_keys, claimed_fuzzy_keys=claimed_fuzzy_keys)

        # --- Step 4: deterministic take-N ---
        picked = _select_deterministic(pool, descriptor.target_count)
        for art in picked:
            # Stamp the canonical slot_id so consumers see our taxonomy, not
            # whatever the provider returned (e.g. NewsData's "lifestyle"
            # when descriptor was "top_stories").
            art["category"] = descriptor.slot_id
            stable_id = make_stable_id(art)
            claimed_ids.add(stable_id)
            if NEWS_FUZZY_DEDUP:
                fuzzy = make_fuzzy_title_key(art)
                if fuzzy:
                    claimed_fuzzy_keys.add(fuzzy)
            report.selected_titles.append(art.get("title", ""))

        selected.extend(picked)
        report.selected_count = len(picked)
        report.fell_short = report.selected_count < descriptor.target_count
        per_category.append(report)

    # Renumber article_index 0..N-1 across the whole result set, matching the
    # current get_diverse_news behavior expected by news_generator.
    for i, art in enumerate(selected):
        art["article_index"] = i

    return OrchestratorReport(articles=selected, per_category=per_category)


# --- Internals --------------------------------------------------------------

async def _fetch_safely(
    provider: BaseNewsProvider,
    descriptor: CategoryDescriptor,
    semaphore: asyncio.Semaphore,
) -> ProviderResult:
    """
    Run provider.afetch_for under the semaphore and turn any unexpected
    raise into an UNEXPECTED ProviderResult. Provider adapters are required
    not to raise (Phase 2 §3.1), but defense-in-depth is cheap and the
    orchestrator must NEVER let a single category kill the whole run.
    """
    try:
        async with semaphore:
            return await provider.afetch_for(descriptor)
    except Exception as e:  # pragma: no cover — providers contract is no-raise
        logger.exception("[ORCHESTRATOR] %s raised on slot=%s — defensive catch",
                         provider.name, descriptor.slot_id)
        return ProviderResult(reason=FetchReason.UNEXPECTED, error_detail=type(e).__name__)


def _is_selectable(article: Dict[str, Any]) -> bool:
    """
    Predicate matching `_select_deterministic`'s drop rule: title and summary
    must both be non-empty/non-whitespace. Centralized so the backfill check
    (Phase 3.5 Fix 1) and the selection step agree on what "selectable" means.
    """
    return bool((article.get("title") or "").strip()) and bool((article.get("summary") or "").strip())


def _count_selectable(pool: List[Dict[str, Any]]) -> int:
    """Number of articles in ``pool`` that would survive `_select_deterministic`."""
    return sum(1 for a in pool if _is_selectable(a))


def _extend_pool(
    pool: List[Dict[str, Any]],
    pool_ids: set[str],
    claimed_ids: set[str],
    incoming: List[Dict[str, Any]],
    *,
    pool_fuzzy_keys: Optional[set[str]] = None,
    claimed_fuzzy_keys: Optional[set[str]] = None,
) -> None:
    """
    Add ``incoming`` articles to ``pool`` while honoring:
      - URL-based global dedup via ``claimed_ids``,
      - URL-based per-category dedup via ``pool_ids``,
      - (Phase 3.5 Fix 2, optional) fuzzy-title global dedup via
        ``claimed_fuzzy_keys``, and per-category fuzzy dedup via
        ``pool_fuzzy_keys``, gated by ``NEWS_FUZZY_DEDUP``.

    The fuzzy step prevents the same story (different URL) being selected
    by two categories. Fuzzy keys are only consulted when ``NEWS_FUZZY_DEDUP``
    is True; when False, the function preserves Phase-3 URL-only behavior.
    An empty fuzzy key (untitled article) is always allowed through — Fix 2
    is conservative and never blocks an article on missing fuzzy data.
    """
    fuzzy_on = NEWS_FUZZY_DEDUP and pool_fuzzy_keys is not None and claimed_fuzzy_keys is not None
    for art in incoming:
        sid = make_stable_id(art)
        if sid in claimed_ids or sid in pool_ids:
            continue
        if fuzzy_on:
            fkey = make_fuzzy_title_key(art)
            if fkey and (fkey in claimed_fuzzy_keys or fkey in pool_fuzzy_keys):
                continue
            if fkey:
                pool_fuzzy_keys.add(fkey)
        pool_ids.add(sid)
        pool.append(art)


def _select_deterministic(
    pool: List[Dict[str, Any]],
    target_count: int,
) -> List[Dict[str, Any]]:
    """
    Pick up to ``target_count`` articles from ``pool``, deterministically.

    Steps (must remain deterministic — the corresponding test pins this):

      1. Drop articles where ``title`` is empty/whitespace OR ``summary``
         is empty/whitespace. Both are required for the downstream
         language-learning adaptation to produce anything useful, and
         their absence is the easiest signal of a poor-quality fetch.

      2. Sort by ``published_at`` DESCENDING (most-recent first). If
         ``published_at`` is empty, treat as oldest (empty string sorts
         before any non-empty string). Tie-break by ``make_stable_id``
         ASCENDING so the order is fully deterministic given a fixed pool.

      3. Source-diversity pass: greedily walk the sorted list and pick
         articles whose ``source`` we haven't picked yet. Once every
         distinct source in the pool has been picked once (or the pool
         is exhausted), continue picking the next-most-recent articles
         without the diversity constraint. This keeps the most recent
         article from a source, then the next most recent from a *different*
         source, until we run out of distinct sources, then resumes normal
         order.

      4. Take the first ``target_count`` from the diversity-ordered list.
         If the post-filter pool is shorter than ``target_count``, return
         what we have. **Never fabricate.**
    """
    # 1. Quality filter — same predicate the backfill check uses.
    cleaned = [a for a in pool if _is_selectable(a)]
    if not cleaned:
        return []

    # 2. Deterministic ordering: most recent first, tie-break by stable id.
    def _sort_key(a: Dict[str, Any]) -> tuple[str, str]:
        published = a.get("published_at") or ""
        # Negate semantically by inverting in the comparator below; here we
        # just return the tuple. We use sorted(... reverse=True) on published
        # first, then a secondary sort by stable id ASC. Two-pass sort:
        return (published, make_stable_id(a))

    # Sort by stable id ascending (secondary key, stable), then by
    # published_at descending (primary key, sort is stable so secondary order
    # is preserved within ties).
    cleaned.sort(key=lambda a: make_stable_id(a))
    cleaned.sort(key=lambda a: a.get("published_at") or "", reverse=True)

    # 3. Source-diversity greedy pass.
    picked: List[Dict[str, Any]] = []
    seen_sources: set[str] = set()
    deferred: List[Dict[str, Any]] = []

    for art in cleaned:
        source = art.get("source") or ""
        if source not in seen_sources:
            picked.append(art)
            seen_sources.add(source)
        else:
            deferred.append(art)
        if len(picked) >= target_count:
            break

    # If we still haven't hit target_count, the diversity constraint is now
    # exhausted (every distinct source was used). Take the most-recent
    # remaining articles (deferred list is already in the right order).
    if len(picked) < target_count:
        picked.extend(deferred[: target_count - len(picked)])

    return picked[:target_count]
