"""
Daily Digest Generator - Proactive Coach Messages

Generates personalized daily digest messages from Taal Coach based on:
- User's journey stage and recent activity
- Speaking DNA trends and breakthroughs
- Streak status and milestone achievements
- Intervention needs (inactivity, struggling)

Messages are generated in the user's interface language and delivered
via push notifications at their optimal morning time.

Message Types:
- MOTIVATION: Encouraging messages to maintain momentum
- TIP: Actionable learning tips based on performance
- CELEBRATION: Milestone and breakthrough celebrations
- INTERVENTION: Re-engagement for inactive/struggling users
- REMINDER: Gentle nudges for practice

Author: MyTacoAI Backend Team
Date: 2026-04-20
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId

from database import (
    users_collection,
    daily_digest_messages_collection,
    speaking_breakthroughs_collection,
    daily_stats_collection,
    conversation_sessions_collection,
    challenge_sessions_collection
)
from models import (
    DailyDigestMessage,
    LearningJourneyState,
    JourneyStage
)
from services.journey_state_detector import journey_state_detector


class DailyDigestGenerator:
    """
    Generates personalized daily digest messages from Taal Coach.

    This class creates proactive, context-aware messages that guide users
    through their learning journey with personalized encouragement, tips,
    and celebrations.
    """

    def __init__(self):
        """Initialize the daily digest generator"""
        self.message_templates = self._initialize_message_templates()

    def _initialize_message_templates(self) -> Dict[str, List[str]]:
        """
        Initialize message templates for different scenarios.

        Templates use placeholders:
        {name}, {language}, {streak}, {sessions_count}, {dna_metric}, etc.
        """
        return {
            # EXPLORING stage messages
            "exploring_first_session": [
                "Welcome to your language learning journey, {name}! Ready to practice {language} today? Just 3 minutes can make a difference.",
                "Hey {name}! Let's continue exploring {language} together. Your next session awaits!",
                "Good morning, {name}! Time to discover more about {language}. Start your session when ready!"
            ],

            # BUILDING_HABIT stage messages
            "building_habit_streak": [
                "Amazing, {name}! You're on a {streak}-day streak. Keep it alive with a quick session today!",
                "{streak} days in a row, {name}! Consistency is building your {language} skills. Let's go!",
                "Your {streak}-day streak shows dedication, {name}. One more session today keeps it going!"
            ],
            "building_habit_no_streak": [
                "Good morning, {name}! Daily practice builds lasting skills. Ready for today's {language} session?",
                "Hey {name}! Let's build that practice habit. A quick 3-minute session is all it takes!",
                "Time to practice, {name}! Consistency is the key to mastering {language}."
            ],

            # PROGRESSING stage messages
            "progressing_plan": [
                "Great progress, {name}! You're {progress}% through your learning plan. Let's continue!",
                "You've completed {completed}/{total} sessions, {name}. Your dedication is paying off!",
                "Keep up the momentum, {name}! {sessions_left} sessions left in your plan. You've got this!"
            ],
            "progressing_general": [
                "Your {language} skills are growing, {name}! Ready for today's practice?",
                "Consistent progress, {name}! Let's keep building those {language} skills.",
                "You're doing great, {name}! Time for another session to keep progressing."
            ],

            # STRUGGLING stage messages
            "struggling_encouragement": [
                "Learning has ups and downs, {name}. Let's take it easy today with a short, supportive session.",
                "You've got this, {name}! Sometimes we need to slow down. Try an easy 3-minute session today.",
                "It's okay to struggle, {name}. That's how we grow! Let's practice together with no pressure.",
                "Every expert was once a beginner, {name}. Be patient with yourself. Ready for a gentle session?"
            ],
            "struggling_low_accuracy": [
                "I noticed some challenges, {name}. Let's focus on easier topics today to rebuild confidence.",
                "Progress isn't always linear, {name}. Let's try some review exercises to strengthen your foundation.",
                "You're working hard, {name}! Let's practice fundamentals today. Small steps lead to big wins."
            ],

            # ACCELERATING stage messages
            "accelerating_breakthrough": [
                "WOW, {name}! Your {dna_metric} improved {improvement}%! You're on fire! 🔥",
                "Incredible breakthrough, {name}! Your Speaking DNA shows amazing progress in {dna_metric}!",
                "You're accelerating fast, {name}! {dna_metric} is up {improvement}%. Keep this energy!"
            ],
            "accelerating_challenge": [
                "You're crushing it, {name}! Your accuracy is {accuracy}%. Ready for harder challenges?",
                "Amazing progress, {name}! You're ready for the next level. Let's push your limits!",
                "Your growth is impressive, {name}! Time to challenge yourself with advanced content."
            ],

            # MAINTAINING stage messages
            "maintaining_consistency": [
                "Your consistency is incredible, {name}! {sessions_count} sessions and counting. Let's keep it going!",
                "Steady wins the race, {name}! Your regular practice is building real mastery.",
                "You've made {language} practice a habit, {name}! That's the secret to success."
            ],

            # DORMANT stage messages
            "dormant_gentle": [
                "We've missed you, {name}! It's been {days_inactive} days. Ready to ease back in with a quick session?",
                "Hey {name}, no pressure - but your {language} skills would love to hear from you! Just 3 minutes?",
                "Welcome back anytime, {name}! Your learning journey is waiting. Start whenever you're ready."
            ],
            "dormant_encouraging": [
                "Life gets busy, {name}. But even 3 minutes today can reignite your {language} progress!",
                "It's never too late, {name}! Your {language} practice is here when you're ready to return.",
                "Missing {language} practice, {name}? Let's get back on track together, one session at a time."
            ],

            # RETURNING stage messages
            "returning_welcome": [
                "Welcome back, {name}! Great to see you again! Let's ease back in with a quick session.",
                "You're back, {name}! Your {language} journey continues. Ready to pick up where you left off?",
                "So glad you're back, {name}! Let's start fresh with an easy, fun session today."
            ],

            # DNA-based messages
            "dna_confidence_up": [
                "Your confidence is soaring, {name}! Your Speaking DNA shows {improvement}% improvement. Amazing!",
                "I can hear it in your practice, {name} - your confidence is up {improvement}%! Keep shining!",
                "That's the spirit, {name}! Your confidence jumped {improvement}%. You're believing in yourself!"
            ],
            "dna_fluency_up": [
                "Your fluency is improving beautifully, {name}! You're speaking {improvement}% faster and smoother.",
                "Listen to this progress, {name}: Your fluency improved {improvement}%! Natural flow is developing!",
                "Your speaking rhythm is getting better, {name}! {improvement}% improvement in fluency!"
            ],

            # Streak-based messages
            "streak_lost": [
                "Streaks come and go, {name}, but your learning continues! Ready to start a new streak today?",
                "Let's rebuild that streak, {name}! One session today starts a fresh winning streak.",
                "New day, new streak, {name}! Your progress isn't defined by streaks - let's practice!"
            ],
            "streak_milestone_7": [
                "ONE WEEK STREAK, {name}! 7 days of dedication! You're building a real habit! 🎉",
                "7 days strong, {name}! A full week of practice! Your {language} skills are thanking you!",
                "Week 1 complete, {name}! 7-day streak achieved! This is how mastery is built!"
            ],
            "streak_milestone_30": [
                "30-DAY STREAK, {name}! ONE MONTH! You're officially a dedicated learner! 🏆",
                "INCREDIBLE, {name}! 30 consecutive days! Your commitment is extraordinary!",
                "ONE MONTH STREAK, {name}! 30 days of showing up! This is true mastery in action!"
            ],

            # Challenge-based messages
            "challenge_accuracy_high": [
                "{accuracy}% accuracy, {name}! Your challenge performance is outstanding!",
                "You're acing the challenges, {name}! {accuracy}% accuracy shows real understanding!",
                "Crushing those challenges, {name}! {accuracy}% - you've mastered this level!"
            ],

            # Learning plan messages
            "plan_50_percent": [
                "HALFWAY THERE, {name}! 50% of your learning plan complete! The finish line is in sight!",
                "Half of your journey complete, {name}! 50% done. You're crushing this plan!",
                "50% milestone reached, {name}! You're halfway through. Keep this momentum!"
            ],
            "plan_75_percent": [
                "75% COMPLETE, {name}! Three quarters done! You're so close to finishing!",
                "Almost there, {name}! 75% of your plan complete. The final stretch begins!",
                "Incredible progress, {name}! 75% done. Just a few more sessions to go!"
            ],
            "plan_completed": [
                "PLAN COMPLETE, {name}! You did it! 🎉 Ready for the final assessment?",
                "CONGRATULATIONS, {name}! Learning plan finished! Time to test your new skills!",
                "YOU FINISHED, {name}! Plan 100% complete! Let's see how much you've learned!"
            ],

            # General motivation
            "general_motivation": [
                "Every session makes you better, {name}. Ready to practice {language} today?",
                "Your future self will thank you for today's practice, {name}. Let's go!",
                "Small daily efforts create big results, {name}. Time for {language} practice!",
                "You're investing in yourself, {name}. Each session is progress. Ready?"
            ]
        }

    async def generate_daily_digest(
        self,
        user_id: str,
        force_new: bool = False
    ) -> Optional[DailyDigestMessage]:
        """
        Generate today's daily digest message for a user.

        Args:
            user_id: User's unique identifier
            force_new: If True, generate new digest even if one exists

        Returns:
            DailyDigestMessage object or None if already exists/can't generate
        """
        try:
            # Check if user already has today's digest
            if not force_new:
                existing = await self._get_todays_digest(user_id)
                if existing:
                    return existing

            # Fetch user
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Detect journey stage
            journey_state = await journey_state_detector.detect_journey_stage(user_id)

            # Gather context
            context = await self._gather_digest_context(user_id, user, journey_state)

            # Generate message based on priority:
            # 1. Breakthrough celebrations (highest priority)
            # 2. Milestone achievements
            # 3. Intervention needs
            # 4. Stage-specific motivation

            message_data = await self._select_message(user, journey_state, context)

            if not message_data:
                return None

            # Calculate scheduled send time (user's morning - 8 AM in their timezone)
            scheduled_for = self._calculate_morning_time(user.get("timezone", "UTC"))

            # Create digest message
            digest = DailyDigestMessage(
                user_id=user_id,
                generated_at=datetime.utcnow(),
                scheduled_for=scheduled_for,
                message_type=message_data["type"],
                subject=message_data["subject"],
                message=message_data["message"],
                quick_actions=message_data["quick_actions"],
                context=context
            )

            # Save to database
            result = await daily_digest_messages_collection.insert_one(
                digest.dict(by_alias=False, exclude={"id"})
            )
            digest.id = str(result.inserted_id)

            return digest

        except Exception as e:
            print(f"Error generating daily digest for user {user_id}: {str(e)}")
            return None

    async def _get_todays_digest(self, user_id: str) -> Optional[DailyDigestMessage]:
        """Get existing digest for today if it exists"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            existing = await daily_digest_messages_collection.find_one({
                "user_id": user_id,
                "generated_at": {"$gte": today_start}
            })

            if existing:
                return DailyDigestMessage(**existing)

            return None

        except Exception as e:
            print(f"Error fetching today's digest: {str(e)}")
            return None

    async def _gather_digest_context(
        self,
        user_id: str,
        user: Dict[str, Any],
        journey_state: LearningJourneyState
    ) -> Dict[str, Any]:
        """Gather all context needed for message generation"""
        try:
            # Get recent activity
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            recent_sessions = await conversation_sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago}
            })

            recent_challenges = await challenge_sessions_collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago}
            })

            # Get uncelebrated breakthroughs
            breakthroughs = await speaking_breakthroughs_collection.find({
                "user_id": user_id,
                "celebrated": False
            }).to_list(None)

            # Get today's stats
            from services.timezone_utils import get_current_local_date
            local_date = get_current_local_date(user.get("timezone", "UTC"))

            today_stats = await daily_stats_collection.find_one({
                "user_id": user_id,
                "local_date": local_date
            })

            # Get yesterday's stats for comparison
            yesterday = datetime.utcnow() - timedelta(days=1)
            from services.timezone_utils import convert_to_local_date
            yesterday_date = convert_to_local_date(yesterday, user.get("timezone", "UTC"))

            yesterday_stats = await daily_stats_collection.find_one({
                "user_id": user_id,
                "local_date": yesterday_date
            })

            # Calculate challenge accuracy
            challenge_accuracy = 0.0
            if recent_challenges > 0:
                recent_challenge_docs = await challenge_sessions_collection.find(
                    {"user_id": user_id, "created_at": {"$gte": seven_days_ago}},
                    limit=20
                ).to_list(None)

                if recent_challenge_docs:
                    correct = sum(1 for c in recent_challenge_docs if c.get("is_correct", False))
                    challenge_accuracy = (correct / len(recent_challenge_docs)) * 100

            # Get user stats
            stats = user.get("stats", {})
            current_streak = stats.get("current_streak", 0)

            # Check if streak was lost (had streak yesterday but 0 today)
            previous_streak = user.get("journey_state", {}).get("current_streak", 0)
            streak_lost = previous_streak > 0 and current_streak == 0

            return {
                "name": user.get("name", "there"),
                "language": (user.get("preferred_language") or "english").title(),
                "level": user.get("preferred_level") or "A2",
                "current_streak": current_streak,
                "previous_streak": previous_streak,
                "streak_lost": streak_lost,
                "days_inactive": journey_state.days_since_last_activity,
                "recent_sessions": recent_sessions,
                "recent_challenges": recent_challenges,
                "challenge_accuracy": challenge_accuracy,
                "breakthroughs": breakthroughs,
                "today_practiced": today_stats is not None,
                "yesterday_practiced": yesterday_stats is not None,
                "subscription_status": user.get("subscription_status", "free"),
                "journey_stage": journey_state.stage,
                "intervention_needed": journey_state.intervention_needed,
                "intervention_reason": journey_state.intervention_reason
            }

        except Exception as e:
            print(f"Error gathering digest context: {str(e)}")
            return {
                "name": "there",
                "language": "English",
                "current_streak": 0,
                "days_inactive": 0,
                "recent_sessions": 0,
                "recent_challenges": 0,
                "challenge_accuracy": 0.0,
                "breakthroughs": [],
                "journey_stage": JourneyStage.EXPLORING
            }

    async def _select_message(
        self,
        user: Dict[str, Any],
        journey_state: LearningJourneyState,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Select the most appropriate message based on priority.

        Returns:
            Dictionary with: type, subject, message, quick_actions
        """
        # Priority 1: Breakthroughs (celebrate immediately)
        if context["breakthroughs"]:
            return self._create_breakthrough_message(context)

        # Priority 2: Streak milestones
        if context["current_streak"] in [7, 14, 30, 60, 100]:
            return self._create_streak_milestone_message(context)

        # Priority 3: Streak lost (supportive message)
        if context["streak_lost"]:
            return self._create_streak_lost_message(context)

        # Priority 4: Intervention needed (struggling, dormant)
        if journey_state.intervention_needed:
            return self._create_intervention_message(context)

        # Priority 5: Stage-specific messages
        return self._create_stage_message(journey_state, context)

    def _create_breakthrough_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create message for uncelebrated DNA breakthroughs"""
        breakthrough = context["breakthroughs"][0]  # Get first uncelebrated

        breakthrough_type = breakthrough.get("type", "improvement")
        improvement = breakthrough.get("improvement_percentage", 0)

        # Map breakthrough type to friendly name
        metric_names = {
            "confidence_jump": "Confidence",
            "fluency_streak": "Fluency",
            "vocabulary_expansion": "Vocabulary",
            "speed_improvement": "Speaking Speed",
            "grammar_mastery": "Grammar"
        }

        metric_name = metric_names.get(breakthrough_type, "Speaking")

        import random
        message = random.choice([
            f"WOW, {context['name']}! Your {metric_name} improved {improvement:.0f}%! You're on fire! 🔥",
            f"Incredible breakthrough, {context['name']}! Your Speaking DNA shows amazing progress in {metric_name}!",
            f"You're accelerating fast, {context['name']}! {metric_name} is up {improvement:.0f}%. Keep this energy!"
        ])

        return {
            "type": "celebration",
            "subject": f"🎉 {metric_name} Breakthrough!",
            "message": message,
            "quick_actions": []
        }

    def _create_streak_milestone_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create message for streak milestones"""
        streak = context["current_streak"]

        if streak == 7:
            template_key = "streak_milestone_7"
        elif streak == 30:
            template_key = "streak_milestone_30"
        else:
            template_key = "streak_milestone_7"  # Default

        import random
        message = random.choice(self.message_templates[template_key])
        message = message.format(**context)

        return {
            "type": "celebration",
            "subject": f"🔥 {streak}-Day Streak!",
            "message": message,
            "quick_actions": []
        }

    def _create_streak_lost_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create supportive message when streak is lost"""
        import random
        message = random.choice(self.message_templates["streak_lost"])
        message = message.format(**context)

        return {
            "type": "motivation",
            "subject": "Start Fresh Today",
            "message": message,
            "quick_actions": []
        }

    def _create_intervention_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create intervention message for struggling/dormant users"""
        stage = context["journey_stage"]

        if stage == JourneyStage.DORMANT:
            days = context["days_inactive"]
            import random
            if days >= 14:
                message = random.choice(self.message_templates["dormant_encouraging"])
            else:
                message = random.choice(self.message_templates["dormant_gentle"])

            message = message.format(**context)

            return {
                "type": "intervention",
                "subject": "We've Missed You!",
                "message": message,
                "quick_actions": []
            }

        elif stage == JourneyStage.STRUGGLING:
            import random
            message = random.choice(self.message_templates["struggling_encouragement"])
            message = message.format(**context)

            return {
                "type": "intervention",
                "subject": "You've Got This!",
                "message": message,
                "quick_actions": []
            }

        # Default intervention
        return self._create_stage_message(context["journey_stage"], context)

    def _create_stage_message(
        self,
        journey_state: LearningJourneyState,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create stage-specific motivational message"""
        stage = context["journey_stage"]
        import random

        if stage == JourneyStage.EXPLORING:
            message = random.choice(self.message_templates["exploring_first_session"])
            message = message.format(**context)
            return {
                "type": "motivation",
                "subject": "Continue Exploring",
                "message": message,
                "quick_actions": []
            }

        elif stage == JourneyStage.BUILDING_HABIT:
            if context["current_streak"] > 0:
                message = random.choice(self.message_templates["building_habit_streak"])
                message = message.format(**context, streak=context["current_streak"])
            else:
                message = random.choice(self.message_templates["building_habit_no_streak"])
                message = message.format(**context)

            return {
                "type": "motivation",
                "subject": "Build Your Habit",
                "message": message,
                "quick_actions": []
            }

        elif stage == JourneyStage.PROGRESSING:
            message = random.choice(self.message_templates["progressing_general"])
            message = message.format(**context)

            return {
                "type": "motivation",
                "subject": "Keep Progressing!",
                "message": message,
                "quick_actions": []
            }

        elif stage == JourneyStage.ACCELERATING:
            if context["challenge_accuracy"] > 75:
                message = random.choice(self.message_templates["accelerating_challenge"])
                message = message.format(**context, accuracy=f"{context['challenge_accuracy']:.0f}%")
            else:
                message = random.choice(self.message_templates["general_motivation"])
                message = message.format(**context)

            return {
                "type": "motivation",
                "subject": "You're Accelerating!",
                "message": message,
                "quick_actions": []
            }

        elif stage == JourneyStage.MAINTAINING:
            message = random.choice(self.message_templates["maintaining_consistency"])
            message = message.format(**context, sessions_count=context["recent_sessions"])

            return {
                "type": "motivation",
                "subject": "Maintain Your Momentum",
                "message": message,
                "quick_actions": []
            }

        elif stage == JourneyStage.RETURNING:
            message = random.choice(self.message_templates["returning_welcome"])
            message = message.format(**context)

            return {
                "type": "motivation",
                "subject": "Welcome Back!",
                "message": message,
                "quick_actions": []
            }

        # Default fallback
        message = random.choice(self.message_templates["general_motivation"])
        message = message.format(**context)

        return {
            "type": "motivation",
            "subject": "Time to Practice!",
            "message": message,
            "quick_actions": []
        }

    def _calculate_morning_time(self, timezone: str) -> datetime:
        """
        Calculate user's next morning time (8 AM in their timezone).

        Args:
            timezone: User's IANA timezone string

        Returns:
            datetime object for tomorrow 8 AM in user's timezone (UTC)
        """
        try:
            from zoneinfo import ZoneInfo

            # Get user's timezone
            user_tz = ZoneInfo(timezone)

            # Get tomorrow's date at 8 AM in user's timezone
            now_utc = datetime.utcnow()
            now_user_tz = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)

            # Calculate tomorrow 8 AM
            tomorrow = now_user_tz.date() + timedelta(days=1)
            morning_time = datetime.combine(tomorrow, datetime.min.time().replace(hour=8))
            morning_time = morning_time.replace(tzinfo=user_tz)

            # Convert back to UTC for storage
            morning_time_utc = morning_time.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            return morning_time_utc

        except Exception as e:
            print(f"Error calculating morning time: {str(e)}")
            # Default to tomorrow 8 AM UTC
            tomorrow = datetime.utcnow().date() + timedelta(days=1)
            return datetime.combine(tomorrow, datetime.min.time().replace(hour=8))


# Singleton instance
daily_digest_generator = DailyDigestGenerator()
