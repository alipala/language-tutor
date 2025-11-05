"""
Prompt Optimization Helper Functions
Phase 0: Critical Optimizations for Token Reduction

This module contains helper functions for optimizing prompts to reduce token usage
and improve cost efficiency while maintaining quality.
"""

from openai import OpenAI
import os
from typing import Dict, Any

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_personality_tone_section(language: str, level: str) -> str:
    """
    Build the Personality & Tone section with STRICT 2-sentence response limit.
    
    This is a critical optimization that reduces AI response tokens by ~50%
    (from 60 tokens to 30 tokens per response).
    
    Args:
        language: Target language for learning
        level: CEFR level (A1, A2, B1, B2, C1, C2)
    
    Returns:
        Formatted personality and tone instructions
    """
    return f"""
# Personality & Tone

## Personality
- Friendly, encouraging {language} language tutor
- Patient and supportive with {level} learners
- Enthusiastic about language learning

## Tone
- Warm, conversational, never condescending
- Natural pacing, not rushed

## Length - STRICTLY ENFORCE ⚠️
- MAXIMUM 2 sentences per response
- Each sentence: 10-15 words maximum
- Be concise and direct
- ✅ Good: "Great job! Let's practice verbs now."
- ❌ Bad: "That was really excellent work on your pronunciation! I'm very impressed with how you handled that difficult word. Now, I think it would be beneficial for us to move on to practicing some verb conjugations, if that sounds good to you?"

## Variety
- Vary your responses; avoid repetition
- Use different sentence structures
- Mix questions, statements, and encouragement
"""


def build_reference_pronunciations() -> str:
    """
    Build the Reference Pronunciations section.
    
    🔥 PHASE 1 OPTIMIZATION: Ensures consistent brand pronunciation
    and professional delivery of technical terms.
    
    Returns:
        Formatted pronunciation guidance
    """
    return """
# Reference Pronunciations

When voicing these words, use the respective pronunciations:
- Pronounce "MyTaco" as "my-TAH-co" (not "my-TACK-o")
- Pronounce "CEFR" as "SEE-fer" (not "C-E-F-R")
- Pronounce "A1" as "A-one" (not "A-first")
- Pronounce "A2" as "A-two" (not "A-second")
- Pronounce "B1" as "B-one" (not "B-first")
- Pronounce "B2" as "B-two" (not "B-second")
- Pronounce "C1" as "C-one" (not "C-first")
- Pronounce "C2" as "C-two" (not "C-second")
"""


def build_sample_phrases(language: str) -> str:
    """
    Build the Sample Phrases section for consistent brand voice.
    
    🔥 PHASE 1 OPTIMIZATION: Provides style guidance for natural,
    consistent conversation flow.
    
    Args:
        language: Target language for learning
    
    Returns:
        Formatted sample phrases
    """
    return f"""
# Sample Phrases

Below are sample examples for inspiration. DO NOT ALWAYS USE THESE EXAMPLES - VARY YOUR RESPONSES.

## Acknowledgements
"On it." "One moment." "Good question." "I see." "Got it."

## Clarifiers
"Do you mean A or B?" "Can you say that again?" "Which one?" "Tell me more."

## Bridges
"Here's the plan." "Let's try this." "Now for..." "Next up..."

## Encouragement (brief)
"Nice work!" "You're improving!" "Keep going!" "Almost there!" "Excellent!"

## Corrections (gentle)
"Try: [correct form]" "Actually, it's [correction]" "Close! Say: [correct]"

## Closers
"Anything else?" "Ready to wrap up?" "Great session!" "See you next time!"

## {language}-Specific
Use natural {language} expressions appropriate for the learner's level.
Keep all phrases concise and conversational.
"""


def compress_session_summary(summary: str) -> str:
    """
    Compress session summary to 30-50 tokens using gpt-4o-mini.
    
    This is a CRITICAL optimization that reduces session summary tokens by 93%
    (from 696 tokens to ~40 tokens per summary).
    
    Format: "[Skill practiced] - [Main improvement]" (max 15 words)
    
    Args:
        summary: Full session summary text
    
    Returns:
        Compressed summary (30-50 tokens)
    
    Example:
        Input: "The student practiced past tense verbs during this session..."
        Output: "Past tense verbs - Improved accuracy with irregular forms"
    """
    try:
        print(f"[COMPRESSION] Compressing summary: {len(summary)} chars")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Compress this session summary to max 15 words in format '[Skill practiced] - [Main improvement]':

