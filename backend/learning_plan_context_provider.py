"""
Learning Plan Context Provider
Provides learning plan context for conversation help system.
Handles all cases: custom learning plans, practice conversations, guest users.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LearningPlanContextProvider:
    """
    Provides learning plan context for conversation help generation.
    Handles all conversation types gracefully:
    - Custom learning plan sessions (rich context)
    - Practice conversations (no learning plan context)
    - Guest users (no user context)
    """
    
    @staticmethod
    async def get_session_context(
        user_id: Optional[str],
        plan_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get learning plan context for conversation help.
        Returns None for practice conversations and guest users.
        """
        
        # Handle cases where we have no context
        if not user_id or not plan_id:
            print(f"[LEARNING_PLAN_CONTEXT] No context available - user_id: {user_id is not None}, plan_id: {plan_id is not None}")
            return None
        
        try:
            print(f"[LEARNING_PLAN_CONTEXT] 🔍 Fetching context for user {user_id}, plan {plan_id}")
            
            # Import here to avoid circular imports
            from learning_plan_service import LearningPlanService
            
            # Get the learning plan
            learning_plan = await LearningPlanService.get_learning_plan_safe(plan_id)
            
            if not learning_plan:
                print(f"[LEARNING_PLAN_CONTEXT] ❌ Learning plan not found: {plan_id}")
                return None
            
            # Verify ownership
            if learning_plan.get("user_id") != user_id:
                print(f"[LEARNING_PLAN_CONTEXT] ❌ Plan ownership mismatch")
                return None
            
            # Extract context information
            context = LearningPlanContextProvider._extract_context_from_plan(learning_plan)
            
            print(f"[LEARNING_PLAN_CONTEXT] ✅ Context extracted successfully")
            print(f"[LEARNING_PLAN_CONTEXT] Focus: {context.get('current_focus', 'N/A')}")
            print(f"[LEARNING_PLAN_CONTEXT] Level: {context.get('proficiency_level', 'N/A')}")
            
            return context
            
        except Exception as e:
            print(f"[LEARNING_PLAN_CONTEXT] ❌ Error fetching context: {str(e)}")
            logger.error(f"Error fetching learning plan context: {str(e)}")
            return None
    
    @staticmethod
    def _extract_context_from_plan(learning_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from learning plan for conversation help"""
        
        # Basic plan information
        context = {
            "proficiency_level": learning_plan.get("proficiency_level", "B1"),
            "language": learning_plan.get("language", "english"),
            "plan_id": learning_plan.get("id"),
        }
        
        # Extract assessment data if available
        assessment_data = learning_plan.get("assessment_data", {})
        if assessment_data:
            context["strengths"] = assessment_data.get("strengths", [])
            context["areas_for_improvement"] = assessment_data.get("areas_for_improvement", [])
            context["recommended_level"] = assessment_data.get("recommended_level")
        
        # Extract current week and focus
        weekly_schedule = learning_plan.get("plan_content", {}).get("weekly_schedule", [])
        if weekly_schedule:
            current_week_info = LearningPlanContextProvider._get_current_week_info(
                learning_plan, weekly_schedule
            )
            context.update(current_week_info)
        
        # Extract learning objectives
        plan_content = learning_plan.get("plan_content", {})
        context["learning_objectives"] = plan_content.get("learning_objectives", [])
        
        # Get tutor instructions context
        tutor_context = LearningPlanContextProvider._get_tutor_instructions_context(
            context["language"], 
            context["proficiency_level"]
        )
        context.update(tutor_context)
        
        return context
    
    @staticmethod
    def _get_current_week_info(
        learning_plan: Dict[str, Any], 
        weekly_schedule: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine current week and focus based on progress"""
        
        completed_sessions = learning_plan.get("completed_sessions", 0)
        sessions_per_week = 2  # Default sessions per week
        
        # Calculate current week (0-based)
        current_week_index = min(completed_sessions // sessions_per_week, len(weekly_schedule) - 1)
        
        if current_week_index < len(weekly_schedule):
            current_week = weekly_schedule[current_week_index]
            return {
                "current_week": current_week_index + 1,
                "current_focus": current_week.get("focus", "Language practice"),
                "current_activities": current_week.get("activities", []),
                "sessions_completed_this_week": completed_sessions % sessions_per_week,
                "total_weeks": len(weekly_schedule)
            }
        
        # Fallback for completed plans
        return {
            "current_week": len(weekly_schedule),
            "current_focus": "Advanced practice and review",
            "current_activities": ["Continue practicing all learned skills"],
            "sessions_completed_this_week": 0,
            "total_weeks": len(weekly_schedule)
        }
    
    @staticmethod
    def _get_tutor_instructions_context(language: str, proficiency_level: str) -> Dict[str, Any]:
        """Get relevant tutor instructions for the language and level"""
        
        try:
            # Import tutor instructions
            import json
            import os
            
            tutor_instructions_path = os.path.join(os.path.dirname(__file__), "tutor_instructions.json")
            
            if os.path.exists(tutor_instructions_path):
                with open(tutor_instructions_path, 'r', encoding='utf-8') as f:
                    tutor_instructions = json.load(f)
                
                # Get language-specific instructions
                language_instructions = tutor_instructions.get("languages", {}).get(language, {})
                level_instructions = language_instructions.get("levels", {}).get(proficiency_level, {})
                
                if level_instructions:
                    return {
                        "tutor_focus_areas": LearningPlanContextProvider._extract_focus_areas(level_instructions),
                        "teaching_approach": LearningPlanContextProvider._extract_teaching_approach(level_instructions),
                        "cultural_context": language_instructions.get("name", language.title())
                    }
            
        except Exception as e:
            print(f"[LEARNING_PLAN_CONTEXT] Warning: Could not load tutor instructions: {str(e)}")
        
        # Fallback context
        return {
            "tutor_focus_areas": ["General communication", "Vocabulary building", "Grammar practice"],
            "teaching_approach": "Supportive and encouraging",
            "cultural_context": language.title()
        }
    
    @staticmethod
    def _extract_focus_areas(level_instructions: Dict[str, Any]) -> List[str]:
        """Extract focus areas from tutor instructions"""
        
        instructions_text = level_instructions.get("instructions", "")
        
        # Simple extraction of focus areas from instructions
        focus_areas = []
        
        # Look for bullet points or numbered lists
        lines = instructions_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                # Remove bullet point and clean up
                focus_area = line[1:].strip()
                if focus_area and len(focus_area) < 100:  # Reasonable length
                    focus_areas.append(focus_area)
        
        # If no focus areas found, provide defaults based on level
        if not focus_areas:
            level_defaults = {
                "A1": ["Basic vocabulary", "Simple sentences", "Pronunciation"],
                "A2": ["Daily conversations", "Past tense", "Common expressions"],
                "B1": ["Travel situations", "Opinion expression", "Storytelling"],
                "B2": ["Complex discussions", "Advanced grammar", "Cultural topics"],
                "C1": ["Academic language", "Nuanced expression", "Professional communication"],
                "C2": ["Native-like precision", "Cultural subtleties", "Specialized vocabulary"]
            }
            focus_areas = level_defaults.get(level_instructions.get("description", "").split()[0], ["General communication"])
        
        return focus_areas[:5]  # Limit to 5 focus areas
    
    @staticmethod
    def _extract_teaching_approach(level_instructions: Dict[str, Any]) -> str:
        """Extract teaching approach from tutor instructions"""
        
        instructions_text = level_instructions.get("instructions", "")
        
        # Look for teaching approach keywords
        if "encouraging" in instructions_text.lower():
            return "Encouraging and supportive"
        elif "challenging" in instructions_text.lower():
            return "Challenging and rigorous"
        elif "patient" in instructions_text.lower():
            return "Patient and methodical"
        elif "interactive" in instructions_text.lower():
            return "Interactive and engaging"
        else:
            return "Adaptive and personalized"

class UserContextProvider:
    """
    Provides user context for conversation help generation.
    Handles registered users and guest users.
    """
    
    @staticmethod
    def create_user_context(
        target_language: str,
        proficiency_level: str,
        user_language: str,
        is_guest: bool = False
    ) -> Dict[str, Any]:
        """
        Create user context for conversation help.
        Works for both registered and guest users.
        """
        
        return {
            "target_language": target_language.lower(),
            "proficiency_level": proficiency_level,
            "user_language": user_language.lower(),
            "is_guest": is_guest,
            "context_type": "guest" if is_guest else "registered"
        }
