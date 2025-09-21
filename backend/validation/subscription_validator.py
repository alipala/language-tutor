#!/usr/bin/env python3
"""
Subscription Period Validator
Validates subscription periods and detects inconsistencies to prevent dashboard bugs
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from database import database
from bson import ObjectId

logger = logging.getLogger(__name__)

class SubscriptionValidator:
    """Validates subscription data to prevent dashboard calculation errors"""
    
    @staticmethod
    async def validate_subscription_period(user_id: str) -> Dict[str, Any]:
        """
        Validate that user's subscription period is properly set
        Returns validation result with any issues found
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
            
            validation_result = {
                "is_valid": True,
                "user_id": user_id,
                "user_email": user.get("email", "unknown"),
                "issues": [],
                "warnings": [],
                "corrections_needed": [],
                "period_info": {}
            }
            
            # Check if subscription period dates exist
            period_start = user.get("current_period_start")
            period_end = user.get("current_period_end")
            subscription_plan = user.get("subscription_plan", "try_learn")
            
            validation_result["period_info"] = {
                "period_start": period_start,
                "period_end": period_end,
                "subscription_plan": subscription_plan
            }
            
            # Validation 1: Check if period dates exist
            if not period_start or not period_end:
                validation_result["issues"].append("Missing subscription period dates")
                validation_result["corrections_needed"].append("set_subscription_period")
                validation_result["is_valid"] = False
            
            # Validation 2: Check if period dates are reasonable
            if period_start and period_end:
                now = datetime.utcnow()
                
                # Check if period is in the past
                if period_end < now - timedelta(days=32):  # More than 32 days ago
                    validation_result["issues"].append("Subscription period is too far in the past")
                    validation_result["corrections_needed"].append("update_subscription_period")
                
                # Check if period is too far in the future
                if period_start > now + timedelta(days=400):  # More than ~13 months in future
                    validation_result["warnings"].append("Subscription period starts far in the future")
                
                # Check period length
                period_length = (period_end - period_start).days
                if period_length < 25:  # Less than 25 days (monthly should be ~30)
                    validation_result["warnings"].append(f"Period length is short: {period_length} days")
                elif period_length > 400:  # More than ~13 months (annual should be ~365)
                    validation_result["warnings"].append(f"Period length is long: {period_length} days")
            
            # Validation 3: Check subscription status consistency
            subscription_status = user.get("subscription_status")
            subscription_expires_at = user.get("subscription_expires_at")
            
            if subscription_status == "active" and subscription_expires_at:
                if subscription_expires_at < datetime.utcnow():
                    validation_result["issues"].append("Subscription marked active but expiry date is in the past")
                    validation_result["corrections_needed"].append("update_subscription_status")
                    validation_result["is_valid"] = False
            
            # Validation 4: Check Stripe customer ID exists for paid plans
            if subscription_plan != "try_learn":
                stripe_customer_id = user.get("stripe_customer_id")
                if not stripe_customer_id:
                    validation_result["warnings"].append("Paid plan without Stripe customer ID")
            
            logger.info(f"[VALIDATION] Subscription validation for {user.get('email', user_id)}: "
                       f"{'✅ Valid' if validation_result['is_valid'] else '❌ Invalid'}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"[VALIDATION] Error validating subscription period: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e),
                "user_id": user_id
            }
    
    @staticmethod
    async def validate_period_boundaries(user_id: str) -> Dict[str, Any]:
        """
        Validate that current date falls properly within subscription boundaries
        """
        try:
            validation_result = await SubscriptionValidator.validate_subscription_period(user_id)
            
            if not validation_result.get("is_valid"):
                return validation_result
            
            period_info = validation_result["period_info"]
            period_start = period_info["period_start"]
            period_end = period_info["period_end"]
            now = datetime.utcnow()
            
            boundary_validation = {
                "is_valid": True,
                "user_id": user_id,
                "current_time": now,
                "period_start": period_start,
                "period_end": period_end,
                "is_within_period": False,
                "days_into_period": None,
                "days_until_end": None,
                "boundary_issues": []
            }
            
            if period_start and period_end:
                # Check if current time is within period
                if period_start <= now <= period_end:
                    boundary_validation["is_within_period"] = True
                    boundary_validation["days_into_period"] = (now - period_start).days
                    boundary_validation["days_until_end"] = (period_end - now).days
                else:
                    boundary_validation["is_valid"] = False
                    
                    if now < period_start:
                        boundary_validation["boundary_issues"].append("Current time is before period start")
                    elif now > period_end:
                        boundary_validation["boundary_issues"].append("Current time is after period end")
            
            return boundary_validation
            
        except Exception as e:
            logger.error(f"[VALIDATION] Error validating period boundaries: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e),
                "user_id": user_id
            }
    
    @staticmethod
    async def auto_fix_subscription_period(user_id: str) -> Dict[str, Any]:
        """
        Automatically fix common subscription period issues
        """
        try:
            validation_result = await SubscriptionValidator.validate_subscription_period(user_id)
            
            if validation_result.get("is_valid"):
                return {
                    "fixes_applied": False,
                    "message": "No fixes needed - subscription period is valid"
                }
            
            fixes_applied = []
            corrections_needed = validation_result.get("corrections_needed", [])
            
            # Get user data again
            try:
                user_object_id = ObjectId(user_id)
                query = {"_id": user_object_id}
            except:
                query = {"_id": user_id}
            
            user = await database["users"].find_one(query)
            if not user:
                return {"fixes_applied": False, "error": "User not found"}
            
            update_fields = {}
            now = datetime.utcnow()
            
            # Fix 1: Set missing subscription period
            if "set_subscription_period" in corrections_needed:
                subscription_plan = user.get("subscription_plan", "try_learn")
                
                # Calculate appropriate period based on plan and current date
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                if subscription_plan == "fluency_builder" or subscription_plan == "team_mastery":
                    # Monthly subscription
                    if period_start.month == 12:
                        period_end = period_start.replace(year=period_start.year + 1, month=1)
                    else:
                        period_end = period_start.replace(month=period_start.month + 1)
                else:
                    # Free plan - use current month
                    if period_start.month == 12:
                        period_end = period_start.replace(year=period_start.year + 1, month=1)
                    else:
                        period_end = period_start.replace(month=period_start.month + 1)
                
                update_fields["current_period_start"] = period_start
                update_fields["current_period_end"] = period_end
                update_fields["subscription_expires_at"] = period_end
                
                fixes_applied.append(f"Set subscription period: {period_start.date()} to {period_end.date()}")
            
            # Fix 2: Update subscription status for expired subscriptions
            if "update_subscription_status" in corrections_needed:
                subscription_expires_at = user.get("subscription_expires_at")
                if subscription_expires_at and subscription_expires_at < now:
                    update_fields["subscription_status"] = "expired"
                    fixes_applied.append("Updated subscription status to 'expired'")
            
            # Apply fixes if any
            if update_fields:
                update_fields["last_validation_fix"] = now.isoformat()
                update_fields["validation_fix_reason"] = "auto_fix_subscription_period"
                
                result = await database["users"].update_one(query, {"$set": update_fields})
                
                if result.modified_count > 0:
                    logger.info(f"[VALIDATION] Applied subscription fixes for user {user.get('email', user_id)}: {fixes_applied}")
                    return {
                        "fixes_applied": True,
                        "fixes": fixes_applied,
                        "update_fields": update_fields
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
            logger.error(f"[VALIDATION] Error auto-fixing subscription period: {str(e)}")
            return {
                "fixes_applied": False,
                "error": str(e)
            }

if __name__ == "__main__":
    # Test the validator
    import asyncio
    
    async def test_validator():
        user_id = "688921c268819565ef1ce3dc"
        
        print("🧪 TESTING SUBSCRIPTION VALIDATOR")
        print("=" * 50)
        
        # Test period validation
        result = await SubscriptionValidator.validate_subscription_period(user_id)
        print(f"✅ Period Validation: {'Valid' if result['is_valid'] else 'Invalid'}")
        if result.get('issues'):
            print(f"   Issues: {result['issues']}")
        if result.get('warnings'):
            print(f"   Warnings: {result['warnings']}")
        
        # Test boundary validation  
        boundary_result = await SubscriptionValidator.validate_period_boundaries(user_id)
        print(f"✅ Boundary Validation: {'Valid' if boundary_result['is_valid'] else 'Invalid'}")
        print(f"   Within Period: {boundary_result.get('is_within_period', False)}")
        
    asyncio.run(test_validator())
