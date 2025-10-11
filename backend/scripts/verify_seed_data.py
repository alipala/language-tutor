#!/usr/bin/env python3
"""
Verify that seed data was created correctly
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "language_tutor")

async def verify_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("🔍 Verifying seed data...")

    # Check institutions
    institutions = await db.institutions.find().to_list(length=None)
    print(f"📚 Institutions: {len(institutions)}")
    for inst in institutions:
        print(f"  - {inst['name']} ({inst['institution_code']}) - {inst['subscription_plan']}")

    # Check tutors
    tutors = await db.tutors.find().to_list(length=None)
    print(f"\n👨‍🏫 Tutors: {len(tutors)}")
    for tutor in tutors:
        print(f"  - {tutor['name']} ({tutor['email']})")

    # Check invitations
    invitations = await db.invitations.find().to_list(length=None)
    print(f"\n📧 Invitations: {len(invitations)}")
    for invite in invitations:
        status = "✅ Active" if invite['expires_at'] > invite['created_at'] else "❌ Expired"
        print(f"  - {invite['email']} ({invite['invitation_type']}) - {status}")

    # Check institutional learners
    learners = await db.institutional_learners.find().to_list(length=None)
    print(f"\n🎓 Institutional Learners: {len(learners)}")
    for learner in learners:
        consent_status = "✅ Consented" if learner.get('consent_given') else "❌ No consent"
        print(f"  - {learner['user_id']} - {consent_status}")

    # Check consent records
    consents = await db.consent_records.find().to_list(length=None)
    print(f"\n📋 Consent Records: {len(consents)}")
    for consent in consents:
        print(f"  - {consent['action']} - {consent['data_shared']}")

    print("\n✅ Verification complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(verify_data())
