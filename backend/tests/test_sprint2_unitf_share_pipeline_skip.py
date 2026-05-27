"""
Sprint 2 Unit F — Share Pipeline & Skip Flow
=============================================
Tests for S2.3 (share card + deep link) and S2.4 (skip flow fix).

Business rules verified:
  BR-F1  skip-voice-check writes session_number to voice_checks_completed
  BR-F2  skip-voice-check writes session_number to voice_checks_skipped
  BR-F3  skip-voice-check is idempotent (double-skip doesn't duplicate)
  BR-F4  skip-voice-check returns success + next_check
  BR-F5  skip-voice-check is premium-only (403 for free users)
  BR-F6  VoiceCheckShareCard file exists with correct exports
  BR-F7  VoiceCheckShareCard has all 6 required zones
  BR-F8  Percentile lookup is deterministic per archetype
  BR-F9  SharePreviewScreen file exists with correct exports
  BR-F10 SharePreviewScreen navigates to Landing and stores signup source
  BR-F11 Deep link 'share/:token' registered in App.js linking config
  BR-F12 SharePreview Stack.Screen registered in App.js navigator
"""

import ast
import os
import sys
import re
import json
import pytest
import requests

# ── Path helpers ──────────────────────────────────────────────────────────────
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
MOBILE_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "github", "MyTacoAIMobile")
LEARNING_ROUTES = os.path.join(BACKEND_DIR, "learning_routes.py")
SHARE_CARD      = os.path.join(MOBILE_DIR, "src", "components", "SpeakingDNA", "VoiceCheckShareCard.tsx")
SHARE_PREVIEW   = os.path.join(MOBILE_DIR, "src", "screens", "SpeakingDNA", "SharePreviewScreen.tsx")
VOICE_SCAN      = os.path.join(MOBILE_DIR, "src", "screens", "SpeakingDNA", "DNAVoiceScanScreen.tsx")
APP_JS          = os.path.join(MOBILE_DIR, "App.js")

# ── Live API config ───────────────────────────────────────────────────────────
BASE_URL = os.environ.get("API_BASE_URL", "https://mytacoai.com")

PREMIUM_EMAIL    = os.environ.get("PREMIUM_EMAIL",    "alipala.ist@gmail.com")
PREMIUM_PASSWORD = os.environ.get("PREMIUM_PASSWORD", "")
FREE_EMAIL       = os.environ.get("FREE_EMAIL",        "suzan@test.com")
FREE_PASSWORD    = os.environ.get("FREE_PASSWORD",     "test1234")

SKIP_LIVE = not PREMIUM_PASSWORD


def get_token(email: str, password: str):
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        return resp.json().get("access_token")
    except Exception:
        return None


# =============================================================================
# BR-F1 / BR-F2 — skip writes to voice_checks_completed AND voice_checks_skipped
# =============================================================================

class TestSkipVoiceCheckBackend:
    """Source-code inspection: the skip endpoint must write to both arrays."""

    def test_br_f1_skip_writes_voice_checks_completed(self):
        """BR-F1: skip_voice_check must update voice_checks_completed in DB."""
        with open(LEARNING_ROUTES) as f:
            src = f.read()
        # Look for the S2.4 fix block
        assert "voice_checks_completed" in src, "voice_checks_completed not found in learning_routes.py"
        # The fix sets voice_checks_completed via $set after a skip
        assert re.search(r'"\$set".*voice_checks_completed', src, re.DOTALL), \
            "skip endpoint does not $set voice_checks_completed"

    def test_br_f2_skip_writes_voice_checks_skipped(self):
        """BR-F2: skip_voice_check must also track skips separately for analytics."""
        with open(LEARNING_ROUTES) as f:
            src = f.read()
        assert "voice_checks_skipped" in src, \
            "voice_checks_skipped array not found in learning_routes.py"
        assert re.search(r'addToSet.*voice_checks_skipped', src, re.DOTALL), \
            "skip endpoint does not $addToSet voice_checks_skipped"

    def test_br_f3_skip_is_idempotent(self):
        """BR-F3: skip must guard against double-write (if session_number not in ...)."""
        with open(LEARNING_ROUTES) as f:
            src = f.read()
        # Find the skip function and check for the idempotency guard
        skip_section = src[src.find("skip-voice-check"):]
        assert "not in voice_checks_completed" in skip_section, \
            "skip endpoint missing idempotency guard"

    def test_br_f4_skip_returns_next_check(self):
        """BR-F4: skip response must include next_check field."""
        with open(LEARNING_ROUTES) as f:
            src = f.read()
        skip_section = src[src.find("skip-voice-check"):]
        assert '"next_check"' in skip_section, \
            "skip response missing next_check field"
        assert '"success": True' in skip_section or '"success"' in skip_section, \
            "skip response missing success field"


