'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { RealtimeMessage } from '@/lib/types';
import { useRouter } from 'next/navigation';
import PronunciationAssessment from '@/components/pronunciation-assessment';

interface SpeechClientProps {
  language: string;
  level: string;
  topic?: string;
}

export default function SpeechClient({ language, level, topic }: SpeechClientProps) {
  // Moving the console.log out of the component body to prevent excessive logging
  const initialRenderRef = useRef(true);
  
  const router = useRouter();
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(false);
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const micPermissionDeniedRef = useRef(false);
  
  // Add language alert state
  const [showLanguageAlert, setShowLanguageAlert] = useState(false);
  const languageAlertTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Add state for transcript processing
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  
  // Only log on initial render, not on every re-render
  useEffect(() => {
    if (initialRenderRef.current) {
      console.log('SpeechClient initializing with language:', language, 'level:', level, 'topic:', topic, 'at:', new Date().toISOString());
      initialRenderRef.current = false;
    }
  }, [language, level, topic]);
  
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
  const { isRecording, messages, error, toggleConversation, stopConversation, initialize } = useRealtime();
  
  // Process messages for display
  const processedMessages = messages.map((message, index) => {
    return {
      ...message,
      itemId: `message-${index}`,
      role: message.role === 'assistant' ? 'assistant' : 'user'
    };
  });
  
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

  // Handle language alert - only show when user speaks a different language
  useEffect(() => {
    if (isRecording && language === 'dutch' && detectedWrongLanguage && !showLanguageAlert) {
      setShowLanguageAlert(true);
      
      // Clear any existing timeout
      if (languageAlertTimeoutRef.current) {
        clearTimeout(languageAlertTimeoutRef.current);
      }
      
      // Set timeout to hide the alert after 5 seconds
      languageAlertTimeoutRef.current = setTimeout(() => {
        setShowLanguageAlert(false);
        // Reset the detected language flag after hiding the alert
        setDetectedWrongLanguage(false);
      }, 5000);
    }
    
    return () => {
      if (languageAlertTimeoutRef.current) {
        clearTimeout(languageAlertTimeoutRef.current);
      }
    };
  }, [isRecording, language, showLanguageAlert, detectedWrongLanguage]);
  
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
        
        // Pass the language, level, and topic parameters to the initialize function
        await initialize(language, level, topic);
        console.log('Realtime service initialized successfully');
      } catch (err) {
        console.error('Failed to initialize realtime service:', err);
        setLocalError('Failed to initialize the speech service. Please try again.');
      }
    };
    
    initializeService();
  }, [initialize, language, level, topic]);
  
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
        
        // If the text contains more English patterns than Dutch patterns, it's likely not Dutch
        if ((containsEnglish && !containsDutch) || 
            (text.length > 5 && !containsDutch && !text.includes('ij') && !text.includes('aa') && !text.includes('ee') && !text.includes('oo') && !text.includes('uu'))) {
          setDetectedWrongLanguage(true);
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
    stopConversation();
  };
  
  // Handle continue learning
  const handleContinueLearning = () => {
    // Slight delay to allow the UI to update
    setTimeout(() => {
      console.log('Continuing conversation from where we left off');
      toggleConversation();
    }, 300);
  };
  
  // Handle change language
  const handleChangeLanguage = () => {
    router.push('/topic-selection');
  };
  
  // Handle change level
  const handleChangeLevel = () => {
    router.push(`/level-selection?language=${language}`);
  };
  
  return (
    <main className="flex min-h-screen flex-col bg-gradient-to-b from-slate-900 to-slate-800 text-white p-4 overflow-x-hidden">
      <div className="w-full max-w-5xl mx-auto h-full flex flex-col">
        {/* Language alert notification */}
        {showLanguageAlert && language === 'dutch' && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-amber-600 text-white px-6 py-3 rounded-md shadow-lg z-50 animate-fade-in flex items-center space-x-2 max-w-md">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Dit is een Nederlandse les. Probeer alsjeblieft in het Nederlands te spreken.</span>
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
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white rounded-md shadow-lg transition-all duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50"
            >
              Change Language
            </button>
            <button 
              type="button"
              onClick={handleChangeLevel}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white rounded-md shadow-lg transition-all duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50"
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
                          [...processedMessages]
                            .sort((a, b) => {
                              if (a.timestamp && b.timestamp) {
                                return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
                              }
                              return 0;
                            })
                            .map((message, index) => {
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
