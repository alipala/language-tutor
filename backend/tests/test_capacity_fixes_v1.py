"""
CAPACITY_FIXES_V1 — tests for the three flag-gated capacity fixes.

Work Item 1: fixed-window rate limiter (RATE_LIMITER_ALGO=fixed_window, 2 ops/req)
Work Item 2: limiter path exemptions (RATE_LIMITER_EXEMPT_PATHS, exact match)
Work Item 3: notification poll cache (NOTIF_POLL_CACHE_V1, 45s TTL, 2 signatures)

Harness mirrors tests/test_rate_limiter_redis.py: unittest.mock.AsyncMock +
patch("redis_client.redis_client", ...) with recorded pipeline command sequences.
"""

import os
import re
import json
import time
import types
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.requests import Request

BACKEND_DIR = Path(__file__).resolve().parent.parent


# ── Shared fakes ──────────────────────────────────────────────────────────────

class FakePipe:
    """Records commands; applies INCR/ZADD/ZCARD/DEL semantics on a shared store."""

    def __init__(self, store, log, kv=None):
        self.store, self.log, self.cmds = store, log, []
        self.kv = {} if kv is None else kv

    def zremrangebyscore(self, key, lo, hi):
        self.cmds.append(("ZREMRANGEBYSCORE", key)); return self

    def zadd(self, key, mapping):
        self.cmds.append(("ZADD", key)); return self

    def zcard(self, key):
        self.cmds.append(("ZCARD", key)); return self

    def expire(self, key, ttl, **kw):
        self.cmds.append(("EXPIRE", key, ttl, tuple(sorted(kw.items())))); return self

    def incr(self, key):
        self.cmds.append(("INCR", key)); return self

    def delete(self, key):
        self.cmds.append(("DEL", key)); return self

    async def execute(self):
        out = []
        for c in self.cmds:
            self.log.append(c)
            out.append(self._apply(c))
        self.cmds = []
        return out

    def _apply(self, c):
        op, key = c[0], c[1]
        if op in ("ZADD", "INCR"):
            self.store[key] = self.store.get(key, 0) + 1
            return self.store[key] if op == "INCR" else 1
        if op == "ZCARD":
            return self.store.get(key, 0)
        if op == "DEL":
            counted = self.store.pop(key, None) is not None
            cached = self.kv.pop(key, None) is not None
            return 1 if (counted or cached) else 0
        return True if op == "EXPIRE" else 0


class FakeRedis:
    def __init__(self):
        self.store, self.kv, self.log = {}, {}, []

    def pipeline(self):
        return FakePipe(self.store, self.log, self.kv)

    async def zrem(self, key, member):
        self.log.append(("ZREM", key)); return 1

    async def zrange(self, key, a, b, withscores=False):
        self.log.append(("ZRANGE", key))
        return [("m", (time.time() - 10) * 1000)]

    async def get(self, key):
        self.log.append(("GET", key)); return self.kv.get(key)

    async def setex(self, key, ttl, val):
        self.log.append(("SETEX", key, ttl)); self.kv[key] = val; return True


class FakeCursor:
    def __init__(self, docs): self.docs = list(docs)
    def __aiter__(self): self._it = iter(self.docs); return self
    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration
    async def to_list(self, n): return self.docs[: (n or len(self.docs))]


def make_request(path, method="GET"):
    return Request({
        "type": "http", "method": method, "path": path, "raw_path": path.encode(),
        "query_string": b"", "headers": [], "client": ("198.51.100.1", 4321),
        "scheme": "http", "server": ("test", 80), "root_path": "",
    })


async def passthrough_call_next(request):
    from starlette.responses import PlainTextResponse
    return PlainTextResponse("ok")


