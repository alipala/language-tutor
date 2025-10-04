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

router = APIRouter(prefix="/api/v1/institution/dashboard", tags=["institution-dashboard"])

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
        # Get all learners for this institution
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        # Get user IDs
        user_ids = [ObjectId(l["user_id"]) for l in learners if l.get("user_id")]
        
        # Aggregate language distribution
        pipeline = [
            {"$match": {"_id": {"$in": user_ids}}},
            {"$group": {
                "_id": "$preferred_language",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await database.users.aggregate(pipeline).to_list(length=None)
        
        # Format results
        distribution = []
        total = 0
        for result in results:
            language = result["_id"] or "Not Set"
            count = result["count"]
            total += count
            distribution.append({
                "language": language,
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
        # Get all learners for this institution
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        # Get user IDs
        user_ids = [ObjectId(l["user_id"]) for l in learners if l.get("user_id")]
        
        # Aggregate level distribution
        pipeline = [
            {"$match": {"_id": {"$in": user_ids}}},
            {"$group": {
                "_id": "$preferred_level",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}  # Sort by level (A1, A2, B1, B2, C1, C2)
        ]
        
        results = await database.users.aggregate(pipeline).to_list(length=None)
        
        # Format results with proper ordering
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2", None]
        distribution = []
        total = 0
        
        for level in level_order:
            matching = [r for r in results if r["_id"] == level]
            if matching:
                count = matching[0]["count"]
                total += count
                distribution.append({
                    "level": level or "Not Set",
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
    Get all tutors for an institution with their assigned learners
    """
    try:
        # Get all tutors sorted by creation date (newest first)
        tutors = await database.tutors.find({
            "institution_id": institution_id,
            "is_active": True
        }).sort("created_at", -1).to_list(length=None)
        
        # For each tutor, get their assigned learners
        tutor_list = []
        for tutor in tutors:
            tutor_id = str(tutor["_id"])
            
            # Get learner count and list
            learners = await database.institutional_learners.find({
                "institution_id": institution_id,
                "tutor_id": tutor_id,
                "is_active": True
            }).to_list(length=None)
            
            # Get learner details
            learner_details = []
            for learner in learners:
                user_id = learner.get("user_id")
                if user_id:
                    try:
                        user = await database.users.find_one({"_id": ObjectId(user_id)})
                        if user:
                            learner_details.append({
                                "user_id": str(user["_id"]),
                                "name": user.get("name"),
                                "email": user.get("email"),
                                "language": user.get("preferred_language"),
                                "level": user.get("preferred_level"),
                                "enrolled_at": learner.get("enrolled_at")
                            })
                    except:
                        pass
            
            tutor_list.append({
                "id": tutor_id,
                "name": tutor.get("name"),
                "email": tutor.get("email"),
                "bio": tutor.get("bio"),
                "specializations": tutor.get("specializations", []),
                "learner_count": len(learners),
                "learners": learner_details,
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
    """
    try:
        # Validate required fields
        if not tutor_data.get("name") or not tutor_data.get("email"):
            raise HTTPException(status_code=400, detail="Name and email are required")
        
        # Check if tutor email already exists
        existing = await database.tutors.find_one({"email": tutor_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Tutor with this email already exists")
        
        # Create tutor document
        tutor = {
            "name": tutor_data["name"],
            "email": tutor_data["email"],
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
            "message": "Tutor added successfully",
            "tutor_id": str(result.inserted_id),
            "tutor": {
                "id": str(result.inserted_id),
                "name": tutor["name"],
                "email": tutor["email"],
                "bio": tutor["bio"],
                "specializations": tutor["specializations"],
                "permissions": tutor["permissions"],
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
    Remove/deactivate a tutor
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
    Get all learners for an institution with progress data
    """
    try:
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        learner_list = []
        for learner in learners:
            user_id = learner.get("user_id")
            if user_id:
                try:
                    user = await database.users.find_one({"_id": ObjectId(user_id)})
                    if user:
                        # Get tutor info
                        tutor = None
                        if learner.get("tutor_id"):
                            tutor_doc = await database.tutors.find_one({"_id": ObjectId(learner["tutor_id"])})
                            if tutor_doc:
                                tutor = {
                                    "id": str(tutor_doc["_id"]),
                                    "name": tutor_doc.get("name"),
                                    "email": tutor_doc.get("email")
                                }
                        
                        # Get learning plan progress
                        progress = None
                        learning_plan = await database.learning_plans.find_one({"user_id": user_id})
                        if learning_plan:
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
                            "user_id": str(user["_id"]),
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
                except:
                    pass
        
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
    Deactivate/archive a learner
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


@router.get("/{institution_id}/learners/{user_id}/details",
            dependencies=[Depends(check_feature_enabled)])
async def get_learner_details(institution_id: str, user_id: str) -> Dict[str, Any]:
    """
    Get detailed learning progress for a specific learner (requires consent)
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
        
        # Get learning plan
        learning_plan = await database.learning_plans.find_one({'user_id': user_id})
        
        # Get conversation history (last 10 sessions)
        conversations = await database.conversations.find({
            'user_id': user_id
        }).sort('created_at', -1).limit(10).to_list(length=None)
        
        # Get subscription info
        subscription = await database.subscriptions.find_one({'user_id': user_id})
        
        # Format learning plan for response
        plan_data = None
        if learning_plan:
            plan_data = {
                'progress_percentage': learning_plan.get('progress_percentage', 0),
                'completed_sessions': learning_plan.get('completed_sessions', 0),
                'total_sessions': learning_plan.get('total_sessions', 16),
                'practice_minutes_used': learning_plan.get('practice_minutes_used', 0),
                'total_practice_minutes': learning_plan.get('total_practice_minutes', 80),
                'language': learning_plan.get('language'),
                'proficiency_level': learning_plan.get('proficiency_level'),
                'created_at': learning_plan.get('created_at')
            }
        
        return {
            'user': {
                'id': str(user['_id']),
                'name': user.get('name'),
                'email': user.get('email'),
                'preferred_language': user.get('preferred_language'),
                'preferred_level': user.get('preferred_level'),
                'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
            },
            'learning_plan': plan_data,
            'recent_sessions': [
                {
                    'id': str(conv['_id']),
                    'created_at': conv.get('created_at').isoformat() if conv.get('created_at') else None,
                    'duration_minutes': conv.get('duration_minutes', 0),
                    'message_count': len(conv.get('messages', [])),
                    'language': conv.get('language'),
                    'level': conv.get('level')
                } for conv in conversations
            ],
            'subscription': {
                'status': subscription.get('status') if subscription else 'none',
                'minutes_remaining': subscription.get('minutes_remaining', 0) if subscription else 0
            } if subscription else None,
            'consent_given': learner.get('consent_given', False),
            'enrolled_at': learner.get('enrolled_at').isoformat() if learner.get('enrolled_at') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learner details: {str(e)}")


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
