from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from bson import ObjectId
import asyncio
from models import UserInDB, HeartPool, HeartSystemState, HeartEvent
from database import database

class HeartService:
    """Service for managing heart system logic"""

    # Challenge type constants
    CHALLENGE_TYPES = [
        "error_spotting",
        "swipe_fix",
        "micro_quiz",
        "smart_flashcard",
        "native_check",
        "brain_tickler",
        "story_builder"
    ]

    # Subscription tier configurations
    TIER_CONFIG = {
        "try_learn": {
            "max_hearts": 5,
            "refill_minutes_per_heart": 36,  # 3 hours total
            "total_refill_minutes": 180
        },
        "fluency_builder": {
            "max_hearts": 10,
            "refill_minutes_per_heart": 6,   # 1 hour total
            "total_refill_minutes": 60
        },
        "team_mastery": {
            "max_hearts": 999999,  # Unlimited
            "refill_minutes_per_heart": 0,
            "total_refill_minutes": 0
        }
    }

    def __init__(self):
        self.db = database

    async def initialize_heart_system(self, user: UserInDB) -> HeartSystemState:
        """
        Initialize heart system for user (first time or migration)
        Called during user registration or migration script
        """
        tier_config = self.TIER_CONFIG.get(
            user.subscription_plan or "try_learn",
            self.TIER_CONFIG["try_learn"]
        )

        heart_pools = {}
        for challenge_type in self.CHALLENGE_TYPES:
            heart_pools[challenge_type] = HeartPool(
                challenge_type=challenge_type,
                current_hearts=tier_config["max_hearts"],
                max_hearts=tier_config["max_hearts"],
                refill_rate_minutes=tier_config["refill_minutes_per_heart"],
                last_heart_lost_at=None,
                refill_started_at=None,
                streak_shield_active=False,
                streak_shield_activated_at=None,
                current_correct_streak=0
            )

        heart_system = HeartSystemState(
            heart_pools=heart_pools,
            last_updated=datetime.utcnow(),
            feature_enabled=True
        )

        # Update user document (convert string ID to ObjectId if needed)
        user_id_obj = ObjectId(user.id) if isinstance(user.id, str) else user.id
        result = await self.db.users.update_one(
            {"_id": user_id_obj},
            {"$set": {"heart_system": heart_system.dict()}}
        )

        if result.matched_count == 0:
            raise ValueError(f"Failed to initialize heart system: User {user.id} not found")

        print(f"✅ Heart system initialized for user {user.id}")
        return heart_system

    async def get_current_hearts(
        self,
        user_id: str,
        challenge_type: str,
        user: Optional[UserInDB] = None
    ) -> Tuple[int, HeartPool]:
        """
        Get current hearts for a challenge type (with real-time refill calculation)
        Returns: (current_hearts, updated_heart_pool)

        Args:
            user_id: User ID (for DB operations)
            challenge_type: Challenge type to check
            user: Optional user object to avoid DB fetch
        """
        # If user object not provided, fetch from DB
        if user is None:
            # Convert string ID to ObjectId for MongoDB query
            user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
            user_doc = await self.db.users.find_one({"_id": user_id_obj})
            if not user_doc or "heart_system" not in user_doc:
                raise ValueError("Heart system not initialized for user")
            user_doc["_id"] = str(user_doc["_id"])
            user = UserInDB(**user_doc)

        if not user.heart_system:
            raise ValueError("Heart system not initialized for user")

        heart_system = user.heart_system
        heart_pool = heart_system.heart_pools.get(challenge_type)

        # Auto-migrate: Add missing heart pool for new challenge types
        if not heart_pool:
            if challenge_type not in self.CHALLENGE_TYPES:
                raise ValueError(f"Invalid challenge type: {challenge_type}")

            # Create new heart pool for this challenge type
            tier_config = self.TIER_CONFIG.get(
                user.subscription_plan or "try_learn",
                self.TIER_CONFIG["try_learn"]
            )
            heart_pool = HeartPool(
                challenge_type=challenge_type,
                current_hearts=tier_config["max_hearts"],
                max_hearts=tier_config["max_hearts"],
                refill_rate_minutes=tier_config["refill_minutes_per_heart"],
                last_heart_lost_at=None,
                refill_started_at=None,
                streak_shield_active=False,
                streak_shield_activated_at=None,
                current_correct_streak=0
            )
            heart_system.heart_pools[challenge_type] = heart_pool

            # Save to database
            await self.db.users.update_one(
                {"_id": user_id_obj},
                {"$set": {f"heart_system.heart_pools.{challenge_type}": heart_pool.model_dump()}}
            )
            print(f"[HEART_SERVICE] ✅ Auto-migrated {challenge_type} heart pool for user {user_id}")

        # Language Mastery: always return max hearts
        user_plan = user.subscription_plan or "try_learn"
        if user_plan == "team_mastery":
            return (heart_pool.max_hearts, heart_pool)

        # Calculate refilled hearts
        if heart_pool.refill_started_at and heart_pool.current_hearts < heart_pool.max_hearts:
            refilled_hearts = self._calculate_refilled_hearts(heart_pool)
            heart_pool.current_hearts = min(
                heart_pool.current_hearts + refilled_hearts,
                heart_pool.max_hearts
            )

            # If fully refilled, clear refill state
            if heart_pool.current_hearts >= heart_pool.max_hearts:
                heart_pool.refill_started_at = None

                # Expire shield if fully refilled
                if heart_pool.streak_shield_active:
                    await self._expire_shield(user_id, challenge_type, "hearts_refilled")
                    heart_pool.streak_shield_active = False
                    heart_pool.streak_shield_activated_at = None

            # Update database
            await self._update_heart_pool(user_id, challenge_type, heart_pool)

        # Check shield expiration (24 hours)
        if heart_pool.streak_shield_active and heart_pool.streak_shield_activated_at:
            hours_since_activation = (
                datetime.utcnow() - heart_pool.streak_shield_activated_at
            ).total_seconds() / 3600

            if hours_since_activation >= 24:
                await self._expire_shield(user_id, challenge_type, "24h_timeout")
                heart_pool.streak_shield_active = False
                heart_pool.streak_shield_activated_at = None
                await self._update_heart_pool(user_id, challenge_type, heart_pool)

        return (heart_pool.current_hearts, heart_pool)

    def _calculate_refilled_hearts(self, heart_pool: HeartPool) -> int:
        """Calculate how many hearts have refilled since refill started"""
        if not heart_pool.refill_started_at or heart_pool.refill_rate_minutes == 0:
            return 0

        elapsed_minutes = (datetime.utcnow() - heart_pool.refill_started_at).total_seconds() / 60
        refilled_count = int(elapsed_minutes / heart_pool.refill_rate_minutes)

        return refilled_count

    async def consume_heart(
        self,
        user_id: str,
        challenge_type: str,
        is_correct: bool,
        session_id: Optional[str] = None,
        user: Optional[UserInDB] = None
    ) -> Dict[str, Any]:
        """
        Process challenge answer and update hearts/shield

        Args:
            user_id: User ID (for DB operations)
            challenge_type: Challenge type
            is_correct: Whether answer was correct
            session_id: Optional session ID for logging
            user: Optional user object to avoid DB fetch

        Returns:
            {
                "hearts_lost": bool,
                "hearts_remaining": int,
                "shield_used": bool,
                "shield_activated": bool,
                "shield_active": bool,
                "current_streak": int,
                "out_of_hearts": bool,
                "refill_info": {...}
            }
        """
        # Pass user object to avoid redundant DB fetch
        current_hearts, heart_pool = await self.get_current_hearts(user_id, challenge_type, user=user)

        # If user not provided, fetch it (should not happen with optimization)
        if user is None:
            user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
            user_doc = await self.db.users.find_one({"_id": user_id_obj})
            user_doc["_id"] = str(user_doc["_id"])
            user = UserInDB(**user_doc)

        user_plan = user.subscription_plan or "try_learn"

        result = {
            "hearts_lost": False,
            "hearts_remaining": current_hearts,
            "shield_used": False,
            "shield_activated": False,
            "shield_active": heart_pool.streak_shield_active,
            "current_streak": heart_pool.current_correct_streak,
            "out_of_hearts": False,
            "refill_info": None
        }

        # Language Mastery: no heart consumption
        if user_plan == "team_mastery":
            if is_correct:
                heart_pool.current_correct_streak += 1
            else:
                heart_pool.current_correct_streak = 0
            await self._update_heart_pool(user_id, challenge_type, heart_pool)
            result["current_streak"] = heart_pool.current_correct_streak
            return result

        if is_correct:
            # Correct answer: increase streak
            heart_pool.current_correct_streak += 1

            # Check if shield should activate (3 correct streak)
            if heart_pool.current_correct_streak >= 3 and not heart_pool.streak_shield_active:
                heart_pool.streak_shield_active = True
                heart_pool.streak_shield_activated_at = datetime.utcnow()
                result["shield_activated"] = True
                result["shield_active"] = True

                # Log shield activation (non-blocking)
                asyncio.create_task(
                    self._log_heart_event(
                        user_id=user_id,
                        event_type="shield_activated",
                        challenge_type=challenge_type,
                        hearts_before=current_hearts,
                        hearts_after=current_hearts,
                        session_id=session_id,
                        subscription_plan=user_plan,
                        user=user
                    )
                )
        else:
            # Wrong answer: check shield or lose heart
            if heart_pool.streak_shield_active:
                # Shield protects from heart loss
                heart_pool.streak_shield_active = False
                heart_pool.streak_shield_activated_at = None
                result["shield_used"] = True

                # Log shield usage (non-blocking)
                asyncio.create_task(
                    self._log_heart_event(
                        user_id=user_id,
                        event_type="shield_used",
                        challenge_type=challenge_type,
                        hearts_before=current_hearts,
                        hearts_after=current_hearts,
                        session_id=session_id,
                        subscription_plan=user_plan,
                        user=user
                    )
                )
            else:
                # Lose 1 heart
                heart_pool.current_hearts = max(0, heart_pool.current_hearts - 1)
                heart_pool.last_heart_lost_at = datetime.utcnow()
                result["hearts_lost"] = True
                result["hearts_remaining"] = heart_pool.current_hearts

                # Start refill timer if hearts hit 0
                if heart_pool.current_hearts == 0:
                    heart_pool.refill_started_at = datetime.utcnow()
                    result["out_of_hearts"] = True
                    result["refill_info"] = self._get_refill_info(heart_pool)

                    # Log refill started (non-blocking)
                    asyncio.create_task(
                        self._log_heart_event(
                            user_id=user_id,
                            event_type="refill_started",
                            challenge_type=challenge_type,
                            hearts_before=current_hearts,
                            hearts_after=0,
                            refill_complete_at=heart_pool.refill_started_at + timedelta(
                                minutes=heart_pool.refill_rate_minutes * heart_pool.max_hearts
                            ),
                            session_id=session_id,
                            subscription_plan=user_plan,
                            user=user
                        )
                    )

                # Log heart loss (non-blocking)
                asyncio.create_task(
                    self._log_heart_event(
                        user_id=user_id,
                        event_type="heart_lost",
                        challenge_type=challenge_type,
                        hearts_before=current_hearts,
                        hearts_after=heart_pool.current_hearts,
                        session_id=session_id,
                        subscription_plan=user_plan,
                        user=user
                    )
                )

            # Reset streak on wrong answer
            heart_pool.current_correct_streak = 0
            result["current_streak"] = 0

        # Update database
        await self._update_heart_pool(user_id, challenge_type, heart_pool)

        return result

    def _get_refill_info(self, heart_pool: HeartPool) -> Dict[str, Any]:
        """Calculate refill timing information"""
        if not heart_pool.refill_started_at:
            return None

        total_refill_time = heart_pool.refill_rate_minutes * heart_pool.max_hearts
        refill_complete_at = heart_pool.refill_started_at + timedelta(minutes=total_refill_time)

        # Calculate next heart refill time
        elapsed_minutes = (datetime.utcnow() - heart_pool.refill_started_at).total_seconds() / 60
        hearts_refilled = int(elapsed_minutes / heart_pool.refill_rate_minutes)
        minutes_to_next_heart = heart_pool.refill_rate_minutes - (elapsed_minutes % heart_pool.refill_rate_minutes)

        return {
            "refill_started_at": heart_pool.refill_started_at.isoformat(),
            "refill_complete_at": refill_complete_at.isoformat(),
            "total_refill_minutes": total_refill_time,
            "minutes_per_heart": heart_pool.refill_rate_minutes,
            "next_heart_in_minutes": round(minutes_to_next_heart, 1),
            "hearts_refilled_so_far": hearts_refilled
        }

    async def _update_heart_pool(
        self,
        user_id: str,
        challenge_type: str,
        heart_pool: HeartPool
    ):
        """Update specific heart pool in user document"""
        # Convert string ID to ObjectId for MongoDB query
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        await self.db.users.update_one(
            {"_id": user_id_obj},
            {
                "$set": {
                    f"heart_system.heart_pools.{challenge_type}": heart_pool.dict(),
                    "heart_system.last_updated": datetime.utcnow()
                }
            }
        )

    async def _expire_shield(
        self,
        user_id: str,
        challenge_type: str,
        reason: str
    ):
        """Log shield expiration event"""
        # Convert string ID to ObjectId for MongoDB query
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = await self.db.users.find_one({"_id": user_id_obj})
        await self._log_heart_event(
            user_id=user_id,
            event_type="shield_expired",
            challenge_type=challenge_type,
            subscription_plan=user.get("subscription_plan", "try_learn"),
            user_action=reason  # "24h_timeout" or "hearts_refilled"
        )

    async def _log_heart_event(
        self,
        user_id: str,
        event_type: str,
        challenge_type: str,
        subscription_plan: str,
        hearts_before: Optional[int] = None,
        hearts_after: Optional[int] = None,
        refill_complete_at: Optional[datetime] = None,
        user_action: Optional[str] = None,
        session_id: Optional[str] = None,
        session_progress: Optional[Dict] = None,
        user: Optional[UserInDB] = None
    ):
        """
        Log heart event to analytics collection

        Args:
            user: Optional user object to avoid DB fetch (optimization)
        """
        # If user object not provided, fetch from DB
        if user is None:
            user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
            user_doc = await self.db.users.find_one({"_id": user_id_obj})
            subscription_status = user_doc.get("subscription_status", "inactive")
            user_timezone = user_doc.get("timezone", "UTC")
        else:
            subscription_status = user.subscription_status or "inactive"
            user_timezone = user.timezone or "UTC"

        event = {
            "user_id": user_id,
            "event_type": event_type,
            "challenge_type": challenge_type,
            "hearts_before": hearts_before,
            "hearts_after": hearts_after,
            "refill_complete_at": refill_complete_at,
            "user_action": user_action,
            "session_id": session_id,
            "session_progress": session_progress,
            "subscription_plan": subscription_plan,
            "subscription_status": subscription_status,
            "timestamp": datetime.utcnow(),
            "user_timezone": user_timezone
        }

        await self.db.heart_events.insert_one(event)

    async def update_hearts_on_subscription_change(
        self,
        user_id: str,
        old_plan: str,
        new_plan: str
    ):
        """
        Update heart pools when user changes subscription
        Called from subscription webhook handler
        """
        old_config = self.TIER_CONFIG.get(old_plan, self.TIER_CONFIG["try_learn"])
        new_config = self.TIER_CONFIG.get(new_plan, self.TIER_CONFIG["try_learn"])

        # Convert string ID to ObjectId for MongoDB query
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = await self.db.users.find_one({"_id": user_id_obj})
        if not user or "heart_system" not in user:
            # Initialize if doesn't exist
            user_obj = UserInDB(**user)
            await self.initialize_heart_system(user_obj)
            user = await self.db.users.find_one({"_id": user_id_obj})

        heart_system = HeartSystemState(**user["heart_system"])

        for challenge_type, heart_pool in heart_system.heart_pools.items():
            # Update max hearts
            heart_pool.max_hearts = new_config["max_hearts"]
            heart_pool.refill_rate_minutes = new_config["refill_minutes_per_heart"]

            # If upgrading and hearts were depleted, grant immediate hearts
            if new_config["max_hearts"] > old_config["max_hearts"]:
                # Grant difference immediately
                bonus_hearts = new_config["max_hearts"] - old_config["max_hearts"]
                heart_pool.current_hearts = min(
                    heart_pool.current_hearts + bonus_hearts,
                    heart_pool.max_hearts
                )

                # Clear refill state if applicable
                if heart_pool.current_hearts > 0:
                    heart_pool.refill_started_at = None

            await self._update_heart_pool(user_id, challenge_type, heart_pool)

    async def log_out_of_hearts_modal(
        self,
        user_id: str,
        challenge_type: str,
        user_action: str,  # "upgrade", "wait", "dismissed"
        session_id: str,
        session_progress: Dict[str, int]
    ):
        """Log when user sees out-of-hearts modal"""
        # Convert string ID to ObjectId for MongoDB query
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = await self.db.users.find_one({"_id": user_id_obj})

        await self._log_heart_event(
            user_id=user_id,
            event_type="out_of_hearts_modal_shown",
            challenge_type=challenge_type,
            subscription_plan=user.get("subscription_plan", "try_learn"),
            user_action=user_action,
            session_id=session_id,
            session_progress=session_progress
        )

    async def log_session_ended_early(
        self,
        user_id: str,
        challenge_type: str,
        session_id: str,
        session_progress: Dict[str, int]
    ):
        """Log when session ends due to no hearts"""
        # Convert string ID to ObjectId for MongoDB query
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = await self.db.users.find_one({"_id": user_id_obj})

        await self._log_heart_event(
            user_id=user_id,
            event_type="session_ended_early",
            challenge_type=challenge_type,
            subscription_plan=user.get("subscription_plan", "try_learn"),
            session_id=session_id,
            session_progress=session_progress
        )
