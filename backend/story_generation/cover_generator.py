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
