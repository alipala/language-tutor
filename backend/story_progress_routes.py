"""
Story Worlds — series model + per-user progress (Phase 1).

Adds the episode/series layer on top of the existing single-player worlds, and
saves each user's place so they resume exactly where they left off.

Collections:
  story_series    — the "show": ordered list of episode (world) ids
  story_worlds    — each doc = one EPISODE (existing; gains series_id/episode_number)
  story_progress  — one doc per (user, series): cursor + stars + xp

All endpoints are ADDITIVE — the existing /api/story-worlds/{id} and /turn are
untouched. Unlock state is DERIVED server-side (never stored → never stale).
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import database
from auth import get_current_user
from services.stats_service import credit_games_xp
from services.timezone_utils import get_local_datetime_now, get_user_timezone_obj

logger = logging.getLogger(__name__)
router = APIRouter(tags=["story-progress"])

# ── DAILY DRIP — one episode per day ────────────────────────────────────────
# When on (default), finishing an episode locks the NEXT one until midnight in the
# user's local timezone ("come back tomorrow"). This paces a 5-episode series over
# ~5 days, turning the feature into a daily-return habit (a serialized mini-series
# instead of a one-sitting binge). Reversible: STORY_DAILY_DRIP=0 restores the old
# instant-unlock behaviour (next episode playable immediately on completion).
STORY_DAILY_DRIP = os.getenv("STORY_DAILY_DRIP", "1") != "0"

# ── SINGLE ACTIVE SERIES — Netflix "one show at a time" ─────────────────────
# When on (default), the lobby shows ONE series at a time. While a series is in
# progress the rest of the catalog is HIDDEN (not listed at all) so the player
# stays on the show they're watching — one episode a day. When no series is in
# progress the FULL catalog is returned so they can browse/filter/pick the next
# one. A new series opens only after the active one is finished. Combined with the
# daily-episode drip this makes "one episode a day" a real per-USER cap (a 1000-story
# library can't be binged). STORY_SINGLE_ACTIVE_SERIES=0 → old behaviour (the whole
# catalog is always listed, every series independently playable).
STORY_SINGLE_ACTIVE_SERIES = os.getenv("STORY_SINGLE_ACTIVE_SERIES", "1") != "0"


def _next_day_unlock(user_timezone: str) -> datetime:
    """UTC instant of the next local midnight in the user's timezone (the moment the
    next episode becomes available). Computed in local time, returned as UTC."""
    try:
        local_now = get_local_datetime_now(user_timezone)
        tz = get_user_timezone_obj(user_timezone)
        local_midnight = (local_now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        # ensure tz-aware in the user's zone, then convert to UTC for storage
        if local_midnight.tzinfo is None:
            local_midnight = local_midnight.replace(tzinfo=tz)
        return local_midnight.astimezone(timezone.utc)
    except Exception as e:  # noqa: BLE001 — never block completion on a tz hiccup
        logger.warning("[STORY-DRIP] unlock-time calc failed (%s) — 24h fallback", e)
        return datetime.now(timezone.utc) + timedelta(hours=24)

series_collection = database.story_series
worlds_collection = database.story_worlds
progress_collection = database.story_progress

# ── Story Worlds XP economy (server-authoritative) ──────────────────────────
# One scene ≈ one game question, but the scene is a richer, typed exchange in the
# flagship game, so it carries a small premium of 10 XP/scene + a 20 XP episode-
# complete bonus. Episodes now run 8 scenes (A1/A2) or 10 (B1/B2), so an episode is
# ~100-120 XP and a 5-episode series ≈ 5×(100..120) + 50 finale ≈ 550-650 XP. The
# math is fully dynamic (per-scene + flat bonuses), so changing scene counts needs
# NO code change here. Flat values — NO CEFR / hint / combo scaling — so the
# games-level currency stays consistent with quick games (A1 and C2 earn the same).
# These feed `xp_by_source.challenges`, the exact bucket the Games-tab level reads.
STORY_XP_PER_SCENE = 10        # first clear of a scene
STORY_XP_EPISODE_BONUS = 20    # first completion of an episode (→ episode = 70)
STORY_XP_FINALE_BONUS = 50     # first completion of the final episode (series done)


def _clean(v):
    from bson import ObjectId
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_clean(x) for x in v]
    return v


# ---------------------------------------------------------------------------
# Progress doc helpers
# ---------------------------------------------------------------------------
async def _get_or_create_progress(user_id: str, series_id: str, language: str, level: str) -> dict:
    doc = await progress_collection.find_one({"user_id": user_id, "series_id": series_id})
    if doc:
        return doc
    doc = {
        "_id": f"{user_id}:{series_id}",
        "user_id": user_id,
        "series_id": series_id,
        "language": language,
        "level": level,
        "status": "not_started",
        "completed_episodes": [],
        "total_xp": 0,
        "total_stars": 0,
        "current": None,
        "episodes": {},
        "created_at": datetime.now(timezone.utc),
        "last_played_at": datetime.now(timezone.utc),
    }
    await progress_collection.insert_one(doc)
    return doc


def _parse_dt(v) -> Optional[datetime]:
    """Coerce a stored value (datetime or ISO string) to a tz-aware UTC datetime."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _episode_state(ep_number: int, completed: list, first_unfinished: Optional[int],
                   unlocked_at: Optional[datetime] = None) -> str:
    """Derive lock state: completed | current | time_locked | locked.

    `time_locked` = the next episode the user has earned, but it is daily-drip gated
    until `unlocked_at` (their next local midnight). It becomes `current` once that
    instant passes. With STORY_DAILY_DRIP off, unlocked_at is never set so this never
    fires and behaviour is the old sequential unlock."""
    if ep_number in completed:
        return "completed"
    if ep_number == first_unfinished:
        ua = _parse_dt(unlocked_at)
        if ua and datetime.now(timezone.utc) < ua:
            return "time_locked"
        return "current"
    return "locked"


