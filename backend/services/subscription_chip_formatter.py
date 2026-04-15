"""
Subscription Chip Formatter - Smart Subscription Card Display
==============================================================
Automatically detects when to show subscription chips in TaalCoach
and formats beautiful inline subscription cards.

Design: Clean white cards with solid color accents (NO GRADIENTS)
Inspired by existing PricingModal but adapted for inline chat display.
"""
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SubscriptionChipFormatter:
    """
    Formats TaalCoach responses with inline subscription chips.

    Shows beautiful subscription cards when users ask about pricing
    or when smart triggers detect high purchase intent.
    """

    def __init__(self):
        # Patterns that indicate subscription chips should be shown
        self.pricing_triggers = [
            # Direct pricing queries (HIGH INTENT - always show)
            r'\b(prices?|pricing|costs?|how much|rates?|fees?)\b',
            r'\b(premium|subscription|plans?|upgrade)\b',
            r'\b(fluency builder|language mastery|try.?learn)\b',
            r'\b(pay|payment|billing)\b',
            r'\b(free trial|trial period)\b',
            r'\b(annual|monthly|year)\b',

            # Comparison queries
            r'\b(compare|difference|between|vs|versus)\b.*\b(plan|subscription)\b',
            r'\b(which plan|what plan|best plan)\b',

            # Feature queries
            r'\b(unlimited|no limit|infinite)\b',
            r'\b(heart|hearts|refill)\b.*\b(how|what|when)\b',
        ]

        # Patterns that indicate user is NOT interested (skip chips)
        self.skip_patterns = [
            # Learning plan queries (NOT pricing queries)
            r'\blearning plans?\b',
            r'\bstudy plans?\b',
            r'\bcourse plans?\b',

            # Learning/educational queries
            r'\b(how to|teach me|explain|what does)\b.*\b(grammar|vocabulary)\b',
            r'\b(practice|session)\b.*\b(how|what|why|when)\b',
            r'\b(should i practice|what should|recommend)\b',

            # Challenge/feature explanations
            r'\b(what is|what are)\b.*\b(micro quiz|error spotting|challenge)\b',
        ]

    def should_show_subscription_chips(
        self,
        user_message: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Determine if subscription chips should be displayed.

        Returns:
            {
                "show": bool,
                "trigger": str,  # "pricing_query", "out_of_minutes", "comparison", etc.
                "display_mode": str,  # "comparison" or "single_highlight"
                "recommended_plan": str  # "fluency_builder_annual" or "language_mastery_annual"
            }
        """
        result = {
            "show": False,
            "trigger": None,
            "display_mode": "comparison",
            "recommended_plan": None
        }

        user_lower = user_message.lower()

        # Handle None conversation history
        if conversation_history is None:
            conversation_history = []

        # 1. Check if already shown in this conversation
        if any(msg.get('type') == 'subscription_chips' for msg in conversation_history):
            logger.info(f"[SUBSCRIPTION_CHIPS] Already shown in conversation, skipping")
            return result

        # 2. Check cooldown (from user context)
        last_shown = user_context.get('last_subscription_chip_shown_at')
        if last_shown:
            # Parse timestamp if string
            if isinstance(last_shown, str):
                try:
                    last_shown = datetime.fromisoformat(last_shown.replace('Z', '+00:00'))
                except:
                    last_shown = None

            if last_shown and datetime.utcnow() - last_shown < timedelta(hours=1):
                logger.info(f"[SUBSCRIPTION_CHIPS] Shown less than 1 hour ago, skipping")
                return result

        # 3. Check daily limit
        chips_today = user_context.get('subscription_chips_shown_today', 0)
        if chips_today >= 2:
            logger.info(f"[SUBSCRIPTION_CHIPS] Daily limit reached (2), skipping")
            return result

        # 4. Check if user dismissed recently
        last_dismissed = user_context.get('last_subscription_chip_dismissed_at')
        if last_dismissed:
            if isinstance(last_dismissed, str):
                try:
                    last_dismissed = datetime.fromisoformat(last_dismissed.replace('Z', '+00:00'))
                except:
                    last_dismissed = None

            if last_dismissed and datetime.utcnow() - last_dismissed < timedelta(days=7):
                logger.info(f"[SUBSCRIPTION_CHIPS] User dismissed within 7 days, skipping")
                return result

        # 5. Skip if user asking about learning (not pricing)
        for pattern in self.skip_patterns:
            if re.search(pattern, user_lower, re.IGNORECASE):
                logger.info(f"[SUBSCRIPTION_CHIPS] Learning query detected, skipping: {pattern}")
                return result

        # 6. HIGH INTENT - Check for pricing triggers (CHECK THIS FIRST BEFORE PREMIUM STATUS)
        # Even premium users should see pricing when explicitly requested
        for pattern in self.pricing_triggers:
            if re.search(pattern, user_lower, re.IGNORECASE):
                logger.info(f"[SUBSCRIPTION_CHIPS] Pricing trigger matched: {pattern}")
                result["show"] = True
                result["trigger"] = "pricing_query"
                result["display_mode"] = "comparison"

                # Recommend plan based on user's current usage
                total_sessions = user_context.get('total_sessions', 0)
                if total_sessions >= 10:
                    result["recommended_plan"] = "language_mastery_monthly"
                else:
                    result["recommended_plan"] = "fluency_builder_monthly"

                return result

        # 7. Check if user is already premium (only blocks AUTOMATIC suggestions, not explicit pricing queries)
        subscription_status = user_context.get('subscription_status', 'free')
        if subscription_status in ['active', 'trialing']:
            subscription_plan = user_context.get('subscription_plan', '')
            if subscription_plan in ['language_mastery', 'team_mastery']:
                logger.info(f"[SUBSCRIPTION_CHIPS] User already has premium plan, skipping automatic suggestions")
                return result

        # 8. Check for "out of minutes" scenario
        practice_minutes_remaining = user_context.get('practice_minutes_remaining', 0)
        if practice_minutes_remaining <= 0 and subscription_status == 'free':
            if any(word in user_lower for word in ['practice', 'session', 'conversation', 'talk']):
                logger.info(f"[SUBSCRIPTION_CHIPS] Out of minutes trigger")
                result["show"] = True
                result["trigger"] = "out_of_minutes"
                result["display_mode"] = "single_highlight"
                result["recommended_plan"] = "fluency_builder_monthly"
                return result

        # 9. Check for "low hearts" scenario (ONLY hearts, NOT challenges)
        if 'heart' in user_lower and 'challenge' not in user_lower:
            # Check if user has low hearts (implementation would need heart system data)
            logger.info(f"[SUBSCRIPTION_CHIPS] Hearts query, showing subscription chips")
            result["show"] = True
            result["trigger"] = "hearts_query"
            result["display_mode"] = "single_highlight"
            result["recommended_plan"] = "language_mastery_monthly"
            return result

        # Default: don't show
        return result

    def format_subscription_chips(
        self,
        trigger: str,
        display_mode: str,
        recommended_plan: str,
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format subscription chips for display.

        Args:
            trigger: Trigger type (pricing_query, out_of_minutes, etc.)
            display_mode: "comparison" or "single_highlight"
            recommended_plan: Plan to highlight
            user_context: User context data

        Returns:
            List of chip data objects
        """
        user_plan = user_context.get('subscription_plan', 'try_learn_free')
        subscription_status = user_context.get('subscription_status', 'free')

        # If user is free, set to try_learn_free
        if subscription_status in ['free', 'expired']:
            user_plan = 'try_learn_free'

        chips = []

        if display_mode == "comparison":
            # Show all 3 plans for comparison
            chips = [
                self._get_try_learn_chip(user_plan),
                self._get_fluency_builder_chip(user_plan, recommended_plan),
                self._get_language_mastery_chip(user_plan, recommended_plan)
            ]
        else:
            # Single highlight mode
            if recommended_plan == "fluency_builder_monthly":
                chips = [self._get_fluency_builder_chip(user_plan, recommended_plan)]
            else:
                chips = [self._get_language_mastery_chip(user_plan, recommended_plan)]

        return chips

    def _get_try_learn_chip(self, user_plan: str) -> Dict[str, Any]:
        """Get Try & Learn (FREE) chip data"""
        is_current = user_plan == 'try_learn_free'

        return {
            "planId": "try_learn_free",
            "planName": "Try & Learn",
            "planEmoji": "",
            "badge": "FREE" if not is_current else "CURRENT",
            "badgeColor": "#6B7280",  # Gray
            "price": "€0",
            "priceSubtext": "",
            "originalPrice": None,
            "savingsText": None,
            "features": [
                {"emoji": "", "text": "Limited practice"},
                {"emoji": "", "text": "5 hearts"}
            ],
            "accentColor": "#6B7280",  # Gray - solid color, no gradient!
            "backgroundColor": "#FFFFFF",  # White card
            "borderColor": "#6B7280",  # Gray border - use accent color!
            "borderWidth": 2,
            "ctaText": "CURRENT" if is_current else "FREE",
            "ctaBackgroundColor": "#F3F4F6" if is_current else "#6B7280",
            "ctaTextColor": "#6B7280" if is_current else "#FFFFFF",
            "ctaDisabled": is_current,
            "action": None,
            "isRecommended": False,
            "isCurrent": is_current
        }

    def _get_fluency_builder_chip(self, user_plan: str, recommended_plan: str) -> Dict[str, Any]:
        """Get Fluency Builder chip data (MONTHLY)"""
        is_current = 'fluency' in user_plan.lower()
        is_recommended = recommended_plan == "fluency_builder_monthly"

        return {
            "planId": "fluency_builder_monthly",
            "planName": "Fluency Builder",
            "planEmoji": "",
            "badge": "POPULAR" if is_recommended else ("CURRENT" if is_current else None),
            "badgeColor": "#14B8A6",  # Teal/turquoise - solid color!
            "price": "€19.99",
            "priceSubtext": "/month",
            "originalPrice": None,
            "savingsText": None,
            "savingsColor": None,
            "features": [
                {"emoji": "", "text": "150 min/month"},
                {"emoji": "", "text": "10 hearts"}
            ],
            "accentColor": "#14B8A6",  # Teal - solid color, no gradient!
            "backgroundColor": "#FFFFFF",  # White card
            "borderColor": "#14B8A6",  # Teal border - always use accent color!
            "borderWidth": 2,
            "ctaText": "FREE TRIAL" if not is_current else "CURRENT",
            "ctaBackgroundColor": "#14B8A6" if not is_current else "#F3F4F6",
            "ctaTextColor": "#FFFFFF" if not is_current else "#6B7280",
            "ctaDisabled": is_current,
            "action": "open_subscription_modal" if not is_current else None,
            "plan": "fluency_builder_monthly",
            "isRecommended": is_recommended,
            "isCurrent": is_current
        }

    def _get_language_mastery_chip(self, user_plan: str, recommended_plan: str) -> Dict[str, Any]:
        """Get Language Mastery chip data (MONTHLY)"""
        is_current = user_plan in ['language_mastery', 'team_mastery']
        is_recommended = recommended_plan == "language_mastery_monthly"

        return {
            "planId": "language_mastery_monthly",
            "planName": "Language Mastery",
            "planEmoji": "",
            "badge": "UNLIMITED" if is_recommended else ("CURRENT" if is_current else "UNLIMITED"),
            "badgeColor": "#F59E0B",  # Amber/gold - solid color!
            "price": "€39.99",
            "priceSubtext": "/month",
            "originalPrice": None,
            "savingsText": None,
            "savingsColor": None,
            "features": [
                {"emoji": "", "text": "Unlimited"},
                {"emoji": "", "text": "Instant refills"}
            ],
            "accentColor": "#F59E0B",  # Amber - solid color, no gradient!
            "backgroundColor": "#FFFFFF",  # White card
            "borderColor": "#F59E0B",  # Amber border - always use accent color!
            "borderWidth": 2,
            "ctaText": "FREE TRIAL" if not is_current else "CURRENT",
            "ctaBackgroundColor": "#F59E0B" if not is_current else "#F3F4F6",
            "ctaTextColor": "#FFFFFF" if not is_current else "#6B7280",
            "ctaDisabled": is_current,
            "action": "open_subscription_modal" if not is_current else None,
            "plan": "language_mastery_monthly",
            "isRecommended": is_recommended,
            "isCurrent": is_current
        }

    def format_response_with_subscription_chips(
        self,
        ai_response: str,
        user_message: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Format AI response to include subscription chips when appropriate.

        Args:
            ai_response: AI's text response
            user_message: User's original message
            user_context: User context data
            conversation_history: Conversation history

        Returns:
            Tuple of (messages, tracking_data)
            - messages: List of message objects (text + subscription_chips)
            - tracking_data: Optional tracking data for analytics
        """
        # Check if we should show chips
        chip_decision = self.should_show_subscription_chips(
            user_message,
            user_context,
            conversation_history
        )

        if not chip_decision["show"]:
            logger.info(f"[SUBSCRIPTION_CHIPS] Not showing chips")
            return ([{
                "type": "text",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }], None)

        # Format subscription chips
        chips = self.format_subscription_chips(
            trigger=chip_decision["trigger"],
            display_mode=chip_decision["display_mode"],
            recommended_plan=chip_decision["recommended_plan"],
            user_context=user_context
        )

        # Build messages
        messages = []

        # IMPORTANT: Do NOT add text message - only show subscription chips!
        # The subscription cards are self-explanatory and look better without text

        # Add subscription chips
        messages.append({
            "type": "subscription_chips",
            "data": {
                "display_mode": chip_decision["display_mode"],
                "chips": chips,
                "context": {
                    "trigger": chip_decision["trigger"],
                    "userPlan": user_context.get('subscription_plan', 'try_learn_free'),
                    "recommendedPlan": chip_decision["recommended_plan"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })

        # Tracking data for analytics
        tracking_data = {
            "trigger": chip_decision["trigger"],
            "display_mode": chip_decision["display_mode"],
            "recommended_plan": chip_decision["recommended_plan"],
            "num_chips": len(chips),
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"[SUBSCRIPTION_CHIPS] Showing {len(chips)} chips (trigger: {chip_decision['trigger']}, mode: {chip_decision['display_mode']})")

        return (messages, tracking_data)


# Singleton instance
subscription_chip_formatter = SubscriptionChipFormatter()
