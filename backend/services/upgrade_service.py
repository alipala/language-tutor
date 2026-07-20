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
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_FLUENCY_BUILDER_YEARLY", "price_1SoQw4JcquSiYwWNzi2zSgXt"),
            "minutes": 1800,
            "period": "annual"
        },
        "language_mastery_monthly": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_MONTHLY", "price_1RdxlGJcquSiYwWNWvyEgmgL"),
            "minutes": -1,  # Unlimited
            "period": "monthly"
        },
        "language_mastery_annual": {
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_YEARLY", "price_1SoQy8JcquSiYwWNalBlWPEQ"),
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
            "price_id": os.getenv("NEXT_PUBLIC_STRIPE_PRICE_TEAM_MASTERY_YEARLY", "price_1SoQy8JcquSiYwWNalBlWPEQ"),
            "minutes": -1,  # Unlimited
            "period": "annual"
        }
    }

    @staticmethod
    def _price_amount(price_id: str) -> float | None:
        """Return a Stripe price's amount in major units (e.g. 59.99), or None.

        Prices are read LIVE from Stripe so displayed amounts never drift from the
        real billing amount (the previous hardcoded 199.99/39.99 values were wrong).
        """
        try:
            price = stripe.Price.retrieve(price_id)
            amount = price.get("unit_amount")
            if amount is None:
                return None
            return round(amount / 100.0, 2)
        except Exception as e:
            logger.warning(f"[UPGRADE] Could not read price {price_id} from Stripe: {e}")
            return None

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

        # Normalize the legacy "team_mastery" plan id to "language_mastery" for logic.
        is_language_mastery = current_plan in ("language_mastery", "team_mastery")

        # Calculate minutes limit based on plan
        if current_plan == "try_learn":
            minutes_limit = 15
        elif current_plan == "fluency_builder":
            minutes_limit = 150 if current_period == "monthly" else 1800
        elif is_language_mastery:
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

        # LIVE prices from Stripe (never hardcode — the old 199.99/39.99 were wrong).
        fb_monthly_price = UpgradeService._price_amount(UpgradeService.PLAN_CONFIGS["fluency_builder_monthly"]["price_id"])
        fb_annual_price = UpgradeService._price_amount(UpgradeService.PLAN_CONFIGS["fluency_builder_annual"]["price_id"])
        lm_monthly_price = UpgradeService._price_amount(UpgradeService.PLAN_CONFIGS["language_mastery_monthly"]["price_id"])
        lm_annual_price = UpgradeService._price_amount(UpgradeService.PLAN_CONFIGS["language_mastery_annual"]["price_id"])

        # Current plan's real price
        if current_plan == "fluency_builder":
            current_price = fb_monthly_price if current_period == "monthly" else fb_annual_price
        elif is_language_mastery:
            current_price = lm_monthly_price if current_period == "monthly" else lm_annual_price
        else:
            current_price = 0.0

        options = []

        # ========================================
        # OPTION: Upgrade monthly -> annual (SAME plan only)
        # Cross-plan (FB -> LM) is intentionally out of scope for now.
        # ========================================
        if current_period == "monthly" and current_plan == "fluency_builder" and fb_annual_price:
            monthly_year_cost = round((fb_monthly_price or 0) * 12, 2)
            savings_amount = round(monthly_year_cost - fb_annual_price, 2) if fb_monthly_price else None
            savings_pct = round(100 * savings_amount / monthly_year_cost) if (savings_amount and monthly_year_cost) else None
            effective_monthly = round(fb_annual_price / 12, 2)
            options.append({
                "type": "upgrade_to_annual",
                "title": f"Upgrade to Annual Plan" + (f" (Save {savings_pct}%)" if savings_pct else ""),
                "current_price": current_price,
                "new_price": effective_monthly,          # effective per-month rate
                "annual_total": fb_annual_price,
                "savings_amount": savings_amount,
                "savings_percentage": savings_pct,
                "immediate_benefit": "Get 1,800 minutes for the next 12 months",
                "features": [
                    f"€{effective_monthly}/month effective rate",
                    "1,800 minutes total per year",
                    (f"Save €{savings_amount} vs monthly payments" if savings_amount else "Best value"),
                    "Locked-in pricing for 12 months",
                    "Fresh start - usage resets to 0",
                ],
                "stripe_price_id": UpgradeService.PLAN_CONFIGS["fluency_builder_annual"]["price_id"],
                "recommended": True,
            })

        if current_period == "monthly" and is_language_mastery and lm_annual_price:
            monthly_year_cost = round((lm_monthly_price or 0) * 12, 2)
            savings_amount = round(monthly_year_cost - lm_annual_price, 2) if lm_monthly_price else None
            savings_pct = round(100 * savings_amount / monthly_year_cost) if (savings_amount and monthly_year_cost) else None
            effective_monthly = round(lm_annual_price / 12, 2)
            options.append({
                "type": "upgrade_to_language_mastery_annual",
                "title": f"Upgrade to Annual Plan" + (f" (Save {savings_pct}%)" if savings_pct else ""),
                "current_price": current_price,
                "new_price": effective_monthly,
                "annual_total": lm_annual_price,
                "savings_amount": savings_amount,
                "savings_percentage": savings_pct,
                "immediate_benefit": "Unlimited minutes for the next 12 months",
                "features": [
                    f"€{effective_monthly}/month effective rate",
                    "Unlimited minutes",
                    (f"Save €{savings_amount} vs monthly payments" if savings_amount else "Best value"),
                    "Locked-in pricing for 12 months",
                ],
                "stripe_price_id": UpgradeService.PLAN_CONFIGS["language_mastery_annual"]["price_id"],
                "recommended": True,
            })

        # ========================================
        # OPTION: Wait for renewal (always available)
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
                "price": current_price,
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
            
            # Get current subscription from Stripe — include trialing users.
            # IMPORTANT: fetch ALL subscriptions (not limit=1) and then filter, so we
            # never miss the live one when the most-recent subscription is canceled.
            subscriptions = stripe.Subscription.list(
                customer=stripe_customer_id,
                status="all",
                limit=100,
            )
            # Filter to active or trialing only
            active_subs = [s for s in subscriptions.data if s.status in ("active", "trialing")]

            if not active_subs:
                raise HTTPException(status_code=400, detail="No active or trialing subscription found")

            # If somehow more than one is active, prefer the most recently created so we
            # modify the subscription the user is actually paying on right now.
            current_subscription = max(active_subs, key=lambda s: s.get("created", 0))
            
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

            elif upgrade_type == "upgrade_to_language_mastery_monthly":
                # Any plan → Language Mastery Monthly: keep current period
                new_plan = "language_mastery"
                new_period = "monthly"
                keep_current_period = True

            elif upgrade_type == "upgrade_to_language_mastery_annual":
                # Any plan → Language Mastery Annual: new 12-month period
                new_plan = "language_mastery"
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
            
            # Get the subscription item ID — use dict access for SDK v11 compatibility
            sub_item_id = current_subscription["items"]["data"][0]["id"]
            logger.info(f"[UPGRADE] Subscription item ID: {sub_item_id}")

            # Modify subscription
            updated_subscription = stripe.Subscription.modify(
                current_subscription.id,
                items=[{
                    "id": sub_item_id,
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
                    updated_subscription["current_period_start"]
                )
                new_period_end = datetime.fromtimestamp(
                    updated_subscription["current_period_end"]
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
            if new_plan in ("team_mastery", "language_mastery"):
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
                "subscription_id": updated_subscription["id"],
                "new_plan": new_plan,
                "new_period": new_period,
                "period_start": new_period_start.isoformat(),
                "period_end": new_period_end.isoformat(),
                "usage_reset": True,
                "period_kept": keep_current_period,
                "minutes_total": minutes_total,
                "unlimited": new_plan in ("team_mastery", "language_mastery")
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"[UPGRADE] Stripe error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"[UPGRADE] Error processing upgrade: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
