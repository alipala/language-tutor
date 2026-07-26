from __future__ import annotations  # Enable forward references for type hints

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

# Custom ObjectId field for Pydantic models
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not v or not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field):
        return {"type": "string"}

# ============================================================================
# HEART SYSTEM MODELS (Focus Energy System)
# ============================================================================

class HeartPool(BaseModel):
    """Heart pool for a specific challenge type"""
    challenge_type: str  # error_spotting, swipe_fix, micro_quiz, etc.
    current_hearts: int  # Current available hearts
    max_hearts: int      # Max hearts based on subscription
    last_heart_lost_at: Optional[datetime] = None  # When last heart was lost
    refill_started_at: Optional[datetime] = None   # When refill started
    refill_rate_minutes: int  # Minutes per heart refill

    # Streak Shield
    streak_shield_active: bool = False
    streak_shield_activated_at: Optional[datetime] = None
    current_correct_streak: int = 0  # Consecutive correct in this type

    # Undo Support (1-second forgiveness mechanic)
    last_action_timestamp: Optional[datetime] = None
    last_action_hearts_before: Optional[int] = None
    last_action_shield_before: bool = False
    last_action_streak_before: int = 0
    last_action_challenge_id: Optional[str] = None
    last_action_is_correct: Optional[bool] = None
    last_action_undoable: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class HeartSystemState(BaseModel):
    """User's heart system state"""
    heart_pools: Dict[str, HeartPool]  # Keyed by challenge_type
    last_updated: datetime
    feature_enabled: bool = True  # Feature flag per user

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class HeartEvent(BaseModel):
    """Analytics event for heart system"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    event_type: str  # "heart_lost", "refill_started", "shield_activated", etc.
    challenge_type: str

    # Event-specific data
    hearts_before: Optional[int] = None
    hearts_after: Optional[int] = None
    refill_complete_at: Optional[datetime] = None
    user_action: Optional[str] = None  # "upgrade", "wait", "dismissed"
    session_id: Optional[str] = None
    session_progress: Optional[Dict[str, Any]] = None  # {completed: 3, total: 10}

    # Context
    subscription_plan: str
    subscription_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_timezone: str

    # Metadata
    app_version: Optional[str] = None
    platform: Optional[str] = None  # "ios", "android", "web"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ============================================================================
# USER MODELS
# ============================================================================

# User models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    preferred_language: Optional[str] = None
    preferred_level: Optional[str] = None
    preferred_voice: Optional[str] = "alloy"  # AI Tutor voice preference
    last_assessment_data: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    hashed_password: str
    apple_user_id: Optional[str] = None  # Apple Sign-In unique identifier
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None  # active, canceled, past_due, expired, trialing
    subscription_plan: Optional[str] = None    # try_learn, fluency_builder, team_mastery
    subscription_period: Optional[str] = None  # monthly, annual
    subscription_price_id: Optional[str] = None # Track exact price subscribed to
    subscription_expires_at: Optional[datetime] = None  # When subscription expires
    subscription_started_at: Optional[datetime] = None  # When subscription started
    
    # Trial tracking
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    is_in_trial: bool = False
    
    # Usage tracking for current billing period
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    practice_sessions_used: int = 0  # Sessions used in current period
    assessments_used: int = 0  # Assessments used in current period
    
    # NEW: Minute tracking for duration-based limits
    practice_minutes_used: float = 0.0  # Speaking minutes used in current period
    
    # Learning plan preservation
    learning_plan_preserved: bool = False  # True if plan is in preservation mode
    learning_plan_data: Optional[Dict[str, Any]] = None  # Preserved learning plan data
    learning_plan_progress: Optional[Dict[str, Any]] = None  # Progress milestones
    
    # Upgrade tracking
    last_upgrade_date: Optional[datetime] = None
    upgrade_history: Optional[List[Dict[str, Any]]] = []

    # Push notifications
    push_token: Optional[str] = None  # Expo Push Token
    device_type: Optional[str] = None  # 'ios' or 'android'
    device_info: Optional[Dict[str, Any]] = None  # Device brand, model, OS version
    push_token_updated_at: Optional[datetime] = None  # Last time token was updated

    # Timezone for stats calculations
    timezone: Optional[str] = "UTC"  # User's timezone (e.g., "America/New_York")

    # Statistics (new gamification system)
    stats: Optional[Dict[str, Any]] = None  # Embedded stats document

    # Heart System (Focus Energy)
    heart_system: Optional[HeartSystemState] = None  # Heart pools and refill state

    # 🆕 NEW: Session duration preference (for smart defaults)
    preferred_session_duration: Optional[int] = None  # 3 or 5, null = use level-based default

    # 🆕 LEARNING JOURNEY ORCHESTRATOR: Journey state tracking
    journey_state: Optional["LearningJourneyState"] = None  # Current learning journey stage and metrics (forward reference)

    # Profile hero card customisation (banner colour + featured stat)
    profile_hero_prefs: Optional[Dict[str, Any]] = None

    # Onboarding personalization answers
    onboarding_goal: Optional[str] = None
    onboarding_level: Optional[str] = None
    onboarding_daily_minutes: Optional[int] = None

    # UI language preference (en/tr/es/fr/de/nl/pt) — drives localised push notifications
    app_language: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserResponse(UserBase):
    id: str = Field(..., alias="_id")
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_period: Optional[str] = None
    subscription_price_id: Optional[str] = None
    timezone: Optional[str] = "UTC"

    # Learned preferences (set by user in Profile or derived from onboarding)
    preferred_level: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_session_duration: Optional[int] = None  # 3 or 5 minutes

    # Usage tracking
    assessments_used: int = 0
    assessments_limit: Optional[int] = None

    # Statistics (gamification)
    stats: Optional[Dict[str, Any]] = None
    challengeStats: Optional[Dict[str, Any]] = None  # backwards compat

    # Profile hero card customisation
    profile_hero_prefs: Optional[Dict[str, Any]] = None

    # Onboarding personalization answers (stored for future use)
    onboarding_goal: Optional[str] = None
    onboarding_level: Optional[str] = None
    onboarding_daily_minutes: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_level: Optional[str] = None
    preferred_voice: Optional[str] = None  # AI Tutor voice preference
    last_assessment_data: Optional[Dict[str, Any]] = None
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_period: Optional[str] = None
    subscription_price_id: Optional[str] = None
    profile_hero_prefs: Optional[Dict[str, Any]] = None
    preferred_session_duration: Optional[int] = None  # 3 or 5 minutes
    # Onboarding personalization answers
    onboarding_goal: Optional[str] = None
    onboarding_level: Optional[str] = None
    onboarding_daily_minutes: Optional[int] = None
    # UI language for localised push notifications
    app_language: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Authentication models
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    name: str
    email: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class GoogleLoginRequest(BaseModel):
    token: str

class AppleLoginRequest(BaseModel):
    token: str  # Apple identity token (JWT)
    user_identifier: str  # Apple user ID
    email: Optional[str] = None  # Email (only provided on first sign-in)
    name: Optional[str] = None  # Full name (only provided on first sign-in)

class PasswordResetRequest(BaseModel):
    email: EmailStr
    
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Session model
class Session(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Password reset model
class PasswordReset(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    email: EmailStr
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Email verification model
class EmailVerification(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    email: EmailStr
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Email verification request models
class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    token: str
    
class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Conversation session models
class ConversationMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationSession(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    language: str
    level: str
    topic: Optional[str] = None
    messages: List[ConversationMessage] = []
    duration_minutes: float = 0.0
    selected_duration: Optional[int] = 5  # User's selected session duration in minutes (1, 3, or 5)
    message_count: int = 0
    summary: Optional[str] = None
    enhanced_analysis: Optional[Dict[str, Any]] = None  # New enhanced analysis data
    is_streak_eligible: bool = False  # True if session >= selected_duration
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# XP awarded for completing a conversation session by chosen duration.
# XP rebalance PR2: speaking is the brand's premium action — buffed so the
# 5-minute session is meaningfully bigger than a typical 10-question game
# (~40 XP) and a perfect+fast game (~70 XP). Keep in sync with
# XP_PER_DURATION on the frontend (ConversationScreen.tsx).
CONVERSATION_SESSION_XP: dict[int, int] = {
    1: 40,   # Sprint   — buffed from 15
    3: 110,  # Quick    — buffed from 50
    5: 180,  # Standard — buffed from 100
}
# Fallback for any unrecognised duration: proportional at the 5-min rate
# (180 XP / 5 min = 36 XP/min), clamped between the 1-min floor and 5-min cap.
_XP_PER_MIN_FALLBACK = 36


def get_session_xp(selected_duration: int) -> int:
    """Return base XP for a completed conversation session.

    Uses the lookup table for the three canonical durations (1, 3, 5 min).
    For any other value the result is clamped to a proportional amount so
    legacy clients or future durations never award 0 or unbounded XP.
    """
    if selected_duration in CONVERSATION_SESSION_XP:
        return CONVERSATION_SESSION_XP[selected_duration]
    return min(max(selected_duration * _XP_PER_MIN_FALLBACK, 40), 180)


class SaveConversationRequest(BaseModel):
    language: str
    level: str
    topic: Optional[str] = None
    messages: List[Dict[str, Any]]
    duration_minutes: float
    selected_duration: Optional[int] = 5  # Chosen session length in minutes (1, 3, or 5); default 5 for backward compat
    learning_plan_id: Optional[str] = None
    conversation_type: Optional[str] = 'practice'
    sentences_for_analysis: Optional[List[Dict[str, Any]]] = []
    # Bonus XP earned during the session:
    #   +10 correction engagement (≥50% of corrections dismissed via "Got it")
    #   +5  fluency burst (2 consecutive clean turns with no correction)
    # XP rebalance PR2: server-side clamp range widened from [0, 15] to [0, 20]
    # so the speaking buff can rise alongside the base table.
    correction_bonus_xp: Optional[int] = 0
    user_timezone: Optional[str] = 'UTC'
    # For news sessions only: the article's category (ai/business/gaming/…),
    # sent by the client from the article it opened. Powers per-category
    # interest tracking (stats.lifetime.news_by_category) so smart reminders
    # can nudge users with fresh news in categories they actually practice.
    news_category: Optional[str] = None

class ConversationStats(BaseModel):
    total_sessions: int
    total_minutes: float
    current_streak: int
    longest_streak: int
    sessions_this_week: int
    sessions_this_month: int
    average_minutes_per_day: Optional[float] = 0.0
    days_since_first_practice: Optional[int] = 0
    first_practice_date: Optional[str] = None

class ConversationHistoryResponse(BaseModel):
    sessions: List[ConversationSession]
    total_count: int
    stats: ConversationStats

# Subscription models
class SubscriptionPlan(BaseModel):
    plan_id: str  # try_learn, fluency_builder, team_mastery
    name: str
    monthly_price: float
    annual_price: float
    monthly_sessions: int  # -1 for unlimited
    annual_sessions: int   # -1 for unlimited
    monthly_assessments: int  # -1 for unlimited
    annual_assessments: int   # -1 for unlimited
    # NEW: Minute limits for duration-based tracking
    monthly_minutes: int  # -1 for unlimited
    annual_minutes: int   # -1 for unlimited
    features: List[str]
    is_free: bool = False

class SubscriptionLimits(BaseModel):
    plan: str
    period: str  # monthly, annual
    sessions_limit: int  # -1 for unlimited
    assessments_limit: int  # -1 for unlimited
    sessions_used: int
    assessments_used: int
    sessions_remaining: int  # -1 for unlimited
    assessments_remaining: int  # -1 for unlimited
    # NEW: Minute limits and usage tracking
    minutes_limit: int  # -1 for unlimited
    minutes_used: float
    minutes_remaining: float  # -1 for unlimited
    # 🔥 FIX: Add lifetime sessions count for Profile display
    sessions_completed: int = 0  # Lifetime total (never resets)
    period_start: datetime
    period_end: datetime
    is_unlimited: bool = False

class SubscriptionStatus(BaseModel):
    status: Optional[str] = None  # active, expired, canceled, past_due, trialing
    plan: Optional[str] = None
    period: Optional[str] = None
    provider: Optional[str] = None  # stripe, apple, google_play
    price_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    limits: Optional[SubscriptionLimits] = None
    is_preserved: bool = False
    preservation_message: Optional[str] = None
    days_until_expiry: Optional[int] = None
    # Trial information
    is_in_trial: bool = False
    trial_end_date: Optional[datetime] = None
    trial_days_remaining: Optional[int] = None
    # 🏫 Institution sponsorship (B2B): present only when the user redeemed a
    # school's Stripe promo code. {sponsored, name, promo_code}. None for normal
    # B2C subscribers, so clients can treat "institution is None" as "self-serve".
    institution: Optional[Dict[str, Any]] = None

class UsageTrackingRequest(BaseModel):
    user_id: Optional[str] = None  # Will be set automatically from authenticated user
    usage_type: str  # 'practice_session' or 'assessment'
    duration_minutes: Optional[float] = None

# NEW: Speaking time tracking request
class SpeakingTimeTrackingRequest(BaseModel):
    user_id: str
    session_id: str  # Unique identifier for the session (conversation/session UUID)
    speaking_minutes: float
    session_completed: bool = False  # True if session was completed (5+ minutes + saved)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class LearningPlanPreservation(BaseModel):
    user_id: str
    plan_data: Dict[str, Any]
    progress_data: Dict[str, Any]
    weeks_completed: int
    current_week: int
    achievements: List[str]
    vocabulary_learned: List[str]
    grammar_improvements: List[str]
    preserved_at: datetime = Field(default_factory=datetime.utcnow)

# Notification models
class NotificationType(str):
    MAINTENANCE = "Maintenance"
    SPECIAL_OFFER = "Special Offer"
    INFORMATION = "Information"

class NotificationBase(BaseModel):
    title: str
    content: str  # Rich text content
    notification_type: str  # NotificationType
    target_user_ids: Optional[List[str]] = None  # None means all users
    send_immediately: bool = True
    scheduled_send_time: Optional[datetime] = None
    created_by: str  # Admin user ID who created the notification

    # Optional metadata fields for custom notification types
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    language: Optional[str] = None
    sentence_count: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        extra = "allow"  # Allow additional fields

class NotificationCreate(BaseModel):
    title: str
    content: str  # Rich text content
    notification_type: str  # NotificationType
    target_user_ids: Optional[List[str]] = None  # None means all users
    send_immediately: bool = True
    scheduled_send_time: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class NotificationInDB(NotificationBase):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    is_sent: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"  # Allow additional fields like session_id, job_id, etc.

class NotificationResponse(NotificationBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    sent_at: Optional[datetime] = None
    is_sent: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        extra = "allow"  # Allow additional fields like session_id, job_id, etc.

# User notification tracking
class UserNotificationBase(BaseModel):
    user_id: str
    notification_id: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None  # Soft delete timestamp

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserNotificationInDB(UserNotificationBase):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserNotificationResponse(UserNotificationBase):
    id: str = Field(..., alias="_id")
    notification: NotificationResponse
    created_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class NotificationMarkReadRequest(BaseModel):
    notification_id: str

class NotificationDeleteRequest(BaseModel):
    notification_id: str

class NotificationListResponse(BaseModel):
    notifications: List[UserNotificationResponse]
    unread_count: int
    total_count: int

# User notification preferences
class NotificationPreferencesBase(BaseModel):
    user_id: str

    # Category preferences (matches mobile app settings)
    practice_reminders_enabled: bool = True  # Default ON - matches the other reminder kinds
    achievement_alerts_enabled: bool = True   # Default ON
    learning_plan_updates_enabled: bool = True  # Default ON
    product_updates_enabled: bool = True  # Default ON
    news_reminders_enabled: bool = True  # Default ON - fresh/interest-based news
    story_reminders_enabled: bool = True  # Default ON - Story Worlds nudges

    # Timing preferences
    preferred_notification_time: Optional[int] = 10  # Hour of day (0-23), default 10 AM
    timezone: Optional[str] = None  # IANA timezone (e.g., "America/New_York")
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[int] = 22  # 10 PM
    quiet_hours_end: Optional[int] = 8    # 8 AM

    # Engagement settings
    max_notifications_per_week: int = 3  # Default limit

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class NotificationPreferencesInDB(NotificationPreferencesBase):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Tracking for weekly limits
    last_notification_sent_at: Optional[datetime] = None
    notification_count_this_week: int = 0
    week_start_date: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class NotificationPreferencesResponse(NotificationPreferencesBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class NotificationPreferencesUpdate(BaseModel):
    practice_reminders_enabled: Optional[bool] = None
    achievement_alerts_enabled: Optional[bool] = None
    learning_plan_updates_enabled: Optional[bool] = None
    product_updates_enabled: Optional[bool] = None
    news_reminders_enabled: Optional[bool] = None
    story_reminders_enabled: Optional[bool] = None
    preferred_notification_time: Optional[int] = None
    timezone: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    max_notifications_per_week: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Flashcard models
class Flashcard(BaseModel):
    id: str
    session_id: str  # Links to conversation session
    user_id: str
    language: str
    level: str
    topic: Optional[str] = None
    front: str  # Question/prompt
    back: str   # Answer/explanation
    category: str  # grammar, vocabulary, pronunciation, fluency, etc.
    difficulty: str  # easy, medium, hard
    tags: List[str] = []  # Additional categorization tags
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_reviewed: Optional[datetime] = None
    review_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    mastery_level: float = 0.0  # 0.0 to 1.0, based on spaced repetition algorithm
    next_review_date: Optional[datetime] = None
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FlashcardSet(BaseModel):
    id: str
    session_id: str
    user_id: str
    language: str
    level: str
    topic: Optional[str] = None
    title: str
    description: str
    flashcards: List[Flashcard]
    total_cards: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    # Tracks whether the user has opened and reviewed this set (for mission progress)
    is_reviewed: bool = False
    reviewed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FlashcardGenerationRequest(BaseModel):
    session_id: str
    language: str
    level: str
    topic: Optional[str] = None
    conversation_content: Optional[str] = None
    session_summary: Optional[str] = None
    count: int = 5  # Number of flashcards to generate (5-10)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class FlashcardReviewRequest(BaseModel):
    flashcard_id: str
    correct: bool  # True if answered correctly, False if incorrect

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class FlashcardProgress(BaseModel):
    total_cards: int
    reviewed_today: int
    due_today: int
    mastered_cards: int
    average_mastery: float

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Voice selection models
class VoiceSelectionRequest(BaseModel):
    voice: str  # One of: alloy, ash, ballad, coral, echo, sage, shimmer, verse
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class VoiceSelectionResponse(BaseModel):
    success: bool
    voice: str
    message: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Challenge models for Explore Tab
class ChallengeOption(BaseModel):
    id: str
    text: str
    isCorrect: bool

class SwipeFixExample(BaseModel):
    text: str
    isCorrect: bool
    explanation: str

class ChallengeBase(BaseModel):
    id: str
    type: str  # error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler, story_builder
    title: str
    emoji: str
    description: str
    cefrLevel: str  # A1, A2, B1, B2, C1, C2
    estimatedSeconds: int
    completed: Optional[bool] = False
    tags: List[str] = []  # For personalization (e.g., "past_tense", "articles", "vocabulary")

class ErrorSpottingChallenge(ChallengeBase):
    type: str = "error_spotting"
    sentence: str
    options: List[ChallengeOption]
    explanation: str
    correctedSentence: str

class SwipeFixChallenge(ChallengeBase):
    type: str = "swipe_fix"
    concept: str
    examples: List[SwipeFixExample]

class MicroQuizChallenge(ChallengeBase):
    type: str = "micro_quiz"
    question: str
    options: List[ChallengeOption]
    explanation: str

class SmartFlashcardChallenge(ChallengeBase):
    type: str = "smart_flashcard"
    word: str
    context: str
    explanation: str
    exampleSentence: str

class NativeCheckChallenge(ChallengeBase):
    type: str = "native_check"
    sentence: str
    isNatural: bool
    correctedVersion: Optional[str] = None
    explanation: str

class BrainTicklerChallenge(ChallengeBase):
    type: str = "brain_tickler"
    question: str
    options: List[ChallengeOption]
    timeLimit: int  # in seconds
    explanation: str

class StoryGap(BaseModel):
    """Represents a gap in the story that needs to be filled"""
    id: str
    correctWord: str
    positionIndex: int  # Position in the story (0-indexed)
    alternativeCorrectWords: Optional[List[str]] = []  # For flexible answers (e.g., "went"/"traveled")

class StoryBuilderChallenge(ChallengeBase):
    type: str = "story_builder"
    storyText: str  # Story with placeholders like "Yesterday, I ___ to the office"
    gaps: List[StoryGap]  # Gap definitions with correct answers
    wordBank: List[str]  # All words including distractors
    explanation: str
    styleNote: Optional[str] = None  # For C1-C2 nuance explanations

# User challenge progress tracking
class UserChallengeStats(BaseModel):
    totalCompleted: int = 0
    currentStreak: int = 0
    lastChallengeDate: Optional[datetime] = None
    completedToday: List[str] = []  # List of challenge IDs completed today
    completionHistory: Dict[str, Any] = {}  # Date -> challenge_ids mapping

class ChallengeCompletionRequest(BaseModel):
    challenge_id: str
    correct: bool  # Whether user answered correctly
    time_spent: int  # Time spent in seconds
    language: Optional[str] = None  # NEW: Language for stats tracking
    level: Optional[str] = None  # NEW: CEFR level for stats tracking
    challenge_type: Optional[str] = None  # NEW: Challenge type for stats tracking

class DailyChallengesResponse(BaseModel):
    challenges: List[Dict[str, Any]]  # List of challenge objects (polymorphic)
    total_completed_today: int
    streak: int
    last_updated: datetime

# Challenge Pool System Models
class ChallengePoolItem(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    cefr_level: str  # A1-C2
    challenge_type: str  # error_spotting, swipe_fix, etc.
    challenge_data: Dict[str, Any]  # Full challenge object
    status: str = "available"  # available, completed, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ReferenceChallengeItem(BaseModel):
    """
    Generic pre-written challenges for new users
    Reusable across all users of same level
    """
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    cefr_level: str  # A1-C2
    challenge_type: str  # error_spotting, swipe_fix, etc.
    challenge_data: Dict[str, Any]  # Full challenge object
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []  # For categorization

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChallengeCountsResponse(BaseModel):
    error_spotting: int
    swipe_fix: int
    micro_quiz: int
    smart_flashcard: int
    native_check: int
    brain_tickler: int
    story_builder: int
    total: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ChallengesByTypeResponse(BaseModel):
    challenges: List[Dict[str, Any]]
    total: int
    type: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# Progression spine (Phase A — Games experience architecture)
# ---------------------------------------------------------------------------
class ProgressionXP(BaseModel):
    """Lifetime XP roll-up with level-progress breakdown."""
    total_xp: int
    level: int
    xp_into_level: int       # XP earned past the current level threshold
    xp_for_level: int        # XP span of the current level (bar denominator)
    xp_to_next: int          # XP still needed for next level


class ProgressionDailyGoal(BaseModel):
    # XP rebalance PR2: daily goal is now XP-based. The legacy challenge-count
    # fields stay populated for backward compatibility with mobile clients
    # built before this change; new clients should read `target_xp` /
    # `current_xp`. `is_complete` reflects the XP comparison (the new
    # source-of-truth), not the legacy challenge count.
    target: int              # legacy: equals target_xp (kept for back-compat)
    completed_today: int     # legacy: equals current_xp (kept for back-compat)
    is_complete: bool
    target_xp: int           # XP rebalance PR2: daily XP goal (default 50)
    current_xp: int          # XP rebalance PR2: from daily_stats.total_xp


class ProgressionResponse(BaseModel):
    success: bool = True
    xp: ProgressionXP
    current_streak: int
    longest_streak: int
    daily_goal: ProgressionDailyGoal
    readiness: int           # 0..100, computed on read
    timezone: str
    date: str                # local date used for daily_goal lookup


class NextStepResponse(BaseModel):
    success: bool = True
    challenge_type: str
    display_title: str
    reason: str
    estimated_duration_sec: int
    language: str
    level: str


# Achievement models for gamification
class AchievementBase(BaseModel):
    id: str  # perfect_session, speed_demon, combo_master, ultimate_combo
    title: str
    description: str
    icon: str  # Emoji icon
    xpBonus: int  # XP bonus for unlocking

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserAchievementInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    achievement_id: str  # Links to AchievementBase.id
    unlocked_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None  # Challenge session that unlocked it

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserAchievementResponse(AchievementBase):
    unlocked_at: datetime
    session_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class AchievementUnlockRequest(BaseModel):
    achievement_id: str
    session_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserAchievementsResponse(BaseModel):
    achievements: List[UserAchievementResponse]
    total_count: int
    total_xp: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Challenge session models for gamification
class ChallengeSessionCreate(BaseModel):
    user_id: str
    language: str
    level: str  # CEFR level
    challenge_type: str
    source: str  # 'reference' or 'learning_plan'

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ChallengeSessionInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    language: str
    level: str
    challenge_type: str
    source: str
    challenge_ids: List[str] = []  # List of 10 challenge IDs
    correct_answers: int = 0
    wrong_answers: int = 0
    max_combo: int = 0
    total_xp: int = 0
    is_active: bool = True
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # NEW: Pre-calculated fields for statistics
    total_challenges: int = 0  # correct + wrong
    accuracy: float = 0.0  # Percentage (0-100)
    duration_seconds: float = 0.0  # Total time spent

    # NEW: Timezone support
    user_timezone: Optional[str] = "UTC"  # User's timezone
    local_date: Optional[str] = None  # Date in user's timezone (e.g., "2025-12-21")

    # NEW: Analytics tags
    tags: Optional[Dict[str, Any]] = None  # Additional metadata

    # Challenges data (for history tracking)
    challenges: Optional[List[Dict[str, Any]]] = []  # Full challenge data if needed

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChallengeSessionComplete(BaseModel):
    session_id: str
    correct_answers: int
    wrong_answers: int
    max_combo: int
    total_xp: int
    answer_times: List[float]  # Time spent on each challenge in seconds
    achievements: List[str]  # Achievement IDs unlocked

    # Optional: Client can send timezone if available
    user_timezone: Optional[str] = None

    # Optional: Session context for better stats tracking
    language: Optional[str] = None
    level: Optional[str] = None
    challenge_type: Optional[str] = None

    # Optional: Challenge IDs for completion tracking (Freestyle Practice)
    challenge_ids: Optional[List[str]] = None

    # Client-declared "tap-and-bounce" flag — true only when the user opened a
    # challenge tile and quit without answering any questions. The audit row is
    # still persisted; what gets gated is the downstream stats / streak /
    # welcome-push processing so a 0-engagement abandon never advances the
    # user's totals. Default False keeps every existing client (including
    # older mobile builds that don't know this field) working as before.
    # Server-side hardening: corroborated by total_challenges == 0 in the
    # caller, so a future mis-flagging client cannot silently discard a
    # session that contained real work.
    abandoned: Optional[bool] = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ============================================================================
# GAMIFICATION & STATISTICS MODELS
# New models for the gamification and statistics system
# ============================================================================

# Daily Statistics Models
class DailyStatsBreakdown(BaseModel):
    """Breakdown of stats by language/level/type"""
    challenges: int = 0
    correct: int = 0
    incorrect: int = 0
    accuracy: float = 0.0
    xp: int = 0

class DailyStatsInDB(BaseModel):
    """Pre-aggregated daily statistics"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    local_date: str  # "2025-12-21" in user's timezone
    user_timezone: str = "UTC"

    # Overall metrics
    total_sessions: int = 0
    total_challenges: int = 0
    correct_challenges: int = 0
    incorrect_challenges: int = 0
    accuracy_percent: float = 0.0
    total_xp: int = 0
    total_time_seconds: float = 0.0

    # Breakdown by dimensions (stored as dict)
    by_language: Dict[str, Dict[str, Any]] = {}
    by_level: Dict[str, Dict[str, Any]] = {}
    by_type: Dict[str, Dict[str, Any]] = {}

    # Streak tracking
    is_streak_day: bool = True
    streak_count: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_session_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Daily Stats Response Models
