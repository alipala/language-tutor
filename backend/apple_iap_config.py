"""
Apple In-App Purchase Configuration
Maps Apple product IDs to internal plan IDs and provides receipt verification
"""

import os
import logging
from typing import Optional, Dict
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Apple IAP Product ID to Internal Plan ID mapping
APPLE_IAP_PRODUCTS = {
    "com.bigdavinci.mytaco.fluency_builder_monthly": {
        "plan_id": "fluency_builder",
        "period": "monthly",
        "price": 9.99,
        "minutes": 150,
        "assessments": 2
    },
    "com.bigdavinci.mytaco.fluency_builder_annual": {
        "plan_id": "fluency_builder",
        "period": "annual",
        "price": 59.99,
        "minutes": 1800,
        "assessments": 24
    },
    "com.bigdavinci.mytaco.language_mastery_monthly": {
        "plan_id": "language_mastery",
        "period": "monthly",
        "price": 17.99,
        "minutes": -1,  # Unlimited
        "assessments": -1  # Unlimited
    },
    "com.bigdavinci.mytaco.language_mastery_annual": {
        "plan_id": "language_mastery",
        "period": "annual",
        "price": 107.88,
        "minutes": -1,  # Unlimited
        "assessments": -1  # Unlimited
    }
}


class AppleIAPVerifier:
    """Verify Apple IAP receipts with Apple's servers"""

    # Apple verification endpoints
    PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"

    @classmethod
    async def verify_receipt(cls, receipt_data: str, product_id: str) -> Dict:
        """
        Verify receipt with Apple's servers

        Args:
            receipt_data: Base64 encoded receipt data from iOS
            product_id: Apple product ID (e.g., com.bigdavinci.mytaco.fluency_builder_monthly)

        Returns:
            Dict with verification result and subscription info
        """
        logger.info(f"[APPLE_IAP] Verifying receipt for product: {product_id}")

        # Get Apple shared secret from environment
        shared_secret = os.getenv("APPLE_IAP_SHARED_SECRET")
        if not shared_secret:
            logger.error("[APPLE_IAP] APPLE_IAP_SHARED_SECRET not configured")
            raise ValueError("Apple IAP shared secret not configured")

        # Prepare request payload
        payload = {
            "receipt-data": receipt_data,
            "password": shared_secret,
            "exclude-old-transactions": True
        }

        # Try production first, then sandbox
        try:
            response = await cls._send_verification_request(cls.PRODUCTION_URL, payload)

            # If status is 21007, receipt is from sandbox - retry with sandbox URL
            if response.get("status") == 21007:
                logger.info("[APPLE_IAP] Receipt is from sandbox, retrying with sandbox URL")
                response = await cls._send_verification_request(cls.SANDBOX_URL, payload)

            return cls._parse_verification_response(response, product_id)

        except Exception as e:
            logger.error(f"[APPLE_IAP] Receipt verification failed: {str(e)}")
            raise

    @classmethod
    async def _send_verification_request(cls, url: str, payload: Dict) -> Dict:
        """Send verification request to Apple"""
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"[APPLE_IAP] Request to Apple failed: {str(e)}")
            raise

    @classmethod
    def _parse_verification_response(cls, response: Dict, product_id: str) -> Dict:
        """Parse Apple's verification response"""
        status = response.get("status")

        # Status 0 = valid receipt
        if status != 0:
            error_msg = cls._get_status_error_message(status)
            logger.error(f"[APPLE_IAP] Verification failed: {error_msg} (status: {status})")
            raise ValueError(f"Receipt verification failed: {error_msg}")

        logger.info("[APPLE_IAP] Receipt verification successful")

        # Extract latest receipt info
        latest_receipt_info = response.get("latest_receipt_info", [])
        if not latest_receipt_info:
            raise ValueError("No receipt info found in response")

        # Find the specific product in the receipt
        product_receipt = None
        for receipt in latest_receipt_info:
            if receipt.get("product_id") == product_id:
                product_receipt = receipt
                break

        if not product_receipt:
            raise ValueError(f"Product {product_id} not found in receipt")

        # Parse subscription details
        expires_date_ms = product_receipt.get("expires_date_ms")
        expires_date = None
        if expires_date_ms:
            expires_date = datetime.fromtimestamp(int(expires_date_ms) / 1000)

        return {
            "valid": True,
            "product_id": product_id,
            "transaction_id": product_receipt.get("transaction_id"),
            "original_transaction_id": product_receipt.get("original_transaction_id"),
            "purchase_date": product_receipt.get("purchase_date"),
            "expires_date": expires_date,
            "is_trial_period": product_receipt.get("is_trial_period") == "true",
            "is_in_intro_offer_period": product_receipt.get("is_in_intro_offer_period") == "true",
            "environment": response.get("environment", "Production")
        }

    @staticmethod
    def _get_status_error_message(status: int) -> str:
        """Get human-readable error message for Apple status codes"""
        error_messages = {
            21000: "The App Store could not read the JSON object you provided",
            21002: "The data in the receipt-data property was malformed",
            21003: "The receipt could not be authenticated",
            21004: "The shared secret you provided does not match",
            21005: "The receipt server is not currently available",
            21006: "This receipt is valid but the subscription has expired",
            21007: "This receipt is from the sandbox environment",
            21008: "This receipt is from the production environment",
            21009: "Internal data access error",
            21010: "The user account cannot be found or has been deleted"
        }
        return error_messages.get(status, f"Unknown error (status: {status})")


def get_plan_for_product(product_id: str) -> Optional[Dict]:
    """Get internal plan configuration for Apple product ID"""
    return APPLE_IAP_PRODUCTS.get(product_id)