{summary}

Compressed summary:"""
            }],
            max_tokens=30,
            temperature=0.3
        )
        
        if not response or not response.choices:
            print(f"[COMPRESSION] ❌ No response from OpenAI")
            # Fallback: truncate to first 100 chars
            return summary[:100] + "..."
        
        compressed = response.choices[0].message.content.strip()
        
        # Calculate compression ratio
        original_tokens = len(summary.split())
        compressed_tokens = len(compressed.split())
        compression_ratio = (compressed_tokens / original_tokens * 100) if original_tokens > 0 else 0
        
        print(f"[COMPRESSION] ✅ Original: {len(summary)} chars ({original_tokens} words)")
        print(f"[COMPRESSION] ✅ Compressed: {len(compressed)} chars ({compressed_tokens} words)")
        print(f"[COMPRESSION] ✅ Compression ratio: {compression_ratio:.1f}%")
        
        return compressed
        
    except Exception as e:
        print(f"[COMPRESSION] ❌ Error: {str(e)}")
        # Fallback: truncate to first 100 chars
        return summary[:100] + "..."


def build_compressed_session_context(session_summaries: list, max_summaries: int = 3) -> str:
    """
    Build compressed session context from summaries.
    
    Uses ultra-compressed format to reduce tokens by 93%.
    
    Args:
        session_summaries: List of session summary strings
        max_summaries: Maximum number of recent summaries to include (default: 3)
    
    Returns:
        Formatted session context string
    """
    if not session_summaries:
        return ""
    
    # Take only last N summaries
    recent_summaries = session_summaries[-max_summaries:]
    
    # Calculate session numbers
    total_sessions = len(session_summaries)
    start_session = total_sessions - len(recent_summaries) + 1
    
    # Build compressed context
    summary_lines = []
    for i, summary in enumerate(recent_summaries, start=start_session):
        summary_lines.append(f"- S{i}: {summary}")
    
    context = f"""
📝 RECENT PROGRESS:
{chr(10).join(summary_lines)}
"""
    
    print(f"[SESSION_CONTEXT] Built context with {len(recent_summaries)} summaries")
    print(f"[SESSION_CONTEXT] Context length: {len(context)} chars")
    
    return context


def build_truncation_config() -> Dict[str, Any]:
    """
    Build truncation configuration for OpenAI Realtime API.
    
    This prevents runaway costs in long sessions (20+ turns) by automatically
    dropping older conversation history while maintaining cache effectiveness.
    
    Returns:
        Truncation configuration dict
    """
    return {
        "type": "retention_ratio",
        "retention_ratio": 0.8,  # Drop 20% extra to maintain cache
        "token_limits": {
            "post_instructions": 8000  # Limit conversation history
        }
    }


def log_token_usage(usage_data: Dict[str, Any]) -> None:
    """
    Log token usage with compression statistics.
    
    Args:
        usage_data: Dictionary containing token usage information
    """
    input_tokens = usage_data.get('input_tokens', 0)
    output_tokens = usage_data.get('output_tokens', 0)
    cached_tokens = usage_data.get('cached_tokens', 0)
    
    cache_hit_rate = (cached_tokens / input_tokens * 100) if input_tokens > 0 else 0
    
    print("="*80)
    print(f"📊 [TOKEN_USAGE] Token Usage Report")
    print(f"Input tokens: {input_tokens:,}")
    print(f"Output tokens: {output_tokens:,}")
    print(f"Cached tokens: {cached_tokens:,}")
    print(f"Cache hit rate: {cache_hit_rate:.1f}%")
    print(f"Total tokens: {input_tokens + output_tokens:,}")
    print("="*80)


def build_conversation_flow_section(language: str, level: str, topic: str = None) -> str:
    """
    Build conversation flow section with 3 clear phases and state transitions.
    
    🔥 PHASE 2 OPTIMIZATION: Implements structured conversation flow with:
    - Clear 3-phase structure (Greeting, Practice, Wrap-up)
    - Exit criteria for each phase
    - Goal statements and guidance
    - Better session management
    
    Args:
        language: Target language for learning
        level: CEFR level (A1, A2, B1, B2, C1, C2)
        topic: Optional topic name for focused conversation
    
    Returns:
        Formatted conversation flow instructions
    """
    topic_context = f" about {topic}" if topic else ""
    
    return f"""
