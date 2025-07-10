import { useState, useEffect, useCallback, useRef } from 'react';
import realtimeService from './realtimeService';
import { RealtimeMessage, RealtimeEvent, RealtimeTextDeltaEvent, RealtimeAudioTranscriptionEvent } from './types';

// Enhanced conversation memory interface
interface ConversationMemory {
  recentMessages: RealtimeMessage[];
  conversationSummary: string;
  learningContext: {
    corrections: string[];
    objectives: string[];
    progressNotes: string[];
  };
  sessionMetadata: {
    planId?: string;
    weekNumber?: number;
    sessionNumber?: number;
    startTime: Date;
    language: string;
    level: string;
    topic: string;
  };
}

// Helper function to clean transcript text by removing duplicates
function cleanTranscript(transcript: string): string {
  if (!transcript) return '';
  
  // Split by newlines and remove duplicates
  const lines = transcript.split('\n').map(line => line.trim()).filter(line => line.length > 0);
  
  // Remove duplicate lines using Array.from instead of spread operator
  const uniqueLines = Array.from(new Set(lines));
  
  // Join back with a single space if there are multiple unique lines
  return uniqueLines.join(' ');
}

// Helper function to manage sliding window memory
function manageConversationMemory(
  messages: RealtimeMessage[], 
  existingMemory?: ConversationMemory
): ConversationMemory {
  const RECENT_MESSAGE_LIMIT = 12; // Keep last 12 messages in full detail
  
  // Get recent messages
  const recentMessages = messages.slice(-RECENT_MESSAGE_LIMIT);
  
  // If we have more messages than the limit, we need to summarize older ones
  const olderMessages = messages.slice(0, -RECENT_MESSAGE_LIMIT);
  
  let conversationSummary = existingMemory?.conversationSummary || '';
  
  // If we have older messages that aren't summarized yet, create a simple summary
  if (olderMessages.length > 0 && !conversationSummary) {
    const userMessages = olderMessages.filter(m => m.role === 'user').length;
    const assistantMessages = olderMessages.filter(m => m.role === 'assistant').length;
    conversationSummary = `Earlier conversation: ${userMessages} student messages, ${assistantMessages} tutor responses. Topics covered and corrections made.`;
  }
  
  return {
    recentMessages,
    conversationSummary,
    learningContext: existingMemory?.learningContext || {
      corrections: [],
      objectives: [],
      progressNotes: []
    },
    sessionMetadata: existingMemory?.sessionMetadata || {
      startTime: new Date(),
      language: '',
      level: '',
      topic: ''
    }
  };
}

// Enhanced context builder for conversation resumption with better formatting
function buildEnhancedConversationContext(memory: ConversationMemory): string {
  const recentHistory = memory.recentMessages
    .map(m => `${m.role === 'user' ? 'Student' : 'Tutor'}: ${m.content}`)
    .join('\n');
  
  let context = '';
  
  // 🎯 ENHANCED CONTEXT PRESERVATION - More detailed and structured
  context += `CONVERSATION CONTINUATION INSTRUCTIONS:
This is a CONTINUATION of an ongoing conversation. DO NOT restart or greet again.
Continue naturally from where the conversation left off.

LEARNING SESSION CONTEXT:
- Student Level: ${memory.sessionMetadata.level}
- Topic: ${memory.sessionMetadata.topic}
- Language: ${memory.sessionMetadata.language}
- Session Duration: ${Math.round((Date.now() - memory.sessionMetadata.startTime.getTime()) / 60000)} minutes

`;

  if (memory.conversationSummary) {
    context += `CONVERSATION SUMMARY:
${memory.conversationSummary}

`;
  }
  
  if (memory.recentMessages.length > 0) {
    context += `RECENT CONVERSATION:
${recentHistory}

`;
  }
  
  if (memory.learningContext.corrections.length > 0) {
    context += `CORRECTIONS MADE:
${memory.learningContext.corrections.join(', ')}

`;
  }
  
  if (memory.learningContext.objectives.length > 0) {
    context += `LEARNING OBJECTIVES COVERED:
${memory.learningContext.objectives.join(', ')}

`;
  }
  
  context += `CONTINUE SEAMLESSLY from where the conversation left off. Do not restart or greet again.`;
  
  return context;
}

