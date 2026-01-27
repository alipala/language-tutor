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

logger = logging.getLogger(__name__)


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
    SESSION_WEIGHTS = {
        "learning": {
            "rhythm": 0.8,
            "confidence": 1.0,
            "vocabulary": 0.7,
            "accuracy": 1.0,
            "learning": 1.0,
            "emotional": 0.9
        },
        "freestyle": {
            "rhythm": 1.0,
            "confidence": 1.0,
            "vocabulary": 1.0,
            "accuracy": 0.7,
            "learning": 0.6,
            "emotional": 1.0
        },
        "news": {
            "rhythm": 0.9,
            "confidence": 0.9,
            "vocabulary": 1.0,
            "accuracy": 0.8,
            "learning": 0.7,
            "emotional": 0.8
        }
    }

    # Thresholds for breakthrough detection
    BREAKTHROUGH_THRESHOLDS = {
        "confidence_jump": 0.15,          # 15% confidence increase
        "fluency_streak_multiplier": 1.5,  # 50% longer than previous best
        "vocabulary_expansion": 10,        # 10 new words in session
        "speed_improvement": 0.20,         # 20% WPM increase
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
        self.db = database

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
            user_oid = ObjectId(user_id)

            # Get existing profile or create new one
            existing_profile = await self.db.speaking_dna_profiles_collection.find_one({
                "user_id": user_id,
                "language": language
            })

            logger.info(f"[DNA] Analyzing session for user {user_id}, language {language}")

            # Extract metrics from session
            session_metrics = self._extract_session_metrics(session_data)
            logger.info(f"[DNA] Extracted metrics: WPM={session_metrics.get('words_per_minute', 0):.1f}")

            # Calculate strand updates
            updated_strands = self._calculate_strand_updates(
                existing_profile,
                session_metrics,
                session_data.get("session_type", "learning")
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

            profile_update = {
                "user_id": user_id,
                "language": language,
                "dna_strands": updated_strands,
                "overall_profile": overall_profile,
                "sessions_analyzed": sessions_analyzed,
                "total_speaking_minutes": total_minutes,
                "updated_at": now
            }

            if existing_profile:
                await self.db.speaking_dna_profiles_collection.update_one(
                    {"_id": existing_profile["_id"]},
                    {"$set": profile_update}
                )
                logger.info(f"[DNA] Updated existing profile for user {user_id}")
            else:
                profile_update["created_at"] = now
                result = await self.db.speaking_dna_profiles_collection.insert_one(profile_update)
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

                await self.db.speaking_breakthroughs_collection.insert_many(breakthrough_docs)
                logger.info(f"[DNA] Stored {len(breakthrough_docs)} breakthroughs")

            return {
                "profile": profile_update,
                "breakthroughs": breakthroughs,
                "session_insights": self._generate_session_insights(session_metrics, updated_strands)
            }

        except Exception as e:
            logger.error(f"[DNA] Error analyzing session: {str(e)}", exc_info=True)
            raise

    def _extract_session_metrics(self, session_data: Dict) -> Dict:
        """
        Extract quantifiable metrics from session data.

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

            if turn.get("start_time_ms") and turn.get("end_time_ms"):
                total_speaking_time_ms += turn["end_time_ms"] - turn["start_time_ms"]

        wpm = (total_words / (total_speaking_time_ms / 60000)) if total_speaking_time_ms > 0 else 0

        # Detect filler words (common across languages + language-specific)
        filler_patterns = [
            "uh", "um", "eh", "ah", "like", "you know",  # English
            "nou", "dus", "eigenlijk", "gewoon",   # Dutch
            "euh", "ben", "pues", "este", "o sea"        # Spanish
        ]
        filler_count = sum(
            1 for word in all_words
            if word.lower() in filler_patterns
        )
        filler_rate = (filler_count / (total_speaking_time_ms / 60000)) if total_speaking_time_ms > 0 else 0

        # Calculate unique vocabulary
        unique_words = set(word.lower() for word in all_words if len(word) > 2)

        # Self-corrections (simple heuristic: repeated phrases or correction markers)
        self_corrections = sum(
            1 for turn in user_turns
            if any(marker in turn.get("transcript", "").lower()
                   for marker in ["i mean", "sorry", "no wait", "ik bedoel", "quiero decir"])
        )

        # Calculate standard deviation of latencies for consistency
        import statistics
        latency_std = statistics.stdev(latencies) if len(latencies) > 1 else 500

        return {
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
            "corrections_received": len(session_data.get("corrections_received", []))
        }

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

    def _calculate_strand_updates(
        self,
        existing_profile: Optional[Dict],
        session_metrics: Dict,
        session_type: str
    ) -> Dict:
        """
        Calculate updated DNA strands using weighted moving average.

        Uses exponential moving average to smooth updates while still
        being responsive to recent sessions.
        """
        weights = self.SESSION_WEIGHTS.get(session_type, self.SESSION_WEIGHTS["learning"])
        alpha = 0.3  # Learning rate for exponential moving average

        existing_strands = existing_profile.get("dna_strands", {}) if existing_profile else {}

        # Calculate each strand
        updated = {
            "rhythm": self._update_rhythm_strand(existing_strands.get("rhythm"), session_metrics, alpha, weights["rhythm"]),
            "confidence": self._update_confidence_strand(existing_strands.get("confidence"), session_metrics, alpha, weights["confidence"]),
            "vocabulary": self._update_vocabulary_strand(existing_strands.get("vocabulary"), session_metrics, alpha, weights["vocabulary"]),
            "accuracy": self._update_accuracy_strand(existing_strands.get("accuracy"), session_metrics, alpha, weights["accuracy"]),
            "learning": self._update_learning_strand(existing_strands.get("learning"), session_metrics, alpha, weights["learning"]),
            "emotional": self._update_emotional_strand(existing_strands.get("emotional"), session_metrics, alpha, weights["emotional"])
        }

        return updated

    def _update_rhythm_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update rhythm strand based on speaking pace and pauses."""
        wpm = metrics["words_per_minute"]

        # Determine rhythm type
        if wpm < 70:
            rhythm_type = "thoughtful_pacer"
            description = "Takes time to formulate thoughts, speaks deliberately"
        elif wpm > 120:
            rhythm_type = "rapid_responder"
            description = "Quick and spontaneous, comfortable with fast exchanges"
        else:
            rhythm_type = "steady_speaker"
            description = "Maintains a balanced, natural speaking pace"

        # Calculate consistency score based on standard deviation
        latency_std = metrics.get("response_latency_std_ms", 500)
        consistency = max(0, 1 - (latency_std / 2000))  # Lower std = higher consistency

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
            "pause_duration_avg_ms": round(metrics["response_latency_avg_ms"], 0),
            "consistency_score": round(new_consistency, 2),
            "description": description
        }

    def _update_confidence_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update confidence strand based on latency, fillers, and self-corrections."""
        # Calculate raw confidence score (0-1)
        latency_factor = max(0, 1 - (metrics["response_latency_avg_ms"] / 5000))  # <5s is good
        filler_factor = max(0, 1 - (metrics["filler_rate_per_minute"] / 10))  # <10/min is good
        correction_factor = max(0, 1 - (metrics["self_corrections"] / 5))  # <5 per session is good

        raw_score = (latency_factor * 0.4 + filler_factor * 0.3 + correction_factor * 0.3)

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
        """Update vocabulary strand based on word variety and complexity."""
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

    def _update_accuracy_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update accuracy strand based on corrections and self-monitoring."""
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

        if existing:
            new_accuracy = existing.get("grammar_accuracy", accuracy) * (1 - alpha * weight) + accuracy * alpha * weight
            common_errors = existing.get("common_errors", [])
            improving_areas = existing.get("improving_areas", [])
        else:
            new_accuracy = accuracy
            common_errors = []
            improving_areas = []

        return {
            "pattern": pattern,
            "grammar_accuracy": round(new_accuracy, 2),
            "common_errors": common_errors,
            "improving_areas": improving_areas,
            "description": description
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

    def _update_emotional_strand(self, existing: Optional[Dict], metrics: Dict, alpha: float, weight: float) -> Dict:
        """Update emotional strand based on session patterns."""
        # This would ideally use within-session analysis
        # For now, use latency as proxy for emotional state

        latency = metrics["response_latency_avg_ms"]
        filler_rate = metrics["filler_rate_per_minute"]

        # Estimate start vs end confidence (would need actual timestamps)
        # Using simplified heuristic
        if existing:
            prev_end_confidence = existing.get("session_end_confidence", 0.6)
            # Assume we improve during session
            start_confidence = prev_end_confidence * 0.9
            end_confidence = prev_end_confidence + (0.1 if latency < 2000 else -0.05)
            end_confidence = max(0.3, min(0.95, end_confidence))
        else:
            start_confidence = 0.5
            end_confidence = 0.6

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

        return {
            "pattern": pattern,
            "session_start_confidence": round(start_confidence, 2),
            "session_end_confidence": round(end_confidence, 2),
            "anxiety_triggers": existing.get("anxiety_triggers", []) if existing else [],
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
        """
        try:
            profile = await self.db.speaking_dna_profiles_collection.find_one({
                "user_id": user_id,
                "language": language
            })

            if not profile:
                return self._get_default_coach_instructions(session_type)

            strands = profile.get("dna_strands", {})
            overall = profile.get("overall_profile", {})

            # Get recent uncelebrated breakthroughs
            recent_breakthroughs = await self.db.speaking_breakthroughs_collection.find({
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

            return instructions

        except Exception as e:
            logger.error(f"[DNA] Error building coach instructions: {str(e)}", exc_info=True)
            return self._get_default_coach_instructions(session_type)

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
    # PROFILE RETRIEVAL & EVOLUTION
    # =========================================================================

    async def get_dna_profile(self, user_id: str, language: str) -> Optional[Dict]:
        """Get the current DNA profile for a user."""
        try:
            profile = await self.db.speaking_dna_profiles_collection.find_one({
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
        weeks: int = 12
    ) -> List[Dict]:
        """Get DNA evolution history for visualization."""
        try:
            history = await self.db.speaking_dna_history_collection.find({
                "user_id": user_id,
                "language": language
            }).sort("week_start", -1).limit(weeks).to_list(weeks)

            # Convert ObjectIds to strings
            for entry in history:
                entry["_id"] = str(entry["_id"])

            return list(reversed(history))  # Chronological order

        except Exception as e:
            logger.error(f"[DNA] Error getting evolution: {str(e)}", exc_info=True)
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

            breakthroughs = await self.db.speaking_breakthroughs_collection.find(query).sort(
                "created_at", -1
            ).limit(limit).to_list(limit)

            for bt in breakthroughs:
                bt["_id"] = str(bt["_id"])

            return breakthroughs

        except Exception as e:
            logger.error(f"[DNA] Error getting breakthroughs: {str(e)}", exc_info=True)
            return []

    async def mark_breakthrough_celebrated(self, breakthrough_id: str) -> bool:
        """Mark a breakthrough as celebrated."""
        try:
            result = await self.db.speaking_breakthroughs_collection.update_one(
                {"_id": breakthrough_id},
                {"$set": {"celebrated": True}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"[DNA] Error marking breakthrough celebrated: {str(e)}", exc_info=True)
            return False


# Singleton instance
speaking_dna_service = SpeakingDNAService()
