"""
Learning Plan Optimizer Service

Automatically updates user's learning plan based on sentence analysis data
from completed sessions. Uses existing batched sentence analysis results
to identify patterns and adjust the learning plan progressively.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter
from bson import ObjectId


class LearningPlanOptimizer:
    """
    Analyzes sentence analysis results from sessions and updates learning plans
    to address specific issues, celebrate progress, and adapt to user's actual performance.
    """

    @staticmethod
    async def analyze_session_patterns(
        user_id: str,
        lookback_sessions: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze sentence analysis data from recent sessions to identify patterns.

        Args:
            user_id: User ID
            lookback_sessions: Number of recent sessions to analyze

        Returns:
            Pattern analysis with recurring issues, progress indicators, skill scores
        """
        from database import database

        # Fetch recent sessions with sentence analysis data
        sessions = await database.conversation_sessions.find(
            {
                "user_id": user_id,
                "sentence_analyses": {"$exists": True, "$ne": []}
            }
        ).sort("created_at", -1).limit(lookback_sessions).to_list(lookback_sessions)

        if not sessions or len(sessions) < 2:
            return {
                "insufficient_data": True,
                "sessions_analyzed": len(sessions),
                "message": "Need at least 2 sessions with sentence analysis"
            }

        # Aggregate all sentence analyses
        all_analyses = []
        for session in sessions:
            sentence_analyses = session.get("sentence_analyses", [])
            for analysis in sentence_analyses:
                all_analyses.append({
                    "session_date": session.get("created_at"),
                    **analysis
                })

        if len(all_analyses) < 5:
            return {
                "insufficient_data": True,
                "analyses_found": len(all_analyses),
                "message": "Need at least 5 sentence analyses"
            }

        # Extract grammar issue types
        grammar_issues_counter = Counter()
        improvement_suggestions_counter = Counter()

        for analysis in all_analyses:
            # Count grammar issue types
            for issue in analysis.get("grammar_issues", []):
                issue_type = issue.get("type", "unknown")
                grammar_issues_counter[issue_type] += 1

            # Count improvement suggestions
            for suggestion in analysis.get("improvement_suggestions", []):
                # Normalize suggestion for counting
                normalized = suggestion.lower().strip()
                improvement_suggestions_counter[normalized] += 1

        # Calculate average scores
        avg_grammar = sum(a.get("grammatical_score", 0) for a in all_analyses) / len(all_analyses)
        avg_vocabulary = sum(a.get("vocabulary_score", 0) for a in all_analyses) / len(all_analyses)
        avg_complexity = sum(a.get("complexity_score", 0) for a in all_analyses) / len(all_analyses)
        avg_appropriateness = sum(a.get("appropriateness_score", 0) for a in all_analyses) / len(all_analyses)
        avg_overall = sum(a.get("overall_score", 0) for a in all_analyses) / len(all_analyses)

        # Detect trends (compare first half vs second half)
        midpoint = len(all_analyses) // 2
        first_half_avg = sum(a.get("overall_score", 0) for a in all_analyses[:midpoint]) / midpoint
        second_half_avg = sum(a.get("overall_score", 0) for a in all_analyses[midpoint:]) / (len(all_analyses) - midpoint)
        trend = second_half_avg - first_half_avg

        # Identify recurring issues (appears in 40%+ of analyses)
        threshold = len(all_analyses) * 0.4
        recurring_grammar_issues = [
            {"type": issue_type, "frequency": count, "severity": "high" if count >= threshold * 1.5 else "medium"}
            for issue_type, count in grammar_issues_counter.most_common(5)
            if count >= threshold
        ]

        recurring_suggestions = [
            {"suggestion": suggestion, "frequency": count}
            for suggestion, count in improvement_suggestions_counter.most_common(5)
            if count >= threshold
        ]

        return {
            "sessions_analyzed": len(sessions),
            "total_analyses": len(all_analyses),
            "average_scores": {
                "grammar": round(avg_grammar, 1),
                "vocabulary": round(avg_vocabulary, 1),
                "complexity": round(avg_complexity, 1),
                "appropriateness": round(avg_appropriateness, 1),
                "overall": round(avg_overall, 1)
            },
            "trend": {
                "direction": "improving" if trend > 5 else "declining" if trend < -5 else "stable",
                "change": round(trend, 1)
            },
            "recurring_grammar_issues": recurring_grammar_issues,
            "recurring_suggestions": recurring_suggestions,
            "skill_assessment": {
                "grammar_strength": avg_grammar >= 75,
                "vocabulary_strength": avg_vocabulary >= 75,
                "needs_grammar_focus": avg_grammar < 65,
                "needs_vocabulary_focus": avg_vocabulary < 65,
                "ready_for_complexity": avg_complexity >= 70 and avg_overall >= 75
            }
        }

    @staticmethod
    async def update_learning_plan_based_on_patterns(
        plan_id: str,
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the learning plan's weekly schedule based on identified patterns.

        Args:
            plan_id: Learning plan ID
            pattern_analysis: Output from analyze_session_patterns()

        Returns:
            Updated plan details
        """
        from database import database

        # Get the learning plan
        plan = await database.learning_plans.find_one({"id": plan_id})
        if not plan:
            # Try ObjectId
            plan = await database.learning_plans.find_one({"_id": ObjectId(plan_id)})

        if not plan:
            return {"error": "Learning plan not found"}

        # Get current progress
        completed_sessions = plan.get("completed_sessions", 0)
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])

        if not weekly_schedule:
            return {"error": "No weekly schedule found in plan"}

        # Calculate current week (2 sessions per week)
        current_week_index = min(completed_sessions // 2, len(weekly_schedule) - 1)

        # Don't update past weeks, only upcoming weeks
        upcoming_weeks = weekly_schedule[current_week_index + 1:]

        if not upcoming_weeks:
            return {
                "message": "No upcoming weeks to update",
                "plan_complete": True
            }

        # Generate adaptive adjustments based on patterns
        adjustments = []

        # 1. Address recurring grammar issues
        recurring_issues = pattern_analysis.get("recurring_grammar_issues", [])
        if recurring_issues:
            top_issue = recurring_issues[0]
            issue_type = top_issue["type"]

            # Map issue types to learning focus
            issue_focus_map = {
                "verb_tense": "verb tense mastery",
                "article": "article usage",
                "preposition": "preposition accuracy",
                "subject_verb_agreement": "subject-verb agreement",
                "word_order": "sentence structure",
                "plural": "plural forms",
                "pronoun": "pronoun usage"
            }

            focus_area = issue_focus_map.get(issue_type, f"{issue_type} correction")
            adjustments.append({
                "type": "grammar_focus",
                "reason": f"Recurring {issue_type} issues detected ({top_issue['frequency']} times)",
                "action": f"Add {focus_area} exercises",
                "focus_area": focus_area
            })

        # 2. Adjust based on skill strengths/weaknesses
        skill_assessment = pattern_analysis.get("skill_assessment", {})

        if skill_assessment.get("needs_grammar_focus"):
            adjustments.append({
                "type": "grammar_emphasis",
                "reason": f"Grammar score below threshold ({pattern_analysis['average_scores']['grammar']}/100)",
                "action": "Increase grammar practice activities"
            })

        if skill_assessment.get("needs_vocabulary_focus"):
            adjustments.append({
                "type": "vocabulary_emphasis",
                "reason": f"Vocabulary score below threshold ({pattern_analysis['average_scores']['vocabulary']}/100)",
                "action": "Add vocabulary building exercises"
            })

        if skill_assessment.get("ready_for_complexity"):
            adjustments.append({
                "type": "increase_complexity",
                "reason": "Strong performance across all areas",
                "action": "Introduce more complex language structures"
            })

        # 3. Respond to trends
        trend = pattern_analysis.get("trend", {})
        if trend.get("direction") == "declining":
            adjustments.append({
                "type": "review_focus",
                "reason": f"Performance declining ({trend.get('change')}pts drop)",
                "action": "Add review sessions for previous material"
            })
        elif trend.get("direction") == "improving":
            adjustments.append({
                "type": "progression",
                "reason": f"Steady improvement ({trend.get('change')}pts gain)",
                "action": "Continue current approach, add challenge exercises"
            })

        # Apply adjustments to upcoming weeks
        updated_weeks = []
        for i, week in enumerate(upcoming_weeks):
            # Take first 2-3 adjustments for next few weeks
            applicable_adjustments = adjustments[:min(3, len(adjustments))]

            if not applicable_adjustments:
                break  # No more adjustments to apply

            updated_week = week.copy()

            # Add adjustment to week focus
            adjustment_focuses = [adj.get("focus_area") or adj.get("action") for adj in applicable_adjustments]

            current_focus = updated_week.get("focus", "")
            updated_focus = f"{current_focus} + Focus on: {', '.join(adjustment_focuses[:2])}"
            updated_week["focus"] = updated_focus

            # Add activities based on adjustments
            activities = updated_week.get("activities", [])
            for adjustment in applicable_adjustments:
                if adjustment["type"] == "grammar_focus":
                    activities.append(f"📝 Grammar drill: {adjustment['focus_area']}")
                elif adjustment["type"] == "vocabulary_emphasis":
                    activities.append("📚 Vocabulary expansion exercises")
                elif adjustment["type"] == "review_focus":
                    activities.append("🔄 Review previous lessons and patterns")

            updated_week["activities"] = activities[:6]  # Limit to 6 activities

            # Mark as adapted
            updated_week["adapted"] = True
            updated_week["adapted_at"] = datetime.utcnow().isoformat()
            updated_week["adaptation_reason"] = "; ".join([adj["reason"] for adj in applicable_adjustments])

            updated_weeks.append(updated_week)

        # Update the schedule in database
        if updated_weeks:
            # Merge updated weeks back into schedule
            updated_schedule = (
                weekly_schedule[:current_week_index + 1] +  # Past and current weeks (unchanged)
                updated_weeks +  # Updated upcoming weeks
                weekly_schedule[current_week_index + 1 + len(updated_weeks):]  # Remaining weeks
            )

            result = await database.learning_plans.update_one(
                {"_id": plan["_id"]},
                {
                    "$set": {
                        "plan_content.weekly_schedule": updated_schedule,
                        "last_adapted_at": datetime.utcnow(),
                        "adaptation_history": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "adjustments": adjustments,
                            "pattern_analysis_summary": {
                                "sessions_analyzed": pattern_analysis.get("sessions_analyzed"),
                                "average_score": pattern_analysis.get("average_scores", {}).get("overall"),
                                "trend": trend.get("direction")
                            }
                        }
                    },
                    "$push": {
                        "adaptation_log": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "weeks_updated": len(updated_weeks),
                            "adjustments_applied": adjustments
                        }
                    }
                }
            )

            return {
                "success": True,
                "weeks_updated": len(updated_weeks),
                "adjustments_applied": adjustments,
                "pattern_summary": {
                    "sessions_analyzed": pattern_analysis.get("sessions_analyzed"),
                    "recurring_issues": len(recurring_issues),
                    "performance_trend": trend.get("direction")
                }
            }

        return {
            "success": False,
            "message": "No updates needed"
        }

    @staticmethod
    async def analyze_single_session(
        user_id: str,
        current_session_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a single session's sentence analysis data for immediate concerns.

        Args:
            user_id: User ID
            current_session_analyses: List of sentence analyses from current session

        Returns:
            Single session analysis with immediate action flags
        """
        if not current_session_analyses:
            return {"no_data": True}

        # Calculate current session averages
        avg_grammar = sum(a.get("grammatical_score", 0) for a in current_session_analyses) / len(current_session_analyses)
        avg_vocabulary = sum(a.get("vocabulary_score", 0) for a in current_session_analyses) / len(current_session_analyses)
        avg_complexity = sum(a.get("complexity_score", 0) for a in current_session_analyses) / len(current_session_analyses)
        avg_overall = sum(a.get("overall_score", 0) for a in current_session_analyses) / len(current_session_analyses)

        # Collect all grammar issues from this session
        grammar_issues = []
        for analysis in current_session_analyses:
            grammar_issues.extend(analysis.get("grammar_issues", []))

        # Collect improvement suggestions
        improvement_suggestions = []
        for analysis in current_session_analyses:
            improvement_suggestions.extend(analysis.get("improvement_suggestions", []))

        # Flag immediate concerns
        concerns = []

        # Critical weakness (< 50 in any area)
        if avg_grammar < 50:
            concerns.append({
                "type": "critical_grammar_weakness",
                "severity": "high",
                "score": round(avg_grammar, 1),
                "action": "Add intensive grammar review to next week"
            })

        if avg_vocabulary < 50:
            concerns.append({
                "type": "critical_vocabulary_weakness",
                "severity": "high",
                "score": round(avg_vocabulary, 1),
                "action": "Add vocabulary building exercises to next week"
            })

        # Moderate weakness (50-65)
        if 50 <= avg_grammar < 65:
            concerns.append({
                "type": "grammar_needs_attention",
                "severity": "medium",
                "score": round(avg_grammar, 1),
                "action": "Increase grammar practice"
            })

        if 50 <= avg_vocabulary < 65:
            concerns.append({
                "type": "vocabulary_needs_attention",
                "severity": "medium",
                "score": round(avg_vocabulary, 1),
                "action": "Focus on vocabulary expansion"
            })

        # Low complexity (student using too simple language)
        if avg_complexity < 40:
            concerns.append({
                "type": "low_complexity",
                "severity": "medium",
                "score": round(avg_complexity, 1),
                "action": "Encourage use of more complex structures"
            })

        # Excellent performance (ready to advance)
        if avg_grammar >= 85 and avg_vocabulary >= 85 and avg_overall >= 85:
            concerns.append({
                "type": "ready_to_advance",
                "severity": "positive",
                "score": round(avg_overall, 1),
                "action": "Increase difficulty and introduce advanced topics"
            })

        # Check for frequent specific grammar issues in this session
        if grammar_issues:
            issue_counter = Counter([issue.get("type", "unknown") for issue in grammar_issues])
            # If same issue appears 3+ times in ONE session
            for issue_type, count in issue_counter.items():
                if count >= 3:
                    concerns.append({
                        "type": "repeated_grammar_issue",
                        "severity": "high",
                        "issue": issue_type,
                        "frequency": count,
                        "action": f"Add targeted practice for {issue_type}"
                    })

        return {
            "session_scores": {
                "grammar": round(avg_grammar, 1),
                "vocabulary": round(avg_vocabulary, 1),
                "complexity": round(avg_complexity, 1),
                "overall": round(avg_overall, 1)
            },
            "analyses_count": len(current_session_analyses),
            "immediate_concerns": concerns,
            "grammar_issues_count": len(grammar_issues),
            "improvement_suggestions": list(set(improvement_suggestions))[:5]  # Top 5 unique
        }

    @staticmethod
    async def check_performance_regression(
        user_id: str
    ) -> Dict[str, Any]:
        """
        Compare current session to previous session to detect sudden drops.

        Args:
            user_id: User ID

        Returns:
            Regression analysis comparing last two sessions
        """
        from database import database

        # Get last 2 sessions with sentence analyses
        sessions = await database.conversation_sessions.find(
            {
                "user_id": user_id,
                "sentence_analyses": {"$exists": True, "$ne": []}
            }
        ).sort("created_at", -1).limit(2).to_list(2)

        if len(sessions) < 2:
            return {"insufficient_data": True, "reason": "Need 2 sessions to compare"}

        current_session = sessions[0]
        previous_session = sessions[1]

        # Calculate averages for both sessions
        def calc_avg(analyses, field):
            if not analyses:
                return 0
            return sum(a.get(field, 0) for a in analyses) / len(analyses)

        current_analyses = current_session.get("sentence_analyses", [])
        previous_analyses = previous_session.get("sentence_analyses", [])

        current_grammar = calc_avg(current_analyses, "grammatical_score")
        previous_grammar = calc_avg(previous_analyses, "grammatical_score")

        current_vocabulary = calc_avg(current_analyses, "vocabulary_score")
        previous_vocabulary = calc_avg(previous_analyses, "vocabulary_score")

        current_overall = calc_avg(current_analyses, "overall_score")
        previous_overall = calc_avg(previous_analyses, "overall_score")

        # Calculate drops
        grammar_drop = previous_grammar - current_grammar
        vocabulary_drop = previous_vocabulary - current_vocabulary
        overall_drop = previous_overall - current_overall

        # Flag significant regressions (> 15 point drop)
        regressions = []

        if grammar_drop > 15:
            regressions.append({
                "type": "grammar_regression",
                "severity": "high",
                "drop": round(grammar_drop, 1),
                "previous": round(previous_grammar, 1),
                "current": round(current_grammar, 1),
                "action": "Review recent grammar topics and add reinforcement exercises"
            })

        if vocabulary_drop > 15:
            regressions.append({
                "type": "vocabulary_regression",
                "severity": "high",
                "drop": round(vocabulary_drop, 1),
                "previous": round(previous_vocabulary, 1),
                "current": round(current_vocabulary, 1),
                "action": "Review vocabulary from previous sessions"
            })

        if overall_drop > 15:
            regressions.append({
                "type": "overall_regression",
                "severity": "high",
                "drop": round(overall_drop, 1),
                "previous": round(previous_overall, 1),
                "current": round(current_overall, 1),
                "action": "Add comprehensive review session"
            })

        # Check time between sessions
        time_between = (current_session.get("created_at") - previous_session.get("created_at")).days
        if time_between > 7 and overall_drop > 10:
            regressions.append({
                "type": "inactivity_regression",
                "severity": "medium",
                "days_gap": time_between,
                "drop": round(overall_drop, 1),
                "action": "Student took long break, add review before advancing"
            })

        return {
            "regression_detected": len(regressions) > 0,
            "regressions": regressions,
            "score_changes": {
                "grammar": round(grammar_drop, 1),
                "vocabulary": round(vocabulary_drop, 1),
                "overall": round(overall_drop, 1)
            },
            "days_between_sessions": time_between
        }

    @staticmethod
    async def update_plan_immediate(
        plan_id: str,
        immediate_analysis: Dict[str, Any],
        regression_check: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make immediate updates to learning plan based on single session concerns.

        Args:
            plan_id: Learning plan ID
            immediate_analysis: Output from analyze_single_session()
            regression_check: Output from check_performance_regression()

        Returns:
            Immediate update result
        """
        from database import database

        # Collect all immediate adjustments
        adjustments = []

        # From immediate concerns
        for concern in immediate_analysis.get("immediate_concerns", []):
            adjustments.append({
                "source": "single_session",
                "type": concern["type"],
                "severity": concern["severity"],
                "action": concern["action"],
                "data": concern
            })

        # From regression checks
        if regression_check.get("regression_detected"):
            for regression in regression_check.get("regressions", []):
                adjustments.append({
                    "source": "regression_detection",
                    "type": regression["type"],
                    "severity": regression["severity"],
                    "action": regression["action"],
                    "data": regression
                })

        if not adjustments:
            return {"no_immediate_updates": True}

        # Get the learning plan
        plan = await database.learning_plans.find_one({"id": plan_id})
        if not plan:
            plan = await database.learning_plans.find_one({"_id": ObjectId(plan_id)})

        if not plan:
            return {"error": "Learning plan not found"}

        # Get current progress
        completed_sessions = plan.get("completed_sessions", 0)
        weekly_schedule = plan.get("plan_content", {}).get("weekly_schedule", [])

        # Calculate next week to update
        current_week_index = min(completed_sessions // 2, len(weekly_schedule) - 1)
        next_week_index = min(current_week_index + 1, len(weekly_schedule) - 1)

        if next_week_index >= len(weekly_schedule):
            return {"error": "No upcoming weeks to update"}

        # Update next week based on immediate adjustments
        next_week = weekly_schedule[next_week_index].copy()

        # Add immediate focus areas
        focus_areas = []
        activities = next_week.get("activities", [])

        for adj in adjustments[:3]:  # Top 3 priorities
            if adj["type"] == "critical_grammar_weakness":
                focus_areas.append("🚨 Intensive grammar review")
                activities.insert(0, "📝 Grammar fundamentals review")
            elif adj["type"] == "critical_vocabulary_weakness":
                focus_areas.append("🚨 Vocabulary building")
                activities.insert(0, "📚 Core vocabulary expansion")
            elif adj["type"] == "grammar_regression":
                focus_areas.append(f"🔄 Grammar review (dropped {adj['data'].get('drop')}pts)")
                activities.insert(0, "🔄 Review previous grammar lessons")
            elif adj["type"] == "vocabulary_regression":
                focus_areas.append(f"🔄 Vocabulary review (dropped {adj['data'].get('drop')}pts)")
                activities.insert(0, "🔄 Review previous vocabulary")
            elif adj["type"] == "repeated_grammar_issue":
                issue = adj["data"].get("issue", "grammar")
                focus_areas.append(f"🎯 Fix {issue} issues")
                activities.insert(0, f"📝 Targeted practice: {issue}")
            elif adj["type"] == "ready_to_advance":
                focus_areas.append("🚀 Advanced challenge")
                activities.append("🌟 Advanced exercises and complex topics")
            elif adj["type"] == "low_complexity":
                focus_areas.append("📈 Increase complexity")
                activities.append("🎯 Practice complex sentence structures")

        # Update next week
        if focus_areas:
            current_focus = next_week.get("focus", "")
            next_week["focus"] = f"{current_focus}\n⚡ IMMEDIATE: {', '.join(focus_areas[:2])}"
            next_week["activities"] = activities[:6]  # Limit to 6
            next_week["immediate_adaptation"] = True
            next_week["adapted_at"] = datetime.utcnow().isoformat()
            next_week["adaptation_reason"] = f"Immediate concerns from session {completed_sessions}"

            # Update in database
            weekly_schedule[next_week_index] = next_week

            result = await database.learning_plans.update_one(
                {"_id": plan["_id"]},
                {
                    "$set": {
                        "plan_content.weekly_schedule": weekly_schedule,
                        "last_immediate_adaptation": datetime.utcnow()
                    },
                    "$push": {
                        "immediate_adaptations": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "session_number": completed_sessions,
                            "week_updated": next_week_index + 1,
                            "adjustments": adjustments,
                            "session_scores": immediate_analysis.get("session_scores")
                        }
                    }
                }
            )

            return {
                "success": True,
                "immediate_update": True,
                "week_updated": next_week_index + 1,
                "adjustments_applied": adjustments,
                "focus_areas": focus_areas
            }

        return {"no_updates_needed": True}

    @staticmethod
    async def auto_update_plan_after_session(
        user_id: str,
        plan_id: str,
        current_session_analyses: Optional[List[Dict[str, Any]]] = None,
        minimum_sessions_for_update: int = 3
    ) -> Dict[str, Any]:
        """
        Main entry point: Two-tier update strategy.

        Tier 1 (Every Session): Check for immediate concerns
        Tier 2 (Every N Sessions): Pattern-based updates

        Args:
            user_id: User ID
            plan_id: Learning plan ID
            current_session_analyses: Sentence analyses from current session (if available)
            minimum_sessions_for_update: Minimum completed sessions before pattern update

        Returns:
            Combined update result
        """
        from database import database

        # Get plan to check completed sessions
        plan = await database.learning_plans.find_one({"id": plan_id})
        if not plan:
            plan = await database.learning_plans.find_one({"_id": ObjectId(plan_id)})

        if not plan:
            return {"error": "Plan not found"}

        completed_sessions = plan.get("completed_sessions", 0)

        result = {
            "completed_sessions": completed_sessions,
            "tier1_immediate": None,
            "tier2_patterns": None
        }

        # TIER 1: Immediate single-session analysis (runs every session)
        if current_session_analyses:
            print(f"[PLAN_OPTIMIZER] Running Tier 1 (immediate) analysis with {len(current_session_analyses)} analyses")

            immediate_analysis = await LearningPlanOptimizer.analyze_single_session(
                user_id=user_id,
                current_session_analyses=current_session_analyses
            )

            regression_check = await LearningPlanOptimizer.check_performance_regression(
                user_id=user_id
            )

            # Update plan immediately if concerns found
            if immediate_analysis.get("immediate_concerns") or regression_check.get("regression_detected"):
                immediate_update = await LearningPlanOptimizer.update_plan_immediate(
                    plan_id=plan_id,
                    immediate_analysis=immediate_analysis,
                    regression_check=regression_check
                )

                result["tier1_immediate"] = {
                    "analysis": immediate_analysis,
                    "regression_check": regression_check,
                    "update": immediate_update
                }

                if immediate_update.get("immediate_update"):
                    print(f"[PLAN_OPTIMIZER] ✅ Tier 1 immediate update applied!")
            else:
                print(f"[PLAN_OPTIMIZER] Tier 1: No immediate concerns")
                result["tier1_immediate"] = {"no_concerns": True}

        # TIER 2: Pattern-based analysis (runs every N sessions)
        if completed_sessions > 0 and completed_sessions % minimum_sessions_for_update == 0:
            print(f"[PLAN_OPTIMIZER] Running Tier 2 (pattern) analysis")

            # Analyze patterns
            pattern_analysis = await LearningPlanOptimizer.analyze_session_patterns(
                user_id=user_id,
                lookback_sessions=5
            )

            if not pattern_analysis.get("insufficient_data"):
                # Update plan based on patterns
                pattern_update = await LearningPlanOptimizer.update_learning_plan_based_on_patterns(
                    plan_id=plan_id,
                    pattern_analysis=pattern_analysis
                )

                result["tier2_patterns"] = {
                    "pattern_analysis": pattern_analysis,
                    "update": pattern_update
                }

                if pattern_update.get("success"):
                    print(f"[PLAN_OPTIMIZER] ✅ Tier 2 pattern update applied!")
            else:
                print(f"[PLAN_OPTIMIZER] Tier 2: Insufficient data")
                result["tier2_patterns"] = {"insufficient_data": True}
        else:
            print(f"[PLAN_OPTIMIZER] Tier 2: Not due yet (session {completed_sessions})")
            result["tier2_patterns"] = {"skipped": True}

        # Determine if any updates were made
        result["auto_updated"] = (
            result.get("tier1_immediate", {}).get("update", {}).get("immediate_update") or
            result.get("tier2_patterns", {}).get("update", {}).get("success")
        )

        return result
