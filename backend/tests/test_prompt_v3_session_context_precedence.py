"""
Regression tests: the learner's chosen subject must win over their learning plan.

Background
----------
/api/realtime/token loads the user's active learning plan on EVERY session as
background context. PROMPT_V3 then selected its mode with a plain
`if learning_plan_data: ... elif news_raw: ... elif topic: ...` chain, so for any
user with an in_progress plan in that language the plan branch always won and the
news/topic/custom branches were unreachable. A news session was rebuilt as a plan
session: the article never reached the model, and the prompt carried the plan's
weekly focus, vocabulary and the corrections carried over from earlier PLAN
sessions ("watch for 'X' -> 'Y'").

These tests pin both halves of the fix:
  1. explicit session context (news / user_prompt / topic) beats learning_plan_data
  2. the LEARNING PLAN CONTRACT paragraph only appears in real plan sessions

and — just as important — that genuine plan sessions are left untouched.
"""

import json

import pytest

from prompt_v3 import build_instructions_v3
from tutor_config import has_explicit_session_context


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────────────────────

# Exactly the shape fetch_active_learning_plan() returns in realtime_routes.py.
PLAN = {
    "plan_content": {
        "weekly_schedule": [
            {
                "focus": "Family and home life",
                "activities": ["Describe your family members"],
                "key_vocabulary": ["moeder", "vader", "zus", "broer"],
                "key_phrases": ["Ik heb twee zussen"],
            }
        ]
    },
    "completed_sessions": 2,
    "total_sessions": 8,
    "goals": ["daily_life"],
    "sub_goals": ["family"],
    "session_history": [
        {
            "structured_summary": {
                "vocabulary_practiced": ["moeder", "vader"],
                "focus_next_session": "possessive pronouns",
                "corrections_made": [
                    {"wrong": "mijn moeder is 50 jaren", "correct": "mijn moeder is 50 jaar"}
                ],
            }
        }
    ],
    "session_summaries": [],
}

NEWS_RAW = json.dumps(
    {
        "news_title": "Dutch trains face delays",
        "news_summary": "NS announced widespread delays after signal failures.",
        "vocabulary": [{"word": "vertraging"}, {"word": "spoor"}],
        "discussion_questions": ["Reis jij vaak met de trein?"],
    }
)

# Strings that only ever appear when plan content was injected.
PLAN_MARKERS = [
    "Family and home life",
    "Describe your family members",
    "moeder",
    "Plan goal(s)",
    "Plan sub-goal(s)",
    "TODAY'S GOAL (session",
    "Last session:",
    "mijn moeder is 50 jaren",  # the leaked cross-session "memory"
]


class Req:
    """Stand-in for TutorSessionRequest with mobile-app defaults."""

    def __init__(self, **kwargs):
        self.session_mode = "conversation"
        self.selected_duration = 5
        self.disable_corrections = False
        self.research_data = None
        self.topic = None
        self.user_prompt = None
        self.news_context = None
        self.learning_plan_data = None
        for key, value in kwargs.items():
            setattr(self, key, value)


def build(**kwargs):
    language = kwargs.pop("language", "dutch")
    level = kwargs.pop("level", "B1")
    return build_instructions_v3(Req(**kwargs), language, level)


def assert_no_plan_content(instructions):
    assert instructions is not None
    leaked = [m for m in PLAN_MARKERS if m in instructions]
    assert not leaked, f"learning plan content leaked into a non-plan session: {leaked}"


# ─────────────────────────────────────────────────────────────────────────────
# 1. The bug: explicit session context must beat an active learning plan
# ─────────────────────────────────────────────────────────────────────────────