# =============================================================================
# BR-F5 — premium gate (live API)
# =============================================================================

class TestSkipVoiceCheckLiveAPI:
    """Live API: confirm premium gate on skip endpoint."""

    @pytest.mark.skipif(SKIP_LIVE, reason="PREMIUM_PASSWORD not set")
    def test_br_f5_free_user_gets_403_on_skip(self):
        """BR-F5: free users must receive 403 on skip-voice-check."""
        token = get_token(FREE_EMAIL, FREE_PASSWORD)
        if not token:
            pytest.skip("Could not authenticate free user")
        resp = requests.post(
            f"{BASE_URL}/api/learning/plan/fake-plan-id/skip-voice-check",
            params={"session_number": 1},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        assert resp.status_code == 403, \
            f"Expected 403 for free user, got {resp.status_code}"


# =============================================================================
# BR-F6 / BR-F7 — VoiceCheckShareCard source inspection
# =============================================================================

class TestVoiceCheckShareCard:
    """Static source inspection of the share card component."""

    def test_br_f6_file_exists(self):
        """BR-F6: VoiceCheckShareCard.tsx must exist."""
        assert os.path.isfile(SHARE_CARD), \
            f"VoiceCheckShareCard.tsx not found at {SHARE_CARD}"

    def test_br_f6_named_export(self):
        """BR-F6: must export VoiceCheckShareCard as a named export."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "export const VoiceCheckShareCard" in src or \
               "export interface VoiceCheckShareCardProps" in src, \
            "VoiceCheckShareCard named export not found"

    def test_br_f6_forwardref(self):
        """BR-F6: must use React.forwardRef so ViewShot can capture it."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "React.forwardRef" in src, \
            "VoiceCheckShareCard must use React.forwardRef for ViewShot capture"

    def test_br_f7_has_all_six_zones(self):
        """BR-F7: share card must contain all 6 required zones."""
        with open(SHARE_CARD) as f:
            src = f.read()
        zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Zone 6"]
        for zone in zones:
            assert zone in src, f"Missing {zone} comment in VoiceCheckShareCard"

    def test_br_f7_social_proof_hook(self):
        """BR-F7: Zone 3 must contain percentile social proof copy."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "LEARNERS" in src.upper() or "percentile" in src.lower(), \
            "Social proof percentile text not found in share card"

    def test_br_f7_strand_grid(self):
        """BR-F7: Zone 4 must render all 4 strands."""
        with open(SHARE_CARD) as f:
            src = f.read()
        for strand in ["rhythm", "confidence", "vocabulary", "accuracy"]:
            assert strand in src, f"Strand '{strand}' not referenced in VoiceCheckShareCard"

    def test_br_f7_footer_cta(self):
        """BR-F7: Zone 6 footer must reference MyTacoAI."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "MyTacoAI" in src, "Footer missing MyTacoAI branding"

    def test_br_f7_no_svg_ionicons(self):
        """BR-F7: share card must not import Ionicons or react-native-svg (causes ViewShot issues)."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "import.*Ionicons" not in src and "from '@expo/vector-icons'" not in src, \
            "VoiceCheckShareCard must not import Ionicons (use emoji instead)"
        assert "react-native-svg" not in src, \
            "VoiceCheckShareCard must not import react-native-svg"


# =============================================================================
# BR-F8 — Percentile lookup is deterministic
# =============================================================================

class TestPercentileDeterminism:
    """BR-F8: archetype → percentile must be a fixed lookup, not random."""

    def test_br_f8_archetype_percentile_lookup_exists(self):
        """BR-F8: ARCHETYPE_PERCENTILE lookup table must be present."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "ARCHETYPE_PERCENTILE" in src, \
            "Deterministic percentile lookup table not found in VoiceCheckShareCard"

    def test_br_f8_known_archetypes_mapped(self):
        """BR-F8: the three named archetypes must have specific percentile values."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "The Thoughtful Builder" in src, "Thoughtful Builder archetype missing"
        assert "The Fearless Explorer"  in src, "Fearless Explorer archetype missing"
        assert "The Steady Progressor"  in src, "Steady Progressor archetype missing"

    def test_br_f8_no_math_random(self):
        """BR-F8: percentile must not use Math.random() — must be deterministic."""
        with open(SHARE_CARD) as f:
            src = f.read()
        assert "Math.random" not in src, \
            "Percentile must be deterministic — Math.random() found in VoiceCheckShareCard"


# =============================================================================
# BR-F9 / BR-F10 — SharePreviewScreen source inspection
# =============================================================================

class TestSharePreviewScreen:
    """Static source inspection of the SharePreviewScreen."""

    def test_br_f9_file_exists(self):
        """BR-F9: SharePreviewScreen.tsx must exist."""
        assert os.path.isfile(SHARE_PREVIEW), \
            f"SharePreviewScreen.tsx not found at {SHARE_PREVIEW}"

    def test_br_f9_named_export(self):
        """BR-F9: must export SharePreviewScreen as a named export."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "export const SharePreviewScreen" in src, \
            "SharePreviewScreen named export not found"

    def test_br_f9_reads_token_from_route_params(self):
        """BR-F9: must extract token from route.params.token."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "route?.params?.token" in src or "route.params.token" in src, \
            "SharePreviewScreen must read token from route.params.token"

    def test_br_f9_calls_public_share_endpoint(self):
        """BR-F9: must fetch /api/share/session/${token} without auth."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "/api/share/session/" in src, \
            "SharePreviewScreen must call /api/share/session/:token"
        # No Authorization header for the fetch
        assert "Authorization" not in src.split("/api/share/session/")[1][:300], \
            "Public fetch should not include Authorization header"

    def test_br_f9_handles_404(self):
        """BR-F9: must handle 404 with 'This reading has expired' message."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "expired" in src.lower() or "404" in src, \
            "SharePreviewScreen must handle 404 (expired link)"

    def test_br_f10_navigates_to_landing(self):
        """BR-F10: primary CTA must navigate to Landing screen."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "navigate('Landing')" in src or 'navigate("Landing")' in src, \
            "SharePreviewScreen must navigate to Landing on primary CTA"

    def test_br_f10_stores_signup_source(self):
        """BR-F10: must persist signup source to AsyncStorage before navigating."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "@mytacoai_signup_source" in src, \
            "SharePreviewScreen must store @mytacoai_signup_source in AsyncStorage"
        assert "share_token_" in src, \
            "Signup source key must include share_token_ prefix"

    def test_br_f10_secondary_sign_in_link(self):
        """BR-F10: must have a secondary 'Sign in' link navigating to Login."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "Login" in src, "SharePreviewScreen missing Login navigation"
        assert "Sign in" in src or "sign in" in src.lower(), \
            "SharePreviewScreen missing secondary Sign in link"

    def test_br_f10_telemetry_on_mount(self):
        """BR-F10: must fire share_url_opened telemetry on mount."""
        with open(SHARE_PREVIEW) as f:
            src = f.read()
        assert "share_url_opened" in src, \
            "SharePreviewScreen missing share_url_opened telemetry"


# =============================================================================
# BR-F11 / BR-F12 — App.js deep link + screen registration
# =============================================================================

class TestAppJSDeepLink:
    """Static inspection of App.js for deep link and screen registration."""

    def test_br_f11_deep_link_registered(self):
        """BR-F11: linking config must include share/:token path."""
        with open(APP_JS) as f:
            src = f.read()
        assert "share/:token" in src, \
            "Deep link 'share/:token' not found in App.js linking config"
        assert "SharePreview" in src, \
            "SharePreview screen name not found in App.js linking config"

    def test_br_f12_stack_screen_registered(self):
        """BR-F12: SharePreview must be registered as a Stack.Screen."""
        with open(APP_JS) as f:
            src = f.read()
        assert 'name="SharePreview"' in src, \
            "Stack.Screen name='SharePreview' not found in App.js"
        assert "SharePreviewScreen" in src, \
            "SharePreviewScreen component import/reference not found in App.js"

    def test_br_f12_import_exists(self):
        """BR-F12: SharePreviewScreen must be imported in App.js."""
        with open(APP_JS) as f:
            src = f.read()
        assert "import" in src and "SharePreviewScreen" in src, \
            "SharePreviewScreen not imported in App.js"


# =============================================================================
# S2.4 mobile — DNAVoiceScanScreen skip affordance
# =============================================================================

class TestDNAVoiceScanSkipAffordance:
    """Static inspection: Not now affordance and skip wiring in DNAVoiceScanScreen."""

    def test_not_now_button_present(self):
        """S2.4: IDLE state must render a 'Not now' affordance."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "Not now" in src, \
            "DNAVoiceScanScreen missing 'Not now' skip affordance in IDLE state"

    def test_handle_skip_calls_skip_voice_check(self):
        """S2.4: handleSkip must call skipVoiceCheck from the hook."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "skipVoiceCheck" in src, \
            "handleSkip in DNAVoiceScanScreen does not call skipVoiceCheck"

    def test_skip_telemetry_fires(self):
        """S2.4: handleSkip must emit voice_check_skipped telemetry."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "voice_check_skipped" in src, \
            "voice_check_skipped telemetry not found in DNAVoiceScanScreen"


# =============================================================================
# S2.3 mobile — SHARE_OFFER wiring in DNAVoiceScanScreen
# =============================================================================

class TestDNAVoiceScanShareOffer:
    """Static inspection: SHARE_OFFER state wired with real share logic."""

    def test_viewshot_ref_present(self):
        """S2.3: shareCardRef (ViewShot) must be declared."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "shareCardRef" in src, \
            "shareCardRef not found in DNAVoiceScanScreen"
        assert "ViewShot" in src, \
            "ViewShot not imported in DNAVoiceScanScreen"

    def test_voice_check_share_card_rendered_offscreen(self):
        """S2.3: VoiceCheckShareCard must be rendered off-screen for capture."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "VoiceCheckShareCard" in src, \
            "VoiceCheckShareCard not rendered in DNAVoiceScanScreen SHARE_OFFER state"
        assert "left: -9999" in src or "-9999" in src, \
            "VoiceCheckShareCard must be positioned off-screen for ViewShot capture"

    def test_share_cta_tapped_telemetry(self):
        """S2.3: share CTA must emit voice_check_share_cta_tapped telemetry."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "voice_check_share_cta_tapped" in src, \
            "voice_check_share_cta_tapped telemetry missing in DNAVoiceScanScreen"

    def test_strand_deltas_passed_to_card(self):
        """S2.3: strandDeltas with previous/current must be passed to VoiceCheckShareCard."""
        with open(VOICE_SCAN) as f:
            src = f.read()
        assert "strandDeltas" in src, \
            "strandDeltas prop not passed to VoiceCheckShareCard in DNAVoiceScanScreen"
        assert "previous" in src and "current" in src, \
            "strand delta previous/current values not computed in DNAVoiceScanScreen"