# Conversation Flow

## Phase 1: Greeting (30 seconds)
**Goal:** Welcome learner and establish conversation focus
**How to respond:**
- Greet warmly in {language}
- Introduce topic{topic_context}
- Ask one opening question
- CRITICAL: Max 2 sentences total

**Exit Criteria:** Learner responds to opening question

**Example:**
"¡Hola! Hablemos de viajes. ¿Cuál es tu destino favorito?"

---

## Phase 2: Practice (4 minutes)
**Goal:** Engage in focused {language} conversation at {level} level
**How to respond:**
- Ask follow-up questions based on learner's responses
- Provide natural, immediate corrections when needed
- Encourage elaboration with prompts
- Use {level}-appropriate vocabulary and structures
- CRITICAL: Max 2 sentences per turn

**Exit Criteria:** 
- 4 minutes elapsed OR
- Learner signals end ("I'm done", "That's all", etc.)

**Correction Format:**
"Try: [correct form]" then continue conversation

**Example:**
"Interesante. ¿Qué te gustó más de ese lugar?"

---

## Phase 3: Wrap-up (30 seconds)
**Goal:** Summarize progress and encourage continued practice
**How to respond:**
- Highlight 1-2 specific strengths observed
- Mention 1 area for improvement
- Encourage continued practice
- CRITICAL: Max 2 sentences total

**Exit Criteria:** Summary delivered

**Example:**
"¡Excelente trabajo con el vocabulario de viajes! Sigue practicando los verbos en pasado."

---

## State Transition Rules
- Move from Greeting → Practice after learner's first response
- Stay in Practice until time limit or learner signals end
- Move to Wrap-up when Practice phase ends
- End session after Wrap-up delivered
"""


def build_safety_escalation_section(language: str) -> str:
    """
    Build safety and escalation section with clear triggers and procedures.
    
    🔥 PHASE 2 OPTIMIZATION: Provides clear safety guidelines with:
    - Explicit escalation triggers
    - Mandatory escalation scripts
    - Professional handling procedures
    - Clear failure handling
    
    Args:
        language: Target language for learning
    
    Returns:
        Formatted safety and escalation instructions
    """
    return f"""
# Safety & Escalation

## When to Escalate Immediately (No Troubleshooting)
Escalate if learner exhibits ANY of these:

1. **Safety Risks:**
   - Self-harm mentions or threats
   - Threats toward others
   - Harassment or abusive language
   - Dangerous activity discussion

2. **Explicit Requests:**
   - "I want a human tutor"
   - "Connect me to a real person"
   - "This isn't working, get me help"

3. **Severe Dissatisfaction:**
   - Repeated complaints (3+ times)
   - Profanity directed at system
   - Extreme frustration expressed

4. **Out-of-Scope Requests:**
   - Medical advice or diagnosis
   - Legal advice or guidance
   - Financial advice
   - Personal counseling

---

## Mandatory Escalation Script

When escalation is needed, say EXACTLY this in {language}:

**English:** "I understand this is important. Let me connect you with a human tutor who can help better."

**Spanish:** "Entiendo que esto es importante. Permíteme conectarte con un tutor humano que puede ayudarte mejor."

**French:** "Je comprends que c'est important. Permettez-moi de vous connecter avec un tuteur humain qui peut mieux vous aider."

**German:** "Ich verstehe, dass dies wichtig ist. Lassen Sie mich Sie mit einem menschlichen Tutor verbinden, der besser helfen kann."

**Dutch:** "Ik begrijp dat dit belangrijk is. Laat me je verbinden met een menselijke tutor die beter kan helpen."

Then END the session gracefully.

---

## Examples Requiring Immediate Escalation

❌ "I hate this stupid app, get me a real teacher!"
→ Use escalation script, end session

❌ "Can you diagnose why I can't pronounce this sound?"
→ Use escalation script, end session

❌ "I'm feeling really depressed about my progress"
→ Use escalation script, end session

❌ User uses threatening or abusive language
→ Use escalation script, end session

---

## Failure Handling

If escalation is triggered:
1. Use mandatory escalation script
2. Do NOT attempt to continue teaching
3. Do NOT try to resolve the issue yourself
4. End session immediately after script
5. Log incident for review

