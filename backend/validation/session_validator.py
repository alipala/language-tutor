#!/usr/bin/env python3
"""
Session Validator
Validates session data completeness to prevent dashboard calculation errors
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import database
from bson import ObjectId

logger = logging.getLogger(__name__)

class SessionValidator:
    """Validates session data to prevent dashboard calculation discrepancies"""
    
    @staticmethod
    async def validate_session_completeness(user_id: str) -> Dict[str, Any]:
        """
        Validate that user's sessions are properly saved and complete
        Returns validation result with any missing sessions detected
        """
        try:
            # Get user data
            try:
                user_object_id = ObjectId(user_id)
                query = {"_id": user_object_id}
            except:
                query = {"_id": user_id}
            
            user = await database["users"].find_one(query)
            if not user:
                return {
                    "is_valid": False,
                    "error": "User not found",
                    "user_id": user_id
                }
            
            # Get subscription period
            period_start = user.get("current_period_start")
            period_end = user.get("current_period_end")
            
            if not period_start or not period_end:
                return {
                    "is_valid": False,
                    "error": "Missing subscription period - cannot validate sessions",
                    "user_id": user_id
                }
            
            validation_result = {
                "is_valid": True,
                "user_id": user_id,
                "user_email": user.get("email", "unknown"),
                "period_start": period_start,
                "period_end": period_end,
                "session_analysis": {},
                "discrepancies": [],
                "warnings": [],
                "corrections_needed": []
            }
            
            # Get actual session data from collections
            conversation_sessions = await database["conversation_sessions"].find({
                "user_id": user_id,
                "created_at": {
                    "$gte": period_start,
                    "$lt": period_end
                }
            }).to_list(length=None)
            
            # Get learning plan sessions
            learning_plans = await database["learning_plans"].find({
                "user_id": user_id
            }).to_list(length=None)
            
            learning_session_minutes = 0.0
            learning_session_count = 0
            
            for plan in learning_plans:
                sessions = plan.get("sessions", [])
                for session in sessions:
                    session_date = session.get("completed_at")
                    if session_date:
                        # Handle both string and datetime objects
                        if isinstance(session_date, str):
                            try:
                                session_date = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                            except:
                                continue
                        
                        if period_start <= session_date < period_end:
                            learning_session_minutes += session.get("duration_minutes", 0.0)
                            learning_session_count += 1
            
            # Calculate actual totals
            conversation_minutes = sum(s.get("duration_minutes", 0.0) for s in conversation_sessions)
            conversation_count = len(conversation_sessions)
            
            actual_total_minutes = conversation_minutes + learning_session_minutes
            actual_total_sessions = conversation_count + learning_session_count
            
            # Get user record data
            user_record_minutes = user.get("practice_minutes_used", 0.0)
            user_record_sessions = user.get("practice_sessions_used", 0)
            
            validation_result["session_analysis"] = {
                "conversation_sessions": {
                    "count": conversation_count,
                    "minutes": conversation_minutes
                },
                "learning_plan_sessions": {
                    "count": learning_session_count,
                    "minutes": learning_session_minutes
                },
                "actual_totals": {
                    "sessions": actual_total_sessions,
                    "minutes": actual_total_minutes
                },
                "user_record": {
                    "sessions": user_record_sessions,
                    "minutes": user_record_minutes
                }
            }
            
            # Check for discrepancies
            minutes_discrepancy = abs(user_record_minutes - actual_total_minutes)
            sessions_discrepancy = abs(user_record_sessions - actual_total_sessions)
            
            if minutes_discrepancy > 0.1:  # 0.1 minute tolerance
                validation_result["discrepancies"].append({
                    "type": "minutes_mismatch",
                    "user_record": user_record_minutes,
                    "actual_total": actual_total_minutes,
                    "difference": minutes_discrepancy
                })
                validation_result["corrections_needed"].append("fix_minutes_discrepancy")
                validation_result["is_valid"] = False
            
            if sessions_discrepancy > 0:
                validation_result["discrepancies"].append({
                    "type": "sessions_mismatch", 
                    "user_record": user_record_sessions,
                    "actual_total": actual_total_sessions,
                    "difference": sessions_discrepancy
                })
                validation_result["corrections_needed"].append("fix_sessions_discrepancy")
                validation_result["is_valid"] = False
            
            # Additional validations
            # Check for sessions with invalid data
            invalid_sessions = []
            for session in conversation_sessions:
                if not session.get("duration_minutes") or session.get("duration_minutes") <= 0:
                    invalid_sessions.append({
                        "id": str(session["_id"]),
                        "issue": "Invalid duration"
                    })
                if not session.get("created_at"):
                    invalid_sessions.append({
                        "id": str(session["_id"]),
                        "issue": "Missing created_at timestamp"
                    })
            
            if invalid_sessions:
                validation_result["warnings"].append(f"Found {len(invalid_sessions)} sessions with invalid data")
                validation_result["session_analysis"]["invalid_sessions"] = invalid_sessions
            
            logger.info(f"[VALIDATION] Session validation for {user.get('email', user_id)}: "
                       f"{'✅ Valid' if validation_result['is_valid'] else '❌ Invalid'} "
                       f"({actual_total_minutes:.1f} min, {actual_total_sessions} sessions)")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"[VALIDATION] Error validating session completeness: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e),
                "user_id": user_id
            }
    
    @staticmethod
    async def detect_missing_sessions(user_id: str, expected_activity: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect if user has missing sessions based on expected activity patterns
        """
        try:
            validation_result = await SessionValidator.validate_session_completeness(user_id)
            
            if not validation_result.get("is_valid"):
                return validation_result
            
            session_analysis = validation_result["session_analysis"]
            actual_totals = session_analysis["actual_totals"]
            
            missing_session_analysis = {
                "user_id": user_id,
                "period_start": validation_result["period_start"],
                "period_end": validation_result["period_end"],
                "current_sessions": actual_totals["sessions"],
                "current_minutes": actual_totals["minutes"],
                "potential_issues": [],
                "recommendations": []
            }
            
            # Check for suspiciously low activity for paid subscribers
            try:
                user_object_id = ObjectId(user_id)
                query = {"_id": user_object_id}
            except:
                query = {"_id": user_id}
                
            user = await database["users"].find_one(query)
            subscription_plan = user.get("subscription_plan", "try_learn")
            
            # Days into current period
            now = datetime.utcnow()
            days_into_period = (now - validation_result["period_start"]).days
            
            if subscription_plan == "fluency_builder" and days_into_period > 7:
                # For Fluency Builder, expect some activity after a week
                if actual_totals["sessions"] == 0:
                    missing_session_analysis["potential_issues"].append(
                        f"Fluency Builder subscriber with 0 sessions after {days_into_period} days"
                    )
                elif actual_totals["minutes"] < 5 and days_into_period > 14:
                    missing_session_analysis["potential_issues"].append(
                        f"Very low usage: {actual_totals['minutes']:.1f} minutes in {days_into_period} days"
                    )
            
            # Check for gaps in session timestamps (potential missing sessions)
            conversation_sessions = await database["conversation_sessions"].find({
                "user_id": user_id,
                "created_at": {
                    "$gte": validation_result["period_start"],
                    "$lt": validation_result["period_end"]
                }
            }).sort("created_at", 1).to_list(length=None)
            
            if len(conversation_sessions) > 1:
                # Look for large gaps between sessions that might indicate missing data
                for i in range(1, len(conversation_sessions)):
                    prev_session = conversation_sessions[i-1]
                    curr_session = conversation_sessions[i]
                    
                    time_gap = curr_session["created_at"] - prev_session["created_at"]
                    if time_gap.total_seconds() < 300:  # Less than 5 minutes apart
                        missing_session_analysis["potential_issues"].append(
                            f"Sessions very close together: {time_gap.total_seconds():.0f} seconds apart"
                        )
            
            # Recommendations based on findings
            if missing_session_analysis["potential_issues"]:
                missing_session_analysis["recommendations"].extend([
                    "Check if frontend is properly saving all sessions",
                    "Verify session completion detection is working",
                    "Consider implementing backup session tracking"
                ])
            
            return missing_session_analysis
            
        except Exception as e:
            logger.error(f"[VALIDATION] Error detecting missing sessions: {str(e)}")
            return {
                "error": str(e),
                "user_id": user_id
            }
    
    @staticmethod
    async def fix_session_discrepancies(user_id: str) -> Dict[str, Any]:
        """
        Fix session data discrepancies by updating user record to match actual session data
        """
        try:
            validation_result = await SessionValidator.validate_session_completeness(user_id)
            
            if validation_result.get("is_valid"):
                return {
                    "fixes_applied": False,
                    "message": "No session discrepancies found"
                }
            
            corrections_needed = validation_result.get("corrections_needed", [])
            if not any("discrepancy" in correction for correction in corrections_needed):
                return {
                    "fixes_applied": False,
                    "message": "No session discrepancy corrections needed"
                }
            
            session_analysis = validation_result["session_analysis"]
            actual_totals = session_analysis["actual_totals"]
            
            # Get user data
            try:
                user_object_id = ObjectId(user_id)
                query = {"_id": user_object_id}
            except:
                query = {"_id": user_id}
            
            user = await database["users"].find_one(query)
            if not user:
                return {"fixes_applied": False, "error": "User not found"}
            
            fixes_applied = []
            update_fields = {}
            
            # Fix minutes discrepancy
            if "fix_minutes_discrepancy" in corrections_needed:
                old_minutes = user.get("practice_minutes_used", 0.0)
                new_minutes = actual_totals["minutes"]
                
                update_fields["practice_minutes_used"] = new_minutes
                fixes_applied.append(f"Updated minutes: {old_minutes:.2f} → {new_minutes:.2f}")
            
            # Fix sessions discrepancy
            if "fix_sessions_discrepancy" in corrections_needed:
                old_sessions = user.get("practice_sessions_used", 0)
                new_sessions = actual_totals["sessions"]
                
                update_fields["practice_sessions_used"] = new_sessions
                fixes_applied.append(f"Updated sessions: {old_sessions} → {new_sessions}")
            
            # Apply fixes
            if update_fields:
                update_fields["last_session_validation_fix"] = datetime.utcnow().isoformat()
                update_fields["session_validation_fix_reason"] = "fix_session_discrepancies"
                
                result = await database["users"].update_one(query, {"$set": update_fields})
                
                if result.modified_count > 0:
                    logger.info(f"[VALIDATION] Fixed session discrepancies for user {user.get('email', user_id)}: {fixes_applied}")
                    return {
                        "fixes_applied": True,
                        "fixes": fixes_applied,
                        "update_fields": update_fields,
                        "session_analysis": session_analysis
                    }
                else:
                    return {
                        "fixes_applied": False,
                        "error": "Database update failed"
                    }
            else:
                return {
                    "fixes_applied": False,
                    "message": "No applicable fixes found"
                }
                
        except Exception as e:
            logger.error(f"[VALIDATION] Error fixing session discrepancies: {str(e)}")
            return {
                "fixes_applied": False,
                "error": str(e)
            }

