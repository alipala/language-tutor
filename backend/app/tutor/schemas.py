from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class TutorInviteRequest(BaseModel):
    email: EmailStr
    name: str
    institution_id: str
    invited_by: str  # admin user_id

class TutorAcceptInviteRequest(BaseModel):
    invitation_code: str
    bio: Optional[str] = None
    qualifications: Optional[str] = None

class TutorBulkInviteRequest(BaseModel):
    institution_id: str
    invited_by: str
    tutors: List[dict]  # [{"email": "", "name": ""}, ...]

class TutorResponse(BaseModel):
    id: str
    email: str
    name: str
    institution_id: str
    is_active: bool
    invitation_accepted: bool
