"""
Sprint 3 Unit H — Session Strand Delta Animation (S3.4) + Breakthrough Reveal Card (S3.5)
==========================================================================================
Tests for:
  - S3.4: per-session strand delta returned by analyze_session_for_dna and surfaced via
    the /api/speaking-dna/analyze-session endpoint.
  - S3.5: sealed "Rare moment" breakthrough_unlocked field surfaced to the mobile for
    the tap-to-reveal card in SessionSummaryModal.

All tests are static source-inspection tests (no live DB, no conftest).
Run with: pytest test_sprint3_unitH_session_delta_breakthrough.py --noconftest -v

Business rules verified:
  BR-H1  _compute_strand_deltas method exists in SpeakingDNAService
  BR-H2  strand_deltas key returned in analyze_session_for_dna result dict
  BR-H3  strand_deltas covers exactly: rhythm, confidence, vocabulary, accuracy
  BR-H4  strand_deltas dict has previous/current/delta sub-keys
  BR-H5  strand_deltas empty when previous_strands is empty (first session)
  BR-H6  AnalyzeSessionResponse model includes strand_deltas Optional field
  BR-H7  AnalyzeSessionResponse model includes breakthrough_unlocked Optional field
  BR-H8  analyze-session route populates breakthrough_unlocked from first breakthrough
  BR-H9  analyze-session route passes strand_deltas from service result
  BR-H10 Mobile: StrandDeltaBlock component hides when max|delta| < noise threshold
  BR-H11 Mobile: StrandDeltaBlock renders animated bars for each strand
  BR-H12 Mobile: BreakthroughRevealCard shows sealed state before tap
  BR-H13 Mobile: BreakthroughRevealCard exists in SessionSummaryModal
  BR-H14 Mobile: dnaStrandDeltas prop wired to SessionSummaryModal
  BR-H15 Mobile: breakthroughUnlocked prop wired to SessionSummaryModal
  BR-H16 Mobile: DNA analyzeSession result captured (not fire-and-forget) in ConversationScreen
  BR-H17 Mobile: StrandDelta type exported from speakingDNA types
  BR-H18 Mobile: breakthrough_unlocked field in AnalyzeSessionResponse type
  BR-H19 Mobile: strand_deltas field in AnalyzeSessionResponse type
  BR-H20 DNA route: only first breakthrough surfaced as breakthrough_unlocked (one per session)
"""

import os
import re
import pytest

# ── Path helpers ──────────────────────────────────────────────────────────────
BACKEND_DIR      = os.path.join(os.path.dirname(__file__), "..")
MOBILE_DIR       = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "github", "MyTacoAIMobile")
DNA_SERVICE      = os.path.join(BACKEND_DIR, "services", "speaking_dna_service.py")
DNA_ROUTES       = os.path.join(BACKEND_DIR, "routes", "speaking_dna_routes.py")
MODELS           = os.path.join(BACKEND_DIR, "models.py")
SESSION_SUMMARY  = os.path.join(MOBILE_DIR, "src", "components", "SessionSummaryModal.tsx")
CONVERSATION_SCR = os.path.join(MOBILE_DIR, "src", "screens", "Practice", "ConversationScreen.tsx")
DNA_TYPES        = os.path.join(MOBILE_DIR, "src", "types", "speakingDNA.ts")


def _read(path):
    with open(path, "r") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════════════════════
# S3.4 Backend: _compute_strand_deltas service method
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeStrandDeltasMethod:
    """BR-H1: _compute_strand_deltas method exists in SpeakingDNAService."""

    def test_method_exists(self):
        src = _read(DNA_SERVICE)
        assert "_compute_strand_deltas" in src, (
            "_compute_strand_deltas method must exist in SpeakingDNAService"
        )

    def test_method_is_instance_method(self):
        src = _read(DNA_SERVICE)
        # Method may be single-line `def _compute_strand_deltas(self,` or
        # multi-line `def _compute_strand_deltas(\n        self,`
        assert "def _compute_strand_deltas(self," in src or \
               ("def _compute_strand_deltas(" in src and "self," in src), (
            "_compute_strand_deltas must be an instance method (self first param)"
        )

    def test_returns_dict_of_dicts(self):
        """BR-H3 + BR-H4: covers four strands with previous/current/delta keys."""
        src = _read(DNA_SERVICE)
        # All four display strands must be present
        for strand in ("rhythm", "confidence", "vocabulary", "accuracy"):
            assert f'"{strand}"' in src, (
                f"_compute_strand_deltas must handle strand '{strand}'"
            )
        # Sub-keys must be computed
        for sub in ("previous", "current", "delta"):
            assert f'"{sub}"' in src, (
                f"_compute_strand_deltas must produce '{sub}' sub-key in each entry"
            )

    def test_empty_return_when_no_previous_strands(self):
        """BR-H5: returns empty dict on first session (no previous values)."""
        src = _read(DNA_SERVICE)
        # Guard clause checking for empty previous_strands
        assert "if not previous_strands or not updated_strands:" in src, (
            "_compute_strand_deltas must return {} when previous_strands is empty"
        )
        # Must return empty dict in that branch
        assert "return {}" in src


