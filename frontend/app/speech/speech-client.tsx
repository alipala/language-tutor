'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { RealtimeMessage } from '@/lib/types';
import { useRouter } from 'next/navigation';
import PronunciationAssessment from '@/components/pronunciation-assessment';

interface SpeechClientProps {
  language: string;
  level: string;
  topic?: string;
  userPrompt?: string;
}

export default function SpeechClient({ language, level, topic, userPrompt }: SpeechClientProps) {
  // Moving the console.log out of the component body to prevent excessive logging
  const initialRenderRef = useRef(true);
  
  const router = useRouter();
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(false);
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const micPermissionDeniedRef = useRef(false);
  
  // Language alert state - simplified
  const [showLanguageAlert, setShowLanguageAlert] = useState(false);
  const languageAlertTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const globalSafetyTimeoutRef = useRef<NodeJS.Timeout | null>(null); // Backup safety mechanism
  
  // Add state for transcript processing
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  // State to track if conversation is paused for review (not ended)
  const [isPaused, setIsPaused] = useState<boolean>(false);
  // Ref to store conversation history when pausing
  const conversationHistoryRef = useRef<string>('');
  
  // Only log on initial render, not on every re-render
  useEffect(() => {
    if (initialRenderRef.current) {
      console.log('SpeechClient initializing with language:', language, 'level:', level, 'topic:', topic, 'at:', new Date().toISOString());
      if (topic === 'custom' && userPrompt) {
        console.log('Custom topic prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
      }
      initialRenderRef.current = false;
    }
  }, [language, level, topic, userPrompt]);
  
  // Add a useEffect to track component mounting and unmounting
  useEffect(() => {
    console.log('SpeechClient component mounted at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Store a flag to detect if the component unmounts unexpectedly
    const mountTimestamp = Date.now();
    sessionStorage.setItem('speechClientMountTime', mountTimestamp.toString());
    
    return () => {
      console.log('SpeechClient component unmounted at:', new Date().toISOString());
      console.log('Component was mounted for:', (Date.now() - mountTimestamp) / 1000, 'seconds');
      sessionStorage.removeItem('speechClientMountTime');
    };
  }, []);
  
  // Initialize the realtime service and handle messages
  const { isRecording, messages, error, toggleConversation, stopConversation, startConversation, initialize, getFormattedConversationHistory } = useRealtime();
  
  // Process messages for display and deduplicate assistant messages
  const processedMessages = useMemo(() => {
    // First, map the messages to add consistent IDs
    const mappedMessages = messages.map((message, index) => ({
      ...message,
      itemId: `message-${index}`,
      role: message.role === 'assistant' ? 'assistant' : 'user'
    }));

    // Deduplicate assistant messages by filtering out those with very similar content
    const filteredMessages: typeof mappedMessages = [];
    const seenContents: string[] = [];

    for (const message of mappedMessages) {
      if (message.role === 'user') {
        // Always keep user messages
        filteredMessages.push(message);
      } else {
        // For assistant messages, check if we've seen very similar content recently
        const contentToCheck = message.content.trim();
        let isDuplicate = false;

        // Check if this content is a duplicate or subset of a message we've already seen
        for (const seenContent of seenContents) {
          // If the content is very similar (one contains the other), consider it a duplicate
          if (seenContent.includes(contentToCheck) || contentToCheck.includes(seenContent)) {
            isDuplicate = true;
            break;
          }
        }

        if (!isDuplicate) {
          seenContents.push(contentToCheck);
          filteredMessages.push(message);
        }
      }
    }

    return filteredMessages;
  }, [messages]);
  
  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Show messages container when conversation starts
  useEffect(() => {
    if (messages.length > 0 && !showMessages) {
      setShowMessages(true);
    }
  }, [messages, showMessages]);
  
  // Track detected language for language alert
  const [detectedWrongLanguage, setDetectedWrongLanguage] = useState(false);
  // Add state for animation with better naming for clarity
  const [alertAnimationState, setAlertAnimationState] = useState<'entering' | 'visible' | 'exiting' | 'hidden'>('hidden');
  // Add ref to track if animation is in progress
  const animationInProgressRef = useRef(false);

  // Simplified function to show and auto-hide the language alert
  const showAndHideLanguageAlert = useCallback(() => {
    console.log('Showing language alert notification');
    
    // Clear any existing timeouts first
    if (languageAlertTimeoutRef.current) {
      clearTimeout(languageAlertTimeoutRef.current);
      languageAlertTimeoutRef.current = null;
    }
    
    // Clear any existing global safety timeout
    if (globalSafetyTimeoutRef.current) {
      clearTimeout(globalSafetyTimeoutRef.current);
      globalSafetyTimeoutRef.current = null;
    }
    
    // Show the alert with enter animation
    setShowLanguageAlert(true);
    setAlertAnimationState('entering');
    
    // Wait a tiny bit for entering animation to apply
    setTimeout(() => {
      // Set to visible state
      setAlertAnimationState('visible');
      
      // Set primary timeout to hide after exactly 2 seconds
      languageAlertTimeoutRef.current = setTimeout(() => {
        // Start exit animation
        setAlertAnimationState('exiting');
        
        // Wait for exit animation to complete
        setTimeout(() => {
          // Hide alert entirely
          setShowLanguageAlert(false);
          setAlertAnimationState('hidden');
          setDetectedWrongLanguage(false);
        }, 350); // Slightly longer than animation duration for safety
      }, 2000); // Show for exactly 2 seconds
      
      // Set a guaranteed fallback timeout that will force-hide regardless
      // This is our safety net in case animations fail
      globalSafetyTimeoutRef.current = setTimeout(() => {
        // If we're still showing the alert after 2.5 seconds, force hide it
        console.log('Global safety timeout check');
        
        // Force hide the alert regardless of state
        setShowLanguageAlert(false);
        setAlertAnimationState('hidden');
        setDetectedWrongLanguage(false);
        
        // Direct DOM manipulation as last resort
        const alertElement = document.getElementById('language-alert-notification');
        if (alertElement) {
          alertElement.style.display = 'none';
        }
      }, 2500); // 2.5 seconds total (2s display + 0.5s buffer)
    }, 10);
  }, []);
  
  // Handle language alert - only show when user speaks a different language
  useEffect(() => {
    // Only proceed if we're recording, using Dutch, detected wrong language, and not currently animating/showing alert
    if (isRecording && language === 'dutch' && detectedWrongLanguage && !showLanguageAlert) {
      showAndHideLanguageAlert();
    }
    
    // Cleanup function to prevent memory leaks
    return () => {
      if (languageAlertTimeoutRef.current) {
        clearTimeout(languageAlertTimeoutRef.current);
        languageAlertTimeoutRef.current = null;
      }
      
      // Also clear the global safety timeout
      if (globalSafetyTimeoutRef.current) {
        clearTimeout(globalSafetyTimeoutRef.current);
        globalSafetyTimeoutRef.current = null;
      }
    };
  }, [isRecording, language, showLanguageAlert, detectedWrongLanguage, showAndHideLanguageAlert]);
  
  // Handle errors
  useEffect(() => {
    if (error) {
      console.error('Realtime error:', error);
      setLocalError(error);
    } else {
      setLocalError(null);
    }
  }, [error]);
  
  // Initialize the realtime service
  useEffect(() => {
    const initializeService = async () => {
      try {
        // Make sure language and level are defined before initializing
        if (!language || !level) {
          console.error('Missing required parameters: language or level');
          setLocalError('Missing language or level. Please try again.');
          return;
        }
        
        // Log the parameters being passed to the initialize function
        console.log('Initializing with parameters - language:', language, 'level:', level, 'topic:', topic || 'none');
        if (topic === 'custom' && userPrompt) {
          console.log('Custom topic prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
        }
        
        // Pass the language, level, topic, and userPrompt parameters to the initialize function
        await initialize(language, level, topic, userPrompt);
        console.log('Realtime service initialized successfully');
      } catch (err) {
        console.error('Failed to initialize realtime service:', err);
        setLocalError('Failed to initialize the speech service. Please try again.');
      }
    };
    
    initializeService();
  }, [initialize, language, level, topic, userPrompt]);
  
  // Handle transcript updates and language detection
  useEffect(() => {
    // Extract the latest user message for the transcript
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const latestUserMessage = userMessages[userMessages.length - 1];
      setCurrentTranscript(latestUserMessage.content);
      
      // Simple language detection for Dutch vs non-Dutch
      if (language === 'dutch') {
        // List of common Dutch words and patterns
        const dutchPatterns = [
          /\b(ik|je|het|de|een|en|is|zijn|hebben|mijn|jouw|hoe|wat|waar|waarom|wanneer|wie)\b/i,
          /\b(goed|slecht|mooi|lelijk|groot|klein|nieuw|oud|veel|weinig)\b/i,
          /\b(hallo|dag|goedemorgen|goedemiddag|goedenavond|doei|tot ziens)\b/i
        ];
        
        // List of common English words that would indicate English is being spoken
        const englishPatterns = [
          /\b(i|you|he|she|it|we|they|am|is|are|was|were|have|has|had|my|your|how|what|where|why|when|who)\b/i,
          /\b(good|bad|nice|ugly|big|small|new|old|many|few)\b/i,
          /\b(hello|hi|morning|afternoon|evening|goodbye|bye|see you)\b/i
        ];
        
        const text = latestUserMessage.content.toLowerCase();
        
        // Check if the text contains Dutch patterns
        const containsDutch = dutchPatterns.some(pattern => pattern.test(text));
        
        // Check if the text contains English patterns
        const containsEnglish = englishPatterns.some(pattern => pattern.test(text));
        
        // More precise language detection
        const hasNonDutchCharacters = /[qwxyz]/i.test(text) && text.length > 3; // These characters are rare in Dutch
        const hasDutchSpecificCombinations = /\b(ij|aa|ee|oo|uu|eu|oe|ui)\b/i.test(text);
        
        // If the text contains more English patterns than Dutch patterns, it's likely not Dutch
        if ((containsEnglish && !containsDutch) || 
            (text.length > 5 && !containsDutch && !hasDutchSpecificCombinations) ||
            hasNonDutchCharacters) {
          // Only set to true if we're not already showing the alert
          if (!showLanguageAlert || alertAnimationState === 'hidden') {
            setDetectedWrongLanguage(true);
          }
        } else if (containsDutch && !containsEnglish) {
          // If the user is now speaking Dutch, hide the alert with animation
          if (showLanguageAlert && alertAnimationState !== 'exiting' && alertAnimationState !== 'hidden') {
            // Start exit animation
            setAlertAnimationState('exiting');
            
            // After exit animation completes, hide the alert
            setTimeout(() => {
              setShowLanguageAlert(false);
              setAlertAnimationState('hidden');
              setDetectedWrongLanguage(false);
            }, 300); // Match this with CSS animation duration
          }
        }
      }
    }
  }, [messages, language]);
  
  // Handle recording toggle
  const handleToggleRecording = async (e: React.MouseEvent) => {
    e.preventDefault();
    
    if (isRecording) {
      handleEndConversation();
      return;
    }
    
    // If starting a brand new conversation, reset the paused state
    setIsPaused(false);
    setIsAttemptingToRecord(true);
    
    try {
      await toggleConversation();
      setIsAttemptingToRecord(false);
    } catch (err) {
      console.error('Error toggling conversation:', err);
      setIsAttemptingToRecord(false);
      
      if (err instanceof Error && err.message.includes('Permission denied')) {
        micPermissionDeniedRef.current = true;
        setLocalError('Microphone permission denied. Please allow microphone access and try again.');
      } else {
        setLocalError('Failed to start recording. Please try again.');
      }
    }
  };
  
  // Handle end conversation
  const handleEndConversation = () => {
    // Store the conversation history before pausing
    conversationHistoryRef.current = getFormattedConversationHistory();
    console.log('Storing conversation history before pausing:', conversationHistoryRef.current);
    
    // Set the conversation as paused for pronunciation review
    setIsPaused(true);
    stopConversation();
  };
  
  // Handle continue learning
  const handleContinueLearning = () => {
    // Slight delay to allow the UI to update
    setTimeout(async () => {
      console.log('Continuing conversation from where we left off');
      
      if (isPaused && conversationHistoryRef.current) {
        console.log('Resuming paused conversation with previous context:', conversationHistoryRef.current);
        // Instead of toggling conversation (which would reset everything),
        // we use startConversation with the saved conversation history
        setShowMessages(true);
        await startConversation(conversationHistoryRef.current);
        setIsPaused(false);
      } else {
        // Only if not paused (fully ended), start a new conversation
        toggleConversation();
      }
    }, 300);
  };
  
  // Handle change language
  const handleChangeLanguage = () => {
    // Clear all selections except language which will be reselected
    sessionStorage.removeItem('selectedLevel');
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    // Clear any navigation flags
    sessionStorage.removeItem('fromLevelSelection');
    sessionStorage.removeItem('intentionalNavigation');
    
    console.log('Navigating to language selection from speech client');
    window.location.href = '/language-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('speech')) {
        console.log('Still on speech page, using fallback navigation to language selection');
        window.location.replace('/language-selection');
      }
    }, 1000);
  };
  
  // Handle change topic
  const handleChangeTopic = () => {
    // Keep language but clear topic and level
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    sessionStorage.removeItem('selectedLevel');
    // Set a flag to indicate we're intentionally going to topic selection
    sessionStorage.setItem('fromLevelSelection', 'true');
    // Clear any other navigation flags
    sessionStorage.removeItem('intentionalNavigation');
    
    console.log('Navigating to topic selection from speech client');
    window.location.href = '/topic-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('speech')) {
        console.log('Still on speech page, using fallback navigation to topic selection');
        window.location.replace('/topic-selection');
      }
    }, 1000);
  };
  
  // Handle change level
  const handleChangeLevel = () => {
    // Clear level selection but keep language and topic
    sessionStorage.removeItem('selectedLevel');
    // Clear any navigation flags
    sessionStorage.removeItem('intentionalNavigation');
    
    console.log('Navigating to level selection from speech client');
    window.location.href = '/level-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('speech')) {
        console.log('Still on speech page, using fallback navigation to level selection');
        window.location.replace('/level-selection');
      }
    }, 1000);
  };
  
  return (
    <main className="flex min-h-screen flex-col bg-gradient-to-b from-slate-900 to-slate-800 text-white p-4 overflow-x-hidden">
      <div className="w-full max-w-5xl mx-auto h-full flex flex-col">
        {/* Language alert notification with animation states */}
        {showLanguageAlert && language === 'dutch' && (
          <div 
            className={`fixed top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-amber-600 to-amber-500 text-white px-6 py-3 rounded-lg border border-amber-400/20 z-50 flex items-center space-x-3 max-w-md
              ${alertAnimationState === 'entering' ? 'animate-slide-in-top' : ''}
              ${alertAnimationState === 'exiting' ? 'animate-slide-out-top' : ''}
            `}
            role="alert"
            aria-live="assertive"
            id="language-alert-notification"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 flex-shrink-0 text-amber-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex flex-col">
              <span className="text-sm md:text-base font-medium">Dit is een Nederlandse les.</span>
              <span className="text-xs md:text-sm text-amber-100">Probeer alsjeblieft in het Nederlands te spreken.</span>
            </div>
          </div>
        )}
        
        {/* Header - Redesigned */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold tracking-tight gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            {language.charAt(0).toUpperCase() + language.slice(1)} Conversation
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2 text-improved">
            Level: {level.toUpperCase()} - Click the microphone to start talking
          </p>
          
          {/* Redesigned Navigation Controls */}
          <div className="flex flex-wrap justify-center gap-3 mt-5 mb-6 animate-fade-in" style={{animationDelay: '200ms'}}>
            <button 
              type="button"
              onClick={handleChangeLanguage}
              className="app-button"
            >
              Change Language
            </button>
            <button 
              type="button"
              onClick={handleChangeTopic}
              className="app-button"
            >
              Change Topic
            </button>
            <button 
              type="button"
              onClick={handleChangeLevel}
              className="app-button"
            >
              Change Level
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Main Content Area - Redesigned for better responsiveness and alignment */}
          <div className="w-full max-w-6xl mx-auto relative">
            {/* Microphone Section - Centered when no conversation, animates out when recording starts */}
            <div className={`flex flex-col items-center justify-center transition-all duration-700 ease-in-out ${isRecording || showMessages ? 'opacity-0 scale-90 pointer-events-none absolute top-0 left-1/2 transform -translate-x-1/2' : 'opacity-100 mb-12'}`}>
              {/* Microphone UI with improved animations */}
              <div className="relative flex items-center justify-center transform transition-all duration-500">
                {/* Decorative rings with improved animations */}
                <div className="absolute w-40 h-40 rounded-full mic-btn-ring"></div>
                <div className="absolute w-36 h-36 rounded-full mic-btn-ring" style={{ animationDelay: '0.5s' }}></div>
                <div className="absolute w-32 h-32 rounded-full mic-btn-ring" style={{ animationDelay: '1s' }}></div>
                
                {/* Enhanced overlay for initializing state */}
                {isAttemptingToRecord && !isRecording && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm rounded-full z-20 flex items-center justify-center">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-xs text-white/80 animate-pulse">Initializing...</span>
                    </div>
                  </div>
                )}
                
                {/* Microphone Button with gradient */}
                <Button
                  type="button"
                  onClick={(e) => handleToggleRecording(e)}
                  onTouchStart={(e) => e.preventDefault()}
                  aria-label="Start recording"
                  className={`mic-btn relative z-10 rounded-full w-28 h-28 flex items-center justify-center transition-all duration-500 touch-target ${isAttemptingToRecord && !isRecording ? 'opacity-70' : 'opacity-100'}`}
                  disabled={isAttemptingToRecord && !isRecording}
                >
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 opacity-90"></div>
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-indigo-600 to-purple-700 opacity-0 hover:opacity-90 transition-opacity duration-300"></div>
                  
                  {/* Microphone icon with animation */}
                  <div className="relative z-10 flex items-center justify-center">
                    <div className="relative">
                      {/* Animated rings when recording */}
                      {isRecording && (
                        <>
                          <div className="absolute w-full h-full rounded-full bg-purple-500/5 animate-ping-slow"></div>
                          <div className="absolute w-[110%] h-[110%] rounded-full bg-blue-500/5 animate-ping-slower"></div>
                        </>
                      )}
                      
                      {/* Audio wave animation when recording */}
                      {isRecording ? (
                        <div className="flex items-center justify-center h-10 w-10">
                          <div className="relative h-10 w-10">
                            <div className="audio-wave">
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                            </div>
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="h-3 w-3 rounded-full bg-red-500 animate-pulse"></div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <MicrophoneIcon isRecording={isRecording} size={32} />
                      )}
                    </div>
                  </div>
                </Button>
              </div>
              
              <p className="mt-6 text-lg text-slate-300 animate-fade-in">
                {isAttemptingToRecord ? 'Initializing microphone...' : 'Click to start speaking'}
              </p>
              
              {/* Error message */}
              {localError && (
                <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-200 max-w-md text-center animate-fade-in">
                  <p>{localError}</p>
                </div>
              )}
            </div>
            
            {/* Transcript Sections - Animate in when conversation starts */}
            {showMessages && (
              <div className="w-full transition-all duration-700 ease-in-out opacity-100 translate-y-0">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                  {/* Real-time Transcript Component */}
                  <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 shadow-lg animate-fade-in" style={{animationDelay: '200ms'}}>
                    <h3 className="text-lg font-semibold mb-3 text-blue-400 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                      Real-time Transcript
                    </h3>
                    <PronunciationAssessment
                      transcript={currentTranscript}
                      isRecording={isRecording}
                      onStopRecording={handleEndConversation}
                      onContinueLearning={handleContinueLearning}
                      language={language}
                      level={level}
                    />
                  </div>
                  
                  {/* Conversation Transcript Section */}
                  <div className="relative bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 shadow-lg animate-fade-in" style={{animationDelay: '300ms'}}>
                    <h3 className="text-lg font-semibold mb-3 text-indigo-400 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      Conversation Transcript
                    </h3>
                    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/80 backdrop-blur-sm rounded-xl border border-slate-700/50 p-4 h-[300px] md:h-[400px] overflow-y-auto custom-scrollbar">
                      <div className="space-y-4">
                        {processedMessages.length > 0 ? (
                          // Sort messages by timestamp if available, otherwise use the array order
                          processedMessages
                            .sort((a: any, b: any) => {
                              if (a.timestamp && b.timestamp) {
                                return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
                              }
                              return 0;
                            })
                            .map((message: any, index: number) => {
                              // Parse timestamp for display or use current time as fallback
                              const messageTime = message.timestamp 
                                ? new Date(message.timestamp) 
                                : new Date();
                              
                              // Format the time for display
                              const timeDisplay = messageTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                              
                              // Log message for debugging
                              console.log(`Rendering message ${index}: ${message.role}, content: ${message.content.substring(0, 30)}..., timestamp: ${timeDisplay}`);
                              
                              return (
                                <div 
                                  key={`${message.role}-${index}-${message.itemId || messageTime.getTime()}`}
                                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                                >
                                  {message.role !== 'user' && (
                                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mr-2 shadow-md">
                                      <span className="text-xs font-bold text-white">T</span>
                                    </div>
                                  )}
                                  <div 
                                    className={`max-w-[75%] break-words p-4 rounded-2xl shadow-md ${
                                      message.role === 'user' 
                                        ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white ml-2 rounded-tr-none' 
                                        : 'bg-gradient-to-r from-purple-500 to-purple-600 text-white mr-2 rounded-tl-none'
                                    }`}
                                    style={{
                                      wordBreak: 'break-word',
                                      overflowWrap: 'break-word',
                                      whiteSpace: 'pre-wrap'
                                    }}
                                  >
                                    <div className="flex items-center justify-between mb-1 text-white/90">
                                      <span className="text-xs font-semibold">
                                        {message.role === 'user' ? 'You' : 'Tutor'}
                                      </span>
                                      <span className="text-xs opacity-75 ml-2">
                                        {timeDisplay}
                                      </span>
                                    </div>
                                    <p className="text-sm leading-relaxed text-white/95 mt-1">{message.content}</p>
                                  </div>
                                  {message.role === 'user' && (
                                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center ml-2 shadow-md">
                                      <span className="text-xs font-bold text-white">U</span>
                                    </div>
                                  )}
                                </div>
                              );
                            })
                        ) : (
                          <div className="flex justify-center items-center h-full">
                            <div className="text-center p-6 rounded-lg bg-indigo-500/10 border border-indigo-500/20 animate-fadeIn">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto mb-3 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                              </svg>
                              <p className="text-indigo-300 font-medium">Your conversation will appear here</p>
                              <p className="text-indigo-200/70 text-sm mt-2">Click the microphone button to start talking</p>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} />
                      </div>
                    </div>
                    <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-indigo-500 to-purple-500 h-1 w-1/3 rounded-full opacity-70"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

// Microphone icon component with audio wave animation
function MicrophoneIcon({ isRecording, size = 20 }: { isRecording: boolean; size?: number }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="text-white"
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" x2="12" y1="19" y2="22"></line>
    </svg>
  );
}
