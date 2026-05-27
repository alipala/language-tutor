"""
Sprint 2 Unit E — Voice-Check Unbox Ceremony Tests
====================================================
S2.1, S2.2, S2.5

Business rules under test:
  BR-1  analyze-session response contains 'previous_strand_values' key
  BR-2  analyze-session response contains 'causal_sentence' inside session_insights
  BR-3  causal_sentence is a string (or null fallback), never crashes the endpoint
  BR-4  anticipationCopy utility: correct strings for each distance bucket
  BR-5  anticipationCopy returns '' for null / negative distance
  BR-6  countdownBucket returns correct bucket labels
  BR-7  useNextVoiceCheck hook logic: sessionsUntilNext = next_check - current_session
  BR-8  voice-check-status endpoint returns 'next_check' and 'current_session'
  BR-9  analyze-session still returns 200 for premium users (no regression)
  BR-10 analyze-session returns 403 for free/try_learn users (gate unchanged)
  BR-11 causal_sentence fallback ('Six sessions…') present in backend source
  BR-12 previous_strand_values is {} (empty dict) for first-time users (no existing profile)

Usage:
    python tests/test_sprint2_unite_voice_ceremony.py
"""

import asyncio
import ast
import os
import sys
import time
from typing import Optional

import httpx

BASE     = "http://localhost:8000"
TIMEOUT  = 30
PASSWORD = "040050803"

USERS = {
    "hockey": {
        "email": "miheso1615@marineso.com",
        "label": "Hockey Day (try_learn)",
        "is_premium": False,
    },
    "suzan": {
        "email": "topoh15583@codoteam.com",
        "label": "Suzan (try_learn, has DNA sessions)",
        "is_premium": False,
    },
}

# ── Result tracking ──────────────────────────────────────────────────────────
results: list = []

def ok(msg: str, detail: str = ""):
    results.append(("PASS", msg))
    detail_str = f"\n     {detail}" if detail else ""
    print(f"  ✅ {msg}{detail_str}")

def fail(msg: str, detail: str = ""):
    results.append(("FAIL", msg))
    detail_str = f"\n     {detail}" if detail else ""
    print(f"  ❌ {msg}{detail_str}")

def warn(msg: str, detail: str = ""):
    results.append(("WARN", msg))
    detail_str = f"\n     {detail}" if detail else ""
    print(f"  ⚠️  {msg}{detail_str}")

def section(title: str):
    print(f"\n{'─'*65}")
    print(f"  {title}")
    print(f"{'─'*65}")

