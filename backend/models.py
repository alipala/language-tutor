from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

# Custom ObjectId field for Pydantic models
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, **kwargs):
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
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        
class UserResponse(UserBase):
    id: str = Field(..., alias="_id")
    
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

# Conversation session models
class ConversationMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    language: str
    level: str
    topic: Optional[str] = None
    messages: List[ConversationMessage] = []
    duration_minutes: float = 0.0
    message_count: int = 0
    summary: Optional[str] = None
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
