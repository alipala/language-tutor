"""
Consent records for GDPR compliance and data sharing audit trail
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .institution import PyObjectId

class ConsentRecordBase(BaseModel):
    learner_id: str  # user_id from users collection
    institution_id: str
    tutor_id: str

    # What data is shared
    data_shared: List[str] = Field(
        default_factory=lambda: [
            "assessment_results",
            "learning_plans",
            "practice_sessions",
            "progress_metrics"
        ]
    )

    # Consent action
    action: str = Field(...)  # "granted" or "revoked"
    action_date: datetime = Field(default_factory=datetime.utcnow)

    # Audit trail
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class ConsentRecord(ConsentRecordBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
