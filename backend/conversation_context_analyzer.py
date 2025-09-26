"""
Conversation Context Analyzer
Intelligent analysis of AI tutor responses to provide contextually relevant help suggestions.
Handles all cases: learning plans, practice conversations, guest users, and edge cases.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ConversationIntent(Enum):
    """AI Tutor Intent Classification"""
    REPEAT_PRACTICE = "repeat_practice"
    GRAMMAR_CORRECTION = "grammar_correction" 
    VOCABULARY_INTRODUCTION = "vocabulary_introduction"
    CONVERSATION_STARTER = "conversation_starter"
    QUESTION_ASKING = "question_asking"
    ENCOURAGEMENT = "encouragement"
    LESSON_CONCLUSION = "lesson_conclusion"
    CULTURAL_EXPLANATION = "cultural_explanation"
    PRONUNCIATION_FOCUS = "pronunciation_focus"
    UNKNOWN = "unknown"

class LessonPhase(Enum):
    """Current phase of the lesson"""
    INTRODUCTION = "introduction"
    WARM_UP = "warm_up"
    MAIN_PRACTICE = "main_practice"
    CORRECTION = "correction"
    REINFORCEMENT = "reinforcement"
    CONCLUSION = "conclusion"
    UNKNOWN = "unknown"

@dataclass
class ContextAnalysis:
    """Comprehensive context analysis result"""
    intent: ConversationIntent
    lesson_phase: LessonPhase
    confidence_score: float  # 0.0 to 1.0
    complexity_level: int  # 1-10
    detected_language: Optional[str]
    key_phrases: List[str]
    requires_pronunciation_help: bool
    requires_grammar_help: bool
    requires_vocabulary_help: bool
    cultural_context_present: bool
    conversation_flow_indicator: str  # "opening", "continuing", "closing"

class ConversationContextAnalyzer:
    """
    Intelligent context analyzer that works for ALL conversation types:
    - Custom learning plan sessions (with rich context)
    - Practice conversations (minimal context)
    - Guest user sessions (no user context)
    - Edge cases and error scenarios
    """
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.phase_patterns = self._initialize_phase_patterns()
        self.language_indicators = self._initialize_language_indicators()
        
    def _initialize_intent_patterns(self) -> Dict[ConversationIntent, List[str]]:
        """Initialize regex patterns for intent detection"""
        return {
            ConversationIntent.REPEAT_PRACTICE: [
                r"repeat after me",
                r"say.*again",
                r"practice saying",
                r"try to say",
                r"pronunciation.*exercise",
                r"listen and repeat",
                r"herhaal.*na.*mij",  # Dutch
                r"répète.*après.*moi",  # French
                r"repite.*después.*de.*mí",  # Spanish
                r"wiederhole.*nach.*mir",  # German
            ],
            ConversationIntent.GRAMMAR_CORRECTION: [
                r"correct.*is",
                r"should be",
                r"grammar.*mistake",
                r"try.*instead",
                r"better.*would.*be",
                r"the.*right.*way",
                r"grammatically",
                r"conjugation",
                r"tense.*should.*be",
            ],
            ConversationIntent.VOCABULARY_INTRODUCTION: [
                r"new word",
                r"means.*in",
                r"vocabulary.*lesson",
                r"learn.*word",
                r"this.*word.*means",
                r"definition.*of",
                r"let.*me.*teach.*you",
                r"word.*for.*today",
            ],
            ConversationIntent.CONVERSATION_STARTER: [
                r"tell me about",
                r"what do you think",
                r"describe.*your",
                r"share.*your.*opinion",
                r"how.*do.*you.*feel",
                r"what.*is.*your.*favorite",
                r"let.*s.*talk.*about",
                r"discuss",
            ],
            ConversationIntent.QUESTION_ASKING: [
                r"\?",  # Contains question mark
                r"what.*is",
                r"how.*do.*you",
                r"where.*did.*you",
                r"when.*was",
                r"why.*do.*you",
                r"which.*one",
                r"can.*you.*tell.*me",
            ],
            ConversationIntent.ENCOURAGEMENT: [
                r"good.*job",
                r"well.*done",
                r"excellent",
                r"perfect",
                r"great.*work",
                r"you.*re.*doing.*well",
                r"keep.*it.*up",
                r"very.*good",
                r"fantastic",
            ],
            ConversationIntent.LESSON_CONCLUSION: [
                r"today.*we.*practiced",
                r"in.*our.*next.*session",
                r"see.*you.*next.*time",
                r"that.*s.*all.*for.*today",
                r"great.*session",
                r"keep.*practicing",
                r"until.*next.*time",
                r"session.*complete",
            ],
            ConversationIntent.CULTURAL_EXPLANATION: [
                r"in.*culture",
                r"traditionally",
                r"cultural.*context",
                r"people.*usually",
                r"custom.*is",
                r"culturally.*speaking",
                r"in.*this.*country",
            ],
            ConversationIntent.PRONUNCIATION_FOCUS: [
                r"pronunciation",
                r"sounds.*like",
                r"accent",
                r"stress.*on",
                r"syllable",
                r"phonetic",
                r"intonation",
                r"rhythm",
            ]
        }
    
    def _initialize_phase_patterns(self) -> Dict[LessonPhase, List[str]]:
        """Initialize patterns for lesson phase detection"""
        return {
            LessonPhase.INTRODUCTION: [
                r"hello.*i.*m.*your",
                r"welcome.*to",
                r"let.*s.*start",
                r"today.*we.*will",
                r"good.*morning",
                r"nice.*to.*meet",
            ],
            LessonPhase.WARM_UP: [
                r"how.*are.*you",
                r"how.*was.*your",
                r"tell.*me.*about.*your.*day",
                r"what.*did.*you.*do",
                r"let.*s.*begin.*with",
            ],
            LessonPhase.MAIN_PRACTICE: [
                r"now.*let.*s.*practice",
                r"exercise",
                r"activity",
                r"try.*this",
                r"your.*turn",
                r"practice.*time",
            ],
            LessonPhase.CORRECTION: [
                r"actually",
                r"not.*quite",
                r"let.*me.*help",
                r"correction",
                r"mistake",
                r"try.*again",
            ],
            LessonPhase.REINFORCEMENT: [
                r"remember",
                r"as.*we.*learned",
                r"practice.*more",
                r"keep.*working.*on",
                r"don.*t.*forget",
            ],
            LessonPhase.CONCLUSION: [
                r"that.*s.*all",
                r"great.*session",
                r"see.*you.*next",
                r"keep.*practicing",
                r"until.*next.*time",
            ]
        }
    
    def _initialize_language_indicators(self) -> Dict[str, List[str]]:
        """Initialize language detection patterns"""
        return {
            "dutch": [
                r"\b(hallo|dag|goedemorgen|goedemiddag|dank.*je|alsjeblieft|ik|ben|het|van|een|de)\b",
                r"\b(spreek|nederlands|holland|nederland)\b"
            ],
            "spanish": [
                r"\b(hola|buenos|días|gracias|por.*favor|yo|soy|el|la|de|un|una)\b",
                r"\b(habla|español|castellano)\b"
            ],
            "french": [
                r"\b(bonjour|salut|merci|s.*il.*vous.*plaît|je|suis|le|la|de|un|une)\b",
                r"\b(parle|français|france)\b"
            ],
            "german": [
                r"\b(hallo|guten.*tag|danke|bitte|ich|bin|der|die|das|ein|eine)\b",
                r"\b(spreche|deutsch|deutschland)\b"
            ],
            "portuguese": [
                r"\b(olá|bom.*dia|obrigado|por.*favor|eu|sou|o|a|de|um|uma)\b",
                r"\b(fala|português|brasil|portugal)\b"
            ],
            "italian": [
                r"\b(ciao|buongiorno|grazie|prego|io|sono|il|la|di|un|una)\b",
                r"\b(parla|italiano|italia)\b"
            ]
        }
    
    def analyze_context(
        self,
        ai_response: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        learning_plan_context: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ContextAnalysis:
        """
        Comprehensive context analysis that handles ALL scenarios:
        - Learning plan sessions (rich context)
        - Practice conversations (minimal context)
        - Guest users (no user context)
        - Edge cases and errors
        """
        
        try:
            # Validate and clean input
            if not ai_response or not ai_response.strip():
                return self._create_fallback_analysis()
            
            ai_response = ai_response.strip()
            conversation_history = conversation_history or []
            
            # Step 1: Detect intent with confidence scoring
            intent, intent_confidence = self._detect_intent(ai_response)
            
            # Step 2: Detect lesson phase
            lesson_phase = self._detect_lesson_phase(ai_response, conversation_history)
            
            # Step 3: Assess complexity
            complexity_level = self._assess_complexity(ai_response, learning_plan_context)
            
            # Step 4: Detect language
            detected_language = self._detect_language(ai_response, user_context)
            
            # Step 5: Extract key phrases
            key_phrases = self._extract_key_phrases(ai_response)
            
            # Step 6: Determine help requirements
            help_requirements = self._analyze_help_requirements(ai_response, intent)
            
            # Step 7: Assess cultural context
            cultural_context = self._detect_cultural_context(ai_response)
            
            # Step 8: Determine conversation flow
            flow_indicator = self._analyze_conversation_flow(ai_response, conversation_history)
            
            return ContextAnalysis(
                intent=intent,
                lesson_phase=lesson_phase,
                confidence_score=intent_confidence,
                complexity_level=complexity_level,
                detected_language=detected_language,
                key_phrases=key_phrases,
                requires_pronunciation_help=help_requirements["pronunciation"],
                requires_grammar_help=help_requirements["grammar"],
                requires_vocabulary_help=help_requirements["vocabulary"],
                cultural_context_present=cultural_context,
                conversation_flow_indicator=flow_indicator
            )
            
        except Exception as e:
            logger.error(f"Context analysis failed: {str(e)}")
            return self._create_fallback_analysis()
    
    def _detect_intent(self, ai_response: str) -> Tuple[ConversationIntent, float]:
        """Detect AI tutor intent with confidence scoring"""
        ai_response_lower = ai_response.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, ai_response_lower, re.IGNORECASE):
                    matches += 1
                    # Weight based on pattern specificity
                    if len(pattern) > 20:  # Complex patterns get higher weight
                        score += 0.8
                    else:
                        score += 0.5
            
            if matches > 0:
                # Normalize score based on number of patterns
                intent_scores[intent] = min(score / len(patterns), 1.0)
        
        if not intent_scores:
            return ConversationIntent.UNKNOWN, 0.3
        
        # Return intent with highest confidence
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]
    
    def _detect_lesson_phase(self, ai_response: str, conversation_history: List[Dict[str, str]]) -> LessonPhase:
        """Detect current lesson phase"""
        ai_response_lower = ai_response.lower()
        
        # Check conversation length for phase hints
        history_length = len(conversation_history)
        
        if history_length <= 2:
            # Early in conversation - likely introduction or warm-up
            for phase in [LessonPhase.INTRODUCTION, LessonPhase.WARM_UP]:
                for pattern in self.phase_patterns.get(phase, []):
                    if re.search(pattern, ai_response_lower, re.IGNORECASE):
                        return phase
        
        # Check for explicit phase indicators
        for phase, patterns in self.phase_patterns.items():
            for pattern in patterns:
                if re.search(pattern, ai_response_lower, re.IGNORECASE):
                    return phase
        
        # Default based on conversation length
        if history_length <= 1:
            return LessonPhase.INTRODUCTION
        elif history_length <= 3:
            return LessonPhase.WARM_UP
        elif history_length >= 10:
            return LessonPhase.CONCLUSION
        else:
            return LessonPhase.MAIN_PRACTICE
    
    def _assess_complexity(self, ai_response: str, learning_plan_context: Optional[Dict[str, Any]]) -> int:
        """Assess response complexity (1-10 scale)"""
        complexity = 5  # Base complexity
        
        # Adjust based on learning plan context if available
        if learning_plan_context:
            proficiency = learning_plan_context.get("proficiency_level", "B1")
            proficiency_complexity = {
                "A1": 2, "A2": 3, "B1": 5, "B2": 7, "C1": 8, "C2": 9
            }
            complexity = proficiency_complexity.get(proficiency, 5)
        
        # Adjust based on response characteristics
        word_count = len(ai_response.split())
        if word_count > 50:
            complexity += 2
        elif word_count < 10:
            complexity -= 1
        
        # Check for complex grammar structures
        complex_indicators = [
            r"subjunctive", r"conditional", r"passive voice", r"complex.*tense",
            r"advanced.*grammar", r"sophisticated", r"nuanced"
        ]
        
        for indicator in complex_indicators:
            if re.search(indicator, ai_response.lower()):
                complexity += 1
                break
        
        return max(1, min(complexity, 10))
    
    def _detect_language(self, ai_response: str, user_context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Detect the language being taught"""
        
        # First, check user context if available
        if user_context:
            target_language = user_context.get("target_language")
            if target_language:
                return target_language.lower()
        
        # Fallback to pattern detection
        ai_response_lower = ai_response.lower()
        
        for language, patterns in self.language_indicators.items():
            for pattern in patterns:
                if re.search(pattern, ai_response_lower, re.IGNORECASE):
                    return language
        
        return None
    
    def _extract_key_phrases(self, ai_response: str) -> List[str]:
        """Extract key phrases for context"""
        # Simple extraction of quoted phrases and important terms
        key_phrases = []
        
        # Extract quoted text
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', ai_response)
        key_phrases.extend(quoted_matches)
        
        # Extract emphasized terms (capitalized words)
        emphasized = re.findall(r'\b[A-Z][A-Z]+\b', ai_response)
        key_phrases.extend(emphasized)
        
        # Extract potential vocabulary words (words followed by "means" or "is")
        vocab_matches = re.findall(r'(\w+)\s+(?:means|is|refers to)', ai_response.lower())
        key_phrases.extend(vocab_matches)
        
        return list(set(key_phrases))[:5]  # Return up to 5 unique phrases
    
    def _analyze_help_requirements(self, ai_response: str, intent: ConversationIntent) -> Dict[str, bool]:
        """Determine what type of help is needed"""
        ai_response_lower = ai_response.lower()
        
        return {
            "pronunciation": (
                intent == ConversationIntent.REPEAT_PRACTICE or
                intent == ConversationIntent.PRONUNCIATION_FOCUS or
                any(word in ai_response_lower for word in ["pronunciation", "repeat", "say", "sounds"])
            ),
            "grammar": (
                intent == ConversationIntent.GRAMMAR_CORRECTION or
                any(word in ai_response_lower for word in ["grammar", "tense", "conjugation", "correct"])
            ),
            "vocabulary": (
                intent == ConversationIntent.VOCABULARY_INTRODUCTION or
                any(word in ai_response_lower for word in ["word", "means", "definition", "vocabulary"])
            )
        }
    
    def _detect_cultural_context(self, ai_response: str) -> bool:
        """Detect if cultural context is present"""
        cultural_indicators = [
            "culture", "traditional", "custom", "culturally", "society",
            "people usually", "in this country", "local", "native"
        ]
        
        ai_response_lower = ai_response.lower()
        return any(indicator in ai_response_lower for indicator in cultural_indicators)
    
    def _analyze_conversation_flow(self, ai_response: str, conversation_history: List[Dict[str, str]]) -> str:
        """Analyze conversation flow position"""
        history_length = len(conversation_history)
        ai_response_lower = ai_response.lower()
        
        # Opening indicators
        opening_patterns = ["hello", "welcome", "let's start", "good morning", "nice to meet"]
        if any(pattern in ai_response_lower for pattern in opening_patterns) or history_length <= 1:
            return "opening"
        
        # Closing indicators
        closing_patterns = ["goodbye", "see you next", "that's all", "great session", "keep practicing"]
        if any(pattern in ai_response_lower for pattern in closing_patterns):
            return "closing"
        
        return "continuing"
    
    def _create_fallback_analysis(self) -> ContextAnalysis:
        """Create safe fallback analysis for error cases"""
        return ContextAnalysis(
            intent=ConversationIntent.UNKNOWN,
            lesson_phase=LessonPhase.UNKNOWN,
            confidence_score=0.3,
            complexity_level=5,
            detected_language=None,
            key_phrases=[],
            requires_pronunciation_help=False,
            requires_grammar_help=False,
            requires_vocabulary_help=False,
            cultural_context_present=False,
            conversation_flow_indicator="continuing"
        )

# Global analyzer instance
context_analyzer = ConversationContextAnalyzer()
