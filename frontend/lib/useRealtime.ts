import { useState, useEffect, useCallback, useRef } from 'react';
import enhancedRealtimeService from './enhancedRealtimeService';
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

// Helper function to split transcript into sentences
function splitIntoSentences(text: string): string[] {
  if (!text || text.trim() === '') return [];
  
  // Split by sentence-ending punctuation, keeping the punctuation
  const sentences = text
    .split(/([.!?]+\s*)/)
    .reduce((acc: string[], part: string, index: number) => {
      if (index % 2 === 0) {
        // This is the text part
        if (part.trim()) {
          acc.push(part.trim());
        }
      } else {
        // This is the punctuation part
        if (acc.length > 0) {
          acc[acc.length - 1] += part;
        }
      }
      return acc;
    }, [])
    .map(sentence => sentence.trim())
    .filter(sentence => sentence.length > 0);
  
  // If no sentences were found (no punctuation), return the original text as one sentence
  if (sentences.length === 0 && text.trim()) {
    return [text.trim()];
  }
  
  return sentences;
}

// Smart sentence grouping function for better bubble organization
function smartGroupSentences(sentences: string[]): string[] {
  if (sentences.length === 0) return [];
  if (sentences.length === 1) return sentences;
  
  const groups: string[] = [];
  let currentGroup: string[] = [];
  let currentGroupLength = 0;
  
  for (const sentence of sentences) {
    const sentenceLength = sentence.length;
    
    // If sentence is very long (>120 chars), make it its own bubble
    if (sentenceLength > 120) {
      // Flush current group first
      if (currentGroup.length > 0) {
        groups.push(currentGroup.join(' '));
        currentGroup = [];
        currentGroupLength = 0;
      }
      // Add long sentence as separate bubble
      groups.push(sentence);
    }
    // If adding this sentence would make group too long (>150 total), start new group
    else if (currentGroupLength + sentenceLength > 150 && currentGroup.length > 0) {
      groups.push(currentGroup.join(' '));
      currentGroup = [sentence];
      currentGroupLength = sentenceLength;
    }
    // Add to current group
    else {
      currentGroup.push(sentence);
      currentGroupLength += sentenceLength + 1; // +1 for space
    }
  }
  
  // Don't forget the last group
  if (currentGroup.length > 0) {
    groups.push(currentGroup.join(' '));
  }
  
  return groups.length > 0 ? groups : sentences;
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

  // Track if AI has started speaking in current response
  const aiSpeakingStartedRef = useRef(false);

  // Handle incoming messages
  const handleMessage = useCallback((event: RealtimeEvent) => {
    // Detect when AI starts speaking (first audio transcript delta)
    if (event.type === 'response.audio_transcript.delta' && !aiSpeakingStartedRef.current) {
      console.log('[CONVERSATION_HELP] AI started speaking - emitting ai-speaking-start event');
      aiSpeakingStartedRef.current = true;
      
      // Emit custom event for conversation help modal to hide
      if (typeof window !== 'undefined') {
        const aiSpeakingStartEvent = new CustomEvent('ai-speaking-start');
        window.dispatchEvent(aiSpeakingStartEvent);
      }
    }
    
    // Reset AI speaking flag when response is complete
    if (event.type === 'response.done') {
      console.log('[CONVERSATION_HELP] AI response complete - resetting speaking flag');
      aiSpeakingStartedRef.current = false;
    }
    
    if (event.type === 'response.audio_transcript.done') {
      const transcriptEvent = event as RealtimeAudioTranscriptionEvent;
      if (transcriptEvent.transcript) {
        const cleanedTranscript = cleanTranscript(transcriptEvent.transcript);
        if (cleanedTranscript) {
          // Split transcript into sentences and apply smart grouping
          const sentences = splitIntoSentences(cleanedTranscript);
          const smartGroups = smartGroupSentences(sentences);
          const baseTimestamp = new Date().toISOString();
          const baseItemId = transcriptEvent.item_id || Date.now().toString();
          
          // Create multiple messages for each smart group
          const newMessages: RealtimeMessage[] = smartGroups.map((group, index) => ({
            role: 'assistant',
            content: group,
            itemId: `${baseItemId}-group-${index}`,
            timestamp: new Date(Date.now() + index * 100).toISOString(), // Slight delay between groups
            isComplete: true
          }));
          
          setMessages(prev => {
            const updated = [...prev, ...newMessages];
            
            // Update conversation memory
            setConversationMemory(current => {
              if (!current) return current;
              return manageConversationMemory(updated, current);
            });
            
            return updated;
          });
          
          // DO NOT emit ai-response-complete here - this triggers after each speech bubble
          // We only want to trigger help after ALL speech bubbles are complete
          // The correct trigger is in 'output_audio_buffer.stopped' below
        }
      }
    } else if (event.type === 'output_audio_buffer.stopped') {
      // This is the key event that indicates AI has finished speaking
      console.log('[CONVERSATION_HELP] Received message type: output_audio_buffer.stopped');
      
      // Wait a moment for all messages to be processed, then emit the help event
      setTimeout(() => {
        setMessages(currentMessages => {
          // Get all recent assistant messages (they should be the latest ones)
          const recentAssistantMessages = currentMessages.filter(msg => msg.role === 'assistant');
          
          if (recentAssistantMessages.length > 0) {
            // Get the last few assistant messages that form the complete response
            // Look for messages with similar timestamps (within last 2 seconds)
            const now = Date.now();
            const recentThreshold = 2000; // 2 seconds
            
            const recentAiMessages = recentAssistantMessages.filter(msg => {
              const msgTime = msg.timestamp ? new Date(msg.timestamp).getTime() : now;
              return (now - msgTime) < recentThreshold;
            });
            
            // Combine all recent AI messages into one complete response
            const completeAiResponse = recentAiMessages.length > 0 
              ? recentAiMessages.map(msg => msg.content).join(' ')
              : recentAssistantMessages[recentAssistantMessages.length - 1].content;
            
            // Emit custom event for conversation help system
            if (typeof window !== 'undefined') {
              const helpEvent = new CustomEvent('ai-response-complete', {
                detail: {
                  aiResponse: completeAiResponse,
                  conversationContext: currentMessages.slice(-5) // Last 5 messages for context
                }
              });
              window.dispatchEvent(helpEvent);
              console.log('[CONVERSATION_HELP] Emitted ai-response-complete event from output_audio_buffer.stopped');
              console.log('[CONVERSATION_HELP] Complete AI response:', completeAiResponse.substring(0, 100) + '...');
            }
          }
          
          return currentMessages; // Don't modify messages, just use them for the event
        });
      }, 100); // Small delay to ensure all messages are processed
    } else if (event.type === 'conversation.item.input_audio_transcription.completed') {
      const userTranscriptEvent = event as any;
      if (userTranscriptEvent.transcript) {
        const cleanedTranscript = cleanTranscript(userTranscriptEvent.transcript);
        if (cleanedTranscript) {
          // Split transcript into sentences and apply smart grouping
          const sentences = splitIntoSentences(cleanedTranscript);
          const smartGroups = smartGroupSentences(sentences);
          const baseTimestamp = new Date().toISOString();
          const baseItemId = userTranscriptEvent.item_id || Date.now().toString();
          
          // Create multiple messages for each smart group
          const newMessages: RealtimeMessage[] = smartGroups.map((group, index) => ({
            role: 'user',
            content: group,
            itemId: `${baseItemId}-group-${index}`,
            timestamp: new Date(Date.now() + index * 100).toISOString(), // Slight delay between groups
            isComplete: true
          }));
          
          setMessages(prev => {
            const updated = [...prev, ...newMessages];
            
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
      
      const success = await enhancedRealtimeService.initialize(
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
      const micSuccess = await enhancedRealtimeService.startMicrophone();
      if (!micSuccess) {
        setError('Failed to start microphone');
        return false;
      }
      
      // Connect to OpenAI
      const connectSuccess = await enhancedRealtimeService.connect();
      if (!connectSuccess) {
        setError('Failed to connect to OpenAI');
        return false;
      }
      
      // Start the conversation
      const conversationSuccess = await enhancedRealtimeService.startConversation(instructions);
      if (!conversationSuccess) {
        setError('Failed to start conversation');
        return false;
      }
      
      setIsRecording(true);
      retryCountRef.current = 0;
      
      // Emit user speaking start event for conversation help cancellation
      if (typeof window !== 'undefined') {
        const userSpeakingEvent = new CustomEvent('user-speaking-start');
        window.dispatchEvent(userSpeakingEvent);
        console.log('[CONVERSATION_HELP] Emitted user-speaking-start event');
      }
      
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
      const success = enhancedRealtimeService.pauseConversation();
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
      const success = enhancedRealtimeService.resumeConversation();
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
      enhancedRealtimeService.disconnect();
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
    return enhancedRealtimeService.isPausedState();
  }, []);

  // Get pause duration
  const getPauseDuration = useCallback((): number => {
    return enhancedRealtimeService.getPauseDuration();
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isBrowser) {
        enhancedRealtimeService.disconnect();
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
