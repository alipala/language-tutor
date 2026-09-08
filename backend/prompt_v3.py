"""
PROMPT_V3 — guide-aligned instruction builder for gpt-realtime-mini.

Why this exists (field feedback, 2026-07-17):
  1. "Talking into a wall" — the V1/V2 prompts FORBID explicit correction
     (recast-only). Recasts are invisible in audio, so learners feel
     uncorrected and unhelped.
  2. "Every session repeats / tutor loses the plan" — the legacy prompt
     mandates an EXACT first message and injects the same week-level
     context into every session of the week, while its 4–6.5k-token
     rule-wall makes the mini model drop instructions unpredictably.

Design principles (OpenAI realtime prompting guide + cookbook):
  - SHORT, sectioned skeleton (Role / Personality / Language / Context /
    Corrections / Flow / Samples). Bullets over paragraphs. ~1.5k tokens.
  - No overlapping ALWAYS/NEVER walls — one rule, once.
  - Duration is a first-class input: sessions are 1 / 3 / 5 minutes
    (~4 / 10 / 16 exchanges). The whole prompt is sized so it survives a
    full session on a mini model WITHOUT mid-session session.update.
  - Session-granular curriculum: activity + vocabulary ROTATE per session
    within the week (legacy injected identical context all week).
  - Deterministic opener rotation kills the "same greeting every session"
    loop (the model cannot remember previous sessions; we vary for it).
  - Explicit-lite corrections: recasts for slips, short spoken "quick tip"
    fixes for clear errors, report_grammar_mistake on every explicit fix.
  - Honest wrap-up tied to what actually happened — no unconditional
    celebration.

Feature flag: PROMPT_V3 (env, default off). build_instructions_v3 returns
None for modes it does not support (roleplay, learning-plan FINAL
assessment) — the caller falls through to the legacy builders, so flag-off
and unsupported paths stay byte-identical.
"""

import json
import os
from typing import Any, Dict, List, Optional

from tutor_config import (
    get_session_pacing,
    get_topic_config,
    get_topic_vocabulary,
    get_subtopic_arcs,
    has_explicit_session_context,
)

# ─────────────────────────────────────────────────────────────────────────────
# Per-CEFR conversation profiles — one compact line each, no essays.
# ─────────────────────────────────────────────────────────────────────────────

_LEVEL_PROFILES: Dict[str, Dict[str, str]] = {
    "A1": {
        "turn":      "Your turn IS the question: ask it and stop. One short sentence, max ~8 words, spoken slowly and clearly. Do not restate their answer or comment on it first — that lead-in is what makes turns long and makes you sound like an echo.",
        "ratio":     "The student should speak about 60% of the time.",
        "questions": "Ask yes/no or this-or-that questions about simple facts, and reach for this-or-that first: a plain yes/no buys back one word, while a choice makes the student produce a real one. Two bare yes/no questions in a row is the pattern to avoid. One question per turn, asked and then finished — no spoken tag like 'yes or no?' on the end. Nothing needing 'why', an opinion or a story yet.",
        "fix_style": "Corrections: 3–5 words, then say the full correct phrase once and move on.",
    },
    "A2": {
        "turn":      "Your turn IS the question: ask it and stop. One sentence, max ~10 words. Do not restate their answer or comment on it first.",
        "ratio":     "The student should speak about 70% of the time.",
        "questions": "Simple open questions are fine. One question per turn. An occasional gentle 'why' is OK.",
        "fix_style": "Corrections: one short sentence, then continue.",
    },
    "B1": {
        "turn":      "A short reaction to what they just said, then your question — two sentences, no third.",
        "ratio":     "The student should speak about 80% of the time.",
        "questions": "Open questions and 'why' are good. One question per turn.",
        "fix_style": "Corrections: direct and brief — name the fix, give the correct form, continue.",
    },
    "B2": {
        "turn":      "React to what they said, then ask — two or three natural sentences; idioms welcome.",
        "ratio":     "The student should speak about 80% of the time.",
        "questions": "Push for detail, opinions and comparisons. One question per turn.",
        "fix_style": "Corrections: direct — include word-choice and register issues, not just grammar.",
    },
    "C1": {
        "turn":      "React, then ask — one or two dense, natural sentences.",
        "ratio":     "The student should speak about 85% of the time.",
        "questions": "Probe nuance and counter-arguments. One question per turn.",
        "fix_style": "Corrections: precise — target nuance, collocation and register.",
    },
    "C2": {
        "turn":      "React, then ask, in natural native register — concise turns.",
        "ratio":     "The student should speak about 85% of the time.",
        "questions": "Challenge precision and style. One question per turn.",
        "fix_style": "Corrections: hold them to near-native standard; flag anything unidiomatic.",
    },
}

