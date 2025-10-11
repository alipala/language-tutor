#!/usr/bin/env python3
"""
Test institution signup API
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env
from app.institution.service import InstitutionService
from database import database

async def test_institution_signup():
    """Test institution signup functionality"""
    print("🏫 Testing Institution Signup...")

    # Initialize service
    service = InstitutionService(database)

    # Test data with unique email to avoid conflicts
    import time
    unique_id = str(int(time.time()))  # Use timestamp for uniqueness

    signup_data = {
        "name": "Test Academy",
        "domain": "test-academy.edu",
        "admin_email": f"admin{unique_id}@test-academy.edu",
        "admin_password": "abc",  # Very short password for bcrypt compatibility
        "admin_name": "John Admin",
        "subscription_plan": "starter"
    }

    print(f"📝 Attempting to create institution: {signup_data['name']}")

    try:
        # Create institution
        result = await service.create_institution(**signup_data)
        print("✅ Institution created successfully!")
        print(f"   Institution ID: {result['institution_id']}")
        print(f"   Institution Code: {result['institution_code']}")
        print(f"   Admin Email: {result['admin_email']}")
        print(f"   Plan: {result['subscription_plan']}")

        # Test authentication
        print("\n🔐 Testing admin authentication...")
        auth_result = await service.authenticate_admin(
            admin_email=signup_data["admin_email"],
            password=signup_data["admin_password"]
        )

        if auth_result:
            print("✅ Admin authentication successful!")
            print(f"   Institution: {auth_result['institution_name']}")
            print(f"   Role: admin")
        else:
            print("❌ Admin authentication failed!")

        # Test institution stats
        print("\n📊 Testing institution stats...")
        stats = await service.get_institution_stats(result['institution_id'])
        print("✅ Institution stats retrieved!")
        print(f"   Tutors: {stats['total_tutors']}/{stats['max_tutors']}")
        print(f"   Learners: {stats['total_learners']}/{stats['max_learners']}")
        print(f"   Plan: {stats['subscription_plan']}")

        print("\n🎉 Institution signup test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_institution_signup())
