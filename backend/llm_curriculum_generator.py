"""
LLM curriculum generator — week-by-week plan content from gpt-5.6-terra.

Why this exists (2026-08-03):
  The previous pipeline let gpt-4.1 write only `overview` + 5 objectives + 5
  resources; all 24 weeks came from a static Python dict
  (enriched_goals_config.ENRICHED_GOALS). Measured on a real production plan
  (1cd8cabe, Dutch A1, 6 months / 96 sessions):

      24 weeks -> 5 distinct vocabulary sets, 32 distinct words TOTAL,
      every word in ENGLISH, and 0 influence from the assessment scores.

  prompt_v3._plan_context() injects `key_vocabulary` verbatim into the live
  tutor prompt, so a Dutch learner's session was told to work in
  "price, size, color, receipt". That is also where the hallucinated
  correction came from (tutor "corrected" a correct Dutch sentence to match
  the English word it had been handed).

Design:
  - The MODEL owns pedagogy: week focus, activities, target-language
    vocabulary + phrases, skill sequencing against the assessment.
  - The CODE owns structure: week count, numbering, session_details,
    total_sessions, and every field name consumers read. The model never
    supplies a count or an index, so a bad generation cannot produce a
    malformed plan — only weaker content.
  - Any failure returns None and the caller falls back to the existing
    IntelligentScheduleGenerator, so plan creation never fails because of it.

API contract (verified live against gpt-5.6-terra, 2026-08-03):
  - MUST use /v1/responses. On /v1/chat/completions the API rejects function
    tools with 400: "Function tools with reasoning_effort are not supported
    for gpt-5.6-terra in /v1/chat/completions."
  - `temperature` is rejected (only the default 1 is accepted).
  - `max_tokens` is rejected; the parameter is `max_output_tokens`.
  - Structured output goes in `text.format` as a json_schema with strict=True,
    which requires `additionalProperties: false` and every property listed in
    `required` at each object level.

Feature flag: LLM_CURRICULUM_V1 (env, default off). Flag off = the previous
code path runs unchanged.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Strips a leading "Session 1:" / "Sessions 2-3:" / "Sessie 2:" label from an
# activity. Position in the list decides the session, so an embedded number that
# disagrees with the slot is worse than no number at all.
_SESSION_PREFIX_RE = re.compile(
    r"^\s*(?:session|sessions|sessie|sessies|sitzung|séance|sesión|sessão)\s*"
    r"[0-9]+\s*(?:[-–—]\s*[0-9]+)?\s*[:.)-]\s*",
    re.IGNORECASE,
)

MODEL = "gpt-5.6-terra"

# Reasoning effort. "high" measurably re-orders the skill sequence to match the
# assessment (verified: fluency 27 < grammar 28 -> fluency scheduled first),
# which is the entire point of moving to a reasoning model.
REASONING_EFFORT = os.getenv("LLM_CURRICULUM_EFFORT", "high")

# Generation is a one-off at plan creation; a generous ceiling avoids a
# truncated JSON body on 24-week plans. Reasoning tokens count against this.
MAX_OUTPUT_TOKENS = 32000
REQUEST_TIMEOUT_S = float(os.getenv("LLM_CURRICULUM_TIMEOUT", "180"))

# Interface-language code -> name, mirroring learning_routes._INTERFACE_LANG_NAMES.
_INTERFACE_LANG_NAMES = {
    "tr": "Turkish", "nl": "Dutch", "de": "German",
    "fr": "French", "es": "Spanish", "pt": "Portuguese",
    "en": "English",
}

# The assessment pipeline injects this UI warning into areas_for_improvement.
# It is user-facing copy, not a learning gap — it must never reach the model.
_SHORT_SAMPLE_MARKER = "we recommend speaking for at least 60 words"


def _week_schema(n_weeks: int, sessions_per_week: int = 4) -> Dict[str, Any]:
    """
    Strict json_schema for the weekly curriculum.

    minItems/maxItems are NOT supported by strict structured outputs, so the
    exact week count is enforced in the prompt and then repaired in code
    (_normalize). Every object sets additionalProperties=false and lists all
    properties in `required`, as strict mode demands.
    """
    return {
        "type": "object",
        "properties": {
            "overview": {
                "type": "string",
                "description": (
                    "2-3 sentences addressed to the learner as 'you'. Name a real "
                    "strength from the assessment, then say how THIS plan targets "
                    "their specific weak areas and chosen topics."
                ),
            },
            "learning_objectives": {
                "type": "array",
                "description": (
                    "Exactly 5 concrete, measurable objectives. Each maps to a real "
                    "skill gap and references the weeks that deliver it. Never generic."
                ),
                "items": {"type": "string"},
            },
            "resources": {
                "type": "array",
                "description": (
                    "Exactly 5 real, level-appropriate resources for this specific "
                    "target language (apps, books, podcasts, YouTube channels)."
                ),
                "items": {"type": "string"},
            },
            "weeks": {
                "type": "array",
                "description": f"Exactly {n_weeks} week objects, in teaching order.",
                "items": {
                    "type": "object",
                    "properties": {
                        "focus": {
                            "type": "string",
                            "description": (
                                "Concrete, specific title for this week's topic and angle. "
                                "Never a bare skill name."
                            ),
                        },
                        "primary_skill": {
                            "type": "string",
                            "enum": ["pronunciation", "grammar", "vocabulary", "fluency", "coherence"],
                        },
                        "sub_goal": {
                            "type": "string",
                            "description": "Which learner sub-goal this week serves, or 'general'.",
                        },
                        "activities": {
                            "type": "array",
                            "description": (
                                f"Exactly {sessions_per_week} activities — ONE per session of "
                                f"this week, in order. prompt_v3 picks activities[session_index] "
                                f"as that session's goal, so a short list makes late sessions "
                                f"repeat earlier ones. Do NOT prefix them with 'Session N:' — "
                                f"position already determines the session. Each one is a few "
                                f"minutes of spoken conversation with an AI tutor: no screen, "
                                f"nothing to read or write, no pictures or recordings, and no "
                                f"role-play — the tutor never plays a character. Describe what "
                                f"the student SAYS."
                            ),
                            "items": {"type": "string"},
                        },
                        "key_vocabulary": {
                            "type": "array",
                            "description": (
                                "6-10 words IN THE TARGET LANGUAGE the student is learning. "
                                "Never in the interface language."
                            ),
                            "items": {"type": "string"},
                        },
                        "key_phrases": {
                            "type": "array",
                            "description": (
                                "3-4 full usable sentences IN THE TARGET LANGUAGE, "
                                "level-appropriate."
                            ),
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "focus", "primary_skill", "sub_goal",
                        "activities", "key_vocabulary", "key_phrases",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["overview", "learning_objectives", "resources", "weeks"],
        "additionalProperties": False,
    }


def _build_prompt(
    *,
    language: str,
    level: str,
    n_weeks: int,
    sessions_per_week: int,
    session_minutes: int,
    goals: List[str],
    sub_goals: List[str],
    assessment_data: Dict[str, Any],
    interface_language: str,
) -> str:
    lang = language.capitalize()
    iface_name = _INTERFACE_LANG_NAMES.get((interface_language or "en").lower().strip(), "English")

    # Per-skill scores with the assessor's own feedback — this is what the
    # reasoning model uses to sequence weeks against real weaknesses.
    skill_lines = []
    for key, label in [
        ("pronunciation", "Pronunciation"), ("grammar", "Grammar"),
        ("vocabulary", "Vocabulary"), ("fluency", "Fluency"),
        ("coherence", "Coherence"),
    ]:
        obj = assessment_data.get(key) or {}
        if isinstance(obj, dict):
            score = obj.get("score", 0)
            fb = str(obj.get("feedback", "") or "")[:220]
            skill_lines.append(f"  - {label}: {score}/100" + (f" — {fb}" if fb else ""))
    skills_block = "\n".join(skill_lines) or "  (no skill breakdown available)"

    raw_areas = assessment_data.get("areas_for_improvement") or []
    areas = [
        a for a in raw_areas
        if isinstance(a, str) and _SHORT_SAMPLE_MARKER not in a
    ][:6]
    areas_block = "\n".join(f"  - {a}" for a in areas) or "  - General improvement"

    strengths = [s for s in (assessment_data.get("strengths") or []) if isinstance(s, str)][:4]
    strengths_block = "\n".join(f"  - {s}" for s in strengths) or "  - Basic communication"

    transcript = str(assessment_data.get("recognized_text") or "").strip()[:600]
    transcript_block = (
        f"\n=== WHAT THE STUDENT ACTUALLY SAID (assessment transcript) ===\n{transcript}\n"
        if transcript else ""
    )

    # Speaking DNA — learner archetype and pace, when available.
    dna_block = ""
    dna = assessment_data.get("dna_profile") or {}
    if isinstance(dna, dict) and dna:
        overall = dna.get("overall_profile") or {}
        strands = dna.get("dna_strands") or {}
        rhythm = (strands.get("rhythm") or {}).get("description", "")
        conf = (strands.get("confidence") or {}).get("level", "")
        growth = overall.get("growth_areas") or []
        bits = []
        if overall.get("speaker_archetype"):
            bits.append(f"  - Archetype: {overall['speaker_archetype']}")
        if rhythm:
            bits.append(f"  - Speaking rhythm: {rhythm}")
        if conf:
            bits.append(f"  - Confidence: {conf}")
        if growth:
            bits.append(f"  - Growth areas: {', '.join(str(g) for g in growth)}")
        if bits:
            dna_block = "\n=== SPEAKING DNA ===\n" + "\n".join(bits) + "\n"

    goals_txt = ", ".join(goals) if goals else "general communication"
    sub_goals_txt = ", ".join(sub_goals) if sub_goals else "not specified"

    # The session budget is not a guess — it is the same table the live tutor
    # runs on (tutor_config.SESSION_PACING), so an activity can never ask for
    # more ground than the tutor is given time to cover. Measured failure that
    # led to this: a 3-minute A1 activity read "Give a short personal
    # introduction with five different facts", while the tutor prompt for that
    # very session said "Cover 2 subtopics" — 5 against 2 in one prompt. The
    # tutor split the difference into six rapid-fire closed questions and the
    # student never gave an introduction at all.
    try:
        from tutor_config import SESSION_PACING
        _pace = SESSION_PACING.get(int(session_minutes or 3)) or SESSION_PACING[3]
    except Exception:
        _pace = {"turns_target": 10, "subtopics_to_cover": 2}
    turns_target = _pace.get("turns_target", 10)
    subtopics = _pace.get("subtopics_to_cover", 2)
    # Tutor turns include the opener and the wrap-up, so what is actually left
    # for the activity itself is smaller than the headline number.
    student_answers = max(turns_target - 2, 2)

    # What the tutor is ALLOWED to ask at this level, quoted from the runtime
    # prompt's own level profile. An activity that needs a question the tutor
    # may not ask is unachievable by construction, however good it looks.
    _CEFR_ASK = {
        "A1": ("yes/no and this-or-that questions about simple facts, present tense only. "
               "The tutor may NOT ask 'why', opinions, stories, times, dates, or numbers "
               "beyond simple counting"),
        "A2": ("simple open questions, present and simple past; an occasional gentle 'why'"),
        "B1": ("open questions and 'why'; reasons, plans and short narratives"),
        "B2": ("detail, opinions and comparisons; hypotheticals"),
        "C1": ("nuance, counter-arguments and abstract discussion"),
        "C2": ("precision, register and style; native-level challenge"),
    }
    cefr_ask = _CEFR_ASK.get(str(level).upper(), _CEFR_ASK["B1"])

    return f"""You are a CEFR-certified curriculum designer. Design a complete \
{n_weeks}-week speaking curriculum for one real student.

