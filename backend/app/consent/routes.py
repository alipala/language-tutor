"""
Consent API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.consent.service import ConsentService
from app.consent.schemas import (
    ConsentGrantRequest,
    ConsentRevokeRequest,
    ConsentStatusResponse
)
from app.config.feature_flags import feature_flags
from database import database

router = APIRouter(prefix="/consent", tags=["consent"])

def check_feature_enabled():
    """Dependency to check if institutional features are enabled"""
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Institutional features are not enabled"
        )

@router.post("/grant", dependencies=[Depends(check_feature_enabled)])
async def grant_consent(
    request: Request,
    consent_data: ConsentGrantRequest,
    db = Depends(lambda: database)
) -> Dict[str, Any]:
    """
    Grant consent for data sharing with institution
    """
    service = ConsentService(db)

    # Extract IP and user agent from request
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        result = await service.grant_consent(
            learner_id=consent_data.learner_id,
            institution_id=consent_data.institution_id,
            tutor_id=consent_data.tutor_id,
            data_to_share=[
                "assessment_results",
                "learning_plans",
                "practice_sessions",
                "progress_metrics"
            ],
            ip_address=ip_address,
            user_agent=user_agent
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/revoke", dependencies=[Depends(check_feature_enabled)])
async def revoke_consent(
    consent_data: ConsentRevokeRequest,
    db = Depends(lambda: database)
) -> Dict[str, Any]:
    """
    Revoke consent for data sharing
    """
    service = ConsentService(db)

    try:
        result = await service.revoke_consent(
            learner_id=consent_data.learner_id,
            institution_id=consent_data.institution_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/status/{learner_id}/{institution_id}",
            response_model=ConsentStatusResponse,
            dependencies=[Depends(check_feature_enabled)])
async def get_consent_status(
    learner_id: str,
    institution_id: str,
    db = Depends(lambda: database)
):
    """
    Get consent status for a learner
    """
    service = ConsentService(db)
    status = await service.get_consent_status(learner_id, institution_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found"
        )

    return status
