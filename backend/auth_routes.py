from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from typing import Optional
import httpx
import os
from pydantic import BaseModel

# Import Google Auth libraries
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from models import (
    UserCreate, 
    UserResponse, 
    Token, 
    LoginRequest, 
    GoogleLoginRequest, 
    PasswordResetRequest, 
    PasswordResetConfirm,
    UserUpdate,
    EmailVerificationRequest,
    EmailVerificationConfirm,
    ResendVerificationRequest
)

# Add password update model
class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str

from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user, 
    create_user,
    create_password_reset_token,
    reset_password,
    create_session,
    delete_session,
    verify_email_token,
    mark_user_verified,
    resend_verification_email,
    mark_existing_users_verified,
    get_user_by_id,
    verify_password,
    get_password_hash
)
from email_service import send_welcome_email
from database import users_collection

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """
    Register a new user with email and password
    """
    return await create_user(user)

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login with email and password
    """
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user's email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email and click the verification link.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await users_collection.update_one(
        {"_id": user.id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7 days
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create session
    session_token = await create_session(str(user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await users_collection.update_one(
        {"_id": user.id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7 days
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create session
    session_token = await create_session(str(user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email
    }

@router.post("/google-login", response_model=Token)
async def google_login(login_data: GoogleLoginRequest):
    """
    Login with Google OAuth token
    """
    # Verify Google token
    try:
        # Get the Google client ID from environment variables
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google client ID not configured",
            )
        
        # Verify the token using Google Auth library
        try:
            google_data = id_token.verify_oauth2_token(
                login_data.token, 
                google_requests.Request(), 
                google_client_id
            )
            
            # Get user email from verified token
            email = google_data.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not found in Google token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Check if user exists
            user = await users_collection.find_one({"email": email})
            if not user:
                # Create new user
                name = google_data.get("name", "Google User")
                user_data = {
                    "email": email,
                    "name": name,
                    "is_active": True,
                    "is_verified": True,  # Google users are automatically verified
                    "created_at": datetime.utcnow(),
                    "last_login": datetime.utcnow(),
                    "hashed_password": "GOOGLE_OAUTH"  # Special marker for Google users
                }
                result = await users_collection.insert_one(user_data)
                user_id = str(result.inserted_id)
                user = await users_collection.find_one({"_id": result.inserted_id})
            else:
                # Update existing user
                user_id = str(user["_id"])
                await users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7 days
            access_token = create_access_token(
                data={"sub": user_id},
                expires_delta=access_token_expires
            )
            
            # Create session
            session_token = await create_session(user_id)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user_id,
                "name": user["name"],
                "email": user["email"]
            }
        except ValueError as e:
            # Token validation failed
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/google-callback")
async def google_callback(code: str = None, error: str = None, state: str = None):
    """
    Handle Google OAuth callback
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    # In a complete implementation, you would exchange the code for tokens
    # and then verify the ID token. For this example, we'll just return
    # a success message since the frontend will handle the token exchange.
    
    return {"message": "Google authentication successful. You can close this window."}

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(request: PasswordResetRequest, background_tasks: BackgroundTasks):
    """
    Request a password reset token
    """
    # Create password reset token
    token = await create_password_reset_token(request.email)
    
    # In a real application, you would send an email with the reset link
    # For now, we'll just log it
    if token:
        print(f"Password reset token for {request.email}: {token}")
        # In production, you would use a background task to send an email
        # background_tasks.add_task(send_reset_email, request.email, token)
    
    # Always return 204 to prevent email enumeration
    return None

@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_reset_password(request: PasswordResetConfirm):
    """
    Reset password using token
    """
    success = await reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    return None

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: UserResponse = Depends(get_current_user)):
    """
    Logout and invalidate the current session
    """
    # In a real implementation, you would get the session token from the request
    # and delete it from the database
    # For simplicity, we'll just return success
    return None

@router.get("/me", response_model=UserResponse)
async def get_user_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user