=== STUDENT ===
Learning (TARGET LANGUAGE — all vocabulary and phrases go in this language): {lang}
App interface language (all descriptive text goes in this language): {iface_name}
CEFR level: {level}
Plan length: {n_weeks} weeks, {sessions_per_week} speaking sessions per week

=== THE SIZE OF ONE SESSION — read this before writing any activity ===
One session is {session_minutes} minute(s) of live speech. In that time the tutor
gets about {turns_target} turns in total: one to open, one to close, and the rest
for the activity. So the student answers roughly {student_answers} times, and the
tutor can cover about {subtopics} subtopic(s) — no more.
At {level} the tutor may only ask: {cefr_ask}.
An activity that needs more turns than this, or a question the tutor is not
allowed to ask at {level}, CANNOT be done. It is not an ambitious activity —
it is a broken one.
Overall assessment score: {assessment_data.get('overall_score', 0)}/100

=== SKILL ASSESSMENT ===
{skills_block}

=== STRENGTHS ===
{strengths_block}

=== WEAKNESSES TO FIX ===
{areas_block}
{transcript_block}{dna_block}
=== WHAT THE STUDENT SIGNED UP FOR ===
Main goals: {goals_txt}
Specific topics they chose: {sub_goals_txt}

=== HOW TO BUILD IT ===
1. SEQUENCE BY WEAKNESS. Look at the skill scores above. The lowest-scoring
   skills must get the most weeks and must come FIRST. Set `primary_skill` on
   each week accordingly. Do not spread weeks evenly.
