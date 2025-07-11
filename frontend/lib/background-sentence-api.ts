import { getApiUrl } from './api-utils';

// Types for background sentence analysis
export interface SentenceEvaluationRequest {
  text: string;
  language: string;
  level: string;
  conversation_context?: string;
}

export interface SentenceEvaluationResponse {
  should_analyze: boolean;
  reason: string;
  confidence: number;
}

export interface BackgroundAnalysisRequest {
  text: string;
  language: string;
  level: string;
  exercise_type?: string;
  conversation_context?: string;
}

export interface GrammarIssue {
  issue_type: string;
  description: string;
  suggestion: string;
  severity: string;
}

export interface BackgroundAnalysisResponse {
  analysis_id: string;
  recognized_text: string;
  grammatical_score: number;
  vocabulary_score: number;
  complexity_score: number;
  appropriateness_score: number;
  overall_score: number;
  grammar_issues: GrammarIssue[];
  improvement_suggestions: string[];
  corrected_text?: string;
  level_appropriate_alternatives?: string[];
  timestamp: string;
}

export interface BackgroundProcessResponse {
  analyzed: boolean;
  reason?: string;
  analysis?: BackgroundAnalysisResponse;
  evaluation?: {
    should_analyze: boolean;
    reason: string;
    confidence: number;
  };
}

/**
 * Meta-conversational detection result
 */
export interface MetaConversationalResult {
  isMetaConversational: boolean;
  confidence: 'high' | 'medium' | 'low';
  category?: 'clarification' | 'technical' | 'pace' | 'volume' | 'conversation_management';
  reason: string;
}

/**
 * Enhanced analysis decision interface
 */
export interface AnalysisDecision {
  shouldAnalyze: boolean;
  reason: string;
  confidence: number;
  isMetaConversational?: boolean;
  metaCategory?: string;
}

/**
 * Detect if text is meta-conversational (about managing the conversation itself)
 * rather than demonstrating language learning content
 */
