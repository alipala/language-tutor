"""
Speaking DNA Service
====================
Core service for analyzing speaking patterns and managing DNA profiles.

This service implements the Speaking DNA feature which creates unique speaking
fingerprints for each learner based on their conversation patterns.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId
import logging

from database import database
from services.audio_analysis_service import audio_analysis_service

logger = logging.getLogger(__name__)

# ── S2.1 causal sentence fallback ───────────────────────────────────────────
_CAUSAL_FALLBACK = "Six sessions of practice moved your DNA. Keep going."


class SpeakingDNAService:
    """
    Manages Speaking DNA profiles, analysis, and coach instructions.

    Key responsibilities:
    - Analyze session data to extract speaking metrics
    - Calculate and update 6 DNA strands (rhythm, confidence, vocabulary, accuracy, learning, emotional)
    - Detect breakthrough moments
    - Generate personalized coach instructions
    - Track DNA evolution over time
    """

    # DNA Strand Weights for different session types
    # S4: pronunciation and fluency weights added for the 6-strand model.
    #   pronunciation — acoustic-only, pinned unless has_audio=True; voice_check / speaking_assessment get full weight
    #   fluency       — transcript-based, every session; lower weight for acoustic-heavy types
    SESSION_WEIGHTS = {
        "learning": {
            "rhythm": 0.8,
            "confidence": 1.0,
            "pronunciation": 0.0,   # pinned (no audio in learning sessions)
            "vocabulary": 0.7,
            "accuracy": 1.0,
            "fluency": 0.9,
            "learning": 1.0,
            "emotional": 0.9
        },
        "freestyle": {
            "rhythm": 1.0,
            "confidence": 1.0,
            "pronunciation": 0.0,
            "vocabulary": 1.0,
            "accuracy": 0.7,
            "fluency": 1.0,
            "learning": 0.6,
            "emotional": 1.0
        },
        "news": {
            "rhythm": 0.9,
            "confidence": 0.9,
            "pronunciation": 0.0,
            "vocabulary": 1.0,
            "accuracy": 0.8,
            "fluency": 0.8,
            "learning": 0.7,
            "emotional": 0.8
        },
        # Voice check: pure acoustic baseline — pronunciation gets full weight here.
        # Fluency/accuracy/vocabulary carry light signal (30-second monologue, no AI corrections).
        "voice_check": {
            "rhythm": 1.0,
            "confidence": 1.0,
            "pronunciation": 1.0,   # primary acoustic update
            "vocabulary": 0.3,
            "accuracy": 0.3,
            "fluency": 0.8,
            "learning": 0.3,
            "emotional": 1.0
        },
        "speaking_assessment": {
            "rhythm": 1.0,
            "confidence": 1.0,
            "pronunciation": 1.0,   # assessment carries real pronunciation signal
            "vocabulary": 0.6,
            "accuracy": 0.8,
            "fluency": 1.0,
            "learning": 0.5,
            "emotional": 1.0
        },
        # S3.3 — transcript-only session types from save-conversation.
        "custom_topic": {
            "rhythm": 0.0,
            "confidence": 0.0,
            "pronunciation": 0.0,
            "vocabulary": 0.5,
            "accuracy": 0.5,
            "fluency": 0.5,
            "learning": 0.3,
            "emotional": 0.0
        },
        "practice": {
            "rhythm": 0.0,
            "confidence": 0.0,
            "pronunciation": 0.0,
            "vocabulary": 0.5,
            "accuracy": 0.5,
            "fluency": 0.5,
            "learning": 0.3,
            "emotional": 0.0
        },
    }

    # Thresholds for breakthrough detection
    BREAKTHROUGH_THRESHOLDS = {
        "confidence_jump": 0.15,          # 15% confidence increase
        "fluency_streak_multiplier": 1.5,  # 50% longer than previous best
        "vocabulary_expansion": 10,        # 10 new words in session
        "speed_improvement": 0.20,         # 20% WPM increase
    }

    # Language-specific filler words and hesitation markers
    FILLER_WORDS = {
        "english": [
            "uh", "um", "ah", "er", "eh", "hmm", "hm",
            "like", "you know", "i mean", "so", "well",
            "actually", "basically", "literally", "just",
            "right", "okay", "ok", "yeah", "yep"
        ],
        "dutch": [
            "eh", "uh", "um", "ah", "nou", "ja", "dus",
            "eigenlijk", "gewoon", "zeg maar", "nou ja",
            "tja", "hè", "hoor", "ofzo", "enzo",
            "soort van", "eh ja", "weet je"
        ],
        "spanish": [
            "eh", "ah", "um", "este", "pues", "bueno",
            "entonces", "o sea", "como", "verdad",
            "mmm", "eeeh", "aaah", "este", "estee",
            "digamos", "sabes", "¿no?", "¿verdad?"
        ],
        "french": [
            "euh", "bah", "ben", "alors", "donc",
            "voilà", "quoi", "hein", "tu vois",
            "enfin", "bon", "disons", "genre",
            "en fait", "c'est-à-dire"
        ],
        "german": [
            "äh", "ähm", "eh", "hm", "also",
            "sozusagen", "eigentlich", "halt", "ja",
            "naja", "ne", "oder", "weißt du",
            "quasi", "irgendwie"
        ],
        "italian": [
            "ehm", "eh", "ah", "allora", "cioè",
            "diciamo", "insomma", "praticamente", "tipo",
            "sai", "no?", "vero?", "ecco", "boh"
        ]
    }

    # Self-correction markers (language-independent patterns)
    CORRECTION_MARKERS = [
        "i mean", "sorry", "no wait", "wait", "actually",
        "ik bedoel", "sorry", "wacht", "eigenlijk",
        "quiero decir", "perdón", "espera", "en realidad",
        "je veux dire", "désolé", "attends",
        "ich meine", "entschuldigung", "warte",
        "voglio dire", "scusa", "aspetta"
    ]

    # Error type normalization mapping for common errors extraction
    ERROR_TYPE_MAPPING = {
        "subject-verb-agreement": "subject_verb_agreement",
        "subject verb agreement": "subject_verb_agreement",
        "subjectverb": "subject_verb_agreement",
        "article-usage": "article_usage",
        "article usage": "article_usage",
        "articles": "article_usage",
        "tense-conjugation": "tense_conjugation",
        "verb-tense": "tense_conjugation",
        "verb tense": "tense_conjugation",
        "tense": "tense_conjugation",
        "word-order": "word_order",
        "word order": "word_order",
        "syntax": "word_order",
        "preposition-selection": "preposition_usage",
        "preposition": "preposition_usage",
        "prepositions": "preposition_usage",
        "gender-agreement": "gender_agreement",
        "gender": "gender_agreement",
        "spelling-error": "spelling",
        "spelling": "spelling",
        "pronunciation-error": "pronunciation",
        "pronunciation": "pronunciation",
    }

    # Speaker archetypes based on DNA combination
    ARCHETYPES = {
        ("thoughtful_pacer", "perfectionist", "persistent"): {
            "name": "The Thoughtful Builder",
            "summary": "A deliberate learner who values accuracy and builds confidence through mastery.",
            "coach_approach": "patient_encourager"
        },
        ("rapid_responder", "risk_taker", "explorer"): {
            "name": "The Fearless Explorer",
            "summary": "An adventurous speaker who learns through experimentation and isn't afraid of mistakes.",
            "coach_approach": "challenge_provider"
        },
        ("steady_speaker", "balanced", "persistent"): {
            "name": "The Steady Progressor",
            "summary": "A balanced learner who makes consistent progress through regular practice.",
            "coach_approach": "balanced_guide"
        },
    }

    def __init__(self):
        """Initialize the Speaking DNA Service with database and caching."""
        self.db = database
        self._coach_instructions_cache = {}  # {cache_key: (instructions, timestamp)}
        self._cache_ttl = 600  # 10 minutes TTL in seconds

    # =========================================================================
    # CORE ANALYSIS METHODS
    # =========================================================================

    async def analyze_session_for_dna(
        self,
        user_id: str,
        language: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a completed session and update the user's DNA profile.

        Args:
            user_id: User's MongoDB ObjectId as string
            language: Target language code (e.g., "dutch", "spanish")
            session_data: Session data including transcripts, timestamps, etc.

        Returns:
            Dict with updated profile, detected breakthroughs, and coach notes
        """
        try:
            # Get existing profile or create new one
            existing_profile = await self.db.speaking_dna_profiles.find_one({
                "user_id": user_id,
                "language": language
            })

            logger.info(f"[DNA] Analyzing session for user {user_id}, language {language}")

            # S2.1 — capture previous strand values for the reveal ceremony delta animation
            previous_strand_values = existing_profile.get("dna_strands", {}) if existing_profile else {}

            # Extract acoustic metrics + Azure pronunciation assessment in parallel (if audio available)
            acoustic_metrics = None
            azure_pronunciation_result = None
            if session_data.get("audio_base64"):
                import asyncio as _asyncio
                from pronunciation_assessment_service import pronunciation_service as _pron_svc

                session_type_for_audio = session_data.get("session_type", "learning")
                # Only call Azure for session types that carry pronunciation signal
                _AZURE_SESSION_TYPES = {"voice_check", "speaking_assessment"}
                run_azure = session_type_for_audio in _AZURE_SESSION_TYPES and _pron_svc.enabled

                async def _extract_acoustic():
                    try:
                        logger.info("[DNA] Extracting acoustic metrics from session audio")
                        result = await audio_analysis_service.extract_acoustic_metrics(
                            audio_base64=session_data["audio_base64"],
                            audio_format=session_data.get("audio_format", "wav"),
                            language=language,
                            max_duration=60.0
                        )
                        logger.info(
                            f"[DNA] Acoustic metrics extracted: "
                            f"pitch={result.get('pitch_mean', 0):.1f}Hz, "
                            f"jitter={result.get('jitter', 0):.4f}"
                        )
                        return result
                    except Exception as e:
                        logger.warning(f"[DNA] Acoustic analysis failed: {e} - continuing without acoustic metrics")
                        return None

                async def _azure_assess():
                    if not run_azure:
                        return None
                    try:
                        logger.info(f"[DNA] Running Azure Pronunciation Assessment for {session_type_for_audio}")
                        result = await _pron_svc.assess_from_base64(
                            audio_base64=session_data["audio_base64"],
                            language=language,
                        )
                        logger.info(
                            f"[DNA] Azure Pronunciation Assessment: "
                            f"pron={result.get('pronunciation_score')}, "
                            f"fluency={result.get('fluency_score')}"
                        )
                        return result
                    except Exception as e:
                        logger.warning(f"[DNA] Azure Pronunciation Assessment failed (non-fatal): {e}")
                        return None

                acoustic_metrics, azure_pronunciation_result = await _asyncio.gather(
                    _extract_acoustic(), _azure_assess()
                )

            # Extract metrics from session (including acoustic if available)
            session_metrics = self._extract_session_metrics(
                session_data,
                language,
                acoustic_metrics=acoustic_metrics
            )
            logger.info(f"[DNA] Extracted metrics: WPM={session_metrics.get('words_per_minute', 0):.1f}")

            # S3.1 / S3.2: derive pinning flags from session payload
            has_audio      = bool(session_data.get("audio_base64"))
            has_challenges = session_data.get("challenges_offered", 0) > 0

            # Calculate strand updates
            updated_strands = await self._calculate_strand_updates(
                existing_profile,
                session_metrics,
                session_data.get("session_type", "learning"),
                user_id,
                language,
                session_data,
                has_audio=has_audio,
                has_challenges=has_challenges,
                azure_pronunciation_result=azure_pronunciation_result,
            )

            # Detect any breakthroughs
            breakthroughs = await self._detect_breakthroughs(
                user_id=user_id,
                language=language,
                existing_profile=existing_profile,
                new_strands=updated_strands,
                session_data=session_data
            )

            logger.info(f"[DNA] Detected {len(breakthroughs)} breakthroughs")

            # Determine overall profile
            overall_profile = self._determine_overall_profile(updated_strands)

            # Update or create profile
            now = datetime.utcnow()
            sessions_analyzed = (existing_profile.get("sessions_analyzed", 0) if existing_profile else 0) + 1
            total_minutes = (existing_profile.get("total_speaking_minutes", 0) if existing_profile else 0) + session_metrics.get("session_duration_minutes", 5)

            # Update baseline assessment with acoustic metrics (ongoing analysis)
            baseline_assessment = None
            if acoustic_metrics:
                # Get existing baseline or create new
                existing_baseline = existing_profile.get("baseline_assessment") if existing_profile else None

                if existing_baseline:
                    # Update existing baseline with moving average of last 10 sessions
                    # For simplicity, we store the latest metrics (future: implement moving average)
                    baseline_assessment = {
                        "date": now,
                        "acoustic_metrics": acoustic_metrics
                    }
                    logger.info("[DNA] Updated baseline assessment with new acoustic metrics")
                else:
                    # First baseline
                    baseline_assessment = {
                        "date": now,
                        "acoustic_metrics": acoustic_metrics
                    }
                    logger.info("[DNA] Created initial baseline assessment")

            # ── Phase 0 — DNA-acceleration fuel ──────────────────────
            # Compute per-strand deltas BEFORE persisting so we can store the
            # freshest delta on the profile itself. The hub then reads it via
            # _get_dna_summary() and can show "this session pushed Fluency +X"
            # without needing the background task to be synchronous.
            #
            # last_session_delta = full per-strand {previous, current, delta}
            # top_strand / top_delta = the strand with the largest positive delta
            #   (handy for one-line UI like "Your Fluency climbed +3 today").
            last_session_delta_strands = self._compute_strand_deltas(
                previous_strand_values, updated_strands
            )
            top_strand_key: Optional[str] = None
            top_strand_delta: float = 0.0
            for _strand_key, _vals in last_session_delta_strands.items():
                _d = float(_vals.get("delta", 0.0))
                if _d > top_strand_delta:
                    top_strand_delta = _d
                    top_strand_key = _strand_key

            last_session_delta_doc = {
                "session_id": session_data.get("session_id"),
                "session_type": session_data.get("session_type", "learning"),
                "computed_at": now,
                "strands": last_session_delta_strands,
                "top_strand": top_strand_key,
                "top_delta": round(top_strand_delta, 4),
            }

            profile_update = {
                "user_id": user_id,
                "language": language,
                "dna_strands": updated_strands,
                "overall_profile": overall_profile,
                "sessions_analyzed": sessions_analyzed,
                "total_speaking_minutes": total_minutes,
                "updated_at": now,
                "last_session_delta": last_session_delta_doc,
            }

            # Add baseline assessment if we have acoustic metrics
            if baseline_assessment:
                profile_update["baseline_assessment"] = baseline_assessment

            if existing_profile:
                await self.db.speaking_dna_profiles.update_one(
                    {"_id": existing_profile["_id"]},
                    {"$set": profile_update}
                )
                logger.info(f"[DNA] Updated existing profile for user {user_id}")
            else:
                profile_update["created_at"] = now
                result = await self.db.speaking_dna_profiles.insert_one(profile_update)
                logger.info(f"[DNA] Created new profile for user {user_id}: {result.inserted_id}")

            # Store breakthroughs
            if breakthroughs:
                # Convert to dict format for MongoDB
                breakthrough_docs = []
                for bt in breakthroughs:
                    breakthrough_docs.append({
                        "_id": str(ObjectId()),
                        "user_id": user_id,
                        "language": language,
                        "session_id": session_data.get("session_id"),
                        "breakthrough_type": bt["breakthrough_type"],
                        "category": bt["category"],
                        "title": bt["title"],
                        "description": bt["description"],
                        "emoji": bt["emoji"],
                        "metrics": bt["metrics"],
                        "context": bt["context"],
                        "celebrated": False,
                        "shared": False,
                        "created_at": now
                    })

                await self.db.speaking_breakthroughs.insert_many(breakthrough_docs)
                logger.info(f"[DNA] Stored {len(breakthrough_docs)} breakthroughs")

                # S1.7 — Fire push notification for the first breakthrough in this batch.
                # One push per session; cooldown enforced inside the helper.
                try:
                    await _send_breakthrough_push(
                        user_id=user_id,
                        breakthrough=breakthroughs[0],
                    )
                except Exception as _push_err:
                    logger.warning(f"[DNA] Breakthrough push failed (non-fatal): {_push_err}")

            # Weekly snapshot disabled — replaced by session-level history
            # await self._create_weekly_snapshot(
            #     user_id=user_id,
            #     language=language,
            #     strands=updated_strands,
            #     session_duration_minutes=session_metrics.get("session_duration_minutes", 5),
            #     breakthroughs_count=len(breakthroughs),
            #     acoustic_metrics=acoustic_metrics  # Add acoustic metrics to weekly snapshot
            # )

            # Append session-level history (transcript each session, acoustic on voice checks)
            await self._append_session_history(
                user_id=user_id,
                language=language,
                updated_strands=updated_strands,
                session_number=sessions_analyzed,
                session_type=session_data.get("session_type", "learning"),
                voice_checks_count=updated_strands.get("pronunciation", {}).get("voice_checks_count", 0),
            )

            # S2.1 — generate causal sentence for the reveal ceremony
            causal_sentence = await self._generate_causal_sentence(
                previous_strands=previous_strand_values,
                updated_strands=updated_strands,
                session_data=session_data,
                language=language,
            )

            session_insights = self._generate_session_insights(session_metrics, updated_strands)
            session_insights["causal_sentence"] = causal_sentence

            # S3.4 — per-strand delta for the session summary animation.
            # Phase 0: reuse the already-computed dict from the
            # last_session_delta block above instead of recomputing.
            strand_deltas = last_session_delta_strands

            return {
                "profile": profile_update,
                "breakthroughs": breakthroughs,
                "session_insights": session_insights,
                "previous_strand_values": previous_strand_values,
                "strand_deltas": strand_deltas,
            }

        except Exception as e:
            logger.error(f"[DNA] Error analyzing session: {str(e)}", exc_info=True)
            raise

    # =========================================================================
    # S3.4 — STRAND DELTA COMPUTATION
    # =========================================================================

    def _compute_strand_deltas(
        self,
        previous_strands: Dict[str, Any],
        updated_strands: Dict[str, Any],
    ) -> Dict[str, Dict[str, float]]:
        """
        S3.4 — Compute per-strand numeric deltas for the session-summary animation.

        Extracts the canonical 0-1 score from each strand object (same logic as the
        mobile strandScore helper) and returns a dict of the form:
          { "rhythm": {"previous": 0.42, "current": 0.55, "delta": 0.13}, ... }

        Only the four display strands (rhythm, confidence, vocabulary, accuracy) are
        included; the emotional and learning strands are omitted from the summary UI.

        Returns an empty dict when either mapping is empty (first session ever).
        """
        if not previous_strands or not updated_strands:
            return {}

        def _score(strands: Dict, key: str) -> float:
            s = strands.get(key) or {}
            if key == "rhythm":
                return float(s.get("consistency_score") or 0.0)
            if key == "confidence":
                return float(s.get("score") or 0.0)
            if key == "pronunciation":
                return float(s.get("score") or 0.0)
            if key == "vocabulary":
                return float(s.get("new_word_attempt_rate") or 0.0)
            if key == "accuracy":
                return float(s.get("grammar_accuracy") or 0.0)
            if key == "fluency":
                return float(s.get("score") or 0.0)
            return 0.0

        # S4: include all 6 display strands
        deltas: Dict[str, Dict[str, float]] = {}
        for key in ("rhythm", "confidence", "pronunciation", "vocabulary", "accuracy", "fluency"):
            prev = round(_score(previous_strands, key), 4)
            curr = round(_score(updated_strands, key), 4)
            deltas[key] = {
                "previous": prev,
                "current": curr,
                "delta": round(curr - prev, 4),
            }

        logger.debug(f"[DNA] S3.4 strand_deltas computed: {deltas}")
        return deltas

    def _extract_session_metrics(
        self,
        session_data: Dict,
        language: str = "english",
        acoustic_metrics: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Extract quantifiable metrics from session data.

        Args:
            session_data: Session data dict
            language: Target language for language-specific analysis
            acoustic_metrics: Optional acoustic metrics from audio analysis

        Expected session_data structure:
        {
            "session_type": "learning" | "freestyle" | "news",
            "duration_seconds": 300,
            "user_turns": [
                {
                    "transcript": "Ik ga naar de winkel",
                    "start_time_ms": 12500,
                    "end_time_ms": 15200,
                    "ai_prompt_end_time_ms": 11000
                },
                ...
            ],
            "corrections_received": [...],
            "challenges_offered": 2,
            "challenges_accepted": 1,
            "topics_discussed": [...]
        }
        """
        user_turns = session_data.get("user_turns", [])

        if not user_turns:
            return self._get_default_metrics()

        # Calculate response latencies
        latencies = []
        for turn in user_turns:
            if turn.get("ai_prompt_end_time_ms") and turn.get("start_time_ms"):
                latency = turn["start_time_ms"] - turn["ai_prompt_end_time_ms"]
                if latency > 0:  # Valid latency
                    latencies.append(latency)

        # Calculate words per minute
        total_words = 0
        total_speaking_time_ms = 0
        all_words = []

        for turn in user_turns:
            transcript = turn.get("transcript", "")
            words = transcript.split()
            total_words += len(words)
            all_words.extend(words)

            if turn.get("start_time_ms") is not None and turn.get("end_time_ms") is not None:
                turn_duration = turn["end_time_ms"] - turn["start_time_ms"]
                total_speaking_time_ms += turn_duration
                logger.debug(f"[DNA] Turn duration: {turn_duration}ms, words: {len(words)}")

        logger.info(f"[DNA] Total words: {total_words}, Total speaking time: {total_speaking_time_ms}ms")
        wpm = (total_words / (total_speaking_time_ms / 60000)) if total_speaking_time_ms > 0 else 0
        logger.info(f"[DNA] Calculated WPM: {wpm:.1f}")

        # Detect filler words using language-specific dictionary
        filler_patterns = self.FILLER_WORDS.get(language.lower(), self.FILLER_WORDS["english"])
        filler_count = 0
        transcript_lower = " ".join(word.lower() for word in all_words)

        # Check multi-word fillers (like "you know", "o sea")
        for filler in filler_patterns:
            if " " in filler:  # Multi-word filler
                filler_count += transcript_lower.count(filler)
            else:  # Single word filler
                filler_count += sum(1 for word in all_words if word.lower() == filler)

        filler_rate = (filler_count / (total_speaking_time_ms / 60000)) if total_speaking_time_ms > 0 else 0

        # Calculate unique vocabulary (excluding filler words)
        filler_set = set(f.lower() for f in filler_patterns if " " not in f)
        unique_words = set(
            word.lower() for word in all_words
            if len(word) > 2 and word.lower() not in filler_set
        )

        # Self-corrections using correction markers
        self_corrections = sum(
            1 for turn in user_turns
            if any(marker in turn.get("transcript", "").lower()
                   for marker in self.CORRECTION_MARKERS)
        )

        # Also detect pause-based hesitations (long response latencies)
        hesitation_count = sum(1 for lat in latencies if lat > 3000)  # >3s = hesitation

        # Calculate standard deviation of latencies for consistency
        import statistics
        latency_std = statistics.stdev(latencies) if len(latencies) > 1 else 500

        metrics = {
            "session_duration_minutes": session_data.get("duration_seconds", 300) / 60,
            "response_latency_avg_ms": sum(latencies) / len(latencies) if latencies else 2000,
            "response_latency_std_ms": latency_std,
            "words_per_minute": wpm,
            "total_words": total_words,
            "unique_words": len(unique_words),
            "filler_rate_per_minute": filler_rate,
            "self_corrections": self_corrections,
            "turns_count": len(user_turns),
            "challenges_offered": session_data.get("challenges_offered", 0),
            "challenges_accepted": session_data.get("challenges_accepted", 0),
            "corrections_received": len(session_data.get("corrections_received", [])),
            "corrections_data": session_data.get("corrections_received", []),  # Raw corrections for pattern extraction
            "hesitation_count": hesitation_count,
            # Acoustic metrics (if available)
            **({f"acoustic_{k}": v for k, v in acoustic_metrics.items()} if acoustic_metrics else {})
        }

        # 🔥 NEW: Add assessment scores if this is a speaking assessment
        if session_data.get("assessment_scores"):
            metrics["assessment_scores"] = session_data["assessment_scores"]
            logger.info(f"[DNA] Assessment scores included: grammar={metrics['assessment_scores']['grammar']}, vocabulary={metrics['assessment_scores']['vocabulary']}")

        return metrics

    def _get_default_metrics(self) -> Dict:
        """Return default metrics for empty sessions."""
        return {
            "session_duration_minutes": 5,
            "response_latency_avg_ms": 2000,
            "response_latency_std_ms": 500,
            "words_per_minute": 80,
            "total_words": 50,
            "unique_words": 30,
            "filler_rate_per_minute": 2.0,
            "self_corrections": 1,
            "turns_count": 5,
            "challenges_offered": 0,
            "challenges_accepted": 0,
            "corrections_received": 0
        }

    async def _calculate_strand_updates(
        self,
        existing_profile: Optional[Dict],
        session_metrics: Dict,
        session_type: str,
        user_id: str,
        language: str,
        session_data: Dict = None,
        has_audio: bool = True,
        has_challenges: bool = True,
        azure_pronunciation_result: Optional[Dict] = None,
    ) -> Dict:
        """
        Calculate updated DNA strands using weighted moving average.

        Uses exponential moving average to smooth updates while still
        being responsive to recent sessions.

        S3.1 — has_audio=False: Rhythm, Confidence, Pronunciation, Emotional are
        pinned to their existing values. Prevents silent drift for sessions that
        carry no audio (every regular conversation, news, freestyle).

        S3.2 — has_challenges=False: Learning strand is pinned.

        S4   — Pronunciation strand is acoustic-only (voice_check / speaking_assessment).
               Fluency strand is transcript-based and runs every session.
        """
        weights = self.SESSION_WEIGHTS.get(session_type, self.SESSION_WEIGHTS["learning"])
        alpha = 0.3  # Learning rate for exponential moving average

        existing_strands = existing_profile.get("dna_strands", {}) if existing_profile else {}

        # ── S3.1 / S4: acoustic strand pinning ───────────────────────────────
        if not has_audio:
            logger.info(
                f"[DNA] Acoustic strands pinned (no audio). user_id={user_id} "
                f"language={language} session_type={session_type}"
            )
            rhythm_result        = existing_strands.get("rhythm")        or self._update_rhythm_strand(None, session_metrics, alpha, weights["rhythm"])
            confidence_result    = existing_strands.get("confidence")    or self._update_confidence_strand(None, session_metrics, alpha, weights["confidence"])
            pronunciation_result = existing_strands.get("pronunciation") or self._update_pronunciation_strand(None, None, session_type)
            emotional_result     = existing_strands.get("emotional")     or await self._update_emotional_strand(None, session_metrics, alpha, weights["emotional"], user_id, language, session_data)
        else:
            rhythm_result     = self._update_rhythm_strand(existing_strands.get("rhythm"), session_metrics, alpha, weights["rhythm"])
            confidence_result = self._update_confidence_strand(existing_strands.get("confidence"), session_metrics, alpha, weights["confidence"])
            pronunciation_result = self._update_pronunciation_strand(
                existing_strands.get("pronunciation"),
                azure_pronunciation_result,
                session_type,
            )
            emotional_result  = await self._update_emotional_strand(
                existing_strands.get("emotional"),
                session_metrics,
                alpha,
                weights["emotional"],
                user_id,
                language,
                session_data
            )

        # ── S3.2: learning strand pinning ─────────────────────────────────────
        if not has_challenges:
            logger.info(
                f"[DNA] Learning strand skipped (no challenges). user_id={user_id} "
                f"language={language} session_type={session_type}"
            )
            learning_result = existing_strands.get("learning") or self._update_learning_strand(None, session_metrics, alpha, weights["learning"])
        else:
            learning_result = self._update_learning_strand(existing_strands.get("learning"), session_metrics, alpha, weights["learning"])

        updated = {
            "rhythm":        rhythm_result,
            "confidence":    confidence_result,
            "pronunciation": pronunciation_result,
            "vocabulary":    self._update_vocabulary_strand(existing_strands.get("vocabulary"), session_metrics, alpha, weights["vocabulary"]),
            "accuracy":      self._update_accuracy_strand(existing_strands.get("accuracy"), session_metrics, alpha, weights["accuracy"]),
            "fluency":       self._update_fluency_strand(existing_strands.get("fluency"), session_metrics, alpha, weights.get("fluency", 0.8)),
            "learning":      learning_result,
            "emotional":     emotional_result,
        }

        return updated

    def _update_rhythm_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """
        Update rhythm strand based on speaking pace and pauses.

        Enhanced with acoustic analysis for more accurate pause detection.
        """
        wpm = metrics["words_per_minute"]

        # Use acoustic pause metrics if available (more accurate than text-based)
        pause_ratio = metrics.get("acoustic_pause_ratio")
        avg_pause_ms = metrics.get("acoustic_avg_pause_duration_ms")

        # Determine rhythm type (consider acoustic pauses for refinement)
        if wpm < 70:
            rhythm_type = "thoughtful_pacer"
            description = "Takes time to formulate thoughts, speaks deliberately"
            # Refine based on pause patterns
            if pause_ratio and pause_ratio > 0.3:
                description = "Thoughtful pacer with frequent pauses for reflection"
        elif wpm > 120:
            rhythm_type = "rapid_responder"
            description = "Quick and spontaneous, comfortable with fast exchanges"
            # Refine based on pause patterns
            if pause_ratio and pause_ratio < 0.15:
                description = "Rapid responder with minimal pauses, very fluent"
        else:
            rhythm_type = "steady_speaker"
            description = "Maintains a balanced, natural speaking pace"
            # Refine based on pause patterns
            if pause_ratio and pause_ratio > 0.25:
                description = "Steady speaker with natural pauses for clarity"

        # Calculate consistency score
        latency_std = metrics.get("response_latency_std_ms", 500)
        consistency = max(0, 1 - (latency_std / 2000))  # Lower std = higher consistency

        # Enhance consistency with acoustic speaking_ratio if available
        if metrics.get("acoustic_speaking_ratio"):
            speaking_ratio = metrics["acoustic_speaking_ratio"]
            # High speaking ratio = more consistent flow
            acoustic_consistency = speaking_ratio  # 0.8-0.9 is good
            consistency = (consistency * 0.6 + acoustic_consistency * 0.4)  # Blend with text-based

        if existing:
            # Exponential moving average
            new_wpm = existing.get("words_per_minute_avg", wpm) * (1 - alpha * weight) + wpm * alpha * weight
            new_consistency = existing.get("consistency_score", consistency) * (1 - alpha * weight) + consistency * alpha * weight
        else:
            new_wpm = wpm
            new_consistency = consistency

        return {
            "type": rhythm_type,
            "words_per_minute_avg": round(new_wpm, 1),
            "pause_duration_avg_ms": round(avg_pause_ms if avg_pause_ms else metrics["response_latency_avg_ms"], 0),
            "consistency_score": round(new_consistency, 2),
            "description": description
        }

    def _update_confidence_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """
        Update confidence strand based on latency, fillers, self-corrections, voice quality OR assessment scores.

        Enhanced with acoustic analysis for voice stability assessment.
        """

        # 🔥 NEW: Use assessment fluency & pronunciation scores if available
        if metrics.get("assessment_scores"):
            fluency_score = metrics["assessment_scores"]["fluency"]
            pronunciation_score = metrics["assessment_scores"]["pronunciation"]
            logger.info(f"[DNA] Using assessment scores for confidence: fluency={fluency_score}, pronunciation={pronunciation_score}")

            # Confidence is based on fluency and pronunciation (how well they speak)
            raw_score = (fluency_score + pronunciation_score) / 200.0  # Average of both, normalized to 0-1
        else:
            # Original logic for practice sessions
            # Calculate raw confidence score (0-1)
            latency_factor = max(0, 1 - (metrics["response_latency_avg_ms"] / 5000))  # <5s is good
            filler_factor = max(0, 1 - (metrics["filler_rate_per_minute"] / 10))  # <10/min is good
            correction_factor = max(0, 1 - (metrics["self_corrections"] / 5))  # <5 per session is good

            # Voice quality factor from acoustic analysis
            voice_quality_factor = None
            if metrics.get("acoustic_jitter") is not None and metrics.get("acoustic_shimmer") is not None:
                jitter = metrics["acoustic_jitter"]
                shimmer = metrics["acoustic_shimmer"]

                # Low jitter/shimmer = steady voice = high confidence
                # Typical ranges: jitter <1% good, >5% nervous; shimmer <3% good, >10% nervous
                jitter_score = max(0, 1 - (jitter / 0.05))  # Normalize to 0-1 (5% jitter = 0 score)
                shimmer_score = max(0, 1 - (shimmer / 0.10))  # Normalize to 0-1 (10% shimmer = 0 score)

                voice_quality_factor = (jitter_score * 0.5 + shimmer_score * 0.5)

            # Calculate weighted raw score
            if voice_quality_factor is not None:
                # With acoustic: reduce weight of latency, add voice quality
                raw_score = (
                    latency_factor * 0.25 +
                    filler_factor * 0.25 +
                    correction_factor * 0.25 +
                    voice_quality_factor * 0.25  # Voice stability
                )
            else:
                # Without acoustic: original weights
                raw_score = (
                    latency_factor * 0.4 +
                    filler_factor * 0.3 +
                    correction_factor * 0.3
                )

        # Determine level
        if raw_score < 0.3:
            level = "hesitant"
        elif raw_score < 0.5:
            level = "building"
        elif raw_score < 0.75:
            level = "comfortable"
        else:
            level = "fluent"

        # Determine trend
        if existing:
            old_score = existing.get("score", raw_score)
            if raw_score > old_score + 0.05:
                trend = "improving"
            elif raw_score < old_score - 0.05:
                trend = "declining"
            else:
                trend = "stable"

            new_score = old_score * (1 - alpha * weight) + raw_score * alpha * weight
            new_latency = existing.get("response_latency_avg_ms", metrics["response_latency_avg_ms"]) * (1 - alpha * weight) + metrics["response_latency_avg_ms"] * alpha * weight
            new_filler = existing.get("filler_rate_per_minute", metrics["filler_rate_per_minute"]) * (1 - alpha * weight) + metrics["filler_rate_per_minute"] * alpha * weight
        else:
            trend = "stable"
            new_score = raw_score
            new_latency = metrics["response_latency_avg_ms"]
            new_filler = metrics["filler_rate_per_minute"]

        # Generate description
        descriptions = {
            "hesitant": "Still building speaking comfort, benefits from extra encouragement",
            "building": "Growing more confident, especially in familiar topics",
            "comfortable": "Speaks with reasonable confidence in most situations",
            "fluent": "Confident and natural in conversation"
        }

        return {
            "level": level,
            "score": round(new_score, 2),
            "response_latency_avg_ms": round(new_latency, 0),
            "filler_rate_per_minute": round(new_filler, 1),
            "trend": trend,
            "description": descriptions[level]
        }

    def _update_vocabulary_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update vocabulary strand based on word variety and complexity OR assessment scores."""

        # 🔥 NEW: Use assessment vocabulary score if available
        if metrics.get("assessment_scores"):
            vocab_score = metrics["assessment_scores"]["vocabulary"]
            logger.info(f"[DNA] Using assessment vocabulary score: {vocab_score}/100")

            # Map vocabulary score to style (based on actual performance)
            if vocab_score < 30:
                style = "safety_first"
                description = "Limited vocabulary range, needs expansion"
                complexity = "beginner"
            elif vocab_score < 60:
                style = "balanced"
                description = "Developing vocabulary with room to grow"
                complexity = "intermediate"
            else:
                style = "adventurous"
                description = "Good vocabulary range and word choice"
                complexity = "advanced"

            unique_ratio = vocab_score / 100.0  # Approximate based on score
        else:
            # Original logic for practice sessions
            unique_ratio = metrics["unique_words"] / max(metrics["total_words"], 1)

            # Determine vocabulary style
            if unique_ratio > 0.7:
                style = "adventurous"
                description = "Actively experiments with new vocabulary"
            elif unique_ratio < 0.4:
                style = "safety_first"
                description = "Prefers familiar words but occasionally experiments"
            else:
                style = "balanced"
                description = "Good mix of familiar and new vocabulary"

            # Determine complexity level (simplified - could use word frequency lists)
            avg_word_length = metrics["total_words"] / max(metrics["turns_count"], 1)
            if avg_word_length > 15:
                complexity = "advanced"
            elif avg_word_length > 8:
                complexity = "intermediate"
            else:
                complexity = "beginner"

        if existing:
            new_unique = existing.get("unique_words_per_session", metrics["unique_words"]) * (1 - alpha * weight) + metrics["unique_words"] * alpha * weight
        else:
            new_unique = metrics["unique_words"]

        return {
            "style": style,
            "unique_words_per_session": round(new_unique, 0),
            "new_word_attempt_rate": round(unique_ratio, 2),
            "complexity_level": complexity,
            "description": description
        }

    def _normalize_error_type(self, error_type: str) -> str:
        """Normalize error type string for consistency."""
        normalized = error_type.lower().strip().replace("_", "-")
        return self.ERROR_TYPE_MAPPING.get(normalized, error_type.lower().replace("-", "_"))

    def _extract_error_patterns(self, corrections_data: List, existing_errors: List[str] = None) -> tuple:
        """
        Extract common error patterns from corrections data.
        Enhanced to use structured grammar_issues with severity ranking.

        Returns:
            tuple: (common_errors, improving_areas)
        """
        if not corrections_data:
            return (existing_errors or [], [])

        error_patterns = {}

        # Extract from structured grammar_issues (preferred)
        for correction in corrections_data:
            # Handle different correction structures
            grammar_issues = []

            if isinstance(correction, dict):
                # Check for grammar_issues array (from BackgroundAnalysisResponse)
                if "grammar_issues" in correction and isinstance(correction["grammar_issues"], list):
                    grammar_issues = correction["grammar_issues"]
                # Check for direct issue_type field (simplified structure)
                elif "issue_type" in correction:
                    grammar_issues = [correction]

            # Process grammar issues with structured data
            for issue in grammar_issues:
                if isinstance(issue, dict) and "issue_type" in issue:
                    # Get and normalize error type
                    error_type_raw = issue.get("issue_type", "unknown")
                    error_type = self._normalize_error_type(error_type_raw)

                    # Initialize tracking
                    if error_type not in error_patterns:
                        error_patterns[error_type] = {
                            "count": 0,
                            "severity_sum": 0.0,
                        }

                    # Increment count
                    error_patterns[error_type]["count"] += 1

                    # Track severity
                    severity_raw = issue.get("severity", "low")
                    severity_score = {
                        "critical": 1.0,
                        "high": 0.75,
                        "medium": 0.5,
                        "low": 0.25
                    }.get(str(severity_raw).lower(), 0.25)

                    error_patterns[error_type]["severity_sum"] += severity_score

        # Fallback: keyword-based extraction if no structured data
        if not error_patterns:
            error_categories = {
                "verb_conjugation": ["verb", "tense", "conjugation", "past", "present", "future"],
                "gender_agreement": ["gender", "de", "het", "der", "die", "das", "el", "la"],
                "word_order": ["word order", "syntax", "sentence structure"],
                "article_usage": ["article", "definite", "indefinite", "a", "an", "the"],
                "preposition": ["preposition", "at", "in", "on", "to"],
                "pronunciation": ["pronunciation", "sound", "accent"],
                "vocabulary": ["word choice", "vocabulary", "wrong word"]
            }

            error_counts = {}

            # Analyze corrections with keyword matching
            for correction in corrections_data:
                if isinstance(correction, dict):
                    text = (correction.get("feedback", "") +
                           " " + correction.get("category", "") +
                           " " + correction.get("type", "") +
                           " " + correction.get("description", "")).lower()
                else:
                    text = str(correction).lower()

                # Categorize errors
                for category, keywords in error_categories.items():
                    if any(keyword in text for keyword in keywords):
                        error_counts[category] = error_counts.get(category, 0) + 1

            # Convert to error_patterns format
            for category, count in error_counts.items():
                error_patterns[category] = {
                    "count": count,
                    "severity_sum": count * 0.5  # Assume medium severity
                }

        # Filter by frequency (min 2 occurrences) and calculate average severity
        common_errors = []
        min_frequency = 2  # Lower threshold for single session

        for error_type, data in error_patterns.items():
            if data["count"] >= min_frequency:
                avg_severity = data["severity_sum"] / data["count"]
                common_errors.append((error_type, data["count"], avg_severity))

        # Sort by severity (desc), then frequency (desc)
        common_errors.sort(key=lambda x: (x[2], x[1]), reverse=True)

        # Return top 5 error types
        top_errors = [error_type for error_type, _, _ in common_errors[:5]]

        # Detect improving areas (errors that decreased)
        improving_areas = []
        if existing_errors:
            existing_set = set(err.replace(" ", "_") for err in existing_errors)
            current_set = set(top_errors)

            # Errors that were common before but not anymore
            improved = existing_set - current_set
            improving_areas = [err.replace("_", " ") for err in improved]

        logger.info(f"[ERROR_EXTRACTION] Found {len(top_errors)} common errors, {len(improving_areas)} improving")

        return (top_errors, improving_areas[:3])  # Top 3 improving areas

    def _update_accuracy_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update accuracy strand based on corrections and self-monitoring OR assessment scores."""

        # 🔥 NEW: Use actual grammar score from speaking assessment if available
        if metrics.get("assessment_scores"):
            grammar_score = metrics["assessment_scores"]["grammar"]
            # Convert 0-100 score to 0-1 accuracy
            accuracy = grammar_score / 100.0
            self_corrections = 0  # No self-corrections in assessment
            logger.info(f"[DNA] Using assessment grammar score for accuracy: {grammar_score}/100 = {accuracy:.2f}")
        else:
            # Original logic for practice sessions
            corrections = metrics["corrections_received"]
            self_corrections = metrics["self_corrections"]
            turns = max(metrics["turns_count"], 1)

            # Accuracy rate (inverse of correction rate)
            external_error_rate = corrections / turns
            accuracy = max(0, 1 - external_error_rate)

        # Determine pattern
        if self_corrections > 2 and accuracy > 0.7:
            pattern = "perfectionist"
            description = "High accuracy focus, sometimes hesitates to avoid mistakes"
        elif self_corrections < 1 and accuracy < 0.6:
            pattern = "risk_taker"
            description = "Prioritizes fluency over accuracy, learns from mistakes"
        else:
            pattern = "balanced"
            description = "Good balance between accuracy and spontaneity"

        # Extract error patterns from raw corrections data
        corrections_data = metrics.get("corrections_data", [])
        existing_errors = existing.get("common_errors", []) if existing else []

        common_errors, improving_areas = self._extract_error_patterns(
            corrections_data,
            existing_errors
        )

        if existing:
            new_accuracy = existing.get("grammar_accuracy", accuracy) * (1 - alpha * weight) + accuracy * alpha * weight
            # Keep existing errors if no new corrections
            if not common_errors:
                common_errors = existing_errors
        else:
            new_accuracy = accuracy

        return {
            "pattern": pattern,
            "grammar_accuracy": round(new_accuracy, 2),
            "common_errors": common_errors,
            "improving_areas": improving_areas,
            "description": description
        }

    # ── S4: Fluency strand (transcript-based, every session) ─────────────────

    def _update_fluency_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """
        S4 — Fluency strand: transcript-based, updated every session.

        Components:
          filler_component    = 1 - min(filler_rate_per_minute / 10, 1)   [0-1]
          variance_component  = 1 - min(latency_std / 2000, 1)            [0-1]
          pause_component     = acoustic_speaking_ratio if available,
                                else derived from latency_avg              [0-1]

        score = 0.5 * filler_component + 0.3 * variance_component + 0.2 * pause_component
        EMA alpha=0.15 (slower update than transcript strands — fluency changes gradually).
        """
        filler_rate  = metrics.get("filler_rate_per_minute", 2.0)
        latency_std  = metrics.get("response_latency_std_ms", 500)
        latency_avg  = metrics.get("response_latency_avg_ms", 2000)

        # Component 1: filler density (0 fillers = 1.0, 10+/min = 0.0)
        filler_component = max(0.0, 1.0 - min(filler_rate / 10.0, 1.0))

        # Component 2: response latency variance (low variance = more fluent)
        variance_component = max(0.0, 1.0 - min(latency_std / 2000.0, 1.0))

        # Component 3: pause/flow from acoustic or latency proxy
        acoustic_speaking_ratio = metrics.get("acoustic_speaking_ratio")
        if acoustic_speaking_ratio is not None:
            pause_component = float(acoustic_speaking_ratio)  # 0-1 (0.7-0.9 is natural)
        else:
            # Proxy: high avg latency → more pauses → lower fluency
            pause_component = max(0.0, 1.0 - min(latency_avg / 5000.0, 1.0))

        raw_score = (
            0.5 * filler_component +
            0.3 * variance_component +
            0.2 * pause_component
        )
        raw_score = max(0.0, min(1.0, raw_score))

        # EMA — lower alpha for fluency (gradual change)
        fluency_alpha = 0.15
        if existing:
            score = existing.get("score", raw_score) * (1 - fluency_alpha * weight) + raw_score * fluency_alpha * weight
        else:
            score = raw_score

        score = round(max(0.0, min(1.0, score)), 2)

        # Qualitative level
        if score >= 0.75:
            level = "natural"
            description = "Speech flows naturally with minimal hesitation"
        elif score >= 0.55:
            level = "developing"
            description = "Generally fluent with occasional pauses or fillers"
        elif score >= 0.35:
            level = "building"
            description = "Developing fluency — pauses and fillers are common"
        else:
            level = "early"
            description = "Frequent pauses and hesitations — keep practising"

        return {
            "score": score,
            "level": level,
            "filler_rate": round(filler_rate, 2),
            "wpm_variance": round(latency_std, 0),
            "pause_score": round(pause_component, 2),
            "description": description,
        }

    # ── S4: Pronunciation strand (acoustic-only, voice_check / speaking_assessment) ──

    def _update_pronunciation_strand(
        self,
        existing: Optional[Dict],
        azure_result: Optional[Dict],
        session_type: str,
    ) -> Dict:
        """
        S4 — Pronunciation strand: acoustic-only, updated only when Azure result available.

        Pin guard: if azure_result is None the existing value is returned unchanged
        (same pin-not-skip semantics as other acoustic strands).

        EMA alpha=0.25 — acoustic strand, faster update (voice check is deliberate).
        """
        if azure_result is None:
            if existing:
                logger.info(f"[DNA] Pronunciation pinned (no Azure result). session_type={session_type}")
                return existing
            # No existing + no result → safe defaults (strand not yet measured)
            return {
                "score": 0.0,
                "phoneme_accuracy": 0.0,
                "prosody_score": 0.0,
                "completeness_score": 0.0,
                "fluency_score": 0.0,
                "voice_checks_count": 0,
                "last_updated_session_type": None,
                "description": "Not yet measured — complete a voice check to unlock",
            }

        pron_alpha = 0.25
        new_score        = azure_result.get("pronunciation_score", 0) / 100.0
        new_phoneme      = azure_result.get("accuracy_score", 0) / 100.0
        new_prosody      = azure_result.get("prosody_score", 0) / 100.0
        new_completeness = azure_result.get("completeness_score", 0) / 100.0
        new_fluency      = azure_result.get("fluency_score", 0) / 100.0

        if existing and existing.get("voice_checks_count", 0) > 0:
            score        = existing.get("score", new_score) * (1 - pron_alpha) + new_score * pron_alpha
            phoneme      = existing.get("phoneme_accuracy", new_phoneme) * (1 - pron_alpha) + new_phoneme * pron_alpha
            prosody      = existing.get("prosody_score", new_prosody) * (1 - pron_alpha) + new_prosody * pron_alpha
            completeness = existing.get("completeness_score", new_completeness) * (1 - pron_alpha) + new_completeness * pron_alpha
            fluency      = existing.get("fluency_score", new_fluency) * (1 - pron_alpha) + new_fluency * pron_alpha
            voice_checks_count = existing.get("voice_checks_count", 0) + 1
        else:
            score        = new_score
            phoneme      = new_phoneme
            prosody      = new_prosody
            completeness = new_completeness
            fluency      = new_fluency
            voice_checks_count = 1

        score        = round(max(0.0, min(1.0, score)), 2)
        phoneme      = round(max(0.0, min(1.0, phoneme)), 2)
        prosody      = round(max(0.0, min(1.0, prosody)), 2)
        completeness = round(max(0.0, min(1.0, completeness)), 2)
        fluency      = round(max(0.0, min(1.0, fluency)), 2)

        if score >= 0.80:
            description = "Excellent pronunciation — clear and natural"
        elif score >= 0.65:
            description = "Good pronunciation with minor accent patterns"
        elif score >= 0.45:
            description = "Developing — some phonemes need practice"
        else:
            description = "Early stage — focus on individual sounds"

        logger.info(
            f"[DNA] Pronunciation updated via {session_type}: "
            f"score={score:.2f}, phoneme={phoneme:.2f}, prosody={prosody:.2f}"
        )

        return {
            "score": score,
            "phoneme_accuracy": phoneme,
            "prosody_score": prosody,
            "completeness_score": completeness,
            "fluency_score": fluency,
            "voice_checks_count": voice_checks_count,
            "last_updated_session_type": session_type,
            "description": description,
        }

    def _update_learning_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update learning strand based on challenge acceptance and retry behavior."""
        challenges_offered = max(metrics["challenges_offered"], 1)
        challenges_accepted = metrics["challenges_accepted"]
        challenge_rate = challenges_accepted / challenges_offered

        # Determine learning type
        if challenge_rate > 0.7:
            learning_type = "explorer"
            description = "Embraces challenges, learns through exploration"
        elif challenge_rate < 0.3:
            learning_type = "cautious"
            description = "Prefers gradual progression, builds strong foundations"
        else:
            learning_type = "persistent"
            description = "Learns through repetition, prefers mastery before moving on"

        # Estimate retry rate from self-corrections (simplified)
        retry_rate = min(1.0, metrics["self_corrections"] * 0.3 + 0.5)

        if existing:
            new_challenge_rate = existing.get("challenge_acceptance", challenge_rate) * (1 - alpha * weight) + challenge_rate * alpha * weight
            new_retry_rate = existing.get("retry_rate", retry_rate) * (1 - alpha * weight) + retry_rate * alpha * weight
        else:
            new_challenge_rate = challenge_rate
            new_retry_rate = retry_rate

        return {
            "type": learning_type,
            "retry_rate": round(new_retry_rate, 2),
            "challenge_acceptance": round(new_challenge_rate, 2),
            "description": description
        }

    # =========================================================================
    # ANXIETY DETECTION HELPER METHODS
    # =========================================================================

    def _get_baseline_latency(self, recent_sessions: List[Dict]) -> float:
        """Calculate baseline response latency from recent sessions."""
        import numpy as np
        latencies = []
        for session in recent_sessions:
            strands = session.get("strand_snapshots", {})
            confidence = strands.get("confidence", {})
            # Try different field names for compatibility
            latency = (confidence.get("response_latency_avg_ms") or
                      confidence.get("response_latency") or
                      0)
            if latency and latency > 0:
                latencies.append(latency)

        return float(np.mean(latencies)) if latencies else 2000.0

    def _get_recent_challenge_rate(self, recent_sessions: List[Dict]) -> float:
        """Calculate recent challenge acceptance rate from history."""
        import numpy as np
        acceptance_rates = []
        for session in recent_sessions:
            strands = session.get("strand_snapshots", {})
            learning = strands.get("learning", {})
            rate = learning.get("challenge_acceptance")
            if rate is not None:
                acceptance_rates.append(rate)

        return float(np.mean(acceptance_rates)) if acceptance_rates else 0.5

    def _get_baseline_correction_density(self, recent_sessions: List[Dict]) -> float:
        """Calculate baseline correction density from recent sessions."""
        import numpy as np
        # Use grammar_accuracy as inverse proxy for correction density
        accuracies = []
        for session in recent_sessions:
            strands = session.get("strand_snapshots", {})
            accuracy = strands.get("accuracy", {})
            gram_acc = accuracy.get("grammar_accuracy")
            if gram_acc is not None and gram_acc > 0:
                accuracies.append(1.0 - gram_acc)  # Inverse = correction density

        return float(np.mean(accuracies)) if accuracies else 0.2

    def _get_baseline_filler_rate(self, recent_sessions: List[Dict]) -> float:
        """Calculate baseline filler word rate from recent sessions."""
        import numpy as np
        filler_rates = []
        for session in recent_sessions:
            strands = session.get("strand_snapshots", {})
            confidence = strands.get("confidence", {})
            filler = confidence.get("filler_rate_per_minute") or confidence.get("filler_rate")
            if filler is not None:
                filler_rates.append(filler)

        return float(np.mean(filler_rates)) if filler_rates else 2.0

    async def _detect_anxiety_triggers(
        self,
        user_id: str,
        language: str,
        metrics: Dict,
        session_data: Dict,
        existing_triggers: List[str] = None
    ) -> List[str]:
        """
        Detect anxiety triggers from session patterns using historical baseline analysis.

        Enhanced algorithm analyzes multiple factors:
        - Response latency spikes compared to baseline
        - Challenge avoidance patterns
        - Correction sensitivity
        - Filler word increase
        - Topic-based confidence drops

        Returns:
            List of identified anxiety triggers (max 5)
        """
        import numpy as np
        triggers = set()

        # Get recent session history for baseline comparison
        recent_sessions = await self.db.speaking_dna_history.find({
            "user_id": user_id,
            "language": language
        }).sort("week_start", -1).limit(10).to_list(length=10)

        if len(recent_sessions) < 2:
            # Not enough data for historical analysis - use simple heuristics
            logger.info("[ANXIETY] Not enough history - using simple heuristics")

            latency = metrics.get("response_latency_avg_ms", 2000)
            filler_rate = metrics.get("filler_rate_per_minute", 2.0)
            hesitation_count = metrics.get("hesitation_count", 0)

            # Simple absolute threshold detection
            if latency > 4000:
                triggers.add("thinking_pressure")
            if filler_rate > 8:
                triggers.add("speaking_anxiety")
            if hesitation_count > 5:
                triggers.add("hesitation_pattern")

            # Topic-based (simple)
            topics = session_data.get("topics_discussed", [])
            for topic in topics:
                if latency > 4000:  # High latency with this topic
                    triggers.add(f"topic:{topic}")
                    break  # Only add one topic trigger

            return list(triggers)[:5]

        # Enhanced multi-factor analysis with historical baselines
        logger.info(f"[ANXIETY] Analyzing with {len(recent_sessions)} historical sessions")

        # Factor 1: Response Latency Spikes
        baseline_latency = self._get_baseline_latency(recent_sessions)
        current_latency = metrics.get("response_latency_avg_ms", 2000)

        if current_latency > baseline_latency * 1.5:  # 50% spike
            triggers.add("thinking_pressure")
            logger.info(
                f"[ANXIETY] Latency spike detected: {current_latency}ms vs "
                f"baseline {baseline_latency}ms"
            )

        # Factor 2: Challenge Avoidance
        recent_challenge_rate = self._get_recent_challenge_rate(recent_sessions)
        current_challenge_rate = (
            session_data.get("challenges_accepted", 0) /
            max(session_data.get("challenges_offered", 1), 1)
        )

        if current_challenge_rate < recent_challenge_rate * 0.7:  # 30% drop
            triggers.add("difficulty_level")
            logger.info(
                f"[ANXIETY] Challenge avoidance detected: {current_challenge_rate:.2f} vs "
                f"baseline {recent_challenge_rate:.2f}"
            )

        # Factor 3: Correction Sensitivity (perfectionism)
        baseline_correction_density = self._get_baseline_correction_density(recent_sessions)
        current_correction_density = (
            len(session_data.get("corrections_received", [])) /
            max(len(session_data.get("user_turns", [])), 1)
        )

        if (current_correction_density > baseline_correction_density * 1.3 and
            current_challenge_rate < recent_challenge_rate):
            triggers.add("perfectionism")
            logger.info(
                f"[ANXIETY] Correction sensitivity detected: {current_correction_density:.2f} vs "
                f"baseline {baseline_correction_density:.2f}"
            )

        # Factor 4: Filler Word Increase (nervousness)
        baseline_filler_rate = self._get_baseline_filler_rate(recent_sessions)
        current_filler_rate = metrics.get("filler_rate_per_minute", 2.0)

        if current_filler_rate > baseline_filler_rate * 1.5:  # 50% increase
            triggers.add("speaking_anxiety")
            logger.info(
                f"[ANXIETY] Filler word spike detected: {current_filler_rate:.1f} vs "
                f"baseline {baseline_filler_rate:.1f}"
            )

        # Factor 5: Topic-Based Triggers (if latency spike or filler spike)
        topics = session_data.get("topics_discussed", [])
        if topics and (current_latency > baseline_latency * 1.4 or
                      current_filler_rate > baseline_filler_rate * 1.4):
            # Only add first topic as trigger (most likely culprit)
            triggers.add(f"topic:{topics[0]}")
            logger.info(f"[ANXIETY] Topic trigger detected: {topics[0]}")

        # Merge with existing triggers (keep historical context)
        if existing_triggers:
            # Keep only non-topic triggers from history
            historical_general = [t for t in existing_triggers if not t.startswith("topic:")]
            all_triggers = set(list(triggers) + historical_general[:2])  # Keep 2 historical
        else:
            all_triggers = triggers

        final_triggers = list(all_triggers)[:5]
        logger.info(f"[ANXIETY] Final triggers: {final_triggers}")

        return final_triggers

    async def _update_emotional_strand(
        self,
        existing: Optional[Dict],
        metrics: Dict,
        alpha: float,
        weight: float,
        user_id: str,
        language: str,
        session_data: Dict = None
    ) -> Dict:
        """Update emotional strand based on session patterns and anxiety triggers."""
        latency = metrics["response_latency_avg_ms"]
        filler_rate = metrics["filler_rate_per_minute"]
        hesitation_count = metrics.get("hesitation_count", 0)

        # Calculate confidence based on multiple factors
        latency_confidence = max(0, 1 - (latency / 5000))  # <5s is good
        filler_confidence = max(0, 1 - (filler_rate / 10))  # <10/min is good
        hesitation_confidence = max(0, 1 - (hesitation_count / 5))  # <5 is good

        current_confidence = (latency_confidence * 0.4 + filler_confidence * 0.3 + hesitation_confidence * 0.3)

        # Estimate start vs end confidence
        if existing:
            prev_end_confidence = existing.get("session_end_confidence", 0.6)
            # Assume we improve during session
            start_confidence = prev_end_confidence * 0.9
            end_confidence = prev_end_confidence * (1 - alpha * weight) + current_confidence * alpha * weight
            end_confidence = max(0.3, min(0.95, end_confidence))
        else:
            start_confidence = 0.5
            end_confidence = current_confidence

        # Determine emotional pattern
        improvement = end_confidence - start_confidence
        if improvement > 0.15:
            pattern = "slow_warmer"
            description = "Needs warm-up time, gains confidence as session progresses"
        elif improvement < 0.05:
            pattern = "consistent"
            description = "Maintains steady emotional state throughout sessions"
        else:
            pattern = "quick_starter"
            description = "Starts confident and maintains energy throughout"

        # Detect anxiety triggers with historical baseline analysis
        existing_triggers = existing.get("anxiety_triggers", []) if existing else []
        anxiety_triggers = await self._detect_anxiety_triggers(
            user_id,
            language,
            metrics,
            session_data or {},
            existing_triggers
        )

        return {
            "pattern": pattern,
            "session_start_confidence": round(start_confidence, 2),
            "session_end_confidence": round(end_confidence, 2),
            "anxiety_triggers": anxiety_triggers,
            "description": description
        }

    def _determine_overall_profile(self, strands: Dict) -> Dict:
        """Determine the overall speaker archetype from strand combination."""
        rhythm_type = strands["rhythm"]["type"]
        accuracy_pattern = strands["accuracy"]["pattern"]
        learning_type = strands["learning"]["type"]

        # Find matching archetype
        key = (rhythm_type, accuracy_pattern, learning_type)
        archetype = self.ARCHETYPES.get(key)

        if not archetype:
            # Default archetype if no exact match
            archetype = {
                "name": "The Unique Learner",
                "summary": "A distinctive learner with their own approach to language acquisition.",
                "coach_approach": "adaptive_guide"
            }

        # Determine strengths and growth areas
        strengths = []
        growth_areas = []

        if strands["confidence"]["score"] > 0.7:
            strengths.append("speaking_confidence")
        else:
            growth_areas.append("speaking_confidence")

        if strands["accuracy"]["grammar_accuracy"] > 0.75:
            strengths.append("accuracy_focus")
        else:
            growth_areas.append("grammar_accuracy")

        if strands["vocabulary"]["style"] == "adventurous":
            strengths.append("vocabulary_exploration")
        else:
            growth_areas.append("vocabulary_variety")

        if strands["learning"]["challenge_acceptance"] > 0.6:
            strengths.append("challenge_acceptance")
        else:
            growth_areas.append("taking_challenges")

        return {
            "speaker_archetype": archetype["name"],
            "summary": archetype["summary"],
            "coach_approach": archetype["coach_approach"],
            "strengths": strengths[:3],  # Top 3
            "growth_areas": growth_areas[:3]  # Top 3
        }

    # =========================================================================
    # BREAKTHROUGH DETECTION
    # =========================================================================

    async def _detect_breakthroughs(
        self,
        user_id: str,
        language: str,
        existing_profile: Optional[Dict],
        new_strands: Dict,
        session_data: Dict
    ) -> List[Dict]:
        """Detect any breakthrough moments from this session."""
        breakthroughs = []

        if not existing_profile:
            # First session - no breakthroughs to detect yet
            return breakthroughs

        old_strands = existing_profile.get("dna_strands", {})

        # Check confidence jump
        old_confidence = old_strands.get("confidence", {}).get("score", 0)
        new_confidence = new_strands["confidence"]["score"]
        if new_confidence - old_confidence >= self.BREAKTHROUGH_THRESHOLDS["confidence_jump"]:
            breakthroughs.append({
                "user_id": user_id,
                "language": language,
                "breakthrough_type": "confidence_jump",
                "category": "confidence",
                "title": "Confidence Breakthrough!",
                "description": f"Your confidence score jumped from {int(old_confidence*100)}% to {int(new_confidence*100)}%!",
                "emoji": "🚀",
                "metrics": {
                    "before": {"score": old_confidence},
                    "after": {"score": new_confidence},
                    "improvement_percent": round((new_confidence - old_confidence) * 100, 1)
                },
                "context": {
                    "session_type": session_data.get("session_type", "learning"),
                    "topics": session_data.get("topics_discussed", [])
                }
            })

        # Check vocabulary expansion
        old_vocab = old_strands.get("vocabulary", {}).get("unique_words_per_session", 0)
        new_vocab = new_strands["vocabulary"]["unique_words_per_session"]
        if new_vocab - old_vocab >= self.BREAKTHROUGH_THRESHOLDS["vocabulary_expansion"]:
            breakthroughs.append({
                "user_id": user_id,
                "language": language,
                "breakthrough_type": "vocabulary_expansion",
                "category": "vocabulary",
                "title": "Vocabulary Explosion!",
                "description": f"You used {int(new_vocab - old_vocab)} more unique words than usual!",
                "emoji": "📚",
                "metrics": {
                    "before": {"unique_words": old_vocab},
                    "after": {"unique_words": new_vocab},
                    "improvement_percent": round(((new_vocab - old_vocab) / max(old_vocab, 1)) * 100, 1)
                },
                "context": {
                    "session_type": session_data.get("session_type", "learning")
                }
            })

        # Check challenge acceptance milestone
        old_challenge_rate = old_strands.get("learning", {}).get("challenge_acceptance", 0)
        new_challenge_rate = new_strands["learning"]["challenge_acceptance"]
        if old_challenge_rate < 0.5 and new_challenge_rate >= 0.5:
            breakthroughs.append({
                "user_id": user_id,
                "language": language,
                "breakthrough_type": "challenge_accepted",
                "category": "learning",
                "title": "Challenge Conqueror!",
                "description": "You're now accepting more than half of the challenges offered!",
                "emoji": "💪",
                "metrics": {
                    "before": {"challenge_rate": old_challenge_rate},
                    "after": {"challenge_rate": new_challenge_rate}
                },
                "context": {
                    "session_type": session_data.get("session_type", "learning")
                }
            })

        # Check confidence level upgrade
        old_level = old_strands.get("confidence", {}).get("level", "hesitant")
        new_level = new_strands["confidence"]["level"]
        level_order = ["hesitant", "building", "comfortable", "fluent"]
        if level_order.index(new_level) > level_order.index(old_level):
            breakthroughs.append({
                "user_id": user_id,
                "language": language,
                "breakthrough_type": "confidence_level_up",
                "category": "confidence",
                "title": f"Level Up: {new_level.title()}!",
                "description": f"You've graduated from '{old_level}' to '{new_level}' confidence level!",
                "emoji": "⬆️",
                "metrics": {
                    "before": {"level": old_level},
                    "after": {"level": new_level}
                },
                "context": {
                    "session_type": session_data.get("session_type", "learning")
                }
            })

        return breakthroughs

    def _generate_session_insights(self, metrics: Dict, strands: Dict) -> Dict:
        """Generate human-readable insights from the session."""
        insights = []

        # Speed insight
        wpm = metrics["words_per_minute"]
        if wpm > 100:
            insights.append("You spoke at a great conversational pace today!")
        elif wpm < 60:
            insights.append("You took your time to think through responses - that's perfectly fine!")

        # Confidence insight
        if strands["confidence"]["trend"] == "improving":
            insights.append("Your confidence is trending upward - keep it up!")

        # Vocabulary insight
        if strands["vocabulary"]["style"] == "adventurous":
            insights.append("You're experimenting with new vocabulary - great for growth!")

        return {
            "insights": insights,
            "highlight_stat": {
                "label": "Unique words used",
                "value": metrics["unique_words"]
            }
        }

    # =========================================================================
    # COACH INSTRUCTIONS
    # =========================================================================

    async def build_coach_instructions(
        self,
        user_id: str,
        language: str,
        session_type: str
    ) -> str:
        """
        Build personalized coaching instructions for the AI tutor.

        This is called at the start of each session to inject DNA-aware
        context into the tutor's system prompt.

        Results are cached for 10 minutes to improve performance.
        """
        try:
            # Check cache first
            cache_key = f"{user_id}:{language}:{session_type}"
            now = datetime.utcnow().timestamp()

            if cache_key in self._coach_instructions_cache:
                cached_instructions, cached_time = self._coach_instructions_cache[cache_key]
                if now - cached_time < self._cache_ttl:
                    logger.info(f"[DNA] Using cached coach instructions (age: {int(now - cached_time)}s)")
                    return cached_instructions

            logger.info(f"[DNA] Generating fresh coach instructions")

            profile = await self.db.speaking_dna_profiles.find_one({
                "user_id": user_id,
                "language": language
            })

            if not profile:
                default_instructions = self._get_default_coach_instructions(session_type)
                # Cache default instructions too (shorter TTL)
                self._coach_instructions_cache[cache_key] = (default_instructions, now)
                return default_instructions

            strands = profile.get("dna_strands", {})
            overall = profile.get("overall_profile", {})

            # Get recent uncelebrated breakthroughs
            recent_breakthroughs = await self.db.speaking_breakthroughs.find({
                "user_id": user_id,
                "language": language,
                "celebrated": False
            }).sort("created_at", -1).limit(3).to_list(3)

            # Build instructions
            instructions = f"""
## Learner Speaking DNA Profile

This learner is "{overall.get('speaker_archetype', 'a unique learner')}" - {overall.get('summary', '')}

### Key Characteristics:
- **Speaking Rhythm**: {strands.get('rhythm', {}).get('type', 'unknown')} - {strands.get('rhythm', {}).get('description', '')}
- **Confidence Level**: {strands.get('confidence', {}).get('level', 'building')} ({strands.get('confidence', {}).get('trend', 'stable')} trend)
- **Vocabulary Style**: {strands.get('vocabulary', {}).get('style', 'balanced')} - {strands.get('vocabulary', {}).get('description', '')}
- **Learning Type**: {strands.get('learning', {}).get('type', 'persistent')} - {strands.get('learning', {}).get('description', '')}
- **Emotional Pattern**: {strands.get('emotional', {}).get('pattern', 'consistent')} - {strands.get('emotional', {}).get('description', '')}

### Coaching Approach: {overall.get('coach_approach', 'balanced_guide')}
- Strengths to leverage: {', '.join(overall.get('strengths', ['consistency']))}
- Growth areas to gently encourage: {', '.join(overall.get('growth_areas', ['confidence']))}
"""

            # Add breakthrough celebration instructions
            if recent_breakthroughs:
                instructions += "\n### Recent Breakthroughs to Celebrate:\n"
                for bt in recent_breakthroughs:
                    instructions += f"- {bt['emoji']} {bt['title']}: {bt['description']}\n"
                instructions += "\nMention one of these achievements early in the session to boost motivation!\n"

            # Add session-type specific guidance
            if session_type == "learning":
                instructions += """
### Learning Session Guidance:
- Follow the structured lesson plan
- Be patient with this learner's natural pace
- Offer challenges based on their challenge_acceptance rate
"""
            elif session_type == "freestyle":
                instructions += """
### Freestyle Session Guidance:
- Let the learner lead the conversation
- Encourage vocabulary experimentation based on their style
- Match their energy and pace
"""
            elif session_type == "news":
                instructions += """
### News Session Guidance:
- Help with complex vocabulary from the article
- Be patient as they formulate opinions
- Encourage them to express their thoughts even imperfectly
"""

            # Add anxiety awareness if applicable
            triggers = strands.get("emotional", {}).get("anxiety_triggers", [])
            if triggers:
                instructions += f"\n### Be Mindful Of:\nThis learner may feel anxious with: {', '.join(triggers)}. Approach these gently.\n"

            # Cache the instructions before returning
            cache_key = f"{user_id}:{language}:{session_type}"
            self._coach_instructions_cache[cache_key] = (instructions, datetime.utcnow().timestamp())
            logger.info(f"[DNA] Cached coach instructions (TTL: {self._cache_ttl}s)")

            return instructions

        except Exception as e:
            logger.error(f"[DNA] Error building coach instructions: {str(e)}", exc_info=True)
            default_instructions = self._get_default_coach_instructions(session_type)
            # Cache error fallback too
            cache_key = f"{user_id}:{language}:{session_type}"
            self._coach_instructions_cache[cache_key] = (default_instructions, datetime.utcnow().timestamp())
            return default_instructions

    def _get_default_coach_instructions(self, session_type: str) -> str:
        """Default instructions for users without a DNA profile yet."""
        return f"""
## New Learner

This learner hasn't built their Speaking DNA profile yet. Use this session to:
- Assess their speaking confidence and pace
- Note their vocabulary comfort level
- Observe how they handle corrections
- Be encouraging and supportive as they're just starting their journey

Session type: {session_type}
"""

    # =========================================================================
    # S2.1 CAUSAL SENTENCE GENERATION
    # =========================================================================

    async def _generate_causal_sentence(
        self,
        previous_strands: Dict[str, Any],
        updated_strands: Dict[str, Any],
        session_data: Dict[str, Any],
        language: str,
    ) -> Optional[str]:
        """Generate a one-sentence narrative explaining the biggest strand delta."""
        try:
            # Compute deltas for the six ceremony strands (S4: pronunciation + fluency added)
            STRAND_SCORE = {
                "rhythm":        lambda s: s.get("consistency_score", 0) * 100,
                "confidence":    lambda s: s.get("score", 0) * 100,
                "pronunciation": lambda s: s.get("score", 0) * 100,
                "vocabulary":    lambda s: s.get("new_word_attempt_rate", 0) * 100,
                "accuracy":      lambda s: s.get("grammar_accuracy", 0) * 100,
                "fluency":       lambda s: s.get("score", 0) * 100,
            }
            deltas: Dict[str, float] = {}
            for strand, scorer in STRAND_SCORE.items():
                prev = scorer(previous_strands.get(strand, {}))
                curr = scorer(updated_strands.get(strand, {}))
                if prev or curr:
                    deltas[strand] = round(curr - prev, 1)

            if not deltas:
                return _CAUSAL_FALLBACK

            biggest_strand = max(deltas, key=lambda k: abs(deltas[k]))
            biggest_delta  = deltas[biggest_strand]

            if abs(biggest_delta) < 2:
                return _CAUSAL_FALLBACK

            # Build a minimal prompt — keep the model call lightweight
            topics = ", ".join(session_data.get("topics_discussed", [])) or "general conversation"
            session_type = session_data.get("session_type", "learning")

            from openai_client import get_async_openai
            response = await get_async_openai().chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You write one concise English sentence (max 20 words) explaining "
                            "why a language learner's DNA strand changed during a practice session. "
                            "Be specific and encouraging. No emojis."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Strand: {biggest_strand}, delta: {biggest_delta:+.0f} points. "
                            f"Session type: {session_type}. Topics: {topics}. "
                            f"Language: {language}. Write the causal sentence."
                        ),
                    },
                ],
                temperature=0.4,
                max_tokens=60,
            )
            sentence = response.choices[0].message.content.strip().rstrip(".")
            return sentence if sentence else _CAUSAL_FALLBACK
        except Exception as e:
            logger.warning(f"[DNA] Causal sentence generation failed (non-fatal): {e}")
            return _CAUSAL_FALLBACK

    # =========================================================================
    # WEEKLY SNAPSHOT CREATION
    # =========================================================================

    async def _create_weekly_snapshot(
        self,
        user_id: str,
        language: str,
        strands: Dict,
        session_duration_minutes: float,
        breakthroughs_count: int,
        acoustic_metrics: Optional[Dict] = None
    ) -> None:
        """
        Create or update weekly snapshot for DNA evolution tracking.

        This method stores a weekly snapshot of the user's DNA strands
        for the evolution timeline visualization. Snapshots are created
        for the Monday of the current week (week start).

        Args:
            user_id: User ID string
            language: Target language
            strands: Complete DNA strands dict
            session_duration_minutes: Duration of this session
            breakthroughs_count: Number of breakthroughs in this session
            acoustic_metrics: Optional acoustic metrics dict (pitch, quality, rate, etc.)
        """
        try:
            now = datetime.utcnow()

            # Calculate week start (Monday of current week at 00:00:00 UTC)
            week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start -= timedelta(days=week_start.weekday())  # Go to Monday

            # Calculate ISO week number
            week_number = week_start.isocalendar()[1]

            logger.info(f"[DNA] Creating/updating weekly snapshot for week starting {week_start.date()}")

            # Check if snapshot already exists for this week
            existing_snapshot = await self.db.speaking_dna_history.find_one({
                "user_id": user_id,
                "language": language,
                "week_start": week_start
            })

            if existing_snapshot:
                # Update existing snapshot (increment counters)
                logger.info(f"[DNA] Updating existing snapshot for week {week_number}")

                update_set = {
                    "strand_snapshots": strands,  # Always update to latest strands
                    "updated_at": now
                }

                # Update acoustic metrics if provided (always use latest)
                if acoustic_metrics:
                    update_set["acoustic_metrics_snapshot"] = acoustic_metrics

                await self.db.speaking_dna_history.update_one(
                    {"_id": existing_snapshot["_id"]},
                    {
                        "$set": update_set,
                        "$inc": {
                            "week_stats.sessions_completed": 1,
                            "week_stats.total_minutes": session_duration_minutes,
                            "week_stats.breakthroughs_count": breakthroughs_count
                        }
                    }
                )
                logger.info(f"[DNA] Weekly snapshot updated successfully")

            else:
                # Create new snapshot
                logger.info(f"[DNA] Creating new snapshot for week {week_number}")

                snapshot_doc = {
                    "user_id": user_id,
                    "language": language,
                    "week_start": week_start,
                    "week_number": week_number,
                    "strand_snapshots": strands,
                    "week_stats": {
                        "sessions_completed": 1,
                        "total_minutes": session_duration_minutes,
                        "breakthroughs_count": breakthroughs_count
                    },
                    "created_at": now,
                    "updated_at": now
                }

                # Add acoustic metrics if provided
                if acoustic_metrics:
                    snapshot_doc["acoustic_metrics_snapshot"] = acoustic_metrics

                await self.db.speaking_dna_history.insert_one(snapshot_doc)
                logger.info(f"[DNA] New weekly snapshot created successfully")

        except Exception as e:
            logger.error(f"[DNA] Error creating weekly snapshot (non-fatal): {str(e)}", exc_info=True)
            # Don't raise - weekly snapshots are nice-to-have, not critical

    async def _append_session_history(
        self,
        user_id: str,
        language: str,
        updated_strands: Dict,
        session_number: int,
        session_type: str,
        voice_checks_count: int,
    ) -> None:
        """
        Append per-session and per-voice-check history points to each strand.

        Transcript strands (vocabulary, accuracy, fluency): one entry per session.
        Acoustic strands (rhythm, confidence, pronunciation): one entry per voice check only.

        History arrays are capped at 50 entries (oldest popped).
        """
        TRANSCRIPT_STRANDS = {"vocabulary", "accuracy", "fluency"}
        ACOUSTIC_STRANDS   = {"rhythm", "confidence", "pronunciation"}

        now = datetime.utcnow()

        def _score(strands: Dict, key: str) -> float:
            s = strands.get(key) or {}
            if key == "rhythm":
                return float(s.get("consistency_score") or 0.0)
            if key == "confidence":
                return float(s.get("score") or 0.0)
            if key == "pronunciation":
                return float(s.get("score") or 0.0)
            if key == "vocabulary":
                return float(s.get("new_word_attempt_rate") or 0.0)
            if key == "accuracy":
                return float(s.get("grammar_accuracy") or 0.0)
            if key == "fluency":
                return float(s.get("score") or 0.0)
            return 0.0

        is_voice_check = session_type in {"voice_check", "speaking_assessment"}

        try:
            update_ops: Dict[str, Any] = {}

            for strand_key in TRANSCRIPT_STRANDS:
                value = round(_score(updated_strands, strand_key), 4)
                entry = {
                    "session_number": session_number,
                    "value": value,
                    "timestamp": now,
                }
                # Push to array, slice to last 50
                field = f"dna_strands.{strand_key}.history"
                update_ops[field] = entry

            if is_voice_check:
                for strand_key in ACOUSTIC_STRANDS:
                    value = round(_score(updated_strands, strand_key), 4)
                    entry = {
                        "voice_check_number": voice_checks_count,
                        "value": value,
                        "timestamp": now,
                    }
                    field = f"dna_strands.{strand_key}.voice_check_history"
                    update_ops[field] = entry

            if not update_ops:
                return

            # Use $push with $each + $slice to cap array at 50
            push_ops = {}
            for field, entry in update_ops.items():
                push_ops[field] = {"$each": [entry], "$slice": -50}

            await self.db.speaking_dna_profiles.update_one(
                {"user_id": user_id, "language": language},
                {"$push": push_ops}
            )
            logger.info(
                f"[DNA] Session history appended: session_number={session_number}, "
                f"is_voice_check={is_voice_check}, strands_updated={list(update_ops.keys())}"
            )
        except Exception as e:
            logger.error(f"[DNA] Error appending session history (non-fatal): {e}", exc_info=True)

    # =========================================================================
    # PROFILE RETRIEVAL & EVOLUTION
    # =========================================================================

    async def get_dna_profile(self, user_id: str, language: str) -> Optional[Dict]:
        """Get the current DNA profile for a user."""
        try:
            profile = await self.db.speaking_dna_profiles.find_one({
                "user_id": user_id,
                "language": language
            })

            if profile:
                profile["_id"] = str(profile["_id"])

            return profile

        except Exception as e:
            logger.error(f"[DNA] Error getting profile: {str(e)}", exc_info=True)
            return None

    async def get_dna_evolution(
        self,
        user_id: str,
        language: str,
        weeks: int = 12,  # kept for API compat but now means "last N transcript points"
    ) -> List[Dict]:
        """
        Get DNA evolution history for visualization.

        Returns session-level history for transcript strands (vocabulary, accuracy, fluency).
        The `weeks` param is repurposed as max_points for the last N sessions (default 12).
        """
        try:
            profile = await self.db.speaking_dna_profiles.find_one({
                "user_id": user_id,
                "language": language,
            })
            if not profile:
                return []

            strands = profile.get("dna_strands", {})
            TRANSCRIPT_STRANDS = ["vocabulary", "accuracy", "fluency"]

            # Build unified timeline: each unique session_number is one point
            # Aggregate from all transcript strand histories
            session_map: Dict[int, Dict] = {}  # session_number -> {strand: value, timestamp}

            for strand_key in TRANSCRIPT_STRANDS:
                history = strands.get(strand_key, {}).get("history", [])
                for entry in history:
                    sn = entry.get("session_number")
                    if sn is None:
                        continue
                    if sn not in session_map:
                        session_map[sn] = {
                            "session_number": sn,
                            "timestamp": entry.get("timestamp"),
                            "strand_scores": {},
                        }
                    session_map[sn]["strand_scores"][strand_key] = entry.get("value", 0.0)
                    # Use most recent timestamp for this session
                    ts = entry.get("timestamp")
                    if ts and (not session_map[sn]["timestamp"] or ts > session_map[sn]["timestamp"]):
                        session_map[sn]["timestamp"] = ts

            # Sort chronologically, cap to last `weeks` points
            result = sorted(session_map.values(), key=lambda x: x["session_number"])
            result = result[-weeks:]  # last N points

            # Serialize timestamps
            for entry in result:
                ts = entry.get("timestamp")
                if ts and hasattr(ts, "isoformat"):
                    entry["timestamp"] = ts.isoformat()

            return result
        except Exception as e:
            logger.error(f"[DNA] Error getting evolution: {e}", exc_info=True)
            return []

    async def get_voice_check_evolution(
        self,
        user_id: str,
        language: str,
    ) -> List[Dict]:
        """
        Get acoustic strand evolution using Voice Check events only.

        Returns one data point per Voice Check for rhythm, confidence, pronunciation.
        """
        try:
            profile = await self.db.speaking_dna_profiles.find_one({
                "user_id": user_id,
                "language": language,
            })
            if not profile:
                return []

            strands = profile.get("dna_strands", {})
            ACOUSTIC_STRANDS = ["rhythm", "confidence", "pronunciation"]

            # Build unified timeline: each unique voice_check_number is one point
            vc_map: Dict[int, Dict] = {}

            for strand_key in ACOUSTIC_STRANDS:
                history = strands.get(strand_key, {}).get("voice_check_history", [])
                for entry in history:
                    vcn = entry.get("voice_check_number")
                    if vcn is None:
                        continue
                    if vcn not in vc_map:
                        vc_map[vcn] = {
                            "voice_check_number": vcn,
                            "timestamp": entry.get("timestamp"),
                            "strand_scores": {},
                        }
                    vc_map[vcn]["strand_scores"][strand_key] = entry.get("value", 0.0)

            result = sorted(vc_map.values(), key=lambda x: x["voice_check_number"])

            for entry in result:
                ts = entry.get("timestamp")
                if ts and hasattr(ts, "isoformat"):
                    entry["timestamp"] = ts.isoformat()

            return result
        except Exception as e:
            logger.error(f"[DNA] Error getting voice check evolution: {e}", exc_info=True)
            return []

    async def get_acoustic_evolution(
        self,
        user_id: str,
        language: str,
        weeks: int = 12
    ) -> List[Dict]:
        """
        Get acoustic metrics evolution history for Voice Fingerprint visualization.

        Returns weekly snapshots containing only acoustic metrics data:
        - pitch (Hz)
        - quality (%)
        - rate (WPM)
        - energy (dB)
        - fluency (filler words/min)
        - stability (shimmer %)

        Args:
            user_id: User ID string
            language: Target language
            weeks: Number of weeks to retrieve (default 12)

        Returns:
            List of dicts with week_start, week_number, and acoustic_metrics
        """
        try:
            history = await self.db.speaking_dna_history.find({
                "user_id": user_id,
                "language": language,
                "acoustic_metrics_snapshot": {"$exists": True}  # Only get snapshots with acoustic data
            }).sort("week_start", -1).limit(weeks).to_list(weeks)

            # Extract only acoustic metrics and metadata
            acoustic_evolution = []
            for entry in history:
                # Convert datetime to ISO string for JavaScript parsing
                week_start = entry["week_start"]
                if week_start and hasattr(week_start, 'isoformat'):
                    week_start = week_start.isoformat()

                acoustic_evolution.append({
                    "week_start": week_start,
                    "week_number": entry["week_number"],
                    "acoustic_metrics": entry.get("acoustic_metrics_snapshot", {})
                })

            return list(reversed(acoustic_evolution))  # Chronological order

        except Exception as e:
            logger.error(f"[DNA] Error getting acoustic evolution: {str(e)}", exc_info=True)
            return []

    async def get_breakthroughs(
        self,
        user_id: str,
        language: str,
        limit: int = 20,
        uncelebrated_only: bool = False
    ) -> List[Dict]:
        """Get breakthrough moments for a user."""
        try:
            query = {
                "user_id": user_id,
                "language": language
            }

            if uncelebrated_only:
                query["celebrated"] = False

            breakthroughs = await self.db.speaking_breakthroughs.find(query).sort(
                "created_at", -1
            ).limit(limit).to_list(limit)

            # Ensure all breakthroughs have required fields with defaults
            for bt in breakthroughs:
                bt["_id"] = str(bt["_id"])

                # Convert datetime fields to ISO strings for JavaScript parsing
                if "created_at" in bt and bt["created_at"]:
                    bt["created_at"] = bt["created_at"].isoformat()
                if "celebrated_at" in bt and bt["celebrated_at"]:
                    bt["celebrated_at"] = bt["celebrated_at"].isoformat()

                # Add defaults for any missing fields
                if not bt.get("context") or not isinstance(bt.get("context"), dict):
                    bt["context"] = {"session_type": "learning"}
                else:
                    bt["context"].setdefault("session_type", "learning")

                bt.setdefault("celebrated", False)
                bt.setdefault("shared", False)

                if not bt.get("metrics") or not isinstance(bt.get("metrics"), dict):
                    bt["metrics"] = {"before": {}, "after": {}}
                else:
                    bt["metrics"].setdefault("before", {})
                    bt["metrics"].setdefault("after", {})

                bt.setdefault("emoji", "🎉")
                bt.setdefault("title", "Breakthrough")
                bt.setdefault("description", "You made progress!")
                bt.setdefault("category", "confidence")
                bt.setdefault("breakthrough_type", "progress")

            return breakthroughs

        except Exception as e:
            logger.error(f"[DNA] Error getting breakthroughs: {str(e)}", exc_info=True)
            return []

    async def mark_breakthrough_celebrated(self, breakthrough_id: str) -> bool:
        """Mark a breakthrough as celebrated."""
        try:
            result = await self.db.speaking_breakthroughs.update_one(
                {"_id": breakthrough_id},
                {"$set": {"celebrated": True}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"[DNA] Error marking breakthrough celebrated: {str(e)}", exc_info=True)
            return False


# ──────────────────────────────────────────────────────────────────────────────
# S1.7 — Breakthrough push notification helper
# ──────────────────────────────────────────────────────────────────────────────

_BREAKTHROUGH_COPY: Dict[str, Dict[str, str]] = {
    "confidence_breakthrough": {
        "title": "Your confidence hit a new high!",
        "body":  "Open MyTaco to reveal what changed.",
    },
    "vocabulary_milestone": {
        "title": "You unlocked a vocab milestone!",
        "body":  "See what changed in your DNA tab.",
    },
    "accuracy_breakthrough": {
        "title": "Your accuracy just leveled up.",
        "body":  "Open MyTaco to see the detail.",
    },
    "rhythm_breakthrough": {
        "title": "Your rhythm is more natural now.",
        "body":  "Open MyTaco to see the detail.",
    },
}
_BREAKTHROUGH_COPY_DEFAULT = {
    "title": "You hit a breakthrough!",
    "body":  "Open MyTaco to reveal what changed.",
}

_COOLDOWN_HOURS = 24


async def _send_breakthrough_push(user_id: str, breakthrough: Dict[str, Any]) -> None:
    """
    Send a push notification for a breakthrough.

    Enforces a per-user 24-hour cooldown via a Redis key; if Redis is
    unavailable the push is sent anyway (fail-open, not fail-closed).
    Respects the user's notification preferences — no push if push_token absent
    or notifications disabled.
    """
    bt_type = breakthrough.get("breakthrough_type", "")
    copy = _BREAKTHROUGH_COPY.get(bt_type, _BREAKTHROUGH_COPY_DEFAULT)

    # ── Cooldown check ───────────────────────────────────────────────────────
    cooldown_key = f"breakthrough_push_cooldown:{user_id}"
    try:
        from redis_client import redis_client as _redis
        if _redis and await _redis.exists(cooldown_key):
            logger.info(
                f"[BREAKTHROUGH_PUSH] Cooldown active for user {user_id} — skipping push"
            )
            logger.info(f"[TELEMETRY] breakthrough_push_cooldown_skipped user={user_id} type={bt_type}")
            return
    except Exception as _redis_err:
        logger.warning(f"[BREAKTHROUGH_PUSH] Redis unavailable for cooldown check: {_redis_err} — proceeding")

    # ── Fetch user push token and notification preferences ───────────────────
    try:
        user = await database.users.find_one(
            {"_id": ObjectId(user_id)},
            {"push_token": 1, "notifications_enabled": 1},
        )
    except Exception:
        user = await database.users.find_one(
            {"id": user_id},
            {"push_token": 1, "notifications_enabled": 1},
        )

    if not user:
        logger.warning(f"[BREAKTHROUGH_PUSH] User {user_id} not found — skipping push")
        return

    push_token = user.get("push_token")
    if not push_token:
        logger.info(f"[BREAKTHROUGH_PUSH] User {user_id} has no push token — skipping")
        return

    if user.get("notifications_enabled") is False:
        logger.info(f"[BREAKTHROUGH_PUSH] Notifications disabled for user {user_id} — skipping")
        return

    # ── Send ─────────────────────────────────────────────────────────────────
    from notification_service import send_push_notification

    bt_id = breakthrough.get("_id", "")
    success = await send_push_notification(
        push_token=push_token,
        title=copy["title"],
        body=copy["body"],
        data={
            "type": "breakthrough",
            "deep_link": "mytacoai://dna/breakthroughs",
            "breakthrough_id": str(bt_id),
            "breakthrough_type": bt_type,
        },
        user_id=user_id,
        priority="high",
    )

    if success:
        logger.info(
            f"[BREAKTHROUGH_PUSH] ✅ Sent to user {user_id}, type={bt_type}"
        )
        logger.info(f"[TELEMETRY] breakthrough_push_sent user={user_id} type={bt_type}")

        # Set cooldown key (expires after 24 hours)
        try:
            from redis_client import redis_client as _redis
            if _redis:
                await _redis.setex(cooldown_key, _COOLDOWN_HOURS * 3600, "1")
        except Exception as _redis_err:
            logger.warning(f"[BREAKTHROUGH_PUSH] Could not set cooldown key: {_redis_err}")
    else:
        logger.warning(f"[BREAKTHROUGH_PUSH] Push send returned false for user {user_id}")


# Singleton instance
speaking_dna_service = SpeakingDNAService()
