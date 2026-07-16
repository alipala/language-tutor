"""
Deterministic memory mapper for PROFILE_STORY_V1.

Produces "story moments" from data already persisted in the DB. Never calls
an LLM. Never regenerates analysis. Sessions without `enhanced_analysis` are
skipped gracefully.

Moment types (deterministic):
  - breakthrough → speaking_breakthroughs (per language)
  - milestone    → calculate_milestones thresholds + CEFR level-ups (by_language.highest_level)
  - proud        → conversation_sessions.enhanced_analysis.ai_insights.breakthrough_moments[0]
                   (fallback: speaking_breakthroughs.title when no per-session quote exists)
  - first        → first conversation_session per (mode × language):
                     • news  — earliest conversation_type == "news"
                     • free  — earliest conversation_type == "practice" (or untagged)
                     • plan  — earliest learning_plans.created_at per language
                     • game  — earliest challenge_session per language

Each moment has a stable ID so the mobile client can dedupe across pagination.

Grouping: by user-local date relative to "today":
  - this_week  : last 7 days
  - this_month : 8..30 days
  - earlier    : 31+ days

Per the spec, bounded scans (last ~50 conv sessions per language) and
support for ?before=&limit= pagination on older groups.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo
import hashlib
import logging

from services.timezone_utils import get_user_timezone_obj
from services.profile_story.language_normalizer import (
    canonical_code,
    canonical_name,
    language_match_filter,
)

logger = logging.getLogger(__name__)

# Bound the per-language scan. Spec §R6: ~50.
RECENT_SESSIONS_BOUND = 50
# CEFR ordering, low → high.
CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _stable_id(*parts: str) -> str:
    h = hashlib.sha1(("|".join(parts)).encode("utf-8")).hexdigest()
    return h[:16]


def _to_iso(dt: Any) -> Optional[str]:
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
    if isinstance(dt, str):
        return dt
    return None


def _local_date(dt: Any, tz: str) -> Optional[str]:
    if not isinstance(dt, datetime):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    try:
        return dt.astimezone(get_user_timezone_obj(tz)).strftime("%Y-%m-%d")
    except Exception:
        return None


def _group_for(local_date: str, today_local: str) -> str:
    try:
        d1 = datetime.strptime(local_date, "%Y-%m-%d")
        d2 = datetime.strptime(today_local, "%Y-%m-%d")
        days = (d2 - d1).days
        if days <= 6:
            return "this_week"
        if days <= 29:
            return "this_month"
        return "earlier"
    except Exception:
        return "earlier"


def _cefr_index(level: Optional[str]) -> int:
    if not level:
        return -1
    try:
        return CEFR_ORDER.index(level.upper())
    except Exception:
        return -1


async def build_story(
    *,
    user_id: str,
    user_doc: dict,
    language: Optional[str],
    timezone_str: str,
    before: Optional[str],  # ISO datetime cursor for pagination of older groups
    limit: int,
    conversation_sessions_collection: Any,
    challenge_sessions_collection: Any,
    speaking_breakthroughs_collection: Any,
    learning_plans_collection: Any,
) -> dict:
    """
    Build the `story` response block: total + groups.

    `before` paginates moments OLDER than the supplied ISO datetime; the
    `limit` caps how many moments are returned in older groups. The two
    most recent groups (this_week, this_month) are always returned in full
    so the collapsed default UI feels complete.
    """
    today_local = datetime.now(get_user_timezone_obj(timezone_str)).strftime("%Y-%m-%d")
    cutoff_dt = None
    if before:
        try:
            cutoff_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
            if cutoff_dt.tzinfo is None:
                cutoff_dt = cutoff_dt.replace(tzinfo=ZoneInfo("UTC"))
        except Exception:
            cutoff_dt = None

    moments: list[dict] = []

    moments.extend(
        await _breakthrough_moments(
            user_id=user_id,
            language=language,
            timezone_str=timezone_str,
            today_local=today_local,
            cutoff_dt=cutoff_dt,
            speaking_breakthroughs_collection=speaking_breakthroughs_collection,
        )
    )
    moments.extend(
        _milestone_moments(
            user_doc=user_doc,
            language=language,
            timezone_str=timezone_str,
            today_local=today_local,
            cutoff_dt=cutoff_dt,
        )
    )
    moments.extend(
        await _proud_moments(
            user_id=user_id,
            language=language,
            timezone_str=timezone_str,
            today_local=today_local,
            cutoff_dt=cutoff_dt,
            conversation_sessions_collection=conversation_sessions_collection,
            speaking_breakthroughs_collection=speaking_breakthroughs_collection,
        )
    )
    moments.extend(
        await _first_moments(
            user_id=user_id,
            language=language,
            timezone_str=timezone_str,
            today_local=today_local,
            cutoff_dt=cutoff_dt,
            conversation_sessions_collection=conversation_sessions_collection,
            challenge_sessions_collection=challenge_sessions_collection,
            learning_plans_collection=learning_plans_collection,
        )
    )

    # Dedupe by id (stable across runs), sort by date desc.
    by_id: dict[str, dict] = {}
    for m in moments:
        if not m.get("id") or not m.get("date"):
            continue
        by_id.setdefault(m["id"], m)
    sorted_moments = sorted(by_id.values(), key=lambda m: m["date"], reverse=True)

    # Group
    groups: dict[str, list[dict]] = {"this_week": [], "this_month": [], "earlier": []}
    for m in sorted_moments:
        local_d = _local_date(_parse_iso(m["date"]), timezone_str) or today_local
        g = _group_for(local_d, today_local)
        groups[g].append(m)

    # Cap older group by limit (pagination); top groups are full.
    if limit > 0:
        groups["earlier"] = groups["earlier"][:limit]

    total = sum(len(v) for v in groups.values())

    return {
        "total": total,
        "groups": [
            {"key": "this_week", "label": "This week", "moments": groups["this_week"]},
            {"key": "this_month", "label": "This month", "moments": groups["this_month"]},
            {"key": "earlier", "label": "Earlier", "moments": groups["earlier"]},
        ],
    }


def _parse_iso(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))


# ──────────────────────────────────────────────────────────────────────────
# breakthrough — from speaking_breakthroughs (one type in prod: confidence_level_up)
# ──────────────────────────────────────────────────────────────────────────

async def _breakthrough_moments(
    *,
    user_id: str,
    language: Optional[str],
    timezone_str: str,
    today_local: str,
    cutoff_dt: Optional[datetime],
    speaking_breakthroughs_collection: Any,
) -> list[dict]:
    if speaking_breakthroughs_collection is None:
        return []
    q: dict = {"user_id": user_id}
    if language:
        q["language"] = {"$in": language_match_filter(language)}
    if cutoff_dt is not None:
        q["created_at"] = {"$lt": cutoff_dt}
    out: list[dict] = []
    try:
        async for b in speaking_breakthroughs_collection.find(q).sort("created_at", -1).limit(RECENT_SESSIONS_BOUND):
            lang_norm = canonical_code(b.get("language")) or ""
            title = b.get("title") or "Breakthrough"
            metrics = b.get("metrics") or {}
            before_lvl = (metrics.get("before") or {}).get("level")
            after_lvl = (metrics.get("after") or {}).get("level")
            if before_lvl and after_lvl:
                line = f"You moved from {before_lvl} to {after_lvl}."
                share_quote = f"My speaking confidence in {(canonical_name(b.get('language')) or '').capitalize()} just leveled up: {before_lvl} → {after_lvl}."
            else:
                line = b.get("description") or "A confidence shift you earned."
                share_quote = title
            iso = _to_iso(b.get("created_at"))
            if not iso:
                continue
            out.append({
                "id": _stable_id("breakthrough", str(b.get("_id"))),
                "type": "breakthrough",
                "mode": None,
                "language": lang_norm,
                "date": iso,
                "title": title,
                "line": line,
                "share_quote": share_quote,
                "icon": "spark",
            })
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] breakthrough scan failed: {e}")
    return out


# ──────────────────────────────────────────────────────────────────────────
# milestone — from CEFR level-ups + challenge-count thresholds
# ──────────────────────────────────────────────────────────────────────────

def _milestone_moments(
    *,
    user_doc: dict,
    language: Optional[str],
    timezone_str: str,
    today_local: str,
    cutoff_dt: Optional[datetime],
) -> list[dict]:
    """
    CEFR level reach moments are deterministic from `users.stats.lifetime.by_language[lang].highest_level`.
    We can't recover the timestamp of the level-up, so we anchor it to
    `last_practiced` for that language as a best-available stamp.

    Challenge-count thresholds: we only emit ONE — the most recently reached one
    (current → previous milestone), keyed off `last_practice_date` for now since
    sessions don't carry the cross-threshold timestamp either.
    """
    out: list[dict] = []
    lifetime = (user_doc.get("stats") or {}).get("lifetime") or {}
    by_lang: dict[str, Any] = lifetime.get("by_language") or {}

    # CEFR level reach moments (per language)
    for lang_name, lang_data in by_lang.items():
        if language and canonical_name(language) != canonical_name(lang_name):
            continue
        if not isinstance(lang_data, dict):
            continue
        highest_level = lang_data.get("highest_level")
        if not highest_level or _cefr_index(highest_level) < 0:
            continue
        last_practiced = lang_data.get("last_practiced")
        iso = _to_iso(last_practiced)
        if not iso:
            continue
        if cutoff_dt is not None:
            try:
                d = _parse_iso(iso)
                if d >= cutoff_dt:
                    continue
            except Exception:
                pass
        out.append({
            "id": _stable_id("milestone", "cefr", lang_name, highest_level),
            "type": "milestone",
            "mode": None,
            "language": canonical_code(lang_name) or lang_name,
            "date": iso,
            "title": f"You reached {highest_level}",
            "line": f"Your {(canonical_name(lang_name) or lang_name).capitalize()} hit {highest_level} — a real CEFR step.",
            "share_quote": f"I reached {highest_level} in {(canonical_name(lang_name) or lang_name).capitalize()}.",
            "icon": "trophy",
        })

    # Most-recent passed challenge-count milestone, language-agnostic so emit only when language is None.
    if language is None:
        total_challenges = int(lifetime.get("total_challenges") or 0)
        thresholds = [100, 250, 500, 1000, 2000, 5000]
        reached = [t for t in thresholds if total_challenges >= t]
        if reached:
            t = reached[-1]
            stamp_src = (user_doc.get("stats") or {}).get("last_practice_date")
            iso = None
            if isinstance(stamp_src, str):
                # daily-date string → make a noon UTC iso for stability
                try:
                    iso = datetime.strptime(stamp_src, "%Y-%m-%d").replace(
                        hour=12, tzinfo=ZoneInfo("UTC")
                    ).isoformat().replace("+00:00", "Z")
                except Exception:
                    iso = None
            if not iso:
                iso = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
            if cutoff_dt is None or _parse_iso(iso) < cutoff_dt:
                out.append({
                    "id": _stable_id("milestone", "challenges", str(t)),
                    "type": "milestone",
                    "mode": "game",
                    "language": "",
                    "date": iso,
                    "title": f"{t:,} challenges in",
                    "line": f"You've cleared {total_challenges:,} challenges so far.",
                    "share_quote": f"I've cleared {total_challenges:,} speaking challenges with MyTacoAI.",
                    "icon": "target",
                })
    return out


# ──────────────────────────────────────────────────────────────────────────
# proud — from enhanced_analysis.ai_insights.breakthrough_moments[]
#         fallback: speaking_breakthroughs.title (sparse-user safety net)
# ──────────────────────────────────────────────────────────────────────────

async def _proud_moments(
    *,
    user_id: str,
    language: Optional[str],
    timezone_str: str,
    today_local: str,
    cutoff_dt: Optional[datetime],
    conversation_sessions_collection: Any,
    speaking_breakthroughs_collection: Any,
) -> list[dict]:
    if conversation_sessions_collection is None:
        return []
    q: dict = {"user_id": user_id, "enhanced_analysis": {"$ne": None, "$exists": True}}
    if language:
        q["language"] = {"$in": language_match_filter(language)}
    if cutoff_dt is not None:
        q["created_at"] = {"$lt": cutoff_dt}
    out: list[dict] = []
    try:
        cursor = (
            conversation_sessions_collection.find(
                q,
                {"_id": 1, "created_at": 1, "language": 1, "enhanced_analysis.ai_insights": 1, "conversation_type": 1},
            )
            .sort("created_at", -1)
            .limit(RECENT_SESSIONS_BOUND)
        )
        async for s in cursor:
            ea = (s.get("enhanced_analysis") or {})
            ai = (ea.get("ai_insights") or {})
            bms = ai.get("breakthrough_moments") or []
            if not bms:
                continue
            quote = next((str(x).strip() for x in bms if isinstance(x, str) and str(x).strip()), None)
            if not quote:
                continue
            iso = _to_iso(s.get("created_at"))
            if not iso:
                continue
            lang_norm = canonical_code(s.get("language")) or ""
            mode = "news" if s.get("conversation_type") == "news" else "free"
            out.append({
                "id": _stable_id("proud", str(s.get("_id"))),
                "type": "proud",
                "mode": mode,
                "language": lang_norm,
                "date": iso,
                "title": "A proud moment",
                "line": quote,
                "share_quote": quote,
                "icon": "heart",
            })
    except Exception as e:
        logger.warning(f"[PROFILE_STORY] proud scan failed: {e}")

    # Fallback for thin users — if NO proud moments and we have breakthroughs,
    # surface those titles as "proud" type so the timeline has signal.
    if not out and speaking_breakthroughs_collection is not None:
        q2: dict = {"user_id": user_id}
        if language:
            q2["language"] = {"$in": language_match_filter(language)}
        if cutoff_dt is not None:
            q2["created_at"] = {"$lt": cutoff_dt}
        try:
            async for b in speaking_breakthroughs_collection.find(q2).sort("created_at", -1).limit(3):
                iso = _to_iso(b.get("created_at"))
                if not iso:
                    continue
                title = b.get("title") or "A proud moment"
                out.append({
                    "id": _stable_id("proud-fallback", str(b.get("_id"))),
                    "type": "proud",
                    "mode": None,
                    "language": canonical_code(b.get("language")) or "",
                    "date": iso,
                    "title": "A proud moment",
                    "line": title,
                    "share_quote": title,
                    "icon": "heart",
                })
        except Exception:
            pass

    return out


# ──────────────────────────────────────────────────────────────────────────
# first — first session per (mode × language)
# ──────────────────────────────────────────────────────────────────────────

async def _first_moments(
    *,
    user_id: str,
    language: Optional[str],
    timezone_str: str,
    today_local: str,
    cutoff_dt: Optional[datetime],
    conversation_sessions_collection: Any,
    challenge_sessions_collection: Any,
    learning_plans_collection: Any,
) -> list[dict]:
    out: list[dict] = []

    # Determine which languages to consider.
    if language:
        target_languages: set[str] = {canonical_name(language)}  # type: ignore[arg-type]
        target_languages.discard(None)  # type: ignore[arg-type]
    else:
        target_languages = set()
        # Discover languages from session collections (cheaper + truer than lifetime.by_language).
        try:
            target_languages |= {
                canonical_name(x) for x in (await conversation_sessions_collection.distinct("language", {"user_id": user_id}))
                if canonical_name(x)
            }
        except Exception:
            pass
        try:
            target_languages |= {
                canonical_name(x) for x in (await challenge_sessions_collection.distinct("language", {"user_id": user_id}))
                if canonical_name(x)
            }
        except Exception:
            pass

    for lang_name in target_languages:
        lang_variants = language_match_filter(lang_name)
        lang_code = canonical_code(lang_name) or lang_name

        # first FREESTYLE / NEWS conversation
        try:
            free_doc = await conversation_sessions_collection.find_one(
                {"user_id": user_id, "language": {"$in": lang_variants},
                 "$or": [{"conversation_type": {"$ne": "news"}}, {"conversation_type": {"$exists": False}}]},
                sort=[("created_at", 1)],
            )
            news_doc = await conversation_sessions_collection.find_one(
                {"user_id": user_id, "language": {"$in": lang_variants}, "conversation_type": "news"},
                sort=[("created_at", 1)],
            )
        except Exception as e:
            logger.warning(f"[PROFILE_STORY] first conv scan failed: {e}")
            free_doc = news_doc = None

        # first GAME (challenge)
        try:
            game_doc = await challenge_sessions_collection.find_one(
                {"user_id": user_id, "language": {"$in": lang_variants}},
                sort=[("start_time", 1)],
            )
        except Exception:
            game_doc = None

        # first PLAN (learning_plans created_at per language).
        # Exclude archived plans — a deleted plan should not ghost as
        # "Your first Dutch plan" when the user has started fresh.
        try:
            plan_doc = await learning_plans_collection.find_one(
                {"user_id": user_id, "language": {"$in": lang_variants},
                 "status": {"$ne": "archived"}},
                sort=[("created_at", 1)],
            )
        except Exception:
            plan_doc = None

        for mode, doc, date_field in (
            ("free", free_doc, "created_at"),
            ("news", news_doc, "created_at"),
            ("game", game_doc, "start_time"),
            ("plan", plan_doc, "created_at"),
        ):
            if not doc:
                continue
            iso = _to_iso(doc.get(date_field) or doc.get("created_at"))
            if not iso:
                continue
            if cutoff_dt is not None and _parse_iso(iso) >= cutoff_dt:
                continue
            pretty_lang = (canonical_name(lang_name) or lang_name).capitalize()
            label = {
                "free": f"Your first {pretty_lang} conversation",
                "news": f"Your first {pretty_lang} news session",
                "game": f"Your first {pretty_lang} challenge",
                "plan": f"Your first {pretty_lang} plan",
            }[mode]
            moment: dict = {
                "id": _stable_id("first", mode, lang_name or ""),
                "type": "first",
                "mode": mode,
                "language": lang_code,
                "date": iso,
                "title": label,
                "line": f"This is where your {pretty_lang} story began.",
                "share_quote": label,
                "icon": "seed",
            }
            # Surface the specific challenge type for "first game" moments so
            # the mobile screen can render the matching Games-lobby icon
            # (timer / bulb / albums / search / layers / book). Additive
            # optional field — existing consumers ignoring it stay correct.
            if mode == "game":
                ct = doc.get("challenge_type")
                if isinstance(ct, str) and ct:
                    moment["game_type"] = ct
            out.append(moment)

    return out