class DailyStatsOverall(BaseModel):
    total_sessions: int
    total_challenges: int
    correct: int
    incorrect: int
    accuracy: float
    total_xp: int
    time_minutes: float


class StreakInfo(BaseModel):
    current: int
    longest: int = 0
    is_active_today: bool
    next_milestone: int


class DailyStatsResponse(BaseModel):
    success: bool = True
    date: str  # Local date
    timezone: str
    overall: DailyStatsOverall
    by_language: Dict[str, DailyStatsBreakdown]
    by_level: Dict[str, DailyStatsBreakdown]
    by_type: Dict[str, DailyStatsBreakdown]
    streak: StreakInfo
    metadata: Dict[str, Any]


# Recent Performance Models
class RecentPerformanceSummary(BaseModel):
    total_sessions: int
    total_challenges: int
    average_accuracy: float
    total_xp: int
    total_time_minutes: float
    active_days: int


class RecentPerformanceInsights(BaseModel):
    most_practiced_type: Optional[str] = None
    most_practiced_language: Optional[str] = None
    weakest_level: Optional[str] = None
    weakest_level_accuracy: float = 0.0
    strongest_level: Optional[str] = None
    strongest_level_accuracy: float = 0.0
    improvement_trend: str = "stable"  # positive, negative, stable
    accuracy_change_percent: float = 0.0


