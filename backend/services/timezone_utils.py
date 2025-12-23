"""
Timezone Utilities for Statistics System

Provides timezone-aware date calculations for daily statistics.
"""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo


def get_user_timezone_obj(timezone_str: str = "UTC") -> ZoneInfo:
    """
    Get ZoneInfo object from timezone string.

    Args:
        timezone_str: Timezone string (e.g., "America/New_York")

    Returns:
        ZoneInfo object
    """
    try:
        return ZoneInfo(timezone_str)
    except Exception as e:
        print(f"[TIMEZONE] Invalid timezone '{timezone_str}', falling back to UTC: {e}")
        return ZoneInfo("UTC")


def convert_to_local_date(dt: datetime, timezone_str: str = "UTC") -> str:
    """
    Convert a UTC datetime to a local date string in the user's timezone.

    Args:
        dt: UTC datetime object
        timezone_str: User's timezone (e.g., "America/New_York")

    Returns:
        Local date string in format "YYYY-MM-DD"
    """
    try:
        # Ensure dt is timezone-aware (UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert to user's timezone
        user_tz = get_user_timezone_obj(timezone_str)
        local_dt = dt.astimezone(user_tz)

        # Return date string
        return local_dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"[TIMEZONE] Error converting to local date: {e}")
        # Fallback to UTC date
        return dt.strftime("%Y-%m-%d")


def get_current_local_date(timezone_str: str = "UTC") -> str:
    """
    Get the current date in the user's timezone.

    Args:
        timezone_str: User's timezone

    Returns:
        Current local date string in format "YYYY-MM-DD"
    """
    return convert_to_local_date(datetime.utcnow(), timezone_str)


def get_local_datetime_now(timezone_str: str = "UTC") -> datetime:
    """
    Get current datetime in user's timezone.

    Args:
        timezone_str: User's timezone

    Returns:
        Current datetime in user's timezone
    """
    try:
        user_tz = get_user_timezone_obj(timezone_str)
        utc_now = datetime.now(timezone.utc)
        return utc_now.astimezone(user_tz)
    except Exception as e:
        print(f"[TIMEZONE] Error getting local datetime: {e}")
        return datetime.utcnow()


def is_same_day(date1: datetime, date2: datetime, timezone_str: str = "UTC") -> bool:
    """
    Check if two datetimes are on the same day in the user's timezone.

    Args:
        date1: First datetime
        date2: Second datetime
        timezone_str: User's timezone

    Returns:
        True if dates are on the same day in user's timezone
    """
    local_date1 = convert_to_local_date(date1, timezone_str)
    local_date2 = convert_to_local_date(date2, timezone_str)
    return local_date1 == local_date2


def get_day_start_end(date_str: str, timezone_str: str = "UTC") -> tuple[datetime, datetime]:
    """
    Get the start and end datetime (in UTC) for a given local date.

    Args:
        date_str: Local date string "YYYY-MM-DD"
        timezone_str: User's timezone

    Returns:
        Tuple of (day_start_utc, day_end_utc)
    """
    try:
        user_tz = get_user_timezone_obj(timezone_str)

        # Parse the date string
        year, month, day = map(int, date_str.split("-"))

        # Create start of day in user's timezone
        day_start = datetime(year, month, day, 0, 0, 0, tzinfo=user_tz)

        # Create end of day (23:59:59) in user's timezone
        day_end = datetime(year, month, day, 23, 59, 59, 999999, tzinfo=user_tz)

        # Convert to UTC
        day_start_utc = day_start.astimezone(timezone.utc)
        day_end_utc = day_end.astimezone(timezone.utc)

        return day_start_utc, day_end_utc
    except Exception as e:
        print(f"[TIMEZONE] Error calculating day boundaries: {e}")
        # Fallback: treat as UTC date
        year, month, day = map(int, date_str.split("-"))
        day_start = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
        day_end = datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)
        return day_start, day_end


def is_weekend(dt: datetime, timezone_str: str = "UTC") -> bool:
    """
    Check if a datetime falls on a weekend in the user's timezone.

    Args:
        dt: Datetime to check
        timezone_str: User's timezone

    Returns:
        True if datetime is on Saturday (5) or Sunday (6)
    """
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        user_tz = get_user_timezone_obj(timezone_str)
        local_dt = dt.astimezone(user_tz)

        # weekday() returns 0-6 (Monday-Sunday)
        # 5 = Saturday, 6 = Sunday
        return local_dt.weekday() in [5, 6]
    except Exception as e:
        print(f"[TIMEZONE] Error checking weekend: {e}")
        return False


def get_dates_in_range(start_date: str, end_date: str) -> list[str]:
    """
    Get list of date strings between start_date and end_date (inclusive).

    Args:
        start_date: Start date string "YYYY-MM-DD"
        end_date: End date string "YYYY-MM-DD"

    Returns:
        List of date strings
    """
    from datetime import timedelta

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        dates = []
        current_dt = start_dt
        while current_dt <= end_dt:
            dates.append(current_dt.strftime("%Y-%m-%d"))
            current_dt += timedelta(days=1)

        return dates
    except Exception as e:
        print(f"[TIMEZONE] Error generating date range: {e}")
        return []


def calculate_streak_days(last_practice_date: Optional[str], current_date: str) -> int:
    """
    Calculate how many days streak should be incremented.

    Args:
        last_practice_date: Last date user practiced (local date string)
        current_date: Current practice date (local date string)

    Returns:
        0 if streak is broken, 1 if continuing streak
    """
    if not last_practice_date:
        # First time practicing
        return 1

    try:
        from datetime import timedelta

        last_dt = datetime.strptime(last_practice_date, "%Y-%m-%d")
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")

        day_diff = (current_dt - last_dt).days

        if day_diff == 0:
            # Same day, no increment
            return 0
        elif day_diff == 1:
            # Consecutive day, increment
            return 1
        else:
            # Streak broken, restart
            return -1  # Signal to reset streak
    except Exception as e:
        print(f"[TIMEZONE] Error calculating streak: {e}")
        return 0
