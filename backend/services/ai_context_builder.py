"""
AI Context Builder

Builds context strings from user statistics for AI Tutor prompt generation.
Provides structured learning context for personalized recommendations.
"""

from typing import Dict, Any, Optional
from services.timezone_utils import get_current_local_date
from services.recent_performance_service import get_recent_performance
from services.lifetime_progress_service import get_lifetime_progress
from database import daily_stats_collection, users_collection
from bson import ObjectId


async def build_ai_tutor_context(user_id: str, timezone_str: str = "UTC") -> str:
    """
    Build comprehensive context string for AI tutor prompts.

    This function aggregates user statistics into a human-readable
    format optimized for LLM consumption.

    Args:
        user_id: User ID
        timezone_str: User's timezone

    Returns:
        Formatted context string for AI prompt
    """
    try:
        print(f"[AI_CONTEXT] 🤖 Building AI context for user {user_id}")

        # Fetch all stat layers
        daily_stat = await get_today_summary(user_id, timezone_str)
        recent_perf = await get_recent_performance(user_id, 7, timezone_str)
        lifetime_prog = await get_lifetime_progress(user_id)

        # Build context string
        context = build_context_string(daily_stat, recent_perf, lifetime_prog)

        print(f"[AI_CONTEXT] ✅ AI context built ({len(context)} chars)")

        return context

    except Exception as e:
        print(f"[AI_CONTEXT] ❌ Error building AI context: {str(e)}")
        return "User learning context unavailable."


async def get_today_summary(user_id: str, timezone_str: str) -> Dict[str, Any]:
    """Get today's summary for AI context."""
    local_date = get_current_local_date(timezone_str)

    daily_stat = await daily_stats_collection.find_one({
        'user_id': user_id,
        'local_date': local_date
    })

    if not daily_stat:
        return {
            'total_challenges': 0,
            'accuracy': 0.0,
            'streak': 0,
            'languages': []
        }

    # Get streak from user
    user = await users_collection.find_one({'_id': ObjectId(user_id)})
    streak = user.get('stats', {}).get('current_streak', 0) if user else 0

    return {
        'total_challenges': daily_stat.get('total_challenges', 0),
        'accuracy': daily_stat.get('accuracy_percent', 0.0),
        'streak': streak,
        'languages': list(daily_stat.get('by_language', {}).keys())
    }


def build_context_string(
    daily_stat: Dict[str, Any],
    recent_perf: Dict[str, Any],
    lifetime_prog: Dict[str, Any]
) -> str:
    """Build formatted context string from statistics."""

    # Extract key data
    daily_challenges = daily_stat.get('total_challenges', 0)
    daily_accuracy = daily_stat.get('accuracy', 0.0)
    streak = daily_stat.get('streak', 0)
    daily_languages = daily_stat.get('languages', [])

    recent_challenges = recent_perf.get('total_challenges', 0)
    recent_accuracy = recent_perf.get('average_accuracy', 0.0)
    most_practiced_lang = recent_perf.get('most_practiced_language', 'unknown')
    most_practiced_type = recent_perf.get('most_practiced_type', 'unknown')
    weakest_level = recent_perf.get('weakest_level', 'unknown')
    improvement_trend = recent_perf.get('improvement_trend', 'stable')

    lifetime_summary = lifetime_prog.get('summary', {})
    total_challenges = lifetime_summary.get('total_challenges', 0)
    total_time_hours = lifetime_summary.get('total_time_hours', 0.0)

    language_progress = lifetime_prog.get('language_progress', {})
    learning_path = lifetime_prog.get('learning_path', {})

    # Find highest level across all languages
    highest_level = 'A1'
    for lang_data in language_progress.values():
        lang_level = lang_data.get('highest_level', 'A1')
        from services.stats_service import get_cefr_level_rank
        if get_cefr_level_rank(lang_level) > get_cefr_level_rank(highest_level):
            highest_level = lang_level

    # Get strong areas
    type_mastery = lifetime_prog.get('challenge_type_mastery', {})
    strong_types = [
        ctype for ctype, data in type_mastery.items()
        if data.get('mastery_level', 0) >= 4
    ]

    # Build context
    context = f"""User Learning Context:

TODAY'S ACTIVITY:
- Completed {daily_challenges} challenges with {daily_accuracy:.1f}% accuracy
- Current {streak}-day streak
- Focused on: {', '.join(daily_languages) if daily_languages else 'No practice yet today'}

RECENT PERFORMANCE (Last 7 Days):
- Total challenges: {recent_challenges}
- Average accuracy: {recent_accuracy:.1f}%
- Most practiced: {most_practiced_lang} language using {most_practiced_type} challenges
- Weakest area: {weakest_level} level (needs support)
- Learning trend: {improvement_trend}

LONG-TERM PROGRESS:
- Total challenges completed: {total_challenges}
- Total practice time: {total_time_hours} hours
- Learning: {', '.join(language_progress.keys())}
- Highest proficiency level: {highest_level}
- Strong challenge types: {', '.join(strong_types) if strong_types else 'Still building skills'}

LEARNING PATH:
- Current focus: {learning_path.get('current_focus', 'Not yet determined')}
- Suggested next: {learning_path.get('suggested_next', 'Continue current level')}
- Areas needing work: {', '.join(learning_path.get('weak_areas', [])) or 'All areas progressing well'}

RECOMMENDATIONS:
"""

    # Add recommendations based on data
    if improvement_trend == 'negative':
        context += "- Review fundamentals to address declining accuracy\n"
    if daily_challenges == 0:
        context += f"- Encourage daily practice to maintain {streak}-day streak\n"
    if weakest_level and weakest_level != 'unknown':
        context += f"- Focus extra attention on {weakest_level} level challenges\n"
    if recent_accuracy < 70:
        context += "- Suggest revisiting lower difficulty levels for confidence building\n"
    elif recent_accuracy > 90:
        context += "- User is excelling - suggest advancing to higher difficulty\n"

    context += "\nUse this context to provide personalized, encouraging feedback and adaptive challenge recommendations."

    return context


