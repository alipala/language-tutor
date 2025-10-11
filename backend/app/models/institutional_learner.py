"""
Institutional learner enrollment records
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .institution import PyObjectId

class InstitutionalLearnerBase(BaseModel):
    user_id: str  # Links to users collection
    institution_id: str
    tutor_id: str

    # Enrollment method
    enrollment_method: str = Field(default="admin_invite")  # admin_invite, self_signup, csv_bulk

    # Consent
    consent_given: bool = Field(default=False)
    consent_date: Optional[datetime] = None
    consent_revoked: bool = Field(default=False)
    consent_revoked_date: Optional[datetime] = None

    # Metadata
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

class InstitutionalLearner(InstitutionalLearnerBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