class DailyBreakdownItem(BaseModel):
    date: str
    challenges: int
    accuracy: float
    xp: int
    time_minutes: float
    sessions: int


class LanguageDistribution(BaseModel):
    challenges: int
    percentage: float
    accuracy: float


class RecentPerformanceInDB(BaseModel):
    """Cached recent performance data"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    window_start: datetime
    window_end: datetime

    # Summary metrics
    total_sessions: int = 0
    total_challenges: int = 0
    average_accuracy: float = 0.0
    total_xp: int = 0

    # Insights
    most_practiced_type: Optional[str] = None
    most_practiced_language: Optional[str] = None
    weakest_level: Optional[str] = None
    strongest_level: Optional[str] = None

    # Daily breakdown
    daily_breakdown: List[Dict[str, Any]] = []

    # Distributions
    language_distribution: Dict[str, Dict[str, Any]] = {}
    type_distribution: Dict[str, Dict[str, Any]] = {}
    level_performance: Dict[str, Dict[str, Any]] = {}

    # Cache metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class RecentPerformanceResponse(BaseModel):
    success: bool = True
    window: Dict[str, Any]
    summary: RecentPerformanceSummary
    insights: RecentPerformanceInsights
    daily_breakdown: List[DailyBreakdownItem]
    language_distribution: Dict[str, LanguageDistribution]
    type_distribution: Dict[str, LanguageDistribution]
    level_performance: Dict[str, Dict[str, Any]]
    metadata: Dict[str, Any]


# Lifetime Progress Models
class LifetimeLanguageProgress(BaseModel):
    total_challenges: int
    highest_level: str
    total_xp: int
    started_at: datetime
    last_practiced: datetime
    time_hours: float
    mastery_percent: float
    level_breakdown: Dict[str, Dict[str, Any]] = {}


class LifetimeChallengeTypeMastery(BaseModel):
    total_challenges: int
    accuracy: float
    mastery_level: int  # 1-5 stars
    rank: str  # beginner, intermediate, advanced, expert, master
    favorite: bool = False


class LifetimeSummary(BaseModel):
    total_challenges: int
    total_sessions: int
    total_xp: int
    total_time_hours: float
    member_since: str
    longest_streak: int
    current_streak: int
    xp_by_source: Optional[Dict[str, Any]] = None
    challenge_count: int = 0
    conversation_count: int = 0
    # Count of completed speaking assessments. Drives the "First Voice"
    # badge independently from conversation sessions, so the user gets
    # the motivational ping right after their very first assessment.
    assessments_completed: int = 0
    # Count of completed news-flow conversations. Gates News Reader /
    # Daily Newsie badges separately from generic total_sessions so the
    # badges fire only on actual news activity.
    news_sessions: int = 0
    # Time-of-day counters in the user's local timezone.
    # < 8am → early_bird, ≥ 10pm → late_night.
    early_bird_sessions: int = 0
    late_night_sessions: int = 0


class LifetimeProgressResponse(BaseModel):
    success: bool = True
    summary: LifetimeSummary
    language_progress: Dict[str, Dict[str, Any]]
    level_mastery: Dict[str, Dict[str, Any]]
    challenge_type_mastery: Dict[str, Dict[str, Any]]
    learning_path: Dict[str, Any]
    achievements: Optional[Dict[str, Any]] = None
    milestones: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]


# Unified Stats Response (All three layers)
class UnifiedStatsResponse(BaseModel):
    success: bool = True
    daily: DailyStatsResponse
    recent: RecentPerformanceResponse
    lifetime: LifetimeProgressResponse


# ============================================================================
# SPEAKING DNA MODELS
# Language learning personalization through speaking pattern analysis
# ============================================================================

class DNAStrandRhythm(BaseModel):
    """Speaking rhythm characteristics"""
    type: str  # thoughtful_pacer, rapid_responder, steady_speaker
    words_per_minute_avg: float
    pause_duration_avg_ms: float
    consistency_score: float  # 0-1 scale
    description: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAStrandConfidence(BaseModel):
    """Speaking confidence indicators"""
    level: str  # hesitant, building, comfortable, fluent
    score: float  # 0-1 scale
    response_latency_avg_ms: float
    filler_rate_per_minute: float
    trend: str  # declining, stable, improving
    description: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAStrandVocabulary(BaseModel):
    """Vocabulary usage patterns"""
    style: str  # adventurous, safety_first, balanced
    unique_words_per_session: int
    new_word_attempt_rate: float  # 0-1 scale
    complexity_level: str  # beginner, intermediate, advanced
    description: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAStrandAccuracy(BaseModel):
    """Grammar and accuracy patterns"""
    pattern: str  # perfectionist, risk_taker, balanced
    grammar_accuracy: float  # 0-1 scale
    common_errors: List[str]
    improving_areas: List[str]
    description: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAStrandLearning(BaseModel):
    """Learning style indicators"""
    type: str  # explorer, persistent, cautious
    retry_rate: float  # 0-1 scale
    challenge_acceptance: float  # 0-1 scale
    description: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAStrandEmotional(BaseModel):
    """Emotional and confidence progression patterns"""
    pattern: str  # quick_starter, slow_warmer, consistent
    session_start_confidence: float  # 0-1 scale
    session_end_confidence: float  # 0-1 scale
    anxiety_triggers: List[str]
    description: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAStrandPronunciation(BaseModel):
    """S4 — Pronunciation strand (acoustic, voice-check / assessment driven)."""
    score: float
    phoneme_accuracy: Optional[float] = None
    prosody_score: Optional[float] = None
    completeness_score: Optional[float] = None
    fluency_score: Optional[float] = None
    voice_checks_count: Optional[int] = 0
    last_updated_session_type: Optional[str] = None
    description: Optional[str] = ""

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        extra = "allow"  # tolerate voice_check_history etc.


class DNAStrandFluency(BaseModel):
    """S4 — Fluency strand (transcript-based, every session)."""
    score: float
    level: Optional[str] = None
    filler_rate: Optional[float] = None
    wpm_variance: Optional[float] = None
    pause_score: Optional[float] = None
    description: Optional[str] = ""

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        extra = "allow"  # tolerate history etc.


class DNAStrands(BaseModel):
    """Complete DNA strand collection. S4 expanded the canonical set
    to 6 display strands (rhythm, confidence, pronunciation,
    vocabulary, accuracy, fluency). Learning + emotional remain on
    the model for backwards compatibility — pronunciation and
    fluency are the ones the DNA tab + share card now render.
    Without these two on the response model, FastAPI's
    `response_model=DNAProfileResponse` was silently dropping them
    on serialization — DB had them, the API didn't ship them, and
    the mobile share card rendered Pronunciation/Fluency as 0."""
    rhythm: DNAStrandRhythm
    confidence: DNAStrandConfidence
    pronunciation: Optional[DNAStrandPronunciation] = None
    vocabulary: DNAStrandVocabulary
    accuracy: DNAStrandAccuracy
    fluency: Optional[DNAStrandFluency] = None
    learning: DNAStrandLearning
    emotional: DNAStrandEmotional

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class OverallDNAProfile(BaseModel):
    """Overall speaking DNA profile summary"""
    speaker_archetype: str  # e.g., "The Thoughtful Builder"
    summary: str
    coach_approach: str  # patient_encourager, challenge_provider, balanced_guide
    strengths: List[str]
    growth_areas: List[str]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class BaselineAssessment(BaseModel):
    """Initial speaking assessment metrics"""
    date: datetime
    acoustic_metrics: Dict[str, float]  # pitch_mean, jitter, shimmer, etc.

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SpeakingDNAProfile(BaseModel):
    """Complete Speaking DNA profile for a user-language pair"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    language: str

    # Core DNA data
    dna_strands: DNAStrands
    overall_profile: OverallDNAProfile

    # Optional baseline assessment
    baseline_assessment: Optional[BaselineAssessment] = None

    # Metrics
    sessions_analyzed: int = 0
    total_speaking_minutes: float = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DNAHistorySnapshot(BaseModel):
    """Session-level DNA snapshot for evolution tracking"""
    session_number: int
    timestamp: Optional[datetime] = None
    strand_scores: Dict[str, float] = {}  # vocabulary, accuracy, fluency values (0-1 floats)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class SpeakingBreakthrough(BaseModel):
    """Breakthrough moment detection and storage"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    language: str
    session_id: Optional[str] = None

    # Breakthrough details
    breakthrough_type: str  # confidence_jump, vocabulary_expansion, etc.
    category: str  # Which DNA strand: confidence, vocabulary, etc.
    title: str
    description: str
    emoji: str

    # Metrics
    metrics: Dict[str, Any]  # before/after comparison

    # Context
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)  # session_type, topic, trigger_sentence

    # Status
    celebrated: bool = False
    shared: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# API Request/Response Models

class SessionTurnData(BaseModel):
    """User turn data for DNA analysis"""
    transcript: str
    start_time_ms: int
    end_time_ms: int
    ai_prompt_end_time_ms: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class SessionAnalysisInput(BaseModel):
    """Input for DNA session analysis"""
    session_id: str
    session_type: str  # learning, freestyle, news
    duration_seconds: int
    user_turns: List[SessionTurnData]
    corrections_received: Optional[List[Dict[str, Any]]] = []
    challenges_offered: int = 0
    challenges_accepted: int = 0
    topics_discussed: Optional[List[str]] = []
    audio_base64: Optional[str] = None  # Base64 encoded audio (first 30s of session)
    audio_format: Optional[str] = "m4a"  # Audio format: m4a, wav, webm

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class SessionInsights(BaseModel):
    """Insights generated from session analysis"""
    insights: List[str]
    highlight_stat: Dict[str, Any]
    causal_sentence: Optional[str] = None  # S2.1 narrative for reveal ceremony

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class AnalyzeSessionResponse(BaseModel):
    """Response from session analysis"""
    success: bool
    breakthroughs: List[SpeakingBreakthrough]
    session_insights: SessionInsights
    previous_strand_values: Optional[Dict[str, Any]] = None  # S2.1 for reveal delta animation
    # S3.4: per-strand delta dict {"rhythm": {"previous": 0.42, "current": 0.55, "delta": 0.13}, ...}
    strand_deltas: Optional[Dict[str, Any]] = None
    # S3.5: first breakthrough of this session (if any) for the sealed reveal card
    breakthrough_unlocked: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAProfileResponse(BaseModel):
    """Response with DNA profile data"""
    profile: Optional[SpeakingDNAProfile] = None
    has_profile: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNAEvolutionResponse(BaseModel):
    """Response with DNA evolution history"""
    evolution: List[DNAHistorySnapshot]
    weeks_tracked: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DNABreakthroughsResponse(BaseModel):
    """Response with breakthrough moments"""
    breakthroughs: List[SpeakingBreakthrough]
    total_count: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class CoachInstructionsResponse(BaseModel):
    """Response with DNA-aware coach instructions"""
    instructions: str
    has_profile: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ============================================================================
# SESSION FEEDBACK MODELS
# ============================================================================

class SessionFeedbackRequest(BaseModel):
    """Request model for session feedback"""

    # User identification
    user_id: Optional[str] = None
    is_guest: bool = False
    device_id: Optional[str] = None

    # Session identification
    session_id: str = Field(..., min_length=1, max_length=100)
    session_type: str = Field(
        ...,
        pattern="^(conversation_freestyle|conversation_custom_topic|conversation_news|conversation_learning_plan|challenge)$"
    )
    challenge_type: Optional[str] = None

    # Feedback data
    feedback_type: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    comment: Optional[str] = Field(None, max_length=5000)

    # Session context
    language: str = Field(..., min_length=2, max_length=10)
    level: str = Field(..., min_length=2, max_length=2)
    topic: Optional[str] = Field(None, max_length=200)

    # Session metrics
    session_duration_seconds: Optional[int] = Field(None, ge=0)
    words_spoken: Optional[int] = Field(None, ge=0)
    accuracy: Optional[float] = Field(None, ge=0, le=100)

    # Metadata
    user_agent: Optional[str] = None
    app_version: Optional[str] = None

    class Config:
        populate_by_name = True


class SessionFeedbackResponse(BaseModel):
    """Response model for session feedback"""
    success: bool
    message: str
    feedback_id: Optional[str] = None

    class Config:
        populate_by_name = True


# ============================================================================
# LEARNING JOURNEY ORCHESTRATOR MODELS
# Intelligent system for guiding users through personalized learning journeys
# ============================================================================

class JourneyStage(str):
    """Enumeration of learning journey stages"""
    EXPLORING = "exploring"  # First 3 sessions, discovering features
    BUILDING_HABIT = "building_habit"  # 4-14 sessions, forming consistency
    PROGRESSING = "progressing"  # Active learning, positive trends
    STRUGGLING = "struggling"  # Declining metrics, needs intervention
    ACCELERATING = "accelerating"  # Rapid improvement, high engagement
    MAINTAINING = "maintaining"  # Consistent practice, stable performance
    DORMANT = "dormant"  # No activity for 7+ days
    RETURNING = "returning"  # Coming back after dormancy


class LearningJourneyState(BaseModel):
    """User's current learning journey state and confidence metrics"""
    stage: str = JourneyStage.EXPLORING
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_level: float = 0.5  # 0-1 scale, based on DNA + stats
    intervention_needed: bool = False
    intervention_reason: Optional[str] = None
    last_reviewed_at: datetime = Field(default_factory=datetime.utcnow)

    # Performance indicators
    total_sessions: int = 0
    total_challenges: int = 0
    current_streak: int = 0
    days_since_last_activity: int = 0
    average_session_quality: float = 0.0  # 0-1 scale
    dna_improvement_trend: str = "stable"  # improving, stable, declining

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class RecommendedActionType(str):
    """Types of recommended actions"""
    CONTINUE_PLAN = "continue_plan"
    START_SESSION = "start_session"
    TRY_CHALLENGES = "try_challenges"
    READ_NEWS = "read_news"
    REVIEW_DNA = "review_dna"
    CELEBRATE_MILESTONE = "celebrate_milestone"


