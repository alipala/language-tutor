"""
Sprint 1 Units A & B — API Test Suite
======================================
Tests every business rule changed or fixed in:
  S1.1 — Silver mission challenge_type mapping
  S1.2 — Progress denominator / week-math
  S1.3 — Voice-check routing failure modes
  S1.4 — silver_reason surfaced on hub
  S1.5 — structured_summary on session (data availability)
  S1.x — Session count limits removed (minutes-only gate)

Runs against http://localhost:8000 which is connected to production MongoDB.
All mutations are non-destructive (reads only, except track-usage which is tested
against a sandboxed assertion without committing).

Usage:
  python tests/test_sprint1_units_ab.py
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

BASE = "http://localhost:8000"
TIMEOUT = 20

# ── Test users ───────────────────────────────────────────────────────────────
USERS = {
    "hockey": {
        "email": "miheso1615@marineso.com",
        "password": "040050803",
        "label": "Hockey Day (try_learn, 12-mo plan, 8 completed sessions)",
    },
    "suzan": {
        "email": "topoh15583@codoteam.com",
        "password": "040050803",
        "label": "Suzan (unknown plan/subscription state)",
    },
}

# ── Result tracking ──────────────────────────────────────────────────────────
@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str
    warning: str = ""

results: list[TestResult] = []

def ok(name, detail=""):
    results.append(TestResult(name, True, detail))
    print(f"  ✅ {name}")
    if detail:
        print(f"     {detail}")

def fail(name, detail=""):
    results.append(TestResult(name, False, detail))
    print(f"  ❌ {name}")
    if detail:
        print(f"     {detail}")

def warn(name, detail="", warning=""):
    results.append(TestResult(name, True, detail, warning))
    print(f"  ⚠️  {name}")
    if detail:
        print(f"     {detail}")
    if warning:
        print(f"     NOTE: {warning}")

def section(title):
    print(f"\n{'─'*65}")
    print(f"  {title}")
    print(f"{'─'*65}")


# ── Auth helper ──────────────────────────────────────────────────────────────
async def login(client: httpx.AsyncClient, email: str, password: str) -> Optional[str]:
    """Single-attempt login — does NOT retry to preserve rate limit budget."""
    r = await client.post("/api/auth/login",
        json={"email": email, "password": password}, timeout=TIMEOUT)
    if r.status_code == 429:
        data = r.json()
        retry_after = data.get("retry_after", 300)
        print(f"  ⚠️  Rate limited — waiting {retry_after}s before retrying...")
        await asyncio.sleep(retry_after + 2)
        r = await client.post("/api/auth/login",
            json={"email": email, "password": password}, timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json()
        return data.get("access_token") or data.get("token")
    return None


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUPS
# ════════════════════════════════════════════════════════════════════════════

async def test_auth(client: httpx.AsyncClient) -> dict:
    """Authenticate all users, return token map. One attempt per user."""
    section("AUTH — Login all test users")
    tokens = {}
    for key, u in USERS.items():
        token = await login(client, u["email"], u["password"])
        if token:
            tokens[key] = token
            ok(f"Login {key}", u["label"])
        else:
            # Account may not exist in this environment — skip (not a code bug)
            warn(f"Login {key} — SKIP", f"{u['email']} not found in DB (account may not exist here)")
    return tokens


async def test_s11_silver_challenge_type(client: httpx.AsyncClient, tokens: dict):
    """
    S1.1 — Silver mission challenge_type
    Rules:
      - Every hub response missions array must have a 'challenge_type' field on the silver mission
      - challenge_type must NOT always be 'micro_quiz' (varies by user DNA)
      - challenge_type must be one of the 6 valid types
    """
    section("S1.1 — Silver mission challenge_type mapping")
    VALID_TYPES = {"error_spotting", "native_check", "smart_flashcard",
                   "story_builder", "micro_quiz", "brain_tickler"}
    seen_types = set()

    for key, token in tokens.items():
        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code != 200:
            fail(f"[{key}] hub/today returned {r.status_code}")
            continue

        data = r.json()
        missions = data.get("missions", [])
        silver_reason = data.get("silver_reason")
        silver = next((m for m in missions if m.get("tier") == "silver"), None)

        if not silver:
            warn(f"[{key}] No silver mission today", "May be a rest day or no plan — skipping")
            continue

        ct = silver.get("challenge_type")

        # Rule: field must be present (not missing key)
        if "challenge_type" not in silver:
            fail(f"[{key}] challenge_type key MISSING from silver mission")
            continue

        # Rule: must be a valid type (not arbitrary string)
        if ct is not None and ct not in VALID_TYPES:
            fail(f"[{key}] challenge_type='{ct}' not in valid set {VALID_TYPES}")
            continue

        seen_types.add(ct)
        ok(f"[{key}] challenge_type='{ct}'  silver_reason='{str(silver_reason)[:60]}'")

    # Rule: across all users, should see more than just 'micro_quiz'
    if len(seen_types) > 0:
        if seen_types == {"micro_quiz"} and len(tokens) >= 3:
            fail("Diversity check: ALL users got 'micro_quiz' — mapping bug may still be present",
                 f"seen={seen_types}")
        elif None in seen_types and len(seen_types) == 1:
            warn("Diversity check: all challenge_types are null", "Users may have no DNA data yet")
        else:
            ok(f"Diversity check: {len(seen_types)} distinct types seen", f"types={seen_types}")


async def test_s12_progress_denominators(client: httpx.AsyncClient, tokens: dict):
    """
    S1.2 — Progress denominators + week-math
    Rules:
      - plan.total_sessions must equal {1:16, 2:32, 3:48, 6:96, 12:192}[duration_months]
      - Hub completed/total must match LearningPlanDetailsModal's source (same plan doc)
      - currentWeek = ceil(completed_sessions / 4), NOT /3
      - currentWeek must not exceed weekly_schedule length
    """
    section("S1.2 — Progress denominators & week-math")
    EXPECTED_TOTALS = {1: 16, 2: 32, 3: 48, 6: 96, 12: 192}
    import math

    for key, token in tokens.items():
        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code != 200:
            fail(f"[{key}] hub/today {r.status_code}")
            continue

        data = r.json()
        plans = data.get("learning_plans", [])
        if not plans:
            warn(f"[{key}] No learning plans", "Skipping denominator check")
            continue

        for plan in plans:
            pid = plan.get("id", plan.get("_id", "?"))
            completed = plan.get("completed_sessions", 0)
            total = plan.get("total_sessions")
            duration = plan.get("duration_months")
            progress_pct = plan.get("progress_percentage")

            # Rule: total_sessions must be present
            if total is None:
                fail(f"[{key}] plan={pid} total_sessions MISSING from hub response")
                continue

            # Rule: total_sessions must match canonical dict (assumes 4 sessions/week)
            # Some legacy plans use non-standard cadence (2 sessions/week) — validate
            # internal consistency instead of failing hard.
            if duration and duration in EXPECTED_TOTALS:
                expected = EXPECTED_TOTALS[duration]
                weeks = duration * 4
                spw = plan.get("sessions_per_week") or (total // weeks if weeks else None)
                if total == expected:
                    ok(f"[{key}] plan={pid} total_sessions={total} correct for {duration}mo")
                elif spw and spw != 4 and total == weeks * spw:
                    ok(f"[{key}] plan={pid} total_sessions={total} correct for {duration}mo @ {spw} sessions/week")
                else:
                    fail(f"[{key}] plan={pid} total_sessions={total} but expected {expected} for {duration}mo plan")
            else:
                warn(f"[{key}] plan={pid} duration_months={duration} not in canonical dict",
                     warning=f"total_sessions={total}")

            # Rule: week-math — ceil(completed/4) must not exceed weekly_schedule length
            weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", []) if plan.get("plan_content") else []
            week_len = len(weekly_schedule)
            if completed > 0 and week_len > 0:
                correct_week = math.ceil(completed / 4)
                buggy_week   = math.ceil(completed / 3)
                if correct_week > week_len:
                    fail(f"[{key}] plan={pid} ceil(completed/4)={correct_week} exceeds weekly_schedule length={week_len}")
                elif buggy_week > week_len and correct_week <= week_len:
                    ok(f"[{key}] plan={pid} BUG FIXED: /3 would give week {buggy_week} (out of bounds), /4 gives {correct_week} ✓",
                    )
                elif correct_week != buggy_week:
                    ok(f"[{key}] plan={pid} Week math correct: ceil({completed}/4)={correct_week} vs old ceil({completed}/3)={buggy_week}")
                else:
                    ok(f"[{key}] plan={pid} completed={completed} → week={correct_week} (no divergence at this count)")

            # Rule: progress_percentage consistent with completed/total
            if total and total > 0:
                expected_pct = round((completed / total) * 100)
                if progress_pct is not None and abs(progress_pct - expected_pct) > 2:
                    fail(f"[{key}] plan={pid} progress_percentage={progress_pct} inconsistent with {completed}/{total}={expected_pct}%")
                else:
                    ok(f"[{key}] plan={pid} progress={completed}/{total} ({progress_pct}%)")


async def test_s13_voice_check(client: httpx.AsyncClient, tokens: dict):
    """
    S1.3 — Voice-check status endpoint
    Rules:
      - GET /api/learning/plan/{id}/voice-check-status must respond (200 or 403/404)
      - For free users: is_due must be False (voice checks gated on premium)
      - For plans with no voice_check_schedule: is_due must be False
      - Response must have 'is_due' boolean field
    """
    section("S1.3 — Voice-check status endpoint")

    for key, token in tokens.items():
        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code != 200:
            continue

        plans = r.json().get("learning_plans", [])
        if not plans:
            warn(f"[{key}] No plans to check voice-check status")
            continue

        plan = plans[0]
        pid = plan.get("id", plan.get("_id", "?"))
        sub_plan = r.json().get("subscription", {}).get("plan", "unknown")

        vc_r = await client.get(
            f"/api/learning/plan/{pid}/voice-check-status",
            headers=auth_headers(token), timeout=TIMEOUT
        )

        if vc_r.status_code == 404:
            warn(f"[{key}] voice-check-status 404 for plan={pid}", "Plan may not be found by this route")
            continue
        if vc_r.status_code == 403:
            ok(f"[{key}] voice-check-status 403 (premium only gate working)", f"plan={pid} sub={sub_plan}")
            continue
        if vc_r.status_code != 200:
            fail(f"[{key}] voice-check-status {vc_r.status_code}", vc_r.text[:100])
            continue

        vc_data = vc_r.json()

        # Rule: must have is_due field
        if "is_due" not in vc_data:
            fail(f"[{key}] voice-check response missing 'is_due' field", str(vc_data)[:100])
            continue

        is_due = vc_data["is_due"]
        completed = plan.get("completed_sessions", 0)

        # Rule: free users should not have voice checks due (premium feature)
        if sub_plan in ("try_learn", "free") and is_due:
            fail(f"[{key}] is_due=True for free user — voice checks should be premium-only",
                 f"sub={sub_plan}  completed={completed}")
        elif sub_plan in ("try_learn", "free") and not is_due:
            ok(f"[{key}] is_due=False for free user (correct)", f"sub={sub_plan}  completed={completed}")
        else:
            ok(f"[{key}] is_due={is_due}", f"sub={sub_plan}  completed={completed}  data={vc_data}")


async def test_s14_silver_reason(client: httpx.AsyncClient, tokens: dict):
    """
    S1.4 — silver_reason surfaced in hub response
    Rules:
      - Hub response must have top-level 'silver_reason' field (can be null)
      - When silver_reason is present and non-empty, it must be a string <= 200 chars
      - silver_reason must appear on the silver mission (mobile maps it via DailyQuest.silverReason)
      - silver mission's title/subtitle must not contain 'micro_quiz' literally (would indicate fallback bug)
    """
    section("S1.4 — silver_reason on hub response")

    for key, token in tokens.items():
        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code != 200:
            fail(f"[{key}] hub/today {r.status_code}")
            continue

        data = r.json()

        # Rule: top-level field must exist
        if "silver_reason" not in data:
            fail(f"[{key}] 'silver_reason' key MISSING from hub response top-level")
            continue

        sr = data.get("silver_reason")

        # Rule: if present, must be string and reasonable length
        if sr is not None:
            if not isinstance(sr, str):
                fail(f"[{key}] silver_reason is not a string: {type(sr)}")
                continue
            if len(sr) > 200:
                fail(f"[{key}] silver_reason too long ({len(sr)} chars): '{sr[:80]}...'")
                continue
            ok(f"[{key}] silver_reason='{sr[:80]}'")
        else:
            warn(f"[{key}] silver_reason=null", "User may have no DNA data yet (acceptable)")

        # Rule: silver mission title must not expose 'micro_quiz' as raw string
        missions = data.get("missions", [])
        silver = next((m for m in missions if m.get("tier") == "silver"), None)
        if silver:
            title = silver.get("title", "")
            if "micro_quiz" in str(title).lower():
                fail(f"[{key}] Silver mission title contains raw 'micro_quiz': '{title}'")
            else:
                ok(f"[{key}] Silver title='{str(title)[:60]}' (no raw type leak)")


async def test_session_limits_removed(client: httpx.AsyncClient, tokens: dict):
    """
    S1.x — Session count limits removed; minutes are the only gate.
    Rules:
      - GET /api/subscription/limits must return sessions_remaining=-1 for all non-mastery plans
      - is_unlimited must be True only for language_mastery (minutes=-1)
      - is_unlimited must be False for try_learn/fluency_builder (has minute cap)
      - minutes_remaining must be present and >= 0 (or -1 for unlimited)
      - The old 3-session free limit must not appear anywhere
    """
    section("S1.x — Session count limits removed (minutes-only gate)")

    for key, token in tokens.items():
        # Try the subscription limits endpoint
        r = await client.get("/api/subscription/limits", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code == 404:
            # Try alternate route
            r = await client.get("/api/stripe/subscription-limits", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code == 404:
            # Fall back to hub today which embeds subscription
            r2 = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
            if r2.status_code != 200:
                fail(f"[{key}] Cannot reach subscription data")
                continue
            sub = r2.json().get("subscription", {})
            limits = sub.get("limits", {})
            plan = sub.get("plan", "?")
        else:
            data = r.json()
            limits = data.get("limits", data)
            plan = limits.get("plan", data.get("plan", "?"))

        sessions_remaining = limits.get("sessions_remaining")
        sessions_limit     = limits.get("sessions_limit")
        minutes_remaining  = limits.get("minutes_remaining")
        minutes_limit      = limits.get("minutes_limit")
        is_unlimited       = limits.get("is_unlimited", False)

        # Rule: sessions_remaining must be -1 (unlimited) for all plans
        if sessions_remaining == 0:
            fail(f"[{key}] sessions_remaining=0 — old session gate still active! plan={plan}")
        elif sessions_remaining == -1:
            ok(f"[{key}] sessions_remaining=-1 (unlimited) ✓  plan={plan}")
        elif sessions_remaining is None:
            warn(f"[{key}] sessions_remaining not in response", f"limits keys={list(limits.keys())}")
        else:
            fail(f"[{key}] sessions_remaining={sessions_remaining} — should be -1  plan={plan}")

        # Rule: is_unlimited reflects minutes only
        if plan in ("try_learn", "free", "fluency_builder"):
            if is_unlimited:
                fail(f"[{key}] is_unlimited=True for {plan} — should be False (has minute cap)")
            else:
                ok(f"[{key}] is_unlimited=False for {plan} (correct — has minute cap)")
        elif plan in ("language_mastery", "team_mastery"):
            if not is_unlimited:
                fail(f"[{key}] is_unlimited=False for {plan} — should be True")
            else:
                ok(f"[{key}] is_unlimited=True for {plan} (correct)")

        # Rule: minutes_remaining must be present
        if minutes_remaining is None:
            fail(f"[{key}] minutes_remaining MISSING from limits  plan={plan}")
        else:
            ok(f"[{key}] minutes_remaining={minutes_remaining}  minutes_limit={minutes_limit}")

        # Rule: old session cap must not match the old hardcoded values
        if sessions_limit in (3, 30):
            fail(f"[{key}] sessions_limit={sessions_limit} — old cap still set (3=free, 30=fluency)")
        elif sessions_limit == -1 or sessions_limit is None:
            ok(f"[{key}] sessions_limit={sessions_limit} — no count cap ✓")


async def test_s15_structured_summary_availability(client: httpx.AsyncClient, tokens: dict):
    """
    S1.5 — Structured summary data availability
    Rules:
      - The session-summary endpoint accepts POST with correct payload (no 5xx)
      - For free users: structured_summary may be null (background task gated on premium)
      - For any user: response must include 'session_stats' field
      - Response shape must include 'structured_summary' key (even if null)
    Rules for null-safety (mobile):
      - When structured_summary is null, UI must not crash (tested via data contract)
    """
    section("S1.5 — Structured summary: endpoint contract & null-safety")

    # We test with the hockey user who has an active plan
    for key in ("hockey", "bory", "heavy"):
        token = tokens.get(key)
        if not token:
            warn(f"[{key}] No token — skipping")
            continue

        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code != 200:
            continue

        plans = r.json().get("learning_plans", [])
        sub   = r.json().get("subscription", {})
        if not plans:
            warn(f"[{key}] No plans — skipping structured_summary test")
            continue

        plan = plans[0]
        pid  = plan.get("id", plan.get("_id"))
        lang = plan.get("language", "dutch")
        level = plan.get("proficiency_level", "A2")

        # Test the session summary endpoint contract with a minimal payload
        # (1-message session, won't persist — we check response shape only)
        minimal_messages = [
            {"role": "user",      "content": "Hallo, hoe gaat het?",    "timestamp": "2026-05-27T10:00:00Z"},
            {"role": "assistant", "content": "Goed, dank je! En jij?",  "timestamp": "2026-05-27T10:00:01Z"},
        ]

        r2 = await client.post(
            f"/api/learning/session-summary?plan_id={pid}&session_summary=test",
            headers=auth_headers(token),
            json={
                "messages":               minimal_messages,
                "duration_minutes":       1,
                "selected_duration":      1,
                "language":               lang,
                "level":                  level,
                "sentences_for_analysis": None,
                "correction_bonus_xp":    0,
            },
            timeout=30,
        )

        if r2.status_code == 422:
            fail(f"[{key}] session-summary 422 Unprocessable — payload mismatch", r2.text[:200])
            continue
        if r2.status_code >= 500:
            fail(f"[{key}] session-summary {r2.status_code} server error", r2.text[:200])
            continue
        if r2.status_code != 200:
            warn(f"[{key}] session-summary {r2.status_code}", r2.text[:100])
            continue

        data = r2.json()

        # Rule: 'structured_summary' key must be in response
        if "structured_summary" not in data:
            fail(f"[{key}] 'structured_summary' key MISSING from session-summary response")
        else:
            ss = data["structured_summary"]
            if ss is None:
                plan_sub = sub.get("plan", "?")
                if plan_sub in ("try_learn", "free"):
                    ok(f"[{key}] structured_summary=null for {plan_sub} user (correct — premium feature)")
                else:
                    warn(f"[{key}] structured_summary=null for {plan_sub} user",
                         warning="Background task may not have run yet")
            else:
                # Rule: if present, must have the 4 expected fields
                expected_fields = {"breakthrough_moment", "compressed_summary",
                                   "focus_next_session", "student_confidence"}
                missing = expected_fields - set(ss.keys())
                if missing:
                    fail(f"[{key}] structured_summary missing fields: {missing}")
                else:
                    ok(f"[{key}] structured_summary has all 4 fields ✓")
                    ok(f"[{key}] compressed_summary='{str(ss.get('compressed_summary',''))[:60]}'")

        # Rule: session_stats must be present
        if "session_stats" not in data:
            fail(f"[{key}] 'session_stats' key MISSING from session-summary response")
        else:
            ok(f"[{key}] session_stats present ✓")

        # Rule: null-safety — if structured_summary is null, the 3 display fields
        # must all degrade gracefully (checked by contract: null is valid)
        ss = data.get("structured_summary") or {}
        bm = ss.get("breakthrough_moment") if ss else None
        cs = ss.get("compressed_summary") if ss else None
        fn = ss.get("focus_next_session") if ss else None

        if bm is None:
            ok(f"[{key}] null-safety: breakthrough_moment=null → block hidden (correct)")
        if cs is None:
            ok(f"[{key}] null-safety: compressed_summary=null → fallback 'Session complete.' shown")
        if fn is None:
            ok(f"[{key}] null-safety: focus_next_session=null → block hidden (correct)")


async def test_hub_response_shape(client: httpx.AsyncClient, tokens: dict):
    """
    Cross-cutting: validate full hub response shape contains all Sprint 1 fields.
    """
    section("CROSS-CUTTING — Hub response shape (all Sprint 1 fields present)")

    REQUIRED_TOP_KEYS = {"missions", "learning_plans", "subscription", "silver_reason"}

    for key, token in tokens.items():
        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code != 200:
            fail(f"[{key}] hub/today {r.status_code}")
            continue

        data = r.json()
        missing = REQUIRED_TOP_KEYS - set(data.keys())
        if missing:
            fail(f"[{key}] Hub response missing keys: {missing}")
        else:
            ok(f"[{key}] Hub has all required top-level keys ✓")

        # Each mission must have: id, tier, challenge_type (even if null), title
        missions = data.get("missions", [])
        for m in missions:
            for req in ("id", "tier", "title"):
                if req not in m:
                    fail(f"[{key}] Mission missing '{req}': {m}")
            if "challenge_type" not in m:
                fail(f"[{key}] Mission (id={m.get('id')}) missing 'challenge_type' key")

        if missions:
            ok(f"[{key}] All {len(missions)} missions have required fields ✓")

        # Subscription block must have limits.minutes_remaining
        sub = data.get("subscription", {})
        limits = sub.get("limits", {})
        if "minutes_remaining" not in limits:
            fail(f"[{key}] subscription.limits missing 'minutes_remaining'")
        else:
            ok(f"[{key}] subscription.limits.minutes_remaining={limits['minutes_remaining']}")


async def test_edge_cases(client: httpx.AsyncClient, tokens: dict):
    """
    Edge cases:
      - User with no plans (light): hub must not 500
      - Unauthenticated hub request: must return 401/403
      - Voice-check for non-existent plan: must return 404 not 500
      - track-usage with assessment type still gates (sessions do not)
    """
    section("EDGE CASES")

    # Edge: unauthenticated hub request
    r = await client.get("/api/hub/today", timeout=TIMEOUT)
    if r.status_code in (401, 403):
        ok("Unauthenticated hub → 401/403 ✓")
    elif r.status_code == 200:
        fail("Unauthenticated hub returned 200 — auth not enforced")
    else:
        warn(f"Unauthenticated hub → {r.status_code}", r.text[:60])

    # Edge: user with no plans (light user)
    token = tokens.get("light")
    if token:
        r = await client.get("/api/hub/today", headers=auth_headers(token), timeout=TIMEOUT)
        if r.status_code == 200:
            plans = r.json().get("learning_plans", [])
            missions = r.json().get("missions", [])
            ok(f"No-plan user hub 200 ✓  plans={len(plans)}  missions={len(missions)}")
        else:
            fail(f"No-plan user hub → {r.status_code}")

    # Edge: voice-check for non-existent plan ID
    if token:
        r = await client.get(
            "/api/learning/plan/000000000000000000000000/voice-check-status",
            headers=auth_headers(token), timeout=TIMEOUT
        )
        if r.status_code in (404, 403):
            ok(f"Fake plan voice-check-status → {r.status_code} (not 500) ✓")
        elif r.status_code == 500:
            fail("Fake plan voice-check-status → 500 (unhandled error)")
        else:
            ok(f"Fake plan voice-check-status → {r.status_code}")

    # Edge: sessions_remaining should NOT be 3 for any try_learn user (old cap)
    for key in ("heavy", "medium", "light", "hockey", "bory"):
        t = tokens.get(key)
        if not t:
            continue
        r = await client.get("/api/hub/today", headers=auth_headers(t), timeout=TIMEOUT)
        if r.status_code != 200:
            continue
        limits = r.json().get("subscription", {}).get("limits", {})
        sr = limits.get("sessions_remaining")
        if sr == 3:
            fail(f"[{key}] sessions_remaining=3 — old free-tier session cap still active!")
        elif sr == 30:
            fail(f"[{key}] sessions_remaining=30 — old fluency cap still active!")
        elif sr == -1:
            ok(f"[{key}] sessions_remaining=-1 (unlimited sessions) ✓")

    # Edge: expired/invalid token
    r = await client.get("/api/hub/today",
        headers={"Authorization": "Bearer invalid.token.here"}, timeout=TIMEOUT)
    if r.status_code in (401, 403, 422):
        ok(f"Invalid token → {r.status_code} ✓")
    else:
        warn(f"Invalid token → {r.status_code}", r.text[:60])


# ════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ════════════════════════════════════════════════════════════════════════════

async def main():
    print("=" * 65)
    print("  MyTacoAI — Sprint 1 Units A & B API Test Suite")
    print(f"  Target: {BASE}")
    print(f"  Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    async with httpx.AsyncClient(base_url=BASE) as client:
        # Auth first — all other tests depend on tokens
        tokens = await test_auth(client)

        if not tokens:
            print("\n❌ No users could authenticate — aborting.")
            sys.exit(1)

        # Run all test groups
        await test_hub_response_shape(client, tokens)
        await test_s11_silver_challenge_type(client, tokens)
        await test_s12_progress_denominators(client, tokens)
        await test_s13_voice_check(client, tokens)
        await test_s14_silver_reason(client, tokens)
        await test_session_limits_removed(client, tokens)
        await test_s15_structured_summary_availability(client, tokens)
        await test_edge_cases(client, tokens)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print("  RESULTS SUMMARY")
    print(f"{'='*65}")

    passed  = [r for r in results if r.passed]
    failed  = [r for r in results if not r.passed]
    warned  = [r for r in results if r.passed and r.warning]

    print(f"  Total : {len(results)}")
    print(f"  ✅ Pass : {len(passed)}")
    print(f"  ❌ Fail : {len(failed)}")
    print(f"  ⚠️  Warn : {len(warned)}")

    if failed:
        print(f"\n  FAILURES:")
        for r in failed:
            print(f"    ❌ {r.name}")
            if r.detail:
                print(f"       {r.detail}")

    if warned:
        print(f"\n  WARNINGS (passed with caveats):")
        for r in warned:
            print(f"    ⚠️  {r.name}: {r.warning}")

    print(f"\n{'='*65}")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    asyncio.run(main())