2. COVER THEIR TOPICS. The topics they chose ({sub_goals_txt}) must be covered
   substantially. Treat each topic as a real-life domain, and interpret it in
   the context of their main goals ({goals_txt}) — for example "shopping" for a
   daily-life learner means everyday errands, not tourist souvenir shopping.
3. TWO LANGUAGES, TWO JOBS — do not mix them up:
   a) `key_vocabulary` and `key_phrases` are the STUDY MATERIAL and must be in
      {lang.upper()}, the language the student is learning. Every vocabulary
      entry is a {lang} word; every phrase is a full {lang} sentence the student
      could actually say. NEVER write these in {iface_name} or English
      (unless {lang} is that language). This is the single most important rule.
   b) `focus` and `activities` are what the student READS ABOUT their plan in
      the app, and must be written in {iface_name} — the language of the app
      interface. Do not write them in {lang} and do not default to English.
4. NO REPEATS. Across all {n_weeks} weeks, vocabulary must keep expanding.
   A word used in one week must not reappear as a key word in another. Aim for
   6-10 new words every week.
5. LEVEL-APPROPRIATE — CEFR, not a label. Everything must be sayable by a real
   {level} speaker and askable by a tutor limited to: {cefr_ask}.
   - A1: concrete high-frequency words; one-clause present-tense sentences.
     Activities are answering simple factual questions and naming things.
     Never ask an A1 student to explain, compare, justify or tell a story.
   - A2: present and simple past; two clauses joined by "and"/"but"/"because".
     Short descriptions of routine and recent events.
   - B1: reasons, plans, short narratives; the student can hold a turn.
   - B2: opinions, comparisons, hypotheticals, some abstraction.
   - C1: nuance, counter-argument, abstract topics.
   - C2: precision, register and style.
   Write the activity so that {level} is what makes it hard enough — not the
   number of things packed into it. If an activity would only work at a level
   above {level}, rewrite it, do not keep it as a stretch goal.
