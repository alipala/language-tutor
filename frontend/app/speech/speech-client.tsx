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
  const router = useRouter();
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(false);
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const micPermissionDeniedRef = useRef(false);
  
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

  const handleToggleRecording = async () => {
    // Clear any previous errors
    setLocalError(null);
    clearError();
    
    // If already recording, just stop
    if (isRecording) {
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
      // Initialize with language and level
      console.log('Initializing with language:', language, 'and level:', level);
      await initialize(language, level);
      
      const success = await toggleConversation();
      
      // If the toggle was not successful and no error was set in the hook,
      // we need to show a fallback error
      if (!success && !realtimeError) {
        setLocalError('Failed to start recording. Please try again.');
        setIsAttemptingToRecord(false);
      }
    } catch (err) {
      setLocalError('An error occurred while starting the conversation');
      console.error(err);
      setIsAttemptingToRecord(false);
    }
  };

  const handleEndConversation = () => {
    stopConversation();
    setIsAttemptingToRecord(false);
    // Don't hide messages when ending conversation
  };

  const handleChangeLanguage = () => {
    stopConversation();
    router.push('/language-selection');
  };

  const handleChangeLevel = () => {
    stopConversation();
    router.push('/level-selection');
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            {language.charAt(0).toUpperCase() + language.slice(1)} Conversation
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2 text-improved">
            Level: {level.toUpperCase()} - Click the microphone to start talking
          </p>
          <div className="flex justify-center mt-2 space-x-4">
            <button 
              onClick={handleChangeLanguage}
              className="text-sm text-indigo-500 hover:text-indigo-400 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Change Language
            </button>
            <button 
              onClick={handleChangeLevel}
              className="text-sm text-indigo-500 hover:text-indigo-400 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Change Level
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
                    onClick={handleToggleRecording}
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
                    onClick={handleEndConversation}
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
