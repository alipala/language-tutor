"""
Story Worlds — admin generation/management routes + the public read endpoints
the mobile app consumes, plus the cover-image serving endpoint.

Collections:
  story_worlds   — one doc per generated world (single-player, no multiplayer)
  image_cache    — cover bytes (base64), served by GET /api/img/{id}

Admin endpoints are protected with the existing get_current_admin dependency.
Generation uses gpt-4o-mini (story) + gpt-image-1 (cover).
"""

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from database import database
from admin_routes import get_current_admin, AdminUser
from story_generation.story_generator import generate_world, GENRES, SCENES_BY_LEVEL
from story_generation.cover_generator import generate_cover

logger = logging.getLogger(__name__)

router = APIRouter(tags=["story-worlds"])

worlds_collection = database.story_worlds
series_collection = database.story_series


EPISODES_PER_SERIES = 5  # a "story" = a 5-episode season; episode 5 is the finale
# (legacy single-episode wrapper _create_series_for_world removed —
#  every story is now a full 5-episode series via _generate_full_series)


def _continuity_from(world: dict) -> str:
    """Build a short continuity hint from a generated episode for the next one."""
    ch = world.get("character", {})
    hook = world.get("next_hook") or (world.get("scenes", [{}])[-1].get("narr") if world.get("scenes") else "")
    return f"Character {ch.get('name','the lead')} ({ch.get('role','')}) in {world.get('setting','the setting')}. Cliffhanger: {hook}"


async def _persist_episode(world: dict, series_id: str, admin_email: str) -> str:
    """Insert one generated episode (world) doc linked to a series. Returns world_id."""
    world_id = str(uuid.uuid4())
    doc = {
        "_id": world_id,
        **world,
        "series_id": series_id,
        "status": "draft",
        "cover_url": None,
        "created_by": admin_email,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await worlds_collection.insert_one(doc)
    return world_id


async def _cover_for_episode(world_id: str, world: dict, style_bible: str) -> None:
    """
    Generate + persist this episode's cover, sharing the series style_bible so all
    5 covers show the same character/look. Best-effort: a cover failure must NOT
    abort story generation (the episode is still playable without art).
    """
    try:
        url = await generate_cover(
            world_id,
            cover_prompt=world.get("cover_prompt", "") or world.get("setting", ""),
            genre=world.get("genre", ""),
            setting=world.get("setting", ""),
            style_bible=style_bible,
        )
        await worlds_collection.update_one({"_id": world_id}, {"$set": {"cover_url": url}})
    except Exception as e:  # noqa: BLE001
        logger.warning("[STORY] cover failed for episode %s: %s", world_id, e)


async def _generate_full_series(
    language: str, level: str, genre: str, theme: str, admin_email: str,
    on_progress=None,
) -> dict:
    """
    Generate a whole 5-episode story (series) WITH a cover per episode. Episodes are
    generated sequentially so each continues the previous; episode 5 is the finale.
    The series style_bible (set on ep 1) is reused by every episode so the 5 covers
    are visually consistent. Returns the series doc.

    `on_progress(stage, detail, ep, ep_total, line)` (async) — optional callback fired
    at each episode/cover step so a batch job can stream fine-grained progress.
    """
    async def _emit(stage, detail, ep, line):
        if on_progress:
            try:
                await on_progress(stage, detail, ep, EPISODES_PER_SERIES, line)
            except Exception:  # noqa: BLE001 — progress must never break generation
                pass

    label = f"{language} · {level} · {genre}"
    series_id = str(uuid.uuid4())
    episode_ids = []
    first_world = None
    continuity = ""
    style_bible = ""  # locked from episode 1, reused by 2..N

    for ep_num in range(1, EPISODES_PER_SERIES + 1):
        await _emit("episode", f"Episode {ep_num}/{EPISODES_PER_SERIES}", ep_num,
                    f"{label} — writing episode {ep_num}/{EPISODES_PER_SERIES}")
        world = await generate_world(
            language, level, genre, theme,
            episode_number=ep_num, total_episodes=EPISODES_PER_SERIES,
            continuity_hint=continuity, style_bible=style_bible,
        )
        if ep_num == 1:
            first_world = world
            style_bible = world.get("style_bible", "") or ""  # lock the series look
        wid = await _persist_episode(world, series_id, admin_email)
        episode_ids.append(wid)
        # cover per episode, consistent via the shared style_bible
        await _emit("cover", f"Cover {ep_num}/{EPISODES_PER_SERIES}", ep_num,
                    f"{label} — painting cover {ep_num}/{EPISODES_PER_SERIES}")
        await _cover_for_episode(wid, world, style_bible)
        continuity = _continuity_from(world)

    # series cover = episode 1's cover (already generated)
    ep1_doc = await worlds_collection.find_one({"_id": episode_ids[0]}, {"cover_url": 1})
    series_cover = (ep1_doc or {}).get("cover_url")

    series_doc = {
        "_id": series_id,
        "title": first_world.get("title"),
        "title_en": first_world.get("title_en"),
        "tagline": first_world.get("description"),
        "language": language.lower(),
        "level": level.upper(),
        "genre": genre,
        "cover_url": series_cover,
        "style_bible": style_bible,
        "episode_ids": episode_ids,
        "episode_count": len(episode_ids),
        "status": "draft",
        "created_by": admin_email,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await series_collection.insert_one(series_doc)
    logger.info("[STORY] full series %s: %d episodes + covers (%s/%s/%s)", series_id, len(episode_ids), language, level, genre)
    return series_doc


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class GenerateWorldRequest(BaseModel):
    language: str          # english | spanish | french | german | dutch | portuguese | italian
    level: str             # A1..C2
    genre: str = "daily_life"
    theme: str = ""        # optional creative hint


from bson import ObjectId
from datetime import datetime as _dt


def _clean(v):
    """Recursively make a value JSON-serializable (ObjectId/datetime → str)."""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, _dt):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_clean(x) for x in v]
    return v


