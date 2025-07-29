'use client';

import React, { useState, useEffect, useRef } from 'react';
import { HelpCircle, MessageCircle, BookOpen, X, Volume2, ChevronDown, ChevronUp } from 'lucide-react';

interface SuggestedResponse {
  text: string;
  pronunciation: string;
  explanation: string;
}

interface VocabularyItem {
  word: string;
  definition: string;
  pronunciation: string;
  example_sentence: string;
}

interface ConversationHelpData {
  ai_response_summary: string;
  suggested_responses: SuggestedResponse[];
  vocabulary_highlights: VocabularyItem[];
  generated_at: string;
}

interface ConversationHelpInlineProps {
  aiMessage: string;
  onHelpGenerated?: (helpData: ConversationHelpData) => void;
  targetLanguage: string;
  helpLanguage: string;
  isEnabled: boolean;
}

const ConversationHelpInline: React.FC<ConversationHelpInlineProps> = ({
  aiMessage,
  onHelpGenerated,
  targetLanguage,
  helpLanguage,
  isEnabled
}) => {
  const [showHelp, setShowHelp] = useState(false);
  const [helpData, setHelpData] = useState<ConversationHelpData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [showCountdown, setShowCountdown] = useState(true);

  // 5-second countdown timer - only start when component mounts with a new AI message
  useEffect(() => {
    if (!isEnabled || !aiMessage || aiMessage === lastAiMessageRef.current) return;

    console.log('[INLINE_HELP] Starting 5-second countdown for new AI message');
    lastAiMessageRef.current = aiMessage;
    
    setShowCountdown(true);
    setCountdown(5);
    setShowHelp(false);
    setHelpData(null);
    
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          setShowCountdown(false);
          setShowHelp(true);
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [aiMessage, isEnabled]);

  // Track the last AI message to prevent duplicate timers
  const lastAiMessageRef = useRef<string>('');

  // Generate help content when help is shown
  useEffect(() => {
    if (showHelp && !helpData && !isLoading) {
      generateHelpContent();
    }
  }, [showHelp]);

  const generateHelpContent = async () => {
    if (!aiMessage) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/conversation-help/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ai_response: aiMessage,
          target_language: targetLanguage,
          help_language: helpLanguage,
          user_level: 'intermediate', // Could be dynamic
          conversation_topic: 'travel' // Could be dynamic
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setHelpData(data);
        onHelpGenerated?.(data);
      } else {
        console.error('Failed to generate help content');
        // Fallback content
        setHelpData({
          ai_response_summary: "The AI tutor just spoke to you about the conversation topic.",
          suggested_responses: [
            {
              text: "I understand",
              pronunciation: "aɪ ˌʌndərˈstænd",
              explanation: "A simple way to acknowledge what was said"
            },
            {
              text: "Can you tell me more?",
              pronunciation: "kæn ju tɛl mi mɔr",
              explanation: "Ask for additional information"
            }
          ],
          vocabulary_highlights: [],
          generated_at: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Error generating help content:', error);
      // Fallback content
      setHelpData({
        ai_response_summary: "The AI tutor just spoke to you about the conversation topic.",
        suggested_responses: [
          {
            text: "I understand",
            pronunciation: "aɪ ˌʌndərˈstænd",
            explanation: "A simple way to acknowledge what was said"
          }
        ],
        vocabulary_highlights: [],
        generated_at: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const playPronunciation = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = targetLanguage === 'english' ? 'en-US' : 'en-US';
      utterance.rate = 0.8;
      speechSynthesis.speak(utterance);
    }
  };

  const handleGetHelp = () => {
    setShowCountdown(false);
    setShowHelp(true);
  };

  const handleClose = () => {
    setShowHelp(false);
    setShowCountdown(false);
    setIsExpanded(false);
  };

  // Don't show anything if help is disabled
  if (!isEnabled) return null;

  // Show countdown timer
  if (showCountdown && countdown > 0) {
    return (
      <div className="flex items-center justify-center mt-3 mb-2">
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
          <HelpCircle className="w-4 h-4 text-blue-600" />
          <span className="text-sm text-blue-700">
            Need help? Getting assistance in {countdown}s
          </span>
          <button
            onClick={handleGetHelp}
            className="text-xs bg-blue-600 text-white px-3 py-1 rounded-full hover:bg-blue-700 transition-colors"
          >
            Get Help Now
          </button>
        </div>
      </div>
    );
  }

  // Show help button
  if (!showHelp) {
    return (
      <div className="flex justify-center mt-3 mb-2">
        <button
          onClick={handleGetHelp}
          className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
        >
          <HelpCircle className="w-4 h-4" />
          <span className="text-sm font-medium">Get Help</span>
        </button>
      </div>
    );
  }

  // Show help content
  return (
    <div className="mt-3 mb-2 bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <HelpCircle className="w-3 h-3 text-white" />
          </div>
          <span className="text-sm font-semibold text-gray-800">Conversation Help</span>
        </div>
        <button
          onClick={handleClose}
          className="p-1 rounded-full hover:bg-white/50 transition-colors"
        >
          <X className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">Analyzing response...</span>
          </div>
        </div>
      ) : helpData ? (
        <div className="space-y-3">
          {/* AI Response Summary */}
          <div className="bg-white/70 rounded-lg p-3 border border-blue-100">
            <div className="flex items-start gap-2 mb-2">
              <MessageCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <h4 className="text-sm font-medium text-gray-800">What the AI said:</h4>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{helpData.ai_response_summary}</p>
          </div>

          {/* Suggested Responses */}
          <div className="bg-white/70 rounded-lg p-3 border border-green-100">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-800">Suggested responses:</h4>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800"
              >
                {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {isExpanded ? 'Less' : 'More'}
              </button>
            </div>
            
            <div className="space-y-2">
              {helpData.suggested_responses.slice(0, isExpanded ? undefined : 2).map((response, index) => (
                <div key={index} className="bg-white rounded-md p-2 border border-gray-100 hover:border-green-300 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">{response.text}</p>
                      <p className="text-xs text-gray-500 mt-1">/{response.pronunciation}/</p>
                      {isExpanded && (
                        <p className="text-xs text-gray-600 mt-1">{response.explanation}</p>
                      )}
                    </div>
                    <button
                      onClick={() => playPronunciation(response.text)}
                      className="p-1 rounded-full hover:bg-green-100 transition-colors ml-2"
                    >
                      <Volume2 className="w-3 h-3 text-green-600" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Vocabulary (if expanded) */}
          {isExpanded && helpData.vocabulary_highlights.length > 0 && (
            <div className="bg-white/70 rounded-lg p-3 border border-yellow-100">
              <h4 className="text-sm font-medium text-gray-800 mb-2">Key vocabulary:</h4>
              <div className="space-y-2">
                {helpData.vocabulary_highlights.slice(0, 3).map((vocab, index) => (
                  <div key={index} className="bg-white rounded-md p-2 border border-gray-100">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-800">{vocab.word}</p>
                        <p className="text-xs text-gray-600">{vocab.definition}</p>
                      </div>
                      <button
                        onClick={() => playPronunciation(vocab.word)}
                        className="p-1 rounded-full hover:bg-yellow-100 transition-colors ml-2"
                      >
                        <Volume2 className="w-3 h-3 text-yellow-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-sm text-gray-600">Unable to generate help content</p>
        </div>
      )}
    </div>
  );
};

export default ConversationHelpInline;