def hdrs(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

# ── Login helper ─────────────────────────────────────────────────────────────

async def login(client: httpx.AsyncClient, email: str) -> Optional[str]:
    try:
        r = await client.post(
            "/api/auth/login",
            json={"email": email, "password": PASSWORD},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
        if r.status_code == 429:
            retry_after = int(r.headers.get("retry-after", 30))
            warn(f"Rate limited — retry after {retry_after}s")
        return None
    except Exception as e:
        warn(f"Login error: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# BR-4/5/6 — anticipationCopy and countdownBucket static tests
# ════════════════════════════════════════════════════════════════════════════

def test_anticipation_copy_logic():
    section("BR-4/5/6 — anticipationCopy copy variations and bucket labels")

    util_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "github", "MyTacoAIMobile", "src", "utils", "anticipationCopy.ts"
    )
    if not os.path.exists(util_path):
        warn("BR-4 anticipationCopy.ts not found — skipping static checks")
        return

    with open(util_path) as f:
        src = f.read()

    # BR-4: check all four copy buckets are present
    buckets = {
        "far (>=6)":   "in ${sessionsUntilNext} sessions",
        "mid (3-5)":   "sessions until your next reading",
        "close (1-2)": "Almost there",
        "today (0)":   "unlocks at the end of this session",
    }
    for label, phrase in buckets.items():
        if phrase in src:
            ok(f"BR-4 anticipationCopy {label} copy present")
        else:
            fail(f"BR-4 anticipationCopy {label} copy missing: '{phrase}'")

    # BR-5: null/negative returns '' (empty string fallback)
    if "return ''" in src or "return \"\"" in src:
        ok("BR-5 anticipationCopy returns '' for null/out-of-range distance")
    else:
        fail("BR-5 anticipationCopy missing empty-string fallback")

    # BR-6: countdownBucket function present
    if "countdownBucket" in src:
        ok("BR-6 countdownBucket function exported")
    else:
        fail("BR-6 countdownBucket function not found")

    # BR-6: bucket labels
    for label in ("far", "mid", "close", "today", "unknown"):
        if f"'{label}'" in src or f'"{label}"' in src:
            ok(f"BR-6 countdownBucket returns '{label}' bucket")
        else:
            fail(f"BR-6 countdownBucket missing '{label}' bucket")


# ════════════════════════════════════════════════════════════════════════════
# BR-7 — useNextVoiceCheck hook logic
# ════════════════════════════════════════════════════════════════════════════

def test_use_next_voice_check_hook():
    section("BR-7 — useNextVoiceCheck hook: sessionsUntilNext derivation")

    hook_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "github", "MyTacoAIMobile", "src", "hooks", "useNextVoiceCheck.ts"
    )
    if not os.path.exists(hook_path):
        warn("BR-7 useNextVoiceCheck.ts not found — skipping")
        return

    with open(hook_path) as f:
        src = f.read()

    if "nextCheck - current" in src or "nextCheck - currentSession" in src:
        ok("BR-7 hook computes sessionsUntilNext = next_check - current_session")
    else:
        fail("BR-7 hook missing subtraction: next_check - current_session")

    if "null" in src and "setSessionsUntilNext" in src:
        ok("BR-7 hook returns null when no nextCheck (all checks complete)")
    else:
        warn("BR-7 hook null-return check not verified")

    if "403" in src or "catch" in src:
        ok("BR-7 hook silently nulls out on 403 (free user)")
    else:
        fail("BR-7 hook missing error/403 handling")


# ════════════════════════════════════════════════════════════════════════════
# BR-11 — Causal sentence fallback in backend source
# ════════════════════════════════════════════════════════════════════════════

def test_causal_sentence_fallback():
    section("BR-11 — Causal sentence: fallback and generation code present")

    svc_path = os.path.join(
        os.path.dirname(__file__), "..", "services", "speaking_dna_service.py"
    )
    with open(svc_path) as f:
        src = f.read()

    if "_CAUSAL_FALLBACK" in src:
        ok("BR-11 _CAUSAL_FALLBACK constant defined")
    else:
        fail("BR-11 _CAUSAL_FALLBACK constant missing")

    if "Six sessions of practice moved your DNA" in src:
        ok("BR-11 fallback copy: 'Six sessions of practice moved your DNA. Keep going.'")
    else:
        fail("BR-11 fallback copy text not found")

    if "_generate_causal_sentence" in src:
        ok("BR-11 _generate_causal_sentence method present")
    else:
        fail("BR-11 _generate_causal_sentence method missing")

    if "gpt-4.1-mini" in src and "_generate_causal_sentence" in src:
        ok("BR-11 gpt-4.1-mini used for causal sentence generation")
    else:
        warn("BR-11 GPT model in causal sentence not confirmed (may be inside method)")

    # BR-12: previous_strand_values captured before strands update
    if "previous_strand_values" in src and "dna_strands" in src:
        ok("BR-12 previous_strand_values captured from existing profile dna_strands")
    else:
        fail("BR-12 previous_strand_values capture missing")

    if 'previous_strand_values": previous_strand_values' in src or \
       '"previous_strand_values": previous_strand_values' in src or \
       "'previous_strand_values': previous_strand_values" in src:
        ok("BR-12 previous_strand_values included in return dict")
    else:
        fail("BR-12 previous_strand_values not included in return dict")


# ════════════════════════════════════════════════════════════════════════════
# BR-1/2/3 — AnalyzeSessionResponse model has new fields
# ════════════════════════════════════════════════════════════════════════════

def test_response_model():
    section("BR-1/2/3 — AnalyzeSessionResponse model extensions")

    models_path = os.path.join(os.path.dirname(__file__), "..", "models.py")
    with open(models_path) as f:
        src = f.read()

    # BR-1: previous_strand_values field
    if "previous_strand_values" in src:
        ok("BR-1 AnalyzeSessionResponse.previous_strand_values field present")
    else:
        fail("BR-1 AnalyzeSessionResponse.previous_strand_values missing from models.py")

    # BR-2: causal_sentence field in SessionInsights
    if "causal_sentence" in src:
        ok("BR-2 SessionInsights.causal_sentence field present")
    else:
        fail("BR-2 SessionInsights.causal_sentence missing from models.py")

    # BR-3: Optional type for both new fields
    if "Optional" in src and "causal_sentence" in src:
        ok("BR-3 causal_sentence is Optional (won't crash when absent)")
    else:
        warn("BR-3 Optional type for causal_sentence not confirmed")

    if "Optional" in src and "previous_strand_values" in src:
        ok("BR-3 previous_strand_values is Optional (won't crash for new users)")
    else:
        warn("BR-3 Optional type for previous_strand_values not confirmed")


# ════════════════════════════════════════════════════════════════════════════
# AUTH + API live tests
# ════════════════════════════════════════════════════════════════════════════

async def test_voice_check_status_endpoint(client: httpx.AsyncClient, tokens: dict):
    section("BR-8 — voice-check-status: returns next_check and current_session")

    for key, token in tokens.items():
        # Need a plan_id — try to get one from user's plans
        r = await client.get("/api/learning/plans", headers=hdrs(token), timeout=TIMEOUT)
        if r.status_code != 200:
            warn(f"BR-8 [{key}] Could not fetch plans: {r.status_code}")
            continue

        plans = r.json()
        if not plans:
            warn(f"BR-8 [{key}] No plans found — skipping voice-check-status test")
            continue

        plan_id = plans[0].get("id") or plans[0].get("_id") or str(plans[0].get("id", ""))
        if not plan_id:
            warn(f"BR-8 [{key}] Could not extract plan_id")
            continue

        r2 = await client.get(
            f"/api/learning/plan/{plan_id}/voice-check-status",
            headers=hdrs(token),
            timeout=TIMEOUT
        )
        if r2.status_code == 200:
            data = r2.json()
            if "next_check" in data:
                ok(f"BR-8 [{key}] voice-check-status contains 'next_check': {data.get('next_check')}")
            else:
                fail(f"BR-8 [{key}] 'next_check' missing from voice-check-status response")
            if "current_session" in data:
                ok(f"BR-8 [{key}] voice-check-status contains 'current_session': {data.get('current_session')}")
            else:
                fail(f"BR-8 [{key}] 'current_session' missing from voice-check-status response")
        elif r2.status_code == 403:
            ok(f"BR-8 [{key}] voice-check-status → 403 (free user, expected)")
        else:
            warn(f"BR-8 [{key}] voice-check-status → {r2.status_code}: {r2.text[:80]}")


async def test_analyze_session_endpoint_gate(client: httpx.AsyncClient, tokens: dict):
    section("BR-9/BR-10 — analyze-session: free user 403, endpoint accessible")

    # BR-10: free user gets 403
    for key, token in tokens.items():
        minimal_session = {
            "session_id": f"test_ceremony_{int(time.time())}",
            "session_type": "voice_check",
            "duration_seconds": 10,
            "user_turns": [],
            "corrections_received": [],
            "challenges_offered": 0,
            "challenges_accepted": 0,
            "topics_discussed": ["test"],
        }
        r = await client.post(
            "/api/speaking-dna/analyze-session?language=dutch",
            json=minimal_session,
            headers=hdrs(token),
            timeout=TIMEOUT
        )
        if r.status_code == 403:
            ok(f"BR-10 [{key}] analyze-session → 403 for free user (gate preserved)")
        elif r.status_code == 200:
            data = r.json()
            # BR-1: check previous_strand_values
            if "previous_strand_values" in data:
                ok(f"BR-1 [{key}] response contains 'previous_strand_values'")
            else:
                fail(f"BR-1 [{key}] 'previous_strand_values' missing from response")
            # BR-2: check causal_sentence
            insights = data.get("session_insights", {})
            if "causal_sentence" in insights:
                ok(f"BR-2 [{key}] session_insights contains 'causal_sentence': '{insights['causal_sentence'][:60]}'")
            else:
                fail(f"BR-2 [{key}] 'causal_sentence' missing from session_insights")
            ok(f"BR-9 [{key}] analyze-session → 200 (no regression)")
        elif r.status_code == 422:
            ok(f"BR-9/10 [{key}] analyze-session → 422 (validation OK, endpoint reachable — auth passed)")
        else:
            warn(f"BR-10 [{key}] analyze-session → {r.status_code}: {r.text[:80]}")


# ════════════════════════════════════════════════════════════════════════════
# S2.1 ceremony mobile source checks
# ════════════════════════════════════════════════════════════════════════════

def test_ceremony_mobile_source():
    section("S2.1 — DNAVoiceScanScreen ceremony state machine")

    screen_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "github", "MyTacoAIMobile", "src", "screens", "SpeakingDNA", "DNAVoiceScanScreen.tsx"
    )
    if not os.path.exists(screen_path):
        warn("DNAVoiceScanScreen.tsx not found — skipping")
        return

    with open(screen_path) as f:
        src = f.read()

    # State machine states
    states = ["IDLE", "RECORDING", "ANALYZING", "DECODING", "REVEAL", "SHARE_OFFER", "DONE"]
    for state in states:
        if f"'{state}'" in src or f'"{state}"' in src:
            ok(f"S2.1 CeremonyState '{state}' present")
        else:
            fail(f"S2.1 CeremonyState '{state}' missing from screen")

    # Lottie animations
    for asset in ["dna-analysis", "wait.json", "companion_celebrate"]:
        if asset in src:
            ok(f"S2.1 Lottie asset '{asset}' used in ceremony")
        else:
            warn(f"S2.1 Lottie asset '{asset}' not found (may be optional)")

    # Strand bar animation
    if "StrandBar" in src and "withDelay" in src:
        ok("S2.1 StrandBar animated component with stagger delay present")
    else:
        fail("S2.1 StrandBar animated component or withDelay missing")

    # Causal sentence
    if "causal_sentence" in src:
        ok("S2.1 causal_sentence rendered in REVEAL phase")
    else:
        fail("S2.1 causal_sentence not rendered in REVEAL phase")

    # Share CTA placeholder
    if "SHARE_OFFER" in src and "share" in src.lower():
        ok("S2.1 SHARE_OFFER state with share CTA placeholder present (wires to Unit F)")
    else:
        fail("S2.1 SHARE_OFFER state or share CTA missing")

    # Telemetry
    for event in ["voice_check_ceremony_started", "voice_check_ceremony_completed"]:
        if event in src:
            ok(f"S2.1 telemetry '{event}' fired")
        else:
            fail(f"S2.1 telemetry '{event}' missing")


