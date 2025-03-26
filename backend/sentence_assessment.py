from pydantic import BaseModel
from typing import List, Optional, Dict
import base64
import tempfile
import os
import json
import re
from fastapi import HTTPException
import openai
import httpx

# Helper function to create OpenAI client with proper error handling
def create_openai_client():
    """Create an OpenAI client with proper error handling for the 'proxies' issue."""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return client
    except TypeError as e:
        if "proxies" in str(e):
            print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
            # Alternative initialization without proxies
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=httpx.Client())
            print("OpenAI client initialized with alternative method")
            return client
        else:
            print(f"Error initializing OpenAI client: {str(e)}")
            raise

# Request model
class SentenceAssessmentRequest(BaseModel):
    audio_base64: Optional[str] = None
    transcript: Optional[str] = None  # Allow direct transcript input when audio isn't available
    language: str
    level: str  # A1-C2
    exercise_type: Optional[str] = "free"  # free, guided, translation, completion
    target_grammar: Optional[List[str]] = None  # specific grammar points to focus on
    context: Optional[str] = None  # conversation context or exercise description

# Response models
class GrammarIssue(BaseModel):
    issue_type: str  # e.g., "verb tense", "word order", "agreement", etc.
    description: str
    suggestion: str
    severity: str  # "minor", "moderate", "major"

class SentenceAssessmentResponse(BaseModel):
    recognized_text: str
    grammatical_score: float  # 0-100
    vocabulary_score: float  # 0-100
    complexity_score: float  # 0-100
    appropriateness_score: float  # 0-100 (level appropriate)
    overall_score: float  # 0-100
    grammar_issues: List[GrammarIssue]
    improvement_suggestions: List[str]
    corrected_text: Optional[str] = None
    level_appropriate_alternatives: Optional[List[str]] = None

