"""
Challenge Routes for Explore Tab
Provides daily personalized challenges based on user's CEFR level and weaknesses
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from auth import get_current_user
from models import (
    UserResponse,
    ChallengeCompletionRequest,
    DailyChallengesResponse,
    ChallengeCountsResponse,
    ChallengesByTypeResponse,
    ChallengePoolItem,
)
from database import database
from challenge_generator_ai import get_or_generate_daily_challenges
from services.timezone_utils import convert_to_local_date, get_current_local_date
from services.stats_service import update_daily_stats, update_lifetime_stats, update_streak
from cache_helpers import invalidate_coach_context_smart  # PHASE 4.2: Smart cache invalidation

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


def get_challenges_collection():
    """Get challenges collection from database"""
    return database.challenges


def get_daily_challenges_cache_collection():
    """Get daily challenges cache collection"""
    return database.daily_challenges_cache


def get_challenge_pool_collection():
    """Get challenge pool collection"""
    return database.challenge_pool


async def get_user_active_language(user_id: str) -> str:
    """
    Get user's active learning plan language

    Returns:
        Language code (default: "english")
    """
    try:
        learning_plans_collection = database.learning_plans
        active_plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "is_active": True
        })

        if active_plan:
            language = active_plan.get("language", "english")
            # Ensure lowercase for consistency
            return language.lower()

        # Fallback: get most recent plan
        recent_plan = await learning_plans_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        if recent_plan:
            return recent_plan.get("language", "english").lower()

        return "english"

    except Exception as e:
        print(f"[CHALLENGES] Error getting user language: {str(e)}")
        return "english"


async def resolve_language_and_level(
    user_id: str,
    user_preferred_level: Optional[str],
    language_param: Optional[str] = None,
    level_param: Optional[str] = None
) -> tuple[str, str]:
    """
    Smart resolution of language and level with proper priority fallback.

    Priority for LANGUAGE:
    1. Explicit language parameter (iOS user selection)
    2. User's active learning plan language
    3. Fallback: "english"

    Priority for LEVEL:
    1. Explicit level parameter (iOS user selection)
    2. User's preferred_level from profile
    3. Fallback: "B1"

    Args:
        user_id: User ID
        user_preferred_level: User's preferred level from profile
        language_param: Optional explicit language from query params
        level_param: Optional explicit level from query params

    Returns:
        Tuple of (language, level) both lowercase
    """
    # Resolve language
    if language_param and language_param.strip():
        # Priority 1: Explicit parameter from iOS
        language = language_param.lower().strip()
        print(f"[RESOLVE] Using explicit language parameter: {language}")
    else:
        # Priority 2: User's active learning plan
        language = await get_user_active_language(user_id)
        print(f"[RESOLVE] Using learning plan language: {language}")

    # Resolve level
    if level_param and level_param.strip():
        # Priority 1: Explicit parameter from iOS
        level = level_param.upper().strip()
        print(f"[RESOLVE] Using explicit level parameter: {level}")
    elif user_preferred_level:
        # Priority 2: User's profile preference
        level = user_preferred_level
        print(f"[RESOLVE] Using user preferred level: {level}")
    else:
        # Priority 3: Default fallback
        level = "B1"
        print(f"[RESOLVE] Using default level: {level}")

    # Validate language (supported languages)
    valid_languages = ["english", "spanish", "dutch", "german", "french", "portuguese"]
    if language not in valid_languages:
        print(f"[RESOLVE] ⚠️ Invalid language '{language}', defaulting to 'english'")
        language = "english"

    # Validate level (CEFR levels)
    valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    if level not in valid_levels:
        print(f"[RESOLVE] ⚠️ Invalid level '{level}', defaulting to 'B1'")
        level = "B1"

    print(f"[RESOLVE] ✅ Final: language={language}, level={level}")
    return language, level


async def get_user_weakness_tags(user_id: str) -> List[str]:
    """
    Analyze user's weak areas from existing data:
    - Flashcards with low mastery_level
    - Learning plan struggles
    - Session analysis data

    Returns list of tags like: ["past_tense", "articles", "prepositions"]
    """
    weakness_tags = []

    try:
        # 1. Check flashcards for low mastery items
        flashcards_collection = database.flashcards
        weak_flashcards = await flashcards_collection.find({
            "user_id": user_id,
            "mastery_level": {"$lt": 0.5}  # Less than 50% mastery
        }).limit(10).to_list(length=10)

        for card in weak_flashcards:
            tags = card.get("tags", [])
            weakness_tags.extend(tags)

        # 2. Check learning plan for recent struggles
        learning_plans_collection = database.learning_plans
        learning_plan = await learning_plans_collection.find_one({
            "user_id": user_id
        }, sort=[("updated_at", -1)])

        if learning_plan:
            # Extract struggle areas from plan content
            plan_content = learning_plan.get("plan_content", {})
            # Could analyze weekly_schedule for common error patterns
            # For now, we'll use a simple approach
            pass

        # 3. Remove duplicates and return most common weaknesses
        from collections import Counter
        if weakness_tags:
            tag_counts = Counter(weakness_tags)
            # Return top 5 most common weakness tags
            weakness_tags = [tag for tag, count in tag_counts.most_common(5)]

        print(f"[CHALLENGES] User {user_id} weakness tags: {weakness_tags}")
        return weakness_tags

    except Exception as e:
        print(f"[CHALLENGES] Error analyzing weaknesses: {str(e)}")
        return []


async def select_personalized_challenges(
    user_level: str,
    language: str,
    weakness_tags: List[str],
    exclude_ids: List[str] = []
) -> List[Dict[str, Any]]:
    """
    Select 6 challenges (one of each type) personalized for user

    Args:
        user_level: CEFR level (A1-C2)
        language: Target language
        weakness_tags: User's weak areas
        exclude_ids: Challenge IDs to exclude (already completed today)

    Returns:
        List of 6 challenge dictionaries
    """
    challenges_collection = get_challenges_collection()

    challenge_types = [
        "error_spotting",
        "swipe_fix",
        "micro_quiz",
        "smart_flashcard",
        "native_check",
        "brain_tickler"
    ]

    selected_challenges = []

    for challenge_type in challenge_types:
        # Build query
        query = {
            "type": challenge_type,
            "language": language,
            "cefrLevel": user_level,
            "id": {"$nin": exclude_ids}
        }

        # Try to match weakness tags first (personalization)
        if weakness_tags:
            personalized_challenge = await challenges_collection.find_one({
                **query,
                "tags": {"$in": weakness_tags}
            })

            if personalized_challenge:
                personalized_challenge.pop("_id", None)
                selected_challenges.append(personalized_challenge)
                print(f"[CHALLENGES] Selected personalized {challenge_type} for weaknesses: {weakness_tags}")
                continue

        # Fallback: Random challenge of this type at user's level
        import random
        challenges_cursor = challenges_collection.find(query).limit(5)
        available_challenges = await challenges_cursor.to_list(length=5)

        if available_challenges:
            challenge = random.choice(available_challenges)
            challenge.pop("_id", None)
            selected_challenges.append(challenge)
            print(f"[CHALLENGES] Selected random {challenge_type} (no personalization match)")
        else:
            print(f"[CHALLENGES] ⚠️ No {challenge_type} found for level {user_level}")

    # Shuffle to vary order
    import random
    random.shuffle(selected_challenges)

    return selected_challenges


@router.get("/daily")
async def get_daily_challenges(
    current_user: UserResponse = Depends(get_current_user),
    language: Optional[str] = None,
    level: Optional[str] = None
):
    """
    Get 6 personalized daily challenges

    Query Parameters:
    - language (optional): Target language (english, spanish, dutch, german, french, portuguese)
    - level (optional): CEFR level (A1, A2, B1, B2, C1, C2)

    If not provided, falls back to user's active learning plan or profile preferences.

    - Returns cached challenges if available (24h cache)
    - Personalizes based on user's weak areas from flashcards/sessions
    - Marks challenges as completed if user finished them today
    """
    try:
        print(f"[CHALLENGES] 📅 Getting daily challenges for user {current_user.id}")

        user_id = current_user.id

        # Smart resolution: query params > learning plan > profile > defaults
        user_language, user_level = await resolve_language_and_level(
            user_id=user_id,
            user_preferred_level=current_user.preferred_level,
            language_param=language,
            level_param=level
        )

        # Check cache first
        cache_collection = get_daily_challenges_cache_collection()
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        cached_challenges = await cache_collection.find_one({
            "user_id": user_id,
            "language": user_language,
            "date": today_start
        })

        if cached_challenges:
            print(f"[CHALLENGES] ✅ Found cached challenges for today")
            challenges = cached_challenges.get("challenges", [])

            # Update completed status from user stats
            user = await database.users.find_one({"_id": ObjectId(user_id)})
            if user:
                challenge_stats = user.get("challengeStats", {})
                completed_today = challenge_stats.get("completedToday", [])

                for challenge in challenges:
                    challenge["completed"] = challenge["id"] in completed_today

            return DailyChallengesResponse(
                challenges=challenges,
                total_completed_today=len(completed_today) if user else 0,
                streak=challenge_stats.get("currentStreak", 0) if user else 0,
                last_updated=cached_challenges.get("created_at", datetime.utcnow())
            )

        # No cache - generate new AI challenges
        print(f"[CHALLENGES] 🤖 Generating new AI-powered daily challenges")

        # Use AI generator (100% personalized based on user data)
        challenges = await get_or_generate_daily_challenges(
            user_id=user_id,
            user_level=user_level,
            language=user_language
        )

        # Get user stats for completion tracking
        user = await database.users.find_one({"_id": ObjectId(user_id)})
        completed_today = []
        if user:
            challenge_stats = user.get("challengeStats", {})
            completed_today = challenge_stats.get("completedToday", [])

        # Mark completed status
        for challenge in challenges:
            challenge["completed"] = challenge["id"] in completed_today

        # Note: Caching is handled inside get_or_generate_daily_challenges
        print(f"[CHALLENGES] ✅ Retrieved {len(challenges)} AI-generated challenges")

        return DailyChallengesResponse(
            challenges=challenges,
            total_completed_today=len(completed_today),
            streak=challenge_stats.get("currentStreak", 0) if user and challenge_stats else 0,
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        print(f"[CHALLENGES] ❌ Error getting daily challenges: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get daily challenges: {str(e)}")


@router.post("/{challenge_id}/complete")
async def complete_challenge(
    challenge_id: str,
    request: ChallengeCompletionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark a challenge as completed

    - Tracks completion in user stats
    - Updates streak
    - Awards XP (optional for v1)
    """
    try:
        print(f"[CHALLENGES] ✅ Completing challenge {challenge_id} for user {current_user.id}")

        user_id = current_user.id
        today = datetime.utcnow().date()
        today_str = today.isoformat()

        # Get user document
        users_collection = database.users
        user = await users_collection.find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get or create challenge stats
        challenge_stats = user.get("challengeStats", {
            "totalCompleted": 0,
            "currentStreak": 0,
            "lastChallengeDate": None,
            "completedToday": [],
            "completionHistory": {}
        })

        # Check if already completed today
        if challenge_id in challenge_stats.get("completedToday", []):
            print(f"[CHALLENGES] ⚠️ Challenge {challenge_id} already completed today")
            return {
                "success": True,
                "message": "Challenge already completed",
                "already_completed": True,
                "stats": challenge_stats
            }

        # Update completion tracking
        last_challenge_date = challenge_stats.get("lastChallengeDate")
        if isinstance(last_challenge_date, str):
            last_challenge_date = datetime.fromisoformat(last_challenge_date).date()
        elif isinstance(last_challenge_date, datetime):
            last_challenge_date = last_challenge_date.date()

        # Calculate streak
        current_streak = challenge_stats.get("currentStreak", 0)

        if last_challenge_date:
            days_diff = (today - last_challenge_date).days

            if days_diff == 0:
                # Same day - streak continues
                pass
            elif days_diff == 1:
                # Consecutive day - increment streak
                current_streak += 1
            else:
                # Streak broken - reset to 1
                current_streak = 1
        else:
            # First challenge ever
            current_streak = 1

        # Reset completedToday if it's a new day
        if last_challenge_date != today:
            challenge_stats["completedToday"] = []

        # Add to completedToday
        challenge_stats["completedToday"].append(challenge_id)

        # Update stats
        challenge_stats["totalCompleted"] += 1
        challenge_stats["currentStreak"] = current_streak
        challenge_stats["lastChallengeDate"] = datetime.combine(today, datetime.min.time())

        # Update completion history
        if "completionHistory" not in challenge_stats:
            challenge_stats["completionHistory"] = {}

        if today_str not in challenge_stats["completionHistory"]:
            challenge_stats["completionHistory"][today_str] = []

        challenge_stats["completionHistory"][today_str].append({
            "challenge_id": challenge_id,
            "correct": request.correct,
            "time_spent": request.time_spent,
            "completed_at": datetime.utcnow().isoformat()
        })

        # Save to database
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"challengeStats": challenge_stats}}
        )

        if result.modified_count == 0:
            print(f"[CHALLENGES] ⚠️ No changes made to user {user_id}")

        # CHALLENGE POOL: Mark pool item as completed if it exists
        pool_collection = get_challenge_pool_collection()
        pool_result = await pool_collection.update_one(
            {
                "user_id": user_id,
                "challenge_data.id": challenge_id,
                "status": "available"
            },
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                }
            }
        )

        if pool_result.modified_count > 0:
            print(f"[CHALLENGE_POOL] ✅ Marked pool item as completed")
        else:
            print(f"[CHALLENGE_POOL] ℹ️ No pool item found (legacy challenge or already completed)")

        print(f"[CHALLENGES] ✅ Challenge completed. Streak: {current_streak}, Total: {challenge_stats['totalCompleted']}")

        # NEW: Update new stats system (daily_stats, users.stats) for Recent Performance Card
        # This bridges the gap between legacy endpoint and new stats architecture
        try:
            print(f"[CHALLENGES] 🔄 Updating new stats system...")

            # Get user timezone (fallback to UTC if not set)
            user_timezone = user.get("timezone", "UTC")
            local_date = get_current_local_date(user_timezone)

            # Create session data for stats processing
            # Note: Since this is individual challenge completion (not a full session),
            # we'll update daily_stats directly with minimal data
            session_data = {
                "user_id": user_id,
                "local_date": local_date,
                "user_timezone": user_timezone,
                "language": request.language or "unknown",
                "level": request.level or "B1",
                "challenge_type": request.challenge_type or "unknown",
                "total_challenges": 1,  # Single challenge
                "correct_answers": 1 if request.correct else 0,
                "wrong_answers": 0 if request.correct else 1,
                "total_xp": 10 if request.correct else 5,  # Basic XP
                "created_at": datetime.utcnow()
            }

            # Update daily stats (incremental)
            await update_daily_stats(session_data)

            # Update lifetime stats
            await update_lifetime_stats(session_data)

            # Update streak (uses conversation_sessions for streak calculation)
            await update_streak(user_id, local_date, user_timezone)

            print(f"[CHALLENGES] ✅ New stats system updated successfully")
        except Exception as stats_error:
            # Don't fail the request if stats update fails
            print(f"[CHALLENGES] ⚠️ Error updating new stats system: {str(stats_error)}")
            import traceback
            print(traceback.format_exc())

        # PHASE 4.2: Invalidate TaalCoach cache after challenge completion
        try:
            await invalidate_coach_context_smart(user_id, ["challenge", "achievement"])
            print(f"[COACH CACHE] ✅ Invalidated coach cache for user {user_id} after challenge completion")
        except Exception as cache_error:
            # Don't fail the request if cache invalidation fails
            print(f"[COACH CACHE] ⚠️ Error invalidating coach cache: {str(cache_error)}")

        # 🎯 JOURNEY ORCHESTRATOR: Update journey state after challenge completion
        try:
            from services.journey_state_detector import journey_state_detector

            # Trigger journey state update (non-blocking)
            import asyncio
            asyncio.create_task(
                journey_state_detector.detect_journey_stage(user_id, force_recalculate=True)
            )
            print(f"[JOURNEY] ✅ Triggered journey state update for user {user_id}")
        except Exception as journey_error:
            # Don't fail the request if journey update fails
            print(f"[JOURNEY] ⚠️ Error updating journey state: {str(journey_error)}")

        return {
            "success": True,
            "message": "Challenge completed successfully",
            "stats": challenge_stats,
            "streak": current_streak,
            "total_completed": challenge_stats["totalCompleted"],
            "completed_today": len(challenge_stats["completedToday"])
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHALLENGES] ❌ Error completing challenge: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to complete challenge: {str(e)}")