export function useRealtime() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  const [conversationMemory, setConversationMemory] = useState<ConversationMemory | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  
  const retryCountRef = useRef(0);
  const maxRetries = 3;
  const isBrowser = typeof window !== 'undefined';

  // Handle incoming messages
  const handleMessage = useCallback((event: RealtimeEvent) => {
    if (event.type === 'response.audio_transcript.done') {
      const transcriptEvent = event as RealtimeAudioTranscriptionEvent;
      if (transcriptEvent.transcript) {
        const cleanedTranscript = cleanTranscript(transcriptEvent.transcript);
        if (cleanedTranscript) {
          const newMessage: RealtimeMessage = {
            role: 'assistant',
            content: cleanedTranscript,
            itemId: transcriptEvent.item_id || Date.now().toString(),
            timestamp: new Date().toISOString(),
            isComplete: true
          };
          
          setMessages(prev => {
            const updated = [...prev, newMessage];
            
            // Update conversation memory
            setConversationMemory(current => {
              if (!current) return current;
              return manageConversationMemory(updated, current);
            });
            
            return updated;
          });
        }
      }
    } else if (event.type === 'conversation.item.input_audio_transcription.completed') {
      const userTranscriptEvent = event as any;
      if (userTranscriptEvent.transcript) {
        const cleanedTranscript = cleanTranscript(userTranscriptEvent.transcript);
        if (cleanedTranscript) {
          const newMessage: RealtimeMessage = {
            role: 'user',
            content: cleanedTranscript,
            itemId: userTranscriptEvent.item_id || Date.now().toString(),
            timestamp: new Date().toISOString(),
            isComplete: true
          };
          
          setMessages(prev => {
            const updated = [...prev, newMessage];
            
            // Update conversation memory
            setConversationMemory(current => {
              if (!current) return current;
              return manageConversationMemory(updated, current);
            });
            
            return updated;
          });
        }
      }
    }
  }, []);

  // Initialize the realtime service
  const initialize = useCallback(async (
    language?: string,
    level?: string,
    topic?: string,
    userPrompt?: string,
    assessmentData?: any
  ): Promise<boolean> => {
    if (!isBrowser) return false;
    
    try {
      setError(null);
      
      const success = await realtimeService.initialize(
        handleMessage,
        () => setIsConnected(true),
        () => setIsConnected(false),
        language,
        level,
        topic,
        userPrompt,
        assessmentData
      );
      
      if (success) {
        setIsInitialized(true);
        
        // Initialize conversation memory
        const memory: ConversationMemory = {
          recentMessages: [],
          conversationSummary: '',
          learningContext: {
            corrections: [],
            objectives: [],
            progressNotes: []
          },
          sessionMetadata: {
            startTime: new Date(),
            language: language || '',
            level: level || '',
            topic: topic || ''
          }
        };
        setConversationMemory(memory);
        
        return true;
      } else {
        setError('Failed to initialize realtime service');
        return false;
      }
    } catch (err) {
      console.error('Error initializing realtime service:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    }
  }, [isBrowser, handleMessage]);

  // Start conversation with enhanced context
  const startConversation = useCallback(async (conversationHistory?: string): Promise<boolean> => {
    if (!isBrowser || !isInitialized) return false;
    
    try {
      setError(null);
      
      // Build enhanced context if we have conversation memory
      let instructions = conversationHistory;
      if (conversationMemory && !conversationHistory) {
        instructions = buildEnhancedConversationContext(conversationMemory);
      }
      
      // Start microphone first
      const micSuccess = await realtimeService.startMicrophone();
      if (!micSuccess) {
        setError('Failed to start microphone');
        return false;
      }
      
      // Connect to OpenAI
      const connectSuccess = await realtimeService.connect();
      if (!connectSuccess) {
        setError('Failed to connect to OpenAI');
        return false;
      }
      
      // Start the conversation
      const conversationSuccess = await realtimeService.startConversation(instructions);
      if (!conversationSuccess) {
        setError('Failed to start conversation');
        return false;
      }
      
      setIsRecording(true);
      retryCountRef.current = 0;
      return true;
    } catch (err) {
      console.error('Error starting conversation:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      
      // Retry logic
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        console.log(`Retrying conversation start (${retryCountRef.current}/${maxRetries})...`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        return startConversation(conversationHistory);
      }
      
      return false;
    }
  }, [isBrowser, isInitialized, conversationMemory]);

  // Pause conversation (NEW - keeps connection alive)
  const pauseConversation = useCallback((): boolean => {
    if (!isBrowser) return false;
    
    try {
      const success = realtimeService.pauseConversation();
      if (success) {
        setIsPaused(true);
        setIsRecording(false);
      }
      return success;
    } catch (err) {
      console.error('Error pausing conversation:', err);
      setError(err instanceof Error ? err.message : 'Failed to pause conversation');
      return false;
    }
  }, [isBrowser]);

  // Resume conversation (NEW - resumes from pause)
  const resumeConversation = useCallback((): boolean => {
    if (!isBrowser) return false;
    
    try {
      const success = realtimeService.resumeConversation();
      if (success) {
        setIsPaused(false);
        setIsRecording(true);
      }
      return success;
    } catch (err) {
      console.error('Error resuming conversation:', err);
      setError(err instanceof Error ? err.message : 'Failed to resume conversation');
      return false;
    }
  }, [isBrowser]);

  // Stop conversation
  const stopConversation = useCallback(() => {
    if (!isBrowser) return;
    
    try {
      realtimeService.disconnect();
      setIsConnected(false);
      setIsRecording(false);
      setIsPaused(false);
    } catch (err) {
      console.error('Error stopping conversation:', err);
      setError(err instanceof Error ? err.message : 'Failed to stop conversation');
    }
  }, [isBrowser]);

  // Toggle conversation (for backward compatibility)
  const toggleConversation = useCallback(async (): Promise<void> => {
    if (isRecording) {
      stopConversation();
    } else {
      await startConversation();
    }
  }, [isRecording, startConversation, stopConversation]);

  // Get formatted conversation history
  const getFormattedConversationHistory = useCallback((): string => {
    if (!conversationMemory) return '';
    return buildEnhancedConversationContext(conversationMemory);
  }, [conversationMemory]);

  // Check if conversation is paused
  const isPausedState = useCallback((): boolean => {
    return realtimeService.isPausedState();
  }, []);

  // Get pause duration
  const getPauseDuration = useCallback((): number => {
    return realtimeService.getPauseDuration();
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isBrowser) {
        realtimeService.disconnect();
      }
    };
  }, [isBrowser]);

  return {
    isConnected,
    isRecording,
    isInitialized,
    isPaused,
    error,
    messages,
    conversationMemory,
    initialize,
    startConversation,
    pauseConversation,      // NEW
    resumeConversation,     // NEW
    stopConversation,
    toggleConversation,     // For backward compatibility
    getFormattedConversationHistory,
    isPausedState,          // NEW
    getPauseDuration,       // NEW
    clearError              // NEW
  };
}
