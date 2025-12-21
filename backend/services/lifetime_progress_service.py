"""
Lifetime Progress Service

Handles calculation of lifetime cumulative statistics and mastery levels.
Reads from denormalized user.stats.lifetime field for ultra-fast queries.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId

from database import users_collection
from services.stats_service import calculate_accuracy, get_cefr_level_rank


# ============================================================================
# LIFETIME PROGRESS CALCULATION
# ============================================================================

async def get_lifetime_progress(
    user_id: str,
    language_filter: Optional[str] = None,
    include_achievements: bool = False
) -> Dict[str, Any]:
    """
    Get lifetime progress statistics for a user.

    Reads from denormalized user.stats.lifetime field.

    Args:
        user_id: User ID
        language_filter: Optional language filter
        include_achievements: Whether to include achievement history

    Returns:
        Dictionary with lifetime progress data
    """
    try:
        print(f"[LIFETIME_PROG] 📊 Fetching lifetime progress for user {user_id}")

        # Fetch user document
        user = await users_collection.find_one({'_id': ObjectId(user_id)})

        if not user:
            print(f"[LIFETIME_PROG] ❌ User {user_id} not found")
            return get_empty_lifetime_progress()

        # Extract stats
        stats = user.get('stats', {})
        lifetime = stats.get('lifetime', {})

        # Calculate summary
        summary = calculate_lifetime_summary(user, stats, lifetime)

        # Calculate language progress
        language_progress = calculate_language_progress(
            lifetime.get('by_language', {}),
            language_filter
        )

        # Calculate level mastery
        level_mastery = calculate_level_mastery(lifetime.get('by_level', {}))

        # Calculate challenge type mastery
        type_mastery = calculate_challenge_type_mastery(lifetime.get('by_type', {}))

        # Calculate learning path suggestions
        learning_path = calculate_learning_path(language_progress, level_mastery)

        # Optional: Include achievements
        achievements_data = None
        if include_achievements:
            achievements_data = await get_achievements_data(user_id)

        # Calculate milestones
        milestones = calculate_milestones(summary, language_progress)

        result = {
            'user_id': user_id,
            'summary': summary,
            'language_progress': language_progress,
            'level_mastery': level_mastery,
            'challenge_type_mastery': type_mastery,
            'learning_path': learning_path,
            'achievements': achievements_data,
            'milestones': milestones
        }

        print(f"[LIFETIME_PROG] ✅ Retrieved: {summary['total_challenges']} total challenges, {summary['current_streak']} day streak")

        return result

    except Exception as e:
        print(f"[LIFETIME_PROG] ❌ Error getting lifetime progress: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return get_empty_lifetime_progress()


def calculate_lifetime_summary(user: Dict[str, Any], stats: Dict[str, Any], lifetime: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate lifetime summary metrics."""
    total_challenges = lifetime.get('total_challenges', 0)
    total_sessions = lifetime.get('total_sessions', 0)
    total_xp = lifetime.get('total_xp', 0)
    total_time_minutes = lifetime.get('total_time_minutes', 0.0)

    created_at = user.get('created_at', datetime.utcnow())
    member_since = created_at.strftime('%Y-%m-%d')

    current_streak = stats.get('current_streak', 0)
    longest_streak = stats.get('longest_streak', 0)

    return {
        'total_challenges': total_challenges,
        'total_sessions': total_sessions,
        'total_xp': total_xp,
        'total_time_hours': round(total_time_minutes / 60, 1),
        'member_since': member_since,
        'longest_streak': longest_streak,
        'current_streak': current_streak
    }