# ══════════════════════════════════════════════════════════════════════════════
# WORK ITEM 1 — fixed-window algorithm
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_flag_off_issues_exact_legacy_command_sequence():
    """RATE_LIMITER_ALGO default → 4-op sliding-window zset sequence, no INCR."""
    import rate_limiter as rl
    fake = FakeRedis()
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_ALGO", "sliding_window"):
        await rl._check(make_request("/api/x"), "u1", "general", True, "u1")
    ops = [c[0] for c in fake.log]
    assert ops == ["ZREMRANGEBYSCORE", "ZADD", "ZCARD", "EXPIRE"]
    assert all(c[1] == "ratelimit:general:u1" for c in fake.log)
    # legacy EXPIRE has no NX flag
    assert fake.log[3][3] == ()


@pytest.mark.asyncio
async def test_flag_on_issues_exactly_incr_and_expire_nx():
    import rate_limiter as rl
    fake = FakeRedis()
    fixed_now = 1_750_000_000.0
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "time", types.SimpleNamespace(time=lambda: fixed_now)):
        limited, retry = await rl._redis_fixed_window_check("u1", "general")
    assert not limited and retry is None
    window = rl.LIMITS["general"]["window_seconds"]
    expected_key = f"rl_fw:general:u1:{int(fixed_now // window)}"
    assert fake.log == [
        ("INCR", expected_key),
        ("EXPIRE", expected_key, window + 1, (("nx", True),)),
    ]


@pytest.mark.asyncio
async def test_fixed_window_allows_limit_blocks_limit_plus_one():
    import rate_limiter as rl
    fake = FakeRedis()
    limit = rl.LIMITS["auth"]["max_requests"]
    with patch("redis_client.redis_client", fake):
        for i in range(limit):
            limited, _ = await rl._redis_fixed_window_check("u2", "auth")
            assert not limited, f"request {i+1} should pass"
        limited, retry_after = await rl._redis_fixed_window_check("u2", "auth")
    assert limited
    assert retry_after is not None and 1 <= retry_after <= rl.LIMITS["auth"]["window_seconds"]


@pytest.mark.asyncio
async def test_fixed_window_429_shape_middleware_path():
    """Over-limit through the middleware → same JSONResponse shape as legacy."""
    import rate_limiter as rl
    fake = FakeRedis()
    limit = rl.LIMITS["general"]["max_requests"]
    # pre-load the window counter to the limit so the next request trips it
    fixed_now = 1_750_000_000.0
    window = rl.LIMITS["general"]["window_seconds"]
    key = f"rl_fw:general:198.51.100.1:{int(fixed_now // window)}"
    fake.store = {key: limit}
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_ALGO", "fixed_window"), \
         patch.object(rl, "time", types.SimpleNamespace(time=lambda: fixed_now)), \
         patch.object(rl, "_send_rate_limit_alert", new_callable=AsyncMock) as alert:
        resp = await rl._rate_limit_middleware(make_request("/api/x"), passthrough_call_next)
    assert resp.status_code == 429
    body = json.loads(resp.body)
    assert set(body.keys()) == {"error", "message", "retry_after", "category", "limit", "window"}
    assert body["error"] == "rate_limit_exceeded"
    assert body["category"] == "general"
    assert body["limit"] == limit and body["window"] == window
    assert resp.headers["retry-after"] == str(body["retry_after"])
    alert.assert_called_once()


@pytest.mark.asyncio
async def test_fixed_window_429_shape_dependency_path():
    """Over-limit through check_rate_limit (coach route) → HTTPException detail dict."""
    from fastapi import HTTPException
    import rate_limiter as rl
    fake = FakeRedis()
    fixed_now = 1_750_000_000.0
    window = rl.LIMITS["general"]["window_seconds"]
    key = f"rl_fw:general:dep-user:{int(fixed_now // window)}"
    fake.store = {key: rl.LIMITS["general"]["max_requests"]}
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_ALGO", "fixed_window"), \
         patch.object(rl, "time", types.SimpleNamespace(time=lambda: fixed_now)), \
         patch.object(rl, "_send_rate_limit_alert", new_callable=AsyncMock):
        with pytest.raises(HTTPException) as exc_info:
            await rl.check_rate_limit(make_request("/api/x"), user_id="dep-user")
    exc = exc_info.value
    assert exc.status_code == 429
    assert set(exc.detail.keys()) == {"error", "message", "retry_after", "category", "limit", "window"}
    assert exc.headers["Retry-After"] == str(exc.detail["retry_after"])


