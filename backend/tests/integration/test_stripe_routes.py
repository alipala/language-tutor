"""
Integration tests for Stripe/subscription routes.

Tests cover:
- Subscription status and limits
- Checkout session creation
- Customer portal access
- Usage tracking
- Feature access control
- Webhook handling
- Subscription management
- Payment processing
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

class TestSubscriptionStatus:
    """Test subscription status functionality."""
    
    async def test_get_subscription_status_authenticated(self, client: AsyncClient, auth_headers, test_user):
        """Test getting subscription status for authenticated user."""
        response = await client.get("/api/stripe/subscription-status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "plan" in data
        assert "limits" in data or data["limits"] is None
        assert "is_preserved" in data
    
    async def test_get_subscription_status_unauthenticated(self, client: AsyncClient):
        """Test getting subscription status without authentication."""
        response = await client.get("/api/stripe/subscription-status")
        
        assert response.status_code == 401
    
    async def test_get_subscription_limits(self, client: AsyncClient, auth_headers):
        """Test getting subscription limits."""
        response = await client.get("/api/stripe/subscription-limits", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have limit information or error message
        if "error" not in data:
            assert "sessions_limit" in data
            assert "assessments_limit" in data
            assert "sessions_used" in data
            assert "assessments_used" in data
    
    async def test_get_subscription_plans(self, client: AsyncClient):
        """Test getting available subscription plans."""
        response = await client.get("/api/stripe/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        assert isinstance(data["plans"], dict)
        
        # Check for expected plans
        expected_plans = ["try_learn", "fluency_builder", "team_mastery"]
        for plan_id in expected_plans:
            if plan_id in data["plans"]:
                plan = data["plans"][plan_id]
                assert "name" in plan
                assert "monthly_price" in plan
                assert "annual_price" in plan
                assert "features" in plan
    
    async def test_get_specific_plan_details(self, client: AsyncClient):
        """Test getting details for a specific plan."""
        plan_id = "fluency_builder"
        
        response = await client.get(f"/api/stripe/plan/{plan_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "monthly_price" in data
        assert "annual_price" in data
        assert "features" in data
    
    async def test_get_nonexistent_plan(self, client: AsyncClient):
        """Test getting details for non-existent plan."""
        response = await client.get("/api/stripe/plan/nonexistent_plan")
        
        assert response.status_code == 404

class TestCheckoutSession:
    """Test checkout session creation."""
    
    @patch('stripe.checkout.Session.create')
    @patch('stripe.Customer.create')
    async def test_create_checkout_session_new_customer(self, mock_customer_create, mock_session_create, client: AsyncClient, auth_headers):
        """Test creating checkout session for new customer."""
        # Mock Stripe responses
        mock_customer_create.return_value = MagicMock(id="cus_test123")
        mock_session_create.return_value = MagicMock(url="https://checkout.stripe.com/test")
        
        checkout_data = {
            "price_id": "price_test123",
            "success_url": "http://test.com/success",
            "cancel_url": "http://test.com/cancel"
        }
        
        response = await client.post("/api/stripe/create-checkout-session", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"] == "https://checkout.stripe.com/test"
    
    @patch('stripe.checkout.Session.create')
    async def test_create_checkout_session_existing_customer(self, mock_session_create, client: AsyncClient, auth_headers, test_user):
        """Test creating checkout session for existing customer."""
        # Update test user with Stripe customer ID
        from database import users_collection
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(test_user["id"])},
            {"$set": {"stripe_customer_id": "cus_existing123"}}
        )
        
        mock_session_create.return_value = MagicMock(url="https://checkout.stripe.com/existing")
        
        checkout_data = {
            "price_id": "price_test123"
        }
        
        response = await client.post("/api/stripe/create-checkout-session", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
    
    async def test_create_checkout_session_missing_price(self, client: AsyncClient, auth_headers):
        """Test creating checkout session without price ID."""
        checkout_data = {}
        
        response = await client.post("/api/stripe/create-checkout-session", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "price id" in response.json()["detail"].lower()
    
    async def test_create_checkout_session_unauthenticated(self, client: AsyncClient):
        """Test creating checkout session without authentication."""
        checkout_data = {"price_id": "price_test123"}
        
        response = await client.post("/api/stripe/create-checkout-session", json=checkout_data)
        
        assert response.status_code == 401

class TestCustomerPortal:
    """Test customer portal functionality."""
    
    @patch('stripe.billing_portal.Session.create')
    async def test_create_customer_portal_session(self, mock_portal_create, client: AsyncClient, auth_headers, test_user):
        """Test creating customer portal session."""
        # Update test user with Stripe customer ID
        from database import users_collection
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(test_user["id"])},
            {"$set": {"stripe_customer_id": "cus_test123"}}
        )
        
        mock_portal_create.return_value = MagicMock(url="https://billing.stripe.com/portal")
        
        portal_data = {"return_url": "http://test.com/profile"}
        
        response = await client.post("/api/stripe/customer-portal", json=portal_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"] == "https://billing.stripe.com/portal"
    
    async def test_create_customer_portal_no_customer_id(self, client: AsyncClient, auth_headers):
        """Test creating customer portal without Stripe customer ID."""
        portal_data = {"return_url": "http://test.com/profile"}
        
        response = await client.post("/api/stripe/customer-portal", json=portal_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "no subscription" in response.json()["detail"].lower()
    
    async def test_create_customer_portal_unauthenticated(self, client: AsyncClient):
        """Test creating customer portal without authentication."""
        portal_data = {"return_url": "http://test.com/profile"}
        
        response = await client.post("/api/stripe/customer-portal", json=portal_data)
        
        assert response.status_code == 401

class TestUsageTracking:
    """Test usage tracking functionality."""
    
    async def test_track_practice_session_usage(self, client: AsyncClient, auth_headers, test_user):
        """Test tracking practice session usage."""
        usage_data = {
            "user_id": test_user["id"],
            "usage_type": "practice_session",
            "duration_minutes": 10.5
        }
        
        response = await client.post("/api/stripe/track-usage", json=usage_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
    
    async def test_track_assessment_usage(self, client: AsyncClient, auth_headers, test_user):
        """Test tracking assessment usage."""
        usage_data = {
            "user_id": test_user["id"],
            "usage_type": "assessment"
        }
        
        response = await client.post("/api/stripe/track-usage", json=usage_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    async def test_track_usage_invalid_type(self, client: AsyncClient, auth_headers, test_user):
        """Test tracking usage with invalid type."""
        usage_data = {
            "user_id": test_user["id"],
            "usage_type": "invalid_type"
        }
        
        response = await client.post("/api/stripe/track-usage", json=usage_data, headers=auth_headers)
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    async def test_track_usage_unauthenticated(self, client: AsyncClient):
        """Test tracking usage without authentication."""
        usage_data = {
            "user_id": "test_user_id",
            "usage_type": "practice_session"
        }
        
        response = await client.post("/api/stripe/track-usage", json=usage_data)
        
        assert response.status_code == 401

class TestFeatureAccess:
    """Test feature access control."""
    
    async def test_can_access_practice_session(self, client: AsyncClient, auth_headers):
        """Test checking access to practice sessions."""
        response = await client.get("/api/stripe/can-access/practice_session", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "can_access" in data
        assert "message" in data
        assert "feature_type" in data
        assert data["feature_type"] == "practice_session"
    
    async def test_can_access_assessment(self, client: AsyncClient, auth_headers):
        """Test checking access to assessments."""
        response = await client.get("/api/stripe/can-access/assessment", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "can_access" in data
        assert data["feature_type"] == "assessment"
    
    async def test_can_access_invalid_feature(self, client: AsyncClient, auth_headers):
        """Test checking access to invalid feature."""
        response = await client.get("/api/stripe/can-access/invalid_feature", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Should return false for invalid features
        assert data["can_access"] == False
    
    async def test_can_access_unauthenticated(self, client: AsyncClient):
        """Test checking feature access without authentication."""
        response = await client.get("/api/stripe/can-access/practice_session")
        
        assert response.status_code == 401

class TestSubscriptionManagement:
    """Test subscription management functionality."""
    
    @patch('stripe.Subscription.list')
    @patch('stripe.Subscription.cancel')
    async def test_cancel_subscription(self, mock_cancel, mock_list, client: AsyncClient, auth_headers, test_user):
        """Test canceling an active subscription."""
        # Update test user with Stripe customer ID
        from database import users_collection
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(test_user["id"])},
            {"$set": {"stripe_customer_id": "cus_test123"}}
        )
        
        # Mock Stripe responses
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_list.return_value = MagicMock(data=[mock_subscription])
        mock_cancel.return_value = mock_subscription
        
        response = await client.post("/api/stripe/cancel-subscription", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "subscription_id" in data
    
    @patch('stripe.Subscription.list')
    @patch('stripe.Subscription.cancel')
    async def test_cancel_trial_subscription(self, mock_cancel, mock_list, client: AsyncClient, auth_headers, test_user):
        """Test canceling a trial subscription."""
        # Update test user with Stripe customer ID
        from database import users_collection
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(test_user["id"])},
            {"$set": {"stripe_customer_id": "cus_test123"}}
        )
        
        # Mock trial subscription
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_trial123"
        mock_subscription.status = "trialing"
        mock_list.return_value = MagicMock(data=[mock_subscription])
        mock_cancel.return_value = mock_subscription
        
        response = await client.post("/api/stripe/cancel-subscription", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["was_trial"] == True
    
    @patch('stripe.Subscription.list')
    @patch('stripe.Subscription.modify')
    async def test_reactivate_subscription(self, mock_modify, mock_list, client: AsyncClient, auth_headers, test_user):
        """Test reactivating a canceled subscription."""
        # Update test user with Stripe customer ID
        from database import users_collection
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(test_user["id"])},
            {"$set": {"stripe_customer_id": "cus_test123"}}
        )
        
        # Mock canceled subscription
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_subscription.cancel_at_period_end = True
        mock_list.return_value = MagicMock(data=[mock_subscription])
        
        mock_reactivated = MagicMock()
        mock_reactivated.cancel_at_period_end = False
        mock_modify.return_value = mock_reactivated
        
        response = await client.post("/api/stripe/reactivate-subscription", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    async def test_cancel_subscription_no_customer_id(self, client: AsyncClient, auth_headers):
        """Test canceling subscription without Stripe customer ID."""
        response = await client.post("/api/stripe/cancel-subscription", headers=auth_headers)
        
        assert response.status_code == 400
        assert "no subscription" in response.json()["detail"].lower()

class TestGuestSubscriptionLinking:
    """Test guest subscription linking functionality."""
    
    @patch('stripe.Customer.list')
    @patch('stripe.Subscription.list')
    async def test_link_guest_subscription_by_email(self, mock_sub_list, mock_customer_list, client: AsyncClient, auth_headers, test_user):
        """Test linking guest subscription by email."""
        # Mock Stripe customer
        mock_customer = MagicMock()
        mock_customer.id = "cus_guest123"
        mock_customer_list.return_value = MagicMock(data=[mock_customer])
        
        # Mock subscription
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_guest123"
        mock_subscription.status = "active"
        mock_subscription.items = MagicMock()
        mock_subscription.items.data = [MagicMock()]
        mock_subscription.items.data[0].price = MagicMock()
        mock_subscription.items.data[0].price.id = "price_test123"
        mock_subscription.items.data[0].price.product = "prod_test123"
        mock_subscription.items.data[0].price.recurring = MagicMock()
        mock_subscription.items.data[0].price.recurring.interval = "month"
        mock_sub_list.return_value = MagicMock(data=[mock_subscription])
        
        # Mock product
        with patch('stripe.Product.retrieve') as mock_product:
            mock_product.return_value = MagicMock(name="Fluency Builder")
            
            link_data = {
                "customer_email": test_user["email"]
            }
            
            response = await client.post("/api/stripe/link-guest-subscription", json=link_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "subscription_id" in data
    
    @patch('stripe.checkout.Session.retrieve')
    @patch('stripe.Subscription.list')
    async def test_link_guest_subscription_by_session(self, mock_sub_list, mock_session_retrieve, client: AsyncClient, auth_headers):
        """Test linking guest subscription by session ID."""
        # Mock checkout session
        mock_session = MagicMock()
        mock_session.customer = "cus_session123"
        mock_session_retrieve.return_value = mock_session
        
        # Mock subscription
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_session123"
        mock_subscription.status = "active"
        mock_subscription.items = MagicMock()
        mock_subscription.items.data = []
        mock_sub_list.return_value = MagicMock(data=[mock_subscription])
        
        link_data = {
            "session_id": "cs_test123"
        }
        
        response = await client.post("/api/stripe/link-guest-subscription", json=link_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('stripe.Customer.list')
    async def test_link_guest_subscription_no_customer(self, mock_customer_list, client: AsyncClient, auth_headers):
        """Test linking guest subscription when no customer found."""
        mock_customer_list.return_value = MagicMock(data=[])
        
        link_data = {
            "customer_email": "nonexistent@example.com"
        }
        
        response = await client.post("/api/stripe/link-guest-subscription", json=link_data, headers=auth_headers)
        
        assert response.status_code == 404
        assert "no stripe customer" in response.json()["detail"].lower()

class TestExpiryWarning:
    """Test subscription expiry warning functionality."""
    
    async def test_get_expiry_warning_with_expiry(self, client: AsyncClient, auth_headers, test_user):
        """Test getting expiry warning when subscription is expiring."""
        # Update user with expiring subscription
        from database import users_collection
        from bson import ObjectId
        expiry_date = datetime.utcnow() + timedelta(days=3)  # Expires in 3 days
        
        await users_collection.update_one(
            {"_id": ObjectId(test_user["id"])},
            {"$set": {
                "subscription_expires_at": expiry_date,
                "subscription_status": "active"
            }}
        )
        
        response = await client.get("/api/stripe/expiry-warning", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "has_warning" in data
        assert "days_until_expiry" in data
        if data["has_warning"]:
            assert "message" in data
            assert data["days_until_expiry"] <= 7  # Should warn within 7 days
    
    async def test_get_expiry_warning_no_expiry(self, client: AsyncClient, auth_headers):
        """Test getting expiry warning when no expiry date."""
        response = await client.get("/api/stripe/expiry-warning", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_warning"] == False
        assert data["message"] is None
        assert data["days_until_expiry"] is None

class TestWebhookHandling:
    """Test Stripe webhook handling."""
    
    @patch('stripe.Webhook.construct_event')
    async def test_webhook_subscription_created(self, mock_construct_event, client: AsyncClient):
        """Test handling subscription created webhook."""
        # Mock webhook event
        mock_event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "active",
                    "current_period_start": 1640995200,
                    "current_period_end": 1643673600,
                    "items": {
                        "data": [{
                            "price": {
                                "id": "price_test123",
                                "product": "prod_test123",
                                "recurring": {"interval": "month"}
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        # Create a user with the customer ID
        from database import users_collection
        await users_collection.insert_one({
            "email": "webhook@example.com",
            "name": "Webhook User",
            "stripe_customer_id": "cus_test123"
        })
        
        headers = {"stripe-signature": "test_signature"}
        response = await client.post("/api/stripe/webhook", content=b"test_payload", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    @patch('stripe.Webhook.construct_event')
    async def test_webhook_subscription_updated(self, mock_construct_event, client: AsyncClient):
        """Test handling subscription updated webhook."""
        mock_event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "active",
                    "current_period_start": 1640995200,
                    "current_period_end": 1643673600
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        headers = {"stripe-signature": "test_signature"}
        response = await client.post("/api/stripe/webhook", content=b"test_payload", headers=headers)
        
        assert response.status_code == 200
    
    @patch('stripe.Webhook.construct_event')
    async def test_webhook_invalid_signature(self, mock_construct_event, client: AsyncClient):
        """Test webhook with invalid signature."""
        from stripe.error import SignatureVerificationError
        mock_construct_event.side_effect = SignatureVerificationError("Invalid signature", "sig")
        
        headers = {"stripe-signature": "invalid_signature"}
        response = await client.post("/api/stripe/webhook", content=b"test_payload", headers=headers)
        
        assert response.status_code == 400
        assert "invalid signature" in response.json()["error"].lower()
    
    async def test_webhook_missing_signature(self, client: AsyncClient):
        """Test webhook without signature header."""
        response = await client.post("/api/stripe/webhook", content=b"test_payload")
        
        assert response.status_code == 400
        assert "missing" in response.json()["error"].lower()

class TestSubscriptionLimits:
    """Test subscription limits enforcement."""
    
    async def test_premium_user_unlimited_access(self, client: AsyncClient, premium_auth_headers):
        """Test that premium users have unlimited access."""
        response = await client.get("/api/stripe/can-access/practice_session", headers=premium_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["can_access"] == True
    
    async def test_usage_tracking_updates_limits(self, client: AsyncClient, auth_headers, test_user):
        """Test that usage tracking affects subscription limits."""
        # Get initial limits
        response = await client.get("/api/stripe/subscription-limits", headers=auth_headers)
        assert response.status_code == 200
        initial_data = response.json()
        
        if "sessions_used" in initial_data:
            initial_sessions = initial_data["sessions_used"]
            
            # Track usage
            usage_data = {
                "user_id": test_user["id"],
                "usage_type": "practice_session"
            }
            
            response = await client.post("/api/stripe/track-usage", json=usage_data, headers=auth_headers)
            assert response.status_code == 200
            
            # Check updated limits
            response = await client.get("/api/stripe/subscription-limits", headers=auth_headers)
            assert response.status_code == 200
            updated_data = response.json()
            
            if "sessions_used" in updated_data:
                # Usage should have increased
                assert updated_data["sessions_used"] >= initial_sessions

class TestErrorHandling:
    """Test error handling in Stripe routes."""
    
    @patch('stripe.checkout.Session.create')
    async def test_stripe_api_error_handling(self, mock_session_create, client: AsyncClient, auth_headers):
        """Test handling of Stripe API errors."""
        from stripe.error import StripeError
        mock_session_create.side_effect = StripeError("Test Stripe error")
        
        checkout_data = {"price_id": "price_test123"}
        
        response = await client.post("/api/stripe/create-checkout-session", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "test stripe error" in response.json()["detail"].lower()
    
    async def test_invalid_price_id_format(self, client: AsyncClient, auth_headers):
        """Test handling of invalid price ID format."""
        checkout_data = {"price_id": ""}  # Empty price ID
        
        response = await client.post("/api/stripe/create-checkout-session", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 400
    
    async def test_database_error_during_webhook(self, client: AsyncClient):
        """Test handling of database errors during webhook processing."""
        # This would require mocking database failures
        # For now, test that malformed webhook data is handled
        
        headers = {"stripe-signature": "test_signature"}
        malformed_payload = b"not_json_data"
        
        response = await client.post("/api/stripe/webhook", content=malformed_payload, headers=headers)
        
        # Should handle gracefully
        assert response.status_code in [400, 500]
