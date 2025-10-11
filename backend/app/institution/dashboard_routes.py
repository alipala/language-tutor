"""
Enhanced Institution Dashboard APIs
Provides analytics, tutor management, and learner management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from io import StringIO
import csv

from app.config.feature_flags import feature_flags
from database import database
from auth import create_access_token

router = APIRouter(prefix="/institution/dashboard", tags=["institution-dashboard"])

def check_feature_enabled():
    """Check if institutional features are enabled"""
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Institutional features are not enabled"
        )

# ============================================================================
# ANALYTICS APIs
# ============================================================================

@router.get("/{institution_id}/analytics/language-distribution",
            dependencies=[Depends(check_feature_enabled)])
async def get_language_distribution(institution_id: str) -> Dict[str, Any]:
    """
    Get language distribution of learners in the institution
    """
    try:
        # Get all active learners for this institution
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        # Get user IDs
        user_ids = [l["user_id"] for l in learners if l.get("user_id")]
        
        if not user_ids:
            return {
                "total_learners": 0,
                "distribution": []
            }
        
        # Aggregate language distribution from learning plans with case normalization
        pipeline = [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {
                "_id": {"$toLower": "$language"},  # Normalize to lowercase
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await database.learning_plans.aggregate(pipeline).to_list(length=None)
        
        # Format results
        distribution = []
        total = 0
        for result in results:
            language = result["_id"]
            if language:  # Skip None values
                count = result["count"]
                total += count
                distribution.append({
                    "language": language.capitalize(),  # Capitalize first letter
                    "count": count
                })
        
        # Add percentages
        for item in distribution:
            item["percentage"] = round((item["count"] / total * 100), 1) if total > 0 else 0
        
        return {
            "total_learners": total,
            "distribution": distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get language distribution: {str(e)}")


@router.get("/{institution_id}/analytics/level-distribution",
            dependencies=[Depends(check_feature_enabled)])
async def get_level_distribution(institution_id: str) -> Dict[str, Any]:
    """
    Get proficiency level distribution of learners
    """
    try:
        # Get all active learners for this institution
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        # Get user IDs
        user_ids = [l["user_id"] for l in learners if l.get("user_id")]
        
        if not user_ids:
            return {
                "total_learners": 0,
                "distribution": []
            }
        
        # Aggregate level distribution from learning plans
        pipeline = [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {
                "_id": "$proficiency_level",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await database.learning_plans.aggregate(pipeline).to_list(length=None)
        
        # Format results with proper ordering
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        distribution = []
        total = 0
        
        for level in level_order:
            matching = [r for r in results if r["_id"] == level]
            if matching:
                count = matching[0]["count"]
                total += count
                distribution.append({
                    "level": level,
                    "count": count
                })
        
        # Add percentages
        for item in distribution:
            item["percentage"] = round((item["count"] / total * 100), 1) if total > 0 else 0
        
        return {
            "total_learners": total,
            "distribution": distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get level distribution: {str(e)}")


# ============================================================================
# TUTOR MANAGEMENT APIs
# ============================================================================

@router.get("/{institution_id}/tutors",
            dependencies=[Depends(check_feature_enabled)])
async def get_tutors(institution_id: str) -> Dict[str, Any]:
    """
    Get all tutors for an institution with their assigned learners (including inactive)
    OPTIMIZED: Uses aggregation pipeline to avoid N+1 queries
    """
    try:
        # Single aggregation pipeline - MUCH faster!
        # NOTE: Returns ALL tutors (active and inactive)
        pipeline = [
            {
                "$match": {
                    "institution_id": institution_id
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$lookup": {
                    "from": "institutional_learners",
                    "let": {"tutor_id_str": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$tutor_id", "$$tutor_id_str"]},
                                        {"$eq": ["$is_active", True]},
                                        {"$eq": ["$institution_id", institution_id]}
                                    ]
                                }
                            }
                        },
                        {
                            "$lookup": {
                                "from": "users",
                                "let": {"user_id_str": "$user_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {
                                                "$eq": [{"$toString": "$_id"}, "$$user_id_str"]
                                            }
                                        }
                                    }
                                ],
                                "as": "user_data"
                            }
                        },
                        {
                            "$unwind": {
                                "path": "$user_data",
                                "preserveNullAndEmptyArrays": False
                            }
                        }
                    ],
                    "as": "assigned_learners"
                }
            }
        ]
        
        tutors = await database.tutors.aggregate(pipeline).to_list(length=None)
        
        # Format results
        tutor_list = []
        for tutor in tutors:
            tutor_id = str(tutor["_id"])
            
            # Format learner details
            learner_details = []
            for learner in tutor.get("assigned_learners", []):
                user = learner.get("user_data", {})
                learner_details.append({
                    "user_id": str(user.get("_id", "")),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "language": user.get("preferred_language"),
                    "level": user.get("preferred_level"),
                    "enrolled_at": learner.get("enrolled_at")
                })
            
            tutor_list.append({
                "id": tutor_id,
                "name": tutor.get("name"),
                "email": tutor.get("email"),
                "bio": tutor.get("bio"),
                "specializations": tutor.get("specializations", []),
                "learner_count": len(learner_details),
                "learners": learner_details,
                "is_active": tutor.get("is_active", True),  # Include is_active field
                "created_at": tutor.get("created_at")
            })
        
        return {
            "total_tutors": len(tutor_list),
            "tutors": tutor_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tutors: {str(e)}")


@router.post("/{institution_id}/tutors",
             dependencies=[Depends(check_feature_enabled)])
async def add_tutor(institution_id: str, tutor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new tutor to the institution
    NEW: Now includes password field for tutor login
    """
    try:
        # Import password hashing function
        from app.tutor.tutor_auth import get_password_hash, validate_password_strength
        
        # Validate required fields
        if not tutor_data.get("name") or not tutor_data.get("email"):
            raise HTTPException(status_code=400, detail="Name and email are required")
        
        # NEW: Validate password if provided
        password = tutor_data.get("password", "")
        if not password:
            raise HTTPException(status_code=400, detail="Password is required for tutor account")
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Check if tutor email already exists
        existing = await database.tutors.find_one({"email": tutor_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Tutor with this email already exists")
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create tutor document
        tutor = {
            "name": tutor_data["name"],
            "email": tutor_data["email"],
            "hashed_password": hashed_password,  # NEW: Store hashed password
            "first_login": True,  # NEW: Flag for password change requirement
            "institution_id": institution_id,
            "bio": tutor_data.get("bio", ""),
            "specializations": tutor_data.get("specializations", []),
            "permissions": tutor_data.get("permissions", ["view_learners", "assign_tasks"]),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        result = await database.tutors.insert_one(tutor)
        
        # Convert ObjectId to string for JSON serialization
        tutor_response = {
            "message": "Tutor added successfully. Initial password has been set.",
            "tutor_id": str(result.inserted_id),
            "tutor": {
                "id": str(result.inserted_id),
                "name": tutor["name"],
                "email": tutor["email"],
                "bio": tutor["bio"],
                "specializations": tutor["specializations"],
                "permissions": tutor["permissions"],
                "first_login": True,
                "created_at": tutor["created_at"].isoformat() if tutor.get("created_at") else None
            }
        }
        
        return tutor_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tutor: {str(e)}")


@router.delete("/{institution_id}/tutors/{tutor_id}",
               dependencies=[Depends(check_feature_enabled)])
async def remove_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Remove/deactivate a tutor (DEPRECATED - use deactivate_tutor instead)
    """
    try:
        # Deactivate tutor instead of deleting
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        return {"message": "Tutor deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove tutor: {str(e)}")


@router.post("/{institution_id}/tutors/deactivate/{tutor_id}",
             dependencies=[Depends(check_feature_enabled)])
async def deactivate_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Deactivate a tutor and unassign all their learners
    This is a reversible operation that:
    1. Marks the tutor as inactive (preserves account data)
    2. Unassigns all learners from this tutor (they become "Unassigned")
    3. Allows future reactivation
    """
    try:
        # 1. Deactivate the tutor
        tutor_result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
        )
        
        if tutor_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        # 2. Unassign all learners from this tutor
        learners_result = await database.institutional_learners.update_many(
            {
                "institution_id": institution_id,
                "tutor_id": tutor_id,
                "is_active": True
            },
            {
                "$set": {
                    "tutor_id": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        unassigned_count = learners_result.modified_count
        
        return {
            "message": "Tutor deactivated successfully",
            "unassigned_learners": unassigned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate tutor: {str(e)}")


@router.post("/{institution_id}/tutors/reactivate/{tutor_id}",
             dependencies=[Depends(check_feature_enabled)])
async def reactivate_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Reactivate a previously deactivated tutor
    """
    try:
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {
                "$set": {"is_active": True, "reactivated_at": datetime.utcnow()},
                "$unset": {"deactivated_at": ""}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        return {"message": "Tutor reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate tutor: {str(e)}")


@router.put("/{institution_id}/tutors/{tutor_id}/permissions",
            dependencies=[Depends(check_feature_enabled)])
async def update_tutor_permissions(
    institution_id: str,
    tutor_id: str,
    permissions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update tutor permissions
    """
    try:
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {"permissions": permissions.get("permissions", [])}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        return {"message": "Permissions updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update permissions: {str(e)}")


# ============================================================================
# LEARNER MANAGEMENT APIs
# ============================================================================

@router.get("/{institution_id}/learners",
            dependencies=[Depends(check_feature_enabled)])
async def get_learners(institution_id: str) -> Dict[str, Any]:
    """
    Get all learners for an institution with progress data (including deactivated)
    OPTIMIZED: Uses aggregation pipeline to avoid N+1 queries
    """
    try:
        # Single aggregation pipeline - MUCH faster than N+1 queries!
        # NOTE: Returns ALL learners (active and inactive)
        pipeline = [
            {
                "$match": {
                    "institution_id": institution_id
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"user_id_str": "$user_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$user_id_str"]
                                }
                            }
                        }
                    ],
                    "as": "user_data"
                }
            },
            {
                "$lookup": {
                    "from": "learning_plans",
                    "localField": "user_id",
                    "foreignField": "user_id",
                    "as": "learning_plan"
                }
            },
            {
                "$lookup": {
                    "from": "tutors",
                    "let": {"tutor_id_str": "$tutor_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$tutor_id_str"]
                                }
                            }
                        }
                    ],
                    "as": "tutor_data"
                }
            },
            {
                "$unwind": {
                    "path": "$user_data",
                    "preserveNullAndEmptyArrays": False
                }
            }
        ]
        
        learners = await database.institutional_learners.aggregate(pipeline).to_list(length=None)
        
        learner_list = []
        for learner in learners:
            user = learner.get("user_data", {})
            
            # Get tutor info
            tutor = None
            tutor_data = learner.get("tutor_data", [])
            if tutor_data:
                tutor_doc = tutor_data[0]
                tutor = {
                    "id": str(tutor_doc["_id"]),
                    "name": tutor_doc.get("name"),
                    "email": tutor_doc.get("email")
                }
            
            # Get learning plan progress
            progress = None
            learning_plans = learner.get("learning_plan", [])
            if learning_plans:
                learning_plan = learning_plans[0]  # Get first plan
                percentage = learning_plan.get("progress_percentage", 0)
                completed = learning_plan.get("completed_sessions", 0)
                total = learning_plan.get("total_sessions", 16)
                
                # Categorize progress
                if percentage < 15:
                    category = "Just Started"
                    color = "green"
                    emoji = "🟢"
                elif percentage < 35:
                    category = "Early Progress"
                    color = "blue"
                    emoji = "🔵"
                elif percentage < 60:
                    category = "Intermediate"
                    color = "yellow"
                    emoji = "🟡"
                elif percentage < 85:
                    category = "Advanced"
                    color = "orange"
                    emoji = "🟠"
                else:
                    category = "Nearly Complete"
                    color = "red"
                    emoji = "🔴"
                
                progress = {
                    "percentage": round(percentage, 1),
                    "completed_sessions": completed,
                    "total_sessions": total,
                    "category": category,
                    "color": color,
                    "emoji": emoji
                }
            
            learner_list.append({
                "id": str(learner["_id"]),
                "user_id": user.get("_id") if isinstance(user.get("_id"), str) else str(user.get("_id", "")),
                "name": user.get("name"),
                "email": user.get("email"),
                "language": user.get("preferred_language"),
                "level": user.get("preferred_level"),
                "tutor": tutor,
                "enrollment_method": learner.get("enrollment_method"),
                "consent_given": learner.get("consent_given", False),
                "enrolled_at": learner.get("enrolled_at"),
                "is_active": learner.get("is_active", True),
                "progress": progress
            })
        
        return {
            "total_learners": len(learner_list),
            "learners": learner_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learners: {str(e)}")


@router.post("/{institution_id}/learners/assign-tutor",
             dependencies=[Depends(check_feature_enabled)])
async def assign_learner_to_tutor(
    institution_id: str,
    assignment: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assign a learner to a specific tutor
    """
    try:
        learner_id = assignment.get("learner_id")
        tutor_id = assignment.get("tutor_id")
        
        if not learner_id or not tutor_id:
            raise HTTPException(status_code=400, detail="learner_id and tutor_id are required")
        
        result = await database.institutional_learners.update_one(
            {"_id": ObjectId(learner_id), "institution_id": institution_id},
            {"$set": {"tutor_id": tutor_id, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Learner not found or already assigned")
        
        return {"message": "Learner assigned to tutor successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign learner: {str(e)}")


@router.post("/{institution_id}/learners/deactivate/{learner_id}",
             dependencies=[Depends(check_feature_enabled)])
async def deactivate_learner(institution_id: str, learner_id: str) -> Dict[str, Any]:
    """
    Deactivate/archive a learner (reversible operation)
    """
    try:
        result = await database.institutional_learners.update_one(
            {"_id": ObjectId(learner_id), "institution_id": institution_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Learner not found")
        
        return {"message": "Learner deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate learner: {str(e)}")


@router.post("/{institution_id}/learners/reactivate/{learner_id}",
             dependencies=[Depends(check_feature_enabled)])
async def reactivate_learner(institution_id: str, learner_id: str) -> Dict[str, Any]:
    """
    Reactivate a previously deactivated learner
    """
    try:
        result = await database.institutional_learners.update_one(
            {"_id": ObjectId(learner_id), "institution_id": institution_id},
            {
                "$set": {"is_active": True, "reactivated_at": datetime.utcnow()},
                "$unset": {"deactivated_at": ""}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Learner not found")
        
        return {"message": "Learner reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate learner: {str(e)}")


@router.post("/{institution_id}/learners/bulk-import",
             dependencies=[Depends(check_feature_enabled)])
async def bulk_import_learners(
    institution_id: str,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Bulk import learners from CSV file
    Expected CSV format: name, email, language, level, tutor_email
    """
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_data)
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for row in reader:
            try:
                # Validate required fields
                if not row.get('name') or not row.get('email'):
                    errors.append(f"Row missing name or email: {row}")
                    failed_count += 1
                    continue
                
                # Find or create user
                user = await database.users.find_one({"email": row['email']})
                if not user:
                    # Create new user (simplified - in production, send invitation email)
                    user_data = {
                        "name": row['name'],
                        "email": row['email'],
                        "preferred_language": row.get('language'),
                        "preferred_level": row.get('level'),
                        "is_active": True,
                        "created_at": datetime.utcnow()
                    }
                    user_result = await database.users.insert_one(user_data)
                    user_id = str(user_result.inserted_id)
                else:
                    user_id = str(user["_id"])
                
                # Find tutor by email if provided
                tutor_id = None
                if row.get('tutor_email'):
                    tutor = await database.tutors.find_one({
                        "email": row['tutor_email'],
                        "institution_id": institution_id
                    })
                    if tutor:
                        tutor_id = str(tutor["_id"])
                
                # Check if already enrolled
                existing = await database.institutional_learners.find_one({
                    "user_id": user_id,
                    "institution_id": institution_id
                })
                
                if not existing:
                    # Create enrollment
                    enrollment = {
                        "user_id": user_id,
                        "institution_id": institution_id,
                        "tutor_id": tutor_id,
                        "enrollment_method": "bulk_import",
                        "consent_given": False,
                        "enrolled_at": datetime.utcnow(),
                        "is_active": True
                    }
                    await database.institutional_learners.insert_one(enrollment)
                    success_count += 1
                else:
                    errors.append(f"User {row['email']} already enrolled")
                    failed_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing row {row}: {str(e)}")
                failed_count += 1
        
        return {
            "message": "Bulk import completed",
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors[:10]  # Return first 10 errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import learners: {str(e)}")


@router.get("/{institution_id}/learners/{user_id}/comprehensive-details",
            dependencies=[Depends(check_feature_enabled)])
async def get_comprehensive_learner_details(institution_id: str, user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive learner analytics with AI-generated insights
    Includes ALL learning plans, sessions, assessments, and recommendations
    """
    try:
        # Check if learner belongs to institution
        learner = await database.institutional_learners.find_one({
            'institution_id': institution_id,
            'user_id': user_id,
            'is_active': True
        })
        
        if not learner:
            raise HTTPException(status_code=404, detail="Learner not found")
        
        # Check consent
        if not learner.get('consent_given', False):
            raise HTTPException(
                status_code=403, 
                detail="Learner has not given consent to view detailed progress"
            )
        
        # Get user info
        user = await database.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get ALL learning plans
        all_learning_plans = await database.learning_plans.find({'user_id': user_id}).to_list(length=None)
        
        # Get ALL conversation sessions
        all_conversations = await database.conversations.find({
            'user_id': user_id
        }).sort('created_at', -1).to_list(length=None)
        
        # Get subscription info
        subscription = await database.subscriptions.find_one({'user_id': user_id})
        
        # Get tutor info
        tutor_info = None
        if learner.get('tutor_id'):
            tutor = await database.tutors.find_one({'_id': ObjectId(learner['tutor_id'])})
            if tutor:
                tutor_info = {
                    'id': str(tutor['_id']),
                    'name': tutor.get('name'),
                    'email': tutor.get('email')
                }
        
        # Calculate overall metrics
        total_sessions = sum([plan.get('completed_sessions', 0) for plan in all_learning_plans])
        total_minutes = sum([plan.get('practice_minutes_used', 0) for plan in all_learning_plans])
        
        # Format learning plans
        formatted_plans = []
        for plan in all_learning_plans:
            formatted_plan = {
                'id': plan.get('id'),
                'language': plan.get('language'),
                'proficiency_level': plan.get('proficiency_level'),
                'progress_percentage': plan.get('progress_percentage', 0),
                'completed_sessions': plan.get('completed_sessions', 0),
                'total_sessions': plan.get('total_sessions', 16),
                'practice_minutes_used': plan.get('practice_minutes_used', 0),
                'total_practice_minutes': plan.get('total_practice_minutes', 80),
                'created_at': plan.get('created_at').isoformat() if plan.get('created_at') else None,
                'assessment_data': plan.get('assessment_data', {}),
                'plan_content': {
                    'title': plan.get('plan_content', {}).get('title'),
                    'assessment_summary': plan.get('plan_content', {}).get('assessment_summary', {}),
                    'learning_objectives': plan.get('plan_content', {}).get('learning_objectives', []),
                    'weekly_schedule': plan.get('plan_content', {}).get('weekly_schedule', [])
                },
                'session_summaries': plan.get('session_summaries', [])
            }
            formatted_plans.append(formatted_plan)
        
        # Format conversations
        formatted_conversations = [
            {
                'id': str(conv['_id']),
                'created_at': conv.get('created_at').isoformat() if conv.get('created_at') else None,
                'duration_minutes': conv.get('duration_minutes', 0),
                'message_count': len(conv.get('messages', [])),
                'language': conv.get('language'),
                'level': conv.get('level')
            } for conv in all_conversations
        ]
        
        # Generate AI Insights
        ai_insights = generate_ai_insights(user, formatted_plans, formatted_conversations)
        
        return {
            'profile': {
                'id': str(user['_id']),
                'name': user.get('name'),
                'email': user.get('email'),
                'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
                'total_sessions': total_sessions,
                'total_minutes': total_minutes,
                'languages_studied': list(set([plan['language'] for plan in formatted_plans]))
            },
            'all_learning_plans': formatted_plans,
            'practice_sessions': formatted_conversations,
            'subscription': {
                'status': subscription.get('status') if subscription else 'none',
                'minutes_remaining': subscription.get('minutes_remaining', 0) if subscription else 0,
                'plan_type': subscription.get('plan_type') if subscription else None
            } if subscription else None,
            'tutor': tutor_info,
            'ai_insights': ai_insights,
            'consent_given': learner.get('consent_given', False),
            'enrolled_at': learner.get('enrolled_at').isoformat() if learner.get('enrolled_at') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comprehensive learner details: {str(e)}")


def generate_ai_insights(user, learning_plans, conversations):
    """Generate AI-powered insights from learner data"""
    
    total_sessions = sum([plan['completed_sessions'] for plan in learning_plans])
    total_minutes = sum([plan['practice_minutes_used'] for plan in learning_plans])
    
    # Calculate average progress
    avg_progress = sum([plan['progress_percentage'] for plan in learning_plans]) / len(learning_plans) if learning_plans else 0
    
    # Analyze session patterns
    if conversations:
        session_hours = []
        for conv in conversations:
            try:
                if conv['created_at']:
                    from datetime import datetime
                    dt = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                    session_hours.append(dt.hour)
            except:
                pass
        
        peak_hour = max(set(session_hours), key=session_hours.count) if session_hours else 12
        learning_time = "morning" if peak_hour < 12 else "afternoon" if peak_hour < 17 else "evening"
    else:
        learning_time = "unknown"
    
    # Calculate progress rate
    user_created = user.get('created_at')
    if user_created:
        try:
            from datetime import datetime
            days_active = (datetime.utcnow() - user_created).days
            if days_active > 0:
                sessions_per_week = (total_sessions / days_active) * 7
            else:
                sessions_per_week = total_sessions
        except:
            sessions_per_week = 1
    else:
        sessions_per_week = 1
    
    if sessions_per_week > 3:
        progress_rate = "fast"
        progress_description = "above average"
    elif sessions_per_week > 1.5:
        progress_rate = "moderate"
        progress_description = "steady"
    else:
        progress_rate = "slow"
        progress_description = "needs attention"
    
    # Engagement analysis
    if sessions_per_week > 2:
        consistency = "high"
    elif sessions_per_week > 1:
        consistency = "moderate"
    else:
        consistency = "low"
    
    # Multi-language insights
    is_multi_language = len(learning_plans) > 1
    
    # Generate recommendations
    recommendations = []
    
    for plan in learning_plans:
        lang = plan['language'].title()
        
        # Low progress check
        if plan['progress_percentage'] < 30:
            recommendations.append(f"📈 Increase {lang} practice frequency to accelerate progress")
        
        # Check weak skills from assessment
        if 'assessment_data' in plan and 'skill_scores' in plan['assessment_data']:
            weak_skills = [
                skill for skill, score in plan['assessment_data']['skill_scores'].items() 
                if score < 60
            ]
            for skill in weak_skills[:2]:  # Top 2 weak skills
                recommendations.append(f"🎯 Focus on improving {lang} {skill}")
        
        # Check areas for improvement
        if 'assessment_data' in plan and 'areas_for_improvement' in plan['assessment_data']:
            for area in plan['assessment_data']['areas_for_improvement'][:1]:
                recommendations.append(f"💡 {lang}: {area}")
    
    # Consistency recommendation
    if consistency == "low":
        recommendations.append("⏰ Try to practice more regularly - aim for at least 2 sessions per week")
    
    # Multi-language recommendation
    if is_multi_language:
        recommendations.append("🌍 Balance practice time across both languages for optimal retention")
    
    # Overall summary
    language_list = ", ".join([plan['language'].title() for plan in learning_plans])
    summary = f"This learner is studying {language_list} with {progress_description} progress. "
    summary += f"They have completed {total_sessions} practice sessions totaling {total_minutes} minutes. "
    summary += f"Most active during {learning_time} hours with {consistency} consistency. "
    
    if is_multi_language:
        summary += f"As a multi-language learner, they are developing skills across {len(learning_plans)} languages simultaneously."
    
    # Plan-specific insights
    plan_insights = {}
    for plan in learning_plans:
        plan_id = plan['id']
        lang = plan['language'].title()
        progress = plan['progress_percentage']
        
        if progress < 20:
            insight = f"Just getting started with {lang}. Early progress shows engagement."
        elif progress < 50:
            insight = f"Building foundation in {lang}. Keep the momentum going!"
        elif progress < 80:
            insight = f"Strong progress in {lang}. Approaching mastery of current level."
        else:
            insight = f"Excellent work in {lang}! Nearly completed the learning plan."
        
        # Add assessment-based insight
        if 'assessment_data' in plan and 'strengths' in plan['assessment_data']:
            strengths = plan['assessment_data'].get('strengths', [])
            if strengths:
                insight += f" Key strength: {strengths[0]}"
        
        plan_insights[plan_id] = insight
    
    return {
        'overall_summary': summary,
        'learning_style': {
            'preferred_time': learning_time,
            'type': 'multi-language' if is_multi_language else 'focused'
        },
        'progress_rate': {
            'rate': progress_rate,
            'description': progress_description,
            'sessions_per_week': round(sessions_per_week, 1)
        },
        'engagement': {
            'consistency': consistency,
            'total_sessions': total_sessions,
            'total_minutes': total_minutes,
            'average_session_duration': round(total_minutes / total_sessions, 1) if total_sessions > 0 else 0
        },
        'recommendations': recommendations[:6],  # Top 6 recommendations
        'plan_specific_insights': plan_insights,
        'multi_language_learner': is_multi_language
    }


@router.get("/{institution_id}/learners/export",
            dependencies=[Depends(check_feature_enabled)])
async def export_learners(institution_id: str) -> Dict[str, Any]:
    """
    Export learner data as CSV format data
    """
    try:
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        export_data = []
        for learner in learners:
            user_id = learner.get("user_id")
            if user_id:
                try:
                    user = await database.users.find_one({"_id": ObjectId(user_id)})
                    if user:
                        # Get tutor info
                        tutor_email = ""
                        if learner.get("tutor_id"):
                            tutor = await database.tutors.find_one({"_id": ObjectId(learner["tutor_id"])})
                            if tutor:
                                tutor_email = tutor.get("email", "")
                        
                        export_data.append({
                            "name": user.get("name"),
                            "email": user.get("email"),
                            "language": user.get("preferred_language") or "",
                            "level": user.get("preferred_level") or "",
                            "tutor_email": tutor_email,
                            "enrolled_at": str(learner.get("enrolled_at", "")),
                            "consent_given": learner.get("consent_given", False)
                        })
                except:
                    pass
        
        return {
            "total_records": len(export_data),
            "data": export_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export learners: {str(e)}")
