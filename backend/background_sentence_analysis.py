from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
import uuid
from datetime import datetime
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

def detect_meta_conversational(text: str, language: str = "english") -> Dict:
    """
    Detect if text is meta-conversational (about managing the conversation itself)
    rather than demonstrating language learning content.
    Returns dict with isMetaConversational, confidence, category, and reason.
    """
    
    if not text or len(text.strip()) < 2:
        return {
            "isMetaConversational": False,
            "confidence": "high",
            "reason": "Text too short to be meta-conversational"
        }
    
    import re
    clean_text = text.strip().lower()
    
    # Define multilingual patterns for meta-conversational detection
    patterns = {
        # Clarification requests
        "clarification": {
            "english": [
                r"\b(didn't hear|can't hear|couldn't hear|cannot hear)\b",
                r"\b(repeat|say that again|come again|pardon|excuse me)\b",
                r"\b(what did you (say|just say))\b",
                r"\b(i (didn't|don't) understand)\b",
                r"\b(could you repeat)\b",
                r"\b(sorry,? what)\b"
            ],
            "spanish": [
                r"\b(no te escuché|no escuché|no oí)\b",
                r"\b(puedes repetir|puede repetir|repite)\b",
                r"\b(qué dijiste|qué dijo)\b",
                r"\b(no entendí|no entiendo)\b",
                r"\b(perdón|disculpa|cómo)\b"
            ],
            "french": [
                r"\b(je n'ai pas entendu|je n'entends pas)\b",
                r"\b(pouvez-vous répéter|peux-tu répéter|répétez)\b",
                r"\b(qu'avez-vous dit|qu'est-ce que vous avez dit)\b",
                r"\b(je ne comprends pas|je n'ai pas compris)\b",
                r"\b(pardon|excusez-moi|comment)\b"
            ],
            "german": [
                r"\b(ich habe (sie|dich) nicht gehört|ich höre nicht)\b",
                r"\b(können sie wiederholen|kannst du wiederholen|wiederholen)\b",
                r"\b(was haben sie gesagt|was hast du gesagt)\b",
                r"\b(ich verstehe nicht|ich habe nicht verstanden)\b",
                r"\b(entschuldigung|wie bitte)\b"
            ],
            "dutch": [
                r"\b(ik hoorde je niet|ik hoor je niet|niet gehoord)\b",
                r"\b(kun je herhalen|kunt u herhalen|herhaal)\b",
                r"\b(wat zei je|wat zei u)\b",
                r"\b(ik begrijp het niet|ik snap het niet)\b",
                r"\b(sorry|pardon|wat)\b"
            ],
            "portuguese": [
                r"\b(não te ouvi|não ouvi|não escutei)\b",
                r"\b(podes repetir|pode repetir|repete)\b",
                r"\b(o que disseste|o que disse)\b",
                r"\b(não entendi|não entendo)\b",
                r"\b(desculpa|perdão|como)\b"
            ]
        },
        
        # Technical issues
        "technical": {
            "english": [
                r"\b(audio is|sound is|volume is)\b",
                r"\b(cutting out|breaking up|connection|static)\b",
                r"\b(can't hear you|cannot hear you)\b",
                r"\b(microphone|mic|speaker)\b",
                r"\b(technical (problem|issue))\b"
            ],
            "spanish": [
                r"\b(el audio|el sonido|el volumen)\b",
                r"\b(se corta|conexión|estática)\b",
                r"\b(no te escucho|no puedo escucharte)\b",
                r"\b(micrófono|altavoz)\b",
                r"\b(problema técnico)\b"
            ]
        },
        
        # Pace control
        "pace": {
            "english": [
                r"\b(speak (slower|faster)|talk (slower|faster))\b",
                r"\b(too (fast|slow)|very (fast|slow))\b",
                r"\b(slow down|speed up)\b",
                r"\b(more slowly|more quickly)\b"
            ],
            "spanish": [
                r"\b(habla más (despacio|lento|rápido))\b",
                r"\b(muy (rápido|lento))\b",
                r"\b(más despacio|más rápido)\b"
            ]
        },
        
        # Volume control
        "volume": {
            "english": [
                r"\b(speak (louder|quieter)|talk (louder|quieter))\b",
                r"\b(too (loud|quiet)|very (loud|quiet))\b",
                r"\b(turn up|turn down|volume)\b",
                r"\b(can barely hear|hard to hear)\b"
            ]
        },
        
        # Conversation management
        "conversation_management": {
            "english": [
                r"\b(let's (start over|begin again|restart))\b",
                r"\b(change (topic|subject)|different topic)\b",
                r"\b(can we (talk about|discuss))\b",
                r"\b(i want to (talk about|discuss))\b",
                r"\b(let's talk about)\b",
                r"\b(wait a (moment|second|minute))\b"
            ]
        }
    }
    
    # Check patterns for the specified language and English (as fallback)
    languages_to_check = [language] if language == "english" else [language, "english"]
    
    for lang in languages_to_check:
        for category, lang_patterns in patterns.items():
            category_patterns = lang_patterns.get(lang, [])
            for pattern in category_patterns:
                if re.search(pattern, clean_text, re.IGNORECASE):
                    return {
                        "isMetaConversational": True,
                        "confidence": "high",
                        "category": category,
                        "reason": f"Detected {category} request in {lang}"
                    }
    
    # Check for medium confidence cases (partial matches or context-dependent)
    # Only trigger AI classification for very specific conversation management patterns
    medium_confidence_patterns = [
        r"\b(what did you just say|what did you say)\b",  # More specific repetition requests
        r"\b(i didn't understand you|i don't understand you)\b",  # Specific to conversation clarity
        r"\b(can you repeat that|could you repeat that)\b"  # Specific repetition requests
    ]
    
    for pattern in medium_confidence_patterns:
        if re.search(pattern, clean_text, re.IGNORECASE):
            return {
                "isMetaConversational": False,  # Will be determined by AI
                "confidence": "medium",
                "reason": "Uncertain - requires AI classification"
            }
    
    return {
        "isMetaConversational": False,
        "confidence": "low",
        "reason": "No meta-conversational patterns detected"
    }

