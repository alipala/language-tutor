#!/usr/bin/env python3
"""
Subscription Service Dashboard Fix - Preventive Solution
This module enhances the subscription service to calculate usage from actual session data
rather than relying on potentially stale user record data.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging
from database import database
from bson import ObjectId

logger = logging.getLogger(__name__)

def get_user_query(user_id: str):
    """Helper function to handle both UUID and ObjectId formats"""
    try:
        return {"_id": ObjectId(user_id)}
    except:
        return {"_id": user_id}

class DashboardCalculationFix:
    """Enhanced dashboard calculation that prevents data discrepancies"""
    
    @staticmethod
    async def calculate_actual_usage_from_sessions(user_id: str, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """
        Calculate actual usage from session data in the current subscription period
        This is the source of truth for dashboard calculations
        """
        try:
            # Query conversation sessions in the current period
            conversation_sessions = await database["conversation_sessions"].find({
                "user_id": user_id,
                "created_at": {
                    "$gte": period_start,
                    "$lt": period_end
                }
            }).to_list(length=None)
            
            # Query learning plan sessions in the current period
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
            
            # Calculate totals
            conversation_minutes = sum(session.get("duration_minutes", 0.0) for session in conversation_sessions)
            conversation_count = len(conversation_sessions)
            
            total_minutes = conversation_minutes + learning_session_minutes
            total_sessions = conversation_count + learning_session_count
            
            return {
                "total_minutes": total_minutes,
                "total_sessions": total_sessions,
                "conversation_minutes": conversation_minutes,
                "conversation_sessions": conversation_count,
                "learning_minutes": learning_session_minutes,
                "learning_sessions": learning_session_count
            }
            
        except Exception as e:
            logger.error(f"Error calculating actual usage for user {user_id}: {str(e)}")
            return {
                "total_minutes": 0.0,
                "total_sessions": 0,
                "conversation_minutes": 0.0,
                "conversation_sessions": 0,
                "learning_minutes": 0.0,
                "learning_sessions": 0
            }
    
    @staticmethod
    async def get_dashboard_calculation_with_validation(user_id: str) -> Dict[str, Any]:
        """
        Get dashboard calculation with validation against actual session data
        This prevents the data discrepancy issue from recurring
        """
        try:
            # Get user data
            user = await database["users"].find_one(get_user_query(user_id))
            if not user:
                return {"error": "User not found"}
            
            # Get subscription period
            period_start = user.get("current_period_start")
            period_end = user.get("current_period_end")
            
            if not period_start or not period_end:
                # Calculate current period if not set
                now = datetime.utcnow()
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1)
            
            # Get actual usage from session data (source of truth)
            actual_usage = await DashboardCalculationFix.calculate_actual_usage_from_sessions(
                user_id, period_start, period_end
            )
            
            # Get user record data
            user_record_minutes = user.get("practice_minutes_used", 0.0)
            user_record_sessions = user.get("practice_sessions_used", 0)
            
            # Check for discrepancy
            minutes_discrepancy = abs(user_record_minutes - actual_usage["total_minutes"])
            sessions_discrepancy = abs(user_record_sessions - actual_usage["total_sessions"])
            
            has_discrepancy = minutes_discrepancy > 0.1 or sessions_discrepancy > 0  # 0.1 minute tolerance
            
            # Get subscription plan details
            plan_id = user.get("subscription_plan", "try_learn")
            
            # Calculate limits based on plan
            if plan_id == "try_learn":
                minutes_limit = 15
            elif plan_id == "fluency_builder":
                minutes_limit = 150
            elif plan_id == "team_mastery":
                minutes_limit = -1  # Unlimited
            else:
                minutes_limit = 15  # Default to free tier
            
            # Calculate remaining time using ACTUAL session data (not user record)
            if minutes_limit == -1:
                minutes_remaining = -1  # Unlimited
            else:
                minutes_remaining = max(0, minutes_limit - actual_usage["total_minutes"])
            
            return {
                "user_id": user_id,
                "user_email": user.get("email", "unknown"),
                "subscription_plan": plan_id,
                "period_start": period_start,
                "period_end": period_end,
                "minutes_limit": minutes_limit,
                "actual_usage": actual_usage,
                "user_record": {
                    "minutes_used": user_record_minutes,
                    "sessions_used": user_record_sessions
                },
                "dashboard_calculation": {
                    "minutes_remaining": minutes_remaining,
                    "minutes_used": actual_usage["total_minutes"],
                    "display_text": f"{minutes_remaining:.0f} min left" if minutes_remaining != -1 else "Unlimited"
                },
                "discrepancy_check": {
                    "has_discrepancy": has_discrepancy,
                    "minutes_discrepancy": minutes_discrepancy,
                    "sessions_discrepancy": sessions_discrepancy,
                    "needs_correction": has_discrepancy
                }
            }
            
        except Exception as e:
            logger.error(f"Error in dashboard calculation validation: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def auto_correct_user_record_if_needed(user_id: str) -> Dict[str, Any]:
        """
        Automatically correct user record if discrepancy is detected
        This prevents the dashboard from showing incorrect values
        """
        try:
            # Get dashboard calculation with validation
            calc_result = await DashboardCalculationFix.get_dashboard_calculation_with_validation(user_id)
            
            if "error" in calc_result:
                return calc_result
            
            # Check if correction is needed
            if not calc_result["discrepancy_check"]["needs_correction"]:
                return {
                    "correction_needed": False,
                    "message": "User record is accurate, no correction needed",
                    "dashboard_calculation": calc_result["dashboard_calculation"]
                }
            
            # Perform correction
            actual_minutes = calc_result["actual_usage"]["total_minutes"]
            actual_sessions = calc_result["actual_usage"]["total_sessions"]
            
            # Update user record to match actual session data
            update_result = await database["users"].update_one(
                get_user_query(user_id),
                {
                    "$set": {
                        "practice_minutes_used": actual_minutes,
                        "practice_sessions_used": actual_sessions,
                        "last_auto_correction": datetime.utcnow().isoformat(),
                        "auto_correction_reason": "dashboard_calculation_fix_preventive"
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"✅ Auto-corrected user record for {calc_result['user_email']}: "
                          f"{calc_result['user_record']['minutes_used']:.2f}→{actual_minutes:.2f} min, "
                          f"{calc_result['user_record']['sessions_used']}→{actual_sessions} sessions")
                
                return {
                    "correction_needed": True,
                    "correction_applied": True,
                    "old_values": calc_result["user_record"],
                    "new_values": {
                        "minutes_used": actual_minutes,
                        "sessions_used": actual_sessions
                    },
                    "dashboard_calculation": calc_result["dashboard_calculation"],
                    "message": f"User record corrected automatically. Dashboard now shows: {calc_result['dashboard_calculation']['display_text']}"
                }
            else:
                return {
                    "correction_needed": True,
                    "correction_applied": False,
                    "error": "Failed to update user record"
                }
                
        except Exception as e:
            logger.error(f"Error in auto-correction: {str(e)}")
            return {"error": str(e)}

# Enhanced subscription service method to replace the existing one
async def calculate_subscription_limits_with_validation(user_id: str, plan_id: str, period: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced version of _calculate_subscription_limits that validates against actual session data
    This prevents dashboard calculation discrepancies
    """
    try:
        # Get period dates
        period_start = user_data.get("current_period_start")
        period_end = user_data.get("current_period_end")
        
        if not period_start or not period_end:
            # Calculate current period if not set
            now = datetime.utcnow()
            if period == "annual":
                subscription_started = user_data.get("subscription_started_at")
                if subscription_started:
                    period_start = subscription_started
                    try:
                        period_end = period_start.replace(year=period_start.year + 1)
                    except ValueError:
                        period_end = period_start.replace(year=period_start.year + 1, month=2, day=28)
                else:
                    period_start = now
                    try:
                        period_end = period_start.replace(year=period_start.year + 1)
                    except ValueError:
                        period_end = period_start.replace(year=period_start.year + 1, month=2, day=28)
            else:
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1)
        
        # Get actual usage from session data (source of truth)
        actual_usage = await DashboardCalculationFix.calculate_actual_usage_from_sessions(
            user_id, period_start, period_end
        )
        
        # Get user record data for comparison
        user_record_minutes = user_data.get("practice_minutes_used", 0.0)
        user_record_sessions = user_data.get("practice_sessions_used", 0)
        
        # Check for discrepancy and auto-correct if needed
        minutes_discrepancy = abs(user_record_minutes - actual_usage["total_minutes"])
        if minutes_discrepancy > 0.1:  # 0.1 minute tolerance
            logger.warning(f"⚠️ Dashboard calculation discrepancy detected for user {user_id}: "
                         f"User record: {user_record_minutes:.2f} min, Actual: {actual_usage['total_minutes']:.2f} min")
            
            # Auto-correct the user record
            await database["users"].update_one(
                get_user_query(user_id),
                {
                    "$set": {
                        "practice_minutes_used": actual_usage["total_minutes"],
                        "practice_sessions_used": actual_usage["total_sessions"],
                        "last_auto_correction": datetime.utcnow().isoformat(),
                        "auto_correction_reason": "preventive_dashboard_fix"
                    }
                }
            )
            
            logger.info(f"✅ Auto-corrected user record for user {user_id}")
        
        # Calculate limits based on plan
        if plan_id == "try_learn":
            minutes_limit = 15
            sessions_limit = 3
        elif plan_id == "fluency_builder":
            minutes_limit = 150
            sessions_limit = 30
        elif plan_id == "team_mastery":
            minutes_limit = -1  # Unlimited
            sessions_limit = -1  # Unlimited
        else:
            minutes_limit = 15  # Default to free tier
            sessions_limit = 3
        
        # Use actual session data for calculations (not user record)
        minutes_used = actual_usage["total_minutes"]
        sessions_used = actual_usage["total_sessions"]
        
        # Calculate remaining
        minutes_remaining = minutes_limit - minutes_used if minutes_limit != -1 else -1
        sessions_remaining = sessions_limit - sessions_used if sessions_limit != -1 else -1
        
        return {
            "plan": plan_id,
            "period": period,
            "minutes_limit": minutes_limit,
            "sessions_limit": sessions_limit,
            "minutes_used": minutes_used,
            "sessions_used": sessions_used,
            "minutes_remaining": minutes_remaining,
            "sessions_remaining": sessions_remaining,
            "period_start": period_start,
            "period_end": period_end,
            "is_unlimited": (minutes_limit == -1),
            "data_source": "actual_sessions",  # Indicates this uses actual session data
            "discrepancy_corrected": minutes_discrepancy > 0.1
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced subscription limits calculation: {str(e)}")
        # Fallback to user record data if session calculation fails
        return {
            "error": str(e),
            "fallback": True,
            "minutes_used": user_data.get("practice_minutes_used", 0.0),
            "sessions_used": user_data.get("practice_sessions_used", 0)
        }

if __name__ == "__main__":
    # Test the dashboard calculation fix
    import asyncio
    
    async def test_dashboard_fix():
        user_id = "688921c268819565ef1ce3dc"
        
        print("🧪 TESTING DASHBOARD CALCULATION FIX")
        print("=" * 50)
        
        # Test dashboard calculation with validation
        result = await DashboardCalculationFix.get_dashboard_calculation_with_validation(user_id)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"👤 User: {result['user_email']}")
        print(f"📊 Plan: {result['subscription_plan']}")
        print(f"📅 Period: {result['period_start']} to {result['period_end']}")
        print(f"🎯 Actual Usage: {result['actual_usage']['total_minutes']:.2f} min, {result['actual_usage']['total_sessions']} sessions")
        print(f"📝 User Record: {result['user_record']['minutes_used']:.2f} min, {result['user_record']['sessions_used']} sessions")
        print(f"📊 Dashboard: {result['dashboard_calculation']['display_text']}")
        
        if result['discrepancy_check']['has_discrepancy']:
            print(f"⚠️ Discrepancy detected: {result['discrepancy_check']['minutes_discrepancy']:.2f} min difference")
            
            # Test auto-correction
            correction_result = await DashboardCalculationFix.auto_correct_user_record_if_needed(user_id)
            print(f"🔧 Auto-correction: {correction_result.get('message', 'No correction needed')}")
        else:
            print("✅ No discrepancy detected")
    
    asyncio.run(test_dashboard_fix())