6. PROGRESSION. Later weeks build on earlier ones and get more demanding.
   Each week's `focus` must be a specific, concrete title — never a bare skill
   label like "Vocabulary practice".
7. ONE ACTIVITY PER SESSION. Give exactly {sessions_per_week} activities per
   week — the student does one per session, in the order you list them, and
   they should progress across the week (introduce → practise → produce).
   Do NOT number them or write "Session 1:" / "Sessions 2-3:" in the text;
   their position in the list already determines which session they belong to.
8. EVERY ACTIVITY IS A SPOKEN CONVERSATION. Each session is a few minutes of
   live talk between the student and an AI tutor who asks and listens. There is
   no screen to look at, nothing to read or write, no pictures, cards, lists or
   recordings to play, and no partner but the tutor — who stays the tutor and
   never acts out a character. So never write an activity that asks the student
   to point at, look at, match, read, write, fill in, listen to a recording, or
   role-play with someone. Write what the student SAYS: describing something,
   answering questions about it, telling what they would say in a situation,
   giving a short spoken report. "Say which of two options fits" works (add
   "and why" only where rule 5 allows 'why' at {level}); "Point to the picture
   and name it" or "Role-play with a receptionist" does not.
9. ONE ACTIVITY = ONE THING, AND IT MUST FIT THE SESSION. Each activity covers
   about {subtopics} subtopic(s) and is finished in roughly {student_answers}
   student answers. Never ask for a fixed COUNT of items — no "five different
   facts", no "three sentences", no "name six words", no "cover your job, your
   family and your city". A counted list turns the session into a checklist:
   the tutor announces each item in turn, the student answers in fragments, and
   nobody has a conversation. Name ONE thing the student talks about and let the
   tutor's questions supply the depth. "Answer questions about where you live"
   works; "Give an introduction with five different facts" does not.