**Remember:** Your role is language teaching only. Escalate anything beyond this scope.
"""


def build_state_specific_sample_phrases(language: str, phase: str = "all") -> str:
    """
    Build state-specific sample phrases for each conversation phase.
    
    🔥 PHASE 2 OPTIMIZATION: Extends sample phrases with phase-specific examples
    for natural conversation flow through all states.
    
    Args:
        language: Target language for learning
        phase: Which phase to get phrases for ("greeting", "practice", "wrap-up", or "all")
    
    Returns:
        Formatted sample phrases for specified phase(s)
    """
    
    greeting_phrases = f"""
## Greeting Phase Phrases (30 seconds)

### Warm Welcomes
"Hello! Ready to practice?" "Hi there! Let's begin." "Welcome! Excited to start?"

### Topic Introductions
"Today's topic: [topic]" "Let's explore [topic]" "We'll discuss [topic]"

### Opening Questions
"What interests you?" "Tell me your thoughts." "Where should we start?"

### {language}-Specific Greetings
Use natural {language} greetings appropriate for the learner's level.
Keep it brief and inviting.
"""
    
    practice_phrases = f"""
## Practice Phase Phrases (4 minutes)

### Follow-up Questions
"Tell me more." "Why is that?" "What happened next?" "How did you feel?"

### Natural Corrections
"Try: [correct form]" "Actually: [correction]" "Better: [improved version]"

### Encouragement
"Good point!" "Interesting!" "Keep going!" "Nice work!"

### Elaboration Prompts
"Can you explain?" "Give an example." "What do you mean?" "Describe it."

### Transitions
"Now let's..." "Next topic..." "Moving on..." "Another question..."

### {language}-Specific Practice
Use natural {language} expressions for:
- Asking clarifying questions
- Providing gentle corrections
- Encouraging elaboration
- Transitioning between topics

**Remember:** Keep all responses concise (max 2 sentences)
"""
    
    wrapup_phrases = f"""
## Wrap-up Phase Phrases (30 seconds)

### Positive Feedback
"Great session!" "Well done!" "Excellent progress!" "Nice improvement!"

### Specific Strengths
"Your [skill] was strong." "Good use of [grammar point]." "Clear [pronunciation]."

### Improvement Areas
"Practice [skill] more." "Focus on [area]." "Work on [grammar point]."

### Encouragement
"Keep practicing!" "You're improving!" "See you next time!" "Great effort!"

### {language}-Specific Closers
Use natural {language} expressions for:
- Summarizing progress
- Highlighting achievements
- Suggesting next steps
- Encouraging continued practice
"""
    
    if phase == "greeting":
        return greeting_phrases
    elif phase == "practice":
        return practice_phrases
    elif phase == "wrap-up":
        return wrapup_phrases
    else:  # "all"
        return f"""
# State-Specific Sample Phrases

{greeting_phrases}

{practice_phrases}

{wrapup_phrases}

## General Guidelines
- Vary your responses across all phases
- Match phrases to learner's level
- Keep all responses concise (2 sentences max)
- Use natural {language} expressions
- Adapt tone to conversation phase
"""


# ============================================================================
# PHASE 3: OPTIMIZATION FUNCTIONS
# ============================================================================

def build_speed_instructions() -> str:
    """
    Build speed and pacing instructions for natural audio delivery.
    
    🔥 PHASE 3 OPTIMIZATION: Improves audio experience with natural pacing
    and delivery guidance.
    
    Returns:
        Formatted speed and pacing instructions
    """
    return """
# Speed & Pacing

## Delivery Speed
- Speak at a natural, conversational pace
- Do NOT rush through responses
- Do NOT sound robotic or mechanical
- Match the learner's speaking speed when appropriate

## Pauses
- Use natural pauses between sentences
- Brief pause after questions (0.5-1 second)
- Pause before corrections to let learner process

## Emphasis
- Emphasize key vocabulary words slightly
- Use natural intonation for questions
- Vary tone to maintain engagement

## Avoid
- Speaking too fast (learners need processing time)
- Monotone delivery (sounds robotic)
- Unnatural pauses or hesitations
- Rushed corrections
"""


def build_optimized_assessment_context(assessment_data: Dict[str, Any]) -> str:
    """
    Build optimized assessment context with reduced verbosity.
    
    🔥 PHASE 3 OPTIMIZATION: Reduces assessment context tokens by ~40%
    while maintaining essential information.
    
    Args:
        assessment_data: Dictionary containing assessment results
    
    Returns:
        Formatted, optimized assessment context
    """
    if not assessment_data:
        return ""
    
    # Extract key metrics only
    overall_score = assessment_data.get('overall_score', 0)
    recommended_level = assessment_data.get('recommended_level', 'B1')
    
    # Get top 2 strengths and improvements
    strengths = assessment_data.get('strengths', [])[:2]
    improvements = assessment_data.get('areas_for_improvement', [])[:2]
    
    # Build concise context
    context = f"""
