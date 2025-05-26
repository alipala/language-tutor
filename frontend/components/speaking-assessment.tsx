'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, RotateCw, Volume2, ChevronRight, AlertCircle, ThumbsUp, Check, Target, ArrowUpRight, Footprints } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { assessSpeaking, fetchSpeakingPrompts, saveSpeakingAssessment, SpeakingAssessmentResult, SpeakingPrompt } from '@/lib/speaking-assessment-api';
import { isAuthenticated } from '@/lib/auth-utils';
import { getAssessmentDuration, formatTime, getMaxAssessmentDetails, getGuestLimitationsDescription } from '@/lib/guest-utils';
import { useNotification } from '@/components/ui/notification';
import LearningPlanModal from './learning-plan-modal';

interface SpeakingAssessmentProps {
  language: string;
  onComplete?: (result: SpeakingAssessmentResult) => void;
  onSelectLevel?: (level: string) => void;
}

export default function SpeakingAssessment({ 
  language, 
  onComplete, 
  onSelectLevel 
}: SpeakingAssessmentProps) {
  // Access notification context
  const { showNotification } = useNotification();
  
  // State for recording and assessment
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing' | 'complete'>('idle');
  const [showLearningPlanModal, setShowLearningPlanModal] = useState(false);
  const [timer, setTimer] = useState(60);
  const [initialDuration, setInitialDuration] = useState(60); // Track initial duration for progress calculation
  const [isTimerActive, setIsTimerActive] = useState(false);
  // No longer tracking guest time expiration
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [transcription, setTranscription] = useState('');
  const [assessment, setAssessment] = useState<SpeakingAssessmentResult | null>(null);
  const [error, setError] = useState('');
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const promptRef = useRef('');

  // Initialize the component
  useEffect(() => {
    // Clear any error message
    setError('');
  }, [language]);
  
  // No longer checking for guest time expiration

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isTimerActive && timer > 0) {
      interval = setInterval(() => {
        setTimer((prevTimer) => {
          const newTimer = prevTimer - 1;
          
          // Show notification when 30 seconds have passed (30 seconds remaining) for 60s assessment
          // Show notification when 10 seconds have passed (5 seconds remaining) for 15s assessment
          if (initialDuration === 60 && newTimer === initialDuration / 2) {
            // Create and show a toast notification
            const notification = document.createElement('div');
            notification.className = 'fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg z-50';
            notification.style.animation = 'fadeIn 0.5s';
            notification.innerHTML = `
              <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p class="font-medium">Recording sufficient for analysis</p>
                  <p class="text-sm opacity-90">You can stop now or continue for more accurate results</p>
                </div>
              </div>
            `;
            document.body.appendChild(notification);
            
            // Add fade-out animation
            const style = document.createElement('style');
            style.innerHTML = `
              @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
              }
              @keyframes fadeOut {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(10px); }
              }
            `;
            document.head.appendChild(style);
            
            // Remove the notification after 5 seconds
            setTimeout(() => {
              notification.style.animation = 'fadeOut 0.5s';
              setTimeout(() => {
                if (document.body.contains(notification)) {
                  document.body.removeChild(notification);
                }
                if (document.head.contains(style)) {
                  document.head.removeChild(style);
                }
              }, 500);
            }, 5000);
          } else if (initialDuration === 15 && newTimer === 5) {
            // Create and show a toast notification
            const notification = document.createElement('div');
            notification.className = 'fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg z-50';
            notification.style.animation = 'fadeIn 0.5s';
            notification.innerHTML = `
              <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p class="font-medium">Recording sufficient for analysis</p>
                  <p class="text-sm opacity-90">You can stop now or continue for more accurate results</p>
                </div>
              </div>
            `;
            document.body.appendChild(notification);
            
            // Add fade-out animation
            const style = document.createElement('style');
            style.innerHTML = `
              @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
              }
              @keyframes fadeOut {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(10px); }
              }
            `;
            document.head.appendChild(style);
            
            // Remove the notification after 5 seconds
            setTimeout(() => {
              notification.style.animation = 'fadeOut 0.5s';
              setTimeout(() => {
                if (document.body.contains(notification)) {
                  document.body.removeChild(notification);
                }
                if (document.head.contains(style)) {
                  document.head.removeChild(style);
                }
              }, 500);
            }, 5000);
          }
          
          return newTimer;
        });
      }, 1000);
    } else if (isTimerActive && timer === 0) {
      setIsTimerActive(false);
      stopRecording();
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isTimerActive, timer, initialDuration]);

  // Clean up audio URL when component unmounts
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startRecording = async () => {
    // Check user status and set appropriate limitations
    const isUserAuthenticated = isAuthenticated();
    const assessmentDuration = getAssessmentDuration(isUserAuthenticated); // Get duration from utility function
    
    // No longer blocking guest users from taking assessments
    
    try {
      // Reset state
      setAudioBlob(null);
      setAudioUrl(null);
      setTranscription('');
      setAssessment(null);
      setError('');
      
      // Start timer with appropriate duration
      setTimer(assessmentDuration);
      setInitialDuration(assessmentDuration); // Update initial duration
      setIsTimerActive(true);
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Set up event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        setAudioBlob(audioBlob);
        setAudioUrl(audioUrl);
        
        // Process recording
        processRecording(audioBlob);
      };
      
      // Start recording
      mediaRecorder.start(100);
      setStatus('recording');
    } catch (err: any) {
      console.error('Error starting recording:', err);
      setError(`Error accessing microphone: ${err.message || 'Please check your microphone permissions.'}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsTimerActive(false);
      
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const processRecording = async (blob: Blob) => {
    try {
      setStatus('processing');
      
      // Get assessment from API
      const result = await assessSpeaking(
        blob, 
        language, 
        initialDuration - timer,
        promptRef.current
      );
      
      // Set assessment result
      setAssessment(result);
      setStatus('complete');
      
      // Call onComplete callback if provided
      if (onComplete) {
        onComplete(result);
      }
      
      // Save assessment data to user profile if authenticated
      if (isAuthenticated()) {
        try {
          const saved = await saveSpeakingAssessment(result);
          if (saved) {
            console.log('Assessment data saved to user profile');
          } else {
            console.warn('Failed to save assessment data to user profile');
          }
        } catch (saveErr) {
          console.error('Error saving assessment data:', saveErr);
          // Don't show this error to the user as it's not critical
        }
      }
    } catch (err: any) {
      console.error('Error processing recording:', err);
      setError(`Error processing recording: ${err.message || 'Unknown error'}`);
      setStatus('idle');
    }
  };

  // No longer need prompt selection handlers

  const handlePlayAudio = () => {
    if (audioPlayerRef.current) {
      if (isAudioPlaying) {
        audioPlayerRef.current.pause();
      } else {
        audioPlayerRef.current.play();
      }
      setIsAudioPlaying(!isAudioPlaying);
    }
  };

  const handleTryAgain = () => {
    setStatus('idle');
    setTimer(60);
    setInitialDuration(60); // Reset initial duration
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAssessment(null);
    setTranscription('');
    setError('');
  };

  const handleSelectLevel = () => {
    // Store the assessment data in session storage for use in the speech client
    if (assessment) {
      try {
        sessionStorage.setItem('speakingAssessmentData', JSON.stringify(assessment));
        console.log('Stored speaking assessment data in session storage');
      } catch (e) {
        console.error('Error storing speaking assessment data:', e);
      }
    }
    
    setShowLearningPlanModal(true);
  };

  const handleLearningPlanModalClose = () => {
    setShowLearningPlanModal(false);
    console.log('Learning plan modal closed without creating a plan');
  };

  const handlePlanCreated = (planId: string) => {
    console.log('Learning plan created with ID:', planId);
    sessionStorage.setItem('pendingLearningPlanId', planId);
    
    // If onSelectLevel callback is provided, use it to trigger redirection
    if (onSelectLevel) {
      console.log('Triggering onSelectLevel callback with recommended level:', assessment?.recommended_level);
      onSelectLevel(assessment?.recommended_level || 'A1');
    } else {
      console.warn('No onSelectLevel callback provided, redirection may not work as expected');
    }
  };

  // Format time from seconds to MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Helper function to get color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Helper function to get progress color based on score
  const getProgressColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Check if user is authenticated
  const userIsAuthenticated = isAuthenticated();

  return (
    <div className="bg-white text-[#333333] rounded-lg p-8 w-full mx-auto space-y-8 border border-[#4ECFBF]/30 shadow-md">
      {/* Hidden audio player */}
      {audioUrl && (
        <audio 
          ref={audioPlayerRef} 
          src={audioUrl} 
          onEnded={() => setIsAudioPlaying(false)}
          className="hidden" 
        />
      )}
      
      {/* Guest User Warning */}
      {!isAuthenticated() && (
        <div className="bg-[#FFD63A]/20 border-l-4 border-[#FFD63A] p-4 mb-4 rounded-r-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-[#FFD63A]" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-[#333333]">Guest Mode</h3>
              <div className="mt-1 text-sm text-[#555555]">
                <p>{getGuestLimitationsDescription()}</p>
                <p className="mt-1">Your assessment results will not be saved to your profile unless you sign in.</p>
              </div>
              <div className="mt-3">
                <a 
                  href="/auth/login" 
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md bg-[#F75A5A] hover:bg-[#E55252] text-white shadow-sm"
                >
                  Sign In
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="text-center bg-[#4ECFBF] p-6 rounded-lg shadow-lg mb-6">
        <h2 className="text-3xl font-bold text-white mb-3">Speaking Assessment</h2>
        <p className="text-white text-lg">
          Speak for 30-60 seconds to assess your {language} proficiency level
        </p>
      </div>

      {/* Speaking Instructions (only in idle state) */}
      {status === 'idle' && (
        <div className="bg-[#F8F9FA] border border-[#FFD63A] rounded-lg p-6 mb-6 shadow-md">
          <h3 className="text-lg font-semibold text-[#333333] mb-3 border-b-2 border-[#FFD63A] pb-2">How to Get the Best Assessment</h3>
          
          <div className="space-y-4 text-[#333333]">
            <div className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
              <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 shadow-sm">
                <span className="block w-5 h-5 text-[#333333] text-center font-bold">1</span>
              </div>
              <p>Find a <strong>quiet environment</strong> with minimal background noise for clear audio.</p>
            </div>
            
            <div className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
              <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 shadow-sm">
                <span className="block w-5 h-5 text-[#333333] text-center font-bold">2</span>
              </div>
              <p>Speak <strong>naturally</strong> about any topic you're comfortable with - your hobbies, work, travels, or interests.</p>
            </div>
            
            <div className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
              <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 shadow-sm">
                <span className="block w-5 h-5 text-[#333333] text-center font-bold">3</span>
              </div>
              <p>Try to speak for the <strong>full 30-60 seconds</strong> to provide enough speech for accurate assessment.</p>
            </div>
            
            <div className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
              <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 shadow-sm">
                <span className="block w-5 h-5 text-[#333333] text-center font-bold">4</span>
              </div>
              <p>Use <strong>varied vocabulary</strong> and sentence structures to demonstrate your language skills.</p>
            </div>
            
            <div className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
              <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 shadow-sm">
                <span className="block w-5 h-5 text-[#333333] text-center font-bold">5</span>
              </div>
              <p><strong>Relax and be yourself</strong> - this helps us provide the most accurate assessment of your current level.</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Recording Controls */}
      {status === 'idle' && (
        <div className="flex flex-col items-center justify-center space-y-6 p-6 bg-white rounded-lg shadow-md border border-gray-100">
          <h2 className="text-xl font-semibold text-[#333333]">
            Speak for a quick assessment
          </h2>
          <p className="text-center text-[#555555] max-w-md">
            Press the button and speak in {language} for {formatTime(getAssessmentDuration(isAuthenticated()))} to get an evaluation of your speaking skills.
          </p>
          
          <Button
            onClick={startRecording}
            className="w-32 h-32 rounded-full flex items-center justify-center bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white shadow-lg transition-all duration-300"
          >
            <Mic className="h-10 w-10" />
          </Button>
          
          <p className="text-sm text-[#777777]">
            Speak for up to {formatTime(getAssessmentDuration(isAuthenticated()))}
          </p>
        </div>
      )}
      
      {/* Recording State */}
      {status === 'recording' && (
        <div className="space-y-6 bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
          <div className="flex items-center justify-center space-x-6">
            <div className="w-20 h-20 flex items-center justify-center bg-[#F75A5A] rounded-full animate-pulse shadow-lg">
              <Mic className="h-10 w-10 text-white" />
            </div>
            <div className="text-3xl font-bold text-[#333333] bg-white px-4 py-2 rounded-lg shadow-md border border-[#F75A5A]/30">{formatTime(timer)}</div>
          </div>
          
          <Progress 
            value={(initialDuration - timer) / initialDuration * 100} 
            className="h-3 bg-white" 
            indicatorClassName="bg-[#F75A5A]" 
          />
          
          <div className="flex justify-center mt-4">
            <Button 
              onClick={stopRecording}
              className="bg-white hover:bg-gray-100 text-[#F75A5A] font-medium px-6 py-3 rounded-lg flex items-center space-x-2 shadow-md transition-all duration-300 border border-[#F75A5A]/30"
            >
              <Square className="h-5 w-5" />
              <span>Stop Recording</span>
            </Button>
          </div>
        </div>
      )}
      
      {/* Processing State */}
      {status === 'processing' && (
        <div className="flex flex-col items-center justify-center py-12 space-y-6 bg-[#FFF2C7] rounded-lg border border-[#FFD63A] p-8 shadow-md">
          <div className="w-20 h-20 border-4 border-[#FFD63A] border-t-transparent rounded-full animate-spin shadow-lg"></div>
          <p className="text-[#333333] text-xl font-medium bg-white px-6 py-2 rounded-lg shadow-md border border-[#FFD63A]/30">Analyzing your speaking skills...</p>
          <p className="text-[#555555] text-center max-w-md bg-white p-4 rounded-lg border border-[#FFD63A]/30">Our AI is carefully evaluating your pronunciation, fluency, vocabulary, and grammar to provide an accurate assessment.</p>
        </div>
      )}
      
      {/* Assessment Results */}
      {status === 'complete' && assessment && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* Left Column: General Information */}
          <div className="space-y-6">
            {/* Playback Controls */}
            {audioUrl && (
              <div className="flex items-center justify-center space-x-4 bg-[#F0FDFB] p-3 rounded-lg border border-[#4ECFBF] shadow-md">
                <Button 
                  onClick={handlePlayAudio}
                  className="bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white rounded-full w-12 h-12 flex items-center justify-center shadow-md transition-all duration-300"
                >
                  {isAudioPlaying ? <Square className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                </Button>
                <div className="text-[#333333] text-lg">Listen to your recording</div>
              </div>
            )}
            
            {/* Recommended Level */}
            <div className="bg-[#F0FDFB] p-6 rounded-lg text-center border border-[#4ECFBF] shadow-md">
              <h3 className="text-xl text-[#333333] mb-3 font-medium">Recommended Level</h3>
              <div className="text-5xl font-bold text-[#333333] mb-3">{assessment.recommended_level}</div>
              <div className="inline-block bg-[#4ECFBF] px-4 py-2 rounded-full text-white text-sm font-medium shadow-md">
                Confidence: {assessment.confidence.toFixed(1)}%
              </div>
            </div>
            
            {/* Overall Score */}
            <div className="bg-[#FFFBEB] p-6 rounded-lg border border-[#FFD63A] shadow-md">
              <h3 className="text-xl text-[#333333] mb-3 font-medium">Overall Score</h3>
              <div className="flex items-center space-x-4">
                <div className="text-4xl font-bold text-[#333333] bg-[#FFD63A] rounded-lg px-4 py-2 shadow-md">
                  {assessment.overall_score.toFixed(1)}
                </div>
                <Progress 
                  value={assessment.overall_score} 
                  className="h-4 bg-white flex-1 rounded-full border border-[#FFD63A]/30"
                  indicatorClassName={`${assessment.overall_score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.overall_score < 50 ? 'bg-[#FFD63A]' : 
                    assessment.overall_score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                />
              </div>
            </div>
            
            {/* Transcription */}
            <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
              <h3 className="text-xl text-[#333333] mb-3 font-medium">Your Speech</h3>
              <p className="text-[#333333] bg-white p-4 rounded-lg border border-[#F75A5A]/30 shadow-inner">
                {assessment.recognized_text || "No speech detected"}
              </p>
            </div>
          </div>
          
          {/* Right Column: Detailed Assessment */}
          <div className="space-y-6">
            {/* Skill Scores */}
            <div className="bg-[#F8F9FA] p-6 rounded-lg border border-gray-200 shadow-md overflow-auto">
              <h3 className="text-lg text-[#333333] mb-3 font-medium">Skill Breakdown</h3>
              
              <div className="space-y-4 max-h-[600px] overflow-auto pr-2">
              {/* Pronunciation */}
              <div className="bg-white p-3 rounded-lg border border-[#4ECFBF] shadow-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-[#333333] font-medium">Pronunciation</span>
                  <span className={`text-white px-3 py-1 rounded-md font-medium shadow-sm ${assessment.pronunciation.score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.pronunciation.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                    assessment.pronunciation.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}>
                    {assessment.pronunciation.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.pronunciation.score} 
                  className="h-3 bg-gray-100 rounded-full"
                  indicatorClassName={`${assessment.pronunciation.score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.pronunciation.score < 50 ? 'bg-[#FFD63A]' : 
                    assessment.pronunciation.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                />
                <p className="text-[#555555] mt-1 text-sm bg-[#F0FDFB] p-2 rounded-md border border-[#4ECFBF]/20">{assessment.pronunciation.feedback}</p>
              </div>
              
              {/* Vocabulary */}
              <div className="bg-white p-3 rounded-lg border border-[#FFD63A] shadow-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-[#333333] font-medium">Vocabulary</span>
                  <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.vocabulary.score < 25 ? 'bg-[#F75A5A] text-white' : 
                    assessment.vocabulary.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                    assessment.vocabulary.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                    {assessment.vocabulary.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.vocabulary.score} 
                  className="h-3 bg-gray-100 rounded-full"
                  indicatorClassName={`${assessment.vocabulary.score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.vocabulary.score < 50 ? 'bg-[#FFD63A]' : 
                    assessment.vocabulary.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                />
                <p className="text-[#555555] mt-1 text-sm bg-[#FFFBEB] p-2 rounded-md border border-[#FFD63A]/20">{assessment.vocabulary.feedback}</p>
              </div>
              
              {/* Grammar */}
              <div className="bg-white p-3 rounded-lg border border-[#F75A5A] shadow-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-[#333333] font-medium">Grammar</span>
                  <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.grammar.score < 25 ? 'bg-[#F75A5A] text-white' : 
                    assessment.grammar.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                    assessment.grammar.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                    {assessment.grammar.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.grammar.score} 
                  className="h-3 bg-gray-100 rounded-full"
                  indicatorClassName={`${assessment.grammar.score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.grammar.score < 50 ? 'bg-[#FFD63A]' : 
                    assessment.grammar.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                />
                <p className="text-[#555555] mt-1 text-sm bg-[#FFF8F8] p-2 rounded-md border border-[#F75A5A]/20">{assessment.grammar.feedback}</p>
              </div>
              
              {/* Fluency */}
              <div className="bg-white p-3 rounded-lg border border-[#4ECFBF] shadow-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-[#333333] font-medium">Fluency</span>
                  <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.fluency.score < 25 ? 'bg-[#F75A5A] text-white' : 
                    assessment.fluency.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                    assessment.fluency.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                    {assessment.fluency.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.fluency.score} 
                  className="h-3 bg-gray-100 rounded-full"
                  indicatorClassName={`${assessment.fluency.score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.fluency.score < 50 ? 'bg-[#FFD63A]' : 
                    assessment.fluency.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                />
                <p className="text-[#555555] mt-1 text-sm bg-[#F0FDFB] p-2 rounded-md border border-[#4ECFBF]/20">{assessment.fluency.feedback}</p>
              </div>
              
              {/* Coherence */}
              <div className="bg-white p-3 rounded-lg border border-[#FFD63A] shadow-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-[#333333] font-medium">Coherence</span>
                  <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.coherence.score < 25 ? 'bg-[#F75A5A] text-white' : 
                    assessment.coherence.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                    assessment.coherence.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                    {assessment.coherence.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.coherence.score} 
                  className="h-3 bg-gray-100 rounded-full"
                  indicatorClassName={`${assessment.coherence.score < 25 ? 'bg-[#F75A5A]' : 
                    assessment.coherence.score < 50 ? 'bg-[#FFD63A]' : 
                    assessment.coherence.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                />
                <p className="text-[#555555] mt-1 text-sm bg-[#FFFBEB] p-2 rounded-md border border-[#FFD63A]/20">{assessment.coherence.feedback}</p>
              </div>
            </div>
          </div>
          
            {/* Feedback and Next Steps */}
            {/* Strengths */}
            <div className="bg-[#F0FDFB] p-5 rounded-lg border border-[#4ECFBF] shadow-md">
              <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                <ThumbsUp className="h-5 w-5 mr-2 text-[#4ECFBF]" /> Strengths
              </h3>
              <ul className="space-y-3">
                {assessment.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#4ECFBF]/30 shadow-sm">
                    <div className="bg-[#4ECFBF] rounded-full p-1 mt-0.5 flex-shrink-0">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <p className="text-[#333333]">{strength}</p>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Areas for Improvement */}
            <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
              <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                <Target className="h-5 w-5 mr-2 text-[#F75A5A]" /> Areas for Improvement
              </h3>
              <ul className="space-y-3">
                {assessment.areas_for_improvement.map((area, index) => (
                  <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#F75A5A]/30 shadow-sm">
                    <div className="bg-[#F75A5A] rounded-full p-1 mt-0.5 flex-shrink-0">
                      <ArrowUpRight className="h-4 w-4 text-white" />
                    </div>
                    <p className="text-[#333333]">{area}</p>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Next Steps */}
            <div className="bg-[#FFFBEB] p-6 rounded-lg border border-[#FFD63A] shadow-md">
              <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                <Footprints className="h-5 w-5 mr-2 text-[#FFD63A]" /> Next Steps
              </h3>
              <ul className="space-y-3">
                {assessment.next_steps.map((step, index) => (
                  <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
                    <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 flex-shrink-0">
                      <span className="block w-4 h-4 text-[#333333] text-center font-bold text-xs">{index + 1}</span>
                    </div>
                    <p className="text-[#333333]">{step}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          {/* Action Buttons - Centered at the bottom */}
          <div className="col-span-1 lg:col-span-2">
            <div className="flex flex-col sm:flex-row justify-center gap-4 mt-6">
              <Button 
                onClick={handleTryAgain}
                className="bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white font-medium px-6 py-3 rounded-lg flex items-center justify-center space-x-2 shadow-md transition-all duration-300 flex-1"
              >
                <RotateCw className="h-5 w-5" />
                <span>New Assessment</span>
              </Button>
              
              <Button 
                onClick={handleSelectLevel}
                className="bg-[#FFD63A] hover:bg-[#ECC235] text-[#333333] font-medium px-6 py-3 rounded-lg flex items-center justify-center space-x-2 shadow-md transition-all duration-300 flex-1"
              >
                <Volume2 className="h-5 w-5" />
                <span>Save & Practice</span>
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* Error Message */}
      {error && (
        <div className="bg-[#FFF8F8] border border-[#F75A5A] rounded-lg p-6 mb-6 shadow-md">
          <div className="flex items-center space-x-3 text-[#F75A5A]">
            <AlertCircle className="h-6 w-6" />
            <h3 className="text-lg font-semibold">Error</h3>
          </div>
          <p className="mt-2 text-[#333333]">{error}</p>
          <Button 
            onClick={() => setError('')}
            className="mt-4 bg-white hover:bg-gray-100 text-[#F75A5A] px-4 py-2 rounded-md text-sm font-medium shadow-md transition-all duration-300 border border-[#F75A5A]/30"
          >
            Dismiss
          </Button>
        </div>
      )}
      
      {/* Manual Level Selection button removed */}
      
      {/* Learning Plan Modal */}
      {assessment && (
        <LearningPlanModal 
          isOpen={showLearningPlanModal}
          onClose={handleLearningPlanModalClose}
          proficiencyLevel={assessment.recommended_level}
          language={language}
          onPlanCreated={handlePlanCreated}
          assessmentData={assessment}
        />
      )}
    </div>
  );
}