# ---------------------------------------------------------------------------
# PUBLIC — series list, series detail (with derived unlock state), continue
# ---------------------------------------------------------------------------
@router.get("/api/story-series")
async def list_series(
    language: str,
    level: str,
    current_user=Depends(get_current_user),
):
    """Published series for the player's language + level, with their progress."""
    user_id = str(current_user.id)
    rows = await series_collection.find(
        {"language": language.lower(), "level": level.upper(), "status": "published"}
    ).sort("created_at", -1).to_list(length=50)

    # episode docs we'll need for scene_count + the horizontal episode preview slider
    all_ep_ids = [eid for s in rows for eid in s.get("episode_ids", [])]
    ep_docs = {e["_id"]: e for e in await worlds_collection.find(
        {"_id": {"$in": all_ep_ids}},
        {"scene_count": 1, "scenes": 1, "cover_url": 1, "episode_number": 1,
         "series_finale": 1, "episode_title_en": 1, "title_en": 1},
    ).to_list(length=300)}

    out = []
    for s in rows:
        prog = await progress_collection.find_one({"user_id": user_id, "series_id": s["_id"]})
        completed = (prog or {}).get("completed_episodes", [])
        cur = (prog or {}).get("current")
        ep_ids = s.get("episode_ids", [])
        # Recency for in-progress tiebreak — when a user has several series at
        # the same status, the most recently *played* one should surface first
        # (Continue-Watching semantics), not the most recently *created*.
        last_played = (prog or {}).get("last_played_at")

        # the episode whose scene-progress the card's segment line shows:
        # the current episode if playing, else episode 1.
        active_ep_num = (cur or {}).get("episode_number", 1)
        active_ep_id = ep_ids[active_ep_num - 1] if 0 < active_ep_num <= len(ep_ids) else (ep_ids[0] if ep_ids else None)
        ep_doc = ep_docs.get(active_ep_id, {})
        ep_scene_count = ep_doc.get("scene_count", len(ep_doc.get("scenes", [])) or 5)
        # how many scenes cleared in THAT episode
        ep_block = (prog or {}).get("episodes", {}).get(str(active_ep_num), {})
        ep_scenes_done = ep_block.get("scenes_completed", 0)

        # episode PREVIEW slider — every episode with its cover + derived lock state.
        # Players can swipe through (curiosity), locked ones show a 🔒 and can't be entered.
        ep_progress = (prog or {}).get("episodes", {})
        first_unfinished = None
        for idx, eid in enumerate(ep_ids):
            n = idx + 1
            if n not in completed and (n == 1 or (n - 1) in completed):
                first_unfinished = n
                break
        # the daily-drip unlock instant lives on the cursor of the episode it gates
        cur_unlock = (cur or {}).get("unlocked_at") if cur else None
        ep_preview = []
        for idx, eid in enumerate(ep_ids):
            ed = ep_docs.get(eid, {})
            n = idx + 1
            # unlocked_at only applies to the first-unfinished (the gated) episode
            ua = cur_unlock if n == first_unfinished else None
            state = _episode_state(n, completed, first_unfinished, ua)
            ep_preview.append({
                "world_id": eid,
                "episode_number": n,
                "title_en": ed.get("episode_title_en") or ed.get("title_en"),
                "cover_url": ed.get("cover_url"),
                "scene_count": ed.get("scene_count", len(ed.get("scenes", [])) or 5),
                "scenes_completed": ep_progress.get(str(n), {}).get("scenes_completed", 0),
                "state": state,                       # completed | current | time_locked | locked
                "unlocked_at": _parse_dt(ua).isoformat() if (state == "time_locked" and _parse_dt(ua)) else None,
                "is_finale": ed.get("series_finale", n == len(ep_ids)),
            })

        out.append({
            "id": s["_id"],
            "title": s.get("title"),
            "title_en": s.get("title_en"),
            "tagline": s.get("tagline"),
            "synopsis": s.get("synopsis"),
            "genre": s.get("genre"),
            "cover_url": s.get("cover_url"),
            "episode_count": s.get("episode_count", len(ep_ids)),
            "level": s.get("level"),
            "completed_episodes": len(completed),
            "status": (prog or {}).get("status", "not_started"),
            "current": cur,  # {episode_number, scene_index, world_id} | null
            # scene-level progress of the active episode → drives the segment line
            "active_episode_number": active_ep_num,
            "active_scene_count": ep_scene_count,
            "active_scenes_done": ep_scenes_done,
            # horizontal episode preview slider (locked ones are swipeable but not enterable)
            "episodes": ep_preview,
            # internal sort keys (stripped before returning)
            "_last_played": last_played,
            "_created": s.get("created_at"),
        })

    # Ordering, in priority tiers:
    #   1. in-progress first, then not-started, then completed
    #   2. within in-progress: most recently PLAYED first (resume the series the
    #      user actually last touched, not the newest-generated one)
    #   3. within not-started/completed: most recently CREATED first (freshest
    #      content surfaces as the next "NEW STORY")
    # datetimes can be tz-aware/naive/None across rows; normalize to a sortable
    # epoch so mixed types never raise during comparison.
    def _epoch(dt) -> float:
        if dt is None:
            return 0.0
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return 0.0

    status_order = {"in_progress": 0, "not_started": 1, "completed": 2}

    def _sort_key(x):
        status = x["status"]
        recency = _epoch(x["_last_played"]) if status == "in_progress" else _epoch(x["_created"])
        # negative recency → most-recent first within the tier
        return (status_order.get(status, 1), -recency)

    out.sort(key=_sort_key)

    # ── SINGLE ACTIVE SERIES — Netflix "one show at a time" (HIDE, don't list) ──
    # The lobby never shows a stack of stories. Two states:
    #   A) the user has a series IN PROGRESS → return ONLY that one. The rest of the
    #      catalog is hidden (not locked, not listed) so the player stays focused on
    #      the show they're watching, one episode a day.
    #   B) NO series in progress (new player, or just finished one) → return the FULL
    #      catalog so they can browse covers, filter by genre, and pick what to watch
    #      next. Their choice — we never force a category.
    # `series_lock` stays 'active' on everything returned (entry is always allowed for
    # what we send). When the active series is finished, it flips to completed and the
    # next request falls back to state B → catalog reopens. Reversible via the flag.
    if STORY_SINGLE_ACTIVE_SERIES and out:
        active = next((x for x in out if x["status"] == "in_progress"), None)
        if active:
            out = [active]                 # state A: ONLY the in-progress series
    for x in out:
        x["series_lock"] = "active"

    for x in out:
        x.pop("_last_played", None)
        x.pop("_created", None)
    return out


