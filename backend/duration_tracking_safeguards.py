#!/usr/bin/env python3
"""
Duration Tracking Safeguards - Comprehensive Prevention System
Prevents data corruption and provides monitoring for user duration tracking
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
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

class DurationTrackingSafeguards:
    """Comprehensive safeguards for duration tracking data integrity"""
    
    def __init__(self):
        self.db = database
        
    async def validate_user_data_change(self, user_id: str, old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """
        Validate that a user data change is reasonable and safe
        Returns validation result with warnings/errors
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        old_minutes = old_data.get('practice_minutes_used', 0)
        new_minutes = new_data.get('practice_minutes_used', 0)
        old_sessions = old_data.get('practice_sessions_used', 0)
        new_sessions = new_data.get('practice_sessions_used', 0)
        
        # Check for suspicious data resets
        if old_minutes > 10 and new_minutes == 0:
            validation_result["errors"].append(
                f"DANGEROUS: Resetting minutes from {old_minutes} to 0 - this looks like data corruption!"
            )
            validation_result["is_valid"] = False
            
        if old_sessions > 2 and new_sessions == 0:
            validation_result["errors"].append(
                f"DANGEROUS: Resetting sessions from {old_sessions} to 0 - this looks like data corruption!"
            )
            validation_result["is_valid"] = False
        
        # Check for unrealistic increases
        minutes_increase = new_minutes - old_minutes
        if minutes_increase > 500:  # More than 8+ hours in one update
            validation_result["warnings"].append(
                f"Large minutes increase: +{minutes_increase:.2f} minutes - please verify this is correct"
            )
            
        sessions_increase = new_sessions - old_sessions
        if sessions_increase > 50:  # More than 50 sessions in one update
            validation_result["warnings"].append(
                f"Large sessions increase: +{sessions_increase} sessions - please verify this is correct"
            )
        
        # Check for negative values
        if new_minutes < 0:
            validation_result["errors"].append("Minutes cannot be negative")
            validation_result["is_valid"] = False
            
        if new_sessions < 0:
            validation_result["errors"].append("Sessions cannot be negative")
            validation_result["is_valid"] = False
        
        # Check for reasonable ratios
        if new_sessions > 0 and new_minutes > 0:
            avg_minutes_per_session = new_minutes / new_sessions
            if avg_minutes_per_session > 60:  # More than 1 hour per session
                validation_result["warnings"].append(
                    f"High average session duration: {avg_minutes_per_session:.1f} min/session"
                )
            elif avg_minutes_per_session < 1:  # Less than 1 minute per session
                validation_result["warnings"].append(
                    f"Low average session duration: {avg_minutes_per_session:.1f} min/session"
                )
        
        return validation_result
    
    async def safe_update_user_duration(self, user_id: str, new_minutes: float, new_sessions: int, 
                                      reason: str, bypass_validation: bool = False) -> Dict[str, Any]:
        """
        Safely update user duration data with validation and logging
        """
        try:
            # Get current user data
            user = await self.db.users.find_one({"_id": user_id} if isinstance(user_id, str) else {"_id": user_id})
            if not user:
                return {"success": False, "error": "User not found"}
            
            old_data = {
                "practice_minutes_used": user.get('practice_minutes_used', 0),
                "practice_sessions_used": user.get('practice_sessions_used', 0)
            }
            
            new_data = {
                "practice_minutes_used": new_minutes,
                "practice_sessions_used": new_sessions
            }
            
            # Validate the change
            if not bypass_validation:
                validation = await self.validate_user_data_change(user_id, old_data, new_data)
                
                if not validation["is_valid"]:
                    logger.error(f"❌ Validation failed for user {user_id}: {validation['errors']}")
                    return {
                        "success": False, 
                        "error": "Validation failed", 
                        "validation": validation
                    }
                
                if validation["warnings"]:
                    logger.warning(f"⚠️ Validation warnings for user {user_id}: {validation['warnings']}")
            
            # Create audit trail
            audit_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": str(user_id),
                "user_email": user.get('email', 'unknown'),
                "reason": reason,
                "old_minutes": old_data["practice_minutes_used"],
                "new_minutes": new_minutes,
                "old_sessions": old_data["practice_sessions_used"],
                "new_sessions": new_sessions,
                "minutes_diff": new_minutes - old_data["practice_minutes_used"],
                "sessions_diff": new_sessions - old_data["practice_sessions_used"]
            }
            
            # Update user data
            update_result = await self.db.users.update_one(
                {"_id": user_id} if isinstance(user_id, str) else {"_id": user_id},
                {
                    "$set": {
                        "practice_minutes_used": new_minutes,
                        "practice_sessions_used": new_sessions,
                        "last_duration_update": datetime.now(timezone.utc).isoformat(),
                        "last_duration_update_reason": reason
                    },
                    "$push": {
                        "duration_audit_trail": {
                            "$each": [audit_data],
                            "$slice": -10  # Keep last 10 changes
                        }
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"✅ Successfully updated user {user.get('email', user_id)}: "
                          f"{old_data['practice_minutes_used']:.2f}→{new_minutes:.2f} min, "
                          f"{old_data['practice_sessions_used']}→{new_sessions} sessions")
                
                return {
                    "success": True,
                    "audit_data": audit_data,
                    "validation": validation if not bypass_validation else None
                }
            else:
                return {"success": False, "error": "Database update failed"}
                
        except Exception as e:
            logger.error(f"❌ Error updating user duration: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_data_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect potential data anomalies across all users
        """
        anomalies = []
        
        try:
            # Get all users with usage data
            async for user in self.db.users.find({
                "$or": [
                    {"practice_minutes_used": {"$gt": 0}},
                    {"practice_sessions_used": {"$gt": 0}}
                ]
            }):
                user_id = str(user['_id'])
                email = user.get('email', 'unknown')
                minutes = user.get('practice_minutes_used', 0)
                sessions = user.get('practice_sessions_used', 0)
                
                # Check for anomalies
                issues = []
                
                # Sessions without minutes
                if sessions > 0 and minutes == 0:
                    issues.append("Has sessions but 0 minutes")
                
                # Minutes without sessions
                if minutes > 0 and sessions == 0:
                    issues.append("Has minutes but 0 sessions")
                
                # Unrealistic ratios
                if sessions > 0 and minutes > 0:
                    avg_per_session = minutes / sessions
                    if avg_per_session > 120:  # More than 2 hours per session
                        issues.append(f"Very high avg session duration: {avg_per_session:.1f} min")
                    elif avg_per_session < 0.5:  # Less than 30 seconds per session
                        issues.append(f"Very low avg session duration: {avg_per_session:.1f} min")
                
                # Excessive usage
                if minutes > 1000:  # More than 16+ hours
                    issues.append(f"Excessive minutes: {minutes}")
                if sessions > 200:  # More than 200 sessions
                    issues.append(f"Excessive sessions: {sessions}")
                
                if issues:
                    anomalies.append({
                        "user_id": user_id,
                        "email": email,
                        "minutes": minutes,
                        "sessions": sessions,
                        "issues": issues
                    })
                    
        except Exception as e:
            logger.error(f"❌ Error detecting anomalies: {e}")
        
        return anomalies
    
    async def create_data_backup(self, user_id: str) -> Dict[str, Any]:
        """
        Create a backup of user's current duration data before making changes
        """
        try:
            user = await self.db.users.find_one({"_id": user_id} if isinstance(user_id, str) else {"_id": user_id})
            if not user:
                return {"success": False, "error": "User not found"}
            
            backup_data = {
                "user_id": str(user_id),
                "email": user.get('email'),
                "backup_timestamp": datetime.now(timezone.utc).isoformat(),
                "practice_minutes_used": user.get('practice_minutes_used', 0),
                "practice_sessions_used": user.get('practice_sessions_used', 0),
                "assessments_used": user.get('assessments_used', 0),
                "current_period_start": user.get('current_period_start'),
                "current_period_end": user.get('current_period_end'),
                "subscription_plan": user.get('subscription_plan'),
                "subscription_status": user.get('subscription_status')
            }
            
            # Store backup
            await self.db.user_data_backups.insert_one(backup_data)
            
            logger.info(f"✅ Created backup for user {user.get('email', user_id)}")
            return {"success": True, "backup_data": backup_data}
            
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            return {"success": False, "error": str(e)}

# Utility functions for easy use
async def safe_duration_update(user_id: str, minutes: float, sessions: int, reason: str):
    """Easy-to-use function for safe duration updates"""
    safeguards = DurationTrackingSafeguards()
    return await safeguards.safe_update_user_duration(user_id, minutes, sessions, reason)

async def check_for_anomalies():
    """Easy-to-use function to check for data anomalies"""
    safeguards = DurationTrackingSafeguards()
    return await safeguards.detect_data_anomalies()

async def main():
    """Test the safeguards system"""
    print("🛡️ Duration Tracking Safeguards System")
    print("=" * 50)
    
    safeguards = DurationTrackingSafeguards()
    
    # Check for anomalies
    print("🔍 Checking for data anomalies...")
    anomalies = await safeguards.detect_data_anomalies()
    
    if anomalies:
        print(f"⚠️ Found {len(anomalies)} potential anomalies:")
        for anomaly in anomalies:
            print(f"  {anomaly['email']}: {', '.join(anomaly['issues'])}")
    else:
        print("✅ No anomalies detected")

if __name__ == "__main__":
    asyncio.run(main())
