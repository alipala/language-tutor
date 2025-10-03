import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_institutions():
    load_dotenv()
    
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL")
    if not mongo_uri:
        print("❌ No MongoDB URI found in environment")
        return
    
    print(f"🔌 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["mytaco_prod"]
    
    # Check institutions collection
    institutions_collection = db["institutions"]
    
    print("\n" + "="*80)
    print("📊 INSTITUTIONS IN PRODUCTION DATABASE")
    print("="*80)
    
    institutions = await institutions_collection.find({}).to_list(None)
    
    if not institutions:
        print("\n⚠️  No institutions found in database")
    else:
        print(f"\n✅ Found {len(institutions)} institution(s):\n")
        
        for i, inst in enumerate(institutions, 1):
            print(f"{i}. Institution:")
            print(f"   ID: {inst.get('_id')}")
            print(f"   Name: {inst.get('name')}")
            print(f"   Code: {inst.get('institution_code')}")
            print(f"   Admin Email: {inst.get('admin_email')}")
            print(f"   Domain: {inst.get('domain', 'N/A')}")
            print(f"   Plan: {inst.get('subscription_plan')}")
            print(f"   Created: {inst.get('created_at')}")
            print(f"   Max Tutors: {inst.get('max_tutors')}")
            print(f"   Max Learners: {inst.get('max_learners')}")
            print(f"   Total Tutors: {inst.get('total_tutors', 0)}")
            print(f"   Total Learners: {inst.get('total_learners', 0)}")
            print()
    
    # Check related collections
    print(f"👥 Tutors: {await db.tutors.count_documents({})}")
    print(f"🎓 Institutional Learners: {await db.institutional_learners.count_documents({})}")
    print(f"✉️  Invitations: {await db.invitations.count_documents({})}")
    print(f"📝 Consent Records: {await db.consent_records.count_documents({})}")
    
    print("\n" + "="*80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_institutions())
