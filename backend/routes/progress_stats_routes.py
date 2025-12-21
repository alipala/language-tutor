"""
User Progress Statistics API
Tracks how many challenges a user has completed for each type/language/level
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from auth import get_current_user
from database import database, challenge_sessions_collection
from models import UserInDB

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/challenge-stats")
async def get_challenge_progress(
    language: str,
    level: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get user's challenge completion statistics

    Returns:
    - completed_count: Total challenges completed for this language/level
    - completed_by_type: Dict of completed count per challenge type
    - total_available: Total challenges available (from reference)
    - progress_percentage: Overall progress percentage
    """
    try:
        user_id = current_user.id

        print(f"[PROGRESS_STATS] 📊 Getting progress for user {user_id}, language: {language}, level: {level}")

        # Get all completed challenge IDs from user's sessions
        completed_challenge_ids = set()

        # Query all user's sessions
        async for session in challenge_sessions_collection.find({"user_id": user_id}):
            # Extract challenge IDs from each session
            if "challenges" in session:
                for challenge in session["challenges"]:
                    if "id" in challenge:
                        # Check if challenge matches language/level
                        challenge_lang = challenge.get("language", "").lower()
                        challenge_level = challenge.get("cefrLevel", "")

                        if challenge_lang == language.lower() and challenge_level == level:
                            completed_challenge_ids.add(challenge["id"])

        # Count by type
        completed_by_type = {
            "error_spotting": 0,
            "swipe_fix": 0,
            "micro_quiz": 0,
            "smart_flashcard": 0,
            "native_check": 0,
            "brain_tickler": 0,
        }

        # Recount with type filtering
        completed_challenge_ids_by_type = {type_name: set() for type_name in completed_by_type.keys()}

        async for session in challenge_sessions_collection.find({"user_id": user_id}):
            if "challenges" in session:
                for challenge in session["challenges"]:
                    challenge_lang = challenge.get("language", "").lower()
                    challenge_level = challenge.get("cefrLevel", "")
                    challenge_type = challenge.get("type", "")
                    challenge_id = challenge.get("id")

                    if (challenge_lang == language.lower() and
                        challenge_level == level and
                        challenge_type in completed_by_type and
                        challenge_id):
                        completed_challenge_ids_by_type[challenge_type].add(challenge_id)

        # Update counts
        for type_name, ids in completed_challenge_ids_by_type.items():
            completed_by_type[type_name] = len(ids)

        total_completed = sum(completed_by_type.values())

        # Get total available from reference_challenges
        reference_collection = database.reference_challenges
        total_available = await reference_collection.count_documents({
            "language": language,
            "cefr_level": level
        })

        # Get available by type
        available_by_type = {}
        for challenge_type in completed_by_type.keys():
            count = await reference_collection.count_documents({
                "language": language,
                "cefr_level": level,
                "challenge_type": challenge_type
            })
            available_by_type[challenge_type] = count

        # Calculate progress percentage
        progress_percentage = (total_completed / total_available * 100) if total_available > 0 else 0

        result = {
            "completed_count": total_completed,
            "completed_by_type": completed_by_type,
            "total_available": total_available,
            "available_by_type": available_by_type,
            "progress_percentage": round(progress_percentage, 1),
            "language": language,
            "level": level
        }

        print(f"[PROGRESS_STATS] ✅ Progress: {total_completed}/{total_available} ({progress_percentage:.1f}%)")

        return result

    except Exception as e:
        print(f"[PROGRESS_STATS] ❌ Error getting progress stats: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get progress stats: {str(e)}"
        )
