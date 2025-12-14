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
)
from database import database
from challenge_generator import generate_daily_challenges_intelligent

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


def get_challenges_collection():
    """Get challenges collection from database"""
    return database.challenges


def get_daily_challenges_cache_collection():
    """Get daily challenges cache collection"""
    return database.daily_challenges_cache


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
    weakness_tags: List[str],
    exclude_ids: List[str] = []
) -> List[Dict[str, Any]]:
    """
    Select 6 challenges (one of each type) personalized for user

    Args:
        user_level: CEFR level (A1-C2)
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
async def get_daily_challenges(current_user: UserResponse = Depends(get_current_user)):
    """
    Get 6 personalized daily challenges

    - Returns cached challenges if available (24h cache)
    - Personalizes based on user's weak areas from flashcards/sessions
    - Marks challenges as completed if user finished them today
    """
    try:
        print(f"[CHALLENGES] 📅 Getting daily challenges for user {current_user.id}")

        user_id = current_user.id
        user_level = current_user.preferred_level or "B1"

        # Check cache first
        cache_collection = get_daily_challenges_cache_collection()
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        cached_challenges = await cache_collection.find_one({
            "user_id": user_id,
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

        # No cache - generate new daily challenges INTELLIGENTLY
        print(f"[CHALLENGES] 🔄 Generating new intelligent daily challenges")

        # Use intelligent generator (50% user data + 50% seed data)
        challenges = await generate_daily_challenges_intelligent(
            user_id=user_id,
            user_level=user_level
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

        # Cache for 24 hours
        cache_doc = {
            "user_id": user_id,
            "date": today_start,
            "challenges": challenges,
            "created_at": datetime.utcnow()
        }

        # Create TTL index on cache collection (24 hours)
        await cache_collection.create_index("created_at", expireAfterSeconds=24*60*60)
        await cache_collection.insert_one(cache_doc)

        print(f"[CHALLENGES] ✅ Generated and cached {len(challenges)} challenges")

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

        print(f"[CHALLENGES] ✅ Challenge completed. Streak: {current_streak}, Total: {challenge_stats['totalCompleted']}")

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