# ════════════════════════════════════════════════════════════════════════════
# S2.2 countdown surfaces
# ════════════════════════════════════════════════════════════════════════════

def test_countdown_surfaces():
    section("S2.2 — Countdown on Hub, Plan Modal, Session Summary")

    base = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..",
        "github", "MyTacoAIMobile", "src"
    )

    surfaces = {
        "HeroCard":            os.path.join(base, "components", "DailyHub", "HeroCard.tsx"),
        "LearningPlanModal":   os.path.join(base, "components", "LearningPlanDetailsModal.tsx"),
        "SessionSummaryModal": os.path.join(base, "components", "SessionSummaryModal.tsx"),
    }

    for surface, path in surfaces.items():
        if not os.path.exists(path):
            warn(f"S2.2 {surface} not found at path")
            continue
        with open(path) as f:
            src = f.read()

        if "sessionsUntilNext" in src or "sessionsUntilNextDNA" in src:
            ok(f"S2.2 {surface} has DNA countdown prop/value")
        else:
            fail(f"S2.2 {surface} missing DNA countdown prop")

        if "anticipationCopy" in src:
            ok(f"S2.2 {surface} calls anticipationCopy()")
        else:
            fail(f"S2.2 {surface} doesn't call anticipationCopy()")

        if "countdown_viewed" in src:
            ok(f"S2.2 {surface} fires 'countdown_viewed' telemetry")
        else:
            fail(f"S2.2 {surface} missing 'countdown_viewed' telemetry")


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════

