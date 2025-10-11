"""
Tutor model for instructors monitoring learners
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .institution import PyObjectId

class TutorBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    institution_id: str  # Link to institution

    # Profile
    bio: Optional[str] = Field(None, max_length=500)
    qualifications: Optional[str] = Field(None, max_length=500)

    # Assigned learners (list of user_ids)
    assigned_learners: List[str] = Field(default_factory=list)

    # Status
    is_active: bool = Field(default=True)
    invitation_accepted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Tutor(TutorBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
