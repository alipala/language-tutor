"""
Journey Orchestrator API Routes

Provides endpoints for:
- Getting journey status and current stage
- Fetching recommended actions
- Dismissing/completing recommendations
- Viewing daily digest messages
- Getting journey timeline

Author: MyTacoAI Backend Team
Date: 2026-04-20
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId

from auth import get_current_user
from database import (
    users_collection,
    recommended_actions_collection,
    journey_checkpoints_collection,
    daily_digest_messages_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,
    speaking_breakthroughs_collection,
    learning_plans_collection
)
from models import (
    JourneyStatusResponse,
    RecommendedActionResponse,
    DismissRecommendationRequest,
    CompleteRecommendationRequest,
    DailyDigestResponse,
    JourneyTimelineResponse,
    JourneyTimelineEvent,
    RecommendedAction,
    JourneyCheckpoint,
    DailyDigestMessage,
    LearningJourneyState
)
from services.journey_state_detector import journey_state_detector
from services.recommendation_engine import recommendation_engine
from services.daily_digest_generator import daily_digest_generator

router = APIRouter()


@router.get("/journey/status", response_model=JourneyStatusResponse)
async def get_journey_status(current_user = Depends(get_current_user)):
    """
    Get user's current learning journey status.

    Returns:
        - Current journey stage and metrics
        - Today's primary recommendation
        - Recent checkpoints (milestones, breakthroughs)
        - Whether daily digest is available
    """
    try:
        user_id = str(current_user.id)

        # Detect current journey stage
        journey_state = await journey_state_detector.detect_journey_stage(user_id)

        # Get today's recommendation
        current_recommendation = await recommendation_engine.generate_daily_recommendation(user_id)

        # Get recent checkpoints (last 5)
        recent_checkpoints_docs = await journey_checkpoints_collection.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=5
        ).to_list(None)

        recent_checkpoints = [JourneyCheckpoint(**cp) for cp in recent_checkpoints_docs]

        # Check if today's digest is available
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_digest = await daily_digest_messages_collection.find_one({
            "user_id": user_id,
            "generated_at": {"$gte": today_start}
        })

        daily_digest_available = today_digest is not None

        return JourneyStatusResponse(
            success=True,
            journey_state=journey_state,
            current_recommendation=current_recommendation,
            recent_checkpoints=recent_checkpoints,
            daily_digest_available=daily_digest_available
        )

    except Exception as e:
        print(f"Error getting journey status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting journey status: {str(e)}")


@router.get("/journey/has-unviewed-recommendation")
async def has_unviewed_recommendation(current_user = Depends(get_current_user)):
    """
    Check if user has an unviewed recommendation (for badge logic).

    This endpoint does NOT mark the recommendation as viewed.
    Use this for checking badge status without side effects.

    Returns:
        {
            "has_unviewed": boolean,
            "recommendation_id": string or null
        }
    """
    try:
        user_id = str(current_user.id)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Check for unviewed recommendation
        unviewed = await recommended_actions_collection.find_one({
            "user_id": user_id,
            "completed": False,
            "dismissed": False,
            "viewed": False,  # Only unviewed
            "expires_at": {"$gt": datetime.utcnow()},
            "recommended_at": {"$gte": today_start},
            "priority": 1
        })

        return {
            "has_unviewed": unviewed is not None,
            "recommendation_id": str(unviewed["_id"]) if unviewed else None
        }

    except Exception as e:
        print(f"Error checking unviewed recommendation: {str(e)}")
        return {"has_unviewed": False, "recommendation_id": None}


@router.get("/journey/recommended-action", response_model=RecommendedActionResponse)
async def get_recommended_action(current_user = Depends(get_current_user)):
    """
    Get today's primary recommended action with alternatives.

    Returns:
        - Primary recommended action (priority 1)
        - 2-3 alternative actions
        - Personalized message
    """
    try:
        user_id = str(current_user.id)

        # Get primary recommendation
        primary_action = await recommendation_engine.generate_daily_recommendation(user_id)

        if not primary_action:
            return RecommendedActionResponse(
                success=True,
                action=None,
                alternative_actions=[],
                message="You're all caught up! Keep up the great work!"
            )

        # Mark as viewed
        await recommended_actions_collection.update_one(
            {"_id": ObjectId(primary_action.id)},
            {
                "$set": {
                    "viewed": True,
                    "viewed_at": datetime.utcnow()
                }
            }
        )

        # Generate alternative actions
        alternatives = await recommendation_engine.generate_alternative_actions(
            user_id,
            primary_action,
            max_alternatives=2
        )

        return RecommendedActionResponse(
            success=True,
            action=primary_action,
            alternative_actions=alternatives,
            message=f"Here's what we recommend for you today, {current_user.name or ''}!"
        )

    except Exception as e:
        print(f"Error getting recommended action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendation: {str(e)}")


@router.post("/journey/dismiss-recommendation")
async def dismiss_recommendation(
    request: DismissRecommendationRequest,
    current_user = Depends(get_current_user)
):
    """
    Dismiss a recommendation (user doesn't want to do it).

    This helps improve future recommendations.
    """
    try:
        user_id = str(current_user.id)

        # Verify recommendation belongs to user
        recommendation = await recommended_actions_collection.find_one({
            "_id": ObjectId(request.recommendation_id),
            "user_id": user_id
        })

        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Mark as dismissed
        await recommended_actions_collection.update_one(
            {"_id": ObjectId(request.recommendation_id)},
            {
                "$set": {
                    "dismissed": True,
                    "dismissed_at": datetime.utcnow()
                }
            }
        )

        return {"success": True, "message": "Recommendation dismissed"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error dismissing recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error dismissing recommendation: {str(e)}")


@router.post("/journey/complete-recommendation")
async def complete_recommendation(
    request: CompleteRecommendationRequest,
    current_user = Depends(get_current_user)
):
    """
    Mark a recommendation as completed (user did the action).

    This tracks engagement and helps improve recommendations.
    """
    try:
        user_id = str(current_user.id)

        # Verify recommendation belongs to user
        recommendation = await recommended_actions_collection.find_one({
            "_id": ObjectId(request.recommendation_id),
            "user_id": user_id
        })

        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Mark as completed
        await recommended_actions_collection.update_one(
            {"_id": ObjectId(request.recommendation_id)},
            {
                "$set": {
                    "completed": True,
                    "completed_at": datetime.utcnow()
                }
            }
        )

        return {"success": True, "message": "Great job! Recommendation completed!"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error completing recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error completing recommendation: {str(e)}")


@router.get("/journey/daily-digest", response_model=DailyDigestResponse)
async def get_daily_digest(current_user = Depends(get_current_user)):
    """
    Get today's daily digest message from Taal Coach.

    Returns:
        - Today's personalized message
        - Quick action buttons
        - Message type (motivation, tip, celebration, etc.)
    """
    try:
        user_id = str(current_user.id)

        # Get today's digest
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        digest_doc = await daily_digest_messages_collection.find_one({
            "user_id": user_id,
            "generated_at": {"$gte": today_start}
        })

        if not digest_doc:
            # Generate one on-demand if it doesn't exist
            digest = await daily_digest_generator.generate_daily_digest(user_id, force_new=True)

            if not digest:
                return DailyDigestResponse(
                    success=True,
                    digest=None,
                    has_unread_digest=False,
                    message="No digest available today"
                )

            digest_doc = digest.dict(by_alias=False)
        else:
            # Convert ObjectId to string for Pydantic model
            if "_id" in digest_doc:
                digest_doc["_id"] = str(digest_doc["_id"])

        digest = DailyDigestMessage(**digest_doc)

        # Mark as opened
        if not digest.opened:
            await daily_digest_messages_collection.update_one(
                {"_id": ObjectId(digest.id)},
                {
                    "$set": {
                        "opened": True,
                        "opened_at": datetime.utcnow()
                    }
                }
            )

        has_unread = not digest.opened

        return DailyDigestResponse(
            success=True,
            digest=digest,
            has_unread_digest=has_unread,
            message="Here's your daily message from Taal Coach!"
        )

    except Exception as e:
        print(f"Error getting daily digest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting daily digest: {str(e)}")


@router.get("/journey/timeline", response_model=JourneyTimelineResponse)
async def get_journey_timeline(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """
    Get user's learning journey timeline.

    Shows chronological view of all activities:
    - Sessions completed
    - Challenges completed
    - Breakthroughs achieved
    - Milestones reached
    - Learning plans completed

    Args:
        days: Number of days to fetch (default: 30)

    Returns:
        Chronological timeline with summary statistics
    """
    try:
        user_id = str(current_user.id)

        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)

        # Gather all timeline events
        timeline_events = []

        # 1. Conversation sessions
        sessions = await conversation_sessions_collection.find(
            {"user_id": user_id, "created_at": {"$gte": start_date}},
            sort=[("created_at", -1)]
        ).to_list(None)

        for session in sessions:
            timeline_events.append(JourneyTimelineEvent(
                id=f"session_{str(session['_id'])}",
                timestamp=session["created_at"],
                event_type="session",
                title=f"{session.get('language', 'Language').title()} Session",
                description=f"{session.get('duration_minutes', 0):.0f} minutes - {session.get('topic', 'Practice')}",
                language=session.get("language"),
                level=session.get("level"),
                data={
                    "session_id": str(session["_id"]),
                    "duration": session.get("duration_minutes", 0),
                    "topic": session.get("topic", "")
                },
                icon="💬",
                color="#14B8A6"  # Teal
            ))

        # 2. Challenge sessions
        challenges = await challenge_sessions_collection.find(
            {"user_id": user_id, "created_at": {"$gte": start_date}},
            sort=[("created_at", -1)]
        ).to_list(None)

        for challenge in challenges:
            is_correct = challenge.get("is_correct", False)
            timeline_events.append(JourneyTimelineEvent(
                id=f"challenge_{str(challenge['_id'])}",
                timestamp=challenge["created_at"],
                event_type="challenge",
                title=f"Challenge {'✓' if is_correct else '✗'}",
                description=f"{challenge.get('challenge_type', 'Challenge').replace('_', ' ').title()}",
                language=challenge.get("language"),
                level=challenge.get("level"),
                data={
                    "challenge_id": challenge.get("challenge_id"),
                    "is_correct": is_correct,
                    "xp_earned": challenge.get("xp_earned", 0)
                },
                icon="🎯" if is_correct else "⚡",
                color="#F59E0B" if is_correct else "#6B7280"  # Amber or Gray
            ))

        # 3. Speaking DNA breakthroughs
        breakthroughs = await speaking_breakthroughs_collection.find(
            {"user_id": user_id, "detected_at": {"$gte": start_date}},
            sort=[("detected_at", -1)]
        ).to_list(None)

        for breakthrough in breakthroughs:
            breakthrough_type = breakthrough.get("type", "improvement")
            improvement = breakthrough.get("improvement_percentage", 0)

            timeline_events.append(JourneyTimelineEvent(
                id=f"breakthrough_{str(breakthrough['_id'])}",
                timestamp=breakthrough["detected_at"],
                event_type="breakthrough",
                title=f"🎉 {breakthrough_type.replace('_', ' ').title()}",
                description=f"Improved {improvement:.0f}% - {breakthrough.get('achievement_message', '')}",
                language=breakthrough.get("language"),
                data={
                    "breakthrough_id": str(breakthrough["_id"]),
                    "type": breakthrough_type,
                    "improvement": improvement
                },
                icon="🔥",
                color="#EF4444"  # Red
            ))

        # 4. Journey checkpoints
        checkpoints = await journey_checkpoints_collection.find(
            {"user_id": user_id, "timestamp": {"$gte": start_date}},
            sort=[("timestamp", -1)]
        ).to_list(None)

        for checkpoint in checkpoints:
            timeline_events.append(JourneyTimelineEvent(
                id=f"checkpoint_{str(checkpoint['_id'])}",
                timestamp=checkpoint["timestamp"],
                event_type="milestone",
                title=checkpoint["title"],
                description=checkpoint["description"],
                language=checkpoint.get("language"),
                level=checkpoint.get("level"),
                data=checkpoint.get("data", {}),
                icon="⭐",
                color="#8B5CF6"  # Purple
            ))

        # Sort all events by timestamp (descending)
        timeline_events.sort(key=lambda x: x.timestamp, reverse=True)

        # Calculate summary statistics
        total_sessions = len([e for e in timeline_events if e.event_type == "session"])
        total_challenges = len([e for e in timeline_events if e.event_type == "challenge"])
        total_breakthroughs = len([e for e in timeline_events if e.event_type == "breakthrough"])
        total_milestones = len([e for e in timeline_events if e.event_type == "milestone"])

        challenges_correct = len([
            e for e in timeline_events
            if e.event_type == "challenge" and e.data.get("is_correct", False)
        ])
        challenge_accuracy = (challenges_correct / total_challenges * 100) if total_challenges > 0 else 0

        # Current week summary
        week_ago = datetime.utcnow() - timedelta(days=7)
        current_week_events = [e for e in timeline_events if e.timestamp >= week_ago]

        current_week_summary = {
            "sessions": len([e for e in current_week_events if e.event_type == "session"]),
            "challenges": len([e for e in current_week_events if e.event_type == "challenge"]),
            "breakthroughs": len([e for e in current_week_events if e.event_type == "breakthrough"]),
            "days_active": len(set(e.timestamp.date() for e in current_week_events))
        }

        summary = {
            "total_events": len(timeline_events),
            "total_sessions": total_sessions,
            "total_challenges": total_challenges,
            "total_breakthroughs": total_breakthroughs,
            "total_milestones": total_milestones,
            "challenge_accuracy": round(challenge_accuracy, 1),
            "days_range": days
        }

        return JourneyTimelineResponse(
            success=True,
            timeline=timeline_events,
            summary=summary,
            current_week_summary=current_week_summary
        )

    except Exception as e:
        print(f"Error getting journey timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")


@router.post("/journey/force-recalculate")
async def force_recalculate_journey(current_user = Depends(get_current_user)):
    """
    Force recalculation of journey state (admin/debug endpoint).

    Useful for testing or when user data is updated externally.
    """
    try:
        user_id = str(current_user.id)

        # Force recalculate journey stage
        journey_state = await journey_state_detector.detect_journey_stage(
            user_id,
            force_recalculate=True
        )

        # Generate new recommendation
        recommendation = await recommendation_engine.generate_daily_recommendation(
            user_id,
            force_new=True
        )

        return {
            "success": True,
            "message": "Journey state recalculated",
            "journey_state": journey_state.dict(),
            "new_recommendation": recommendation.dict() if recommendation else None
        }

    except Exception as e:
        print(f"Error force recalculating journey: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recalculating: {str(e)}")