if __name__ == "__main__":
    # Test the validator
    import asyncio
    
    async def test_validator():
        user_id = "688921c268819565ef1ce3dc"
        
        print("🧪 TESTING SESSION VALIDATOR")
        print("=" * 50)
        
        # Test session completeness validation
        result = await SessionValidator.validate_session_completeness(user_id)
        print(f"✅ Session Validation: {'Valid' if result['is_valid'] else 'Invalid'}")
        
        if result.get('session_analysis'):
            analysis = result['session_analysis']
            print(f"   Conversation Sessions: {analysis['conversation_sessions']['count']} ({analysis['conversation_sessions']['minutes']:.1f} min)")
            print(f"   Learning Plan Sessions: {analysis['learning_plan_sessions']['count']} ({analysis['learning_plan_sessions']['minutes']:.1f} min)")
            print(f"   Actual Total: {analysis['actual_totals']['sessions']} sessions, {analysis['actual_totals']['minutes']:.1f} min")
            print(f"   User Record: {analysis['user_record']['sessions']} sessions, {analysis['user_record']['minutes']:.1f} min")
        
        if result.get('discrepancies'):
            print(f"   Discrepancies: {len(result['discrepancies'])}")
            for disc in result['discrepancies']:
                print(f"      {disc['type']}: {disc['difference']}")
        
        # Test missing sessions detection
        missing_result = await SessionValidator.detect_missing_sessions(user_id)
        print(f"✅ Missing Sessions Check: {len(missing_result.get('potential_issues', []))} potential issues")
        
    asyncio.run(test_validator())