@pytest.mark.asyncio
async def test_fixed_window_rollover_resets_counter():
    import rate_limiter as rl
    fake = FakeRedis()
    window = rl.LIMITS["auth"]["window_seconds"]
    limit = rl.LIMITS["auth"]["max_requests"]
    clock = [1_750_000_000.0]
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "time", types.SimpleNamespace(time=lambda: clock[0])):
        for _ in range(limit + 1):
            limited, _ = await rl._redis_fixed_window_check("u3", "auth")
        assert limited, "over limit in first window"
        clock[0] += window  # advance past the window boundary → new window_index
        limited, _ = await rl._redis_fixed_window_check("u3", "auth")
        assert not limited, "new window must start fresh"
    keys = {c[1] for c in fake.log if c[0] == "INCR"}
    assert len(keys) == 2, "rollover must use a different key"


@pytest.mark.asyncio
async def test_key_isolation_between_algorithms():
    """Flipping the algo mid-traffic: rl_fw: counters and ratelimit: zsets coexist."""
    import rate_limiter as rl
    fake = FakeRedis()
    req = make_request("/api/x")
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"):
        with patch.object(rl, "RATE_LIMITER_ALGO", "sliding_window"):
            await rl._check(req, "u4", "general", True, "u4")
        with patch.object(rl, "RATE_LIMITER_ALGO", "fixed_window"):
            await rl._check(req, "u4", "general", True, "u4")
    legacy_keys = {c[1] for c in fake.log if c[1].startswith("ratelimit:")}
    fw_keys = {c[1] for c in fake.log if c[1].startswith("rl_fw:")}
    assert legacy_keys and fw_keys
    assert not (legacy_keys & fw_keys)
    # both counters tracked independently in the store
    assert fake.store[next(iter(legacy_keys))] == 1
    assert fake.store[next(iter(fw_keys))] == 1


@pytest.mark.asyncio
async def test_fixed_window_concurrent_requests_exact_count():
    """50 parallel checks → no lost updates (INCR atomicity preserved by the code)."""
    import rate_limiter as rl
    fake = FakeRedis()
    with patch("redis_client.redis_client", fake):
        results = await asyncio.gather(
            *[rl._redis_fixed_window_check("u5", "auth") for _ in range(50)]
        )
    limit = rl.LIMITS["auth"]["max_requests"]
    blocked = sum(1 for limited, _ in results if limited)
    assert blocked == 50 - limit, f"exactly {50 - limit} of 50 must be blocked at limit {limit}"
    key = [k for k in fake.store if k.startswith("rl_fw:auth:u5:")][0]
    assert fake.store[key] == 50, "every request must be counted exactly once"


@pytest.mark.asyncio
async def test_fixed_window_redis_down_fails_open_like_legacy():
    import rate_limiter as rl
    broken_pipe = MagicMock()
    broken_pipe.incr = MagicMock(return_value=broken_pipe)
    broken_pipe.expire = MagicMock(return_value=broken_pipe)
    broken_pipe.execute = AsyncMock(side_effect=ConnectionError("Redis down"))
    broken = MagicMock()
    broken.pipeline = MagicMock(return_value=broken_pipe)
    with patch("redis_client.redis_client", broken), \
         patch.object(rl, "_send_redis_failure_alert", new_callable=AsyncMock) as alert:
        limited, retry = await rl._redis_fixed_window_check("u6", "general")
    assert not limited and retry is None, "must fail OPEN like legacy"
    alert.assert_called_once()


@pytest.mark.asyncio
async def test_fixed_window_redis_none_fails_open():
    import rate_limiter as rl
    with patch("redis_client.redis_client", None):
        limited, retry = await rl._redis_fixed_window_check("u7", "general")
    assert not limited and retry is None


