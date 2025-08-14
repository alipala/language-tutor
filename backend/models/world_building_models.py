from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

# Custom ObjectId field for Pydantic models (reusing from main models.py)
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None):
        if not v or not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field):
        return {"type": "string"}

# Enums for validation
class LanguageEnum(str, Enum):
    EN = "en"
    NL = "nl"
    ES = "es"
    DE = "de"
    FR = "fr"
    PT = "pt"

class TargetLevelEnum(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class GenreEnum(str, Enum):
    MYSTERY = "mystery"
    ADVENTURE = "adventure"
    ROMANCE = "romance"
    SCI_FI = "sci-fi"
    HISTORICAL = "historical"
    BUSINESS = "business"
    CULTURAL = "cultural"

class PrivacySettingEnum(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"

class PrimaryFocusEnum(str, Enum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    CULTURAL = "cultural"

class ContributionOrderEnum(str, Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    SCHEDULED = "scheduled"

class WorldStatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ContributionTypeEnum(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    MIXED = "mixed"

class InvitationTypeEnum(str, Enum):
    DIRECT = "direct"
    LINK = "link"
    QR_CODE = "qr_code"

class InvitationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"

class QueueStatusEnum(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    MISSED = "missed"

class ContributionStatusEnum(str, Enum):
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"

# Sub-models for nested structures
class Character(BaseModel):
    name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)

class Location(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)

class ImportantItem(BaseModel):
    name: str = Field(..., max_length=100)
    significance: str = Field(..., max_length=500)

class WorldState(BaseModel):
    current_plot_point: str = Field(..., max_length=1000)
    active_characters: List[Character] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    important_items: List[ImportantItem] = Field(default_factory=list)

class LearningObjectives(BaseModel):
    primary_focus: PrimaryFocusEnum
    target_structures: List[str] = Field(default_factory=list)
    vocabulary_themes: List[str] = Field(default_factory=list)

class CollaborationSettings(BaseModel):
    max_contributors: int = Field(..., ge=2, le=10)
    session_duration_minutes: int = Field(..., ge=5, le=30)
    requires_approval: bool = False
    contribution_order: ContributionOrderEnum = ContributionOrderEnum.SEQUENTIAL

class Statistics(BaseModel):
    total_sessions: int = Field(default=0, ge=0)
    total_contributors: int = Field(default=0, ge=0)
    average_session_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    learning_effectiveness_score: float = Field(default=0.0, ge=0.0, le=100.0)

class LearningMetrics(BaseModel):
    words_spoken: int = Field(default=0, ge=0)
    unique_vocabulary: List[str] = Field(default_factory=list)
    grammar_structures_used: List[str] = Field(default_factory=list)
    pronunciation_score: float = Field(default=0.0, ge=0.0, le=100.0)
    fluency_score: float = Field(default=0.0, ge=0.0, le=100.0)

class StoryImpact(BaseModel):
    plot_advancement: str = Field(..., max_length=1000)
    characters_introduced: List[str] = Field(default_factory=list)
    locations_visited: List[str] = Field(default_factory=list)

class Correction(BaseModel):
    error: str = Field(..., max_length=500)
    correction: str = Field(..., max_length=500)
    type: str = Field(..., max_length=100)

class AIFeedback(BaseModel):
    corrections: List[Correction] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    praise_points: List[str] = Field(default_factory=list)

class PeerReactions(BaseModel):
    likes: int = Field(default=0, ge=0)
    helpful_votes: int = Field(default=0, ge=0)
    creative_votes: int = Field(default=0, ge=0)

# Main collection models
class StoryWorldBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    creator_id: PyObjectId
    language: LanguageEnum
    target_level: TargetLevelEnum
    genre: GenreEnum
    privacy_setting: PrivacySettingEnum = PrivacySettingEnum.PUBLIC
    learning_objectives: LearningObjectives
    world_state: WorldState
    collaboration_settings: CollaborationSettings
    statistics: Statistics = Field(default_factory=Statistics)
    contributors: List[PyObjectId] = Field(default_factory=list)
    status: WorldStatusEnum = WorldStatusEnum.DRAFT
    tags: List[str] = Field(default_factory=list)
    featured: bool = False

class StoryWorldCreate(StoryWorldBase):
    pass

class StoryWorldInDB(StoryWorldBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_contribution_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class StoryWorldResponse(StoryWorldBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime
    last_contribution_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class StoryContributionBase(BaseModel):
    world_id: PyObjectId
    contributor_id: PyObjectId
    session_number: int = Field(..., ge=1)
    contribution_type: ContributionTypeEnum
    audio_url: Optional[str] = None
    transcript: str = Field(..., max_length=5000)
    duration_seconds: int = Field(..., ge=0)
    learning_metrics: LearningMetrics = Field(default_factory=LearningMetrics)
    story_impact: StoryImpact
    ai_feedback: AIFeedback = Field(default_factory=AIFeedback)
    peer_reactions: PeerReactions = Field(default_factory=PeerReactions)
    status: ContributionStatusEnum = ContributionStatusEnum.ACTIVE

class StoryContributionCreate(StoryContributionBase):
    pass

class StoryContributionInDB(StoryContributionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class StoryContributionResponse(StoryContributionBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class WorldInvitationBase(BaseModel):
    world_id: PyObjectId
    inviter_id: PyObjectId
    invitee_email: Optional[str] = None
    invitee_id: Optional[PyObjectId] = None
    invitation_code: str = Field(..., min_length=8, max_length=8)
    invitation_type: InvitationTypeEnum
    message: Optional[str] = Field(None, max_length=500)
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    status: InvitationStatusEnum = InvitationStatusEnum.PENDING

class WorldInvitationCreate(BaseModel):
    world_id: str
    invitee_email: Optional[str] = None
    invitee_id: Optional[str] = None
    invitation_type: InvitationTypeEnum = InvitationTypeEnum.DIRECT
    message: Optional[str] = Field(None, max_length=500)
    expires_in_hours: int = Field(default=168, ge=1, le=720)  # Default 7 days, max 30 days

class WorldInvitationInDB(WorldInvitationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class WorldInvitationResponse(WorldInvitationBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class CollaborationQueueBase(BaseModel):
    world_id: PyObjectId
    scheduled_contributor_id: PyObjectId
    scheduled_start: datetime
    scheduled_end: datetime
    reminder_sent: bool = False
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: QueueStatusEnum = QueueStatusEnum.UPCOMING

class CollaborationQueueCreate(BaseModel):
    world_id: str
    scheduled_contributor_id: str
    scheduled_start: datetime
    scheduled_end: datetime

class CollaborationQueueInDB(CollaborationQueueBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CollaborationQueueResponse(CollaborationQueueBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class WorldCheckpointBase(BaseModel):
    world_id: PyObjectId
    checkpoint_number: int = Field(..., ge=1)
    world_state_snapshot: Dict[str, Any]
    contribution_count: int = Field(..., ge=0)

class WorldCheckpointCreate(BaseModel):
    world_id: str
    checkpoint_number: int = Field(..., ge=1)
    world_state_snapshot: Dict[str, Any]
    contribution_count: int = Field(..., ge=0)

class WorldCheckpointInDB(WorldCheckpointBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class WorldCheckpointResponse(WorldCheckpointBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Request/Response models for API endpoints
class WorldListRequest(BaseModel):
    language: Optional[LanguageEnum] = None
    target_level: Optional[TargetLevelEnum] = None
    genre: Optional[GenreEnum] = None
    status: Optional[WorldStatusEnum] = None
    featured_only: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class WorldListResponse(BaseModel):
    worlds: List[StoryWorldResponse]
    total_count: int
    has_more: bool

class ContributionListRequest(BaseModel):
    world_id: str
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class ContributionListResponse(BaseModel):
    contributions: List[StoryContributionResponse]
    total_count: int
    has_more: bool

class InvitationAcceptRequest(BaseModel):
    invitation_code: str = Field(..., min_length=8, max_length=8)

class WorldJoinRequest(BaseModel):
    world_id: str
    invitation_code: Optional[str] = None

# Update models for existing records
class StoryWorldUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    privacy_setting: Optional[PrivacySettingEnum] = None
    learning_objectives: Optional[LearningObjectives] = None
    collaboration_settings: Optional[CollaborationSettings] = None
    status: Optional[WorldStatusEnum] = None
    tags: Optional[List[str]] = None
    featured: Optional[bool] = None

class ContributionUpdate(BaseModel):
    status: Optional[ContributionStatusEnum] = None
    peer_reactions: Optional[PeerReactions] = None

# Statistics and analytics models
class WorldAnalytics(BaseModel):
    world_id: str
    total_contributions: int
    unique_contributors: int
    average_contribution_length: float
    most_active_contributor: Optional[str] = None
    learning_progress_metrics: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserWorldStats(BaseModel):
    user_id: str
    worlds_created: int
    worlds_contributed_to: int
    total_contributions: int
    total_speaking_time_minutes: float
    favorite_genres: List[str]
    languages_practiced: List[str]
    achievement_badges: List[str]
