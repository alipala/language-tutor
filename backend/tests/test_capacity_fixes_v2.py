"""
CAPACITY_FIXES_V2 — tests.

Work item: FU-12 coach double-count fix (RATE_LIMITER_SKIP_DOUBLE_CHECK).
Index additions are verified by an init_db integration check, not unit tests.
"""

import pytest
from unittest.mock import patch

from tests.test_capacity_fixes_v1 import FakeRedis, make_request


@pytest.mark.asyncio
async def test_flag_off_dependency_still_double_counts():
    """Legacy behavior: middleware + dependency both record (pre-existing quirk)."""
    import rate_limiter as rl
    fake = FakeRedis()
    req = make_request("/api/coach/chat")
    req.state.rate_limit_checked = True  # middleware already ran
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_SKIP_DOUBLE_CHECK", False):
        await rl.check_rate_limit(req, user_id="coach-user")
    assert len(fake.log) > 0, "flag OFF must preserve the legacy double-count exactly"


@pytest.mark.asyncio
async def test_flag_on_dependency_skips_when_middleware_checked():
    import rate_limiter as rl
    fake = FakeRedis()
    req = make_request("/api/coach/chat")
    req.state.rate_limit_checked = True
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_SKIP_DOUBLE_CHECK", True):
        await rl.check_rate_limit(req, user_id="coach-user")
    assert fake.log == [], "flag ON + middleware-checked → zero Redis ops in dependency"


@pytest.mark.asyncio
async def test_flag_on_dependency_still_checks_unmarked_requests():
    """Safety: a request that did NOT pass the middleware is still limited."""
    import rate_limiter as rl
    fake = FakeRedis()
    req = make_request("/api/coach/chat")  # no rate_limit_checked on state
    with patch("redis_client.redis_client", fake), \
         patch.object(rl, "RATE_LIMITER_BACKEND", "redis"), \
         patch.object(rl, "RATE_LIMITER_SKIP_DOUBLE_CHECK", True):
        await rl.check_rate_limit(req, user_id="coach-user")
    assert len(fake.log) > 0, "unmarked requests must still be checked with flag ON"
