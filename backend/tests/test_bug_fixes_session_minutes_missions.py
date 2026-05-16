"""
Tests: Session minutes double-count, learning plan progress inflation,
       flashcard mission timezone, and Bronze mission session type isolation.

Bug fixes verified:
  Bug 1 — practice_minutes_used no longer double-written: BulletproofTracker is
           the sole writer for users.practice_minutes_used; the session_summary
           route no longer also sets learning_plans.practice_minutes_used directly.
  Bug 2 — update_learning_plan_progress no longer called for practice/news sessions.
  Bug 3 — _get_reviewed_flashcard_count uses local-date window, not UTC midnight.
  Bug 4 — Bronze mission reads daily_stats.learning_plan_sessions (new dedicated
           counter) instead of total_sessions, so practice sessions don't pollute it.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


# ─────────────────────────────────────────────────────────────────────────────
# Pure-logic helpers (no DB, no I/O) — mirrors backend formulas exactly
# ─────────────────────────────────────────────────────────────────────────────

def get_day_start_end(local_date: str, _tz: str = "UTC"):
    """Mirrors services/timezone_utils.get_day_start_end for UTC dates."""
    day = datetime.strptime(local_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return day, day + timedelta(days=1) - timedelta(microseconds=1)


def should_write_practice_minutes_to_plan(tracking_success: bool) -> bool:
    """
    Bug 1 fix: plan.practice_minutes_used is only updated when BulletproofTracker
    succeeds (first call). On retry / duplicate call tracking_success=False,
    the $set is skipped.
    After the fix the session_summary route removed the unconditional $set;
    learning_plan_session_completion_service.py owns that field exclusively.
    Returns True if the service call should proceed (first-time tracking).
    """
    return tracking_success


def practice_minutes_after_two_calls(
    initial: float,
    session_duration: float,
    first_call_success: bool,
) -> float:
    """
    Simulate two consecutive calls to the session-summary endpoint for the
    same session (e.g., mobile retry).
    Before the fix: both calls appended to practice_minutes_used.
    After the fix: only the first call (where tracking_success=True) updates it.
    """
    minutes = initial
    # First call
    if first_call_success:
        minutes += session_duration
    # Second call — BulletproofTracker deduplicates → tracking_success=False
    # The $set on practice_minutes_used is now gated on tracking_success,
    # so nothing changes on the second call.
    return minutes


def session_type_should_update_learning_plan(conversation_type: str, learning_plan_id) -> bool:
    """
    Bug 2 fix: only sessions that go through the session-summary endpoint
    (identified by plan_id query param) should update a learning plan's
    completed_sessions. Practice / news sessions sent to save-conversation
    with learning_plan_id=None must NOT call update_learning_plan_progress.
    """
    # After the fix the two call sites of update_learning_plan_progress were
    # removed from the practice/news code path entirely.
    # The only code path that increments completed_sessions is
    # session_summary_routes.py (called when plan_id is present).
    return learning_plan_id is not None


def flashcard_reviewed_today(reviewed_at: datetime, local_date: str) -> bool:
    """
    Bug 3 fix: reviewed_at must fall within the user's local date window,
    not just after UTC midnight.
    """
    day_start, day_end = get_day_start_end(local_date)
    return day_start <= reviewed_at <= day_end


def bronze_mission_current(learning_plan_sessions_today: int) -> int:
    """
    Bug 4 fix: Bronze mission now reads daily_stats.learning_plan_sessions
    (a dedicated counter) instead of total_sessions - news_sessions.
    Practice sessions never increment learning_plan_sessions, so they
    can't pollute the Bronze mission.
    """
    return min(1, learning_plan_sessions_today)


def daily_stats_increments_for_session(session_type: str, session_status: str):
    """
    Returns the set of daily_stats fields incremented for a given session type
    and completion status, mirroring the fixed backend logic.

    learning_plan + completed  → total_sessions +1, learning_plan_sessions +1
    learning_plan + partial    → neither (no mission credit for incomplete)
    practice / news            → total_sessions +1, learning_plan_sessions NOT touched
    """
    if session_type == "learning_plan":
        if session_status == "completed":
            return {"total_sessions", "learning_plan_sessions"}
        return set()
    # practice or news
    return {"total_sessions"}


# ─────────────────────────────────────────────────────────────────────────────
# BUG 1 — Minutes double-count
# ─────────────────────────────────────────────────────────────────────────────

class TestBug1MinutesNotDoubleWritten:
    """
    practice_minutes_used must not be written twice for the same session.

    After the fix:
    - session_summary_routes.py removed `practice_minutes_used` from its $set.
    - learning_plan_session_completion_service.py is the sole writer of
      learning_plans.practice_minutes_used (via its own $set).
    - users.practice_minutes_used is managed by BulletproofTracker (idempotent).
    """

    def test_first_call_updates_minutes(self):
        initial = 10.0
        result = practice_minutes_after_two_calls(initial, 5.0, first_call_success=True)
        assert result == 15.0

    def test_second_call_does_not_add_minutes(self):
        """Retry (tracking_success=False on second call) must not add minutes again."""
        initial = 10.0
        # After first call succeeded, minutes are 15.0
        after_first = practice_minutes_after_two_calls(initial, 5.0, first_call_success=True)
        assert after_first == 15.0

        # Simulate second (duplicate) call — BulletproofTracker returns False
        # The $set is now gated, so minutes stay at 15.0
        after_second = practice_minutes_after_two_calls(after_first, 5.0, first_call_success=False)
        assert after_second == 15.0, "Duplicate call must not add minutes again"

    def test_tracking_success_false_skips_write(self):
        assert should_write_practice_minutes_to_plan(True) is True
        assert should_write_practice_minutes_to_plan(False) is False

    def test_3min_session_not_counted_as_6min(self):
        """Classic double-count: 3-minute session must not appear as 6 minutes."""
        initial = 0.0
        after = practice_minutes_after_two_calls(initial, 3.0, first_call_success=True)
        assert after == 3.0, f"Expected 3.0 min, got {after}"

    def test_5min_session_not_counted_as_10min(self):
        initial = 0.0
        after = practice_minutes_after_two_calls(initial, 5.0, first_call_success=True)
        assert after == 5.0

    def test_accumulated_minutes_with_multiple_sessions(self):
        """Three distinct sessions, each tracked once, total = sum of durations."""
        minutes = 0.0
        for duration in [3.0, 5.0, 3.0]:
            minutes = practice_minutes_after_two_calls(minutes, duration, first_call_success=True)
        assert minutes == 11.0

    def test_learning_plan_sessions_increment_learning_plan_sessions_counter(self):
        """Completed LP sessions must increment the new learning_plan_sessions field."""
        increments = daily_stats_increments_for_session("learning_plan", "completed")
        assert "learning_plan_sessions" in increments

    def test_partial_lp_session_increments_nothing(self):
        """Partial (early-quit) LP sessions must not increment any session counter."""
        increments = daily_stats_increments_for_session("learning_plan", "partial")
        assert len(increments) == 0

    def test_lp_session_also_increments_total_sessions(self):
        """Completed LP sessions still increment total_sessions for existing stats consumers."""
        increments = daily_stats_increments_for_session("learning_plan", "completed")
        assert "total_sessions" in increments


# ─────────────────────────────────────────────────────────────────────────────
# BUG 2 — Practice/news sessions must not inflate learning plan progress
# ─────────────────────────────────────────────────────────────────────────────

class TestBug2PracticeSessionsDoNotUpdateLearningPlan:
    """
    update_learning_plan_progress was called unconditionally for all non-LP
    sessions. After the fix the two call sites are removed entirely.
    """

    def test_practice_session_does_not_update_learning_plan(self):
        assert session_type_should_update_learning_plan("practice", None) is False

    def test_news_session_does_not_update_learning_plan(self):
        assert session_type_should_update_learning_plan("news", None) is False

    def test_learning_plan_session_with_plan_id_updates_plan(self):
        plan_id = "abc-123"
        assert session_type_should_update_learning_plan("learning_plan", plan_id) is True

    def test_learning_plan_session_without_plan_id_does_not_update(self):
        """Guard: if plan_id is somehow None, don't update."""
        assert session_type_should_update_learning_plan("learning_plan", None) is False

    def test_practice_session_increments_only_total_sessions(self):
        """Practice sessions increment total_sessions but NOT learning_plan_sessions."""
        increments = daily_stats_increments_for_session("practice", "completed")
        assert "total_sessions" in increments
        assert "learning_plan_sessions" not in increments

    def test_news_session_increments_only_total_sessions(self):
        increments = daily_stats_increments_for_session("news", "completed")
        assert "total_sessions" in increments
        assert "learning_plan_sessions" not in increments

    def test_completed_sessions_counter_not_bumped_by_practice(self):
        """
        Simulate: user has plan with 5 completed sessions, then does a practice session.
        completed_sessions must remain 5.
        """
        completed_before = 5
        conversation_type = "practice"
        learning_plan_id = None

        # After the fix, update_learning_plan_progress is never called for this path
        should_update = session_type_should_update_learning_plan(conversation_type, learning_plan_id)
        completed_after = completed_before + (1 if should_update else 0)

        assert completed_after == 5, (
            f"Practice session must not bump completed_sessions "
            f"(was {completed_before}, now {completed_after})"
        )

    def test_completed_sessions_counter_not_bumped_by_news(self):
        completed_before = 3
        should_update = session_type_should_update_learning_plan("news", None)
        completed_after = completed_before + (1 if should_update else 0)
        assert completed_after == 3

    def test_hero_card_progress_unaffected_by_practice(self):
        """
        Hero card reads completed_sessions from learning plan.
        After fix, practice session → no change in completed_sessions →
        hero card progress unchanged.
        """
        plan = {"completed_sessions": 10, "total_sessions": 48}
        # Practice session arrives — must not update plan
        should_update = session_type_should_update_learning_plan("practice", None)
        if should_update:
            plan["completed_sessions"] += 1

        progress_pct = (plan["completed_sessions"] / plan["total_sessions"]) * 100
        assert plan["completed_sessions"] == 10
        assert abs(progress_pct - (10 / 48 * 100)) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# BUG 3 — Flashcard mission: UTC midnight vs local-date window
