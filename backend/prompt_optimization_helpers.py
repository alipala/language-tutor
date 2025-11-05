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
