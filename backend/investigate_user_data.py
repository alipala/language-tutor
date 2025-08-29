#!/usr/bin/env python3
"""
Investigate the specific user data to understand the discrepancy
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

async def investigate_user():
    """Investigate the user data"""
    try:
        logger.info(f"🔍 Investigating user: {TARGET_USER}")
        
        # Get user data
        user = await database.users.find_one({"email": TARGET_USER})
        if not user:
            logger.error(f"❌ User not found: {TARGET_USER}")
            return
        
        logger.info(f"✅ User found with ID: {user['_id']}")
        
        # Print key fields
        key_fields = [
            'practice_minutes_used', 'practice_sessions_used', 'assessments_used',
            'current_period_start', 'current_period_end', 'subscription_plan',
            'subscription_status', 'subscription_expires_at', 'created_at', 'last_login'
        ]
        
        logger.info("📊 User data:")
        for field in key_fields:
            value = user.get(field, 'NOT SET')
            logger.info(f"   {field}: {value}")
        
        # Check for fix flags
        fix_fields = [
            'backfill_applied', 'backfill_date', 'backfill_details',
            'session_count_fix_applied', 'session_count_fix_date', 'session_count_fix_details',
            'duration_fix_applied', 'duration_fix_date', 'duration_fix_details'
        ]
        
        logger.info("\n🔧 Fix history:")
        for field in fix_fields:
            value = user.get(field, 'NOT SET')
            if value != 'NOT SET':
                logger.info(f"   {field}: {value}")
        
        # Count sessions in database
        user_id = str(user['_id'])
        
        # Count learning plans
        learning_count = await database.learning_plans.count_documents({"user_id": user_id})
        logger.info(f"\n📚 Learning plans: {learning_count}")
        
        # Show some learning plan data
        if learning_count > 0:
            async for plan in database.learning_plans.find({"user_id": user_id}).limit(3):
                sessions = plan.get('sessions', [])
                completed = sum(1 for s in sessions if s.get('completed', False))
                logger.info(f"   Plan created: {plan.get('created_at', 'unknown')}, sessions: {len(sessions)}, completed: {completed}")
        
        # Count conversation sessions
        conversation_count = await database.conversation_sessions.count_documents({"user_id": user_id})
        logger.info(f"\n💬 Conversation sessions: {conversation_count}")
        
        # Show some conversation data
        if conversation_count > 0:
            async for session in database.conversation_sessions.find({"user_id": user_id}).limit(3):
                duration = session.get('duration', 0)
                created = session.get('created_at', 'unknown')
                logger.info(f"   Session created: {created}, duration: {duration}s ({duration/60:.2f}min)")
        
        logger.info("\n🎯 Investigation complete!")
        
    except Exception as e:
        logger.error(f"❌ Error investigating user: {e}")

if __name__ == "__main__":
    asyncio.run(investigate_user())
