#!/usr/bin/env python3
"""
FIX FOR CRITICAL DOUBLE COUNTING BUG
Problem: Sessions are being counted twice (1 session = 2 sessions, 5 min = 10 min)
Root Cause: Multiple endpoints calling track_speaking_time for the same session
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fix_double_counting():
    """Fix the double counting issue for user 688921c268819565ef1ce3dc"""
    
    # Load PRODUCTION .env file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
    logger.info(f"✅ Loaded PRODUCTION .env")
    
    # Get MongoDB URL
    mongodb_url = os.getenv('MONGODB_URL')
    
    logger.info("=" * 80)
    logger.info("🔧 FIXING DOUBLE COUNTING BUG")
    logger.info("=" * 80)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        db = client.language_tutor
        
        # User to fix
        user_id = "688921c268819565ef1ce3dc"
        user_oid = ObjectId(user_id)
        
        # 1. Get current user state
        logger.info("\n1️⃣ CURRENT USER STATE:")
        logger.info("-" * 40)
        
        user = await db.users.find_one({"_id": user_oid})
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            return
            
        current_minutes = user.get('practice_minutes_used', 0)
        current_sessions = user.get('practice_sessions_used', 0)
        
        logger.info(f"   Email: {user.get('email', 'N/A')}")
        logger.info(f"   Current minutes: {current_minutes}")
        logger.info(f"   Current sessions: {current_sessions}")
        
        # 2. Get actual sessions from database
        logger.info("\n2️⃣ ACTUAL SESSIONS IN DATABASE:")
        logger.info("-" * 40)
        
        period_start = user.get('current_period_start')
        sessions_query = {"user_id": user_id}
        if period_start:
            sessions_query["created_at"] = {"$gte": period_start}
            
        conv_sessions = await db.conversation_sessions.find(sessions_query).to_list(None)
        
        actual_sessions = len(conv_sessions)
        actual_minutes = sum(s.get('duration_minutes', 0) for s in conv_sessions)
        
        logger.info(f"   Actual sessions: {actual_sessions}")
        logger.info(f"   Actual minutes: {actual_minutes}")
        
        # 3. Calculate the correct values
        logger.info("\n3️⃣ CALCULATING CORRECT VALUES:")
        logger.info("-" * 40)
        
        # The correct values should match what's actually in the database
        correct_minutes = actual_minutes
        correct_sessions = actual_sessions
        
        logger.info(f"   Correct minutes: {correct_minutes}")
        logger.info(f"   Correct sessions: {correct_sessions}")
        
        # 4. Fix the user record
        logger.info("\n4️⃣ FIXING USER RECORD:")
        logger.info("-" * 40)
        
        logger.info(f"   Minutes: {current_minutes} → {correct_minutes}")
        logger.info(f"   Sessions: {current_sessions} → {correct_sessions}")
        
        # Update the user record with correct values
        result = await db.users.update_one(
            {"_id": user_oid},
            {
                "$set": {
                    "practice_minutes_used": correct_minutes,
                    "practice_sessions_used": correct_sessions
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info("\n✅ USER RECORD FIXED!")
        else:
            logger.info("\n⚠️ No changes made (values might already be correct)")
        
        # 5. Verify the fix
        logger.info("\n5️⃣ VERIFYING FIX:")
        logger.info("-" * 40)
        
        updated_user = await db.users.find_one({"_id": user_oid})
        new_minutes = updated_user.get('practice_minutes_used', 0)
        new_sessions = updated_user.get('practice_sessions_used', 0)
        
        logger.info(f"   New minutes: {new_minutes}")
        logger.info(f"   New sessions: {new_sessions}")
        logger.info(f"   Minutes remaining: {150 - new_minutes}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 FIX SUMMARY:")
        logger.info("=" * 80)
        logger.info(f"   User: {user.get('email')}")
        logger.info(f"   Minutes fixed: {current_minutes} → {correct_minutes}")
        logger.info(f"   Sessions fixed: {current_sessions} → {correct_sessions}")
        logger.info(f"   Minutes remaining: {150 - correct_minutes} / 150")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

async def main():
    """Main function"""
    await fix_double_counting()

if __name__ == "__main__":
    asyncio.run(main())
