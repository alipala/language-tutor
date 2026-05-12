"""
Institution management business logic
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import bcrypt
from app.institution.utils import generate_institution_code

class InstitutionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.institutions = db.institutions
        self.tutors = db.tutors

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            print(f"[INSTITUTION_AUTH] Error in verify_password: {str(e)}")
            return False

    async def create_institution(
        self,
        name: str,
        admin_email: str,
        admin_password: str,
        admin_name: str,
        activation_code: str,
        institution_type: str = "school",
        subscription_plan: str = "starter"
    ) -> Dict[str, Any]:
        """
        Create new institution and admin account
        """
        # Validate activation code
        activation_codes = self.db.activation_codes
        code_doc = await activation_codes.find_one({"activation_code": activation_code})

        if not code_doc:
            raise ValueError("Invalid activation code")

        if code_doc["status"] in ("used", "active_trial", "active_paid"):
            raise ValueError("This activation code has already been used")

        # BUG #1 FIX: enforce expiry by time, not just by manual status
        code_expires_at = code_doc.get("code_expires_at")
        if code_expires_at and code_expires_at < datetime.utcnow():
            await activation_codes.update_one(
                {"activation_code": activation_code},
                {"$set": {"status": "expired", "updated_at": datetime.utcnow()}}
            )
            raise ValueError("This activation code has expired")

        if code_doc["status"] == "expired":
            raise ValueError("This activation code has expired")

        # Check if admin email already exists
        existing = await self.institutions.find_one({"admin_email": admin_email})
        if existing:
            raise ValueError("Institution with this admin email already exists")

        # Generate unique institution code
        institution_code = generate_institution_code(name)
        while await self.institutions.find_one({"institution_code": institution_code}):
            institution_code = generate_institution_code(name)

        # BUG #2 FIX: use limits and plan from the activation code, not the request
        max_tutors = code_doc.get("max_tutors", 10)
        max_learners = code_doc.get("max_learners", 200)
        is_trial = code_doc.get("is_trial", True)
        trial_duration_days = code_doc.get("trial_duration_days", 30)
        resolved_plan = code_doc.get("target_plan", subscription_plan)
        resolved_type = code_doc.get("institution_type", institution_type)

        now = datetime.utcnow()

        # Create institution document
        institution = {
            "name": name,
            "institution_type": resolved_type,
            "admin_email": admin_email,
            "admin_password": self.hash_password(admin_password),
            "admin_name": admin_name,
            "institution_code": institution_code,
            "subscription_plan": resolved_plan,
            "max_tutors": max_tutors,
            "max_learners": max_learners,
            "is_trial": is_trial,
            "trial_ends_at": now + timedelta(days=trial_duration_days) if is_trial else None,
            "activation_code": activation_code,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        result = await self.institutions.insert_one(institution)

        # BUG #4+5 FIX: correct status value + set activated_at
        new_status = "active_trial" if is_trial else "active_paid"
        await activation_codes.update_one(
            {"activation_code": activation_code},
            {
                "$set": {
                    "status": new_status,
                    "activated_at": now,
                    "used_at": now,
                    "used_by_institution_id": str(result.inserted_id),
                    "used_by_email": admin_email,
                    "updated_at": now
                }
            }
        )

        return {
            "institution_id": str(result.inserted_id),
            "institution_code": institution_code,
            "admin_email": admin_email,
            "subscription_plan": resolved_plan
        }

    async def authenticate_admin(
        self,
        admin_email: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate institution admin
        """
        institution = await self.institutions.find_one({"admin_email": admin_email})

        if not institution:
            return None

        if not self.verify_password(password, institution["admin_password"]):
            return None

        return {
            "institution_id": str(institution["_id"]),
            "institution_name": institution["name"],
            "admin_email": institution["admin_email"],
            "subscription_plan": institution["subscription_plan"]
        }

    async def get_institution(self, institution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get institution details by ID
        """
        from bson import ObjectId
        
        try:
            institution = await self.institutions.find_one({"_id": ObjectId(institution_id)})
        except Exception:
            # Invalid ObjectId format
            return None
        
        if not institution:
            return None
        
        # Convert ObjectId to string and remove password
        institution["id"] = str(institution["_id"])
        del institution["_id"]
        del institution["admin_password"]  # Never return password
        
        return institution

    async def get_institution_stats(self, institution_id: str) -> Dict[str, Any]:
        """
        Get institution statistics
        """
        from bson import ObjectId

        # Count tutors
        tutor_count = await self.tutors.count_documents({
            "institution_id": institution_id,
            "is_active": True
        })

        # Count learners
        learner_count = await self.db.institutional_learners.count_documents({
            "institution_id": institution_id,
            "is_active": True
        })

        # Get institution details
        institution = await self.institutions.find_one({"_id": ObjectId(institution_id)})

        if not institution:
            raise ValueError(f"Institution with ID {institution_id} not found")

        return {
            "total_tutors": tutor_count,
            "total_learners": learner_count,
            "max_tutors": institution["max_tutors"],
            "max_learners": institution["max_learners"],
            "subscription_plan": institution["subscription_plan"]
        }
