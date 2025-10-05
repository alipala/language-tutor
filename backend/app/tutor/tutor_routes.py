"""
Tutor Dashboard Routes
Provides all tutor-specific endpoints for dashboard functionality
Includes: Authentication, Learner Management, Analytics, Reports
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from database import database
from app.tutor.tutor_auth import (
    TutorLoginRequest,
    TutorLoginResponse,
    TutorChangePasswordRequest,
    authenticate_tutor,
    create_tutor_access_token,
    get_current_tutor,
    verify_tutor_access,
    update_tutor_password,
    validate_password_strength
)

router = APIRouter(prefix="/tutor", tags=["tutor-dashboard"])


# ============================================================================
# PHASE 1: AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/login", response_model=TutorLoginResponse)
async def tutor_login(credentials: TutorLoginRequest) -> TutorLoginResponse:
    """
    Tutor login endpoint
    
    Returns JWT token and tutor information
    Rejects if tutor is inactive or has no password set
    """
    try:
        # Authenticate tutor
        tutor = await authenticate_tutor(credentials.email, credentials.password)
        
        if not tutor:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        token_data = {
            "sub": str(tutor["_id"]),
            "email": tutor["email"],
            "name": tutor["name"],
            "institution_id": tutor["institution_id"]
        }
        
        access_token = create_tutor_access_token(token_data)
        
        # Return response
        return TutorLoginResponse(
            access_token=access_token,
            token_type="bearer",
            tutor_id=str(tutor["_id"]),
            name=tutor["name"],
            email=tutor["email"],
            first_login=tutor.get("first_login", False),
            institution_id=tutor["institution_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TUTOR_LOGIN] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/change-password")
async def change_password(
    request: TutorChangePasswordRequest,
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, str]:
    """
    Change tutor password
    
    Validates current password and updates to new password
    Clears first_login flag
    """
    try:
        # Verify current password
        from app.tutor.tutor_auth import verify_password
        
        if not verify_password(request.current_password, current_tutor["hashed_password"]):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        is_valid, message = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Update password
        success = await update_tutor_password(
            str(current_tutor["_id"]),
            request.new_password
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHANGE_PASSWORD] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password change failed")


# ============================================================================
# PHASE 1 & 2: LEARNERS LIST WITH FILTERING
# ============================================================================

@router.get("/dashboard/{tutor_id}/learners")
async def get_assigned_learners(
    tutor_id: str,
    # Phase 2: Filter parameters
    language: Optional[str] = Query(None, description="Filter by language"),
    level: Optional[str] = Query(None, description="Filter by proficiency level (A1-C2)"),
    status: Optional[str] = Query(None, description="Filter by progress status (on_track|at_risk|inactive)"),
    last_activity: Optional[str] = Query(None, description="Filter by last activity (today|week|month|1month|2months)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, Any]:
    """
    Get all learners assigned to this tutor with progress data
    
    PHASE 1: Basic learner list
    PHASE 2: Advanced filtering by language, level, status, activity
    
    Security: Verifies tutor can only access their own learners
    """
    try:
        # Security: Verify tutor_id matches authenticated tutor
        await verify_tutor_access(tutor_id, current_tutor)
        
        # Build aggregation pipeline
        # Get tutor's institution_id for security filtering
        tutor = await database.tutors.find_one({"_id": ObjectId(tutor_id)})
        if not tutor:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        institution_id = tutor.get("institution_id")
        
        pipeline = [
            # Match learners assigned to this tutor AND institution
            {
                "$match": {
                    "tutor_id": tutor_id,
                    "institution_id": institution_id,  # Security: Only learners from same institution
                    "is_active": True
                }
            },
            # Lookup user data
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
            # Lookup learning plans
            {
                "$lookup": {
                    "from": "learning_plans",
                    "localField": "user_id",
                    "foreignField": "user_id",
                    "as": "learning_plans"
                }
            },
            # Lookup conversations for last activity
            {
                "$lookup": {
                    "from": "conversations",
                    "localField": "user_id",
                    "foreignField": "user_id",
                    "as": "conversations"
                }
            },
            # Unwind user data
            {
                "$unwind": {
                    "path": "$user_data",
                    "preserveNullAndEmptyArrays": False
                }
            }
        ]
        
        learners = await database.institutional_learners.aggregate(pipeline).to_list(length=None)
        
        # Process and format learners
        formatted_learners = []
        now = datetime.utcnow()
        
        for learner in learners:
            user = learner.get("user_data", {})
            learning_plans = learner.get("learning_plans", [])
            conversations = learner.get("conversations", [])
            
            # Get most recent learning plan (may be None for new learners)
            main_plan = learning_plans[0] if learning_plans else None
            
            # Calculate last activity from conversations
            last_activity_date = None
            if conversations:
                sorted_convs = sorted(conversations, key=lambda x: x.get("created_at", datetime.min), reverse=True)
                last_activity_date = sorted_convs[0].get("created_at")
            
            # Calculate days since last activity
            days_since_activity = 999  # Default to large number
            if last_activity_date:
                days_since_activity = (now - last_activity_date).days
            
            if main_plan:
                # Learner HAS a learning plan
                # Calculate progress status (PHASE 2: Business Logic)
                progress_status = calculate_progress_status(main_plan, days_since_activity, learner)
                
                # Get assessment score from learning plan
                assessment_data = main_plan.get("assessment_data", {})
                assessment_score = assessment_data.get("overall_score", 0)
                
                # Get last session summary
                session_summaries = main_plan.get("session_summaries", [])
                last_session_summary = session_summaries[-1] if session_summaries else None
                
                # Get next focus area from assessment
                areas_for_improvement = assessment_data.get("areas_for_improvement", [])
                next_focus_area = areas_for_improvement[0] if areas_for_improvement else "Continue practicing"
                
                # Format learning plan
                formatted_plan = {
                    "id": main_plan.get("id"),
                    "language": main_plan.get("language"),
                    "proficiency_level": main_plan.get("proficiency_level"),
                    "progress_percentage": round(main_plan.get("progress_percentage", 0), 1),
                    "progress_status": progress_status,
                    "last_activity_date": last_activity_date.isoformat() if last_activity_date else None,
                    "days_since_activity": days_since_activity,
                    "completed_sessions": main_plan.get("completed_sessions", 0),
                    "total_sessions": main_plan.get("total_sessions", 16),
                    "assessment_score": assessment_score,
                    "last_session_summary": last_session_summary,
                    "next_focus_area": next_focus_area
                }
                
                # PHASE 2: Apply filters (only if learner has a plan)
                if language and formatted_plan["language"].lower() != language.lower():
                    continue
                
                if level and formatted_plan["proficiency_level"] != level:
                    continue
                
                if status and formatted_plan["progress_status"] != status:
                    continue
                
                if last_activity:
                    if not should_include_by_activity(days_since_activity, last_activity):
                        continue
            else:
                # Learner DOES NOT have a learning plan yet (new learner)
                # Get target languages from user profile
                target_languages = user.get("target_languages", [])
                language_str = target_languages[0] if target_languages else "Not set"
                
                # Create placeholder plan data
                formatted_plan = {
                    "id": None,
                    "language": language_str,
                    "proficiency_level": user.get("level", "Not set"),
                    "progress_percentage": 0,
                    "progress_status": "inactive",  # New learners are inactive until they start
                    "last_activity_date": None,
                    "days_since_activity": 999,
                    "completed_sessions": 0,
                    "total_sessions": 16,
                    "assessment_score": 0,
                    "last_session_summary": None,
                    "next_focus_area": "Complete initial assessment"
                }
                
                # Apply filters (with defaults for new learners)
                if language and formatted_plan["language"].lower() != language.lower():
                    continue
                
                if level and formatted_plan["proficiency_level"] != level:
                    continue
                
                if status and formatted_plan["progress_status"] != status:
                    continue
                
                # Skip last_activity filter for new learners (they have no activity)
            
            # Format learner (common for both cases)
            formatted_learner = {
                "id": str(learner["_id"]),
                "user_id": str(user.get("_id", "")),
                "name": user.get("name"),
                "email": user.get("email"),
                "enrolled_at": learner.get("enrolled_at").isoformat() if learner.get("enrolled_at") else None,
                "consent_given": learner.get("consent_given", False),
                "learning_plans": [formatted_plan]
            }
            
            # Apply search filter (common for both cases)
            if search:
                search_lower = search.lower()
                if search_lower not in formatted_learner["name"].lower() and \
                   search_lower not in formatted_learner["email"].lower():
                    continue
            
            formatted_learners.append(formatted_learner)
        
        # Calculate summary statistics (before pagination)
        total_learners = len(formatted_learners)
        active_learners = sum(1 for l in formatted_learners 
                             if l["learning_plans"][0]["progress_status"] == "on_track")
        at_risk_count = sum(1 for l in formatted_learners 
                           if l["learning_plans"][0]["progress_status"] == "at_risk")
        inactive_count = sum(1 for l in formatted_learners 
                            if l["learning_plans"][0]["progress_status"] == "inactive")
        
        # Apply pagination
        total_pages = (total_learners + per_page - 1) // per_page if total_learners > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_learners = formatted_learners[start_idx:end_idx]
        
        return {
            "total_learners": total_learners,
            "active_learners": active_learners,
            "at_risk_count": at_risk_count,
            "inactive_count": inactive_count,
            "learners": paginated_learners,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total_learners,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GET_LEARNERS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get learners: {str(e)}")


def calculate_progress_status(learning_plan: dict, days_since_activity: int, learner: dict) -> str:
    """
    Calculate progress status based on business logic
    
    Returns: "on_track" | "at_risk" | "inactive"
    """
    # Check if learner account is deactivated
    if not learner.get("is_active", True):
        return "inactive"
    
    # Inactive: No activity in over 14 days
    if days_since_activity > 14:
        return "inactive"
    
    # Calculate expected progress
    created_at = learning_plan.get("created_at", datetime.utcnow())
    weeks_elapsed = max((datetime.utcnow() - created_at).days / 7, 0.1)
    total_weeks = 8  # Assuming 8-week plans
    expected_progress = (weeks_elapsed / total_weeks) * 100
    actual_progress = learning_plan.get("progress_percentage", 0)
    
    # At Risk: Behind schedule OR low engagement
    completed_sessions = learning_plan.get("completed_sessions", 0)
    expected_sessions = weeks_elapsed * 2  # 2 sessions per week
    
    if (actual_progress < (expected_progress - 15) or  # More than 15% behind
        (days_since_activity > 7 and days_since_activity <= 14) or  # 7-14 days inactive
        completed_sessions < (expected_sessions * 0.7)):  # Less than 70% of expected sessions
        return "at_risk"
    
    # On Track: Within 15% of expected progress AND activity in last 7 days
    if actual_progress >= (expected_progress - 15) and days_since_activity <= 7:
        return "on_track"
    
    # Default to at_risk if doesn't match other criteria
    return "at_risk"


def should_include_by_activity(days_since_activity: int, filter_value: str) -> bool:
    """Check if learner should be included based on activity filter"""
    if filter_value == "today" and days_since_activity < 1:
        return True
    elif filter_value == "week" and days_since_activity < 7:
        return True
    elif filter_value == "month" and days_since_activity < 30:
        return True
    elif filter_value == "1month" and days_since_activity > 30:
        return True
    elif filter_value == "2months" and days_since_activity > 60:
        return True
    else:
        return False


# ============================================================================
# PHASE 3: LEARNER DETAILS & ANALYTICS
# ============================================================================

@router.get("/dashboard/{tutor_id}/learner/{user_id}/details")
async def get_learner_details(
    tutor_id: str,
    user_id: str,
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, Any]:
    """
    Get comprehensive learner details (respects consent_given)
    
    Security:
    - Verifies tutor_id matches authenticated tutor
    - Checks learner is assigned to this tutor
    - Respects consent_given field
    """
    try:
        # Security: Verify tutor_id matches authenticated tutor
        await verify_tutor_access(tutor_id, current_tutor)
        
        # Check if learner is assigned to this tutor
        learner = await database.institutional_learners.find_one({
            "user_id": user_id,
            "tutor_id": tutor_id,
            "is_active": True
        })
        
        if not learner:
            raise HTTPException(
                status_code=404,
                detail="Learner not found or not assigned to you"
            )
        
        # Check consent
        if not learner.get("consent_given", False):
            raise HTTPException(
                status_code=403,
                detail="Learner has not provided consent for detailed data access"
            )
        
        # Reuse institution dashboard comprehensive details logic
        # Get user info
        user = await database.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get ALL learning plans
        all_learning_plans = await database.learning_plans.find({"user_id": user_id}).to_list(length=None)
        
        # Get ALL conversation sessions from BOTH collections
        conversations = await database.conversations.find({
            "user_id": user_id
        }).sort("created_at", -1).to_list(length=None)
        
        conversation_sessions = await database.conversation_sessions.find({
            "user_id": user_id
        }).sort("created_at", -1).to_list(length=None)
        
        all_conversations = conversations + conversation_sessions
        
        # Get subscription info
        subscription = await database.subscriptions.find_one({"user_id": user_id})
        
        # Calculate overall metrics
        total_sessions = sum([plan.get("completed_sessions", 0) for plan in all_learning_plans])
        total_minutes = sum([plan.get("practice_minutes_used", 0) for plan in all_learning_plans])
        
        # Format learning plans
        formatted_plans = []
        for plan in all_learning_plans:
            formatted_plan = {
                "id": plan.get("id"),
                "language": plan.get("language"),
                "proficiency_level": plan.get("proficiency_level"),
                "progress_percentage": plan.get("progress_percentage", 0),
                "completed_sessions": plan.get("completed_sessions", 0),
                "total_sessions": plan.get("total_sessions", 16),
                "practice_minutes_used": plan.get("practice_minutes_used", 0),
                "total_practice_minutes": plan.get("total_practice_minutes", 80),
                "created_at": plan.get("created_at").isoformat() if plan.get("created_at") else None,
                "assessment_data": plan.get("assessment_data", {}),
                "plan_content": {
                    "title": plan.get("plan_content", {}).get("title"),
                    "assessment_summary": plan.get("plan_content", {}).get("assessment_summary", {}),
                    "learning_objectives": plan.get("plan_content", {}).get("learning_objectives", []),
                    "weekly_schedule": plan.get("plan_content", {}).get("weekly_schedule", [])
                },
                "session_summaries": plan.get("session_summaries", [])
            }
            formatted_plans.append(formatted_plan)
        
        # Format conversations
        formatted_conversations = [
            {
                "id": str(conv["_id"]),
                "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
                "duration_minutes": conv.get("duration_minutes", 0),
                "message_count": len(conv.get("messages", [])),
                "language": conv.get("language"),
                "level": conv.get("level")
            } for conv in all_conversations
        ]
        
        # Generate AI Insights (reuse from institution dashboard)
        ai_insights = generate_tutor_ai_insights(user, formatted_plans, formatted_conversations)
        
        return {
            "profile": {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                "total_sessions": total_sessions,
                "total_minutes": total_minutes,
                "languages_studied": list(set([plan["language"] for plan in formatted_plans]))
            },
            "all_learning_plans": formatted_plans,
            "practice_sessions": formatted_conversations,
            "subscription": {
                "status": subscription.get("status") if subscription else "none",
                "minutes_remaining": subscription.get("minutes_remaining", 0) if subscription else 0,
                "plan_type": subscription.get("plan_type") if subscription else None
            } if subscription else None,
            "ai_insights": ai_insights,
            "consent_given": learner.get("consent_given", False),
            "enrolled_at": learner.get("enrolled_at").isoformat() if learner.get("enrolled_at") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GET_LEARNER_DETAILS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get learner details: {str(e)}")


@router.get("/dashboard/{tutor_id}/analytics")
async def get_tutor_analytics(
    tutor_id: str,
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, Any]:
    """
    Get tutor's personal statistics and analytics
    
    Returns overview of all assigned learners' progress
    """
    try:
        # Security: Verify tutor_id matches authenticated tutor
        await verify_tutor_access(tutor_id, current_tutor)
        
        # Get all assigned learners
        learners = await database.institutional_learners.find({
            "tutor_id": tutor_id,
            "is_active": True
        }).to_list(length=None)
        
        if not learners:
            return {
                "total_assigned_learners": 0,
                "active_learners": 0,
                "at_risk_learners": 0,
                "inactive_learners": 0,
                "average_progress": 0,
                "total_sessions_completed": 0,
                "total_minutes_practiced": 0,
                "languages_taught": [],
                "level_distribution": {},
                "recent_activity": []
            }
        
        # Get user IDs
        user_ids = [l["user_id"] for l in learners]
        
        # Get learning plans for all learners
        learning_plans = await database.learning_plans.find({
            "user_id": {"$in": user_ids}
        }).to_list(length=None)
        
        # Calculate statistics
        total_sessions = sum([plan.get("completed_sessions", 0) for plan in learning_plans])
        total_minutes = sum([plan.get("practice_minutes_used", 0) for plan in learning_plans])
        total_progress = sum([plan.get("progress_percentage", 0) for plan in learning_plans])
        average_progress = total_progress / len(learning_plans) if learning_plans else 0
        
        # Get unique languages
        languages_taught = list(set([plan.get("language") for plan in learning_plans if plan.get("language")]))
        
        # Level distribution
        level_distribution = {}
        for plan in learning_plans:
            level = plan.get("proficiency_level", "Unknown")
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # Count learners by status (simplified - would need full calculation)
        active_count = len(learners)  # All are active since we filtered
        at_risk_count = 0
        inactive_count = 0
        
        # Get recent conversations for activity
        recent_conversations = await database.conversations.find({
            "user_id": {"$in": user_ids}
        }).sort("created_at", -1).limit(10).to_list(length=10)
        
        recent_activity = [
            {
                "learner_id": conv.get("user_id"),
                "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
                "language": conv.get("language"),
                "duration_minutes": conv.get("duration_minutes", 0)
            } for conv in recent_conversations
        ]
        
        return {
            "total_assigned_learners": len(learners),
            "active_learners": active_count,
            "at_risk_learners": at_risk_count,
            "inactive_learners": inactive_count,
            "average_progress": round(average_progress, 1),
            "total_sessions_completed": total_sessions,
            "total_minutes_practiced": total_minutes,
            "languages_taught": languages_taught,
            "level_distribution": level_distribution,
            "recent_activity": recent_activity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GET_ANALYTICS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# ============================================================================
# PHASE 4: REPORT GENERATION
# ============================================================================

@router.post("/dashboard/{tutor_id}/reports/generate")
async def generate_learner_report(
    tutor_id: str,
    report_request: Dict[str, Any],
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, Any]:
    """
    Generate PDF report for a learner
    
    Request body:
    {
        "learner_id": "user_id",
        "sections": ["profile", "learning_plans", "assessment_results", ...],
        "date_range": {"start": "2025-01-01", "end": "2025-10-05"}
    }
    """
    try:
        # Security: Verify tutor_id matches authenticated tutor
        await verify_tutor_access(tutor_id, current_tutor)
        
        learner_id = report_request.get("learner_id")
        sections = report_request.get("sections", [])
        date_range = report_request.get("date_range", {})
        
        if not learner_id:
            raise HTTPException(status_code=400, detail="learner_id is required")
        
        # Verify learner is assigned to this tutor
        learner = await database.institutional_learners.find_one({
            "user_id": learner_id,
            "tutor_id": tutor_id,
            "is_active": True
        })
        
        if not learner:
            raise HTTPException(
                status_code=404,
                detail="Learner not found or not assigned to you"
            )
        
        # Check consent
        if not learner.get("consent_given", False):
            raise HTTPException(
                status_code=403,
                detail="Learner has not provided consent for report generation"
            )
        
        # For now, return placeholder - actual PDF generation would go here
        # Would integrate with existing professional_pdf_generator.py
        
        report_id = str(ObjectId())
        
        # In production, would:
        # 1. Generate PDF using professional_pdf_generator.py
        # 2. Store in tutor_reports collection
        # 3. Return download URL
        
        return {
            "report_id": report_id,
            "download_url": f"/api/v1/tutor/reports/{report_id}/download",
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "message": "Report generation initiated. Download will be available shortly."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GENERATE_REPORT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, Any]:
    """
    Download generated PDF report
    
    Returns: PDF file stream (to be implemented)
    """
    try:
        # For now, return placeholder
        # In production, would:
        # 1. Verify report belongs to this tutor
        # 2. Check if report exists and not expired
        # 3. Return PDF file stream
        
        return {
            "message": "Report download endpoint - PDF generation to be implemented",
            "report_id": report_id
        }
        
    except Exception as e:
        print(f"[DOWNLOAD_REPORT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_tutor_ai_insights(user, learning_plans, conversations):
    """Generate AI-powered insights for tutor view"""
    # Reuse logic from institution dashboard with tutor-specific messaging
    
    total_sessions = sum([plan["completed_sessions"] for plan in learning_plans])
    total_minutes = sum([plan["practice_minutes_used"] for plan in learning_plans])
    
    # Calculate average progress
    avg_progress = sum([plan["progress_percentage"] for plan in learning_plans]) / len(learning_plans) if learning_plans else 0
    
    # Analyze session patterns
    if conversations:
        session_hours = []
        for conv in conversations:
            try:
                if conv["created_at"]:
                    dt = datetime.fromisoformat(conv["created_at"].replace("Z", "+00:00"))
                    session_hours.append(dt.hour)
            except:
                pass
        
        peak_hour = max(set(session_hours), key=session_hours.count) if session_hours else 12
        learning_time = "morning" if peak_hour < 12 else "afternoon" if peak_hour < 17 else "evening"
    else:
        learning_time = "unknown"
    
    # Calculate progress rate
    user_created = user.get("created_at")
    if user_created:
        try:
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
        progress_description = "excellent"
    elif sessions_per_week > 1.5:
        progress_rate = "moderate"
        progress_description = "good"
    else:
        progress_rate = "slow"
        progress_description = "needs encouragement"
    
    # Engagement analysis
    if sessions_per_week > 2:
        consistency = "high"
    elif sessions_per_week > 1:
        consistency = "moderate"
    else:
        consistency = "low"
    
    # Generate recommendations for tutor
    recommendations = []
    
    for plan in learning_plans:
        lang = plan["language"].title()
        
        if plan["progress_percentage"] < 30:
            recommendations.append(f"Consider scheduling additional {lang} practice sessions")
        
        if "assessment_data" in plan and "skill_scores" in plan["assessment_data"]:
            weak_skills = [
                skill for skill, score in plan["assessment_data"]["skill_scores"].items() 
                if score < 60
            ]
            for skill in weak_skills[:2]:
                recommendations.append(f"Focus on {lang} {skill} exercises in next session")
    
    # Consistency recommendation
    if consistency == "low":
        recommendations.append("Schedule regular check-ins to improve consistency")
    
    # Overall summary
    language_list = ", ".join([plan["language"].title() for plan in learning_plans])
    summary = f"Learner is studying {language_list} with {progress_description} progress. "
    summary += f"Completed {total_sessions} sessions ({total_minutes} minutes). "
    summary += f"Most active during {learning_time} with {consistency} consistency."
    
    return {
        "overall_summary": summary,
        "learning_style": {
            "preferred_time": learning_time,
            "sessions_per_week": round(sessions_per_week, 1)
        },
        "progress_rate": {
            "rate": progress_rate,
            "description": progress_description
        },
        "engagement": {
            "consistency": consistency,
            "total_sessions": total_sessions,
            "total_minutes": total_minutes
        },
        "recommendations": recommendations[:5]
    }
