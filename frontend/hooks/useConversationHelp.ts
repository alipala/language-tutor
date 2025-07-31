'use client';

import { useState, useEffect, useCallback } from 'react';
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

export const useConversationHelp = (
  targetLanguage: string,
  proficiencyLevel: string,
  topic?: string
) => {
  const [helpSettings, setHelpSettings] = useState<HelpSettings>({
    help_enabled: false,
    help_language: "english",
    show_pronunciation: true,
    show_grammar_tips: true,
    show_cultural_notes: true,
    show_vocabulary: true
  });

  const [helpData, setHelpData] = useState<ConversationHelpData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

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
        console.log('[CONVERSATION_HELP] Loaded user settings:', settings);
      } else {
        console.warn('[CONVERSATION_HELP] Failed to load settings, using defaults');
      }
    } catch (error) {
      console.error('[CONVERSATION_HELP] Error loading settings:', error);
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
        console.log('[CONVERSATION_HELP] Settings unchanged, skipping update');
        return;
      }
      
      setHelpSettings(updatedSettings);

      const token = localStorage.getItem('token');
      if (!token) {
        // For guests, just update local state
        console.log('[CONVERSATION_HELP] Guest user, settings updated locally only');
        return;
      }

      console.log('[CONVERSATION_HELP] Updating settings on server:', newSettings);

      const response = await fetch(`${getApiUrl()}/api/conversation-help/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSettings),
      });

      if (response.ok) {
        console.log('[CONVERSATION_HELP] Settings updated successfully');
        
        // Track settings update
        trackHelpUsage('settings_updated');
      } else {
        console.error('[CONVERSATION_HELP] Failed to update settings');
      }
    } catch (error) {
      console.error('[CONVERSATION_HELP] Error updating settings:', error);
    }
  }, [helpSettings]);

  const generateHelpContent = async (
    aiResponse: string,
    conversationContext: ConversationMessage[]
  ): Promise<ConversationHelpData | null> => {
    if (!helpSettings.help_enabled) {
      console.log('[CONVERSATION_HELP] Help is disabled, skipping generation');
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('[CONVERSATION_HELP] Generating help content for AI response:', aiResponse.substring(0, 100) + '...');

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
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate help content');
      }

      const helpContent = await response.json();
      setHelpData(helpContent);
      
      console.log('[CONVERSATION_HELP] Help content generated successfully');
      
      // Track help generation
      trackHelpUsage('help_generated');
      
      return helpContent;
    } catch (error) {
      console.error('[CONVERSATION_HELP] Error generating help content:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate help content');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const showHelpModal = useCallback(async (
    aiResponse: string,
    conversationContext: ConversationMessage[]
  ) => {
    if (!helpSettings.help_enabled) {
      return;
    }

    console.log('[CONVERSATION_HELP] Showing help modal for AI response');
    
    // Show modal immediately, then load content
    setIsModalOpen(true);
    
    // Track modal opening
    trackHelpUsage('modal_opened');
    
    // Generate help content
    await generateHelpContent(aiResponse, conversationContext);
  }, [helpSettings.help_enabled]); // Removed unstable dependencies

  const closeHelpModal = useCallback(() => {
    setIsModalOpen(false);
    setHelpData(null);
    setError(null);
    
    // Track modal closing
    trackHelpUsage('modal_closed');
  }, []);

  const selectSuggestedResponse = useCallback((response: string) => {
    console.log('[CONVERSATION_HELP] User selected suggested response:', response);
    
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
      console.error('[CONVERSATION_HELP] Error tracking usage:', error);
      // Don't throw error for analytics failures
    }
  };

  // Listen for AI response completion events
  useEffect(() => {
    const handleAIResponseComplete = (event: CustomEvent) => {
      const { aiResponse, conversationContext } = event.detail;
      
      if (helpSettings.help_enabled && aiResponse) {
        console.log('[CONVERSATION_HELP] Detected AI response completion, triggering help modal');
        showHelpModal(aiResponse, conversationContext || []);
      }
    };

    // Listen for the custom event that indicates AI has finished speaking
    window.addEventListener('ai-response-complete', handleAIResponseComplete as EventListener);

    return () => {
      window.removeEventListener('ai-response-complete', handleAIResponseComplete as EventListener);
    };
  }, [showHelpModal, helpSettings.help_enabled]);

  return {
    // Settings
    helpSettings,
    updateHelpSettings,
    
    // Help content
    helpData,
    isLoading,
    error,
    
    // Modal state
    isModalOpen,
    showHelpModal,
    closeHelpModal,
    
    // Actions
    selectSuggestedResponse,
    generateHelpContent,
    trackHelpUsage
  };
};

export default useConversationHelp;
