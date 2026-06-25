"""
Story Worlds cover-art generator — gpt-image-1 (the current OpenAI image model;
dall-e-3 was removed from the API). Generates a professional, on-brand cover for
a world and stores it so the URL never expires.

gpt-image-1 returns base64 directly (b64_json), so unlike dall-e-3 there's no
short-lived URL to race — we persist the bytes immediately.

Quality is `medium` by design (founder decision: good-looking, low cost ~$0.04/img).
"""

import base64
import logging
import os
from typing import Optional

from openai_client import get_async_openai
from database import database

logger = logging.getLogger(__name__)

# Image model. gpt-image-1-mini is OpenAI's cost-efficient image model (recommended
# for high-volume work since Mar 2026) and ~60% cheaper than gpt-image-1 at medium
# quality (~$0.015-0.02 vs ~$0.04 / 1024² image). Our covers are stylised storybook
# illustrations, not photoreal, so mini's quality is a good fit. Also note gpt-image-1
# is being deprecated (Oct 2026), so mini is the forward path. Override via env for an
# instant rollback to the old model/quality if a generation looks worse.
IMAGE_MODEL = os.getenv("STORY_IMAGE_MODEL", "gpt-image-1-mini")
SIZE = "1024x1024"
QUALITY = os.getenv("STORY_IMAGE_QUALITY", "medium")  # low | medium | high

# Brand palette woven into the prompt so covers feel native to the app.
# NOTE: the app uses a near-black dark theme, so covers must be BRIGHT and luminous
# or they vanish into the background and read as gloomy. We deliberately steer the
# model toward bright daylight + vivid colour (not "dramatic"/low-key lighting, which
# was producing dark, murky covers). This is a prompt-only change — quality/size/cost
# (medium, 1024², ~$0.04) are unchanged.
STYLE = (
    "Bright, vibrant storybook cover illustration, luminous daylight, clear airy "
    "atmosphere, vivid saturated colours, high key lighting with strong light-to-dark "
    "contrast so the subject pops, uplifting and inviting mood, painterly digital art, "
    "a sense of wonder and adventure, no text, no words, no letters, no UI. Avoid dark, "
    "murky, gloomy, or night scenes — keep it light and colourful."
)


def _build_prompt(cover_prompt: str, genre: str, setting: str, style_bible: str = "") -> str:
    """
    Compose the image prompt. `style_bible` is the SERIES-wide visual identity
    (same character look, palette, art style) shared by every episode cover so
    the 5 covers feel like one show; `cover_prompt` is this episode's moment.
    """
    parts = [STYLE]
    if style_bible:
        parts.append(f"Series visual identity (keep consistent across episodes): {style_bible}")
    parts.append(f"Genre: {genre}. Setting: {setting}.")
    parts.append(f"This episode's scene: {cover_prompt}")
    return "\n".join(parts)


async def generate_cover(
    world_id: str,
    cover_prompt: str,
    genre: str = "",
    setting: str = "",
    style_bible: str = "",
) -> str:
    """
    Generate a cover for a world, persist the bytes, and return a stable URL path
    (served by the existing /api/img/{id} cache). Raises on failure.
    Pass `style_bible` to keep all episodes of one series visually consistent.
    """
    client = get_async_openai()
    prompt = _build_prompt(cover_prompt, genre, setting, style_bible)
    logger.info("[STORY-COVER] Generating cover for world %s", world_id)

    resp = await client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=SIZE,
        quality=QUALITY,
        n=1,
    )

    b64 = resp.data[0].b64_json
    if not b64:
        raise ValueError("Image model returned no data")
    img_bytes = base64.b64decode(b64)

    # Persist into the same image-cache collection the app already serves from.
    # Stored as a base64 data the /api/img endpoint streams back. Keyed by world.
    doc_id = f"story_cover_{world_id}"
    await database.image_cache.update_one(
        {"_id": doc_id},
        {"$set": {
            "_id": doc_id,
            "content_type": "image/png",
            "data_base64": b64,
            "source": "story_worlds",
            "world_id": world_id,
            "model": IMAGE_MODEL,
            "quality": QUALITY,
        }},
        upsert=True,
    )
    url_path = f"/api/img/{doc_id}"
    logger.info("[STORY-COVER] ✓ cover stored (%d bytes) → %s", len(img_bytes), url_path)
    return url_path


# Portrait framing for the in-game character avatar — a close, face-forward bust
# so it reads clearly when cropped into a small circular avatar in the chat UI.
PORTRAIT_STYLE = (
    "Character portrait, head-and-shoulders bust, face clearly visible and centered, "
    "looking toward the viewer, bright luminous lighting, soft warm key light, painterly "
    "digital storybook art, clean light simple background, vivid colours, friendly "
    "inviting mood, no text, no words, no letters, no UI. Avoid dark or murky lighting."
)


def _build_portrait_prompt(character: dict, genre: str, setting: str, style_bible: str = "") -> str:
    """
    Compose a CHARACTER portrait prompt (distinct from the scene cover). Anchored
    on the same `style_bible` so the avatar matches the covers' lead-character look,
    plus the character's name/role/persona to capture who they are.
    """
    name = (character or {}).get("name", "")
    role = (character or {}).get("role", "")
    persona = (character or {}).get("persona", "")
    parts = [PORTRAIT_STYLE]
    if style_bible:
        parts.append(f"Lead character appearance (match exactly, same person as the covers): {style_bible}")
    who = ", ".join(p for p in [name, role] if p)
    if who:
        parts.append(f"This is {who}.")
    if persona:
        parts.append(f"Character: {persona}")
    parts.append(f"Genre: {genre}. Setting: {setting}.")
    return "\n".join(parts)