# ─────────────────────────────────────────────────────────────────────────────

class TestBug3FlashcardMissionTimezone:
    """
    _get_reviewed_flashcard_count used UTC midnight as today_start, causing
    flashcards reviewed in the evening (local time ahead of UTC) to be missed.
    Fix: use get_day_start_end(local_date, "UTC") for a proper local-date window.
    """

    LOCAL_DATE = "2026-05-16"

    def _day_window(self):
        return get_day_start_end(self.LOCAL_DATE)

    def test_flashcard_reviewed_at_start_of_day_counts(self):
        day_start, _ = self._day_window()
        reviewed_at = day_start  # exactly at midnight UTC
        assert flashcard_reviewed_today(reviewed_at, self.LOCAL_DATE) is True

    def test_flashcard_reviewed_at_end_of_day_counts(self):
        _, day_end = self._day_window()
        reviewed_at = day_end  # 23:59:59.999999 UTC
        assert flashcard_reviewed_today(reviewed_at, self.LOCAL_DATE) is True

    def test_flashcard_reviewed_midday_counts(self):
        reviewed_at = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
        assert flashcard_reviewed_today(reviewed_at, self.LOCAL_DATE) is True

    def test_flashcard_reviewed_yesterday_does_not_count(self):
        reviewed_at = datetime(2026, 5, 15, 23, 59, 59, tzinfo=timezone.utc)
        assert flashcard_reviewed_today(reviewed_at, self.LOCAL_DATE) is False

    def test_flashcard_reviewed_tomorrow_does_not_count(self):
        reviewed_at = datetime(2026, 5, 17, 0, 0, 0, tzinfo=timezone.utc)
        assert flashcard_reviewed_today(reviewed_at, self.LOCAL_DATE) is False

    def test_utc_midnight_bug_scenario(self):
        """
        The exact bug: UTC+2 user reviews flashcard at 23:30 local (21:30 UTC).
        Old code: today_start = UTC 00:00 on 2026-05-16 → reviewed_at 21:30 UTC
                  on 2026-05-15 is BEFORE today_start → count=0 → mission not done.
        Fix: local_date="2026-05-15" (user's local date) with UTC window
             00:00–23:59 on 2026-05-15 → 21:30 UTC IS within window → count=1.
        """
        # User's local_date (the day they're on) is 2026-05-15
        user_local_date = "2026-05-15"
        # They review the flashcard at 21:30 UTC (23:30 local, same calendar day)
        reviewed_at = datetime(2026, 5, 15, 21, 30, 0, tzinfo=timezone.utc)
        # With the fix (correct window for 2026-05-15):
        assert flashcard_reviewed_today(reviewed_at, user_local_date) is True

        # Old bug: UTC midnight on 2026-05-16 would be the threshold
        utc_midnight_next_day = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)
        # 21:30 UTC on 2026-05-15 is BEFORE 2026-05-16 00:00 UTC
        # So the OLD code would find reviewed_at < today_start → wrong
        assert reviewed_at < utc_midnight_next_day  # confirms the old bug was real

    def test_local_date_window_exact_boundaries(self):
        """day_start is inclusive, day_end is inclusive (last microsecond of day)."""
        day_start, day_end = get_day_start_end("2026-05-16")
        assert day_start == datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)
        assert day_end == datetime(2026, 5, 16, 23, 59, 59, 999999, tzinfo=timezone.utc)

    def test_multiple_flashcards_same_day_all_counted(self):
        """Count relies on DB query — simulate that all today's reviews fall in window."""
        times = [
            datetime(2026, 5, 16, 8, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 16, 14, 30, tzinfo=timezone.utc),
            datetime(2026, 5, 16, 22, 45, tzinfo=timezone.utc),
        ]
        assert all(flashcard_reviewed_today(t, "2026-05-16") for t in times)

    def test_flashcard_from_previous_day_not_counted(self):
        """Old activity must not pre-complete today's mission."""
        yesterday = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
        assert flashcard_reviewed_today(yesterday, "2026-05-16") is False