@router.get("/api/story-series/{series_id}")
async def series_detail(series_id: str, current_user=Depends(get_current_user)):
    """The episode PATH: each episode + its derived lock state for this user."""
    user_id = str(current_user.id)
    s = await series_collection.find_one({"_id": series_id, "status": "published"})
    if not s:
        raise HTTPException(404, "Series not found")

    prog = await progress_collection.find_one({"user_id": user_id, "series_id": series_id})
    completed = (prog or {}).get("completed_episodes", [])
    ep_progress = (prog or {}).get("episodes", {})
    cur_unlock = ((prog or {}).get("current") or {}).get("unlocked_at")

    # episodes in order
    ep_ids = s.get("episode_ids", [])
    episodes = []
    eps_docs = {e["_id"]: e for e in await worlds_collection.find(
        {"_id": {"$in": ep_ids}}
    ).to_list(length=100)}

    # first unfinished episode_number whose predecessor is done (or ep 1)
    first_unfinished = None
    for idx, eid in enumerate(ep_ids):
        n = idx + 1
        if n not in completed and (n == 1 or (n - 1) in completed):
            first_unfinished = n
            break

    for idx, eid in enumerate(ep_ids):
        ep = eps_docs.get(eid)
        if not ep:
            continue
        n = idx + 1
        ua = cur_unlock if n == first_unfinished else None
        state = _episode_state(n, completed, first_unfinished, ua)
        ep_done = ep_progress.get(str(n), {})
        # the briefing/synopsis are visible for any episode the learner can see/enter
        # (completed, current, or time_locked) — hidden only for the sequentially-locked
        # ones we don't want to spoil. time_locked still shows them: the user knows
        # what's coming tomorrow (a return hook), they just can't play it yet.
        reveal = state in ("completed", "current", "time_locked")
        episodes.append({
            "world_id": eid,
            "episode_number": n,
            "episode_title": ep.get("episode_title") or ep.get("title"),
            "episode_title_en": ep.get("episode_title_en") or ep.get("title_en"),
            "scene_count": ep.get("scene_count", len(ep.get("scenes", []))),
            "state": state,                     # completed | current | time_locked | locked
            "unlocked_at": _parse_dt(ua).isoformat() if (state == "time_locked" and _parse_dt(ua)) else None,
            "stars": ep_done.get("scenes_completed", 0) if state == "completed" else 0,
            "scenes_completed": ep_done.get("scenes_completed", 0),
            "is_finale": (n == len(ep_ids)),
            "title_teaser": ep.get("episode_title_en") or ep.get("title_en") if state == "locked" else None,
            # per-episode "what happens here" summary (target language). Hidden for
            # locked episodes so we don't spoil what's coming.
            "episode_synopsis": ep.get("episode_synopsis") if reveal else None,
            # English study-aid briefing shown in the pre-conversation modal.
            "student_briefing": ep.get("student_briefing") if reveal else None,
        })

    return {
        "id": s["_id"],
        "title": s.get("title"),
        "title_en": s.get("title_en"),
        "tagline": s.get("tagline"),
        "synopsis": s.get("synopsis"),
        "genre": s.get("genre"),
        "cover_url": s.get("cover_url"),
        "language": s.get("language"),
        "level": s.get("level"),
        "episodes": episodes,
        "current": (prog or {}).get("current"),
    }