# Deterministic opener rotation — indexed by completed_sessions % 4 for plan
# sessions (0 otherwise). The model cannot remember earlier sessions, so WE
# provide the variety it is asked for.
_OPENER_STYLES: List[str] = [
    "Say hello and name today's goal in a few words, then ask one easy starter question.",
    "Say hello and name today's goal, then ask a question built around one of today's words.",
    "Say hello, recall one thing from the last session (see Context), then bridge to today's goal with a question.",
    # This one used to read "drop the student straight into a tiny real-life
    # scenario ... and ask what they would say", and the tutor answered the
    # invitation by becoming a character in the scene — offering its own passport
    # and asking whether its own booking was fine. A situation the student speaks
    # about is fine; a scene the tutor acts in is not.
    "Say hello and name today's goal, then name one everyday situation where it comes up and ask the student what they would say in it.",
]


def _rotate_slice(items: List[Any], index: int, size: int) -> List[Any]:
    """Deterministic rotating window over a list (wraps around)."""
    if not items:
        return []
    if len(items) <= size:
        return list(items)
    start = (index * size) % len(items)
    window = items[start:start + size]
    if len(window) < size:
        window += items[: size - len(window)]
    return window


# ─────────────────────────────────────────────────────────────────────────────
# Mode context builders — each returns (context_block, todays_goal_short)
# ─────────────────────────────────────────────────────────────────────────────

