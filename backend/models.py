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
    message_count: int = 0
    summary: Optional[str] = None
    enhanced_analysis: Optional[Dict[str, Any]] = None  # New enhanced analysis data
    is_streak_eligible: bool = False  # True if session >= 5 minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SaveConversationRequest(BaseModel):
    language: str
    level: str
    topic: Optional[str] = None
    messages: List[Dict[str, Any]]
    duration_minutes: float
    learning_plan_id: Optional[str] = None
    conversation_type: Optional[str] = 'practice'
    sentences_for_analysis: Optional[List[Dict[str, Any]]] = []  # 🔥 NEW: Batch sentence analysis

class ConversationStats(BaseModel):
    total_sessions: int
    total_minutes: float
    current_streak: int
    longest_streak: int
    sessions_this_week: int
    sessions_this_month: int

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
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

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

class NotificationResponse(NotificationBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    sent_at: Optional[datetime] = None
    is_sent: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

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
    type: str  # error_spotting, swipe_fix, micro_quiz, smart_flashcard, native_check, brain_tickler
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

class DailyChallengesResponse(BaseModel):
    challenges: List[Dict[str, Any]]  # List of challenge objects (polymorphic)
    total_completed_today: int
    streak: int
    last_updated: datetime