@router.get("/api/story/continue")
async def get_continue(current_user=Depends(get_current_user)):
    """The most-recently-played in-progress series → resume card. Null if none."""
    user_id = str(current_user.id)
    prog = await progress_collection.find_one(
        {"user_id": user_id, "status": "in_progress"},
        sort=[("last_played_at", -1)],
    )
    if not prog or not prog.get("current"):
        return None
    s = await series_collection.find_one({"_id": prog["series_id"]})
    cur = prog["current"]
    ep = await worlds_collection.find_one({"_id": cur.get("world_id")})
    return {
        "series_id": prog["series_id"],
        "series_title": (s or {}).get("title"),
        "cover_url": (s or {}).get("cover_url"),
        "world_id": cur.get("world_id"),
        "episode_number": cur.get("episode_number"),
        "episode_title": (ep or {}).get("episode_title") or (ep or {}).get("title"),
        "scene_index": cur.get("scene_index", 0),
        "scene_count": (ep or {}).get("scene_count", 5),
    }


@router.get("/api/story/lobby-promo")
async def get_lobby_promo(current_user=Depends(get_current_user)):
    """The PUBLISHED Games-lobby promo cover (the 'discover Story Worlds' hero shown
    to new users). Returns {image_url} or null if the admin hasn't published one."""
    doc = await database.lobby_promos.find_one(
        {"_id": "lobby_promo", "status": "published"})
    if not doc or not doc.get("image_url"):
        return None
    return {"image_url": doc.get("image_url")}


