"""
Consent management business logic
"""
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

class ConsentService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.consent_records = db.consent_records
        self.institutional_learners = db.institutional_learners
        self.institutions = db.institutions
        self.tutors = db.tutors

    async def check_consent(
        self,
        learner_id: str,
        institution_id: str
    ) -> bool:
        """
        Check if learner has given consent to institution
        """
        enrollment = await self.institutional_learners.find_one({
            "user_id": learner_id,
            "institution_id": institution_id,
            "consent_given": True,
            "consent_revoked": False,
            "is_active": True
        })
        return enrollment is not None

    async def grant_consent(
        self,
        learner_id: str,
        institution_id: str,
        tutor_id: str,
        data_to_share: list,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Grant consent and create audit record
        """
        # 1. Update institutional_learner record
        update_result = await self.institutional_learners.update_one(
            {
                "user_id": learner_id,
                "institution_id": institution_id
            },
            {
                "$set": {
                    "consent_given": True,
                    "consent_date": datetime.utcnow(),
                    "consent_revoked": False,
                    "consent_revoked_date": None
                }
            }
        )

        if update_result.modified_count == 0:
            raise ValueError("Learner enrollment not found")

        # 2. Create consent audit record
        consent_record = {
            "learner_id": learner_id,
            "institution_id": institution_id,
            "tutor_id": tutor_id,
            "data_shared": data_to_share,
            "action": "granted",
            "action_date": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent
        }

        result = await self.consent_records.insert_one(consent_record)

        return {
            "success": True,
            "consent_record_id": str(result.inserted_id),
            "message": "Consent granted successfully"
        }

    async def revoke_consent(
        self,
        learner_id: str,
        institution_id: str
    ) -> Dict[str, Any]:
        """
        Revoke consent and create audit record
        """
        # 1. Get enrollment to find tutor_id
        enrollment = await self.institutional_learners.find_one({
            "user_id": learner_id,
            "institution_id": institution_id
        })

        if not enrollment:
            raise ValueError("Enrollment not found")

        # 2. Update enrollment
        await self.institutional_learners.update_one(
            {"_id": enrollment["_id"]},
            {
                "$set": {
                    "consent_revoked": True,
                    "consent_revoked_date": datetime.utcnow()
                }
            }
        )

        # 3. Create revocation audit record
        consent_record = {
            "learner_id": learner_id,
            "institution_id": institution_id,
            "tutor_id": enrollment["tutor_id"],
            "data_shared": [],
            "action": "revoked",
            "action_date": datetime.utcnow()
        }

        result = await self.consent_records.insert_one(consent_record)

        return {
            "success": True,
            "consent_record_id": str(result.inserted_id),
            "message": "Consent revoked successfully"
        }

    async def get_consent_status(
        self,
        learner_id: str,
        institution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed consent status for a learner
        """
        # Get enrollment
        enrollment = await self.institutional_learners.find_one({
            "user_id": learner_id,
            "institution_id": institution_id
        })

        if not enrollment:
            return None

        # Get institution and tutor details
        institution = await self.institutions.find_one(
            {"_id": ObjectId(institution_id)}
        )
        tutor = await self.tutors.find_one(
            {"_id": ObjectId(enrollment["tutor_id"])}
        )

        # Get latest consent record
        latest_consent = await self.consent_records.find_one(
            {
                "learner_id": learner_id,
                "institution_id": institution_id
            },
            sort=[("action_date", -1)]
        )

        return {
            "has_consent": enrollment.get("consent_given", False),
            "consent_given_date": enrollment.get("consent_date"),
            "consent_revoked": enrollment.get("consent_revoked", False),
            "institution_name": institution["name"] if institution else "Unknown",
            "tutor_name": tutor["name"] if tutor else "Unknown",
            "data_shared": latest_consent.get("data_shared", []) if latest_consent else []
        }