class RecommendedAction(BaseModel):
    """A recommended action for the user to take"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    action_type: str  # RecommendedActionType
    priority: int = 1  # 1=highest, 5=lowest

    # Rationale and context
    title: str  # "Continue Your Learning Plan"
    description: str  # "You're 60% through B1 Spanish - keep going!"
    rationale: str  # Internal: why this was recommended

    # Action-specific data
    action_data: Dict[str, Any] = {}  # challenge_ids, learning_plan_id, topic, etc.

    # Source and timing
    source: str  # "journey_orchestrator", "dna_review", "coach", "session_analysis"
    recommended_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # When this recommendation is no longer relevant

    # User interaction
    completed: bool = False
    completed_at: Optional[datetime] = None
    dismissed: bool = False
    dismissed_at: Optional[datetime] = None
    viewed: bool = False
    viewed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class JourneyCheckpointType(str):
    """Types of journey checkpoints"""
    FEATURE_DISCOVERED = "feature_discovered"
    MILESTONE_REACHED = "milestone_reached"
    STRUGGLE_DETECTED = "struggle_detected"
    BREAKTHROUGH_ACHIEVED = "breakthrough_achieved"
    STREAK_MILESTONE = "streak_milestone"
    LEVEL_COMPLETED = "level_completed"
    PLAN_COMPLETED = "plan_completed"
    DNA_IMPROVEMENT = "dna_improvement"


class JourneyCheckpoint(BaseModel):
    """Milestone or event in the user's learning journey"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    checkpoint_type: str  # JourneyCheckpointType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Checkpoint details
    title: str  # "First Session Complete!"
    description: str  # "You completed your first practice session"
    data: Dict[str, Any] = {}  # Context-specific data

    # Celebration and notification
    celebrated: bool = False
    celebrated_at: Optional[datetime] = None
    notified: bool = False
    notified_at: Optional[datetime] = None
    notification_id: Optional[str] = None

    # Metadata
    language: Optional[str] = None
    level: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DailyDigestMessage(BaseModel):
    """Proactive coach message for daily digest"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: datetime  # When to send (user's morning time)

    # Message content
    message_type: str  # "motivation", "tip", "celebration", "intervention", "reminder"
    subject: str  # "Great progress this week!"
    message: str  # Full message text
    quick_actions: List[Dict[str, Any]] = []  # Suggested actions user can take

    # Context that generated this message
    context: Dict[str, Any] = {}  # journey_stage, recent_activity, dna_trends, etc.

    # Delivery tracking
    sent: bool = False
    sent_at: Optional[datetime] = None
    notification_id: Optional[str] = None
    opened: bool = False
    opened_at: Optional[datetime] = None
    acted_upon: bool = False  # User took one of the quick actions
    action_taken: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# API Request/Response Models

class JourneyStatusResponse(BaseModel):
    """Current journey status for the user"""
    success: bool = True
    journey_state: LearningJourneyState
    current_recommendation: Optional[RecommendedAction] = None
    recent_checkpoints: List[JourneyCheckpoint] = []
    daily_digest_available: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class RecommendedActionResponse(BaseModel):
    """Today's primary recommended action"""
    success: bool = True
    action: Optional[RecommendedAction] = None
    alternative_actions: List[RecommendedAction] = []
    message: str = "Here's what we recommend for you today"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DismissRecommendationRequest(BaseModel):
    """Request to dismiss a recommendation"""
    recommendation_id: str
    reason: Optional[str] = None  # "not_interested", "already_done", "too_difficult", etc.

    class Config:
        populate_by_name = True


class CompleteRecommendationRequest(BaseModel):
    """Request to mark recommendation as completed"""
    recommendation_id: str
    completion_data: Optional[Dict[str, Any]] = None  # Session ID, challenge results, etc.

    class Config:
        populate_by_name = True


class DailyDigestResponse(BaseModel):
    """Today's daily digest from the coach"""
    success: bool = True
    digest: Optional[DailyDigestMessage] = None
    has_unread_digest: bool = False
    message: str = ""

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class JourneyTimelineEvent(BaseModel):
    """An event in the user's learning journey timeline"""
    id: str  # Unique identifier for the event
    timestamp: datetime
    event_type: str  # "session", "challenge", "assessment", "breakthrough", "milestone"
    title: str
    description: str
    language: Optional[str] = None
    level: Optional[str] = None
    data: Dict[str, Any] = {}
    icon: str  # Icon name for UI
    color: str  # Color for UI visualization

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class JourneyTimelineResponse(BaseModel):
    """Complete learning journey timeline"""
    success: bool = True
    timeline: List[JourneyTimelineEvent] = []
    summary: Dict[str, Any] = {}  # Total sessions, streaks, breakthroughs, etc.
    current_week_summary: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