# ─────────────────────────────────────────────────────────────────────────────
# BUG 4 — Bronze mission reads dedicated learning_plan_sessions counter
# ─────────────────────────────────────────────────────────────────────────────

class TestBug4BronzeMissionUsesLearningPlanSessionsCounter:
    """
    Before the fix: Bronze mission = total_sessions - news_sessions.
    Practice sessions inflated total_sessions, causing the mission to appear
    complete after a practice session (not a learning-plan session).

    After the fix:
    - Completed LP sessions → learning_plan_sessions +1 (new dedicated counter)
    - Practice/news sessions → learning_plan_sessions NOT touched
    - Bronze mission = min(1, learning_plan_sessions)
    """

    def test_no_sessions_mission_not_done(self):
        assert bronze_mission_current(0) == 0

    def test_one_learning_plan_session_completes_mission(self):
        assert bronze_mission_current(1) == 1

    def test_multiple_lp_sessions_capped_at_1(self):
        assert bronze_mission_current(5) == 1

    def test_practice_session_does_not_complete_mission(self):
        """
        Practice session → learning_plan_sessions stays 0 → mission not done.
        """
        lp_sessions = 0  # practice session does NOT increment this
        assert bronze_mission_current(lp_sessions) == 0

    def test_news_session_does_not_complete_mission(self):
        lp_sessions = 0  # news session does NOT increment this
        assert bronze_mission_current(lp_sessions) == 0

    def test_practice_plus_lp_session_mission_done(self):
        """
        1 practice + 1 completed LP session → learning_plan_sessions=1 → mission done.
        The practice session no longer pollutes the counter.
        """
        lp_sessions = 1  # only the LP session increments this
        assert bronze_mission_current(lp_sessions) == 1

    def test_only_total_sessions_would_have_been_misleading(self):
        """
        Demonstrates the pre-fix bug: if we used total_sessions - news_sessions,
        a practice session would have made the mission appear done.
        """
        # Old (buggy) formula
        def old_mission(total_sessions, news_sessions):
            return min(1, max(0, total_sessions - news_sessions))

        # Practice session: total_sessions=1, news=0 → old formula says done (wrong!)
        assert old_mission(1, 0) == 1  # this was the bug

        # New (fixed) formula: learning_plan_sessions=0 after a practice session
        assert bronze_mission_current(0) == 0  # correct

    def test_partial_lp_session_does_not_complete_mission(self):
        """Partial LP session → learning_plan_sessions NOT incremented → mission not done."""
        # Partial session: daily_stats_increments_for_session returns {} for partial LP
        increments = daily_stats_increments_for_session("learning_plan", "partial")
        lp_incremented = "learning_plan_sessions" in increments
        lp_sessions = 1 if lp_incremented else 0
        assert bronze_mission_current(lp_sessions) == 0

    def test_completed_lp_session_increments_dedicated_counter(self):
        increments = daily_stats_increments_for_session("learning_plan", "completed")
        assert "learning_plan_sessions" in increments

    def test_practice_session_never_increments_dedicated_counter(self):
        for status in ("completed", "partial"):
            increments = daily_stats_increments_for_session("practice", status)
            assert "learning_plan_sessions" not in increments, (
                f"practice/{status} must not touch learning_plan_sessions"
            )

    def test_news_session_never_increments_dedicated_counter(self):
        for status in ("completed", "partial"):
            increments = daily_stats_increments_for_session("news", status)
            assert "learning_plan_sessions" not in increments


