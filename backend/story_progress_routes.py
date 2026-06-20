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
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import database
from auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["story-progress"])

series_collection = database.story_series
worlds_collection = database.story_worlds
progress_collection = database.story_progress


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


def _episode_state(ep_number: int, completed: list, first_unfinished: Optional[int]) -> str:
    """Derive lock state: completed | current | locked."""
    if ep_number in completed:
        return "completed"
    if ep_number == first_unfinished:
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
        ep_preview = []
        for idx, eid in enumerate(ep_ids):
            ed = ep_docs.get(eid, {})
            n = idx + 1
            state = _episode_state(n, completed, first_unfinished)
            ep_preview.append({
                "world_id": eid,
                "episode_number": n,
                "title_en": ed.get("episode_title_en") or ed.get("title_en"),
                "cover_url": ed.get("cover_url"),
                "scene_count": ed.get("scene_count", len(ed.get("scenes", [])) or 5),
                "scenes_completed": ep_progress.get(str(n), {}).get("scenes_completed", 0),
                "state": state,                       # completed | current | locked
                "is_finale": ed.get("series_finale", n == len(ep_ids)),
            })

        out.append({
            "id": s["_id"],
            "title": s.get("title"),
            "title_en": s.get("title_en"),
            "tagline": s.get("tagline"),
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
        })
    # in-progress first, then not-started, then completed
    order = {"in_progress": 0, "not_started": 1, "completed": 2}
    out.sort(key=lambda x: order.get(x["status"], 1))
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
        state = _episode_state(n, completed, first_unfinished)
        ep_done = ep_progress.get(str(n), {})
        episodes.append({
            "world_id": eid,
            "episode_number": n,
            "episode_title": ep.get("episode_title") or ep.get("title"),
            "episode_title_en": ep.get("episode_title_en") or ep.get("title_en"),
            "scene_count": ep.get("scene_count", len(ep.get("scenes", []))),
            "state": state,                     # completed | current | locked
            "stars": ep_done.get("scenes_completed", 0) if state == "completed" else 0,
            "scenes_completed": ep_done.get("scenes_completed", 0),
            "is_finale": (n == len(ep_ids)),
            "title_teaser": ep.get("episode_title_en") or ep.get("title_en") if state == "locked" else None,
        })

    return {
        "id": s["_id"],
        "title": s.get("title"),
        "title_en": s.get("title_en"),
        "tagline": s.get("tagline"),
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
        else:
            new_current = None  # series finished

    completed_eps = set(prog.get("completed_episodes", []))
    if episode_just_completed:
        completed_eps.add(body.episode_number)
    series_just_completed = len(completed_eps) >= len(series.get("episode_ids", []))

    # XP/stars only count on FIRST clear of a scene (anti-farm)
    xp_delta = body.xp if not already else 0
    star_delta = 1 if (not already and body.star in ("gold", "silver")) else 0

    await progress_collection.update_one(
        {"_id": prog["_id"]},
        {"$set": {
            f"episodes.{en}": ep_block,
            "current": new_current,
            "completed_episodes": sorted(completed_eps),
            "status": "completed" if series_just_completed else "in_progress",
            "last_played_at": datetime.now(timezone.utc),
        }, "$inc": {"total_xp": xp_delta, "total_stars": star_delta}},
    )

    return {
        "saved": True,
        "episode_completed": episode_just_completed,
        "series_completed": series_just_completed,
        "next": new_current,           # where to go next (episode/scene) | null
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
