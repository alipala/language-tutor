"""
IMPROVED Speaking Assessment with Pronunciation & Reading Detection
=====================================================================

Major Improvements:
1. Real pronunciation assessment using Azure Speech SDK (phoneme-level)
2. Reading detection to catch users reading from textbooks
3. MUCH stricter GPT-4 evaluation with realistic CEFR benchmarks
4. Multi-layered verification combining audio + text analysis

Author: Language Tutor AI
Date: 2026-02-04
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple
import base64
import tempfile
import os
import json
import logging
from fastapi import HTTPException
from sentence_assessment import create_openai_client, recognize_speech

# Import our new services
from pronunciation_assessment_service import pronunciation_service
from reading_detection_service import reading_detector

logger = logging.getLogger(__name__)


# Speaking Assessment Models
class SkillScore(BaseModel):
    score: float  # 0-100
    feedback: str
    examples: List[str] = []


class SpeakingAssessmentRequest(BaseModel):
    audio_base64: Optional[str] = None
    transcript: Optional[str] = None
    language: str
    duration: Optional[int] = 60
    prompt: Optional[str] = None
    # Device UI locale — e.g. 'tr', 'tr-TR', 'fr', 'de'.
    # When provided and supported, all user-facing text fields will also be
    # stored/returned under a `_<locale>` suffixed key alongside English.
    ui_locale: Optional[str] = None


class SpeakingAssessmentResponse(BaseModel):
    recognized_text: str
    recommended_level: str
    overall_score: float
    confidence: float
    pronunciation: SkillScore
    grammar: SkillScore
    vocabulary: SkillScore
    fluency: SkillScore
    coherence: SkillScore
    strengths: List[str]
    areas_for_improvement: List[str]
    next_steps: List[str]
    dna_profile: Optional[Dict] = None
    # Locale of the translated fields present in this response (if any).
    # Client uses this to know which _<locale> keys to read.
    ui_locale: Optional[str] = None


async def evaluate_language_proficiency_improved(
    text: str,
    language: str,
    duration: int = 60,
    prompt: Optional[str] = None,
    audio_file_path: Optional[str] = None
) -> Dict:
    """
    IMPROVED comprehensive assessment with pronunciation + reading detection

    Args:
        text: Transcribed speech text
        language: Target language
        duration: Duration in seconds
        prompt: Optional prompt given to user
        audio_file_path: Optional path to audio file for pronunciation assessment

    Returns:
        Complete assessment with accurate pronunciation and reading detection
    """
    logger.info(f"🎯 Starting IMPROVED assessment for {language}")

    word_count_pre = len(text.split()) if text else 0
    wpm_pre = (word_count_pre / max(duration, 1)) * 60
    logger.info(
        f"📝 Text: '{text[:100]}...' "
        f"({word_count_pre} words in {duration}s, ~{wpm_pre:.0f} WPM)"
    )

    # ── MINIMUM SAMPLE GATE ────────────────────────────────────────────────────
    # Research minimum for reliable CEFR scoring: 60 word tokens (75 preferred).
    # Below this threshold vocabulary diversity (TTR) and grammar complexity
    # measures are statistically unreliable (PMC8552541; clinical LSA research).
    #
    # MOBILE CONTRACT: We NEVER return HTTP 4xx here — the mobile app maps any
    # 400 response to "subscription limit reached" and shows the upgrade modal.
    # Instead we return a fully valid SpeakingAssessmentResponse with a soft
    # warning in areas_for_improvement and a conservative A1/A2 level.
    _MIN_WORDS_FOR_RELIABLE_SCORING = 60
    if word_count_pre < _MIN_WORDS_FOR_RELIABLE_SCORING and word_count_pre > 0:
        logger.warning(
            f"⚠️ SHORT SAMPLE: {word_count_pre} words < {_MIN_WORDS_FOR_RELIABLE_SCORING} "
            f"minimum — returning soft warning in valid response"
        )
        # Proceed with assessment but inject a warning; bottleneck logic will
        # naturally produce a conservative level from the thin evidence.
        _sample_warning = (
            f"Your recording was {word_count_pre} words — we recommend speaking "
            f"for at least 60 words (roughly 45-60 seconds) for a reliable level "
            f"assessment. Try again with more speech for a more accurate result."
        )
    else:
        _sample_warning = None

    # STEP 1: Detect if user is reading from text
    # Pass a rough CEFR estimate so the detector can suppress beginner-normal
    # signals (slow WPM, no fillers) that are not reading indicators at A1/A2.
    # We don't have a GPT score yet so estimate from WPM only as a hint.
    _wpm_hint = wpm_pre
    _level_hint = (
        "A1" if _wpm_hint < 70
        else "A2" if _wpm_hint < 95
        else "B1" if _wpm_hint < 115
        else "B2"
    )
    logger.info("🔍 STEP 1: Reading detection...")
    reading_analysis = reading_detector.detect_reading_patterns(
        transcript=text,
        audio_duration=duration,
        language=language,
        prompt=prompt,
        estimated_cefr_level=_level_hint,
    )

    # STEP 2: Get real pronunciation assessment (if audio available)
    pronunciation_result = None
    if audio_file_path and os.path.exists(audio_file_path):
        logger.info("🎤 STEP 2: Real pronunciation assessment (Azure)...")
        try:
            pronunciation_result = await pronunciation_service.assess_pronunciation(
                audio_file_path=audio_file_path,
                reference_text=text,
                language=language
            )
            logger.info(f"✅ Pronunciation: {pronunciation_result['pronunciation_score']:.1f}/100")
        except Exception as e:
            logger.error(f"❌ Pronunciation assessment failed: {e}")
            pronunciation_result = None
    else:
        logger.warning("⚠️ No audio file - pronunciation will be estimated")

    # STEP 3: Get STRICT GPT-4 evaluation
    logger.info("🤖 STEP 3: Strict GPT-4 text evaluation...")
    gpt_evaluation = await _strict_gpt4_evaluation(
        text=text,
        language=language,
        duration=duration,
        prompt=prompt,
        reading_analysis=reading_analysis
    )

    # STEP 4: Replace fake pronunciation score with real one
    if pronunciation_result:
        logger.info("🔄 STEP 4: Replacing GPT pronunciation with Azure phoneme analysis...")
        gpt_evaluation['pronunciation'] = {
            'score': pronunciation_result['pronunciation_score'],
            'feedback': pronunciation_result['feedback'],
            'examples': [
                f"Accuracy: {pronunciation_result['accuracy_score']:.1f}/100",
                f"Fluency: {pronunciation_result['fluency_score']:.1f}/100",
                f"Prosody: {pronunciation_result['prosody_score']:.1f}/100"
            ]
        }

    # STEP 5: Apply reading penalties
    if reading_analysis['is_likely_reading'] or reading_analysis['is_possibly_reading']:
        logger.warning(f"⚠️ STEP 5: Applying reading penalties (factor: {reading_analysis['penalty_factor']})")
        gpt_evaluation = _apply_reading_penalties(gpt_evaluation, reading_analysis)

    # STEP 6: Calculate final overall score
    # Weight distribution — research-calibrated for spoken proficiency:
    #   fluency    25%  (primary differentiator between CEFR bands)
    #   grammar    25%  (structural competence)
    #   vocabulary 20%  (range and precision)
    #   pronunciation 20%  (intelligibility)
    #   coherence  10%  (discourse organisation — hardest to measure from short samples)
    final_score = (
        gpt_evaluation['fluency']['score']       * 0.25 +
        gpt_evaluation['grammar']['score']       * 0.25 +
        gpt_evaluation['vocabulary']['score']    * 0.20 +
        gpt_evaluation['pronunciation']['score'] * 0.20 +
        gpt_evaluation['coherence']['score']     * 0.10
    )
    gpt_evaluation['overall_score'] = round(final_score, 1)

    # STEP 7: Determine CEFR level using bottleneck rule (industry standard)
    # Primary: lowest skill band governs the final level.
    # Secondary: composite score used as a tie-breaker sanity check.
    skill_scores = {
        'pronunciation': gpt_evaluation['pronunciation']['score'],
        'grammar':       gpt_evaluation['grammar']['score'],
        'vocabulary':    gpt_evaluation['vocabulary']['score'],
        'fluency':       gpt_evaluation['fluency']['score'],
        'coherence':     gpt_evaluation['coherence']['score'],
    }
    bottleneck_level = _skill_scores_to_cefr_level(skill_scores)
    composite_level  = _score_to_cefr_level(final_score)

    # Accept the bottleneck level unless composite suggests it's 2+ bands too harsh
    # (guards against extreme GPT scoring outliers on very short samples)
    btn_idx  = _CEFR_ORDER.index(bottleneck_level)
    comp_idx = _CEFR_ORDER.index(composite_level)
    if comp_idx - btn_idx >= 2:
        # Composite is much more generous — split the difference (move up 1 band)
        final_level = _CEFR_ORDER[btn_idx + 1]
        logger.info(
            f"[CEFR_LEVEL] Composite ({composite_level}) vs bottleneck ({bottleneck_level}) "
            f"gap ≥2 → using {final_level}"
        )
    else:
        final_level = bottleneck_level

    gpt_evaluation['recommended_level'] = final_level

    logger.info(
        f"✅ Final assessment: {final_level} "
        f"(composite={final_score:.1f}/100, bottleneck={bottleneck_level}, "
        f"composite_band={composite_level})"
    )

    # ── Short-sample warning injection ────────────────────────────────────────
    # Prepend the reliability warning so the learner sees it prominently in the
    # app's areas_for_improvement list.  This is purely additive — no field
    # is removed or renamed, so the mobile contract is unaffected.
    if _sample_warning:
        existing = gpt_evaluation.get("areas_for_improvement", [])
        if not isinstance(existing, list):
            existing = [str(existing)] if existing else []
        gpt_evaluation["areas_for_improvement"] = [_sample_warning] + existing
        logger.info(f"[SHORT_SAMPLE] Warning injected into areas_for_improvement")

    return gpt_evaluation


async def _strict_gpt4_evaluation(
    text: str,
    language: str,
    duration: int,
    prompt: Optional[str],
    reading_analysis: Dict
) -> Dict:
    """
    STRICT GPT-4 evaluation with realistic CEFR benchmarks

    This is MUCH harsher than the original prompt.
    """
    # ── CEFR benchmarks: 2020 Companion Volume + research-validated metrics ──
    # Key update from CEFR 2020: native-speaker norms are REMOVED.
    # The standard is COMMUNICATIVE EFFECTIVENESS / INTELLIGIBILITY — not
    # proximity to a native speaker.  Vocabulary sizes from Milton & Alexiou
    # (2009) research corpus; WPM from LINDSEI corpus (Huang & Gráf, 2025).
    cefr_strict_benchmarks = {
        "A1": {
            "standard": "CEFR 2020 Companion Volume A1",
            "communicative_standard": (
                "Can communicate basic personal information when the listener "
                "is cooperative and patient. Speech is understood despite a "
                "strong L1 accent."
            ),
            "grammar": (
                "Only isolated words and formulaic phrases. Present tense "
                "only; frequent errors expected even in basic structures."
            ),
            "vocabulary": (
                "Fewer than 1,500 word families. Survival basics: greetings, "
                "numbers, colours, family, simple objects."
            ),
            "fluency": (
                "Very slow (50-70 WPM), many pauses. Heavy L1 reliance. "
                "This rate is NORMAL for A1 — do NOT penalise it."
            ),
            "coherence": (
                "Isolated sentences; no linking devices beyond 'and'. "
                "No extended discourse expected."
            ),
            "minimum_words": 15,
            "max_errors_per_10_words": 4,
            "wpm_range": "50-70",
        },
        "A2": {
            "standard": "CEFR 2020 Companion Volume A2",
            "communicative_standard": (
                "Can handle simple routine exchanges on familiar topics. "
                "Intelligible to patient interlocutors familiar with L2 speakers."
            ),
            "grammar": (
                "Simple present and simple past; frequent tense and agreement errors. "
                "Compound sentences (and/but/because) attempted."
            ),
            "vocabulary": (
                "1,500-2,500 word families. Limited to concrete, familiar topics: "
                "family, shopping, local geography, daily routines."
            ),
            "fluency": (
                "Slow (70-90 WPM), frequent pauses. This rate is NORMAL for A2 — "
                "do NOT penalise it as reading. No fillers expected."
            ),
            "coherence": (
                "Short sequences of simple sentences. Basic connectors. "
                "Limited extended discourse."
            ),
            "minimum_words": 30,
            "max_errors_per_10_words": 3,
            "wpm_range": "70-90",
        },
        "B1": {
            "standard": "CEFR 2020 Companion Volume B1",
            "communicative_standard": (
                "Can maintain conversation on familiar topics and handle "
                "most travel/daily-life situations. Clearly intelligible."
            ),
            "grammar": (
                "Correct basic structures; noticeable errors in complex "
                "tenses, conditionals, and subordinate clauses."
            ),
            "vocabulary": (
                "2,750-3,250 word families. Can paraphrase when exact word "
                "is missing. Limited range in abstract topics."
            ),
            "fluency": (
                "Moderate pace (90-110 WPM). Pauses for planning; occasional "
                "reformulation. Some fillers (um, uh) present."
            ),
            "coherence": (
                "Connected discourse with simple connectors. Can narrate and "
                "describe with some detail."
            ),
            "minimum_words": 60,
            "max_errors_per_10_words": 2,
            "wpm_range": "90-110",
        },
        "B2": {
            "standard": "CEFR 2020 Companion Volume B2",
            "communicative_standard": (
                "Fluent and spontaneous enough for regular interaction with "
                "L2 speakers without strain for either party."
            ),
            "grammar": (
                "Good grammatical control. Occasional non-systematic errors. "
                "Complex sentence structures attempted and mostly correct."
            ),
            "vocabulary": (
                "3,250-3,750 word families. Good range across most topics. "
                "Uses synonyms and paraphrase effectively."
            ),
            "fluency": (
                "Generally smooth (~118 WPM average). Minor hesitations. "
                "Natural self-correction patterns present."
            ),
            "coherence": (
                "Clear, detailed discourse with appropriate connectors. "
                "Can develop arguments and opinions."
            ),
            "minimum_words": 80,
            "max_errors_per_10_words": 1,
            "wpm_range": "110-130",
        },
        "C1": {
            "standard": "CEFR 2020 Companion Volume C1",
            "communicative_standard": (
                "Expresses fluently and spontaneously without much obvious "
                "searching for expressions. Full prosodic control."
            ),
            "grammar": (
                "Consistent control including rare and complex structures. "
                "Errors are very rare and minor."
            ),
            "vocabulary": (
                "3,750-4,500 word families. Sophisticated, precise expressions. "
                "Uses idiomatic language naturally."
            ),
            "fluency": (
                "Smooth and flexible (~142 WPM average). High prosodic control: "
                "stress, rhythm, and intonation used to convey meaning."
            ),
            "coherence": (
                "Well-structured extended discourse. Cohesive devices used "
                "with high control."
            ),
            "minimum_words": 100,
            "max_errors_per_10_words": 0.5,
            "wpm_range": "130-160",
        },
        "C2": {
            "standard": "CEFR 2020 Companion Volume C2",
            "communicative_standard": (
                "Full range of phonological features with high control. "
                "Accent may be retained but never impedes communication."
            ),
            "grammar": (
                "Virtually error-free even in complex and unusual structures."
            ),
            "vocabulary": (
                "4,500-5,000+ word families. Full idiomatic, colloquial and "
                "specialised range."
            ),
            "fluency": (
                "Effortless, fully natural. Prosodic features used to convey "
                "subtle nuances of meaning."
            ),
            "coherence": (
                "Sophisticated, precisely tailored discourse structure."
            ),
            "minimum_words": 120,
            "max_errors_per_10_words": 0,
            "wpm_range": "140+",
        },
    }

    # Language-specific focus
    language_features = {
        "english": {
            "assessment_focus": "article usage, prepositions, verb tenses, word order",
            "phonetic_challenges": "th sounds, vowel differentiation, word stress, intonation"
        },
        "dutch": {
            "assessment_focus": "word order, verb placement, het/de articles, separable verbs",
            "phonetic_challenges": "g/ch sounds, ui/eu vowels, diphthongs, r-pronunciation"
        },
        "spanish": {
            "assessment_focus": "ser/estar usage, subjunctive mood, gender agreement",
            "phonetic_challenges": "r/rr sounds, b/v distinction, vowel clarity"
        },
        "german": {
            "assessment_focus": "case system, word order, verb position, separable verbs",
            "phonetic_challenges": "umlauts, ch sounds, r-pronunciation"
        },
        "french": {
            "assessment_focus": "gender agreement, verb conjugation, negation structure, liaison",
            "phonetic_challenges": "nasal vowels, r-pronunciation, vowel distinctions, liaison"
        },
        "portuguese": {
            "assessment_focus": "ser/estar usage, contractions, verb conjugation",
            "phonetic_challenges": "nasal vowels, s/z/ç sounds, open/closed vowels"
        }
    }

    lang_focus = language_features.get(language.lower(), language_features["english"])

    # Build reading detection context
    reading_context = ""
    if reading_analysis['is_likely_reading']:
        reading_context = f"""