# Helper function for speech recognition using OpenAI's audio transcription
async def recognize_speech(audio_base64: str, language: str) -> str:
    # Map language codes
    language_map = {
        "english": "en",
        "dutch": "nl",
        "spanish": "es",
        "german": "de",
        "french": "fr",
        "portuguese": "pt"
    }
    speech_language = language_map.get(language.lower(), "en")
    
    # Decode audio
    audio_data = base64.b64decode(audio_base64)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        temp_audio.write(audio_data)
        temp_audio_path = temp_audio.name
    
    try:
        # Create OpenAI client using helper function
        client = create_openai_client()
        
        # Open the audio file
        with open(temp_audio_path, "rb") as audio_file:
            # Call OpenAI's transcription API
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=speech_language,
                response_format="text"
            )
        
        return transcript
    
    except Exception as e:
        print(f"Error in speech recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)

# Helper function for sentence analysis using OpenAI
async def analyze_sentence(text: str, language: str, level: str, exercise_type: str, target_grammar: Optional[List[str]] = None) -> Dict:
    # Define level-appropriate expectations
    level_expectations = {
        "A1": {
            "grammar": ["simple present tense", "basic word order", "simple questions"],
            "vocabulary": ["basic, everyday words", "numbers, colors, common nouns"],
            "complexity": ["simple sentences", "basic conjunctions (and, but)"],
            "max_errors": 5
        },
        "A2": {
            "grammar": ["present and past tense", "basic prepositions", "common irregular verbs"],
            "vocabulary": ["daily routines", "simple descriptions", "basic opinions"],
            "complexity": ["compound sentences", "basic time expressions"],
            "max_errors": 4
        },
        "B1": {
            "grammar": ["present, past, future tenses", "modal verbs", "comparative forms"],
            "vocabulary": ["opinions", "experiences", "hopes and plans", "abstract concepts"],
            "complexity": ["compound and simple complex sentences", "limited subordinate clauses"],
            "max_errors": 3
        },
        "B2": {
            "grammar": ["all tenses", "passive forms", "conditionals", "reported speech"],
            "vocabulary": ["specialized terms", "idiomatic expressions", "connotation"],
            "complexity": ["complex sentences", "varied conjunctions", "discourse markers"],
            "max_errors": 2
        },
        "C1": {
            "grammar": ["nuanced tense usage", "complex structures", "exceptions to rules"],
            "vocabulary": ["precise terminology", "colloquialisms", "academic language"],
            "complexity": ["sophisticated sentence structures", "varied syntax", "rhetorical devices"],
            "max_errors": 1
        },
        "C2": {
            "grammar": ["native-like accuracy", "stylistic variation", "creative manipulation"],
            "vocabulary": ["near-native range", "sophisticated expressions", "subtle distinctions"],
            "complexity": ["natural flow", "eloquence", "stylistic appropriateness"],
            "max_errors": 0.5
        }
    }
    
    # Get expectations for the user's level
    user_expectations = level_expectations.get(level.upper(), level_expectations["B1"])
    
    # Create language-specific prompt for analysis
    language_specific = {
        "english": {
            "common_errors": "article usage, prepositions, subject-verb agreement, verb tense consistency",
            "analysis_focus": "clarity, conciseness, and natural flow"
        },
        "dutch": {
            "common_errors": "word order, verb placement, het/de articles, separable verbs",
            "analysis_focus": "sentence structure, verb positioning, and natural expression"
        },
        "spanish": {
            "common_errors": "ser/estar usage, subjunctive mood, gender agreement, por/para distinction",
            "analysis_focus": "verb conjugation, gender/number agreement, and natural expression"
        },
        "german": {
            "common_errors": "word order, case system, verb position, noun gender, separable verbs",
            "analysis_focus": "sentence structure, case usage, and compound word formation"
        },
        "french": {
            "common_errors": "gender agreement, verb conjugation, negation, preposition usage",
            "analysis_focus": "gender/number agreement, verb tenses, and natural expression"
        },
        "portuguese": {
            "common_errors": "ser/estar usage, contractions, verb conjugation, gender agreement",
            "analysis_focus": "verb tenses, preposition usage, and natural expression"
        }
    }
    
    lang_focus = language_specific.get(language.lower(), language_specific["english"])
    
    # Build analysis prompt for OpenAI
    grammar_focus = ""
    if target_grammar:
        grammar_focus = f"Pay special attention to these grammar points: {', '.join(target_grammar)}."
    
    system_prompt = f"""
    You are a language assessment expert for {language} at CEFR level {level}. 
    Analyze the following sentence construction for a {level} level student.
    
    For this level, I expect: 
    - Grammar: {', '.join(user_expectations['grammar'])}
    - Vocabulary: {', '.join(user_expectations['vocabulary'])}
    - Complexity: {', '.join(user_expectations['complexity'])}
    
    Common errors in {language} include: {lang_focus['common_errors']}
    Focus on: {lang_focus['analysis_focus']}
    
    {grammar_focus}
    
    Provide a detailed analysis in JSON format with these keys:
    - grammatical_score (0-100)
    - vocabulary_score (0-100)
    - complexity_score (0-100)
    - appropriateness_score (0-100)
    - overall_score (0-100)
    - grammar_issues (array of objects with issue_type, description, suggestion, severity)
    - improvement_suggestions (array of strings)
    - corrected_text (string)
    - level_appropriate_alternatives (array of strings)
    """
    
    # Create OpenAI client using helper function
    client = create_openai_client()
    
    # Validate input text
    if not text or text.strip() == "":
        print("Warning: Empty text provided for analysis")
        text = "No text provided for analysis"
    
    print(f"Analyzing text: '{text}'")
    
    # Call OpenAI for analysis
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Exercise type: {exercise_type}\nText to analyze: \"{text}\""}
            ],
            temperature=0.1  # Low temperature for consistent results
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        print(f"Successfully analyzed text: '{text}'")
        return result
    except Exception as e:
        print(f"Error in OpenAI sentence analysis: {str(e)}")
        # Log more details about the error
        import traceback
        print(traceback.format_exc())
        # Fallback minimal response
        return {
            "grammatical_score": 50,
            "vocabulary_score": 50,
            "complexity_score": 50,
            "appropriateness_score": 50,
            "overall_score": 50,
            "grammar_issues": [],
            "improvement_suggestions": ["Could not analyze sentence completely. Please try again."],
            "corrected_text": text,
            "level_appropriate_alternatives": []
        }

# Function to generate practice exercises based on user's level and needs
async def generate_exercises(language: str, level: str, exercise_type: str, target_grammar: Optional[List[str]] = None) -> Dict:
    # Create OpenAI client using helper function
    client = create_openai_client()
    
    # Exercise type descriptions
    exercise_descriptions = {
        "free": "Create open-ended prompts for the user to form sentences about",
        "guided": "Provide vocabulary and grammar patterns for structured sentence building",
        "transformation": "Give sentences to transform (e.g., active to passive, past to present)",
        "correction": "Provide sentences with deliberate errors to fix",
        "translation": "Give sentences in the user's native language to translate"
    }
    
    exercise_type_desc = exercise_descriptions.get(exercise_type, exercise_descriptions["free"])
    
    grammar_focus = ""
    if target_grammar:
        grammar_focus = f"Focus exercises on these grammar points: {', '.join(target_grammar)}."
    
    # Build system prompt
    system_prompt = f"""
    You are a language teaching expert creating {exercise_type} exercises for {language} at CEFR level {level}.
    
    {exercise_type_desc}
    {grammar_focus}
    
    Create a set of 5 exercises appropriate for level {level}.
    
    Return the exercises in JSON format with these keys:
    - exercises (array of objects with:
      - prompt (the exercise instruction or question)
      - example (a sample correct response if applicable)
      - notes (teaching notes or hints)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create {exercise_type} exercises for {level} {language} learners"}
            ],
            temperature=0.7  # Higher temperature for creative exercises
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error generating exercises: {str(e)}")
        return {
            "exercises": [
                {
                    "prompt": "Create a simple sentence about your day.",
                    "example": "I went to the store today.",
                    "notes": "Practice using past tense correctly."
                }
            ]
        }
