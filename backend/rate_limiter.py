"""
Rate Limiting Middleware for FastAPI
Prevents abuse, protects budget, and improves stability.

Backend is controlled by RATE_LIMITER_BACKEND env var:
  "memory" (default) — in-process dict, resets on restart, NOT shared across workers
  "redis"            — Redis sorted-set sliding window, shared across all workers

Switch to "redis" before enabling multiple uvicorn workers (Phase F).
Rollback: set RATE_LIMITER_BACKEND=memory in Railway — no code deploy needed.
"""

import os
import time
import logging
from typing import Dict, Optional
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from monitoring.slack_notifier import slack_notifier, AlertContext, AlertSeverity, Alert

logger = logging.getLogger(__name__)

# ── Feature flag ──────────────────────────────────────────────────────────────

RATE_LIMITER_BACKEND = os.getenv("RATE_LIMITER_BACKEND", "memory").lower()

# ── Shared configuration ──────────────────────────────────────────────────────

LIMITS: Dict[str, Dict] = {
    "general":       {"max_requests": 100, "window_seconds": 60},    # 100/min
    "realtime":      {"max_requests": 10,  "window_seconds": 3600},  # 10/hour
    "auth":          {"max_requests": 10,  "window_seconds": 300},   # 10/5min
    "coach":         {"max_requests": 10,  "window_seconds": 3600},  # 10/hour (free)
    "coach_premium": {"max_requests": 20,  "window_seconds": 3600},  # 20/hour (paid)
}

# ── Category routing (unchanged from original) ────────────────────────────────

_MID_SESSION_PATTERNS = [
    "/conversation-help",
    "/realtime/usage-log",
    "/realtime/semantic-feedback",
    "/realtime/session-summary",
    "/sentence-assessment",
    "/chat",
    "/contextual-chat",
]


def _get_category(path: str, subscription_status: Optional[str] = None) -> str:
    # Coach checked first — /api/coach/chat contains "/chat" which is a mid-session
    # pattern, so coach must win before the mid-session loop runs.
    if "/coach/chat" in path:
        return "coach_premium" if subscription_status in ("active", "trialing") else "coach"
    for pattern in _MID_SESSION_PATTERNS:
        if pattern in path:
            return "general"
    if "/realtime/token" in path:
        return "realtime"
    if "/auth/" in path or "/login" in path or "/register" in path:
        return "auth"
    return "general"


def _user_friendly_message(category: str, retry_after: int) -> str:
    minutes = max(1, int(retry_after / 60))
    messages = {
        "realtime":      f"You've practiced a lot! Take a {minutes}-minute break to let your learning sink in. 🧘",
        "auth":          f"For your account security, please wait {minutes} minute(s) before trying again. 🔒",
        "coach":         f"You've chatted a lot with your coach! ☕ Take a {minutes}-minute break to reflect on the advice.",
        "coach_premium": f"Even premium users need reflection time! 🧘 Please wait {minutes} minute(s) and come back refreshed.",
        "general":       f"Please wait {retry_after if retry_after < 60 else f'{minutes} minute(s)'} and try again.",
    }
    return messages.get(category, messages["general"])


# ── In-memory backend ─────────────────────────────────────────────────────────

from collections import defaultdict


class _MemoryBackend:
    """Original sliding-window in-memory implementation. Not shared across workers."""

    def __init__(self):
        self._requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    def check_and_record(self, identifier: str, category: str) -> tuple[bool, Optional[int]]:
        now = time.time()
        config = LIMITS[category]
        window = config["window_seconds"]
        max_req = config["max_requests"]

        timestamps = self._requests[identifier][category]
        cutoff = now - window
        valid = [ts for ts in timestamps if ts > cutoff]
        self._requests[identifier][category] = valid

        if len(valid) >= max_req:
            oldest = min(valid)
            retry_after = max(1, int(oldest + window - now))
            return True, retry_after

        valid.append(now)
        return False, None

    def request_count(self, identifier: str, category: str) -> int:
        return len(self._requests[identifier][category])

    def cleanup(self):
        cutoff = time.time() - 3600
        for uid in list(self._requests.keys()):
            for cat in list(self._requests[uid].keys()):
                self._requests[uid][cat] = [ts for ts in self._requests[uid][cat] if ts > cutoff]
                if not self._requests[uid][cat]:
                    del self._requests[uid][cat]
            if not self._requests[uid]:
                del self._requests[uid]


_memory_backend = _MemoryBackend()


# ── Redis backend ─────────────────────────────────────────────────────────────

async def _redis_check_and_record(identifier: str, category: str) -> tuple[bool, Optional[int]]:
    """
    Sorted-set sliding window via a single pipeline.
    Key format: ratelimit:{category}:{identifier}
    Fails OPEN (returns False) if Redis is unreachable.
    """
    from redis_client import redis_client

    if redis_client is None:
        # Redis not initialised yet — fail open, log warning
        logger.warning("[RATE_LIMITER] Redis client not ready, failing open for %s/%s", category, identifier)
        return False, None

    config = LIMITS[category]
    window = config["window_seconds"]
    max_req = config["max_requests"]
    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - (window * 1000)
    key = f"ratelimit:{category}:{identifier}"

    try:
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff_ms)        # drop expired entries
        pipe.zadd(key, {str(now_ms): now_ms})           # record this request
        pipe.zcard(key)                                 # count in window
        pipe.expire(key, window + 10)                   # auto-expire key
        results = await pipe.execute()

        count = results[2]  # zcard result

        if count > max_req:
            # Over limit — remove the entry we just added, then find retry-after
            await redis_client.zrem(key, str(now_ms))
            oldest = await redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = max(1, int((oldest[0][1] / 1000) + window - time.time()))
            else:
                retry_after = window
            return True, retry_after

        return False, None

    except Exception as exc:
        # Redis unreachable — fail open, alert Slack
        logger.error("[RATE_LIMITER] Redis error, failing open: %s", exc)
        await _send_redis_failure_alert(str(exc))
        return False, None


