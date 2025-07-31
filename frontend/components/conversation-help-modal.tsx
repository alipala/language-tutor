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
    <div className={`fixed inset-0 z-50 transition-all duration-300 ${isOpen ? 'opacity-100' : 'opacity-0'}`}>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className={`
        absolute inset-4 md:inset-8 lg:inset-16 
        bg-white rounded-2xl shadow-2xl 
        transform transition-all duration-300 ease-out
        ${isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'}
        flex flex-col overflow-hidden
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
              <Lightbulb className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-bold text-gray-900">Conversation Help</h2>
              <p className="text-sm text-gray-600">AI-powered assistance for your {targetLanguage} conversation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
            aria-label="Close help modal"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-600">Generating personalized help content...</p>
              </div>
            </div>
          ) : helpData ? (
            <>
              {/* AI Response Summary */}
              <div className="p-4 md:p-6 bg-blue-50 border-b border-blue-100">
                <div className="flex items-start gap-3">
                  <MessageCircle className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-blue-900 mb-2">What the AI Tutor Said</h3>
                    <p className="text-blue-800 leading-relaxed">{helpData.ai_response_summary}</p>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-gray-200 bg-gray-50 px-4 md:px-6">
                <button
                  onClick={() => setActiveTab('responses')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'responses'
                      ? 'border-blue-500 text-blue-600 bg-white'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Suggested Responses ({helpData.suggested_responses.length})
                </button>
                <button
                  onClick={() => setActiveTab('vocabulary')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'vocabulary'
                      ? 'border-blue-500 text-blue-600 bg-white'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Vocabulary ({helpData.vocabulary_highlights.length})
                </button>
                <button
                  onClick={() => setActiveTab('grammar')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'grammar'
                      ? 'border-blue-500 text-blue-600 bg-white'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Grammar ({helpData.grammar_tips.length})
                </button>
                {helpData.cultural_context && (
                  <button
                    onClick={() => setActiveTab('culture')}
                    className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'culture'
                        ? 'border-blue-500 text-blue-600 bg-white'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Culture
                  </button>
                )}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-4 md:p-6">
                {activeTab === 'responses' && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900 mb-4">Choose a response to continue the conversation:</h3>
                    {helpData.suggested_responses.map((response, index) => (
                      <div
                        key={index}
                        className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50 transition-all cursor-pointer group"
                        onClick={() => onResponseSelect(response.text)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 mb-1">{response.text}</p>
                            <p className="text-sm text-gray-600 mb-2">/{response.pronunciation}/</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getDifficultyColor(response.difficulty_level)}`}>
                              {response.difficulty_level}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                playPronunciation(response.text);
                              }}
                              className="p-1 rounded-full hover:bg-blue-100 transition-colors"
                              aria-label="Play pronunciation"
                            >
                              <Volume2 className="w-4 h-4 text-blue-600" />
                            </button>
                          </div>
                        </div>
                        <p className="text-sm text-gray-700">{response.explanation}</p>
                        <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <p className="text-xs text-blue-600 font-medium">Click to use this response</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'vocabulary' && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900 mb-4">Key vocabulary from the conversation:</h3>
                    {helpData.vocabulary_highlights.map((vocab, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold text-gray-900">{vocab.word}</h4>
                              <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getDifficultyColor(vocab.difficulty_level)}`}>
                                {vocab.difficulty_level}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-1">/{vocab.pronunciation}/</p>
                          </div>
                          <button
                            onClick={() => playPronunciation(vocab.word)}
                            className="p-1 rounded-full hover:bg-blue-100 transition-colors"
                            aria-label="Play pronunciation"
                          >
                            <Volume2 className="w-4 h-4 text-blue-600" />
                          </button>
                        </div>
                        <p className="text-gray-700 mb-2">{vocab.definition}</p>
                        <div className="bg-gray-50 rounded-md p-3">
                          <p className="text-sm text-gray-600 font-medium mb-1">Example:</p>
                          <p className="text-sm text-gray-800 italic">"{vocab.example_sentence}"</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'grammar' && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900 mb-4">Grammar patterns to learn:</h3>
                    {helpData.grammar_tips.map((tip, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <BookOpen className="w-5 h-5 text-green-600" />
                          <h4 className="font-semibold text-gray-900">{tip.pattern}</h4>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getDifficultyColor(tip.difficulty_level)}`}>
                            {tip.difficulty_level}
                          </span>
                        </div>
                        <p className="text-gray-700 mb-3">{tip.explanation}</p>
                        <div className="bg-green-50 rounded-md p-3">
                          <p className="text-sm text-green-600 font-medium mb-1">Example:</p>
                          <p className="text-sm text-green-800 font-mono">"{tip.example}"</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'culture' && helpData.cultural_context && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900 mb-4">Cultural context:</h3>
                    <div className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Globe className="w-5 h-5 text-purple-600" />
                        <h4 className="font-semibold text-gray-900">{helpData.cultural_context.context}</h4>
                      </div>
                      <p className="text-gray-700 mb-3">{helpData.cultural_context.explanation}</p>
                      <div className="bg-purple-50 rounded-md p-3">
                        <p className="text-sm text-purple-600 font-medium mb-1">Why this matters:</p>
                        <p className="text-sm text-purple-800">{helpData.cultural_context.relevance}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Lightbulb className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-600">No help content available</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 md:p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500">
              Help content generated by AI • Press Esc to close
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Continue Conversation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationHelpModal;
