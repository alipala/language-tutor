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
        # Matches the App Store price point; 12 × 17.99 = 107.88 is not one, so
        # the store charges 107.99. Stripe still uses 107.88 for its own plans.
        "price": 107.99,
        "minutes": -1,  # Unlimited
        "assessments": -1  # Unlimited
    }
}


class AppleIAPVerifier:
    """Verify Apple IAP receipts with Apple's servers"""

    # Apple verification endpoints (legacy StoreKit 1 receipts only)
    PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"

    # iOS bundle identifier, checked against the JWS payload so a transaction
    # signed for another app can never grant a subscription here.
    BUNDLE_ID = os.getenv("APPLE_BUNDLE_ID", "com.bigdavinci.mytaco")

    # App Store app id, required by the verifier for PRODUCTION transactions
    # (it is ignored for sandbox). Matches eas.json submit.production.ios.ascAppId.
    APP_APPLE_ID = int(os.getenv("APPLE_APP_ID", "6757149290"))

    # Populated on first use by _load_root_certificates().
    _root_certificates = None

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

        # Two credential formats reach this method:
        #
        #  - StoreKit 2 signed transaction (JWS): three dot-separated base64url
        #    segments. This is what react-native-iap v14 produces, and in
        #    practice it is the ONLY thing available — under StoreKit 2 the
        #    on-device receipt file often does not exist at all, so the client's
        #    getReceiptDataIOS() returns nil (verified in the openiap native
        #    source: it returns nil when appStoreReceiptURL is missing).
        #  - Legacy base64 app receipt (PKCS#7): a single base64 blob, no dots.
        #
        # They are unambiguous to tell apart because standard base64 has no "."
        # in its alphabet. JWS is verified locally against Apple's root
        # certificates; the legacy path still goes to /verifyReceipt so older
        # clients keep working.
        if cls._looks_like_jws(receipt_data):
            return cls._verify_signed_transaction(receipt_data, product_id)

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

    @staticmethod
    def _looks_like_jws(value: str) -> bool:
        """
        True for a StoreKit 2 signed transaction, False for a legacy receipt.

        A JWS is header.payload.signature in base64url. A legacy app receipt is
        standard base64, whose alphabet contains no ".", so a valid receipt can
        never be mistaken for a JWS.
        """
        stripped = value.strip()
        return stripped.count(".") == 2 and " " not in stripped

    @classmethod
    def _load_root_certificates(cls) -> list:
        """
        Apple's root certificates, in DER form, for offline JWS verification.

        Cached after the first read: they are a few hundred bytes each and never
        change at runtime, and re-reading them per purchase would put disk I/O on
        the payment path. Ships in the repo (backend/certs/apple) rather than
        being fetched at runtime so verification cannot fail because
        apple.com is unreachable.
        """
        if cls._root_certificates is not None:
            return cls._root_certificates

        cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "apple")
        certificates = []
        for name in ("AppleRootCA-G3.cer", "AppleRootCA-G2.cer", "AppleIncRootCertificate.cer"):
            path = os.path.join(cert_dir, name)
            try:
                with open(path, "rb") as handle:
                    certificates.append(handle.read())
            except OSError as exc:
                # Not fatal on its own — G3 is the one StoreKit JWS chains to,
                # and the verifier only needs the root that the chain reaches.
                logger.warning(f"[APPLE_IAP] Could not read root certificate {name}: {exc}")

        if not certificates:
            raise ValueError(
                f"No Apple root certificates found in {cert_dir}; "
                "StoreKit 2 verification cannot run"
            )

        cls._root_certificates = certificates
        return certificates

    @classmethod
    def _verify_signed_transaction(cls, signed_transaction: str, product_id: str) -> Dict:
        """
        Verify a StoreKit 2 JWS locally and return the same shape as the legacy
        /verifyReceipt path, so callers do not care which format arrived.

        Verification is offline: the library checks the x5c certificate chain
        against Apple's roots and the Apple-specific marker OIDs. No shared
        secret, no network call, no dependency on a deprecated endpoint.
        """
        try:
            from appstoreserverlibrary.signed_data_verifier import (
                SignedDataVerifier,
                VerificationException,
            )
            from appstoreserverlibrary.models.Environment import Environment
        except ImportError as exc:
            logger.error(f"[APPLE_IAP] app-store-server-library not installed: {exc}")
            raise ValueError("StoreKit 2 verification unavailable on this server")

        root_certificates = cls._load_root_certificates()

        # The verifier pins one environment and rejects a mismatch, but the
        # environment is only known after decoding. Sandbox is tried first
        # because that is where TestFlight and review builds run; a production
        # transaction simply fails that attempt and succeeds on the second.
        # enable_online_checks stays False: it adds an OCSP round-trip to Apple
        # on every purchase, and a transient OCSP failure would reject a
        # legitimate paid transaction.
        attempts = [
            (Environment.SANDBOX, None),
            (Environment.PRODUCTION, cls.APP_APPLE_ID),
        ]

        last_error = None
        for environment, app_apple_id in attempts:
            try:
                verifier = SignedDataVerifier(
                    root_certificates,
                    False,
                    environment,
                    cls.BUNDLE_ID,
                    app_apple_id,
                )
                payload = verifier.verify_and_decode_signed_transaction(signed_transaction)
                logger.info(
                    f"[APPLE_IAP] JWS verified ({environment.value}) for "
                    f"product {payload.productId}"
                )
                return cls._parse_signed_transaction(payload, product_id, environment.value)
            except VerificationException as exc:
                last_error = exc
                logger.info(
                    f"[APPLE_IAP] JWS did not verify as {environment.value}: {exc}"
                )

        logger.error(f"[APPLE_IAP] StoreKit 2 verification failed: {last_error}")
        raise ValueError(f"Receipt verification failed: {last_error}")

    @classmethod
    def _parse_signed_transaction(cls, payload, product_id: str, environment: str) -> Dict:
        """Map a decoded StoreKit 2 transaction onto the legacy result shape."""
        # The JWS describes exactly one transaction, so a mismatch means the
        # client asked us to activate a different product than it paid for.
        if payload.productId != product_id:
            raise ValueError(
                f"Product {product_id} does not match the signed transaction "
                f"({payload.productId})"
            )

        # expiresDate is milliseconds since epoch, and is absent for
        # non-renewing purchases.
        expires_date = None
        if payload.expiresDate:
            expires_date = datetime.fromtimestamp(payload.expiresDate / 1000)

        purchase_date = None
        if payload.purchaseDate:
            purchase_date = datetime.fromtimestamp(payload.purchaseDate / 1000).isoformat()

        # offerType 1 is Apple's introductory offer, which is how a free trial
        # is represented; the legacy receipt exposed the same thing as
        # is_trial_period / is_in_intro_offer_period.
        raw_offer_type = getattr(payload, "rawOfferType", None)
        is_intro_offer = raw_offer_type == 1

        # A revoked (refunded) transaction must never grant entitlement.
        if getattr(payload, "revocationDate", None):
            raise ValueError("Transaction has been revoked (refunded)")

        return {
            "valid": True,
            "product_id": product_id,
            "transaction_id": payload.transactionId,
            "original_transaction_id": payload.originalTransactionId,
            "purchase_date": purchase_date,
            "expires_date": expires_date,
            "is_trial_period": is_intro_offer,
            "is_in_intro_offer_period": is_intro_offer,
            "environment": environment,
        }

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
