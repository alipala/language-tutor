"""
Recent Performance Service

Handles calculation of rolling window statistics (7-day recent performance).
Implements caching strategy with MongoDB TTL collection.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId

from database import (
    challenge_sessions_collection,
    daily_stats_collection,
    recent_performance_collection
)
from services.timezone_utils import get_dates_in_range
from services.stats_service import calculate_accuracy


# ============================================================================
# RECENT PERFORMANCE CALCULATION
# ============================================================================

async def calculate_recent_performance(
    user_id: str,
    days: int = 7,
    timezone_str: str = "UTC"
) -> Dict[str, Any]:
    """
    Calculate recent performance statistics for a user.

    This implementation uses daily_stats collection for efficiency
    instead of aggregating from raw challenge_sessions.

    Args:
        user_id: User ID
        days: Number of days to look back (default: 7)
        timezone_str: User's timezone

    Returns:
        Dictionary with recent performance metrics
    """
    try:
        print(f"[RECENT_PERF] 📊 Calculating {days}-day performance for user {user_id}")

        # Calculate date range
        from services.timezone_utils import get_current_local_date
        end_date = get_current_local_date(timezone_str)

        # Parse end_date and calculate start_date
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=days - 1)
        start_date = start_dt.strftime("%Y-%m-%d")

        print(f"[RECENT_PERF] Date range: {start_date} to {end_date}")

        # Get all daily stats in range
        cursor = daily_stats_collection.find({
            'user_id': user_id,
            'local_date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }).sort('local_date', 1)

        daily_stats_list = await cursor.to_list(length=None)

        if not daily_stats_list:
            print(f"[RECENT_PERF] No data found for user {user_id} in date range")
            return get_empty_recent_performance(days, start_date, end_date)

        # Aggregate summary metrics
        summary = calculate_summary_metrics(daily_stats_list)

        # Calculate insights
        insights = calculate_insights(daily_stats_list)

        # Build daily breakdown
        daily_breakdown = build_daily_breakdown(daily_stats_list, start_date, end_date)

        # Calculate distributions
        language_dist = calculate_language_distribution(daily_stats_list)
        type_dist = calculate_type_distribution(daily_stats_list)
        level_perf = calculate_level_performance(daily_stats_list)

        # Build result
        result = {
            'user_id': user_id,
            'window_start': datetime.strptime(start_date, "%Y-%m-%d"),
            'window_end': datetime.strptime(end_date, "%Y-%m-%d"),
            'total_sessions': summary['total_sessions'],
            'total_challenges': summary['total_challenges'],
            'average_accuracy': summary['average_accuracy'],
            'total_xp': summary['total_xp'],
            'most_practiced_type': insights.get('most_practiced_type'),
            'most_practiced_language': insights.get('most_practiced_language'),
            'weakest_level': insights.get('weakest_level'),
            'strongest_level': insights.get('strongest_level'),
            'daily_breakdown': daily_breakdown,
            'language_distribution': language_dist,
            'type_distribution': type_dist,
            'level_performance': level_perf,
            'calculated_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=1)
        }

        print(f"[RECENT_PERF] ✅ Calculated: {summary['total_challenges']} challenges, {summary['average_accuracy']:.1f}% avg accuracy")

        return result

    except Exception as e:
        print(f"[RECENT_PERF] ❌ Error calculating recent performance: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return get_empty_recent_performance(days, None, None)


def calculate_summary_metrics(daily_stats_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary metrics from daily stats."""
    total_sessions = sum(ds.get('total_sessions', 0) for ds in daily_stats_list)
    total_challenges = sum(ds.get('total_challenges', 0) for ds in daily_stats_list)
    total_correct = sum(ds.get('correct_challenges', 0) for ds in daily_stats_list)
    total_xp = sum(ds.get('total_xp', 0) for ds in daily_stats_list)
    total_time = sum(ds.get('total_time_seconds', 0) for ds in daily_stats_list)

    average_accuracy = calculate_accuracy(total_correct, total_challenges)
    active_days = len([ds for ds in daily_stats_list if ds.get('total_challenges', 0) > 0])

    return {
        'total_sessions': total_sessions,
        'total_challenges': total_challenges,
        'average_accuracy': average_accuracy,
        'total_xp': total_xp,
        'total_time_minutes': round(total_time / 60, 1),
        'active_days': active_days
    }


