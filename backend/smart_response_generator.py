"""
Smart Response Generator
Generates contextually appropriate conversation help responses based on AI tutor intent and context.
Handles all conversation types with intelligent model selection and fallback strategies.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

from conversation_context_analyzer import (
    ConversationIntent, 
    LessonPhase, 
    ContextAnalysis,
    context_analyzer
)
from conversation_help import (
    ConversationHelpRequest,
    ConversationHelpResponse,
    SuggestedResponse,
    VocabularyItem,
    GrammarTip,
    CulturalNote,
    INSTANT_RESPONSE_TEMPLATES,
    client  # OpenAI client
)

logger = logging.getLogger(__name__)

class ResponseStrategy(Enum):
    """Strategy for generating responses"""
    TEMPLATE_FAST = "template_fast"  # Instant template responses
    GPT4O_MINI_STANDARD = "gpt4o_mini_standard"  # Standard GPT-4o-mini
    GPT4O_SMART = "gpt4o_smart"  # Advanced GPT-4o for complex cases
    LEARNING_PLAN_ENHANCED = "learning_plan_enhanced"  # Learning plan context

@dataclass
class ResponseGenerationContext:
    """Context for response generation"""
    strategy: ResponseStrategy
    context_analysis: ContextAnalysis
    learning_plan_context: Optional[Dict[str, Any]]
    user_context: Optional[Dict[str, Any]]
    time_budget_seconds: float
    fallback_required: bool = False

class SmartResponseGenerator:
    """
    Intelligent response generator that adapts to different conversation contexts:
    - Custom learning plan sessions (rich context)
    - Practice conversations (standard context)
    - Guest users (minimal context)
    - All edge cases and error scenarios
    """
    
    def __init__(self):
        self.intent_response_templates = self._initialize_intent_templates()
        self.performance_cache = {}  # Simple caching for common patterns
        
    def _initialize_intent_templates(self) -> Dict[ConversationIntent, Dict[str, List[Dict[str, str]]]]:
        """Initialize intent-specific response templates for ultra-fast responses"""
        return {
            ConversationIntent.REPEAT_PRACTICE: {
                "english": [
                    {"text": "I'll try to repeat that", "pronunciation": "aɪl traɪ tu rɪˈpit ðæt", "explanation": "Shows willingness to practice pronunciation"},
                    {"text": "Let me practice that again", "pronunciation": "lɛt mi ˈpræktɪs ðæt əˈgɛn", "explanation": "Requests more pronunciation practice"},
                ],
                "dutch": [
                    {"text": "Ik ga het herhalen", "pronunciation": "ɪk ɣaː ət hərˈhaːlə", "explanation": "I will repeat it"},
                    {"text": "Laat me dat oefenen", "pronunciation": "laːt mə dɑt ˈufənə", "explanation": "Let me practice that"},
                ],
                "spanish": [
                    {"text": "Voy a repetir eso", "pronunciation": "boy a re-pe-tir e-so", "explanation": "I'm going to repeat that"},
                    {"text": "Déjame practicar eso", "pronunciation": "de-ha-me prak-ti-kar e-so", "explanation": "Let me practice that"},
                ]
            },
            ConversationIntent.GRAMMAR_CORRECTION: {
                "english": [
                    {"text": "Thank you for the correction", "pronunciation": "θæŋk ju fɔr ðə kəˈrɛkʃən", "explanation": "Acknowledges grammar help"},
                    {"text": "I understand the mistake", "pronunciation": "aɪ ˌʌndərˈstænd ðə mɪˈsteɪk", "explanation": "Shows comprehension of error"},
                ],
                "dutch": [
                    {"text": "Dank je voor de correctie", "pronunciation": "dɑŋk jə voːr də kɔˈrɛksi", "explanation": "Thank you for the correction"},
                    {"text": "Ik begrijp de fout", "pronunciation": "ɪk bəˈɣrɛip də fʌut", "explanation": "I understand the mistake"},
                ],
                "spanish": [
                    {"text": "Gracias por la corrección", "pronunciation": "gra-sias por la ko-rek-sion", "explanation": "Thank you for the correction"},
                    {"text": "Entiendo el error", "pronunciation": "en-tien-do el e-ror", "explanation": "I understand the error"},
                ]
            },
            ConversationIntent.VOCABULARY_INTRODUCTION: {
                "english": [
                    {"text": "That's a useful word", "pronunciation": "ðæts ə ˈjusfəl wɜrd", "explanation": "Acknowledges new vocabulary"},
                    {"text": "I'll remember that word", "pronunciation": "aɪl rɪˈmɛmbər ðæt wɜrd", "explanation": "Shows intent to learn vocabulary"},
                ],
                "dutch": [
                    {"text": "Dat is een nuttig woord", "pronunciation": "dɑt ɪs ən ˈnʏtəx woːrt", "explanation": "That's a useful word"},
                    {"text": "Ik onthoud dat woord", "pronunciation": "ɪk ˈɔnthʌut dɑt woːrt", "explanation": "I'll remember that word"},
                ],
                "spanish": [
                    {"text": "Esa es una palabra útil", "pronunciation": "e-sa es u-na pa-la-bra u-til", "explanation": "That's a useful word"},
                    {"text": "Recordaré esa palabra", "pronunciation": "re-kor-da-re e-sa pa-la-bra", "explanation": "I'll remember that word"},
                ]
            },
            ConversationIntent.CONVERSATION_STARTER: {
                "english": [
                    {"text": "That's an interesting topic", "pronunciation": "ðæts æn ˈɪntrəstɪŋ ˈtɑpɪk", "explanation": "Shows engagement with conversation"},
                    {"text": "I'd like to share my thoughts", "pronunciation": "aɪd laɪk tu ʃɛr maɪ θɔts", "explanation": "Indicates readiness to participate"},
                ],
                "dutch": [
                    {"text": "Dat is een interessant onderwerp", "pronunciation": "dɑt ɪs ən ɪntərɛˈsɑnt ˈɔndərwɛrp", "explanation": "That's an interesting topic"},
                    {"text": "Ik wil graag mijn mening delen", "pronunciation": "ɪk wɪl ɣraːx mɛin ˈmeːnɪŋ ˈdeːlə", "explanation": "I'd like to share my opinion"},
                ],
                "spanish": [
                    {"text": "Es un tema interesante", "pronunciation": "es un te-ma in-te-re-san-te", "explanation": "It's an interesting topic"},
                    {"text": "Me gustaría compartir mi opinión", "pronunciation": "me gus-ta-ri-a kom-par-tir mi o-pi-nion", "explanation": "I'd like to share my opinion"},
                ]
            },
            ConversationIntent.ENCOURAGEMENT: {
                "english": [
                    {"text": "Thank you for the encouragement", "pronunciation": "θæŋk ju fɔr ði ɪnˈkɜrɪdʒmənt", "explanation": "Acknowledges positive feedback"},
                    {"text": "That motivates me to continue", "pronunciation": "ðæt ˈmoʊtəˌveɪts mi tu kənˈtɪnju", "explanation": "Shows motivation from praise"},
                ],
                "dutch": [
                    {"text": "Dank je voor de aanmoediging", "pronunciation": "dɑŋk jə voːr də ˈaːnmudiɣɪŋ", "explanation": "Thank you for the encouragement"},
                    {"text": "Dat motiveert me om door te gaan", "pronunciation": "dɑt moːtiˈveːrt mə ɔm doːr tə ɣaːn", "explanation": "That motivates me to continue"},
                ],
                "spanish": [
                    {"text": "Gracias por el ánimo", "pronunciation": "gra-sias por el a-ni-mo", "explanation": "Thank you for the encouragement"},
                    {"text": "Eso me motiva a continuar", "pronunciation": "e-so me mo-ti-va a kon-ti-nu-ar", "explanation": "That motivates me to continue"},
                ]
            }
        }
    
    async def generate_smart_response(
        self,
        request: ConversationHelpRequest,
        learning_plan_context: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        time_budget: float = 7.0
    ) -> ConversationHelpResponse:
        """
        Generate contextually appropriate response using smart strategy selection.
        Handles ALL conversation types with graceful fallbacks.
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            print(f"[SMART_RESPONSE] 🚀 Starting smart response generation")
            print(f"[SMART_RESPONSE] Time budget: {time_budget}s")
            print(f"[SMART_RESPONSE] Learning plan context: {learning_plan_context is not None}")
            print(f"[SMART_RESPONSE] User context: {user_context is not None}")
            
            # Step 1: Analyze context (fast operation)
            context_analysis = context_analyzer.analyze_context(
                ai_response=request.ai_response,
                conversation_history=request.conversation_context,
                learning_plan_context=learning_plan_context,
                user_context=user_context
            )
            
            print(f"[SMART_RESPONSE] Context analysis: intent={context_analysis.intent.value}, confidence={context_analysis.confidence_score:.2f}")
            
            # Step 2: Select optimal strategy
            strategy = self._select_response_strategy(
                context_analysis=context_analysis,
                learning_plan_context=learning_plan_context,
                user_context=user_context,
                time_budget=time_budget
            )
            
            print(f"[SMART_RESPONSE] Selected strategy: {strategy.value}")
            
            # Step 3: Generate response using selected strategy
            generation_context = ResponseGenerationContext(
                strategy=strategy,
                context_analysis=context_analysis,
                learning_plan_context=learning_plan_context,
                user_context=user_context,
                time_budget_seconds=time_budget
            )
            
            response = await self._generate_response_by_strategy(request, generation_context)
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            print(f"[SMART_RESPONSE] ✅ Response generated in {elapsed_time:.2f}s using {strategy.value}")
            
            return response
            
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            print(f"[SMART_RESPONSE] ❌ Error after {elapsed_time:.2f}s: {str(e)}")
            logger.error(f"Smart response generation failed: {str(e)}")
            
            # Ultimate fallback
            return self._create_emergency_fallback_response(request)
    
    def _select_response_strategy(
        self,
        context_analysis: ContextAnalysis,
        learning_plan_context: Optional[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]],
        time_budget: float
    ) -> ResponseStrategy:
        """
        COMPLETELY CONTEXT-AWARE strategy selection.
        NO MORE IRRELEVANT TEMPLATE RESPONSES!
        """
        
        print(f"[STRATEGY_SELECTION] Intent: {context_analysis.intent.value}, Confidence: {context_analysis.confidence_score:.2f}")
        print(f"[STRATEGY_SELECTION] Complexity: {context_analysis.complexity_level}/10")
        print(f"[STRATEGY_SELECTION] Time budget: {time_budget}s")
        
        # Strategy 1: Learning Plan Enhanced (for custom learning plan sessions)
        if learning_plan_context and time_budget >= 5.0:
            print(f"[STRATEGY_SELECTION] → LEARNING_PLAN_ENHANCED (has learning plan context)")
            return ResponseStrategy.LEARNING_PLAN_ENHANCED
        
        # Strategy 2: GPT-4o Smart (for complex situations that need deep understanding)
        if context_analysis.complexity_level >= 6 and time_budget >= 5.0:
            print(f"[STRATEGY_SELECTION] → GPT4O_SMART (high complexity: {context_analysis.complexity_level})")
            return ResponseStrategy.GPT4O_SMART
        
        # Strategy 3: NEVER USE TEMPLATES UNLESS 100% CONFIDENT AND RELEVANT
        # Only use templates for extremely high confidence (>0.9) and very simple, predictable cases
        if (context_analysis.confidence_score > 0.9 and 
            context_analysis.intent in [ConversationIntent.ENCOURAGEMENT] and  # Only for very simple cases
            context_analysis.complexity_level <= 3):
            print(f"[STRATEGY_SELECTION] → TEMPLATE_FAST (ultra-high confidence: {context_analysis.confidence_score:.2f})")
            return ResponseStrategy.TEMPLATE_FAST
        
        # Strategy 4: DEFAULT - Always use GPT-4o-mini for context-aware responses
        # This ensures we ALWAYS get contextually relevant responses
        print(f"[STRATEGY_SELECTION] → GPT4O_MINI_STANDARD (context-aware generation)")
        return ResponseStrategy.GPT4O_MINI_STANDARD
    
    async def _generate_response_by_strategy(
        self,
        request: ConversationHelpRequest,
        context: ResponseGenerationContext
    ) -> ConversationHelpResponse:
        """Generate response using the selected strategy"""
        
        if context.strategy == ResponseStrategy.TEMPLATE_FAST:
            return await self._generate_template_response(request, context)
        elif context.strategy == ResponseStrategy.LEARNING_PLAN_ENHANCED:
            return await self._generate_learning_plan_enhanced_response(request, context)
        elif context.strategy == ResponseStrategy.GPT4O_SMART:
            return await self._generate_gpt4o_smart_response(request, context)
        else:  # GPT4O_MINI_STANDARD
            return await self._generate_gpt4o_mini_response(request, context)
    
    async def _generate_template_response(
        self,
        request: ConversationHelpRequest,
        context: ResponseGenerationContext
    ) -> ConversationHelpResponse:
        """Generate ultra-fast template-based response"""
        
        print(f"[TEMPLATE_RESPONSE] 🏃‍♂️ Generating template response for {context.context_analysis.intent.value}")
        
        # Get intent-specific templates
        intent_templates = self.intent_response_templates.get(context.context_analysis.intent, {})
        language = context.context_analysis.detected_language or request.target_language
        
        # Get language-specific templates
        language_templates = intent_templates.get(language, intent_templates.get("english", []))
        
        if not language_templates:
            # Fallback to general templates
            general_templates = INSTANT_RESPONSE_TEMPLATES.get(language, INSTANT_RESPONSE_TEMPLATES["english"])
            level_templates = general_templates.get(request.proficiency_level, general_templates.get("beginner", []))
            language_templates = [
                {"text": t["text"], "pronunciation": t["pronunciation"], "explanation": t["explanation"]}
                for t in level_templates[:2]
            ]
        
        # Create suggested responses
        suggested_responses = []
        for template in language_templates[:2]:  # Limit to 2 responses
            suggested_responses.append(SuggestedResponse(
                text=template["text"],
                pronunciation=template["pronunciation"],
                difficulty_level=request.proficiency_level,
                explanation=template["explanation"]
            ))
        
        # Create contextual summary
        summary = self._create_contextual_summary(request, context.context_analysis)
        
        print(f"[TEMPLATE_RESPONSE] ✅ Generated {len(suggested_responses)} template responses")
        
        return ConversationHelpResponse(
            ai_response_summary=summary,
            suggested_responses=suggested_responses,
            vocabulary_highlights=[],
            grammar_tips=[]
        )
    
    async def _generate_learning_plan_enhanced_response(
        self,
        request: ConversationHelpRequest,
        context: ResponseGenerationContext
    ) -> ConversationHelpResponse:
        """Generate learning plan context-enhanced response"""
        
        print(f"[LEARNING_PLAN_RESPONSE] 🎯 Generating learning plan enhanced response")
        
        learning_plan = context.learning_plan_context
        
        # Extract learning plan context
        current_focus = learning_plan.get("current_focus", "language practice")
        target_skills = learning_plan.get("areas_for_improvement", [])
        strengths = learning_plan.get("strengths", [])
        proficiency_level = learning_plan.get("proficiency_level", request.proficiency_level)
        
        # Create enhanced prompt with learning plan context
        enhanced_prompt = f"""AI tutor said: "{request.ai_response[:200]}"

LEARNING PLAN CONTEXT:
- Current focus: {current_focus}
- Target skills to improve: {', '.join(target_skills) if target_skills else 'general communication'}
- Student strengths: {', '.join(strengths) if strengths else 'developing'}
- Proficiency level: {proficiency_level}
- Intent detected: {context.context_analysis.intent.value}

Generate 2 contextual responses that align with the learning plan focus and help the student practice their target improvement areas.

Target language: {request.target_language}
Help language: {request.user_language}

JSON format:
{{"summary": "brief summary in {request.user_language}", "responses": [{{"text": "response in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "how this helps with current learning focus"}}]}}"""
        
        try:
            # Use GPT-4o-mini with learning plan context
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=400,
                timeout=3.0  # Reduced timeout for faster fallback
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                
                # Clean and parse JSON
                content = self._clean_json_content(content)
                help_data = json.loads(content)
                
                # Build response
                suggested_responses = []
                for resp in help_data.get("responses", [])[:2]:
                    if isinstance(resp, dict) and resp.get("text"):
                        suggested_responses.append(SuggestedResponse(
                            text=resp.get("text", ""),
                            pronunciation=resp.get("pronunciation", ""),
                            difficulty_level=proficiency_level,
                            explanation=resp.get("explanation", "")
                        ))
                
                if suggested_responses:
                    print(f"[LEARNING_PLAN_RESPONSE] ✅ Generated {len(suggested_responses)} learning plan aligned responses")
                    
                    return ConversationHelpResponse(
                        ai_response_summary=help_data.get("summary", f"The AI tutor is helping you practice {current_focus}."),
                        suggested_responses=suggested_responses,
                        vocabulary_highlights=[],
                        grammar_tips=[]
                    )
            
        except Exception as e:
            print(f"[LEARNING_PLAN_RESPONSE] ❌ Enhanced generation failed: {str(e)}")
        
        # Fallback to standard response
        return await self._generate_gpt4o_mini_response(request, context)
    
    async def _generate_gpt4o_smart_response(
        self,
        request: ConversationHelpRequest,
        context: ResponseGenerationContext
    ) -> ConversationHelpResponse:
        """Generate advanced response using GPT-4o for complex pedagogical situations"""
        
        print(f"[GPT4O_SMART] 🧠 Generating advanced response for complex situation")
        
        # Create sophisticated prompt for complex pedagogical analysis
        smart_prompt = f"""You are an expert language pedagogy AI analyzing a tutoring interaction.

AI TUTOR RESPONSE: "{request.ai_response[:300]}"

CONTEXT ANALYSIS:
- Detected intent: {context.context_analysis.intent.value}
- Lesson phase: {context.context_analysis.lesson_phase.value}
- Complexity level: {context.context_analysis.complexity_level}/10
- Key phrases: {', '.join(context.context_analysis.key_phrases)}
- Requires pronunciation help: {context.context_analysis.requires_pronunciation_help}
- Requires grammar help: {context.context_analysis.requires_grammar_help}
- Cultural context present: {context.context_analysis.cultural_context_present}

Generate 2 pedagogically sophisticated responses that:
1. Match the specific teaching moment and intent
2. Provide appropriate scaffolding for the proficiency level
3. Address the detected learning needs
4. Support the conversational flow

Target language: {request.target_language}
Student level: {request.proficiency_level}
Help language: {request.user_language}

Respond in JSON:
{{"summary": "pedagogical analysis in {request.user_language}", "responses": [{{"text": "sophisticated response in {request.target_language}", "pronunciation": "detailed phonetic guide", "explanation": "pedagogical reasoning for this response"}}], "vocabulary": [{{"word": "key term", "definition": "meaning", "context": "usage context"}}], "grammar_tips": [{{"pattern": "grammar pattern", "explanation": "when and how to use", "example": "example sentence"}}]}}"""
        
        try:
            # Use GPT-4o for sophisticated analysis
            response = client.chat.completions.create(
                model="gpt-4o",  # Advanced model for complex cases
                messages=[{"role": "user", "content": smart_prompt}],
                temperature=0.1,
                max_tokens=700,
                timeout=6.0
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                content = self._clean_json_content(content)
                help_data = json.loads(content)
                
                # Build comprehensive response
                suggested_responses = []
                for resp in help_data.get("responses", [])[:2]:
                    if isinstance(resp, dict) and resp.get("text"):
                        suggested_responses.append(SuggestedResponse(
                            text=resp.get("text", ""),
                            pronunciation=resp.get("pronunciation", ""),
                            difficulty_level=request.proficiency_level,
                            explanation=resp.get("explanation", "")
                        ))
                
                # Add vocabulary items
                vocabulary_highlights = []
                for vocab in help_data.get("vocabulary", [])[:3]:
                    if isinstance(vocab, dict) and vocab.get("word"):
                        vocabulary_highlights.append(VocabularyItem(
                            word=vocab.get("word", ""),
                            definition=vocab.get("definition", ""),
                            pronunciation="",
                            example_sentence=vocab.get("context", ""),
                            difficulty_level=request.proficiency_level
                        ))
                
                # Add grammar tips
                grammar_tips = []
                for tip in help_data.get("grammar_tips", [])[:2]:
                    if isinstance(tip, dict) and tip.get("pattern"):
                        grammar_tips.append(GrammarTip(
                            pattern=tip.get("pattern", ""),
                            explanation=tip.get("explanation", ""),
                            example=tip.get("example", ""),
                            difficulty_level=request.proficiency_level
                        ))
                
                if suggested_responses:
                    print(f"[GPT4O_SMART] ✅ Generated sophisticated response with {len(vocabulary_highlights)} vocab items and {len(grammar_tips)} grammar tips")
                    
                    return ConversationHelpResponse(
                        ai_response_summary=help_data.get("summary", "Advanced pedagogical analysis of the tutoring interaction."),
                        suggested_responses=suggested_responses,
                        vocabulary_highlights=vocabulary_highlights,
                        grammar_tips=grammar_tips
                    )
            
        except Exception as e:
            print(f"[GPT4O_SMART] ❌ Advanced generation failed: {str(e)}")
        
        # Fallback to standard response
        return await self._generate_gpt4o_mini_response(request, context)
    
    async def _generate_gpt4o_mini_response(
        self,
        request: ConversationHelpRequest,
        context: ResponseGenerationContext
    ) -> ConversationHelpResponse:
        """Generate HIGHLY CONTEXT-AWARE response using GPT-4o-mini"""
        
        print(f"[GPT4O_MINI] 🔄 Generating CONTEXT-AWARE response")
        
        # ULTRA-DETAILED prompt for maximum context awareness
        enhanced_prompt = f"""You are helping a language student respond to their AI tutor. The student needs ACTUAL RESPONSES they can say in the target language.

AI TUTOR'S EXACT WORDS: "{request.ai_response}"

CRITICAL ANALYSIS:
- What is the tutor asking the student to SAY or DO?
- If asking to describe something, provide actual descriptions
- If asking to repeat, provide the actual content to repeat
- If asking to correct, provide the corrected version
- If asking for practice, provide actual practice content

EXAMPLES:
- If tutor says "describe your morning routine": Return actual morning routine descriptions
- If tutor says "repeat after me: hello": Return "hello" and variations
- If tutor says "correct this sentence": Return the corrected sentence
- If tutor says "try using different words": Return actual content with different vocabulary

CONTEXT:
- Target language: {request.target_language}
- Student level: {request.proficiency_level}
- Help language: {request.user_language}
- Key phrases from tutor: {', '.join(context.context_analysis.key_phrases)}

Generate 2 ACTUAL RESPONSES the student can say in {request.target_language}:
1. Direct responses to what the tutor is asking for
2. Appropriate content for the proficiency level
3. Natural language the student would actually speak
4. NOT meta-responses about what they will do

RESPOND IN JSON:
{{"summary": "what the tutor is asking for in {request.user_language}", "responses": [{{"text": "actual response content in {request.target_language}", "pronunciation": "phonetic guide", "explanation": "why this content fits the tutor's request"}}]}}"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=300,  # Reduced for faster response
                timeout=2.5  # Much shorter timeout
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                content = self._clean_json_content(content)
                help_data = json.loads(content)
                
                suggested_responses = []
                for resp in help_data.get("responses", [])[:2]:
                    if isinstance(resp, dict) and resp.get("text"):
                        suggested_responses.append(SuggestedResponse(
                            text=resp.get("text", ""),
                            pronunciation=resp.get("pronunciation", ""),
                            difficulty_level=request.proficiency_level,
                            explanation=resp.get("explanation", "")
                        ))
                
                if suggested_responses:
                    print(f"[GPT4O_MINI] ✅ Generated {len(suggested_responses)} standard responses")
                    
                    return ConversationHelpResponse(
                        ai_response_summary=help_data.get("summary", "The AI tutor provided guidance."),
                        suggested_responses=suggested_responses,
                        vocabulary_highlights=[],
                        grammar_tips=[]
                    )
            
        except Exception as e:
            print(f"[GPT4O_MINI] ❌ Standard generation failed: {str(e)}")
        
        # Final fallback to CONTEXTUAL emergency response
        return self._create_emergency_fallback_response(request)
    
    def _clean_json_content(self, content: str) -> str:
        """Clean JSON content from API response"""
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        
        if content.endswith('```'):
            content = content[:-3]
        
        return content.strip()
    
    def _create_contextual_summary(self, request: ConversationHelpRequest, analysis: ContextAnalysis) -> str:
        """Create contextual summary based on analysis"""
        
        intent_summaries = {
            ConversationIntent.REPEAT_PRACTICE: f"The AI tutor is helping you practice pronunciation in {request.target_language}.",
            ConversationIntent.GRAMMAR_CORRECTION: f"The AI tutor provided a grammar correction to help improve your {request.target_language}.",
            ConversationIntent.VOCABULARY_INTRODUCTION: f"The AI tutor introduced new vocabulary in {request.target_language}.",
            ConversationIntent.CONVERSATION_STARTER: f"The AI tutor started a conversation topic to practice {request.target_language}.",
            ConversationIntent.ENCOURAGEMENT: f"The AI tutor provided encouragement for your {request.target_language} learning progress.",
            ConversationIntent.LESSON_CONCLUSION: f"The AI tutor is concluding the {request.target_language} lesson.",
        }
        
        return intent_summaries.get(analysis.intent, f"The AI tutor provided guidance in {request.target_language}.")
    
    def _create_emergency_fallback_response(self, request: ConversationHelpRequest) -> ConversationHelpResponse:
        """Create CONTEXTUAL emergency fallback response for critical errors"""
        
        print(f"[EMERGENCY_FALLBACK] 🚨 Creating CONTEXTUAL emergency fallback response")
        
        # Analyze the AI tutor's request to create contextual fallbacks
        ai_response_lower = request.ai_response.lower()
        
        # Create contextual responses based on what the AI tutor is asking
        if ("describe" in ai_response_lower and "morning" in ai_response_lower) or ("morning routine" in ai_response_lower):
            # Morning routine description
            suggested_responses = [
                SuggestedResponse(
                    text="I wake up, brush my teeth, and get ready for the day",
                    pronunciation="aɪ weɪk ʌp, brʌʃ maɪ tiθ, ænd gɛt ˈrɛdi fɔr ðə deɪ",
                    difficulty_level=request.proficiency_level,
                    explanation="A simple morning routine description"
                ),
                SuggestedResponse(
                    text="In the morning, I wash my face and have breakfast",
                    pronunciation="ɪn ðə ˈmɔrnɪŋ, aɪ wɑʃ maɪ feɪs ænd hæv ˈbrɛkfəst",
                    difficulty_level=request.proficiency_level,
                    explanation="Another way to describe morning activities"
                )
            ]
        elif "vocabulary" in ai_response_lower or "word" in ai_response_lower:
            # Vocabulary practice
            if "thoroughly" in ai_response_lower:
                suggested_responses = [
                    SuggestedResponse(
                        text="I clean my room thoroughly every week",
                        pronunciation="aɪ klin maɪ rum ˈθɜroʊli ˈɛvri wik",
                        difficulty_level=request.proficiency_level,
                        explanation="Using 'thoroughly' to mean completely or carefully"
                    ),
                    SuggestedResponse(
                        text="She studied the lesson thoroughly",
                        pronunciation="ʃi ˈstʌdid ðə ˈlɛsən ˈθɜroʊli",
                        difficulty_level=request.proficiency_level,
                        explanation="Another example of using 'thoroughly' in context"
                    )
                ]
            else:
                suggested_responses = [
                    SuggestedResponse(
                        text="That's a useful new word to learn",
                        pronunciation="ðæts ə ˈjusfəl nu wɜrd tu lɜrn",
                        difficulty_level=request.proficiency_level,
                        explanation="Acknowledging new vocabulary"
                    ),
                    SuggestedResponse(
                        text="I'll try to use this word in conversation",
                        pronunciation="aɪl traɪ tu juz ðɪs wɜrd ɪn ˌkɑnvərˈseɪʃən",
                        difficulty_level=request.proficiency_level,
                        explanation="Showing intent to practice new vocabulary"
                    )
                ]
        elif "sentence structure" in ai_response_lower or "grammar" in ai_response_lower:
            # Grammar correction
            suggested_responses = [
                SuggestedResponse(
                    text="I usually brush my teeth, wash my face, and then help my children",
                    pronunciation="aɪ ˈjuʒuəli brʌʃ maɪ tiθ, wɑʃ maɪ feɪs, ænd ðɛn hɛlp maɪ ˈʧɪldrən",
                    difficulty_level=request.proficiency_level,
                    explanation="Better sentence structure with proper coordination"
                ),
                SuggestedResponse(
                    text="Every morning, I brush my teeth and wash my face before helping the kids",
                    pronunciation="ˈɛvri ˈmɔrnɪŋ, aɪ brʌʃ maɪ tiθ ænd wɑʃ maɪ feɪs bɪˈfɔr ˈhɛlpɪŋ ðə kɪdz",
                    difficulty_level=request.proficiency_level,
                    explanation="Alternative structure using time sequence"
                )
            ]
        else:
            # Generic contextual responses
            templates = INSTANT_RESPONSE_TEMPLATES.get(request.target_language, INSTANT_RESPONSE_TEMPLATES["english"])
            level_templates = templates.get(request.proficiency_level, templates.get("beginner", templates[list(templates.keys())[0]]))
            
            suggested_responses = [
                SuggestedResponse(
                    text=template["text"],
                    pronunciation=template["pronunciation"],
                    difficulty_level=request.proficiency_level,
                    explanation=template["explanation"]
                ) for template in level_templates[:2]
            ]
        
        return ConversationHelpResponse(
            ai_response_summary=f"The AI tutor is asking you to practice {request.target_language}.",
            suggested_responses=suggested_responses,
            vocabulary_highlights=[],
            grammar_tips=[]
        )

# Global generator instance
smart_response_generator = SmartResponseGenerator()