class TestExplicitContextBeatsPlan:
    def test_news_session_keeps_the_article(self):
        out = build(news_context=NEWS_RAW, learning_plan_data=PLAN)
        assert "Dutch trains face delays" in out
        assert "vertraging" in out
        assert "Reis jij vaak met de trein?" in out
        assert_no_plan_content(out)

    def test_custom_topic_session_keeps_the_topic(self):
        out = build(topic="custom", user_prompt="Formula 1 racing", learning_plan_data=PLAN)
        assert "Formula 1 racing" in out
        assert_no_plan_content(out)

    def test_predefined_topic_session_keeps_the_topic(self):
        out = build(topic="travel", learning_plan_data=PLAN)
        assert "Topic:" in out
        assert_no_plan_content(out)

    def test_dna_strand_session_keeps_the_strand(self):
        """SpeakingDNAScreenHorizontal navigates with topic=<strand>, level='intermediate'."""
        out = build(topic="grammar_accuracy", level="intermediate", learning_plan_data=PLAN)
        assert_no_plan_content(out)
        assert "INTERMEDIATE" not in out  # named level is mapped to CEFR

    def test_research_backed_custom_topic_keeps_its_research(self):
        out = build(
            topic="custom",
            user_prompt="Formula 1 racing",
            research_data="The 2026 season introduces active aerodynamics.",
            learning_plan_data=PLAN,
        )
        assert "active aerodynamics" in out
        assert_no_plan_content(out)

    def test_cross_session_corrections_do_not_leak(self):
        """The most user-visible symptom: tutor quoting a fix from a PLAN session."""
        out = build(news_context=NEWS_RAW, learning_plan_data=PLAN)
        assert "mijn moeder is 50 jaren" not in out
        assert "possessive pronouns" not in out
        assert "Last session:" not in out


# ─────────────────────────────────────────────────────────────────────────────
# 2. Genuine plan sessions must be completely unaffected
# ─────────────────────────────────────────────────────────────────────────────


class TestPlanSessionsUnchanged:
    def test_plan_session_still_gets_plan_context(self):
        out = build(learning_plan_data=PLAN)
        assert "Week 1 focus: Family and home life" in out
        assert "TODAY'S GOAL (session 3 of this week): Describe your family members" in out
        assert "moeder" in out
        assert "Plan goal(s): daily life" in out
        assert "Plan sub-goal(s): family" in out

    def test_plan_session_still_gets_continuity_memory(self):
        """Carry-over from the previous session is wanted HERE — just not elsewhere."""
        out = build(learning_plan_data=PLAN)
        assert "carry-over focus: possessive pronouns" in out
        assert "watch for 'mijn moeder is 50 jaren' -> 'mijn moeder is 50 jaar'" in out

    def test_opener_still_rotates_with_completed_sessions(self):
        openers = set()
        for completed in range(4):
            plan = {**PLAN, "completed_sessions": completed}
            openers.add(build(learning_plan_data=plan).split("1. OPEN (first turn):")[1][:60])
        assert len(openers) == 4, "opener rotation regressed"

    def test_final_assessment_still_falls_through_to_legacy(self):
        plan = {**PLAN, "completed_sessions": 8, "total_sessions": 8}
        assert build(learning_plan_data=plan) is None

    def test_roleplay_still_falls_through_to_legacy(self):
        assert build(session_mode="roleplay", topic="travel", learning_plan_data=PLAN) is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Negative cases — no plan at all
# ─────────────────────────────────────────────────────────────────────────────


class TestWithoutPlan:
    def test_news_without_plan(self):
        out = build(news_context=NEWS_RAW)
        assert "Dutch trains face delays" in out

    def test_topic_without_plan(self):
        out = build(topic="travel")
        assert "Topic:" in out

    def test_bare_session_falls_back_to_free_practice(self):
        out = build()
        assert "Free practice" in out

    def test_empty_plan_dict_is_not_a_plan_session(self):
        out = build(news_context=NEWS_RAW, learning_plan_data={})
        assert "Dutch trains face delays" in out

    def test_unparseable_news_still_falls_through_to_legacy(self):
        """Must fall back to the legacy builder, NOT silently become a plan session."""
        assert build(news_context="not json", learning_plan_data=PLAN) is None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Contract paragraph must match the actual mode
# ─────────────────────────────────────────────────────────────────────────────