# ══════════════════════════════════════════════════════════════════════════════
# WORK ITEM 2 — path exemptions
# ══════════════════════════════════════════════════════════════════════════════

def test_exempt_paths_parsing_robustness():
    from rate_limiter import _parse_exempt_paths
    assert _parse_exempt_paths(" /api/health , ,/healthz ") == frozenset({"/api/health", "/healthz"})
    assert _parse_exempt_paths("") == frozenset()
    assert _parse_exempt_paths("   ") == frozenset()
    assert _parse_exempt_paths(None) == frozenset()


@pytest.mark.asyncio
async def test_empty_exempt_set_limits_every_path_including_health():
    import rate_limiter as rl
    fake = FakeRedis()
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_EXEMPT_PATHS", frozenset()):
        resp = await rl._rate_limit_middleware(make_request("/api/health"), passthrough_call_next)
    assert resp.status_code == 200
    assert len(fake.log) > 0, "with no exemptions, /api/health must hit Redis"


@pytest.mark.asyncio
async def test_exempt_path_zero_redis_ops_and_normal_response():
    import rate_limiter as rl
    fake = FakeRedis()
    exempt = frozenset({"/api/health"})
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_EXEMPT_PATHS", exempt):
        resp = await rl._rate_limit_middleware(make_request("/api/health"), passthrough_call_next)
        assert resp.status_code == 200
        assert fake.log == [], "exempt path must issue ZERO Redis commands"
        # OPTIONS on the exempt path is also exempt (exact path match, any method)
        resp = await rl._rate_limit_middleware(make_request("/api/health", method="OPTIONS"), passthrough_call_next)
        assert resp.status_code == 200
        assert fake.log == []
        # sibling paths are NOT exempt — exact match only
        for sibling in ("/api/healthx", "/api/health/sub"):
            await rl._rate_limit_middleware(make_request(sibling), passthrough_call_next)
        assert len(fake.log) > 0, "sibling paths must still be limited"


# ══════════════════════════════════════════════════════════════════════════════
# WORK ITEM 3 — notification poll cache
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_DOCS = [
    {
        "_id": "un1", "user_id": "u-notif", "notification_id": "n1",
        "is_read": False, "read_at": None, "deleted_at": None,
        "created_at": "2026-06-12T09:00:00+00:00",
        "notification": {
            "_id": "n1", "title": "T1", "content": "C1",
            "notification_type": "Information", "created_by": "system",
            "created_at": "2026-06-12T08:59:00+00:00",
            "sent_at": "2026-06-12T08:59:30+00:00", "is_sent": True,
        },
    },
]


def make_notif_collection(log, docs=None):
    docs = SAMPLE_DOCS if docs is None else docs
    coll = MagicMock()

    def agg(pipeline):
        log.append("MONGO_AGGREGATE")
        if pipeline and pipeline[-1] == {"$count": "total"}:
            return FakeCursor([{"total": len(docs)}])
        return FakeCursor(docs)

    async def cnt(q):
        log.append("MONGO_COUNT")
        return len(docs)

    coll.aggregate = MagicMock(side_effect=agg)
    coll.count_documents = AsyncMock(side_effect=cnt)
    return coll


def poll_kwargs(sig=True, **overrides):
    kw = dict(skip=0, limit=20, unread_only=False, include_session_analysis=sig,
              current_user=types.SimpleNamespace(id="u-notif"))
    kw.update(overrides)
    return kw


@pytest.mark.asyncio
async def test_flag_off_zero_redis_ops_on_poll(monkeypatch):
    monkeypatch.delenv("NOTIF_POLL_CACHE_V1", raising=False)
    import notification_routes as nr
    fake = FakeRedis()
    mongo_log = []
    with patch("redis_client.redis_client", fake), \
         patch.object(nr, "user_notifications_collection", make_notif_collection(mongo_log)):
        out1 = await nr.get_user_notifications(**poll_kwargs())
        out2 = await nr.get_user_notifications(**poll_kwargs())
    assert fake.log == [], "flag OFF must not touch Redis at all — not even a GET"
    assert mongo_log.count("MONGO_AGGREGATE") == 2, "every poll hits Mongo when flag OFF"
    from fastapi.encoders import jsonable_encoder
    assert jsonable_encoder(out1) == jsonable_encoder(out2)


