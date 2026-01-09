"""
Upgrade Service - Handles subscription upgrades with proper period and usage management
"""

from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
import stripe
import logging
import os

from database import database

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class UpgradeService:
    """Manage subscription upgrades and conversions"""
    
    # Plan configurations
    PLAN_CONFIGS = {
        "fluency_builder_monthly": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_FLUENCY_BUILDER_MONTHLY", "price_1RdxNjJcquSiYwWN2XQMwwYW"),
            "minutes": 150,
            "period": "monthly"
        },
        "fluency_builder_annual": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_FLUENCY_BUILDER_YEARLY", "price_1RdxNjJcquSiYwWNIpmYrKSE"),
            "minutes": 1800,
            "period": "annual"
        },
        "language_mastery_monthly": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_LANGUAGE_MASTERY_MONTHLY", "price_1RdxlGJcquSiYwWNWvyEgmgL"),
            "minutes": -1,  # Unlimited
            "period": "monthly"
        },
        "language_mastery_annual": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_LANGUAGE_MASTERY_YEARLY", "price_1RdxmRJcquSiYwWN7Oc6NnNe"),
            "minutes": -1,  # Unlimited
            "period": "annual"
        },
        # Backward compatibility for old plan names
        "team_mastery_monthly": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_MONTHLY", "price_1RdxlGJcquSiYwWNWvyEgmgL"),
            "minutes": -1,  # Unlimited
            "period": "monthly"
        },
        "team_mastery_annual": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_YEARLY", "price_1RdxmRJcquSiYwWN7Oc6NnNe"),
            "minutes": -1,  # Unlimited
            "period": "annual"
        }
    }
    
    @staticmethod
    async def get_upgrade_options(user_id: str) -> dict:
        """
        Get available upgrade options for user
        
        Business Logic:
        - Show annual upgrade if on monthly plan
        - Show Team Mastery upgrade if on Fluency Builder
        - Always show "Wait for renewal" option
        """
        
        logger.info(f"[UPGRADE] Getting upgrade options for user {user_id}")
        
        # Get user data
        user = await database["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_plan = user.get("subscription_plan", "try_learn")
        current_period = user.get("subscription_period", "monthly")
        minutes_used = user.get("practice_minutes_used", 0)
        
        # Calculate minutes limit based on plan
        if current_plan == "try_learn":
            minutes_limit = 15
        elif current_plan == "fluency_builder":
            minutes_limit = 150 if current_period == "monthly" else 1800
        elif current_plan == "team_mastery":
            minutes_limit = -1  # Unlimited
        else:
            minutes_limit = 0
            
        minutes_remaining = max(0, minutes_limit - minutes_used) if minutes_limit != -1 else -1
        
        # Calculate days until renewal
        renewal_date = user.get("current_period_end")
        if renewal_date:
            days_until_renewal = (renewal_date - datetime.utcnow()).days
        else:
            days_until_renewal = 0
        
        options = []
        
        # ========================================
        # OPTION 1: Upgrade to Annual (if on monthly)
        # ========================================
        if current_period == "monthly" and current_plan == "fluency_builder":
            options.append({
                "type": "upgrade_to_annual",
                "title": "Upgrade to Annual Plan (Save 17%)",
                "current_price": 19.99,
                "new_price": 16.66,  # €199.99/12
                "annual_total": 199.99,
                "savings_amount": 40.00,  # (19.99 * 12) - 199.99
                "savings_percentage": 17,
                "immediate_benefit": "Get 1,800 minutes for the next 12 months",
                "features": [
                    "€16.66/month effective rate",
                    "1,800 minutes total per year",
                    "Save €40 vs monthly payments",
                    "Locked-in pricing for 12 months",
                    "Fresh start - usage resets to 0"
                ],
                "stripe_price_id": UpgradeService.PLAN_CONFIGS["fluency_builder_annual"]["price_id"],
                "recommended": True
            })
        
        # ========================================
        # OPTION 2: Upgrade to Team Mastery
        # ========================================
        if current_plan == "fluency_builder":
            team_price = 39.99 if current_period == "monthly" else 399.99
            team_price_id = UpgradeService.PLAN_CONFIGS[f"team_mastery_{current_period}"]["price_id"]
            
            options.append({
                "type": "upgrade_to_team_mastery",
                "title": f"Upgrade to Team Mastery {current_period.title()}",
                "current_price": 19.99 if current_period == "monthly" else 199.99,
                "new_price": team_price,
                "price_difference": team_price - (19.99 if current_period == "monthly" else 199.99),
                "immediate_benefit": "UNLIMITED minutes starting now",
                "features": [
                    "Unlimited practice sessions",
                    "Unlimited speaking assessments",
                    "Priority support",
                    "Advanced analytics",
                    "Early access to new features"
                ],
                "stripe_price_id": team_price_id,
                "recommended": False
            })
        
        # ========================================
        # OPTION 3: Wait for renewal
        # ========================================
        options.append({
            "type": "wait_renewal",
            "title": "Wait Until Next Billing Cycle",
            "renewal_date": renewal_date.isoformat() if renewal_date else None,
            "days_remaining": days_until_renewal,
            "new_minutes_on_renewal": minutes_limit if minutes_limit != -1 else 0,
            "immediate_benefit": f"Your subscription renews in {days_until_renewal} days",
            "features": [
                f"New cycle starts: {renewal_date.strftime('%B %d, %Y') if renewal_date else 'Unknown'}",
                f"You'll receive: {minutes_limit} fresh minutes" if minutes_limit != -1 else "Unlimited minutes continue",
                "Current plan continues unchanged",
                "No action required"
            ],
            "recommended": False
        })
        
        return {
            "current_plan": {
                "name": f"{current_plan.replace('_', ' ').title()} {current_period.title()}",
                "price": 19.99 if current_period == "monthly" else 199.99,
                "billing_period": current_period,
                "minutes_total": minutes_limit,
                "minutes_used": minutes_used,
                "minutes_remaining": minutes_remaining,
                "renewal_date": renewal_date.isoformat() if renewal_date else None,
                "days_until_renewal": days_until_renewal
            },
            "upgrade_options": options
        }
    
    @staticmethod
    async def process_upgrade(
        user_id: str,
        upgrade_type: str,
        new_price_id: str
    ) -> dict:
        """
        Process subscription upgrade with proper handling of:
        - Period dates (keep or reset based on upgrade type)
        - Usage counters (always reset to 0)
        - Stripe subscription modification
        - Database updates
        
        Business Rules:
        1. Monthly → Annual: Reset period to NOW, 12 months from now
        2. Fluency → Team Mastery (same cycle): KEEP period dates
        3. Always reset usage counters
        4. No proration charges (users have 0 minutes typically)
        """
        
        try:
            logger.info(f"[UPGRADE] Processing upgrade for user {user_id}: {upgrade_type}")
            logger.info(f"[UPGRADE] New price ID: {new_price_id}")
            
            # Get user data
            user = await database["users"].find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            stripe_customer_id = user.get("stripe_customer_id")
            if not stripe_customer_id:
                raise HTTPException(status_code=400, detail="No Stripe customer ID found")
            
            current_plan = user.get("subscription_plan", "try_learn")
            current_period = user.get("subscription_period", "monthly")
            current_period_start = user.get("current_period_start")
            current_period_end = user.get("current_period_end")
            
            # Get current subscription from Stripe
            subscriptions = stripe.Subscription.list(
                customer=stripe_customer_id,
                status="active",
                limit=1
            )
            
            if not subscriptions.data:
                raise HTTPException(status_code=400, detail="No active subscription found")
            
            current_subscription = subscriptions.data[0]
            
            # ========================================
            # DETERMINE NEW PLAN DETAILS
            # ========================================
            new_plan = None
            new_period = None
            keep_current_period = False
            
            if upgrade_type == "upgrade_to_annual":
                # Monthly → Annual: New 12-month period starts NOW
                new_plan = "fluency_builder"
                new_period = "annual"
                keep_current_period = False
                
            elif upgrade_type == "upgrade_to_team_mastery":
                # Fluency → Team Mastery: KEEP current period
                new_plan = "team_mastery"
                new_period = current_period  # Stay on same billing cycle
                keep_current_period = True
            
            logger.info(f"[UPGRADE] New plan: {new_plan}, New period: {new_period}")
            logger.info(f"[UPGRADE] Keep current period: {keep_current_period}")
            
            # ========================================
            # UPDATE STRIPE SUBSCRIPTION
            # ========================================
            logger.info(f"[UPGRADE] Modifying Stripe subscription: {current_subscription.id}")
            
            # Modify subscription
            updated_subscription = stripe.Subscription.modify(
                current_subscription.id,
                items=[{
                    "id": current_subscription.items.data[0].id,
                    "price": new_price_id,
                }],
                # IMPORTANT: No proration for our use case
                # Users typically have 0 minutes when upgrading
                proration_behavior="none",
            )
            
            logger.info(f"[UPGRADE] Stripe subscription updated successfully")
            
            # ========================================
            # CALCULATE NEW PERIOD DATES
            # ========================================
            if keep_current_period:
                # Keep existing period dates (Fluency → Team Mastery)
                new_period_start = current_period_start
                new_period_end = current_period_end
                logger.info(f"[UPGRADE] Keeping current period: {new_period_start} to {new_period_end}")
            else:
                # Use new period from Stripe (Monthly → Annual)
                new_period_start = datetime.fromtimestamp(
                    updated_subscription.current_period_start
                )
                new_period_end = datetime.fromtimestamp(
                    updated_subscription.current_period_end
                )
                logger.info(f"[UPGRADE] New period from Stripe: {new_period_start} to {new_period_end}")
            
            # ========================================
            # PREPARE DATABASE UPDATE
            # ========================================
            now = datetime.utcnow()
            
            db_update = {
                # Subscription details
                "subscription_plan": new_plan,
                "subscription_period": new_period,
                "subscription_price_id": new_price_id,
                
                # Period dates
                "current_period_start": new_period_start,
                "current_period_end": new_period_end,
                
                # CRITICAL: Reset all usage counters to 0
                "practice_minutes_used": 0,
                "practice_sessions_used": 0,
                "assessments_used": 0,
                
                # Tracking
                "last_upgrade_date": now,
            }
            
            # Create upgrade history record
            upgrade_record = {
                "from_plan": f"{current_plan}_{current_period}",
                "to_plan": f"{new_plan}_{new_period}",
                "upgraded_at": now,
                "reason": "user_initiated_upgrade",
                "period_kept": keep_current_period,
                "usage_reset": True
            }
            
            # ========================================
            # UPDATE DATABASE
            # ========================================
            await database["users"].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": db_update,
                    "$push": {"upgrade_history": upgrade_record}
                }
            )
            
            logger.info(f"[UPGRADE] Successfully upgraded user {user_id} to {new_plan} ({new_period})")
            logger.info(f"[UPGRADE] Usage counters reset to 0")
            
            # Calculate minutes total
            if new_plan == "team_mastery":
                minutes_total = -1  # Unlimited
            elif new_period == "annual":
                minutes_total = 1800
            else:
                minutes_total = 150
            
            # ========================================
            # PREPARE RESPONSE
            # ========================================
            return {
                "success": True,
                "subscription_id": updated_subscription.id,
                "new_plan": new_plan,
                "new_period": new_period,
                "period_start": new_period_start.isoformat(),
                "period_end": new_period_end.isoformat(),
                "usage_reset": True,
                "period_kept": keep_current_period,
                "minutes_total": minutes_total,
                "unlimited": new_plan == "team_mastery"
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"[UPGRADE] Stripe error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"[UPGRADE] Error processing upgrade: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
