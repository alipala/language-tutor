from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
import jwt
from passlib.context import CryptContext

# Import existing modules
from database import database, users_collection, conversation_sessions_collection, learning_plans_collection
from auth import get_password_hash, verify_password, SECRET_KEY, ALGORITHM
from models import UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin user model
class AdminUser(BaseModel):
    id: str
    email: str
    name: str
    role: str = "admin"
    permissions: List[str] = ["read:users", "write:users", "read:analytics"]

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: AdminUser

class DashboardMetrics(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    total_conversations: int
    total_assessments: int
    total_learning_plans: int

class UserListResponse(BaseModel):
    data: List[Dict[str, Any]]
    total: int

# Admin credentials (in production, store in database)
ADMIN_USERS = {
    "admin@languagetutor.com": {
        "id": "admin_001",
        "email": "admin@languagetutor.com",
        "name": "Admin User",
        "hashed_password": get_password_hash("admin123"),  # Change this password!
        "role": "admin",
        "permissions": ["read:users", "write:users", "read:analytics", "system:admin"]
    }
}

def create_admin_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token for admin users"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=8)  # 8 hour sessions for admins
    
    to_encode.update({"exp": expire, "type": "admin"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin(token: str = Depends(security)):
    """Validate admin JWT token and return admin user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from Bearer format
        if hasattr(token, 'credentials'):
            token_str = token.credentials
        else:
            token_str = str(token)
            
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        token_type = payload.get("type")
        
        if admin_id is None or token_type != "admin":
            raise credentials_exception
            
        # Find admin user (in production, query from admin users table)
        admin_user = None
        for email, user_data in ADMIN_USERS.items():
            if user_data["id"] == admin_id:
                admin_user = AdminUser(**user_data)
                break
                
        if admin_user is None:
            raise credentials_exception
            
        return admin_user
    except jwt.JWTError:
        raise credentials_exception

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(login_data: AdminLoginRequest):
    """Admin login endpoint"""
    try:
        # Find admin user
        admin_data = ADMIN_USERS.get(login_data.email)
        if not admin_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )
        
        # Verify password
        if not verify_password(login_data.password, admin_data["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )
        
        # Create access token
        access_token = create_admin_access_token(
            data={"sub": admin_data["id"]},
            expires_delta=timedelta(hours=8)
        )
        
        # Create admin user response
        admin_user = AdminUser(
            id=admin_data["id"],
            email=admin_data["email"],
            name=admin_data["name"],
            role=admin_data["role"],
            permissions=admin_data["permissions"]
        )
        
        return AdminLoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=admin_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Admin login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(current_admin: AdminUser = Depends(get_current_admin)):
    """Get dashboard metrics"""
    try:
        # Count total users
        total_users = await users_collection.count_documents({})
        
        # Count active users
        active_users = await users_collection.count_documents({"is_active": True})
        
        # Count verified users
        verified_users = await users_collection.count_documents({"is_verified": True})
        
        # Count conversations
        total_conversations = await conversation_sessions_collection.count_documents({})
        
        # Count learning plans
        total_learning_plans = await learning_plans_collection.count_documents({})
        
        # For assessments, we'll use a placeholder since we don't have a dedicated collection yet
        total_assessments = 0
        
        return DashboardMetrics(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            total_conversations=total_conversations,
            total_assessments=total_assessments,
            total_learning_plans=total_learning_plans
        )
        
    except Exception as e:
        print(f"Dashboard metrics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard metrics"
        )

@router.get("/users", response_model=UserListResponse)
async def get_users_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get users with pagination for admin panel"""
    try:
        print(f"Admin users request: page={page}, per_page={per_page}, sort_field={sort_field}, sort_order={sort_order}")
        
        # Calculate skip value
        skip = (page - 1) * per_page
        print(f"Skip value: {skip}")
        
        # Build sort criteria - handle different field names
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        print(f"Sort: {sort_field} {sort_direction}")
        
        # Get users with pagination - use simpler approach
        try:
            cursor = users_collection.find({})
            if sort_field and sort_field in ["_id", "created_at", "email", "name"]:
                cursor = cursor.sort(sort_field, sort_direction)
            cursor = cursor.skip(skip).limit(per_page)
            users = await cursor.to_list(length=per_page)
            print(f"Found {len(users)} users")
        except Exception as cursor_error:
            print(f"Cursor error: {str(cursor_error)}")
            # Fallback: get users without sorting
            cursor = users_collection.find({}).skip(skip).limit(per_page)
            users = await cursor.to_list(length=per_page)
            print(f"Fallback: Found {len(users)} users")
        
        # Get total count
        total = await users_collection.count_documents({})
        print(f"Total users: {total}")
        
        # Convert ObjectId to string and format response
        formatted_users = []
        for user in users:
            try:
                user_dict = {
                    "id": str(user["_id"]),
                    "email": user.get("email", ""),
                    "name": user.get("name", ""),
                    "is_active": user.get("is_active", True),
                    "is_verified": user.get("is_verified", False),
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                    "last_login": user.get("last_login").isoformat() if user.get("last_login") else None,
                    "preferred_language": user.get("preferred_language"),
                    "preferred_level": user.get("preferred_level")
                }
                formatted_users.append(user_dict)
            except Exception as format_error:
                print(f"Error formatting user {user.get('_id')}: {str(format_error)}")
                continue
        
        print(f"Returning {len(formatted_users)} formatted users")
        return UserListResponse(data=formatted_users, total=total)
        
    except Exception as e:
        print(f"Get users error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/users/{user_id}")
async def get_user_admin(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get single user details"""
    try:
        from bson import ObjectId
        
        # Find user
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Format response
        user_dict = {
            "id": str(user["_id"]),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "is_active": user.get("is_active", True),
            "is_verified": user.get("is_verified", False),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            "last_login": user.get("last_login").isoformat() if user.get("last_login") else None,
            "preferred_language": user.get("preferred_language"),
            "preferred_level": user.get("preferred_level")
        }
        
        return {"data": user_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )

@router.put("/users/{user_id}")
async def update_user_admin(
    user_id: str,
    user_data: dict,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Update user details"""
    try:
        from bson import ObjectId
        
        # Remove id from update data if present
        update_data = {k: v for k, v in user_data.items() if k != "id"}
        
        # Update user
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get updated user
        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        # Format response
        user_dict = {
            "id": str(updated_user["_id"]),
            "email": updated_user.get("email", ""),
            "name": updated_user.get("name", ""),
            "is_active": updated_user.get("is_active", True),
            "is_verified": updated_user.get("is_verified", False),
            "created_at": updated_user.get("created_at").isoformat() if updated_user.get("created_at") else None,
            "last_login": updated_user.get("last_login").isoformat() if updated_user.get("last_login") else None,
            "preferred_language": updated_user.get("preferred_language"),
            "preferred_level": updated_user.get("preferred_level")
        }
        
        return {"data": user_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.get("/health")
async def admin_health_check():
    """Admin health check endpoint"""
    return {
        "status": "ok",
        "service": "admin",
        "timestamp": datetime.utcnow().isoformat()
    }
