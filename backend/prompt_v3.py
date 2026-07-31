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
from typing import Any, Dict, List, Optional

from tutor_config import (
    get_session_pacing,
    get_topic_config,
    get_topic_vocabulary,
    get_subtopic_arcs,
)

# ─────────────────────────────────────────────────────────────────────────────
# Per-CEFR conversation profiles — one compact line each, no essays.
# ─────────────────────────────────────────────────────────────────────────────

_LEVEL_PROFILES: Dict[str, Dict[str, str]] = {
    "A1": {
        "turn":      "ONE short simple sentence per turn (max ~8 words), spoken slowly and clearly.",
        "ratio":     "The student should speak about 60% of the time.",
        "questions": "Ask yes/no or this-or-that questions about simple facts. Ask the question and STOP — never tack a spoken tag like 'yes or no?' onto the end; the question form already makes the choice clear, and the tag makes you sound robotic. One question per turn. Never ask 'why', opinions, or anything needing numbers, dates or reasons.",
        "fix_style": "Corrections: 3–5 words, then say the full correct phrase once and move on.",
    },
    "A2": {
        "turn":      "One or two short sentences per turn (max ~12 words total).",
        "ratio":     "The student should speak about 70% of the time.",
        "questions": "Simple open questions are fine. One question per turn. An occasional gentle 'why' is OK.",
        "fix_style": "Corrections: one short sentence, then continue.",
    },
    "B1": {
        "turn":      "One or two natural sentences per turn.",
        "ratio":     "The student should speak about 80% of the time.",
        "questions": "Open questions and 'why' are good. One question per turn.",
        "fix_style": "Corrections: direct and brief — name the fix, give the correct form, continue.",
    },
    "B2": {
        "turn":      "Two or three natural sentences per turn; idioms welcome.",
        "ratio":     "The student should speak about 80% of the time.",
        "questions": "Push for detail, opinions and comparisons. One question per turn.",
        "fix_style": "Corrections: direct — include word-choice and register issues, not just grammar.",
    },
    "C1": {
        "turn":      "One or two dense, natural sentences per turn.",
        "ratio":     "The student should speak about 85% of the time.",
        "questions": "Probe nuance and counter-arguments. One question per turn.",
        "fix_style": "Corrections: precise — target nuance, collocation and register.",
    },
    "C2": {
        "turn":      "Natural native register, concise turns.",
        "ratio":     "The student should speak about 85% of the time.",
        "questions": "Challenge precision and style. One question per turn.",
        "fix_style": "Corrections: hold them to near-native standard; flag anything unidiomatic.",
    },
}

