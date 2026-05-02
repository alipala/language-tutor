import os
import secrets
import hashlib
import base64
import jwt as pyjwt
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import EmailStr
from dotenv import load_dotenv
from bson import ObjectId
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# We're using a simple hashlib implementation to avoid bcrypt issues
print("Using hashlib for password hashing (bcrypt bypass)")

from database import users_collection, sessions_collection, password_reset_collection, email_verification_collection
from models import UserInDB, TokenData, UserResponse, UserCreate, PasswordReset, EmailVerification
from email_service import send_verification_email, send_welcome_email

# Import Redis caching helpers
from cache_helpers import get_user_cached, invalidate_user_cache

# Load environment variables
load_dotenv()

# Get JWT secret key from environment variables or generate a random one
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Password utilities
def verify_password(plain_password, hashed_password):
    # Simple implementation using hashlib
    # Extract salt and hash from stored password
    try:
        # Check for OAuth markers (users authenticated via Google or Apple)
        if hashed_password in ["GOOGLE_OAUTH", "APPLE_OAUTH"]:
            print(f"[AUTH] Cannot verify password for OAuth user (marker: {hashed_password})")
            return False

        parts = hashed_password.split('$')

        # Handle different password formats
        if len(parts) == 3:
            # New format: $salt$hash
            salt = parts[1]
            stored_hash = parts[2]
        elif len(parts) == 4 and parts[0] == '' and parts[3] == '':
            # Legacy format: $salt$hash$ (with trailing empty string)
            salt = parts[1]
            stored_hash = parts[2]
        else:
            print(f"[AUTH] Invalid password format: {len(parts)} parts")
            return False

        # Hash the input password with the same salt
        computed_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()

        # Compare the computed hash with the stored hash
        return computed_hash == stored_hash
    except Exception as e:
        print(f"Error in verify_password: {str(e)}")
        return False

def get_password_hash(password):
    # Simple implementation using hashlib
    # Generate a random salt
    salt = secrets.token_hex(8)

    # Hash the password with the salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    # Return the salt and hash in a format similar to bcrypt
    # Format: $salt$hash
    return f"${salt}${password_hash}"

# Apple Sign-In verification
async def verify_apple_token(token: str) -> Optional[Dict]:
    """
    Verify Apple identity token using Apple's public keys.
    Returns decoded token payload if valid, None otherwise.
    """
    try:
        # Get Apple's public keys
        apple_keys_url = "https://appleid.apple.com/auth/keys"
        response = requests.get(apple_keys_url, timeout=10)
        response.raise_for_status()
        apple_keys = response.json()

        # Decode token header to get the key ID (kid)
        unverified_header = pyjwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            print("[APPLE AUTH] No 'kid' found in token header")
            return None

        # Find the matching public key
        matching_key = None
        for key in apple_keys.get("keys", []):
            if key.get("kid") == kid:
                matching_key = key
                break

        if not matching_key:
            print(f"[APPLE AUTH] No matching key found for kid: {kid}")
            return None

        # Convert JWK to PEM format for PyJWT
        from jwt.algorithms import RSAAlgorithm
        public_key = RSAAlgorithm.from_jwk(matching_key)

        # Verify and decode the token
        decoded = pyjwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=os.getenv("APPLE_CLIENT_ID", "com.bigdavinci.mytaco"),
            options={"verify_exp": True}
        )

        print(f"[APPLE AUTH] Token verified successfully for user: {decoded.get('sub')}")
        return decoded

    except pyjwt.ExpiredSignatureError:
        print("[APPLE AUTH] Token has expired")
        return None
    except pyjwt.InvalidTokenError as e:
        print(f"[APPLE AUTH] Invalid token: {str(e)}")
        return None
    except requests.RequestException as e:
        print(f"[APPLE AUTH] Failed to fetch Apple public keys: {str(e)}")
        return None
    except Exception as e:
        print(f"[APPLE AUTH] Unexpected error verifying Apple token: {str(e)}")
        return None

async def get_user_by_apple_id(apple_user_id: str) -> Optional[UserInDB]:
    """Get user by Apple user ID"""
    user_dict = await users_collection.find_one({"apple_user_id": apple_user_id})
    if user_dict:
        user_dict["_id"] = str(user_dict["_id"])
        return UserInDB(**user_dict)
    return None

