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
from typing import Optional

from openai_client import get_async_openai
from database import database

logger = logging.getLogger(__name__)

IMAGE_MODEL = "gpt-image-1"  # dall-e-3 is retired from the OpenAI API
SIZE = "1024x1024"
QUALITY = "medium"  # low | medium | high — medium balances cost/quality

# Brand palette woven into the prompt so covers feel native to the app.
STYLE = (
    "Cinematic storybook cover illustration, warm dramatic lighting, rich saturated "
    "colours, painterly digital art, sense of adventure and mystery, no text, no words, "
    "no letters, no UI. Mood evokes a language-learning adventure game."
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