async def evaluate_sentence_worthiness(text: str, language: str, level: str, conversation_context: Optional[str] = None) -> Dict:
    """
    Enhanced evaluation with meta-conversational detection and fast rule-based analysis.
    This reduces API calls by ~80% while maintaining accuracy.
    """
    
    # Quick filters for obviously non-substantial content
    if not text or len(text.strip()) < 8:
        return {
            "should_analyze": False,
            "reason": "Text too short (< 8 chars)",
            "confidence": 1.0
        }
    
    # First check for meta-conversational content
    meta_result = detect_meta_conversational(text, language)
    if meta_result["isMetaConversational"] and meta_result["confidence"] == "high":
        return {
            "should_analyze": False,
            "reason": f"Meta-conversational: {meta_result['reason']}",
            "confidence": 0.9,
            "isMetaConversational": True,
            "metaCategory": meta_result.get("category")
        }
    
    # If medium confidence meta-conversational, use AI to decide
    if meta_result["confidence"] == "medium":
        print(f"🤖 [META_AI] Using AI for meta-conversational classification: '{text[:30]}...'")
        
        try:
            client = create_openai_client()
            
            system_prompt = f"""
            You are determining if a student's utterance is meta-conversational (about managing the conversation) 
            or contains language learning content worth analyzing.
            
            ONLY classify as meta-conversational if it's PURELY about conversation mechanics:
            
            Meta-conversational (SKIP analysis):
            - "I didn't hear you, can you repeat?"
            - "Can you speak slower/louder?"
            - "What did you just say?" (asking for repetition)
            - "The audio is cutting out"
            - "Your microphone is not working"
            
            Learning content (ANALYZE these):
            - "I don't understand this topic" (content confusion, not conversation management)
            - "Can you explain more about economics?" (asking for topic explanation)
            - "What does this word mean?" (vocabulary learning)
            - "I have no idea about this subject" (expressing knowledge gaps)
            - "Actually, I think..." (expressing opinions with complex grammar)
            - Any attempt to engage with the topic content, even if confused
            
            IMPORTANT: If the student is trying to engage with the topic content (even if confused), 
            it should be analyzed for language learning value.
            
            Language: {language}
            Student Level: {level}
            
            Respond in JSON format with:
            - should_analyze (boolean): false ONLY if purely about conversation mechanics
            - reason (string): brief explanation
            - confidence (float): 0-1 confidence
            - isMetaConversational (boolean): true only if about conversation management, not topic content
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify: \"{text}\""}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            print(f"✅ [META_AI] AI classification: {ai_result}")
            
            if ai_result.get("isMetaConversational", False):
                return {
                    "should_analyze": False,
                    "reason": f"AI classified as meta-conversational: {ai_result.get('reason')}",
                    "confidence": ai_result.get("confidence", 0.7),
                    "isMetaConversational": True
                }
            
            # Continue with normal evaluation if not meta-conversational
            
        except Exception as e:
            print(f"❌ [META_AI] Error in AI meta-conversational classification: {str(e)}")
            # Continue with normal evaluation if AI fails
    
    words = text.split()
    word_count = len(words)
    
    # Reject very short sentences
    if word_count < 3:
        return {
            "should_analyze": False,
            "reason": "Too few words (< 3)",
            "confidence": 0.95
        }
    
    # Enhanced short response detection with language-specific responses
    short_responses = {
        "yes", "no", "ok", "okay", "sure", "maybe", "thanks", "thank you",
        "hi", "hello", "bye", "goodbye", "me too", "same", "exactly",
        "right", "correct", "wrong", "true", "false", "good", "bad",
        "nice", "great", "awesome", "terrible", "awful", "perfect",
        "absolutely", "definitely", "probably", "possibly", "certainly",
        "of course", "no problem", "you too", "sounds good", "makes sense",
        "i see", "i understand", "got it", "alright", "fine", "cool"
    }
    
    # Add language-specific common responses
    if language == "spanish":
        short_responses.update({"sí", "claro", "bueno", "vale", "perfecto", "gracias"})
    elif language == "french":
        short_responses.update({"oui", "bien", "parfait", "daccord", "merci", "salut"})
    elif language == "german":
        short_responses.update({"ja", "gut", "perfekt", "danke", "genau", "hallo"})
    elif language == "dutch":
        short_responses.update({"ja", "goed", "perfect", "dank je", "precies", "hallo"})
    
    cleaned_text = text.strip().lower().replace(".", "").replace("!", "").replace("?", "")
    if cleaned_text in short_responses:
        return {
            "should_analyze": False,
            "reason": "Simple/common response",
            "confidence": 0.95
        }
    
    # Rule-based complexity analysis
    complexity_score = 0
    reasons = []
    
    # Check for complex grammar patterns
    import re
    complex_patterns = [
        r'\b(because|although|however|therefore|meanwhile|furthermore|nevertheless|consequently)\b',
        r'\b(would|could|should|might|may|will|shall|must|ought)\b',
        r'\b(if|when|while|since|unless|until|before|after|during|despite)\b',
        r'\b(who|which|that|where|why|how|what|whose)\b.*\b(is|are|was|were|have|has|had)\b',
        r'\b(not only|either|neither|both|whether)\b'
    ]
    
    has_complex_grammar = any(re.search(pattern, text, re.IGNORECASE) for pattern in complex_patterns)
    if has_complex_grammar:
        complexity_score += 3
        reasons.append("complex grammar")
    
    # Check for interesting vocabulary (longer words)
    interesting_words = [word for word in words if len(word) > 6 and not word.lower() in 
                        ["because", "however", "therefore", "although"]]
    if interesting_words:
        complexity_score += 2
        reasons.append("advanced vocabulary")
    
    # Check for verb complexity
    verb_patterns = [
        r'\b\w+ing\b',  # Present participle/gerund
        r'\b\w+ed\b',   # Past tense (regular)
        r'\bhave\s+\w+ed\b',  # Present perfect
        r'\bhad\s+\w+ed\b',   # Past perfect
        r'\bwill\s+\w+\b'     # Future tense
    ]
    
    has_complex_verbs = any(re.search(pattern, text, re.IGNORECASE) for pattern in verb_patterns)
    if has_complex_verbs:
        complexity_score += 1
        reasons.append("complex verb forms")
    
    # Length scoring
    if 8 <= word_count <= 20:
        complexity_score += 2
        reasons.append("optimal length")
    elif word_count > 20:
        complexity_score += 1
        reasons.append("comprehensive sentence")
    
    # Question form bonus
    if "?" in text:
        complexity_score += 1
        reasons.append("question form")
    
    # Penalty for very short sentences
    if word_count < 5:
        complexity_score -= 2
        reasons.append("very short")
    
    # Rule-based decision (handles ~80% of cases)
    if complexity_score >= 4:
        return {
            "should_analyze": True,
            "reason": f"High learning value: {', '.join(reasons)}",
            "confidence": min(0.9, 0.6 + (complexity_score * 0.1))
        }
    elif complexity_score >= 2:
        return {
            "should_analyze": True,
            "reason": f"Moderate learning value: {', '.join(reasons)}",
            "confidence": 0.6 + (complexity_score * 0.05)
        }
    elif complexity_score <= 0:
        return {
            "should_analyze": False,
            "reason": "Low learning value: insufficient complexity",
            "confidence": 0.8
        }
    
    # Only use AI for uncertain cases (complexity_score = 1)
    print(f"🤖 [AI_FALLBACK] Using AI evaluation for uncertain case: '{text[:30]}...'")
    
    try:
        client = create_openai_client()
        
        system_prompt = f"""
        You are evaluating a borderline case for language learning analysis.
        
        The sentence has moderate complexity but needs expert judgment.
        
        Language: {language}
        Student Level: {level}
        
        Respond in JSON format with:
        - should_analyze (boolean): true if worth analyzing
        - reason (string): brief explanation
        - confidence (float): 0-1 confidence
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Evaluate: \"{text}\""}
            ],
            temperature=0.1,
            max_tokens=150  # Reduced for faster response
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"✅ [AI_FALLBACK] AI decision: {result.get('should_analyze')} - {result.get('reason')}")
        return result
        
    except Exception as e:
        print(f"❌ [AI_FALLBACK] Error in AI evaluation: {str(e)}")
        # Conservative fallback for uncertain cases
        return {
            "should_analyze": word_count >= 5 and len(text.strip()) > 15,
            "reason": "Fallback evaluation based on basic metrics",
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
        
        # 🔥 CRITICAL FIX: Ensure analysis_result is a dict and has all required fields
        if not isinstance(analysis_result, dict):
            print(f"❌ [BACKGROUND_ANALYSIS] analyze_sentence returned non-dict: {type(analysis_result)}")
            raise ValueError("analyze_sentence returned invalid format")
        
        # Ensure all required fields exist with defaults
        required_fields = {
            "recognized_text": text,
            "grammatical_score": 50.0,
            "vocabulary_score": 50.0,
            "complexity_score": 50.0,
            "appropriateness_score": 50.0,
            "overall_score": 50.0,
            "grammar_issues": [],
            "improvement_suggestions": [],
            "corrected_text": text,
            "level_appropriate_alternatives": []
        }
        
        # Merge with defaults to ensure all fields exist
        for field, default_value in required_fields.items():
            if field not in analysis_result:
                print(f"⚠️ [BACKGROUND_ANALYSIS] Missing field '{field}', using default: {default_value}")
                analysis_result[field] = default_value
        
        background_result = {
            "analysis_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            **analysis_result
        }
        
        print(f"✅ [BACKGROUND_ANALYSIS] Successfully created background result with analysis_id: {background_result['analysis_id']}")
        return background_result
        
    except Exception as e:
        print(f"❌ [BACKGROUND_ANALYSIS] Error in background analysis: {str(e)}")
        import traceback
        print(f"❌ [BACKGROUND_ANALYSIS] Full traceback: {traceback.format_exc()}")
        
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

async def batch_analyze_sentences(
    sentences: List[str], 
    language: str, 
    level: str
) -> List[BackgroundAnalysisResponse]:
    """
    Analyze multiple sentences in a single GPT-4o call for cost optimization.
    
    Args:
        sentences: List of sentence texts to analyze
        language: Target language (e.g., 'spanish', 'french')
        level: Proficiency level (e.g., 'A1', 'B2')
    
    Returns:
        List of analysis results in same order as input
    """
    
    if not sentences:
        return []
    
    # Limit batch size to prevent token overflow
    MAX_BATCH_SIZE = 10
    if len(sentences) > MAX_BATCH_SIZE:
        print(f"[BATCH_ANALYSIS] Splitting {len(sentences)} sentences into batches of {MAX_BATCH_SIZE}")
        # Split into multiple batches
        batches = [sentences[i:i+MAX_BATCH_SIZE] 
                   for i in range(0, len(sentences), MAX_BATCH_SIZE)]
        
        all_results = []
        for batch_idx, batch in enumerate(batches):
            print(f"[BATCH_ANALYSIS] Processing batch {batch_idx + 1}/{len(batches)}")
            results = await batch_analyze_sentences(batch, language, level)
            all_results.extend(results)
        return all_results
    
    print(f"[BATCH_ANALYSIS] Analyzing {len(sentences)} sentences in single GPT-4o-mini call")
    
    # Build numbered sentence list
    numbered_sentences = "\n".join([
        f"{i+1}. \"{sentence}\""
        for i, sentence in enumerate(sentences)
    ])
    
    # Create comprehensive prompt
    system_prompt = f"""You are an expert language teacher analyzing student speech.

Language: {language.title()}
Student Level: {level.upper()}

Analyze each sentence for:
1. Grammar correctness (0-100)
2. Vocabulary appropriateness (0-100)
3. Complexity level (0-100)
4. Overall appropriateness (0-100)
5. Specific grammar issues
6. Improvement suggestions
7. Corrected version (if needed)
8. Level-appropriate alternatives

Return a JSON object with an "analyses" array containing one analysis object per sentence, in the same order.
Each object must have this exact structure:
{{
    "recognized_text": "original sentence",
    "grammatical_score": 85,
    "vocabulary_score": 90,
    "complexity_score": 75,
    "appropriateness_score": 88,
    "overall_score": 84.5,
    "grammar_issues": [
        {{
            "issue": "description",
            "correction": "fix",
            "explanation": "why"
        }}
    ],
    "improvement_suggestions": ["suggestion 1", "suggestion 2"],
    "corrected_text": "corrected version",
    "level_appropriate_alternatives": ["alternative 1", "alternative 2"]
}}"""

    user_prompt = f"""Analyze these {len(sentences)} sentences:

{numbered_sentences}

Return JSON object with "analyses" array containing analysis for each sentence."""

    try:
        client = create_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o-mini for cost optimization (94% cheaper)
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000  # Enough for 10 sentences
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Handle both array and object with 'analyses' key
        analyses_data = result.get('analyses', []) if isinstance(result, dict) else result
        
        if not analyses_data:
            print(f"[BATCH_ANALYSIS] ⚠️ No analyses returned from GPT-4o-mini")
            analyses_data = []
        
        # Convert to BackgroundAnalysisResponse objects
        analyses = []
        for i, analysis_data in enumerate(analyses_data):
            # Add metadata
            analysis_data['analysis_id'] = str(uuid.uuid4())
            analysis_data['timestamp'] = datetime.now().isoformat()
            
            # Ensure recognized_text matches input
            if 'recognized_text' not in analysis_data and i < len(sentences):
                analysis_data['recognized_text'] = sentences[i]
            
            # Ensure all required fields exist
            required_fields = {
                'grammatical_score': 50.0,
                'vocabulary_score': 50.0,
                'complexity_score': 50.0,
                'appropriateness_score': 50.0,
                'overall_score': 50.0,
                'grammar_issues': [],
                'improvement_suggestions': [],
                'corrected_text': analysis_data.get('recognized_text', sentences[i] if i < len(sentences) else ''),
                'level_appropriate_alternatives': []
            }
            
            for field, default_value in required_fields.items():
                if field not in analysis_data:
                    analysis_data[field] = default_value
            
            # Create response object
            try:
                analyses.append(BackgroundAnalysisResponse(**analysis_data))
            except Exception as e:
                print(f"[BATCH_ANALYSIS] ⚠️ Error creating response object for sentence {i}: {str(e)}")
                continue
        
        print(f"✅ [BATCH_ANALYSIS] Successfully analyzed {len(analyses)} sentences")
        return analyses
        
    except Exception as e:
        print(f"❌ [BATCH_ANALYSIS] Error: {str(e)}")
        import traceback
        print(f"❌ [BATCH_ANALYSIS] Traceback: {traceback.format_exc()}")
        
        # Return minimal analyses for failed sentences
        return [
            BackgroundAnalysisResponse(
                analysis_id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                recognized_text=sentence,
                grammatical_score=0,
                vocabulary_score=0,
                complexity_score=0,
                appropriateness_score=0,
                overall_score=0,
                grammar_issues=[],
                improvement_suggestions=["Analysis failed. Please try again."],
                corrected_text=sentence,
                level_appropriate_alternatives=[]
            )
            for sentence in sentences
        ]

async def process_sentence_for_background_analysis(text: str, language: str, level: str, conversation_context: Optional[str] = None) -> Dict:
    """
    Complete pipeline: evaluate if sentence should be analyzed, and if so, perform the analysis.
    Returns explicit response whether analyzed or rejected, enabling proper frontend feedback.
    """
    
    # Step 1: Evaluate if sentence is worth analyzing
    evaluation = await evaluate_sentence_worthiness(text, language, level, conversation_context)
    
    if not evaluation.get("should_analyze", False):
        print(f"Skipping analysis for: '{text}' - Reason: {evaluation.get('reason', 'Unknown')}")
        
        # NEW: Return explicit rejection response instead of None
        return {
            "analyzed": False,
            "reason": evaluation.get("reason", "Not suitable for analysis"),
            "confidence": evaluation.get("confidence", 0.5),
            "should_retry": False,
            "rejection_feedback_enabled": True,  # Signal frontend to show feedback option
            "evaluation": evaluation,
            "text": text,
            "language": language,
            "level": level
        }
    
    print(f"Performing background analysis for: '{text}' - Reason: {evaluation.get('reason', 'Substantial content detected')}")
    
    # Step 2: Perform the analysis
    analysis_result = await perform_background_analysis(text, language, level, "free", conversation_context)
    
    # Add evaluation metadata and success indicators
    return {
        "analyzed": True,
        "reason": "Analysis completed successfully",
        "confidence": 1.0,
        "should_retry": False,
        "rejection_feedback_enabled": False,
        "evaluation": evaluation,
        "analysis": analysis_result
    }
