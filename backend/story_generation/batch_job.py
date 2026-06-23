"""
Story Worlds — background batch generation with progress tracking.

Big runs (all languages × levels × genres = hundreds of 5-episode stories) must
not block the admin panel. The admin POSTs a job spec; it runs in a background
task; the admin polls a progress endpoint. State lives in MongoDB so it survives
across requests (and the admin can refresh/close the page).

One in-memory asyncio lock guards against two concurrent jobs (a single backend
process). Progress is persisted to `story_gen_jobs`.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from database import database

logger = logging.getLogger(__name__)

jobs_collection = database.story_gen_jobs
_running_lock = asyncio.Lock()

EPISODES = 5  # episodes per story (mirror of admin_story_routes.EPISODES_PER_SERIES)

# How many WHOLE STORIES generate concurrently. Each story is internally SEQUENTIAL
# (episode N needs episode N-1's style_bible + continuity), so parallelism is across
# stories only. Kept modest for Railway's single process + OpenAI rate limits.
# Override with env STORY_GEN_CONCURRENCY. With 1 story to build, this is effectively 1.
try:
    STORY_CONCURRENCY = max(1, int(os.getenv("STORY_GEN_CONCURRENCY", "4")))
except ValueError:
    STORY_CONCURRENCY = 4


async def create_job(language_list: List[str], level_list: List[str], genre_list: List[str], admin_email: str) -> dict:
    """Create a job doc (queued). Returns it."""
    combos = [(lang, lvl, g) for lang in language_list for lvl in level_list for g in genre_list]
    job_id = str(uuid.uuid4())
    doc = {
        "_id": job_id,
        "status": "queued",                 # queued | running | done | failed | cancelled
        "languages": language_list,
        "levels": level_list,
        "genres": genre_list,
        "total": len(combos),               # stories to create
        "completed": 0,
        "failed": 0,
        "current": None,                    # "dutch · A1 · mystery"
        # fine-grained live stage for the SSE progress UI:
        "stage": None,                      # "episode" | "cover" | "story" | None
        "stage_detail": None,               # "Episode 3/5" | "Cover 3/5" | ...
        "stage_episode": 0,                 # 0..5 within current story
        "stage_total_episodes": 5,
        "log": [],                          # recent human-readable lines (tail)
        "errors": [],
        "created_by": admin_email,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await jobs_collection.insert_one(doc)
    return doc


async def run_job(job_id: str, admin_email: str):
    """Background worker: generate one full 5-episode series per (lang, level, genre)."""
    # Import here to avoid a circular import (admin_story_routes imports this module indirectly).
    from admin_story_routes import _generate_full_series

    job = await jobs_collection.find_one({"_id": job_id})
    if not job:
        return

    # Single-flight: if another job holds the lock, mark this one and bail.
    if _running_lock.locked():
        await jobs_collection.update_one({"_id": job_id}, {"$set": {
            "status": "failed", "errors": ["Another generation job is already running."],
            "updated_at": datetime.now(timezone.utc)}})
        return

    async with _running_lock:
        await jobs_collection.update_one({"_id": job_id}, {"$set": {"status": "running", "updated_at": datetime.now(timezone.utc)}})
        combos = [(lang, lvl, g) for lang in job["languages"] for lvl in job["levels"] for g in job["genres"]]

        # Shared counters guarded by a lock (workers run concurrently).
        state = {"completed": 0, "failed": 0, "errors": [], "cancelled": False}
        counter_lock = asyncio.Lock()
        # Across-stories parallelism only; never exceed the number of stories.
        concurrency = min(STORY_CONCURRENCY, len(combos))
        sem = asyncio.Semaphore(concurrency)
        # record concurrency so the UI knows whether per-episode detail is meaningful
        await jobs_collection.update_one({"_id": job_id}, {"$set": {"concurrency": concurrency}})

        async def progress(stage: str, detail: str, ep: int, ep_total: int, line: str):
            """Persist fine-grained stage for the SSE progress UI (called per episode/cover)."""
            await jobs_collection.update_one({"_id": job_id}, {
                "$set": {
                    "stage": stage, "stage_detail": detail,
                    "stage_episode": ep, "stage_total_episodes": ep_total,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$push": {"log": {"$each": [line], "$slice": -30}},  # keep last 30 lines
            })

        async def build_one(lang: str, lvl: str, genre: str):
            """Build one whole story (internally sequential). Honors cancellation."""
            label = f"{lang} · {lvl} · {genre}"
            async with sem:
                # SAFE STOP: skip stories not yet started once cancelled. In-flight
                # stories finish naturally (so no half-built series is left behind).
                if state["cancelled"]:
                    return
                fresh = await jobs_collection.find_one({"_id": job_id}, {"status": 1})
                if fresh and fresh.get("status") == "cancelled":
                    state["cancelled"] = True
                    return

                await jobs_collection.update_one({"_id": job_id}, {"$set": {
                    "current": label, "stage": "story", "stage_detail": "Starting…",
                    "stage_episode": 0, "updated_at": datetime.now(timezone.utc)}})
                try:
                    await _generate_full_series(lang, lvl, genre, "", admin_email, on_progress=progress)
                    async with counter_lock:
                        state["completed"] += 1
                    await progress("story", "Done", EPISODES, EPISODES, f"✓ {label} — story complete")
                except Exception as e:  # noqa: BLE001
                    async with counter_lock:
                        state["failed"] += 1
                        state["errors"].append({"combo": label, "error": str(e)[:200]})
                    logger.warning("[STORY-JOB] %s failed: %s", label, e)
                    await progress("story", "Failed", 0, EPISODES, f"✗ {label} — {str(e)[:80]}")
                # flush counters to the job doc (SSE picks this up)
                async with counter_lock:
                    snapshot = (state["completed"], state["failed"], list(state["errors"][-20:]))
                await jobs_collection.update_one({"_id": job_id}, {"$set": {
                    "completed": snapshot[0], "failed": snapshot[1], "errors": snapshot[2],
                    "updated_at": datetime.now(timezone.utc)}})

        logger.info("[STORY-JOB] %s running %d stories, concurrency=%d", job_id, len(combos), concurrency)
        # gather all stories; the semaphore bounds how many run at once
        await asyncio.gather(*(build_one(l, lv, g) for (l, lv, g) in combos))

        final_status = "cancelled" if state["cancelled"] else "done"
        await jobs_collection.update_one({"_id": job_id}, {"$set": {
            "status": final_status, "current": None, "stage": None, "stage_detail": None,
            "updated_at": datetime.now(timezone.utc)}})
        logger.info("[STORY-JOB] %s %s: %d created, %d failed",
                    job_id, final_status, state["completed"], state["failed"])


async def get_active_job() -> Optional[dict]:
    """The most recent running/queued job (for the admin progress bar)."""
    return await jobs_collection.find_one(
        {"status": {"$in": ["queued", "running"]}},
        sort=[("created_at", -1)],
    )


async def get_job(job_id: str) -> Optional[dict]:
    return await jobs_collection.find_one({"_id": job_id})


async def cancel_job(job_id: str) -> bool:
    res = await jobs_collection.update_one(
        {"_id": job_id, "status": {"$in": ["queued", "running"]}},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}},
    )
    return res.modified_count > 0


# ---------------------------------------------------------------------------
# SSE — live progress stream (Server-Sent Events)
# ---------------------------------------------------------------------------
import json


def _job_payload(job: dict) -> dict:
    """The compact progress snapshot the admin UI renders."""
    return {
        "id": job["_id"],
        "status": job.get("status"),
        "total": job.get("total", 0),
        "completed": job.get("completed", 0),
        "failed": job.get("failed", 0),
        "current": job.get("current"),
        "stage": job.get("stage"),
        "stage_detail": job.get("stage_detail"),
        "stage_episode": job.get("stage_episode", 0),
        "stage_total_episodes": job.get("stage_total_episodes", EPISODES),
        "concurrency": job.get("concurrency", 1),
        "log": job.get("log", [])[-30:],
        "errors": job.get("errors", [])[-10:],
    }


async def stream_job(job_id: str):
    """
    Async generator yielding SSE frames as the job advances. Emits a frame whenever
    the job document's `updated_at` changes (poll-on-server, push-to-client — the
    client holds one long-lived EventSource, no client polling). Ends on terminal status.
    """
    last_sig = None
    terminal = {"done", "failed", "cancelled"}
    # ~30 min safety cap so a wedged job can't hold the connection forever
    for _ in range(30 * 60):
        job = await jobs_collection.find_one({"_id": job_id})
        if not job:
            yield f"event: error\ndata: {json.dumps({'error': 'job not found'})}\n\n"
            return
        sig = job.get("updated_at")
        if sig != last_sig:
            last_sig = sig
            yield f"data: {json.dumps(_job_payload(job))}\n\n"
        if job.get("status") in terminal:
            yield f"event: end\ndata: {json.dumps(_job_payload(job))}\n\n"
            return
        await asyncio.sleep(1)  # server-side poll cadence; client just receives pushes
    # safety timeout — close the stream, client will reconnect if still needed
    yield "event: end\ndata: {}\n\n"
