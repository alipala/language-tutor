"""
App Version Check Routes
========================

Returns whether the client app is up to date, behind, or critically outdated.
Used by the mobile app to show a smart update modal.

Config via Railway env vars (no redeploy needed, just change variables):
  IOS_LATEST_VERSION     e.g. "1.1.41"
  IOS_MIN_VERSION        e.g. "1.1.30"   (below this = force update)
  ANDROID_LATEST_VERSION e.g. "1.1.41"
  ANDROID_MIN_VERSION    e.g. "1.1.30"

If vars are unset the endpoint returns no_update so the modal never appears.
"""

import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class VersionCheckResponse(BaseModel):
    status: str                      # "no_update" | "soft_update" | "force_update"
    latest_version: Optional[str]    # current latest, e.g. "1.1.42"
    min_version: Optional[str]       # minimum supported, e.g. "1.1.30"
    store_url: Optional[str]         # deep link to the correct store listing


# Store URLs — HTTPS universal links work in every region without country prefix
_IOS_STORE_URL = "https://apps.apple.com/app/id6744053599"
_ANDROID_STORE_URL = "https://play.google.com/store/apps/details?id=com.bigdavinci.MyTacoAI"


def _parse_version(v: str) -> tuple[int, ...]:
    """'1.1.41' → (1, 1, 41).  Returns (0,) on any parse error."""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except Exception:
        return (0,)


@router.get("/api/version/check", response_model=VersionCheckResponse)
async def check_version(platform: str = "ios", current: str = "0.0.0"):
    """
    Check whether the given app version needs an update.

    Query params:
      platform  — "ios" or "android"
      current   — semver string of the installed app, e.g. "1.1.41"

    Safe-by-default: any configuration error returns no_update so the
    modal is never shown incorrectly.
    """
    platform = platform.lower().strip()

    # ── Load config from env ───────────────────────────────────────────────
    if platform == "android":
        latest_str = os.getenv("ANDROID_LATEST_VERSION", "").strip()
        min_str    = os.getenv("ANDROID_MIN_VERSION", "").strip()
        store_url  = _ANDROID_STORE_URL
    else:
        latest_str = os.getenv("IOS_LATEST_VERSION", "").strip()
        min_str    = os.getenv("IOS_MIN_VERSION", "").strip()
        store_url  = _IOS_STORE_URL

    # ── Guard: if either version is unconfigured → never show modal ────────
    if not latest_str or not min_str:
        return VersionCheckResponse(
            status="no_update",
            latest_version=None,
            min_version=None,
            store_url=None,
        )

    current_v = _parse_version(current)
    latest_v  = _parse_version(latest_str)
    min_v     = _parse_version(min_str)

    # ── Guard: bad parse → never show modal ───────────────────────────────
    if current_v == (0,) or latest_v == (0,) or min_v == (0,):
        return VersionCheckResponse(
            status="no_update",
            latest_version=None,
            min_version=None,
            store_url=None,
        )

    # ── Guard: sanity — min must not exceed latest ─────────────────────────
    if min_v > latest_v:
        return VersionCheckResponse(
            status="no_update",
            latest_version=None,
            min_version=None,
            store_url=None,
        )

    # ── Decision ───────────────────────────────────────────────────────────
    if current_v >= latest_v:
        # Already on latest (or somehow ahead — e.g. internal beta)
        return VersionCheckResponse(
            status="no_update",
            latest_version=latest_str,
            min_version=min_str,
            store_url=None,
        )

    if current_v < min_v:
        # Below minimum — force update, user cannot skip
        return VersionCheckResponse(
            status="force_update",
            latest_version=latest_str,
            min_version=min_str,
            store_url=store_url,
        )

    # Between min and latest — soft update, user can dismiss
    return VersionCheckResponse(
        status="soft_update",
        latest_version=latest_str,
        min_version=min_str,
        store_url=store_url,
    )