# ---------------------------------------------------------------------------
# PUBLIC — START a series (commit to it on "Begin Episode", before any scene)
# ---------------------------------------------------------------------------
class StartSeriesRequest(BaseModel):
    series_id: str
    episode_number: int = 1
    scene_index: int = 0
    world_id: Optional[str] = None


@router.post("/api/story/progress/start")
async def start_series(body: StartSeriesRequest, current_user=Depends(get_current_user)):
    """Commit the user to a series the moment they tap 'Begin Episode' (before any
    scene is cleared). Marks it in_progress with a cursor at the entered episode/scene.
    Enforces single-active-series: you cannot start a NEW series while another is in
    progress. Idempotent — re-starting an already-active series is a no-op resume."""
    user_id = str(current_user.id)
    series = await series_collection.find_one({"_id": body.series_id})
    if not series:
        raise HTTPException(404, "Series not found")

    existing = await progress_collection.find_one({"user_id": user_id, "series_id": body.series_id})

    # single-active guard: block starting a NEW series while another is in_progress.
    if STORY_SINGLE_ACTIVE_SERIES and (existing is None or existing.get("status") == "not_started"):
        other_active = await progress_collection.find_one(
            {"user_id": user_id, "status": "in_progress", "series_id": {"$ne": body.series_id}})
        if other_active:
            raise HTTPException(409, "Finish your current story before starting a new one.")

    prog = await _get_or_create_progress(
        user_id, body.series_id, series.get("language", ""), series.get("level", ""))

    # already completed → starting again is a replay; don't flip it back to in_progress.
    if prog.get("status") == "completed":
        return {"started": True, "status": "completed"}

    # set the cursor to where they're entering (only if not already further along).
    ep_ids = series.get("episode_ids", [])
    world_id = body.world_id or (ep_ids[body.episode_number - 1] if 0 < body.episode_number <= len(ep_ids) else None)
    new_current = prog.get("current") or {
        "episode_number": body.episode_number, "scene_index": body.scene_index, "world_id": world_id}

    await progress_collection.update_one(
        {"_id": prog["_id"]},
        {"$set": {
            "status": "in_progress",
            "current": new_current,
            "last_played_at": datetime.now(timezone.utc),
        }},
    )
    return {"started": True, "status": "in_progress"}


