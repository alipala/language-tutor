"""
Database setup for institutional collections
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING

async def setup_institutional_collections(db: AsyncIOMotorDatabase):
    """
    Create collections and indexes for institutional features
    """

    # 1. Institutions collection
    institutions = db.institutions
    await institutions.create_indexes([
        IndexModel([("institution_code", ASCENDING)], unique=True),
        IndexModel([("admin_email", ASCENDING)]),
        IndexModel([("is_active", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)])
    ])

    # 2. Tutors collection
    tutors = db.tutors
    await tutors.create_indexes([
        IndexModel([("email", ASCENDING)], unique=True),
        IndexModel([("institution_id", ASCENDING)]),
        IndexModel([("is_active", ASCENDING)]),
        IndexModel([("invitation_accepted", ASCENDING)])
    ])

    # 3. Institutional learners collection
    institutional_learners = db.institutional_learners
    await institutional_learners.create_indexes([
        IndexModel([("user_id", ASCENDING), ("institution_id", ASCENDING)], unique=True),
        IndexModel([("tutor_id", ASCENDING)]),
        IndexModel([("consent_given", ASCENDING)]),
        IndexModel([("is_active", ASCENDING)])
    ])

    # 4. Invitations collection (with TTL for auto-expiry)
    invitations = db.invitations
    await invitations.create_indexes([
        IndexModel([("code", ASCENDING)], unique=True),
        IndexModel([("email", ASCENDING)]),
        IndexModel([("institution_id", ASCENDING)]),
        IndexModel([("is_accepted", ASCENDING)]),
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0)  # TTL index
    ])

    # 5. Consent records collection (audit trail)
    consent_records = db.consent_records
    await consent_records.create_indexes([
        IndexModel([("learner_id", ASCENDING)]),
        IndexModel([("institution_id", ASCENDING)]),
        IndexModel([("action", ASCENDING)]),
        IndexModel([("action_date", DESCENDING)])
    ])

    print("✅ Institutional collections and indexes created successfully")
