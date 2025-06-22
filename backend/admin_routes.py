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

@router.get("/explore")
async def explore_database_structure(current_admin: AdminUser = Depends(get_current_admin)):
    """Explore database structure for admin panel development"""
    try:
        # Get collections info
        collections = await database.list_collection_names()
        
        # Explore users
        user_sample = await users_collection.find_one()
        users_with_language = await users_collection.count_documents({"preferred_language": {"$ne": None}})
        users_with_level = await users_collection.count_documents({"preferred_level": {"$ne": None}})
        users_with_login = await users_collection.count_documents({"last_login": {"$ne": None}})
        
        # Explore conversations
        conv_sample = await conversation_sessions_collection.find_one()
        conv_count = await conversation_sessions_collection.count_documents({})
        
        # Explore learning plans
        plan_sample = await learning_plans_collection.find_one()
        plan_count = await learning_plans_collection.count_documents({})
        
        # Sample user activity analysis
        sample_users = await users_collection.find({}, {"_id": 1, "email": 1}).limit(5).to_list(length=5)
        user_activity = []
        
        for user in sample_users:
            user_id = str(user["_id"])
            email = user.get("email", "No email")
            
            # Check conversations and plans for this user
            user_convs = await conversation_sessions_collection.count_documents({"user_id": user_id})
            user_plans = await learning_plans_collection.count_documents({"user_id": user_id})
            
            user_activity.append({
                "email": email,
                "user_id": user_id,
                "conversations": user_convs,
                "learning_plans": user_plans
            })
        
        return {
            "collections": collections,
            "users": {
                "total": await users_collection.count_documents({}),
                "with_language": users_with_language,
                "with_level": users_with_level,
                "with_login_history": users_with_login,
                "sample_fields": list(user_sample.keys()) if user_sample else [],
                "sample_data": {k: v for k, v in user_sample.items() if k != '_id'} if user_sample else {}
            },
            "conversations": {
                "total": conv_count,
                "sample_fields": list(conv_sample.keys()) if conv_sample else [],
                "sample_data": {k: v for k, v in conv_sample.items() if k not in ['_id', 'conversation_data']} if conv_sample else {}
            },
            "learning_plans": {
                "total": plan_count,
                "sample_fields": list(plan_sample.keys()) if plan_sample else [],
                "sample_data": {k: v for k, v in plan_sample.items() if k not in ['_id', 'plan_content']} if plan_sample else {}
            },
            "user_activity_sample": user_activity
        }
        
    except Exception as e:
        print(f"Database exploration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explore database: {str(e)}"
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
                "created_at": plan.get("created_at").isoformat() if plan.get("created_at") else None
            }
            formatted_plans.append(plan_dict)
        
        return {"data": formatted_plans, "total": total}
        
    except Exception as e:
        print(f"Get learning plans error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch learning plans: {str(e)}"
        )

@router.get("/learning_plans/{plan_id}")
async def get_learning_plan_admin(
    plan_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get single learning plan details"""
    try:
        # Find learning plan by id field (not _id)
        plan = await learning_plans_collection.find_one({"id": plan_id})
        if not plan:
            # Try with _id as fallback
            from bson import ObjectId
            try:
                plan = await learning_plans_collection.find_one({"_id": ObjectId(plan_id)})
            except:
                pass
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found"
            )
        
        # Format response
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
            "plan_content": plan.get("plan_content"),
            "created_at": plan.get("created_at").isoformat() if plan.get("created_at") else None
        }
        
        return {"data": plan_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get learning plan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch learning plan"
        )

@router.get("/speaking_assessments")
async def get_speaking_assessments_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get speaking assessments with pagination for admin panel"""
    try:
        speaking_assessments_collection = database.speaking_assessments
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get assessments with pagination
        cursor = speaking_assessments_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "language", "overall_score"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        assessments = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await speaking_assessments_collection.count_documents({})
        
        # Format assessments
        formatted_assessments = []
        for assessment in assessments:
            assessment_dict = {
                "id": str(assessment["_id"]),
                "user_id": assessment.get("user_id"),
                "language": assessment.get("language"),
                "overall_score": assessment.get("overall_score", 0),
                "pronunciation_score": assessment.get("pronunciation", {}).get("score", 0),
                "grammar_score": assessment.get("grammar", {}).get("score", 0),
                "vocabulary_score": assessment.get("vocabulary", {}).get("score", 0),
                "fluency_score": assessment.get("fluency", {}).get("score", 0),
                "coherence_score": assessment.get("coherence", {}).get("score", 0),
                "recommended_level": assessment.get("recommended_level"),
                "confidence": assessment.get("confidence", 0),
                "created_at": assessment.get("created_at").isoformat() if assessment.get("created_at") else None
            }
            formatted_assessments.append(assessment_dict)
        
        return {"data": formatted_assessments, "total": total}
        
    except Exception as e:
        print(f"Get speaking assessments error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch speaking assessments: {str(e)}"
        )

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

@router.get("/activities")
async def get_activities_admin(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get user activities with pagination for admin panel"""
    try:
        activities_collection = database.activities
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build sort criteria
        if sort_field == "id":
            sort_field = "_id"
        
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get activities with pagination
        cursor = activities_collection.find({})
        if sort_field and sort_field in ["_id", "created_at", "user_id", "activity_type"]:
            cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(per_page)
        activities = await cursor.to_list(length=per_page)
        
        # Get total count
        total = await activities_collection.count_documents({})
        
        # Format activities
        formatted_activities = []
        for activity in activities:
            activity_dict = {
                "id": str(activity["_id"]),
                "user_id": activity.get("user_id"),
                "activity_type": activity.get("activity_type"),
                "description": activity.get("description"),
                "metadata": activity.get("metadata"),
                "created_at": activity.get("created_at").isoformat() if activity.get("created_at") else None
            }
            formatted_activities.append(activity_dict)
        
        return {"data": formatted_activities, "total": total}
        
    except Exception as e:
        print(f"Get activities error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activities: {str(e)}"
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

@router.get("/collections/explore")
async def explore_additional_collections(current_admin: AdminUser = Depends(get_current_admin)):
    """Explore additional collections for data availability"""
    try:
        collections_data = {}
        
        # Check each collection for data
        collection_names = ["speaking_assessments", "user_stats", "badges", "activities", "assessment_history"]
        
        for collection_name in collection_names:
            collection = database[collection_name]
            count = await collection.count_documents({})
            sample = await collection.find_one() if count > 0 else None
            
            collections_data[collection_name] = {
                "count": count,
                "fields": list(sample.keys()) if sample else [],
                "sample_data": {k: v for k, v in sample.items() if k != '_id'} if sample else {}
            }
        
        return collections_data
        
    except Exception as e:
        print(f"Collection exploration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explore collections: {str(e)}"
        )

@router.get("/health")
async def admin_health_check():
    """Admin health check endpoint"""
    return {
        "status": "ok",
        "service": "admin",
        "timestamp": datetime.utcnow().isoformat()
    }
