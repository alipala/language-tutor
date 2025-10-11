from datetime import datetime
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import secrets

class TutorService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.tutors = db.tutors
        self.invitations = db.invitations
        self.institutions = db.institutions

    async def invite_tutor(
        self,
        email: str,
        name: str,
        institution_id: str,
        invited_by: str
    ) -> Dict[str, Any]:
        """
        Send invitation to a tutor
        """
        # Check if tutor already exists
        existing = await self.tutors.find_one({
            "email": email,
            "institution_id": institution_id
        })
        if existing:
            raise ValueError("Tutor already exists")

        # Check institution limits
        institution = await self.institutions.find_one(
            {"_id": ObjectId(institution_id)}
        )
        if not institution:
            raise ValueError("Institution not found")

        tutor_count = await self.tutors.count_documents({
            "institution_id": institution_id,
            "is_active": True
        })

        if tutor_count >= institution["max_tutors"]:
            raise ValueError(
                f"Maximum tutor limit ({institution['max_tutors']}) reached"
            )

        # Generate invitation code
        invitation_code = secrets.token_urlsafe(32)

        # Create invitation
        invitation = {
            "email": email,
            "name": name,
            "invitation_type": "tutor",
            "institution_id": institution_id,
            "invited_by": invited_by,
            "code": invitation_code,
            "is_accepted": False,
            "created_at": datetime.utcnow()
        }

        result = await self.invitations.insert_one(invitation)

        # TODO: Send email with invitation link
        # invitation_url = f"https://mytaco.ai/invitation/{invitation_code}"

        return {
            "invitation_id": str(result.inserted_id),
            "invitation_code": invitation_code,
            "email": email,
            "message": "Invitation sent successfully"
        }

    async def accept_invitation(
        self,
        invitation_code: str,
        bio: str = None,
        qualifications: str = None
    ) -> Dict[str, Any]:
        """
        Accept tutor invitation and create tutor account
        """
        # Find invitation
        invitation = await self.invitations.find_one({
            "code": invitation_code,
            "invitation_type": "tutor",
            "is_accepted": False
        })

        if not invitation:
            raise ValueError("Invalid or expired invitation")

        # Create tutor account
        tutor = {
            "email": invitation["email"],
            "name": invitation["name"],
            "institution_id": invitation["institution_id"],
            "bio": bio,
            "qualifications": qualifications,
            "assigned_learners": [],
            "is_active": True,
            "invitation_accepted": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.tutors.insert_one(tutor)

        # Mark invitation as accepted
        await self.invitations.update_one(
            {"_id": invitation["_id"]},
            {
                "$set": {
                    "is_accepted": True,
                    "accepted_at": datetime.utcnow()
                }
            }
        )

        return {
            "tutor_id": str(result.inserted_id),
            "message": "Invitation accepted successfully"
        }

    async def get_institution_tutors(
        self,
        institution_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all tutors for an institution
        """
        tutors = await self.tutors.find({
            "institution_id": institution_id
        }).to_list(length=None)

        return [
            {
                "id": str(tutor["_id"]),
                "email": tutor["email"],
                "name": tutor["name"],
                "is_active": tutor["is_active"],
                "invitation_accepted": tutor["invitation_accepted"],
                "assigned_learners_count": len(tutor.get("assigned_learners", []))
            }
            for tutor in tutors
        ]
