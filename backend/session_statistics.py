"""
Session Statistics Calculator
Calculates comprehensive session metrics for progress tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import re


class SessionStatistics:
    """Calculate and format session statistics for progress tracking"""

    @staticmethod
    def calculate_words_spoken(messages: List[Dict[str, Any]], role: str = 'user') -> int:
        """
        Calculate total words spoken by a specific role (default: user)

        Args:
            messages: List of conversation messages
            role: Role to count words for ('user' or 'assistant')

        Returns:
            Total word count
        """
        word_count = 0
        for msg in messages:
            if msg.get('role') == role:
                content = msg.get('content', '')
                # Split by whitespace and count non-empty words
                words = [w for w in content.split() if w.strip()]
                word_count += len(words)

        return word_count

    @staticmethod
    def calculate_speaking_speed(words_spoken: int, duration_minutes: float) -> float:
        """
        Calculate speaking speed in words per minute

        Args:
            words_spoken: Total words spoken
            duration_minutes: Session duration in minutes

        Returns:
            Speaking speed in words per minute (rounded to 1 decimal)
        """
        if duration_minutes <= 0:
            return 0.0

        wpm = words_spoken / duration_minutes
        return round(wpm, 1)

    @staticmethod
    def calculate_unique_vocabulary(messages: List[Dict[str, Any]], role: str = 'user') -> int:
        """
        Calculate unique vocabulary size for a specific role

        Args:
            messages: List of conversation messages
            role: Role to count vocabulary for ('user' or 'assistant')

        Returns:
            Count of unique words
        """
        unique_words = set()

        for msg in messages:
            if msg.get('role') == role:
                content = msg.get('content', '').lower()
                # Remove punctuation and split into words
                words = re.findall(r'\b\w+\b', content)
                unique_words.update(words)

        return len(unique_words)

    @staticmethod
    def calculate_conversation_turns(messages: List[Dict[str, Any]]) -> int:
        """
        Calculate number of conversation turns (exchanges)
        A turn is counted when role changes from one message to next

        Args:
            messages: List of conversation messages

        Returns:
            Number of conversation turns
        """
        if not messages:
            return 0

        turns = 1  # First message is a turn
        prev_role = messages[0].get('role')

        for msg in messages[1:]:
            current_role = msg.get('role')
            if current_role != prev_role:
                turns += 1
                prev_role = current_role

        return turns

    @staticmethod
    def extract_quality_scores(background_analyses: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        """
        Extract grammar, pronunciation, and fluency scores from background analyses

        Args:
            background_analyses: List of sentence analysis results

        Returns:
            Dict with grammar_score, pronunciation_score, fluency_score (averaged)
        """
        grammar_scores = []
        pronunciation_scores = []
        fluency_scores = []

        for analysis in background_analyses:
            # Extract scores if available
            if 'grammar_score' in analysis and analysis['grammar_score'] is not None:
                grammar_scores.append(analysis['grammar_score'])

            if 'pronunciation_score' in analysis and analysis['pronunciation_score'] is not None:
                pronunciation_scores.append(analysis['pronunciation_score'])

            if 'fluency_score' in analysis and analysis['fluency_score'] is not None:
                fluency_scores.append(analysis['fluency_score'])

        # Calculate averages
        result = {
            'grammar_score': round(sum(grammar_scores) / len(grammar_scores), 1) if grammar_scores else None,
            'pronunciation_score': round(sum(pronunciation_scores) / len(pronunciation_scores), 1) if pronunciation_scores else None,
            'fluency_score': round(sum(fluency_scores) / len(fluency_scores), 1) if fluency_scores else None,
        }

        return result

    @staticmethod
    def calculate_session_stats(
        messages: List[Dict[str, Any]],
        duration_minutes: float,
        background_analyses: Optional[List[Dict[str, Any]]] = None,
        session_number: Optional[int] = None,
        week_number: Optional[int] = None,
        week_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive session statistics

        Args:
            messages: List of conversation messages
            duration_minutes: Session duration in minutes
            background_analyses: Optional list of sentence analyses
            session_number: Optional session number (for learning plans)
            week_number: Optional week number (for learning plans)
            week_focus: Optional week focus (for learning plans)

        Returns:
            Dict containing all session statistics
        """
        # Calculate core metrics
        words_spoken = SessionStatistics.calculate_words_spoken(messages, role='user')
        speaking_speed_wpm = SessionStatistics.calculate_speaking_speed(words_spoken, duration_minutes)
        unique_vocabulary = SessionStatistics.calculate_unique_vocabulary(messages, role='user')
        conversation_turns = SessionStatistics.calculate_conversation_turns(messages)

        # Count messages
        user_messages = [m for m in messages if m.get('role') == 'user']
        total_messages = len(messages)
        user_message_count = len(user_messages)

        # Build stats dict
        stats = {
            'words_spoken': words_spoken,
            'speaking_speed_wpm': speaking_speed_wpm,
            'unique_vocabulary': unique_vocabulary,
            'conversation_turns': conversation_turns,
            'duration_minutes': round(duration_minutes, 2),
            'message_count': total_messages,
            'user_message_count': user_message_count,
        }

        # Add quality scores if analyses available
        if background_analyses:
            quality_scores = SessionStatistics.extract_quality_scores(background_analyses)
            stats.update(quality_scores)

        # Add learning plan specific fields
        if session_number is not None:
            stats['session_number'] = session_number
        if week_number is not None:
            stats['week_number'] = week_number
        if week_focus is not None:
            stats['week_focus'] = week_focus

        return stats

    @staticmethod
    def calculate_comparison(
        current_stats: Dict[str, Any],
        previous_session: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comparison between current and previous session

        Args:
            current_stats: Current session statistics
            previous_session: Previous session data (messages, duration, etc.)

        Returns:
            Dict containing comparison metrics
        """
        if not previous_session:
            return {
                'has_previous_session': False
            }

        # Calculate previous session stats
        previous_messages = previous_session.get('messages', [])
        previous_duration = previous_session.get('duration_minutes', 0)

        if not previous_messages or previous_duration <= 0:
            return {
                'has_previous_session': False
            }

        previous_words = SessionStatistics.calculate_words_spoken(previous_messages, role='user')
        previous_speed = SessionStatistics.calculate_speaking_speed(previous_words, previous_duration)
        previous_vocabulary = SessionStatistics.calculate_unique_vocabulary(previous_messages, role='user')

        # Calculate improvements
        words_improvement = current_stats['words_spoken'] - previous_words
        speed_improvement = current_stats['speaking_speed_wpm'] - previous_speed
        vocabulary_growth = current_stats['unique_vocabulary'] - previous_vocabulary

        # Calculate percentage improvements
        words_improvement_percent = (words_improvement / previous_words * 100) if previous_words > 0 else 0
        speed_improvement_percent = (speed_improvement / previous_speed * 100) if previous_speed > 0 else 0
        vocabulary_growth_percent = (vocabulary_growth / previous_vocabulary * 100) if previous_vocabulary > 0 else 0

        comparison = {
            'has_previous_session': True,
            'words_improvement': words_improvement,
            'words_improvement_percent': round(words_improvement_percent, 1),
            'speed_improvement': round(speed_improvement, 1),
            'speed_improvement_percent': round(speed_improvement_percent, 1),
            'vocabulary_growth': vocabulary_growth,
            'vocabulary_growth_percent': round(vocabulary_growth_percent, 1),
        }

        return comparison

    @staticmethod
    def get_overall_progress(
        user_id: str,
        total_sessions: int,
        total_minutes: float,
        current_streak: int,
        longest_streak: int,
        sessions_this_week: int,
        sessions_this_month: int,
        plan_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format overall progress statistics

        Args:
            user_id: User ID
            total_sessions: Total sessions completed
            total_minutes: Total minutes practiced
            current_streak: Current streak in days
            longest_streak: Longest streak ever
            sessions_this_week: Sessions completed this week
            sessions_this_month: Sessions completed this month
            plan_data: Optional learning plan data

        Returns:
            Dict containing overall progress metrics
        """
        progress = {
            'total_sessions': total_sessions,
            'total_minutes': round(total_minutes, 1),
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'sessions_this_week': sessions_this_week,
            'sessions_this_month': sessions_this_month,
        }

        # Add learning plan progress if applicable
        if plan_data:
            progress['plan_progress_percentage'] = round(plan_data.get('progress_percentage', 0), 1)
            progress['plan_completed_sessions'] = plan_data.get('completed_sessions', 0)
            progress['plan_total_sessions'] = plan_data.get('total_sessions', 0)

        return progress
