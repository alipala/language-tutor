from pydantic import BaseModel
from typing import List, Optional, Dict
import base64
import tempfile
import os
import json
from fastapi import HTTPException
from sentence_assessment import create_openai_client, recognize_speech

# Speaking Assessment Models
class SkillScore(BaseModel):
    score: float  # 0-100
    feedback: str
    examples: List[str]

class SpeakingAssessmentRequest(BaseModel):
    audio_base64: Optional[str] = None
    transcript: Optional[str] = None  # Allow direct transcript input
    language: str
    duration: Optional[int] = 60  # Duration in seconds
    prompt: Optional[str] = None  # The prompt that was given to the user

class SpeakingAssessmentResponse(BaseModel):
    recognized_text: str
    recommended_level: str  # A1, A2, B1, B2, C1, or C2
    overall_score: float  # 0-100
    confidence: float  # Confidence in level recommendation (0-100)
    pronunciation: SkillScore
    grammar: SkillScore
    vocabulary: SkillScore
    fluency: SkillScore
    coherence: SkillScore
    strengths: List[str]
    areas_for_improvement: List[str]
    next_steps: List[str]

async def evaluate_language_proficiency(text: str, language: str, duration: int = 60) -> Dict:
    """Comprehensive assessment of language proficiency based on spoken text"""
    
    # CEFR level descriptions and criteria
    cefr_levels = {
        "A1": {
            "description": "Can understand and use familiar everyday expressions and very basic phrases.",
            "grammar": "Uses basic sentence structures, frequent errors even in simple structures",
            "vocabulary": "Limited to basic personal and concrete needs",
            "fluency": "Very hesitant speech with many pauses and reformulations",
            "minimum_words": 20,
            "typical_errors": "Basic word order, verb conjugation, articles"
        },
        "A2": {
            "description": "Can communicate in simple and routine tasks on familiar topics.",
            "grammar": "Uses simple structures correctly but still makes basic mistakes",
            "vocabulary": "Sufficient for everyday needs and basic descriptions",
            "fluency": "Noticeable pauses, particularly in longer stretches",
            "minimum_words": 40,
            "typical_errors": "Past tense forms, plurals, prepositions"
        },
        "B1": {
            "description": "Can deal with most situations likely to arise while traveling.",
            "grammar": "Reasonable accuracy in familiar contexts, predictable patterns of error",
            "vocabulary": "Sufficient to express self on familiar topics and interests",
            "fluency": "Some pauses for grammatical and lexical planning",
            "minimum_words": 65,
            "typical_errors": "Tense consistency, complex structures, idiomatic expressions"
        },
        "B2": {
            "description": "Can interact with a degree of fluency and spontaneity.",
            "grammar": "Good grammatical control, occasional slips and non-systematic errors",
            "vocabulary": "Good range for general topics, able to vary formulation",
            "fluency": "Few noticeable lengthy pauses, fairly even tempo",
            "minimum_words": 90,
            "typical_errors": "Nuanced expressions, hypothetical structures, complex clauses"
        },
        "C1": {
            "description": "Can express ideas fluently and spontaneously without much searching for expressions.",
            "grammar": "High degree of grammatical control, errors are rare",
            "vocabulary": "Broad range, good command of idiomatic expressions",
            "fluency": "Smooth flow, only conceptually difficult subjects impede flow",
            "minimum_words": 120,
            "typical_errors": "Very specific vocabulary, stylistic features, register"
        },
        "C2": {
            "description": "Can express with precision in complex situations.",
            "grammar": "Maintains consistent grammatical control of complex language",
            "vocabulary": "Very broad lexical repertoire including colloquial expressions",
            "fluency": "Natural, effortless expression with only conceptually difficult subject hindering flow",
            "minimum_words": 150,
            "typical_errors": "Subtle nuances of meaning, cultural references"
        }
    }
    
    # Language-specific criteria
    language_features = {
        "english": {
            "assessment_focus": "article usage, prepositions, verb tenses, word order",
            "phonetic_challenges": "th sounds, vowel differentiation, word stress, intonation"
        },
        "dutch": {
            "assessment_focus": "word order, verb placement, het/de articles, separable verbs",
            "phonetic_challenges": "g/ch sounds, ui/eu vowels, diphthongs, r-pronunciation"
        },
        "spanish": {
            "assessment_focus": "ser/estar usage, subjunctive mood, gender agreement",
            "phonetic_challenges": "r/rr sounds, b/v distinction, vowel clarity"
        },
        "german": {
            "assessment_focus": "case system, word order, verb position, separable verbs",
            "phonetic_challenges": "umlauts, ch sounds, r-pronunciation"
        },
        "french": {
            "assessment_focus": "gender agreement, verb conjugation, negation structure",
            "phonetic_challenges": "nasal vowels, r-pronunciation, vowel distinctions, liaison"
        },
        "portuguese": {
            "assessment_focus": "ser/estar usage, contractions, verb conjugation",
            "phonetic_challenges": "nasal vowels, s/z/ç sounds, open/closed vowels"
        }
    }
    
    lang_focus = language_features.get(language.lower(), language_features["english"])
    
    # Create customized prompt for OpenAI based on language and criteria
    system_prompt = f"""
    You are an expert CEFR language proficiency assessor for {language}. 
    Analyze the following transcribed speech from a {duration}-second speaking task to determine the speaker's proficiency level.
    
    For this language, pay special attention to: {lang_focus['assessment_focus']}
    Common pronunciation challenges include: {lang_focus['phonetic_challenges']}
    
    Consider these factors in your assessment:
    1. Grammatical accuracy and complexity
    2. Vocabulary range and appropriateness
    3. Fluency and pace
    4. Coherence and organization
    5. Pronunciation and intonation
    
    Based on a {duration}-second speaking sample, analyze the text and:
    - Count the total words spoken (important for fluency assessment)
    - Identify grammatical structures used and errors made
    - Assess vocabulary range, repetition, and appropriateness
    - Evaluate sentence complexity and connection of ideas
    
    Then provide a comprehensive assessment in JSON format with these keys:
    - recognized_text (echo back the input text)
    - recommended_level (string: single CEFR level "A1", "A2", "B1", "B2", "C1", or "C2")
    - overall_score (float: 0-100)
    - confidence (float: 0-100, how confident you are in this level assessment)
    - pronunciation, grammar, vocabulary, fluency, coherence (each should be a SkillScore object with score, feedback, and examples fields)
    - strengths (array of strings highlighting what the speaker does well)
    - areas_for_improvement (array of strings identifying key areas to work on)
    - next_steps (array of strings with specific learning recommendations)
    """
    
    # Create OpenAI client using helper function
    client = create_openai_client()
    
    # Validate input text
    if not text or text.strip() == "":
        print("Warning: Empty text provided for assessment")
        text = "No text provided for assessment"
    
    print(f"Analyzing speaking proficiency for: '{text}'")
    word_count = len(text.split())
    print(f"Word count: {word_count}")
    
    # Call OpenAI for assessment
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcribed speech ({word_count} words in {duration} seconds): \"{text}\""}
            ],
            temperature=0.1  # Low temperature for consistent results
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        print(f"Successfully analyzed speaking proficiency")
        return result
    except Exception as e:
        print(f"Error in OpenAI speaking assessment: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Fallback minimal response
        return {
            "recognized_text": text,
            "recommended_level": "B1",  # Safe middle ground
            "overall_score": 50,
            "confidence": 30,  # Low confidence since this is a fallback
            "pronunciation": {"score": 50, "feedback": "Could not fully analyze pronunciation.", "examples": []},
            "grammar": {"score": 50, "feedback": "Could not fully analyze grammar.", "examples": []},
            "vocabulary": {"score": 50, "feedback": "Could not fully analyze vocabulary.", "examples": []},
            "fluency": {"score": 50, "feedback": "Could not fully analyze fluency.", "examples": []},
            "coherence": {"score": 50, "feedback": "Could not fully analyze coherence.", "examples": []},
            "strengths": ["Unable to determine specific strengths from this sample."],
            "areas_for_improvement": ["Please try again with a clearer recording."],
            "next_steps": ["Reattempt the speaking assessment with a 30-60 second response."]
        }

# Function to generate speaking prompts based on language
async def generate_speaking_prompts(language: str) -> Dict[str, List[str]]:
    """Generate speaking prompts for assessment in different languages"""
    
    # Default prompts in English
    default_prompts = {
        "general": [
            "Tell me about yourself and your language learning experience.",
            "Describe your hometown and what you like about it.",
            "What are your hobbies and interests?",
            "Talk about your favorite book, movie, or TV show.",
            "Describe your typical day."
        ],
        "travel": [
            "Describe a memorable trip you've taken.",
            "What's your favorite place to visit and why?",
            "Talk about a place you would like to visit in the future.",
            "Describe your ideal vacation.",
            "What do you usually do when you travel?"
        ],
        "education": [
            "Talk about your educational background.",
            "Describe a teacher who influenced you.",
            "What subjects did you enjoy studying?",
            "How do you think education has changed in recent years?",
            "Describe your learning style."
        ]
    }
    
    # Create OpenAI client using helper function
    client = create_openai_client()
    
    # If the language is English, return default prompts
    if language.lower() == "english":
        return default_prompts
    
    # For other languages, translate the prompts
    try:
        # Prepare the language code
        language_map = {
            "english": "en",
            "dutch": "nl",
            "spanish": "es",
            "german": "de",
            "french": "fr",
            "portuguese": "pt"
        }
        target_lang = language_map.get(language.lower(), "en")
        
        # Create a system prompt for translation
        system_prompt = f"""
        You are a professional translator. Translate the following prompts from English to {language}.
        Maintain the meaning and tone, but make any cultural adaptations necessary.
        Return the translations in JSON format with the same structure as the input.
        """
        
        # Call OpenAI for translation
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate these prompts to {language}: {json.dumps(default_prompts)}"}
            ],
            temperature=0.1
        )
        
        # Parse response
        translated_prompts = json.loads(response.choices[0].message.content)
        print(f"Successfully translated prompts to {language}")
        return translated_prompts
    except Exception as e:
        print(f"Error translating prompts: {str(e)}")
        # Return default English prompts if translation fails
        return default_prompts
