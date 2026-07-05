"""
Tutor Authentication Module
Provides separate authentication system for tutors with JWT tokens
"""
import os
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from pydantic import BaseModel, EmailStr

from database import database, tutors_collection

# JWT Configuration (same as main auth but with different context)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth2 scheme for tutor authentication
tutor_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/tutor/login")


# Pydantic Models
class TutorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TutorLoginResponse(BaseModel):
    access_token: str
    token_type: str
    tutor_id: str
    name: str
    email: str
    first_login: bool
    institution_id: str


class TutorChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TutorTokenData(BaseModel):
    tutor_id: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = "tutor"


# Password utilities (matching main auth.py implementation)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using hashlib (matching auth.py implementation)"""
    try:
        parts = hashed_password.split('$')
        
        # Handle different password formats
        if len(parts) == 3:
            # Format: $salt$hash
            salt = parts[1]
            stored_hash = parts[2]
        elif len(parts) == 4 and parts[0] == '' and parts[3] == '':
            # Legacy format: $salt$hash$
            salt = parts[1]
            stored_hash = parts[2]
        else:
            print(f"[TUTOR_AUTH] Invalid password format: {len(parts)} parts")
            return False
        
        # Hash the input password with the same salt
        computed_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        
        # Compare hashes
        return computed_hash == stored_hash
    except Exception as e:
        print(f"[TUTOR_AUTH] Error in verify_password: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """Hash password using hashlib (matching auth.py implementation)"""
    # Generate random salt
    salt = secrets.token_hex(8)
    
    # Hash password with salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Return in format: $salt$hash
    return f"${salt}${password_hash}"


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is strong"


# Tutor utilities
async def get_tutor_by_email(email: str) -> Optional[dict]:
    """Get tutor by email from tutors collection"""
    tutor = await database.tutors.find_one({"email": email})
    if tutor:
        tutor["_id"] = str(tutor["_id"])
    return tutor


async def get_tutor_by_id(tutor_id: str) -> Optional[dict]:
    """Get tutor by ID from tutors collection"""
    try:
        if isinstance(tutor_id, str) and ObjectId.is_valid(tutor_id):
            tutor_id = ObjectId(tutor_id)
        
        tutor = await database.tutors.find_one({"_id": tutor_id})
        if tutor:
            tutor["_id"] = str(tutor["_id"])
        return tutor
    except Exception as e:
        print(f"[TUTOR_AUTH] Error in get_tutor_by_id: {str(e)}")
        return None


async def authenticate_tutor(email: str, password: str) -> Optional[dict]:
    """
    Authenticate tutor with email and password
    
    Returns:
        dict: Tutor document if authentication successful
        None: If authentication failed
    """
    # Get tutor by email
    tutor = await get_tutor_by_email(email)
    if not tutor:
        print(f"[TUTOR_AUTH] Tutor not found: {email}")
        return None
    
    # Check if tutor is active
    if not tutor.get("is_active", True):
        print(f"[TUTOR_AUTH] Tutor inactive: {email}")
        return None
    
    # Check if tutor has password set
    if not tutor.get("hashed_password"):
        print(f"[TUTOR_AUTH] Tutor has no password set: {email}")
        return None
    
    # Verify password
    if not verify_password(password, tutor["hashed_password"]):
        print(f"[TUTOR_AUTH] Invalid password for tutor: {email}")
        return None
    
    print(f"[TUTOR_AUTH] ✅ Tutor authenticated: {email}")
    return tutor


# Token utilities
def create_tutor_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for tutor"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "tutor",
        "jti": str(uuid.uuid4()),
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_tutor(token: str = Depends(tutor_oauth2_scheme)) -> dict:
    """
    Get current authenticated tutor from JWT token.
    Raises HTTPException if token is invalid, blocklisted, or tutor not found.
    """
    from redis_client import is_token_blocklisted
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tutor_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")

        if token_type != "tutor":
            print(f"[TUTOR_AUTH] Invalid token type: {token_type}")
            raise credentials_exception

        if tutor_id is None:
            raise credentials_exception

        # Check blocklist
        if jti and await is_token_blocklisted(jti):
            print(f"[TUTOR_AUTH] Blocklisted token used: {jti}")
            raise credentials_exception

    except JWTError as e:
        print(f"[TUTOR_AUTH] JWT Error: {str(e)}")
        raise credentials_exception
    
    # Get tutor from database
    tutor = await get_tutor_by_id(tutor_id)
    if tutor is None:
        print(f"[TUTOR_AUTH] Tutor not found: {tutor_id}")
        raise credentials_exception
    
    # Check if tutor is still active
    if not tutor.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tutor account is deactivated"
        )
    
    return tutor


async def verify_tutor_access(tutor_id: str, current_tutor: dict = Depends(get_current_tutor)) -> None:
    """
    Verify that authenticated tutor matches the requested tutor_id
    
    Security: Ensures tutors can only access their own data
    """
    if str(current_tutor["_id"]) != tutor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own data"
        )


async def update_tutor_password(tutor_id: str, new_password: str) -> bool:
    """
    Update tutor password and clear BOTH onboarding flags (first_login and
    must_reset_password) so the change-password gate is not re-triggered on the
    next login regardless of which flag the tutor was created with.
    """
    try:
        # Hash new password
        hashed_password = get_password_hash(new_password)

        # Update tutor
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id)},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "first_login": False,
                    "must_reset_password": False,
                    "password_changed_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0
    except Exception as e:
        print(f"[TUTOR_AUTH] Error updating password: {str(e)}")
        return False


# Session tracking (optional, for logout functionality)
async def create_tutor_session(tutor_id: str, token: str) -> bool:
    """Create tutor session record (for future logout functionality)"""
    try:
        session_data = {
            "tutor_id": tutor_id,
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        
        await database.tutor_sessions.insert_one(session_data)
        return True
    except Exception as e:
        print(f"[TUTOR_AUTH] Error creating session: {str(e)}")
        return False


async def delete_tutor_session(token: str) -> bool:
    """Delete tutor session (logout)"""
    try:
        result = await database.tutor_sessions.delete_one({"token": token})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[TUTOR_AUTH] Error deleting session: {str(e)}")
        return False
