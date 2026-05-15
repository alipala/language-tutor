"""
Voice Check Schedule Service

Manages periodic voice check scheduling for Speaking DNA acoustic analysis.
Voice checks are triggered after learning plan sessions to capture acoustic data
(pitch, jitter, shimmer, WPM, pauses, filler rate) without interfering with
the OpenAI Realtime API WebRTC stream.

Premium Feature: Only available for users with active subscriptions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime


class VoiceCheckScheduleService:
    """
    Calculates and tracks voice check schedules for learning plans.

    Plans use 4 sessions/week. Voice checks are spaced ~monthly (every ~16 sessions)
    so each check feels like a real progress milestone, not an interruption.

    Session 1 is always the Speaking Assessment (initial baseline).
    """

    # Sessions per week — must match the plan creation constant
    SESSIONS_PER_WEEK = 4
    WEEKS_PER_MONTH = 4

    @classmethod
    def _total_sessions(cls, duration_months: int) -> int:
        return duration_months * cls.WEEKS_PER_MONTH * cls.SESSIONS_PER_WEEK

    @staticmethod
    def calculate_voice_check_schedule(duration_months: int) -> List[int]:
        """
        Calculate voice check sessions based on plan duration.

        Design principles:
        - Plans are 3, 6, 9, or 12 months at 4 sessions/week.
        - Voice checks occur roughly once per month (every ~16 sessions).
        - NO check on session 1 (initial Speaking Assessment baseline).
        - NO check on the final session (ends with full Speaking Assessment).

        Schedules (4 sessions/week × 4 weeks = 16 sessions/month):
            3-month  (48 sessions):  [12, 24, 36]                    – 3 checks
            6-month  (96 sessions):  [12, 24, 36, 48, 60, 72, 84]   – 7 checks
            9-month  (144 sessions): [16, 32, 48, 64, 80, 96, 112, 128] – 8 checks
            12-month (192 sessions): [16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176] – 11 checks
        """
        SESSIONS_PER_MONTH = 16  # 4 sessions/week × 4 weeks

        total_sessions = duration_months * SESSIONS_PER_MONTH

        if duration_months <= 3:      # 3-month (48 sessions)
            schedule = [12, 24, 36]
        elif duration_months <= 6:    # 6-month (96 sessions)
            schedule = [12, 24, 36, 48, 60, 72, 84]
        elif duration_months <= 9:    # 9-month (144 sessions)
            schedule = [16, 32, 48, 64, 80, 96, 112, 128]
        else:                         # 12-month (192 sessions)
            schedule = [16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176]

        # Safety: exclude session 1 and the final session
        schedule = [s for s in schedule if 1 < s < total_sessions]

        return schedule

    @staticmethod
    def is_voice_check_due(
        completed_sessions: int,
        duration_months: int,
        voice_checks_completed: Optional[List[int]] = None
    ) -> bool:
        """
        Check if a voice check is due after the current session.

        Args:
            completed_sessions: Number of sessions completed so far
            duration_months: Learning plan duration
            voice_checks_completed: List of session numbers where voice checks were completed

        Returns:
            True if voice check is due, False otherwise
        """
        if voice_checks_completed is None:
            voice_checks_completed = []

        schedule = VoiceCheckScheduleService.calculate_voice_check_schedule(duration_months)

        # Check if current session is in the schedule and hasn't been completed yet
        return completed_sessions in schedule and completed_sessions not in voice_checks_completed

    @staticmethod
    def get_next_voice_check(
        completed_sessions: int,
        duration_months: int,
        voice_checks_completed: Optional[List[int]] = None
    ) -> Optional[int]:
        """
        Get the next scheduled voice check session number.

        Args:
            completed_sessions: Number of sessions completed so far
            duration_months: Learning plan duration
            voice_checks_completed: List of session numbers where voice checks were completed

        Returns:
            Next voice check session number, or None if all completed
        """
        if voice_checks_completed is None:
            voice_checks_completed = []

        schedule = VoiceCheckScheduleService.calculate_voice_check_schedule(duration_months)

        # Find the next voice check in the schedule that hasn't been completed
        for session_num in schedule:
            if session_num > completed_sessions and session_num not in voice_checks_completed:
                return session_num

        return None

    @staticmethod
    def get_voice_check_progress(
        duration_months: int,
        voice_checks_completed: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get voice check progress statistics.

        Args:
            duration_months: Learning plan duration
            voice_checks_completed: List of session numbers where voice checks were completed

        Returns:
            Dictionary with progress stats:
            - total_scheduled: Total number of voice checks in the plan
            - completed: Number of voice checks completed
            - remaining: Number of voice checks remaining
            - completion_percentage: Percentage of voice checks completed
            - schedule: Full list of scheduled voice check sessions
        """
        if voice_checks_completed is None:
            voice_checks_completed = []

        schedule = VoiceCheckScheduleService.calculate_voice_check_schedule(duration_months)
        total_scheduled = len(schedule)
        completed = len([s for s in schedule if s in voice_checks_completed])
        remaining = total_scheduled - completed
        completion_percentage = (completed / total_scheduled * 100) if total_scheduled > 0 else 0.0

        return {
            "total_scheduled": total_scheduled,
            "completed": completed,
            "remaining": remaining,
            "completion_percentage": round(completion_percentage, 1),
            "schedule": schedule,
            "completed_sessions": sorted(voice_checks_completed)
        }

    @staticmethod
    def mark_voice_check_completed(
        voice_checks_completed: Optional[List[int]],
        session_number: int
    ) -> List[int]:
        """
        Mark a voice check as completed.

        Args:
            voice_checks_completed: Current list of completed voice checks
            session_number: Session number to mark as completed

        Returns:
            Updated list of completed voice checks
        """
        if voice_checks_completed is None:
            voice_checks_completed = []

        # Ensure no duplicates
        if session_number not in voice_checks_completed:
            voice_checks_completed.append(session_number)

        return sorted(voice_checks_completed)

    @staticmethod
    def get_voice_check_prompt(check_number: int) -> Dict[str, str]:
        """
        Get a voice check prompt with variety rotation.

        Args:
            check_number: Voice check number (0-indexed from first check after assessment)

        Returns:
            Dictionary with title, prompt, and icon
        """
        prompts = [
            {
                "title": "Daily Life",
                "prompt": "Tell me about something interesting that happened to you recently.",
                "icon": "calendar"
            },
            {
                "title": "Opinions",
                "prompt": "What's your opinion on learning languages online?",
                "icon": "chatbubbles"
            },
            {
                "title": "Future Plans",
                "prompt": "What are you looking forward to in the coming weeks?",
                "icon": "rocket"
            },
            {
                "title": "Experiences",
                "prompt": "Describe a place you visited that you really enjoyed.",
                "icon": "airplane"
            },
            {
                "title": "Preferences",
                "prompt": "What do you like to do in your free time and why?",
                "icon": "heart"
            },
            {
                "title": "Reflections",
                "prompt": "How do you feel about your language learning progress so far?",
                "icon": "trending-up"
            },
        ]

        # Rotate prompts based on check number
        return prompts[check_number % len(prompts)]


# Singleton instance
voice_check_service = VoiceCheckScheduleService()