@router.put("/update-profile", response_model=UserResponse)
async def update_profile(profile_data: UserUpdate, current_user: UserResponse = Depends(get_current_user)):
    """
    Update user profile information
    """
    # Update user in database
    update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
    
    if not update_data:
        return current_user
    
    result = await users_collection.update_one(
        {"_id": current_user.id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        # No changes were made
        return current_user
    
    # Get updated user
    updated_user = await users_collection.find_one({"_id": current_user.id})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert MongoDB _id to string
    updated_user["id"] = str(updated_user["_id"])
    del updated_user["_id"]
    
    return UserResponse(**updated_user)

@router.post("/update-password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(request: PasswordUpdateRequest, current_user: UserResponse = Depends(get_current_user)):
    """
    Update user password
    """
    # Get the current user from database to verify current password
    user = await get_user_by_id(str(current_user.id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is a Google OAuth user
    if user.hashed_password == "GOOGLE_OAUTH":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update password for Google OAuth users"
        )
    
    # Verify current password
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash the new password
    new_hashed_password = get_password_hash(request.new_password)
    
    # Update the password in database
    result = await users_collection.update_one(
        {"_id": user.id},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return None

@router.post("/deactivate-account", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account(current_user: UserResponse = Depends(get_current_user)):
    """
    Deactivate user account by setting is_active to false
    """
    # Get the current user from database
    user = await get_user_by_id(str(current_user.id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if account is already deactivated
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already deactivated"
        )
    
    # Deactivate the account by setting is_active to false
    result = await users_collection.update_one(
        {"_id": user.id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )
    
    return None

# Email verification endpoints
@router.get("/verify-email")
async def verify_email_get_redirect(token: str):
    """
    Handle GET requests from email links - directly verify and show success page
    """
    print(f"[VERIFY-GET] Processing verification directly for token: {token[:10]}...")
    
    try:
        # Verify the token directly
        user_id = await verify_email_token(token)
        
        if not user_id:
            print(f"[VERIFY-GET] ❌ Token verification failed")
            return HTMLResponse("""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">Verification Failed</h1>
                <p>The verification link is invalid or has expired.</p>
                <a href="/auth/login" style="color: #4ECFBF; text-decoration: none;">Go to Login</a>
            </body></html>
            """)
        
        # Mark user as verified
        success = await mark_user_verified(user_id)
        
        if not success:
            print(f"[VERIFY-GET] ❌ Failed to mark user as verified")
            return HTMLResponse("""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">Verification Failed</h1>
                <p>Failed to verify email. Please try again.</p>
                <a href="/auth/login" style="color: #4ECFBF; text-decoration: none;">Go to Login</a>
            </body></html>
            """)
        
        print(f"[VERIFY-GET] ✅ User verified successfully")
        
        # Return success page with auto-redirect
        return HTMLResponse("""
        <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #4ECFBF, #3a9e92);">
            <div style="background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                <div style="width: 60px; height: 60px; background: #4ECFBF; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 30px;">✓</span>
                </div>
                <h1 style="color: #2d7a6e; margin-bottom: 10px;">Email Verified!</h1>
                <p style="color: #666; margin-bottom: 30px;">Your email has been successfully verified.</p>
                <p style="color: #666; margin-bottom: 20px;">Redirecting to login page in <span id="countdown">3</span> seconds...</p>
                <a href="/auth/login" style="background: #4ECFBF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Go to Login Now</a>
            </div>
            <script>
                let count = 3;
                const countdown = document.getElementById('countdown');
                const timer = setInterval(() => {
                    count--;
                    countdown.textContent = count;
                    if (count <= 0) {
                        clearInterval(timer);
                        window.location.href = '/auth/login?verified=true';
                    }
                }, 1000);
            </script>
        </body></html>
        """)
        
    except Exception as e:
        print(f"[VERIFY-GET] ❌ Error: {str(e)}")
        return HTMLResponse("""
        <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: red;">Verification Error</h1>
            <p>An error occurred during verification. Please try again.</p>
            <a href="/auth/login" style="color: #4ECFBF; text-decoration: none;">Go to Login</a>
        </body></html>
        """)

@router.post("/verify-email")
async def verify_email(request: EmailVerificationConfirm):
    """
    Verify email address using verification token
    """
    print(f"[VERIFY-BACKEND] Starting email verification process")
    print(f"[VERIFY-BACKEND] Token received: {request.token[:10]}...")
    
    try:
        # Verify the token
        print(f"[VERIFY-BACKEND] Verifying token...")
        user_id = await verify_email_token(request.token)
        
        if not user_id:
            print(f"[VERIFY-BACKEND] ❌ Token verification failed - invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        print(f"[VERIFY-BACKEND] ✅ Token verified successfully for user_id: {user_id}")
        
        # Mark user as verified
        print(f"[VERIFY-BACKEND] Marking user as verified...")
        success = await mark_user_verified(user_id)
        
        if not success:
            print(f"[VERIFY-BACKEND] ❌ Failed to mark user as verified")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify email"
            )
        
        print(f"[VERIFY-BACKEND] ✅ User marked as verified successfully")
        
        # Get user details for welcome email
        user = await get_user_by_id(user_id)
        if user:
            print(f"[VERIFY-BACKEND] User details retrieved: {user.email}")
            # Send welcome email
            try:
                await send_welcome_email(user.email, user.name)
                print(f"[VERIFY-BACKEND] ✅ Welcome email sent to {user.email}")
            except Exception as e:
                print(f"[VERIFY-BACKEND] ❌ Error sending welcome email: {str(e)}")
                # Don't fail verification if welcome email fails
        else:
            print(f"[VERIFY-BACKEND] ⚠️ Could not retrieve user details for user_id: {user_id}")
        
        print(f"[VERIFY-BACKEND] ✅ Email verification completed successfully")
        return {
            "message": "Email verified successfully",
            "verified": True
        }
        
    except HTTPException as he:
        print(f"[VERIFY-BACKEND] ❌ HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        print(f"[VERIFY-BACKEND] ❌ Unexpected error verifying email: {str(e)}")
        import traceback
        print(f"[VERIFY-BACKEND] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )

@router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest):
    """
    Resend verification email to user
    """
    try:
        success = await resend_verification_email(request.email)
        
        # Always return success to prevent email enumeration
        return {
            "message": "If your email is registered and not yet verified, a new verification email has been sent.",
            "sent": True
        }
        
    except Exception as e:
        print(f"❌ Error resending verification email: {str(e)}")
        # Still return success to prevent email enumeration
        return {
            "message": "If your email is registered and not yet verified, a new verification email has been sent.",
            "sent": True
        }

@router.post("/mark-existing-users-verified")
async def mark_existing_verified():
    """
    Mark all existing users as verified (migration endpoint)
    """
    try:
        count = await mark_existing_users_verified()
        return {
            "message": f"Marked {count} existing users as verified",
            "count": count
        }
    except Exception as e:
        print(f"❌ Error marking existing users as verified: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark existing users as verified"
        )

@router.get("/verification-status/{email}")
async def get_verification_status(email: str):
    """
    Get verification status for an email (for debugging)
    """
    try:
        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "email": email,
            "is_verified": user.get("is_verified", False),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting verification status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verification status"
        )
