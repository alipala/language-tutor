'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface ConversationHelpData {
  ai_response_summary: string;
  suggested_responses: Array<{
    text: string;
    pronunciation: string;
    explanation: string;
  }>;
  vocabulary_highlights: Array<{
    word: string;
    definition: string;
    pronunciation: string;
    example_sentence: string;
  }>;
  generated_at: string;
}

interface HelpSettings {
  enabled: boolean;
  helpLanguage: string;
}

export const useInlineConversationHelp = (
  targetLanguage: string = 'english',
  userLevel: string = 'intermediate',
  topic: string = 'general'
) => {
  const [settings, setSettings] = useState<HelpSettings>({
    enabled: true,
    helpLanguage: 'english'
  });

  const [pendingHelp, setPendingHelp] = useState<{
    aiMessage: string;
    timestamp: number;
  } | null>(null);

  const [userResponseTimer, setUserResponseTimer] = useState<NodeJS.Timeout | null>(null);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const lastAiMessageRef = useRef<string>('');

  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('inlineHelpSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('[INLINE_HELP] Error loading settings:', error);
      }
    }
  }, []);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('inlineHelpSettings', JSON.stringify(settings));
  }, [settings]);

  const updateSettings = useCallback((newSettings: Partial<HelpSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  // Handle AI response completion - start 5-second timer
  const handleAiResponseComplete = useCallback((aiMessage: string) => {
    if (!settings.enabled || !aiMessage || aiMessage === lastAiMessageRef.current) {
      return;
    }

    console.log('[INLINE_HELP] AI response detected, starting 5-second timer');
    lastAiMessageRef.current = aiMessage;

    // Clear any existing timer
    if (userResponseTimer) {
      clearTimeout(userResponseTimer);
    }

    // Set pending help
    setPendingHelp({
      aiMessage,
      timestamp: Date.now()
    });

    // Start 5-second timer
    const timer = setTimeout(() => {
      if (!isUserSpeaking) {
        console.log('[INLINE_HELP] 5 seconds elapsed, user has not responded - showing help');
        // The help will be shown by the component that uses this hook
      }
    }, 5000);

    setUserResponseTimer(timer);
  }, [settings.enabled, userResponseTimer, isUserSpeaking]);

  // Handle user starting to speak - cancel help
  const handleUserSpeakingStart = useCallback(() => {
    console.log('[INLINE_HELP] User started speaking, canceling help');
    setIsUserSpeaking(true);
    
    // Clear timer and pending help
    if (userResponseTimer) {
      clearTimeout(userResponseTimer);
      setUserResponseTimer(null);
    }
    setPendingHelp(null);
  }, [userResponseTimer]);

  // Handle user stopping speaking
  const handleUserSpeakingStop = useCallback(() => {
    console.log('[INLINE_HELP] User stopped speaking');
    setIsUserSpeaking(false);
  }, []);

  // Clear help when user responds
  const clearPendingHelp = useCallback(() => {
    if (userResponseTimer) {
      clearTimeout(userResponseTimer);
      setUserResponseTimer(null);
    }
    setPendingHelp(null);
    setIsUserSpeaking(false);
  }, [userResponseTimer]);

  // Listen for AI response completion events from useRealtime
  useEffect(() => {
    const handleAiResponseComplete = (event: CustomEvent) => {
      const { aiResponse, conversationContext } = event.detail;
      
      if (settings.enabled && aiResponse) {
        console.log('[INLINE_HELP] AI response detected, starting 5-second timer');
        lastAiMessageRef.current = aiResponse;

        // Clear any existing timer
        if (userResponseTimer) {
          clearTimeout(userResponseTimer);
        }

        // Set pending help
        setPendingHelp({
          aiMessage: aiResponse,
          timestamp: Date.now()
        });

        // Start 5-second timer
        const timer = setTimeout(() => {
          if (!isUserSpeaking) {
            console.log('[INLINE_HELP] 5 seconds elapsed, user has not responded - showing help');
            // The help will be shown by the component that uses this hook
          }
        }, 5000);

        setUserResponseTimer(timer);
      }
    };

    // Listen for the custom event that indicates AI has finished speaking
    window.addEventListener('ai-response-complete', handleAiResponseComplete as EventListener);
    
    return () => {
      window.removeEventListener('ai-response-complete', handleAiResponseComplete as EventListener);
    };
  }, [settings.enabled, userResponseTimer, isUserSpeaking]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (userResponseTimer) {
        clearTimeout(userResponseTimer);
      }
    };
  }, [userResponseTimer]);

  return {
    settings,
    updateSettings,
    pendingHelp,
    isUserSpeaking,
    clearPendingHelp,
    handleAiResponseComplete,
    handleUserSpeakingStart,
    handleUserSpeakingStop,
    targetLanguage,
    userLevel,
    topic
  };
};

export default useInlineConversationHelp;
