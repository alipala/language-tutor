"""
Caching Helpers for MongoDB Queries
Provides cache-first data access patterns with Redis

Key Caching Strategies:
- User profiles: 5 minutes (frequently read, rarely updated)
- Learning plans: 10 minutes (moderate read frequency)
- Subscription status: 5 minutes (checked on every request)
- Daily stats: 10 minutes (updated after each challenge)
- Reference challenges: 1 hour (static content, rarely changes)
- TaalCoach user context: 5 minutes (personalized chatbot responses)
"""

from typing import Optional, Dict, Any, List
from bson import ObjectId
import logging

from redis_client import get_cached, set_cached, delete_cached, delete_pattern
from database import (
    users_collection,
    learning_plans_collection,
    daily_stats_collection,
    reference_challenges_collection,
    conversation_sessions_collection,
    challenge_sessions_collection,  # CRITICAL: Challenge gameplay data
    # COMPREHENSIVE USER DATA COLLECTIONS (100% COVERAGE)
    flashcard_sets_collection,
    flashcards_collection,
    assessments_collection,
    session_completions_collection,
    speaking_time_tracking_collection,
    sentence_analysis_feedback_collection,
    story_contributions_collection,
    user_story_achievements_collection,
    learning_goals_collection,
    # NEWLY ADDED: Complete TaalCoach awareness (12 critical collections)
    speaking_dna_profiles_collection,
    speaking_dna_history_collection,
    speaking_breakthroughs_collection,
    user_achievements_collection,
    recent_performance_collection,
    session_feedback_collection,
    news_articles_collection,
    notifications_collection,
    heart_events_collection,
    rescue_events_collection,
    sharing_activity_collection,
    user_notifications_collection
)

logger = logging.getLogger(__name__)

# ============================================================================
# USER PROFILE CACHING
# ============================================================================

