"""
Learning Trajectory Analyzer - Phase 2
=======================================
Analyzes user's learning trends, velocity, plateaus, and breakthroughs.

Provides insights for personalized coaching:
- Improvement velocity (% per week)
- Plateau detection (< 3% change in 4 weeks)
- Breakthrough moments (> 15% improvement in 2 weeks)
- Consistency scoring (practice frequency)
- Trend classification (accelerating, steady, plateauing, declining)
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class LearningTrajectoryAnalyzer:
    """
    Analyzes user's learning trajectory over time.

    Data Sources:
    - Speaking DNA snapshots (pronunciation, fluency, grammar, vocabulary)
    - Challenge performance history
    - Practice session frequency and duration
    - Assessment results
    """

    # Thresholds
    PLATEAU_THRESHOLD = 3.0  # < 3% change in 4 weeks = plateau
    BREAKTHROUGH_THRESHOLD = 15.0  # > 15% improvement in 2 weeks = breakthrough
    MIN_SNAPSHOTS = 2  # Minimum DNA snapshots needed for analysis

    def __init__(self):
        logger.info("[TRAJECTORY] Learning Trajectory Analyzer initialized")

    async def analyze(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user's learning trajectory.

        Args:
            user_id: User ID
            context: Cached context with:
                - speaking_dna: DNA profile with snapshots
                - practice_sessions_details: Recent practice sessions
                - challenge_results: Challenge performance

        Returns:
            Dictionary with:
                - velocity: Improvement rates per week
                - plateaus: List of skills in plateau
                - breakthroughs: List of (skill, improvement%) tuples
                - trend: Overall trend classification
                - consistency: Practice consistency score
                - insufficient_data: True if not enough data
        """
        try:
            # Extract DNA snapshots
            dna_data = context.get('speaking_dna', {})
            snapshots = dna_data.get('recent_snapshots', [])

            if len(snapshots) < self.MIN_SNAPSHOTS:
                logger.debug(f"[TRAJECTORY] Insufficient DNA snapshots: {len(snapshots)} < {self.MIN_SNAPSHOTS}")
                return {"insufficient_data": True, "reason": f"Need {self.MIN_SNAPSHOTS}+ DNA snapshots"}

            logger.debug(f"[TRAJECTORY] Analyzing {len(snapshots)} DNA snapshots for user {user_id}")

            # Calculate velocity (improvement per week)
            velocity = self._calculate_velocity(snapshots)

            # Detect plateaus
            plateaus = self._detect_plateaus(snapshots)

            # Detect breakthroughs
            breakthroughs = self._detect_breakthroughs(snapshots)

            # Classify overall trend
            trend = self._classify_trend(velocity)

            # Calculate consistency from practice sessions
            practice_sessions = context.get('practice_sessions_details', [])
            consistency = self._calculate_consistency(practice_sessions)

            # Calculate challenge performance trend
            challenge_trend = self._analyze_challenge_trend(context)

            result = {
                "insufficient_data": False,
                "velocity": velocity,
                "plateaus": plateaus,
                "breakthroughs": breakthroughs,
                "trend": trend,
                "consistency": consistency,
                "challenge_trend": challenge_trend,
                "snapshots_analyzed": len(snapshots)
            }

            logger.info(
                f"[TRAJECTORY] Analysis complete: trend={trend}, "
                f"plateaus={len(plateaus)}, breakthroughs={len(breakthroughs)}"
            )

            return result

        except Exception as e:
            logger.error(f"[TRAJECTORY] Analysis failed: {e}")
            return {"insufficient_data": True, "error": str(e)}

    def _calculate_velocity(self, snapshots: List[Dict]) -> Dict[str, float]:
        """
        Calculate improvement velocity (% per week) for each skill.

        Returns dict with keys: pronunciation_per_week, fluency_per_week, etc.
        """
        if len(snapshots) < 2:
            return {}

        # Sort by date (oldest first)
        sorted_snaps = sorted(snapshots, key=lambda s: s.get('created_at', ''))

        # Calculate deltas for each skill
        skills = ['pronunciation', 'fluency', 'grammar', 'vocabulary']
        velocity = {}

        for skill in skills:
            values = [s.get(skill, 0) for s in sorted_snaps]
            dates = [s.get('created_at', '') for s in sorted_snaps]

            if len(values) < 2:
                continue

            # Calculate weekly velocity (simple linear regression would be better)
            first_val = values[0]
            last_val = values[-1]
            first_date = datetime.fromisoformat(dates[0].replace('Z', '+00:00'))
            last_date = datetime.fromisoformat(dates[-1].replace('Z', '+00:00'))

            weeks_elapsed = max(1, (last_date - first_date).days / 7.0)
            delta = last_val - first_val
            weekly_velocity = delta / weeks_elapsed

            velocity[f"{skill}_per_week"] = round(weekly_velocity, 2)

        return velocity

    def _detect_plateaus(self, snapshots: List[Dict]) -> List[str]:
        """
        Detect plateaus (< 3% change in last 4 weeks).

        Returns list of skills in plateau.
        """
        if len(snapshots) < 2:
            return []

        # Get snapshots from last 4 weeks
        now = datetime.utcnow()
        four_weeks_ago = now - timedelta(weeks=4)

        recent_snaps = [
            s for s in snapshots
            if datetime.fromisoformat(s.get('created_at', '').replace('Z', '+00:00')) >= four_weeks_ago
        ]

        if len(recent_snaps) < 2:
            return []

        # Check each skill for plateau
        skills = ['pronunciation', 'fluency', 'grammar', 'vocabulary']
        plateaus = []

        for skill in skills:
            values = [s.get(skill, 0) for s in recent_snaps]
            if len(values) < 2:
                continue

            min_val = min(values)
            max_val = max(values)
            change = max_val - min_val

            if change < self.PLATEAU_THRESHOLD:
                plateaus.append(skill)
                logger.debug(f"[TRAJECTORY] Plateau detected: {skill} (change: {change:.1f}%)")

        return plateaus

    def _detect_breakthroughs(self, snapshots: List[Dict]) -> List[Tuple[str, float]]:
        """
        Detect breakthroughs (> 15% improvement in 2 weeks).

        Returns list of (skill, improvement%) tuples.
        """
        if len(snapshots) < 2:
            return []

        # Get snapshots from last 2 weeks
        now = datetime.utcnow()
        two_weeks_ago = now - timedelta(weeks=2)

        recent_snaps = [
            s for s in snapshots
            if datetime.fromisoformat(s.get('created_at', '').replace('Z', '+00:00')) >= two_weeks_ago
        ]

        if len(recent_snaps) < 2:
            return []

        # Sort by date
        recent_snaps = sorted(recent_snaps, key=lambda s: s.get('created_at', ''))

        # Check each skill for breakthrough
        skills = ['pronunciation', 'fluency', 'grammar', 'vocabulary']
        breakthroughs = []

        for skill in skills:
            values = [s.get(skill, 0) for s in recent_snaps]
            if len(values) < 2:
                continue

            first_val = values[0]
            last_val = values[-1]
            improvement = last_val - first_val

            if improvement >= self.BREAKTHROUGH_THRESHOLD:
                breakthroughs.append((skill, round(improvement, 1)))
                logger.info(f"[TRAJECTORY] 🎉 Breakthrough: {skill} +{improvement:.1f}% in 2 weeks!")

        return breakthroughs

    def _classify_trend(self, velocity: Dict[str, float]) -> str:
        """
        Classify overall trend based on velocity.

        Returns: 'accelerating', 'steady', 'plateauing', 'declining', or 'unknown'
        """
        if not velocity:
            return 'unknown'

        # Average velocity across all skills
        velocities = list(velocity.values())
        avg_velocity = sum(velocities) / len(velocities)

        if avg_velocity > 3.0:
            return 'accelerating'  # > 3% per week = accelerating
        elif avg_velocity > 1.0:
            return 'steady'  # 1-3% per week = steady progress
        elif avg_velocity > -1.0:
            return 'plateauing'  # -1 to +1% per week = plateau
        else:
            return 'declining'  # < -1% per week = declining

    def _calculate_consistency(self, practice_sessions: List[Dict]) -> Dict[str, Any]:
        """
        Calculate practice consistency.

        Returns:
            - score: 0.0-1.0 consistency score
            - sessions_per_week: Average sessions per week
            - streak_days: Current streak
        """
        if not practice_sessions:
            return {"score": 0.0, "sessions_per_week": 0, "streak_days": 0}

        # Count sessions per week (last 4 weeks)
        now = datetime.utcnow()
        four_weeks_ago = now - timedelta(weeks=4)

        recent_sessions = [
            s for s in practice_sessions
            if 'created_at' in s and
            datetime.fromisoformat(s['created_at'].replace('Z', '+00:00')) >= four_weeks_ago
        ]

        sessions_per_week = len(recent_sessions) / 4.0

        # Calculate streak (consecutive days with practice)
        session_dates = set()
        for session in practice_sessions:
            if 'created_at' in session:
                date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00')).date()
                session_dates.add(date)

        # Count consecutive days
        streak_days = 0
        current_date = datetime.utcnow().date()
        while current_date in session_dates:
            streak_days += 1
            current_date -= timedelta(days=1)

        # Consistency score (0-1)
        # Ideal: 3-5 sessions per week
        if sessions_per_week >= 3:
            score = min(1.0, sessions_per_week / 5.0)
        else:
            score = sessions_per_week / 3.0

        return {
            "score": round(score, 2),
            "sessions_per_week": round(sessions_per_week, 1),
            "streak_days": streak_days
        }

    def _analyze_challenge_trend(self, context: Dict) -> Dict[str, Any]:
        """
        Analyze challenge performance trend.

        Returns trend for challenge accuracy over time.
        """
        # This would analyze challenge_sessions collection
        # For now, return placeholder
        return {
            "trend": "unknown",
            "avg_accuracy": 0.0,
            "improvement": 0.0
        }

    def format_for_prompt(self, analysis: Dict[str, Any]) -> str:
        """
        Format trajectory analysis for LLM prompt.

        Args:
            analysis: Output from analyze()

        Returns:
            Formatted string for prompt injection
        """
        if analysis.get('insufficient_data'):
            return ""

        lines = ["\n📊 LEARNING TRAJECTORY ANALYSIS:"]

        # Breakthroughs
        breakthroughs = analysis.get('breakthroughs', [])
        if breakthroughs:
            lines.append("\n🎉 BREAKTHROUGHS (last 2 weeks):")
            for skill, improvement in breakthroughs:
                lines.append(f"  - {skill.upper()}: +{improvement}% improvement!")

        # Plateaus
        plateaus = analysis.get('plateaus', [])
        if plateaus:
            plateau_list = ', '.join(plateaus)
            lines.append(f"\n⚠️  PLATEAU DETECTED: {plateau_list}")
            lines.append("   → This is NORMAL at level transitions (A2→B1, B1→B2)")
            lines.append("   → Recommend: Focus on OTHER skills while this consolidates")

        # Velocity
        velocity = analysis.get('velocity', {})
        if velocity:
            lines.append("\n📈 Improvement Velocity:")
            for skill_key, rate in velocity.items():
                skill = skill_key.replace('_per_week', '')
                symbol = "📈" if rate > 0 else "📉" if rate < 0 else "➡️"
                lines.append(f"  {symbol} {skill}: {rate:+.1f}%/week")

        # Trend
        trend = analysis.get('trend', 'unknown')
        if trend != 'unknown':
            trend_msgs = {
                'accelerating': "🚀 Overall trend: ACCELERATING (excellent progress!)",
                'steady': "✅ Overall trend: STEADY (consistent improvement)",
                'plateauing': "⏸️  Overall trend: PLATEAUING (normal, consolidation phase)",
                'declining': "⚠️  Overall trend: DECLINING (needs intervention)"
            }
            lines.append(f"\n{trend_msgs.get(trend, '')}")

        # Consistency
        consistency = analysis.get('consistency', {})
        if consistency:
            score = consistency.get('score', 0)
            sessions_pw = consistency.get('sessions_per_week', 0)
            streak = consistency.get('streak_days', 0)

            if score >= 0.7:
                lines.append(f"\n🔥 High consistency: {sessions_pw} sessions/week, {streak} day streak")
            elif score >= 0.4:
                lines.append(f"\n✅ Moderate consistency: {sessions_pw} sessions/week")
            else:
                lines.append(f"\n⚠️  Low consistency: Only {sessions_pw} sessions/week (recommend 3-5)")

        lines.append("\n" + "="*60 + "\n")

        return '\n'.join(lines)


# Global singleton instance
trajectory_analyzer = LearningTrajectoryAnalyzer()