🚨 CRITICAL ALERT - READING SUSPECTED:
The speech pattern analysis detected HIGH probability of reading from text:
- Spontaneity score: {reading_analysis['spontaneity_score']:.1f}/100
- Indicators: {', '.join(reading_analysis['indicators'])}

IMPORTANT: Be EXTRA HARSH on scores when reading is detected. Reading from text does NOT demonstrate language ability.
Penalize fluency and coherence scores heavily.
"""
    elif reading_analysis['is_possibly_reading']:
        reading_context = f"""
⚠️ WARNING - POSSIBLE READING:
Speech patterns show signs of rehearsed or read content:
- Indicators: {', '.join(reading_analysis['indicators'])}

Be more critical in your evaluation.
"""

    # Build prompt context
    prompt_context = ""
    if prompt and prompt.strip():
        prompt_context = f"""
TOPIC CONTEXT: "{prompt}"

Check if response addresses this topic appropriately.
Off-topic responses suggest reading from unrelated text.
"""

    # word_count and wpm must be calculated BEFORE system_prompt f-string
    # because the prompt embeds them directly.
    if not text or text.strip() == "":
        logger.warning("⚠️ Empty text provided")
        text = "No text provided for assessment"

    word_count = len(text.split())
    wpm_calculated = (word_count / duration * 60) if duration > 0 else 0
    logger.info(f"📊 Word count: {word_count}, Duration: {duration}s, WPM: {wpm_calculated:.0f}")

    # ── GPT-4.1 system prompt — CEFR 2020 Companion Volume standard ─────────
    # Critical change: native-speaker comparison is REMOVED per the 2020
    # update which explicitly eliminated native-speaker norms from all
    # CEFR descriptors.  The benchmark is COMMUNICATIVE EFFECTIVENESS.
    system_prompt = f"""
