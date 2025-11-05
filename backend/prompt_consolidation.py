"""
Phase 1: Instruction Consolidation & Simplification
Reduces prompt tokens by 30-40% through better organization and conciseness
"""

def build_consolidated_instructions(language: str, level: str, topic: str = None, 
                                   user_prompt: str = None, week_focus: str = None) -> str:
    """
    Build consolidated, simplified instructions with 30-40% token reduction.
    
    🔥 PHASE 1 OPTIMIZATION: Consolidates repetitive statements, uses bullets,
    and simplifies language while maintaining clarity.
    
    Args:
        language: Target language
        level: CEFR level
        topic: Topic name (if applicable)
        user_prompt: Custom user prompt (if applicable)
        week_focus: Learning plan week focus (if applicable)
    
    Returns:
        Consolidated instruction string
    """
    
    # Determine focus area
    focus_area = user_prompt or topic or week_focus or f"{language} conversation"
    
    return f"""
# Teaching Approach

## Your Role
Proactive {language} tutor for {level} learners

## Core Behavior
- Lead conversations; don't ask permission
- Move to next activity after corrections
- Follow structured session plan
- Example: "Great! Now let's practice..."

## Content Focus
CRITICAL: Keep all conversation about: {focus_area}
- Redirect off-topic attempts immediately
- Maintain educational focus throughout
- Connect practice to learning objectives

# Safety Guidelines

## Refuse Immediately
- Violence, weapons, illegal content
- Sexual/adult themes
- Hate speech, discrimination
- Personal information requests
- Self-harm, dangerous activities

## Redirect Script
"Let's focus on {language} practice with {focus_area}. This serves your learning goals."

# Language Rules

## {language} Only
- Respond exclusively in {language}
- If student uses other language: "Let's practice in {language}. Try saying that in {language}."
- Adapt complexity to {level} level

## Corrections
- Provide natural, immediate corrections
- Use format: "Try: [correct form]"
- Continue conversation flow
"""


def build_topic_context(topic_name: str, topic_description: str = None, 
                       research_content: str = None) -> str:
    """
    Build concise topic context section.
    
    Args:
        topic_name: Name of the topic
        topic_description: Optional description
        research_content: Optional research data
    
    Returns:
        Formatted topic context
    """
    context = f"""
# Topic: {topic_name}
"""
    
    if topic_description:
        context += f"\n{topic_description}\n"
    
    if research_content:
        # Truncate research if too long
        max_length = 500
        if len(research_content) > max_length:
            research_content = research_content[:max_length] + "..."
        context += f"\n## Key Information\n{research_content}\n"
    
    context += f"""
## Conversation Guidance
- Use topic vocabulary naturally
- Ask engaging questions
- Encourage elaboration
- Provide relevant examples
"""
    
    return context


def build_assessment_context_concise(assessment_data: dict) -> str:
    """
    Build concise assessment context (reduced from verbose version).
    
    🔥 PHASE 1 OPTIMIZATION: Reduces assessment context by ~50%
    
    Args:
        assessment_data: Assessment data dictionary
    
    Returns:
        Concise assessment context
    """
    overall_score = assessment_data.get('overall_score', 0)
    recommended_level = assessment_data.get('recommended_level', 'B1')
    strengths = assessment_data.get('strengths', [])
    areas = assessment_data.get('areas_for_improvement', [])
    
    # Get skill scores
    pronunciation = assessment_data.get('pronunciation', {}).get('score', 0)
    grammar = assessment_data.get('grammar', {}).get('score', 0)
    vocabulary = assessment_data.get('vocabulary', {}).get('score', 0)
    fluency = assessment_data.get('fluency', {}).get('score', 0)
    
    return f"""
# Student Profile

## Scores
Overall: {overall_score}/100 | Level: {recommended_level}
Pronunciation: {pronunciation} | Grammar: {grammar} | Vocabulary: {vocabulary} | Fluency: {fluency}

## Focus
Strengths: {', '.join(strengths[:2]) if strengths else 'General communication'}
Improve: {', '.join(areas[:2]) if areas else 'Overall skills'}

## Approach
- Build on strengths
- Target improvement areas
- Match {recommended_level} difficulty
"""


def build_learning_plan_context_concise(plan_data: dict, week_number: int, 
                                       session_summaries: list = None) -> str:
    """
    Build concise learning plan context.
    
    🔥 PHASE 1 OPTIMIZATION: Reduces learning plan context by ~40%
    
    Args:
        plan_data: Learning plan data
        week_number: Current week number
        session_summaries: List of compressed session summaries
    
    Returns:
        Concise learning plan context
    """
    plan_content = plan_data.get('plan_content', {})
    weekly_schedule = plan_content.get('weekly_schedule', [])
    
    if not weekly_schedule or week_number > len(weekly_schedule):
        return ""
    
    current_week = weekly_schedule[week_number - 1]
    week_focus = current_week.get('focus', 'Building skills')
    activities = current_week.get('activities', [])
    
    context = f"""
# Learning Plan

## Current Week (Week {week_number})
Focus: {week_focus}
Activities: {', '.join(activities[:3]) if activities else 'Practice conversation'}
"""
    
    # Add compressed session summaries if available
    if session_summaries:
        from prompt_optimization_helpers import build_compressed_session_context
        context += build_compressed_session_context(session_summaries, max_summaries=3)
    
    context += """
## Session Goals
- Practice week's focus area
- Apply learning plan activities
- Build on previous progress
"""
    
    return context


def build_first_message_guidance(focus_area: str, is_custom_topic: bool = False) -> str:
    """
    Build concise first message guidance.
    
    Args:
        focus_area: Main focus area
        is_custom_topic: Whether this is a custom topic
    
    Returns:
        First message guidance
    """
    if is_custom_topic:
        return f"""
# First Message
Start immediately with {focus_area}:
"Let's talk about {focus_area}! [Share interesting fact]. What interests you?"

NOT: "Hello! How can I help you?"
"""
    else:
        return f"""
# First Message
Introduce {focus_area} and ask engaging question:
"Let's talk about {focus_area}! What interests you most?"
"""
