"""
Script to update passwords for B2B test users
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
MONGODB_URL = "mongodb://mongo:rdJVDcRfesCmdVXgYuJPNJlDzkFzxIoT@crossover.proxy.rlwy.net:44437/language_tutor?authSource=admin"
DATABASE_NAME = "language_tutor"

async def update_passwords():
    """Update passwords for B2B test users"""
    
    # Connect to database
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        # Update tutor password
        tutor_email = "sarah.johnson@lincoln.edu"
        tutor_password = "TestTutor2025!"
        tutor_hashed = pwd_context.hash(tutor_password)
        
        print(f"Updating password for tutor: {tutor_email}")
        tutor_result = await db.tutors.update_one(
            {"email": tutor_email},
            {"$set": {"password": tutor_hashed}}
        )
        
        if tutor_result.matched_count > 0:
            print(f"✅ Tutor password updated successfully")
            print(f"   Email: {tutor_email}")
            print(f"   Password: {tutor_password}")
        else:
            print(f"❌ Tutor not found: {tutor_email}")
        
        print()
        
        # Update institution admin password
        institution_email = "l@edu.tr"
        institution_password = "abc"
        institution_hashed = pwd_context.hash(institution_password)
        
        print(f"Updating password for institution admin: {institution_email}")
        institution_result = await db.institutions.update_one(
            {"admin_email": institution_email},
            {"$set": {"admin_password": institution_hashed}}
        )
        
        if institution_result.matched_count > 0:
            print(f"✅ Institution admin password updated successfully")
            print(f"   Email: {institution_email}")
            print(f"   Password: {institution_password}")
        else:
            print(f"❌ Institution not found: {institution_email}")
            
    except Exception as e:
        print(f"❌ Error updating passwords: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Updating B2B Test User Passwords")
    print("=" * 60)
    print()
    
    asyncio.run(update_passwords())
    
    print()
    print("=" * 60)
    print("Password Update Complete")
    print("=" * 60)