export function detectMetaConversational(text: string, language: string = 'english'): MetaConversationalResult {
  if (!text || text.trim().length < 2) {
    return {
      isMetaConversational: false,
      confidence: 'high',
      reason: 'Text too short to be meta-conversational'
    };
  }

  const cleanText = text.trim().toLowerCase();
  
  // Define multilingual patterns for meta-conversational detection
  const patterns = {
    // Clarification requests
    clarification: {
      english: [
        /\b(didn't hear|can't hear|couldn't hear|cannot hear)\b/i,
        /\b(repeat|say that again|come again|pardon|excuse me)\b/i,
        /\b(what did you (say|just say))\b/i,
        /\b(i (didn't|don't) understand)\b/i,
        /\b(could you repeat)\b/i,
        /\b(sorry,? what)\b/i
      ],
      spanish: [
        /\b(no te escuché|no escuché|no oí)\b/i,
        /\b(puedes repetir|puede repetir|repite)\b/i,
        /\b(qué dijiste|qué dijo)\b/i,
        /\b(no entendí|no entiendo)\b/i,
        /\b(perdón|disculpa|cómo)\b/i
      ],
      french: [
        /\b(je n'ai pas entendu|je n'entends pas)\b/i,
        /\b(pouvez-vous répéter|peux-tu répéter|répétez)\b/i,
        /\b(qu'avez-vous dit|qu'est-ce que vous avez dit)\b/i,
        /\b(je ne comprends pas|je n'ai pas compris)\b/i,
        /\b(pardon|excusez-moi|comment)\b/i
      ],
      german: [
        /\b(ich habe (sie|dich) nicht gehört|ich höre nicht)\b/i,
        /\b(können sie wiederholen|kannst du wiederholen|wiederholen)\b/i,
        /\b(was haben sie gesagt|was hast du gesagt)\b/i,
        /\b(ich verstehe nicht|ich habe nicht verstanden)\b/i,
        /\b(entschuldigung|wie bitte)\b/i
      ],
      dutch: [
        /\b(ik hoorde je niet|ik hoor je niet|niet gehoord)\b/i,
        /\b(kun je herhalen|kunt u herhalen|herhaal)\b/i,
        /\b(wat zei je|wat zei u)\b/i,
        /\b(ik begrijp het niet|ik snap het niet)\b/i,
        /\b(sorry|pardon|wat)\b/i
      ],
      portuguese: [
        /\b(não te ouvi|não ouvi|não escutei)\b/i,
        /\b(podes repetir|pode repetir|repete)\b/i,
        /\b(o que disseste|o que disse)\b/i,
        /\b(não entendi|não entendo)\b/i,
        /\b(desculpa|perdão|como)\b/i
      ]
    },
    
    // Technical issues
    technical: {
      english: [
        /\b(audio is|sound is|volume is)\b/i,
        /\b(cutting out|breaking up|connection|static)\b/i,
        /\b(can't hear you|cannot hear you)\b/i,
        /\b(microphone|mic|speaker)\b/i,
        /\b(technical (problem|issue))\b/i
      ],
      spanish: [
        /\b(el audio|el sonido|el volumen)\b/i,
        /\b(se corta|conexión|estática)\b/i,
        /\b(no te escucho|no puedo escucharte)\b/i,
        /\b(micrófono|altavoz)\b/i,
        /\b(problema técnico)\b/i
      ],
      french: [
        /\b(l'audio|le son|le volume)\b/i,
        /\b(ça coupe|connexion|statique)\b/i,
        /\b(je ne vous entends pas|je ne t'entends pas)\b/i,
        /\b(microphone|haut-parleur)\b/i,
        /\b(problème technique)\b/i
      ],
      german: [
        /\b(das audio|der ton|die lautstärke)\b/i,
        /\b(bricht ab|verbindung|rauschen)\b/i,
        /\b(ich höre sie nicht|ich höre dich nicht)\b/i,
        /\b(mikrofon|lautsprecher)\b/i,
        /\b(technisches problem)\b/i
      ],
      dutch: [
        /\b(de audio|het geluid|het volume)\b/i,
        /\b(valt weg|verbinding|ruis)\b/i,
        /\b(ik hoor je niet|ik kan je niet horen)\b/i,
        /\b(microfoon|luidspreker)\b/i,
        /\b(technisch probleem)\b/i
      ],
      portuguese: [
        /\b(o áudio|o som|o volume)\b/i,
        /\b(está cortando|conexão|estática)\b/i,
        /\b(não te ouço|não consigo te ouvir)\b/i,
        /\b(microfone|alto-falante)\b/i,
        /\b(problema técnico)\b/i
      ]
    },
    
    // Pace control
    pace: {
      english: [
        /\b(speak (slower|faster)|talk (slower|faster))\b/i,
        /\b(too (fast|slow)|very (fast|slow))\b/i,
        /\b(slow down|speed up)\b/i,
        /\b(more slowly|more quickly)\b/i
      ],
      spanish: [
        /\b(habla más (despacio|lento|rápido))\b/i,
        /\b(muy (rápido|lento))\b/i,
        /\b(más despacio|más rápido)\b/i
      ],
      french: [
        /\b(parlez plus (lentement|vite))\b/i,
        /\b(trop (vite|lent))\b/i,
        /\b(plus lentement|plus rapidement)\b/i
      ],
      german: [
        /\b(sprechen sie (langsamer|schneller))\b/i,
        /\b(zu (schnell|langsam))\b/i,
        /\b(langsamer|schneller)\b/i
      ],
      dutch: [
        /\b(spreek (langzamer|sneller))\b/i,
        /\b(te (snel|langzaam))\b/i,
        /\b(langzamer|sneller)\b/i
      ],
      portuguese: [
        /\b(fala mais (devagar|rápido))\b/i,
        /\b(muito (rápido|devagar))\b/i,
        /\b(mais devagar|mais rápido)\b/i
      ]
    },
    
    // Volume control
    volume: {
      english: [
        /\b(speak (louder|quieter)|talk (louder|quieter))\b/i,
        /\b(too (loud|quiet)|very (loud|quiet))\b/i,
        /\b(turn up|turn down|volume)\b/i,
        /\b(can barely hear|hard to hear)\b/i
      ],
      spanish: [
        /\b(habla más (alto|fuerte|bajo))\b/i,
        /\b(muy (alto|bajo))\b/i,
        /\b(volumen|más fuerte)\b/i
      ],
      french: [
        /\b(parlez plus (fort|doucement))\b/i,
        /\b(trop (fort|faible))\b/i,
        /\b(volume|plus fort)\b/i
      ],
      german: [
        /\b(sprechen sie (lauter|leiser))\b/i,
        /\b(zu (laut|leise))\b/i,
        /\b(lautstärke|lauter)\b/i
      ],
      dutch: [
        /\b(spreek (harder|zachter))\b/i,
        /\b(te (hard|zacht))\b/i,
        /\b(volume|harder)\b/i
      ],
      portuguese: [
        /\b(fala mais (alto|baixo))\b/i,
        /\b(muito (alto|baixo))\b/i,
        /\b(volume|mais alto)\b/i
      ]
    },
    
    // Conversation management
    conversation_management: {
      english: [
        /\b(let's (start over|begin again|restart))\b/i,
        /\b(change (topic|subject)|different topic)\b/i,
        /\b(can we (talk about|discuss))\b/i,
        /\b(i want to (talk about|discuss))\b/i,
        /\b(let's talk about)\b/i,
        /\b(wait a (moment|second|minute))\b/i
      ],
      spanish: [
        /\b(empecemos de nuevo|volvamos a empezar)\b/i,
        /\b(cambiemos de tema|otro tema)\b/i,
        /\b(podemos hablar de|hablemos de)\b/i,
        /\b(quiero hablar de)\b/i,
        /\b(espera un momento)\b/i
      ],
      french: [
        /\b(recommençons|on recommence)\b/i,
        /\b(changeons de sujet|autre sujet)\b/i,
        /\b(on peut parler de|parlons de)\b/i,
        /\b(je veux parler de)\b/i,
        /\b(attendez un moment)\b/i
      ],
      german: [
        /\b(fangen wir neu an|von vorne)\b/i,
        /\b(wechseln wir das thema|anderes thema)\b/i,
        /\b(können wir über|sprechen wir über)\b/i,
        /\b(ich möchte über)\b/i,
        /\b(warten sie einen moment)\b/i
      ],
      dutch: [
        /\b(laten we opnieuw beginnen|opnieuw starten)\b/i,
        /\b(ander onderwerp|onderwerp veranderen)\b/i,
        /\b(kunnen we praten over|laten we praten over)\b/i,
        /\b(ik wil praten over)\b/i,
        /\b(wacht even)\b/i
      ],
      portuguese: [
        /\b(vamos recomeçar|começar de novo)\b/i,
        /\b(mudar de assunto|outro assunto)\b/i,
        /\b(podemos falar sobre|vamos falar sobre)\b/i,
        /\b(quero falar sobre)\b/i,
        /\b(espera um momento)\b/i
      ]
    }
  };

  // Check patterns for the specified language and English (as fallback)
  const languagesToCheck = language === 'english' ? ['english'] : [language, 'english'];
  
  for (const lang of languagesToCheck) {
    for (const [category, langPatterns] of Object.entries(patterns)) {
      const categoryPatterns = langPatterns[lang as keyof typeof langPatterns];
      if (categoryPatterns) {
        for (const pattern of categoryPatterns) {
          if (pattern.test(cleanText)) {
            return {
              isMetaConversational: true,
              confidence: 'high',
              category: category as MetaConversationalResult['category'],
              reason: `Detected ${category} request in ${lang}`
            };
          }
        }
      }
    }
  }

  // Check for medium confidence cases (partial matches or context-dependent)
  const mediumConfidencePatterns = [
    /\b(what|que|quoi|was|wat|o que)\b.*\b(you|tu|sie|je|você)\b.*\b(said|dijiste|dit|gesagt|zei|disse)\b/i,
    /\b(i|yo|je|ich|ik|eu)\b.*\b(don't|no|ne|nicht|niet|não)\b.*\b(understand|entiendo|comprends|verstehe|begrijp|entendo)\b/i,
    /\b(can|puedes|peux|können|kun|podes)\b.*\b(you|tu|sie|je|você)\b/i
  ];

  for (const pattern of mediumConfidencePatterns) {
    if (pattern.test(cleanText)) {
      return {
        isMetaConversational: false, // Will be determined by AI
        confidence: 'medium',
        reason: 'Uncertain - requires AI classification'
      };
    }
  }

  return {
    isMetaConversational: false,
    confidence: 'low',
    reason: 'No meta-conversational patterns detected'
  };
}

/**
 * Enhanced utility function to determine if a sentence should be analyzed based on comprehensive criteria
 * Includes meta-conversational detection, repetition checking, and learning value assessment
 */
export function shouldConsiderForAnalysis(
  text: string, 
  recentUserMessages: string[] = [], 
  language: string = 'english'
): AnalysisDecision {
  if (!text || text.trim().length < 3) {
    return {
      shouldAnalyze: false,
      reason: 'Text too short',
      confidence: 1.0
    };
  }

  // First check for meta-conversational content
  const metaResult = detectMetaConversational(text, language);
  if (metaResult.isMetaConversational && metaResult.confidence === 'high') {
    return {
      shouldAnalyze: false,
      reason: `Meta-conversational: ${metaResult.reason}`,
      confidence: 0.9,
      isMetaConversational: true,
      metaCategory: metaResult.category
    };
  }

  // If medium confidence meta-conversational, let backend AI decide
  if (metaResult.confidence === 'medium') {
    return {
      shouldAnalyze: true, // Let backend AI classify
      reason: 'Uncertain meta-conversational - needs AI classification',
      confidence: 0.5,
      isMetaConversational: false
    };
  }

  // Quick check for very short responses
  const shortResponses = [
    'yes', 'no', 'ok', 'okay', 'sure', 'maybe', 'thanks', 'thank you',
    'hi', 'hello', 'bye', 'goodbye', 'me too', 'same', 'exactly',
    'right', 'correct', 'wrong', 'true', 'false', 'good', 'bad',
    // Multilingual short responses
    'sí', 'oui', 'ja', 'sim', // yes
    'gracias', 'merci', 'danke', 'dank je', 'obrigado', // thank you
    'hola', 'bonjour', 'hallo', 'olá', // hello
    'adiós', 'au revoir', 'auf wiedersehen', 'tot ziens', 'tchau' // goodbye
  ];

  const cleanedText = text.trim().toLowerCase().replace(/[.!?]/g, '');
  if (shortResponses.includes(cleanedText)) {
    return {
      shouldAnalyze: false,
      reason: 'Simple acknowledgment or short response',
      confidence: 0.9
    };
  }

  // Check word count
  const wordCount = text.split(/\s+/).length;
  if (wordCount < 4) {
    return {
      shouldAnalyze: false,
      reason: 'Too few words for meaningful analysis',
      confidence: 0.8
    };
  }

  // Enhanced repetition detection with conversation context
  if (recentUserMessages.length > 0) {
    const currentTextLower = text.toLowerCase().trim();
    
    for (const recentMessage of recentUserMessages) {
      const recentLower = recentMessage.toLowerCase().trim();
      
      // Exact match
      if (currentTextLower === recentLower) {
        return {
          shouldAnalyze: false,
          reason: 'Exact repetition of recent message',
          confidence: 0.95
        };
      }
      
      // High similarity check (90% word overlap)
      const currentWords = currentTextLower.split(/\s+/);
      const recentWords = recentLower.split(/\s+/);
      
      if (currentWords.length > 3 && recentWords.length > 3) {
        let matchCount = 0;
        for (const word of currentWords) {
          if (word.length > 2 && recentWords.includes(word)) {
            matchCount++;
          }
        }
        
        const similarity = matchCount / Math.max(currentWords.length, recentWords.length);
        if (similarity > 0.9) {
          return {
            shouldAnalyze: false,
            reason: 'Highly similar to recent message',
            confidence: 0.85
          };
        }
      }
    }
  }

  // Advanced scoring system for learning value
  let score = 0;
  let reasons = [];

  // Grammar complexity indicators
  const complexGrammarPatterns = [
    /\b(although|however|nevertheless|furthermore|moreover|consequently)\b/i,
    /\b(would have|could have|should have|might have)\b/i,
    /\b(if.*had.*would|were.*to)\b/i, // Conditionals
    /\b(having|being).*\b(ed|ing)\b/i, // Participles
  ];

  for (const pattern of complexGrammarPatterns) {
    if (pattern.test(text)) {
      score += 15;
      reasons.push('complex grammar');
      break;
    }
  }

  // Advanced vocabulary indicators
  const advancedVocabPatterns = [
    /\b(sophisticated|comprehensive|fundamental|significant|substantial|considerable)\b/i,
    /\b(analyze|synthesize|evaluate|demonstrate|implement|establish)\b/i,
    /\b(consequently|furthermore|nevertheless|simultaneously|predominantly)\b/i
  ];

  for (const pattern of advancedVocabPatterns) {
    if (pattern.test(text)) {
      score += 10;
      reasons.push('advanced vocabulary');
      break;
    }
  }

  // Complex verb forms
  const complexVerbPatterns = [
    /\b(has been|have been|had been).*ing\b/i, // Perfect continuous
    /\b(will have|would have).*ed\b/i, // Future/conditional perfect
    /\b(being|having been).*ed\b/i // Passive participles
  ];

  for (const pattern of complexVerbPatterns) {
    if (pattern.test(text)) {
      score += 12;
      reasons.push('complex verb forms');
      break;
    }
  }

  // Question forms (valuable for analysis)
  if (/^(what|how|why|when|where|which|who).*\?$/i.test(text.trim())) {
    score += 8;
    reasons.push('question form');
  }

  // Optimal length bonus
  if (wordCount >= 8 && wordCount <= 25) {
    score += 10;
    reasons.push('optimal length');
  } else if (wordCount > 25) {
    score += 5;
    reasons.push('substantial length');
  }

  // Language-specific patterns
  const languageSpecificPatterns = {
    spanish: [/\b(subjuntivo|condicional)\b/i, /\bque.*[áéíóú]\b/i],
    french: [/\b(subjonctif|conditionnel)\b/i, /\bque.*[àâäéèêëïîôöùûü]\b/i],
    german: [/\b(konjunktiv|würde)\b/i, /\b[äöüß]\b/i],
    dutch: [/\b(zouden|zullen)\b/i, /\bij\b/i],
    portuguese: [/\b(subjuntivo|condicional)\b/i, /\bque.*[áàâãéêíóôõúç]\b/i]
  };

  const langPatterns = languageSpecificPatterns[language as keyof typeof languageSpecificPatterns];
  if (langPatterns) {
    for (const pattern of langPatterns) {
      if (pattern.test(text)) {
        score += 8;
        reasons.push('language-specific complexity');
        break;
      }
    }
  }

  // Decision based on score
  if (score >= 25) {
    return {
      shouldAnalyze: true,
      reason: `High learning value: ${reasons.join(', ')}`,
      confidence: 0.9
    };
  } else if (score >= 15) {
    return {
      shouldAnalyze: true,
      reason: `Moderate learning value: ${reasons.join(', ')}`,
      confidence: 0.7
    };
  } else if (score >= 8) {
    return {
      shouldAnalyze: true,
      reason: `Some learning value: ${reasons.join(', ')}`,
      confidence: 0.6
    };
  } else {
    return {
      shouldAnalyze: false,
      reason: 'Limited learning value for analysis',
      confidence: 0.7
    };
  }
}

// Analysis cache interface
interface AnalysisCache {
  [textHash: string]: {
    result: BackgroundAnalysisResponse;
    timestamp: number;
    language: string;
    level: string;
  };
}

// In-memory cache for analysis results
const analysisCache: AnalysisCache = {};
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// Generate cache key for analysis results
function getCacheKey(text: string, language: string, level: string): string {
  const normalizedText = text.toLowerCase().trim().replace(/[.!?]/g, '');
  return btoa(`${normalizedText}-${language}-${level}`).replace(/[^a-zA-Z0-9]/g, '');
}

// Get cached analysis result
export function getCachedAnalysis(
  text: string, 
  language: string, 
  level: string
): BackgroundAnalysisResponse | null {
  const key = getCacheKey(text, language, level);
  const cached = analysisCache[key];
  
  if (cached && (Date.now() - cached.timestamp) < CACHE_DURATION) {
    console.log('✅ [CACHE] Using cached analysis for:', text.substring(0, 30) + '...');
    return cached.result;
  }
  
  // Clean up expired cache entries
  if (cached && (Date.now() - cached.timestamp) >= CACHE_DURATION) {
    delete analysisCache[key];
  }
  
  return null;
}

// Store analysis result in cache
export function setCachedAnalysis(
  text: string, 
  language: string, 
  level: string, 
  result: BackgroundAnalysisResponse
): void {
  const key = getCacheKey(text, language, level);
  analysisCache[key] = {
    result,
    timestamp: Date.now(),
    language,
    level
  };
  console.log('💾 [CACHE] Stored analysis for:', text.substring(0, 30) + '...');
}

/**
 * Evaluate whether a sentence is substantial enough for analysis
 */
export async function evaluateSentenceWorthiness(
  request: SentenceEvaluationRequest
): Promise<SentenceEvaluationResponse> {
  try {
    console.log('🔍 [EVALUATION_API] Evaluating sentence worthiness:', request.text);
    
    const response = await fetch(`${getApiUrl()}/api/sentence/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ [EVALUATION_API] Evaluation result:', result);
    
    return result;
  } catch (error) {
    console.error('❌ [EVALUATION_API] Error evaluating sentence:', error);
    throw error;
  }
}

/**
 * Perform background sentence analysis
 */
export async function performBackgroundAnalysis(
  request: BackgroundAnalysisRequest
): Promise<BackgroundAnalysisResponse> {
  try {
    console.log('🔬 [ANALYSIS_API] Performing background analysis:', request.text);
    
    const response = await fetch(`${getApiUrl()}/api/sentence/background-analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ [ANALYSIS_API] Analysis completed:', result.analysis_id);
    
    return result;
  } catch (error) {
    console.error('❌ [ANALYSIS_API] Error performing analysis:', error);
    throw error;
  }
}

/**
 * Complete background sentence processing pipeline
 * Evaluates if sentence should be analyzed, and if so, performs the analysis
 */
export async function processBackgroundSentence(
  request: BackgroundAnalysisRequest
): Promise<BackgroundProcessResponse> {
  try {
    console.log('🔄 [PROCESS_API] Processing sentence in background:', request.text);
    
    const response = await fetch(`${getApiUrl()}/api/sentence/process-background`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    
    if (result.analyzed) {
      console.log('✅ [PROCESS_API] Sentence analyzed successfully:', result.analysis.analysis_id);
    } else {
      console.log('⏭️ [PROCESS_API] Sentence skipped:', result.reason);
    }
    
    return result;
  } catch (error) {
    console.error('❌ [PROCESS_API] Error processing sentence:', error);
    throw error;
  }
}

/**
 * Get color class based on score for UI display
 */
export function getScoreColorClass(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-yellow-600';
  return 'text-red-600';
}

/**
 * Get background class based on score for UI display
 */
export function getScoreBackgroundClass(score: number): string {
  if (score >= 80) return 'bg-green-500/20 border-green-500/30';
  if (score >= 60) return 'bg-yellow-500/20 border-yellow-500/30';
  return 'bg-red-500/20 border-red-500/30';
}

/**
 * Format timestamp for display
 */
export function formatAnalysisTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (error) {
    return 'Unknown time';
  }
}
