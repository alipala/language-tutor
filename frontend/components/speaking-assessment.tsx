'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, RotateCw, Volume2, ChevronRight, AlertCircle, ThumbsUp, Check, Target, ArrowUpRight, Footprints } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { assessSpeaking, fetchSpeakingPrompts, saveSpeakingAssessment, SpeakingAssessmentResult, SpeakingPrompt } from '@/lib/speaking-assessment-api';
import { isAuthenticated } from '@/lib/auth-utils';
import { getAssessmentDuration, formatTime, getMaxAssessmentDetails, getGuestLimitationsDescription, ASSESSMENT_DURATION_GUEST, ASSESSMENT_DURATION_REGISTERED, CONVERSATION_DURATION_GUEST, CONVERSATION_DURATION_REGISTERED } from '@/lib/guest-utils';
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
    
    // Check if assessment was already completed
    const assessmentCompleted = sessionStorage.getItem('assessmentCompleted');
    if (assessmentCompleted === 'true') {
      // Redirect to home page
      window.location.href = '/';
    }
  }, [language]);
  
  // No longer checking for guest time expiration

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isTimerActive && timer > 0) {
      interval = setInterval(() => {
        setTimer((prevTimer) => {
          const newTimer = prevTimer - 1;
          
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
      
      // Mark assessment as completed in session storage
      sessionStorage.setItem('assessmentCompleted', 'true');
      
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
    // Remove the completed flag to allow a new assessment
    sessionStorage.removeItem('assessmentCompleted');
    
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
    // Keep the assessmentCompleted flag to prevent restarting after refresh
  };

  const handlePlanCreated = (planId: string) => {
    console.log('Learning plan created with ID:', planId);
    sessionStorage.setItem('pendingLearningPlanId', planId);
    
    // Ensure the assessment is marked as completed
    sessionStorage.setItem('assessmentCompleted', 'true');
    
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
      {/* Hidden audio player*/}
      {/* audioUrl && (
        <audio 
          ref={audioPlayerRef} 
          src={audioUrl} 
          onEnded={() => setIsAudioPlaying(false)}
          className="hidden" 
        />
      )}
      
      {/* Guest User Mode Banner*/}
      {!isAuthenticated() && (
        <div className="relative overflow-hidden bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] p-6 mb-6 rounded-xl shadow-lg">
          <div className="absolute top-0 right-0 w-32 h-32 -mt-8 -mr-8 opacity-20">
            <svg viewBox="0 0 100 100" className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
              <circle cx="50" cy="50" r="40" fill="white" />
              <path d="M50 10 A40 40 0 0 1 90 50" stroke="white" strokeWidth="4" fill="none" />
              <path d="M50 90 A40 40 0 0 1 10 50" stroke="white" strokeWidth="4" fill="none" />
            </svg>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center">
                <div className="bg-white/20 p-2 rounded-full mr-3">
                  <Mic className="h-5 w-5 text-white" />
                </div>
                <h3 className="text-lg font-bold text-white">Guest Experience</h3>
              </div>
              
              <div className="mt-3 text-white/90 text-sm max-w-xl leading-relaxed">
                <p>You're using the free guest mode with limited features:</p>
                <ul className="mt-2 space-y-1 list-disc list-inside pl-1">
                  <li><span className="font-semibold">{ASSESSMENT_DURATION_GUEST}-second</span> speaking assessment (vs {ASSESSMENT_DURATION_REGISTERED}s)</li>
                  <li><span className="font-semibold">{CONVERSATION_DURATION_GUEST}-second</span> conversation practice (vs {CONVERSATION_DURATION_REGISTERED}s)</li>
                  <li>Results not saved to your profile</li>
                </ul>
                <div className="mt-4 flex space-x-3">
                  <a 
                    href="/signup" 
                    className="inline-flex items-center px-4 py-2 bg-white text-[#3AA8B1] font-medium rounded-lg shadow-md hover:bg-white/90 transition-all duration-200 group"
                  >
                    Sign Up for Full Access
                    <ChevronRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </a>
                  <a 
                    href="/auth/login" 
                    className="inline-flex items-center px-4 py-2 bg-transparent border border-white text-white font-medium rounded-lg hover:bg-white/10 transition-all duration-200 group"
                  >
                    Sign In
                    <ArrowUpRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                  </a>
                </div>
              </div>
            </div>
            
            <div className="hidden">
              <a 
                href="/auth/login" 
                className="inline-flex items-center px-4 py-2 bg-white text-[#3AA8B1] font-medium rounded-lg shadow-md hover:bg-white/90 transition-all duration-200 group"
              >
                Sign In
                <ArrowUpRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>
            </div>
          </div>
          
          <div className="mt-4 md:hidden">
            <a 
              href="/auth/login" 
              className="inline-flex items-center px-4 py-2 bg-white text-[#3AA8B1] font-medium rounded-lg shadow-md hover:bg-white/90 transition-all duration-200 w-full justify-center"
            >
              Sign In
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </a>
          </div>
        </div>
      )}
      
      {/* Header*/}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#4ECFBF] to-[#3AA8B1] p-8 rounded-xl shadow-lg mb-6 text-center">
        <div className="absolute inset-0 opacity-10">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="white" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>
        
        <div className="relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
            Speaking Assessment
          </h2>
          <p className="text-white/90 text-lg max-w-2xl mx-auto">
            {isAuthenticated() 
              ? `Speak for up to ${formatTime(ASSESSMENT_DURATION_REGISTERED)} to assess your ${language} proficiency level` 
              : `Speak for ${formatTime(ASSESSMENT_DURATION_GUEST)} to assess your ${language} proficiency level`
            }
          </p>
        </div>
      </div>

      {/* Speaking Instructions (only in idle state)*/}
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
      
      {/* Recording Controls*/}
      {status === 'idle' && (
        <div className="flex flex-col items-center justify-center p-8 bg-white rounded-xl shadow-lg border border-gray-100">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-[#333333] mb-3">
              Ready to assess your {language} skills?
            </h2>
            <p className="text-[#555555] max-w-md mx-auto">
              Press the microphone button and speak naturally in {language} for {isAuthenticated() ? 'up to ' : ''}{formatTime(getAssessmentDuration(isAuthenticated()))}.
            </p>
          </div>
          
          <div className="relative mb-6 group">
            <div className="absolute -inset-4 bg-gradient-to-r from-[#4ECFBF]/30 to-[#3AA8B1]/30 rounded-full blur-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <Button
              onClick={startRecording}
              className="relative w-36 h-36 rounded-full flex items-center justify-center bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] text-white shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
            >
              <Mic className="h-12 w-12" />
            </Button>
          </div>
          
          <div className="flex items-center justify-center space-x-2 text-sm text-[#777777] bg-gray-50 px-4 py-2 rounded-full">
            <div className="w-2 h-2 rounded-full bg-[#4ECFBF] animate-pulse"></div>
            <p>Microphone ready • {isAuthenticated() ? 'Up to ' : ''}{formatTime(getAssessmentDuration(isAuthenticated()))}</p>
          </div>
        </div>
      )}
      
      {/* Recording State*/}
      {status === 'recording' && (
        <div className="bg-gradient-to-br from-[#FFF8F8] to-[#FFF0F0] p-8 rounded-xl shadow-lg">
          <div className="flex flex-col md:flex-row items-center justify-between mb-8">
            <div className="flex items-center mb-6 md:mb-0">
              <div className="relative">
                <div className="absolute inset-0 bg-[#F75A5A]/30 rounded-full blur-lg animate-pulse"></div>
                <div className="relative w-24 h-24 flex items-center justify-center bg-[#F75A5A] rounded-full shadow-lg">
                  <Mic className="h-10 w-10 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-md">
                  <div className="w-3 h-3 rounded-full bg-[#F75A5A] animate-pulse"></div>
                </div>
              </div>
              <div className="ml-6">
                <h3 className="text-xl font-bold text-[#333333]">Recording...</h3>
                <p className="text-[#555555]">{isAuthenticated() ? 'Speak naturally' : 'Make every second count!'}</p>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-[#F75A5A]/10 rounded-xl blur-md"></div>
              <div className="relative text-4xl font-bold text-[#F75A5A] bg-white px-6 py-3 rounded-xl shadow-md border border-[#F75A5A]/20">
                {formatTime(timer)}
              </div>
            </div>
          </div>
          
          <div className="mb-6">
            <div className="flex justify-between text-sm text-[#555555] mb-2">
              <span>0:00</span>
              <span>{formatTime(initialDuration)}</span>
            </div>
            <Progress 
              value={(initialDuration - timer) / initialDuration * 100} 
              className="h-4 bg-white rounded-full" 
              indicatorClassName="bg-gradient-to-r from-[#F75A5A] to-[#FF8A8A] rounded-full" 
            />
          </div>
          
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
      
      {/* Processing State*/}
      {status === 'processing' && (
        <div className="relative overflow-hidden bg-gradient-to-br from-[#FFF8E1] to-[#FFEDB3] p-8 rounded-xl shadow-lg">
          <div className="absolute inset-0 opacity-10">
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">
                  <circle cx="10" cy="10" r="1.5" fill="#FFD63A" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#dots)" />
            </svg>
          </div>
          
          <div className="flex flex-col items-center justify-center py-8 relative z-10">
            <div className="relative mb-8">
              <div className="absolute -inset-3 bg-[#FFD63A]/30 rounded-full blur-lg"></div>
              <div className="relative">
                <div className="w-24 h-24 border-4 border-[#FFD63A] border-t-[#FFD63A]/20 rounded-full animate-spin shadow-lg"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center">
                    <Target className="h-8 w-8 text-[#FFD63A]" />
                  </div>
                </div>
              </div>
            </div>
            
            <h3 className="text-2xl font-bold text-[#333333] mb-4 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-xl shadow-md border border-[#FFD63A]/30">
              Analyzing your speaking skills...
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full mb-6">
              {['Pronunciation', 'Fluency', 'Vocabulary', 'Grammar'].map((skill, index) => (
                <div key={skill} className="bg-white/80 backdrop-blur-sm p-4 rounded-lg border border-[#FFD63A]/30 shadow-sm flex items-center">
                  <div className="w-3 h-3 rounded-full bg-[#FFD63A] mr-3 animate-pulse" style={{ animationDelay: `${index * 0.2}s` }}></div>
                  <span className="font-medium text-[#333333]">{skill}</span>
                </div>
              ))}
            </div>
            
            <p className="text-[#555555] text-center max-w-md bg-white/80 backdrop-blur-sm p-4 rounded-lg border border-[#FFD63A]/30 shadow-md">
              Our AI is carefully evaluating your {language} speaking skills to provide an accurate assessment of your current proficiency level.
            </p>
          </div>
        </div>
      )}
      
      {/* Assessment Results*/}
      {status === 'complete' && assessment && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {isAuthenticated() ? (
            <>
              {/* Left Column: General Information - Authenticated User*/}
              <div className="space-y-6">
                {/* Playback Controls - Commented out as requested*/}
                {/* audioUrl && (
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
                
                {/* Recommended Level*/}
                <div className="bg-[#F0FDFB] p-6 rounded-lg text-center border border-[#4ECFBF] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Recommended Level</h3>
                  <div className="text-5xl font-bold text-[#333333] mb-3">{assessment.recommended_level}</div>
                  <div className="inline-block bg-[#4ECFBF] px-4 py-2 rounded-full text-white text-sm font-medium shadow-md">
                    Confidence: {assessment.confidence.toFixed(1)}%
                  </div>
                </div>
                
                {/* Overall Score*/}
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
                
                {/* Strengths*/}
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
                
                {/* Transcription*/}
                <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Your Speech</h3>
                  <p className="text-[#333333] bg-white p-4 rounded-lg border border-[#F75A5A]/30 shadow-inner">
                    {assessment.recognized_text || "No speech detected"}
                  </p>
                </div>
              </div>
              
              {/* Right Column: Detailed Assessment - Authenticated User*/}
              <div className="space-y-6">
                {/* Skill Scores*/}
                <div className="bg-[#F8F9FA] p-6 rounded-lg border border-gray-200 shadow-md overflow-auto">
                  <h3 className="text-lg text-[#333333] mb-3 font-medium">Skill Breakdown</h3>
                  
                  <div className="space-y-4 max-h-[600px] overflow-auto pr-2">
                    {/* Pronunciation*/}
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
                    
                    {/* Vocabulary*/}
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
                    
                    {/* Grammar*/}
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
                    
                    {/* Fluency*/}
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
                    
                    {/* Coherence*/}
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
          
            {/* Feedback and Next Steps*/}
            {/* Next Steps*/}
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
            </>
          ) : (
            <>
              {/* Left Column: Limited Information - Guest User*/}
              <div className="space-y-6">
                {/* Playback Controls - Commented out as requested*/}
                {/* audioUrl && (
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
                
                {/* Recommended Level*/}
                <div className="bg-[#F0FDFB] p-6 rounded-lg text-center border border-[#4ECFBF] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Recommended Level</h3>
                  <div className="text-5xl font-bold text-[#333333] mb-3">{assessment.recommended_level}</div>
                </div>
                
                {/* Strengths*/}
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

                {/* Transcription*/}
                <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Your Speech</h3>
                  <p className="text-[#333333] bg-white p-4 rounded-lg border border-[#F75A5A]/30 shadow-inner">
                    {assessment.recognized_text || "No speech detected"}
                  </p>
                </div>


              </div>
              
              {/* Right Column: Feedback and Next Steps - Guest User*/}
              <div className="space-y-6">
                {/* Areas for Improvement*/}
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
                
                {/* Next Steps*/}
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
            </>
          )}
          
          {/* Action Buttons - Centered at the bottom*/}
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
      
      {/* Error Message*/}
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
      
      {/* Manual Level Selection button removed*/}
      
      {/* Learning Plan Modal*/}
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