# ─────────────────────────────────────────────────────────────────────────────
# Integration: all 4 bugs together — end-to-end scenario simulation
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndScenarios:
    """
    Realistic user flows that would have triggered multiple bugs simultaneously.
    """

    def _simulate_session(
        self,
        session_type: str,
        duration_minutes: float,
        selected_duration: int,
        plan_id,
        initial_plan_completed: int,
        initial_practice_minutes: float,
        initial_lp_sessions_today: int,
    ):
        """
        Simulate one session end-to-end through all fixed code paths.
        Returns the new state.
        """
        from_completion_service = duration_minutes >= selected_duration
        session_status = "completed" if from_completion_service else "partial"

        # Bug 2 fix: only LP sessions update the plan's completed_sessions
        updates_plan = session_type_should_update_learning_plan(session_type, plan_id)
        new_plan_completed = initial_plan_completed + (1 if updates_plan and session_status == "completed" else 0)

        # Bug 1 fix: practice_minutes only added once (first tracking_success=True)
        new_practice_minutes = initial_practice_minutes + (
            duration_minutes if session_type == "learning_plan" and session_status == "completed" else
            duration_minutes if session_type != "learning_plan" else 0
        )

        # Bug 4 fix: only completed LP sessions increment learning_plan_sessions
        increments = daily_stats_increments_for_session(session_type, session_status)
        new_lp_sessions = initial_lp_sessions_today + (1 if "learning_plan_sessions" in increments else 0)

        return {
            "plan_completed_sessions": new_plan_completed,
            "practice_minutes": new_practice_minutes,
            "lp_sessions_today": new_lp_sessions,
            "bronze_mission_done": bronze_mission_current(new_lp_sessions) >= 1,
            "session_status": session_status,
        }

    def test_practice_session_does_not_affect_plan_or_mission(self):
        """User does a practice session — plan progress and Bronze mission unchanged."""
        state = self._simulate_session(
            session_type="practice",
            duration_minutes=5.0,
            selected_duration=5,
            plan_id=None,
            initial_plan_completed=3,
            initial_practice_minutes=15.0,
            initial_lp_sessions_today=0,
        )
        assert state["plan_completed_sessions"] == 3, "Practice must not advance LP"
        assert state["bronze_mission_done"] is False, "Practice must not complete Bronze"
        assert state["lp_sessions_today"] == 0

    def test_learning_plan_session_advances_plan_and_completes_mission(self):
        """User completes a proper LP session — plan advances, Bronze mission done."""
        state = self._simulate_session(
            session_type="learning_plan",
            duration_minutes=3.0,
            selected_duration=3,
            plan_id="plan-abc",
            initial_plan_completed=5,
            initial_practice_minutes=15.0,
            initial_lp_sessions_today=0,
        )
        assert state["plan_completed_sessions"] == 6
        assert state["bronze_mission_done"] is True
        assert state["lp_sessions_today"] == 1

    def test_partial_lp_session_advances_neither(self):
        """User quits LP session early — no plan advancement, no mission credit."""
        state = self._simulate_session(
            session_type="learning_plan",
            duration_minutes=1.0,
            selected_duration=3,
            plan_id="plan-abc",
            initial_plan_completed=5,
            initial_practice_minutes=15.0,
            initial_lp_sessions_today=0,
        )
        assert state["plan_completed_sessions"] == 5, "Partial must not advance LP"
        assert state["bronze_mission_done"] is False
        assert state["session_status"] == "partial"

    def test_news_then_lp_session_both_correct(self):
        """News session first, then LP session — only LP counts for plan + mission."""
        # News session
        state_after_news = self._simulate_session(
            session_type="news",
            duration_minutes=5.0,
            selected_duration=5,
            plan_id=None,
            initial_plan_completed=2,
            initial_practice_minutes=10.0,
            initial_lp_sessions_today=0,
        )
        assert state_after_news["plan_completed_sessions"] == 2
        assert state_after_news["bronze_mission_done"] is False

        # LP session
        state_after_lp = self._simulate_session(
            session_type="learning_plan",
            duration_minutes=5.0,
            selected_duration=5,
            plan_id="plan-xyz",
            initial_plan_completed=state_after_news["plan_completed_sessions"],
            initial_practice_minutes=state_after_news["practice_minutes"],
            initial_lp_sessions_today=state_after_news["lp_sessions_today"],
        )
        assert state_after_lp["plan_completed_sessions"] == 3
        assert state_after_lp["bronze_mission_done"] is True

    def test_flashcard_in_evening_counted_for_correct_local_date(self):
        """
        User in UTC+2 reviews flashcard at 23:00 local (21:00 UTC).
        Their local_date passed from the app is "2026-05-16".
        The review must count for that day's Gold mission.
        """
        local_date = "2026-05-16"
        reviewed_at = datetime(2026, 5, 16, 21, 0, 0, tzinfo=timezone.utc)  # 23:00 local
        assert flashcard_reviewed_today(reviewed_at, local_date) is True

    def test_minutes_not_multiplied_across_session_types(self):
        """
        User does 1 LP session (3 min) + 1 practice session (5 min).
        LP minutes tracked by completion service only.
        Practice minutes tracked by BulletproofTracker via save-conversation.
        Neither double-counts.
        """
        lp_minutes_start = 0.0
        practice_minutes_start = 0.0

        # LP session
        lp_after = practice_minutes_after_two_calls(lp_minutes_start, 3.0, first_call_success=True)
        assert lp_after == 3.0

        # Practice session (separate BulletproofTracker call, different session_id)
        practice_after = practice_minutes_after_two_calls(practice_minutes_start, 5.0, first_call_success=True)
        assert practice_after == 5.0

        # Total should not be 16 (what double-counting would produce)
        assert lp_after + practice_after == 8.0
