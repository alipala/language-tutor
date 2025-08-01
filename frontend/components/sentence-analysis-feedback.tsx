'use client';

import { useState, useEffect } from 'react';
import { 
  submitAnalysisFeedback, 
  SentenceAnalysisFeedback,
  BackgroundAnalysisResponse 
} from '@/lib/background-sentence-api';

interface SentenceAnalysisFeedbackProps {
  analysis: BackgroundAnalysisResponse;
  language: string;
  level: string;
  sessionId: string;
  onFeedbackSubmitted?: () => void;
  onClose?: () => void;
}

// Global store to track feedback per analysis ID
const feedbackStore = new Map<string, boolean>();

export default function SentenceAnalysisFeedbackComponent({
  analysis,
  language,
  level,
  sessionId,
  onFeedbackSubmitted,
  onClose
}: SentenceAnalysisFeedbackProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  // Check if feedback was already given for this specific analysis
  useEffect(() => {
    const alreadyGiven = feedbackStore.get(analysis.analysis_id);
    if (alreadyGiven) {
      setFeedbackGiven(true);
    } else {
      setFeedbackGiven(false); // Reset for new analysis
      setIsSubmitting(false); // Also reset submitting state for new analysis
    }
  }, [analysis.analysis_id]);

  const handleFeedback = async (rating: number, feedbackType: 'positive' | 'neutral' | 'negative') => {
    // Prevent multiple submissions - check both local state and global store
    if (feedbackGiven || isSubmitting || feedbackStore.get(analysis.analysis_id)) {
      console.log('🚫 [FEEDBACK] Already submitted for analysis:', analysis.analysis_id);
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const feedback: SentenceAnalysisFeedback = {
        session_id: sessionId,
        feedback_type: 'quality_rating',
        sentence_text: analysis.recognized_text,
        language,
        level,
        analysis_decision: {
          should_analyze: true,
          reason: 'Analysis completed',
          confidence: 0.9
        },
        user_rating: rating,
        user_comment: feedbackType === 'positive' ? 'Helpful analysis' : 
                     feedbackType === 'neutral' ? 'Neutral feedback' : 
                     'Analysis could be improved'
      };

      const success = await submitAnalysisFeedback(feedback);
      
      if (success) {
        console.log('✅ [FEEDBACK] Rating submitted successfully:', feedbackType, 'for analysis:', analysis.analysis_id);
        
        // Mark as submitted in global store
        feedbackStore.set(analysis.analysis_id, true);
        setFeedbackGiven(true);
        onFeedbackSubmitted?.();
        
        // Auto-close after 2 seconds
        setTimeout(() => {
          onClose?.();
        }, 2000);
      } else {
        console.error('❌ [FEEDBACK] Failed to submit rating');
        setIsSubmitting(false);
      }
    } catch (error) {
      console.error('❌ [FEEDBACK] Error submitting rating:', error);
      setIsSubmitting(false);
    }
  };

  if (feedbackGiven) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-2 shadow-sm">
        <div className="flex items-center justify-center gap-2 text-green-700">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-xs font-medium">Feedback submitted</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-2 shadow-sm">
      <div className="flex items-center justify-center gap-1 sm:gap-2">
        {/* Thumbs Up */}
        <button
          onClick={() => handleFeedback(5, 'positive')}
          disabled={isSubmitting}
          className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 bg-green-100 hover:bg-green-200 text-green-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-target"
        >
          <span className="text-sm sm:text-base leading-none flex items-center justify-center">👍</span>
        </button>

        {/* Neutral */}
        <button
          onClick={() => handleFeedback(3, 'neutral')}
          disabled={isSubmitting}
          className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-target"
        >
          <span className="text-sm sm:text-base leading-none flex items-center justify-center">😐</span>
        </button>

        {/* Thumbs Down */}
        <button
          onClick={() => handleFeedback(1, 'negative')}
          disabled={isSubmitting}
          className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 bg-red-100 hover:bg-red-200 text-red-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-target"
        >
          <span className="text-sm sm:text-base leading-none flex items-center justify-center">👎</span>
        </button>

        {isSubmitting && (
          <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin ml-1"></div>
        )}
      </div>
    </div>
  );
}
