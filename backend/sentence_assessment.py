from pydantic import BaseModel
from typing import List, Optional, Dict
import base64
import tempfile
import os
import json
import re
from fastapi import HTTPException
from openai_client import get_async_openai

def create_openai_client():
    """Backwards-compat shim — returns the shared AsyncOpenAI singleton."""
    return get_async_openai()

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

# Helper function for speech recognition using OpenAI's audio transcription.
#
# This is the FILE-BASED (non-realtime) path: the full audio clip is sent to
# /audio/transcriptions.
#
# MODEL CHOICE — whisper-1 (2026-07-02):
# We default to whisper-1 because gpt-4o-transcribe-diarize (and the whole
# gpt-4o-transcribe family) rejects some real-world mobile recordings with
# "This model does not support the format you provided" (unsupported_format,
# param: 'messages'). This hit EVERY Android assessment: expo-av records m4a
# (MPEG_4/AAC) on Android, and diarize rejected that specific m4a container
# while accepting iOS WAV — so iOS worked and Android always failed. It is a
# known, still-open OpenAI bug (openai-python#2477); the confirmed fix there
# is that whisper-1 transcribes the same files fine. whisper-1 is NOT retired
# (verified against OpenAI's 2026 deprecations page) and accepts mp3/mp4/m4a/
# wav/webm, so it fixes Android without changing the working iOS path.
#
# whisper-1 supports `language` (no `prompt` steering, no `chunking_strategy`).
# Override via FILE_TRANSCRIBE_MODEL if a future model is preferred.
async def recognize_speech(audio_base64: str, language: str) -> str:
    # Import the audio format validator
    from audio_format_validator import AudioFormatValidator

    # 🎛️ Configuration: primary + fallback transcription model via env vars.
    # Default to whisper-1 (tolerant of Android m4a; see note above).
    PRIMARY_MODEL = os.getenv("FILE_TRANSCRIBE_MODEL", "whisper-1")
    FALLBACK_MODEL = os.getenv("FILE_TRANSCRIBE_FALLBACK_MODEL", "whisper-1")

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
    
    # ROBUST AUDIO FORMAT VALIDATION
    print(f"🔍 [AUDIO_VALIDATION] Validating audio format for {language} transcription...")
    
    # Validate the audio format before processing
    is_valid, error_message, metadata = AudioFormatValidator.validate_audio_data(audio_base64)
    
    if not is_valid:
        print(f"❌ [AUDIO_VALIDATION] {error_message}")
        print(f"📊 [AUDIO_VALIDATION] Metadata: {metadata}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid audio format: {error_message}. Please record in a supported format (MP3, WAV, M4A, WebM)."
        )
    
    print(f"✅ [AUDIO_VALIDATION] Audio format validated: {metadata.get('detected_format', 'unknown')} ({metadata.get('file_size', 0)} bytes)")
    
    # Decode audio data
    audio_data = base64.b64decode(audio_base64)
    
    # Create temporary file with proper extension
    temp_audio_path = None
    try:
        temp_audio_path, _ = AudioFormatValidator.create_temp_audio_file(audio_data, metadata)
        
        # Create OpenAI client using helper function
        client = create_openai_client()

        # Build model-specific transcription kwargs. Each model family accepts a
        # different parameter set:
        #   - gpt-4o-transcribe-diarize: requires chunking_strategy, NO prompt
        #   - gpt-4o-transcribe:         supports prompt, NO language
        #   - whisper-1:                 supports language, NO prompt steering
        def _transcribe_kwargs(model_name: str) -> dict:
            kwargs = {"model": model_name, "response_format": "text"}
            if model_name == "gpt-4o-transcribe-diarize":
                kwargs["language"] = speech_language
                kwargs["chunking_strategy"] = "auto"
            elif model_name == "gpt-4o-transcribe":
                kwargs["prompt"] = (
                    f"This is a {language} language learning conversation. "
                    f"Focus on accurate transcription of student speech for language assessment."
                )
            else:  # whisper-1 and other language-aware models
                kwargs["language"] = speech_language
            return kwargs

        # Open the audio file
        with open(temp_audio_path, "rb") as audio_file:
            try:
                transcript = await client.audio.transcriptions.create(
                    file=audio_file,
                    **_transcribe_kwargs(PRIMARY_MODEL),
                )
                print(f"✅ [TRANSCRIPTION] Used {PRIMARY_MODEL} for {language} transcription")
                return transcript

            except Exception as primary_error:
                print(f"⚠️ [TRANSCRIPTION] {PRIMARY_MODEL} failed: {primary_error}")

                # Skip the fallback call if it would just repeat the primary model.
                if FALLBACK_MODEL == PRIMARY_MODEL:
                    raise

                print(f"🔄 [TRANSCRIPTION] Falling back to {FALLBACK_MODEL} for {language}")
                # Reset file pointer for fallback
                audio_file.seek(0)
                transcript = await client.audio.transcriptions.create(
                    file=audio_file,
                    **_transcribe_kwargs(FALLBACK_MODEL),
                )
                print(f"✅ [TRANSCRIPTION] Used {FALLBACK_MODEL} fallback for {language} transcription")
                return transcript
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is (these are validation errors)
        raise
    except Exception as e:
        print(f"❌ [TRANSCRIPTION] Error in speech recognition: {str(e)}")
        # Provide more specific error message based on the error type
        if "format" in str(e).lower() or "decode" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail=f"Audio format error: The audio file could not be processed. Please try recording again in a supported format (MP3, WAV, M4A, WebM)."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Speech recognition failed: {str(e)}")
    finally:
        # Clean up temp file using validator's cleanup method
        if temp_audio_path:
            AudioFormatValidator.cleanup_temp_file(temp_audio_path)

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
        response = await client.chat.completions.create(
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
        
        # 🔥 CRITICAL FIX: Add the recognized_text field that the API response model requires
        result["recognized_text"] = text
        
        print(f"Successfully analyzed text: '{text}'")
        return result
    except Exception as e:
        print(f"Error in OpenAI sentence analysis: {str(e)}")
        # Log more details about the error
        import traceback
        print(traceback.format_exc())
        # Fallback minimal response
        return {
            "recognized_text": text,  # 🔥 CRITICAL FIX: Include recognized_text in fallback response
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
        response = await client.chat.completions.create(
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
