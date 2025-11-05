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
