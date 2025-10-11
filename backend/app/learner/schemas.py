from pydantic import BaseModel, EmailStr
from typing import Optional

class LearnerEnrollRequest(BaseModel):
    """Admin enrolls learner"""
    email: EmailStr
    name: str
    institution_id: str
    tutor_id: str
    enrolled_by: str  # admin user_id

class LearnerSelfSignupRequest(BaseModel):
    """Learner signs up with institution code"""
    email: EmailStr
    name: str
    password: str
    institution_code: str

class LearnerSelfSignupResponse(BaseModel):
    user_id: str
    institution_id: str
    tutor_id: str
    requires_consent: bool
    message: str

class LearnerResponse(BaseModel):
    user_id: str
    name: str
    email: str
    consent_given: bool
    enrolled_at: str
