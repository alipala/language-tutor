'use client';

import React, { useState, useEffect } from 'react';
import { X, Volume2, BookOpen, MessageCircle, Globe, Lightbulb } from 'lucide-react';

interface SuggestedResponse {
  text: string;
  pronunciation: string;
  difficulty_level: string;
  explanation: string;
}

interface VocabularyItem {
  word: string;
  definition: string;
  pronunciation: string;
  example_sentence: string;
  difficulty_level: string;
}

interface GrammarTip {
  pattern: string;
  explanation: string;
  example: string;
  difficulty_level: string;
}

interface CulturalNote {
  context: string;
  explanation: string;
  relevance: string;
}

interface ConversationHelpData {
  ai_response_summary: string;
  suggested_responses: SuggestedResponse[];
  vocabulary_highlights: VocabularyItem[];
  grammar_tips: GrammarTip[];
  cultural_context?: CulturalNote;
  generated_at: string;
}

interface ConversationHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  helpData: ConversationHelpData | null;
  isLoading: boolean;
  onResponseSelect: (response: string) => void;
  targetLanguage: string;
}

const ConversationHelpModal: React.FC<ConversationHelpModalProps> = ({
  isOpen,
  onClose,
  helpData,
  isLoading,
  onResponseSelect,
  targetLanguage
}) => {
  const [activeTab, setActiveTab] = useState<'responses' | 'vocabulary' | 'grammar' | 'culture'>('responses');
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
    } else {
      const timer = setTimeout(() => setIsVisible(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const playPronunciation = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = getLanguageCode(targetLanguage);
      utterance.rate = 0.8;
      speechSynthesis.speak(utterance);
    }
  };

  const getLanguageCode = (language: string): string => {
    const languageMap: { [key: string]: string } = {
      'english': 'en-US',
      'spanish': 'es-ES',
      'french': 'fr-FR',
      'german': 'de-DE',
      'italian': 'it-IT',
      'portuguese': 'pt-PT',
      'dutch': 'nl-NL',
      'russian': 'ru-RU',
      'chinese': 'zh-CN',
      'japanese': 'ja-JP',
      'korean': 'ko-KR',
      'arabic': 'ar-SA',
      'hindi': 'hi-IN',
      'turkish': 'tr-TR'
    };
    return languageMap[language.toLowerCase()] || 'en-US';
  };

  const getDifficultyColor = (level: string): string => {
    switch (level.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (!isVisible) return null;

  return (
    <div className="bg-white border border-purple-200 rounded-lg shadow-lg p-4 mb-4 mx-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-bold">D</span>
          </div>
          <h3 className="font-semibold text-gray-900">Conversation Help</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Close help"
        >
          <X className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-4">
          <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p className="text-sm text-gray-600">Generating help...</p>
        </div>
      ) : helpData ? (
        <>
          {/* AI Response Summary */}
          <div className="mb-3">
            <div className="flex items-start gap-2">
              <MessageCircle className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-gray-900 text-sm mb-1">What the AI said:</h4>
                <p className="text-sm text-gray-700">{helpData.ai_response_summary}</p>
              </div>
            </div>
          </div>

          {/* Suggested Responses */}
          {helpData.suggested_responses.length > 0 && (
            <div className="mb-3">
              <h4 className="font-medium text-gray-900 text-sm mb-2">Suggested responses:</h4>
              <div className="space-y-2">
                {helpData.suggested_responses.slice(0, 2).map((response, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-md p-2 hover:border-purple-300 hover:bg-purple-50 transition-all cursor-pointer group"
                    onClick={() => onResponseSelect(response.text)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{response.text}</p>
                        <p className="text-xs text-gray-500">/{response.pronunciation}/</p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          playPronunciation(response.text);
                        }}
                        className="p-1 rounded-full hover:bg-purple-100 transition-colors"
                        aria-label="Play pronunciation"
                      >
                        <Volume2 className="w-3 h-3 text-purple-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              {helpData.suggested_responses.length > 2 && (
                <button className="text-xs text-purple-600 hover:text-purple-700 mt-1">
                  ▼ More
                </button>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-4">
          <p className="text-sm text-gray-600">No help content available</p>
        </div>
      )}
    </div>
  );
};

export default ConversationHelpModal;