📊 LEARNER PROFILE:
Level: {recommended_level} | Score: {overall_score}/100
Strengths: {', '.join(strengths) if strengths else 'General communication'}
Focus: {', '.join(improvements) if improvements else 'Overall improvement'}
"""
    
    print(f"[ASSESSMENT_CONTEXT] Optimized context: {len(context)} chars")
    return context


def build_dynamic_context_injection(
    language: str,
    level: str,
    topic: str = None,
    assessment_data: Dict[str, Any] = None,
    session_summaries: list = None
) -> Dict[str, str]:
    """
    Build dynamic context for session.update injection.
    
    🔥 PHASE 3 OPTIMIZATION: Separates static instructions from dynamic context
    for better cache utilization and token efficiency.
    
    Args:
        language: Target language
        level: CEFR level
        topic: Optional topic
        assessment_data: Optional assessment results
        session_summaries: Optional previous session summaries
    
    Returns:
        Dictionary with 'static' and 'dynamic' context sections
    """
    # Static context (cached)
    static_context = {
        "language": language,
        "level": level,
        "topic": topic or "general conversation"
    }
    
    # Dynamic context (injected via session.update)
    dynamic_context = {}
    
    if assessment_data:
        dynamic_context["assessment"] = build_optimized_assessment_context(assessment_data)
    
    if session_summaries:
        dynamic_context["progress"] = build_compressed_session_context(session_summaries, max_summaries=2)
    
    print(f"[DYNAMIC_CONTEXT] Static keys: {list(static_context.keys())}")
    print(f"[DYNAMIC_CONTEXT] Dynamic keys: {list(dynamic_context.keys())}")
    
    return {
        "static": static_context,
        "dynamic": dynamic_context
    }


# ============================================================================
# PHASE 4: VALIDATION & METRICS FUNCTIONS
# ============================================================================

def calculate_token_savings(
    original_tokens: int,
    optimized_tokens: int
) -> Dict[str, Any]:
    """
    Calculate token savings and cost impact.
    
    🔥 PHASE 4 VALIDATION: Measures optimization effectiveness.
    
    Args:
        original_tokens: Token count before optimization
        optimized_tokens: Token count after optimization
    
    Returns:
        Dictionary with savings metrics
    """
    tokens_saved = original_tokens - optimized_tokens
    percentage_saved = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0
    
    # Cost calculations (gpt-realtime-mini pricing)
    cost_per_token_input = 0.60 / 1_000_000  # $0.60 per 1M tokens
    cost_per_token_output = 2.40 / 1_000_000  # $2.40 per 1M tokens
    
    # Assume 70% input, 30% output
    input_savings = tokens_saved * 0.7 * cost_per_token_input
    output_savings = tokens_saved * 0.3 * cost_per_token_output
    total_cost_savings = input_savings + output_savings
    
    # Monthly projections (1000 sessions)
    monthly_savings = total_cost_savings * 1000
    annual_savings = monthly_savings * 12
    
    return {
        "tokens_saved": tokens_saved,
        "percentage_saved": round(percentage_saved, 2),
        "cost_savings_per_session": round(total_cost_savings, 6),
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens
    }


def track_quality_metrics(
    session_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Track quality metrics for validation.
    
    🔥 PHASE 4 VALIDATION: Monitors conversation quality and user satisfaction.
    
    Args:
        session_data: Dictionary containing session information
    
    Returns:
        Dictionary with quality metrics
    """
    metrics = {
        "session_id": session_data.get("session_id"),
        "duration_seconds": session_data.get("duration_seconds", 0),
        "turns_count": session_data.get("turns_count", 0),
        "topic_adherence": session_data.get("topic_adherence", True),
        "instruction_following": session_data.get("instruction_following", True),
        "user_satisfaction": session_data.get("user_satisfaction", 0),  # 1-5 stars
        "completion_status": session_data.get("completion_status", "completed"),
        "escalation_triggered": session_data.get("escalation_triggered", False),
        "phase_transitions": session_data.get("phase_transitions", []),
        "average_response_length": session_data.get("average_response_length", 0)
    }
    
    # Calculate quality score (0-100)
    quality_score = 0
    if metrics["topic_adherence"]:
        quality_score += 25
    if metrics["instruction_following"]:
        quality_score += 25
    if metrics["user_satisfaction"] >= 4:
        quality_score += 25
    if metrics["completion_status"] == "completed":
        quality_score += 25
    
    metrics["quality_score"] = quality_score
    
    return metrics


