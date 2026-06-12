"""
Statistics Service

Core business logic for calculating and aggregating user statistics.
Implements the event-based architecture from the design document.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId

from database import (
    challenge_sessions_collection,
    daily_stats_collection,
    users_collection,
    recent_performance_collection
)
from services.timezone_utils import (
    convert_to_local_date,
    get_current_local_date,
    calculate_streak_days,
    get_dates_in_range
)
from services.progression import compute_level


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_accuracy(correct: int, total: int) -> float:
    """Calculate accuracy percentage."""
    if total == 0:
        return 0.0
    return round((correct / total) * 100, 2)


def get_cefr_level_rank(level: str) -> int:
    """Get numeric rank for CEFR level (for comparison)."""
    level_ranks = {
        "A1": 1,
        "A2": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
        "C2": 6
    }
    return level_ranks.get(level, 0)


def calculate_next_milestone(current_streak: int) -> int:
    """Calculate next streak milestone."""
    milestones = [7, 10, 14, 21, 30, 50, 100]
    for milestone in milestones:
        if current_streak < milestone:
            return milestone
    return current_streak + 50  # If beyond 100, add 50


# ============================================================================
# DAILY STATS AGGREGATION
# ============================================================================

async def update_daily_stats(session_data: Dict[str, Any]) -> None:
    """
    Update daily statistics after a session is completed.
    Uses incremental aggregation with MongoDB $inc operators.

    Args:
        session_data: Completed session data with all fields
    """
    try:
        user_id = session_data['user_id']
        local_date = session_data['local_date']
        language = session_data['language']
        level = session_data['level']
        challenge_type = session_data['challenge_type']

        # Prepare increment operations
        increments = {
            'total_sessions': 1,
            'total_challenges': session_data['total_challenges'],
            'correct_challenges': session_data['correct_answers'],
            'incorrect_challenges': session_data['wrong_answers'],
            'total_xp': session_data['total_xp'],
            # Source-tagged XP so the Games tab progression bar can
            # surface "challenge XP only" via /progression?source=games.
            # Without this, the Games tab summed *all* XP (including
            # learning-plan conversation XP) and showed 82/50 after a
            # plan session even though the user hadn't played a game.
            'challenge_xp': session_data['total_xp'],
            'total_time_seconds': session_data.get('duration_seconds', 0),

            # Language breakdown
            f'by_language.{language}.challenges': session_data['total_challenges'],
            f'by_language.{language}.correct': session_data['correct_answers'],
            f'by_language.{language}.incorrect': session_data['wrong_answers'],
            f'by_language.{language}.xp': session_data['total_xp'],

            # Level breakdown
            f'by_level.{level}.challenges': session_data['total_challenges'],
            f'by_level.{level}.correct': session_data['correct_answers'],
            f'by_level.{level}.incorrect': session_data['wrong_answers'],

            # Type breakdown
            f'by_type.{challenge_type}.challenges': session_data['total_challenges'],
            f'by_type.{challenge_type}.correct': session_data['correct_answers'],
            f'by_type.{challenge_type}.incorrect': session_data['wrong_answers'],
            f'by_type.{challenge_type}.xp': session_data['total_xp'],
        }

        # Upsert daily stats document
        result = await daily_stats_collection.update_one(
            {
                'user_id': user_id,
                'local_date': local_date
            },
            {
                '$inc': increments,
                '$set': {
                    'user_timezone': session_data.get('user_timezone', 'UTC'),
                    'updated_at': datetime.utcnow(),
                    'last_session_id': session_data.get('_id')
                },
                '$setOnInsert': {
                    'created_at': datetime.utcnow(),
                    'is_streak_day': True
                }
            },
            upsert=True
        )

        # Recalculate accuracy percentages for this daily stat
        await recalculate_daily_accuracy(user_id, local_date)

        print(f"[STATS_SERVICE] ✅ Updated daily stats for user {user_id}, date {local_date}")

    except Exception as e:
        print(f"[STATS_SERVICE] ❌ Error updating daily stats: {str(e)}")
        import traceback
        print(traceback.format_exc())


async def recalculate_daily_accuracy(user_id: str, local_date: str) -> None:
    """
    Recalculate accuracy percentages for a daily stat document.

    Args:
        user_id: User ID
        local_date: Local date string
    """
    try:
        daily_stat = await daily_stats_collection.find_one({
            'user_id': user_id,
            'local_date': local_date
        })

        if not daily_stat:
            return

        # Calculate overall accuracy
        total = daily_stat.get('total_challenges', 0)
        correct = daily_stat.get('correct_challenges', 0)
        overall_accuracy = calculate_accuracy(correct, total)

        # Calculate accuracy by language
        by_language = daily_stat.get('by_language', {})
        for lang, lang_data in by_language.items():
            lang_total = lang_data.get('challenges', 0)
            lang_correct = lang_data.get('correct', 0)
            by_language[lang]['accuracy'] = calculate_accuracy(lang_correct, lang_total)

        # Calculate accuracy by level
        by_level = daily_stat.get('by_level', {})
        for level, level_data in by_level.items():
            level_total = level_data.get('challenges', 0)
            level_correct = level_data.get('correct', 0)
            by_level[level]['accuracy'] = calculate_accuracy(level_correct, level_total)

        # Calculate accuracy by type
        by_type = daily_stat.get('by_type', {})
        for ctype, type_data in by_type.items():
            type_total = type_data.get('challenges', 0)
            type_correct = type_data.get('correct', 0)
            by_type[ctype]['accuracy'] = calculate_accuracy(type_correct, type_total)

        # Update document
        await daily_stats_collection.update_one(
            {'_id': daily_stat['_id']},
            {
                '$set': {
                    'accuracy_percent': overall_accuracy,
                    'by_language': by_language,
                    'by_level': by_level,
                    'by_type': by_type
                }
            }
        )

    except Exception as e:
        print(f"[STATS_SERVICE] ❌ Error recalculating accuracy: {str(e)}")


# ============================================================================
# LIFETIME STATS UPDATE
# ============================================================================

async def update_lifetime_stats(session_data: Dict[str, Any]) -> None:
    """
    Update lifetime statistics in the user document.

    Args:
        session_data: Completed session data
    """
    try:
        user_id = session_data['user_id']
        language = session_data['language']
        level = session_data['level']
        challenge_type = session_data['challenge_type']

        # Prepare increments
        increments = {
            'stats.lifetime.total_challenges': session_data['total_challenges'],
            'stats.lifetime.total_sessions': 1,
            'stats.lifetime.total_xp': session_data['total_xp'],
            'stats.lifetime.xp_by_source.challenges': session_data['total_xp'],
            'stats.lifetime.total_time_minutes': session_data.get('duration_seconds', 0) / 60,

            f'stats.lifetime.by_language.{language}.total_challenges': session_data['total_challenges'],
            f'stats.lifetime.by_language.{language}.total_xp': session_data['total_xp'],

            f'stats.lifetime.by_level.{level}.total_challenges': session_data['total_challenges'],
            f'stats.lifetime.by_level.{level}.correct': session_data['correct_answers'],
            f'stats.lifetime.by_level.{level}.incorrect': session_data['wrong_answers'],

            f'stats.lifetime.by_type.{challenge_type}.total_challenges': session_data['total_challenges'],
            f'stats.lifetime.by_type.{challenge_type}.correct': session_data['correct_answers'],
            f'stats.lifetime.by_type.{challenge_type}.incorrect': session_data['wrong_answers'],

            # Per-language-per-level counters — feed the CEFR earn gate
            # below. Additive; older documents simply start at zero.
            f'stats.lifetime.by_language.{language}.by_level.{level}.total_challenges': session_data['total_challenges'],
            f'stats.lifetime.by_language.{language}.by_level.{level}.correct': session_data['correct_answers'],
            f'stats.lifetime.by_language.{language}.by_level.{level}.incorrect': session_data['wrong_answers'],
        }

        updates = {
            'stats.last_calculated': datetime.utcnow(),
            f'stats.lifetime.by_language.{language}.last_practiced': datetime.utcnow(),
        }

        # Check if we need to update highest level.
        #
        # CEFR earn gate: completing a single game at a level used to raise
        # `highest_level` unconditionally, which let a day-one user claim a
        # C2 (legendary) badge by simply selecting C2 in the level picker
        # and finishing one session at any accuracy. Challenges now have to
        # EARN the level: at least CEFR_GATE_MIN_CHALLENGES at that level
        # with CEFR_GATE_MIN_ACCURACY overall accuracy (post-session,
        # per-language). Speaking assessments remain the direct path — the
        # assessment route raises highest_level from recommended_level
        # without this gate, because there the level is measured, not picked.
        CEFR_GATE_MIN_CHALLENGES = 20
        CEFR_GATE_MIN_ACCURACY = 0.75

        user = await users_collection.find_one({'_id': ObjectId(user_id)})
        if user:
            lang_stats = (user.get('stats', {})
                          .get('lifetime', {})
                          .get('by_language', {})
                          .get(language, {}))
            current_highest = lang_stats.get('highest_level')

            if get_cefr_level_rank(level) > get_cefr_level_rank(current_highest or ''):
                # Post-session totals for this language+level (pre-image +
                # this session, since $inc applies after our read).
                lvl_stats = (lang_stats.get('by_level', {}) or {}).get(level, {}) or {}
                new_total = int(lvl_stats.get('total_challenges', 0) or 0) + int(session_data['total_challenges'] or 0)
                new_correct = int(lvl_stats.get('correct', 0) or 0) + int(session_data['correct_answers'] or 0)
                new_accuracy = (new_correct / new_total) if new_total > 0 else 0.0
                if new_total >= CEFR_GATE_MIN_CHALLENGES and new_accuracy >= CEFR_GATE_MIN_ACCURACY:
                    updates[f'stats.lifetime.by_language.{language}.highest_level'] = level
                    print(f"[STATS_SERVICE] 🎓 CEFR gate passed: {language} -> {level} "
                          f"({new_total} challenges @ {round(new_accuracy * 100)}%)")
                else:
                    print(f"[STATS_SERVICE] CEFR gate not met for {language} {level}: "
                          f"{new_total}/{CEFR_GATE_MIN_CHALLENGES} challenges @ {round(new_accuracy * 100)}%")

            # Set started_at if this is first time for this language
            if not lang_stats.get('started_at') and not current_highest:
                updates[f'stats.lifetime.by_language.{language}.started_at'] = datetime.utcnow()

        # Phase A: persist the derived gameplay level alongside total_xp so
        # readers (Hub header, Coach, recommender) don't need to recompute.
        # We compute against the post-increment total because $inc and $set in
        # the same update operate on the pre-image; the value will be one
        # session behind for one read at most, then the next write catches up.
        previous_total_xp = int(
            (user or {})
            .get('stats', {})
            .get('lifetime', {})
            .get('total_xp', 0)
            or 0
        )
        projected_total_xp = previous_total_xp + int(session_data.get('total_xp', 0) or 0)
        updates['stats.lifetime.level'] = compute_level(projected_total_xp)

        # Update user document
        await users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$inc': increments,
                '$set': updates
            }
        )

        print(f"[STATS_SERVICE] ✅ Updated lifetime stats for user {user_id}")

    except Exception as e:
        print(f"[STATS_SERVICE] ❌ Error updating lifetime stats: {str(e)}")
        import traceback
        print(traceback.format_exc())


# ============================================================================
# STREAK MANAGEMENT
# ============================================================================

async def maybe_update_streak_for_voice_session(
    user_id: str,
    local_date: str,
    timezone_str: str,
    *,
    engaged: bool,
) -> None:
    """
    Forward-only, engagement-gated wrapper around ``update_streak``.

    Purpose: keep ``users.stats.current_streak`` honest for conversation /
    news / custom-topic / learning-plan sessions, which (unlike challenges)
    do not flow through ``process_session_completion`` and therefore never
    call ``update_streak`` directly today. Without this, the Hub's streak
    field is stale for voice-only users.

    Two guards mirror the just-shipped challenge-side ``abandoned`` gate:

    1. **Engagement floor** — the caller passes ``engaged`` based on a
       real signal at the save site (e.g. ``is_streak_eligible`` for
       free conversations, ``session_duration_minutes >= selected_duration``
       for learning-plan sessions). An empty/abandoned conversation must
       arrive with ``engaged=False`` and is silently skipped.

    2. **Forward-only date guard** — accepts the call only when
       ``local_date`` is today or yesterday in the user's timezone.
       Tolerates the just-before-midnight save boundary (session starts
       23:59 today, save fires 00:01 tomorrow → diff=1, allowed).
       Rejects any historical replay / backfill / retry of an older
       session, so a stray write can never move ``last_practice_date``
       backwards or trigger a spurious reset.

    Failures are non-fatal: the wrapper logs and returns rather than
    raising, so the caller's save-path is never broken by a streak
    bookkeeping problem.
    """
    if not engaged:
        print(
            f"[STREAK] ⏭️  Skipping non-engaged session for user {user_id} "
            f"(local_date={local_date})"
        )
        return

    try:
        today_local = get_current_local_date(timezone_str=timezone_str)
        today_dt    = datetime.strptime(today_local, "%Y-%m-%d")
        session_dt  = datetime.strptime(local_date,  "%Y-%m-%d")
        day_diff    = (today_dt - session_dt).days
    except Exception as parse_err:
        print(
            f"[STREAK] ⏭️  Skipping streak update — could not parse dates "
            f"(local_date={local_date}, tz={timezone_str}): {parse_err}"
        )
        return

    if not (0 <= day_diff <= 1):
        # Historical (>=2 days old) or future-dated payload. Refuse.
        print(
            f"[STREAK] ⏭️  Skipping out-of-window session for user {user_id} "
            f"(local_date={local_date}, today={today_local}, day_diff={day_diff})"
        )
        return

    try:
        await update_streak(user_id, local_date, timezone_str)
    except Exception as e:
        # Defensive — update_streak() already swallows its own exceptions,
        # but we belt-and-brace so the caller's save flow never breaks.
        print(f"[STREAK] ⚠️  Non-fatal failure in voice-session streak update: {e}")


async def update_streak(user_id: str, local_date: str, timezone_str: str) -> None:
    """
    Update user's streak based on practice date.

    Args:
        user_id: User ID
        local_date: Current practice date in user's timezone
        timezone_str: User's timezone
    """
    try:
        user = await users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return

        # Get current streak data
        stats = user.get('stats', {})
        last_practice_date = stats.get('last_practice_date')
        current_streak = stats.get('current_streak', 0)
        longest_streak = stats.get('longest_streak', 0)

        # Calculate streak change
        streak_change = calculate_streak_days(last_practice_date, local_date)

        if streak_change == -1:
            # Streak broken, reset to 1
            new_streak = 1
        elif streak_change == 1:
            # Consecutive day, increment
            new_streak = current_streak + 1
        else:
            # Same day, no change
            new_streak = current_streak

        # Update longest streak if needed
        new_longest = max(longest_streak, new_streak)

        # Update user document
        await users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'stats.current_streak': new_streak,
                    'stats.longest_streak': new_longest,
                    'stats.last_practice_date': local_date
                }
            }
        )

        # Update today's daily stat with streak count
        await daily_stats_collection.update_one(
            {
                'user_id': user_id,
                'local_date': local_date
            },
            {
                '$set': {
                    'streak_count': new_streak
                }
            }
        )

        print(f"[STATS_SERVICE] ✅ Updated streak for user {user_id}: {new_streak} (longest: {new_longest})")

    except Exception as e:
        print(f"[STATS_SERVICE] ❌ Error updating streak: {str(e)}")
        import traceback
        print(traceback.format_exc())


# ============================================================================
# CACHE INVALIDATION
# ============================================================================

async def invalidate_recent_performance_cache(user_id: str) -> None:
    """
    Invalidate (delete) recent performance cache for a user.

    Args:
        user_id: User ID
    """
    try:
        result = await recent_performance_collection.delete_many({'user_id': user_id})
        if result.deleted_count > 0:
            print(f"[STATS_SERVICE] 🗑️  Invalidated recent performance cache for user {user_id}")
    except Exception as e:
        print(f"[STATS_SERVICE] ❌ Error invalidating cache: {str(e)}")


# ============================================================================
# MAIN SESSION COMPLETION HANDLER
# ============================================================================

async def process_session_completion(session_data: Dict[str, Any]) -> None:
    """
    Main entry point for processing a completed session.
    This orchestrates all statistics updates.

    Args:
        session_data: Complete session data including timezone and local_date
    """
    try:
        user_id = session_data['user_id']
        local_date = session_data['local_date']
        timezone_str = session_data.get('user_timezone', 'UTC')

        print(f"[STATS_SERVICE] 📊 Processing session completion for user {user_id}")

        # 1. Update daily stats (incremental)
        await update_daily_stats(session_data)

        # 2. Update lifetime stats
        await update_lifetime_stats(session_data)

        # 3. Update streak
        await update_streak(user_id, local_date, timezone_str)

        # 4. Invalidate recent performance cache
        await invalidate_recent_performance_cache(user_id)

        print(f"[STATS_SERVICE] ✅ Session processing complete for user {user_id}")

    except Exception as e:
        print(f"[STATS_SERVICE] ❌ Error processing session completion: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # Don't raise - we don't want to fail the session completion
