#!/usr/bin/env python3
"""
LEARNING PLAN FINAL ASSESSMENT SERVICE
=======================================

Handles final assessment requirements for learning plans.

Key Features:
- Check if user needs final assessment
- Get assessment requirements (duration, focus areas)
- Evaluate assessment (dual criteria: current mastery + next level readiness)
- Record assessment attempts
- Generate next level plan suggestions
- Finalize plan completion

IMPORTANT: Final assessments DO NOT count toward subscription limits (unlimited).
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId
from database import database

logger = logging.getLogger(__name__)

class LearningPlanFinalAssessmentService:
    """Service for managing final assessments for learning plans"""

    @classmethod
    async def check_final_assessment_required(
        cls,
        user_id: str,
        learning_plan_id: str
    ) -> Dict[str, Any]:
        """
        Check if user needs to take final assessment for their learning plan.

        Returns:
            {
                "required": bool,
                "status": str,  # "in_progress" | "awaiting_final_assessment" | "completed"
                "all_sessions_completed": bool,
                "last_attempt": dict or None,
                "can_retry": bool,
                "message": str
            }
        """
        try:
            logger.info(f"[FINAL_ASSESSMENT] Checking if assessment required for plan {learning_plan_id}, user {user_id}")

            # Get learning plan
            plan = await database["learning_plans"].find_one({
                "id": learning_plan_id,
                "user_id": user_id
            })

            if not plan:
                return {
                    "required": False,
                    "error": "Learning plan not found",
                    "status": "not_found"
                }

            status = plan.get("status", "in_progress")
            final_assessment = plan.get("final_assessment", {})
            completed_sessions = plan.get("completed_sessions", 0)
            total_sessions = plan.get("total_sessions", 0)

            # Check if all sessions are completed
            all_sessions_completed = completed_sessions >= total_sessions

            # Get last attempt if exists
            attempts = final_assessment.get("attempts", [])
            last_attempt = attempts[-1] if attempts else None

            # Determine if assessment is required
            assessment_required = (
                status == "awaiting_final_assessment" or
                (all_sessions_completed and not final_assessment.get("passed", False))
            )

            # Determine if user can retry
            can_retry = (
                assessment_required and
                last_attempt is not None and
                not last_attempt.get("passed", False)
            )

            # Generate message
            if status == "completed" and final_assessment.get("passed", False):
                message = "Learning plan completed! Final assessment passed."
            elif status == "awaiting_final_assessment":
                if last_attempt:
                    message = f"Please retry your final assessment (Last score: {last_attempt.get('overall_score', 0)}/100)"
                else:
                    message = "All sessions completed! Please take your final assessment to complete this plan."
            elif status == "failed_assessment":
                message = "Final assessment not yet passed. You can retry anytime or practice more."
            elif all_sessions_completed:
                message = "All sessions completed! Final assessment required."
            else:
                message = f"Keep going! {completed_sessions}/{total_sessions} sessions completed."

            return {
                "required": assessment_required,
                "status": status,
                "all_sessions_completed": all_sessions_completed,
                "completed_sessions": completed_sessions,
                "total_sessions": total_sessions,
                "last_attempt": last_attempt,
                "can_retry": can_retry,
                "attempts_count": len(attempts),
                "passed": final_assessment.get("passed", False),
                "message": message
            }

        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT] Error checking assessment requirement: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "required": False,
                "error": str(e),
                "status": "error"
            }

    @classmethod
    async def get_assessment_requirements(
        cls,
        learning_plan_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get the assessment requirements for a learning plan.

        Returns assessment duration, focus areas, and prompts based on:
        - Current proficiency level
        - Learning plan goals
        - Topics covered in the plan
        """
        try:
            logger.info(f"[FINAL_ASSESSMENT] Getting assessment requirements for plan {learning_plan_id}")

            # Get learning plan
            plan = await database["learning_plans"].find_one({
                "id": learning_plan_id,
                "user_id": user_id
            })

            if not plan:
                return {"error": "Learning plan not found"}

            level = plan.get("proficiency_level", "A1").upper()
            language = plan.get("language", "english")
            goals = plan.get("goals", [])
            plan_content = plan.get("plan_content", {})
            final_assessment = plan.get("final_assessment", {})

            # Calculate required duration based on level
            duration_map = {
                'A1': 2,
                'A2': 3,
                'B1': 4,
                'B2': 5,
                'C1': 5,
                'C2': 5
            }
            minimum_duration_minutes = duration_map.get(level, 3)

            # Extract focus areas from plan
            focus_areas = []
            weekly_schedule = plan_content.get("weekly_schedule", [])
            for week in weekly_schedule:
                focus = week.get("focus", "")
                if focus and focus not in focus_areas:
                    focus_areas.append(focus)

            # Get next level for readiness assessment
            next_level = cls._get_next_level(level)

            return {
                "learning_plan_id": learning_plan_id,
                "language": language,
                "current_level": level,
                "next_level": next_level,
                "minimum_duration_minutes": minimum_duration_minutes,
                "goals": goals,
                "focus_areas": focus_areas[:5],  # Limit to top 5 focus areas
                "assessment_type": "hybrid",  # Tests both learned topics and next level scenarios
                "instructions": cls._get_assessment_instructions(language, level, next_level),
                "attempts_made": len(final_assessment.get("attempts", []))
            }

        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT] Error getting assessment requirements: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    @classmethod
    def _get_next_level(cls, current_level: str) -> str:
        """Get the next proficiency level"""
        level_progression = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        try:
            current_index = level_progression.index(current_level.upper())
            if current_index < len(level_progression) - 1:
                return level_progression[current_index + 1]
            return current_level  # Already at highest level
        except ValueError:
            return 'A2'  # Default if unknown level

    @classmethod
    def _get_assessment_instructions(cls, language: str, current_level: str, next_level: str) -> str:
        """Generate assessment instructions"""
        return f"""
This is your final assessment for {language.title()} {current_level} level.

The assessment will evaluate:
1. Your mastery of {current_level} level concepts
2. Your readiness to advance to {next_level} level

Speak naturally for the required duration. You'll be evaluated on:
- Pronunciation
- Grammar accuracy
- Vocabulary range
- Fluency and coherence
- Appropriateness to level

Good luck!
        """.strip()

    @classmethod
    async def evaluate_final_assessment(
        cls,
        user_id: str,
        learning_plan_id: str,
        assessment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate final assessment with dual criteria:
        1. Current level mastery (must pass)
        2. Next level readiness (must pass)

        Both must pass for user to advance to next level.

        Returns:
            {
                "passed": bool,
                "current_level_mastery": {"score": int, "passed": bool, "feedback": str},
                "next_level_readiness": {"score": int, "passed": bool, "feedback": str},
                "overall_score": int,
                "recommendation": str,  # "advance" or "practice_more"
                "detailed_evaluation": dict
            }
        """
        try:
            logger.info(f"[FINAL_ASSESSMENT] Evaluating assessment for plan {learning_plan_id}, user {user_id}")

            # Get learning plan
            plan = await database["learning_plans"].find_one({
                "id": learning_plan_id,
                "user_id": user_id
            })

            if not plan:
                return {"error": "Learning plan not found"}

            current_level = plan.get("proficiency_level", "A1").upper()
            next_level = cls._get_next_level(current_level)

            # Extract assessment results
            overall_score = assessment_data.get("overall_score", 0)
            skills = {
                "pronunciation": assessment_data.get("pronunciation", {}).get("score", 0),
                "grammar": assessment_data.get("grammar", {}).get("score", 0),
                "vocabulary": assessment_data.get("vocabulary", {}).get("score", 0),
                "fluency": assessment_data.get("fluency", {}).get("score", 0),
                "coherence": assessment_data.get("coherence", {}).get("score", 0)
            }

            # Evaluate current level mastery
            # User must demonstrate solid mastery of current level (>= 75)
            current_level_mastery_score = cls._calculate_current_level_mastery(skills, overall_score)
            current_level_passed = current_level_mastery_score >= 75

            # Evaluate next level readiness
            # User must show readiness for next level concepts (>= 70)
            next_level_readiness_score = cls._calculate_next_level_readiness(skills, overall_score, current_level, next_level)
            next_level_passed = next_level_readiness_score >= 70

            # Both must pass
            assessment_passed = current_level_passed and next_level_passed

            # Generate feedback
            current_level_feedback = cls._generate_mastery_feedback(
                current_level,
                current_level_mastery_score,
                current_level_passed,
                skills
            )

            next_level_feedback = cls._generate_readiness_feedback(
                next_level,
                next_level_readiness_score,
                next_level_passed,
                skills
            )

            # Overall recommendation
            if assessment_passed:
                recommendation = "advance"
                message = f"Congratulations! You've demonstrated mastery of {current_level} and readiness for {next_level}."
            else:
                recommendation = "practice_more"
                if not current_level_passed:
                    message = f"You need more practice with {current_level} level concepts before advancing."
                else:
                    message = f"You've mastered {current_level}, but need more preparation for {next_level} level."

            return {
                "passed": assessment_passed,
                "current_level": current_level,
                "next_level": next_level,
                "overall_score": overall_score,
                "current_level_mastery": {
                    "score": current_level_mastery_score,
                    "passed": current_level_passed,
                    "feedback": current_level_feedback,
                    "threshold": 75
                },
                "next_level_readiness": {
                    "score": next_level_readiness_score,
                    "passed": next_level_passed,
                    "feedback": next_level_feedback,
                    "threshold": 70
                },
                "skills": skills,
                "recommendation": recommendation,
                "message": message,
                "strengths": assessment_data.get("strengths", []),
                "areas_for_improvement": assessment_data.get("areas_for_improvement", []),
                "next_steps": assessment_data.get("next_steps", [])
            }

        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT] Error evaluating assessment: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    @classmethod
    def _calculate_current_level_mastery(cls, skills: Dict[str, int], overall_score: int) -> int:
        """
        Calculate current level mastery score.
        Weighted more heavily on grammar, vocabulary, and overall performance.
        """
        # Weight grammar and vocabulary more heavily
        mastery_score = (
            skills["grammar"] * 0.3 +
            skills["vocabulary"] * 0.3 +
            skills["fluency"] * 0.15 +
            skills["pronunciation"] * 0.1 +
            skills["coherence"] * 0.15
        )
        # Blend with overall score
        final_score = (mastery_score * 0.7) + (overall_score * 0.3)
        return int(round(final_score))

    @classmethod
    def _calculate_next_level_readiness(
        cls,
        skills: Dict[str, int],
        overall_score: int,
        current_level: str,
        next_level: str
    ) -> int:
        """
        Calculate readiness for next level.
        Considers if user is pushing boundaries of current level.
        """
        # Readiness is based on whether skills exceed current level expectations
        # and show emerging next-level capabilities
        readiness_score = (
            skills["grammar"] * 0.25 +
            skills["vocabulary"] * 0.25 +
            skills["fluency"] * 0.2 +
            skills["coherence"] * 0.2 +
            skills["pronunciation"] * 0.1
        )
        # Slightly lower threshold - we're looking for potential, not perfection
        final_score = (readiness_score * 0.6) + (overall_score * 0.4)
        return int(round(final_score))

    @classmethod
    def _generate_mastery_feedback(
        cls,
        level: str,
        score: int,
        passed: bool,
        skills: Dict[str, int]
    ) -> str:
        """Generate feedback for current level mastery"""
        if passed:
            return f"Excellent! You've demonstrated strong mastery of {level} level skills (Score: {score}/100). Your grammar and vocabulary usage are consistent with {level} expectations."
        else:
            weak_areas = [k for k, v in skills.items() if v < 70]
            return f"Your {level} level mastery needs improvement (Score: {score}/100). Focus on: {', '.join(weak_areas)}."

    @classmethod
    def _generate_readiness_feedback(
        cls,
        next_level: str,
        score: int,
        passed: bool,
        skills: Dict[str, int]
    ) -> str:
        """Generate feedback for next level readiness"""
        if passed:
            return f"Great! You're showing readiness for {next_level} level concepts (Score: {score}/100). You demonstrate emerging skills appropriate for the next level."
        else:
            return f"You need more preparation for {next_level} level (Score: {score}/100). Continue practicing at your current level to build a stronger foundation."

    @classmethod
    async def record_assessment_attempt(
        cls,
        user_id: str,
        learning_plan_id: str,
        assessment_data: Dict[str, Any],
        evaluation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record an assessment attempt in the learning plan.

        Updates the learning plan status based on pass/fail.
        """
        try:
            logger.info(f"[FINAL_ASSESSMENT] Recording assessment attempt for plan {learning_plan_id}")

            # Get current plan
            plan = await database["learning_plans"].find_one({
                "id": learning_plan_id,
                "user_id": user_id
            })

            if not plan:
                return {"success": False, "error": "Learning plan not found"}

            # Get existing attempts
            final_assessment = plan.get("final_assessment", {})
            attempts = final_assessment.get("attempts", [])

            # Create attempt record
            attempt_number = len(attempts) + 1
            attempt = {
                "attempt_number": attempt_number,
                "taken_at": datetime.utcnow().isoformat(),
                "duration_minutes": assessment_data.get("duration", 0) / 60,  # Convert seconds to minutes
                "recognized_text": assessment_data.get("recognized_text", ""),
                "overall_score": evaluation_result.get("overall_score", 0),
                "passed": evaluation_result.get("passed", False),
                "current_level_mastery": evaluation_result.get("current_level_mastery", {}),
                "next_level_readiness": evaluation_result.get("next_level_readiness", {}),
                "skills": evaluation_result.get("skills", {}),
                "recommendation": evaluation_result.get("recommendation", "practice_more"),
                "strengths": evaluation_result.get("strengths", []),
                "areas_for_improvement": evaluation_result.get("areas_for_improvement", [])
            }

            attempts.append(attempt)

            # Update status based on result
            if evaluation_result.get("passed", False):
                new_status = "completed"
                final_assessment["passed"] = True
                final_assessment["completed"] = True
            else:
                new_status = "failed_assessment"
                final_assessment["passed"] = False
                final_assessment["completed"] = False

            final_assessment["attempts"] = attempts
            final_assessment["last_attempt_date"] = datetime.utcnow().isoformat()

            # Update database
            result = await database["learning_plans"].update_one(
                {"_id": plan["_id"]},
                {
                    "$set": {
                        "status": new_status,
                        "final_assessment": final_assessment,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"[FINAL_ASSESSMENT] ✅ Recorded attempt #{attempt_number}, status: {new_status}")
                return {
                    "success": True,
                    "attempt_number": attempt_number,
                    "status": new_status,
                    "passed": evaluation_result.get("passed", False)
                }
            else:
                logger.error(f"[FINAL_ASSESSMENT] ❌ Failed to update learning plan")
                return {"success": False, "error": "Failed to update learning plan"}

        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT] Error recording assessment attempt: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    @classmethod
    async def generate_next_level_plan_suggestion(
        cls,
        user_id: str,
        current_plan_id: str
    ) -> Dict[str, Any]:
        """
        Auto-generate a suggested learning plan for the next level.
        User can review and customize before confirming.
        """
        try:
            logger.info(f"[FINAL_ASSESSMENT] Generating next level plan suggestion for user {user_id}")

            # Get current plan
            current_plan = await database["learning_plans"].find_one({
                "id": current_plan_id,
                "user_id": user_id
            })

            if not current_plan:
                return {"error": "Current learning plan not found"}

            # Extract plan details
            language = current_plan.get("language", "english")
            current_level = current_plan.get("proficiency_level", "A1")
            next_level = cls._get_next_level(current_level)
            goals = current_plan.get("goals", [])
            duration_months = current_plan.get("duration_months", 2)

            # Get last assessment data for personalization
            final_assessment = current_plan.get("final_assessment", {})
            last_attempt = final_assessment.get("attempts", [])[-1] if final_assessment.get("attempts") else None

            # Extract areas for improvement from last assessment
            areas_for_improvement = []
            if last_attempt:
                areas_for_improvement = last_attempt.get("areas_for_improvement", [])

            # Create suggestion
            suggestion = {
                "suggested": True,
                "based_on_plan": current_plan_id,
                "language": language,
                "proficiency_level": next_level,
                "previous_level": current_level,
                "goals": goals,  # Keep same goals
                "duration_months": duration_months,  # Keep same duration
                "focus_areas": areas_for_improvement[:3] if areas_for_improvement else [],
                "customizable": True,
                "message": f"Based on your {current_level} plan, here's a suggested plan for {next_level} level. You can customize it before confirming."
            }

            logger.info(f"[FINAL_ASSESSMENT] ✅ Generated suggestion for {next_level} level")
            return suggestion

        except Exception as e:
            logger.error(f"[FINAL_ASSESSMENT] Error generating next level plan: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
