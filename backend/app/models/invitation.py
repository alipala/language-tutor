"""
Invitation model for enrolling learners and tutors
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
from .institution import PyObjectId

class InvitationBase(BaseModel):
    email: EmailStr
    invitation_type: str = Field(...)  # "tutor" or "learner"
    institution_id: str
    invited_by: str  # admin user_id

    # Invitation code
    code: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # For learners
    assigned_tutor_id: Optional[str] = None

    # Status
    is_accepted: bool = Field(default=False)
    accepted_at: Optional[datetime] = None
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=7)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

class Invitation(InvitationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
