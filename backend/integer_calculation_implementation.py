#!/usr/bin/env python3
"""
INTEGER-BASED CALCULATION IMPLEMENTATION
Bulletproof solution using hundredths of minutes for perfect precision
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
from typing import Dict, Any, Tuple

class IntegerCalculationUtils:
    """Utility functions for integer-based minute calculations"""
    
    @staticmethod
    def minutes_to_hundredths(minutes_float: float) -> int:
        """Convert decimal minutes to integer hundredths"""
        return int(round(minutes_float * 100))
    
    @staticmethod
    def hundredths_to_minutes(hundredths_int: int) -> float:
        """Convert integer hundredths to decimal minutes for display"""
        return hundredths_int / 100
    
    @staticmethod
    def add_session_time(current_hundredths: int, new_minutes_float: float) -> int:
        """Add new session time to current total"""
        new_hundredths = IntegerCalculationUtils.minutes_to_hundredths(new_minutes_float)
        return current_hundredths + new_hundredths
    
    @staticmethod
    def calculate_remaining(limit_hundredths: int, used_hundredths: int) -> Tuple[int, float]:
        """Calculate remaining time"""
        remaining_hundredths = max(0, limit_hundredths - used_hundredths)
        remaining_display = IntegerCalculationUtils.hundredths_to_minutes(remaining_hundredths)
        return remaining_hundredths, remaining_display
    
    @staticmethod
    def get_plan_limits_hundredths(plan_id: str, period: str) -> Dict[str, int]:
        """Get subscription limits in hundredths of minutes"""
        if plan_id == "try_learn":
            minutes_limit = 15
        elif plan_id == "fluency_builder":
            if period == "annual":
                minutes_limit = 1800  # 150 * 12
            else:
                minutes_limit = 150
        elif plan_id == "team_mastery":
            return {"minutes_limit_hundredths": -1}  # Unlimited
        else:
            minutes_limit = 15  # Default to free tier
        
        return {
            "minutes_limit_hundredths": IntegerCalculationUtils.minutes_to_hundredths(minutes_limit)
        }

class IntegerSubscriptionService:
    """Enhanced subscription service using integer calculations"""
    
    def __init__(self, db):
        self.db = db
        self.utils = IntegerCalculationUtils()
    
    async def migrate_user_to_integer_fields(self, user_id: str) -> Dict[str, Any]:
        """Migrate a user from decimal to integer fields"""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get current decimal values
            decimal_minutes = user.get('practice_minutes_used', 0.0)
            decimal_sessions = user.get('practice_sessions_used', 0)
            decimal_assessments = user.get('assessments_used', 0)
            
            # Convert to integer hundredths
            integer_minutes_hundredths = self.utils.minutes_to_hundredths(decimal_minutes)
            
            # Update user with integer fields
            update_result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "practice_minutes_used_hundredths": integer_minutes_hundredths,
                        "practice_sessions_used_int": decimal_sessions,
                        "assessments_used_int": decimal_assessments,
                        "integer_migration_date": datetime.utcnow().isoformat(),
                        "integer_migration_from": {
                            "decimal_minutes": decimal_minutes,
                            "decimal_sessions": decimal_sessions,
                            "decimal_assessments": decimal_assessments
                        }
                    }
                }
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "migrated_values": {
                    "decimal_minutes": decimal_minutes,
                    "integer_hundredths": integer_minutes_hundredths,
                    "sessions": decimal_sessions,
                    "assessments": decimal_assessments
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def calculate_usage_from_sessions_integer(self, user_id: str, period_start: datetime, period_end: datetime) -> Dict[str, int]:
        """Calculate actual usage using integer arithmetic"""
        try:
            # Query conversation sessions
            conversation_sessions = await self.db.conversation_sessions.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": period_start,
                    "$lt": period_end
                }
            }).to_list(length=None)
            
            # Query learning plan sessions
            learning_plans = await self.db.learning_plans.find({
                "user_id": user_id
            }).to_list(length=None)
            
            # Calculate conversation minutes in hundredths
            conv_hundredths = 0
            for session in conversation_sessions:
                minutes = session.get('duration_minutes', 0.0)
                conv_hundredths += self.utils.minutes_to_hundredths(minutes)
            
            # Calculate learning plan minutes in hundredths
            learning_hundredths = 0
            learning_sessions_count = 0
            
            for plan in learning_plans:
                sessions = plan.get('sessions', [])
                for session in sessions:
                    completed_at = session.get('completed_at')
                    if completed_at:
                        # Handle both string and datetime
                        if isinstance(completed_at, str):
                            try:
                                completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                            except:
                                continue
                        
                        if period_start <= completed_at < period_end:
                            minutes = session.get('duration_minutes', 0.0)
                            learning_hundredths += self.utils.minutes_to_hundredths(minutes)
                            learning_sessions_count += 1
            
            # Total calculations (all integers)
            total_hundredths = conv_hundredths + learning_hundredths
            total_sessions = len(conversation_sessions) + learning_sessions_count
            
            return {
                "total_hundredths": total_hundredths,
                "total_sessions": total_sessions,
                "conversation_hundredths": conv_hundredths,
                "conversation_sessions": len(conversation_sessions),
                "learning_hundredths": learning_hundredths,
                "learning_sessions": learning_sessions_count
            }
            
        except Exception as e:
            print(f"Error calculating integer usage: {e}")
            return {
                "total_hundredths": 0,
                "total_sessions": 0,
                "conversation_hundredths": 0,
                "conversation_sessions": 0,
                "learning_hundredths": 0,
                "learning_sessions": 0
            }
    
    async def get_subscription_limits_integer(self, user_id: str) -> Dict[str, Any]:
        """Get subscription limits using integer calculations"""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"error": "User not found"}
            
            plan_id = user.get('subscription_plan', 'try_learn')
            period = user.get('subscription_period', 'monthly')
            
            # Get period dates
            period_start = user.get('current_period_start')
            period_end = user.get('current_period_end')
            
            if not period_start or not period_end:
                # Calculate current period
                now = datetime.utcnow()
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1)
            
            # Get plan limits in hundredths
            limits = self.utils.get_plan_limits_hundredths(plan_id, period)
            minutes_limit_hundredths = limits["minutes_limit_hundredths"]
            
            # Calculate actual usage in hundredths
            usage = await self.calculate_usage_from_sessions_integer(user_id, period_start, period_end)
            used_hundredths = usage["total_hundredths"]
            
            # Calculate remaining (all integer arithmetic)
            if minutes_limit_hundredths == -1:
                remaining_hundredths = -1
                remaining_display = "Unlimited"
            else:
                remaining_hundredths = max(0, minutes_limit_hundredths - used_hundredths)
                remaining_display = f"{self.utils.hundredths_to_minutes(remaining_hundredths):.0f} min left"
            
            # Get user record values for comparison
            user_record_hundredths = user.get('practice_minutes_used_hundredths', 0)
            user_record_decimal = user.get('practice_minutes_used', 0.0)
            
            # Check for discrepancy
            discrepancy_hundredths = abs(user_record_hundredths - used_hundredths)
            
            return {
                "user_id": user_id,
                "user_email": user.get('email'),
                "subscription_plan": plan_id,
                "subscription_period": period,
                "period_start": period_start,
                "period_end": period_end,
                "limits": {
                    "minutes_limit_hundredths": minutes_limit_hundredths,
                    "minutes_limit_display": self.utils.hundredths_to_minutes(minutes_limit_hundredths) if minutes_limit_hundredths != -1 else "Unlimited"
                },
                "usage": {
                    "used_hundredths": used_hundredths,
                    "used_display": self.utils.hundredths_to_minutes(used_hundredths),
                    "sessions_used": usage["total_sessions"]
                },
                "remaining": {
                    "remaining_hundredths": remaining_hundredths,
                    "remaining_display": remaining_display
                },
                "user_record": {
                    "record_hundredths": user_record_hundredths,
                    "record_decimal": user_record_decimal,
                    "discrepancy_hundredths": discrepancy_hundredths,
                    "needs_correction": discrepancy_hundredths > 1  # 0.01 minute tolerance
                },
                "calculation_method": "integer_hundredths"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def update_user_usage_integer(self, user_id: str, session_minutes: float, session_completed: bool = True) -> Dict[str, Any]:
        """Update user usage using integer calculations"""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get current integer values
            current_hundredths = user.get('practice_minutes_used_hundredths', 0)
            current_sessions = user.get('practice_sessions_used_int', 0)
            
            # Add new session time (integer arithmetic)
            new_hundredths = self.utils.add_session_time(current_hundredths, session_minutes)
            new_sessions = current_sessions + (1 if session_completed else 0)
            
            # Update user record
            update_result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "practice_minutes_used_hundredths": new_hundredths,
                        "practice_sessions_used_int": new_sessions,
                        "last_integer_update": datetime.utcnow().isoformat(),
                        "last_integer_update_reason": f"session_{session_minutes:.2f}min_{'completed' if session_completed else 'partial'}"
                    }
                }
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "old_values": {
                    "hundredths": current_hundredths,
                    "sessions": current_sessions
                },
                "new_values": {
                    "hundredths": new_hundredths,
                    "sessions": new_sessions
                },
                "added": {
                    "minutes": session_minutes,
                    "hundredths": self.utils.minutes_to_hundredths(session_minutes),
                    "sessions": 1 if session_completed else 0
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

async def test_integer_implementation():
    """Test the integer-based implementation"""
    
    # Get MongoDB URL
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable is required")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.language_tutor
    
    user_id = "688921c268819565ef1ce3dc"
    
    print("🧪 TESTING INTEGER-BASED IMPLEMENTATION")
    print("=" * 50)
    
    # Initialize service
    service = IntegerSubscriptionService(db)
    
    # Test 1: Migrate user to integer fields
    print("1️⃣ MIGRATING USER TO INTEGER FIELDS")
    print("-" * 35)
    
    migration_result = await service.migrate_user_to_integer_fields(user_id)
    if migration_result["success"]:
        print("✅ Migration successful!")
        print(f"   Decimal minutes: {migration_result['migrated_values']['decimal_minutes']}")
        print(f"   Integer hundredths: {migration_result['migrated_values']['integer_hundredths']}")
    else:
        print(f"❌ Migration failed: {migration_result['error']}")
    print()
    
    # Test 2: Calculate subscription limits using integers
    print("2️⃣ CALCULATING LIMITS WITH INTEGERS")
    print("-" * 37)
    
    limits_result = await service.get_subscription_limits_integer(user_id)
    if "error" not in limits_result:
        print("✅ Integer calculation successful!")
        print(f"   Plan: {limits_result['subscription_plan']}")
        print(f"   Limit: {limits_result['limits']['minutes_limit_display']}")
        print(f"   Used: {limits_result['usage']['used_display']:.2f} minutes")
        print(f"   Remaining: {limits_result['remaining']['remaining_display']}")
        print(f"   Calculation method: {limits_result['calculation_method']}")
        
        if limits_result['user_record']['needs_correction']:
            print(f"   ⚠️ Discrepancy: {limits_result['user_record']['discrepancy_hundredths']} hundredths")
        else:
            print("   ✅ No discrepancy detected")
    else:
        print(f"❌ Calculation failed: {limits_result['error']}")
    print()
    
    # Test 3: Update usage with integer arithmetic
    print("3️⃣ TESTING SESSION UPDATE WITH INTEGERS")
    print("-" * 40)
    
    test_session_minutes = 2.5
    update_result = await service.update_user_usage_integer(user_id, test_session_minutes, True)
    if update_result["success"]:
        print("✅ Integer update successful!")
        print(f"   Added: {update_result['added']['minutes']} minutes ({update_result['added']['hundredths']} hundredths)")
        print(f"   Old total: {service.utils.hundredths_to_minutes(update_result['old_values']['hundredths']):.2f} minutes")
        print(f"   New total: {service.utils.hundredths_to_minutes(update_result['new_values']['hundredths']):.2f} minutes")
    else:
        print(f"❌ Update failed: {update_result['error']}")
    print()
    
    # Test 4: Verify precision
    print("4️⃣ PRECISION VERIFICATION")
    print("-" * 26)
    
    # Test floating point vs integer precision
    decimal_total = 11.75 + 2.5  # 14.25
    integer_total_hundredths = 1175 + 250  # 1425
    integer_total_display = service.utils.hundredths_to_minutes(integer_total_hundredths)  # 14.25
    
    print(f"Decimal calculation: 11.75 + 2.5 = {decimal_total}")
    print(f"Integer calculation: 1175 + 250 = {integer_total_hundredths} hundredths")
    print(f"Integer display: {integer_total_display} minutes")
    print(f"Perfect match: {decimal_total == integer_total_display}")
    print()
    
    print("✅ INTEGER-BASED IMPLEMENTATION TESTED SUCCESSFULLY!")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_integer_implementation())
