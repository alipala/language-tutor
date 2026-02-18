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

    Voice checks are adaptive based on plan duration:
    - 1-month (8 sessions): Every 3 sessions → 3 voice samples
    - 2-month (16 sessions): Every 5 sessions → 4 voice samples
    - 3-month (24 sessions): Every 6 sessions → 5 voice samples
    - 6-month (48 sessions): Every 8 sessions → 7 voice samples
    - 12-month (96 sessions): Every 10 sessions → 11 voice samples

    Session 1 is always the Speaking Assessment (initial baseline).
    """

    @staticmethod
    def calculate_voice_check_schedule(duration_months: int) -> List[int]:
        """
        Calculate voice check sessions based on plan duration.

        Design principles:
        - NO check on session 1: the learning plan is created right after a full
          Speaking Assessment, so session 1 already has a fresh acoustic baseline.
        - NO check on the final session: it already ends with a full Speaking
          Assessment that generates the next learning plan.
        - Checks are placed at natural mid-plan milestones so they feel like
          progress snapshots, not interruptions (~2-3 per month max).

        Args:
            duration_months: Learning plan duration (1, 2, 3, 6, or 12 months)

        Returns:
            List of session numbers where voice checks should occur

        Schedules:
            1-month  (8 sessions):  [3, 6]              – 2 checks
            2-month  (16 sessions): [4, 8, 12]          – 3 checks
            3-month  (24 sessions): [6, 12, 18]         – 3 checks
            6-month  (48 sessions): [8, 16, 24, 32, 40] – 5 checks
            12-month (96 sessions): [12,24,36,48,60,72,84] – 7 checks
        """
        total_sessions = duration_months * 8

        if total_sessions <= 8:       # 1-month
            schedule = [3, 6]
        elif total_sessions <= 16:    # 2-month
            schedule = [4, 8, 12]
        elif total_sessions <= 24:    # 3-month
            schedule = [6, 12, 18]
        elif total_sessions <= 48:    # 6-month
            schedule = [8, 16, 24, 32, 40]
        else:                         # 12-month
            schedule = [12, 24, 36, 48, 60, 72, 84]

        # Safety: remove any entry that equals the final session or exceeds it
        schedule = [s for s in schedule if s < total_sessions]

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
