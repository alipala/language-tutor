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
    logger.info(f"📝 Text: '{text[:100]}...' ({len(text.split())} words in {duration}s)")

    # STEP 1: Detect if user is reading from text
    logger.info("🔍 STEP 1: Reading detection...")
    reading_analysis = reading_detector.detect_reading_patterns(
        transcript=text,
        audio_duration=duration,
        language=language,
        prompt=prompt
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
    final_score = (
        gpt_evaluation['pronunciation']['score'] * 0.25 +
        gpt_evaluation['grammar']['score'] * 0.20 +
        gpt_evaluation['vocabulary']['score'] * 0.20 +
        gpt_evaluation['fluency']['score'] * 0.20 +
        gpt_evaluation['coherence']['score'] * 0.15
    )
    gpt_evaluation['overall_score'] = round(final_score, 1)

    # Adjust CEFR level based on final score
    gpt_evaluation['recommended_level'] = _score_to_cefr_level(final_score)

    logger.info(f"✅ Final assessment: {gpt_evaluation['recommended_level']} ({final_score:.1f}/100)")

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
    # CEFR level STRICT descriptions
    cefr_strict_benchmarks = {
        "A1": {
            "description": "Absolute beginner - can only use memorized phrases",
            "grammar": "Constant errors even in present tense, no verb conjugation",
            "vocabulary": "< 500 words, only survival basics",
            "fluency": "Long pauses every few words, heavy dependence on first language",
            "minimum_words": 15,
            "max_errors_per_10_words": 4
        },
        "A2": {
            "description": "Elementary - can handle simple exchanges",
            "grammar": "Basic structures only, frequent errors in past tense",
            "vocabulary": "500-1000 words, limited to concrete topics",
            "fluency": "Frequent pauses, slow speech, simple sentences only",
            "minimum_words": 30,
            "max_errors_per_10_words": 3
        },
        "B1": {
            "description": "Intermediate - can maintain conversation on familiar topics",
            "grammar": "Some complex structures, but still noticeable errors",
            "vocabulary": "1000-2000 words, some ability to paraphrase",
            "fluency": "Noticeable pauses for planning, occasional reformulation",
            "minimum_words": 60,
            "max_errors_per_10_words": 2
        },
        "B2": {
            "description": "Upper intermediate - fairly fluent with occasional errors",
            "grammar": "Good control, rare systematic errors",
            "vocabulary": "2000-4000 words, good range for most topics",
            "fluency": "Generally smooth with minor hesitations",
            "minimum_words": 80,
            "max_errors_per_10_words": 1
        },
        "C1": {
            "description": "Advanced - near-native fluency",
            "grammar": "Consistent control, errors are very rare and minor",
            "vocabulary": "4000+ words, sophisticated expressions",
            "fluency": "Smooth and effortless, native-like pace",
            "minimum_words": 100,
            "max_errors_per_10_words": 0.5
        },
        "C2": {
            "description": "Mastery - indistinguishable from educated native speaker",
            "grammar": "Perfect control even in complex situations",
            "vocabulary": "6000+ words, including idioms and cultural references",
            "fluency": "Completely natural and effortless",
            "minimum_words": 120,
            "max_errors_per_10_words": 0
        }
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

    # SUPER STRICT system prompt
    system_prompt = f"""
You are an EXTREMELY STRICT CEFR language proficiency assessor for {language}.

🚨 CRITICAL GRADING RULES - READ CAREFULLY:

1. **BE HARSH**: Most learners are A1-B1, not B2-C1. Default to LOWER levels.
2. **ANY basic grammar error = maximum B1** (e.g., wrong verb tense, agreement errors)
3. **Limited vocabulary = maximum A2** (repetitive words, simple vocabulary only)
4. **Hesitations/pauses = lower fluency score significantly**
5. **Compare to NATIVE SPEAKERS**, not just "understandable"
6. **When in doubt, score LOWER**

STRICT CEFR BENCHMARKS:
{json.dumps(cefr_strict_benchmarks, indent=2)}

Language-specific focus for {language}:
- Grammar focus: {lang_focus['assessment_focus']}
- Pronunciation challenges: {lang_focus['phonetic_challenges']}

{reading_context}
{prompt_context}

ASSESSMENT PROCESS:
1. Count words and errors meticulously
2. Calculate error rate per 10 words
3. Check against STRICT benchmarks above
4. Identify specific grammatical/lexical mistakes
5. Be CRITICAL - err on the side of LOWER scores

SCORING GUIDELINES (0-100):
- 90-100: Near-perfect, rare for non-natives
- 75-89: Good with minor issues
- 60-74: Acceptable with noticeable errors
- 45-59: Significant problems
- 30-44: Major difficulties
- 0-29: Minimal ability

Based on {duration} seconds of speech, provide a STRICT assessment in JSON format:
- recognized_text
- recommended_level (be conservative - lower is more likely correct)
- overall_score (be harsh)
- confidence (0-100)
- pronunciation, grammar, vocabulary, fluency, coherence (each with score, feedback, examples)
- strengths (be honest - may be none)
- areas_for_improvement (be specific and direct)
- next_steps (concrete recommendations)

Remember: Better to under-assess than over-assess. Most learners are NOT B2-C1.
"""

    # Create OpenAI client
    client = create_openai_client()

    # Validate input
    if not text or text.strip() == "":
        logger.warning("⚠️ Empty text provided")
        text = "No text provided for assessment"

    word_count = len(text.split())
    logger.info(f"📊 Word count: {word_count}, Duration: {duration}s, WPM: {(word_count/duration)*60:.0f}")

    # Call GPT-4o with strict prompt
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcribed speech ({word_count} words in {duration}s): \"{text}\""}
            ],
            temperature=0.05  # Even lower for maximum consistency and strictness
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
    Convert numerical score to CEFR level (STRICT thresholds)

    Args:
        score: Overall score (0-100)

    Returns:
        CEFR level string
    """
    if score >= 95:
        return "C2"
    elif score >= 85:
        return "C1"
    elif score >= 72:
        return "B2"
    elif score >= 58:
        return "B1"
    elif score >= 42:
        return "A2"
    else:
        return "A1"


# Keep the original function for backwards compatibility
async def evaluate_language_proficiency(
    text: str,
    language: str,
    duration: int = 60,
    prompt: str = None
) -> Dict:
    """
    Backwards compatible wrapper - calls improved version

    Args:
        text: Transcribed speech
        language: Target language
        duration: Duration in seconds
        prompt: Optional prompt

    Returns:
        Assessment result
    """
    return await evaluate_language_proficiency_improved(
        text=text,
        language=language,
        duration=duration,
        prompt=prompt,
        audio_file_path=None  # No audio file in old API
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