async def _send_redis_failure_alert(error: str):
    try:
        context = AlertContext(
            endpoint="rate_limiter",
            method="INTERNAL",
            environment="production" if slack_notifier.is_production else "development",
        )
        await slack_notifier.send_alert(
            Alert(
                title="Rate Limiter: Redis unreachable — failing open",
                message=(
                    f"⚠️ Redis rate limiter could not reach Redis.\n"
                    f"Failing open (requests allowed). Fix Redis ASAP.\n\n"
                    f"**Error:** `{error}`"
                ),
                severity=AlertSeverity.HIGH,
                error_type="RateLimiter_Redis_Failure",
                timestamp=datetime.now(),
                context=context,
            )
        )
    except Exception:
        pass  # Never let alert failure break request handling


# ── Slack alert on rate-limit hit ─────────────────────────────────────────────

async def _send_rate_limit_alert(
    identifier: str,
    user_id: Optional[str],
    category: str,
    request: Request,
    retry_after: int,
    is_authenticated: bool,
):
    try:
        severity = AlertSeverity.HIGH if category in ("realtime", "gpt4o") else AlertSeverity.MEDIUM
        context = AlertContext(
            user_id=user_id if is_authenticated else None,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            environment="production" if slack_notifier.is_production else "development",
        )
        if is_authenticated:
            title = f"Rate Limit Exceeded: User {user_id[:8]}..."
            message = (
                f"🚫 **Authenticated user** exceeded rate limits.\n\n"
                f"**Category:** `{category.upper()}`\n"
                f"**Endpoint:** `{request.method} {request.url.path}`\n"
                f"**Limit:** {LIMITS[category]['max_requests']} req/{LIMITS[category]['window_seconds']}s\n"
                f"⏱️ Must wait **{retry_after}s**."
            )
        else:
            title = f"Rate Limit Exceeded: IP {request.client.host}"
            message = (
                f"🚫 **Anonymous user** (IP) exceeded rate limits.\n\n"
                f"**Category:** `{category.upper()}`\n"
                f"**IP:** `{request.client.host}`\n"
                f"**Endpoint:** `{request.method} {request.url.path}`\n"
                f"**Limit:** {LIMITS[category]['max_requests']} req/{LIMITS[category]['window_seconds']}s\n"
                f"⏱️ Must wait **{retry_after}s**.\n⚠️ Possible abuse."
            )
        await slack_notifier.send_alert(
            Alert(
                title=title, message=message, severity=severity,
                error_type="Rate_Limit_Exceeded", timestamp=datetime.now(),
                context=context,
            )
        )
    except Exception as e:
        logger.warning("[RATE_LIMITER] Failed to send Slack alert: %s", e)


# ── Core check function ───────────────────────────────────────────────────────

async def _check(request: Request, identifier: str, category: str, is_authenticated: bool, user_id: Optional[str]):
    """Run the appropriate backend check and raise 429 if limited."""
    if RATE_LIMITER_BACKEND == "redis":
        is_limited, retry_after = await _redis_check_and_record(identifier, category)
    else:
        is_limited, retry_after = _memory_backend.check_and_record(identifier, category)

    if is_limited:
        await _send_rate_limit_alert(identifier, user_id, category, request, retry_after, is_authenticated)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": _user_friendly_message(category, retry_after),
                "retry_after": retry_after,
                "category": category,
                "limit": LIMITS[category]["max_requests"],
                "window": LIMITS[category]["window_seconds"],
            },
            headers={"Retry-After": str(retry_after)},
        )


# ── Public API (identical to original) ───────────────────────────────────────

async def check_rate_limit(
    request: Request,
    user_id: Optional[str] = None,
    subscription_status: Optional[str] = None,
):
    """FastAPI dependency — same signature as before, no route changes needed."""
    identifier = user_id or request.client.host
    category = _get_category(request.url.path, subscription_status)
    await _check(request, identifier, category, bool(user_id), user_id)


# ── Middleware ────────────────────────────────────────────────────────────────

async def _rate_limit_middleware(request: Request, call_next):
    user_id: Optional[str] = None
    subscription_status: Optional[str] = None

    # Single JWT decode per request — result stored on request.state
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from jose import jwt, JWTError
            secret = os.getenv("JWT_SECRET_KEY", "fallback_key")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get("sub")
            subscription_status = payload.get("subscription_status")
            # Cache on request.state so downstream handlers can reuse without re-decoding
            request.state.jwt_payload = payload
            request.state.user_id = user_id
        except Exception:
            pass

    try:
        identifier = user_id or request.client.host
        category = _get_category(request.url.path, subscription_status)
        await _check(request, identifier, category, bool(user_id), user_id)
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers or {},
        )

    return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Drop-in replacement — same class name, same registration in main.py."""

    async def dispatch(self, request: Request, call_next):
        return await _rate_limit_middleware(request, call_next)


# ── Backwards-compat shim: RateLimiter class ─────────────────────────────────
# Some tests patch `rate_limiter.rate_limiter` directly. Keep a thin shim so
# those imports don't break.

class _RateLimiterShim:
    """Thin shim preserving the old module-level `rate_limiter` name."""
    limits = LIMITS

    async def check_rate_limit(self, request, user_id=None, subscription_status=None):
        await check_rate_limit(request, user_id, subscription_status)


rate_limiter = _RateLimiterShim()