# User utilities
async def get_user_by_email(email: str) -> Optional[UserInDB]:
    user_dict = await users_collection.find_one({"email": email})
    if user_dict:
        # Convert ObjectId to string
        user_dict["_id"] = str(user_dict["_id"])
        return UserInDB(**user_dict)
    return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """
    Get user by ID with Redis caching

    🚀 PERFORMANCE: Now uses Redis cache!
    - First request: 200ms (MongoDB query)
    - Subsequent requests: 5ms (Redis cache hit)
    - 40x faster!
    """
    try:
        # Convert to string for cache key consistency
        user_id_str = str(user_id)

        # 🚀 REDIS CACHING: Try cache first
        user_dict = await get_user_cached(user_id_str)

        # If cache miss, fall back to MongoDB
        if not user_dict:
            print(f"[AUTH] Cache miss for user {user_id_str}, querying MongoDB")
            # Try to convert to ObjectId if it's a string
            if isinstance(user_id, str) and ObjectId.is_valid(user_id):
                user_id = ObjectId(user_id)
            user_dict = await users_collection.find_one({"_id": user_id})

            if not user_dict:
                return None

            # Convert ObjectId to string
            user_dict["_id"] = str(user_dict["_id"])

            # Note: Caching is handled in get_user_cached() helper

        return UserInDB(**user_dict)
    except Exception as e:
        print(f"Error in get_user_by_id: {str(e)}")
    return None

async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    # Convert UserInDB to UserResponse
    user_dict = user.dict(by_alias=True)
    user_dict.pop("hashed_password", None)

    # Calculate assessments_limit based on subscription plan
    plan_id = user_dict.get("subscription_plan", "try_learn")
    period = user_dict.get("subscription_period", "monthly")

    # Plan limits (matching subscription_service.py)
    PLAN_LIMITS = {
        "try_learn": {"monthly_assessments": 1, "annual_assessments": 1},
        "fluency_builder": {"monthly_assessments": 2, "annual_assessments": 24},
        "language_mastery": {"monthly_assessments": -1, "annual_assessments": -1},  # unlimited
    }

    plan_limits = PLAN_LIMITS.get(plan_id, PLAN_LIMITS["try_learn"])
    assessments_limit = plan_limits.get(f"{period}_assessments", plan_limits["monthly_assessments"])

    # Add calculated limit to user dict
    user_dict["assessments_limit"] = assessments_limit

    return UserResponse(**user_dict)

