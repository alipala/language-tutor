from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.learner.service import LearnerService
from app.learner.schemas import *
from app.config.feature_flags import feature_flags
from app.db.database import get_database

router = APIRouter(prefix="/api/v1/learners", tags=["learners"])

def check_feature_enabled():
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(403, "Institutional features not enabled")

@router.post("/enroll", dependencies=[Depends(check_feature_enabled)])
async def enroll_learner(
    enroll_data: LearnerEnrollRequest,
    db=Depends(get_database)
):
    """Admin enrolls a learner (sends invitation)"""
    service = LearnerService(db)
    try:
        return await service.enroll_learner_by_admin(
            email=enroll_data.email,
            name=enroll_data.name,
            institution_id=enroll_data.institution_id,
            tutor_id=enroll_data.tutor_id,
            enrolled_by=enroll_data.enrolled_by
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/self-signup",
    response_model=LearnerSelfSignupResponse,
    dependencies=[Depends(check_feature_enabled)])
async def self_signup(
    signup_data: LearnerSelfSignupRequest,
    db=Depends(get_database)
):
    """Learner signs up using institution code"""
    service = LearnerService(db)
    try:
        return await service.self_signup_with_code(
            email=signup_data.email,
            name=signup_data.name,
            password=signup_data.password,
            institution_code=signup_data.institution_code
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/tutor/{tutor_id}",
    dependencies=[Depends(check_feature_enabled)])
async def get_tutor_learners(
    tutor_id: str,
    db=Depends(get_database)
):
    """Get all learners assigned to a tutor"""
    service = LearnerService(db)
    return await service.get_tutor_learners(tutor_id)

@router.get("/institution/{institution_id}",
    dependencies=[Depends(check_feature_enabled)])
async def get_institution_learners(
    institution_id: str,
    db=Depends(get_database)
):
    """Get all learners for an institution"""
    service = LearnerService(db)
    return await service.get_institution_learners(institution_id)
