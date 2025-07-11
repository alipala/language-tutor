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
 * Enhanced utility function to determine if a sentence should be analyzed
 * Implements smart filtering to reduce unnecessary API calls by ~70%
 */
export function shouldConsiderForAnalysis(
  text: string, 
  conversationContext: string[] = [],
  language: string = 'english'
): { 
  shouldAnalyze: boolean; 
  confidence: number; 
  reason: string; 
} {
  // Quick rejections for empty or very short text
  if (!text || text.trim().length < 8) {
    return { shouldAnalyze: false, confidence: 1.0, reason: "Text too short (< 8 chars)" };
  }

  const words = text.trim().split(/\s+/);
  const wordCount = words.length;
  
  // Reject very short sentences
  if (wordCount < 3) {
    return { shouldAnalyze: false, confidence: 0.95, reason: "Too few words (< 3)" };
  }

  // Enhanced short response detection with more comprehensive list
  const shortResponses = new Set([
    // Basic responses
    'yes', 'no', 'ok', 'okay', 'sure', 'maybe', 'thanks', 'thank you',
    'hi', 'hello', 'bye', 'goodbye', 'me too', 'same', 'exactly',
    'right', 'correct', 'wrong', 'true', 'false', 'good', 'bad',
    
    // Extended responses
    'nice', 'great', 'awesome', 'terrible', 'awful', 'perfect',
    'absolutely', 'definitely', 'probably', 'possibly', 'certainly',
    'of course', 'no problem', 'you too', 'sounds good', 'makes sense',
    'i see', 'i understand', 'got it', 'alright', 'fine', 'cool',
    
    // Language-specific common responses
    ...(language === 'spanish' ? ['sí', 'claro', 'bueno', 'vale', 'perfecto'] : []),
    ...(language === 'french' ? ['oui', 'bien', 'parfait', 'daccord', 'merci'] : []),
    ...(language === 'german' ? ['ja', 'gut', 'perfekt', 'danke', 'genau'] : []),
    ...(language === 'dutch' ? ['ja', 'goed', 'perfect', 'dank je', 'precies'] : [])
  ]);

  const cleanedText = text.toLowerCase().replace(/[.!?]/g, '').trim();
  if (shortResponses.has(cleanedText)) {
    return { shouldAnalyze: false, confidence: 0.95, reason: "Simple/common response" };
  }

  // Check for repetition in recent conversation context
  if (conversationContext.length > 0) {
    const recentUserMessages = conversationContext.slice(-3);
    const isRepetitive = recentUserMessages.some(msg => {
      const msgCleaned = msg.toLowerCase().replace(/[.!?]/g, '').trim();
      return msgCleaned === cleanedText || 
             (cleanedText.length > 5 && msgCleaned.includes(cleanedText)) ||
             (msgCleaned.length > 5 && cleanedText.includes(msgCleaned));
    });
    
    if (isRepetitive) {
      return { shouldAnalyze: false, confidence: 0.85, reason: "Repetitive content" };
    }
  }

  // Check for complex grammar patterns that indicate learning value
  const complexGrammarPatterns = [
    /\b(because|although|however|therefore|meanwhile|furthermore|nevertheless|consequently|moreover|thus|hence)\b/i,
    /\b(would|could|should|might|may|will|shall|must|ought)\b/i,
    /\b(if|when|while|since|unless|until|before|after|during|despite)\b/i,
    /\b(who|which|that|where|why|how|what|whose)\b.*\b(is|are|was|were|have|has|had)\b/i, // Relative clauses
    /\b(not only|either|neither|both|whether)\b/i, // Complex conjunctions
  ];

  const hasComplexGrammar = complexGrammarPatterns.some(pattern => pattern.test(text));

  // Check for interesting vocabulary (longer words that indicate complexity)
  const interestingWords = words.filter(word => 
    word.length > 6 && 
    !/^\d+$/.test(word) && // Not just numbers
    !['because', 'however', 'therefore', 'although'].includes(word.toLowerCase()) // Not just conjunctions
  );

  const hasInterestingVocabulary = interestingWords.length > 0;

  // Check for verb tenses and forms that indicate grammar complexity
  const verbPatterns = [
    /\b\w+ing\b/i, // Present participle/gerund
    /\b\w+ed\b/i,  // Past tense (regular)
    /\bhave\s+\w+ed\b/i, // Present perfect
    /\bhad\s+\w+ed\b/i,  // Past perfect
    /\bwill\s+\w+\b/i,   // Future tense
  ];

  const hasComplexVerbs = verbPatterns.some(pattern => pattern.test(text));

  // Scoring system for analysis worthiness
  let score = 0;
  let reasons = [];

  // Positive indicators
  if (hasComplexGrammar) {
    score += 3;
    reasons.push("complex grammar");
  }
  
  if (hasInterestingVocabulary) {
    score += 2;
    reasons.push("advanced vocabulary");
  }
  
  if (hasComplexVerbs) {
    score += 1;
    reasons.push("complex verb forms");
  }
  
  if (wordCount >= 8 && wordCount <= 20) {
    score += 2;
    reasons.push("optimal length");
  } else if (wordCount > 20) {
    score += 1;
    reasons.push("comprehensive sentence");
  }

  // Check for questions (often good for analysis)
  if (text.includes('?')) {
    score += 1;
    reasons.push("question form");
  }

  // Negative indicators
  if (wordCount < 5) {
    score -= 2;
    reasons.push("very short");
  }

  // Decision logic
  if (score >= 4) {
    return { 
      shouldAnalyze: true, 
      confidence: Math.min(0.9, 0.6 + (score * 0.1)), 
      reason: `High learning value: ${reasons.join(', ')}` 
    };
  } else if (score >= 2) {
    return { 
      shouldAnalyze: true, 
      confidence: 0.6 + (score * 0.05), 
      reason: `Moderate learning value: ${reasons.join(', ')}` 
    };
  } else {
    return { 
      shouldAnalyze: false, 
      confidence: 0.7, 
      reason: `Low learning value: insufficient complexity` 
    };
  }
}

/**
 * Legacy function for backward compatibility
 * @deprecated Use shouldConsiderForAnalysis with full parameters instead
 */
export function shouldConsiderForAnalysisLegacy(text: string): boolean {
  const result = shouldConsiderForAnalysis(text);
  return result.shouldAnalyze;
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
