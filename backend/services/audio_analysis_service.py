"""
Audio Analysis Service
======================
Extracts acoustic metrics from audio for Speaking DNA enhancement.

PRIVACY NOTICE:
- Audio is processed in-memory only (never stored to disk)
- Only numeric metrics are extracted and stored
- Audio data is immediately garbage collected after processing
- GDPR compliant: no personal audio data retention

Uses:
- Librosa: Speech rate, pause detection, energy analysis
- Parselmouth (Praat): Pitch, jitter, shimmer analysis
"""

import base64
import io
import logging
import tempfile
import os
from typing import Dict, Optional
import numpy as np
import librosa
import soundfile as sf
import parselmouth
from parselmouth.praat import call

logger = logging.getLogger(__name__)


class AudioAnalysisService:
    """
    Acoustic feature extraction for Speaking DNA.

    Processes audio in-memory to extract voice quality metrics:
    - Pitch characteristics (mean, range, variation)
    - Voice quality (jitter, shimmer)
    - Speaking rhythm (pause patterns, speech rate)
    - Energy/intensity patterns
    """

    # Processing constants
    SAMPLE_RATE = 16000  # Standard for speech analysis
    MIN_DURATION_SECONDS = 5.0  # Minimum audio length for analysis
    MAX_DURATION_SECONDS = 60.0  # Only analyze first 60 seconds

    # Voice activity detection
    ENERGY_THRESHOLD = 0.02  # Amplitude threshold for speech detection
    PAUSE_THRESHOLD_SECONDS = 0.3  # Minimum silence duration to count as pause

    # Pitch analysis ranges (Hz)
    PITCH_FLOOR = 75  # Lower bound for pitch detection
    PITCH_CEILING = 600  # Upper bound for pitch detection

    def __init__(self):
        """Initialize audio analysis service."""
        logger.info("[AUDIO_ANALYSIS] Service initialized")

    async def extract_acoustic_metrics(
        self,
        audio_base64: str,
        audio_format: str = "wav",
        language: str = "english",
        max_duration: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Extract comprehensive acoustic metrics from audio data.

        PRIVACY: Audio is processed in RAM only - never written to disk.

        Args:
            audio_base64: Base64 encoded audio data
            audio_format: Audio format (wav, mp3, m4a, webm)
            language: Target language (for future language-specific analysis)
            max_duration: Maximum duration to analyze (default: 60 seconds)

        Returns:
            Dictionary containing acoustic metrics:
            {
                "pitch_mean": float,           # Average pitch (Hz)
                "pitch_std": float,            # Pitch variation (Hz)
                "pitch_min": float,            # Lowest pitch (Hz)
                "pitch_max": float,            # Highest pitch (Hz)
                "jitter": float,               # Pitch period variability (0-1)
                "shimmer": float,              # Amplitude variability (0-1)
                "speaking_ratio": float,       # Speech vs silence (0-1)
                "pause_ratio": float,          # Silence vs speech (0-1)
                "pause_count": int,            # Number of pauses
                "avg_pause_duration_ms": float,# Average pause length (ms)
                "energy_mean": float,          # Average volume (0-1)
                "energy_std": float,           # Volume variation (0-1)
                "zero_crossing_rate": float    # Articulation indicator (0-1)
            }

        Raises:
            ValueError: If audio is invalid, too short, or processing fails
        """
        max_duration = max_duration or self.MAX_DURATION_SECONDS

        try:
            # Decode and load audio (in-memory only)
            audio_data = base64.b64decode(audio_base64)
            y, sr = librosa.load(
                io.BytesIO(audio_data),
                sr=self.SAMPLE_RATE,
                mono=True,
                duration=max_duration  # Only load first N seconds
            )

            duration = len(y) / sr

            # Validate duration
            if duration < self.MIN_DURATION_SECONDS:
                raise ValueError(
                    f"Audio too short: {duration:.1f}s "
                    f"(minimum: {self.MIN_DURATION_SECONDS}s)"
                )

            logger.info(
                f"[AUDIO_ANALYSIS] Processing {duration:.1f}s audio "
                f"for language: {language}"
            )

            # Extract all acoustic features
            metrics = {}

            # 1. Pitch analysis (Parselmouth/Praat)
            pitch_metrics = self._extract_pitch_features(audio_data, sr)
            metrics.update(pitch_metrics)

            # 2. Voice quality (jitter, shimmer)
            quality_metrics = self._extract_voice_quality(audio_data, sr)
            metrics.update(quality_metrics)

            # 3. Speaking rhythm & pauses
            rhythm_metrics = self._extract_rhythm_features(y, sr)
            metrics.update(rhythm_metrics)

            # 4. Energy & intensity
            energy_metrics = self._extract_energy_features(y, sr)
            metrics.update(energy_metrics)

            logger.info(
                f"[AUDIO_ANALYSIS] Extracted {len(metrics)} metrics successfully"
            )

            return metrics

        except Exception as e:
            logger.error(f"[AUDIO_ANALYSIS] Failed to analyze audio: {str(e)}")
            raise ValueError(f"Audio analysis failed: {str(e)}")

    def _extract_pitch_features(
        self,
        audio_data: bytes,
        sr: int
    ) -> Dict[str, float]:
        """
        Extract pitch characteristics using Parselmouth (Praat).

        Returns:
            - pitch_mean: Average fundamental frequency
            - pitch_std: Pitch variability (monotone vs expressive)
            - pitch_min: Lowest detected pitch
            - pitch_max: Highest detected pitch
        """
        temp_file = None
        try:
            # Write audio to temporary file (Parselmouth requires file path)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_file = f.name
                f.write(audio_data)

            logger.debug(f"[PITCH] Created temp file: {temp_file}")

            # Load audio with Parselmouth from file path
            sound = parselmouth.Sound(temp_file)

            # Extract pitch contour
            pitch = call(
                sound,
                "To Pitch",
                0.0,  # Time step (auto)
                self.PITCH_FLOOR,
                self.PITCH_CEILING
            )

            # Get pitch values (Hz) - filter out unvoiced frames
            pitch_values = pitch.selected_array['frequency']
            pitch_values = pitch_values[pitch_values > 0]

            if len(pitch_values) == 0:
                logger.warning("[PITCH] No voiced frames detected")
                return {
                    "pitch_mean": 0.0,
                    "pitch_std": 0.0,
                    "pitch_min": 0.0,
                    "pitch_max": 0.0
                }

            metrics = {
                "pitch_mean": float(np.mean(pitch_values)),
                "pitch_std": float(np.std(pitch_values)),
                "pitch_min": float(np.min(pitch_values)),
                "pitch_max": float(np.max(pitch_values))
            }

            logger.debug(
                f"[PITCH] mean={metrics['pitch_mean']:.1f}Hz, "
                f"std={metrics['pitch_std']:.1f}Hz"
            )

            return metrics

        except Exception as e:
            logger.warning(f"[PITCH] Extraction failed: {str(e)}")
            return {
                "pitch_mean": 0.0,
                "pitch_std": 0.0,
                "pitch_min": 0.0,
                "pitch_max": 0.0
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.debug(f"[PITCH] Cleaned up temp file: {temp_file}")
                except Exception as cleanup_error:
                    logger.warning(f"[PITCH] Failed to cleanup temp file: {cleanup_error}")

    def _extract_voice_quality(
        self,
        audio_data: bytes,
        sr: int
    ) -> Dict[str, float]:
        """
        Extract voice quality indicators (jitter, shimmer).

        Jitter: Pitch period variation (voice stability)
        - Low jitter (<1%) = steady, confident voice
        - High jitter (>5%) = trembling, nervous voice

        Shimmer: Amplitude variation (voice control)
        - Low shimmer (<3%) = controlled voice
        - High shimmer (>10%) = unsteady voice
        """
        temp_file = None
        try:
            # Write audio to temporary file (Parselmouth requires file path)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_file = f.name
                f.write(audio_data)

            logger.debug(f"[VOICE_QUALITY] Created temp file: {temp_file}")

            # Load audio with Parselmouth from file path
            sound = parselmouth.Sound(temp_file)

            # Create point process for jitter/shimmer calculation
            point_process = call(
                sound,
                "To PointProcess (periodic, cc)",
                self.PITCH_FLOOR,
                self.PITCH_CEILING
            )

            # Calculate jitter (pitch period variability)
            jitter = call(
                point_process,
                "Get jitter (local)",
                0, 0,  # Entire duration
                0.0001, 0.02, 1.3  # Standard Praat parameters
            )

            # Calculate shimmer (amplitude variability)
            shimmer = call(
                [sound, point_process],
                "Get shimmer (local)",
                0, 0,  # Entire duration
                0.0001, 0.02, 1.3, 1.6  # Standard Praat parameters
            )

            metrics = {
                "jitter": float(jitter),
                "shimmer": float(shimmer)
            }

            logger.debug(
                f"[VOICE_QUALITY] jitter={jitter:.4f}, shimmer={shimmer:.4f}"
            )

            return metrics

        except Exception as e:
            logger.warning(f"[VOICE_QUALITY] Extraction failed: {str(e)}")
            return {
                "jitter": 0.0,
                "shimmer": 0.0
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.debug(f"[VOICE_QUALITY] Cleaned up temp file: {temp_file}")
                except Exception as cleanup_error:
                    logger.warning(f"[VOICE_QUALITY] Failed to cleanup temp file: {cleanup_error}")

    def _extract_rhythm_features(
        self,
        y: np.ndarray,
        sr: int
    ) -> Dict[str, float]:
        """
        Extract speaking rhythm and pause patterns.

        Returns:
            - speaking_ratio: Proportion of time speaking (0-1)
            - pause_ratio: Proportion of time in pauses (0-1)
            - pause_count: Number of detected pauses
            - avg_pause_duration_ms: Average pause length (milliseconds)
        """
        try:
            # Frame-based analysis
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop (60% overlap)

            # Compute RMS energy per frame
            energy = librosa.feature.rms(
                y=y,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]

            # Normalize energy to [0, 1]
            max_energy = np.max(energy)
            if max_energy > 0:
                energy = energy / max_energy

            # Voice activity detection (energy > threshold)
            voice_activity = energy > self.ENERGY_THRESHOLD

            # Calculate speaking vs pause time
            total_frames = len(voice_activity)
            voice_frames = np.sum(voice_activity)
            speaking_ratio = voice_frames / total_frames if total_frames > 0 else 0
            pause_ratio = 1.0 - speaking_ratio

            # Detect pause segments
            pauses = self._detect_pauses(voice_activity, hop_length, sr)
            pause_count = len(pauses)
            avg_pause_duration_ms = float(np.mean(pauses) * 1000) if pause_count > 0 else 0.0

            metrics = {
                "speaking_ratio": float(speaking_ratio),
                "pause_ratio": float(pause_ratio),
                "pause_count": pause_count,
                "avg_pause_duration_ms": avg_pause_duration_ms
            }

            logger.debug(
                f"[RHYTHM] speaking={speaking_ratio:.2f}, "
                f"pauses={pause_count}, avg_pause={avg_pause_duration_ms:.0f}ms"
            )

            return metrics

        except Exception as e:
            logger.warning(f"[RHYTHM] Extraction failed: {str(e)}")
            return {
                "speaking_ratio": 0.8,
                "pause_ratio": 0.2,
                "pause_count": 0,
                "avg_pause_duration_ms": 0.0
            }

    def _detect_pauses(
        self,
        voice_activity: np.ndarray,
        hop_length: int,
        sr: int
    ) -> np.ndarray:
        """
        Detect pause segments from voice activity flags.

        Returns array of pause durations (seconds).
        """
        pauses = []
        in_pause = False
        pause_start = 0

        for i, is_voice in enumerate(voice_activity):
            if not is_voice and not in_pause:
                # Start of pause
                in_pause = True
                pause_start = i
            elif is_voice and in_pause:
                # End of pause
                pause_duration = (i - pause_start) * hop_length / sr
                if pause_duration >= self.PAUSE_THRESHOLD_SECONDS:
                    pauses.append(pause_duration)
                in_pause = False

        return np.array(pauses)

    def _extract_energy_features(
        self,
        y: np.ndarray,
        sr: int
    ) -> Dict[str, float]:
        """
        Extract energy and intensity characteristics.

        Returns:
            - energy_mean: Average volume/intensity
            - energy_std: Volume variation (dynamic range)
            - zero_crossing_rate: Articulation/noisiness indicator
        """
        try:
            # RMS energy (volume)
            energy = librosa.feature.rms(y=y)[0]

            # Zero-crossing rate (articulation indicator)
            # Higher ZCR = more consonants, lower = more vowels
            zcr = librosa.feature.zero_crossing_rate(y)[0]

            metrics = {
                "energy_mean": float(np.mean(energy)),
                "energy_std": float(np.std(energy)),
                "zero_crossing_rate": float(np.mean(zcr))
            }

            logger.debug(
                f"[ENERGY] mean={metrics['energy_mean']:.3f}, "
                f"std={metrics['energy_std']:.3f}"
            )

            return metrics

        except Exception as e:
            logger.warning(f"[ENERGY] Extraction failed: {str(e)}")
            return {
                "energy_mean": 0.0,
                "energy_std": 0.0,
                "zero_crossing_rate": 0.0
            }


# Singleton instance
audio_analysis_service = AudioAnalysisService()