def _serialize(doc: dict) -> dict:
    out = {k: _clean(x) for k, x in dict(doc).items()}
    out["id"] = str(out.pop("_id", ""))
    return out


# ---------------------------------------------------------------------------
# ADMIN — generate / manage
# ---------------------------------------------------------------------------
@router.post("/api/admin/story-worlds/generate")
async def admin_generate_world(
    body: GenerateWorldRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Generate a full STORY = a 5-episode series (episode 5 is the finale)."""
    if body.level.upper() not in SCENES_BY_LEVEL:
        raise HTTPException(400, f"Invalid level. Use one of {list(SCENES_BY_LEVEL)}")
    if body.genre not in GENRES:
        raise HTTPException(400, f"Invalid genre. Use one of {GENRES}")
    try:
        series = await _generate_full_series(
            body.language, body.level, body.genre, body.theme, current_admin.email,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("[STORY] generation failed")
        raise HTTPException(502, f"Story generation failed: {e}")
    return _serialize(series)


class GenerateBatchRequest(BaseModel):
    language: str   # one language for the test batch
    level: str      # one level
    # generates one world for EACH genre (7 worlds)


@router.post("/api/admin/story-worlds/generate-batch")
async def admin_generate_batch(
    body: GenerateBatchRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    One-click batch: generate one full 5-episode STORY for EVERY genre at the
    given language + level (= 7 stories × 5 episodes). Covers added separately.
    """
    if body.level.upper() not in SCENES_BY_LEVEL:
        raise HTTPException(400, f"Invalid level. Use one of {list(SCENES_BY_LEVEL)}")

    created = []
    errors = []
    for genre in GENRES:
        try:
            series = await _generate_full_series(body.language, body.level, genre, "", current_admin.email)
            created.append(_serialize(series))
        except Exception as e:  # noqa: BLE001
            logger.warning("[STORY] batch genre %s failed: %s", genre, e)
            errors.append({"genre": genre, "error": str(e)})

    logger.info("[STORY] batch: %d stories created, %d failed (by %s)", len(created), len(errors), current_admin.email)
    return {"created": created, "created_count": len(created), "errors": errors}


# ---------------------------------------------------------------------------
# FLEXIBLE BACKGROUND GENERATION (single / batch / everything) + progress
# ---------------------------------------------------------------------------
ALL_LANGUAGES = ["english", "spanish", "french", "german", "dutch", "portuguese"]
ALL_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


@router.get("/api/admin/story-worlds/options")
async def admin_generation_options(current_admin: AdminUser = Depends(get_current_admin)):
    """Catalog the admin UI needs: languages, levels, genres."""
    return {"languages": ALL_LANGUAGES, "levels": ALL_LEVELS, "genres": GENRES}


class GenerateJobRequest(BaseModel):
    languages: list[str]   # one or many
    levels: list[str]      # one or many
    genres: list[str]      # one or many


@router.post("/api/admin/story-worlds/generate-job")
async def admin_start_generation_job(
    body: GenerateJobRequest,
    background: BackgroundTasks,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Start a BACKGROUND generation job for the chosen languages × levels × genres.
    Each combo → one full 5-episode story. Returns the job id; poll for progress.
    Handles all three admin modes: single (1×1×1), batch (subset), everything (all).
    """
    from story_generation.batch_job import create_job, run_job, get_active_job

    langs = [l.lower() for l in body.languages if l.lower() in ALL_LANGUAGES]
    levels = [l.upper() for l in body.levels if l.upper() in ALL_LEVELS]
    genres = [g for g in body.genres if g in GENRES]
    if not langs or not levels or not genres:
        raise HTTPException(400, "Pick at least one language, level, and genre")

    active = await get_active_job()
    if active:
        raise HTTPException(409, "A generation job is already running. Wait for it to finish or cancel it.")

    job = await create_job(langs, levels, genres, current_admin.email)
    background.add_task(run_job, job["_id"], current_admin.email)
    logger.info("[STORY] job %s started: %d stories (by %s)", job["_id"], job["total"], current_admin.email)
    return {"job_id": job["_id"], "total": job["total"]}


@router.get("/api/admin/story-worlds/generate-job/active")
async def admin_active_job(current_admin: AdminUser = Depends(get_current_admin)):
    """The currently-running/queued job (for the progress bar). Null if none."""
    from story_generation.batch_job import get_active_job
    job = await get_active_job()
    return _serialize(job) if job else None


@router.get("/api/admin/story-worlds/generate-job/{job_id}")
async def admin_job_status(job_id: str, current_admin: AdminUser = Depends(get_current_admin)):
    from story_generation.batch_job import get_job
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _serialize(job)


@router.post("/api/admin/story-worlds/generate-job/{job_id}/cancel")
async def admin_cancel_job(job_id: str, current_admin: AdminUser = Depends(get_current_admin)):
    from story_generation.batch_job import cancel_job
    ok = await cancel_job(job_id)
    return {"cancelled": ok}


def _verify_admin_token(token: str) -> bool:
    """Validate an admin JWT passed as a query param (EventSource can't send headers)."""
    from jose import jwt
    from admin_routes import SECRET_KEY, ALGORITHM, ADMIN_USERS
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "admin":
            return False
        admin_id = payload.get("sub")
        return any(u["id"] == admin_id for u in ADMIN_USERS.values())
    except Exception:  # noqa: BLE001
        return False


@router.get("/api/admin/story-worlds/generate-job/{job_id}/stream")
async def admin_job_stream(job_id: str, token: str = Query("")):
    """
    Server-Sent Events stream of live job progress. The admin opens one long-lived
    EventSource; the server pushes a frame on every job update (episode/cover/story).
    Auth is via ?token= because the EventSource API cannot set Authorization headers.
    """
    if not _verify_admin_token(token):
        raise HTTPException(401, "Invalid admin token")
    from story_generation.batch_job import stream_job
    return StreamingResponse(
        stream_job(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/railway)
        },
    )


@router.post("/api/admin/story-worlds/{world_id}/generate-cover")
async def admin_generate_cover(
    world_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Generate (or regenerate) the cover image for a world via gpt-image-1."""
    doc = await worlds_collection.find_one({"_id": world_id})
    if not doc:
        raise HTTPException(404, "World not found")
    try:
        url = await generate_cover(
            world_id,
            cover_prompt=doc.get("cover_prompt", doc.get("description", "")),
            genre=doc.get("genre", ""),
            setting=doc.get("setting", ""),
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("[STORY] cover failed")
        raise HTTPException(502, f"Cover generation failed: {e}")

    await worlds_collection.update_one(
        {"_id": world_id},
        {"$set": {"cover_url": url, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"cover_url": url}


@router.get("/api/admin/story-worlds")
async def admin_list_worlds(
    current_admin: AdminUser = Depends(get_current_admin),
    language: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
):
    """List all worlds for the admin grid (newest first)."""
    # Only OUR single-player worlds (have a `scenes` array). The same collection
    # also holds old collaborative-branch seed docs (different schema) — exclude them.
    q: dict = {"scenes": {"$exists": True}}
    if language:
        q["language"] = language.lower()
    if level:
        q["level"] = level.upper()
    if status:
        q["status"] = status
    rows = await worlds_collection.find(q).sort("created_at", -1).to_list(length=500)
    return [_serialize(r) for r in rows]


@router.get("/api/admin/story-worlds/{world_id}")
async def admin_get_world(
    world_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
):
    doc = await worlds_collection.find_one({"_id": world_id})
    if not doc:
        raise HTTPException(404, "World not found")
    return _serialize(doc)


class EditWorldRequest(BaseModel):
    title: Optional[str] = None
    title_en: Optional[str] = None
    description: Optional[str] = None
    cover_prompt: Optional[str] = None
    scenes: Optional[list] = None   # admin can hand-edit scene text


@router.put("/api/admin/story-worlds/{world_id}")
async def admin_edit_world(
    world_id: str,
    body: EditWorldRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Edit world metadata / scenes (admin curation)."""
    doc = await worlds_collection.find_one({"_id": world_id})
    if not doc:
        raise HTTPException(404, "World not found")
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if not updates:
        return _serialize(doc)
    if "scenes" in updates:
        updates["scene_count"] = len(updates["scenes"])
    updates["updated_at"] = datetime.now(timezone.utc)
    await worlds_collection.update_one({"_id": world_id}, {"$set": updates})
    doc = await worlds_collection.find_one({"_id": world_id})
    return _serialize(doc)


class StatusRequest(BaseModel):
    status: str  # draft | published


@router.post("/api/admin/story-worlds/{world_id}/status")
async def admin_set_status(
    world_id: str,
    body: StatusRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Publish / unpublish a world. Published worlds appear in the mobile app."""
    status = body.status
    if status not in ("draft", "published"):
        raise HTTPException(400, "status must be 'draft' or 'published'")
    doc = await worlds_collection.find_one({"_id": world_id})
    if not doc:
        raise HTTPException(404, "World not found")
    if status == "published" and not doc.get("cover_url"):
        raise HTTPException(400, "Generate a cover before publishing")
    await worlds_collection.update_one(
        {"_id": world_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
    )
    # Keep the parent series in sync: publishing an episode publishes its series,
    # and copies the episode cover up to the series poster if it has none.
    sid = doc.get("series_id")
    if sid:
        sset = {"status": status, "updated_at": datetime.now(timezone.utc)}
        s = await series_collection.find_one({"_id": sid})
        if status == "published" and s and not s.get("cover_url") and doc.get("cover_url"):
            sset["cover_url"] = doc["cover_url"]
        await series_collection.update_one({"_id": sid}, {"$set": sset})
    return {"status": status}


@router.delete("/api/admin/story-worlds/{world_id}")
async def admin_delete_world(
    world_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
):
    await worlds_collection.delete_one({"_id": world_id})
    await database.image_cache.delete_one({"_id": f"story_cover_{world_id}"})
    return {"deleted": True}


# ---------------------------------------------------------------------------
# ADMIN — SERIES-GROUPED view (each story = one series + its 5 episodes)
# ---------------------------------------------------------------------------
@router.get("/api/admin/story-series")
async def admin_list_series(
    current_admin: AdminUser = Depends(get_current_admin),
    language: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    List STORIES (series) with their episodes nested — the grouped admin view.
    Each row is one story; episodes are ordered EP1..EP5 (finale last).
    """
    q: dict = {}
    if language:
        q["language"] = language.lower()
    if level:
        q["level"] = level.upper()
    if status:
        q["status"] = status
    series_rows = await series_collection.find(q).sort("created_at", -1).to_list(length=500)

    # fetch all episodes for these series in one query
    all_ep_ids = [eid for s in series_rows for eid in s.get("episode_ids", [])]
    ep_docs = {}
    if all_ep_ids:
        ep_docs = {e["_id"]: e for e in await worlds_collection.find(
            {"_id": {"$in": all_ep_ids}}
        ).to_list(length=3000)}

    out = []
    for s in series_rows:
        eps = []
        total_scenes = 0
        covers_done = 0
        for idx, eid in enumerate(s.get("episode_ids", [])):
            e = ep_docs.get(eid)
            if not e:
                continue
            sc = e.get("scene_count", len(e.get("scenes", [])))
            total_scenes += sc
            if e.get("cover_url"):
                covers_done += 1
            eps.append({
                "id": eid,
                "episode_number": e.get("episode_number", idx + 1),
                "title": e.get("episode_title") or e.get("title"),
                "title_en": e.get("episode_title_en") or e.get("title_en"),
                "scene_count": sc,
                "cover_url": e.get("cover_url"),
                "status": e.get("status", "draft"),
                "is_finale": e.get("series_finale", idx == len(s.get("episode_ids", [])) - 1),
            })
        eps.sort(key=lambda x: x["episode_number"])
        out.append({
            "id": s["_id"],
            "title": s.get("title"),
            "title_en": s.get("title_en"),
            "tagline": s.get("tagline"),
            "genre": s.get("genre"),
            "language": s.get("language"),
            "level": s.get("level"),
            "cover_url": s.get("cover_url"),
            "status": s.get("status", "draft"),
            "episode_count": len(eps),
            "total_scenes": total_scenes,
            "covers_done": covers_done,
            "created_at": s.get("created_at"),
            "episodes": eps,
        })
    return [_clean(o) for o in out]


@router.post("/api/admin/story-series/{series_id}/status")
async def admin_series_status(
    series_id: str,
    body: StatusRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Publish / unpublish a WHOLE story in one click — the series and ALL its episodes
    flip together. Publishing requires every episode to have a cover.
    """
    status = body.status
    if status not in ("draft", "published"):
        raise HTTPException(400, "status must be 'draft' or 'published'")
    s = await series_collection.find_one({"_id": series_id})
    if not s:
        raise HTTPException(404, "Series not found")
    ep_ids = s.get("episode_ids", [])

    if status == "published":
        eps = await worlds_collection.find({"_id": {"$in": ep_ids}}, {"cover_url": 1}).to_list(length=100)
        missing = [e["_id"] for e in eps if not e.get("cover_url")]
        if missing or len(eps) < len(ep_ids):
            raise HTTPException(400, f"All {len(ep_ids)} episodes need a cover before publishing ({len(missing)} missing)")

    now = datetime.now(timezone.utc)
    await worlds_collection.update_many({"_id": {"$in": ep_ids}}, {"$set": {"status": status, "updated_at": now}})
    sset = {"status": status, "updated_at": now}
    if status == "published" and not s.get("cover_url"):
        ep1 = await worlds_collection.find_one({"_id": ep_ids[0]}, {"cover_url": 1}) if ep_ids else None
        if ep1 and ep1.get("cover_url"):
            sset["cover_url"] = ep1["cover_url"]
    await series_collection.update_one({"_id": series_id}, {"$set": sset})
    logger.info("[STORY] series %s → %s (%d episodes) by %s", series_id, status, len(ep_ids), current_admin.email)
    return {"status": status, "episodes": len(ep_ids)}


@router.delete("/api/admin/story-series/{series_id}")
async def admin_delete_series(
    series_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Delete a whole story: the series, all its episodes, and their covers."""
    s = await series_collection.find_one({"_id": series_id})
    if not s:
        raise HTTPException(404, "Series not found")
    ep_ids = s.get("episode_ids", [])
    await worlds_collection.delete_many({"_id": {"$in": ep_ids}})
    for eid in ep_ids:
        await database.image_cache.delete_one({"_id": f"story_cover_{eid}"})
    await series_collection.delete_one({"_id": series_id})
    logger.info("[STORY] series %s deleted (%d episodes) by %s", series_id, len(ep_ids), current_admin.email)
    return {"deleted": True, "episodes": len(ep_ids)}


# ---------------------------------------------------------------------------
# PUBLIC — mobile app reads published worlds by language + level
# ---------------------------------------------------------------------------
@router.get("/api/story-worlds")
async def public_list_worlds(
    language: str = Query(...),
    level: str = Query(...),
):
    """Published worlds for the player's selected language + level (from the Hub)."""
    rows = await worlds_collection.find(
        {"language": language.lower(), "level": level.upper(), "status": "published", "scenes": {"$exists": True}}
    ).sort("created_at", -1).to_list(length=50)
    # Trim to what the lobby card needs; full scenes come from the detail endpoint.
    out = []
    for r in rows:
        out.append({
            "id": str(r["_id"]),
            "title": r.get("title"),
            "description": r.get("description"),
            "genre": r.get("genre"),
            "cover_url": r.get("cover_url"),
            "scene_count": r.get("scene_count"),
            "level": r.get("level"),
        })
    return out


@router.get("/api/story-worlds/{world_id}")
async def public_get_world(world_id: str):
    """Full world (scenes, character) for an in-game session."""
    doc = await worlds_collection.find_one({"_id": world_id, "status": "published"})
    if not doc:
        raise HTTPException(404, "World not found")
    return _serialize(doc)


class TurnRequest(BaseModel):
    world_id: str
    scene_index: int
    text: str                       # the player's TYPED reply
    support_lang: str = "english"   # for translating the character's reply


@router.post("/api/story-worlds/turn")
async def play_turn(body: TurnRequest):
    """
    Score one TYPED turn: gpt-4o-mini judges whether the text meets the scene
    goal (is it an acceptable answer?), writes the character's reply, translates
    it, and gives a gentle spelling note. Text-based v1 — no STT/TTS.
    """
    doc = await worlds_collection.find_one({"_id": body.world_id, "status": "published"})
    if not doc:
        raise HTTPException(404, "World not found")
    scenes = doc.get("scenes", [])
    if body.scene_index < 0 or body.scene_index >= len(scenes):
        raise HTTPException(400, "Invalid scene index")
    scene = scenes[body.scene_index]

    from story_generation.turn_service import score_turn_text

    try:
        result = await score_turn_text(
            text=body.text,
            scene=scene,
            language=doc.get("language", "english"),
            level=doc.get("level", "A1"),
            support_lang=body.support_lang,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("[STORY] turn scoring failed")
        raise HTTPException(502, f"Turn scoring failed: {e}")
    return result


# ---------------------------------------------------------------------------
# Image serving — covers are stored as base64 in image_cache
# ---------------------------------------------------------------------------
@router.get("/api/img/{image_id}")
async def serve_image(image_id: str, request: Request):
    """
    Serve a cached image (story cover) by id. Covers are immutable, so we attach a
    strong ETag and honour If-None-Match: when the client already has the image, we
    return an empty 304 instead of re-sending ~1.3 MB. Combined with the client-side
    disk cache (expo-image), the bytes are fetched at most once per device.
    """
    # The id already uniquely identifies the immutable bytes → it IS the ETag.
    etag = f'"{image_id}"'
    if request.headers.get("if-none-match") == etag:
        # client already has it — no DB read, no body
        return Response(status_code=304, headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=31536000, immutable",
        })

    doc = await database.image_cache.find_one({"_id": image_id}, {"data_base64": 1, "content_type": 1})
    if not doc or not doc.get("data_base64"):
        raise HTTPException(404, "Image not found")
    img_bytes = base64.b64decode(doc["data_base64"])
    return Response(
        content=img_bytes,
        media_type=doc.get("content_type", "image/png"),
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": etag,
        },
    )
