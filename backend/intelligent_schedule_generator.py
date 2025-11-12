"""
Intelligent Schedule Generator
Generates optimized weekly schedules based on assessment analysis and enriched goals
"""

from typing import Dict, List, Any
import logging
from enriched_goals_config import (
    get_level_category,
    get_sub_goal,
    get_sub_goal_activities,
    ENRICHED_GOALS
)
from assessment_analyzer import AssessmentAnalyzer

logger = logging.getLogger(__name__)


class IntelligentScheduleGenerator:
    """
    Generates personalized weekly schedules using:
    - Deep assessment analysis
    - Enriched goal activities
    - Skill-based focus distribution
    - Progressive difficulty
    """
    
    @staticmethod
    def generate_optimized_schedule(
        duration_months: int,
        assessment_data: Dict[str, Any],
        goals: List[str],
        language: str,
        sub_goals: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a truly personalized weekly schedule
        
        Args:
            duration_months: Plan duration in months
            assessment_data: Complete assessment data
            goals: List of main learning goals
            language: Target language
            sub_goals: Optional list of specific sub-goals
            
        Returns:
            List of weekly schedule dictionaries
        """
        try:
            logger.info(f"[SCHEDULE_GEN] Generating optimized schedule:")
            logger.info(f"  Duration: {duration_months} months")
            logger.info(f"  Goals: {goals}")
            logger.info(f"  Sub-goals: {sub_goals}")
            logger.info(f"  Language: {language}")
            
            # 1. Deep analysis
            level = assessment_data.get('recommended_level', 'B1')
            skill_profile = AssessmentAnalyzer.analyze_skill_profile(assessment_data)
            learning_velocity = AssessmentAnalyzer.determine_learning_velocity(
                duration_months, 
                level
            )
            goal_priorities = AssessmentAnalyzer.map_goals_to_skill_priorities(
                goals,
                level
            )
            
            # 2. Calculate optimal focus distribution
            focus_distribution = AssessmentAnalyzer.calculate_focus_distribution(
                skill_profile,
                goal_priorities,
                duration_months
            )
            
            # 3. Generate week-by-week schedule
            total_weeks = duration_months * 4
            weekly_schedule = []
            
            # If sub-goals are specified, use goal-focused generation
            if sub_goals and len(sub_goals) > 0:
                weekly_schedule = IntelligentScheduleGenerator._generate_goal_focused_schedule(
                    total_weeks=total_weeks,
                    goals=goals,
                    sub_goals=sub_goals,
                    level=level,
                    language=language,
                    skill_profile=skill_profile,
                    focus_distribution=focus_distribution,
                    learning_velocity=learning_velocity,
                    assessment_data=assessment_data
                )
            else:
                # Use skill-focused generation (backward compatible)
                weekly_schedule = IntelligentScheduleGenerator._generate_skill_focused_schedule(
                    total_weeks=total_weeks,
                    skill_profile=skill_profile,
                    focus_distribution=focus_distribution,
                    learning_velocity=learning_velocity,
                    goals=goals,
                    level=level,
                    language=language,
                    assessment_data=assessment_data
                )
            
            logger.info(f"[SCHEDULE_GEN] ✅ Generated {len(weekly_schedule)} weeks")
            return weekly_schedule
            
        except Exception as e:
            logger.error(f"[SCHEDULE_GEN] ❌ Error generating schedule: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return safe fallback schedule
            return IntelligentScheduleGenerator._generate_fallback_schedule(
                duration_months, level, language, assessment_data
            )
    
    @staticmethod
    def _generate_goal_focused_schedule(
        total_weeks: int,
        goals: List[str],
        sub_goals: List[str],
        level: str,
        language: str,
        skill_profile: Dict[str, Any],
        focus_distribution: Dict[str, Any],
        learning_velocity: str,
        assessment_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate schedule focused on specific sub-goals
        
        60% of weeks focus on selected sub-goals
        40% of weeks focus on general skill development
        """
        logger.info(f"[SCHEDULE_GEN] Using goal-focused generation")
        
        weekly_schedule = []
        level_category = get_level_category(level)
        
        # Calculate week allocation
        sub_goal_weeks = int(total_weeks * 0.6)
        skill_weeks = int(total_weeks * 0.4)
        
        # Distribute sub-goal weeks evenly
        weeks_per_sub_goal = sub_goal_weeks // len(sub_goals) if sub_goals else 0
        
        week_num = 1
        
        # Generate weeks for each sub-goal
        for sub_goal_id in sub_goals:
            # Find which main goal this sub-goal belongs to
            main_goal = None
            for goal_id in goals:
                if goal_id in ENRICHED_GOALS:
                    if sub_goal_id in ENRICHED_GOALS[goal_id].get('sub_goals', {}):
                        main_goal = goal_id
                        break
            
            if not main_goal:
                logger.warning(f"[SCHEDULE_GEN] Sub-goal {sub_goal_id} not found in goals {goals}")
                continue
            
            # Get sub-goal configuration
            sub_goal_config = get_sub_goal(main_goal, sub_goal_id)
            if not sub_goal_config:
                continue
            
            # Get level-appropriate activities
            activities = get_sub_goal_activities(main_goal, sub_goal_id, level)
            if not activities:
                activities = [
                    f"Practice {sub_goal_config.get('text', 'language skills')}",
                    f"Focus on {sub_goal_config.get('description', 'communication')}",
                    "Complete exercises for your level"
                ]
            
            # Generate weeks for this sub-goal
            for i in range(weeks_per_sub_goal):
                if week_num > total_weeks:
                    break
                
                week_data = {
                    "week": week_num,
                    "focus": f"{sub_goal_config.get('text', 'Language Practice')}: {sub_goal_config.get('description', '')}",
                    "main_goal": main_goal,
                    "sub_goal": sub_goal_id,
                    "activities": activities[:3],  # Top 3 activities
                    "key_vocabulary": sub_goal_config.get('key_vocabulary', []),
                    "key_phrases": sub_goal_config.get('key_phrases', []),
                    "sessions_completed": 0,
                    "total_sessions": 2,
                    "session_details": IntelligentScheduleGenerator._initialize_session_details(
                        f"{sub_goal_config.get('text', 'Language Practice')}: {sub_goal_config.get('description', '')}"
                    )
                }
                
                weekly_schedule.append(week_data)
                week_num += 1
        
        # Fill remaining weeks with skill-focused content
        areas_for_improvement = assessment_data.get('areas_for_improvement', [])
        strengths = assessment_data.get('strengths', [])
        
        while week_num <= total_weeks:
            # Determine focus based on skill distribution
            primary_skill = focus_distribution.get('primary_focus', 'fluency')
            
            # Create focus description
            if areas_for_improvement:
                focus_area = areas_for_improvement[0]
                focus = f"Skill Development: {focus_area} (Focus: {primary_skill.title()})"
            else:
                focus = f"Skill Development: Improving {primary_skill.title()}"
            
            # Get activities for this skill
            activities = IntelligentScheduleGenerator._get_skill_activities(
                primary_skill, level, language, learning_velocity
            )
            
            week_data = {
                "week": week_num,
                "focus": focus,
                "primary_skill": primary_skill,
                "activities": activities,
                "sessions_completed": 0,
                "total_sessions": 2,
                "session_details": IntelligentScheduleGenerator._initialize_session_details(focus)
            }
            
            weekly_schedule.append(week_data)
            week_num += 1
        
        return weekly_schedule
    
    @staticmethod
    def _generate_skill_focused_schedule(
        total_weeks: int,
        skill_profile: Dict[str, Any],
        focus_distribution: Dict[str, Any],
        learning_velocity: str,
        goals: List[str],
        level: str,
        language: str,
        assessment_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate schedule focused on skill development
        Uses intelligent focus distribution
        """
        logger.info(f"[SCHEDULE_GEN] Using skill-focused generation")
        
        weekly_schedule = []
        weeks_per_skill = focus_distribution.get('weeks_per_skill', {})
        
        # Create schedule that distributes skills optimally
        skill_schedule = []
        for skill, weeks in sorted(weeks_per_skill.items(), key=lambda x: x[1], reverse=True):
            skill_schedule.extend([skill] * weeks)
        
        # Ensure we have enough entries
        primary_focus = focus_distribution.get('primary_focus', 'fluency')
        while len(skill_schedule) < total_weeks:
            skill_schedule.append(primary_focus)
        
        # Get assessment insights
        areas_for_improvement = assessment_data.get('areas_for_improvement', [])
        strengths = assessment_data.get('strengths', [])
        
        # Generate weeks
        for week_num in range(1, total_weeks + 1):
            # Determine which skill to focus on this week
            current_skill = skill_schedule[week_num - 1] if week_num <= len(skill_schedule) else primary_focus
            
            # Create focus description
            progress_percentage = (week_num / total_weeks) * 100
            
            if progress_percentage < 25:
                phase = "Building Foundation"
            elif progress_percentage < 50:
                phase = "Developing Skills"
            elif progress_percentage < 75:
                phase = "Refining Abilities"
            else:
                phase = "Mastering Advanced Techniques"
            
            # Find relevant improvement area for this skill
            relevant_improvement = None
            for area in areas_for_improvement:
                if current_skill.lower() in area.lower():
                    relevant_improvement = area
                    break
            
            if relevant_improvement:
                focus = f"{phase}: {relevant_improvement} (Focus: {current_skill.title()})"
            else:
                focus = f"{phase}: Strengthening {current_skill.title()} skills"
            
            # Get activities
            activities = IntelligentScheduleGenerator._get_skill_activities(
                current_skill, level, language, learning_velocity
            )
            
            week_data = {
                "week": week_num,
                "focus": focus,
                "primary_skill": current_skill,
                "activities": activities,
                "sessions_completed": 0,
                "total_sessions": 2,
                "session_details": IntelligentScheduleGenerator._initialize_session_details(focus)
            }
            
            weekly_schedule.append(week_data)
        
        return weekly_schedule
    
    @staticmethod
    def _get_skill_activities(
        skill: str,
        level: str,
        language: str,
        learning_velocity: str
    ) -> List[str]:
        """
        Get level-appropriate activities for a specific skill
        """
        # Comprehensive activity library
        ACTIVITY_LIBRARY = {
            "pronunciation": {
                "A1-A2": [
                    "Practice basic sounds and phonemes with audio recordings",
                    "Record yourself reading simple sentences",
                    "Focus on word stress in common vocabulary"
                ],
                "B1-B2": [
                    "Practice intonation patterns in questions vs statements",
                    "Work on connected speech and linking sounds",
                    "Record and analyze your pronunciation of complex words"
                ],
                "C1-C2": [
                    "Master subtle pronunciation differences in similar words",
                    "Practice natural rhythm and stress in longer discourse",
                    "Work on regional accent reduction or adoption"
                ]
            },
            "grammar": {
                "A1-A2": [
                    "Master present simple tense in all forms",
                    "Practice basic sentence structure: Subject + Verb + Object",
                    "Learn and use common irregular verbs in context"
                ],
                "B1-B2": [
                    "Practice complex sentence structures with subordinate clauses",
                    "Master all past tenses and their appropriate usage",
                    "Work on conditional sentences in real contexts"
                ],
                "C1-C2": [
                    "Refine use of subjunctive mood and advanced conditionals",
                    "Practice sophisticated sentence structures for emphasis",
                    "Master nuanced grammar for formal vs informal contexts"
                ]
            },
            "vocabulary": {
                "A1-A2": [
                    "Learn 30 essential words for daily activities",
                    "Practice using new vocabulary in simple sentences",
                    "Create personal vocabulary cards with images"
                ],
                "B1-B2": [
                    "Expand vocabulary in specific domains (work, hobbies, news)",
                    "Learn collocations and common word partnerships",
                    "Practice using synonyms to vary your expression"
                ],
                "C1-C2": [
                    "Master idiomatic expressions and their appropriate usage",
                    "Learn specialized vocabulary for your field of interest",
                    "Practice using advanced vocabulary naturally in context"
                ]
            },
            "fluency": {
                "A1-A2": [
                    "Practice speaking for 1 minute without stopping",
                    "Use simple linking words (and, but, because)",
                    "Reduce pauses by preparing common phrases"
                ],
                "B1-B2": [
                    "Speak for 3-5 minutes on various topics without preparation",
                    "Practice thinking in the target language",
                    "Work on reducing filler words and unnecessary pauses"
                ],
                "C1-C2": [
                    "Engage in spontaneous discussions on complex topics",
                    "Practice maintaining natural flow when searching for words",
                    "Work on speaking at native-like speed with clarity"
                ]
            },
            "coherence": {
                "A1-A2": [
                    "Practice organizing simple stories with beginning, middle, end",
                    "Use basic sequencing words (first, then, finally)",
                    "Connect related sentences using simple conjunctions"
                ],
                "B1-B2": [
                    "Structure longer narratives with clear sections",
                    "Use discourse markers to show relationships between ideas",
                    "Practice presenting arguments with supporting evidence"
                ],
                "C1-C2": [
                    "Master sophisticated discourse organization techniques",
                    "Use advanced cohesive devices for seamless flow",
                    "Practice creating compelling narratives with complex structure"
                ]
            }
        }
        
        level_category = get_level_category(level)
        activities = ACTIVITY_LIBRARY.get(skill, {}).get(level_category, [
            f"Practice {skill} at {level} level",
            f"Complete exercises focusing on {skill}",
            f"Apply {skill} in real conversations"
        ])
        
        return activities[:3]  # Return top 3 activities
    
    @staticmethod
    def _initialize_session_details(focus: str) -> List[Dict[str, Any]]:
        """
        Initialize session details array for a week
        """
        return [
            {
                "session_number": 1,
                "focus": focus,
                "completed_at": None,
                "duration_minutes": None,
                "session_summary": None,
                "status": "pending"
            },
            {
                "session_number": 2,
                "focus": focus,
                "completed_at": None,
                "duration_minutes": None,
                "session_summary": None,
                "status": "pending"
            }
        ]
    
    @staticmethod
    def _generate_fallback_schedule(
        duration_months: int,
        level: str,
        language: str,
        assessment_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate a safe fallback schedule if main generation fails
        """
        logger.warning(f"[SCHEDULE_GEN] Using fallback schedule generation")
        
        total_weeks = duration_months * 4
        weekly_schedule = []
        
        areas_for_improvement = assessment_data.get('areas_for_improvement', ['general language skills'])
        
        for week_num in range(1, total_weeks + 1):
            focus_area = areas_for_improvement[0] if areas_for_improvement else "general language skills"
            
            week_data = {
                "week": week_num,
                "focus": f"Week {week_num}: Improving {focus_area}",
                "activities": [
                    f"Practice {language} conversation",
                    f"Focus on {focus_area}",
                    "Complete exercises for your level"
                ],
                "sessions_completed": 0,
                "total_sessions": 2,
                "session_details": IntelligentScheduleGenerator._initialize_session_details(
                    f"Week {week_num}: Improving {focus_area}"
                )
            }
            
            weekly_schedule.append(week_data)
        
        return weekly_schedule
