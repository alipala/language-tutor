"""
Learning Journey State Detector

This service analyzes user activity patterns and determines their current
learning journey stage, enabling personalized recommendations and interventions.

Journey Stages:
- EXPLORING: First 3 sessions, discovering features (0-3 sessions)
- BUILDING_HABIT: Forming consistency (4-14 sessions, learning the routine)
- PROGRESSING: Active learning with positive trends (consistent practice, improving)
- STRUGGLING: Declining metrics, needs intervention (dropping accuracy, losing streak)
- ACCELERATING: Rapid improvement, high engagement (improving DNA, high accuracy)
- MAINTAINING: Consistent practice, stable performance (long-term users, steady)
- DORMANT: No activity for 7+ days (needs re-engagement)
- RETURNING: Coming back after dormancy (special welcome back flow)

Author: MyTacoAI Backend Team
Date: 2026-04-20
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId

from database import (
    users_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,
    daily_stats_collection,
    speaking_dna_profiles_collection,
    speaking_dna_history_collection
)
from models import LearningJourneyState, JourneyStage


class JourneyStateDetector:
    """
    Detects and updates user's learning journey stage based on activity patterns.

    This class uses multiple data sources to create a comprehensive picture
    of the user's current learning state:
    - Total sessions and challenges completed
    - Recent activity patterns (last 7 days)
    - Speaking DNA trends (if premium user)
    - Streak and accuracy metrics
    - Time since last activity
    """

    def __init__(self):
        """Initialize the journey state detector"""
        pass

    async def detect_journey_stage(
        self,
        user_id: str,
        force_recalculate: bool = False
    ) -> LearningJourneyState:
        """
        Detect the current journey stage for a user.

        Args:
            user_id: User's unique identifier
            force_recalculate: If True, ignore cache and recalculate

        Returns:
            LearningJourneyState object with stage and metrics

        Raises:
            ValueError: If user not found
        """
        try:
            # Fetch user document
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Check if we can use cached journey state (if recent and not forced)
            if not force_recalculate and user.get("journey_state"):
                journey_state = user["journey_state"]
                last_reviewed = journey_state.get("last_reviewed_at")

                # Use cached state if reviewed within last 6 hours
                if last_reviewed and isinstance(last_reviewed, datetime):
                    hours_since_review = (datetime.utcnow() - last_reviewed).total_seconds() / 3600
                    if hours_since_review < 6:
                        return LearningJourneyState(**journey_state)

            # Gather activity metrics
            metrics = await self._gather_activity_metrics(user_id, user)

            # Determine journey stage
            stage = await self._determine_stage(metrics, user)

            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(metrics)

            # Check if intervention needed
            intervention_needed, intervention_reason = self._check_intervention_needed(metrics, stage)

            # Get DNA improvement trend (if available)
            dna_trend = await self._get_dna_improvement_trend(user_id)

            # Build journey state
            journey_state = LearningJourneyState(
                stage=stage,
                detected_at=datetime.utcnow(),
                confidence_level=confidence_level,
                intervention_needed=intervention_needed,
                intervention_reason=intervention_reason,
                last_reviewed_at=datetime.utcnow(),
                total_sessions=metrics["total_sessions"],
                total_challenges=metrics["total_challenges"],
                current_streak=metrics["current_streak"],
                days_since_last_activity=metrics["days_since_last_activity"],
                average_session_quality=metrics["average_session_quality"],
                dna_improvement_trend=dna_trend
            )

            # Update user document with new journey state
            await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "journey_state": journey_state.dict(by_alias=False)
                    }
                }
            )

            return journey_state

        except Exception as e:
            print(f"Error detecting journey stage for user {user_id}: {str(e)}")
            # Return default exploring stage on error
            return LearningJourneyState(
                stage=JourneyStage.EXPLORING,
                detected_at=datetime.utcnow(),
                confidence_level=0.5,
                intervention_needed=False,
                last_reviewed_at=datetime.utcnow()
            )

    async def _gather_activity_metrics(self, user_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather comprehensive activity metrics for the user.

        Returns:
            Dictionary with all activity metrics needed for stage detection
        """
        try:
            # Get total conversation sessions
            total_sessions = await conversation_sessions_collection.count_documents({
                "user_id": user_id
            })

            # Get total challenges
            total_challenges = await challenge_sessions_collection.count_documents({
                "user_id": user_id
            })

            # Get recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_sessions = await conversation_sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago}
            })

            recent_challenges = await challenge_sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago}
            })

            # Get current streak from user stats
            stats = user.get("stats", {})
            current_streak = stats.get("current_streak", 0)

            # Calculate days since last activity
            last_session = await conversation_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            last_challenge = await challenge_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )

            latest_activity = None
            if last_session and last_challenge:
                latest_activity = max(
                    last_session.get("created_at", datetime.min),
                    last_challenge.get("created_at", datetime.min)
                )
            elif last_session:
                latest_activity = last_session.get("created_at")
            elif last_challenge:
                latest_activity = last_challenge.get("created_at")

            days_since_last_activity = 999  # Default to large number if no activity
            if latest_activity:
                days_since_last_activity = (datetime.utcnow() - latest_activity).days

            # Calculate average session quality (last 5 sessions)
            recent_session_quality = await self._calculate_recent_session_quality(user_id)

            # Get accuracy metrics from recent challenges
            accuracy = await self._calculate_recent_accuracy(user_id)

            # Determine activity velocity (sessions + challenges per week)
            activity_velocity = recent_sessions + recent_challenges

            return {
                "total_sessions": total_sessions,
                "total_challenges": total_challenges,
                "recent_sessions": recent_sessions,
                "recent_challenges": recent_challenges,
                "current_streak": current_streak,
                "days_since_last_activity": days_since_last_activity,
                "average_session_quality": recent_session_quality,
                "recent_accuracy": accuracy,
                "activity_velocity": activity_velocity
            }

        except Exception as e:
            print(f"Error gathering activity metrics: {str(e)}")
            return {
                "total_sessions": 0,
                "total_challenges": 0,
                "recent_sessions": 0,
                "recent_challenges": 0,
                "current_streak": 0,
                "days_since_last_activity": 999,
                "average_session_quality": 0.0,
                "recent_accuracy": 0.0,
                "activity_velocity": 0
            }

    async def _calculate_recent_session_quality(self, user_id: str) -> float:
        """
        Calculate average quality score for recent sessions (last 5).
        Quality is based on: duration, message count, and completion.

        Returns:
            Quality score 0-1, where 1 is excellent
        """
        try:
            recent_sessions = await conversation_sessions_collection.find(
                {"user_id": user_id},
                sort=[("created_at", -1)],
                limit=5
            ).to_list(None)

            if not recent_sessions:
                return 0.5  # Default to neutral

            quality_scores = []
            for session in recent_sessions:
                score = 0.0

                # Duration quality (3+ minutes is good)
                duration = session.get("duration_minutes", 0)
                if duration >= 5:
                    score += 0.4
                elif duration >= 3:
                    score += 0.3
                elif duration >= 1:
                    score += 0.2

                # Message count quality (10+ messages is engaged)
                message_count = session.get("message_count", 0)
                if message_count >= 15:
                    score += 0.3
                elif message_count >= 10:
                    score += 0.2
                elif message_count >= 5:
                    score += 0.1

                # Enhanced analysis presence (indicates completed session)
                if session.get("enhanced_analysis"):
                    score += 0.3

                quality_scores.append(min(score, 1.0))  # Cap at 1.0

            return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

        except Exception as e:
            print(f"Error calculating session quality: {str(e)}")
            return 0.5

    async def _calculate_recent_accuracy(self, user_id: str) -> float:
        """
        Calculate accuracy from recent challenges (last 20).

        Returns:
            Accuracy 0-1
        """
        try:
            recent_challenges = await challenge_sessions_collection.find(
                {"user_id": user_id},
                sort=[("created_at", -1)],
                limit=20
            ).to_list(None)

            if not recent_challenges:
                return 0.5  # Default to neutral

            correct_count = sum(1 for c in recent_challenges if c.get("is_correct", False))
            return correct_count / len(recent_challenges)

        except Exception as e:
            print(f"Error calculating accuracy: {str(e)}")
            return 0.5

    async def _determine_stage(self, metrics: Dict[str, Any], user: Dict[str, Any]) -> str:
        """
        Determine the journey stage based on activity metrics.

        Uses a decision tree approach to classify the user's current stage.
        """
        total_sessions = metrics["total_sessions"]
        days_inactive = metrics["days_since_last_activity"]
        recent_activity = metrics["activity_velocity"]
        streak = metrics["current_streak"]
        accuracy = metrics["recent_accuracy"]
        session_quality = metrics["average_session_quality"]

        # Check for returning user (was dormant, now active)
        current_stage = user.get("journey_state", {}).get("stage", JourneyStage.EXPLORING)
        if current_stage == JourneyStage.DORMANT and days_inactive <= 1:
            return JourneyStage.RETURNING

        # Check for dormant (7+ days inactive)
        if days_inactive >= 7:
            return JourneyStage.DORMANT

        # Exploring: First 3 sessions, discovering features
        if total_sessions <= 3:
            return JourneyStage.EXPLORING

        # Building habit: 4-14 sessions, forming consistency
        if total_sessions <= 14:
            # If they're practicing regularly (3+ activities this week), they're building
            if recent_activity >= 3:
                return JourneyStage.BUILDING_HABIT
            else:
                # Low activity but still early - might be struggling
                return JourneyStage.STRUGGLING

        # For users with 15+ sessions, assess their current trajectory

        # Struggling: Low recent activity, dropping streak, or low accuracy
        if (recent_activity < 2 or
            (streak == 0 and current_stage != JourneyStage.EXPLORING) or
            accuracy < 0.4 or
            session_quality < 0.3):
            return JourneyStage.STRUGGLING

        # Accelerating: High activity, improving, high quality
        if (recent_activity >= 5 and
            accuracy > 0.75 and
            session_quality > 0.7 and
            streak >= 3):
            return JourneyStage.ACCELERATING

        # Progressing: Active learning with positive trends
        if (recent_activity >= 3 and
            accuracy > 0.6 and
            session_quality > 0.5):
            return JourneyStage.PROGRESSING

        # Maintaining: Consistent practice, stable performance
        if recent_activity >= 2 and accuracy > 0.5:
            return JourneyStage.MAINTAINING

        # Default to progressing if we can't determine
        return JourneyStage.PROGRESSING

    def _calculate_confidence_level(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate user's confidence level (0-1) based on performance metrics.

        This is NOT speaking confidence, but confidence in their learning progress.
        """
        # Factors:
        # 1. Recent accuracy (40% weight)
        # 2. Session quality (30% weight)
        # 3. Consistency (streak) (20% weight)
        # 4. Activity velocity (10% weight)

        accuracy_score = metrics["recent_accuracy"]
        quality_score = metrics["average_session_quality"]

        # Streak score: normalize to 0-1 (7+ day streak = 1.0)
        streak_score = min(metrics["current_streak"] / 7.0, 1.0)

        # Activity score: normalize to 0-1 (5+ activities per week = 1.0)
        activity_score = min(metrics["activity_velocity"] / 5.0, 1.0)

        confidence = (
            accuracy_score * 0.4 +
            quality_score * 0.3 +
            streak_score * 0.2 +
            activity_score * 0.1
        )

        return round(confidence, 2)

    def _check_intervention_needed(
        self,
        metrics: Dict[str, Any],
        stage: str
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if the user needs intervention (coaching message, encouragement).

        Returns:
            Tuple of (intervention_needed: bool, reason: str)
        """
        # Intervention triggers:
        # 1. Dormant or struggling stage
        # 2. Streak lost (was >3, now 0)
        # 3. Very low accuracy (<0.4)
        # 4. No activity in 3+ days
        # 5. Low session quality (<0.3)

        if stage == JourneyStage.DORMANT:
            days = metrics["days_since_last_activity"]
            return True, f"No activity for {days} days - needs re-engagement"

        if stage == JourneyStage.STRUGGLING:
            if metrics["recent_accuracy"] < 0.4:
                return True, "Low accuracy - needs encouragement and easier content"
            if metrics["average_session_quality"] < 0.3:
                return True, "Low session quality - might be frustrated or confused"
            return True, "General struggling - needs supportive intervention"

        if metrics["days_since_last_activity"] >= 3:
            return True, "3+ days inactive - gentle reminder needed"

        if metrics["current_streak"] == 0 and metrics["total_sessions"] > 5:
            return True, "Streak lost - motivational message needed"

        return False, None

    async def _get_dna_improvement_trend(self, user_id: str) -> str:
        """
        Analyze Speaking DNA history to determine improvement trend.

        Returns:
            "improving", "stable", or "declining"
        """
        try:
            # Get DNA history for all languages (last 4 weeks)
            four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
            dna_snapshots = await speaking_dna_history_collection.find(
                {
                    "user_id": user_id,
                    "week_start": {"$gte": four_weeks_ago}
                },
                sort=[("week_start", 1)]
            ).to_list(None)

            if len(dna_snapshots) < 2:
                return "stable"  # Not enough data

            # Calculate average confidence score trend
            confidence_scores = []
            for snapshot in dna_snapshots:
                confidence = snapshot.get("confidence", {})
                score = confidence.get("score", 0.5)
                confidence_scores.append(score)

            # Simple trend: compare first half vs second half
            mid_point = len(confidence_scores) // 2
            first_half_avg = sum(confidence_scores[:mid_point]) / mid_point
            second_half_avg = sum(confidence_scores[mid_point:]) / (len(confidence_scores) - mid_point)

            improvement = second_half_avg - first_half_avg

            if improvement > 0.1:
                return "improving"
            elif improvement < -0.1:
                return "declining"
            else:
                return "stable"

        except Exception as e:
            print(f"Error getting DNA trend: {str(e)}")
            return "stable"


# Singleton instance
journey_state_detector = JourneyStateDetector()
