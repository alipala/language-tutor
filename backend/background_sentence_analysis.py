from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
from fastapi import HTTPException
import openai
import httpx
from sentence_assessment import create_openai_client, analyze_sentence

# Request model for sentence evaluation
class SentenceEvaluationRequest(BaseModel):
    text: str
    language: str
    level: str
    conversation_context: Optional[str] = None

# Response model for sentence evaluation
class SentenceEvaluationResponse(BaseModel):
    should_analyze: bool
    reason: str
    confidence: float  # 0-1

# Request model for background analysis
class BackgroundAnalysisRequest(BaseModel):
    text: str
    language: str
    level: str
    exercise_type: Optional[str] = "free"
    conversation_context: Optional[str] = None

# Response model for background analysis
class BackgroundAnalysisResponse(BaseModel):
    analysis_id: str
    recognized_text: str
    grammatical_score: float
    vocabulary_score: float
    complexity_score: float
    appropriateness_score: float
    overall_score: float
    grammar_issues: List[Dict]
    improvement_suggestions: List[str]
    corrected_text: Optional[str] = None
    level_appropriate_alternatives: Optional[List[str]] = None
    timestamp: str

async def evaluate_sentence_worthiness(text: str, language: str, level: str, conversation_context: Optional[str] = None) -> Dict:
    """
    Evaluate whether a sentence is substantial enough to warrant analysis.
    Uses AI to determine if the sentence contains meaningful language learning content.
    """
    
    # Quick filters for obviously non-substantial content
    if not text or len(text.strip()) < 3:
        return {
            "should_analyze": False,
            "reason": "Text too short",
            "confidence": 1.0
        }
    
    # Common short responses that don't need analysis
    short_responses = [
        "yes", "no", "ok", "okay", "sure", "maybe", "thanks", "thank you",
        "hi", "hello", "bye", "goodbye", "me too", "same", "exactly",
        "right", "correct", "wrong", "true", "false", "good", "bad",
        "nice", "great", "awesome", "terrible", "awful"
    ]
    
    # Check if it's just a short response
    cleaned_text = text.strip().lower().replace(".", "").replace("!", "").replace("?", "")
    if cleaned_text in short_responses:
        return {
            "should_analyze": False,
            "reason": "Simple acknowledgment or short response",
            "confidence": 0.9
        }
    
    # If text is very short (under 5 words), likely not substantial
    word_count = len(text.split())
    if word_count < 5:
        return {
            "should_analyze": False,
            "reason": "Too few words for meaningful analysis",
            "confidence": 0.8
        }
    
    # Use AI to evaluate more complex cases
    try:
        client = create_openai_client()
        
        system_prompt = f"""
        You are an AI language learning assistant evaluating whether a student's sentence is substantial enough for grammatical and linguistic analysis.

        Consider a sentence "substantial enough" if it contains:
        1. Complete thoughts or meaningful expressions (not just "yes", "ok", "me too")
        2. Grammar structures that can be analyzed (verbs, sentence structure, etc.)
        3. Vocabulary that demonstrates language use beyond basic acknowledgments
        4. At least 5-8 words or a complete sentence structure
        5. Learning opportunities (potential errors, complex structures, etc.)

        Language: {language}
        Student Level: {level}
        
        Context: {conversation_context or "No previous context"}

        Respond in JSON format with:
        - should_analyze (boolean): true if worth analyzing
        - reason (string): brief explanation of decision
        - confidence (float): 0-1 confidence in decision
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use faster model for evaluation
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Evaluate this sentence: \"{text}\""}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"Error in AI sentence evaluation: {str(e)}")
        # Fallback: analyze if it's longer than 10 characters and has some complexity
        should_analyze = len(text.strip()) > 10 and word_count >= 4
        return {
            "should_analyze": should_analyze,
            "reason": "Fallback evaluation based on length and word count",
            "confidence": 0.6
        }

async def perform_background_analysis(text: str, language: str, level: str, exercise_type: str = "free", conversation_context: Optional[str] = None) -> Dict:
    """
    Perform the actual sentence analysis in the background.
    This is the same analysis as the current system but designed for background processing.
    """
    
    try:
        # Use the existing sentence analysis function
        analysis_result = await analyze_sentence(text, language, level, exercise_type)
        
        # Add metadata for background processing
        import uuid
        from datetime import datetime
        
        background_result = {
            "analysis_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            **analysis_result
        }
        
        return background_result
        
    except Exception as e:
        print(f"Error in background analysis: {str(e)}")
        # Return minimal error response
        import uuid
        from datetime import datetime
        
        return {
            "analysis_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "recognized_text": text,
            "grammatical_score": 0,
            "vocabulary_score": 0,
            "complexity_score": 0,
            "appropriateness_score": 0,
            "overall_score": 0,
            "grammar_issues": [],
            "improvement_suggestions": ["Analysis failed. Please try again."],
            "corrected_text": text,
            "level_appropriate_alternatives": []
        }

async def process_sentence_for_background_analysis(text: str, language: str, level: str, conversation_context: Optional[str] = None) -> Optional[Dict]:
    """
    Complete pipeline: evaluate if sentence should be analyzed, and if so, perform the analysis.
    Returns None if sentence doesn't warrant analysis, otherwise returns analysis results.
    """
    
    # Step 1: Evaluate if sentence is worth analyzing
    evaluation = await evaluate_sentence_worthiness(text, language, level, conversation_context)
    
    if not evaluation.get("should_analyze", False):
        print(f"Skipping analysis for: '{text}' - Reason: {evaluation.get('reason', 'Unknown')}")
        return None
    
    print(f"Performing background analysis for: '{text}' - Reason: {evaluation.get('reason', 'Substantial content detected')}")
    
    # Step 2: Perform the analysis
    analysis_result = await perform_background_analysis(text, language, level, "free", conversation_context)
    
    # Add evaluation metadata
    analysis_result["evaluation"] = evaluation
    
    return analysis_result
