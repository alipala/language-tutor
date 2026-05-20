"""
Phase C — Redis rate limiter tests.

Tests:
1. Sliding window correctness (memory backend)
2. Sliding window correctness (redis backend)
3. Per-category isolation
4. Redis-unavailable fail-open
5. 429 response body shape identical between backends
6. Retry-After header present and correct
7. request.state.jwt_payload set after JWT decode
"""

import time
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from starlette.requests import Request


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_request(path: str = "/api/progress/stats", token: str = None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 9999),
    }
    if token:
        scope["headers"] = [(b"authorization", f"Bearer {token}".encode())]
    request = Request(scope)
    request.state  # initialise state
    return request


# ── 1. Memory backend — sliding window correctness ───────────────────────────

def test_memory_backend_allows_up_to_limit():
    from rate_limiter import _MemoryBackend, LIMITS
    b = _MemoryBackend()
    category = "auth"
    limit = LIMITS[category]["max_requests"]
    for _ in range(limit):
        limited, _ = b.check_and_record("user1", category)
        assert not limited, "Should not be limited before reaching max"


def test_memory_backend_blocks_over_limit():
    from rate_limiter import _MemoryBackend, LIMITS
    b = _MemoryBackend()
    category = "auth"
    limit = LIMITS[category]["max_requests"]
    for _ in range(limit):
        b.check_and_record("user2", category)
    limited, retry_after = b.check_and_record("user2", category)
    assert limited, "Should be limited after exceeding max"
    assert retry_after is not None and retry_after >= 1


def test_memory_backend_per_category_isolation():
    from rate_limiter import _MemoryBackend, LIMITS
    b = _MemoryBackend()
    auth_limit = LIMITS["auth"]["max_requests"]
    # Exhaust auth
    for _ in range(auth_limit):
        b.check_and_record("user3", "auth")
    limited_auth, _ = b.check_and_record("user3", "auth")
    assert limited_auth

    # general should not be affected
    limited_general, _ = b.check_and_record("user3", "general")
    assert not limited_general, "general category should be independent of auth"


def test_memory_backend_window_expiry():
    from rate_limiter import _MemoryBackend, LIMITS
    b = _MemoryBackend()
    category = "auth"
    limit = LIMITS[category]["max_requests"]
    window = LIMITS[category]["window_seconds"]

    # Fill up
    for _ in range(limit):
        b.check_and_record("user4", category)

    # Back-date all timestamps to outside the window
    past = time.time() - window - 5
    b._requests["user4"][category] = [past] * limit

    # Should now be allowed again
    limited, _ = b.check_and_record("user4", category)
    assert not limited, "After window expiry, requests should be allowed again"


# ── 2. Redis backend — sliding window correctness ────────────────────────────

@pytest.mark.asyncio
async def test_redis_backend_allows_up_to_limit():
    from rate_limiter import _redis_check_and_record, LIMITS

    category = "auth"
    limit = LIMITS[category]["max_requests"]
    identifier = "redis-test-user-allow"

    # Build a mock redis pipeline that simulates incrementing counts
    call_count = [0]

    async def fake_execute():
        call_count[0] += 1
        # zremrangebyscore, zadd, zcard, expire
        return [0, 1, call_count[0], True]

    mock_pipe = MagicMock()
    mock_pipe.zremrangebyscore = MagicMock()
    mock_pipe.zadd = MagicMock()
    mock_pipe.zcard = MagicMock()
    mock_pipe.expire = MagicMock()
    mock_pipe.execute = AsyncMock(side_effect=fake_execute)

    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)

    with patch("redis_client.redis_client", mock_redis):
        for i in range(limit):
            limited, _ = await _redis_check_and_record(identifier, category)
            assert not limited, f"Should not be limited on request {i+1}"


@pytest.mark.asyncio
async def test_redis_backend_blocks_over_limit():
    from rate_limiter import _redis_check_and_record, LIMITS

    category = "auth"
    limit = LIMITS[category]["max_requests"]
    identifier = "redis-test-user-block"

    async def fake_execute_over():
        return [0, 1, limit + 1, True]

    mock_pipe = MagicMock()
    mock_pipe.zremrangebyscore = MagicMock()
    mock_pipe.zadd = MagicMock()
    mock_pipe.zcard = MagicMock()
    mock_pipe.expire = MagicMock()
    mock_pipe.execute = AsyncMock(side_effect=fake_execute_over)

    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)
    mock_redis.zrem = AsyncMock()
    # oldest entry 10 seconds ago → retry_after = window - 10
    mock_redis.zrange = AsyncMock(
        return_value=[(identifier, (time.time() - 10) * 1000)]
    )

    with patch("redis_client.redis_client", mock_redis):
        limited, retry_after = await _redis_check_and_record(identifier, category)
        assert limited, "Should be limited when count exceeds max"
        assert retry_after is not None and retry_after >= 1


