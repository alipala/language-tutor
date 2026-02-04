"""
Pronunciation Assessment Service using Azure Speech SDK
========================================================

Provides phoneme-level pronunciation accuracy scoring for language learners.
Uses Azure Cognitive Services Speech SDK for accurate pronunciation assessment.

Features:
- Phoneme-level accuracy scoring
- Prosody analysis (stress, intonation)
- Language-specific pronunciation rules
- Detailed feedback on pronunciation quality

Author: Language Tutor AI
"""

import os
import logging
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logging.warning("Azure Speech SDK not available. Pronunciation assessment will be limited.")

load_dotenv()

logger = logging.getLogger(__name__)


class PronunciationAssessmentService:
    """
    Service for assessing pronunciation quality using Azure Speech SDK
    """

    def __init__(self):
        """Initialize the pronunciation assessment service"""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not self.speech_key or not self.speech_region:
            logger.warning(
                "Azure Speech credentials not found. "
                "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in .env"
            )
            self.enabled = False
        else:
            self.enabled = AZURE_AVAILABLE
            if self.enabled:
                logger.info(f"✅ Azure Pronunciation Assessment enabled (Region: {self.speech_region})")

    def _get_language_code(self, language: str) -> str:
        """
        Convert language name to Azure locale code

        Args:
            language: Language name (e.g., 'french', 'spanish')

        Returns:
            Azure locale code (e.g., 'fr-FR', 'es-ES')
        """
        language_map = {
            'english': 'en-US',
            'french': 'fr-FR',
            'spanish': 'es-ES',
            'german': 'de-DE',
            'dutch': 'nl-NL',
            'portuguese': 'pt-PT',
        }

        return language_map.get(language.lower(), 'en-US')

    async def assess_pronunciation(
        self,
        audio_file_path: str,
        reference_text: str,
        language: str
    ) -> Dict:
        """
        Assess pronunciation quality from audio file

        Args:
            audio_file_path: Path to audio file (WAV format recommended)
            reference_text: Expected text that should be spoken
            language: Target language for assessment

        Returns:
            Dictionary containing:
            - pronunciation_score: Overall pronunciation accuracy (0-100)
            - accuracy_score: Phoneme-level accuracy (0-100)
            - fluency_score: Speaking fluency (0-100)
            - completeness_score: How much of reference text was spoken (0-100)
            - prosody_score: Intonation and stress patterns (0-100)
            - word_scores: List of per-word pronunciation scores
            - feedback: Human-readable feedback
            - confidence: Confidence in the assessment (0-100)
        """
        if not self.enabled:
            logger.warning("Pronunciation assessment disabled - returning estimated scores")
            return self._fallback_assessment(reference_text)

        try:
            # Configure speech service
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )

            # Set language
            locale = self._get_language_code(language)
            speech_config.speech_recognition_language = locale

            # Configure audio input
            audio_config = speechsdk.AudioConfig(filename=audio_file_path)

            # Configure pronunciation assessment
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True
            )

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            # Apply pronunciation assessment configuration
            pronunciation_config.apply_to(speech_recognizer)

            # Perform recognition
            logger.info(f"🎤 Assessing pronunciation for {language}...")
            result = speech_recognizer.recognize_once()

            # Check result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info("✅ Speech recognized successfully")
                return self._parse_pronunciation_result(result, language)

            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("⚠️ No speech recognized in audio")
                return self._create_low_score_result(
                    "No clear speech detected in the audio. Please speak more clearly."
                )

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"❌ Recognition canceled: {cancellation.reason}")
                if cancellation.error_details:
                    logger.error(f"Error details: {cancellation.error_details}")

                return self._fallback_assessment(reference_text)

            else:
                logger.warning(f"⚠️ Unexpected result reason: {result.reason}")
                return self._fallback_assessment(reference_text)

        except Exception as e:
            logger.error(f"❌ Error in pronunciation assessment: {str(e)}")
            return self._fallback_assessment(reference_text)

    def _parse_pronunciation_result(
        self,
        result: 'speechsdk.SpeechRecognitionResult',
        language: str
    ) -> Dict:
        """
        Parse Azure pronunciation assessment result

        Args:
            result: Azure speech recognition result
            language: Target language

        Returns:
            Structured pronunciation assessment dictionary
        """
        try:
            # Get pronunciation assessment result
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

            # Extract scores with null safety
            pronunciation_score = pronunciation_result.pronunciation_score or 0
            accuracy_score = pronunciation_result.accuracy_score or 0
            fluency_score = pronunciation_result.fluency_score or 0
            completeness_score = pronunciation_result.completeness_score or 0

            # Prosody score (available in some SDK versions)
            try:
                prosody_score = pronunciation_result.prosody_score
                if prosody_score is None:
                    prosody_score = (pronunciation_score + fluency_score) / 2
            except AttributeError:
                prosody_score = (pronunciation_score + fluency_score) / 2

            # Get word-level scores
            word_scores = []
            try:
                for word in result.properties.get("PRONUNCIATION_ASSESSMENT_WORD_DETAILS", []):
                    word_scores.append({
                        'word': word.get('Word', ''),
                        'accuracy_score': word.get('AccuracyScore', 0),
                        'error_type': word.get('ErrorType', 'None')
                    })
            except Exception as e:
                logger.warning(f"Could not extract word details: {e}")

            # Generate feedback
            feedback = self._generate_feedback(
                pronunciation_score,
                accuracy_score,
                fluency_score,
                completeness_score,
                prosody_score,
                language
            )

            # Calculate confidence (how reliable is this assessment)
            # Use completeness and fluency if available, otherwise use pronunciation score
            if completeness_score > 0 and fluency_score > 0:
                confidence = min(100, (completeness_score + fluency_score) / 2)
            elif pronunciation_score > 0:
                confidence = pronunciation_score
            else:
                confidence = 50  # Default moderate confidence

            logger.info(f"📊 Pronunciation scores - Overall: {pronunciation_score:.1f}, "
                       f"Accuracy: {accuracy_score:.1f}, Fluency: {fluency_score:.1f}")

            return {
                'pronunciation_score': round(pronunciation_score, 1),
                'accuracy_score': round(accuracy_score, 1),
                'fluency_score': round(fluency_score, 1),
                'completeness_score': round(completeness_score, 1),
                'prosody_score': round(prosody_score, 1),
                'word_scores': word_scores,
                'feedback': feedback,
                'confidence': round(confidence, 1),
                'recognized_text': result.text,
                'assessment_method': 'azure_phoneme'
            }

        except Exception as e:
            logger.error(f"Error parsing pronunciation result: {e}")
            return self._fallback_assessment("")

    def _generate_feedback(
        self,
        pronunciation_score: float,
        accuracy_score: float,
        fluency_score: float,
        completeness_score: float,
        prosody_score: float,
        language: str
    ) -> str:
        """
        Generate human-readable feedback based on scores

        Args:
            pronunciation_score: Overall pronunciation score
            accuracy_score: Phoneme accuracy score
            fluency_score: Speaking fluency score
            completeness_score: Text completeness score
            prosody_score: Prosody score
            language: Target language

        Returns:
            Human-readable feedback string
        """
        feedback_parts = []

        # Overall assessment
        if pronunciation_score >= 90:
            feedback_parts.append("Excellent pronunciation! Your speech is very clear and natural.")
        elif pronunciation_score >= 75:
            feedback_parts.append("Good pronunciation overall with room for improvement.")
        elif pronunciation_score >= 60:
            feedback_parts.append("Your pronunciation is understandable but needs practice.")
        else:
            feedback_parts.append("Pronunciation needs significant improvement. Focus on clarity.")

        # Specific feedback
        if accuracy_score < 70:
            feedback_parts.append(f"Work on pronouncing {language} sounds more accurately.")

        if fluency_score < 70:
            feedback_parts.append("Try to speak more smoothly without long pauses.")

        if completeness_score < 80:
            feedback_parts.append("Make sure to complete your sentences fully.")

        if prosody_score < 70:
            feedback_parts.append("Pay attention to intonation and stress patterns.")

        return " ".join(feedback_parts)

    def _create_low_score_result(self, feedback: str) -> Dict:
        """
        Create a low-score result when pronunciation is poor or unclear

        Args:
            feedback: Reason for low score

        Returns:
            Low-score pronunciation assessment result
        """
        return {
            'pronunciation_score': 30.0,
            'accuracy_score': 30.0,
            'fluency_score': 40.0,
            'completeness_score': 20.0,
            'prosody_score': 35.0,
            'word_scores': [],
            'feedback': feedback,
            'confidence': 50.0,
            'recognized_text': '',
            'assessment_method': 'azure_phoneme'
        }

    def _fallback_assessment(self, reference_text: str) -> Dict:
        """
        Fallback assessment when Azure is unavailable
        Provides conservative estimates based on text length

        Args:
            reference_text: Reference text

        Returns:
            Estimated pronunciation assessment
        """
        word_count = len(reference_text.split())

        # Conservative scores (slightly below average)
        base_score = 55.0

        # Adjust based on text length (longer = more reliable)
        length_bonus = min(10, word_count / 2)

        estimated_score = base_score + length_bonus

        return {
            'pronunciation_score': round(estimated_score, 1),
            'accuracy_score': round(estimated_score - 5, 1),
            'fluency_score': round(estimated_score, 1),
            'completeness_score': round(estimated_score + 5, 1),
            'prosody_score': round(estimated_score, 1),
            'word_scores': [],
            'feedback': (
                "Pronunciation score is estimated (Azure assessment unavailable). "
                "For accurate phoneme-level feedback, ensure Azure Speech credentials are configured."
            ),
            'confidence': 40.0,
            'recognized_text': reference_text,
            'assessment_method': 'estimated'
        }


# Create singleton instance
pronunciation_service = PronunciationAssessmentService()