def calculate_language_progress(
    by_language: Dict[str, Any],
    language_filter: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Calculate language-specific progress."""
    progress = {}

    for lang, lang_data in by_language.items():
        # Apply filter if specified
        if language_filter and lang != language_filter:
            continue

        total_challenges = lang_data.get('total_challenges', 0)
        total_xp = lang_data.get('total_xp', 0)
        highest_level = lang_data.get('highest_level', 'A1')
        started_at = lang_data.get('started_at', datetime.utcnow())
        last_practiced = lang_data.get('last_practiced', datetime.utcnow())

        # Calculate time invested (estimate based on challenges)
        time_hours = round(total_challenges * 0.25 / 60, 1)  # ~15 sec per challenge

        # Calculate mastery percentage (based on highest level achieved)
        level_rank = get_cefr_level_rank(highest_level)
        mastery_percent = round((level_rank / 6) * 100, 1)

        # Calculate level breakdown
        level_breakdown = {}
        # This would ideally come from lifetime.by_level filtered by language
        # For now, we'll provide a simplified version
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            if get_cefr_level_rank(level) <= level_rank:
                level_breakdown[level] = {
                    'completed': 100,  # Simplified
                    'accuracy': 85.0,  # Placeholder
                    'mastered': get_cefr_level_rank(level) < level_rank
                }

        progress[lang] = {
            'total_challenges': total_challenges,
            'highest_level': highest_level,
            'total_xp': total_xp,
            'started_at': started_at,
            'last_practiced': last_practiced,
            'time_hours': time_hours,
            'mastery_percent': mastery_percent,
            'level_breakdown': level_breakdown
        }

    return progress


def calculate_level_mastery(by_level: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Calculate mastery by CEFR level."""
    mastery = {}

    for level, level_data in by_level.items():
        total_challenges = level_data.get('total_challenges', 0)
        correct = level_data.get('correct', 0)
        incorrect = level_data.get('incorrect', 0)

        accuracy = calculate_accuracy(correct, total_challenges)

        # Calculate mastery stars (1-5)
        if total_challenges >= 200 and accuracy >= 90:
            mastery_stars = 5
        elif total_challenges >= 150 and accuracy >= 85:
            mastery_stars = 4
        elif total_challenges >= 100 and accuracy >= 80:
            mastery_stars = 3
        elif total_challenges >= 50 and accuracy >= 75:
            mastery_stars = 2
        elif total_challenges > 0:
            mastery_stars = 1
        else:
            mastery_stars = 0

        mastery[level] = {
            'total_challenges': total_challenges,
            'accuracy': accuracy,
            'mastery_stars': mastery_stars,
            'languages': []  # Would need cross-reference to know which languages
        }

    return mastery


def calculate_challenge_type_mastery(by_type: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Calculate mastery by challenge type."""
    mastery = {}

    for ctype, type_data in by_type.items():
        total_challenges = type_data.get('total_challenges', 0)
        correct = type_data.get('correct', 0)

        accuracy = calculate_accuracy(correct, total_challenges)

        # Calculate mastery level (1-5)
        if total_challenges >= 200 and accuracy >= 90:
            mastery_level = 5
            rank = 'master'
        elif total_challenges >= 150 and accuracy >= 85:
            mastery_level = 4
            rank = 'expert'
        elif total_challenges >= 100 and accuracy >= 80:
            mastery_level = 3
            rank = 'advanced'
        elif total_challenges >= 50 and accuracy >= 75:
            mastery_level = 2
            rank = 'intermediate'
        elif total_challenges > 0:
            mastery_level = 1
            rank = 'beginner'
        else:
            mastery_level = 0
            rank = 'novice'

        # Determine if this is a favorite type (most practiced)
        favorite = False  # Will be set by comparing across types

        mastery[ctype] = {
            'total_challenges': total_challenges,
            'accuracy': accuracy,
            'mastery_level': mastery_level,
            'rank': rank,
            'favorite': favorite
        }

    # Mark the most practiced type as favorite
    if mastery:
        max_challenges_type = max(mastery.items(), key=lambda x: x[1]['total_challenges'])
        mastery[max_challenges_type[0]]['favorite'] = True

    return mastery


def calculate_learning_path(
    language_progress: Dict[str, Dict[str, Any]],
    level_mastery: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate learning path recommendations."""
    path = {
        'current_focus': None,
        'suggested_next': None,
        'weak_areas': [],
        'ready_for_next_level': []
    }

    if not language_progress:
        return path

    # Find current focus (most recently practiced language at highest level)
    most_recent = max(
        language_progress.items(),
        key=lambda x: x[1].get('last_practiced', datetime.min)
    )
    current_lang = most_recent[0]
    current_level = most_recent[1]['highest_level']
    path['current_focus'] = f"{current_lang} {current_level}"

    # Suggest next level if mastery is high
    current_level_rank = get_cefr_level_rank(current_level)
    if current_level_rank < 6:  # Not at C2 yet
        next_level_map = {
            'A1': 'A2',
            'A2': 'B1',
            'B1': 'B2',
            'B2': 'C1',
            'C1': 'C2'
        }
        next_level = next_level_map.get(current_level)
        if next_level:
            path['suggested_next'] = f"{current_lang} {next_level}"

    # Identify weak areas (low accuracy levels)
    for level, level_data in level_mastery.items():
        accuracy = level_data['accuracy']
        if accuracy < 75 and level_data['total_challenges'] > 0:
            # Find which language(s) this level is associated with
            path['weak_areas'].append(f"{current_lang} {level}")

    # Identify languages ready for next level (high mastery)
    for lang, lang_data in language_progress.items():
        mastery = lang_data.get('mastery_percent', 0)
        if mastery >= 80:
            current_level = lang_data.get('highest_level', 'A1')
            if get_cefr_level_rank(current_level) < 6:
                path['ready_for_next_level'].append(lang)

    return path


async def get_achievements_data(user_id: str) -> Dict[str, Any]:
    """Get achievement data for the user."""
    from database import user_achievements_collection

    try:
        cursor = user_achievements_collection.find({'user_id': user_id})
        achievements_list = await cursor.to_list(length=None)

        total_unlocked = len(achievements_list)
        total_xp_from_achievements = 0  # Would need to calculate from achievement definitions

        # Get recent achievements (last 5)
        recent_achievements = sorted(
            achievements_list,
            key=lambda x: x.get('unlocked_at', datetime.min),
            reverse=True
        )[:5]

        recent_formatted = []
        for ach in recent_achievements:
            recent_formatted.append({
                'id': ach.get('achievement_id'),
                'title': ach.get('achievement_id', '').replace('_', ' ').title(),
                'unlocked_at': ach.get('unlocked_at'),
                'xp_bonus': 100  # Placeholder
            })

        return {
            'total_unlocked': total_unlocked,
            'total_xp_from_achievements': total_xp_from_achievements,
            'recent_achievements': recent_formatted
        }

    except Exception as e:
        print(f"[LIFETIME_PROG] ❌ Error getting achievements: {str(e)}")
        return {
            'total_unlocked': 0,
            'total_xp_from_achievements': 0,
            'recent_achievements': []
        }


def calculate_milestones(summary: Dict[str, Any], language_progress: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate progress toward next milestones."""
    total_challenges = summary['total_challenges']

    # Next challenge milestone
    challenge_milestones = [100, 250, 500, 1000, 2000, 5000]
    next_challenge_milestone = None
    for milestone in challenge_milestones:
        if total_challenges < milestone:
            next_challenge_milestone = milestone
            break

    milestones = {}

    if next_challenge_milestone:
        progress_percent = (total_challenges / next_challenge_milestone) * 100
        milestones['next_milestone'] = {
            'type': 'total_challenges',
            'current': total_challenges,
            'target': next_challenge_milestone,
            'progress_percent': round(progress_percent, 1),
            'reward_xp': next_challenge_milestone  # 1 XP per challenge milestone
        }

    # Language mastery milestones
    upcoming = []
    for lang, lang_data in language_progress.items():
        mastery = lang_data.get('mastery_percent', 0)
        if mastery < 100:
            upcoming.append({
                'type': f'{lang}_mastery',
                'current': mastery,
                'target': 100.0,
                'progress_percent': mastery
            })

    milestones['upcoming'] = upcoming[:3]  # Top 3

    return milestones


def get_empty_lifetime_progress() -> Dict[str, Any]:
    """Return empty lifetime progress structure."""
    return {
        'user_id': None,
        'summary': {
            'total_challenges': 0,
            'total_sessions': 0,
            'total_xp': 0,
            'total_time_hours': 0.0,
            'member_since': datetime.utcnow().strftime('%Y-%m-%d'),
            'longest_streak': 0,
            'current_streak': 0
        },
        'language_progress': {},
        'level_mastery': {},
        'challenge_type_mastery': {},
        'learning_path': {
            'current_focus': None,
            'suggested_next': None,
            'weak_areas': [],
            'ready_for_next_level': []
        },
        'achievements': None,
        'milestones': {}
    }
