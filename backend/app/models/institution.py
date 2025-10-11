"""
Institution model for organizations using MyTaco AI
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class InstitutionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    institution_type: str = Field(default="school")  # school, university, language_center, corporate
    logo_url: Optional[str] = None
    admin_email: EmailStr
    institution_code: str = Field(..., min_length=6, max_length=20)  # For learner signup

    # Subscription info
    subscription_plan: str = Field(default="starter")  # starter, professional, enterprise
    max_tutors: int = Field(default=2)
    max_learners: int = Field(default=50)

    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Institution(InstitutionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