@router.get("/stats")
async def get_challenge_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    Get user's challenge statistics

    Returns:
        - Total completed
        - Current streak
        - Completed today count
        - Challenge history
    """
    try:
        print(f"[CHALLENGES] 📊 Getting stats for user {current_user.id}")

        user_id = current_user.id
        users_collection = database.users

        user = await users_collection.find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        challenge_stats = user.get("challengeStats", {
            "totalCompleted": 0,
            "currentStreak": 0,
            "lastChallengeDate": None,
            "completedToday": [],
            "completionHistory": {}
        })

        return {
            "success": True,
            "stats": challenge_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHALLENGES] ❌ Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get challenge stats: {str(e)}")


# ==================== CHALLENGE POOL SYSTEM ENDPOINTS ====================

@router.get("/counts", response_model=ChallengeCountsResponse)
async def get_challenge_counts(
    current_user: UserResponse = Depends(get_current_user),
    language: Optional[str] = None,
    level: Optional[str] = None,
    source: Optional[str] = None
):
    """
    Get available challenge counts per type for the user

    Query Parameters:
    - language (optional): Target language (english, spanish, dutch, german, french, portuguese)
    - level (optional): CEFR level (A1, A2, B1, B2, C1, C2)
    - source (optional): Challenge source - 'reference' for Freestyle Practice (fast, no AI),
                        'learning_plan' for personalized challenges (AI-generated),
                        None for default behavior (backward compatible)

    If not provided, falls back to user's active learning plan or profile preferences.

    Auto-handling:
    - New users: Instant copy from reference challenges
    - Low pool: Auto-replenishes with personalized AI challenges
    - Always ensures user has content
    """
    try:
        print(f"[CHALLENGE_POOL] 📊 Getting challenge counts for user {current_user.id}, source={source}")

        user_id = current_user.id

        # Smart resolution: query params > learning plan > profile > defaults
        user_language, user_level = await resolve_language_and_level(
            user_id=user_id,
            user_preferred_level=current_user.preferred_level,
            language_param=language,
            level_param=level
        )

        # Import helper functions
        from challenge_pool_helpers import (
            ensure_pool_has_challenges,
            is_new_user,
            get_reference_challenge_counts
        )

        # FREESTYLE PRACTICE: Fetch from reference_challenges collection (FAST - no AI)
        if source == "reference":
            print(f"[REFERENCE] ✅ Using reference challenges (Freestyle Practice)")
            counts = await get_reference_challenge_counts(user_language, user_level)
            return ChallengeCountsResponse(**counts)

        # LEARNING PLAN: Use existing personalized logic (can be slow - AI generation)
        elif source == "learning_plan":
            print(f"[CHALLENGE_POOL] ✅ Using learning plan challenges (Personalized)")
            # Check if new user
            new_user = await is_new_user(user_id)
            # Ensure pool has challenges (handles all scenarios)
            counts = await ensure_pool_has_challenges(user_id, user_level, user_language, new_user)
            return ChallengeCountsResponse(**counts)

        # DEFAULT: Backward compatible (existing behavior)
        else:
            print(f"[CHALLENGE_POOL] ✅ Using default behavior (backward compatible)")
            # Check if new user
            new_user = await is_new_user(user_id)
            # Ensure pool has challenges (handles all scenarios)
            counts = await ensure_pool_has_challenges(user_id, user_level, user_language, new_user)
            print(f"[CHALLENGE_POOL] ✅ Counts: {counts}")
            return ChallengeCountsResponse(**counts)

    except Exception as e:
        print(f"[CHALLENGE_POOL] ❌ Error getting counts: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get challenge counts: {str(e)}")


@router.get("/by-type/{challenge_type}", response_model=ChallengesByTypeResponse)
async def get_challenges_by_type(
    challenge_type: str,
    current_user: UserResponse = Depends(get_current_user),
    language: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 50,
    source: Optional[str] = None
):
    """
    Get available challenges of a specific type

    Path Parameters:
    - challenge_type: Type of challenge (error_spotting, swipe_fix, etc.)

    Query Parameters:
    - language (optional): Target language (english, spanish, dutch, german, french, portuguese)
    - level (optional): CEFR level (A1, A2, B1, B2, C1, C2)
    - limit: Maximum number of challenges to return (default 50)
    - source (optional): Challenge source - 'reference' for Freestyle Practice (fast, no AI),
                        'learning_plan' for personalized challenges (AI-generated),
                        None for default behavior (backward compatible)

    If language/level not provided, falls back to user's active learning plan or profile preferences.

    Returns list of available challenges sorted by creation date
    """
    try:
        # Validate challenge type
        valid_types = [
            "error_spotting", "swipe_fix", "micro_quiz",
            "smart_flashcard", "native_check", "brain_tickler", "story_builder"
        ]

        if challenge_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid challenge type. Must be one of: {', '.join(valid_types)}"
            )

        user_id = current_user.id

        # Smart resolution: query params > learning plan > profile > defaults
        user_language, user_level = await resolve_language_and_level(
            user_id=user_id,
            user_preferred_level=current_user.preferred_level,
            language_param=language,
            level_param=level
        )

        print(f"[CHALLENGE_POOL] 📚 Getting {challenge_type} challenges for user {current_user.id}, language: {user_language}, level: {user_level}, source={source}")

        # FREESTYLE PRACTICE: Fetch from reference_challenges collection (FAST - no AI)
        if source == "reference":
            print(f"[REFERENCE] ✅ Using reference challenges (Freestyle Practice)")
            from challenge_pool_helpers import get_reference_challenges

            challenges = await get_reference_challenges(
                challenge_type=challenge_type,
                language=user_language,
                level=user_level,
                limit=limit,
                user_id=user_id
            )

            return ChallengesByTypeResponse(
                challenges=challenges,
                total=len(challenges),
                type=challenge_type
            )

        # LEARNING PLAN or DEFAULT: Use existing pool logic
        else:
            if source == "learning_plan":
                print(f"[CHALLENGE_POOL] ✅ Using learning plan challenges (Personalized)")
            else:
                print(f"[CHALLENGE_POOL] ✅ Using default behavior (backward compatible)")

            pool_collection = get_challenge_pool_collection()

            # Get available challenges of this type - FILTER BY LANGUAGE AND CEFR LEVEL!
            cursor = pool_collection.find({
                "user_id": user_id,
                "language": user_language,
                "challenge_type": challenge_type,
                "cefr_level": user_level,
                "status": "available"
            }).sort("created_at", -1).limit(limit)

            challenges_raw = await cursor.to_list(length=limit)

            # Extract challenge_data from each pool item
            challenges = []
            for item in challenges_raw:
                challenge_data = item.get("challenge_data", {})
                # Add pool item ID for completion tracking
                challenge_data["pool_item_id"] = str(item.get("_id"))
                challenges.append(challenge_data)

            print(f"[CHALLENGE_POOL] ✅ Found {len(challenges)} {challenge_type} challenges for language {user_language}, level {user_level}")

            return ChallengesByTypeResponse(
                challenges=challenges,
                total=len(challenges),
                type=challenge_type
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHALLENGE_POOL] ❌ Error getting challenges by type: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get challenges: {str(e)}")


@router.get("/languages")
async def get_available_languages(
    current_user: UserResponse = Depends(get_current_user),
    level: Optional[str] = None
):
    """
    Get list of all available languages and user's learning status

    Query Parameters:
    - level (optional): CEFR level to check counts for (A1, A2, B1, B2, C1, C2)

    Returns:
        List of languages with:
        - Language name
        - Whether user has active plan
        - Challenge counts available (for specified or user's level)
    """
    try:
        print(f"[CHALLENGES] 🌍 Getting available languages for user {current_user.id}")

        user_id = current_user.id

        # Use provided level or user's preferred level
        user_level = level.upper() if level else (current_user.preferred_level or "B1")

        # Validate level
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if user_level not in valid_levels:
            user_level = "B1"

        # All supported languages
        all_languages = ["english", "spanish", "dutch", "german", "french", "portuguese"]

        # Get user's learning plans
        learning_plans_collection = database.learning_plans
        user_plans = await learning_plans_collection.find({
            "user_id": user_id
        }).to_list(length=10)

        # Build language status map
        languages_with_plans = {}
        active_language = None

        for plan in user_plans:
            lang = plan.get("language", "").lower()
            is_active = plan.get("is_active", False)

            if lang:
                languages_with_plans[lang] = {
                    "has_plan": True,
                    "is_active": is_active
                }

                if is_active:
                    active_language = lang

        # Get challenge counts for each language
        pool_collection = get_challenge_pool_collection()

        result = []
        for language in all_languages:
            # Count available challenges for this language
            count = await pool_collection.count_documents({
                "user_id": user_id,
                "language": language,
                "cefr_level": user_level,
                "status": "available"
            })

            plan_info = languages_with_plans.get(language, {"has_plan": False, "is_active": False})

            result.append({
                "language": language,
                "has_learning_plan": plan_info["has_plan"],
                "is_active": plan_info["is_active"],
                "available_challenges": count
            })

        print(f"[CHALLENGES] ✅ Found {len(result)} languages. Active: {active_language}")

        return {
            "success": True,
            "languages": result,
            "active_language": active_language
        }

    except Exception as e:
        print(f"[CHALLENGES] ❌ Error getting languages: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")
