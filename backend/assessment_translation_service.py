"""
Assessment Translation Service
================================
Translates GPT-generated assessment text fields into the user's UI locale.

Design principles:
- English is always generated first (authoritative source, never replaced)
- Translation is a single additional GPT call covering ALL text fields at once
- If translation fails for any reason, the caller gets English — never an error
- locale == 'en' short-circuits immediately (zero extra cost)
- Only the 7 app-supported locales are accepted; anything else falls back to English

Translated fields:
  Assessment:
    pronunciation.feedback, grammar.feedback, vocabulary.feedback,
    fluency.feedback, coherence.feedback,
    strengths[], areas_for_improvement[], next_steps[]
  DNA profile:
    overall_profile.speaker_archetype, overall_profile.summary,
    overall_profile.strengths[], overall_profile.growth_areas[],
    dna_strands.<each>.description
"""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Locales the app supports — anything else silently falls back to English
SUPPORTED_LOCALES = {"en", "es", "fr", "de", "nl", "pt", "tr"}

# Human-readable locale names for the GPT prompt
LOCALE_NAMES = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "nl": "Dutch",
    "pt": "Portuguese (Brazilian)",
    "tr": "Turkish",
}

# Key suffix used when storing / returning translated content
def locale_key(field: str, locale: str) -> str:
    return f"{field}_{locale}"


def _is_translatable_locale(locale: Optional[str]) -> bool:
    """Return True only when we should actually perform translation."""
    if not locale:
        return False
    lc = locale.lower().split("-")[0]   # 'tr-TR' → 'tr'
    return lc in SUPPORTED_LOCALES and lc != "en"


def _normalise_locale(locale: str) -> str:
    return locale.lower().split("-")[0]


async def translate_assessment(
    assessment: Dict,
    ui_locale: Optional[str],
) -> Dict:
    """
    Translate all user-facing text fields in `assessment` into `ui_locale`.

    Returns:
        The same dict with extra `_<locale>` keys added in-place.
        On any error, returns the original dict unchanged.
    """
    if not _is_translatable_locale(ui_locale):
        return assessment

    locale = _normalise_locale(ui_locale)
    lang_name = LOCALE_NAMES[locale]

    # ── Collect all strings to translate in a single structured payload ──
    payload: Dict = {}

    # Skill feedback
    for skill in ("pronunciation", "grammar", "vocabulary", "fluency", "coherence"):
        skill_data = assessment.get(skill, {})
        if isinstance(skill_data, dict) and skill_data.get("feedback"):
            payload[f"{skill}_feedback"] = skill_data["feedback"]

    # Lists
    for field in ("strengths", "areas_for_improvement", "next_steps"):
        items = assessment.get(field, [])
        if items:
            payload[field] = items

    # DNA overall profile
    op = assessment.get("dna_profile", {})
    if isinstance(op, dict):
        op = op.get("overall_profile", {}) or {}

    for field in ("speaker_archetype", "summary"):
        if op.get(field):
            payload[f"dna_{field}"] = op[field]

    for field in ("strengths", "growth_areas"):
        if op.get(field):
            payload[f"dna_{field}"] = op[field]

    # DNA strand descriptions
    strands = {}
    dna = assessment.get("dna_profile", {})
    if isinstance(dna, dict):
        strands = dna.get("dna_strands", {}) or {}

    for strand_key, strand_val in strands.items():
        if isinstance(strand_val, dict) and strand_val.get("description"):
            payload[f"strand_{strand_key}_description"] = strand_val["description"]

    if not payload:
        return assessment

    # ── Single GPT call ──
    try:
        from sentence_assessment import create_openai_client
        client = create_openai_client()

        system_prompt = (
            f"You are a professional translator specialising in language-learning app content. "
            f"Translate the following JSON values into {lang_name}. "
            f"Rules:\n"
            f"1. Translate ONLY the values, never the keys.\n"
            f"2. For arrays, translate each element and keep the same array length.\n"
            f"3. Keep technical terms (CEFR levels like A1, B2, etc.) unchanged.\n"
            f"4. Match the tone: encouraging, direct, Gen-Z friendly.\n"
            f"5. Return ONLY valid JSON with the exact same keys.\n"
            f"6. Do NOT add explanations or markdown.\n"
            f"7. For 'dna_speaker_archetype' (personality label like 'The Thoughtful Builder'): "
            f"   adapt it culturally, not literally. The result must feel natural and motivating "
            f"   as a personality archetype in {lang_name}. Keep the 'The ...' article pattern "
            f"   if it fits the target language, otherwise use the most natural equivalent.\n"
            f"8. For feedback, strengths, and improvement areas: use natural, conversational "
            f"   {lang_name} as if a friendly coach is speaking directly to the learner."
        )

        user_content = json.dumps(payload, ensure_ascii=False)

        response = client.chat.completions.create(
            model="gpt-4o-mini",      # cheap + fast enough for translation
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )

        translated: Dict = json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.warning(f"[TRANSLATION] Failed to translate assessment to {locale}: {e}")
        return assessment   # graceful fallback — English stays

    # ── Merge translated values back under locale-suffixed keys ──
    try:
        # Skill feedback
        for skill in ("pronunciation", "grammar", "vocabulary", "fluency", "coherence"):
            key = f"{skill}_feedback"
            if key in translated and isinstance(assessment.get(skill), dict):
                assessment[skill][locale_key("feedback", locale)] = translated[key]

        # Lists
        for field in ("strengths", "areas_for_improvement", "next_steps"):
            if field in translated:
                assessment[locale_key(field, locale)] = translated[field]

        # DNA overall profile
        dna = assessment.get("dna_profile")
        if isinstance(dna, dict):
            op = dna.get("overall_profile")
            if isinstance(op, dict):
                for field in ("speaker_archetype", "summary"):
                    tkey = f"dna_{field}"
                    if tkey in translated:
                        op[locale_key(field, locale)] = translated[tkey]
                for field in ("strengths", "growth_areas"):
                    tkey = f"dna_{field}"
                    if tkey in translated:
                        op[locale_key(field, locale)] = translated[tkey]

            # Strand descriptions
            dna_strands = dna.get("dna_strands") or {}
            for strand_key in dna_strands:
                tkey = f"strand_{strand_key}_description"
                if tkey in translated and isinstance(dna_strands[strand_key], dict):
                    dna_strands[strand_key][locale_key("description", locale)] = translated[tkey]

        logger.info(f"[TRANSLATION] ✅ Assessment translated to {locale} ({len(translated)} fields)")

    except Exception as e:
        logger.warning(f"[TRANSLATION] Failed to merge translation for {locale}: {e}")
        # assessment already has English — still safe to return

    return assessment
