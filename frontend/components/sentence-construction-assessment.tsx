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
  onAnalyzeRef?: React.MutableRefObject<(() => void) | null>;
  onMessageAnalyzed?: (messageId: string) => void;
  currentMessageId?: string;
}

export default function SentenceConstructionAssessment({
  transcript,
  isRecording,
  onStopRecording,
  language,
  level,
  exerciseType,
  onContinueLearning,
  onChangeExerciseType,
  onAnalyzeRef,
  onMessageAnalyzed,
  currentMessageId
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

  // Store the analyze function in the ref if provided
  useEffect(() => {
    if (onAnalyzeRef) {
      onAnalyzeRef.current = () => {
        if (transcript.length > 0 && !isAssessing && isInTargetLanguage(transcript)) {
          // If recording, stop it first
          if (isRecording) {
            onStopRecording();
          }
          // Then analyze the sentence
          handleAnalyzeSentence();
          
          // Mark this message as analyzed if we have the callback and message ID
          if (onMessageAnalyzed && currentMessageId) {
            onMessageAnalyzed(currentMessageId);
          }
        }
      };
    }
  }, [transcript, isAssessing, isRecording, currentMessageId]);

  // Function to detect if text is in the target language
  const isInTargetLanguage = (text: string): boolean => {
    if (!text || text.trim() === '') return false;
    
    const lowerText = text.toLowerCase();
    
    // Language detection patterns (same as in speech-client.tsx)
    const languagePatterns: Record<string, RegExp[]> = {
      dutch: [
        /\b(ik|je|het|de|een|en|is|zijn|hebben|mijn|jouw|hoe|wat|waar|waarom|wanneer|wie)\b/i,
        /\b(goed|slecht|mooi|lelijk|groot|klein|nieuw|oud|veel|weinig)\b/i,
        /\b(hallo|dag|goedemorgen|goedemiddag|goedenavond|doei|tot ziens)\b/i
      ],
      spanish: [
        /\b(yo|tu|el|ella|nosotros|ellos|es|son|tengo|tiene|mi|tu|como|que|donde|por que|cuando|quien)\b/i,
        /\b(bueno|malo|bonito|feo|grande|pequeño|nuevo|viejo|mucho|poco)\b/i,
        /\b(hola|buenos dias|buenas tardes|buenas noches|adios|hasta luego)\b/i
      ],
      german: [
        /\b(ich|du|er|sie|es|wir|sie|bin|ist|sind|habe|hat|mein|dein|wie|was|wo|warum|wann|wer)\b/i,
        /\b(gut|schlecht|schön|hässlich|groß|klein|neu|alt|viel|wenig)\b/i,
        /\b(hallo|guten tag|guten morgen|guten abend|auf wiedersehen|tschüss)\b/i
      ],
      french: [
        /\b(je|tu|il|elle|nous|ils|elles|suis|est|sont|ai|a|mon|ton|comment|quoi|où|pourquoi|quand|qui)\b/i,
        /\b(bon|mauvais|beau|laid|grand|petit|nouveau|vieux|beaucoup|peu)\b/i,
        /\b(bonjour|salut|bonsoir|au revoir|à bientôt)\b/i
      ],
      portuguese: [
        /\b(eu|tu|ele|ela|nós|eles|elas|sou|é|são|tenho|tem|meu|teu|como|que|onde|por que|quando|quem)\b/i,
        /\b(bom|mau|bonito|feio|grande|pequeno|novo|velho|muito|pouco)\b/i,
        /\b(olá|bom dia|boa tarde|boa noite|adeus|até logo)\b/i
      ],
      english: [
        /\b(i|you|he|she|it|we|they|am|is|are|was|were|have|has|had|my|your|how|what|where|why|when|who)\b/i,
        /\b(good|bad|nice|ugly|big|small|new|old|many|few)\b/i,
        /\b(hello|hi|morning|afternoon|evening|goodbye|bye|see you)\b/i
      ]
    };
    
    // Check if text contains patterns from the target language
    const currentLanguage = language as keyof typeof languagePatterns;
    const containsTargetLanguage = languagePatterns[currentLanguage]?.some((pattern: RegExp) => pattern.test(lowerText)) || false;
    
    // Check if text contains English patterns (common wrong language)
    const containsEnglish = languagePatterns.english.some((pattern: RegExp) => pattern.test(lowerText));
    
    // Additional language-specific checks
    let isLikelyWrongLanguage = false;
    
    if (language === 'dutch') {
      // Dutch-specific detection
      const hasNonDutchCharacters = /[qwxyz]/i.test(lowerText) && lowerText.length > 3; // These characters are rare in Dutch
      const hasDutchSpecificCombinations = /\b(ij|aa|ee|oo|uu|eu|oe|ui)\b/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasDutchSpecificCombinations) ||
                           hasNonDutchCharacters;
    } else if (language === 'spanish') {
      // Spanish-specific detection
      const hasNonSpanishCharacters = /[kw]/i.test(lowerText) && lowerText.length > 3; // These are uncommon in Spanish
      const hasSpanishSpecificCharacters = /[ñáéíóúü]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasSpanishSpecificCharacters) ||
                           hasNonSpanishCharacters;
    } else if (language === 'german') {
      // German-specific detection
      const hasGermanSpecificCharacters = /[äöüß]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasGermanSpecificCharacters);
    } else if (language === 'french') {
      // French-specific detection
      const hasFrenchSpecificCharacters = /[éèêëàâçîïôùûüÿ]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasFrenchSpecificCharacters);
    } else if (language === 'portuguese') {
      // Portuguese-specific detection
      const hasPortugueseSpecificCharacters = /[áàâãéêíóôõúç]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasPortugueseSpecificCharacters);
    }
    
    // Return true if it's likely in the target language (not wrong language)
    return !isLikelyWrongLanguage;
  };

  // Handle analyze button click
  const handleAnalyzeSentence = async () => {
    // Stop recording
    onStopRecording();
    
    // Check if the transcript is in the target language
    if (!isInTargetLanguage(transcript)) {
      console.log('Not analyzing sentence because it is not in the target language:', transcript);
      return;
    }
    
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
      
      // Add to assessment history only if in target language
      if (transcript && transcript.trim() !== '' && isInTargetLanguage(transcript)) {
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
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-[#F75A5A]';
  };

  // Get background class based on score for progress indicators
  const getScoreBackgroundClass = (score: number): string => {
    if (score >= 80) return 'bg-green-500/20 border-green-500/30';
    if (score >= 60) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-red-500/20 border-red-500/30';
  };

  return (
    <div className="w-full flex flex-col">
      {/* Exercise Type and Current Exercise sections removed */}

      {/* Analysis Button removed from here and moved to speech bubble */}
      
      {/* Warning message when content is not in target language */}
      {isRecording && transcript.length > 0 && !isAssessing && !isInTargetLanguage(transcript) && (
        <div className="flex justify-center mb-6">
          <div className="px-4 py-3 bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-200 max-w-md text-center animate-fade-in">
            <p className="text-sm">Please speak in {language.charAt(0).toUpperCase() + language.slice(1)} to analyze your sentence.</p>
          </div>
        </div>
      )}

      {/* Previous Assessments History - Condensed */}
      {assessmentHistory.length > 0 && (
        <div className="mb-4 bg-[#FFECB3] rounded-lg border border-[#FFD63A]/50 p-3 flex-shrink-0">
          <h3 className="text-sm font-semibold mb-1 text-[#FFA955] flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Previous Sentences
          </h3>
          <div className="max-h-[120px] overflow-y-auto custom-scrollbar">
            {assessmentHistory.map((item, index) => (
              <div 
                key={index} 
                className={`p-2 mb-1 rounded-lg border ${index === selectedHistoryIndex ? 'bg-[#FFD63A]/20 border-[#FFD63A]/50' : 'bg-[#FFF8E1]/80 border-[#FFD63A]/20'} hover:bg-[#FFD63A]/30 cursor-pointer transition-colors`}
                onClick={() => handleSelectHistoricalAssessment(index)}
              >
                <div className="flex justify-between items-center">
                  <p className="text-slate-800 truncate">{item.transcript}</p>
                  <div className="flex items-center space-x-2 ml-2 flex-shrink-0">
                    <span className="text-xs px-2 py-1 rounded-full bg-[#FFD63A] text-slate-800">
                      Score: {item.result.overall_score.toFixed(1)}
                    </span>
                    <span className="text-xs text-slate-600">
                      {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Progress Tracking - Show when we have history - Condensed */}
      {progress.gradeHistory.length > 0 && (
        <div className="mb-4 bg-[#FFCDD2] rounded-lg border border-[#F75A5A]/50 p-3 flex-shrink-0">
          <h3 className="text-sm font-semibold mb-1 text-[#F75A5A] flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            Your Progress
          </h3>
          
          {/* Score History */}
          <div className="mb-3">
            <p className="text-sm text-slate-600 mb-2">Score History:</p>
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
            <div className="bg-[#F0FAFA] p-2 rounded border border-[#4ECFBF]/30">
              <p className="text-xs text-slate-600">Error Reduction</p>
              <p className="text-lg font-semibold text-[#4ECFBF]">{progress.errorReduction > 0 ? `+${progress.errorReduction}` : "0"}</p>
            </div>
            <div className="bg-[#FFF0F0] p-2 rounded border border-[#F75A5A]/30">
              <p className="text-xs text-slate-600">Complexity Growth</p>
              <p className="text-lg font-semibold text-[#F75A5A]">{progress.complexityGrowth.toFixed(1)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Assessment Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-2 sm:p-4 animate-fadeIn">
          <div className="bg-white border border-[#4ECFBF]/30 shadow-lg rounded-xl max-w-3xl w-full max-h-[90vh] sm:max-h-[80vh] overflow-hidden flex flex-col">
            {/* Header Section with Sticky Positioning */}
            <div className="sticky top-0 bg-white pt-2 sm:pt-3 px-3 sm:px-5 pb-2 sm:pb-3 z-10 border-b border-[#4ECFBF]/30">
              <div className="flex justify-between items-center">
                <h2 className="text-base sm:text-lg font-bold text-[#F75A5A]">Sentence Assessment</h2>
                <Button
                  onClick={handleCloseModal}
                  variant="ghost"
                  className="rounded-full h-8 w-8 p-0 text-slate-500 hover:text-[#F75A5A] hover:bg-slate-100"
                >
                  <X size={18} />
                </Button>
              </div>
              
              {!isLoading && !error && assessmentResult && (
                <div className="w-full mt-3">
                  <Button
                    onClick={handleContinue}
                    className="w-full py-1.5 sm:py-2 bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white text-sm sm:text-base font-medium rounded-md flex items-center justify-center shadow-sm transition-colors"
                  >
                    Continue Learning
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                  </Button>
                </div>
              )}
            </div>

            {/* Scrollable Content Area */}
            <div className="p-3 sm:p-5 pt-2 sm:pt-3 overflow-y-auto">
              {isLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="h-12 w-12 border-4 border-[#4ECFBF] border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-[#4ECFBF] font-medium">Analyzing your sentence...</p>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <div className="text-[#F75A5A] mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-slate-600 mb-2">{error}</p>
                <Button onClick={handleCloseModal} className="mt-4 bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white transition-colors">
                  Close
                </Button>
              </div>
            ) : assessmentResult && (
              <>
                {/* Recognized Text */}
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-slate-600">Recognized Text</h3>
                  <p className="text-slate-800 bg-slate-100 p-3 rounded-md mt-1 border border-slate-200">{assessmentResult.recognized_text}</p>
                </div>

                {/* Scores */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 mb-3 sm:mb-4">
                  {[
                    { label: "Grammar", score: assessmentResult.grammatical_score },
                    { label: "Vocabulary", score: assessmentResult.vocabulary_score },
                    { label: "Complexity", score: assessmentResult.complexity_score },
                    { label: "Overall", score: assessmentResult.overall_score },
                  ].map((item, i) => (
                    <div key={i} className="bg-slate-100 border border-slate-200 p-3 rounded-md text-center shadow-sm">
                      <div className="text-sm text-slate-600 font-medium">{item.label}</div>
                      <div className={`text-2xl font-bold ${getScoreColorClass(item.score)}`}>
                        {item.score}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Grammar Issues */}
                {assessmentResult.grammar_issues.length > 0 && (
                  <div className="mb-3">
                    <h3 className="text-sm font-medium text-slate-600 mb-2">Grammar Issues</h3>
                    <div className="space-y-2">
                      {assessmentResult.grammar_issues.map((issue, i) => (
                        <div key={i} className="bg-slate-50 p-3 rounded-md border border-slate-200 border-l-4 border-l-yellow-500 text-sm sm:text-base shadow-sm">
                          <div className="flex justify-between">
                            <span className="font-medium text-slate-800">{issue.issue_type}</span>
                            <span className={`text-sm font-medium ${
                              issue.severity === 'minor' ? 'text-green-600' : 
                              issue.severity === 'moderate' ? 'text-yellow-600' : 'text-[#F75A5A]'
                            }`}>
                              {issue.severity}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">{issue.description}</p>
                          <p className="text-sm text-[#4ECFBF] font-medium mt-1">Suggestion: {issue.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Corrected Text */}
                {assessmentResult.corrected_text && (
                  <div className="mb-3">
                    <h3 className="text-sm font-medium text-slate-600">Corrected Text</h3>
                    <p className="text-slate-800 bg-slate-50 p-3 rounded-md mt-1 border border-slate-200 border-l-4 border-l-green-500 shadow-sm">
                      {assessmentResult.corrected_text}
                    </p>
                  </div>
                )}

                {/* Improvement Suggestions */}
                {assessmentResult.improvement_suggestions.length > 0 && (
                  <div className="mb-3">
                    <h3 className="text-sm font-medium text-slate-600 mb-1">Improvement Suggestions</h3>
                    <div className="bg-slate-50 p-3 rounded-md border border-slate-200 shadow-sm">
                      <ul className="list-disc pl-5 space-y-1">
                        {assessmentResult.improvement_suggestions.map((suggestion, i) => (
                          <li key={i} className="text-slate-700">{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Alternative Expressions */}
                {assessmentResult.level_appropriate_alternatives && assessmentResult.level_appropriate_alternatives.length > 0 && (
                  <div className="mb-3">
                    <h3 className="text-sm font-medium text-slate-600 mb-1">Alternative Expressions</h3>
                    <div className="bg-slate-50 p-3 rounded-md border border-slate-200 shadow-sm">
                      <div className="space-y-2">
                        {assessmentResult.level_appropriate_alternatives.map((alt, i) => (
                          <div key={i} className="bg-white p-2 rounded-md border border-slate-200 text-slate-700">{alt}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Bottom padding area to ensure content isn't cut off */}
                <div className="h-6"></div>
              </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Transcript Display */}
      <div ref={transcriptContainerRef} className="w-full p-4 bg-[#FFF8E1] rounded-lg border border-[#FFD63A]/50 min-h-[100px] max-h-[300px] overflow-y-auto">
        {transcript ? (
          <p className="text-slate-800">{transcript}</p>
        ) : (
          <p className="text-slate-500 italic">Your spoken text will appear here...</p>
        )}
      </div>
    </div>
  );
}
