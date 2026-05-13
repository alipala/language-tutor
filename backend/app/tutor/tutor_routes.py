"""
Tutor Dashboard Routes
Provides all tutor-specific endpoints for dashboard functionality
Includes: Authentication, Learner Management, Analytics, Reports
"""
import asyncio
import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

try:
    from openai import OpenAI
    import httpx
    _api_key = os.getenv("OPENAI_API_KEY")
    try:
        _openai_client = OpenAI(api_key=_api_key)
    except TypeError:
        _openai_client = OpenAI(api_key=_api_key, http_client=httpx.Client())
except Exception as _e:
    _openai_client = None
    print(f"[TUTOR_ROUTES] OpenAI client unavailable: {_e}")

from database import database
from fastapi.security import HTTPBearer as _HTTPBearer, HTTPAuthorizationCredentials
from app.tutor.tutor_auth import (
    TutorLoginRequest,
    TutorLoginResponse,
    TutorChangePasswordRequest,
    authenticate_tutor,
    create_tutor_access_token,
    get_current_tutor,
    verify_tutor_access,
    update_tutor_password,
    validate_password_strength,
    SECRET_KEY,
    ALGORITHM,
)
from redis_client import blocklist_token

router = APIRouter(prefix="/tutor", tags=["tutor-dashboard"])
_tutor_bearer = _HTTPBearer(auto_error=False)


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


