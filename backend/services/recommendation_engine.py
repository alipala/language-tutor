"""
Daily Recommendation Engine

Generates personalized daily recommendations for users based on their
learning journey stage, recent activity, and performance metrics.

This engine intelligently bridges features (sessions → challenges → assessments)
and provides clear guidance on what the user should do next.

Recommendation Types:
- CONTINUE_PLAN: Continue your active learning plan
- START_SESSION: Start a new practice session
- TAKE_ASSESSMENT: Time to assess your progress
- TRY_CHALLENGES: Practice with targeted challenges
- READ_NEWS: Engage with news-based practice
- REVIEW_DNA: Check your Speaking DNA insights
- COACH_TIP: Get guidance from Taal Coach
- CELEBRATE_MILESTONE: Celebrate an achievement

Author: MyTacoAI Backend Team
Date: 2026-04-20
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId

from database import (
    users_collection,
    learning_plans_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,
    recommended_actions_collection,
    speaking_dna_profiles_collection,
    speaking_breakthroughs_collection,
    daily_stats_collection
)
from models import (
    RecommendedAction,
    RecommendedActionType,
    JourneyStage,
    LearningJourneyState
)
from services.journey_state_detector import journey_state_detector


class RecommendationEngine:
    """
    Generates personalized daily recommendations based on user's learning journey.

    Uses journey stage, recent activity, learning plan status, and performance
    to determine the single best action for the user to take today.
    """

    def __init__(self):
        """Initialize the recommendation engine"""
        pass

    async def generate_daily_recommendation(
        self,
        user_id: str,
        force_new: bool = False
    ) -> Optional[RecommendedAction]:
        """
        Generate the primary recommended action for today.

        Args:
            user_id: User's unique identifier
            force_new: If True, generate new recommendation even if one exists

        Returns:
            RecommendedAction object or None if no recommendation

        Raises:
            ValueError: If user not found
        """
        try:
            # Check if user already has a valid recommendation for today
            if not force_new:
                existing = await self._get_todays_recommendation(user_id)
                if existing:
                    return existing

            # Fetch user and detect current journey stage
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Detect journey stage (will use cache if recent)
            journey_state = await journey_state_detector.detect_journey_stage(user_id)

            # Gather context for recommendation
            context = await self._gather_recommendation_context(user_id, user, journey_state)

            # Generate recommendation based on journey stage
            recommendation = await self._generate_recommendation_for_stage(
                user_id,
                journey_state,
                context
            )

            if recommendation:
                # Save to database
                await recommended_actions_collection.insert_one(
                    recommendation.dict(by_alias=False, exclude={"id"})
                )

            return recommendation

        except Exception as e:
            print(f"Error generating daily recommendation for user {user_id}: {str(e)}")
            return None

    async def generate_alternative_actions(
        self,
        user_id: str,
        primary_action: RecommendedAction,
        max_alternatives: int = 2
    ) -> List[RecommendedAction]:
        """
        Generate 2-3 alternative actions the user can take.

        These are shown as backup options if the user doesn't want to do
        the primary recommended action.

        Returns:
            List of alternative RecommendedAction objects
        """
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return []

            journey_state = user.get("journey_state")
            if not journey_state:
                return []

            journey_state = LearningJourneyState(**journey_state)
            context = await self._gather_recommendation_context(user_id, user, journey_state)

            alternatives = []

            # Don't repeat the primary action type
            primary_type = primary_action.action_type

            # Generate alternatives based on context
            if primary_type != RecommendedActionType.TRY_CHALLENGES and context["recent_challenges_count"] < 3:
                alt = await self._create_challenge_recommendation(user_id, context, priority=2)
                if alt:
                    alternatives.append(alt)

            if primary_type != RecommendedActionType.READ_NEWS and context["recent_news_read_count"] == 0:
                alt = await self._create_news_recommendation(user_id, context, priority=3)
                if alt:
                    alternatives.append(alt)

            if primary_type != RecommendedActionType.START_SESSION:
                alt = await self._create_freestyle_session_recommendation(user_id, context, priority=3)
                if alt:
                    alternatives.append(alt)

            # Save alternatives to database
            for alt in alternatives[:max_alternatives]:
                await recommended_actions_collection.insert_one(
                    alt.dict(by_alias=False, exclude={"id"})
                )

            return alternatives[:max_alternatives]

        except Exception as e:
            print(f"Error generating alternatives: {str(e)}")
            return []

    async def _get_todays_recommendation(self, user_id: str) -> Optional[RecommendedAction]:
        """
        Get existing recommendation for today if it exists and hasn't expired.

        Returns:
            RecommendedAction or None
        """
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            existing = await recommended_actions_collection.find_one({
                "user_id": user_id,
                "completed": False,
                "dismissed": False,
                "expires_at": {"$gt": datetime.utcnow()},
                "recommended_at": {"$gte": today_start},
                "priority": 1  # Only primary recommendations
            })

            if existing:
                # Convert ObjectId to string for Pydantic model
                if "_id" in existing:
                    existing["_id"] = str(existing["_id"])
                return RecommendedAction(**existing)

            return None

        except Exception as e:
            print(f"Error fetching today's recommendation: {str(e)}")
            return None

    async def _gather_recommendation_context(
        self,
        user_id: str,
        user: Dict[str, Any],
        journey_state: LearningJourneyState
    ) -> Dict[str, Any]:
        """
        Gather all context needed for recommendation generation.

        Returns:
            Dictionary with context data
        """
        try:
            # Get active learning plan
            active_plan = await learning_plans_collection.find_one({
                "user_id": user_id,
                "is_active": True,
                "status": "in_progress"
            })

            # Get recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            recent_sessions_count = await conversation_sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago}
            })

            recent_challenges_count = await challenge_sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago}
            })

            # Get uncelebrated breakthroughs
            uncelebrated_breakthroughs = await speaking_breakthroughs_collection.count_documents({
                "user_id": user_id,
                "celebrated": False
            })

            # Get today's stats
            user_timezone = user.get("timezone", "UTC")
            from services.timezone_utils import get_current_local_date
            local_date = get_current_local_date(user_timezone)

            today_stats = await daily_stats_collection.find_one({
                "user_id": user_id,
                "local_date": local_date
            })

            today_sessions = 0
            today_challenges = 0
            if today_stats:
                overall = today_stats.get("overall", {})
                today_sessions = overall.get("total_sessions", 0)
                today_challenges = overall.get("total_challenges", 0)

            # Check if user has Speaking DNA profile
            has_dna_profile = await speaking_dna_profiles_collection.count_documents({
                "user_id": user_id
            }) > 0

            # Get user's preferred language and level
            preferred_language = user.get("preferred_language", "english")
            preferred_level = user.get("preferred_level", "A2")

            # Get last session details
            last_session = await conversation_sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )

            return {
                "active_plan": active_plan,
                "has_active_plan": active_plan is not None,
                "plan_progress": active_plan.get("progress_percentage", 0) if active_plan else 0,
                "plan_completed_sessions": active_plan.get("completed_sessions", 0) if active_plan else 0,
                "plan_total_sessions": active_plan.get("total_sessions", 1) if active_plan else 1,
                "recent_sessions_count": recent_sessions_count,
                "recent_challenges_count": recent_challenges_count,
                "recent_news_read_count": 0,  # TODO: Track news reading
                "uncelebrated_breakthroughs": uncelebrated_breakthroughs,
                "today_sessions": today_sessions,
                "today_challenges": today_challenges,
                "has_dna_profile": has_dna_profile,
                "preferred_language": preferred_language,
                "preferred_level": preferred_level,
                "last_session": last_session,
                "subscription_status": user.get("subscription_status", "free"),
                "current_streak": user.get("stats", {}).get("current_streak", 0)
            }

        except Exception as e:
            print(f"Error gathering recommendation context: {str(e)}")
            return {
                "has_active_plan": False,
                "plan_progress": 0,
                "recent_sessions_count": 0,
                "recent_challenges_count": 0,
                "recent_news_read_count": 0,
                "uncelebrated_breakthroughs": 0,
                "today_sessions": 0,
                "today_challenges": 0,
                "has_dna_profile": False,
                "preferred_language": "english",
                "preferred_level": "A2",
                "subscription_status": "free",
                "current_streak": 0
            }

    async def _generate_recommendation_for_stage(
        self,
        user_id: str,
        journey_state: LearningJourneyState,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """
        Generate recommendation based on user's journey stage.

        This is the core decision logic that determines what users should do.
        """
        stage = journey_state.stage

        # EXPLORING: Guide new users to their first sessions
        if stage == JourneyStage.EXPLORING:
            return await self._recommend_for_exploring(user_id, context)

        # BUILDING_HABIT: Encourage consistency
        elif stage == JourneyStage.BUILDING_HABIT:
            return await self._recommend_for_building_habit(user_id, context)

        # PROGRESSING: Support continued growth
        elif stage == JourneyStage.PROGRESSING:
            return await self._recommend_for_progressing(user_id, context)

        # STRUGGLING: Provide support and easier content
        elif stage == JourneyStage.STRUGGLING:
            return await self._recommend_for_struggling(user_id, context)

        # ACCELERATING: Challenge them more
        elif stage == JourneyStage.ACCELERATING:
            return await self._recommend_for_accelerating(user_id, context)

        # MAINTAINING: Keep them engaged
        elif stage == JourneyStage.MAINTAINING:
            return await self._recommend_for_maintaining(user_id, context)

        # DORMANT: Re-engage
        elif stage == JourneyStage.DORMANT:
            return await self._recommend_for_dormant(user_id, context)

        # RETURNING: Welcome back
        elif stage == JourneyStage.RETURNING:
            return await self._recommend_for_returning(user_id, context)

        return None

    async def _recommend_for_exploring(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in EXPLORING stage (first 3 sessions)"""
        # Priority: Get them to complete their first few sessions

        if context["today_sessions"] == 0:
            # Encourage first session of the day
            return RecommendedAction(
                user_id=user_id,
                action_type=RecommendedActionType.START_SESSION,
                priority=1,
                title="Start Your First Session Today",
                description=f"Practice {context['preferred_language'].title()} with AI for 3-5 minutes. Build your confidence!",
                rationale="Exploring stage, no sessions today",
                action_data={
                    "session_type": "guided",
                    "language": context["preferred_language"],
                    "level": context["preferred_level"],
                    "duration": 3
                },
                source="journey_orchestrator",
                expires_at=datetime.utcnow() + timedelta(days=1)
            )

        # If they've done a session today, suggest trying challenges
        if context["today_challenges"] == 0:
            return await self._create_challenge_recommendation(user_id, context, priority=1)

        # Default: Continue exploring
        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.START_SESSION,
            priority=1,
            title="Keep Exploring",
            description="Try another quick practice session to discover what you like!",
            rationale="Exploring stage, continuing discovery",
            action_data={"session_type": "guided"},
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

    async def _recommend_for_building_habit(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in BUILDING_HABIT stage (4-14 sessions)"""
        # Priority: Establish daily practice routine

        # If no session today, encourage practice
        if context["today_sessions"] == 0:
            streak = context["current_streak"]
            if streak > 0:
                return RecommendedAction(
                    user_id=user_id,
                    action_type=RecommendedActionType.START_SESSION,
                    priority=1,
                    title=f"Keep Your {streak}-Day Streak Going!",
                    description=f"Just 3 minutes of practice today keeps your streak alive.",
                    rationale="Building habit, maintain streak",
                    action_data={"session_type": "guided", "duration": 3},
                    source="journey_orchestrator",
                    expires_at=datetime.utcnow() + timedelta(hours=18)
                )
            else:
                return RecommendedAction(
                    user_id=user_id,
                    action_type=RecommendedActionType.START_SESSION,
                    priority=1,
                    title="Build Your Practice Habit",
                    description="Daily practice is key to progress. Start a quick session!",
                    rationale="Building habit, no session today",
                    action_data={"session_type": "guided"},
                    source="journey_orchestrator",
                    expires_at=datetime.utcnow() + timedelta(days=1)
                )

        # If they've done a session, suggest challenges
        if context["today_challenges"] < 3:
            return await self._create_challenge_recommendation(user_id, context, priority=1)

        # If learning plan not created, suggest creating one
        if not context["has_active_plan"]:
            return RecommendedAction(
                user_id=user_id,
                action_type=RecommendedActionType.CONTINUE_PLAN,
                priority=1,
                title="Create Your Learning Plan",
                description="Ready to get structured? Create a personalized learning plan!",
                rationale="Building habit, no learning plan",
                action_data={"action": "create_plan"},
                source="journey_orchestrator",
                expires_at=datetime.utcnow() + timedelta(days=2)
            )

        return None

    async def _recommend_for_progressing(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in PROGRESSING stage (active learning)"""
        # Priority: Continue learning plan or practice

        # If has active plan, recommend continuing it
        if context["has_active_plan"]:
            plan = context["active_plan"]
            progress = context["plan_progress"]
            completed = context["plan_completed_sessions"]
            total = context["plan_total_sessions"]

            return RecommendedAction(
                user_id=user_id,
                action_type=RecommendedActionType.CONTINUE_PLAN,
                priority=1,
                title=f"Continue Your Learning Plan ({int(progress)}% Complete)",
                description=f"You've completed {completed}/{total} sessions. Keep the momentum going!",
                rationale=f"Progressing stage, learning plan at {progress}%",
                action_data={
                    "learning_plan_id": str(plan["_id"]),
                    "language": plan.get("language"),
                    "level": plan.get("proficiency_level"),
                    "completed_sessions": completed,
                    "total_sessions": total
                },
                source="journey_orchestrator",
                expires_at=datetime.utcnow() + timedelta(days=1)
            )

        # No active plan but progressing - suggest sessions or challenges
        if context["today_sessions"] == 0:
            return RecommendedAction(
                user_id=user_id,
                action_type=RecommendedActionType.START_SESSION,
                priority=1,
                title="Continue Your Practice",
                description="You're making great progress! Keep it up with another session.",
                rationale="Progressing stage, maintain momentum",
                action_data={"session_type": "guided"},
                source="journey_orchestrator",
                expires_at=datetime.utcnow() + timedelta(days=1)
            )

        return await self._create_challenge_recommendation(user_id, context, priority=1)

    async def _recommend_for_struggling(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in STRUGGLING stage (needs support)"""
        # Priority: Easier content, shorter sessions, encouragement

        # Suggest short, easy session
        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.START_SESSION,
            priority=1,
            title="Take It Easy - Quick 3-Minute Session",
            description="Let's get back on track with an easy, short session. You've got this!",
            rationale="Struggling stage, supportive session",
            action_data={
                "session_type": "guided",
                "duration": 3,
                "difficulty": "easy",
                "supportive": True
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

    async def _recommend_for_accelerating(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in ACCELERATING stage (rapid improvement)"""
        # Priority: Challenge them, celebrate progress

        # If uncelebrated breakthroughs, celebrate first
        if context["uncelebrated_breakthroughs"] > 0:
            return RecommendedAction(
                user_id=user_id,
                action_type=RecommendedActionType.CELEBRATE_MILESTONE,
                priority=1,
                title="Celebrate Your Breakthrough!",
                description="You've achieved something amazing! Check your Speaking DNA.",
                rationale=f"Accelerating stage, {context['uncelebrated_breakthroughs']} breakthroughs",
                action_data={"breakthrough_count": context["uncelebrated_breakthroughs"]},
                source="journey_orchestrator",
                expires_at=datetime.utcnow() + timedelta(days=2)
            )

        # If learning plan exists, continue it
        if context["has_active_plan"]:
            return await self._recommend_for_progressing(user_id, context)

        # Otherwise, challenge them with harder content
        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.START_SESSION,
            priority=1,
            title="You're On Fire! Try a Challenging Session",
            description="Your progress is amazing! Ready for a tougher challenge?",
            rationale="Accelerating stage, challenge user",
            action_data={
                "session_type": "guided",
                "difficulty": "challenging"
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

    async def _recommend_for_maintaining(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in MAINTAINING stage (long-term, consistent)"""
        # Priority: Keep them engaged, variety

        # Rotate between sessions, challenges, and news
        day_of_week = datetime.utcnow().weekday()

        if day_of_week % 3 == 0:
            # Sessions
            if context["today_sessions"] == 0:
                return RecommendedAction(
                    user_id=user_id,
                    action_type=RecommendedActionType.START_SESSION,
                    priority=1,
                    title="Your Daily Practice Awaits",
                    description="Consistency is your superpower. Let's practice!",
                    rationale="Maintaining stage, daily practice",
                    action_data={"session_type": "guided"},
                    source="journey_orchestrator",
                    expires_at=datetime.utcnow() + timedelta(days=1)
                )

        elif day_of_week % 3 == 1:
            # Challenges
            return await self._create_challenge_recommendation(user_id, context, priority=1)

        else:
            # News or DNA review
            if context["has_dna_profile"]:
                return RecommendedAction(
                    user_id=user_id,
                    action_type=RecommendedActionType.REVIEW_DNA,
                    priority=1,
                    title="Check Your Speaking DNA Progress",
                    description="See how your speaking patterns have evolved this week!",
                    rationale="Maintaining stage, DNA review day",
                    action_data={},
                    source="journey_orchestrator",
                    expires_at=datetime.utcnow() + timedelta(days=1)
                )

        return await self._create_news_recommendation(user_id, context, priority=1)

    async def _recommend_for_dormant(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in DORMANT stage (7+ days inactive)"""
        # Priority: Re-engage gently

        days_inactive = (datetime.utcnow() - context.get("last_session", {}).get("created_at", datetime.utcnow())).days if context.get("last_session") else 7

        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.START_SESSION,
            priority=1,
            title="We've Missed You!",
            description=f"It's been {days_inactive} days. Start with an easy 3-minute session to get back on track.",
            rationale=f"Dormant stage, {days_inactive} days inactive",
            action_data={
                "session_type": "guided",
                "duration": 3,
                "difficulty": "easy"
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=3)
        )

    async def _recommend_for_returning(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[RecommendedAction]:
        """Recommendations for users in RETURNING stage (coming back after dormancy)"""
        # Priority: Welcome back warmly

        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.START_SESSION,
            priority=1,
            title="Welcome Back!",
            description="Great to see you again! Let's ease back in with a quick session.",
            rationale="Returning stage, warm welcome",
            action_data={
                "session_type": "guided",
                "duration": 3
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

    # Helper methods for creating specific recommendation types

    async def _create_challenge_recommendation(
        self,
        user_id: str,
        context: Dict[str, Any],
        priority: int = 1
    ) -> RecommendedAction:
        """Create a challenge recommendation"""
        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.TRY_CHALLENGES,
            priority=priority,
            title="Practice with Challenges",
            description="Reinforce your learning with fun, quick challenges!",
            rationale="Challenge recommendation",
            action_data={
                "language": context["preferred_language"],
                "level": context["preferred_level"],
                "count": 3
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

    async def _create_news_recommendation(
        self,
        user_id: str,
        context: Dict[str, Any],
        priority: int = 1
    ) -> RecommendedAction:
        """Create a news reading recommendation"""
        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.READ_NEWS,
            priority=priority,
            title="Read Today's News",
            description="Practice with real-world content. Read and discuss today's news!",
            rationale="News recommendation",
            action_data={
                "language": context["preferred_language"],
                "level": context["preferred_level"]
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )

    async def _create_freestyle_session_recommendation(
        self,
        user_id: str,
        context: Dict[str, Any],
        priority: int = 2
    ) -> RecommendedAction:
        """Create a freestyle session recommendation"""
        return RecommendedAction(
            user_id=user_id,
            action_type=RecommendedActionType.START_SESSION,
            priority=priority,
            title="Try a Freestyle Session",
            description="Talk about anything you want with your AI tutor!",
            rationale="Freestyle session recommendation",
            action_data={
                "session_type": "freestyle",
                "language": context["preferred_language"]
            },
            source="journey_orchestrator",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )


# Singleton instance
recommendation_engine = RecommendationEngine()