# Deterministic opener rotation — indexed by completed_sessions % 4 for plan
# sessions (0 otherwise). The model cannot remember earlier sessions, so WE
# provide the variety it is asked for.
_OPENER_STYLES: List[str] = [
    "Name today's goal in a few words, then ask one easy starter question.",
    "Open with a question that uses one of today's vocabulary words — no preamble.",
    "Briefly recall one thing from the last session (see Context), then bridge to today's goal with a question.",
    "Drop the student straight into a tiny real-life scenario about today's goal and ask what they would say.",
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
    phrases = _rotate_slice(week.get("key_phrases") or [], session_in_week, 2)

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

    lines = []

    # Top-level plan identity — tutor sees the learner's actual commitment
    if goal_labels:
        lines.append(f"- Plan goal(s): {', '.join(goal_labels)}")
    if sub_goal_labels:
        lines.append(f"- Plan sub-goal(s): {', '.join(sub_goal_labels)}")

    lines += [
        f"- Week {week_idx + 1} focus: {focus}",
        f"- TODAY'S GOAL (session {session_in_week + 1} of this week): {activity}",
    ]
    if vocab:
        lines.append(f"- Today's vocabulary to work in naturally: {', '.join(str(v) for v in vocab)}")
    if phrases:
        lines.append(f"- Useful phrases: {' | '.join(str(p) for p in phrases)}")

    # Continuity from the last 2 sessions — corrections to re-check and the
    # carry-over focus. Metadata only; keeps the prompt small.
    history = learning_plan_data.get("session_history") or []
    for hist in reversed(history[-2:]):
        ss = hist.get("structured_summary") or {}
        if not ss:
            continue
        prev = []
        practiced = ss.get("vocabulary_practiced") or []
        if practiced:
            prev.append(f"practiced {', '.join(str(w) for w in practiced[:4])}")
        focus_next = ss.get("focus_next_session")
        if focus_next:
            prev.append(f"carry-over focus: {focus_next}")
        corrections = ss.get("corrections_made") or []
        for c in corrections[:2]:
            if isinstance(c, dict) and c.get("wrong") and c.get("correct"):
                prev.append(f"watch for '{c['wrong']}' -> '{c['correct']}'")
        if prev:
            lines.append(f"- Last session: {'; '.join(prev)}")
        break  # one line of continuity is enough — newest session with a summary

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

    if learning_plan_data:
        built = _plan_context(learning_plan_data)
        if built is None:
            return None  # final assessment → legacy
        context_block, goal_short = built
        opener_idx = int(learning_plan_data.get("completed_sessions") or 0) % len(_OPENER_STYLES)
    elif news_raw:
        built = _news_context(news_raw)
        if built is None:
            return None  # unparseable news payload → legacy handles it
        context_block, goal_short = built
    elif topic and topic != "custom":
        context_block, goal_short = _topic_context(topic, level, pacing)
    elif user_prompt:
        context_block, goal_short = _custom_context(user_prompt, getattr(request, "research_data", None))
    else:
        context_block = f"- Free practice. Pick ONE everyday theme suited to {level} and stay on it."

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
2. THEN, out loud, give only a brief natural acknowledgement and move on — e.g. "Goed — en ..." or "Nice, and ...". Do NOT read the correction, the words "quick tip", or the wrong/right forms aloud. The card already shows them.
- ONLY correct REAL errors. If the sentence is already correct, do NOT correct it and do NOT call the tool — just reply and ask the next question.
- At most ONE correction per student turn, and aim for one every 2–3 turns — let most turns flow uncorrected so the student keeps talking.
- Tiny slips (a dropped article, a small mispronunciation): just recast naturally in your reply, no tool, no comment.
- Never say the tool's name. Never announce that you are correcting."""
    else:
        corrections_section = """# Corrections
Corrections are disabled for this session. Recast errors naturally in your replies; never correct explicitly, and do not call any tool."""

    wrapup_line = (
        "In your LAST 1–2 turns: name ONE specific thing the student did well and ONE specific thing "
        "to practice, both based on what actually happened this session. If they made several errors, "
        "say so kindly — honest beats flattering. No generic praise."
    )

    # Sample phrases: the model copies these closely (guide G3). The spoken
    # part after a correction is ONLY a brief acknowledgement + next question —
    # the correction itself lives in the tool card, never in speech. Samples
    # also obey each level's grammar ceiling (A1 present tense only).
    if level == "A1":
        sample_fix = '(after calling the tool) "Goed! En jij — koffie of thee?"  — a short cheer + next question, NOT the correction itself.'
        sample_wrap = '"Good job today! You said many words. Next time: try longer answers, not just yes."'
    elif level == "A2":
        sample_fix = '(after calling the tool) "Prima — en wat deed je daarna?"  — brief acknowledgement + next question, never the fix aloud.'
        sample_wrap = '"Nice work — your questions were clear. One thing to practice: past tense, it slipped a few times."'
    else:
        sample_fix = '(after calling the tool) "Good point — and what happened next?"  — acknowledge and continue; the card shows the fix.'
        sample_wrap = '"Strong session — your past tense was solid. One thing to practice: articles; they slipped a few times today."'

    _art = "an" if level.startswith("A") else "a"

    # Duration-scaled focus rules: shorter sessions = stricter on-topic enforcement.
    # 1 min (~4 exchanges) — zero drift budget; 3 min — one redirect max; 5 min — brief follow + redirect.
    if duration <= 1:
        drift_rule = (
            "STAY ON TODAY'S GOAL for all exchanges — there is no time for detours. "
            "If the student goes off-topic, redirect immediately: \"Interesting — and back to [goal]: ...\""
        )
    elif duration <= 3:
        drift_rule = (
            "If the student drifts off TODAY'S GOAL, acknowledge with ONE short sentence then redirect: "
            "\"Nice — and back to [goal]: ...\" Do NOT follow the detour for more than one exchange."
        )
    else:
        drift_rule = (
            "If the student drifts far off TODAY'S GOAL, follow briefly (one exchange), "
            "then steer back with a question tied to the goal."
        )

    instructions = f"""# Role & Objective
You are a {lang_name} speaking coach in a live {duration}-minute voice session with {_art} {level} learner.
A successful session means: the student did most of the talking, they practiced TODAY'S GOAL throughout, and they leave with 1–2 concrete corrections.

LEARNING PLAN CONTRACT — the student built this plan to improve in these specific areas. You must honor it every session, even short ones. Never drift to unrelated small talk or generic topics when a goal and sub-goal are listed in Context.

# Personality & Tone
- Warm, encouraging, natural — a coach, not a quiz machine and not a cheerleader.
- {profile['turn']}
- {profile['ratio']}
- {profile['questions']}
- Vary your wording between turns. Never repeat a sentence or opener you already used this session.

# Language
- Speak ONLY {lang_name}, at difficulty matching {level}.
- If the student answers in another language: give them the {lang_name} words they needed and continue in {lang_name}. Never switch languages yourself.
- If their audio is unclear, ask them ONCE in simple {lang_name} to say it again. If still unclear, move on with your best guess — never ask a third time.{lexical_block}

# Context
- Session length: {duration} minute(s) — about {turns} exchanges. {pacing.get('pacing_note', '')}
{context_block}

{corrections_section}

# Conversation Flow
1. OPEN (first turn): {_OPENER_STYLES[opener_idx]} Do NOT use a generic greeting like "Hello! What would you like to practice?"
2. PRACTICE — STAY ON GOAL: {drift_rule}
3. WRAP-UP: {wrapup_line}

# Never drill a phrase — NEVER make the student repeat the same sentence more than once
- Do NOT run pronunciation drills. If the student mispronounces or struggles with a phrase, ask them to try it ONE more time AT MOST.
- If it is still not perfect on that second try: say the correct version ONCE, praise the effort ("Goed geprobeerd!"), and MOVE ON to a new question. NEVER ask for the same phrase a third time.
- A1/A2 learners will not be perfect — that is expected. Progress and flow matter more than a perfect phrase. Getting stuck on one sentence breaks the conversation.

# Sample phrases (patterns only — speak them in {lang_name}, vary them, never copy every time)
- Fix: {sample_fix}
- Redirect: "Nice — and back to {goal_short}: ..."
- Honest wrap: {sample_wrap}
"""
    return instructions
