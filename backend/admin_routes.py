from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr

# Import existing modules
from database import database, users_collection, conversation_sessions_collection, learning_plans_collection
from auth import get_password_hash, verify_password, SECRET_KEY, ALGORITHM
from models import UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()

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
    from jose import jwt
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
    from jose import jwt
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
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    preferred_language: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get users with pagination and search for admin panel"""
    try:
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build search query
        query = {}
        
        # Text search across name, email, and ID
        if q is not None and str(q).strip():  # More robust check
            search_term = str(q).strip()
            
            # Try to match ObjectId if it looks like one
            search_conditions = [
                {"name": {"$regex": search_term, "$options": "i"}},
                {"email": {"$regex": search_term, "$options": "i"}}
            ]
            
            # If q looks like an ObjectId, add it to search
            if len(search_term) == 24:
                try:
                    from bson import ObjectId
                    search_conditions.append({"_id": ObjectId(search_term)})
                except:
                    pass
            
            query["$or"] = search_conditions
        
        # Filter by active status
        if is_active is not None:
            query["is_active"] = is_active
            
        # Filter by verified status
        if is_verified is not None:
            query["is_verified"] = is_verified
            
        # Filter by preferred language
        if preferred_language:
            query["preferred_language"] = preferred_language
        
        # Build sort criteria - handle different field names
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get users with pagination and search
        try:
            cursor = users_collection.find(query)
            if sort_field and sort_field in ["_id", "created_at", "email", "name"]:
                cursor = cursor.sort(sort_field, sort_direction)
            cursor = cursor.skip(skip).limit(per_page)
            users = await cursor.to_list(length=per_page)
        except Exception as cursor_error:
            # Fallback: get users without sorting but with search
            cursor = users_collection.find(query).skip(skip).limit(per_page)
            users = await cursor.to_list(length=per_page)
        
        # Get total count with search filters
        total = await users_collection.count_documents(query)
        
        # Helper function to safely format dates
        def safe_isoformat(date_value):
            if date_value is None:
                return None
            if isinstance(date_value, str):
                # If it's already a string, check if it looks like an ISO date
                if 'T' in str(date_value) or '-' in str(date_value):
                    return date_value  # Already formatted
                return str(date_value)
            if hasattr(date_value, 'isoformat'):
                return date_value.isoformat()
            return str(date_value)

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
                    "created_at": safe_isoformat(user.get("created_at")),
                    "last_login": safe_isoformat(user.get("last_login")),
                    "preferred_language": user.get("preferred_language"),
                    "preferred_level": user.get("preferred_level"),
                    # Add subscription fields for list view
                    "stripe_customer_id": user.get("stripe_customer_id"),
                    "subscription_status": user.get("subscription_status"),
                    "subscription_plan": user.get("subscription_plan"),
                    "subscription_period": user.get("subscription_period"),
                    "subscription_price_id": user.get("subscription_price_id"),
                    "subscription_expires_at": safe_isoformat(user.get("subscription_expires_at")),
                    "subscription_started_at": safe_isoformat(user.get("subscription_started_at")),
                    "current_period_start": safe_isoformat(user.get("current_period_start")),
                    "current_period_end": safe_isoformat(user.get("current_period_end")),
                    "practice_sessions_used": user.get("practice_sessions_used", 0),
                    "assessments_used": user.get("assessments_used", 0),
                    "learning_plan_preserved": user.get("learning_plan_preserved", False)
                }
                formatted_users.append(user_dict)
            except Exception as format_error:
                # Log error but continue processing other users
                continue
        
        return UserListResponse(data=formatted_users, total=total)
        
    except Exception as e:
        # Log error for debugging but don't expose internal details
        import traceback
        print(f"Get users error: {str(e)}")
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
        
        # Helper function to safely format dates
        def safe_isoformat(date_value):
            if date_value is None:
                return None
            if isinstance(date_value, str):
                return date_value
            if hasattr(date_value, 'isoformat'):
                return date_value.isoformat()
            return str(date_value)

        # Format response
        user_dict = {
            "id": str(user["_id"]),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "is_active": user.get("is_active", True),
            "is_verified": user.get("is_verified", False),
            "created_at": safe_isoformat(user.get("created_at")),
            "last_login": safe_isoformat(user.get("last_login")),
            "preferred_language": user.get("preferred_language"),
            "preferred_level": user.get("preferred_level"),
            # Subscription fields
            "stripe_customer_id": user.get("stripe_customer_id"),
            "subscription_status": user.get("subscription_status"),
            "subscription_plan": user.get("subscription_plan"),
            "subscription_period": user.get("subscription_period"),
            "subscription_price_id": user.get("subscription_price_id"),
            "subscription_expires_at": safe_isoformat(user.get("subscription_expires_at")),
            "subscription_started_at": safe_isoformat(user.get("subscription_started_at")),
            "current_period_start": safe_isoformat(user.get("current_period_start")),
            "current_period_end": safe_isoformat(user.get("current_period_end")),
            "practice_sessions_used": user.get("practice_sessions_used", 0),
            "assessments_used": user.get("assessments_used", 0),
            "learning_plan_preserved": user.get("learning_plan_preserved", False),
            "learning_plan_data": user.get("learning_plan_data"),
            "learning_plan_progress": user.get("learning_plan_progress")
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

@router.post("/users")
async def create_user_admin(
    user_data: dict,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Create a new user"""
    try:
        from datetime import datetime
        
        # Validate required fields
        if not user_data.get("email") or not user_data.get("name") or not user_data.get("password"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, name, and password are required"
            )
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": user_data["email"]})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash the password
        hashed_password = get_password_hash(user_data["password"])
        
        # Prepare user document
        new_user = {
            "email": user_data["email"],
            "name": user_data["name"],
            "hashed_password": hashed_password,
            "is_active": user_data.get("is_active", True),
            "is_verified": user_data.get("is_verified", False),
            "preferred_language": user_data.get("preferred_language"),
            "preferred_level": user_data.get("preferred_level"),
            "created_at": datetime.utcnow(),
            "last_login": None,
            "email_verification_token": None,
            "password_reset_token": None,
            "password_reset_expires": None
        }
        
        # Insert user
        result = await users_collection.insert_one(new_user)
        
        # Get created user
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        
        # Helper function to safely format dates
        def safe_isoformat(date_value):
            if date_value is None:
                return None
            if isinstance(date_value, str):
                return date_value
            if hasattr(date_value, 'isoformat'):
                return date_value.isoformat()
            return str(date_value)

        # Format response (exclude password hash)
        user_dict = {
            "id": str(created_user["_id"]),
            "email": created_user.get("email", ""),
            "name": created_user.get("name", ""),
            "is_active": created_user.get("is_active", True),
            "is_verified": created_user.get("is_verified", False),
            "created_at": safe_isoformat(created_user.get("created_at")),
            "last_login": safe_isoformat(created_user.get("last_login")),
            "preferred_language": created_user.get("preferred_language"),
            "preferred_level": created_user.get("preferred_level"),
            # Subscription fields
            "stripe_customer_id": created_user.get("stripe_customer_id"),
            "subscription_status": created_user.get("subscription_status"),
            "subscription_plan": created_user.get("subscription_plan"),
            "subscription_period": created_user.get("subscription_period"),
            "subscription_price_id": created_user.get("subscription_price_id"),
            "subscription_expires_at": safe_isoformat(created_user.get("subscription_expires_at")),
            "subscription_started_at": safe_isoformat(created_user.get("subscription_started_at")),
            "current_period_start": safe_isoformat(created_user.get("current_period_start")),
            "current_period_end": safe_isoformat(created_user.get("current_period_end")),
            "practice_sessions_used": created_user.get("practice_sessions_used", 0),
            "assessments_used": created_user.get("assessments_used", 0),
            "learning_plan_preserved": created_user.get("learning_plan_preserved", False),
            "learning_plan_data": created_user.get("learning_plan_data"),
            "learning_plan_progress": created_user.get("learning_plan_progress")
        }
        
        return {"data": user_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
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
        from datetime import datetime
        
        # Remove id from update data if present
        update_data = {k: v for k, v in user_data.items() if k not in ["id", "password"]}
        
        # Handle password update separately if provided
        if "password" in user_data and user_data["password"]:
            update_data["hashed_password"] = get_password_hash(user_data["password"])
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
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
        
        # Helper function to safely format dates
        def safe_isoformat(date_value):
            if date_value is None:
                return None
            if isinstance(date_value, str):
                return date_value
            if hasattr(date_value, 'isoformat'):
                return date_value.isoformat()
            return str(date_value)
        
        # Format response
        user_dict = {
            "id": str(updated_user["_id"]),
            "email": updated_user.get("email", ""),
            "name": updated_user.get("name", ""),
            "is_active": updated_user.get("is_active", True),
            "is_verified": updated_user.get("is_verified", False),
            "created_at": safe_isoformat(updated_user.get("created_at")),
            "last_login": safe_isoformat(updated_user.get("last_login")),
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

@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Delete a user (admin only)"""
    try:
        from bson import ObjectId
        
        print(f"Admin {current_admin.email} attempting to delete user {user_id}")
        
        # Check if user exists first
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_email = user.get("email", "unknown")
        user_name = user.get("name", "unknown")
        
        # Delete related data first (conversations, learning plans, etc.)
        print(f"Deleting related data for user {user_email}")
        
        # Delete user's conversations
        conv_result = await conversation_sessions_collection.delete_many({"user_id": user_id})
        print(f"Deleted {conv_result.deleted_count} conversations for user {user_email}")
        
        # Delete user's learning plans
        plans_result = await learning_plans_collection.delete_many({"user_id": user_id})
        print(f"Deleted {plans_result.deleted_count} learning plans for user {user_email}")
        
        # Delete the user
        result = await users_collection.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        print(f"Successfully deleted user {user_email} ({user_name}) and all related data")
        
        return {
            "message": f"User {user_email} and all related data deleted successfully",
            "deleted_user": {
                "id": user_id,
                "email": user_email,
                "name": user_name
            },
            "deleted_conversations": conv_result.deleted_count,
            "deleted_learning_plans": plans_result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete user error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.get("/conversation_sessions")
async def get_conversations_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get conversation sessions with pagination for admin panel"""
    try:
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get conversations with pagination
        cursor = conversation_sessions_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "language", "level"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        conversations = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await conversation_sessions_collection.count_documents({})
        
        # Format conversations
        formatted_conversations = []
        for conv in conversations:
            conv_dict = {
                "id": str(conv["_id"]),
                "user_id": conv.get("user_id"),
                "language": conv.get("language"),
                "level": conv.get("level"),
                "topic": conv.get("topic"),
                "message_count": conv.get("message_count", 0),
                "duration_minutes": conv.get("duration_minutes", 0),
                "summary": conv.get("summary", ""),
                "enhanced_analysis": conv.get("enhanced_analysis"),
                "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
                "updated_at": conv.get("updated_at").isoformat() if conv.get("updated_at") else None,
                "messages": conv.get("messages", [])
            }
            formatted_conversations.append(conv_dict)
        
        return {"data": formatted_conversations, "total": total}
        
    except Exception as e:
        print(f"Get conversations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )

@router.get("/conversation_sessions/{conversation_id}")
async def get_conversation_admin(
    conversation_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get single conversation details"""
    try:
        from bson import ObjectId
        
        # Find conversation
        conversation = await conversation_sessions_collection.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Format response
        conv_dict = {
            "id": str(conversation["_id"]),
            "user_id": conversation.get("user_id"),
            "language": conversation.get("language"),
            "level": conversation.get("level"),
            "topic": conversation.get("topic"),
            "message_count": conversation.get("message_count", 0),
            "duration_minutes": conversation.get("duration_minutes", 0),
            "summary": conversation.get("summary", ""),
            "enhanced_analysis": conversation.get("enhanced_analysis"),
            "created_at": conversation.get("created_at").isoformat() if conversation.get("created_at") else None,
            "updated_at": conversation.get("updated_at").isoformat() if conversation.get("updated_at") else None,
            "messages": conversation.get("messages", [])
        }
        
        return {"data": conv_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get conversation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation"
        )

@router.get("/learning_plans")
async def get_learning_plans_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get learning plans with pagination for admin panel"""
    try:
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get learning plans with pagination
        cursor = learning_plans_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "language", "proficiency_level"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        plans = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await learning_plans_collection.count_documents({})
        
        # Format learning plans
        formatted_plans = []
        for plan in plans:
            plan_dict = {
                "id": plan.get("id", str(plan["_id"])),
                "user_id": plan.get("user_id"),
                "language": plan.get("language"),
                "proficiency_level": plan.get("proficiency_level"),
                "goals": plan.get("goals", []),
                "duration_months": plan.get("duration_months", 0),
                "custom_goal": plan.get("custom_goal"),
                "total_sessions": plan.get("total_sessions", 0),
                "completed_sessions": plan.get("completed_sessions", 0),
                "progress_percentage": plan.get("progress_percentage", 0),
                "assessment_data": plan.get("assessment_data"),
                "created_at": plan.get("created_at") if isinstance(plan.get("created_at"), str) else plan.get("created_at").isoformat() if plan.get("created_at") else None
            }
            formatted_plans.append(plan_dict)
        
        return {"data": formatted_plans, "total": total}
        
    except Exception as e:
        print(f"Get learning plans error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch learning plans: {str(e)}"
        )

# Mock endpoints for collections that don't exist yet
@router.get("/user_stats")
async def get_user_stats_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get user statistics with pagination for admin panel"""
    try:
        user_stats_collection = database.user_stats
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get user stats with pagination
        cursor = user_stats_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "total_sessions"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        stats = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await user_stats_collection.count_documents({})
        
        # Format user stats
        formatted_stats = []
        for stat in stats:
            stat_dict = {
                "id": str(stat["_id"]),
                "user_id": stat.get("user_id"),
                "total_sessions": stat.get("total_sessions", 0),
                "total_minutes": stat.get("total_minutes", 0),
                "current_streak": stat.get("current_streak", 0),
                "longest_streak": stat.get("longest_streak", 0),
                "last_activity": stat.get("last_activity").isoformat() if stat.get("last_activity") else None,
                "created_at": stat.get("created_at").isoformat() if stat.get("created_at") else None,
                "updated_at": stat.get("updated_at").isoformat() if stat.get("updated_at") else None
            }
            formatted_stats.append(stat_dict)
        
        return {"data": formatted_stats, "total": total}
        
    except Exception as e:
        print(f"Get user stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user stats: {str(e)}"
        )

@router.get("/badges")
async def get_badges_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get badges with pagination for admin panel"""
    try:
        badges_collection = database.badges
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get badges with pagination
        cursor = badges_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "badge_type"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        badges = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await badges_collection.count_documents({})
        
        # Format badges
        formatted_badges = []
        for badge in badges:
            badge_dict = {
                "id": str(badge["_id"]),
                "user_id": badge.get("user_id"),
                "badge_type": badge.get("badge_type"),
                "badge_name": badge.get("badge_name"),
                "description": badge.get("description"),
                "earned_at": badge.get("earned_at").isoformat() if badge.get("earned_at") else None,
                "criteria_met": badge.get("criteria_met"),
                "created_at": badge.get("created_at").isoformat() if badge.get("created_at") else None
            }
            formatted_badges.append(badge_dict)
        
        return {"data": formatted_badges, "total": total}
        
    except Exception as e:
        print(f"Get badges error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch badges: {str(e)}"
        )

@router.get("/assessment_history")
async def get_assessment_history_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get assessment history with pagination for admin panel"""
    try:
        assessment_history_collection = database.assessment_history
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get assessment history with pagination
        cursor = assessment_history_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "assessment_type"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        history = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await assessment_history_collection.count_documents({})
        
        # Format assessment history
        formatted_history = []
        for record in history:
            record_dict = {
                "id": record.get("id", str(record["_id"])),
                "user_id": record.get("user_id"),
                "language": record.get("language"),
                "level": record.get("level"),
                "overall_score": record.get("overall_score", 0),
                "skill_scores": record.get("skill_scores", {}),
                "strengths": record.get("strengths", []),
                "areas_for_improvement": record.get("areas_for_improvement", []),
                "recommendations": record.get("recommendations", []),
                "feedback": record.get("feedback"),
                "recognized_text": record.get("recognized_text"),
                "created_at": record.get("created_at") if isinstance(record.get("created_at"), str) else record.get("created_at").isoformat() if record.get("created_at") else None
            }
            formatted_history.append(record_dict)
        
        return {"data": formatted_history, "total": total}
        
    except Exception as e:
        print(f"Get assessment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch assessment history: {str(e)}"
        )

@router.post("/fix-subscription-dates/{user_id}")
async def fix_subscription_dates(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Fix subscription dates by syncing from Stripe"""
    try:
        from bson import ObjectId
        import stripe
        import os
        from datetime import datetime, timezone
        
        # Initialize Stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        # Find user
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        stripe_customer_id = user.get("stripe_customer_id")
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no Stripe customer ID"
            )
        
        # Get active subscriptions from Stripe
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="active",
            limit=5
        )
        
        if not subscriptions.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscriptions found in Stripe"
            )
        
        subscription = subscriptions.data[0]
        
        # Convert timestamps to datetime
        period_start = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
        period_end = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
        
        # Get subscription details
        price = None
        period_type = "monthly"  # default
        
        try:
            if hasattr(subscription, 'items') and subscription.items and hasattr(subscription.items, 'data') and subscription.items.data:
                price = subscription.items.data[0].price
                if price and hasattr(price, 'recurring') and price.recurring and hasattr(price.recurring, 'interval'):
                    period_type = "annual" if price.recurring.interval == "year" else "monthly"
        except Exception as price_error:
            print(f"Error getting price details: {str(price_error)}")
            # Continue with default monthly
        
        # Update user in database
        update_data = {
            "current_period_start": period_start,
            "current_period_end": period_end,
            "subscription_period": period_type,
            "subscription_status": subscription.status,
            "subscription_id": subscription.id
        }
        
        # Add subscription_started_at if not exists
        if not user.get("subscription_started_at"):
            update_data["subscription_started_at"] = period_start
        
        # Add subscription_expires_at for compatibility
        update_data["subscription_expires_at"] = period_end
        
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "Subscription dates fixed successfully",
                "user_id": user_id,
                "stripe_subscription_id": subscription.id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "period_type": period_type,
                "status": subscription.status
            }
        else:
            return {
                "success": False,
                "message": "No changes were made",
                "user_id": user_id
            }
            
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Fix subscription dates error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix subscription dates: {str(e)}"
        )

@router.get("/health")
async def admin_health_check():
    """Admin health check endpoint"""
    return {
        "status": "ok",
        "service": "admin",
        "timestamp": datetime.utcnow().isoformat()
    }
