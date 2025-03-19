'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';

// Define types for pronunciation assessment
export interface TranscriptSegment {
  text: string;
  assessment: 'correct' | 'minor' | 'error' | 'unassessed';
  confidence?: number;
}

export interface PronunciationAssessmentProps {
  transcript: string;
  isRecording: boolean;
  onStopRecording: () => void;
  language: string;
  level: string;
}

export default function PronunciationAssessment({
  transcript,
  isRecording,
  onStopRecording,
  language,
  level
}: PronunciationAssessmentProps) {
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [isAssessing, setIsAssessing] = useState(false);
  const prevTranscriptRef = useRef('');
  const segmentTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Process transcript changes to create segments
  useEffect(() => {
    if (!transcript || transcript === prevTranscriptRef.current) return;

    // Only process new text if we're recording and not in assessment mode
    if (isRecording && !isAssessing) {
      // Safely extract new text by comparing with previous transcript
      const prevText = prevTranscriptRef.current;
      let newText = '';
      
      // Only process if current transcript is longer than previous
      if (transcript.length > prevText.length) {
        // Check if previous text is at the beginning of current text
        if (transcript.startsWith(prevText)) {
          newText = transcript.substring(prevText.length).trim();
        } else {
          // If not a simple append, treat the whole transcript as new
          // This handles cases where transcript was completely replaced
          newText = transcript.trim();
        }
      }
      
      if (newText) {
        // Split new text into sentences or phrases
        const newSegments = splitIntoSegments(newText);
        
        if (newSegments.length > 0) {
          setSegments(prev => [
            ...prev,
            ...newSegments.map(text => ({
              text,
              assessment: 'unassessed' as const
            }))
          ]);

          // Set up delayed assessment for new segments
          if (segmentTimeoutRef.current) {
            clearTimeout(segmentTimeoutRef.current);
          }
          
          segmentTimeoutRef.current = setTimeout(() => {
            assessNewSegments();
          }, 1000); // Delay assessment to allow for more context
        }
      }
    }
    
    // Always update the previous transcript reference
    prevTranscriptRef.current = transcript;
  }, [transcript, isRecording, isAssessing]);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (segmentTimeoutRef.current) {
        clearTimeout(segmentTimeoutRef.current);
      }
    };
  }, []);

  // Split text into meaningful segments (sentences or phrases)
  const splitIntoSegments = (text: string): string[] => {
    // Simple split by sentence-ending punctuation
    const rawSegments = text.split(/(?<=[.!?])\s+/);
    
    // Filter out empty segments and trim
    return rawSegments
      .map(segment => segment.trim())
      .filter(segment => segment.length > 0);
  };

  // Assess new segments with simulated pronunciation assessment
  // In a real implementation, this would call an API for actual assessment
  const assessNewSegments = () => {
    setSegments(prev => {
      return prev.map(segment => {
        // Only assess segments that haven't been assessed yet
        if (segment.assessment === 'unassessed') {
          // Simulate assessment based on language level
          // In a real implementation, this would use actual pronunciation assessment
          const assessmentResult = simulateAssessment(segment.text, language, level);
          return {
            ...segment,
            assessment: assessmentResult.assessment,
            confidence: assessmentResult.confidence
          };
        }
        return segment;
      });
    });
  };

  // Simulate pronunciation assessment
  // This would be replaced with actual API calls in production
  const simulateAssessment = (
    text: string, 
    language: string, 
    level: string
  ): { assessment: 'correct' | 'minor' | 'error', confidence: number } => {
    // This is just a simulation - in a real implementation, 
    // we would call an actual pronunciation assessment API
    
    // Generate a random assessment weighted by level
    // Higher levels have higher standards
    const levelDifficulty = {
      'a1': 0.2,
      'a2': 0.3,
      'b1': 0.4,
      'b2': 0.5,
      'c1': 0.6,
      'c2': 0.7
    }[level.toLowerCase()] || 0.4;
    
    const randomValue = Math.random();
    const confidence = 0.5 + Math.random() * 0.5; // Random confidence between 0.5 and 1.0
    
    // Simulate more errors for longer text and higher levels
    const errorProbability = levelDifficulty * (0.3 + (text.length / 100));
    const minorProbability = levelDifficulty * (0.5 + (text.length / 80));
    
    if (randomValue < errorProbability) {
      return { assessment: 'error', confidence };
    } else if (randomValue < minorProbability) {
      return { assessment: 'minor', confidence };
    } else {
      return { assessment: 'correct', confidence };
    }
  };

  // Handle review button click
  const handleReviewPronunciation = () => {
    // Stop recording
    onStopRecording();
    setIsAssessing(true);
    
    // Assess any remaining unassessed segments
    setSegments(prev => {
      return prev.map(segment => {
        if (segment.assessment === 'unassessed') {
          const assessmentResult = simulateAssessment(segment.text, language, level);
          return {
            ...segment,
            assessment: assessmentResult.assessment,
            confidence: assessmentResult.confidence
          };
        }
        return segment;
      });
    });
  };

  // Reset assessment state
  const handleContinue = () => {
    setIsAssessing(false);
  };

  // Get color class based on assessment
  const getColorClass = (assessment: string): string => {
    switch (assessment) {
      case 'correct':
        return 'text-green-500 dark:text-green-400';
      case 'minor':
        return 'text-yellow-500 dark:text-yellow-400';
      case 'error':
        return 'text-red-500 dark:text-red-400';
      default:
        return 'text-white';
    }
  };

  // Get background color class based on assessment
  const getBackgroundClass = (assessment: string): string => {
    switch (assessment) {
      case 'correct':
        return 'bg-green-500/10 border-green-500/20';
      case 'minor':
        return 'bg-yellow-500/10 border-yellow-500/20';
      case 'error':
        return 'bg-red-500/10 border-red-500/20';
      default:
        return 'bg-slate-500/10 border-slate-500/20';
    }
  };

  return (
    <div className="w-full">
      {/* Review Button - Only show when recording and have content */}
      {isRecording && segments.length > 0 && !isAssessing && (
        <div className="flex justify-center mb-6">
          <Button
            onClick={handleReviewPronunciation}
            className="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 rounded-full shadow-lg hover:shadow-purple-500/20 transition-all duration-300 flex items-center space-x-2 transform hover:translate-y-[-2px]"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span>Review Pronunciation</span>
          </Button>
        </div>
      )}

      {/* Assessment Results */}
      {segments.length > 0 && (
        <div className={`rounded-xl border border-white/20 p-4 ${isAssessing ? 'bg-slate-800/50' : 'bg-transparent'}`}>
          <h3 className="text-lg font-semibold mb-3 text-indigo-400 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
            {isAssessing ? 'Pronunciation Assessment' : 'Real-time Transcript'}
          </h3>

          <div className="space-y-3">
            {segments.map((segment, index) => (
              <div 
                key={index} 
                className={`p-3 rounded-lg border animate-fadeIn ${getBackgroundClass(segment.assessment)}`}
              >
                <p className={`text-md ${getColorClass(segment.assessment)}`}>
                  {segment.text}
                </p>
                
                {isAssessing && segment.assessment !== 'unassessed' && (
                  <div className="mt-2 flex items-center">
                    <div className="w-full bg-gray-700/30 rounded-full h-2.5">
                      <div 
                        className={`h-2.5 rounded-full ${
                          segment.assessment === 'correct' ? 'bg-green-500' : 
                          segment.assessment === 'minor' ? 'bg-yellow-500' : 'bg-red-500'
                        }`} 
                        style={{ width: `${(segment.confidence || 0.5) * 100}%` }}
                      ></div>
                    </div>
                    <span className="ml-2 text-xs text-gray-400">
                      {segment.assessment === 'correct' ? 'Good' : 
                       segment.assessment === 'minor' ? 'Fair' : 'Needs Work'}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Legend - Only show in assessment mode */}
          {isAssessing && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Color Guide:</h4>
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-300">Good pronunciation</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                  <span className="text-sm text-gray-300">Minor issues</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
                  <span className="text-sm text-gray-300">Needs improvement</span>
                </div>
              </div>
            </div>
          )}

          {/* Continue Button - Only show in assessment mode */}
          {isAssessing && (
            <div className="mt-4 flex justify-center">
              <Button
                onClick={handleContinue}
                className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-full shadow-lg hover:shadow-indigo-500/20 transition-all duration-300"
              >
                Continue Learning
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