# ---------------------------------------------------------------------------
# PUBLIC — persist a cleared scene (advances progress, server-authoritative)
# ---------------------------------------------------------------------------
class SceneCompleteRequest(BaseModel):
    series_id: str
    world_id: str
    episode_number: int
    scene_index: int
    star: str = "gold"        # gold (no hints) | silver (hinted)
    xp: int = 0
    hints_used: int = 0


@router.post("/api/story/progress/scene-complete")
async def scene_complete(body: SceneCompleteRequest, current_user=Depends(get_current_user)):
    """
    Persist one cleared scene. Idempotent (dotted-path upsert keyed by scene_index).
    Advances the cursor; marks episode complete when all scenes cleared; unlocks next.
    Returns whether the episode/series just completed (drives the celebration tier).
    """
    user_id = str(current_user.id)
    series = await series_collection.find_one({"_id": body.series_id})
    if not series:
        raise HTTPException(404, "Series not found")
    ep = await worlds_collection.find_one({"_id": body.world_id})
    if not ep:
        raise HTTPException(404, "Episode not found")
    total_scenes = ep.get("scene_count", len(ep.get("scenes", [])))

    # ── SERVER-SIDE GUARDS (defence in depth) ───────────────────────────────
    # The single-active-series and daily-drip rules are shaped read-side (the lobby
    # hides other series / locked episodes), but the write path must ALSO enforce
    # them so a direct API call can't start a 2nd series or play a locked episode.
    existing = await progress_collection.find_one({"user_id": user_id, "series_id": body.series_id})

    # GUARD 1 — single active series: while another series is in_progress, you cannot
    # start a NEW one. (Continuing the already-active series is fine; a series the
    # user has previously touched, completed, or this very series are all allowed.)
    if STORY_SINGLE_ACTIVE_SERIES and existing is None:
        other_active = await progress_collection.find_one(
            {"user_id": user_id, "status": "in_progress", "series_id": {"$ne": body.series_id}})
        if other_active:
            raise HTTPException(409, "Finish your current story before starting a new one.")

    # GUARD 2 — daily drip + sequential unlock: you may only post scenes for the
    # episode that is currently CURRENT (i.e. unlocked). Re-recording a scene already
    # cleared is idempotent and always allowed (no double credit downstream anyway).
    if existing is not None:
        completed_eps = existing.get("completed_episodes", []) or []
        already_cleared = body.scene_index in (
            (existing.get("episodes", {}).get(str(body.episode_number), {}).get("scenes", {})) or {}
        )
        if not already_cleared and body.episode_number not in completed_eps:
            cur = existing.get("current") or {}
            cur_ep = cur.get("episode_number")
            # A brand-new (never-started) doc has current=None → starting at episode 1
            # is always allowed; otherwise the posted episode must match the cursor.
            if cur_ep is None:
                if body.episode_number != 1:
                    raise HTTPException(423, "This episode is locked.")
            elif cur_ep != body.episode_number:
                # trying to play an episode that isn't the current cursor (sequential lock)
                raise HTTPException(423, "This episode is locked.")
            else:
                # on the current episode → it may be daily-drip locked until tomorrow.
                ua = _parse_dt(cur.get("unlocked_at"))
                if STORY_DAILY_DRIP and ua and datetime.now(timezone.utc) < ua:
                    raise HTTPException(423, "This episode unlocks tomorrow.")

    prog = await _get_or_create_progress(user_id, body.series_id, series.get("language", ""), series.get("level", ""))

    en = str(body.episode_number)
    si = str(body.scene_index)
    ep_block = prog.get("episodes", {}).get(en, {"world_id": body.world_id, "status": "in_progress", "scenes": {}})
    already = si in ep_block.get("scenes", {})

    # record the scene (idempotent)
    ep_block.setdefault("scenes", {})[si] = {
        "star": body.star, "xp": body.xp, "hints_used": body.hints_used,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    scenes_done = len(ep_block["scenes"])
    ep_block["scenes_completed"] = scenes_done
    ep_block["world_id"] = body.world_id

    episode_just_completed = False
    if scenes_done >= total_scenes and ep_block.get("status") != "completed":
        ep_block["status"] = "completed"
        episode_just_completed = True

    # next cursor
    next_scene = body.scene_index + 1
    if next_scene < total_scenes:
        new_current = {"episode_number": body.episode_number, "scene_index": next_scene, "world_id": body.world_id}
    else:
        # episode done → point cursor at next episode scene 0 (if any)
        ep_ids = series.get("episode_ids", [])
        if body.episode_number < len(ep_ids):
            nxt_id = ep_ids[body.episode_number]  # 0-based → next episode
            new_current = {"episode_number": body.episode_number + 1, "scene_index": 0, "world_id": nxt_id}
            # DAILY DRIP: lock the next episode until the user's next local midnight.
            if STORY_DAILY_DRIP:
                tz = getattr(current_user, "timezone", None) or "UTC"
                new_current["unlocked_at"] = _next_day_unlock(tz)
        else:
            new_current = None  # series finished

    completed_eps = set(prog.get("completed_episodes", []))
    if episode_just_completed:
        completed_eps.add(body.episode_number)
    series_just_completed = len(completed_eps) >= len(series.get("episode_ids", []))

    # ── Server-authoritative XP (anti-farm + anti-cheat) ────────────────────
    # XP is computed on the SERVER from flat constants (client body.xp is ignored).
    # CRITICAL anti-farm rule: a scene/bonus is credited to the games economy at
    # most ONCE PER LIFETIME of this (user, series), tracked in the PERSISTENT sets
    # `xp_credited_scenes` / `xp_credited_bonuses`. These sets are NEVER cleared —
    # NOT by reset-episode, NOT by replay — so replaying a finished episode awards
    # ZERO games XP (replay is for re-experiencing the story, not farming levels).
    # (The old per-scene `episodes.{en}.scenes.{si}.credited` flag lived inside the
    # episode block, which reset-episode deletes → that re-opened the farm window
    # and inflated levels. Moving it to a top-level set fixes that.)
    scene_token = f"{en}:{si}"
    credited_scenes = set(prog.get("xp_credited_scenes", []) or [])
    credited_bonuses = set(prog.get("xp_credited_bonuses", []) or [])

    scene_xp = STORY_XP_PER_SCENE if scene_token not in credited_scenes else 0

    bonus_xp = 0
    bonus_token = None
    if episode_just_completed:
        bonus_token = f"finale:{en}" if series_just_completed else f"ep:{en}"
        if bonus_token not in credited_bonuses:
            bonus_xp = STORY_XP_FINALE_BONUS if series_just_completed else STORY_XP_EPISODE_BONUS

    games_xp_delta = scene_xp + bonus_xp
    # star credited once per scene-lifetime too (same persistent gate as XP)
    star_delta = 1 if (scene_xp > 0 and body.star in ("gold", "silver")) else 0

    # Atomic credit gate: only credit when THIS request is the one that adds the
    # token to the persistent set (addToSet + modified_count == 1) — race-safe
    # against double-taps. Build the $addToSet for whatever is newly credited.
    add_to_set: Dict[str, Any] = {}
    if scene_xp > 0:
        add_to_set["xp_credited_scenes"] = scene_token
    if bonus_xp > 0 and bonus_token:
        add_to_set["xp_credited_bonuses"] = bonus_token

    credit_now = False
    if games_xp_delta > 0 and add_to_set:
        # Condition on at least one token being genuinely new so a retry can't
        # double-credit. We re-check membership server-side via the filter.
        gate_filter: Dict[str, Any] = {"_id": prog["_id"]}
        if "xp_credited_scenes" in add_to_set:
            gate_filter["xp_credited_scenes"] = {"$ne": scene_token}
        # (bonus fires on the episode-complete request, which is also the scene's
        #  first clear, so gating on the scene token is sufficient and atomic.)
        flag_res = await progress_collection.update_one(
            gate_filter, {"$addToSet": {k: v for k, v in add_to_set.items()}}
        )
        credit_now = flag_res.modified_count == 1

    await progress_collection.update_one(
        {"_id": prog["_id"]},
        {"$set": {
            f"episodes.{en}": ep_block,
            "current": new_current,
            "completed_episodes": sorted(completed_eps),
            "status": "completed" if series_just_completed else "in_progress",
            "last_played_at": datetime.now(timezone.utc),
        }, "$inc": {"total_xp": games_xp_delta if credit_now else 0,
                    "total_stars": star_delta if credit_now else 0}},
    )

    # Feed the SAME buckets the Games-tab level reads (xp_by_source.challenges +
    # daily challenge_xp). Gated on the atomic lifetime-credit flag so it fires once.
    if credit_now and games_xp_delta > 0:
        tz = getattr(current_user, "timezone", None) or "UTC"
        await credit_games_xp(
            user_id,
            series.get("language", ""),
            games_xp_delta,
            user_timezone=tz,
            source_type="story_worlds",
        )

    # next episode's daily-drip unlock instant (ISO) so the client can show
    # "come back tomorrow" immediately on episode completion, before any refetch.
    locked_until = None
    if isinstance(new_current, dict) and new_current.get("unlocked_at"):
        ua = _parse_dt(new_current["unlocked_at"])
        locked_until = ua.isoformat() if ua else None

    return {
        "saved": True,
        "episode_completed": episode_just_completed,
        "series_completed": series_just_completed,
        "xp_awarded": games_xp_delta if credit_now else 0,  # server-authoritative
        "next": new_current,           # where to go next (episode/scene) | null
        "next_episode_locked_until": locked_until,  # ISO | null (daily-drip gate)
        "next_hook": ep.get("next_hook") if episode_just_completed and not series_just_completed else None,
    }


# ---------------------------------------------------------------------------
# PUBLIC — reset one episode's progress (and everything after it)
# ---------------------------------------------------------------------------
class ResetEpisodeRequest(BaseModel):
    series_id: str
    episode_number: int


@router.post("/api/story/progress/reset-episode")
async def reset_episode(body: ResetEpisodeRequest, current_user=Depends(get_current_user)):
    """
    Reset progress for an episode. Because unlock is sequential, resetting episode N
    also re-locks every episode AFTER it (you can't have N+1 done but N not).
    Idempotent. Returns the new cursor so the app can refresh.
    """
    user_id = str(current_user.id)
    series = await series_collection.find_one({"_id": body.series_id})
    if not series:
        raise HTTPException(404, "Series not found")
    prog = await progress_collection.find_one({"user_id": user_id, "series_id": body.series_id})
    if not prog:
        return {"reset": True, "current": None}  # nothing to reset

    n = body.episode_number
    ep_ids = series.get("episode_ids", [])

    # drop episode N and all after it from the per-episode blocks + completed list
    episodes = {k: v for k, v in (prog.get("episodes", {}) or {}).items() if int(k) < n}
    completed = sorted(e for e in prog.get("completed_episodes", []) if e < n)

    # new cursor → start of episode N (it's now the first unfinished one)
    world_id = ep_ids[n - 1] if 0 < n <= len(ep_ids) else None
    new_current = {"episode_number": n, "scene_index": 0, "world_id": world_id} if world_id else None
    status = "in_progress" if completed else ("not_started" if n == 1 else "in_progress")

    await progress_collection.update_one(
        {"_id": prog["_id"]},
        {"$set": {
            "episodes": episodes,
            "completed_episodes": completed,
            "current": new_current,
            "status": status,
            "last_played_at": datetime.now(timezone.utc),
        }},
    )
    logger.info("[STORY-PROGRESS] user %s reset series %s from episode %d", user_id, body.series_id, n)
    return {"reset": True, "current": new_current, "relocked_from": n}
