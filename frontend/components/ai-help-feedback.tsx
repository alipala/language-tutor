'use client';

import { useState } from 'react';

interface AiHelpFeedbackProps {
  helpContent: string;
  helpType: 'contextual' | 'inline' | 'modal';
  language: string;
  level: string;
  sessionId: string;
  onFeedbackSubmitted?: () => void;
  onClose?: () => void;
}

export default function AiHelpFeedback({
  helpContent,
  helpType,
  language,
  level,
  sessionId,
  onFeedbackSubmitted,
  onClose
}: AiHelpFeedbackProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  const handleFeedback = async (rating: number, feedbackType: 'positive' | 'neutral' | 'negative') => {
    // Prevent multiple submissions
    if (feedbackGiven || isSubmitting) return;
    
    setIsSubmitting(true);
    
    try {
      const feedback = {
        session_id: sessionId,
        help_type: helpType,
        help_content: helpContent.substring(0, 200), // Truncate for logging
        language,
        level,
        rating,
        feedback_type: feedbackType,
        timestamp: new Date().toISOString()
      };

      console.log('📝 [AI_HELP_FEEDBACK] Rating submitted:', feedbackType, feedback);
      
      // TODO: Replace with actual API call when backend endpoint is ready
      // const response = await fetch(`${getApiUrl()}/api/feedback/ai-help`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(feedback)
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setFeedbackGiven(true);
      onFeedbackSubmitted?.();
      
      // Auto-close after 2 seconds
      setTimeout(() => {
        onClose?.();
      }, 2000);
    } catch (error) {
      console.error('❌ [AI_HELP_FEEDBACK] Error submitting feedback:', error);
      setIsSubmitting(false);
    }
  };

  if (feedbackGiven) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-3 shadow-lg">
        <div className="flex items-center justify-center gap-2 text-green-700">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-sm font-medium">Thank you for your feedback!</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-3 shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-semibold text-purple-900 flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Was this AI help useful?
        </h4>
        {onClose && (
          <button
            onClick={onClose}
            className="text-purple-400 hover:text-purple-600 transition-colors"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <div className="flex items-center justify-center gap-2">
        {/* Thumbs Up */}
        <button
          onClick={() => handleFeedback(5, 'positive')}
          disabled={isSubmitting}
          className="flex items-center gap-1 px-3 py-2 text-xs bg-green-100 hover:bg-green-200 text-green-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
          </svg>
          👍
        </button>

        {/* Neutral */}
        <button
          onClick={() => handleFeedback(3, 'neutral')}
          disabled={isSubmitting}
          className="flex items-center gap-1 px-3 py-2 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          😐
        </button>

        {/* Thumbs Down */}
        <button
          onClick={() => handleFeedback(1, 'negative')}
          disabled={isSubmitting}
          className="flex items-center gap-1 px-3 py-2 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.60L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
          </svg>
          👎
        </button>

        {isSubmitting && (
          <div className="w-4 h-4 border border-purple-400 border-t-transparent rounded-full animate-spin ml-2"></div>
        )}
      </div>
    </div>
  );
}
