"""
Reading Detection Service
=========================

Detects if a user is reading from text vs speaking spontaneously.
Analyzes speech patterns to identify unnatural reading behavior.

Detection Methods:
1. Speaking rate analysis (too fast/consistent = reading)
2. Pause pattern analysis (even pauses = reading)
3. Filler word detection (no fillers = likely reading)
4. Grammar perfection detection (too perfect = reading)
5. Content relevance check (off-topic = reading from book)

Author: Language Tutor AI
"""

import logging
import re
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ReadingDetectionService:
    """
    Service for detecting if user is reading from text vs speaking spontaneously
    """

    # Filler words by language
    FILLER_WORDS = {
        'english': ['um', 'uh', 'like', 'you know', 'i mean', 'well', 'so'],
        'french': ['euh', 'ben', 'alors', 'donc', 'enfin', 'voilà', 'quoi'],
        'spanish': ['este', 'pues', 'bueno', 'entonces', 'o sea', 'eh'],
        'german': ['äh', 'ähm', 'also', 'na ja', 'halt', 'sozusagen'],
        'dutch': ['eh', 'nou', 'dus', 'zeg maar', 'gewoon', 'eigenlijk'],
        'portuguese': ['né', 'tipo', 'então', 'pois', 'ahn', 'eh'],
    }

    # Self-correction patterns
    CORRECTION_PATTERNS = [
        r'\b(no|wait|i mean|rather|actually)\b',  # English
        r'\b(non|attends|je veux dire|plutôt)\b',  # French
        r'\b(no|espera|quiero decir|mejor dicho)\b',  # Spanish
        r'\b(nein|warte|ich meine|vielmehr)\b',  # German
        r'\b(nee|wacht|ik bedoel|liever)\b',  # Dutch
        r'\b(não|espera|quero dizer|melhor dizendo)\b',  # Portuguese
    ]

    def __init__(self):
        """Initialize reading detection service"""
        logger.info("✅ Reading Detection Service initialized")

    def detect_reading_patterns(
        self,
        transcript: str,
        audio_duration: int,
        language: str,
        prompt: Optional[str] = None,
        estimated_cefr_level: Optional[str] = None,
    ) -> Dict:
        """
        Analyze speech to detect if user is reading vs speaking spontaneously

        Args:
            transcript: Transcribed speech text
            audio_duration: Duration in seconds
            language: Target language
            prompt: Optional prompt that was given to user
            estimated_cefr_level: Optional CEFR level hint (A1/A2/B1/B2/C1/C2).
                When provided, suppresses reading signals that are normal for that
                level (e.g. slow WPM and no fillers are normal at A1/A2).

        Returns:
            Dictionary containing:
            - is_likely_reading: Boolean indicating if reading is detected
            - confidence: Confidence level (0-100)
            - indicators: List of detected reading indicators
            - spontaneity_score: How spontaneous the speech sounds (0-100)
            - penalty_factor: Multiplier to apply to scores (0.6-1.0)
        """
        indicators = []
        confidence_points = 0

        # Normalise level for comparison
        _level = (estimated_cefr_level or "").upper().strip()
        _is_beginner = _level in ("A1", "A2")

        # 1. Speaking rate analysis
        rate_indicator, rate_confidence = self._analyze_speaking_rate(
            transcript, audio_duration, estimated_cefr_level=_level
        )
        if rate_indicator:
            indicators.append(rate_indicator)
            confidence_points += rate_confidence

        # 2. Filler word detection
        # A1/A2 learners legitimately produce zero fillers — suppress this signal
        # for beginners to avoid false reading penalties.
        if not _is_beginner:
            filler_indicator, filler_confidence = self._analyze_filler_words(
                transcript, language, audio_duration
            )
            if filler_indicator:
                indicators.append(filler_indicator)
                confidence_points += filler_confidence

        # 3. Self-correction detection
        # A1/A2 learners rarely self-correct (limited meta-linguistic awareness)
        # — only apply this signal at B1+ levels.
        if not _is_beginner:
            correction_indicator, correction_confidence = self._analyze_self_corrections(
                transcript
            )
            if correction_indicator:
                indicators.append(correction_indicator)
                confidence_points += correction_confidence

        # 4. Grammar perfection check
        grammar_indicator, grammar_confidence = self._analyze_grammar_perfection(
            transcript
        )
        if grammar_indicator:
            indicators.append(grammar_indicator)
            confidence_points += grammar_confidence

        # 5. Content relevance (if prompt provided)
        if prompt:
            relevance_indicator, relevance_confidence = self._analyze_content_relevance(
                transcript, prompt
            )
            if relevance_indicator:
                indicators.append(relevance_indicator)
                confidence_points += relevance_confidence

        # Calculate overall scores
        max_confidence = 100
        confidence = min(100, confidence_points)

        # Determine if likely reading
        is_likely_reading = confidence >= 60
        is_possibly_reading = confidence >= 40

        # Calculate spontaneity score (inverse of reading confidence)
        spontaneity_score = 100 - confidence

        # Calculate penalty factor (how much to reduce scores)
        if is_likely_reading:
            penalty_factor = 0.6  # 40% penalty
            severity = "high"
        elif is_possibly_reading:
            penalty_factor = 0.8  # 20% penalty
            severity = "moderate"
        else:
            penalty_factor = 1.0  # No penalty
            severity = "low"

        result = {
            'is_likely_reading': is_likely_reading,
            'is_possibly_reading': is_possibly_reading,
            'confidence': round(confidence, 1),
            'spontaneity_score': round(spontaneity_score, 1),
            'indicators': indicators,
            'penalty_factor': penalty_factor,
            'severity': severity
        }

        if indicators:
            logger.warning(f"⚠️ Reading patterns detected ({severity} severity, {confidence:.1f}% confidence)")
            for indicator in indicators:
                logger.warning(f"  - {indicator}")
        else:
            logger.info("✅ Speech appears spontaneous")

        return result

    def _analyze_speaking_rate(
        self,
        transcript: str,
        duration: int,
        estimated_cefr_level: str = "",
    ) -> Tuple[Optional[str], int]:
        """
        Analyze speaking rate to detect reading.

        Research-calibrated thresholds (LINDSEI corpus + CEFR trajectory):
          A1: 50-70 WPM  (genuinely slow — NOT reading)
          A2: 70-90 WPM
          B1: 90-110 WPM
          B2: ~118 WPM
          C1: ~142 WPM
          Native: 106-265 WPM (highly variable)

        Reading detection thresholds:
          > 200 WPM  → very fast reading aloud (high confidence)
          < 40 WPM with > 40 words → unnaturally slow even for A1 (moderate)
          Note: the old 60 WPM threshold falsely flagged genuine A1/A2 speakers.

        The estimated_cefr_level adds a further gate: if the level is A1/A2,
        even rates as low as 45 WPM are within normal range and are not flagged.

        Args:
            transcript: Speech text
            duration: Duration in seconds
            estimated_cefr_level: Optional CEFR level hint

        Returns:
            Tuple of (indicator message or None, confidence points)
        """
        if duration == 0:
            return None, 0

        word_count = len(transcript.split())
        words_per_minute = (word_count / duration) * 60

        # Fast reading aloud — strong signal at any level
        if words_per_minute > 200:
            return (
                f"Very fast speaking rate ({words_per_minute:.0f} WPM) suggests reading aloud",
                30,
            )

        # Slow reading threshold — lowered from 60 → 40 WPM
        # A1/A2 genuine speech sits at 50-90 WPM; only flag truly crawling pace
        _level = estimated_cefr_level.upper()
        _slow_floor = 45 if _level in ("A1", "A2") else 40

        if words_per_minute < _slow_floor and word_count > 40:
            return (
                f"Unusually slow speaking rate ({words_per_minute:.0f} WPM) "
                f"may indicate reading carefully",
                15,  # reduced confidence — less certain at this threshold
            )

        return None, 0

    def _analyze_filler_words(
        self,
        transcript: str,
        language: str,
        duration: int
    ) -> Tuple[Optional[str], int]:
        """
        Detect absence of filler words (indicates reading)

        Spontaneous speech includes fillers like "um", "uh", "like"
        Reading from text rarely includes these

        Args:
            transcript: Speech text
            language: Target language
            duration: Duration in seconds

        Returns:
            Tuple of (indicator message or None, confidence points)
        """
        fillers = self.FILLER_WORDS.get(language.lower(), self.FILLER_WORDS['english'])

        # Count filler words
        transcript_lower = transcript.lower()
        filler_count = sum(
            transcript_lower.count(f" {filler} ") + transcript_lower.count(f"{filler} ")
            for filler in fillers
        )

        word_count = len(transcript.split())
        filler_ratio = filler_count / max(word_count, 1)

        # Natural speech has 2-5% filler words
        # Zero fillers in >30 words = suspicious
        if filler_count == 0 and word_count > 30:
            return (
                "No filler words detected in extended speech (unnatural for spontaneous speaking)",
                25
            )

        # Very low filler rate
        if filler_ratio < 0.01 and word_count > 50:
            return (
                "Very low filler word rate suggests rehearsed or read speech",
                15
            )

        return None, 0

    def _analyze_self_corrections(
        self,
        transcript: str
    ) -> Tuple[Optional[str], int]:
        """
        Detect absence of self-corrections (indicates reading)

        Spontaneous speech includes false starts, corrections, restarts
        Reading from text does not

        Args:
            transcript: Speech text

        Returns:
            Tuple of (indicator message or None, confidence points)
        """
        transcript_lower = transcript.lower()
        word_count = len(transcript.split())

        # Check for correction patterns
        has_corrections = any(
            re.search(pattern, transcript_lower)
            for pattern in self.CORRECTION_PATTERNS
        )

        # Check for repetitions (another spontaneity indicator)
        words = transcript_lower.split()
        repetitions = sum(
            1 for i in range(len(words) - 1)
            if words[i] == words[i + 1] and len(words[i]) > 2
        )

        # If long speech with no corrections or repetitions = likely reading
        if word_count > 50 and not has_corrections and repetitions == 0:
            return (
                "No self-corrections or restarts in extended speech (typical of reading)",
                20
            )

        return None, 0

    def _analyze_grammar_perfection(
        self,
        transcript: str
    ) -> Tuple[Optional[str], int]:
        """
        Detect unnaturally perfect grammar (indicates reading)

        Spontaneous speech has grammatical errors, incomplete sentences
        Written text read aloud is grammatically perfect

        Args:
            transcript: Speech text

        Returns:
            Tuple of (indicator message or None, confidence points)
        """
        # Check for overly perfect sentence structure
        sentences = [s.strip() for s in transcript.split('.') if s.strip()]

        if len(sentences) < 2:
            return None, 0

        # Perfect punctuation is suspicious in transcription
        # Most STT doesn't add perfect punctuation from spoken audio
        perfect_capitalization = all(
            s[0].isupper() if s else False
            for s in sentences
        )

        # Check for formal/literary language patterns
        formal_indicators = [
            'therefore', 'furthermore', 'consequently', 'moreover', 'nevertheless',
            'en outre', 'par conséquent', 'néanmoins',  # French
            'por lo tanto', 'sin embargo', 'además',  # Spanish
        ]

        formal_count = sum(
            1 for indicator in formal_indicators
            if indicator in transcript.lower()
        )

        if perfect_capitalization and len(sentences) > 3:
            return (
                "Unnaturally perfect sentence structure and punctuation (suggests written text)",
                15
            )

        if formal_count >= 2:
            return (
                "Formal/literary language patterns suggest reading from written text",
                15
            )

        return None, 0

    def _analyze_content_relevance(
        self,
        transcript: str,
        prompt: str
    ) -> Tuple[Optional[str], int]:
        """
        Check if response matches the given prompt

        If prompt asks about daily routine but response discusses history,
        user is likely reading from a textbook

        Args:
            transcript: Speech text
            prompt: Given prompt/question

        Returns:
            Tuple of (indicator message or None, confidence points)
        """
        # Extract key themes from prompt
        prompt_lower = prompt.lower()
        transcript_lower = transcript.lower()

        # Define topic keywords
        topics = {
            'personal': ['you', 'your', 'my', 'i', 'me', 'toi', 'tu', 'je', 'moi'],
            'daily': ['day', 'morning', 'evening', 'routine', 'daily', 'jour', 'matin'],
            'travel': ['travel', 'trip', 'visit', 'vacation', 'voyage', 'viaje'],
            'food': ['food', 'eat', 'meal', 'restaurant', 'nourriture', 'comida'],
            'work': ['work', 'job', 'office', 'travail', 'trabajo'],
            'history': ['history', 'historical', 'century', 'histoire', 'historia'],
            'academic': ['research', 'study', 'university', 'recherche', 'investigación'],
        }

        # Check if response is wildly off-topic
        # (This is a simplified check - could be more sophisticated)
        if 'daily' in prompt_lower or 'routine' in prompt_lower:
            # If prompt asks about daily routine but response is academic/historical
            if any(word in transcript_lower for word in topics['history']) or \
               any(word in transcript_lower for word in topics['academic']):
                if not any(word in transcript_lower for word in topics['daily']):
                    return (
                        "Response content does not match given prompt (suggests reading from unrelated text)",
                        25
                    )

        return None, 0


# Create singleton instance
reading_detector = ReadingDetectionService()