@pytest.mark.asyncio
@pytest.mark.parametrize("sig", [True, False])
async def test_flag_on_cold_then_warm_identical_response(monkeypatch, sig):
    monkeypatch.setenv("NOTIF_POLL_CACHE_V1", "true")
    import notification_routes as nr
    from fastapi.encoders import jsonable_encoder
    fake = FakeRedis()
    mongo_log = []
    with patch("redis_client.redis_client", fake), \
         patch.object(nr, "user_notifications_collection", make_notif_collection(mongo_log)):
        cold = await nr.get_user_notifications(**poll_kwargs(sig=sig))
        mongo_after_cold = list(mongo_log)
        warm = await nr.get_user_notifications(**poll_kwargs(sig=sig))
    assert "MONGO_AGGREGATE" in mongo_after_cold, "cold poll must query Mongo"
    assert mongo_log == mongo_after_cold, "warm poll must issue ZERO Mongo calls"
    expected_key = f"notif_poll:u-notif:{'sa1' if sig else 'sa0'}"
    assert ("SETEX", expected_key, 45) in fake.log, "cached with 45s TTL under the right key"
    assert jsonable_encoder(cold) == jsonable_encoder(warm), "warm response must equal cold field-for-field"
    assert warm.total_count == 1 and len(warm.notifications) == 1


@pytest.mark.asyncio
async def test_flag_on_non_default_params_bypass_cache(monkeypatch):
    monkeypatch.setenv("NOTIF_POLL_CACHE_V1", "true")
    import notification_routes as nr
    fake = FakeRedis()
    mongo_log = []
    with patch("redis_client.redis_client", fake), \
         patch.object(nr, "user_notifications_collection", make_notif_collection(mongo_log)):
        await nr.get_user_notifications(**poll_kwargs(skip=5))
        await nr.get_user_notifications(**poll_kwargs(limit=10))
        await nr.get_user_notifications(**poll_kwargs(unread_only=True))
    assert fake.log == [], "non-default params must bypass the cache entirely"
    assert mongo_log.count("MONGO_AGGREGATE") == 3


@pytest.mark.asyncio
async def test_invalidate_deletes_both_signature_keys(monkeypatch):
    monkeypatch.setenv("NOTIF_POLL_CACHE_V1", "true")
    from cache_helpers import invalidate_notif_poll_cache
    fake = FakeRedis()
    fake.store = {"notif_poll:u-notif:sa1": 1, "notif_poll:u-notif:sa0": 1}
    with patch("redis_client.redis_client", fake):
        await invalidate_notif_poll_cache("u-notif")
    assert ("DEL", "notif_poll:u-notif:sa1") in fake.log
    assert ("DEL", "notif_poll:u-notif:sa0") in fake.log
    assert len([c for c in fake.log if c[0] == "DEL"]) == 2


@pytest.mark.asyncio
async def test_invalidate_is_noop_when_flag_off(monkeypatch):
    monkeypatch.delenv("NOTIF_POLL_CACHE_V1", raising=False)
    from cache_helpers import invalidate_notif_poll_cache
    fake = FakeRedis()
    with patch("redis_client.redis_client", fake):
        await invalidate_notif_poll_cache("u-notif")
    assert fake.log == [], "flag OFF → invalidation must be a Redis no-op"