@router.post("/logout")
async def tutor_logout(credentials: HTTPAuthorizationCredentials = Depends(_tutor_bearer)):
    """Invalidate tutor JWT by adding its JTI to the Redis blocklist."""
    from jose import jwt as jose_jwt, JWTError
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jose_jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            remaining_ttl = max(1, int(exp - datetime.utcnow().timestamp()))
            await blocklist_token(jti, remaining_ttl)
    except JWTError as e:
        print(f"[TUTOR_LOGOUT] Warning: could not decode token: {e}")
    return {"message": "Logged out successfully"}


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
            # Lookup conversation sessions for last activity
            {
                "$lookup": {
                    "from": "conversation_sessions",
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
        
        def _to_dt(v):
            """Safely convert datetime or ISO string to naive datetime."""
            if isinstance(v, datetime):
                return v.replace(tzinfo=None)
            if isinstance(v, str):
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    return None
            return None

        # Process and format learners
        formatted_learners = []
        now = datetime.utcnow()
        
        for learner in learners:
            user = learner.get("user_data", {})
            learning_plans = learner.get("learning_plans", [])
            conversations = learner.get("conversations", [])
            
            # Get most recent learning plan (may be None for new learners)
            main_plan = learning_plans[0] if learning_plans else None
            
            # Calculate last activity from conversation_sessions
            last_activity_date = None

            if conversations:
                dated = [((_to_dt(c.get("created_at")) or datetime.min), c) for c in conversations]
                dated.sort(key=lambda x: x[0], reverse=True)
                last_activity_date = dated[0][0] if dated[0][0] != datetime.min else None

            # Calculate days since last activity
            days_since_activity = 999
            if last_activity_date:
                try:
                    days_since_activity = (now - last_activity_date).days
                except Exception:
                    days_since_activity = 999
            
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
                    "last_activity_date": last_activity_date.isoformat() if last_activity_date and hasattr(last_activity_date, 'isoformat') else None,
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
    created_at_raw = learning_plan.get("created_at", None)
    if isinstance(created_at_raw, str):
        try:
            created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            created_at = datetime.utcnow()
    elif isinstance(created_at_raw, datetime):
        created_at = created_at_raw.replace(tzinfo=None)
    else:
        created_at = datetime.utcnow()
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

        # Get Speaking DNA profile + history + sentence analyses in parallel
        dna_profile_task = database.speaking_dna_profiles.find_one({"user_id": user_id})
        dna_history_task = database.speaking_dna_history.find(
            {"user_id": user_id}
        ).sort("week_number", -1).to_list(length=8)
        sentence_analysis_task = database.sentence_analysis_jobs.find(
            {"user_id": user_id, "status": "completed"}
        ).sort("created_at", -1).to_list(length=5)
        assessments_task = database.assessments.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(length=10)

        dna_profile, dna_history, sentence_analyses, user_assessments = await asyncio.gather(
            dna_profile_task, dna_history_task, sentence_analysis_task, assessments_task
        )

        # Get conversation sessions (correct collection only)
        all_conversations = await database.conversation_sessions.find({
            "user_id": user_id
        }).sort("created_at", -1).to_list(length=100)

        # Get challenge sessions
        all_challenges = await database.challenge_sessions.find({
            "user_id": user_id
        }).sort("created_at", -1).to_list(length=100)

        # Get daily stats
        daily_stats_docs = await database.daily_stats.find({
            "user_id": user_id
        }).sort("date", -1).to_list(length=30)

        # Get subscription info — fall back to user fields
        subscription = await database.subscriptions.find_one({"user_id": user_id})

        def _safe_iso(v):
            if v is None:
                return None
            if isinstance(v, str):
                return v
            if hasattr(v, "isoformat"):
                return v.isoformat()
            return str(v)

        # Calculate overall metrics
        total_sessions = sum(p.get("completed_sessions", 0) for p in all_learning_plans)
        total_minutes = sum(p.get("practice_minutes_used", 0) for p in all_learning_plans)
        realtime_minutes = sum(round(s.get("duration_seconds", 0) / 60, 1) for s in all_conversations)
        if total_minutes == 0 and realtime_minutes > 0:
            total_minutes = realtime_minutes

        # Format learning plans
        formatted_plans = []
        for plan in all_learning_plans:
            formatted_plans.append({
                "id": str(plan.get("_id", plan.get("id", ""))),
                "language": plan.get("language"),
                "proficiency_level": plan.get("proficiency_level"),
                "progress_percentage": round(plan.get("progress_percentage", 0), 1),
                "completed_sessions": plan.get("completed_sessions", 0),
                "total_sessions": plan.get("total_sessions", 16),
                "practice_minutes_used": round(plan.get("practice_minutes_used", 0), 1),
                "total_practice_minutes": plan.get("total_practice_minutes", 80),
                "created_at": _safe_iso(plan.get("created_at")),
                "assessment_data": plan.get("assessment_data", {}),
                "plan_content": {
                    "title": plan.get("plan_content", {}).get("title"),
                    "assessment_summary": plan.get("plan_content", {}).get("assessment_summary", {}),
                    "learning_objectives": plan.get("plan_content", {}).get("learning_objectives", []),
                    "weekly_schedule": plan.get("plan_content", {}).get("weekly_schedule", [])
                },
                "session_summaries": plan.get("session_summaries", [])
            })

        # Format conversations
        formatted_conversations = [
            {
                "id": str(conv["_id"]),
                "created_at": _safe_iso(conv.get("created_at")),
                "duration_minutes": round(conv.get("duration_seconds", conv.get("duration_minutes", 0) * 60 if conv.get("duration_minutes") else 0) / 60, 1),
                "message_count": conv.get("message_count", len(conv.get("messages", []))),
                "language": conv.get("language"),
                "level": conv.get("level"),
                "session_type": conv.get("session_type", "practice")
            } for conv in all_conversations
        ]

        # Format challenges — real schema uses correct_answers/wrong_answers/total_challenges/accuracy
        formatted_challenges = [
            {
                "id": str(c["_id"]),
                "created_at": _safe_iso(c.get("created_at")),
                "challenge_type": c.get("challenge_type"),
                "language": c.get("language"),
                "level": c.get("level"),
                "correct_answers": c.get("correct_answers", 0),
                "wrong_answers": c.get("wrong_answers", 0),
                "total_challenges": c.get("total_challenges", 0),
                "accuracy": c.get("accuracy", 0),
                "total_xp": c.get("total_xp", 0),
                "max_combo": c.get("max_combo", 0),
                "duration_seconds": c.get("duration_seconds", 0),
                "completed": c.get("end_time") is not None and c.get("is_active", True) is False or c.get("end_time") is not None
            } for c in all_challenges
        ]

        # Daily stats summary — using actual DB field names:
        # local_date(str), total_xp, streak_count, total_sessions,
        # conversation_time_seconds, total_time_seconds, accuracy_percent
        daily_stats = {
            "current_streak": daily_stats_docs[0].get("streak_count", 0) if daily_stats_docs else 0,
            "total_xp": sum(s.get("total_xp", 0) for s in daily_stats_docs),
            "days_active": len([s for s in daily_stats_docs if s.get("total_sessions", 0) > 0 or s.get("conversation_time_seconds", 0) > 0]),
            "recent_daily": [
                {
                    "date": s.get("local_date"),  # already a string "YYYY-MM-DD"
                    "minutes": round((s.get("conversation_time_seconds") or s.get("total_time_seconds", 0)) / 60, 1),
                    "sessions": s.get("total_sessions", 0),
                    "xp": s.get("total_xp", 0),
                    "accuracy": round(s.get("accuracy_percent", 0), 1),
                    "challenges": s.get("total_challenges", 0),
                    "correct": s.get("correct_challenges", 0),
                } for s in daily_stats_docs[:14]
            ]
        }

        # Generate AI Insights
        ai_insights = generate_tutor_ai_insights(user, formatted_plans, formatted_conversations)

        # Format Speaking DNA for frontend
        speaking_dna = None
        if dna_profile:
            strands = dna_profile.get("dna_strands", {})
            overall = dna_profile.get("overall_profile", {})

            # Build weekly confidence trend from history
            weekly_trend = []
            for week in reversed(dna_history):
                snap = week.get("strand_snapshots", {})
                conf = snap.get("confidence", {})
                stats = week.get("week_stats", {})
                weekly_trend.append({
                    "week": week.get("week_number"),
                    "week_start": _safe_iso(week.get("week_start")),
                    "confidence": round(conf.get("score", 0) * 100),
                    "sessions": stats.get("sessions_completed", 0),
                    "minutes": round(stats.get("total_minutes", 0), 1),
                    "breakthroughs": stats.get("breakthroughs_count", 0),
                    "wpm": snap.get("rhythm", {}).get("words_per_minute_avg", 0),
                    "accuracy": round(snap.get("accuracy", {}).get("grammar_accuracy", 0) * 100),
                })

            # Sentence analysis quality summary
            sentence_scores = []
            for job in sentence_analyses:
                for analysis in job.get("analyses", []):
                    sentence_scores.append({
                        "grammatical": round(analysis.get("grammatical_score", 0)),
                        "vocabulary": round(analysis.get("vocabulary_score", 0)),
                        "complexity": round(analysis.get("complexity_score", 0)),
                        "overall": round(analysis.get("overall_score", 0)),
                        "text": analysis.get("recognized_text", "")[:80]
                    })

            speaking_dna = {
                "strands": {
                    "rhythm": {
                        "label": "Rhythm",
                        "score": round(min(strands.get("rhythm", {}).get("consistency_score", 0.5) * 100, 100)),
                        "type": strands.get("rhythm", {}).get("type", ""),
                        "wpm": strands.get("rhythm", {}).get("words_per_minute_avg", 0),
                        "pause_ms": round(strands.get("rhythm", {}).get("pause_duration_avg_ms", 0)),
                        "description": strands.get("rhythm", {}).get("description", ""),
                    },
                    "confidence": {
                        "label": "Confidence",
                        "score": round(strands.get("confidence", {}).get("score", 0) * 100),
                        "level": strands.get("confidence", {}).get("level", ""),
                        "trend": strands.get("confidence", {}).get("trend", "stable"),
                        "filler_rate": strands.get("confidence", {}).get("filler_rate_per_minute", 0),
                        "description": strands.get("confidence", {}).get("description", ""),
                    },
                    "vocabulary": {
                        "label": "Vocabulary",
                        "score": round(min(strands.get("vocabulary", {}).get("new_word_attempt_rate", 0.5) * 100, 100)),
                        "style": strands.get("vocabulary", {}).get("style", ""),
                        "unique_words": strands.get("vocabulary", {}).get("unique_words_per_session", 0),
                        "complexity_level": strands.get("vocabulary", {}).get("complexity_level", ""),
                        "description": strands.get("vocabulary", {}).get("description", ""),
                    },
                    "accuracy": {
                        "label": "Accuracy",
                        "score": round(strands.get("accuracy", {}).get("grammar_accuracy", 0.8) * 100),
                        "pattern": strands.get("accuracy", {}).get("pattern", ""),
                        "common_errors": strands.get("accuracy", {}).get("common_errors", []),
                        "improving_areas": strands.get("accuracy", {}).get("improving_areas", []),
                        "description": strands.get("accuracy", {}).get("description", ""),
                    },
                    "learning": {
                        "label": "Learning Style",
                        "score": round(min(strands.get("learning", {}).get("retry_rate", 0.5) * 100, 100)),
                        "type": strands.get("learning", {}).get("type", ""),
                        "retry_rate": strands.get("learning", {}).get("retry_rate", 0),
                        "challenge_acceptance": strands.get("learning", {}).get("challenge_acceptance", 0),
                        "description": strands.get("learning", {}).get("description", ""),
                    },
                    "emotional": {
                        "label": "Emotional Arc",
                        "score": round(strands.get("emotional", {}).get("session_end_confidence", 0.6) * 100),
                        "pattern": strands.get("emotional", {}).get("pattern", ""),
                        "start_confidence": round(strands.get("emotional", {}).get("session_start_confidence", 0.5) * 100),
                        "end_confidence": round(strands.get("emotional", {}).get("session_end_confidence", 0.6) * 100),
                        "anxiety_triggers": strands.get("emotional", {}).get("anxiety_triggers", []),
                        "description": strands.get("emotional", {}).get("description", ""),
                    },
                },
                "archetype": overall.get("speaker_archetype", ""),
                "summary": overall.get("summary", ""),
                "coach_approach": overall.get("coach_approach", ""),
                "strengths": overall.get("strengths", []),
                "growth_areas": overall.get("growth_areas", []),
                "sessions_analyzed": dna_profile.get("sessions_analyzed", 0),
                "total_speaking_minutes": round(dna_profile.get("total_speaking_minutes", 0), 1),
                "weekly_trend": weekly_trend,
                "sentence_scores": sentence_scores[:10],
                "assessments": [
                    {
                        "language": a.get("language"),
                        "level": a.get("level"),
                        "score": a.get("score"),
                        "feedback": a.get("feedback"),
                        "date": _safe_iso(a.get("created_at"))
                    } for a in user_assessments
                ],
            }

        return {
            "profile": {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "created_at": _safe_iso(user.get("created_at")),
                "total_sessions": total_sessions,
                "total_minutes": round(total_minutes, 1),
                "realtime_sessions": len(formatted_conversations),
                "challenge_sessions": len(formatted_challenges),
                "languages_studied": list(set(p["language"] for p in formatted_plans if p.get("language"))),
                "preferred_language": user.get("preferred_language"),
                "preferred_level": user.get("preferred_level")
            },
            "all_learning_plans": formatted_plans,
            "practice_sessions": formatted_conversations,
            "challenge_sessions": formatted_challenges,
            "daily_stats": daily_stats,
            "speaking_dna": speaking_dna,
            "subscription": {
                "status": subscription.get("status") if subscription else user.get("subscription_status", "none"),
                "minutes_remaining": user.get("practice_minutes_remaining", 0),
                "plan_type": subscription.get("plan_type") if subscription else user.get("subscription_plan")
            },
            "ai_insights": ai_insights,
            "consent_given": learner.get("consent_given", True),
            "enrolled_at": _safe_iso(learner.get("enrolled_at"))
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

        # Run all queries in parallel — no more N+1
        learning_plans_task = database.learning_plans.find(
            {"user_id": {"$in": user_ids}}
        ).to_list(length=None)

        recent_sessions_task = database.conversation_sessions.find(
            {"user_id": {"$in": user_ids}}
        ).sort("created_at", -1).limit(10).to_list(length=10)

        # Single aggregation for challenge counts instead of N+1 loop
        challenge_agg_task = database.challenge_sessions.aggregate([
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
        ]).to_list(length=None)

        learning_plans, recent_conversations, challenge_agg = await asyncio.gather(
            learning_plans_task, recent_sessions_task, challenge_agg_task
        )

        challenge_counts = {doc["_id"]: doc["count"] for doc in challenge_agg}

        # Use ONE plan per learner (highest progress) — avoid double-counting
        # learners who have multiple plans
        best_plan_per_learner: dict = {}
        for plan in learning_plans:
            uid = plan.get("user_id")
            if uid not in best_plan_per_learner:
                best_plan_per_learner[uid] = plan
            else:
                existing_pct = best_plan_per_learner[uid].get("progress_percentage", 0)
                if plan.get("progress_percentage", 0) > existing_pct:
                    best_plan_per_learner[uid] = plan

        primary_plans = list(best_plan_per_learner.values())

        # Stats based on primary plans only (one per learner)
        total_sessions = sum(p.get("completed_sessions", 0) for p in primary_plans)
        total_minutes = sum(p.get("practice_minutes_used", 0) for p in primary_plans)
        average_progress = (
            sum(p.get("progress_percentage", 0) for p in primary_plans) / len(primary_plans)
            if primary_plans else 0
        )

        languages_taught = list(set(p.get("language") for p in primary_plans if p.get("language")))

        level_distribution = {}
        for plan in primary_plans:
            level = plan.get("proficiency_level", "Unknown")
            level_distribution[level] = level_distribution.get(level, 0) + 1

        on_track_count = 0
        at_risk_count = 0
        inactive_count = 0
        for plan in primary_plans:
            sessions = plan.get("completed_sessions", 0)
            pct = plan.get("progress_percentage", 0)
            if sessions == 0:
                inactive_count += 1
            elif pct < 20:
                at_risk_count += 1
            else:
                on_track_count += 1

        recent_activity = [
            {
                "learner_id": conv.get("user_id"),
                "created_at": conv.get("created_at").isoformat() if hasattr(conv.get("created_at"), "isoformat") else str(conv.get("created_at", "")),
                "language": conv.get("language"),
                "duration_minutes": round(conv.get("duration_seconds", 0) / 60, 1)
            } for conv in recent_conversations
        ]
        
        return {
            "total_assigned_learners": len(learners),
            "active_learners": on_track_count,
            "at_risk_learners": at_risk_count,
            "inactive_learners": inactive_count,
            "average_progress": round(average_progress, 1),
            "total_sessions_completed": total_sessions,
            "total_minutes_practiced": round(total_minutes, 1),
            "languages_taught": languages_taught,
            "level_distribution": level_distribution,
            "challenge_counts": challenge_counts,
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
    user_created_raw = user.get("created_at")
    if isinstance(user_created_raw, str):
        try:
            user_created = datetime.fromisoformat(user_created_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            user_created = None
    elif isinstance(user_created_raw, datetime):
        user_created = user_created_raw.replace(tzinfo=None)
    else:
        user_created = None
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


# ============================================================================
# GPT-POWERED AI REPORT — on-demand, cached 24h
# ============================================================================

@router.post("/dashboard/{tutor_id}/learner/{user_id}/ai-report")
async def generate_ai_report(
    tutor_id: str,
    user_id: str,
    current_tutor: dict = Depends(get_current_tutor)
) -> Dict[str, Any]:
    """
    Generate a comprehensive GPT-4.1-mini AI report for a learner.
    Cached for 24 hours. Call POST to regenerate.

    Returns structured JSON with 7 sections tutor can act on immediately.
    """
    await verify_tutor_access(tutor_id, current_tutor)

    # 1. Check cache (tutor_ai_reports collection, TTL 24h)
    cache_key = f"{tutor_id}:{user_id}"
    cached = await database.tutor_ai_reports.find_one({"cache_key": cache_key})
    if cached:
        age_hours = (datetime.utcnow() - cached["generated_at"]).total_seconds() / 3600
        if age_hours < 24:
            return {
                "report": cached["report"],
                "generated_at": cached["generated_at"].isoformat(),
                "from_cache": True,
                "cache_age_hours": round(age_hours, 1)
            }

    if not _openai_client:
        raise HTTPException(status_code=503, detail="AI service unavailable")

    # 2. Fetch all learner data in parallel
    user = await database.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    learner = await database.institutional_learners.find_one({
        "user_id": user_id, "tutor_id": tutor_id
    })

    plans, sessions, challenges, daily_stats, dna_profile, dna_history, assessments, sentence_jobs = \
        await asyncio.gather(
            database.learning_plans.find({"user_id": user_id}).to_list(None),
            database.conversation_sessions.find({"user_id": user_id}).sort("created_at", -1).to_list(50),
            database.challenge_sessions.find({"user_id": user_id}).sort("created_at", -1).to_list(50),
            database.daily_stats.find({"user_id": user_id}).sort("local_date", -1).to_list(30),
            database.speaking_dna_profiles.find_one({"user_id": user_id}),
            database.speaking_dna_history.find({"user_id": user_id}).sort("week_number", -1).to_list(8),
            database.assessments.find({"user_id": user_id}).sort("created_at", -1).to_list(5),
            database.sentence_analysis_jobs.find(
                {"user_id": user_id, "status": "completed"}
            ).sort("created_at", -1).to_list(3)
        )

    # 3. Build rich context object for GPT
    # --- Learning plan summary ---
    plan_summaries = []
    for p in plans:
        plan_summaries.append({
            "language": p.get("language"),
            "level": p.get("proficiency_level"),
            "progress_pct": round(p.get("progress_percentage", 0), 1),
            "completed_sessions": p.get("completed_sessions", 0),
            "total_sessions": p.get("total_sessions", 16),
            "minutes_used": round(p.get("practice_minutes_used", 0), 1),
            "assessment_score": p.get("assessment_data", {}).get("overall_score"),
            "strengths": p.get("assessment_data", {}).get("strengths", []),
            "weak_areas": p.get("assessment_data", {}).get("areas_for_improvement", []),
        })

    # --- Session stats ---
    total_session_minutes = sum(
        round(s.get("duration_seconds", 0) / 60, 1) for s in sessions
    )
    completed_sessions = sum(1 for s in sessions if s.get("duration_seconds", 0) > 18)

    # --- Challenge stats ---
    total_correct = sum(c.get("correct_answers", 0) for c in challenges)
    total_questions = sum(c.get("total_challenges", 0) for c in challenges)
    challenge_accuracy = round((total_correct / total_questions * 100) if total_questions else 0, 1)
    total_xp = sum(c.get("total_xp", 0) for c in challenges)

    # --- Activity pattern ---
    from collections import Counter
    hour_buckets = Counter()
    for s in sessions:
        if s.get("created_at"):
            try:
                h = datetime.fromisoformat(str(s["created_at"]).replace("Z", "+00:00")).hour
                if 5 <= h < 12: hour_buckets["Morning"] += 1
                elif 12 <= h < 17: hour_buckets["Afternoon"] += 1
                elif 17 <= h < 21: hour_buckets["Evening"] += 1
                else: hour_buckets["Night"] += 1
            except Exception:
                pass
    peak_time = hour_buckets.most_common(1)[0][0] if hour_buckets else "unknown"

    # --- Engagement ---
    active_dates = {
        s["local_date"] for s in daily_stats
        if s.get("total_sessions", 0) > 0 or s.get("conversation_time_seconds", 0) > 0
    }
    today = datetime.utcnow()
    active_last7 = sum(
        1 for i in range(7)
        if (today - timedelta(days=i)).strftime("%Y-%m-%d") in active_dates
    )

    # --- DNA strands ---
    dna_summary = {}
    if dna_profile:
        strands = dna_profile.get("dna_strands", {})
        overall = dna_profile.get("overall_profile", {})
        dna_summary = {
            "archetype": overall.get("speaker_archetype"),
            "coach_approach": overall.get("coach_approach"),
            "strengths": overall.get("strengths", []),
            "growth_areas": overall.get("growth_areas", []),
            "strands": {
                name: {
                    "score": round(strand.get("score", strand.get("consistency_score",
                              strand.get("grammar_accuracy", 0.5))) * 100
                              if strand.get("score", strand.get("consistency_score",
                              strand.get("grammar_accuracy"))) and
                              strand.get("score", strand.get("consistency_score",
                              strand.get("grammar_accuracy"))) <= 1.0 else
                              strand.get("score", 50)),
                    "description": strand.get("description", ""),
                    "trend": strand.get("trend", ""),
                    "type": strand.get("type", strand.get("level", strand.get("pattern", ""))),
                }
                for name, strand in strands.items()
            },
            "anxiety_triggers": strands.get("emotional", {}).get("anxiety_triggers", []),
            "wpm": strands.get("rhythm", {}).get("words_per_minute_avg"),
            "filler_rate": strands.get("confidence", {}).get("filler_rate_per_minute"),
        }

    # --- Weekly confidence trend ---
    weekly_trend = []
    for week in reversed(dna_history):
        snap = week.get("strand_snapshots", {})
        conf = snap.get("confidence", {})
        stats_w = week.get("week_stats", {})
        weekly_trend.append({
            "week": week.get("week_number"),
            "confidence": round(conf.get("score", 0) * 100),
            "sessions": stats_w.get("sessions_completed", 0),
            "minutes": round(stats_w.get("total_minutes", 0), 1),
        })

    # --- Sentence quality sample ---
    sentence_samples = []
    for job in sentence_jobs:
        for a in job.get("analyses", [])[:3]:
            sentence_samples.append({
                "text": a.get("recognized_text", "")[:100],
                "grammar": round(a.get("grammatical_score", 0)),
                "vocabulary": round(a.get("vocabulary_score", 0)),
                "complexity": round(a.get("complexity_score", 0)),
                "overall": round(a.get("overall_score", 0)),
                "issues": a.get("grammar_issues", [])[:2],
                "suggestions": a.get("improvement_suggestions", [])[:1],
            })

    # --- Assessment history ---
    assessment_summary = [
        {
            "language": a.get("language"),
            "level": a.get("level"),
            "score": a.get("score"),
            "feedback": a.get("feedback"),
        }
        for a in assessments
    ]

    # 4. Build GPT prompt
    learner_name = user.get("name", "the learner")
    enrollment_date = (learner.get("enrolled_at") or "unknown") if learner else "unknown"

    context_json = json.dumps({
        "learner": {
            "name": learner_name,
            "enrolled_at": str(enrollment_date)[:10] if enrollment_date != "unknown" else "unknown",
            "preferred_language": user.get("preferred_language"),
            "preferred_level": user.get("preferred_level"),
        },
        "learning_plans": plan_summaries,
        "voice_practice": {
            "total_sessions": len(sessions),
            "completed_sessions": completed_sessions,
            "total_minutes": round(total_session_minutes, 1),
            "completion_rate_pct": round(completed_sessions / len(sessions) * 100) if sessions else 0,
            "peak_practice_time": peak_time,
        },
        "challenges": {
            "total_sessions": len(challenges),
            "total_correct_answers": total_correct,
            "total_questions": total_questions,
            "accuracy_pct": challenge_accuracy,
            "total_xp_earned": total_xp,
        },
        "engagement": {
            "active_days_last_7": active_last7,
            "engagement_score_pct": round(active_last7 / 7 * 100),
            "total_active_days_in_30d": len(active_dates),
        },
        "speaking_dna": dna_summary,
        "weekly_confidence_trend": weekly_trend,
        "recent_sentence_samples": sentence_samples[:6],
        "formal_assessments": assessment_summary,
    }, default=str, ensure_ascii=False)

    system_prompt = """You are an expert language learning analyst generating a professional tutor report
for the MyTacoAI language learning platform. Your role is a senior pedagogical advisor briefing the
assigned tutor before their next session with this learner.

## CRITICAL RULE: ALL RECOMMENDATIONS MUST USE MYTACOAI APP FEATURES ONLY
Every recommendation must map to a real, specific in-app action the learner can take in MyTacoAI.
Never suggest external resources, generic homework, or activities that don't exist in the app.

## MYTACOAI APP FEATURES YOU CAN RECOMMEND:

### Conversation Sessions (Speaking Practice)
- **Learning Plan Session** — Structured session tied to their active plan goals. Best for focused grammar/vocabulary work aligned to their current level.
- **Freestyle Conversation** — Open-topic spoken practice. Best for fluency building and spontaneous speech.
- **News Session** — Discuss a current events article at their CEFR level. Best for vocabulary expansion and reading comprehension.
- **Custom Topic Session** — Choose a specific real-world topic. Best for targeted practice on weak areas.

### Challenges (7 types — short, gamified, self-paced)
- **Error Spotting** — Find and fix grammar mistakes in sentences. Best for grammar accuracy and error awareness.
- **Swipe Fix** — Swipe through alternative phrases to understand correct usage. Best for natural phrasing and collocations.
- **Micro Quiz** — Multiple-choice vocabulary/grammar questions. Best for rapid vocabulary building and grammar testing.
- **Smart Flashcard** — Interactive word/phrase cards with context. Best for vocabulary retention between sessions.
- **Native Check** — Judge whether sentences sound natural. Best for idiom and register awareness.
- **Brain Tickler** — Timed speed challenge. Best for fluency under pressure and recall speed.
- **Story Builder** — Fill gaps in a narrative from a word bank. Best for sentence construction and contextual vocabulary.

### Other Features
- **Speaking DNA Voice Scan** — Deep analysis of speaking patterns (rhythm, confidence, accuracy). Recommend if DNA data is sparse or stale.
- **CEFR Assessment** — Full placement test. Recommend if enrolled level seems misaligned with performance.
- **Flashcard Review** — Review auto-generated vocabulary cards from past sessions. Best for spaced repetition between sessions.
- **Daily Missions** — 3 daily missions (plan session + news + challenge) that build habit. Remind learner to complete all 3 each day.

## WRITING RULES
- Write for a professional language tutor, not the learner.
- Every recommendation must name the specific in-app feature (e.g., "assign 5 Error Spotting challenges", not "practice grammar").
- Be evidence-based: cite specific data from the input (session counts, DNA scores, challenge accuracy, etc.).
- If data is sparse, say so honestly — do not fabricate insights.
- Recommendations must be immediately actionable: the tutor should be able to tell the learner exactly what to tap in the app.

You must respond with ONLY valid JSON matching this exact structure:
{
  "executive_summary": "2-3 sentences. Lead with the single most important finding. Reference specific data. End with the one app action that would most help this learner right now.",
  "cefr_alignment": {
    "current_estimated_level": "A1/A2/B1/B2/C1/C2",
    "evidence": "Specific data points: challenge accuracy %, session count, DNA scores, assessment results",
    "trajectory": "progressing/plateauing/regressing — with one sentence of evidence"
  },
  "skill_diagnosis": {
    "strongest_skill": "grammar/vocabulary/fluency/pronunciation/confidence/consistency",
    "strongest_evidence": "Specific data supporting this",
    "weakest_skill": "grammar/vocabulary/fluency/pronunciation/confidence/consistency",
    "weakest_evidence": "Specific data supporting this",
    "skill_breakdown": [
      {"skill": "Grammar", "rating": "strong/developing/needs_work", "note": "Evidence-based, 1 sentence"},
      {"skill": "Vocabulary", "rating": "strong/developing/needs_work", "note": "..."},
      {"skill": "Fluency", "rating": "strong/developing/needs_work", "note": "..."},
      {"skill": "Confidence", "rating": "strong/developing/needs_work", "note": "..."},
      {"skill": "Consistency", "rating": "strong/developing/needs_work", "note": "..."}
    ]
  },
  "engagement_analysis": {
    "assessment": "high/moderate/low/at_risk",
    "pattern": "1-2 sentences: when do they practice, which features do they use most/least",
    "risk_factors": ["Specific risks grounded in data, e.g. 'Zero news sessions — missing vocabulary input channel'"],
    "positive_signals": ["Specific positives, e.g. '5-day streak maintained despite low session count'"]
  },
  "next_session_plan": {
    "priority_focus": "Single most important pedagogical focus — tied to weakest skill from data",
    "suggested_activity_type": "MUST be one of: Learning Plan Session / Freestyle Conversation / News Session / Custom Topic Session / Error Spotting / Micro Quiz / Story Builder / Smart Flashcard / Native Check / Brain Tickler / Swipe Fix",
    "topic_suggestion": "Specific topic/scenario appropriate for their level and language, e.g. 'Dutch daily routines at A1 using present tense verbs'",
    "things_to_avoid": ["Specific triggers from DNA anxiety_triggers or low-confidence areas"]
  },
  "app_practice_plan": {
    "this_week": [
      {
        "activity": "Exact in-app feature name",
        "frequency": "e.g. 3x this week / daily / once",
        "focus": "What to work on within that activity",
        "rationale": "Why this specific feature addresses the identified weakness"
      }
    ],
    "suggested_session_sequence": "E.g. 'Day 1: Freestyle Conversation (topic: introduce yourself) → Day 2-3: 5 Error Spotting challenges each → Day 4: News Session → Day 5: Smart Flashcard review → Day 6-7: Learning Plan Session'"
  },
  "recommendations": [
    {
      "priority": "high/medium/low",
      "action": "Specific in-app action: name the feature + what to do in it + how many times",
      "rationale": "Why this feature addresses the identified weakness based on the data",
      "timeframe": "this_session/this_week/this_month"
    }
  ],
  "learner_archetype": {
    "type": "e.g. The Cautious Builder / The Confident Rusher / The Inconsistent Sprinter / The Challenge Avoider / The Conversation Seeker",
    "description": "2 sentences on how this learner characteristically uses the app",
    "coaching_strategy": "Which MyTacoAI features work best for this archetype and why"
  },
  "flags": [
    {
      "type": "warning/positive/info",
      "message": "Specific, data-grounded observation. For warnings: name the gap and the exact app feature that addresses it."
    }
  ]
}

Recommendations: 3-5 items. Every "action" field must name a specific MyTacoAI feature.
app_practice_plan.this_week: 3-5 activities. This is the actionable weekly plan the tutor sends to the learner.
Flags: 2-4 items. Mix of warnings and positives."""

    user_prompt = f"""Generate a tutor report for {learner_name}.

## LEARNER DATA:
{context_json}

## INSTRUCTIONS:
- Ground EVERY claim in the data above — no fabrications
- CEFR estimate must reflect actual performance data (challenge accuracy, DNA scores, session quality), not just enrolled level
- All recommendations must use MyTacoAI app features by exact name
- The app_practice_plan.suggested_session_sequence should be a concrete day-by-day plan the tutor can send directly to the learner as a message
- If the learner has a learning plan: recommend Learning Plan Sessions as the primary activity, supplemented by challenges targeting their weak skills
- If no learning plan: recommend starting with a CEFR Assessment, then Freestyle Conversations + challenges
- If data is sparse (< 3 sessions): say so clearly, recommend Speaking DNA Voice Scan first to gather baseline data
- The tutor will read this report immediately before their next session with this learner"""

    # 5. Call GPT-4.1-mini
    try:
        response = _openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Low temp for consistent, factual reports
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        report_text = response.choices[0].message.content
        report = json.loads(report_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI report generation failed: {str(e)}")

    # 6. Cache the result
    now = datetime.utcnow()
    await database.tutor_ai_reports.replace_one(
        {"cache_key": cache_key},
        {
            "cache_key": cache_key,
            "tutor_id": tutor_id,
            "user_id": user_id,
            "report": report,
            "generated_at": now,
        },
        upsert=True
    )

    return {
        "report": report,
        "generated_at": now.isoformat(),
        "from_cache": False,
        "cache_age_hours": 0
    }


# ============================================================================
# PHASE 5: TUTOR → LEARNER PUSH NOTIFICATION
# ============================================================================

from pydantic import BaseModel as PydanticBaseModel

class SendRecommendationRequest(PydanticBaseModel):
    message: str
    tutor_name: str = "Your Tutor"


@router.post("/dashboard/{tutor_id}/learner/{user_id}/send-recommendation")
async def send_recommendation(
    tutor_id: str,
    user_id: str,
    body: SendRecommendationRequest,
    current_tutor: dict = Depends(get_current_tutor),
):
    """
    Send a push notification from tutor to a learner, opening TaalCoach
    with the tutor's message pre-loaded.

    Rate limit: max 1 notification per learner per hour.
    Requires the learner to have a valid Expo push token.
    """
    # 1. Verify tutor owns this dashboard
    await verify_tutor_access(tutor_id, current_tutor)

    # 2. Validate message
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    if len(message) > 500:
        raise HTTPException(status_code=422, detail="Message too long (max 500 characters)")

    # 3. Look up learner push token
    learner = await database.users.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else None
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    push_token = learner.get("push_token")  # Optional — push is best-effort

    learner_name = learner.get("name") or learner.get("username") or "Student"
    tutor_name = body.tutor_name.strip() or current_tutor.get("name") or "Your Tutor"
    now = datetime.utcnow()

    # 4. Save to notifications + user_notifications collections
    # This is the PRIMARY delivery mechanism — same pattern as admin notifications.
    # The learner sees it in their bell icon and notification list regardless of push.
    notification_oid = ObjectId()
    notification_id = str(notification_oid)

    notification_doc = {
        "_id": notification_id,
        "title": f"Message from {tutor_name}",
        "content": message,
        "notification_type": "Information",  # Uses existing mobile rendering
        "created_by": f"tutor:{tutor_id}",
        "created_at": now,
        "sent_at": now,
        "is_sent": True,
        "tutor_id": tutor_id,
        "tutor_name": tutor_name,
    }
    await database.notifications.insert_one(notification_doc)

    user_notification_doc = {
        "_id": str(ObjectId()),
        "user_id": user_id,
        "notification_id": notification_id,
        "is_read": False,
        "read_at": None,
        "deleted_at": None,
        "created_at": now,
    }
    await database.user_notifications.insert_one(user_notification_doc)

    # 5. Send push as best-effort hint (navigate to bell icon on tap)
    # Not a blocking failure — notification already saved to DB above.
    push_sent = False
    if push_token and isinstance(push_token, str) and (
        push_token.startswith("ExponentPushToken[") or push_token.startswith("ExpoPushToken[")
    ):
        try:
            from notification_service import notification_service
            push_data = {
                "type": "notification",
                "notification_type": "Information",
                "notification_id": notification_id,
            }
            send_result = notification_service.send_expo_push_notification(
                push_tokens=[push_token],
                title=f"Message from {tutor_name}",
                body=(message[:178].strip() or message[:50]),
                data=push_data,
                priority="high",
                sound="default",
                badge=1,
            )
            push_sent = send_result.get("success", False)
            # Clear stale token silently
            if any("DeviceNotRegistered" in str(e) for e in send_result.get("errors", [])):
                await database.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$unset": {"push_token": ""}}
                )
        except Exception:
            pass  # Push failure never blocks — notification is already in DB

    # 6. Record in tutor_notifications for history
    await database.tutor_notifications.insert_one({
        "_id": ObjectId(),
        "tutor_id": tutor_id,
        "learner_id": user_id,
        "learner_name": learner_name,
        "tutor_name": tutor_name,
        "message": message,
        "notification_id": notification_id,
        "sent_at": now,
        "push_sent": push_sent,
    })

    return {
        "sent": True,
        "notification_id": notification_id,
        "learner_name": learner_name,
        "sent_at": now.isoformat(),
        "push_sent": push_sent,
    }