def _plan_context(learning_plan_data: Dict) -> Optional[tuple]:
    plan_content = learning_plan_data.get("plan_content") or {}
    completed = int(learning_plan_data.get("completed_sessions") or 0)
    total = int(learning_plan_data.get("total_sessions") or 0)
    if total and completed >= total:
        return None  # final assessment — legacy builder owns that flow

    # fetch_active_learning_plan (realtime_routes) provides exactly:
    # plan_content / completed_sessions / total_sessions / session_history /
    # session_summaries / goals / sub_goals. The get() below therefore
    # always falls back to 4, which is deliberate: the legacy builder
    # hardcodes sessions_per_week = 4 for its week math, and V3 must map
    # sessions to the same weeks or a mid-plan flag flip would shift the
    # curriculum.
    spw = int(learning_plan_data.get("sessions_per_week") or 4)
    weekly = plan_content.get("weekly_schedule") or []
    week_idx = min(completed // spw, max(len(weekly) - 1, 0))
    week = weekly[week_idx] if weekly else {}
    session_in_week = completed % spw

    focus = week.get("focus", "general speaking practice")
    activities = week.get("activities") or []
    # Session-granular rotation: a different activity and vocab slice per
    # session, so two sessions in the same week never share the same goal.
    activity = activities[session_in_week % len(activities)] if activities else focus
    vocab = _rotate_slice(week.get("key_vocabulary") or [], session_in_week, 4)
    # key_phrases is deliberately NOT read. The curriculum generator writes it
    # from the student's own assessment transcript, so the entries are
    # first-person statements of fact about them ("Ik woon in Utrecht.",
    # "Ik kom uit Turkije."). Handing those to the coach as language to use has
    # no good reading: say them as itself and it is claiming the student's life
    # as its own, or turn them into questions and it is telling the student what
    # the answer is. The measured session did the latter — "woon je in Utrecht
    # of in een andere stad?", "Kom je uit Turkije of uit een ander land?" — and
    # then could not let go of Utrecht when the student named a Turkish city,
    # asking "Is jouw stad in Nederland?" four turns after they had said
    # otherwise, because the instruction outranks the transcript. Vocabulary is
    # safe (single words carry no claim); sentences are not.

    # User-selected goals and sub-goals (stored on the plan document).
    # These are the macro topics the learner committed to when creating the plan.
    # We show them to the tutor as the non-negotiable learning contract so it
    # never drifts to an unrelated topic, even in short 1-minute sessions.
    raw_goals = learning_plan_data.get("goals") or []
    raw_sub_goals = learning_plan_data.get("sub_goals") or []
    # Humanize IDs: "daily_life" → "daily life", keep short strings as-is
    def _humanize(s: str) -> str:
        return str(s).replace("_", " ").replace("-", " ").strip()

    goal_labels = [_humanize(g) for g in raw_goals if g]
    sub_goal_labels = [_humanize(sg) for sg in raw_sub_goals if sg]

    # Layered per the realtime guide's Long Context Behavior pattern: the model
    # is told which lines govern today and which are background, instead of
    # being handed one flat list and left to infer priority. Plan history grows
    # every session, and undifferentiated bullets let last week's carry-over
    # compete with today's goal — the guide's stated failure mode ("Do not rely
    # on the model to infer source priority from a raw transcript or large
    # context dump. Use structure.").
    lines = [
        "## Today — this governs the session",
        f"- TODAY'S GOAL (session {session_in_week + 1} of week {week_idx + 1}): {activity}",
    ]
    if vocab:
        lines.append(f"- Words to work in: {', '.join(str(v) for v in vocab)}")

    # Continuity from the newest session that has a summary. The recurring
    # errors belong with TODAY because re-checking them is the point of carrying
    # them forward at all; filing them under "background, today wins" would tell
    # the tutor to ignore the one thing it is meant to watch for. Only the softer
    # continuity — what was covered, what was suggested next — is background,
    # where it cannot outrank the goal this session was built around.
    history = learning_plan_data.get("session_history") or []
    recheck: List[str] = []
    background: List[str] = []
    for hist in reversed(history[-2:]):
        ss = hist.get("structured_summary") or {}
        if not ss:
            continue
        recheck = [
            f"'{c['wrong']}' -> '{c['correct']}'"
            for c in (ss.get("corrections_made") or [])[:2]
            if isinstance(c, dict) and c.get("wrong") and c.get("correct")
        ]
        practiced = ss.get("vocabulary_practiced") or []
        if practiced:
            background.append(f"- Covered last time: {', '.join(str(w) for w in practiced[:4])}")
        focus_next = ss.get("focus_next_session")
        if focus_next:
            background.append(f"- Suggested next focus: {focus_next}")
        break

    if recheck:
        lines.append(f"- Watch for these again: {'; '.join(recheck)}")

    plan_lines = [f"- This week: {focus}"]
    if goal_labels:
        plan_lines.append(f"- Long-term goals: {', '.join(goal_labels)}")
    if sub_goal_labels:
        plan_lines.append(f"- Areas: {', '.join(sub_goal_labels)}")
    lines += ["", "## The plan this belongs to"] + plan_lines

    if background:
        lines += ["", "## Background — earlier sessions"] + background + [
            "- Status: background. Where any of it competes with TODAY'S GOAL, today wins."
        ]

    return "\n".join(lines), str(activity)


def _news_context(news_context_raw: str) -> Optional[tuple]:
    try:
        data = json.loads(news_context_raw) if isinstance(news_context_raw, str) else news_context_raw
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    title = data.get("news_title") or data.get("title") or "a news article"
    summary = data.get("news_summary") or data.get("summary") or ""
    vocab = data.get("vocabulary") or []
    questions = data.get("discussion_questions") or []

    vocab_words = []
    for v in vocab[:5]:
        if isinstance(v, dict):
            vocab_words.append(str(v.get("word", "")))
        else:
            vocab_words.append(str(v))
    vocab_words = [w for w in vocab_words if w]

    lines = [f"- Article: {title}"]
    if summary:
        lines.append(f"- Summary: {str(summary)[:400]}")
    if vocab_words:
        lines.append(f"- Vocabulary to work in naturally: {', '.join(vocab_words)}")
    for q in questions[:3]:
        lines.append(f"- Discussion question: {q}")
    return "\n".join(lines), f"discussing the article '{title}'"


def _topic_context(topic: str, level: str, pacing: Dict) -> tuple:
    # Catalogue entries (tutor_config.TOPIC_CATALOGUE) use display_name and
    # subtopic_arcs = [{"name", "questions": [...]}]; get_topic_config
    # resolves aliases and returns None for unknown/DNA-strand topics.
    cfg = get_topic_config(topic)
    if not cfg:
        return f"- Topic: {topic.replace('_', ' ').replace('-', ' ')}", topic.replace("_", " ").replace("-", " ")
    name = cfg.get("display_name", topic)
    lines = [f"- Topic: {name}"]
    desc = cfg.get("description")
    if desc:
        lines.append(f"- Angle: {desc}")
    vocab = get_topic_vocabulary(topic, level)
    if vocab:
        lines.append(f"- Vocabulary to work in naturally: {', '.join(vocab[:5])}")
    arcs = get_subtopic_arcs(topic, pacing.get("subtopics_to_cover", 2))
    for arc in arcs:
        arc_name = arc.get("name") or ""
        questions = arc.get("questions") or []
        starter = questions[0] if questions else ""
        if arc_name:
            lines.append(f"- Subtopic: {arc_name}" + (f" (starter: {starter})" if starter else ""))
    return "\n".join(lines), str(name)


def _custom_context(user_prompt: str, research_context: Optional[str]) -> tuple:
    lines = [f"- The student chose this topic: {user_prompt}"]
    if research_context:
        digest = str(research_context).strip().replace("\n\n", "\n")[:500]
        lines.append(f"- Background you can draw on: {digest}")
    return "\n".join(lines), str(user_prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Main builder
# ─────────────────────────────────────────────────────────────────────────────

def build_instructions_v3(request: Any, language: str, level: str) -> Optional[str]:
    """
    Build the PROMPT_V3 instruction string, or return None when this mode
    should fall back to the legacy builders (roleplay, final assessment,
    unparseable context).
    """
    session_mode = getattr(request, "session_mode", "conversation") or "conversation"
    if session_mode == "roleplay":
        return None

    # Normalize non-CEFR level values. The DNA-strand practice flow sends
    # level='intermediate' (SpeakingDNAScreenHorizontal navigates with that
    # literal); map named levels to CEFR so the prompt never says
    # "an INTERMEDIATE learner".
    level = {"BEGINNER": "A1", "INTERMEDIATE": "B1", "ADVANCED": "C1"}.get(
        level.upper(), level.upper()
    )
    profile = _LEVEL_PROFILES.get(level, _LEVEL_PROFILES["B1"])
    if level not in _LEVEL_PROFILES:
        level = "B1"
    lang_name = language.capitalize()

    duration = getattr(request, "selected_duration", 5) or 5
    pacing = get_session_pacing(duration)
    turns = pacing.get("turns_target", 10)

    # ── Resolve mode context ─────────────────────────────────────────────
    learning_plan_data = getattr(request, "learning_plan_data", None)
    news_raw = getattr(request, "news_context", None)
    topic = getattr(request, "topic", None)
    user_prompt = getattr(request, "user_prompt", None)

    opener_idx = 0
    context_block: Optional[str] = None
    goal_short = f"{lang_name} conversation practice"

    # /api/realtime/token attaches the user's active learning plan to EVERY
    # session, so learning_plan_data alone does not mean "this is a plan
    # session". Whatever the learner explicitly picked must win: without this
    # guard a news or freestyle session for a user with an active plan was
    # rebuilt as a plan session — the article and the chosen topic never reached
    # the model at all, and the tutor quoted corrections from earlier PLAN
    # sessions. The legacy A1/A2 builder has carried the same guard since
    # BEGINNER_PROMPT_V2; V3 runs before it, so it needs its own.
    explicit_context = has_explicit_session_context(news_raw, user_prompt, topic)
    is_plan_session = bool(learning_plan_data) and not explicit_context

    # `mode` records which branch actually produced the Context block, so the
    # contract paragraph below can describe the real session instead of guessing
    # from the inputs. topic="custom" with no user_prompt names no subject and
    # lands in free practice, for example — it must not claim the student chose
    # something.
    if is_plan_session:
        built = _plan_context(learning_plan_data)
        if built is None:
            return None  # final assessment → legacy
        context_block, goal_short = built
        opener_idx = int(learning_plan_data.get("completed_sessions") or 0) % len(_OPENER_STYLES)
        mode = "plan"
    elif news_raw:
        built = _news_context(news_raw)
        if built is None:
            return None  # unparseable news payload → legacy handles it
        context_block, goal_short = built
        mode = "news"
    elif topic and topic != "custom":
        context_block, goal_short = _topic_context(topic, level, pacing)
        mode = "topic"
    elif user_prompt:
        context_block, goal_short = _custom_context(user_prompt, getattr(request, "research_data", None))
        mode = "custom"
    else:
        context_block = f"- Free practice. Pick ONE everyday theme suited to {level} and stay on it."
        mode = "free"

    # ── A1/A2 lexical + grammar ceiling ──────────────────────────────────
    # CEFR research (arxiv 2501.15247; ERIC EJ1466280): the model only hits A1
    # vs A2 when the prompt carries an EXPLICIT high-frequency word list. For
    # B1+ this returns None (broad range is desired) and nothing is injected.
    from beginner_wordlists import get_beginner_lexical_lock
    lexical_lock = get_beginner_lexical_lock(language, level)
    lexical_block = f"\n\n{lexical_lock}" if lexical_lock else ""

    corrections_enabled = not getattr(request, "disable_corrections", False)

    # ── Corrections section — the behavioral core of V3 ──────────────────
    # TOOL-FIRST design: the correction itself is shown to the student in a
    # visual card triggered by the report_grammar_mistake tool call — NOT spoken
    # out loud. Speaking every fix ("Quick tip: ...") both drowned the session
    # in corrections AND caused the mini model to skip the tool call (it felt
    # "done" after speaking), so the card never appeared. Here the tool call is
    # the primary action; speech is a brief acknowledgement only.
    if corrections_enabled:
        corrections_section = f"""# Corrections — via the tool, not your voice
When the student makes a CLEAR error (grammar, verb form, word choice, word order):
1. FIRST call report_grammar_mistake with the wrong form, the correct form, and a short tip. This shows the student a correction card — it is how corrections reach them.
2. THEN, out loud: take your normal turn for this level, exactly as described above — a correction adds nothing to it. Do NOT read the correction, the words "quick tip", or the wrong/right forms aloud; the card already shows them.
- Correct REAL errors only: a sentence that is already right gets no tool call and no comment — just your reply and the next question.
- At most ONE correction per student turn, and aim for one every 2–3 turns — let most turns flow uncorrected so the student keeps talking.
- Tiny slips (a dropped article, a small mispronunciation): just recast naturally in your reply, no tool, no comment.
- Say nothing about the machinery: not the tool's name, not that a correction happened, not what you are about to do next. The student hears a conversation, not a description of one.

## After a fix, move forward
This is the rule students notice most, so apply it every time you fix something.
- The turn after a fix has the same shape as every other turn at this level. Nothing extra is tacked on because a correction happened.
- When the student mispronounces or fumbles a phrase: say the correct version ONCE yourself, then ask a new question about the SAME topic. That is the whole repair.
- Never hand the student a sentence to say back. This is banned as a SHAPE, in any wording and any language: "say that again", "now say: ...", "repeat after me", "ask the question: ...". A {duration}-minute conversation has no room for drilling, and at {level} the correct form sticks because they heard you use it, not because they recited it.
- Imperfect pronunciation is expected at {level} and is not a problem to solve today. Keep the conversation moving; the student improves by talking more, not by repeating one line."""
    else:
        corrections_section = """# Corrections
Corrections are disabled for this session. Recast errors naturally in your replies; never correct explicitly, and do not call any tool."""

    # Counted in exchanges, not in time. Realtime conversation items carry no
    # timestamps and the model gets no elapsed-session signal, so "in your last
    # 1-2 turns" was an instruction it could not evaluate — and an unsatisfiable
    # rule competes with the satisfiable ones around it. Exchanges it can count
    # from the conversation it is holding.
    wrapup_line = (
        f"Once you have had about {max(turns - 2, 2)} exchanges, close the session: name ONE specific thing "
        "the student did well and ONE specific thing to practise, both from what actually happened "
        "today. If they struggled, say so kindly — honest beats flattering, and generic praise is "
        "worse than none."
    )

    # Sample phrases: the model copies these closely (OpenAI realtime prompting
    # guide → "Reduce repetition"), so they are written as SHAPES with the
    # content left blank rather than as speakable lines.
    #
    # A literal example is a hallucination source, not just a style issue: the
    # A1 sample used to read "Goed! En jij — koffie of thee?", and in production
    # the tutor asked a learner about coffee-or-tea in the middle of a shopping
    # lesson and again during a personal-profile lesson — the only concrete
    # topic in the prompt was the one baked into the example. Describing the
    # slot ("ask your next question about TODAY'S GOAL") leaves nothing to copy.
    if level == "A1":
        sample_fix = (
            'ONE new short question about TODAY\'S GOAL '
            '— never about a topic that is not in Context.'
        )
        sample_wrap = (
            'name one thing they did well and one thing to practise, in {level}-level words, '
            'both taken from what actually happened in this session.'
        ).replace('{level}', level)
    elif level == "A2":
        sample_fix = (
            'ONE new question that moves TODAY\'S GOAL forward. '
            'Never say the fix aloud.'
        )
        sample_wrap = (
            'one genuine strength plus one concrete thing to practise, both from this session.'
        )
    else:
        sample_fix = (
            'acknowledge in a few words and continue with a question '
            'that deepens TODAY\'S GOAL; the card shows the fix.'
        )
        sample_wrap = (
            'one specific strength and one specific weakness observed this session — no generic praise.'
        )

    _art = "an" if level.startswith("A") else "a"

    # Duration-scaled focus rules: shorter sessions = stricter on-topic enforcement.
    # 1 min (~4 exchanges) — zero drift budget; 3 min — one redirect max; 5 min — brief follow + redirect.
    # No quoted redirect line here. The guide is explicit that "the model closely
    # follows sample phrases", and a quoted template with blanks is a script: the
    # tutor read one aloud in production ("and back to the conversation: ...").
    # These describe the move instead of scripting it.
    # Free practice has no assigned goal, so both the step label and the redirect
    # example have to stop naming one. Left alone they pointed at goal_short,
    # which in this mode is the placeholder "<Language> conversation practice" —
    # a subject the student never chose and the tutor would be policing.
    practice_label = "PRACTICE — STAY ON YOUR THEME" if mode == "free" else "PRACTICE — STAY ON GOAL"
    redirect_target = "the theme you picked" if mode == "free" else goal_short
    # Test hook: pin the rotation to one opener so a specific style can be
    # exercised now instead of waiting for completed_sessions to come round to
    # it (a given style returns only every 4th plan session). Leave unset in
    # normal operation — an unset or non-numeric value keeps the rotation.
    _pinned = (os.getenv("REALTIME_OPENER_STYLE") or "").strip()
    if _pinned.isdigit():
        opener_idx = int(_pinned) % len(_OPENER_STYLES)

    # The rotation's openers all name today's goal, which free practice does not
    # have — off-plan sessions always land on index 0 ("Name today's goal…").
    opener_line = (
        "Say hello, name the everyday theme you have picked for today, then ask one easy "
        "starter question about it."
        if mode == "free" else _OPENER_STYLES[opener_idx]
    )

    if mode == "free":
        drift_rule = (
            "You chose the theme, so keep the conversation inside it. If the student "
            "opens a new subject, follow them there and make THAT the theme rather "
            "than steering back."
        )
    elif duration <= 1:
        drift_rule = (
            "Stay on TODAY'S GOAL for every exchange — there is no time for detours. "
            "If the student goes elsewhere, let it pass and ask your next question about the goal."
        )
    elif duration <= 3:
        drift_rule = (
            "If the student goes off TODAY'S GOAL, give their answer a few words, then ask "
            "your next question about the goal. One exchange of detour is the limit, and the "
            "change of subject is made by asking — not by announcing it."
        )
    else:
        drift_rule = (
            "If the student goes far off TODAY'S GOAL, follow for one exchange, then ask a "
            "question tied to the goal. Change the subject by asking, not by announcing it."
        )

    # The plan contract belongs to plan sessions only. It used to be emitted
    # unconditionally, which told the tutor to honour "this plan" during news and
    # freestyle sessions whose Context lists no plan at all — so even after the
    # precedence fix above, the model was still being pointed at a plan that was
    # not there. Each mode now states its own contract, and free practice (which
    # has no subject yet) gets none because its Context block already says to
    # pick one theme and stay on it.
    if mode == "plan":
        contract_block = (
            "\nLEARNING PLAN CONTRACT — the student built this plan to improve in these specific "
            "areas. You must honor it every session, even short ones. Never drift to unrelated small "
            "talk or generic topics when a goal and sub-goal are listed in Context.\n"
        )
    elif mode == "free":
        contract_block = ""
    else:
        contract_block = (
            f"\nSESSION CONTRACT — this session is about {goal_short}. That is what the student chose: "
            "stay on it from the first turn to the last, and never drift to unrelated small talk or to a "
            "different subject.\n"
        )

    instructions = f"""# Role & Objective
You are a {lang_name} speaking coach in a live {duration}-minute voice session with {_art} {level} learner.
A successful session means: the student did most of the talking, they practiced TODAY'S GOAL throughout, and they leave with 1–2 concrete corrections.
You are the coach in every single turn, start to finish. Situations are places the STUDENT speaks; you stay outside them and keep asking. You never take a part in one yourself — never speak as the customer, the receptionist, the friend or the shopkeeper, never say "my" about anything in the scene, and never answer your own question as if you were the other person. If the student addresses you as a character, answer as the coach and hand the question back to them.
{contract_block}
# Personality & Tone
- Warm, encouraging, natural — a coach, not a quiz machine and not a cheerleader.
- {profile['turn']}
- {profile['ratio']}
- {profile['questions']}
- Vary how you open. No two turns this session begin the same way, and the same praise word twice running is the tell that you have stopped listening.

# Language
- Speak ONLY {lang_name}, at difficulty matching {level}.
- If the student answers in another language: give them the {lang_name} words they needed and continue in {lang_name}. Never switch languages yourself.
- If their audio is unclear, ask them ONCE in simple {lang_name} to say it again. If still unclear, move on with your best guess — never ask a third time.{lexical_block}

# Context
- Session length: {duration} minute(s) — about {turns} exchanges. {pacing.get('pacing_note', '')}
{context_block}

{corrections_section}

# Conversation Flow
1. OPEN (first turn): {opener_line} Do NOT use a generic greeting like "Hello! What would you like to practice?"
2. {practice_label}: {drift_rule}
3. WRAP-UP: {wrapup_line}

# Sample phrases — SHAPES, NOT SCRIPTS
DO NOT ALWAYS USE THESE EXAMPLES, VARY YOUR RESPONSES. They show the SHAPE of a
turn; the words come from what the student just said and from today's goal — a
subject that appears only here is not a subject for this session.
- Fix (tool call first, then speak): {sample_fix}
- Redirect: a few words on what they just said, then your next question about {redirect_target}.
- Honest wrap: {sample_wrap}
"""
    return instructions
