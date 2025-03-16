'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { RealtimeMessage } from '@/lib/types';
import { useRouter } from 'next/navigation';

interface SpeechClientProps {
  language: string;
  level: string;
}

export default function SpeechClient({ language, level }: SpeechClientProps) {
  console.log('SpeechClient initializing with language:', language, 'level:', level, 'at:', new Date().toISOString());
  
  const router = useRouter();
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(false);
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const micPermissionDeniedRef = useRef(false);
  
  // Add a useEffect to track component mounting and unmounting
  useEffect(() => {
    console.log('SpeechClient component mounted at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Store a flag to detect if the component unmounts unexpectedly
    const mountTimestamp = Date.now();
    sessionStorage.setItem('speechClientMountTime', mountTimestamp.toString());
    
    return () => {
      console.log('SpeechClient component unmounting at:', new Date().toISOString());
      console.log('Component was mounted for:', Date.now() - mountTimestamp, 'ms');
      
      // Store the unmount reason to help with debugging
      sessionStorage.setItem('speechClientUnmountReason', 'normal_unmount');
    };
  }, []);
  
  // Use the Realtime API hook
  const {
    isRecording,
    messages,
    error: realtimeError,
    toggleConversation,
    stopConversation,
    clearError,
    initialize
  } = useRealtime();

  // Clear error when recording state changes
  useEffect(() => {
    if (isRecording) {
      setLocalError(null);
      setIsAttemptingToRecord(false);
      micPermissionDeniedRef.current = false;
    }
  }, [isRecording]);

  // Always show messages panel
  useEffect(() => {
    setShowMessages(true);
  }, []);

  // Handle realtime errors
  useEffect(() => {
    if (realtimeError) {
      // If the error is about microphone access, mark it
      if (realtimeError.includes('microphone')) {
        micPermissionDeniedRef.current = true;
      }
      
      // Stop attempting to record if there's an error
      if (isAttemptingToRecord) {
        setIsAttemptingToRecord(false);
      }
    }
  }, [realtimeError, isAttemptingToRecord]);

  // Scroll to bottom of messages
  useEffect(() => {
    if (messagesEndRef.current && showMessages) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, showMessages]);

  const handleToggleRecording = async (e?: React.MouseEvent | React.TouchEvent) => {
    // Prevent default browser behavior that might cause page refresh
    if (e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('Toggle recording event prevented at:', new Date().toISOString());
    }
    
    console.log('handleToggleRecording called - isRecording:', isRecording, 'isAttemptingToRecord:', isAttemptingToRecord);
    
    // Set a flag in session storage to indicate we're in a conversation
    // This will be used by the beforeunload handler to prevent accidental refreshes
    if (!isRecording) {
      sessionStorage.setItem('isInConversation', 'true');
    } else {
      sessionStorage.removeItem('isInConversation');
    }
    
    // Clear any previous errors
    setLocalError(null);
    clearError();
    
    // If already recording, just stop
    if (isRecording) {
      console.log('Already recording, stopping conversation...');
      stopConversation();
      return;
    }
    
    // Check if microphone permission was previously denied
    if (micPermissionDeniedRef.current) {
      setLocalError('Microphone access was denied. Please grant microphone permissions and reload the page.');
      return;
    }
    
    // Otherwise, attempt to start recording
    setIsAttemptingToRecord(true);
    try {
      console.log('Starting microphone initialization sequence...');
      
      // First, ensure we're fully disconnected from any previous session
      stopConversation();
      
      // Add a small delay to ensure cleanup is complete
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Initialize with language and level
      console.log('Initializing with language:', language, 'and level:', level);
      
      // Store the current URL to detect navigation issues
      const currentUrl = window.location.href;
      sessionStorage.setItem('lastMicrophoneInitUrl', currentUrl);
      
      const initSuccess = await initialize(language, level);
      
      // Check if we're still on the same page after initialization
      if (window.location.href !== currentUrl) {
        console.error('Page URL changed during initialization, aborting microphone start');
        return;
      }
      
      if (!initSuccess) {
        console.error('Failed to initialize realtime service');
        setLocalError('Failed to initialize voice service. Please try again.');
        setIsAttemptingToRecord(false);
        sessionStorage.removeItem('isInConversation');
        return;
      }
      
      // Add a small delay after initialization
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Check again if we're still on the same page
      if (window.location.href !== currentUrl) {
        console.error('Page URL changed before starting conversation, aborting');
        return;
      }
      
      console.log('Starting conversation...');
      const success = await toggleConversation();
      
      // If the toggle was not successful and no error was set in the hook,
      // we need to show a fallback error
      if (!success && !realtimeError) {
        setLocalError('Failed to start recording. Please try again.');
        setIsAttemptingToRecord(false);
        sessionStorage.removeItem('isInConversation');
      }
    } catch (err) {
      setLocalError('An error occurred while starting the conversation');
      console.error('Error in handleToggleRecording:', err);
      setIsAttemptingToRecord(false);
      sessionStorage.removeItem('isInConversation');
    }
  };

  const handleEndConversation = (e?: React.MouseEvent | React.TouchEvent) => {
    // Prevent default browser behavior that might cause page refresh
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    // Remove the conversation flag since we're ending the conversation
    sessionStorage.removeItem('isInConversation');
    
    stopConversation();
    setIsAttemptingToRecord(false);
    // Don't hide messages when ending conversation
  };

  const handleChangeLanguage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    stopConversation();
    // Clear the language selection to force re-selection
    sessionStorage.removeItem('selectedLanguage');
    console.log('Navigating to language selection');
    
    // Use setTimeout to ensure the navigation happens after the current event loop
    setTimeout(() => {
      console.log('Executing navigation to language selection');
      window.location.href = '/language-selection';
      
      // Fallback navigation in case the first attempt fails (for Railway)
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('speech')) {
          console.log('Still on speech page, using fallback navigation to language selection');
          window.location.replace('/language-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 100);
  };

  const handleChangeLevel = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    stopConversation();
    // Keep the language but clear the level
    sessionStorage.removeItem('selectedLevel');
    console.log('Navigating to level selection');
    
    // Use setTimeout to ensure the navigation happens after the current event loop
    setTimeout(() => {
      console.log('Executing navigation to level selection');
      window.location.href = '/level-selection';
      
      // Fallback navigation in case the first attempt fails (for Railway)
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('speech')) {
          console.log('Still on speech page, using fallback navigation to level selection');
          window.location.replace('/level-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 100);
  };
  
  const handleStartOver = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    stopConversation();
    
    // Mark that we're intentionally navigating away
    sessionStorage.setItem('intentionalNavigation', 'true');
    console.log('Starting over - clearing session storage');
    
    // Clear all session storage
    sessionStorage.clear();
    
    // Immediately set the intentional navigation flag again since we just cleared it
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Use setTimeout to ensure the navigation happens after the current event loop
    setTimeout(() => {
      console.log('Executing navigation to home page');
      window.location.href = '/';
      
      // Fallback navigation in case the first attempt fails (for Railway)
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('speech')) {
          console.log('Still on speech page, using fallback navigation to home');
          window.location.replace('/');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 100);
  };

  return (
    <main className="flex min-h-screen flex-col bg-gradient-to-b from-slate-900 to-slate-800 text-white p-4">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            {language.charAt(0).toUpperCase() + language.slice(1)} Conversation
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2 text-improved">
            Level: {level.toUpperCase()} - Click the microphone to start talking
          </p>
          <div className="flex flex-wrap justify-center gap-4 mb-8 animate-fade-in" style={{animationDelay: '200ms'}}>
            <button 
              type="button"
              onClick={handleChangeLanguage}
              className="px-5 py-3 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 rounded-full shadow-lg hover:shadow-blue-500/20 transition-all duration-300 flex items-center space-x-2 transform hover:translate-y-[-2px]" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              <span>Change Language</span>
            </button>
            <button 
              type="button"
              onClick={handleChangeLevel}
              className="px-5 py-3 text-sm font-medium text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-full shadow-lg hover:shadow-indigo-500/20 transition-all duration-300 flex items-center space-x-2 transform hover:translate-y-[-2px]" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Change Level</span>
            </button>
            <button 
              type="button"
              onClick={handleStartOver}
              className="px-5 py-3 text-sm font-medium text-white bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 rounded-full shadow-lg hover:shadow-red-500/20 transition-all duration-300 flex items-center space-x-2 transform hover:translate-y-[-2px]" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Start Over</span>
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Main Content Area - Split into two sections when messages are shown */}
          <div className={`w-full flex ${showMessages ? 'flex-col md:flex-row' : 'flex-col items-center'} gap-6 md:gap-8`}>
            {/* Microphone Section */}
            <div className="w-full md:w-1/2 flex flex-col items-center justify-center">
              {/* Microphone UI - Only shown when not recording */}
              {!isRecording && !isAttemptingToRecord ? (
                <div className="relative flex items-center justify-center transform transition-all duration-500">
                  {/* Decorative rings */}
                  <div className="absolute w-40 h-40 rounded-full mic-btn-ring"></div>
                  <div className="absolute w-36 h-36 rounded-full mic-btn-ring" style={{ animationDelay: '0.5s' }}></div>
                  <div className="absolute w-32 h-32 rounded-full mic-btn-ring" style={{ animationDelay: '1s' }}></div>
                  
                  {/* Microphone Button with gradient */}
                  <Button
                    type="button"
                    onClick={(e) => handleToggleRecording(e)}
                    onTouchStart={(e) => e.preventDefault()}
                    aria-label="Start recording"
                    className="mic-btn relative z-10 rounded-full w-28 h-28 flex items-center justify-center transition-all duration-500 touch-target"
                  >
                    <MicrophoneIcon isRecording={false} size={32} />
                  </Button>
                </div>
              ) : (
                /* Audio Visualization - Shown when recording or attempting to record */
                <div className="my-12 flex flex-col items-center justify-center">
                  <div className="relative w-48 h-48 flex items-center justify-center">
                    {/* Animated rings */}
                    <div className="absolute w-full h-full rounded-full bg-purple-500/5 animate-ping-slow"></div>
                    <div className="absolute w-[110%] h-[110%] rounded-full bg-blue-500/5 animate-ping-slower"></div>
                    
                    {/* Central audio visualization */}
                    <div className="relative w-32 h-32 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                      <div className="absolute inset-0 rounded-full flex items-center justify-center">
                        <div className="flex items-center justify-center w-full h-full">
                          {Array.from({ length: 24 }).map((_, i) => {
                            const angle = (i * 15) * Math.PI / 180;
                            const x = Math.cos(angle) * 50;
                            const y = Math.sin(angle) * 50;
                            return (
                              <div 
                                key={i}
                                className="absolute w-1.5 bg-gradient-to-t from-blue-500 to-purple-600 rounded-full animate-sound-wave"
                                style={{
                                  height: `${Math.max(10, Math.min(40, 15 + Math.sin(i/3) * 25))}px`,
                                  animationDelay: `${i * 0.05}s`,
                                  transform: `translate(${x}px, ${y}px) rotate(${angle + Math.PI/2}rad)`,
                                  transformOrigin: 'bottom',
                                }}
                              ></div>
                            );
                          })}
                        </div>
                      </div>
                      <div className="text-lg font-medium text-white bg-gradient-to-r from-blue-500 to-purple-600 rounded-full w-16 h-16 flex items-center justify-center shadow-lg">
                        <span className="animate-pulse">Live</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Status Text */}
              <div className="mt-6 text-center">
                <p className="text-lg font-medium gradient-text dark:from-indigo-400 dark:to-purple-400">
                  {isRecording ? "I'm listening..." : isAttemptingToRecord ? "Starting..." : "Click to speak"}
                </p>
                {(localError || realtimeError) && (
                  <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-md border border-red-200 dark:border-red-800/30 max-w-xs mx-auto">
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {localError || realtimeError}
                    </p>
                    <button 
                      onClick={() => {
                        setLocalError(null);
                        clearError();
                        setIsAttemptingToRecord(false);
                      }}
                      className="text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 mt-1 underline"
                    >
                      Dismiss
                    </button>
                  </div>
                )}
              </div>
              
              {/* Recording Controls - Only shown when recording */}
              {isRecording && (
                <div className="mt-8">
                  <Button
                    type="button"
                    onClick={(e) => handleEndConversation(e)}
                    onTouchStart={(e) => e.preventDefault()}
                    variant="destructive"
                    className="px-6 py-2 rounded-full"
                  >
                    End Conversation
                  </Button>
                </div>
              )}
            </div>
            
            {/* Conversation Transcript Section - Enhanced Design */}
            {showMessages && (
              <div className="w-full md:w-1/2 flex flex-col">
                <div className="relative">
                  <h3 className="text-lg font-semibold mb-2 text-indigo-600 dark:text-indigo-300 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    Conversation Transcript
                  </h3>
                  <div className="bg-gradient-to-br from-white/10 to-white/5 dark:from-slate-800/50 dark:to-slate-900/80 backdrop-blur-sm rounded-xl border border-white/20 dark:border-indigo-500/20 shadow-lg shadow-indigo-500/5 dark:shadow-purple-500/10 p-4 h-[300px] md:h-[400px] overflow-y-auto scrollbar-thin scrollbar-thumb-indigo-500/20 scrollbar-track-transparent">
                    {/* Debug info removed */}
                    
                    <div className="space-y-4">
                      {messages.length > 0 ? (
                        messages.map((message, index) => (
                          <div 
                            key={index}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                          >
                          {message.role !== 'user' && (
                            <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mr-2 shadow-md">
                              <span className="text-xs font-bold text-white">T</span>
                            </div>
                          )}
                          <div 
                            className={`max-w-[80%] p-3 rounded-lg shadow-sm ${
                              message.role === 'user' 
                                ? 'bg-gradient-to-r from-indigo-500/80 to-indigo-600/80 text-white rounded-tr-none border-r border-t border-indigo-400/30' 
                                : 'bg-gradient-to-r from-purple-500/80 to-purple-600/80 text-white rounded-tl-none border-l border-t border-purple-400/30'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-semibold opacity-90">
                                {message.role === 'user' ? 'You' : 'Tutor'}
                              </span>
                              <span className="text-xs opacity-60">
                                {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}  
                              </span>
                            </div>
                            <p className="text-sm font-medium leading-relaxed">{message.content || '(empty message)'}</p>
                          </div>
                          {message.role === 'user' && (
                            <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center ml-2 shadow-md">
                              <span className="text-xs font-bold text-white">U</span>
                            </div>
                          )}
                          </div>
                        ))
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