def calculate_insights(daily_stats_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate insights from daily stats."""
    insights = {}

    # Aggregate by challenge type
    type_totals = {}
    for ds in daily_stats_list:
        by_type = ds.get('by_type', {})
        for ctype, type_data in by_type.items():
            if ctype not in type_totals:
                type_totals[ctype] = 0
            type_totals[ctype] += type_data.get('challenges', 0)

    # Most practiced type
    if type_totals:
        most_practiced_type = max(type_totals.items(), key=lambda x: x[1])
        insights['most_practiced_type'] = most_practiced_type[0]

    # Aggregate by language
    lang_totals = {}
    for ds in daily_stats_list:
        by_lang = ds.get('by_language', {})
        for lang, lang_data in by_lang.items():
            if lang not in lang_totals:
                lang_totals[lang] = 0
            lang_totals[lang] += lang_data.get('challenges', 0)

    # Most practiced language
    if lang_totals:
        most_practiced_lang = max(lang_totals.items(), key=lambda x: x[1])
        insights['most_practiced_language'] = most_practiced_lang[0]

    # Aggregate by level for accuracy comparison
    level_stats = {}
    for ds in daily_stats_list:
        by_level = ds.get('by_level', {})
        for level, level_data in by_level.items():
            if level not in level_stats:
                level_stats[level] = {'correct': 0, 'total': 0}
            level_stats[level]['correct'] += level_data.get('correct', 0)
            level_stats[level]['total'] += level_data.get('challenges', 0)

    # Calculate accuracy per level
    level_accuracies = {}
    for level, stats in level_stats.items():
        level_accuracies[level] = calculate_accuracy(stats['correct'], stats['total'])

    # Weakest and strongest levels
    if level_accuracies:
        weakest_level = min(level_accuracies.items(), key=lambda x: x[1])
        strongest_level = max(level_accuracies.items(), key=lambda x: x[1])
        insights['weakest_level'] = weakest_level[0]
        insights['weakest_level_accuracy'] = weakest_level[1]
        insights['strongest_level'] = strongest_level[0]
        insights['strongest_level_accuracy'] = strongest_level[1]

    # Improvement trend (compare first half vs second half)
    if len(daily_stats_list) >= 2:
        mid_point = len(daily_stats_list) // 2
        first_half = daily_stats_list[:mid_point]
        second_half = daily_stats_list[mid_point:]

        first_half_correct = sum(ds.get('correct_challenges', 0) for ds in first_half)
        first_half_total = sum(ds.get('total_challenges', 0) for ds in first_half)
        second_half_correct = sum(ds.get('correct_challenges', 0) for ds in second_half)
        second_half_total = sum(ds.get('total_challenges', 0) for ds in second_half)

        first_acc = calculate_accuracy(first_half_correct, first_half_total)
        second_acc = calculate_accuracy(second_half_correct, second_half_total)

        accuracy_change = second_acc - first_acc

        if accuracy_change > 2:
            insights['improvement_trend'] = 'positive'
        elif accuracy_change < -2:
            insights['improvement_trend'] = 'negative'
        else:
            insights['improvement_trend'] = 'stable'

        insights['accuracy_change_percent'] = round(accuracy_change, 2)

    return insights


def build_daily_breakdown(
    daily_stats_list: List[Dict[str, Any]],
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Build daily breakdown with zero-filled gaps."""
    # Create a map of existing daily stats
    daily_map = {ds['local_date']: ds for ds in daily_stats_list}

    # Generate all dates in range
    all_dates = get_dates_in_range(start_date, end_date)

    daily_breakdown = []
    for date_str in all_dates:
        if date_str in daily_map:
            ds = daily_map[date_str]
            daily_breakdown.append({
                'date': date_str,
                'challenges': ds.get('total_challenges', 0),
                'accuracy': ds.get('accuracy_percent', 0.0),
                'xp': ds.get('total_xp', 0),
                'time_minutes': round(ds.get('total_time_seconds', 0) / 60, 1),
                'sessions': ds.get('total_sessions', 0)
            })
        else:
            # Fill gaps with zeros
            daily_breakdown.append({
                'date': date_str,
                'challenges': 0,
                'accuracy': 0.0,
                'xp': 0,
                'time_minutes': 0.0,
                'sessions': 0
            })

    return daily_breakdown


def calculate_language_distribution(daily_stats_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate language distribution from daily stats."""
    lang_totals = {}

    for ds in daily_stats_list:
        by_lang = ds.get('by_language', {})
        for lang, lang_data in by_lang.items():
            if lang not in lang_totals:
                lang_totals[lang] = {'challenges': 0, 'correct': 0}
            lang_totals[lang]['challenges'] += lang_data.get('challenges', 0)
            lang_totals[lang]['correct'] += lang_data.get('correct', 0)

    # Calculate percentages and accuracy
    total_all_challenges = sum(d['challenges'] for d in lang_totals.values())

    distribution = {}
    for lang, data in lang_totals.items():
        challenges = data['challenges']
        correct = data['correct']
        percentage = (challenges / total_all_challenges * 100) if total_all_challenges > 0 else 0
        accuracy = calculate_accuracy(correct, challenges)

        distribution[lang] = {
            'challenges': challenges,
            'percentage': round(percentage, 1),
            'accuracy': accuracy
        }

    return distribution


def calculate_type_distribution(daily_stats_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate challenge type distribution from daily stats."""
    type_totals = {}

    for ds in daily_stats_list:
        by_type = ds.get('by_type', {})
        for ctype, type_data in by_type.items():
            if ctype not in type_totals:
                type_totals[ctype] = {'challenges': 0, 'correct': 0}
            type_totals[ctype]['challenges'] += type_data.get('challenges', 0)
            type_totals[ctype]['correct'] += type_data.get('correct', 0)

    # Calculate percentages and accuracy
    total_all_challenges = sum(d['challenges'] for d in type_totals.values())

    distribution = {}
    for ctype, data in type_totals.items():
        challenges = data['challenges']
        correct = data['correct']
        percentage = (challenges / total_all_challenges * 100) if total_all_challenges > 0 else 0
        accuracy = calculate_accuracy(correct, challenges)

        distribution[ctype] = {
            'challenges': challenges,
            'percentage': round(percentage, 1),
            'accuracy': accuracy
        }

    return distribution


def calculate_level_performance(daily_stats_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate level-wise performance from daily stats."""
    level_stats = {}

    for ds in daily_stats_list:
        by_level = ds.get('by_level', {})
        for level, level_data in by_level.items():
            if level not in level_stats:
                level_stats[level] = {'challenges': 0, 'correct': 0}
            level_stats[level]['challenges'] += level_data.get('challenges', 0)
            level_stats[level]['correct'] += level_data.get('correct', 0)

    # Calculate accuracy and rank
    performance = {}
    for level, data in level_stats.items():
        challenges = data['challenges']
        correct = data['correct']
        accuracy = calculate_accuracy(correct, challenges)

        # Determine rank based on accuracy
        if accuracy >= 90:
            rank = 'excellent'
        elif accuracy >= 80:
            rank = 'good'
        elif accuracy >= 70:
            rank = 'fair'
        else:
            rank = 'needs_work'

        performance[level] = {
            'challenges': challenges,
            'accuracy': accuracy,
            'rank': rank
        }

    return performance


def get_empty_recent_performance(days: int, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
    """Return empty recent performance structure."""
    return {
        'user_id': None,
        'window_start': datetime.utcnow() - timedelta(days=days),
        'window_end': datetime.utcnow(),
        'total_sessions': 0,
        'total_challenges': 0,
        'average_accuracy': 0.0,
        'total_xp': 0,
        'most_practiced_type': None,
        'most_practiced_language': None,
        'weakest_level': None,
        'strongest_level': None,
        'daily_breakdown': [],
        'language_distribution': {},
        'type_distribution': {},
        'level_performance': {},
        'calculated_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(hours=1)
    }


# ============================================================================
# CACHING
# ============================================================================

async def get_recent_performance(
    user_id: str,
    days: int = 7,
    timezone_str: str = "UTC"
) -> Dict[str, Any]:
    """
    Get recent performance with caching.

    Checks cache first, calculates if needed, and stores in cache.

    Args:
        user_id: User ID
        days: Number of days to look back
        timezone_str: User's timezone

    Returns:
        Recent performance data
    """
    try:
        # Check cache
        cached = await recent_performance_collection.find_one({
            'user_id': user_id,
            'expires_at': {'$gt': datetime.utcnow()}
        })

        if cached:
            print(f"[RECENT_PERF] ⚡ Cache hit for user {user_id}")
            return cached

        # Cache miss - calculate
        print(f"[RECENT_PERF] 🔄 Cache miss for user {user_id}, calculating...")
        result = await calculate_recent_performance(user_id, days, timezone_str)

        # Store in cache
        await recent_performance_collection.update_one(
            {'user_id': user_id},
            {'$set': result},
            upsert=True
        )

        print(f"[RECENT_PERF] 💾 Cached result for user {user_id}")

        return result

    except Exception as e:
        print(f"[RECENT_PERF] ❌ Error getting recent performance: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return get_empty_recent_performance(days, None, None)