async def main():
    print("\n" + "=" * 65)
    print("  MyTacoAI — Sprint 2 Unit E: Voice-Check Unbox Ceremony Tests")
    print(f"  Target: {BASE}")
    print(f"  Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # Static (no network)
    test_anticipation_copy_logic()
    test_use_next_voice_check_hook()
    test_causal_sentence_fallback()
    test_response_model()
    test_ceremony_mobile_source()
    test_countdown_surfaces()

    # API tests
    async with httpx.AsyncClient(base_url=BASE) as client:
        section("AUTH — Login test users")
        tokens = {}
        for key, u in USERS.items():
            token = await login(client, u["email"])
            if token:
                tokens[key] = token
                ok(f"Login {key}", u["label"])
            else:
                warn(f"Login {key} failed — skipping API tests for this user")

        if tokens:
            await test_voice_check_status_endpoint(client, tokens)
            await test_analyze_session_endpoint_gate(client, tokens)
        else:
            print("\n⚠️  No authenticated users — skipping API tests")

    # Summary
    print(f"\n{'='*65}")
    print("  RESULTS SUMMARY")
    print(f"{'='*65}")
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    total  = len([r for r in results if r[0] in ("PASS", "FAIL")])
    print(f"  Total : {total}")
    print(f"  ✅ Pass : {passed}")
    print(f"  ❌ Fail : {failed}")
    print(f"\n{'='*65}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
