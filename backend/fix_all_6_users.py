#!/usr/bin/env python3
"""
Simple Fix Script for All 6 Production Users
Addresses duration tracking inconsistencies with appropriate scale solution.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
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

# All 6 production users
PRODUCTION_USERS = [
    "ruz19bar05@gmail.com",
    "mr.theta.iii@gmail.com", 
    "hgonulkirmaz@gmail.com",
    "sub@nicktao.gr",
    "alipala.ist@gmail.com",
    "anastasiabarka2@gmail.com"
]

class UserDurationFixer:
    def __init__(self):
        self.db = None
        
    async def initialize(self):
        """Initialize database connection and services"""
        self.db = database
        logger.info("✅ Database connection established")
        
    async def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """Get all session data for a user"""
        try:
            # Get learning plan sessions
            learning_sessions = []
            async for session in self.db.learning_plans.find({"user_id": user_id}):
                learning_sessions.append(session)
            
            # Get conversation sessions  
            conversation_sessions = []
            async for session in self.db.conversation_sessions.find({"user_id": user_id}):
                conversation_sessions.append(session)
                
            return {
                "learning_sessions": learning_sessions,
                "conversation_sessions": conversation_sessions
            }
        except Exception as e:
            logger.error(f"❌ Error getting sessions for user {user_id}: {e}")
            return {"learning_sessions": [], "conversation_sessions": []}
    
    def calculate_session_duration(self, session: Dict[str, Any]) -> float:
        """Calculate duration for a single session in minutes"""
        try:
            # For learning plan sessions
            if 'sessions' in session:
                total_minutes = 0.0
                for sess in session.get('sessions', []):
                    if sess.get('completed', False):
                        # Estimate 5 minutes per completed session
                        total_minutes += 5.0
                return total_minutes
            
            # For conversation sessions
            elif 'duration' in session:
                duration = session['duration']
                if isinstance(duration, (int, float)):
                    return float(duration) / 60.0  # Convert seconds to minutes
                    
            # Fallback estimation
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating session duration: {e}")
            return 0.0
    
    def is_session_in_current_period(self, session: Dict[str, Any], period_start: datetime, period_end: datetime) -> bool:
        """Check if session is within current subscription period"""
        try:
            # Try different timestamp fields
            timestamp_fields = ['created_at', 'timestamp', 'updated_at', 'date']
            session_time = None
            
            for field in timestamp_fields:
                if field in session:
                    timestamp = session[field]
                    if isinstance(timestamp, str):
                        session_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif hasattr(timestamp, 'replace'):  # datetime object
                        session_time = timestamp
                    break
            
            if not session_time:
                # If no timestamp found, assume it's recent
                return True
                
            # Ensure timezone awareness
            if session_time.tzinfo is None:
                session_time = session_time.replace(tzinfo=timezone.utc)
                
            return period_start <= session_time <= period_end
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking session period: {e}")
            return True  # Default to including the session
    
    async def calculate_correct_usage(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate correct usage for current period"""
        try:
            user_id = str(user['_id'])
            
            # Get current period boundaries
            period_start = user.get('current_period_start')
            period_end = user.get('current_period_end')
            
            if not period_start or not period_end:
                logger.warning(f"⚠️ Missing period boundaries for user {user.get('email')}")
                return {"total_minutes": 0.0, "total_sessions": 0}
            
            # Ensure datetime objects
            if isinstance(period_start, str):
                period_start = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            if isinstance(period_end, str):
                period_end = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
                
            # Get all sessions
            sessions_data = await self.get_user_sessions(user_id)
            
            total_minutes = 0.0
            total_sessions = 0
            
            # Process learning sessions
            for session in sessions_data['learning_sessions']:
                if self.is_session_in_current_period(session, period_start, period_end):
                    duration = self.calculate_session_duration(session)
                    total_minutes += duration
                    if duration > 0:
                        total_sessions += 1
            
            # Process conversation sessions
            for session in sessions_data['conversation_sessions']:
                if self.is_session_in_current_period(session, period_start, period_end):
                    duration = self.calculate_session_duration(session)
                    total_minutes += duration
                    if duration > 0:
                        total_sessions += 1
            
            return {
                "total_minutes": round(total_minutes, 2),
                "total_sessions": total_sessions,
                "period_start": period_start,
                "period_end": period_end
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating usage for user {user.get('email')}: {e}")
            return {"total_minutes": 0.0, "total_sessions": 0}
    
    async def fix_user_data(self, email: str) -> Dict[str, Any]:
        """Fix duration tracking data for a single user"""
        try:
            logger.info(f"\n🔧 Fixing user: {email}")
            
            # Get user data
            user = await self.db.users.find_one({"email": email})
            if not user:
                logger.error(f"❌ User not found: {email}")
                return {"status": "error", "message": "User not found"}
            
            # Get current stored values
            current_minutes = user.get('practice_minutes_used', 0)
            current_sessions = user.get('practice_sessions_used', 0)
            
            logger.info(f"📊 Current stored: {current_minutes:.2f} minutes, {current_sessions} sessions")
            
            # Calculate correct values
            correct_usage = await self.calculate_correct_usage(user)
            correct_minutes = correct_usage['total_minutes']
            correct_sessions = correct_usage['total_sessions']
            
            logger.info(f"✅ Calculated correct: {correct_minutes:.2f} minutes, {correct_sessions} sessions")
            
            # Check if fix is needed
            minutes_diff = abs(current_minutes - correct_minutes)
            sessions_diff = abs(current_sessions - correct_sessions)
            
            if minutes_diff < 0.01 and sessions_diff == 0:
                logger.info(f"✅ User {email} data is already correct")
                return {
                    "status": "no_change_needed",
                    "current_minutes": current_minutes,
                    "current_sessions": current_sessions
                }
            
            # Apply fix
            logger.info(f"🔄 Applying fix...")
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
                            "sessions_diff": correct_sessions - current_sessions
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
                    "sessions_diff": correct_sessions - current_sessions
                }
            else:
                logger.error(f"❌ Failed to update user {email}")
                return {"status": "error", "message": "Database update failed"}
                
        except Exception as e:
            logger.error(f"❌ Error fixing user {email}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def fix_all_users(self) -> Dict[str, Any]:
        """Fix all 6 production users"""
        logger.info("🚀 Starting fix for all 6 production users")
        
        results = {}
        summary = {
            "total_users": len(PRODUCTION_USERS),
            "fixed": 0,
            "no_change_needed": 0,
            "errors": 0
        }
        
        for email in PRODUCTION_USERS:
            try:
                result = await self.fix_user_data(email)
                results[email] = result
                
                if result["status"] == "fixed":
                    summary["fixed"] += 1
                elif result["status"] == "no_change_needed":
                    summary["no_change_needed"] += 1
                else:
                    summary["errors"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error for {email}: {e}")
                results[email] = {"status": "error", "message": str(e)}
                summary["errors"] += 1
        
        return {"results": results, "summary": summary}

async def main():
    """Main execution function"""
    logger.info("🎯 Starting Duration Fix for All 6 Production Users")
    logger.info("=" * 60)
    
    fixer = UserDurationFixer()
    
    try:
        # Initialize
        await fixer.initialize()
        
        # Fix all users
        results = await fixer.fix_all_users()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📋 FINAL SUMMARY")
        logger.info("=" * 60)
        
        summary = results["summary"]
        logger.info(f"Total users processed: {summary['total_users']}")
        logger.info(f"✅ Fixed: {summary['fixed']}")
        logger.info(f"✅ No change needed: {summary['no_change_needed']}")
        logger.info(f"❌ Errors: {summary['errors']}")
        
        # Print detailed results
        logger.info("\n📊 DETAILED RESULTS:")
        for email, result in results["results"].items():
            if result["status"] == "fixed":
                logger.info(f"✅ {email}: Fixed ({result['minutes_diff']:+.2f} min, {result['sessions_diff']:+d} sessions)")
            elif result["status"] == "no_change_needed":
                logger.info(f"✅ {email}: Already correct")
            else:
                logger.info(f"❌ {email}: Error - {result.get('message', 'Unknown error')}")
        
        logger.info("\n🎉 Duration fix process completed!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
