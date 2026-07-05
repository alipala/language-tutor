"""
Institution API endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.institution.service import InstitutionService
from app.institution.schemas import (
    InstitutionSignupRequest,
    InstitutionSignupResponse,
    InstitutionLoginRequest,
    InstitutionLoginResponse,
    ActivationCodePreviewResponse
)
from app.config.feature_flags import feature_flags
from database import database
from auth import create_access_token

router = APIRouter(prefix="/institution", tags=["institution"])

def check_feature_enabled():
    """Check if institutional features are enabled"""
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Institutional features are not enabled"
        )


@router.get("/activation-code/{code}/preview",
            response_model=ActivationCodePreviewResponse,
            dependencies=[Depends(check_feature_enabled)])
async def preview_activation_code(code: str):
    """
    PUBLIC (no auth) preview of an activation code, used to pre-fill the
    school-admin activation/signup page. Returns ONLY non-sensitive institution
    metadata that the master admin already entered when generating the code —
    so the invited admin only has to confirm and set a password.

    Mirrors the same validity rules as create_institution(): the code must exist,
    not already be consumed, and not be expired.
    """
    code_doc = await database.activation_codes.find_one({"activation_code": code})
    if not code_doc:
        raise HTTPException(status_code=404, detail="Invalid activation code")

    if code_doc.get("status") in ("used", "active_trial", "active_paid"):
        raise HTTPException(status_code=409, detail="This activation code has already been used")

    expires_at = code_doc.get("code_expires_at")
    if expires_at and expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="This activation code has expired")
    if code_doc.get("status") == "expired":
        raise HTTPException(status_code=410, detail="This activation code has expired")

    return ActivationCodePreviewResponse(
        institution_name=code_doc.get("institution_name", ""),
        institution_email=code_doc.get("institution_email", ""),
        institution_type=code_doc.get("institution_type", "school"),
        subscription_plan=code_doc.get("target_plan", "starter"),
        is_trial=bool(code_doc.get("is_trial", True)),
        max_tutors=int(code_doc.get("max_tutors", 0) or 0),
        max_learners=int(code_doc.get("max_learners", 0) or 0),
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
            activation_code=signup_data.activation_code,
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
