'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { getApiUrl } from '@/lib/api-utils';

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

interface HelpSettings {
  help_enabled: boolean;
  help_language: string;
  show_pronunciation: boolean;
  show_grammar_tips: boolean;
  show_cultural_notes: boolean;
  show_vocabulary: boolean;
}

interface ConversationMessage {
  role: string;
  content: string;
  timestamp?: string;
}

export const useConversationHelpSystem = (
  targetLanguage: string,
  proficiencyLevel: string,
  topic?: string
) => {
  const [helpSettings, setHelpSettings] = useState<HelpSettings>({
    help_enabled: true, // Default to enabled for new system
    help_language: "english",
    show_pronunciation: true,
    show_grammar_tips: true,
    show_cultural_notes: true,
    show_vocabulary: true
  });

  const [helpData, setHelpData] = useState<ConversationHelpData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHelpReady, setIsHelpReady] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Track the last AI message to avoid duplicate processing
  const lastProcessedMessageRef = useRef<string>('');
  const helpGenerationTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load user's help settings on mount
  useEffect(() => {
    loadHelpSettings();
  }, []);

  const loadHelpSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        // Use default settings for guests
        return;
      }

      const response = await fetch(`${getApiUrl()}/api/conversation-help/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const settings = await response.json();
        setHelpSettings(settings);
        console.log('[CONVERSATION_HELP_SYSTEM] Loaded user settings:', settings);
      } else {
        console.warn('[CONVERSATION_HELP_SYSTEM] Failed to load settings, using defaults');
      }
    } catch (error) {
      console.error('[CONVERSATION_HELP_SYSTEM] Error loading settings:', error);
    }
  };

  const updateHelpSettings = useCallback(async (newSettings: Partial<HelpSettings>) => {
    try {
      const updatedSettings = { ...helpSettings, ...newSettings };
      
      // Only update if settings actually changed
      const hasChanged = Object.keys(newSettings).some(
        key => helpSettings[key as keyof HelpSettings] !== newSettings[key as keyof HelpSettings]
      );
      
      if (!hasChanged) {
        console.log('[CONVERSATION_HELP_SYSTEM] Settings unchanged, skipping update');
        return;
      }
      
      setHelpSettings(updatedSettings);

      const token = localStorage.getItem('token');
      if (!token) {
        // For guests, just update local state
        console.log('[CONVERSATION_HELP_SYSTEM] Guest user, settings updated locally only');
        return;
      }

      console.log('[CONVERSATION_HELP_SYSTEM] Updating settings on server:', newSettings);

      const response = await fetch(`${getApiUrl()}/api/conversation-help/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSettings),
      });

      if (response.ok) {
        console.log('[CONVERSATION_HELP_SYSTEM] Settings updated successfully');
        
        // Track settings update
        trackHelpUsage('settings_updated');
      } else {
        console.error('[CONVERSATION_HELP_SYSTEM] Failed to update settings');
      }
    } catch (error) {
      console.error('[CONVERSATION_HELP_SYSTEM] Error updating settings:', error);
    }
  }, [helpSettings]);

  const generateHelpContent = async (
    aiResponse: string,
    conversationContext: ConversationMessage[]
  ): Promise<ConversationHelpData | null> => {
    if (!helpSettings.help_enabled) {
      console.log('[CONVERSATION_HELP_SYSTEM] Help is disabled, skipping generation');
      return null;
    }

    // Avoid duplicate processing
    if (aiResponse === lastProcessedMessageRef.current) {
      console.log('[CONVERSATION_HELP_SYSTEM] Skipping duplicate AI response processing');
      return helpData;
    }

    setIsLoading(true);
    setError(null);
    setIsHelpReady(false);

    try {
      console.log('[CONVERSATION_HELP_SYSTEM] Generating help content for AI response:', aiResponse.substring(0, 100) + '...');

      const requestData = {
        ai_response: aiResponse,
        conversation_context: conversationContext.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        target_language: targetLanguage,
        user_language: helpSettings.help_language,
        proficiency_level: proficiencyLevel,
        topic: topic || null
      };

      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${getApiUrl()}/api/conversation-help/generate`, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestData),
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (response.status === 204) {
        // No contextual help available
        console.log('[CONVERSATION_HELP_SYSTEM] No contextual help available');
        setHelpData(null);
        setIsHelpReady(false);
        lastProcessedMessageRef.current = aiResponse;
        return null;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate help content');
      }

      const helpContent = await response.json();
      setHelpData(helpContent);
      setIsHelpReady(true);
      lastProcessedMessageRef.current = aiResponse;
      
      console.log('[CONVERSATION_HELP_SYSTEM] Help content generated successfully - ready for user interaction');
      
      // Track help generation
      trackHelpUsage('help_generated');
      
      return helpContent;
    } catch (error) {
      console.error('[CONVERSATION_HELP_SYSTEM] Error generating help content:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate help content');
      setIsHelpReady(false);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const showHelpModal = useCallback(() => {
    if (!helpSettings.help_enabled) {
      console.log('[CONVERSATION_HELP_SYSTEM] Help is disabled');
      return;
    }

    if (!isHelpReady || !helpData) {
      console.log('[CONVERSATION_HELP_SYSTEM] No help content available - button should not be clickable');
      return;
    }

    console.log('[CONVERSATION_HELP_SYSTEM] Showing help modal');
    setIsModalOpen(true);
    
    // Track modal opening
    trackHelpUsage('modal_opened');
  }, [helpSettings.help_enabled, isHelpReady, helpData]);

  const closeHelpModal = useCallback(() => {
    setIsModalOpen(false);
    
    // Track modal closing
    trackHelpUsage('modal_closed');
  }, []);

  const selectSuggestedResponse = useCallback((response: string) => {
    console.log('[CONVERSATION_HELP_SYSTEM] User selected suggested response:', response);
    
    // Track response selection
    trackHelpUsage('response_selected');
    
    // Close modal
    closeHelpModal();
    
    return response;
  }, [closeHelpModal]);

  const trackHelpUsage = async (helpType: string) => {
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      await fetch(`${getApiUrl()}/api/conversation-help/track-usage`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          help_type: helpType,
          language: targetLanguage
        }),
      });
    } catch (error) {
      console.error('[CONVERSATION_HELP_SYSTEM] Error tracking usage:', error);
      // Don't throw error for analytics failures
    }
  };

  // Reset help ready state when user starts speaking
  const resetHelpState = useCallback(() => {
    setIsHelpReady(false);
    setHelpData(null);
    setError(null);
    lastProcessedMessageRef.current = '';
    
    // Clear any pending help generation
    if (helpGenerationTimeoutRef.current) {
      clearTimeout(helpGenerationTimeoutRef.current);
      helpGenerationTimeoutRef.current = null;
    }
  }, []);

  // Listen for AI response completion events
  useEffect(() => {
    const handleAIResponseComplete = (event: CustomEvent) => {
      const { aiResponse, conversationContext } = event.detail;
      
      if (helpSettings.help_enabled && aiResponse) {
        console.log('[CONVERSATION_HELP_SYSTEM] AI response completion detected, starting help generation');
        
        // Clear any existing timeout
        if (helpGenerationTimeoutRef.current) {
          clearTimeout(helpGenerationTimeoutRef.current);
        }
        
        // Generate help content immediately when transcript is ready
        helpGenerationTimeoutRef.current = setTimeout(() => {
          generateHelpContent(aiResponse, conversationContext || []);
        }, 500); // Small delay to ensure transcript is fully processed
      }
    };

    // Listen for user speaking to reset help state
    const handleUserSpeakingStart = () => {
      if (isHelpReady || isLoading) {
        console.log('[CONVERSATION_HELP_SYSTEM] User started speaking, resetting help state');
        resetHelpState();
      }
    };

    // Listen for conversation end events
    const handleConversationEnd = () => {
      console.log('[CONVERSATION_HELP_SYSTEM] Conversation ended - resetting help state');
      resetHelpState();
    };

    const handleTimeUp = () => {
      console.log('[CONVERSATION_HELP_SYSTEM] Time up - resetting help state');
      resetHelpState();
    };

    // Listen for the custom events
    window.addEventListener('ai-response-complete', handleAIResponseComplete as EventListener);
    window.addEventListener('user-speaking-start', handleUserSpeakingStart as EventListener);
    window.addEventListener('conversation-ended', handleConversationEnd as EventListener);
    window.addEventListener('conversation-time-up', handleTimeUp as EventListener);

    return () => {
      window.removeEventListener('ai-response-complete', handleAIResponseComplete as EventListener);
      window.removeEventListener('user-speaking-start', handleUserSpeakingStart as EventListener);
      window.removeEventListener('conversation-ended', handleConversationEnd as EventListener);
      window.removeEventListener('conversation-time-up', handleTimeUp as EventListener);
      
      // Cleanup timeout
      if (helpGenerationTimeoutRef.current) {
        clearTimeout(helpGenerationTimeoutRef.current);
      }
    };
  }, [helpSettings.help_enabled, isHelpReady, isLoading, resetHelpState]);

  return {
    // Settings
    helpSettings,
    updateHelpSettings,
    
    // Help content and state
    helpData,
    isLoading,
    error,
    isHelpReady,
    
    // Modal state
    isModalOpen,
    showHelpModal,
    closeHelpModal,
    
    // Actions
    selectSuggestedResponse,
    generateHelpContent,
    trackHelpUsage,
    resetHelpState
  };
};

export default useConversationHelpSystem;
