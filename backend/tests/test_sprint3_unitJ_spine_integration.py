"""
S3.7 Spine Integration — static source-inspection tests.

Run with:
    pytest tests/test_sprint3_unitJ_spine_integration.py -v --noconftest
"""

import ast
import pathlib
import re

BACKEND = pathlib.Path(__file__).parents[1]
MOBILE  = pathlib.Path.home() / "github" / "MyTacoAIMobile"


# ── Helpers ────────────────────────────────────────────────────────────────────

def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# strands.tsx — constants module
# ─────────────────────────────────────────────────────────────────────────────

STRANDS_TS = MOBILE / "src" / "constants" / "strands.tsx"


def test_strands_file_exists():
    assert STRANDS_TS.exists(), "src/constants/strands.tsx must exist"


def test_strands_exports_strand_key_type():
    src = read(STRANDS_TS)
    assert "export type StrandKey" in src


def test_strands_exports_strand_meta():
    src = read(STRANDS_TS)
    assert "export const STRAND_META" in src


def test_strands_exports_all_strand_keys():
    src = read(STRANDS_TS)
    assert "export const ALL_STRAND_KEYS" in src


def test_strands_exports_get_strand_score():
    src = read(STRANDS_TS)
    assert "export function getStrandScore" in src


def test_strands_exports_weakest_strand():
    src = read(STRANDS_TS)
    assert "export function weakestStrand" in src


def test_strands_exports_strand_pip():
    src = read(STRANDS_TS)
    assert "export const StrandPip" in src


def test_strands_has_six_strand_keys():
    src = read(STRANDS_TS)
    for key in ("rhythm", "confidence", "vocabulary", "accuracy", "learning", "emotional"):
        assert f"'{key}'" in src or f'"{key}"' in src


# ─────────────────────────────────────────────────────────────────────────────
# hub_routes.py — weakest_strand field
# ─────────────────────────────────────────────────────────────────────────────

HUB_ROUTES = BACKEND / "routes" / "hub_routes.py"


def test_hub_routes_weakest_strand_in_response_model():
    src = read(HUB_ROUTES)
    assert "weakest_strand" in src


def test_hub_routes_weakest_strand_key_helper():
    src = read(HUB_ROUTES)
    assert "_weakest_strand_key" in src


def test_hub_routes_weakest_strand_score_fields():
    src = read(HUB_ROUTES)
    assert "consistency_score" in src
    assert "grammar_accuracy" in src


def test_hub_routes_weakest_strand_passed_to_response():
    src = read(HUB_ROUTES)
    assert "weakest_strand=_weakest_strand_key" in src


# ─────────────────────────────────────────────────────────────────────────────
# DailyQuestsSection.tsx — strand pip on silver card
# ─────────────────────────────────────────────────────────────────────────────

DAILY_QUESTS = MOBILE / "src" / "components" / "DailyHub" / "DailyQuestsSection.tsx"


def test_daily_quests_imports_strand_pip():
    src = read(DAILY_QUESTS)
    assert "StrandPip" in src


def test_daily_quests_imports_strand_meta():
    src = read(DAILY_QUESTS)
    assert "STRAND_META" in src


def test_daily_quests_weakest_strand_in_section_props():
    src = read(DAILY_QUESTS)
    assert "weakestStrand" in src
    assert "DailyQuestsSectionProps" in src


def test_daily_quests_weakest_strand_in_mission_card_props():
    src = read(DAILY_QUESTS)
    assert "MissionCardProps" in src
    # weakestStrand should appear in MissionCardProps interface
    lines = src.splitlines()
    in_mission_card_props = False
    found = False
    for line in lines:
        if "interface MissionCardProps" in line:
            in_mission_card_props = True
        if in_mission_card_props and "weakestStrand" in line:
            found = True
            break
        if in_mission_card_props and line.strip() == "}":
            break
    assert found, "weakestStrand not found in MissionCardProps interface"


def test_daily_quests_strand_pip_rendered_in_silver_section():
    src = read(DAILY_QUESTS)
    assert "<StrandPip" in src


def test_daily_quests_weakest_strand_threaded_to_mission_card():
    src = read(DAILY_QUESTS)
    # MissionCard render call should pass weakestStrand
    assert "weakestStrand={quest.tier === 'silver'" in src or "weakestStrand=" in src


# ─────────────────────────────────────────────────────────────────────────────
# DailyHubScreen.tsx — weakest_strand state + hero copy
# ─────────────────────────────────────────────────────────────────────────────

DAILY_HUB = MOBILE / "src" / "screens" / "Dashboard" / "DailyHubScreen.tsx"


def test_daily_hub_weakest_strand_state():
    src = read(DAILY_HUB)
    assert "weakestStrand" in src
    assert "setWeakestStrand" in src


def test_daily_hub_weakest_strand_from_hub_data():
    src = read(DAILY_HUB)
    assert "data.weakest_strand" in src


