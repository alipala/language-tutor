"""
Google Play Billing Configuration
Maps Google Play product IDs to internal plan IDs and provides purchase verification
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Google API dependencies (may not be available in local development)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_PLAY_AVAILABLE = True
except ImportError:
    logger.warning("Google Play dependencies not available - billing verification disabled for local development")
    GOOGLE_PLAY_AVAILABLE = False
    service_account = None
    build = None

# Google Play Product ID to Internal Plan ID mapping
GOOGLE_PLAY_PRODUCTS = {
    "fluency_builder_monthly": {
        "plan_id": "fluency_builder",
        "period": "monthly",
        "price": 9.99,
        "minutes": 150,
        "assessments": 2
    },
    "fluency_builder_annual": {
        "plan_id": "fluency_builder",
        "period": "annual",
        "price": 59.99,
        "minutes": 1800,
        "assessments": 24
    },
    "language_mastery_monthly": {
        "plan_id": "language_mastery",
        "period": "monthly",
        "price": 17.99,
        "minutes": -1,  # Unlimited
        "assessments": -1  # Unlimited
    },
    "language_mastery_annual": {
        "plan_id": "language_mastery",
        "period": "annual",
        "price": 107.88,
        "minutes": -1,  # Unlimited
        "assessments": -1  # Unlimited
    }
}


class GooglePlayVerifier:
    """Verify Google Play purchases with Google Play Developer API"""

    # Package name for your app
    PACKAGE_NAME = "com.bigdavinci.MyTacoAI"

    @classmethod
    async def verify_purchase(cls, purchase_token: str, product_id: str) -> Dict:
        """
        Verify purchase with Google Play Developer API

        Args:
            purchase_token: Purchase token from Android
            product_id: Google Play product ID (e.g., fluency_builder_monthly)

        Returns:
            Dict with verification result and subscription info
        """
        logger.info(f"[GOOGLE_PLAY] Verifying purchase for product: {product_id}")

        # Check if Google Play dependencies are available
        if not GOOGLE_PLAY_AVAILABLE:
            logger.error("[GOOGLE_PLAY] Google Play dependencies not installed")
            raise ValueError("Google Play billing not available - install google-api-python-client")

        # Get service account credentials path from environment
        credentials_path = os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
        if not credentials_path:
            logger.error("[GOOGLE_PLAY] GOOGLE_PLAY_SERVICE_ACCOUNT_JSON not configured")
            raise ValueError("Google Play service account not configured")

        try:
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/androidpublisher']
            )

            # Build Google Play Developer API service
            service = build('androidpublisher', 'v3', credentials=credentials)

            # Verify the subscription purchase
            result = service.purchases().subscriptions().get(
                packageName=cls.PACKAGE_NAME,
                subscriptionId=product_id,
                token=purchase_token
            ).execute()

            return cls._parse_verification_response(result, product_id, purchase_token)

        except Exception as e:
            logger.error(f"[GOOGLE_PLAY] Purchase verification failed: {str(e)}")
            raise

    @classmethod
    def _parse_verification_response(cls, response: Dict, product_id: str, purchase_token: str) -> Dict:
        """Parse Google Play's verification response"""

        # Check if purchase is valid and active
        payment_state = response.get("paymentState")
        # paymentState: 0 = pending, 1 = received, 2 = free trial, 3 = pending deferred upgrade/downgrade

        if payment_state not in [1, 2]:
            raise ValueError(f"Invalid payment state: {payment_state}")

        logger.info("[GOOGLE_PLAY] Purchase verification successful")

        # Parse expiry time
        expiry_time_millis = response.get("expiryTimeMillis")
        expires_date = None
        if expiry_time_millis:
            expires_date = datetime.fromtimestamp(int(expiry_time_millis) / 1000)

        # Check if in trial period
        is_trial = response.get("paymentState") == 2  # 2 = free trial

        return {
            "valid": True,
            "product_id": product_id,
            "purchase_token": purchase_token,
            "order_id": response.get("orderId"),
            "purchase_time": response.get("startTimeMillis"),
            "expires_date": expires_date,
            "is_trial_period": is_trial,
            "auto_renewing": response.get("autoRenewing", False),
            "country_code": response.get("countryCode"),
            "price_currency_code": response.get("priceCurrencyCode"),
            "price_amount_micros": response.get("priceAmountMicros"),
        }


def get_plan_for_product(product_id: str) -> Optional[Dict]:
    """Get internal plan configuration for Google Play product ID"""
    return GOOGLE_PLAY_PRODUCTS.get(product_id)