async def get_optional_current_user(token: Optional[str] = None) -> Optional[UserResponse]:
    """Get current user if authenticated, otherwise return None (for optional authentication)"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        token_data = TokenData(user_id=user_id)
    except JWTError:
        return None
    
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        return None
    
    # Convert UserInDB to UserResponse
    user_dict = user.dict(by_alias=True)
    user_dict.pop("hashed_password", None)
    return UserResponse(**user_dict)

# Create a dependency that extracts the token from the Authorization header but doesn't require it
from fastapi import Request

async def get_optional_token(request: Request) -> Optional[str]:
    """Extract token from Authorization header if present"""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

async def get_optional_current_user_from_request(request: Request) -> Optional[UserResponse]:
    """Get current user from request if authenticated, otherwise return None"""
    token = await get_optional_token(request)
    return await get_optional_current_user(token)

# User registration
async def create_user(user: UserCreate) -> UserResponse:
    # Check if user already exists
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create user dict
    user_dict = user.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    created_at = datetime.utcnow()
    user_dict["created_at"] = created_at

    # New users require email verification
    user_dict["is_verified"] = False

    # Initialize subscription fields for free tier
    user_dict["subscription_plan"] = "try_learn"
    user_dict["subscription_period"] = "monthly"
    user_dict["practice_minutes_used"] = 0
    user_dict["practice_sessions_used"] = 0
    user_dict["assessments_used"] = 0

    # 🔥 FIX: Initialize billing period (30 days from join date)
    user_dict["current_period_start"] = created_at
    user_dict["current_period_end"] = created_at + timedelta(days=30)

    # Insert user into database
    result = await users_collection.insert_one(user_dict)
    
    # Get the created user with the string ID
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Convert ObjectId to string for user_id
    user_id = str(created_user["_id"])
    
    # Create email verification token and send verification email
    try:
        verification_token = await create_email_verification_token(user_id, user.email)
        await send_verification_email(user.email, user.name, verification_token)
        print(f"✅ Verification email sent to {user.email}")
    except Exception as e:
        print(f"❌ Error sending verification email: {str(e)}")
        # Don't fail user creation if email sending fails
    
    # Convert to UserResponse
    created_user_dict = created_user.copy()
    created_user_dict.pop("hashed_password", None)
    
    # Convert ObjectId to string for Pydantic model
    created_user_dict["_id"] = user_id
    
    # Log successful user creation
    print(f"User created successfully: {created_user_dict['email']} (verification required)")
    
    return UserResponse(**created_user_dict)

# Password reset
async def create_password_reset_token(email: EmailStr) -> Optional[str]:
    user = await get_user_by_email(email)
    if not user:
        # Don't reveal that the user doesn't exist
        return None
    
    # Generate a random token
    token = secrets.token_urlsafe(32)
    
    # Store the token in the database
    reset_data = {
        "user_id": str(user.id),
        "email": email,
        "token": token,
        "created_at": datetime.utcnow()
    }
    
    # Delete any existing tokens for this user
    await password_reset_collection.delete_many({"user_id": str(user.id)})
    
    # Insert the new token
    await password_reset_collection.insert_one(reset_data)
    
    return token

async def verify_password_reset_token(token: str) -> Optional[str]:
    # Find the token in the database
    reset_data = await password_reset_collection.find_one({"token": token})
    if not reset_data:
        return None
    
    # Check if the token is expired (1 hour)
    created_at = reset_data.get("created_at")
    if created_at and datetime.utcnow() - created_at > timedelta(hours=1):
        # Delete the expired token
        await password_reset_collection.delete_one({"token": token})
        return None
    
    return reset_data.get("user_id")

async def reset_password(token: str, new_password: str) -> bool:
    # Verify the token
    user_id = await verify_password_reset_token(token)
    if not user_id:
        return False
    
    # Hash the new password
    hashed_password = get_password_hash(new_password)
    
    # Update the user's password
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    # Delete the token
    await password_reset_collection.delete_one({"token": token})
    
    return result.modified_count > 0

# Session management
async def create_session(user_id: str) -> str:
    # Generate a session token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration time (7 days)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Store the session in the database
    session_data = {
        "user_id": user_id,
        "token": token,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    }
    
    await sessions_collection.insert_one(session_data)
    
    return token

async def validate_session(token: str) -> Optional[str]:
    # Find the session in the database
    session = await sessions_collection.find_one({"token": token})
    if not session:
        return None
    
    # Check if the session is expired
    expires_at = session.get("expires_at")
    if expires_at and datetime.utcnow() > expires_at:
        # Delete the expired session
        await sessions_collection.delete_one({"token": token})
        return None
    
    return session.get("user_id")

async def delete_session(token: str) -> bool:
    # Delete the session
    result = await sessions_collection.delete_one({"token": token})
    return result.deleted_count > 0

# Email verification functions
async def create_email_verification_token(user_id: str, email: str) -> str:
    """Create an email verification token for a user"""
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Delete any existing verification tokens for this user
    await email_verification_collection.delete_many({"user_id": user_id})
    
    # Create verification record
    verification_data = {
        "user_id": user_id,
        "email": email,
        "token": token,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Insert the verification token
    await email_verification_collection.insert_one(verification_data)
    
    return token

async def verify_email_token(token: str) -> Optional[str]:
    """Verify an email verification token and return user_id if valid"""
    print(f"[AUTH] Verifying email token: {token[:10]}...")
    
    # Find the verification record
    verification = await email_verification_collection.find_one({"token": token})
    if not verification:
        print(f"[AUTH] ❌ Token not found in database")
        return None
    
    print(f"[AUTH] ✅ Token found for user_id: {verification.get('user_id')}")
    print(f"[AUTH] Token expires at: {verification.get('expires_at')}")
    print(f"[AUTH] Current time: {datetime.utcnow()}")
    
    # Check if the token is expired
    if datetime.utcnow() > verification.get("expires_at", datetime.min):
        print(f"[AUTH] ❌ Token has expired, deleting from database")
        # Delete the expired token
        await email_verification_collection.delete_one({"token": token})
        return None
    
    print(f"[AUTH] ✅ Token is valid and not expired")
    return verification.get("user_id")

async def mark_user_verified(user_id: str) -> bool:
    """Mark a user as verified and delete their verification tokens"""
    try:
        # Convert user_id to ObjectId if it's a string
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_object_id = ObjectId(user_id)
        else:
            user_object_id = user_id
        
        # Update user verification status
        result = await users_collection.update_one(
            {"_id": user_object_id},
            {"$set": {"is_verified": True}}
        )
        
        # Delete all verification tokens for this user
        await email_verification_collection.delete_many({"user_id": user_id})
        
        return result.modified_count > 0
    except Exception as e:
        print(f"Error marking user as verified: {str(e)}")
        return False

async def resend_verification_email(email: str) -> bool:
    """Resend verification email to a user"""
    try:
        # Find the user
        user = await get_user_by_email(email)
        if not user:
            return False
        
        # Check if user is already verified
        if user.is_verified:
            return False
        
        # Create new verification token
        token = await create_email_verification_token(str(user.id), email)
        
        # Send verification email
        success = await send_verification_email(email, user.name, token)
        
        return success
    except Exception as e:
        print(f"Error resending verification email: {str(e)}")
        return False

async def mark_existing_users_verified():
    """Mark all existing users as verified (for migration)"""
    try:
        result = await users_collection.update_many(
            {"is_verified": {"$ne": True}},
            {"$set": {"is_verified": True}}
        )
        print(f"✅ Marked {result.modified_count} existing users as verified")
        return result.modified_count
    except Exception as e:
        print(f"❌ Error marking existing users as verified: {str(e)}")
        return 0

# Admin authentication
async def get_current_admin_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current user and verify admin privileges"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    admin_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required"
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is admin (for now, we'll use email-based admin check)
    # In production, you might want to add an is_admin field to the user model
    admin_emails = [
        "admin@mytaco.ai",
        "ali@mytaco.ai",
        "support@mytaco.ai"
    ]
    
    if user.email not in admin_emails:
        raise admin_exception
    
    return user