def test_daily_hub_weakest_strand_saved_to_async_storage():
    src = read(DAILY_HUB)
    assert "weakest_strand" in src
    assert "AsyncStorage.setItem" in src


def test_daily_hub_weakest_strand_passed_to_quests_section():
    src = read(DAILY_HUB)
    assert "weakestStrand={weakestStrand" in src


def test_daily_hub_weakest_strand_passed_to_hero_card():
    src = read(DAILY_HUB)
    assert "weakestStrand={weakestStrand}" in src


# ─────────────────────────────────────────────────────────────────────────────
# HeroCard.tsx — strand-anchored subtitle copy
# ─────────────────────────────────────────────────────────────────────────────

HERO_CARD = MOBILE / "src" / "components" / "DailyHub" / "HeroCard.tsx"


def test_hero_card_weakest_strand_prop():
    src = read(HERO_CARD)
    assert "weakestStrand" in src


def test_hero_card_strand_hero_copy_map():
    src = read(HERO_CARD)
    assert "STRAND_HERO_COPY" in src


def test_hero_card_strand_hero_copy_has_six_strands():
    src = read(HERO_CARD)
    for key in ("rhythm", "confidence", "vocabulary", "accuracy", "learning", "emotional"):
        assert f"'{key}'" in src or f'"{key}"' in src


def test_hero_card_subtitle_uses_strand_copy():
    src = read(HERO_CARD)
    assert "STRAND_HERO_COPY[props.weakestStrand]" in src or "STRAND_HERO_COPY[" in src


# ─────────────────────────────────────────────────────────────────────────────
# ConversationScreen.tsx — strand pip in top bar
# ─────────────────────────────────────────────────────────────────────────────

CONVO_SCREEN = MOBILE / "src" / "screens" / "Practice" / "ConversationScreen.tsx"


def test_conversation_imports_strand_pip():
    src = read(CONVO_SCREEN)
    assert "StrandPip" in src


def test_conversation_imports_strand_meta():
    src = read(CONVO_SCREEN)
    assert "STRAND_META" in src


def test_conversation_session_weakest_strand_state():
    src = read(CONVO_SCREEN)
    assert "sessionWeakestStrand" in src
    assert "setSessionWeakestStrand" in src


def test_conversation_loads_weakest_strand_from_async_storage():
    src = read(CONVO_SCREEN)
    assert "weakest_strand" in src
    assert "AsyncStorage.getItem" in src


def test_conversation_renders_strand_pip():
    src = read(CONVO_SCREEN)
    assert "<StrandPip" in src


def test_conversation_strand_pip_shows_focus_label():
    src = read(CONVO_SCREEN)
    assert "Focus" in src


# ─────────────────────────────────────────────────────────────────────────────
# LearningPlanDetailsModal.tsx — strand-framed voice check copy
# ─────────────────────────────────────────────────────────────────────────────

PLAN_MODAL = MOBILE / "src" / "components" / "LearningPlanDetailsModal.tsx"


def test_plan_modal_imports_strand_pip():
    src = read(PLAN_MODAL)
    assert "StrandPip" in src


def test_plan_modal_imports_weakest_strand_fn():
    src = read(PLAN_MODAL)
    assert "computeWeakestStrand" in src or "weakestStrand as computeWeakestStrand" in src


def test_plan_modal_uses_weakest_strand_in_countdown():
    src = read(PLAN_MODAL)
    assert "computeWeakestStrand" in src


def test_plan_modal_strand_pip_in_countdown_block():
    src = read(PLAN_MODAL)
    # The countdown block should now render a StrandPip
    assert "<StrandPip" in src
    assert "your focus this reading" in src


# ─────────────────────────────────────────────────────────────────────────────
# daily_digest_generator.py — strand-anchored copy
# ─────────────────────────────────────────────────────────────────────────────

DIGEST_GEN = BACKEND / "services" / "daily_digest_generator.py"


def test_digest_gen_strand_templates_exist():
    src = read(DIGEST_GEN)
    for key in ("strand_rhythm", "strand_confidence", "strand_vocabulary",
                "strand_accuracy", "strand_learning", "strand_emotional"):
        assert f'"{key}"' in src or f"'{key}'" in src, f"Missing template key: {key}"


def test_digest_gen_create_strand_message_method():
    src = read(DIGEST_GEN)
    assert "_create_strand_message" in src


def test_digest_gen_weakest_strand_in_context():
    src = read(DIGEST_GEN)
    assert "weakest_strand" in src


def test_digest_gen_weakest_strand_dna_lookup():
    src = read(DIGEST_GEN)
    assert "speaking_dna" in src
    assert "dna_strands" in src


def test_digest_gen_strand_message_in_select_message():
    src = read(DIGEST_GEN)
    assert "_create_strand_message" in src
    # Must be called in _select_message
    lines = src.splitlines()
    in_select = False
    found = False
    for line in lines:
        if "def _select_message" in line:
            in_select = True
        if in_select and "_create_strand_message" in line:
            found = True
            break
    assert found, "_create_strand_message not called from _select_message"
