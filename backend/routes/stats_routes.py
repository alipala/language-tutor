"""
Statistics API Routes

Provides endpoints for gamification and statistics system:
- GET /api/stats/daily - Today's progress
- GET /api/stats/recent - 7-day rolling window
- GET /api/stats/lifetime - All-time progress
- GET /api/stats/all - Unified response (all three layers)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime

from auth import get_current_user
from models import (
    UserInDB,
    DailyStatsResponse,
    DailyStatsOverall,
    DailyStatsBreakdown,
    StreakInfo,
    RecentPerformanceResponse,
    LifetimeProgressResponse,
    UnifiedStatsResponse
)
from database import daily_stats_collection, users_collection
from services.timezone_utils import get_current_local_date
from services.stats_service import calculate_accuracy, calculate_next_milestone
from bson import ObjectId

router = APIRouter(prefix="/api/stats", tags=["statistics"])


# ============================================================================
# DAILY STATISTICS ENDPOINT
# ============================================================================

@router.get("/daily", response_model=DailyStatsResponse)
async def get_daily_stats(
    current_user: UserInDB = Depends(get_current_user),
    timezone: Optional[str] = Query(None, description="User's timezone (e.g., 'America/New_York')")
):
    """
    Get today's statistics for the current user.

    Returns:
        - Overall stats (challenges, accuracy, XP, time)
        - Breakdown by language, level, and challenge type
        - Streak information
    """
    try:
        user_id = current_user.id

        # Get user's timezone (priority: query param > user profile > UTC)
        if not timezone:
            timezone = current_user.timezone or "UTC"

        # Get today's date in user's timezone
        local_date = get_current_local_date(timezone)

        print(f"[STATS_API] 📊 Fetching daily stats for user {user_id}, date: {local_date}, timezone: {timezone}")

        # Fetch daily stats document
        daily_stat = await daily_stats_collection.find_one({
            'user_id': user_id,
            'local_date': local_date
        })

        # Get streak info from user profile
        user = await users_collection.find_one({'_id': ObjectId(user_id)})
        user_stats = user.get('stats', {}) if user else {}
        current_streak = user_stats.get('current_streak', 0)
        longest_streak = user_stats.get('longest_streak', 0)
        last_practice_date = user_stats.get('last_practice_date')

        # Check if user practiced today
        is_active_today = (daily_stat is not None) if daily_stat else False

        # If no data for today, return empty stats
        if not daily_stat:
            return DailyStatsResponse(
                success=True,
                date=local_date,
                timezone=timezone,
                overall=DailyStatsOverall(
                    total_sessions=0,
                    total_challenges=0,
                    correct=0,
                    incorrect=0,
                    accuracy=0.0,
                    total_xp=0,
                    time_minutes=0.0
                ),
                by_language={},
                by_level={},
                by_type={},
                streak=StreakInfo(
                    current=current_streak,
                    longest=longest_streak,
                    is_active_today=is_active_today,
                    next_milestone=calculate_next_milestone(current_streak)
                ),
                metadata={
                    'last_updated': None,
                    'has_more_data': False
                }
            )

        # Extract overall stats
        overall = DailyStatsOverall(
            total_sessions=daily_stat.get('total_sessions', 0),
            total_challenges=daily_stat.get('total_challenges', 0),
            correct=daily_stat.get('correct_challenges', 0),
            incorrect=daily_stat.get('incorrect_challenges', 0),
            accuracy=daily_stat.get('accuracy_percent', 0.0),
            total_xp=daily_stat.get('total_xp', 0),
            time_minutes=round(daily_stat.get('total_time_seconds', 0) / 60, 1)
        )

        # Convert breakdown dictionaries to response models
        by_language = {}
        for lang, lang_data in daily_stat.get('by_language', {}).items():
            by_language[lang] = DailyStatsBreakdown(
                challenges=lang_data.get('challenges', 0),
                correct=lang_data.get('correct', 0),
                incorrect=lang_data.get('incorrect', 0),
                accuracy=lang_data.get('accuracy', 0.0),
                xp=lang_data.get('xp', 0)
            )

        by_level = {}
        for level, level_data in daily_stat.get('by_level', {}).items():
            by_level[level] = DailyStatsBreakdown(
                challenges=level_data.get('challenges', 0),
                correct=level_data.get('correct', 0),
                incorrect=level_data.get('incorrect', 0),
                accuracy=level_data.get('accuracy', 0.0),
                xp=0  # XP not tracked per level currently
            )

        by_type = {}
        for ctype, type_data in daily_stat.get('by_type', {}).items():
            by_type[ctype] = DailyStatsBreakdown(
                challenges=type_data.get('challenges', 0),
                correct=type_data.get('correct', 0),
                incorrect=type_data.get('incorrect', 0),
                accuracy=type_data.get('accuracy', 0.0),
                xp=type_data.get('xp', 0)
            )

        # Build response
        response = DailyStatsResponse(
            success=True,
            date=local_date,
            timezone=timezone,
            overall=overall,
            by_language=by_language,
            by_level=by_level,
            by_type=by_type,
            streak=StreakInfo(
                current=current_streak,
                longest=longest_streak,
                is_active_today=is_active_today,
                next_milestone=calculate_next_milestone(current_streak)
            ),
            metadata={
                'last_updated': daily_stat.get('updated_at'),
                'has_more_data': True
            }
        )

        print(f"[STATS_API] ✅ Daily stats retrieved: {overall.total_challenges} challenges, {overall.accuracy}% accuracy")

        return response

    except Exception as e:
        print(f"[STATS_API] ❌ Error getting daily stats: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily stats: {str(e)}"
        )


# ============================================================================
# PLACEHOLDER ENDPOINTS (TO BE IMPLEMENTED IN LATER PHASES)
# ============================================================================

@router.get("/recent", response_model=RecentPerformanceResponse)
async def get_recent_performance_endpoint(
    current_user: UserInDB = Depends(get_current_user),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    timezone: Optional[str] = Query(None)
):
    """
    Get recent performance statistics (rolling window).

    Returns:
        - Summary metrics (total challenges, average accuracy, XP, time)
        - Insights (most/least practiced areas, improvement trend)
        - Daily breakdown for charting
        - Language and type distributions
        - Level-wise performance rankings
    """
    try:
        user_id = current_user.id

        # Get user's timezone
        if not timezone:
            timezone = current_user.timezone or "UTC"

        print(f"[STATS_API] 📊 Fetching {days}-day performance for user {user_id}, timezone: {timezone}")

        # Import the service
        from services.recent_performance_service import get_recent_performance

        # Get recent performance (with caching)
        perf_data = await get_recent_performance(user_id, days, timezone)

        # Format window dates
        window_start = perf_data['window_start']
        window_end = perf_data['window_end']

        # Build response
        from models import (
            RecentPerformanceSummary,
            RecentPerformanceInsights,
            DailyBreakdownItem,
            LanguageDistribution
        )

        summary = RecentPerformanceSummary(
            total_sessions=perf_data['total_sessions'],
            total_challenges=perf_data['total_challenges'],
            average_accuracy=perf_data['average_accuracy'],
            total_xp=perf_data['total_xp'],
            total_time_minutes=perf_data.get('total_time_minutes', 0.0),
            active_days=len([d for d in perf_data['daily_breakdown'] if d['challenges'] > 0])
        )

        insights = RecentPerformanceInsights(
            most_practiced_type=perf_data.get('most_practiced_type'),
            most_practiced_language=perf_data.get('most_practiced_language'),
            weakest_level=perf_data.get('weakest_level'),
            weakest_level_accuracy=perf_data.get('weakest_level_accuracy', 0.0),
            strongest_level=perf_data.get('strongest_level'),
            strongest_level_accuracy=perf_data.get('strongest_level_accuracy', 0.0),
            improvement_trend=perf_data.get('improvement_trend', 'stable'),
            accuracy_change_percent=perf_data.get('accuracy_change_percent', 0.0)
        )

        daily_breakdown = [
            DailyBreakdownItem(**item)
            for item in perf_data['daily_breakdown']
        ]

        language_distribution = {
            lang: LanguageDistribution(**data)
            for lang, data in perf_data['language_distribution'].items()
        }

        type_distribution = {
            ctype: LanguageDistribution(**data)
            for ctype, data in perf_data['type_distribution'].items()
        }

        response = RecentPerformanceResponse(
            success=True,
            window={
                'start': window_start.strftime('%Y-%m-%d'),
                'end': window_end.strftime('%Y-%m-%d'),
                'days': days
            },
            summary=summary,
            insights=insights,
            daily_breakdown=daily_breakdown,
            language_distribution=language_distribution,
            type_distribution=type_distribution,
            level_performance=perf_data['level_performance'],
            metadata={
                'calculated_at': perf_data['calculated_at'],
                'cached_until': perf_data['expires_at']
            }
        )

        print(f"[STATS_API] ✅ Recent performance retrieved: {summary.total_challenges} challenges, {summary.average_accuracy:.1f}% avg accuracy")

        return response

    except Exception as e:
        print(f"[STATS_API] ❌ Error getting recent performance: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent performance: {str(e)}"
        )


@router.get("/lifetime", response_model=LifetimeProgressResponse)
async def get_lifetime_progress_endpoint(
    current_user: UserInDB = Depends(get_current_user),
    language: Optional[str] = Query(None, description="Filter by language"),
    include_achievements: bool = Query(False, description="Include achievement history")
):
    """
    Get lifetime progress and mastery statistics.

    Returns:
        - Summary metrics (total challenges, XP, time, streaks)
        - Language-specific progress with mastery percentages
        - CEFR level mastery with star ratings
        - Challenge type mastery with rankings
        - Learning path recommendations
        - Optional: Achievement history
        - Milestone tracking
    """
    try:
        user_id = current_user.id

        print(f"[STATS_API] 📊 Fetching lifetime progress for user {user_id}")

        # Import the service
        from services.lifetime_progress_service import get_lifetime_progress

        # Get lifetime progress
        progress_data = await get_lifetime_progress(
            user_id,
            language_filter=language,
            include_achievements=include_achievements
        )

        # Build response
        from models import LifetimeSummary

        summary = LifetimeSummary(**progress_data['summary'])

        response = LifetimeProgressResponse(
            success=True,
            summary=summary,
            language_progress=progress_data['language_progress'],
            level_mastery=progress_data['level_mastery'],
            challenge_type_mastery=progress_data['challenge_type_mastery'],
            learning_path=progress_data['learning_path'],
            achievements=progress_data.get('achievements'),
            milestones=progress_data.get('milestones'),
            metadata={
                'calculated_at': datetime.utcnow(),
                'data_since': summary.member_since
            }
        )

        print(f"[STATS_API] ✅ Lifetime progress retrieved: {summary.total_challenges} challenges, {summary.current_streak} day streak")

        return response

    except Exception as e:
        print(f"[STATS_API] ❌ Error getting lifetime progress: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get lifetime progress: {str(e)}"
        )


@router.get("/all", response_model=UnifiedStatsResponse)
async def get_all_stats(
    current_user: UserInDB = Depends(get_current_user),
    timezone: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30, description="Days for recent performance"),
    include_achievements: bool = Query(False, description="Include achievements in lifetime stats")
):
    """
    Get unified stats response (daily + recent + lifetime).

    This endpoint is optimized for mobile apps to fetch all stats
    in a single request, reducing network overhead.

    Returns:
        - Daily stats (today's progress)
        - Recent performance (7-day rolling window)
        - Lifetime progress (cumulative statistics)
    """
    try:
        user_id = current_user.id

        # Get user's timezone
        if not timezone:
            timezone = current_user.timezone or "UTC"

        print(f"[STATS_API] 📊 Fetching unified stats for user {user_id}, timezone: {timezone}")

        # Fetch all three layers in parallel (for performance)
        import asyncio
        from services.recent_performance_service import get_recent_performance
        from services.lifetime_progress_service import get_lifetime_progress

        # Execute all three queries concurrently
        daily_task = get_daily_stats(current_user=current_user, timezone=timezone)
        recent_task = get_recent_performance(user_id, days, timezone)
        lifetime_task = get_lifetime_progress(user_id, include_achievements=include_achievements)

        # Wait for all to complete
        daily_response, recent_data, lifetime_data = await asyncio.gather(
            daily_task,
            recent_task,
            lifetime_task
        )

        # Build recent response
        from models import (
            RecentPerformanceSummary,
            RecentPerformanceInsights,
            DailyBreakdownItem,
            LanguageDistribution,
            LifetimeSummary
        )

        recent_summary = RecentPerformanceSummary(
            total_sessions=recent_data['total_sessions'],
            total_challenges=recent_data['total_challenges'],
            average_accuracy=recent_data['average_accuracy'],
            total_xp=recent_data['total_xp'],
            total_time_minutes=recent_data.get('total_time_minutes', 0.0),
            active_days=len([d for d in recent_data['daily_breakdown'] if d['challenges'] > 0])
        )

        recent_insights = RecentPerformanceInsights(
            most_practiced_type=recent_data.get('most_practiced_type'),
            most_practiced_language=recent_data.get('most_practiced_language'),
            weakest_level=recent_data.get('weakest_level'),
            weakest_level_accuracy=recent_data.get('weakest_level_accuracy', 0.0),
            strongest_level=recent_data.get('strongest_level'),
            strongest_level_accuracy=recent_data.get('strongest_level_accuracy', 0.0),
            improvement_trend=recent_data.get('improvement_trend', 'stable'),
            accuracy_change_percent=recent_data.get('accuracy_change_percent', 0.0)
        )

        recent_response = RecentPerformanceResponse(
            success=True,
            window={
                'start': recent_data['window_start'].strftime('%Y-%m-%d'),
                'end': recent_data['window_end'].strftime('%Y-%m-%d'),
                'days': days
            },
            summary=recent_summary,
            insights=recent_insights,
            daily_breakdown=[DailyBreakdownItem(**item) for item in recent_data['daily_breakdown']],
            language_distribution={lang: LanguageDistribution(**data) for lang, data in recent_data['language_distribution'].items()},
            type_distribution={ctype: LanguageDistribution(**data) for ctype, data in recent_data['type_distribution'].items()},
            level_performance=recent_data['level_performance'],
            metadata={
                'calculated_at': recent_data['calculated_at'],
                'cached_until': recent_data['expires_at']
            }
        )

        # Build lifetime response
        lifetime_summary = LifetimeSummary(**lifetime_data['summary'])

        lifetime_response = LifetimeProgressResponse(
            success=True,
            summary=lifetime_summary,
            language_progress=lifetime_data['language_progress'],
            level_mastery=lifetime_data['level_mastery'],
            challenge_type_mastery=lifetime_data['challenge_type_mastery'],
            learning_path=lifetime_data['learning_path'],
            achievements=lifetime_data.get('achievements'),
            milestones=lifetime_data.get('milestones'),
            metadata={
                'calculated_at': datetime.utcnow(),
                'data_since': lifetime_summary.member_since
            }
        )

        # Build unified response
        unified_response = UnifiedStatsResponse(
            success=True,
            daily=daily_response,
            recent=recent_response,
            lifetime=lifetime_response
        )

        print(f"[STATS_API] ✅ Unified stats retrieved successfully")

        return unified_response

    except Exception as e:
        print(f"[STATS_API] ❌ Error getting unified stats: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get unified stats: {str(e)}"
        )


# ============================================================================
# CALENDAR ENDPOINT — practiced days for any given month
# ============================================================================

@router.get("/calendar")
async def get_calendar_month(
    year:  int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user = Depends(get_current_user),
):
    """
    Return practiced days for a given month from daily_stats.
    Each item: { date, sessions, challenges, xp, time_minutes, is_streak_day }
    """
    import calendar as cal_mod

    user_id = str(current_user.id)

    # Build date range strings: '2026-04-01' … '2026-04-30'
    last_day   = cal_mod.monthrange(year, month)[1]
    date_start = f"{year}-{month:02d}-01"
    date_end   = f"{year}-{month:02d}-{last_day:02d}"

    docs = await daily_stats_collection.find(
        {
            "user_id":    user_id,
            "local_date": {"$gte": date_start, "$lte": date_end},
        },
        {
            "local_date":        1,
            "total_sessions":    1,
            "total_challenges":  1,
            "total_xp":          1,
            "total_time_seconds":1,
            "is_streak_day":     1,
        }
    ).to_list(31)

    days = [
        {
            "date":         d["local_date"],
            "sessions":     d.get("total_sessions", 0),
            "challenges":   d.get("total_challenges", 0),
            "xp":           d.get("total_xp", 0),
            "time_minutes": round(d.get("total_time_seconds", 0) / 60, 1),
            "is_streak_day": d.get("is_streak_day", False),
        }
        for d in docs
    ]

    print(f"[STATS_API] 📅 Calendar {year}-{month:02d}: {len(days)} practiced days for user {user_id}")
    return {"year": year, "month": month, "days": days}
