#!/usr/bin/env python3
"""
Demo script to test consent functionality
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env
from app.consent.service import ConsentService
from database import database

async def test_consent_flow():
    """Test the consent flow with seed data"""
    print("🧪 Testing Consent Flow...")

    # Initialize service
    service = ConsentService(database)

    # Test data from seed script - using actual ObjectIds
    learner_id = "mock_user_1"
    institution_id = "68dfadddd800da2503cbac09"  # Lincoln Academy
    tutor_id = "68dfadded800da2503cbac0c"  # Sarah Johnson

    print(f"📋 Testing with learner: {learner_id}, institution: {institution_id}")

    # 1. Check initial consent status
    print("\n1️⃣ Checking initial consent status...")
    status = await service.get_consent_status(learner_id, institution_id)
    if status:
        print(f"   Has consent: {status['has_consent']}")
        print(f"   Institution: {status['institution_name']}")
        print(f"   Tutor: {status['tutor_name']}")
    else:
        print("   ❌ No enrollment found")

    # 2. Grant consent
    print("\n2️⃣ Granting consent...")
    try:
        result = await service.grant_consent(
            learner_id=learner_id,
            institution_id=institution_id,
            tutor_id=tutor_id,
            data_to_share=["assessment_results", "learning_plans", "practice_sessions", "progress_metrics"],
            ip_address="192.168.1.100",
            user_agent="TestScript/1.0"
        )
        print(f"   ✅ Consent granted: {result['message']}")
        print(f"   Record ID: {result['consent_record_id']}")
    except Exception as e:
        print(f"   ❌ Failed to grant consent: {e}")

    # 3. Check consent status after granting
    print("\n3️⃣ Checking consent status after granting...")
    status = await service.get_consent_status(learner_id, institution_id)
    if status:
        print(f"   Has consent: {status['has_consent']}")
        print(f"   Consent date: {status['consent_given_date']}")
        print(f"   Data shared: {status['data_shared']}")

    # 4. Check consent via check_consent method
    print("\n4️⃣ Checking consent via check_consent method...")
    has_consent = await service.check_consent(learner_id, institution_id)
    print(f"   Has consent: {has_consent}")

    # 5. Revoke consent
    print("\n5️⃣ Revoking consent...")
    try:
        result = await service.revoke_consent(learner_id, institution_id)
        print(f"   ✅ Consent revoked: {result['message']}")
        print(f"   Record ID: {result['consent_record_id']}")
    except Exception as e:
        print(f"   ❌ Failed to revoke consent: {e}")

    # 6. Check final consent status
    print("\n6️⃣ Checking final consent status...")
    status = await service.get_consent_status(learner_id, institution_id)
    if status:
        print(f"   Has consent: {status['has_consent']}")
        print(f"   Revoked: {status['consent_revoked']}")

    print("\n🎉 Consent flow test completed!")

if __name__ == "__main__":
    asyncio.run(test_consent_flow())
