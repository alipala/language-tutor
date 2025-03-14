import { useState, useEffect, useCallback, useRef } from 'react';
import realtimeService from './realtimeService';
import { RealtimeMessage, RealtimeEvent, RealtimeTextDeltaEvent, RealtimeAudioTranscriptionEvent } from './types';

export function useRealtime() {
  // Check if running in browser environment
  const isBrowser = typeof window !== 'undefined';
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initializationAttemptRef = useRef(false);
  const maxRetries = 2;
  const retryCountRef = useRef(0);

  // Handle incoming messages from the realtime service
  const handleMessage = useCallback((event: RealtimeEvent) => {
    console.log('Received event:', event.type);
    console.log('Event details:', JSON.stringify(event, null, 2));
    
    // Handle different event types
    if (event.type === 'response.text.delta') {
      const textEvent = event as RealtimeTextDeltaEvent;
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        
        if (lastMessage && lastMessage.role === 'assistant') {
          // Update the last message
          const updatedMessages = [...prev];
          updatedMessages[prev.length - 1] = {
            ...lastMessage,
            content: lastMessage.content + (textEvent.delta?.text || '')
          };
          return updatedMessages;
        } else {
          // Create a new message
          return [...prev, { role: 'assistant', content: textEvent.delta?.text || '' }];
        }
      });
    } else if (event.type === 'conversation.item.input_audio_transcription.completed') {
      console.log('Transcription completed event:', event);
      // Add user's transcribed message
      if (event.transcript) {
        const transcriptionText = event.transcript;
        console.log('Adding user transcription:', transcriptionText);
        setMessages(prev => {
          // Find if we already have a placeholder message for this item_id
          const existingIndex = prev.findIndex(msg => 
            msg.role === 'user' && msg.content === '...' && msg.itemId === event.item_id
          );
          
          if (existingIndex >= 0) {
            // Update the placeholder message
            const updatedMessages = [...prev];
            updatedMessages[existingIndex] = {
              role: 'user', 
              content: transcriptionText,
              itemId: event.item_id
            };
            return updatedMessages;
          } else {
            // Add as a new message if no placeholder exists
            return [...prev, { 
              role: 'user', 
              content: transcriptionText,
              itemId: event.item_id 
            }];
          }
        });
      }
    } else if (event.type === 'conversation.item.created') {
      // Handle conversation item created events which can contain user transcripts
      console.log('Item created event:', event);
      if (event.item?.role === 'user') {
        // Check for content in different formats
        let userText = '';
        
        // Check for direct text content
        if (event.item?.input?.content?.text) {
          userText = event.item.input.content.text;
          console.log('Found text content:', userText);
        } 
        // Check for input_audio content with transcript
        else if (event.item?.content && Array.isArray(event.item.content)) {
          // Look for input_audio type content with transcript
          console.log('Checking content array:', event.item.content);
          for (const content of event.item.content) {
            console.log('Content item:', content);
            if (content.type === 'input_audio' && content.transcript) {
              userText = content.transcript;
              console.log('Found transcript in content:', userText);
              break;
            }
          }
        }
        
        if (userText) {
          console.log('Adding user text to messages:', userText);
          setMessages(prev => {
            // Check if this exact message already exists to avoid duplicates
            const messageExists = prev.some(msg => 
              msg.role === 'user' && msg.content === userText
            );
            
            if (!messageExists) {
              return [...prev, { 
                role: 'user', 
                content: userText,
                itemId: event.item.id 
              }];
            }
            return prev;
          });
        } else {
          // Add a placeholder message that will be updated when transcription completes
          console.log('No user text found in the event, adding placeholder message');
          setMessages(prev => {
            // Check if we already have a placeholder for this item
            const placeholderExists = prev.some(msg => 
              msg.role === 'user' && msg.itemId === event.item.id
            );
            
            if (!placeholderExists) {
              return [...prev, { 
                role: 'user', 
                content: '...', // Placeholder content
                itemId: event.item.id 
              }];
            }
            return prev;
          });
        }
      }
    } else if (event.type === 'response.audio_transcript.delta') {
      // Handle assistant messages from audio transcript delta events
      setMessages(prev => {
        const lastMessage = prev.length > 0 ? prev[prev.length - 1] : null;
        
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.itemId === event.item_id) {
          // Update the last message
          const updatedMessages = [...prev];
          updatedMessages[prev.length - 1] = {
            ...lastMessage,
            content: lastMessage.content + (event.delta || '')
          };
          return updatedMessages;
        } else {
          // Create a new message
          return [...prev, { 
            role: 'assistant', 
            content: event.delta || '',
            itemId: event.item_id 
          }];
        }
      });
    } else if (event.type === 'response.audio_transcript.done') {
      if (event.transcript) {
        // Find if we already have a message for this item_id
        setMessages(prev => {
          const existingIndex = prev.findIndex(msg => 
            msg.role === 'assistant' && msg.itemId === event.item_id
          );
          
          if (existingIndex >= 0) {
            // Update the existing message
            const updatedMessages = [...prev];
            updatedMessages[existingIndex] = {
              role: 'assistant', 
              content: event.transcript,
              itemId: event.item_id
            };
            return updatedMessages;
          } else {
            // Add as a new message
            return [...prev, { 
              role: 'assistant', 
              content: event.transcript,
              itemId: event.item_id 
            }];
          }
        });
      }
    }
  }, []);

  // Store language and level parameters for reinitialization
  const languageRef = useRef<string | undefined>();
  const levelRef = useRef<string | undefined>();

  // Initialize the realtime service
  const initialize = useCallback(async (language?: string, level?: string) => {
    // If language and level are provided, store them for future use
    if (language) languageRef.current = language;
    if (level) levelRef.current = level;
    
    // Use stored values if not provided
    const langToUse = language || languageRef.current;
    const levelToUse = level || levelRef.current;
    if (initializationAttemptRef.current) return true; // Return true if already initializing
    initializationAttemptRef.current = true;
    
    try {
      console.log('Initializing realtime service...');
      setError(null);
      
      // First, ensure any existing connections are closed
      realtimeService.disconnect();
      
      const success = await realtimeService.initialize(
        handleMessage,
        () => {
          console.log('Connected to realtime service');
          setIsConnected(true);
        },
        () => {
          console.log('Disconnected from realtime service');
          setIsConnected(false);
          setIsRecording(false);
        },
        langToUse,
        levelToUse
      );
      
      if (success) {
        console.log('Realtime service initialized successfully');
        setIsInitialized(true);
        initializationAttemptRef.current = false;
        retryCountRef.current = 0;
        return true;
      } else {
        console.error('Failed to initialize realtime service');
        setError('Failed to initialize realtime service');
        initializationAttemptRef.current = false;
        return false;
      }
    } catch (err) {
      console.error('Error initializing realtime service:', err);
      setError('Error initializing realtime service');
      initializationAttemptRef.current = false;
      return false;
    }
  }, [handleMessage]);

  // Start a conversation
  const startConversation = useCallback(async () => {
    if (!isBrowser) return false;
    
    try {
      console.log('Starting conversation...');
      setError(null);
      
      // Make sure we're initialized
      if (!isInitialized) {
        console.log('Not initialized, initializing first...');
        const initSuccess = await initialize();
        
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
        const startSuccess = await realtimeService.startConversation();
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
  const toggleConversation = useCallback(async () => {
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
    initialize
  };
}
