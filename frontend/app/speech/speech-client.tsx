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

  // Show messages panel when we have messages
  useEffect(() => {
    if (messages.length > 0) {
      setShowMessages(true);
    }
  }, [messages]);

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
          <div className={`w-full flex ${showMessages ? 'flex-row lg:flex-row md:flex-col sm:flex-col' : 'flex-col items-center'} gap-8`}>
            {/* Microphone Section */}
            <div className={`${showMessages ? 'w-1/2 lg:w-1/2 md:w-full sm:w-full' : 'w-full'} flex flex-col items-center justify-center`}>
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
            
            {/* Messages Section - Only shown when there are messages */}
            {showMessages && (
              <div className="w-1/2 lg:w-1/2 md:w-full sm:w-full flex flex-col">
                <div className="bg-white/5 dark:bg-slate-900/50 backdrop-blur-sm rounded-xl border border-white/10 p-4 h-[400px] overflow-y-auto">
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div 
                        key={index}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div 
                          className={`max-w-[80%] p-3 rounded-lg ${
                            message.role === 'user' 
                              ? 'bg-indigo-500/20 text-indigo-50 dark:bg-indigo-600/30 dark:text-indigo-100 rounded-tr-none' 
                              : 'bg-purple-500/20 text-purple-50 dark:bg-purple-600/30 dark:text-purple-100 rounded-tl-none'
                          }`}
                        >
                          <p className="text-sm">{message.content}</p>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
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
