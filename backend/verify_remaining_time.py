#!/usr/bin/env python3
"""
Verify that remaining time calculations are working correctly
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
from subscription_service import SubscriptionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TARGET_USER = "alipala.ist@gmail.com"

async def verify_remaining_time():
    """Verify remaining time calculations"""
    try:
        logger.info(f"🔍 Verifying remaining time for user: {TARGET_USER}")
        
        # Get user data
        user = await database.users.find_one({"email": TARGET_USER})
        if not user:
            logger.error(f"❌ User not found: {TARGET_USER}")
            return
        
        user_id = str(user['_id'])
        
        # Show current stored values
        current_minutes = user.get('practice_minutes_used', 0)
        current_sessions = user.get('practice_sessions_used', 0)
        subscription_plan = user.get('subscription_plan', 'unknown')
        
        logger.info(f"📊 Current user data:")
        logger.info(f"   Minutes used: {current_minutes}")
        logger.info(f"   Sessions used: {current_sessions}")
        logger.info(f"   Subscription plan: {subscription_plan}")
        logger.info(f"   Period: {user.get('current_period_start')} to {user.get('current_period_end')}")
        
        # Get subscription status using SubscriptionService
        logger.info(f"\n🔄 Getting subscription status...")
        subscription_status = await SubscriptionService.get_user_subscription_status(user_id)
        
        logger.info(f"✅ Subscription status:")
        logger.info(f"   Status: {subscription_status.status}")
        logger.info(f"   Plan: {subscription_status.plan}")
        logger.info(f"   Period: {subscription_status.period}")
        
        if subscription_status.limits:
            logger.info(f"\n📈 Usage limits:")
            logger.info(f"   Minutes limit: {subscription_status.limits.minutes_limit}")
            logger.info(f"   Minutes used: {subscription_status.limits.minutes_used}")
            logger.info(f"   Minutes remaining: {subscription_status.limits.minutes_remaining}")
            logger.info(f"   Sessions limit: {subscription_status.limits.sessions_limit}")
            logger.info(f"   Sessions used: {subscription_status.limits.sessions_used}")
            logger.info(f"   Sessions remaining: {subscription_status.limits.sessions_remaining}")
            
            # Calculate expected remaining time
            if subscription_status.limits.minutes_limit == -1:
                logger.info(f"🎉 User has unlimited minutes!")
            else:
                remaining_minutes = subscription_status.limits.minutes_remaining
                if remaining_minutes is not None:
                    logger.info(f"⏰ User has {remaining_minutes:.1f} minutes remaining this month")
                    
                    # Calculate percentage used
                    if subscription_status.limits.minutes_limit > 0:
                        percentage_used = (subscription_status.limits.minutes_used / subscription_status.limits.minutes_limit) * 100
                        logger.info(f"📊 Usage: {percentage_used:.1f}% of monthly allowance")
        
        # Test can_start_session method
        logger.info(f"\n🚀 Testing session access...")
        can_start, message = await SubscriptionService.can_start_session(user_id)
        logger.info(f"   Can start session: {can_start}")
        logger.info(f"   Message: {message}")
        
        # Test can_access_feature method
        can_practice, practice_message = await SubscriptionService.can_access_feature(user_id, "practice_session")
        logger.info(f"   Can access practice: {can_practice}")
        if practice_message:
            logger.info(f"   Practice message: {practice_message}")
        
        logger.info(f"\n🎯 Verification complete!")
        
        # Summary
        logger.info(f"\n" + "="*60)
        logger.info(f"📋 SUMMARY FOR {TARGET_USER}")
        logger.info(f"="*60)
        logger.info(f"✅ Data restored: {current_minutes:.2f} minutes, {current_sessions} sessions")
        logger.info(f"✅ Subscription: {subscription_status.plan} ({subscription_status.status})")
        if subscription_status.limits and subscription_status.limits.minutes_remaining is not None:
            if subscription_status.limits.minutes_limit == -1:
                logger.info(f"✅ Remaining time: UNLIMITED")
            else:
                logger.info(f"✅ Remaining time: {subscription_status.limits.minutes_remaining:.1f} minutes")
        logger.info(f"✅ Can start new session: {can_start}")
        
    except Exception as e:
        logger.error(f"❌ Error verifying remaining time: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_remaining_time())
