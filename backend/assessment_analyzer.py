"""
Assessment Analyzer
Extracts deep insights from speaking assessment data to create personalized learning plans
"""

from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class AssessmentAnalyzer:
    """
    Analyzes speaking assessment data to extract actionable insights
    for personalized learning plan generation
    """
    
    @staticmethod
    def analyze_skill_profile(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive skill profile analysis
        
        Args:
            assessment_data: Complete assessment data including skill scores
            
        Returns:
            Dictionary with skill profile insights
        """
        try:
            # Extract skill scores
            skill_scores = {}
            
            # Handle different assessment data formats
            if 'skill_scores' in assessment_data:
                # New format: skill_scores dict
                skill_scores = assessment_data['skill_scores']
            else:
                # Old format: individual skill objects
                for skill in ['pronunciation', 'grammar', 'vocabulary', 'fluency', 'coherence']:
                    if skill in assessment_data and isinstance(assessment_data[skill], dict):
                        skill_scores[skill] = assessment_data[skill].get('score', 50)
                    elif skill in assessment_data and isinstance(assessment_data[skill], (int, float)):
                        skill_scores[skill] = assessment_data[skill]
            
            # Ensure we have all 5 skills
            default_skills = {
                'pronunciation': 50,
                'grammar': 50,
                'vocabulary': 50,
                'fluency': 50,
                'coherence': 50
            }
            for skill, default_score in default_skills.items():
                if skill not in skill_scores:
                    skill_scores[skill] = default_score
            
            # 1. Calculate skill statistics
            scores = list(skill_scores.values())
            avg_score = sum(scores) / len(scores) if scores else 50
            max_score = max(scores) if scores else 50
            min_score = min(scores) if scores else 50
            skill_gap = max_score - min_score
            
            # 2. Identify skill categories
            strong_skills = {k: v for k, v in skill_scores.items() if v >= avg_score + 5}
            weak_skills = {k: v for k, v in skill_scores.items() if v <= avg_score - 5}
            moderate_skills = {k: v for k, v in skill_scores.items() 
                              if k not in strong_skills and k not in weak_skills}
            
            # 3. Determine learner profile
            profile_type = AssessmentAnalyzer._determine_profile_type(
                skill_gap, len(weak_skills), len(strong_skills)
            )
            
            # 4. Calculate improvement priorities (lower score = higher priority)
            improvement_priority = sorted(
                skill_scores.items(),
                key=lambda x: (x[1], x[0])  # Sort by score (ascending), then name
            )
            
            # 5. Identify skill dependencies
            dependencies = AssessmentAnalyzer._analyze_skill_dependencies(skill_scores)
            
            # 6. Identify bottleneck skill (lowest score that's blocking progress)
            bottleneck_skill = improvement_priority[0][0] if improvement_priority else None
            
            logger.info(f"[ASSESSMENT_ANALYZER] Skill profile analysis complete:")
            logger.info(f"  Profile type: {profile_type}")
            logger.info(f"  Skill gap: {skill_gap}")
            logger.info(f"  Bottleneck: {bottleneck_skill}")
            logger.info(f"  Strong skills: {list(strong_skills.keys())}")
            logger.info(f"  Weak skills: {list(weak_skills.keys())}")
            
            return {
                "profile_type": profile_type,
                "skill_gap": skill_gap,
                "strong_skills": strong_skills,
                "weak_skills": weak_skills,
                "moderate_skills": moderate_skills,
                "improvement_priority": improvement_priority,
                "skill_dependencies": dependencies,
                "avg_score": avg_score,
                "max_score": max_score,
                "min_score": min_score,
                "bottleneck_skill": bottleneck_skill,
                "all_skill_scores": skill_scores
            }
            
        except Exception as e:
            logger.error(f"[ASSESSMENT_ANALYZER] Error analyzing skill profile: {str(e)}")
            # Return safe defaults
            return {
                "profile_type": "balanced",
                "skill_gap": 0,
                "strong_skills": {},
                "weak_skills": {},
                "moderate_skills": {},
                "improvement_priority": [],
                "skill_dependencies": {},
                "avg_score": 50,
                "max_score": 50,
                "min_score": 50,
                "bottleneck_skill": None,
                "all_skill_scores": {}
            }
    
    @staticmethod
    def _determine_profile_type(skill_gap: float, weak_count: int, strong_count: int) -> str:
        """
        Determine learner profile type based on skill distribution
        
        Args:
            skill_gap: Difference between highest and lowest skill
            weak_count: Number of weak skills
            strong_count: Number of strong skills
            
        Returns:
            Profile type string
        """
        if skill_gap < 15:
            return "balanced"  # All skills similar
        elif weak_count == 1:
            return "single_bottleneck"  # One weak area holding back
        elif strong_count >= 3:
            return "advanced_with_gaps"  # Strong but specific weaknesses
        else:
            return "developing"  # Multiple areas need work
    
    @staticmethod
    def _analyze_skill_dependencies(skill_scores: Dict[str, float]) -> Dict[str, str]:
        """
        Identify which skills depend on others
        
        Args:
            skill_scores: Dictionary of skill scores
            
        Returns:
            Dictionary of dependencies
        """
        dependencies = {}
        
        # Grammar is foundation for vocabulary
        if skill_scores.get('grammar', 50) < 70 and \
           skill_scores.get('vocabulary', 50) > skill_scores.get('grammar', 50) + 10:
            dependencies['vocabulary'] = 'blocked_by_grammar'
        
        # Vocabulary is foundation for fluency
        if skill_scores.get('vocabulary', 50) < 70 and \
           skill_scores.get('fluency', 50) > skill_scores.get('vocabulary', 50) + 10:
            dependencies['fluency'] = 'blocked_by_vocabulary'
        
        # Pronunciation affects confidence and fluency
        if skill_scores.get('pronunciation', 50) < 70:
            dependencies['fluency'] = 'affected_by_pronunciation'
        
        return dependencies
    
    @staticmethod
    def determine_learning_velocity(duration_months: int, current_level: str) -> str:
        """
        Determine how aggressive the learning plan should be
        
        Args:
            duration_months: Plan duration in months
            current_level: CEFR level (A1, A2, B1, B2, C1, C2)
            
        Returns:
            Learning velocity: "intensive", "moderate", or "gradual"
        """
        level_intensity = {
            'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6
        }
        
        intensity = level_intensity.get(current_level, 3)
        
        # Short duration = intensive
        # Long duration = gradual
        # Adjust based on level (higher levels need more time per concept)
        
        if duration_months <= 2:
            return "intensive"  # Fast-paced, focused
        elif duration_months <= 6:
            return "moderate"  # Balanced approach
        else:
            return "gradual"  # Comprehensive, thorough
    
    @staticmethod
    def map_goals_to_skill_priorities(goals: List[str], level: str) -> Dict[str, float]:
        """
        Different goals require different skill emphasis
        
        Args:
            goals: List of learning goals
            level: CEFR level
            
        Returns:
            Dictionary of skill priorities (weights)
        """
        # Define goal-specific skill priorities
        goal_priorities = {
            "travel": {
                "fluency": 1.3,      # Most important for travel
                "vocabulary": 1.2,
                "pronunciation": 1.1,
                "grammar": 0.9,
                "coherence": 0.8
            },
            "business": {
                "coherence": 1.3,    # Most important for business
                "vocabulary": 1.2,
                "grammar": 1.1,
                "fluency": 1.0,
                "pronunciation": 0.9
            },
            "academic": {
                "grammar": 1.3,      # Most important for academic
                "vocabulary": 1.2,
                "coherence": 1.2,
                "fluency": 0.9,
                "pronunciation": 0.8
            },
            "culture": {
                "vocabulary": 1.3,
                "coherence": 1.2,
                "fluency": 1.1,
                "pronunciation": 1.0,
                "grammar": 0.9
            },
            "daily": {
                "fluency": 1.3,
                "vocabulary": 1.2,
                "pronunciation": 1.1,
                "coherence": 1.0,
                "grammar": 0.9
            }
        }
        
        # Combine priorities from all selected goals
        combined_priorities = {
            'pronunciation': 0.0,
            'grammar': 0.0,
            'vocabulary': 0.0,
            'fluency': 0.0,
            'coherence': 0.0
        }
        
        for goal in goals:
            if goal in goal_priorities:
                for skill, weight in goal_priorities[goal].items():
                    combined_priorities[skill] += weight
        
        # Normalize to sum to 5.0 (average of 1.0 per skill)
        total = sum(combined_priorities.values())
        if total > 0:
            normalized = {k: (v / total) * 5.0 for k, v in combined_priorities.items()}
        else:
            # Default: equal weights
            normalized = {k: 1.0 for k in combined_priorities.keys()}
        
        logger.info(f"[ASSESSMENT_ANALYZER] Goal-based skill priorities:")
        for skill, priority in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {skill}: {priority:.2f}")
        
        return normalized
    
    @staticmethod
    def calculate_focus_distribution(
        skill_profile: Dict[str, Any],
        goal_priorities: Dict[str, float],
        duration_months: int
    ) -> Dict[str, Any]:
        """
        Calculate how much time to spend on each skill area
        
        Balances:
        - Skill weaknesses (need improvement)
        - Goal priorities (what matters for user's goals)
        - Duration (time available)
        
        Args:
            skill_profile: Output from analyze_skill_profile
            goal_priorities: Output from map_goals_to_skill_priorities
            duration_months: Plan duration
            
        Returns:
            Dictionary with focus distribution
        """
        try:
            # 1. Start with skill-based needs (100 - score = need)
            skill_needs = {}
            all_scores = skill_profile.get('all_skill_scores', {})
            
            for skill, score in all_scores.items():
                # Lower score = more time needed
                skill_needs[skill] = (100 - score) / 100.0
            
            # 2. Adjust based on goal priorities
            adjusted_needs = {}
            for skill, need in skill_needs.items():
                goal_weight = goal_priorities.get(skill, 1.0)
                adjusted_needs[skill] = need * goal_weight
            
            # 3. Normalize to percentages
            total = sum(adjusted_needs.values())
            if total > 0:
                distribution = {k: v / total for k, v in adjusted_needs.items()}
            else:
                # Default: equal distribution
                distribution = {k: 0.2 for k in skill_needs.keys()}
            
            # 4. Calculate weeks per skill
            total_weeks = duration_months * 4
            weeks_per_skill = {k: int(v * total_weeks) for k, v in distribution.items()}
            
            # 5. Identify primary and secondary focus
            sorted_skills = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
            primary_focus = sorted_skills[0][0] if sorted_skills else None
            secondary_focus = sorted_skills[1][0] if len(sorted_skills) > 1 else None
            
            logger.info(f"[ASSESSMENT_ANALYZER] Focus distribution calculated:")
            logger.info(f"  Primary focus: {primary_focus} ({distribution.get(primary_focus, 0)*100:.1f}%)")
            logger.info(f"  Secondary focus: {secondary_focus} ({distribution.get(secondary_focus, 0)*100:.1f}%)")
            
            return {
                "percentages": distribution,
                "weeks_per_skill": weeks_per_skill,
                "primary_focus": primary_focus,
                "secondary_focus": secondary_focus,
                "total_weeks": total_weeks
            }
            
        except Exception as e:
            logger.error(f"[ASSESSMENT_ANALYZER] Error calculating focus distribution: {str(e)}")
            # Return safe defaults
            return {
                "percentages": {"fluency": 0.2, "vocabulary": 0.2, "grammar": 0.2, 
                               "pronunciation": 0.2, "coherence": 0.2},
                "weeks_per_skill": {},
                "primary_focus": "fluency",
                "secondary_focus": "vocabulary",
                "total_weeks": duration_months * 4
            }