async def get_user_cached(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile with Redis caching

    Cache key: user:{user_id}
    TTL: 5 minutes (300s)

    Args:
        user_id: User ID (string or ObjectId)

    Returns:
        User document or None
    """
    cache_key = f"user:{user_id}"

    # Try cache first
    cached_user = await get_cached(cache_key)
    if cached_user:
        logger.info(f"✅ [CACHE] User profile cache HIT: {user_id}")
        return cached_user

    # Cache miss - query MongoDB
    try:
        logger.info(f"❌ [CACHE] User profile cache MISS: {user_id} - querying MongoDB")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            # Convert ObjectId to string for JSON serialization
            user["_id"] = str(user["_id"])

            # Cache for 5 minutes
            await set_cached(cache_key, user, ttl_seconds=300)
            logger.info(f"📦 [CACHE] Cached user profile: {user_id} (5min TTL)")

        return user
    except Exception as e:
        logger.error(f"❌ Error fetching user {user_id}: {str(e)}")
        return None

async def invalidate_user_cache(user_id: str):
    """
    Invalidate user cache when profile is updated

    Call this after any user update operation:
    - Profile updates
    - Subscription changes
    - Settings changes
    """
    cache_key = f"user:{user_id}"
    await delete_cached(cache_key)

    # Also invalidate subscription cache (which is a subset)
    subscription_key = f"subscription:{user_id}"
    await delete_cached(subscription_key)

    # Also invalidate TaalCoach context cache
    taalcoach_key = f"taalcoach:context:{user_id}"
    await delete_cached(taalcoach_key)

    logger.info(f"🗑️  [CACHE] Invalidated user cache: {user_id}")

# ============================================================================
# LEARNING PLAN CACHING
# ============================================================================

async def get_learning_plan_cached(plan_id: str) -> Optional[Dict[str, Any]]:
    """
    Get learning plan with Redis caching

    Cache key: learning_plan:{plan_id}
    TTL: 10 minutes (600s)

    Args:
        plan_id: Learning plan ID

    Returns:
        Learning plan document or None
    """
    cache_key = f"learning_plan:{plan_id}"

    # Try cache first
    cached_plan = await get_cached(cache_key)
    if cached_plan:
        logger.info(f"✅ [CACHE] Learning plan cache HIT: {plan_id}")
        return cached_plan

    # Cache miss - query MongoDB
    try:
        logger.info(f"❌ [CACHE] Learning plan cache MISS: {plan_id} - querying MongoDB")
        plan = await learning_plans_collection.find_one({"id": plan_id})
        if plan:
            # Convert ObjectId to string
            plan["_id"] = str(plan["_id"])

            # Cache for 10 minutes
            await set_cached(cache_key, plan, ttl_seconds=600)
            logger.info(f"📦 [CACHE] Cached learning plan: {plan_id} (10min TTL)")

        return plan
    except Exception as e:
        logger.error(f"❌ Error fetching learning plan {plan_id}: {str(e)}")
        return None

async def get_user_active_plan_cached(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's active learning plan with Redis caching

    Cache key: user_active_plan:{user_id}
    TTL: 10 minutes (600s)
    """
    cache_key = f"user_active_plan:{user_id}"

    # Try cache first
    cached_plan = await get_cached(cache_key)
    if cached_plan:
        logger.info(f"✅ [CACHE] Active plan cache HIT: {user_id}")
        return cached_plan

    # Cache miss - query MongoDB
    try:
        logger.info(f"❌ [CACHE] Active plan cache MISS: {user_id} - querying MongoDB")
        plan = await learning_plans_collection.find_one({
            "user_id": user_id,
            "is_active": True
        })

        if plan:
            # Convert ObjectId to string
            plan["_id"] = str(plan["_id"])

            # Cache for 10 minutes
            await set_cached(cache_key, plan, ttl_seconds=600)
            logger.info(f"📦 [CACHE] Cached active plan for user: {user_id} (10min TTL)")

        return plan
    except Exception as e:
        logger.error(f"❌ Error fetching active plan for user {user_id}: {str(e)}")
        return None

async def invalidate_learning_plan_cache(plan_id: str, user_id: str = None):
    """
    Invalidate learning plan cache when plan is updated

    Call this after:
    - Session completion
    - Plan progress updates
    - Plan status changes
    """
    cache_key = f"learning_plan:{plan_id}"
    await delete_cached(cache_key)
    logger.info(f"🗑️  [CACHE] Invalidated learning plan cache: {plan_id}")

    # Also invalidate user's active plan cache
    if user_id:
        user_plan_key = f"user_active_plan:{user_id}"
        await delete_cached(user_plan_key)

        # Also invalidate TaalCoach context (includes learning plans)
        taalcoach_key = f"taalcoach:context:{user_id}"
        await delete_cached(taalcoach_key)

        logger.info(f"🗑️  [CACHE] Invalidated user active plan cache: {user_id}")

# ============================================================================
# SUBSCRIPTION STATUS CACHING
# ============================================================================

async def get_subscription_status_cached(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's subscription status with Redis caching

    Cache key: subscription:{user_id}
    TTL: 5 minutes (300s)

    This is a subset of user profile specifically for subscription checks
    Faster than full user profile query
    """
    cache_key = f"subscription:{user_id}"

    # Try cache first
    cached_status = await get_cached(cache_key)
    if cached_status:
        logger.debug(f"✅ [CACHE] Subscription cache HIT: {user_id}")
        return cached_status

    # Cache miss - query MongoDB (only subscription fields)
    try:
        logger.debug(f"❌ [CACHE] Subscription cache MISS: {user_id} - querying MongoDB")
        user = await users_collection.find_one(
            {"_id": ObjectId(user_id)},
            projection={
                "subscription_status": 1,
                "subscription_plan": 1,
                "subscription_period": 1,
                "subscription_expires_at": 1,
                "practice_minutes_used": 1,
                "heart_system_state": 1,
                "is_in_trial": 1
            }
        )

        if user:
            # Convert ObjectId to string
            user["_id"] = str(user["_id"])

            # Cache for 5 minutes
            await set_cached(cache_key, user, ttl_seconds=300)
            logger.info(f"📦 [CACHE] Cached subscription status: {user_id} (5min TTL)")

        return user
    except Exception as e:
        logger.error(f"❌ Error fetching subscription status {user_id}: {str(e)}")
        return None

async def invalidate_subscription_cache(user_id: str):
    """
    Invalidate subscription cache when subscription changes

    Call this after:
    - Subscription upgrades/downgrades
    - Subscription cancellations
    - Trial starts/ends
    - Practice minutes updates
    """
    cache_key = f"subscription:{user_id}"
    await delete_cached(cache_key)

    # Also invalidate full user cache
    user_key = f"user:{user_id}"
    await delete_cached(user_key)

    # Also invalidate TaalCoach context
    taalcoach_key = f"taalcoach:context:{user_id}"
    await delete_cached(taalcoach_key)

    logger.info(f"🗑️  [CACHE] Invalidated subscription cache: {user_id}")

# ============================================================================
# DAILY STATS CACHING
# ============================================================================

async def get_daily_stats_cached(user_id: str, local_date: str) -> Optional[Dict[str, Any]]:
    """
    Get daily stats with Redis caching

    Cache key: daily_stats:{user_id}:{local_date}
    TTL: 10 minutes (600s)

    Args:
        user_id: User ID
        local_date: Local date string (YYYY-MM-DD)
    """
    cache_key = f"daily_stats:{user_id}:{local_date}"

    # Try cache first
    cached_stats = await get_cached(cache_key)
    if cached_stats:
        logger.debug(f"✅ [CACHE] Daily stats cache HIT: {user_id}/{local_date}")
        return cached_stats

    # Cache miss - query MongoDB
    try:
        logger.debug(f"❌ [CACHE] Daily stats cache MISS: {user_id}/{local_date} - querying MongoDB")
        stats = await daily_stats_collection.find_one({
            "user_id": user_id,
            "local_date": local_date
        })

        if stats:
            # Convert ObjectId to string
            stats["_id"] = str(stats["_id"])

            # Cache for 10 minutes
            await set_cached(cache_key, stats, ttl_seconds=600)
            logger.info(f"📦 [CACHE] Cached daily stats: {user_id}/{local_date} (10min TTL)")

        return stats
    except Exception as e:
        logger.error(f"❌ Error fetching daily stats {user_id}/{local_date}: {str(e)}")
        return None

async def invalidate_daily_stats_cache(user_id: str, local_date: str):
    """
    Invalidate daily stats cache when stats are updated

    Call this after:
    - Challenge completion
    - Session end
    - XP updates
    """
    cache_key = f"daily_stats:{user_id}:{local_date}"
    await delete_cached(cache_key)
    logger.info(f"🗑️  [CACHE] Invalidated daily stats cache: {user_id}/{local_date}")

# ============================================================================
# REFERENCE CHALLENGES CACHING
# ============================================================================

async def get_reference_challenges_cached(
    language: str,
    level: str,
    challenge_type: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Get reference challenges with Redis caching

    Cache key: ref_challenges:{language}:{level}:{type}
    TTL: 1 hour (3600s)

    Reference challenges are static content, cache aggressively
    """
    cache_key = f"ref_challenges:{language}:{level}:{challenge_type}"

    # Try cache first
    cached_challenges = await get_cached(cache_key)
    if cached_challenges:
        logger.info(f"✅ [CACHE] Reference challenges cache HIT: {language}/{level}/{challenge_type}")
        return cached_challenges

    # Cache miss - query MongoDB
    try:
        logger.info(f"❌ [CACHE] Reference challenges cache MISS: {language}/{level}/{challenge_type} - querying MongoDB")
        cursor = reference_challenges_collection.find({
            "language": language,
            "level": level,
            "challenge_type": challenge_type
        }).limit(50)

        challenges = await cursor.to_list(length=50)

        if challenges:
            # Convert ObjectId to string
            for challenge in challenges:
                challenge["_id"] = str(challenge["_id"])

            # Cache for 1 hour (static content)
            await set_cached(cache_key, challenges, ttl_seconds=3600)
            logger.info(f"📦 [CACHE] Cached reference challenges: {language}/{level}/{challenge_type} (1hour TTL)")

        return challenges if challenges else None
    except Exception as e:
        logger.error(f"❌ Error fetching reference challenges: {str(e)}")
        return None

async def invalidate_all_reference_challenges():
    """
    Invalidate all reference challenges cache

    Call this after:
    - Seeding reference challenges
    - Updating challenge templates
    """
    await delete_pattern("ref_challenges:*")
    logger.info(f"🗑️  [CACHE] Invalidated all reference challenges cache")

# ============================================================================
# TAALCOACH USER CONTEXT CACHING
# ============================================================================

async def get_taalcoach_context_cached(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get TaalCoach user context with Redis caching

    Cache key: taalcoach:context:{user_id}
    TTL: 5 minutes (300s)

    This caches the comprehensive user context used by the contextual chatbot
    in the "Learn" tab (TaalCoach). Includes:
    - User profile data
    - Subscription status
    - Learning plans
    - Recent conversation history
    - Progress stats

    Args:
        user_id: User ID

    Returns:
        User context dict or None
    """
    cache_key = f"taalcoach:context:{user_id}"

    # Try cache first
    cached_context = await get_cached(cache_key)
    if cached_context:
        logger.info(f"✅ [CACHE] TaalCoach context cache HIT: {user_id}")
        return cached_context

    # Cache miss - build context from MongoDB
    try:
        logger.info(f"❌ [CACHE] TaalCoach context cache MISS: {user_id} - querying MongoDB")

        # Get user document
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return None

        # EXISTING: Core data
        learning_plans = await learning_plans_collection.find({"user_id": user_id}).to_list(length=10)
        conversations = await conversation_sessions_collection.find({"user_id": user_id}).sort("created_at", -1).limit(5).to_list(length=5)

        # CRITICAL: Challenge sessions data (was missing - caused TaalCoach to not respond to challenge queries)
        challenge_sessions = await challenge_sessions_collection.find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)

        # HIGH PRIORITY: Fetch all missing user activity data
        flashcard_sets = await flashcard_sets_collection.find({"user_id": user_id}).to_list(length=100)
        assessments = await assessments_collection.find({"user_id": user_id}).sort("created_at", -1).limit(10).to_list(length=10)
        session_completions = await session_completions_collection.find({"user_id": user_id}).to_list(length=100)
        speaking_time_logs = await speaking_time_tracking_collection.find({"user_id": user_id}).sort("date", -1).limit(30).to_list(length=30)
        sentence_feedback = await sentence_analysis_feedback_collection.find({"user_id": user_id}).sort("created_at", -1).limit(50).to_list(length=50)
        story_contributions = await story_contributions_collection.find({"user_id": user_id}).to_list(length=50)
        story_achievements = await user_story_achievements_collection.find({"user_id": user_id}).to_list(length=50)
        learning_goals = await learning_goals_collection.find({"user_id": user_id}).to_list(length=20)

        # COMPREHENSIVE COVERAGE: Fetch all 12 missing critical collections
        speaking_dna_profile = await speaking_dna_profiles_collection.find_one({"user_id": user_id})
        speaking_dna_history = await speaking_dna_history_collection.find({"user_id": user_id}).sort("created_at", -1).limit(10).to_list(length=10)
        speaking_breakthroughs = await speaking_breakthroughs_collection.find({"user_id": user_id}).sort("detected_at", -1).limit(10).to_list(length=10)
        user_achievements = await user_achievements_collection.find({"user_id": user_id}).to_list(length=100)
        recent_performance = await recent_performance_collection.find_one({"user_id": user_id})
        session_feedback = await session_feedback_collection.find({"user_id": user_id}).sort("created_at", -1).limit(10).to_list(length=10)
        news_articles_read = await news_articles_collection.find({"readers": user_id}).sort("published_at", -1).limit(20).to_list(length=20)
        notifications = await notifications_collection.find({"user_id": user_id}).sort("created_at", -1).limit(20).to_list(length=20)
        heart_events = await heart_events_collection.find({"user_id": user_id}).sort("created_at", -1).limit(50).to_list(length=50)
        rescue_events = await rescue_events_collection.find({"user_id": user_id}).sort("triggered_at", -1).limit(10).to_list(length=10)
        sharing_activity = await sharing_activity_collection.find({"user_id": user_id}).sort("shared_at", -1).limit(10).to_list(length=10)
        user_notifications = await user_notifications_collection.find({"user_id": user_id}).sort("created_at", -1).limit(20).to_list(length=20)

        # Calculate stats
        total_sessions = len(conversations)
        total_minutes = sum(session.get('duration_minutes', 0) for session in conversations)

        # Build comprehensive context with ALL user data
        context = {
            # EXISTING: Core user info
            "user_type": "registered",
            "subscription_plan": user_doc.get("subscription_plan", "try_learn"),
            "subscription_status": user_doc.get("subscription_status", "active"),
            "is_in_trial": user_doc.get("is_in_trial", False),
            "learning_plans_count": len(learning_plans),
            "total_sessions": total_sessions,
            "total_minutes": round(total_minutes, 1),
            "current_streak": user_doc.get("stats", {}).get("current_streak", 0),
            "preferred_language": user_doc.get("preferred_language"),
            "preferred_level": user_doc.get("preferred_level"),
            "recent_languages": list(set([conv.get('language') for conv in conversations if conv.get('language')])),
            "usage_this_month": {
                "sessions_used": user_doc.get("practice_sessions_used", 0),
                "assessments_used": user_doc.get("assessments_used", 0)
            },
            "features_available": get_features_for_plan(user_doc.get("subscription_plan", "try_learn")),
            "limitations": get_limitations_for_plan(user_doc.get("subscription_plan", "try_learn")),

            # CRITICAL: Challenge sessions data (was missing - caused TaalCoach to not respond to challenge queries)
            "challenges": {
                "total_completed": len(challenge_sessions),
                "by_type": {
                    "micro_quiz": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "micro_quiz"]),
                    "error_spotting": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "error_spotting"]),
                    "swipe_fix": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "swipe_fix"]),
                    "brain_tickler": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "brain_tickler"]),
                    "story_builder": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "story_builder"]),
                    "smart_flashcard": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "smart_flashcard"]),
                    "native_check": len([cs for cs in challenge_sessions if cs.get("challenge_type") == "native_check"])
                },
                "recent_sessions": [
                    {
                        "challenge_type": cs.get("challenge_type"),
                        "language": cs.get("language"),
                        "level": cs.get("level"),
                        "score": cs.get("score", 0),
                        "correct_answers": cs.get("correct_answers", 0),
                        "total_questions": cs.get("total_questions", 0),
                        "completed_at": cs.get("created_at"),
                        "duration_seconds": cs.get("duration_seconds", 0)
                    } for cs in challenge_sessions[:20]
                ],
                "total_correct": sum(cs.get("correct_answers", 0) for cs in challenge_sessions),
                "total_questions": sum(cs.get("total_questions", 0) for cs in challenge_sessions),
                "average_score": round(sum(cs.get("score", 0) for cs in challenge_sessions) / len(challenge_sessions), 1) if challenge_sessions else 0
            },

            # NEW: Flashcard data (HIGH PRIORITY)
            "flashcards": {
                "total_sets": len(flashcard_sets),
                "sets": [
                    {
                        "id": str(fs.get("_id", "")),
                        "language": fs.get("language"),
                        "level": fs.get("level"),
                        "title": fs.get("title", ""),
                        "total_cards": fs.get("total_cards", 0),
                        "mastered_cards": fs.get("mastered_cards", 0),
                        "created_from": fs.get("created_from", "")  # learning_plan, challenge, etc.
                    } for fs in flashcard_sets
                ]
            },

            # NEW: Assessment history (HIGH PRIORITY)
            "assessments": {
                "total_count": len(assessments),
                "recent_scores": [
                    {
                        "date": a.get("created_at"),
                        "language": a.get("language"),
                        "level": a.get("level"),
                        "score": a.get("score"),
                        "feedback": a.get("feedback", "")
                    } for a in assessments[:5]
                ],
                "average_score": round(sum(a.get("score", 0) for a in assessments) / len(assessments), 1) if assessments else 0
            },

            # NEW: Session completion tracking (HIGH PRIORITY)
            "session_completions": {
                "total_completed": len(session_completions),
                "recent_completions": [
                    {
                        "date": sc.get("completed_at"),
                        "session_type": sc.get("session_type"),
                        "language": sc.get("language"),
                        "duration_minutes": sc.get("duration_minutes", 0)
                    } for sc in session_completions[:10]
                ]
            },

            # NEW: Speaking time breakdown (HIGH PRIORITY)
            "speaking_time": {
                "total_entries": len(speaking_time_logs),
                "recent": [
                    {
                        "date": st.get("date"),
                        "minutes": st.get("minutes"),
                        "language": st.get("language")
                    } for st in speaking_time_logs[:7]
                ],
                "total_speaking_minutes": sum(st.get("minutes", 0) for st in speaking_time_logs)
            },

            # NEW: Sentence-level feedback (HIGH PRIORITY)
            "sentence_feedback": {
                "total_feedback": len(sentence_feedback),
                "common_mistakes": [
                    {
                        "sentence": sf.get("original_sentence", ""),
                        "correction": sf.get("corrected_sentence", ""),
                        "error_type": sf.get("error_type", ""),
                        "date": sf.get("created_at")
                    } for sf in sentence_feedback[:10]
                ]
            },

            # NEW: Story builder data (HIGH PRIORITY)
            "story_builder": {
                "total_contributions": len(story_contributions),
                "total_achievements": len(story_achievements),
                "recent_stories": [
                    {
                        "title": sc.get("title", ""),
                        "language": sc.get("language"),
                        "created_at": sc.get("created_at"),
                        "word_count": sc.get("word_count", 0)
                    } for sc in story_contributions[:5]
                ],
                "achievements": [
                    {
                        "achievement_type": sa.get("achievement_type", ""),
                        "earned_at": sa.get("earned_at"),
                        "description": sa.get("description", "")
                    } for sa in story_achievements
                ]
            },

            # NEW: Learning goals (HIGH PRIORITY)
            "learning_goals": {
                "total_goals": len(learning_goals),
                "active_goals": [
                    {
                        "goal": lg.get("goal_text", ""),
                        "target_date": lg.get("target_date"),
                        "progress": lg.get("progress_percent", 0),
                        "created_at": lg.get("created_at")
                    } for lg in learning_goals if lg.get("status") == "active"
                ],
                "completed_goals": len([lg for lg in learning_goals if lg.get("status") == "completed"])
            },

            # COMPREHENSIVE COVERAGE: 12 critical collections for 100% TaalCoach awareness

            # 1. Speaking DNA Profile (Premium feature)
            "speaking_dna": {
                "has_profile": speaking_dna_profile is not None,
                "latest_profile": {
                    "confidence": speaking_dna_profile.get("confidence", 0),
                    "fluency": speaking_dna_profile.get("fluency", 0),
                    "pronunciation": speaking_dna_profile.get("pronunciation", 0),
                    "vocabulary": speaking_dna_profile.get("vocabulary", 0),
                    "grammar": speaking_dna_profile.get("grammar", 0),
                    "created_at": speaking_dna_profile.get("created_at"),
                    "language": speaking_dna_profile.get("language")
                } if speaking_dna_profile else None,
                "history_count": len(speaking_dna_history),
                "recent_snapshots": [
                    {
                        "confidence": h.get("confidence", 0),
                        "fluency": h.get("fluency", 0),
                        "created_at": h.get("created_at")
                    } for h in speaking_dna_history[:5]
                ]
            },

            # 2. Speaking Breakthroughs (Significant improvements)
            "speaking_breakthroughs": {
                "total_breakthroughs": len(speaking_breakthroughs),
                "recent": [
                    {
                        "breakthrough_type": sb.get("breakthrough_type"),
                        "metric": sb.get("metric"),
                        "improvement": sb.get("improvement_percent", 0),
                        "detected_at": sb.get("detected_at"),
                        "description": sb.get("description", "")
                    } for sb in speaking_breakthroughs[:5]
                ]
            },

            # 3. User Achievements/Badges (Gamification)
            "achievements": {
                "total_unlocked": len(user_achievements),
                "recent_unlocked": [
                    {
                        "achievement_id": ua.get("achievement_id"),
                        "category": ua.get("category"),
                        "unlocked_at": ua.get("unlocked_at"),
                        "title": ua.get("title", ""),
                        "description": ua.get("description", "")
                    } for ua in sorted(user_achievements, key=lambda x: x.get("unlocked_at", ""), reverse=True)[:10]
                ],
                "by_category": {}  # Will be filled below
            },

            # 4. Recent Performance (Accuracy trends)
            "recent_performance": {
                "has_data": recent_performance is not None,
                "accuracy_7d": recent_performance.get("accuracy_last_7_days", 0) if recent_performance else 0,
                "accuracy_30d": recent_performance.get("accuracy_last_30_days", 0) if recent_performance else 0,
                "sessions_7d": recent_performance.get("sessions_last_7_days", 0) if recent_performance else 0,
                "challenges_7d": recent_performance.get("challenges_last_7_days", 0) if recent_performance else 0,
                "improvement_trend": recent_performance.get("improvement_trend", "stable") if recent_performance else "no_data"
            },

            # 5. Session Feedback (Post-session evaluations)
            "session_feedback_history": {
                "total_feedback": len(session_feedback),
                "recent": [
                    {
                        "session_id": sf.get("session_id"),
                        "rating": sf.get("rating", 0),
                        "feedback_text": sf.get("feedback_text", ""),
                        "areas_improved": sf.get("areas_improved", []),
                        "created_at": sf.get("created_at")
                    } for sf in session_feedback[:5]
                ],
                "average_rating": sum(sf.get("rating", 0) for sf in session_feedback) / len(session_feedback) if session_feedback else 0
            },

            # 6. News Articles Read (Reading practice tracking)
            "news_reading": {
                "total_articles_read": len(news_articles_read),
                "recent_articles": [
                    {
                        "title": na.get("title", ""),
                        "language": na.get("language"),
                        "level": na.get("level"),
                        "category": na.get("category", ""),
                        "published_at": na.get("published_at")
                    } for na in news_articles_read[:10]
                ]
            },

            # 7. Hearts/Focus Energy (Free user tracking)
            "hearts_focus_energy": {
                "total_events": len(heart_events),
                "hearts_consumed_30d": len([h for h in heart_events if h.get("event_type") == "consume"]),
                "hearts_refilled_30d": len([h for h in heart_events if h.get("event_type") == "refill"]),
                "by_challenge_type": {},  # Will be filled below
                "recent_events": [
                    {
                        "event_type": he.get("event_type"),
                        "challenge_type": he.get("challenge_type"),
                        "hearts_delta": he.get("hearts_delta", 0),
                        "created_at": he.get("created_at")
                    } for he in heart_events[:10]
                ]
            },

            # 8. Rescue Events (AI rescue feature usage)
            "rescue_events": {
                "total_rescues": len(rescue_events),
                "recent": [
                    {
                        "rescue_type": re.get("rescue_type"),
                        "triggered_at": re.get("triggered_at"),
                        "was_helpful": re.get("was_helpful", False),
                        "context": re.get("context", "")
                    } for re in rescue_events[:5]
                ]
            },

            # 9. Sharing Activity (Social features)
            "sharing": {
                "total_shares": len(sharing_activity),
                "recent": [
                    {
                        "shared_content_type": sa.get("shared_content_type"),
                        "platform": sa.get("platform", ""),
                        "shared_at": sa.get("shared_at")
                    } for sa in sharing_activity[:5]
                ]
            },

            # 10. Notifications (User notifications)
            "notifications": {
                "total_notifications": len(notifications),
                "unread_count": len([n for n in notifications if not n.get("read", False)]),
                "recent": [
                    {
                        "notification_type": n.get("notification_type"),
                        "title": n.get("title", ""),
                        "read": n.get("read", False),
                        "created_at": n.get("created_at")
                    } for n in notifications[:10]
                ]
            },

            # 11. User Notifications (Additional notification system)
            "user_notifications": {
                "total": len(user_notifications),
                "recent": [
                    {
                        "type": un.get("type"),
                        "message": un.get("message", ""),
                        "created_at": un.get("created_at")
                    } for un in user_notifications[:5]
                ]
            },

            # 12. Daily Stats (XP, streaks, daily metrics)
            "daily_stats": {
                "current_streak": user_doc.get("stats", {}).get("current_streak", 0),
                "longest_streak": user_doc.get("stats", {}).get("longest_streak", 0),
                "total_xp": user_doc.get("stats", {}).get("lifetime", {}).get("total_xp", 0),
                "xp_today": 0,  # Will be calculated from daily_stats if needed
                "level": user_doc.get("stats", {}).get("level", 1)
            }
        }

        # Cache for 5 minutes
        await set_cached(cache_key, context, ttl_seconds=300)
        logger.info(f"📦 [CACHE] Cached TaalCoach context: {user_id} (5min TTL)")

        return context

    except Exception as e:
        logger.error(f"❌ Error building TaalCoach context for {user_id}: {str(e)}")
        return None

def get_features_for_plan(plan: str) -> List[str]:
    """Get features available for a subscription plan"""
    if plan == "try_learn":
        return [
            "3 sessions per month",
            "30s assessments",
            "2min conversations",
            "Basic progress tracking"
        ]
    elif plan == "fluency_builder":
        return [
            "30 sessions per month",
            "60s assessments",
            "5min conversations",
            "Full progress tracking",
            "Enhanced analysis",
            "Achievement system"
        ]
    elif plan == "team_mastery":
        return [
            "Unlimited sessions",
            "60s assessments",
            "5min conversations",
            "Team dashboard",
            "Advanced analytics",
            "API access"
        ]
    return []

def get_limitations_for_plan(plan: str) -> List[str]:
    """Get limitations for a subscription plan"""
    if plan == "try_learn":
        return [
            "Limited to 3 sessions/month",
            "Shorter assessment time",
            "Shorter conversation time",
            "No advanced features"
        ]
    elif plan == "fluency_builder":
        return [
            "Limited to 30 sessions/month",
            "No team features"
        ]
    elif plan == "team_mastery":
        return []
    return ["Unknown plan type"]

async def invalidate_taalcoach_context(user_id: str):
    """
    Invalidate TaalCoach context cache

    Call this after:
    - Any user profile update
    - Subscription changes
    - Learning plan changes
    - Session completion
    """
    cache_key = f"taalcoach:context:{user_id}"
    await delete_cached(cache_key)
    logger.info(f"🗑️  [CACHE] Invalidated TaalCoach context cache: {user_id}")

async def invalidate_coach_context_smart(user_id: str, changed_types: List[str]):
    """
    PHASE 4.1: Smart cache invalidation for TaalCoach - only invalidate affected intent caches.

    This is more granular than invalidating all contexts. It invalidates ONLY the
    intent-specific caches that are affected by the data change.

    Args:
        user_id: User ID
        changed_types: List of data types that changed
                      ["challenge", "session", "learning_plan", "dna", "achievement",
                       "hearts", "feedback", "news", "notification", "sentence_analysis",
                       "flashcard", "assessment", "story_contribution", "story_achievement",
                       "learning_goal", "speaking_time", "sentence_feedback"]

    Example usage:
        # After challenge completion
        await invalidate_coach_context_smart(user_id, ["challenge", "achievement"])

        # After session completion
        await invalidate_coach_context_smart(user_id, ["session", "dna", "sentence_analysis"])

        # After learning plan session completion
        await invalidate_coach_context_smart(user_id, ["learning_plan", "session", "achievement"])

        # After flashcard creation
        await invalidate_coach_context_smart(user_id, ["flashcard"])

        # After story contribution
        await invalidate_coach_context_smart(user_id, ["story_contribution", "story_achievement"])

        # After goal update
        await invalidate_coach_context_smart(user_id, ["learning_goal"])
    """
    # Map data types → intents that need invalidation
    intent_map = {
        # EXISTING: Core data types
        "challenge": ["challenges", "progress", "general"],
        "session": ["general", "progress"],
        "learning_plan": ["learning_plan", "progress", "general"],
        "dna": ["dna"],
        "achievement": ["progress", "general"],
        "hearts": ["challenges", "general"],
        "feedback": ["general"],
        "news": ["general"],
        "notification": ["general"],
        "sentence_analysis": ["dna", "general"],

        # NEW: High-priority data types
        "flashcard": ["learning_plan", "progress", "general"],
        "assessment": ["progress", "general"],
        "story_contribution": ["progress", "general"],
        "story_achievement": ["progress", "general"],
        "learning_goal": ["learning_plan", "general"],
        "speaking_time": ["progress", "general"],
        "sentence_feedback": ["dna", "progress", "general"]
    }

    # Collect all affected intents
    intents_to_invalidate = set()
    for dtype in changed_types:
        intents_to_invalidate.update(intent_map.get(dtype, ["general"]))

    # Invalidate each intent cache
    # NOTE: CoachService uses cache key format: coach_context:{user_id}:{intent}
    for intent in intents_to_invalidate:
        cache_key = f"coach_context:{user_id}:{intent}"
        await delete_cached(cache_key)

    logger.info(f"🗑️ [CACHE] Smart invalidation for user {user_id}: intents={list(intents_to_invalidate)}, data_types={changed_types}")

# ============================================================================
# CACHE MONITORING
# ============================================================================

from fastapi import APIRouter
from redis_client import get_cache_stats

router = APIRouter(prefix="/api/cache", tags=["cache"])

@router.get("/stats")
async def cache_stats():
    """
    Get Redis cache statistics

    Returns:
        Dict with memory usage, hit rate, key count, etc.

    Example response:
    {
        "enabled": true,
        "keys": 1247,
        "memory_used_mb": 12.5,
        "memory_peak_mb": 15.2,
        "hit_rate": 89.3,
        "keyspace_hits": 45231,
        "keyspace_misses": 5432,
        "total_connections": 5421,
        "ops_per_sec": 42,
        "redis_version": "7.0.5",
        "uptime_days": 15.3
    }
    """
    stats = await get_cache_stats()
    return stats

@router.post("/clear")
async def clear_cache(pattern: str = "*"):
    """
    Clear cache by pattern (admin endpoint - should add auth)

    WARNING: Use with caution!

    Examples:
    - pattern="*" clears ALL cache
    - pattern="user:*" clears all user cache
    - pattern="learning_plan:*" clears all learning plan cache
    - pattern="taalcoach:*" clears all TaalCoach cache
    """
    await delete_pattern(pattern)
    return {"status": "success", "pattern": pattern, "message": f"Cleared cache matching pattern: {pattern}"}

# Export all functions
__all__ = [
    "get_user_cached",
    "invalidate_user_cache",
    "get_learning_plan_cached",
    "get_user_active_plan_cached",
    "invalidate_learning_plan_cache",
    "get_subscription_status_cached",
    "invalidate_subscription_cache",
    "get_daily_stats_cached",
    "invalidate_daily_stats_cache",
    "get_reference_challenges_cached",
    "invalidate_all_reference_challenges",
    "get_taalcoach_context_cached",
    "invalidate_taalcoach_context",
    "invalidate_coach_context_smart",  # PHASE 4.1: Smart cache invalidation
    "router"
]