=== ALSO WRITE THE PLAN SUMMARY ===
After designing the {n_weeks} weeks, describe THAT PLAN — not a generic one.
The summary fields must be consistent with the weeks you actually produced:

- `overview`: 2-3 sentences, speaking to the learner as "you". Open with a real
  strength from their assessment, then explain how this plan attacks their
  weakest skills and covers the topics they chose. Use {level}-level wording.
- `learning_objectives`: exactly 5, each tied to a specific skill gap above and
  to the weeks that deliver it. Concrete and checkable — never "improve overall
  speaking". Reference real content from your weeks.
- `resources`: exactly 5 REAL resources for {lang} learners at {level} — name
  actual apps, books, podcasts or channels that exist for this language, and
  match them to the learner's topics. No invented titles.

Write all three in {iface_name} (they are app-facing text, like `focus`).

Return exactly {n_weeks} week objects in `weeks`, in teaching order."""


def _dedupe_preserving_order(items: List[str], seen: set, limit: int) -> List[str]:
    """Drop cross-week duplicates (case-insensitively) while keeping order."""
    out: List[str] = []
    for it in items:
        if not isinstance(it, str):
            continue
        term = it.strip()
        if not term:
            continue
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(term)
        if len(out) >= limit:
            break
    return out


def _session_details(focus: str, sessions_per_week: int) -> List[Dict[str, Any]]:
    """Session skeleton — identical shape to IntelligentScheduleGenerator."""
    return [
        {
            "session_number": i + 1,
            "focus": focus,
            "completed_at": None,
            "duration_minutes": None,
            "session_summary": None,
            "status": "pending",
        }
        for i in range(sessions_per_week)
    ]


def _normalize(
    raw_weeks: List[Dict[str, Any]],
    *,
    n_weeks: int,
    sessions_per_week: int,
    goals: List[str],
    sub_goals: List[str],
) -> List[Dict[str, Any]]:
    """
    Turn model output into the exact structure consumers expect.

    Code owns every structural invariant here: week numbering, week count,
    session_details, total_sessions. The model cannot break the schedule shape
    even if it returns the wrong number of weeks or a malformed entry.
    """
    valid = [w for w in raw_weeks if isinstance(w, dict) and str(w.get("focus", "")).strip()]
    if not valid:
        raise ValueError("model returned no usable weeks")

    # Too few weeks: cycle earlier ones as reinforcement rather than failing.
    if len(valid) < n_weeks:
        logger.warning(
            "[LLM_CURRICULUM] Model returned %d weeks, need %d — cycling for reinforcement",
            len(valid), n_weeks,
        )
        idx = 0
        while len(valid) < n_weeks:
            valid.append(dict(valid[idx % max(len(valid), 1)]))
            idx += 1
    valid = valid[:n_weeks]

    main_goal = goals[0] if goals else None
    seen_vocab: set = set()
    seen_phrases: set = set()
    out: List[Dict[str, Any]] = []

    for i, w in enumerate(valid):
        focus = str(w.get("focus", "")).strip() or f"Week {i + 1} speaking practice"

        # One activity per session. prompt_v3 selects activities[session_in_week],
        # so the list must be exactly sessions_per_week long: too short and late
        # sessions silently replay session 1's goal; too long and the tail is
        # never reachable. Any "Session N:" prefix the model still emits is
        # stripped, because position — not the label — decides the session, and a
        # stale label contradicts the slot it lands in.
        activities = []
        for a in (w.get("activities") or []):
            if not isinstance(a, str) or not a.strip():
                continue
            activities.append(_SESSION_PREFIX_RE.sub("", a.strip()).strip())

        if not activities:
            activities = [focus]
        # Cycle to fill, truncate to fit — never leave a session without a goal.
        if len(activities) < sessions_per_week:
            base = list(activities)
            for k in range(sessions_per_week - len(base)):
                activities.append(base[k % len(base)])
        activities = activities[:sessions_per_week]

        # Cross-week dedup keeps vocabulary expanding, but must never leave a
        # week with nothing: prompt_v3 injects key_vocabulary into the live tutor
        # prompt, and an empty list means that session gets no target words at
        # all. If dedup emptied the week, keep the model's own terms for it.
        raw_vocab = [
            str(v).strip() for v in (w.get("key_vocabulary") or [])
            if isinstance(v, str) and str(v).strip()
        ]
        vocab = _dedupe_preserving_order(raw_vocab, seen_vocab, 10)
        if not vocab and raw_vocab:
            vocab = raw_vocab[:10]

        raw_phrases = [
            str(p).strip() for p in (w.get("key_phrases") or [])
            if isinstance(p, str) and str(p).strip()
        ]
        phrases = _dedupe_preserving_order(raw_phrases, seen_phrases, 4)
        if not phrases and raw_phrases:
            phrases = raw_phrases[:4]

        skill = str(w.get("primary_skill", "") or "").strip().lower()
        if skill not in {"pronunciation", "grammar", "vocabulary", "fluency", "coherence"}:
            skill = "fluency"

        sub_goal = str(w.get("sub_goal", "") or "").strip() or (
            sub_goals[i % len(sub_goals)] if sub_goals else "general"
        )

        week: Dict[str, Any] = {
            "week": i + 1,                     # code-owned, always contiguous
            "focus": focus,
            "primary_skill": skill,
            "activities": activities,
            "key_vocabulary": vocab,
            "key_phrases": phrases,
            "sessions_completed": 0,
            "total_sessions": sessions_per_week,
            "session_details": _session_details(focus, sessions_per_week),
            "sub_goal": sub_goal,
            "generated_by": "llm_curriculum_v1",
        }
        if main_goal:
            week["main_goal"] = main_goal
        out.append(week)

    return out


async def generate_llm_curriculum(
    *,
    language: str,
    level: str,
    duration_months: int,
    sessions_per_week: int,
    goals: List[str],
    sub_goals: Optional[List[str]],
    assessment_data: Dict[str, Any],
    interface_language: str = "en",
    session_minutes: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Generate the whole plan with gpt-5.6-terra in ONE reasoning pass.

    Returns {"weekly_schedule", "overview", "learning_objectives", "resources"}
    on success, or None on ANY failure so the caller can fall back to the
    existing generator. This function never raises.

    Overview/objectives/resources are produced in the same call as the weeks so
    the model reasons about the curriculum it just designed — a separate model
    writing the summary can only guess at what the weeks contain.
    """
    if os.getenv("LLM_CURRICULUM_V1", "false").lower() != "true":
        return None

    n_weeks = max(int(duration_months or 1) * 4, 1)
    goals = [g for g in (goals or []) if g]
    sub_goals = [s for s in (sub_goals or []) if s]

    try:
        from openai_client import get_async_openai
        client = get_async_openai()
        if client is None:
            logger.warning("[LLM_CURRICULUM] OpenAI client unavailable")
            return None

        prompt = _build_prompt(
            language=language, level=level, n_weeks=n_weeks,
            sessions_per_week=sessions_per_week, session_minutes=session_minutes,
            goals=goals, sub_goals=sub_goals,
            assessment_data=assessment_data or {}, interface_language=interface_language,
        )

        logger.info(
            "[LLM_CURRICULUM] Generating %d weeks with %s (effort=%s) for %s %s",
            n_weeks, MODEL, REASONING_EFFORT, language, level,
        )

        # /v1/responses is REQUIRED: chat.completions rejects reasoning models
        # with structured tool output (verified 400 against this exact model).
        # No `temperature` (rejected) and no `max_tokens` (use max_output_tokens).
        response = await client.responses.create(
            model=MODEL,
            input=prompt,
            reasoning={"effort": REASONING_EFFORT},
            text={
                "format": {
                    "type": "json_schema",
                    "name": "weekly_curriculum",
                    "strict": True,
                    "schema": _week_schema(n_weeks, sessions_per_week),
                }
            },
            max_output_tokens=MAX_OUTPUT_TOKENS,
            timeout=REQUEST_TIMEOUT_S,
        )

        # An incomplete response carries truncated (invalid) JSON — treat as failure.
        if getattr(response, "status", None) == "incomplete":
            reason = getattr(getattr(response, "incomplete_details", None), "reason", "unknown")
            logger.warning("[LLM_CURRICULUM] Response incomplete (%s) — falling back", reason)
            return None

        payload = json.loads(response.output_text)
        weeks = _normalize(
            payload.get("weeks") or [],
            n_weeks=n_weeks, sessions_per_week=sessions_per_week,
            goals=goals, sub_goals=sub_goals,
        )

        distinct_vocab = {v.lower() for w in weeks for v in w["key_vocabulary"]}
        empty_vocab = sum(1 for w in weeks if not w["key_vocabulary"])
        usage = getattr(response, "usage", None)
        reasoning_tokens = 0
        if usage is not None:
            reasoning_tokens = getattr(
                getattr(usage, "output_tokens_details", None), "reasoning_tokens", 0
            ) or 0

        # A plan whose weeks carry no vocabulary is the exact failure mode this
        # module exists to fix — reject it rather than ship it.
        if empty_vocab > n_weeks // 2:
            logger.warning(
                "[LLM_CURRICULUM] %d/%d weeks have no vocabulary — falling back",
                empty_vocab, n_weeks,
            )
            return None

        # Summary fields. Each is optional at this layer: if the model returns a
        # short/empty one, the caller simply keeps its programmatic default for
        # that field rather than losing the whole (good) curriculum.
        overview = str(payload.get("overview") or "").strip()
        objectives = [
            str(o).strip() for o in (payload.get("learning_objectives") or [])
            if isinstance(o, str) and str(o).strip()
        ]
        resources = [
            str(r).strip() for r in (payload.get("resources") or [])
            if isinstance(r, str) and str(r).strip()
        ]

        logger.info(
            "[LLM_CURRICULUM] ✅ %d weeks, %d distinct vocabulary terms, "
            "overview=%s objectives=%d resources=%d, "
            "%d reasoning tokens, %d total tokens",
            len(weeks), len(distinct_vocab), "yes" if overview else "no",
            len(objectives), len(resources), reasoning_tokens,
            getattr(usage, "total_tokens", 0) if usage else 0,
        )
        return {
            "weekly_schedule": weeks,
            "overview": overview,
            "learning_objectives": objectives,
            "resources": resources,
        }

    except json.JSONDecodeError as e:
        logger.warning("[LLM_CURRICULUM] Could not parse model JSON: %s — falling back", e)
        return None
    except Exception as e:
        logger.warning(
            "[LLM_CURRICULUM] Generation failed (%s): %s — falling back",
            type(e).__name__, e,
        )
        return None
