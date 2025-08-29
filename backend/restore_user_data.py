#!/usr/bin/env python3
"""
Restore the correct user data based on the provided user record
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any
import logging

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TARGET_USER = "alipala.ist@gmail.com"

# Correct data from the user record provided in the task
CORRECT_DATA = {
    "practice_minutes_used": 58.08603333333333,
    "practice_sessions_used": 14,
    "assessments_used": 1  # Keep current value
}

async def restore_user_data():
    """Restore the correct user data"""
    try:
        logger.info(f"🔧 Restoring correct data for user: {TARGET_USER}")
        
        # Get current user data
        user = await database.users.find_one({"email": TARGET_USER})
        if not user:
            logger.error(f"❌ User not found: {TARGET_USER}")
            return
        
        # Show current values
        current_minutes = user.get('practice_minutes_used', 0)
        current_sessions = user.get('practice_sessions_used', 0)
        current_assessments = user.get('assessments_used', 0)
        
        logger.info(f"📊 Current values:")
        logger.info(f"   Minutes: {current_minutes}")
        logger.info(f"   Sessions: {current_sessions}")
        logger.info(f"   Assessments: {current_assessments}")
        
        logger.info(f"✅ Correct values (from provided user record):")
        logger.info(f"   Minutes: {CORRECT_DATA['practice_minutes_used']}")
        logger.info(f"   Sessions: {CORRECT_DATA['practice_sessions_used']}")
        logger.info(f"   Assessments: {CORRECT_DATA['assessments_used']}")
        
        # Calculate differences
        minutes_diff = CORRECT_DATA['practice_minutes_used'] - current_minutes
        sessions_diff = CORRECT_DATA['practice_sessions_used'] - current_sessions
        
        logger.info(f"🔄 Changes needed:")
        logger.info(f"   Minutes: {current_minutes} → {CORRECT_DATA['practice_minutes_used']} ({minutes_diff:+.2f})")
        logger.info(f"   Sessions: {current_sessions} → {CORRECT_DATA['practice_sessions_used']} ({sessions_diff:+d})")
        
        # Apply the restoration
        update_result = await database.users.update_one(
            {"email": TARGET_USER},
            {
                "$set": {
                    "practice_minutes_used": CORRECT_DATA['practice_minutes_used'],
                    "practice_sessions_used": CORRECT_DATA['practice_sessions_used'],
                    "assessments_used": CORRECT_DATA['assessments_used'],
                    "data_restored": True,
                    "data_restore_date": datetime.now(timezone.utc).isoformat(),
                    "data_restore_details": {
                        "reason": "Restoring correct data from provided user record",
                        "old_minutes": current_minutes,
                        "new_minutes": CORRECT_DATA['practice_minutes_used'],
                        "old_sessions": current_sessions,
                        "new_sessions": CORRECT_DATA['practice_sessions_used'],
                        "minutes_diff": minutes_diff,
                        "sessions_diff": sessions_diff,
                        "source": "User record provided in task description"
                    }
                }
            }
        )
        
        if update_result.modified_count > 0:
            logger.info(f"✅ Successfully restored data for user {TARGET_USER}")
            
            # Verify the update
            updated_user = await database.users.find_one({"email": TARGET_USER})
            logger.info(f"🔍 Verification:")
            logger.info(f"   Minutes: {updated_user.get('practice_minutes_used')}")
            logger.info(f"   Sessions: {updated_user.get('practice_sessions_used')}")
            logger.info(f"   Assessments: {updated_user.get('assessments_used')}")
            
        else:
            logger.error(f"❌ Failed to update user {TARGET_USER}")
        
        logger.info("\n🎉 Data restoration completed!")
        
    except Exception as e:
        logger.error(f"❌ Error restoring user data: {e}")

if __name__ == "__main__":
    asyncio.run(restore_user_data())
