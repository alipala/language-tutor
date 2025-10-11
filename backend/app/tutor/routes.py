from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.tutor.service import TutorService
from app.tutor.schemas import *
from app.config.feature_flags import feature_flags
from database import get_database

router = APIRouter(prefix="/tutors", tags=["tutors"])

def check_feature_enabled():
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(403, "Institutional features not enabled")

@router.post("/invite", dependencies=[Depends(check_feature_enabled)])
async def invite_tutor(
    invite_data: TutorInviteRequest,
    db=Depends(get_database)
):
    service = TutorService(db)
    try:
        return await service.invite_tutor(
            email=invite_data.email,
            name=invite_data.name,
            institution_id=invite_data.institution_id,
            invited_by=invite_data.invited_by
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/accept-invite", dependencies=[Depends(check_feature_enabled)])
async def accept_invitation(
    accept_data: TutorAcceptInviteRequest,
    db=Depends(get_database)
):
    service = TutorService(db)
    try:
        return await service.accept_invitation(
            invitation_code=accept_data.invitation_code,
            bio=accept_data.bio,
            qualifications=accept_data.qualifications
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/institution/{institution_id}",
    response_model=List[TutorResponse],
    dependencies=[Depends(check_feature_enabled)])
async def get_institution_tutors(
    institution_id: str,
    db=Depends(get_database)
):
    service = TutorService(db)
    return await service.get_institution_tutors(institution_id)
