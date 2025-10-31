"""
Batch Sentence Analysis Module
Processes multiple sentences in ONE API call for 90% cost reduction
"""

import os
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_batch_analysis_report(
    language: str,
    level: str,
    topic: str,
    conversation_transcript: str,
    user_sentences: List[str]
) -> Dict[str, Any]:
    """
    Generate a comprehensive batch analysis report using gpt-4o-mini.
    This replaces 7-8 individual API calls with ONE efficient batch call.
    
    Args:
        language: Target language being learned
        level: Proficiency level (A1, A2, B1, B2, C1, C2)
        topic: Conversation topic
        conversation_transcript: Full conversation history
        user_sentences: List of user's sentences to analyze
    
    Returns:
        Dictionary with:
        - session_summary: Overall session feedback
        - detailed_analysis: Array of sentence-by-sentence analysis
    """
    
    logger.info(f"[BATCH_ANALYSIS] 🎯 Starting batch analysis for {len(user_sentences)} sentences")
    logger.info(f"[BATCH_ANALYSIS] Language: {language}, Level: {level}, Topic: {topic}")
    
    # Validate inputs
    if not user_sentences or len(user_sentences) == 0:
        logger.warning("[BATCH_ANALYSIS] ⚠️ No sentences provided for analysis")
        return {
            "session_summary": f"Session completed with {language} practice at {level} level. No sentences were captured for detailed analysis.",
            "detailed_analysis": []
        }
    
    # Build the sentences text for the prompt
    sentences_text = "\n".join([f"{i+1}. {sentence}" for i, sentence in enumerate(user_sentences)])
    
    # Build the comprehensive prompt
    system_prompt = f"""You are an expert language learning analyst. Your task is to provide a comprehensive end-of-session report for a language learner.

Your response MUST be a single, valid JSON object. Do not include any text or markdown before or after the JSON block.

The JSON object must have two top-level keys:
1. `session_summary`: A concise, encouraging summary of the conversation (3-4 sentences).
2. `detailed_analysis`: An array of JSON objects, one for each sentence provided.

For the `session_summary`, you must:
- Provide a 3-4 sentence overview
- Mention the main topics discussed (e.g., "{topic}")
- Highlight 1-2 key vocabulary words or concepts the user practiced
- Give an overall encouraging comment on their performance

For EACH object in the `detailed_analysis` array, provide these exact fields:
- `original_sentence`: The exact sentence the user said
- `grammatical_score`: A number (0-100) rating grammatical correctness
- `vocabulary_score`: A number (0-100) rating vocabulary appropriateness and range
- `complexity_score`: A number (0-100) rating sentence complexity and structure sophistication
- `appropriateness_score`: A number (0-100) rating how appropriate the language is for {level} level
- `overall_score`: A number (0-100) calculated as the average of all scores above
- `corrected_text`: The most natural-sounding correction of the original sentence
- `grammar_issues`: An array of strings, each naming a specific grammar issue (e.g., "Subject-verb agreement", "Incorrect tense"). If no issues, use empty array []
- `improvement_suggestions`: An array of strings, each providing a clear explanation of how to fix issues. If no issues, provide general tips
- `level_appropriate_alternatives`: An array of strings (1-2 items) showing other ways to express the same idea suitable for {level} level

Analyze the sentences in the context of the full conversation, not in isolation."""

    user_prompt = f"""Please generate the end-of-session report based on the following data.

**Language:** {language}
**Proficiency Level:** {level}
**Conversation Topic:** {topic}

**Full Conversation Transcript:**
{conversation_transcript}

**Sentences to Analyze:**
{sentences_text}

Remember, respond with ONLY the valid JSON object. No markdown, no explanations, just the JSON."""

    try:
        logger.info("[BATCH_ANALYSIS] 📤 Sending request to OpenAI gpt-4o-mini")
        
        # Make the API call to gpt-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4096,
            temperature=0.3,  # Lower temperature for more consistent JSON
        )
        
        # Extract the JSON response
        response_text = response.choices[0].message.content.strip()
        
        logger.info(f"[BATCH_ANALYSIS] 📥 Received response: {len(response_text)} characters")
        
        # Remove markdown code fences if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        # Parse the JSON with better error handling
        try:
            batch_report = json.loads(response_text.strip())
        except json.JSONDecodeError as json_err:
            logger.error(f"[BATCH_ANALYSIS] ❌ JSON parsing failed at position {json_err.pos}")
            logger.error(f"[BATCH_ANALYSIS] ❌ Error: {json_err.msg}")
            
            # Try to fix common JSON issues
            # Remove trailing commas before closing braces/brackets
            import re
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
            
            try:
                batch_report = json.loads(fixed_text)
                logger.info("[BATCH_ANALYSIS] ✅ Fixed JSON by removing trailing commas")
            except:
                # If still fails, return fallback
                raise json_err
        
        # Validate the structure
        if "session_summary" not in batch_report or "detailed_analysis" not in batch_report:
            logger.error("[BATCH_ANALYSIS] ❌ Invalid response structure from AI")
            raise ValueError("Invalid response structure from AI - missing required keys")
        
        # Validate each sentence analysis has required fields
        for idx, analysis in enumerate(batch_report.get("detailed_analysis", [])):
            required_fields = ["original_sentence", "grammatical_score", "vocabulary_score", 
                             "complexity_score", "appropriateness_score", "overall_score",
                             "corrected_text", "grammar_issues", "improvement_suggestions", 
                             "level_appropriate_alternatives"]
            
            for field in required_fields:
                if field not in analysis:
                    logger.warning(f"[BATCH_ANALYSIS] ⚠️ Sentence {idx+1} missing field: {field}")
                    # Add default values for missing fields
                    if field.endswith("_score"):
                        analysis[field] = 70
                    elif field == "grammar_issues":
                        analysis[field] = []
                    elif field == "improvement_suggestions":
                        analysis[field] = ["Analysis incomplete"]
                    elif field == "level_appropriate_alternatives":
                        analysis[field] = [analysis.get("original_sentence", "")]
                    elif field == "corrected_text":
                        analysis[field] = analysis.get("original_sentence", "")
        
        # Log token usage
        if hasattr(response, 'usage'):
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate cost (gpt-4o-mini pricing)
            input_cost = (input_tokens / 1_000_000) * 0.150  # $0.150 per 1M input tokens
            output_cost = (output_tokens / 1_000_000) * 0.600  # $0.600 per 1M output tokens
            total_cost = input_cost + output_cost
            
            logger.info(f"[BATCH_ANALYSIS] 💰 Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
            logger.info(f"[BATCH_ANALYSIS] 💰 Cost - Input: ${input_cost:.6f}, Output: ${output_cost:.6f}, Total: ${total_cost:.6f}")
        
        logger.info(f"[BATCH_ANALYSIS] ✅ Successfully analyzed {len(user_sentences)} sentences")
        logger.info(f"[BATCH_ANALYSIS] ✅ Generated {len(batch_report.get('detailed_analysis', []))} analysis results")
        
        return batch_report
        
    except json.JSONDecodeError as e:
        logger.error(f"[BATCH_ANALYSIS] ❌ Failed to parse JSON: {str(e)}")
        logger.error(f"[BATCH_ANALYSIS] ❌ Raw response (first 500 chars): {response_text[:500]}...")
        
        # Return fallback response
        return {
            "session_summary": f"Session completed with {len(user_sentences)} sentences in {language} at {level} level. Technical issue prevented detailed analysis.",
            "detailed_analysis": [
                {
                    "original_sentence": sentence,
                    "grammatical_score": 70,
                    "vocabulary_score": 70,
                    "complexity_score": 70,
                    "appropriateness_score": 70,
                    "overall_score": 70,
                    "corrected_text": sentence,
                    "grammar_issues": [],
                    "improvement_suggestions": ["Analysis unavailable - please try again"],
                    "level_appropriate_alternatives": [sentence]
                }
                for sentence in user_sentences
            ]
        }
        
    except Exception as e:
        logger.error(f"[BATCH_ANALYSIS] ❌ Unexpected error: {str(e)}")
        
        # Return fallback response
        return {
            "session_summary": f"Session completed with {len(user_sentences)} sentences in {language} at {level} level. Technical issue prevented detailed analysis.",
            "detailed_analysis": [
                {
                    "original_sentence": sentence,
                    "grammatical_score": 70,
                    "vocabulary_score": 70,
                    "complexity_score": 70,
                    "appropriateness_score": 70,
                    "overall_score": 70,
                    "corrected_text": sentence,
                    "grammar_issues": [],
                    "improvement_suggestions": ["Analysis unavailable - please try again"],
                    "level_appropriate_alternatives": [sentence]
                }
                for sentence in user_sentences
            ]
        }
