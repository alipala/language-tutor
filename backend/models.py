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
    
    # Learning plan preservation
    learning_plan_preserved: bool = False  # True if plan is in preservation mode
    learning_plan_data: Optional[Dict[str, Any]] = None  # Preserved learning plan data
    learning_plan_progress: Optional[Dict[str, Any]] = None  # Progress milestones
    
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
    user_id: str
    usage_type: str  # 'practice_session' or 'assessment'
    duration_minutes: Optional[float] = None

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

class NotificationListResponse(BaseModel):
    notifications: List[UserNotificationResponse]
    unread_count: int
    total_count: int
