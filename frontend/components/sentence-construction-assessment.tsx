'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { assessSentence, fetchExercises } from '@/lib/sentence-assessment-api';

// Define types for sentence construction assessment
export interface GrammarIssue {
  issue_type: string;
  description: string;
  suggestion: string;
  severity: string;
}

export interface AssessmentResult {
  recognized_text: string;
  grammatical_score: number;
  vocabulary_score: number;
  complexity_score: number;
  appropriateness_score: number;
  overall_score: number;
  grammar_issues: GrammarIssue[];
  improvement_suggestions: string[];
  corrected_text?: string;
  level_appropriate_alternatives?: string[];
}

export interface SentenceConstructionProps {
  transcript: string;
  isRecording: boolean;
  onStopRecording: () => void;
  language: string;
  level: string;
  exerciseType: string;
  onContinueLearning?: () => void;
  onChangeExerciseType?: (type: string) => void;
}

export default function SentenceConstructionAssessment({
  transcript,
  isRecording,
  onStopRecording,
  language,
  level,
  exerciseType,
  onContinueLearning,
  onChangeExerciseType
}: SentenceConstructionProps) {
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult | null>(null);
  const [isAssessing, setIsAssessing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const transcriptContainerRef = useRef<HTMLDivElement>(null);
  
  // Add state for storing assessment history
  const [assessmentHistory, setAssessmentHistory] = useState<Array<{
    transcript: string;
    result: AssessmentResult;
    timestamp: Date;
  }>>([]);
  
  // Add state for selected historical assessment
  const [selectedHistoryIndex, setSelectedHistoryIndex] = useState<number | null>(null);
  
  const [progress, setProgress] = useState<{
    gradeHistory: number[];
    errorReduction: number;
    complexityGrowth: number;
  }>({
    gradeHistory: [],
    errorReduction: 0,
    complexityGrowth: 0
  });

  // Mock exercises for different types
  const [currentExercises, setCurrentExercises] = useState<any[]>([]);

  // Fetch exercises based on exercise type
  useEffect(() => {
    const fetchExercises = async () => {
      try {
        // In a real implementation, this would call the backend API
        // For now we'll use mockup data
        
        // Example exercise data structure
        const mockExercises = {
          free: [
            { prompt: "Describe your favorite hobby", example: "I enjoy hiking in the mountains because it helps me relax." },
            { prompt: "Talk about your last vacation", example: "Last summer, I visited the beach with my family." },
          ],
          guided: [
            { prompt: "Create a sentence using: yesterday, went, store", example: "Yesterday, I went to the store to buy groceries." },
            { prompt: "Use these words: despite, rain, enjoyed", example: "Despite the rain, we enjoyed our picnic under the shelter." },
          ],
          transformation: [
            { prompt: "Change to passive voice: 'The chef prepared the meal.'", example: "The meal was prepared by the chef." },
            { prompt: "Change to past tense: 'I am walking to school.'", example: "I was walking to school." },
          ],
          correction: [
            { prompt: "Correct: 'I goed to the store yesterday.'", example: "I went to the store yesterday." },
            { prompt: "Correct: 'She don't like apples.'", example: "She doesn't like apples." },
          ],
          translation: [
            { prompt: "Translate to English: 'Bonjour, comment ça va?'", example: "Hello, how are you?" },
            { prompt: "Translate to English: 'Ich bin müde.'", example: "I am tired." },
          ]
        };
        
        setCurrentExercises(mockExercises[exerciseType as keyof typeof mockExercises] || mockExercises.free);
      } catch (err) {
        console.error("Error fetching exercises:", err);
        setError("Failed to load exercises. Please try again.");
      }
    };
    
    fetchExercises();
  }, [exerciseType]);

  // Handle analyze button click
  const handleAnalyzeSentence = async () => {
    // Stop recording
    onStopRecording();
    setIsAssessing(true);
    setShowModal(true);
    setIsLoading(true);
    setError(null);
    
    try {
      // Get the audio blob from the MediaRecorder
      // For demo purposes, we'll create a mock audio blob if none exists
      let audioBlob: Blob;
      
      // Check if we have a valid transcript first - if so, prioritize it over audio recording
      if (transcript && transcript.trim() !== '') {
        console.log('Using transcript for analysis:', transcript);
        // Use an empty audio blob since we'll prioritize the transcript
        audioBlob = new Blob([], { type: 'audio/wav' });
      }
      // If no transcript, try to record audio
      else if (window.navigator.mediaDevices) {
        try {
          // Try to get the actual audio recording if available
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const mediaRecorder = new MediaRecorder(stream);
          const audioChunks: BlobPart[] = [];
          
          // Set up event handlers
          mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
          };
          
          // Create a promise to wait for the recording to complete
          const recordingPromise = new Promise<Blob>((resolve) => {
            mediaRecorder.onstop = () => {
              const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
              resolve(audioBlob);
              
              // Stop all tracks to release the microphone
              stream.getTracks().forEach(track => track.stop());
            };
          });
          
          // Start recording a short sample
          mediaRecorder.start();
          
          // Record for 1 second for demo purposes
          setTimeout(() => {
            mediaRecorder.stop();
          }, 1000);
          
          // Wait for the recording to complete
          audioBlob = await recordingPromise;
        } catch (err) {
          console.error('Error accessing microphone:', err);
          // Fallback to an empty audio blob
          audioBlob = new Blob([], { type: 'audio/wav' });
        }
      } else {
        // Fallback for environments without MediaDevices
        audioBlob = new Blob([], { type: 'audio/wav' });
      }
      
      // Call the backend API with the transcript as context
      // This ensures we get a proper analysis even if the audio recording fails
      const result = await assessSentence(
        audioBlob,
        language,
        level,
        exerciseType,
        [], // No specific target grammar
        transcript // Use the transcript as context to ensure proper analysis
      );
      
      // Always use the transcript from the UI if available
      // This ensures we're analyzing the correct text
      if (transcript && transcript.trim() !== '') {
        result.recognized_text = transcript;
      }
      
      // Update assessment result
      setAssessmentResult(result);
      
      // Add to assessment history
      if (transcript && transcript.trim() !== '') {
        setAssessmentHistory(prev => [
          ...prev,
          {
            transcript: transcript,
            result: result,
            timestamp: new Date()
          }
        ]);
        
        // Reset selected history index when adding a new assessment
        setSelectedHistoryIndex(null);
      }
      
      // Update progress tracking
      setProgress(prev => {
        const newHistory = [...prev.gradeHistory, result.overall_score];
        const errorChange = prev.gradeHistory.length > 0 
          ? Math.max(0, result.overall_score - prev.gradeHistory[prev.gradeHistory.length - 1])
          : 0;
        
        return {
          gradeHistory: newHistory,
          errorReduction: prev.errorReduction + (errorChange > 0 ? 1 : 0),
          complexityGrowth: result.complexity_score > 70 ? prev.complexityGrowth + 0.1 : prev.complexityGrowth
        };
      });
      
    } catch (err) {
      console.error("Error analyzing sentence:", err);
      setError("Failed to analyze your sentence. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Continue learning after review
  const handleContinue = () => {
    setIsAssessing(false);
    setShowModal(false);
    setAssessmentResult(null);
    
    if (onContinueLearning) {
      setTimeout(() => {
        onContinueLearning();
      }, 300);
    }
  };
  
  // Close modal without continuing
  const handleCloseModal = () => {
    setShowModal(false);
    setIsAssessing(false);
  };
  
  // Handle selecting a historical assessment
  const handleSelectHistoricalAssessment = (index: number) => {
    setSelectedHistoryIndex(index);
    const historicalItem = assessmentHistory[index];
    setAssessmentResult(historicalItem.result);
    setShowModal(true);
  };

  // Get color class based on score
  const getScoreColorClass = (score: number): string => {
    if (score >= 80) return 'text-green-500 dark:text-green-400';
    if (score >= 60) return 'text-yellow-500 dark:text-yellow-400';
    return 'text-red-500 dark:text-red-400';
  };

  // Get background class based on score for progress indicators
  const getScoreBackgroundClass = (score: number): string => {
    if (score >= 80) return 'bg-green-500/20 border-green-500/30';
    if (score >= 60) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-red-500/20 border-red-500/30';
  };

  return (
    <div className="w-full flex flex-col">
      {/* Exercise Type Selector */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3 text-indigo-400 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Exercise Type
        </h3>
        <div className="flex flex-wrap gap-2 justify-center">
          {[
            { id: 'free', label: 'Free Production' },
            { id: 'guided', label: 'Guided Construction' },
            { id: 'transformation', label: 'Transformation' },
            { id: 'correction', label: 'Error Correction' },
            { id: 'translation', label: 'Translation' },
          ].map(type => (
            <Button
              key={type.id}
              onClick={() => onChangeExerciseType && onChangeExerciseType(type.id)}
              className={`text-sm px-4 py-2 transition-all duration-300 ${
                exerciseType === type.id 
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg' 
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              {type.label}
            </Button>
          ))}
        </div>
      </div>
      
      {/* Current Exercise Display */}
      {currentExercises.length > 0 && (
        <div className="mb-6 bg-slate-800/50 rounded-xl border border-slate-700/50 p-4">
          <h3 className="text-lg font-semibold mb-3 text-indigo-400">Current Exercise</h3>
          <div className="space-y-4">
            {currentExercises.slice(0, 1).map((exercise, idx) => (
              <div key={idx} className="space-y-2">
                <p className="text-white font-medium">{exercise.prompt}</p>
                {exercise.example && (
                  <p className="text-slate-400 text-sm italic">Example: {exercise.example}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Button - Only show when recording and have content */}
      {isRecording && transcript.length > 0 && !isAssessing && (
        <div className="flex justify-center mb-6">
          <Button
            onClick={handleAnalyzeSentence}
            className="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 rounded-full shadow-lg hover:shadow-purple-500/20 transition-all duration-300 flex items-center space-x-2 transform hover:translate-y-[-2px]"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span>Analyze Sentence</span>
          </Button>
        </div>
      )}

      {/* Previous Assessments History */}
      {assessmentHistory.length > 0 && (
        <div className="mb-6 bg-slate-800/30 rounded-xl border border-slate-700/30 p-4 flex-shrink-0">
          <h3 className="text-lg font-semibold mb-3 text-indigo-400 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Previous Sentences
          </h3>
          <div className="max-h-[150px] overflow-y-auto custom-scrollbar">
            {assessmentHistory.map((item, index) => (
              <div 
                key={index} 
                className={`p-3 mb-2 rounded-lg border ${index === selectedHistoryIndex ? 'bg-indigo-900/30 border-indigo-500/50' : 'bg-slate-800/50 border-slate-700/50'} hover:bg-slate-700/50 cursor-pointer transition-colors`}
                onClick={() => handleSelectHistoricalAssessment(index)}
              >
                <div className="flex justify-between items-center">
                  <p className="text-white truncate">{item.transcript}</p>
                  <div className="flex items-center space-x-2 ml-2 flex-shrink-0">
                    <span className="text-xs px-2 py-1 rounded-full bg-indigo-900/70 text-indigo-200">
                      Score: {item.result.overall_score.toFixed(1)}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Progress Tracking - Show when we have history */}
      {progress.gradeHistory.length > 0 && (
        <div className="mb-6 bg-slate-800/30 rounded-xl border border-slate-700/30 p-4 flex-shrink-0">
          <h3 className="text-lg font-semibold mb-3 text-indigo-400 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            Your Progress
          </h3>
          
          {/* Score History */}
          <div className="mb-3">
            <p className="text-sm text-slate-400 mb-2">Score History:</p>
            <div className="flex items-center space-x-1">
              {progress.gradeHistory.map((score, idx) => (
                <div 
                  key={idx} 
                  className={`h-6 w-6 flex items-center justify-center text-xs rounded ${getScoreBackgroundClass(score)}`}
                  title={`Assessment ${idx + 1}: ${score}`}
                >
                  {Math.floor(score / 10)}
                </div>
              ))}
            </div>
          </div>
          
          {/* Improvement Metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-800/50 p-2 rounded">
              <p className="text-xs text-slate-400">Error Reduction</p>
              <p className="text-lg font-semibold text-green-400">{progress.errorReduction > 0 ? `+${progress.errorReduction}` : "0"}</p>
            </div>
            <div className="bg-slate-800/50 p-2 rounded">
              <p className="text-xs text-slate-400">Complexity Growth</p>
              <p className="text-lg font-semibold text-blue-400">{progress.complexityGrowth.toFixed(1)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Assessment Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn overflow-hidden">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">Sentence Assessment</h2>
              <Button
                onClick={handleCloseModal}
                variant="ghost"
                className="rounded-full h-8 w-8 p-0 text-slate-400 hover:text-white"
              >
                <X size={18} />
              </Button>
            </div>

            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-slate-400">Analyzing your sentence...</p>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <div className="text-red-500 mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-red-400 mb-2">{error}</p>
                <Button onClick={handleCloseModal} className="mt-4 bg-slate-700 hover:bg-slate-600">
                  Close
                </Button>
              </div>
            ) : assessmentResult && (
              <>
                {/* Recognized Text */}
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-slate-400">Recognized Text</h3>
                  <p className="text-white bg-slate-800 p-3 rounded mt-1">{assessmentResult.recognized_text}</p>
                </div>

                {/* Scores */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {[
                    { label: "Grammar", score: assessmentResult.grammatical_score },
                    { label: "Vocabulary", score: assessmentResult.vocabulary_score },
                    { label: "Complexity", score: assessmentResult.complexity_score },
                    { label: "Overall", score: assessmentResult.overall_score },
                  ].map((item, i) => (
                    <div key={i} className="bg-slate-800 p-3 rounded text-center">
                      <div className="text-sm text-slate-400">{item.label}</div>
                      <div className={`text-2xl font-bold ${getScoreColorClass(item.score)}`}>
                        {item.score}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Grammar Issues */}
                {assessmentResult.grammar_issues.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-slate-400 mb-2">Grammar Issues</h3>
                    <div className="space-y-3">
                      {assessmentResult.grammar_issues.map((issue, i) => (
                        <div key={i} className="bg-slate-800 p-3 rounded border-l-4 border-yellow-500">
                          <div className="flex justify-between">
                            <span className="font-medium">{issue.issue_type}</span>
                            <span className={`text-sm ${
                              issue.severity === 'minor' ? 'text-green-400' : 
                              issue.severity === 'moderate' ? 'text-yellow-400' : 'text-red-400'
                            }`}>
                              {issue.severity}
                            </span>
                          </div>
                          <p className="text-sm text-slate-300 mt-1">{issue.description}</p>
                          <p className="text-sm text-green-400 mt-1">Suggestion: {issue.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Corrected Text */}
                {assessmentResult.corrected_text && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-slate-400">Corrected Text</h3>
                    <p className="text-white bg-slate-800 p-3 rounded mt-1 border-l-4 border-green-500">
                      {assessmentResult.corrected_text}
                    </p>
                  </div>
                )}

                {/* Improvement Suggestions */}
                {assessmentResult.improvement_suggestions.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-slate-400 mb-2">Improvement Suggestions</h3>
                    <ul className="list-disc pl-5 space-y-1">
                      {assessmentResult.improvement_suggestions.map((suggestion, i) => (
                        <li key={i} className="text-slate-300">{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Alternative Expressions */}
                {assessmentResult.level_appropriate_alternatives && assessmentResult.level_appropriate_alternatives.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-slate-400 mb-2">Alternative Expressions</h3>
                    <div className="space-y-2">
                      {assessmentResult.level_appropriate_alternatives.map((alt, i) => (
                        <div key={i} className="bg-slate-800 p-2 rounded text-slate-300">{alt}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Continue Button */}
                <div className="flex justify-center mt-6">
                  <Button
                    onClick={handleContinue}
                    className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-full"
                  >
                    Continue Learning
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Transcript Display */}
      <div ref={transcriptContainerRef} className="w-full p-4 bg-slate-800/40 rounded-lg border border-slate-700 min-h-[100px] max-h-[300px] overflow-y-auto">
        {transcript ? (
          <p className="text-white">{transcript}</p>
        ) : (
          <p className="text-slate-500 italic">Your spoken text will appear here...</p>
        )}
      </div>
    </div>
  );
}
