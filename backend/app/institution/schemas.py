"""
Schemas for institution API
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class InstitutionSignupRequest(BaseModel):
    """Schema for institution signup"""
    name: str = Field(..., min_length=2, max_length=200)
    domain: Optional[str] = Field(None, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_name: str = Field(..., min_length=2, max_length=100)
    # Optional subscription plan selection
    subscription_plan: str = Field(default="starter")

    @validator('subscription_plan')
    def validate_plan(cls, v):
        valid_plans = ['starter', 'professional', 'enterprise']
        if v not in valid_plans:
            raise ValueError(f'Plan must be one of: {valid_plans}')
        return v

class InstitutionSignupResponse(BaseModel):
    """Response after successful signup"""
    institution_id: str
    institution_code: str
    admin_email: str
    subscription_plan: str
    message: str

class InstitutionLoginRequest(BaseModel):
    """Schema for admin login"""
    admin_email: EmailStr
    password: str

class InstitutionLoginResponse(BaseModel):
    """Response after successful login"""
    access_token: str
    token_type: str
    institution_id: str
    institution_name: str
    admin_email: str
