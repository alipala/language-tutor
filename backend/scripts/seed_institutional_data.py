#!/usr/bin/env python3
"""
Seed institutional data for local development
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "language_tutor")

async def seed_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("🌱 Seeding institutional data...")

    # 1. Create mock institutions
    institutions = [
        {
            "name": "Lincoln Academy",
            "domain": "lincoln-academy.edu",
            "admin_email": "admin@lincoln-academy.edu",
            "institution_code": "LINCOLN2025",
            "subscription_plan": "professional",
            "max_tutors": 10,
            "max_learners": 200,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Global Language Institute",
            "domain": "gli.org",
            "admin_email": "admin@gli.org",
            "institution_code": "GLI2025",
            "subscription_plan": "enterprise",
            "max_tutors": 50,
            "max_learners": 1000,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "StartUp Language School",
            "domain": "startuplang.com",
            "admin_email": "admin@startuplang.com",
            "institution_code": "STARTUP2025",
            "subscription_plan": "starter",
            "max_tutors": 2,
            "max_learners": 50,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    result = await db.institutions.insert_many(institutions)
    institution_ids = [str(id) for id in result.inserted_ids]
    print(f"✅ Created {len(institution_ids)} institutions")

    # 2. Create mock tutors
    tutors = [
        {
            "email": "sarah.johnson@lincoln-academy.edu",
            "name": "Sarah Johnson",
            "institution_id": institution_ids[0],
            "bio": "Experienced English teacher with 10 years of experience",
            "qualifications": "TESOL Certified, M.A. in Linguistics",
            "assigned_learners": [],
            "is_active": True,
            "invitation_accepted": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "michael.chen@lincoln-academy.edu",
            "name": "Michael Chen",
            "institution_id": institution_ids[0],
            "bio": "Specializes in business English and conversational skills",
            "qualifications": "CELTA Certified, 8 years teaching experience",
            "assigned_learners": [],
            "is_active": True,
            "invitation_accepted": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "maria.lopez@gli.org",
            "name": "Maria Lopez",
            "institution_id": institution_ids[1],
            "bio": "Multilingual educator fluent in 5 languages",
            "qualifications": "Ph.D. in Applied Linguistics",
            "assigned_learners": [],
            "is_active": True,
            "invitation_accepted": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    result = await db.tutors.insert_many(tutors)
    tutor_ids = [str(id) for id in result.inserted_ids]
    print(f"✅ Created {len(tutor_ids)} tutors")

    # 3. Create mock invitations (some expired, some active)
    invitations = [
        {
            "email": "new.learner@example.com",
            "invitation_type": "learner",
            "institution_id": institution_ids[0],
            "invited_by": "admin_id_placeholder",
            "code": secrets.token_urlsafe(32),
            "assigned_tutor_id": tutor_ids[0],
            "is_accepted": False,
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "created_at": datetime.utcnow()
        },
        {
            "email": "pending.tutor@lincoln-academy.edu",
            "invitation_type": "tutor",
            "institution_id": institution_ids[0],
            "invited_by": "admin_id_placeholder",
            "code": secrets.token_urlsafe(32),
            "is_accepted": False,
            "expires_at": datetime.utcnow() + timedelta(days=5),
            "created_at": datetime.utcnow()
        },
        {
            "email": "expired.invitation@example.com",
            "invitation_type": "learner",
            "institution_id": institution_ids[1],
            "invited_by": "admin_id_placeholder",
            "code": secrets.token_urlsafe(32),
            "assigned_tutor_id": tutor_ids[2],
            "is_accepted": False,
            "expires_at": datetime.utcnow() - timedelta(days=1),  # Already expired
            "created_at": datetime.utcnow() - timedelta(days=8)
        }
    ]

    result = await db.invitations.insert_many(invitations)
    print(f"✅ Created {len(invitations)} invitations")

    # 4. Create mock institutional learners
    institutional_learners = [
        {
            "user_id": "mock_user_1",  # Would link to actual user in users collection
            "institution_id": institution_ids[0],
            "tutor_id": tutor_ids[0],
            "enrollment_method": "admin_invite",
            "consent_given": True,
            "consent_date": datetime.utcnow(),
            "consent_revoked": False,
            "enrolled_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "user_id": "mock_user_2",
            "institution_id": institution_ids[0],
            "tutor_id": tutor_ids[1],
            "enrollment_method": "self_signup",
            "consent_given": False,
            "consent_revoked": False,
            "enrolled_at": datetime.utcnow(),
            "is_active": True
        }
    ]

    result = await db.institutional_learners.insert_many(institutional_learners)
    learner_ids = [str(id) for id in result.inserted_ids]
    print(f"✅ Created {len(learner_ids)} institutional learners")

    # 5. Create mock consent records
    consent_records = [
        {
            "learner_id": learner_ids[0],
            "institution_id": institution_ids[0],
            "tutor_id": tutor_ids[0],
            "data_shared": ["assessment_results", "learning_plans", "practice_sessions"],
            "action": "granted",
            "action_date": datetime.utcnow(),
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        },
        {
            "learner_id": learner_ids[0],
            "institution_id": institution_ids[0],
            "tutor_id": tutor_ids[0],
            "data_shared": ["assessment_results"],
            "action": "revoked",
            "action_date": datetime.utcnow() - timedelta(days=1),
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    ]

    result = await db.consent_records.insert_many(consent_records)
    print(f"✅ Created {len(consent_records)} consent records")

    # 6. Print summary
    print("\n" + "="*60)
    print("📊 SEED DATA SUMMARY")
    print("="*60)
    print(f"Institutions: {len(institution_ids)}")
    print(f"Tutors: {len(tutor_ids)}")
    print(f"Invitations: {len(invitations)}")
    print(f"Institutional Learners: {len(learner_ids)}")
    print(f"Consent Records: {len(consent_records)}")
    print("\n🔑 Institution Codes:")
    for inst in institutions:
        print(f"  - {inst['name']}: {inst['institution_code']}")
    print("\n📧 Test Emails:")
    for tutor in tutors:
        print(f"  - {tutor['name']}: {tutor['email']}")
    print("\n✅ Seeding complete!")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
