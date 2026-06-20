"""
Story Worlds turn loop — TEXT-based (v1).

The player TYPES their reply; gpt-4o-mini judges whether it meets the scene
goal (is it among the acceptable answers?), writes the character's in-story
reply, translates that reply into the player's support language, and gives a
gentle (non-blocking) spelling note. One cheap JSON call, instant, deterministic
input — no STT, no TTS, no mis-transcription.

Voice is deferred to v2 (streaming Realtime), so this module is intentionally
text-only.
"""

import json
import logging
import re
from typing import Any, Dict

from openai_client import get_async_openai

logger = logging.getLogger(__name__)

JUDGE_MODEL = "gpt-4o-mini"

LANG_NAMES = {
    "english": "English", "spanish": "Spanish", "french": "French",
    "german": "German", "dutch": "Dutch", "portuguese": "Portuguese", "italian": "Italian",
    "turkish": "Turkish",
}


def _judge_prompt(scene: Dict[str, Any], language: str, level: str, support_lang: str) -> str:
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    support_name = LANG_NAMES.get(support_lang.lower(), support_lang.title())
    return f"""You are the judge + scene partner for a {lang_name} ({level}) writing game.

The player TYPES their reply. They must achieve this SCENE GOAL in {lang_name}:
  GOAL: {scene.get('goal_en') or scene.get('goal')}
  A model answer that satisfies it: "{scene.get('me')}"
  The character just said: "{scene.get('open', {}).get('line', '')}"

JUDGING RULES (be fair to a {level} beginner):
- The answer MUST be written in {lang_name}. If the player wrote in English or any
  other language instead of {lang_name}, set goal_met=false and spoke_target_language=false,
  and the character should (in {lang_name}) nudge them to answer in {lang_name}.
- If it IS in {lang_name}: accept ANY answer that reasonably achieves the goal, even
  with small mistakes. Minor spelling errors, missing diacritics/accents, or casing do
  NOT block success — the goal is met if the INTENT is right.
- Reject (goal_met=false) if it's off-topic, in the wrong language, empty, or nonsense.
- Spelling feedback is SEPARATE from goal_met: a player can meet the goal AND get a
  gentle spelling note. The note must never feel punishing.

Return STRICT JSON:
{{
  "goal_met": true|false,
  "reason": "1 short phrase (English) — why it did/didn't meet the goal",
  "character_line": "the character's reply IN {lang_name} (1-2 sentences). If goal met: react warmly and advance the story. If not: stay in character and nudge them to try again — don't break immersion.",
  "character_line_translation": "the character_line translated into {support_name}",
  "spelling_feedback": "if there's a small spelling/accent slip, a gentle 1-line note in English (e.g. \\"Almost — it's 'café' with an é\\"); otherwise null",
  "spoke_target_language": true|false
}}"""


# A single token repeated (STT artifact guard kept for safety, harmless on text).
_REPEAT_RE = re.compile(r"^(\b[\wà-üÀ-Ü]+\b)([ ,.!?]+\1)+[ ,.!?]*$", re.IGNORECASE)


async def score_turn_text(
    text: str,
    scene: Dict[str, Any],
    language: str,
    level: str,
    support_lang: str = "english",
) -> Dict[str, Any]:
    """Judge a TYPED reply. Returns goal_met + character reply (+ translation + spelling)."""
    client = get_async_openai()
    answer = (text or "").strip()

    if not answer:
        return {
            "text": "",
            "goal_met": False,
            "character_line": scene.get("open", {}).get("line", "…?"),
            "character_line_translation": "",
            "spelling_feedback": None,
            "reason": "empty",
            "spoke_target_language": True,
            "retry": True,
        }

    judge = await client.chat.completions.create(
        model=JUDGE_MODEL,
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=400,
        messages=[
            {"role": "system", "content": _judge_prompt(scene, language, level, support_lang)},
            {"role": "user", "content": f'Player typed: "{answer}"'},
        ],
    )
    verdict = json.loads(judge.choices[0].message.content)

    return {
        "text": answer,
        "goal_met": bool(verdict.get("goal_met")),
        "character_line": verdict.get("character_line") or scene.get("reply", {}).get("line", ""),
        "character_line_translation": verdict.get("character_line_translation") or "",
        "spelling_feedback": verdict.get("spelling_feedback"),
        "reason": verdict.get("reason"),
        "spoke_target_language": verdict.get("spoke_target_language", True),
        "retry": False,
    }