class TestStrandDeltasReturnedFromAnalyzeSession:
    """BR-H2: strand_deltas is included in the result of analyze_session_for_dna."""

    def test_strand_deltas_key_in_return_dict(self):
        src = _read(DNA_SERVICE)
        assert '"strand_deltas": strand_deltas,' in src or \
               "'strand_deltas': strand_deltas," in src, (
            "analyze_session_for_dna must include 'strand_deltas' in its return dict"
        )

    def test_compute_call_present(self):
        src = _read(DNA_SERVICE)
        assert "strand_deltas = self._compute_strand_deltas(" in src, (
            "analyze_session_for_dna must call self._compute_strand_deltas()"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# S3.4 + S3.5 Backend: AnalyzeSessionResponse model
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeSessionResponseModel:
    """BR-H6 + BR-H7: Pydantic model has new Optional fields."""

    def test_strand_deltas_field_exists(self):
        src = _read(MODELS)
        assert "strand_deltas" in src, (
            "AnalyzeSessionResponse model must include 'strand_deltas' field"
        )

    def test_strand_deltas_is_optional(self):
        src = _read(MODELS)
        assert "Optional[Dict[str, Any]]" in src, (
            "strand_deltas must be typed Optional[Dict[str, Any]]"
        )

    def test_breakthrough_unlocked_field_exists(self):
        src = _read(MODELS)
        assert "breakthrough_unlocked" in src, (
            "AnalyzeSessionResponse model must include 'breakthrough_unlocked' field"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# S3.5 Backend: analyze-session route populates breakthrough_unlocked
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeSessionRoute:
    """BR-H8 + BR-H9 + BR-H20: route populates both new fields."""

    def test_strand_deltas_passed_to_response(self):
        src = _read(DNA_ROUTES)
        assert "strand_deltas=result.get" in src or \
               'strand_deltas=result["strand_deltas"]' in src, (
            "analyze-session route must forward strand_deltas from service result"
        )

    def test_breakthrough_unlocked_in_response(self):
        src = _read(DNA_ROUTES)
        assert "breakthrough_unlocked=" in src, (
            "analyze-session route must set breakthrough_unlocked in AnalyzeSessionResponse"
        )

    def test_only_first_breakthrough_surfaced(self):
        """BR-H20: One breakthrough per session — only breakthroughs[0]."""
        src = _read(DNA_ROUTES)
        assert "_breakthroughs[0]" in src or "breakthroughs[0]" in src, (
            "route must take only the first breakthrough (index 0)"
        )

    def test_none_when_no_breakthroughs(self):
        src = _read(DNA_ROUTES)
        # The None guard: _breakthrough_unlocked = _breakthroughs[0] if _breakthroughs else None
        assert "else None" in src, (
            "route must set breakthrough_unlocked=None when no breakthroughs"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Mobile: TypeScript type definitions
# ═══════════════════════════════════════════════════════════════════════════════

class TestMobileTypes:
    """BR-H17 + BR-H18 + BR-H19: TypeScript types updated."""

    def test_strand_delta_type_exported(self):
        src = _read(DNA_TYPES)
        assert "export interface StrandDelta" in src, (
            "StrandDelta interface must be exported from speakingDNA.ts"
        )

    def test_strand_delta_has_required_fields(self):
        src = _read(DNA_TYPES)
        for field in ("previous", "current", "delta"):
            assert field in src, (
                f"StrandDelta interface must declare '{field}' field"
            )

    def test_analyze_session_response_has_strand_deltas(self):
        src = _read(DNA_TYPES)
        assert "strand_deltas?" in src, (
            "AnalyzeSessionResponse must have optional strand_deltas field"
        )

    def test_analyze_session_response_has_breakthrough_unlocked(self):
        src = _read(DNA_TYPES)
        assert "breakthrough_unlocked?" in src, (
            "AnalyzeSessionResponse must have optional breakthrough_unlocked field"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Mobile: SessionSummaryModal components
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrandDeltaBlock:
    """BR-H10 + BR-H11: StrandDeltaBlock noise gate and bar rendering."""

    def test_strand_delta_block_component_exists(self):
        src = _read(SESSION_SUMMARY)
        assert "StrandDeltaBlock" in src, (
            "StrandDeltaBlock component must be defined in SessionSummaryModal.tsx"
        )

    def test_noise_threshold_constant_exists(self):
        """BR-H10: delta block hidden when max|delta| < NOISE_THRESHOLD."""
        src = _read(SESSION_SUMMARY)
        assert "NOISE_THRESHOLD" in src, (
            "NOISE_THRESHOLD constant must be defined for noise gating"
        )

    def test_noise_gate_returns_null(self):
        src = _read(SESSION_SUMMARY)
        assert "if (maxAbsDelta < NOISE_THRESHOLD) return null;" in src, (
            "StrandDeltaBlock must return null when all deltas are below threshold"
        )

    def test_animated_strand_row_component_exists(self):
        """BR-H11: Animated bar rows rendered per strand."""
        src = _read(SESSION_SUMMARY)
        assert "AnimatedStrandRow" in src, (
            "AnimatedStrandRow sub-component must exist for per-strand animation"
        )

    def test_four_display_strands_covered(self):
        src = _read(SESSION_SUMMARY)
        for strand in ("rhythm", "confidence", "vocabulary", "accuracy"):
            assert strand in src, (
                f"STRAND_META must include '{strand}' for StrandDeltaBlock"
            )

    def test_uses_reanimated_for_animation(self):
        src = _read(SESSION_SUMMARY)
        assert "useSharedValue" in src, (
            "StrandDeltaBlock must use Reanimated useSharedValue for animation"
        )
        assert "useAnimatedStyle" in src, (
            "StrandDeltaBlock must use Reanimated useAnimatedStyle"
        )

    def test_stagger_delay_applied(self):
        """BR-H11: 200ms stagger between bars."""
        src = _read(SESSION_SUMMARY)
        assert "delay" in src and "200" in src, (
            "StrandDeltaBlock must apply stagger delay (200ms) between bar animations"
        )


class TestBreakthroughRevealCard:
    """BR-H12 + BR-H13: BreakthroughRevealCard sealed state and placement."""

    def test_card_component_exists(self):
        src = _read(SESSION_SUMMARY)
        assert "BreakthroughRevealCard" in src, (
            "BreakthroughRevealCard component must be defined in SessionSummaryModal.tsx"
        )

    def test_sealed_state_shown_before_tap(self):
        """BR-H12: sealed state (lock + tap CTA) before reveal."""
        src = _read(SESSION_SUMMARY)
        assert "Tap to open" in src or "tap to open" in src.lower(), (
            "BreakthroughRevealCard must show 'Tap to open' CTA in sealed state"
        )

    def test_rare_moment_label_present(self):
        src = _read(SESSION_SUMMARY)
        assert "RARE MOMENT" in src, (
            "BreakthroughRevealCard must display 'RARE MOMENT' label"
        )

    def test_revealed_state_shows_title_and_description(self):
        src = _read(SESSION_SUMMARY)
        assert "btTitle" in src and "btDescription" in src, (
            "BreakthroughRevealCard must render btTitle and btDescription on reveal"
        )

    def test_uses_linear_gradient(self):
        src = _read(SESSION_SUMMARY)
        assert "LinearGradient" in src, (
            "BreakthroughRevealCard must use LinearGradient for the sealed card background"
        )

    def test_breakthrough_card_at_top_of_success_screen(self):
        """BR-H13: breakthrough reveal card appears before context card (at top)."""
        src = _read(SESSION_SUMMARY)
        breakthrough_pos = src.find("BreakthroughRevealCard breakthrough=")
        context_card_pos = src.find("Session-type context card")
        assert breakthrough_pos != -1, "BreakthroughRevealCard must be rendered"
        assert context_card_pos != -1, "Context card comment must exist"
        assert breakthrough_pos < context_card_pos, (
            "BreakthroughRevealCard must appear BEFORE the context card (at screen top)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Mobile: SessionSummaryModal props
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionSummaryModalProps:
    """BR-H14 + BR-H15: new props declared in interface and destructured."""

    def test_dna_strand_deltas_prop_declared(self):
        src = _read(SESSION_SUMMARY)
        assert "dnaStrandDeltas?" in src, (
            "SessionSummaryModalProps must declare optional 'dnaStrandDeltas' prop"
        )

    def test_breakthrough_unlocked_prop_declared(self):
        src = _read(SESSION_SUMMARY)
        assert "breakthroughUnlocked?" in src, (
            "SessionSummaryModalProps must declare optional 'breakthroughUnlocked' prop"
        )

    def test_dna_strand_deltas_destructured(self):
        src = _read(SESSION_SUMMARY)
        assert "dnaStrandDeltas," in src or "dnaStrandDeltas}" in src, (
            "dnaStrandDeltas must be destructured in SessionSummaryModal component"
        )

    def test_breakthrough_unlocked_destructured(self):
        src = _read(SESSION_SUMMARY)
        assert "breakthroughUnlocked," in src or "breakthroughUnlocked}" in src, (
            "breakthroughUnlocked must be destructured in SessionSummaryModal component"
        )

    def test_strand_delta_block_conditionally_rendered(self):
        src = _read(SESSION_SUMMARY)
        assert "dnaStrandDeltas" in src and "StrandDeltaBlock strandDeltas=" in src, (
            "StrandDeltaBlock must be conditionally rendered using dnaStrandDeltas prop"
        )

    def test_breakthrough_reveal_card_conditionally_rendered(self):
        src = _read(SESSION_SUMMARY)
        assert "breakthroughUnlocked" in src and \
               "BreakthroughRevealCard breakthrough=" in src, (
            "BreakthroughRevealCard must be conditionally rendered using breakthroughUnlocked"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Mobile: ConversationScreen wiring
# ═══════════════════════════════════════════════════════════════════════════════

class TestConversationScreenWiring:
    """BR-H16: analyzeSession result captured for strand deltas + breakthrough."""

    def test_dna_strand_deltas_state_declared(self):
        src = _read(CONVERSATION_SCR)
        assert "dnaStrandDeltas" in src, (
            "ConversationScreen must declare dnaStrandDeltas state"
        )

    def test_dna_breakthrough_unlocked_state_declared(self):
        src = _read(CONVERSATION_SCR)
        assert "dnaBreakthroughUnlocked" in src, (
            "ConversationScreen must declare dnaBreakthroughUnlocked state"
        )

    def test_analyze_session_result_captured_with_then(self):
        """BR-H16: result is captured via .then() not discarded."""
        src = _read(CONVERSATION_SCR)
        # The .then() handler must reference strand_deltas
        assert ".then((dnaResult)" in src or ".then(dnaResult =>" in src or \
               ".then((dnaResult) =>" in src, (
            "analyzeSession must use .then() to capture the result"
        )
        assert "strand_deltas" in src, (
            "ConversationScreen must read strand_deltas from dnaResult"
        )

    def test_strand_delta_type_imported(self):
        src = _read(CONVERSATION_SCR)
        assert "StrandDelta" in src, (
            "ConversationScreen must import StrandDelta type from speakingDNA"
        )

    def test_dna_strand_deltas_prop_passed_to_modal(self):
        src = _read(CONVERSATION_SCR)
        assert "dnaStrandDeltas={dnaStrandDeltas}" in src, (
            "ConversationScreen must pass dnaStrandDeltas prop to SessionSummaryModal"
        )

    def test_breakthrough_unlocked_prop_passed_to_modal(self):
        src = _read(CONVERSATION_SCR)
        assert "breakthroughUnlocked={dnaBreakthroughUnlocked}" in src, (
            "ConversationScreen must pass breakthroughUnlocked prop to SessionSummaryModal"
        )