async def generate_character_portrait(
    series_id: str,
    character: dict,
    genre: str = "",
    setting: str = "",
    style_bible: str = "",
) -> str:
    """
    Generate ONE character portrait for a series (the in-game chat avatar), persist
    the bytes, and return a stable /api/img path. Series-level: the lead character is
    the same across all episodes (style_bible is series-wide), so this runs once per
    series — same ~$0.04 cost as one cover. Raises on failure.
    """
    client = get_async_openai()
    prompt = _build_portrait_prompt(character, genre, setting, style_bible)
    logger.info("[STORY-CHAR] Generating character portrait for series %s", series_id)

    resp = await client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=SIZE,
        quality=QUALITY,
        n=1,
    )

    b64 = resp.data[0].b64_json
    if not b64:
        raise ValueError("Image model returned no data")
    img_bytes = base64.b64decode(b64)

    doc_id = f"story_char_{series_id}"
    await database.image_cache.update_one(
        {"_id": doc_id},
        {"$set": {
            "_id": doc_id,
            "content_type": "image/png",
            "data_base64": b64,
            "source": "story_worlds_character",
            "series_id": series_id,
            "model": IMAGE_MODEL,
            "quality": QUALITY,
        }},
        upsert=True,
    )
    url_path = f"/api/img/{doc_id}"
    logger.info("[STORY-CHAR] ✓ portrait stored (%d bytes) → %s", len(img_bytes), url_path)
    return url_path


# ── GAMES-LOBBY PROMO COVER ─────────────────────────────────────────────────
# ONE shared "discover Story Worlds" hero image shown in the Games lobby to NEW
# users (before they've started any series), inviting them into the Story Worlds
# screen to browse and pick a story Netflix-style. It is NOT tied to a story, a
# language, or a level — it's a single global marketing cover the admin authors
# with a custom prompt. Uses the FULL gpt-image-1 at HIGH quality (not the cheaper
# mini) because this single image is the front door to the feature. One-off cost.
LOBBY_PROMO_MODEL = os.getenv("STORY_LOBBY_IMAGE_MODEL", "gpt-image-1")
LOBBY_PROMO_QUALITY = os.getenv("STORY_LOBBY_IMAGE_QUALITY", "high")
LOBBY_PROMO_ID = "lobby_promo"            # the PUBLISHED promo the lobby serves
LOBBY_PROMO_DRAFT_PREFIX = "lobby_promo_draft_"   # generated drafts await approval

LOBBY_PROMO_STYLE = (
    "Premium cinematic key-art / movie-poster style cover, Netflix-grade, dramatic "
    "yet BRIGHT and luminous (the app has a dark UI, so keep it vivid and high-key so "
    "it pops, never murky or gloomy), rich saturated colour, a clear inviting hero "
    "subject and a sense of MANY unfolding stories and adventures to choose from, "
    "painterly polished digital illustration, depth and atmosphere, no text, no words, "
    "no letters, no UI."
)


def _build_lobby_prompt(custom_prompt: str) -> str:
    """The admin's custom prompt is the creative brief; we wrap it in the premium
    key-art style so the promo stays on-brand and dark-UI-friendly."""
    parts = [LOBBY_PROMO_STYLE]
    if custom_prompt and custom_prompt.strip():
        parts.append(f"Scene / concept: {custom_prompt.strip()}")
    else:
        parts.append("Scene / concept: an inviting doorway into a world of interactive "
                     "stories — a curious traveller stepping toward a glowing horizon full "
                     "of different adventures (mystery, romance, fantasy, daily life) to choose from.")
    return "\n".join(parts)


async def generate_lobby_promo_draft(draft_id: str, custom_prompt: str = "") -> str:
    """Generate a DRAFT Games-lobby promo cover into image_cache under `draft_id`
    (NOT the published id), and return its /api/img path. Drafts await admin approval
    — publishing copies the chosen draft onto LOBBY_PROMO_ID. Raises on failure."""
    client = get_async_openai()
    prompt = _build_lobby_prompt(custom_prompt)
    logger.info("[LOBBY-PROMO] Generating a draft Games-lobby promo cover (%s)", draft_id)

    resp = await client.images.generate(
        model=LOBBY_PROMO_MODEL,
        prompt=prompt,
        size=SIZE,
        quality=LOBBY_PROMO_QUALITY,
        n=1,
    )

    b64 = resp.data[0].b64_json
    if not b64:
        raise ValueError("Image model returned no data")
    img_bytes = base64.b64decode(b64)

    await database.image_cache.update_one(
        {"_id": draft_id},
        {"$set": {
            "_id": draft_id,
            "content_type": "image/png",
            "data_base64": b64,
            "source": "lobby_promo_draft",
            "model": LOBBY_PROMO_MODEL,
            "quality": LOBBY_PROMO_QUALITY,
        }},
        upsert=True,
    )
    url_path = f"/api/img/{draft_id}"
    logger.info("[LOBBY-PROMO] ✓ draft stored (%d bytes) → %s", len(img_bytes), url_path)
    return url_path
