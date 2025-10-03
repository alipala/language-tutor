#!/usr/bin/env python3
"""
Test script for learner enrollment functionality
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.learner.service import LearnerService
from app.learner.schemas import LearnerEnrollRequest, LearnerSelfSignupRequest
from database import init_db, database
import secrets

async def test_learner_enrollment():
    """Test learner enrollment and management functionality"""
    print("🎓 Testing Learner Enrollment System")
    print("=" * 50)

    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")

        # Create learner service
        service = LearnerService(database)
        print("✅ Learner service created")

        # Test 1: Admin enrolls a learner
        print("\n👨‍🏫 Test 1: Admin enrollment")
        enroll_data = LearnerEnrollRequest(
            email="student@university.edu",
            name="Alice Johnson",
            institution_id="68dfadddd800da2503cbac09",  # Lincoln Academy
            tutor_id="68dfc03879728f91f2b421fc",  # Test tutor we created earlier
            enrolled_by="admin123"
        )

        try:
            result = await service.enroll_learner_by_admin(
                email=enroll_data.email,
                name=enroll_data.name,
                institution_id=enroll_data.institution_id,
                tutor_id=enroll_data.tutor_id,
                enrolled_by=enroll_data.enrolled_by
            )
            print("✅ Admin enrollment created successfully")
            print(f"   Invitation ID: {result['invitation_id']}")
            print(f"   Message: {result['message']}")
        except Exception as e:
            print(f"❌ Admin enrollment failed: {str(e)}")
            return

        # Test 2: Self-signup with institution code
        print("\n🎓 Test 2: Self-signup with institution code")
        signup_data = LearnerSelfSignupRequest(
            email="bob.smith@university.edu",
            name="Bob Smith",
            password="securepassword123",
            institution_code="LINCOLN2025"  # Lincoln Academy code
        )

        try:
            result = await service.self_signup_with_code(
                email=signup_data.email,
                name=signup_data.name,
                password=signup_data.password,
                institution_code=signup_data.institution_code
            )
            print("✅ Self-signup completed successfully")
            print(f"   User ID: {result['user_id']}")
            print(f"   Institution ID: {result['institution_id']}")
            print(f"   Tutor ID: {result['tutor_id']}")
            print(f"   Requires Consent: {result['requires_consent']}")
            print(f"   Message: {result['message']}")
            user_id = result['user_id']
        except Exception as e:
            print(f"❌ Self-signup failed: {str(e)}")
            return

        # Test 3: Get tutor learners
        print("\n📋 Test 3: Getting tutor learners")
        try:
            learners = await service.get_tutor_learners(enroll_data.tutor_id)
            print("✅ Tutor learners retrieved successfully")
            print(f"   Number of learners: {len(learners)}")
            for learner in learners:
                print(f"   - {learner['name']} ({learner['email']}) - Consent: {learner['consent_given']}")
        except Exception as e:
            print(f"❌ Getting tutor learners failed: {str(e)}")
            return

        # Test 4: Get institution learners
        print("\n🏫 Test 4: Getting institution learners")
        try:
            learners = await service.get_institution_learners(enroll_data.institution_id)
            print("✅ Institution learners retrieved successfully")
            print(f"   Number of learners: {len(learners)}")
            for learner in learners:
                print(f"   - {learner['name']} ({learner['email']}) - Tutor: {learner['tutor_name']}, Consent: {learner['consent_given']}")
        except Exception as e:
            print(f"❌ Getting institution learners failed: {str(e)}")
            return

        # Test 5: Try to signup same user again (should fail)
        print("\n🚫 Test 5: Testing duplicate enrollment prevention")
        try:
            result = await service.self_signup_with_code(
                email=signup_data.email,
                name=signup_data.name,
                password=signup_data.password,
                institution_code=signup_data.institution_code
            )
            print("❌ Duplicate enrollment should have failed but didn't")
            return
        except ValueError as e:
            if "already enrolled" in str(e).lower():
                print("✅ Duplicate enrollment prevention working correctly")
            else:
                print(f"❌ Unexpected error: {str(e)}")
                return
        except Exception as e:
            print(f"❌ Unexpected error type: {str(e)}")
            return

        # Test 6: Try invalid institution code
        print("\n🚫 Test 6: Testing invalid institution code")
        try:
            result = await service.self_signup_with_code(
                email="another-student@university.edu",
                name="Charlie Brown",
                password="password123",
                institution_code="INVALID123"
            )
            print("❌ Invalid code should have failed but didn't")
            return
        except ValueError as e:
            if "invalid institution code" in str(e).lower():
                print("✅ Invalid code validation working correctly")
            else:
                print(f"❌ Unexpected error: {str(e)}")
                return
        except Exception as e:
            print(f"❌ Unexpected error type: {str(e)}")
            return

        print("\n🎉 All learner enrollment tests passed successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_learner_enrollment())
