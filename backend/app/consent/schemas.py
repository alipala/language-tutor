"""
Pydantic schemas for consent API
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ConsentRequest(BaseModel):
    """Schema for requesting consent from a learner"""
    learner_id: str
    institution_id: str
    tutor_id: str
    data_to_share: List[str] = [
        "assessment_results",
        "learning_plans",
        "practice_sessions",
        "progress_metrics"
    ]

class ConsentGrantRequest(BaseModel):
    """Schema for granting consent"""
    learner_id: str
    institution_id: str
    tutor_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class ConsentRevokeRequest(BaseModel):
    """Schema for revoking consent"""
    learner_id: str
    institution_id: str
    reason: Optional[str] = None

class ConsentStatusResponse(BaseModel):
    """Schema for consent status"""
    has_consent: bool
    consent_given_date: Optional[datetime] = None
    consent_revoked: bool = False
    institution_name: str
    tutor_name: str
    data_shared: List[str]