@pytest.mark.asyncio
async def test_create_then_poll_returns_fresh_data(monkeypatch):
    """Invalidate-then-read correctness: a write makes the next poll re-query Mongo."""
    monkeypatch.setenv("NOTIF_POLL_CACHE_V1", "true")
    import notification_routes as nr
    from cache_helpers import invalidate_notif_poll_cache
    fake = FakeRedis()
    mongo_log = []
    docs = list(SAMPLE_DOCS)
    coll = make_notif_collection(mongo_log, docs)
    with patch("redis_client.redis_client", fake), \
         patch.object(nr, "user_notifications_collection", coll):
        first = await nr.get_user_notifications(**poll_kwargs())
        assert first.total_count == 1
        # simulate a new notification write + the invalidation the write site issues
        docs.append({**SAMPLE_DOCS[0], "_id": "un2", "notification_id": "n2"})
        await invalidate_notif_poll_cache("u-notif")
        fresh = await nr.get_user_notifications(**poll_kwargs())
    assert fresh.total_count == 2, "poll after invalidating write must see the new notification"


@pytest.mark.asyncio
async def test_redis_down_poll_still_succeeds(monkeypatch):
    monkeypatch.setenv("NOTIF_POLL_CACHE_V1", "true")
    import notification_routes as nr

    class BrokenRedis:
        def pipeline(self): raise ConnectionError("Redis down")
        async def get(self, key): raise ConnectionError("Redis down")
        async def setex(self, *a): raise ConnectionError("Redis down")

    mongo_log = []
    with patch("redis_client.redis_client", BrokenRedis()), \
         patch.object(nr, "user_notifications_collection", make_notif_collection(mongo_log)):
        out = await nr.get_user_notifications(**poll_kwargs())
    assert out.total_count == 1, "Redis outage must never break notifications"
    assert "MONGO_AGGREGATE" in mongo_log


# ── Write-site contract: every per-user mutation invalidates; bulk paths don't ──

WRITE_SITES = [
    ("notification_routes.py", "mark_notification_read"),
    ("notification_routes.py", "mark_all_notifications_read"),
    ("notification_routes.py", "delete_notification("),
    ("progress_routes.py", None),
    ("routes/session_summary_routes.py", None),
    ("app/tutor/tutor_routes.py", None),
]


@pytest.mark.parametrize("rel_path,func_name", WRITE_SITES)
def test_write_site_calls_invalidation(rel_path, func_name):
    """Source-level contract: each per-user write site is followed by
    invalidate_notif_poll_cache within a few lines of the Mongo write."""
    src = (BACKEND_DIR / rel_path).read_text()
    if func_name:
        # scope to the function body (up to the next top-level route decorator)
        start = src.index(f"async def {func_name}")
        end = src.find("@router.", start)
        body = src[start:end if end != -1 else len(src)]
    else:
        body = src
    writes = [m.start() for m in re.finditer(
        r"user_notifications(?:_collection)?\.(insert_one|update_one|update_many)\(", body)]
    assert writes, f"no per-user write found in {rel_path}:{func_name}"
    for w in writes:
        following = body[w: w + 1200]
        assert "invalidate_notif_poll_cache(" in following, (
            f"{rel_path}:{func_name or 'module'} write at offset {w} lacks invalidation")


def test_bulk_paths_do_not_invalidate():
    """Broadcast insert_many and admin delete_many intentionally rely on TTL."""
    src = (BACKEND_DIR / "notification_routes.py").read_text()
    # process_notification (broadcast) body
    start = src.index("async def process_notification")
    end = src.find("\nasync def ", start + 10)
    body = src[start:end]
    assert "insert_many" in body
    assert "invalidate_notif_poll_cache" not in body, "broadcast must NOT invalidate per-user"
    assert "accepted per CAPACITY_FIXES_V1" in body
    # admin bulk delete
    start = src.index("async def delete_notification_admin")
    end = src.find("@router.", start)
    body = src[start:end]
    assert "delete_many" in body
    assert "invalidate_notif_poll_cache" not in body
    assert "accepted per CAPACITY_FIXES_V1" in body


def test_notif_poll_ttl_constant():
    from cache_helpers import NOTIF_POLL_TTL_SECONDS
    assert NOTIF_POLL_TTL_SECONDS == 45