def generate_optimization_report(
    phase: str,
    metrics: Dict[str, Any]
) -> str:
    """
    Generate optimization report for a specific phase.
    
    🔥 PHASE 4 VALIDATION: Creates comprehensive reports for analysis.
    
    Args:
        phase: Phase name (0, 1, 2, 3, or 4)
        metrics: Dictionary containing metrics data
    
    Returns:
        Formatted report string
    """
    report = f"""
# Phase {phase} Optimization Report

## Token Savings
- Original tokens: {metrics.get('original_tokens', 0):,}
- Optimized tokens: {metrics.get('optimized_tokens', 0):,}
- Tokens saved: {metrics.get('tokens_saved', 0):,}
- Percentage saved: {metrics.get('percentage_saved', 0)}%

## Cost Impact
- Cost savings per session: ${metrics.get('cost_savings_per_session', 0):.6f}
- Monthly savings (1000 sessions): ${metrics.get('monthly_savings', 0):.2f}
- Annual savings: ${metrics.get('annual_savings', 0):.2f}

## Quality Metrics
- Quality score: {metrics.get('quality_score', 0)}/100
- Topic adherence: {metrics.get('topic_adherence', 'N/A')}
- Instruction following: {metrics.get('instruction_following', 'N/A')}
- User satisfaction: {metrics.get('user_satisfaction', 0)}/5 stars
- Completion rate: {metrics.get('completion_status', 'N/A')}

## Session Statistics
- Average duration: {metrics.get('duration_seconds', 0)} seconds
- Average turns: {metrics.get('turns_count', 0)}
- Escalations: {metrics.get('escalation_triggered', False)}

## Recommendations
"""
    
    # Add phase-specific recommendations
    if metrics.get('percentage_saved', 0) < 20:
        report += "- Consider additional optimization opportunities\n"
    if metrics.get('quality_score', 0) < 75:
        report += "- Review quality metrics and adjust instructions\n"
    if metrics.get('user_satisfaction', 0) < 4:
        report += "- Gather user feedback for improvements\n"
    
    report += "\n---\n"
    
    return report


def validate_optimization_effectiveness(
    before_metrics: Dict[str, Any],
    after_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate optimization effectiveness by comparing before/after metrics.
    
    🔥 PHASE 4 VALIDATION: Ensures optimizations improve both cost and quality.
    
    Args:
        before_metrics: Metrics before optimization
        after_metrics: Metrics after optimization
    
    Returns:
        Dictionary with validation results
    """
    validation = {
        "token_reduction_achieved": False,
        "quality_maintained": False,
        "cost_savings_achieved": False,
        "overall_success": False
    }
    
    # Check token reduction (target: 20%+ reduction)
    token_reduction = (
        (before_metrics.get('tokens', 0) - after_metrics.get('tokens', 0)) /
        before_metrics.get('tokens', 1) * 100
    )
    validation["token_reduction_achieved"] = token_reduction >= 20
    validation["token_reduction_percentage"] = round(token_reduction, 2)
    
    # Check quality maintenance (target: quality score >= 75)
    quality_before = before_metrics.get('quality_score', 0)
    quality_after = after_metrics.get('quality_score', 0)
    validation["quality_maintained"] = quality_after >= 75 and quality_after >= (quality_before * 0.95)
    validation["quality_change"] = quality_after - quality_before
    
    # Check cost savings (target: positive savings)
    cost_savings = before_metrics.get('cost', 0) - after_metrics.get('cost', 0)
    validation["cost_savings_achieved"] = cost_savings > 0
    validation["cost_savings"] = round(cost_savings, 6)
    
    # Overall success requires all three
    validation["overall_success"] = (
        validation["token_reduction_achieved"] and
        validation["quality_maintained"] and
        validation["cost_savings_achieved"]
    )
    
    return validation
