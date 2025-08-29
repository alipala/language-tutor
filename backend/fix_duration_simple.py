#!/usr/bin/env python3
"""
Simple Duration Fix Script for Production Users
Focused on fixing the specific user mentioned and validating the fix.
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

# Focus on the specific user mentioned in the task
TARGET_USER = "alipala.ist@gmail.com"

class SimpleDurationFixer:
    def __init__(self):
        self.db = database
        
    async def get_user_data(self, email: str) -> Dict[str, Any]:
        """Get user data"""
        user = await self.db.users.find_one({"email": email})
        if not user:
            logger.error(f"❌ User not found: {email}")
            return {}
        return user
    
    async def get_user_sessions_count(self, user_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Get session counts for the current period"""
        try:
            # Count learning plan sessions in current period
            learning_count = 0
            learning_minutes = 0.0
            
            async for session in self.db.learning_plans.find({"user_id": user_id}):
                # Check if session has timestamp in current period
                session_time = None
                for field in ['created_at', 'timestamp', 'updated_at']:
                    if field in session:
                        timestamp = session[field]
                        if isinstance(timestamp, str):
                            session_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        elif hasattr(timestamp, 'replace'):
                            session_time = timestamp
                        break
                
                if session_time and session_time.tzinfo is None:
                    session_time = session_time.replace(tzinfo=timezone.utc)
                
                if session_time and period_start <= session_time <= period_end:
                    # Count completed sessions in this learning plan
                    sessions_list = session.get('sessions', [])
                    completed_sessions = sum(1 for s in sessions_list if s.get('completed', False))
                    learning_count += completed_sessions
                    learning_minutes += completed_sessions * 5.0  # 5 minutes per session
            
            # Count conversation sessions in current period
            conversation_count = 0
            conversation_minutes = 0.0
            
            async for session in self.db.conversation_sessions.find({"user_id": user_id}):
                session_time = None
                for field in ['created_at', 'timestamp', 'updated_at']:
                    if field in session:
                        timestamp = session[field]
                        if isinstance(timestamp, str):
                            session_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        elif hasattr(timestamp, 'replace'):
                            session_time = timestamp
                        break
                
                if session_time and session_time.tzinfo is None:
                    session_time = session_time.replace(tzinfo=timezone.utc)
                
                if session_time and period_start <= session_time <= period_end:
                    conversation_count += 1
                    # Get duration in minutes
                    duration = session.get('duration', 0)
                    if isinstance(duration, (int, float)):
                        conversation_minutes += float(duration) / 60.0
            
            return {
                "learning_sessions": learning_count,
                "learning_minutes": learning_minutes,
                "conversation_sessions": conversation_count,
                "conversation_minutes": conversation_minutes,
                "total_sessions": learning_count + conversation_count,
                "total_minutes": learning_minutes + conversation_minutes
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting session counts: {e}")
            return {
                "learning_sessions": 0,
                "learning_minutes": 0.0,
                "conversation_sessions": 0,
                "conversation_minutes": 0.0,
                "total_sessions": 0,
                "total_minutes": 0.0
            }
    
    async def fix_user_duration(self, email: str) -> Dict[str, Any]:
        """Fix duration tracking for a specific user"""
        try:
            logger.info(f"🔧 Analyzing user: {email}")
            
            # Get user data
            user = await self.get_user_data(email)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Get current stored values
            current_minutes = user.get('practice_minutes_used', 0)
            current_sessions = user.get('practice_sessions_used', 0)
            
            # Get period boundaries
            period_start = user.get('current_period_start')
            period_end = user.get('current_period_end')
            
            if not period_start or not period_end:
                logger.warning(f"⚠️ Missing period boundaries for {email}")
                return {"status": "error", "message": "Missing period boundaries"}
            
            # Ensure datetime objects
            if isinstance(period_start, str):
                period_start = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            if isinstance(period_end, str):
                period_end = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
            
            logger.info(f"📅 Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}")
            logger.info(f"📊 Current stored: {current_minutes:.2f} minutes, {current_sessions} sessions")
            
            # Calculate correct values
            session_data = await self.get_user_sessions_count(str(user['_id']), period_start, period_end)
            
            logger.info(f"🔍 Found sessions:")
            logger.info(f"   Learning: {session_data['learning_sessions']} sessions, {session_data['learning_minutes']:.2f} minutes")
            logger.info(f"   Conversation: {session_data['conversation_sessions']} sessions, {session_data['conversation_minutes']:.2f} minutes")
            logger.info(f"   Total: {session_data['total_sessions']} sessions, {session_data['total_minutes']:.2f} minutes")
            
            # Check if fix is needed
            correct_minutes = round(session_data['total_minutes'], 2)
            correct_sessions = session_data['total_sessions']
            
            minutes_diff = abs(current_minutes - correct_minutes)
            sessions_diff = abs(current_sessions - correct_sessions)
            
            if minutes_diff < 0.01 and sessions_diff == 0:
                logger.info(f"✅ User {email} data is already correct")
                return {
                    "status": "no_change_needed",
                    "current_minutes": current_minutes,
                    "current_sessions": current_sessions,
                    "calculated_minutes": correct_minutes,
                    "calculated_sessions": correct_sessions
                }
            
            logger.info(f"🔄 Fix needed:")
            logger.info(f"   Minutes: {current_minutes:.2f} → {correct_minutes:.2f} (diff: {correct_minutes - current_minutes:+.2f})")
            logger.info(f"   Sessions: {current_sessions} → {correct_sessions} (diff: {correct_sessions - current_sessions:+d})")
            
            # Apply fix
            update_result = await self.db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "practice_minutes_used": correct_minutes,
                        "practice_sessions_used": correct_sessions,
                        "duration_fix_applied": True,
                        "duration_fix_date": datetime.now(timezone.utc).isoformat(),
                        "duration_fix_details": {
                            "old_minutes": current_minutes,
                            "new_minutes": correct_minutes,
                            "old_sessions": current_sessions,
                            "new_sessions": correct_sessions,
                            "minutes_diff": correct_minutes - current_minutes,
                            "sessions_diff": correct_sessions - current_sessions,
                            "session_breakdown": session_data
                        }
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"✅ Successfully fixed user {email}")
                return {
                    "status": "fixed",
                    "old_minutes": current_minutes,
                    "new_minutes": correct_minutes,
                    "old_sessions": current_sessions,
                    "new_sessions": correct_sessions,
                    "minutes_diff": correct_minutes - current_minutes,
                    "sessions_diff": correct_sessions - current_sessions,
                    "session_breakdown": session_data
                }
            else:
                logger.error(f"❌ Failed to update user {email}")
                return {"status": "error", "message": "Database update failed"}
                
        except Exception as e:
            logger.error(f"❌ Error fixing user {email}: {e}")
            return {"status": "error", "message": str(e)}

async def main():
    """Main execution function"""
    logger.info("🎯 Simple Duration Fix for Target User")
    logger.info("=" * 50)
    
    fixer = SimpleDurationFixer()
    
    try:
        # Fix the target user
        result = await fixer.fix_user_duration(TARGET_USER)
        
        # Print results
        logger.info("\n" + "=" * 50)
        logger.info("📋 RESULTS")
        logger.info("=" * 50)
        
        if result["status"] == "fixed":
            logger.info(f"✅ {TARGET_USER}: FIXED")
            logger.info(f"   Minutes: {result['old_minutes']:.2f} → {result['new_minutes']:.2f} ({result['minutes_diff']:+.2f})")
            logger.info(f"   Sessions: {result['old_sessions']} → {result['new_sessions']} ({result['sessions_diff']:+d})")
        elif result["status"] == "no_change_needed":
            logger.info(f"✅ {TARGET_USER}: Already correct")
            logger.info(f"   Current: {result['current_minutes']:.2f} minutes, {result['current_sessions']} sessions")
        else:
            logger.info(f"❌ {TARGET_USER}: Error - {result.get('message', 'Unknown error')}")
        
        logger.info("\n🎉 Fix process completed!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
