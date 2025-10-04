"""
Institution management business logic
"""
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext
from app.institution.utils import generate_institution_code

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class InstitutionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.institutions = db.institutions
        self.tutors = db.tutors

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        # bcrypt has a 72-byte limit, truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_institution(
        self,
        name: str,
        admin_email: str,
        admin_password: str,
        admin_name: str,
        institution_type: str = "school",
        subscription_plan: str = "starter"
    ) -> Dict[str, Any]:
        """
        Create new institution and admin account
        """
        # Check if admin email already exists
        existing = await self.institutions.find_one({"admin_email": admin_email})
        if existing:
            raise ValueError("Institution with this admin email already exists")

        # Generate unique institution code
        institution_code = generate_institution_code(name)

        # Ensure code is unique
        while await self.institutions.find_one({"institution_code": institution_code}):
            institution_code = generate_institution_code(name)

        # Set plan limits
        plan_limits = {
            "starter": {"max_tutors": 2, "max_learners": 50},
            "professional": {"max_tutors": 10, "max_learners": 200},
            "enterprise": {"max_tutors": 50, "max_learners": 1000}
        }
        limits = plan_limits.get(subscription_plan, plan_limits["starter"])

        # Create institution document
        institution = {
            "name": name,
            "institution_type": institution_type,
            "admin_email": admin_email,
            "admin_password": self.hash_password(admin_password),
            "admin_name": admin_name,
            "institution_code": institution_code,
            "subscription_plan": subscription_plan,
            "max_tutors": limits["max_tutors"],
            "max_learners": limits["max_learners"],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.institutions.insert_one(institution)

        return {
            "institution_id": str(result.inserted_id),
            "institution_code": institution_code,
            "admin_email": admin_email,
            "subscription_plan": subscription_plan
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
