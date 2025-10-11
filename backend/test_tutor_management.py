#!/usr/bin/env python3
"""
Test script for tutor management functionality
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tutor.service import TutorService
from app.tutor.schemas import TutorInviteRequest, TutorAcceptInviteRequest
from database import init_db, database
import secrets

async def test_tutor_management():
    """Test tutor invitation and management functionality"""
    print("🎓 Testing Tutor Management System")
    print("=" * 50)

    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")

        # Create tutor service
        service = TutorService(database)
        print("✅ Tutor service created")

        # Test 1: Invite a tutor
        print("\n📧 Test 1: Inviting tutor")
        invite_data = TutorInviteRequest(
            email="test-tutor@university.edu",
            name="Dr. Sarah Johnson",
            institution_id="68dfadddd800da2503cbac09",  # Use existing Lincoln Academy institution
            invited_by="admin123"
        )

        try:
            result = await service.invite_tutor(
                email=invite_data.email,
                name=invite_data.name,
                institution_id=invite_data.institution_id,
                invited_by=invite_data.invited_by
            )
            print("✅ Tutor invitation created successfully")
            print(f"   Invitation ID: {result['invitation_id']}")
            print(f"   Invitation Code: {result['invitation_code']}")
            print(f"   Email: {result['email']}")
            invitation_code = result['invitation_code']
        except Exception as e:
            print(f"❌ Tutor invitation failed: {str(e)}")
            return

        # Test 2: Accept invitation
        print("\n✅ Test 2: Accepting invitation")
        accept_data = TutorAcceptInviteRequest(
            invitation_code=invitation_code,
            bio="Experienced language instructor with 10+ years teaching experience",
            qualifications="PhD in Linguistics, TESOL certified"
        )

        try:
            result = await service.accept_invitation(
                invitation_code=accept_data.invitation_code,
                bio=accept_data.bio,
                qualifications=accept_data.qualifications
            )
            print("✅ Invitation accepted successfully")
            print(f"   Tutor ID: {result['tutor_id']}")
            tutor_id = result['tutor_id']
        except Exception as e:
            print(f"❌ Invitation acceptance failed: {str(e)}")
            return

        # Test 3: Get institution tutors
        print("\n📋 Test 3: Getting institution tutors")
        try:
            tutors = await service.get_institution_tutors(invite_data.institution_id)
            print("✅ Institution tutors retrieved successfully")
            print(f"   Number of tutors: {len(tutors)}")
            for tutor in tutors:
                print(f"   - {tutor['name']} ({tutor['email']}) - Active: {tutor['is_active']}, Accepted: {tutor['invitation_accepted']}")
        except Exception as e:
            print(f"❌ Getting institution tutors failed: {str(e)}")
            return

        # Test 4: Try to invite same tutor again (should fail)
        print("\n🚫 Test 4: Testing duplicate prevention")
        try:
            result = await service.invite_tutor(
                email=invite_data.email,
                name=invite_data.name,
                institution_id=invite_data.institution_id,
                invited_by=invite_data.invited_by
            )
            print("❌ Duplicate invitation should have failed but didn't")
            return
        except ValueError as e:
            if "already exists" in str(e):
                print("✅ Duplicate prevention working correctly")
            else:
                print(f"❌ Unexpected error: {str(e)}")
                return
        except Exception as e:
            print(f"❌ Unexpected error type: {str(e)}")
            return

        print("\n🎉 All tutor management tests passed successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tutor_management())
