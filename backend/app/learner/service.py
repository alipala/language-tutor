from datetime import datetime
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LearnerService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.institutions = db.institutions
        self.institutional_learners = db.institutional_learners
        self.tutors = db.tutors
        self.invitations = db.invitations

    async def enroll_learner_by_admin(
        self,
        email: str,
        name: str,
        institution_id: str,
        tutor_id: str,
        enrolled_by: str
    ) -> Dict[str, Any]:
        """
        Admin enrolls a new learner (sends invitation)
        """
        # Check learner limit
        institution = await self.institutions.find_one(
            {"_id": ObjectId(institution_id)}
        )
        if not institution:
            raise ValueError("Institution not found")

        learner_count = await self.institutional_learners.count_documents({
            "institution_id": institution_id,
            "is_active": True
        })

        if learner_count >= institution["max_learners"]:
            raise ValueError(
                f"Maximum learner limit ({institution['max_learners']}) reached"
            )

        # Check if tutor exists and belongs to institution
        tutor = await self.tutors.find_one({
            "_id": ObjectId(tutor_id),
            "institution_id": institution_id,
            "is_active": True
        })
        if not tutor:
            raise ValueError("Tutor not found or not active")

        # Check if learner already exists in this institution
        existing_enrollment = await self.institutional_learners.find_one({
            "email": email,
            "institution_id": institution_id
        })
        if existing_enrollment:
            raise ValueError("Learner already enrolled in this institution")

        # Generate invitation code
        invitation_code = secrets.token_urlsafe(32)

        # Create invitation
        invitation = {
            "email": email,
            "name": name,
            "invitation_type": "learner",
            "institution_id": institution_id,
            "invited_by": enrolled_by,
            "assigned_tutor_id": tutor_id,
            "code": invitation_code,
            "is_accepted": False,
            "created_at": datetime.utcnow()
        }

        result = await self.invitations.insert_one(invitation)

        # TODO: Send email with invitation link

        return {
            "invitation_id": str(result.inserted_id),
            "invitation_code": invitation.get("code"),
            "message": "Learner invitation sent"
        }

    async def self_signup_with_code(
        self,
        email: str,
        name: str,
        password: str,
        institution_code: str
    ) -> Dict[str, Any]:
        """
        Learner signs up using institution code
        """
        # Find institution
        institution = await self.institutions.find_one({
            "institution_code": institution_code,
            "is_active": True
        })

        if not institution:
            raise ValueError("Invalid institution code")

        institution_id = str(institution["_id"])

        # Check learner limit
        learner_count = await self.institutional_learners.count_documents({
            "institution_id": institution_id,
            "is_active": True
        })

        if learner_count >= institution["max_learners"]:
            raise ValueError(
                f"Institution has reached maximum learner limit ({institution['max_learners']})"
            )

        # Check if user already exists
        existing_user = await self.users.find_one({"email": email})

        if existing_user:
            user_id = str(existing_user["_id"])
            # Check if already enrolled in this institution
            existing_enrollment = await self.institutional_learners.find_one({
                "user_id": user_id,
                "institution_id": institution_id
            })
            if existing_enrollment:
                raise ValueError("You are already enrolled in this institution")
        else:
            # Create new user account
            # Handle bcrypt 72-byte limit
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password = password_bytes[:72].decode('utf-8', errors='ignore')

            user = {
                "email": email,
                "name": name,
                "hashed_password": pwd_context.hash(password),
                "account_type": "institutional_learner",
                "is_active": True,
                "is_verified": False,
                "created_at": datetime.utcnow()
            }

            result = await self.users.insert_one(user)
            user_id = str(result.inserted_id)

        # Assign to first available tutor (simple round-robin or random assignment)
        tutor = await self.tutors.find_one({
            "institution_id": institution_id,
            "is_active": True
        })

        if not tutor:
            raise ValueError("No active tutors available in this institution")

        tutor_id = str(tutor["_id"])

        # Create enrollment record (without consent yet)
        enrollment = {
            "user_id": user_id,
            "email": email,  # Store email for easy lookup
            "institution_id": institution_id,
            "tutor_id": tutor_id,
            "enrollment_method": "self_signup",
            "consent_given": False,  # Will be granted in consent flow
            "enrolled_at": datetime.utcnow(),
            "is_active": True
        }

        await self.institutional_learners.insert_one(enrollment)

        return {
            "user_id": user_id,
            "institution_id": institution_id,
            "tutor_id": tutor_id,
            "requires_consent": True,
            "message": "Account created. Consent required."
        }

    async def get_tutor_learners(
        self,
        tutor_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all learners assigned to a tutor
        """
        enrollments = await self.institutional_learners.find({
            "tutor_id": tutor_id,
            "is_active": True
        }).to_list(length=None)

        learners = []
        for enrollment in enrollments:
            user = await self.users.find_one(
                {"_id": ObjectId(enrollment["user_id"])}
            )
            if user:
                learners.append({
                    "user_id": enrollment["user_id"],
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "consent_given": enrollment.get("consent_given", False),
                    "enrolled_at": enrollment.get("enrolled_at").isoformat() if enrollment.get("enrolled_at") else None
                })

        return learners

    async def get_institution_learners(
        self,
        institution_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all learners for an institution
        """
        enrollments = await self.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)

        learners = []
        for enrollment in enrollments:
            # Handle both valid ObjectIds and string user_ids (for test data)
            user_id = enrollment["user_id"]
            user = None

            try:
                if ObjectId.is_valid(user_id):
                    user = await self.users.find_one({"_id": ObjectId(user_id)})
                else:
                    # For test data or other string IDs, try to find by email if available
                    email = enrollment.get("email")
                    if email:
                        user = await self.users.find_one({"email": email})
            except:
                # If ObjectId conversion fails, try email lookup
                email = enrollment.get("email")
                if email:
                    user = await self.users.find_one({"email": email})

            # Get tutor info
            tutor_id = enrollment["tutor_id"]
            tutor_name = "Unknown"
            try:
                if ObjectId.is_valid(tutor_id):
                    tutor = await self.tutors.find_one({"_id": ObjectId(tutor_id)})
                    if tutor:
                        tutor_name = tutor.get("name", "Unknown")
            except:
                pass

            # Use enrollment data as fallback if user not found
            name = "Unknown"
            email = "unknown@email.com"

            if user:
                name = user.get("name", "Unknown")
                email = user.get("email", "unknown@email.com")
            elif enrollment.get("email"):
                # For enrollments without valid users, use stored email
                email = enrollment.get("email")
                name = f"Pending ({email})"

            learners.append({
                "user_id": user_id,
                "name": name,
                "email": email,
                "tutor_name": tutor_name,
                "consent_given": enrollment.get("consent_given", False),
                "enrollment_method": enrollment.get("enrollment_method"),
                "enrolled_at": enrollment.get("enrolled_at").isoformat() if enrollment.get("enrolled_at") else None
            })

        return learners
