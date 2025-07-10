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

/**
 * Utility function to determine if a sentence should be analyzed based on basic criteria
 * This can be used for quick client-side filtering before making API calls
 */
export function shouldConsiderForAnalysis(text: string): boolean {
  if (!text || text.trim().length < 3) {
    return false;
  }

  // Quick check for very short responses
  const shortResponses = [
    'yes', 'no', 'ok', 'okay', 'sure', 'maybe', 'thanks', 'thank you',
    'hi', 'hello', 'bye', 'goodbye', 'me too', 'same', 'exactly',
    'right', 'correct', 'wrong', 'true', 'false', 'good', 'bad'
  ];

  const cleanedText = text.trim().toLowerCase().replace(/[.!?]/g, '');
  if (shortResponses.includes(cleanedText)) {
    return false;
  }

  // Check word count
  const wordCount = text.split(/\s+/).length;
  if (wordCount < 4) {
    return false;
  }

  return true;
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
