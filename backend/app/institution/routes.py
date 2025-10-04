"""
Institution API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.institution.service import InstitutionService
from app.institution.schemas import (
    InstitutionSignupRequest,
    InstitutionSignupResponse,
    InstitutionLoginRequest,
    InstitutionLoginResponse
)
from app.config.feature_flags import feature_flags
from database import database
from auth import create_access_token

router = APIRouter(prefix="/api/v1/institution", tags=["institution"])

def check_feature_enabled():
    """Check if institutional features are enabled"""
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Institutional features are not enabled"
        )

@router.post("/signup",
            response_model=InstitutionSignupResponse,
            dependencies=[Depends(check_feature_enabled)])
async def signup_institution(
    signup_data: InstitutionSignupRequest,
    db = Depends(lambda: database)
):
    """
    Register a new institution and admin account
    """
    service = InstitutionService(db)
    try:
        result = await service.create_institution(
            name=signup_data.name,
            admin_email=signup_data.admin_email,
            admin_password=signup_data.admin_password,
            admin_name=signup_data.admin_name,
            institution_type=signup_data.institution_type,
            subscription_plan=signup_data.subscription_plan
        )

        return InstitutionSignupResponse(
            **result,
            message="Institution created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login",
            response_model=InstitutionLoginResponse,
            dependencies=[Depends(check_feature_enabled)])
async def login_institution(
    login_data: InstitutionLoginRequest,
    db = Depends(lambda: database)
):
    """
    Authenticate institution admin
    """
    service = InstitutionService(db)
    admin_data = await service.authenticate_admin(
        admin_email=login_data.admin_email,
        password=login_data.password
    )

    if not admin_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": admin_data["admin_email"],
            "institution_id": admin_data["institution_id"],
            "role": "admin"
        }
    )

    return InstitutionLoginResponse(
        access_token=access_token,
        token_type="bearer",
        **admin_data
    )

@router.get("/{institution_id}",
            dependencies=[Depends(check_feature_enabled)])
async def get_institution(
    institution_id: str,
    db = Depends(lambda: database)
) -> Dict[str, Any]:
    """
    Get institution details
    """
    service = InstitutionService(db)
    institution = await service.get_institution(institution_id)
    
    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )
    
    return institution

@router.get("/stats/{institution_id}",
            dependencies=[Depends(check_feature_enabled)])
async def get_institution_stats(
    institution_id: str,
    db = Depends(lambda: database)
) -> Dict[str, Any]:
    """
    Get institution statistics
    """
    service = InstitutionService(db)
    return await service.get_institution_stats(institution_id)
