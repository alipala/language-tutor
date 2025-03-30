'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, RotateCw, Volume2, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { assessSpeaking, fetchSpeakingPrompts, SpeakingAssessmentResult, SpeakingPrompt } from '@/lib/speaking-assessment-api';

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
  // State for recording and assessment
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing' | 'complete'>('idle');
  const [timer, setTimer] = useState(60);
  const [isTimerActive, setIsTimerActive] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [transcription, setTranscription] = useState('');
  const [assessment, setAssessment] = useState<SpeakingAssessmentResult | null>(null);
  const [error, setError] = useState('');
  const [prompts, setPrompts] = useState<SpeakingPrompt | null>(null);
  const [selectedPromptCategory, setSelectedPromptCategory] = useState('general');
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const promptRef = useRef('');

  // Define fallback prompts directly in the component
  const fallbackPrompts = {
    general: [
      'Tell me about yourself and your language learning experience.',
      'Describe your hometown and what you like about it.',
      'What are your hobbies and interests?',
      'Talk about your favorite book, movie, or TV show.',
      'Describe your typical day.'
    ],
    travel: [
      'Describe a memorable trip you\'ve taken.',
      'What\'s your favorite place to visit and why?',
      'Talk about a place you would like to visit in the future.',
      'Describe your ideal vacation.',
      'What do you usually do when you travel?'
    ],
    education: [
      'Talk about your educational background.',
      'Describe a teacher who influenced you.',
      'What subjects did you enjoy studying?',
      'How do you think education has changed in recent years?',
      'Describe your learning style.'
    ]
  };

  // Initialize with fallback prompts immediately to ensure UI is never empty
  useEffect(() => {
    // Set fallback prompts right away
    setPrompts(fallbackPrompts);
    const randomIndex = Math.floor(Math.random() * fallbackPrompts.general.length);
    setSelectedPrompt(fallbackPrompts.general[randomIndex]);
    promptRef.current = fallbackPrompts.general[randomIndex];
    
    // Then try to fetch from API
    const getPrompts = async () => {
      try {
        const promptsData = await fetchSpeakingPrompts(language);
        
        // Only update if we got valid data
        if (promptsData && promptsData.general && promptsData.general.length > 0) {
          setPrompts(promptsData);
          
          // Set a random prompt from the general category
          const randomIndex = Math.floor(Math.random() * promptsData.general.length);
          setSelectedPrompt(promptsData.general[randomIndex]);
          promptRef.current = promptsData.general[randomIndex];
          
          // Clear any error message
          setError(null);
        }
      } catch (err) {
        console.error('Error fetching prompts:', err);
        // We already have fallback prompts set, so just show an error message
        setError('Using default prompts due to connection issue.');
      }
    };
    
    // Try to get prompts from API, but we already have fallbacks if it fails
    getPrompts();
  }, [language]);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isTimerActive && timer > 0) {
      interval = setInterval(() => {
        setTimer((prevTimer) => {
          const newTimer = prevTimer - 1;
          
          // Show notification when 30 seconds have passed (30 seconds remaining)
          if (newTimer === 30) {
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
  }, [isTimerActive, timer]);

  // Clean up audio URL when component unmounts
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startRecording = async () => {
    try {
      audioChunksRef.current = [];
      setStatus('recording');
      setTimer(60);
      setIsTimerActive(true);
      setError('');
      setAssessment(null);
      setTranscription('');

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
        
        // Create audio URL for playback
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        
        processRecording(audioBlob);
      };

      mediaRecorder.start();
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Could not access microphone. Please check your browser permissions.');
      setStatus('idle');
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
    setStatus('processing');
    try {
      // Send to backend for assessment
      const result = await assessSpeaking(
        blob,
        language,
        60 - timer, // Actual duration recorded
        promptRef.current
      );
      
      setTranscription(result.recognized_text);
      setAssessment(result);
      setStatus('complete');
      
      if (onComplete) {
        onComplete(result);
      }
    } catch (err) {
      console.error('Error processing recording:', err);
      setError('Failed to process your speech. Please try again.');
      setStatus('idle');
    }
  };

  const handleSelectPrompt = (prompt: string) => {
    setSelectedPrompt(prompt);
    promptRef.current = prompt;
  };

  const handleSelectPromptCategory = (category: string) => {
    setSelectedPromptCategory(category);
    if (prompts && prompts[category] && prompts[category].length > 0) {
      const randomIndex = Math.floor(Math.random() * prompts[category].length);
      setSelectedPrompt(prompts[category][randomIndex]);
      promptRef.current = prompts[category][randomIndex];
    }
  };

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
    if (assessment && onSelectLevel) {
      onSelectLevel(assessment.recommended_level);
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

  return (
    <div className="flex flex-col space-y-6 w-full max-w-4xl mx-auto bg-gray-800 rounded-xl p-6 shadow-lg">
      {/* Hidden audio player for playback */}
      {audioUrl && (
        <audio 
          ref={audioPlayerRef} 
          src={audioUrl} 
          onEnded={() => setIsAudioPlaying(false)}
          className="hidden" 
        />
      )}
      
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Speaking Assessment</h2>
        <p className="text-gray-300">
          Speak for 30-60 seconds to assess your {language} proficiency level
        </p>
      </div>
      
      {/* Prompt Selection (only in idle state) */}
      {status === 'idle' && (
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-3">Speaking Prompt</h3>
          
          {/* Prompt Categories */}
          <div className="flex flex-wrap gap-2 mb-4">
            {prompts && Object.keys(prompts).map((category) => (
              <button
                key={category}
                onClick={() => handleSelectPromptCategory(category)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedPromptCategory === category 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-600 text-gray-200 hover:bg-gray-500'
                }`}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
          
          {/* Selected Prompt */}
          <div className="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-600">
            <p className="text-white">{selectedPrompt}</p>
          </div>
          
          {/* Other Prompts in Selected Category */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300">Other prompts:</h4>
            {prompts && prompts[selectedPromptCategory]?.map((prompt, index) => (
              prompt !== selectedPrompt && (
                <button
                  key={index}
                  onClick={() => handleSelectPrompt(prompt)}
                  className="block w-full text-left p-2 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm"
                >
                  {prompt}
                </button>
              )
            ))}
          </div>
        </div>
      )}
      
      {/* Recording Controls */}
      {status === 'idle' && (
        <div className="flex justify-center mt-4">
          <Button 
            onClick={startRecording}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-full flex items-center space-x-2"
          >
            <Mic className="h-5 w-5" />
            <span>Start Recording</span>
          </Button>
        </div>
      )}
      
      {/* Recording State */}
      {status === 'recording' && (
        <div className="space-y-4">
          <div className="flex items-center justify-center space-x-4">
            <div className="w-16 h-16 flex items-center justify-center bg-red-600 rounded-full animate-pulse">
              <Mic className="h-8 w-8 text-white" />
            </div>
            <div className="text-2xl font-bold text-white">{formatTime(timer)}</div>
          </div>
          
          <Progress value={(60 - timer) / 60 * 100} className="h-2 bg-gray-700" />
          
          <div className="flex justify-center mt-4">
            <Button 
              onClick={stopRecording}
              className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-full flex items-center space-x-2"
            >
              <Square className="h-5 w-5" />
              <span>Stop Recording</span>
            </Button>
          </div>
        </div>
      )}
      
      {/* Processing State */}
      {status === 'processing' && (
        <div className="flex flex-col items-center justify-center py-8 space-y-4">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-white text-lg">Analyzing your speaking skills...</p>
        </div>
      )}
      
      {/* Assessment Results */}
      {status === 'complete' && assessment && (
        <div className="space-y-6">
          {/* Playback Controls */}
          {audioUrl && (
            <div className="flex items-center justify-center space-x-4 bg-gray-700 p-3 rounded-lg">
              <Button 
                onClick={handlePlayAudio}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-full w-10 h-10 flex items-center justify-center"
              >
                {isAudioPlaying ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <div className="text-white">Listen to your recording</div>
            </div>
          )}
          
          {/* Recommended Level */}
          <div className="bg-gray-700 p-4 rounded-lg text-center">
            <h3 className="text-lg text-gray-300 mb-2">Recommended Level</h3>
            <div className="text-4xl font-bold text-white mb-2">{assessment.recommended_level}</div>
            <div className="text-sm text-gray-400">
              Confidence: {assessment.confidence.toFixed(1)}%
            </div>
          </div>
          
          {/* Overall Score */}
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="text-lg text-gray-300 mb-2">Overall Score</h3>
            <div className="flex items-center space-x-4">
              <div className={`text-3xl font-bold ${getScoreColor(assessment.overall_score)}`}>
                {assessment.overall_score.toFixed(1)}
              </div>
              <Progress 
                value={assessment.overall_score} 
                className={`h-3 bg-gray-600 flex-1`}
                indicatorClassName={getProgressColor(assessment.overall_score)}
              />
            </div>
          </div>
          
          {/* Transcription */}
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="text-lg text-gray-300 mb-2">Your Speech</h3>
            <p className="text-white bg-gray-800 p-3 rounded">
              {assessment.recognized_text || "No speech detected"}
            </p>
          </div>
          
          {/* Skill Scores */}
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="text-lg text-gray-300 mb-3">Skill Breakdown</h3>
            
            <div className="space-y-4">
              {/* Pronunciation */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-300">Pronunciation</span>
                  <span className={getScoreColor(assessment.pronunciation.score)}>
                    {assessment.pronunciation.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.pronunciation.score} 
                  className="h-2 bg-gray-600"
                  indicatorClassName={getProgressColor(assessment.pronunciation.score)}
                />
                <p className="text-sm text-gray-400 mt-1">{assessment.pronunciation.feedback}</p>
              </div>
              
              {/* Grammar */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-300">Grammar</span>
                  <span className={getScoreColor(assessment.grammar.score)}>
                    {assessment.grammar.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.grammar.score} 
                  className="h-2 bg-gray-600"
                  indicatorClassName={getProgressColor(assessment.grammar.score)}
                />
                <p className="text-sm text-gray-400 mt-1">{assessment.grammar.feedback}</p>
              </div>
              
              {/* Vocabulary */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-300">Vocabulary</span>
                  <span className={getScoreColor(assessment.vocabulary.score)}>
                    {assessment.vocabulary.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.vocabulary.score} 
                  className="h-2 bg-gray-600"
                  indicatorClassName={getProgressColor(assessment.vocabulary.score)}
                />
                <p className="text-sm text-gray-400 mt-1">{assessment.vocabulary.feedback}</p>
              </div>
              
              {/* Fluency */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-300">Fluency</span>
                  <span className={getScoreColor(assessment.fluency.score)}>
                    {assessment.fluency.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.fluency.score} 
                  className="h-2 bg-gray-600"
                  indicatorClassName={getProgressColor(assessment.fluency.score)}
                />
                <p className="text-sm text-gray-400 mt-1">{assessment.fluency.feedback}</p>
              </div>
              
              {/* Coherence */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-300">Coherence</span>
                  <span className={getScoreColor(assessment.coherence.score)}>
                    {assessment.coherence.score.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={assessment.coherence.score} 
                  className="h-2 bg-gray-600"
                  indicatorClassName={getProgressColor(assessment.coherence.score)}
                />
                <p className="text-sm text-gray-400 mt-1">{assessment.coherence.feedback}</p>
              </div>
            </div>
          </div>
          
          {/* Strengths and Areas for Improvement */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg text-gray-300 mb-2">Strengths</h3>
              <ul className="list-disc pl-5 text-green-400 space-y-1">
                {assessment.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            </div>
            
            {/* Areas for Improvement */}
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg text-gray-300 mb-2">Areas for Improvement</h3>
              <ul className="list-disc pl-5 text-yellow-400 space-y-1">
                {assessment.areas_for_improvement.map((area, index) => (
                  <li key={index}>{area}</li>
                ))}
              </ul>
            </div>
          </div>
          
          {/* Next Steps */}
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="text-lg text-gray-300 mb-2">Recommended Next Steps</h3>
            <ul className="list-disc pl-5 text-blue-400 space-y-1">
              {assessment.next_steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
          </div>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-4 pt-4">
            <Button 
              onClick={handleTryAgain}
              className="bg-gray-600 hover:bg-gray-500 text-white px-6 py-3 rounded-lg flex items-center justify-center space-x-2"
            >
              <RotateCw className="h-5 w-5" />
              <span>Try Again</span>
            </Button>
            
            <Button 
              onClick={handleSelectLevel}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg flex items-center justify-center space-x-2"
            >
              <ChevronRight className="h-5 w-5" />
              <span>Use This Level</span>
            </Button>
          </div>
        </div>
      )}
      
      {/* Error Message */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded-lg">
          {error}
        </div>
      )}
    </div>
  );
}
