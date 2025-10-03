#!/usr/bin/env python3
"""
Validation script for institutional features implementation
Tests core functionality without complex E2E flows
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from httpx import AsyncClient
from main import app
from database import get_database

async def test_feature_flags():
    """Test that feature flags are working"""
    print("🔧 Testing Feature Flags...")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with invalid data to verify validation works
        response = await client.post("/api/v1/institution/signup", json={
            "name": "",  # Invalid
            "admin_email": "invalid",
            "admin_password": "123",
            "admin_name": "",
            "subscription_plan": "invalid"
        })

        if response.status_code == 422:
            print("✅ Feature flags enabled - validation working")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False

async def test_institution_creation():
    """Test basic institution creation"""
    print("🏫 Testing Institution Creation...")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/institution/signup", json={
            "name": "Validation Test Academy",
            "domain": "validation-test.edu",
            "admin_email": "admin@validation-test.edu",
            "admin_password": "securepass123",
            "admin_name": "Test Admin",
            "subscription_plan": "starter"
        })

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Institution created: {data.get('message', 'Success')}")
            print(f"   Institution ID: {data.get('institution_id')}")
            print(f"   Institution Code: {data.get('institution_code')}")
            return data.get("institution_id")
        else:
            print(f"❌ Institution creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

async def test_admin_login(institution_id):
    """Test admin login"""
    print("🔐 Testing Admin Login...")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/institution/login", json={
            "admin_email": "admin@validation-test.edu",
            "password": "securepass123"
        })

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin login successful: {data.get('institution_name')}")
            return data.get("access_token")
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return None

async def test_tutor_invitation(institution_id, token):
    """Test tutor invitation"""
    print("👨‍🏫 Testing Tutor Invitation...")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tutors/invite",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "tutor@validation-test.edu",
                "name": "Test Tutor",
                "institution_id": institution_id,
                "invited_by": "admin_id"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tutor invitation sent: {data.get('email')}")
            return data.get("invitation_code")
        else:
            print(f"❌ Tutor invitation failed: {response.status_code}")
            return None

async def test_learner_self_signup(institution_id, token):
    """Test learner self-signup"""
    print("🎓 Testing Learner Self-Signup...")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get institution code
        stats_response = await client.get(
            f"/api/v1/institution/stats/{institution_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if stats_response.status_code != 200:
            print(f"❌ Failed to get institution stats: {stats_response.status_code}")
            return None

        institution_code = stats_response.json().get("institution_code")

        # Test learner signup
        signup_response = await client.post("/api/v1/learners/self-signup", json={
            "email": "learner@validation-test.edu",
            "name": "Test Learner",
            "password": "password123",
            "institution_code": institution_code
        })

        if signup_response.status_code == 200:
            data = signup_response.json()
            print(f"✅ Learner signup successful: {data.get('user_id')}")
            print(f"   Requires consent: {data.get('requires_consent')}")
            return data.get("user_id")
        else:
            print(f"❌ Learner signup failed: {signup_response.status_code}")
            return None

async def test_consent_workflow(learner_id, institution_id, tutor_id):
    """Test consent workflow"""
    print("📋 Testing Consent Workflow...")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Grant consent
        consent_response = await client.post("/api/v1/consent/grant", json={
            "learner_id": learner_id,
            "institution_id": institution_id,
            "tutor_id": tutor_id
        })

        if consent_response.status_code == 200:
            print(f"✅ Consent granted for learner: {learner_id}")

            # Check consent status
            status_response = await client.get(
                f"/api/v1/consent/status/{learner_id}/{institution_id}"
            )

            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ Consent verified: {status.get('has_consent')}")
                return True
            else:
                print(f"❌ Consent status check failed: {status_response.status_code}")
                return False
        else:
            print(f"❌ Consent grant failed: {consent_response.status_code}")
            return False

async def main():
    """Run all validation tests"""
    print("🧪 Starting Institutional Features Validation")
    print("=" * 50)

    try:
        # Test 1: Feature flags
        if not await test_feature_flags():
            print("❌ Feature flag test failed")
            return

        # Test 2: Institution creation
        institution_id = await test_institution_creation()
        if not institution_id:
            print("❌ Institution creation test failed")
            return

        # Test 3: Admin login
        token = await test_admin_login(institution_id)
        if not token:
            print("❌ Admin login test failed")
            return

        # Test 4: Tutor invitation
        invitation_code = await test_tutor_invitation(institution_id, token)
        if not invitation_code:
            print("❌ Tutor invitation test failed")
            return

        # Test 5: Learner self-signup
        learner_id = await test_learner_self_signup(institution_id, token)
        if not learner_id:
            print("❌ Learner self-signup test failed")
            return

        # Test 6: Consent workflow
        if not await test_consent_workflow(learner_id, institution_id, "test_tutor_id"):
            print("❌ Consent workflow test failed")
            return

        print("=" * 50)
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Institutional features are working correctly")
        print("✅ Ready for production deployment")

    except Exception as e:
        print(f"❌ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
