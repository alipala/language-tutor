import { useState, useEffect, useCallback, useRef } from 'react';
import realtimeService from './realtimeService';
import { RealtimeMessage, RealtimeEvent, RealtimeTextDeltaEvent, RealtimeAudioTranscriptionEvent } from './types';

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

export function useRealtime() {
  // Check if running in browser environment
  const isBrowser = typeof window !== 'undefined';
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  // Add a ref to track the last message timestamp for proper ordering
  const lastMessageTimestampRef = useRef<string>(new Date().toISOString());
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initializationAttemptRef = useRef(false);
  const maxRetries = 2;
  const retryCountRef = useRef(0);

  // Store language and level parameters for reinitialization
  const languageRef = useRef<string | undefined>();
  const levelRef = useRef<string | undefined>();
  const topicRef = useRef<string | undefined>();
  
  // Reduce number of logs to prevent console spam
  const shouldLogEvent = useRef(true);

  // Helper function to determine if we need a space between text segments
  const needSpaceBetween = (currentText: string, newText: string): boolean => {
    if (!currentText || !newText) return false;
    
    return currentText.length > 0 && 
      !currentText.endsWith(' ') && 
      !currentText.endsWith('.') && 
      !currentText.endsWith(',') && 
      !currentText.endsWith('!') && 
      !currentText.endsWith('?') && 
      !currentText.endsWith(':') && 
      !currentText.endsWith(';') && 
      !currentText.endsWith('-') && 
      !newText.startsWith(' ') && 
      !newText.startsWith('.') && 
      !newText.startsWith(',') && 
      !newText.startsWith('!') && 
      !newText.startsWith('?') && 
      !newText.startsWith(':') && 
      !newText.startsWith(';') && 
      !newText.startsWith('-');
  };

  // Handle incoming messages from the realtime service
  const handleMessage = useCallback((event: RealtimeEvent) => {
    // Log important events
    if (event.type === 'conversation.item.created' || 
        event.type === 'conversation.item.input_audio_transcription.completed' ||
        event.type === 'response.audio_transcript.done' ||
        event.type === 'response.text.delta') {
      console.log('Received important event:', event.type);
      console.log('Event details:', JSON.stringify(event, null, 2));
    }
    
    if (event.type === 'response.text.delta') {
      const textEvent = event as RealtimeTextDeltaEvent;
      if (!textEvent.delta?.text) return;
      
      // Log the incoming delta for debugging
      console.log('Received text delta:', JSON.stringify(textEvent.delta));
      
      setMessages(prev => {
        // Check if we have a user message first
        if (prev.length === 0 || prev[prev.length - 1].role !== 'user') {
          // If there's no user message yet or the last message is not from the user,
          // we might be in an initialization state. In this case, just create a new assistant message.
          const existingAssistantMessage = prev.find(msg => msg.role === 'assistant' && !msg.itemId);
          
          if (existingAssistantMessage) {
            // If we already have an assistant message without an itemId, update it instead of creating a new one
            return prev.map(msg => 
              (msg.role === 'assistant' && !msg.itemId) 
                ? { 
                    ...msg, 
                    content: msg.content + (needSpaceBetween(msg.content, textEvent.delta.text) ? ' ' : '') + textEvent.delta.text 
                  }
                : msg
            );
          }
          
          // Create a new assistant message
          return [...prev, { 
            role: 'assistant', 
            content: textEvent.delta.text,
            timestamp: new Date().toISOString()
          }];
        }
        
        // Find the last assistant message that doesn't have an itemId (current streaming message)
        const lastAssistantIndex = prev.findIndex(msg => 
          msg.role === 'assistant' && !msg.itemId
        );
        
        if (lastAssistantIndex >= 0) {
          // Update existing message
          const lastAssistantMsg = prev[lastAssistantIndex];
          // Add a space before the new text if needed (when the last character isn't a space or punctuation)
          const needsSpace = needSpaceBetween(lastAssistantMsg.content, textEvent.delta.text);
          
          return prev.map((msg, idx) => 
            idx === lastAssistantIndex 
              ? { ...msg, content: msg.content + (needsSpace ? ' ' : '') + textEvent.delta.text }
              : msg
          );
        }
        
        // If we don't have an existing assistant message without an itemId, create a new one
        return [...prev, { 
          role: 'assistant', 
          content: textEvent.delta.text,
          timestamp: new Date().toISOString()
        }];
      });
    } else if (event.type === 'conversation.item.input_audio_transcription.completed') {
      if (!event.transcript?.trim()) return;
      
      // Clean the transcript by removing duplicates and normalizing
      const rawTranscript = event.transcript.trim();
      const transcriptionText = cleanTranscript(rawTranscript);
      
      setMessages(prev => {
        // Check if this transcription already exists by item_id OR by content
        const existingIndex = prev.findIndex(msg => 
          msg.role === 'user' && 
          (msg.itemId === event.item_id || msg.content === transcriptionText)
        );
        
        if (existingIndex >= 0) {
          // Update existing message
          return prev.map((msg, idx) => 
            idx === existingIndex
              ? { 
                  role: 'user',
                  content: transcriptionText,
                  itemId: event.item_id,
                  timestamp: new Date().toISOString()
                }
              : msg
          );
        }
        
        // Add new message only if it doesn't already exist
        return [...prev, {
          role: 'user',
          content: transcriptionText,
          itemId: event.item_id,
          timestamp: new Date().toISOString()
        }];
      });
    } else if (event.type === 'conversation.item.created') {
      if (event.item?.role === 'user') {
        let userText = '';
        
        // Try to get text content from different possible locations
        if (event.item?.input?.content?.text) {
          userText = event.item.input.content.text.trim();
        } else if (event.item?.content && Array.isArray(event.item.content)) {
          for (const content of event.item.content) {
            if (content.type === 'input_audio' && content.transcript) {
              userText = content.transcript.trim();
              break;
            }
          }
        }
        
        if (userText) {
          setMessages(prev => {
            // Check for duplicate messages by content OR item_id
            const isDuplicate = prev.some(msg => 
              msg.role === 'user' && 
              (msg.content === userText || msg.itemId === event.item.id)
            );
            
            if (isDuplicate) {
              console.log('Skipping duplicate user message:', userText);
              return prev;
            }
            
            return [...prev, {
              role: 'user',
              content: userText,
              itemId: event.item.id,
              timestamp: new Date().toISOString()
            }];
          });
        }
      } else if (event.item?.role === 'assistant') {
        // When a new assistant item is created, store its ID to associate future deltas with it
        const itemId = event.item.id;
        console.log('New assistant item created with ID:', itemId);
      }
    } else if (event.type === 'response.audio_transcript.delta') {
      const delta = event.delta?.trim() || '';
      if (!delta) return;
      
      // Log the audio transcript delta for debugging
      console.log('Received audio transcript delta:', delta);
      
      setMessages(prev => {
        // Try to find an existing message with this item_id
        const existingMessageIndex = prev.findIndex(msg => 
          msg.role === 'assistant' && msg.itemId === event.item_id
        );
        
        // If we found a message with this item_id, update it
        if (existingMessageIndex >= 0) {
          const existingMessage = prev[existingMessageIndex];
          const needsSpace = needSpaceBetween(existingMessage.content, delta);
          
          return prev.map((msg, idx) => 
            idx === existingMessageIndex
              ? { ...msg, content: msg.content + (needsSpace ? ' ' : '') + delta }
              : msg
          );
        }
        
        // If we don't have a message with this item_id yet, check if we have any incomplete assistant messages
        // that might be part of the same conversation turn
        const incompleteAssistantMessages = prev.filter(msg => 
          msg.role === 'assistant' && 
          (!msg.itemId || msg.itemId === '') && 
          msg.content.length < 100  // Only consider short messages as potentially incomplete
        );
        
        // If we have incomplete assistant messages, update the most recent one
        if (incompleteAssistantMessages.length > 0) {
          const lastIncompleteIndex = prev.findIndex(msg => 
            msg === incompleteAssistantMessages[incompleteAssistantMessages.length - 1]
          );
          
          const lastIncompleteMsg = prev[lastIncompleteIndex];
          const needsSpace = needSpaceBetween(lastIncompleteMsg.content, delta);
          
          return prev.map((msg, idx) => 
            idx === lastIncompleteIndex
              ? { 
                  ...msg, 
                  content: msg.content + (needsSpace ? ' ' : '') + delta,
                  itemId: event.item_id  // Associate this message with the item_id
                }
              : msg
          );
        }
        
        // If we don't have any existing message to update, create a new one
        return [...prev, {
          role: 'assistant',
          content: delta,
          itemId: event.item_id,
          timestamp: new Date().toISOString()
        }];
      });
    } else if (event.type === 'response.audio_transcript.done') {
      if (!event.transcript?.trim()) return;
      
      const transcript = event.transcript.trim();
      
      setMessages(prev => {
        // First, check if we already have this exact transcript
        const exactDuplicate = prev.some(msg => 
          msg.role === 'assistant' && 
          msg.content === transcript
        );
        
        if (exactDuplicate) {
          console.log('Ignoring duplicate transcript:', transcript.substring(0, 30) + '...');
          return prev;
        }
        
        // Check if we have any message with this item_id
        const existingIndex = prev.findIndex(msg => 
          msg.role === 'assistant' && 
          msg.itemId === event.item_id
        );
        
        if (existingIndex >= 0) {
          // Update existing message with the complete transcript
          return prev.map((msg, idx) => 
            idx === existingIndex
              ? {
                  role: 'assistant',
                  content: transcript,
                  itemId: event.item_id,
                  timestamp: new Date().toISOString(),
                  isComplete: true  // Mark as complete to avoid further updates
                }
              : msg
          );
        }
        
        // If we don't have a message with this item_id, check for any incomplete messages
        // that might contain partial content of this transcript
        const similarContentIndex = prev.findIndex(msg => 
          msg.role === 'assistant' && 
          !msg.isComplete &&
          (transcript.includes(msg.content) || msg.content.includes(transcript.substring(0, 20)))
        );
        
        if (similarContentIndex >= 0) {
          // Replace the similar content with the complete transcript
          return prev.map((msg, idx) => 
            idx === similarContentIndex
              ? {
                  role: 'assistant',
                  content: transcript,
                  itemId: event.item_id,
                  timestamp: new Date().toISOString(),
                  isComplete: true
                }
              : msg
          );
        }
        
        // If we can't find any related message, add a new one
        // This should rarely happen if delta events are working correctly
        console.log('Adding new message for complete transcript with no previous deltas');
        return [...prev, {
          role: 'assistant',
          content: transcript,
          itemId: event.item_id,
          timestamp: new Date().toISOString(),
          isComplete: true
        }];
      });
    }
  }, []);

  // Initialize the realtime service
  const initialize = useCallback(async (language?: string, level?: string, topic?: string, userPrompt?: string, assessmentData?: any) => {
    if (!isBrowser) return false;
    if (!realtimeService) return false;
    
    try {
      console.log('Initializing...');
      setError(null);
      
      // Store the parameters in refs for future use
      if (language) languageRef.current = language;
      if (level) levelRef.current = level;
      if (topic) topicRef.current = topic;
      
      // Store the userPrompt in sessionStorage if it's a custom topic
      if (topic === 'custom' && userPrompt) {
        console.log('Storing custom topic prompt for realtime service');
        sessionStorage.setItem('customTopicPrompt', userPrompt);
      }
      
      // Use either the provided parameters or the stored references
      const langToUse = language || languageRef.current;
      const levelToUse = level || levelRef.current;
      const topicToUse = topic || topicRef.current;
      
      // Get userPrompt from parameter or sessionStorage
      const userPromptToUse = userPrompt || 
        (topicToUse === 'custom' ? sessionStorage.getItem('customTopicPrompt') || undefined : undefined);
      
      // Initialize with language and level if provided
      console.log('Initializing with language:', langToUse, 'level:', levelToUse, 'topic:', topicToUse);
      if (topicToUse === 'custom' && userPromptToUse) {
        console.log('Using custom topic with prompt:', userPromptToUse.substring(0, 50) + (userPromptToUse.length > 50 ? '...' : ''));
      }
      
      // Log assessment data if provided
      if (assessmentData) {
        console.log('Initializing with assessment data:', JSON.stringify(assessmentData, null, 2));
      }
      
      const success = await realtimeService.initialize(
        handleMessage, // Use the handleMessage callback directly
        () => {
          console.log('Connected to service');
          setIsConnected(true);
        },
        () => {
          console.log('Disconnected from service');
          setIsConnected(false);
          setIsRecording(false);
        },
        langToUse,
        levelToUse,
        topicToUse,
        userPromptToUse,
        assessmentData
      );
      
      if (!success) {
        setError('Failed to initialize voice service. Please try again.');
        console.error('Failed to initialize voice service');
        return false;
      }
      
      setIsInitialized(true);
      return true;
    } catch (err) {
      console.error('Error in initialize:', err);
      setError('An error occurred during initialization');
      return false;
    }
  }, [isBrowser, handleMessage]); // Add handleMessage to dependencies

  // Format messages into a conversation history string
  const getFormattedConversationHistory = useCallback(() => {
    if (messages.length === 0) return '';
    
    // Create a formatted string with roles and content
    const formattedHistory = messages.map(msg => {
      const role = msg.role === 'assistant' ? 'Tutor' : 'Student';
      return `${role}: ${msg.content}`;
    }).join('\n');
    
    return formattedHistory;
  }, [messages]);

  // Start a conversation
  const startConversation = useCallback(async (conversationHistory?: string) => {
    if (!isBrowser) return false;
    
    try {
      console.log('Starting conversation...');
      setError(null);
      
      // Make sure we're initialized
      if (!isInitialized) {
        console.log('Not initialized, initializing first...');
        // Pass stored refs to ensure parameters are maintained
        // Get userPrompt from sessionStorage if it's a custom topic
        const storedUserPrompt = topicRef.current === 'custom' ? 
          sessionStorage.getItem('customTopicPrompt') || undefined : undefined;
        
        const initSuccess = await initialize(languageRef.current, levelRef.current, topicRef.current, storedUserPrompt);
        
        // Wait a bit for initialization to complete
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (!initSuccess) {
          console.error('Failed to initialize service');
          setError('Failed to initialize voice service');
          return false;
        }
      }
      
      // Request microphone access
      console.log('Requesting microphone access...');
      const micSuccess = await realtimeService.startMicrophone();
      if (!micSuccess) {
        console.error('Failed to access microphone');
        setError('Failed to access microphone. Please ensure microphone permissions are granted.');
        return false;
      }
      
      // Connect to OpenAI
      console.log('Connecting to OpenAI...');
      const connectSuccess = await realtimeService.connect();
      if (!connectSuccess) {
        console.error('Failed to connect to OpenAI');
        setError('Failed to connect to voice service');
        realtimeService.disconnect(); // Clean up resources
        return false;
      }
      
      // Start the conversation
      console.log('Starting the conversation...');
      try {
        // If there's conversation history, include it in the instructions
        let instructions = undefined;
        if (conversationHistory) {
          console.log('Continuing with previous conversation history');
          instructions = `Continue the conversation exactly where it left off. Here's the previous conversation history:\n\n${conversationHistory}\n\nDO NOT GREET THE USER AGAIN, just continue the conversation where it stopped.`;
        }
        
        const startSuccess = await realtimeService.startConversation(instructions);
        if (!startSuccess) {
          console.error('Failed to start conversation');
          setError('Failed to start conversation');
          realtimeService.disconnect(); // Clean up resources
          return false;
        }
      } catch (err) {
        console.error('Error starting conversation:', err);
        setError('Failed to start conversation');
        realtimeService.disconnect(); // Clean up resources
        return false;
      }
      
      // Everything succeeded
      console.log('Conversation started successfully');
      setIsRecording(true);
      return true;
    } catch (err) {
      console.error('Error starting conversation:', err);
      setError('Error starting conversation. Please try again.');
      realtimeService.disconnect(); // Clean up resources
      
      // Retry logic
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        console.log(`Retrying... Attempt ${retryCountRef.current} of ${maxRetries}`);
        // Wait a bit before retrying
        await new Promise(resolve => setTimeout(resolve, 1000));
        return startConversation();
      }
      
      return false;
    }
  }, [isBrowser, isInitialized, initialize]);

  // Stop the conversation
  const stopConversation = useCallback(() => {
    console.log('Stopping conversation...');
    try {
      realtimeService.disconnect();
    } catch (err) {
      console.error('Error disconnecting:', err);
    } finally {
      setIsRecording(false);
    }
  }, []);

  // Toggle the conversation state
  const toggleConversation = useCallback(async (instructions?: string) => {
    if (!isBrowser || !realtimeService) return false;
    
    try {
      if (isRecording) {
        console.log('Already recording, stopping conversation...');
        stopConversation();
        return true;
      } else {
        console.log('Not recording, starting conversation...');
        return await startConversation();
      }
    } catch (err) {
      console.error('Error toggling conversation:', err);
      setError('Failed to toggle conversation state');
      return false;
    }
  }, [isRecording, startConversation, stopConversation]);

  // Clean up on component unmount
  useEffect(() => {
    if (!isBrowser) return;
    
    return () => {
      console.log('Component unmounting, cleaning up...');
      realtimeService.disconnect();
    };
  }, [isBrowser]);

  return {
    isConnected,
    isRecording,
    messages,
    error,
    toggleConversation,
    startConversation,
    stopConversation,
    clearError: () => setError(null),
    initialize,
    getFormattedConversationHistory
  };
}
