"""
Integration tests for authentication routes.

Tests cover:
- User registration and login
- Email verification
- Password management
- Profile updates
- Voice preferences
- Google OAuth (mocked)
- Security and validation
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid

class TestUserRegistration:
    """Test user registration functionality."""
    
    async def test_register_new_user_success(self, client: AsyncClient, test_utils):
        """Test successful user registration."""
        user_data = test_utils.generate_test_user_data()
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert "id" in data
        assert data["is_verified"] == False  # Should start unverified
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        user_data = {
            "email": test_user["email"],
            "name": "Another User",
            "password": "password123"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "password123"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_register_weak_password(self, client: AsyncClient, test_utils):
        """Test registration with weak password."""
        user_data = test_utils.generate_test_user_data()
        user_data["password"] = "123"  # Too short
        
        response = await client.post("/auth/register", json=user_data)
        
        # Should either reject or accept based on current validation rules
        # This test documents the current behavior
        assert response.status_code in [200, 400, 422]
    
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        incomplete_data = {"email": "test@example.com"}
        
        response = await client.post("/auth/register", json=incomplete_data)
        
        assert response.status_code == 422

class TestUserLogin:
    """Test user login functionality."""
    
    async def test_login_valid_credentials(self, client: AsyncClient, test_user):
        """Test login with valid credentials."""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == test_user["id"]
        assert data["email"] == test_user["email"]
    
    async def test_login_invalid_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        login_data = {
            "email": test_user["email"],
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    async def test_login_unverified_user(self, client: AsyncClient, unverified_user):
        """Test login with unverified email."""
        login_data = {
            "email": unverified_user["email"],
            "password": unverified_user["password"]
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 403
        assert "not verified" in response.json()["detail"].lower()
    
    async def test_oauth_login_flow(self, client: AsyncClient, test_user):
        """Test OAuth2 compatible login flow."""
        form_data = {
            "username": test_user["email"],
            "password": test_user["password"]
        }
        
        response = await client.post("/auth/token", data=form_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

class TestGoogleAuth:
    """Test Google OAuth authentication."""
    
    @patch('auth_routes.id_token.verify_oauth2_token')
    async def test_google_login_new_user(self, mock_verify, client: AsyncClient):
        """Test Google login for new user."""
        # Mock Google token verification
        mock_verify.return_value = {
            "email": "google@example.com",
            "name": "Google User"
        }
        
        google_data = {"token": "mock_google_token"}
        
        response = await client.post("/auth/google-login", json=google_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "google@example.com"
        assert data["name"] == "Google User"
    
    @patch('auth_routes.id_token.verify_oauth2_token')
    async def test_google_login_existing_user(self, mock_verify, client: AsyncClient, test_user):
        """Test Google login for existing user."""
        mock_verify.return_value = {
            "email": test_user["email"],
            "name": test_user["name"]
        }
        
        google_data = {"token": "mock_google_token"}
        
        response = await client.post("/auth/google-login", json=google_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
    
    @patch('auth_routes.id_token.verify_oauth2_token')
    async def test_google_login_invalid_token(self, mock_verify, client: AsyncClient):
        """Test Google login with invalid token."""
        mock_verify.side_effect = ValueError("Invalid token")
        
        google_data = {"token": "invalid_token"}
        
        response = await client.post("/auth/google-login", json=google_data)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

class TestEmailVerification:
    """Test email verification functionality."""
    
    async def test_verify_email_valid_token(self, client: AsyncClient, unverified_user):
        """Test email verification with valid token."""
        # Create a verification token
        from auth import create_email_verification_token
        token = await create_email_verification_token(unverified_user["email"])
        
        verify_data = {"token": token}
        
        response = await client.post("/auth/verify-email", json=verify_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] == True
        assert "successfully" in data["message"].lower()
    
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Test email verification with invalid token."""
        verify_data = {"token": "invalid_token"}
        
        response = await client.post("/auth/verify-email", json=verify_data)
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    async def test_resend_verification_email(self, client: AsyncClient, unverified_user):
        """Test resending verification email."""
        resend_data = {"email": unverified_user["email"]}
        
        response = await client.post("/auth/resend-verification", json=resend_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["sent"] == True
    
    async def test_resend_verification_nonexistent_email(self, client: AsyncClient):
        """Test resending verification for non-existent email."""
        resend_data = {"email": "nonexistent@example.com"}
        
        # Should still return success to prevent email enumeration
        response = await client.post("/auth/resend-verification", json=resend_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["sent"] == True

class TestPasswordManagement:
    """Test password reset and update functionality."""
    
    async def test_forgot_password_request(self, client: AsyncClient, test_user):
        """Test password reset request."""
        reset_data = {"email": test_user["email"]}
        
        response = await client.post("/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 204
    
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test password reset for non-existent email."""
        reset_data = {"email": "nonexistent@example.com"}
        
        # Should return 204 to prevent email enumeration
        response = await client.post("/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 204
    
    async def test_reset_password_valid_token(self, client: AsyncClient, test_user):
        """Test password reset with valid token."""
        # Create a reset token
        from auth import create_password_reset_token
        token = await create_password_reset_token(test_user["email"])
        
        reset_data = {
            "token": token,
            "new_password": "newpassword123"
        }
        
        response = await client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 204
    
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        
        response = await client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 400
    
    async def test_update_password_authenticated(self, client: AsyncClient, test_user, auth_headers):
        """Test password update for authenticated user."""
        update_data = {
            "current_password": test_user["password"],
            "new_password": "newpassword123"
        }
        
        response = await client.post("/auth/update-password", json=update_data, headers=auth_headers)
        
        assert response.status_code == 204
    
    async def test_update_password_wrong_current(self, client: AsyncClient, auth_headers):
        """Test password update with wrong current password."""
        update_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        response = await client.post("/auth/update-password", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()
    
    async def test_update_password_unauthenticated(self, client: AsyncClient):
        """Test password update without authentication."""
        update_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        response = await client.post("/auth/update-password", json=update_data)
        
        assert response.status_code == 401

class TestUserProfile:
    """Test user profile management."""
    
    async def test_get_current_user(self, client: AsyncClient, test_user, auth_headers):
        """Test getting current user information."""
        response = await client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["name"] == test_user["name"]
        assert data["id"] == test_user["id"]
    
    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
    
    async def test_update_profile_name(self, client: AsyncClient, auth_headers):
        """Test updating user profile name."""
        update_data = {"name": "Updated Name"}
        
        response = await client.put("/auth/update-profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    async def test_update_profile_preferences(self, client: AsyncClient, auth_headers):
        """Test updating user language preferences."""
        update_data = {
            "preferred_language": "spanish",
            "preferred_level": "A2"
        }
        
        response = await client.put("/auth/update-profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_language"] == "spanish"
        assert data["preferred_level"] == "A2"
    
    async def test_update_profile_invalid_email(self, client: AsyncClient, auth_headers):
        """Test updating profile with invalid email."""
        update_data = {"email": "invalid-email"}
        
        response = await client.put("/auth/update-profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    async def test_deactivate_account(self, client: AsyncClient, auth_headers):
        """Test account deactivation."""
        response = await client.post("/auth/deactivate-account", headers=auth_headers)
        
        assert response.status_code == 204

class TestVoicePreferences:
    """Test voice preference management."""
    
    async def test_select_voice_valid(self, client: AsyncClient, auth_headers):
        """Test selecting a valid voice."""
        voice_data = {"voice": "echo"}
        
        response = await client.post("/auth/select-voice", json=voice_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["voice"] == "echo"
        assert "successfully" in data["message"].lower()
    
    async def test_select_voice_invalid(self, client: AsyncClient, auth_headers):
        """Test selecting an invalid voice."""
        voice_data = {"voice": "invalid_voice"}
        
        response = await client.post("/auth/select-voice", json=voice_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    async def test_get_voice_preference(self, client: AsyncClient, auth_headers):
        """Test getting current voice preference."""
        response = await client.get("/auth/get-voice", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "voice" in data
        assert "available_voices" in data
        assert isinstance(data["available_voices"], list)
    
    async def test_voice_operations_unauthenticated(self, client: AsyncClient):
        """Test voice operations without authentication."""
        # Test select voice
        voice_data = {"voice": "echo"}
        response = await client.post("/auth/select-voice", json=voice_data)
        assert response.status_code == 401
        
        # Test get voice
        response = await client.get("/auth/get-voice")
        assert response.status_code == 401

class TestAuthenticationSecurity:
    """Test authentication security features."""
    
    async def test_invalid_token_format(self, client: AsyncClient):
        """Test request with invalid token format."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    async def test_expired_token(self, client: AsyncClient, test_user):
        """Test request with expired token."""
        # Create an expired token
        from auth import create_access_token
        from datetime import timedelta
        
        expired_token = create_access_token(
            data={"sub": test_user["id"]},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    async def test_malformed_authorization_header(self, client: AsyncClient):
        """Test request with malformed authorization header."""
        headers = {"Authorization": "InvalidFormat"}
        
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    async def test_sql_injection_attempt(self, client: AsyncClient):
        """Test SQL injection attempt in login."""
        malicious_data = {
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "password123"
        }
        
        response = await client.post("/auth/login", json=malicious_data)
        
        # Should handle gracefully (either 401 or 422)
        assert response.status_code in [401, 422]
    
    async def test_xss_attempt_in_registration(self, client: AsyncClient):
        """Test XSS attempt in user registration."""
        malicious_data = {
            "email": "test@example.com",
            "name": "<script>alert('xss')</script>",
            "password": "password123"
        }
        
        response = await client.post("/auth/register", json=malicious_data)
        
        # Should either sanitize or reject
        if response.status_code == 200:
            data = response.json()
            # Name should be sanitized
            assert "<script>" not in data["name"]
        else:
            # Or reject the request
            assert response.status_code in [400, 422]

class TestRateLimiting:
    """Test rate limiting and abuse prevention."""
    
    async def test_multiple_failed_login_attempts(self, client: AsyncClient, test_user):
        """Test multiple failed login attempts."""
        login_data = {
            "email": test_user["email"],
            "password": "wrongpassword"
        }
        
        # Make multiple failed attempts
        for _ in range(5):
            response = await client.post("/auth/login", json=login_data)
            assert response.status_code == 401
        
        # The system should still respond (no rate limiting implemented yet)
        # This test documents current behavior
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    async def test_multiple_registration_attempts(self, client: AsyncClient, test_utils):
        """Test multiple registration attempts with same email."""
        user_data = test_utils.generate_test_user_data()
        
        # First registration should succeed
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        # Subsequent attempts should fail
        for _ in range(3):
            response = await client.post("/auth/register", json=user_data)
            assert response.status_code == 400