async def build_compact_context(user_id: str, timezone_str: str = "UTC") -> Dict[str, Any]:
    """
    Build compact JSON context for API responses or structured AI inputs.

    Args:
        user_id: User ID
        timezone_str: User's timezone

    Returns:
        Compact dictionary with key stats
    """
    try:
        daily_stat = await get_today_summary(user_id, timezone_str)
        recent_perf = await get_recent_performance(user_id, 7, timezone_str)
        lifetime_prog = await get_lifetime_progress(user_id)

        return {
            'today': {
                'challenges': daily_stat.get('total_challenges', 0),
                'accuracy': round(daily_stat.get('accuracy', 0.0), 1),
                'streak': daily_stat.get('streak', 0)
            },
            'recent': {
                'challenges': recent_perf.get('total_challenges', 0),
                'accuracy': round(recent_perf.get('average_accuracy', 0.0), 1),
                'trend': recent_perf.get('improvement_trend', 'stable'),
                'weak_area': recent_perf.get('weakest_level', 'none')
            },
            'lifetime': {
                'total_challenges': lifetime_prog.get('summary', {}).get('total_challenges', 0),
                'languages': list(lifetime_prog.get('language_progress', {}).keys()),
                'highest_level': get_highest_level(lifetime_prog.get('language_progress', {}))
            },
            'recommendations': generate_recommendations(daily_stat, recent_perf, lifetime_prog)
        }

    except Exception as e:
        print(f"[AI_CONTEXT] ❌ Error building compact context: {str(e)}")
        return {}


def get_highest_level(language_progress: Dict[str, Any]) -> str:
    """Extract highest CEFR level from language progress."""
    highest = 'A1'
    from services.stats_service import get_cefr_level_rank

    for lang_data in language_progress.values():
        level = lang_data.get('highest_level', 'A1')
        if get_cefr_level_rank(level) > get_cefr_level_rank(highest):
            highest = level

    return highest


def generate_recommendations(
    daily_stat: Dict[str, Any],
    recent_perf: Dict[str, Any],
    lifetime_prog: Dict[str, Any]
) -> list[str]:
    """Generate actionable recommendations based on stats."""
    recommendations = []

    recent_accuracy = recent_perf.get('average_accuracy', 0.0)
    improvement_trend = recent_perf.get('improvement_trend', 'stable')
    daily_challenges = daily_stat.get('total_challenges', 0)
    streak = daily_stat.get('streak', 0)
    weakest_level = recent_perf.get('weakest_level')

    if improvement_trend == 'negative':
        recommendations.append('review_fundamentals')
    if daily_challenges == 0 and streak > 0:
        recommendations.append('maintain_streak')
    if weakest_level:
        recommendations.append(f'focus_{weakest_level.lower()}')
    if recent_accuracy < 70:
        recommendations.append('lower_difficulty')
    elif recent_accuracy > 90:
        recommendations.append('increase_difficulty')

    return recommendations
