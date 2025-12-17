#!/usr/bin/env python3
"""
Quick MongoDB Collections Verification Script
==============================================

Verifies the structure and purpose of reference_challenges vs challenge_pool
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

MONGODB_URL = os.getenv('MONGODB_URL')
DATABASE_NAME = "language_tutor"

def verify_collections():
    """Verify and explain the two challenge collections"""

    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print("=" * 80)
    print("MONGODB COLLECTIONS VERIFICATION")
    print("=" * 80)
    print()

    # ========================================================================
    # 1. REFERENCE CHALLENGES
    # ========================================================================
    print("1️⃣  REFERENCE_CHALLENGES Collection")
    print("-" * 80)

    ref_count = db.reference_challenges.count_documents({})
    print(f"📊 Total documents: {ref_count:,}")
    print()

    # Sample document
    sample_ref = db.reference_challenges.find_one()
    if sample_ref:
        print("📝 Sample document structure:")
        print(f"   _id: {sample_ref.get('_id')}")
        print(f"   language: {sample_ref.get('language')}")
        print(f"   cefr_level: {sample_ref.get('cefr_level')}")
        print(f"   challenge_type: {sample_ref.get('challenge_type')}")
        print(f"   user_id: {sample_ref.get('user_id', '❌ NOT PRESENT (correct!)')}")
        print(f"   status: {sample_ref.get('status', '❌ NOT PRESENT (correct!)')}")
        print()

    # Language distribution
    print("🌍 Language distribution:")
    lang_pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    lang_dist = list(db.reference_challenges.aggregate(lang_pipeline))
    for lang in lang_dist:
        print(f"   - {lang['_id']}: {lang['count']} challenges")
    print()

    # Challenge type distribution
    print("🎯 Challenge type distribution:")
    type_pipeline = [
        {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    type_dist = list(db.reference_challenges.aggregate(type_pipeline))
    for ctype in type_dist:
        print(f"   - {ctype['_id']}: {ctype['count']} challenges")
    print()

    # CEFR level distribution
    print("📚 CEFR level distribution:")
    level_pipeline = [
        {"$group": {"_id": "$cefr_level", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    level_dist = list(db.reference_challenges.aggregate(level_pipeline))
    for level in level_dist:
        print(f"   - {level['_id']}: {level['count']} challenges")
    print()

    print("✅ PURPOSE: Template/seed challenges")
    print("✅ USED FOR: Copying to user pools (not direct use)")
    print("✅ GENERATED: Phase 1.5 (one-time generation)")
    print()

    # ========================================================================
    # 2. CHALLENGE POOL
    # ========================================================================
    print()
    print("2️⃣  CHALLENGE_POOL Collection")
    print("-" * 80)

    pool_count = db.challenge_pool.count_documents({})
    print(f"📊 Total documents: {pool_count:,}")
    print()

    # Sample document
    sample_pool = db.challenge_pool.find_one()
    if sample_pool:
        print("📝 Sample document structure:")
        print(f"   _id: {sample_pool.get('_id')}")
        print(f"   user_id: {sample_pool.get('user_id')} ✅ (has user_id!)")
        print(f"   language: {sample_pool.get('language')}")
        print(f"   cefr_level: {sample_pool.get('cefr_level')}")
        print(f"   challenge_type: {sample_pool.get('challenge_type')}")
        print(f"   status: {sample_pool.get('status')} ✅ (has status!)")
        print(f"   created_at: {sample_pool.get('created_at')}")
        print()

    # User distribution
    print("👥 User distribution:")
    user_pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    user_dist = list(db.challenge_pool.aggregate(user_pipeline))
    for i, user in enumerate(user_dist, 1):
        user_id_short = str(user['_id'])[:12] + "..."
        print(f"   {i}. User {user_id_short}: {user['count']} challenges")
    print()

    # Status distribution
    print("📊 Status distribution:")
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    status_dist = list(db.challenge_pool.aggregate(status_pipeline))
    for status in status_dist:
        print(f"   - {status['_id']}: {status['count']} challenges")
    print()

    # Language distribution
    print("🌍 Language distribution:")
    pool_lang_pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    pool_lang_dist = list(db.challenge_pool.aggregate(pool_lang_pipeline))
    for lang in pool_lang_dist:
        print(f"   - {lang['_id']}: {lang['count']} challenges")
    print()

    print("✅ PURPOSE: User-specific challenges")
    print("✅ USED FOR: Actual challenges in Explore tab")
    print("✅ GENERATED: Copied from reference OR AI-generated")
    print()

    # ========================================================================
    # 3. KEY DIFFERENCES
    # ========================================================================
    print()
    print("3️⃣  KEY DIFFERENCES")
    print("-" * 80)
    print()
    print("┌─────────────────────────┬──────────────────────┬──────────────────────┐")
    print("│ Feature                 │ reference_challenges │ challenge_pool       │")
    print("├─────────────────────────┼──────────────────────┼──────────────────────┤")
    print(f"│ Total Count             │ {ref_count:,} challenges     │ {pool_count:,} challenges      │")
    print("│ Has user_id?            │ ❌ NO                 │ ✅ YES                │")
    print("│ Has status field?       │ ❌ NO                 │ ✅ YES                │")
    print("│ Purpose                 │ Template library     │ User inventory       │")
    print("│ Direct usage?           │ ❌ NO (copy first)    │ ✅ YES                │")
    print("│ Generated when?         │ Phase 1.5 (once)     │ Weekly cron + demand │")
    print("└─────────────────────────┴──────────────────────┴──────────────────────┘")
    print()

    # ========================================================================
    # 4. HOW THEY WORK TOGETHER
    # ========================================================================
    print()
    print("4️⃣  HOW THEY WORK TOGETHER")
    print("-" * 80)
    print()
    print("📖 WORKFLOW:")
    print()
    print("   Step 1: reference_challenges created (Phase 1.5)")
    print("   ↓")
    print("   Step 2: User requests challenges (Explore tab)")
    print("   ↓")
    print("   Step 3: Backend checks challenge_pool for user")
    print("   ↓")
    print("   Step 4a: If pool empty → Copy from reference_challenges")
    print("   Step 4b: OR generate new AI challenges")
    print("   ↓")
    print("   Step 5: Insert into challenge_pool with user_id")
    print("   ↓")
    print("   Step 6: User gets challenges from challenge_pool")
    print()

    # ========================================================================
    # 5. VERIFICATION CHECKS
    # ========================================================================
    print()
    print("5️⃣  VERIFICATION CHECKS")
    print("-" * 80)
    print()

    # Check 1: Reference challenges should have NO user_id
    ref_with_user = db.reference_challenges.count_documents({"user_id": {"$exists": True}})
    if ref_with_user == 0:
        print("✅ Check 1: reference_challenges has NO user_id (correct)")
    else:
        print(f"⚠️  Check 1: {ref_with_user} reference_challenges have user_id (unexpected!)")

    # Check 2: Challenge pool should have user_id
    pool_with_user = db.challenge_pool.count_documents({"user_id": {"$exists": True}})
    pool_without_user = db.challenge_pool.count_documents({"user_id": {"$exists": False}})
    if pool_without_user == 0:
        print(f"✅ Check 2: All {pool_with_user} challenge_pool items have user_id (correct)")
    else:
        print(f"⚠️  Check 2: {pool_without_user} challenge_pool items missing user_id!")

    # Check 3: Reference challenges should have language field
    ref_with_lang = db.reference_challenges.count_documents({"language": {"$exists": True}})
    if ref_with_lang == ref_count:
        print(f"✅ Check 3: All {ref_count} reference_challenges have language field")
    else:
        print(f"⚠️  Check 3: {ref_count - ref_with_lang} reference_challenges missing language!")

    # Check 4: Challenge pool should have language field
    pool_with_lang = db.challenge_pool.count_documents({"language": {"$exists": True}})
    if pool_with_lang == pool_count:
        print(f"✅ Check 4: All {pool_count} challenge_pool items have language field")
    else:
        print(f"⚠️  Check 4: {pool_count - pool_with_lang} challenge_pool items missing language!")

    # Check 5: Challenge pool should have status field
    pool_with_status = db.challenge_pool.count_documents({"status": {"$exists": True}})
    if pool_with_status == pool_count:
        print(f"✅ Check 5: All {pool_count} challenge_pool items have status field")
    else:
        print(f"⚠️  Check 5: {pool_count - pool_with_status} challenge_pool items missing status!")

    print()
    print("=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

    client.close()


if __name__ == "__main__":
    try:
        verify_collections()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
