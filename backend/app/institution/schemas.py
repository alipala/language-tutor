"""
Schemas for institution API
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class InstitutionSignupRequest(BaseModel):
    """Schema for institution signup"""
    name: str = Field(..., min_length=2, max_length=200)
    institution_type: str = Field(default="school")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=72, description="Password must be between 8-72 characters (bcrypt limit)")
    admin_name: str = Field(..., min_length=2, max_length=100)
    activation_code: str = Field(..., min_length=1, description="Activation code received via email")
    # Optional subscription plan - managed by MyTacoAI admin
    subscription_plan: Optional[str] = Field(default="starter")

    @validator('institution_type')
    def validate_type(cls, v):
        valid_types = ['school', 'university', 'language_center', 'corporate']
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {valid_types}')
        return v

    @validator('subscription_plan')
    def validate_plan(cls, v):
        if v is None:
            return "starter"
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
    password: str = Field(..., max_length=72, description="Password max 72 characters (bcrypt limit)")

class InstitutionLoginResponse(BaseModel):
    """Response after successful login"""
    access_token: str
    token_type: str
    institution_id: str
    institution_name: str
    admin_email: str