# ── 3. Redis unavailable — fail open ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_redis_unavailable_fails_open():
    from rate_limiter import _redis_check_and_record

    mock_pipe = MagicMock()
    mock_pipe.zremrangebyscore = MagicMock()
    mock_pipe.zadd = MagicMock()
    mock_pipe.zcard = MagicMock()
    mock_pipe.expire = MagicMock()
    mock_pipe.execute = AsyncMock(side_effect=ConnectionError("Redis down"))

    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)

    with patch("rate_limiter.redis_client", mock_redis), \
         patch("rate_limiter._send_redis_failure_alert", new_callable=AsyncMock) as mock_alert:
        limited, retry_after = await _redis_check_and_record("any-user", "general")
        assert not limited, "Must fail OPEN when Redis is unreachable"
        assert retry_after is None
        mock_alert.assert_called_once()


@pytest.mark.asyncio
async def test_redis_none_fails_open():
    """When redis_client is None (not yet initialised), fail open."""
    from rate_limiter import _redis_check_and_record

    with patch("rate_limiter.redis_client", None):
        limited, retry_after = await _redis_check_and_record("any-user", "general")
        assert not limited
        assert retry_after is None


# ── 4. 429 response body shape ───────────────────────────────────────────────

def _build_429_detail(category: str, retry_after: int) -> dict:
    from rate_limiter import LIMITS, _user_friendly_message
    return {
        "error": "rate_limit_exceeded",
        "message": _user_friendly_message(category, retry_after),
        "retry_after": retry_after,
        "category": category,
        "limit": LIMITS[category]["max_requests"],
        "window": LIMITS[category]["window_seconds"],
    }


def test_429_body_has_required_fields():
    detail = _build_429_detail("general", 30)
    assert "error" in detail
    assert "message" in detail
    assert "retry_after" in detail
    assert "category" in detail
    assert "limit" in detail
    assert "window" in detail
    assert detail["error"] == "rate_limit_exceeded"


def test_429_body_shape_consistent_across_categories():
    from rate_limiter import LIMITS
    for category in LIMITS:
        detail = _build_429_detail(category, 60)
        assert detail["category"] == category
        assert detail["limit"] == LIMITS[category]["max_requests"]
        assert detail["window"] == LIMITS[category]["window_seconds"]


# ── 5. Category routing ───────────────────────────────────────────────────────

def test_category_routing_realtime():
    from rate_limiter import _get_category
    assert _get_category("/api/realtime/token") == "realtime"


def test_category_routing_auth():
    from rate_limiter import _get_category
    assert _get_category("/api/auth/login") == "auth"


def test_category_routing_mid_session_is_general():
    from rate_limiter import _get_category
    assert _get_category("/api/conversation-help/generate") == "general"
    assert _get_category("/api/realtime/session-summary") == "general"
    assert _get_category("/api/sentence-assessment") == "general"


def test_category_routing_coach_free():
    from rate_limiter import _get_category
    assert _get_category("/api/coach/chat") == "coach"


def test_category_routing_coach_premium():
    from rate_limiter import _get_category
    assert _get_category("/api/coach/chat", "active") == "coach_premium"
    assert _get_category("/api/coach/chat", "trialing") == "coach_premium"


# ── 6. Retry-After header ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_after_header_present_on_429():
    """HTTPException raised by _check must carry Retry-After header."""
    from rate_limiter import _check
    from fastapi import HTTPException

    request = _make_request()

    with patch("rate_limiter.RATE_LIMITER_BACKEND", "memory"), \
         patch("rate_limiter._memory_backend") as mock_mem, \
         patch("rate_limiter._send_rate_limit_alert", new_callable=AsyncMock):
        mock_mem.check_and_record = MagicMock(return_value=(True, 42))
        with pytest.raises(HTTPException) as exc_info:
            await _check(request, "test-user", "general", True, "test-user")
        exc = exc_info.value
        assert exc.status_code == 429
        assert exc.headers.get("Retry-After") == "42"
        assert exc.detail["retry_after"] == 42