You are a certified CEFR language proficiency assessor for {language}, trained
to the CEFR 2020 Companion Volume standard.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOUNDATIONAL STANDARD (CEFR 2020 UPDATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The 2020 CEFR Companion Volume removed ALL native-speaker norms.
▸ DO NOT compare the learner to a native speaker.
▸ The benchmark is COMMUNICATIVE EFFECTIVENESS and INTELLIGIBILITY.
▸ A strong L1 accent does NOT lower the score if communication succeeds.
▸ A1/A2 speakers WILL speak slowly and without filler words — this is NORMAL,
  not a deficiency.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRADING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **ACCURACY** — Grade against the communicative standard for that level,
   not against a perfect or native-speaker ideal.
2. **VOCABULARY SIZE** — Use the research-validated word-family counts in the
   benchmarks below (NOT the old 500/1000/2000 splits).
3. **FLUENCY AT A1/A2** — Slow speech (50-90 WPM) is EXPECTED at A1/A2.
   Score fluency based on whether communication flows at level, not on pace.
4. **HESITATIONS** — At B1 and below, pauses for planning are NORMAL and
   should not dominate the fluency score.
5. **COHERENCE** — For short samples (< 60 words), coherence scoring is
   unreliable; weight it lightly and acknowledge the sample limitation.
6. **CONSERVATIVE** — When genuinely uncertain between two adjacent bands,
   select the lower one.  Most learners are A1-B1.

CEFR LEVEL BENCHMARKS (2020 standard + corpus-validated metrics):
{json.dumps(cefr_strict_benchmarks, indent=2)}

Language-specific assessment focus for {language}:
- Grammar markers: {lang_focus['assessment_focus']}
- Phonological challenges: {lang_focus['phonetic_challenges']}

{reading_context}
{prompt_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSESSMENT PROCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Count words; note WPM; compare to the wpm_range for candidate levels.
2. Count grammar errors; calculate errors per 10 words.
3. Estimate productive vocabulary range from word variety and topic range.
4. Assess fluency as discourse flow at the expected level.
5. Assess coherence as discourse organisation.
6. Identify the HIGHEST CEFR level where ALL skill criteria are met.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL SCORING RULE — READ THIS CAREFULLY 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALL scores (0-100) are ABSOLUTE across the FULL CEFR spectrum.
They are NOT relative to the detected level.
"Good for A1" does NOT mean 75/100. It means ~20-35/100 on the absolute scale.

ABSOLUTE SCORE ANCHORS — MUST FOLLOW EXACTLY:

| CEFR level | Score range | What it means                              |
|------------|-------------|---------------------------------------------|
| A1         | 10 – 35    | Only isolated words/memorised phrases       |
| A2         | 36 – 50    | Simple sentences on familiar topics         |
| B1         | 51 – 65    | Maintains conversation, noticeable errors   |
| B2         | 66 – 78    | Fluent with minor errors, abstract topics   |
| C1         | 79 – 90    | Sophisticated, near-effortless production   |
| C2         | 91 – 100   | Mastery, full prosodic and structural range |

EXAMPLES of absolute scoring:
▸ Speaker says 8 simple sentences, 41 WPM, no connectors, memorised intro:
  → fluency=25, grammar=30, vocabulary=20, coherence=20  (A1 range)
  → recommended_level="A1"
▸ Speaker uses past tense, asks questions, some errors but communicates:
  → fluency=48, grammar=44, vocabulary=42, coherence=40  (A2 range)
  → recommended_level="A2"
▸ DO NOT give a score of 75-80 and say "this is A1 level speech".
  A score of 75 means B2. If the speech is A1, the score must be in 10-35.

Based on {duration} seconds of speech ({word_count} words, ~{(word_count/duration*60) if duration > 0 else 0:.0f} WPM),
return a JSON assessment with ALL of these fields:

- recognized_text          (string — the transcribed speech)
- recommended_level        (string: A1/A2/B1/B2/C1/C2)
- overall_score            (number 0-100 — MUST match the score range for recommended_level)
- confidence               (number 0-100 — your confidence in the level assignment)
- pronunciation            (object: score 0-100, feedback string, examples array)
- grammar                  (object: score 0-100, feedback string, examples array)
- vocabulary               (object: score 0-100, feedback string, examples array)
- fluency                  (object: score 0-100, feedback string, examples array)
- coherence                (object: score 0-100, feedback string, examples array)
- strengths                (array of strings — at least 1, be specific)
- areas_for_improvement    (array of strings — concrete and actionable)
- next_steps               (array of strings — practical recommendations)

FINAL CHECK before responding:
  → Does your recommended_level match the score ranges in the table above?
  → If recommended_level=A1, ALL skill scores must be in the 10-35 range.
  → If recommended_level=A2, scores must be in the 36-50 range.
  → If any score is outside the range for your recommended level, CORRECT it.
"""

    # Create OpenAI client
    client = create_openai_client()

    # word_count and wpm_calculated already set above before system_prompt was built.

    # Call gpt-4.1 — superior instruction-following (87.4% IFEval vs 81% for gpt-4o)
    # and 1M context window for full transcripts. response_format json_object is
    # reliable on gpt-4.1 for chat completions (not the Assistants API).
    try:
        response = await client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Transcribed speech ({word_count} words in {duration}s, "
                        f"~{(word_count / duration * 60):.0f} WPM): \"{text}\""
                    )
                }
            ],
            temperature=0.05,  # Maximum consistency for assessment scoring
        )

        result = json.loads(response.choices[0].message.content)
        logger.info(f"✅ GPT-4 evaluation complete: {result.get('recommended_level', 'N/A')}")

        # Ensure examples are lists
        for skill in ['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence']:
            if skill in result and 'examples' in result[skill]:
                if isinstance(result[skill]['examples'], str):
                    result[skill]['examples'] = [result[skill]['examples']]
                elif result[skill]['examples'] is None:
                    result[skill]['examples'] = []

        # Ensure strengths, areas_for_improvement, next_steps are lists (not strings)
        for field in ['strengths', 'areas_for_improvement', 'next_steps']:
            if field in result:
                if isinstance(result[field], str):
                    # Convert string to single-item list
                    result[field] = [result[field]] if result[field].strip() else []
                elif result[field] is None:
                    result[field] = []
                elif not isinstance(result[field], list):
                    result[field] = [str(result[field])]

        return result

    except Exception as e:
        logger.error(f"❌ GPT-4 evaluation error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Conservative fallback
        return {
            "recognized_text": text,
            "recommended_level": "A2",  # Conservative default
            "overall_score": 40,
            "confidence": 30,
            "pronunciation": {"score": 40, "feedback": "Could not analyze pronunciation.", "examples": []},
            "grammar": {"score": 40, "feedback": "Could not analyze grammar.", "examples": []},
            "vocabulary": {"score": 40, "feedback": "Could not analyze vocabulary.", "examples": []},
            "fluency": {"score": 40, "feedback": "Could not analyze fluency.", "examples": []},
            "coherence": {"score": 40, "feedback": "Could not analyze coherence.", "examples": []},
            "strengths": ["Unable to determine strengths."],
            "areas_for_improvement": ["Please try again with a clearer recording."],
            "next_steps": ["Retry the speaking assessment."]
        }


def _apply_reading_penalties(evaluation: Dict, reading_analysis: Dict) -> Dict:
    """
    Apply penalties to scores when reading is detected

    Args:
        evaluation: GPT-4 evaluation result
        reading_analysis: Reading detection analysis

    Returns:
        Modified evaluation with penalties applied
    """
    penalty_factor = reading_analysis['penalty_factor']

    logger.warning(f"📉 Applying {(1-penalty_factor)*100:.0f}% penalty for reading detection")

    # Apply penalty to fluency and coherence (most affected by reading)
    evaluation['fluency']['score'] = round(evaluation['fluency']['score'] * penalty_factor, 1)
    evaluation['coherence']['score'] = round(evaluation['coherence']['score'] * penalty_factor, 1)

    # Lighter penalty to grammar and vocabulary
    evaluation['grammar']['score'] = round(evaluation['grammar']['score'] * (penalty_factor + 0.2), 1)
    evaluation['vocabulary']['score'] = round(evaluation['vocabulary']['score'] * (penalty_factor + 0.2), 1)

    # Add to areas for improvement
    if reading_analysis['is_likely_reading']:
        evaluation['areas_for_improvement'].insert(
            0,
            "Speech patterns suggest reading from text rather than spontaneous speaking. "
            "Practice speaking without notes to demonstrate true proficiency."
        )
    elif reading_analysis['is_possibly_reading']:
        evaluation['areas_for_improvement'].append(
            "Some speech patterns appear rehearsed. Try to speak more naturally and spontaneously."
        )

    return evaluation


def _score_to_cefr_level(score: float) -> str:
    """
    Convert a composite score to a CEFR band.

    Used ONLY as a secondary sanity-check signal alongside the bottleneck rule.
    Thresholds match the absolute score anchors enforced in the GPT prompt:
      A1 <36 | A2 36-50 | B1 51-65 | B2 66-78 | C1 79-90 | C2 91+
    """
    if score >= 91:
        return "C2"
    elif score >= 79:
        return "C1"
    elif score >= 66:
        return "B2"
    elif score >= 51:
        return "B1"
    elif score >= 36:
        return "A2"
    else:
        return "A1"


def _skill_score_to_cefr_band(score: float) -> str:
    """
    Map a single ABSOLUTE skill score (0-100) to its CEFR band.

    Calibrated to match the absolute score anchors enforced in the GPT prompt:
      A1  : 10–35   (isolated words / memorised phrases)
      A2  : 36–50   (simple sentences on familiar topics)
      B1  : 51–65   (maintains conversation, noticeable errors)
      B2  : 66–78   (fluent with minor errors)
      C1  : 79–90   (sophisticated, near-effortless)
      C2  : 91–100  (mastery)

    Mid-point boundaries used to avoid cliff-edge sensitivity:
      ≥91 → C2 | ≥79 → C1 | ≥66 → B2 | ≥51 → B1 | ≥36 → A2 | else A1
    """
    if score >= 91:
        return "C2"
    elif score >= 79:
        return "C1"
    elif score >= 66:
        return "B2"
    elif score >= 51:
        return "B1"
    elif score >= 36:
        return "A2"
    else:
        return "A1"


_CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _skill_scores_to_cefr_level(skill_scores: dict) -> str:
    """
    Determine the final CEFR level using the BOTTLENECK RULE.

    Industry standard (Cambridge, IELTS, Speechace):
    - Compute the individual CEFR band for every skill dimension.
    - The final level is the LOWEST band across all critical skills.
    - A learner cannot be B1 overall if their fluency is A1.

    Critical skills for spoken production: fluency, grammar, vocabulary, coherence.
    Pronunciation is considered separately (intelligibility gate, not bottleneck).

    Args:
        skill_scores: dict with keys pronunciation, grammar, vocabulary,
                      fluency, coherence — values are 0-100 scores.

    Returns:
        CEFR level string (e.g. "A2")
    """
    # Skills that act as bottlenecks for spoken proficiency
    _BOTTLENECK_SKILLS = ["fluency", "grammar", "vocabulary", "coherence"]

    # Map each bottleneck skill to its band
    bands = []
    for skill in _BOTTLENECK_SKILLS:
        score = skill_scores.get(skill, 50)
        bands.append(_skill_score_to_cefr_band(score))

    if not bands:
        return "A2"

    # Return the lowest (most limiting) band
    lowest_idx = min(_CEFR_ORDER.index(b) for b in bands)
    bottleneck_level = _CEFR_ORDER[lowest_idx]

    # Soft pronunciation gate: if pronunciation is more than 2 bands below
    # the bottleneck level, apply one-band downgrade (intelligibility failure)
    pron_score = skill_scores.get("pronunciation", 50)
    pron_band = _skill_score_to_cefr_band(pron_score)
    pron_idx = _CEFR_ORDER.index(pron_band)
    bottleneck_idx = _CEFR_ORDER.index(bottleneck_level)
    if bottleneck_idx - pron_idx >= 2:
        bottleneck_idx = max(0, bottleneck_idx - 1)
        bottleneck_level = _CEFR_ORDER[bottleneck_idx]
        logger.info(
            f"[CEFR_LEVEL] Pronunciation gate applied: "
            f"pron={pron_band} caused 1-band downgrade → {bottleneck_level}"
        )

    logger.info(
        f"[CEFR_LEVEL] Bottleneck rule: bands={dict(zip(_BOTTLENECK_SKILLS, bands))} "
        f"→ final={bottleneck_level}"
    )
    return bottleneck_level


# Keep the original function for backwards compatibility
async def evaluate_language_proficiency(
    text: str,
    language: str,
    duration: int = 60,
    prompt: str = None,
    audio_file_path: Optional[str] = None  # 🔥 NEW: Support audio file path
) -> Dict:
    """
    Backwards compatible wrapper - calls improved version

    Args:
        text: Transcribed speech
        language: Target language
        duration: Duration in seconds
        prompt: Optional prompt
        audio_file_path: Optional path to audio file for Azure pronunciation assessment

    Returns:
        Assessment result
    """
    return await evaluate_language_proficiency_improved(
        text=text,
        language=language,
        duration=duration,
        prompt=prompt,
        audio_file_path=audio_file_path  # 🔥 Pass through audio file path
    )


# Prompts generation (unchanged)
async def generate_speaking_prompts(language: str) -> Dict[str, List[str]]:
    """Generate speaking prompts for assessment in different languages"""

    default_prompts = {
        "general": [
            "Tell me about yourself and your language learning experience.",
            "Describe your hometown and what you like about it.",
            "What are your hobbies and interests?",
            "Talk about your favorite book, movie, or TV show.",
            "Describe your typical day."
        ],
        "travel": [
            "Describe a memorable trip you've taken.",
            "What's your favorite place to visit and why?",
            "Talk about a place you would like to visit in the future.",
            "Describe your ideal vacation.",
            "What do you usually do when you travel?"
        ],
        "education": [
            "Talk about your educational background.",
            "Describe a teacher who influenced you.",
            "What subjects did you enjoy studying?",
            "How do you think education has changed in recent years?",
            "Describe your learning style."
        ]
    }

    client = create_openai_client()

    if language.lower() == "english":
        return default_prompts

    try:
        language_map = {
            "english": "en",
            "dutch": "nl",
            "spanish": "es",
            "german": "de",
            "french": "fr",
            "portuguese": "pt"
        }
        target_lang = language_map.get(language.lower(), "en")

        system_prompt = f"""
        You are a professional translator. Translate the following prompts from English to {language}.
        Maintain the meaning and tone, but make any cultural adaptations necessary.
        Return the translations in JSON format with the same structure as the input.
        """

        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate these prompts to {language}: {json.dumps(default_prompts)}"}
            ],
            temperature=0.1
        )

        translated_prompts = json.loads(response.choices[0].message.content)
        logger.info(f"✅ Prompts translated to {language}")
        return translated_prompts

    except Exception as e:
        logger.error(f"❌ Error translating prompts: {e}")
        return default_prompts