class TestContractParagraph:
    def test_plan_session_gets_the_plan_contract(self):
        out = build(learning_plan_data=PLAN)
        assert "LEARNING PLAN CONTRACT" in out
        assert "SESSION CONTRACT" not in out

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"news_context": NEWS_RAW},
            {"topic": "travel"},
            {"topic": "custom", "user_prompt": "Formula 1 racing"},
        ],
    )
    def test_non_plan_sessions_never_claim_a_plan(self, kwargs):
        for plan in (None, PLAN):
            out = build(learning_plan_data=plan, **kwargs)
            assert "LEARNING PLAN CONTRACT" not in out
            assert "SESSION CONTRACT" in out

    def test_free_practice_gets_no_contract(self):
        out = build()
        assert "LEARNING PLAN CONTRACT" not in out
        assert "SESSION CONTRACT" not in out

    def test_contract_omission_leaves_clean_formatting(self):
        out = build()
        assert "corrections.\n\n# Personality & Tone" in out
        assert "\n\n\n" not in out


# ─────────────────────────────────────────────────────────────────────────────
# 5. Edge cases around the predicate itself
# ─────────────────────────────────────────────────────────────────────────────


class TestBlankContextEdgeCases:
    @pytest.mark.parametrize("blank", ["", "   ", "\n\t "])
    def test_blank_topic_is_not_context_so_the_plan_still_applies(self, blank):
        out = build(topic=blank, learning_plan_data=PLAN)
        assert "Week 1 focus: Family and home life" in out

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_user_prompt_is_not_context(self, blank):
        out = build(user_prompt=blank, learning_plan_data=PLAN)
        assert "Week 1 focus: Family and home life" in out

    def test_custom_topic_without_a_prompt_is_still_a_choice(self):
        """topic='custom' is a real selection, so it must not fall back to the plan."""
        out = build(topic="custom", learning_plan_data=PLAN)
        assert_no_plan_content(out)

    def test_custom_topic_without_a_prompt_claims_no_subject(self):
        """
        topic='custom' with nothing typed names no subject: it lands in free
        practice, so the prompt must not claim the student chose anything.
        """
        out = build(topic="custom", learning_plan_data=PLAN)
        assert "Free practice" in out
        assert "SESSION CONTRACT" not in out
        assert "LEARNING PLAN CONTRACT" not in out


class TestHasExplicitSessionContext:
    @pytest.mark.parametrize(
        "args",
        [(None, None, None), ("", "", ""), ("   ", None, None), (None, None, "\t")],
    )
    def test_falsy_and_blank_inputs(self, args):
        assert has_explicit_session_context(*args) is False

    @pytest.mark.parametrize(
        "args",
        [
            (NEWS_RAW, None, None),
            (None, "Formula 1 racing", None),
            (None, None, "travel"),
            ({"news_title": "x"}, None, None),  # non-string payload
        ],
    )
    def test_real_context_inputs(self, args):
        assert has_explicit_session_context(*args) is True

    def test_no_arguments_is_false(self):
        assert has_explicit_session_context() is False


# ─────────────────────────────────────────────────────────────────────────────
# 6. Route-level guard (defence in depth)
# ─────────────────────────────────────────────────────────────────────────────


class TestRouteSkipsPlanLookup:
    def test_plan_lookup_is_guarded_before_any_query(self):
        """
        fetch_active_learning_plan must consult has_explicit_session_context
        BEFORE it touches Mongo, otherwise freestyle/news sessions keep paying
        for the lookup and keep attaching the plan to the request.
        """
        import inspect

        import routes.realtime_routes as rr

        source = inspect.getsource(rr.generate_token)
        body = source.split("async def fetch_active_learning_plan()")[1]

        guard_at = body.find("has_explicit_session_context(")
        query_at = body.find("plans_collection.find_one(")

        assert guard_at != -1, "route-level guard is missing"
        assert query_at != -1, "plan query disappeared — test needs updating"
        assert guard_at < query_at, "guard must run before the plan query"
