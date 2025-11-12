'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ProgressRing } from './ProgressRing';
import { LearningPlan, getUserFlashcardSets, FlashcardSet, reviewFlashcard } from '@/lib/learning-api';
import FlashcardViewer from '@/components/FlashcardViewer';
import {
  X,
  Calendar,
  Target,
  Clock,
  BookOpen,
  CheckCircle,
  Circle,
  Play,
  Award,
  TrendingUp,
  Book,
  Brain
} from 'lucide-react';

interface LearningPlanDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: LearningPlan;
  progressStats?: any;
  onContinueLearning: () => void;
}

// Language flag mapping
const getLanguageFlag = (language: string): string => {
  const flags: Record<string, string> = {
    'english': '🇺🇸',
    'spanish': '🇪🇸',
    'french': '🇫🇷',
    'german': '🇩🇪',
    'dutch': '🇳🇱',
    'portuguese': '🇵🇹',
    'italian': '🇮🇹',
    'chinese': '🇨🇳',
    'japanese': '🇯🇵',
    'korean': '🇰🇷'
  };
  return flags[language.toLowerCase()] || '🌍';
};

// Calculate progress from plan data
const calculateProgress = (plan: LearningPlan): number => {
  if (plan.progress_percentage !== undefined) {
    return plan.progress_percentage;
  }
  
  const completed = plan.completed_sessions || 0;
  const total = plan.total_sessions || 24;
  
  return Math.min((completed / total) * 100, 100);
};

// Get level color
const getLevelColor = (level: string): string => {
  const colors: Record<string, string> = {
    'A1': 'bg-green-100 text-green-700 border-green-200',
    'A2': 'bg-blue-100 text-blue-700 border-blue-200',
    'B1': 'bg-purple-100 text-purple-700 border-purple-200',
    'B2': 'bg-orange-100 text-orange-700 border-orange-200',
    'C1': 'bg-red-100 text-red-700 border-red-200',
    'C2': 'bg-gray-100 text-gray-700 border-gray-200'
  };
  return colors[level.toUpperCase()] || 'bg-teal-100 text-teal-700 border-teal-200';
};

export const LearningPlanDetailsModal: React.FC<LearningPlanDetailsModalProps> = ({
  isOpen,
  onClose,
  plan,
  progressStats,
  onContinueLearning
}) => {
  const progress = calculateProgress(plan);
  const completedSessions = plan.completed_sessions || 0;
  const totalSessions = plan.total_sessions || 24;
  const currentStreak = progressStats?.current_streak || 0;
  const isCompleted = progress >= 100;

  // Parse plan content
  const planContent = plan.plan_content || {};
  const goals = plan.goals || [];
  const weeklySchedule = planContent.weekly_schedule || [];
  const resources = planContent.resources || {};
  const milestones = planContent.milestones || [];

  // Pagination state for weekly schedule
  const [currentPage, setCurrentPage] = React.useState(0);
  const weeksPerPage = 2;
  const totalPages = Math.ceil(weeklySchedule.length / weeksPerPage);

  // Flashcard state
  const [flashcardSets, setFlashcardSets] = useState<FlashcardSet[]>([]);
  const [selectedFlashcardSet, setSelectedFlashcardSet] = useState<FlashcardSet | null>(null);
  const [showFlashcards, setShowFlashcards] = useState(false);
  const [loadingFlashcards, setLoadingFlashcards] = useState(false);

  // Load flashcard sets when modal opens
  useEffect(() => {
    if (isOpen) {
      loadFlashcardSets();
    }
  }, [isOpen]);

  const loadFlashcardSets = async () => {
    try {
      setLoadingFlashcards(true);
      const sets = await getUserFlashcardSets();
      
      // 🔥 CRITICAL FIX: Filter flashcard sets to only show those belonging to this learning plan
      // Learning plan session IDs have the format: learning_plan_{plan_id}_{session_number}_{uuid}
      const planFlashcardSets = sets.filter(set => {
        if (!set.session_id) return false;
        
        // Check if this is a learning plan flashcard set
        if (!set.session_id.startsWith('learning_plan_')) return false;
        
        // Extract the plan ID from session_id (format: learning_plan_{plan_id}_{session_number}_{uuid})
        const parts = set.session_id.split('_');
        if (parts.length < 3) return false;
        
        // The plan_id is at index 2 (learning_plan_{plan_id}_...)
        const flashcardPlanId = parts[2];
        
        // Only include flashcards that belong to this specific learning plan
        return flashcardPlanId === plan.id;
      });
      
      console.log(`[FLASHCARD_FILTER] Found ${sets.length} total flashcard sets`);
      console.log(`[FLASHCARD_FILTER] Filtered to ${planFlashcardSets.length} sets for plan ${plan.id}`);
      
      setFlashcardSets(planFlashcardSets);
    } catch (error) {
      console.error('Error loading flashcard sets:', error);
    } finally {
      setLoadingFlashcards(false);
    }
  };

  const handleFlashcardReview = async (flashcardId: string, correct: boolean) => {
    try {
      await reviewFlashcard({ flashcard_id: flashcardId, correct });
      // Optionally refresh flashcard data or update local state
    } catch (error) {
      console.error('Error reviewing flashcard:', error);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4"
      style={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 99999
      }}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)'
        }}
      />

      {/* Modal */}
      <div
        className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden mx-auto"
        style={{
          position: 'relative',
          zIndex: 1,
          backgroundColor: 'white',
          borderRadius: '1rem',
          maxWidth: '56rem',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'hidden',
          margin: '0 auto',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }}
      >
        {/* Header */}
        <div 
          className="bg-gradient-to-r from-teal-500 to-blue-500 px-6 py-4 text-white relative"
          style={{
            background: 'linear-gradient(to right, #14b8a6, #3b82f6)',
            padding: '1rem 1.5rem',
            color: 'white',
            position: 'relative'
          }}
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
            style={{
              position: 'absolute',
              top: '1rem',
              right: '1rem',
              padding: '0.5rem',
              borderRadius: '9999px',
              border: 'none',
              backgroundColor: 'transparent',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            <X className="h-5 w-5" />
          </button>
          
          <div className="flex items-center space-x-4">
            <div className="text-4xl">
              {getLanguageFlag(plan.language)}
            </div>
            <div>
              <h2 className="text-2xl font-bold capitalize">
                {plan.language} Learning Plan
              </h2>
              <div className="flex items-center space-x-3 mt-1">
                <span className={`inline-block text-xs px-3 py-1 rounded-full font-medium border ${getLevelColor(plan.proficiency_level)}`}>
                  {plan.proficiency_level} Level
                </span>
                {currentStreak > 0 && (
                  <div className="flex items-center space-x-1 bg-white bg-opacity-20 px-2 py-1 rounded-full">
                    <Award className="h-3 w-3" />
                    <span className="text-xs font-medium">{currentStreak} day streak</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div 
          className="p-6 overflow-y-auto"
          style={{
            padding: '1.5rem',
            overflowY: 'auto',
            maxHeight: 'calc(90vh - 120px)'
          }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Progress & Stats */}
            <div className="lg:col-span-1 space-y-6">
              {/* Progress Ring */}
              <div className="text-center">
                <ProgressRing 
                  percentage={progress} 
                  size={120}
                  strokeWidth={8}
                  animated={true}
                />
                <p className="text-sm text-gray-600 mt-2">Overall Progress</p>
              </div>

              {/* Stats Cards */}
              <div className="space-y-3">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Target className="h-4 w-4 text-teal-500" />
                      <span className="text-sm font-medium text-gray-700">Sessions</span>
                    </div>
                    <span className="text-lg font-bold text-gray-800">
                      {completedSessions}/{totalSessions}
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-blue-500" />
                      <span className="text-sm font-medium text-gray-700">Practice Time</span>
                    </div>
                    <span className="text-lg font-bold text-gray-800">
                      {Math.round((progressStats?.total_minutes || 0))} min
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="h-4 w-4 text-purple-500" />
                      <span className="text-sm font-medium text-gray-700">This Week</span>
                    </div>
                    <span className="text-lg font-bold text-gray-800">
                      {progressStats?.sessions_this_week || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Continue Learning Button */}
              <Button
                onClick={() => {
                  // Store plan context for speech practice
                  sessionStorage.setItem('selectedLanguage', plan.language);
                  sessionStorage.setItem('selectedLevel', plan.proficiency_level);
                  sessionStorage.setItem('currentPlanId', plan.id);
                  
                  // Call the onContinueLearning callback
                  onContinueLearning();
                }}
                disabled={isCompleted}
                className={`w-full font-medium py-3 rounded-xl transition-all duration-300 shadow-md ${
                  isCompleted 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white hover:shadow-lg'
                }`}
              >
                {isCompleted ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Plan Completed
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Continue Learning
                  </>
                )}
              </Button>
            </div>

            {/* Right Column - Plan Details */}
            <div className="lg:col-span-2 space-y-6">
              {/* Plan Title & Overview */}
              {(planContent.title || planContent.overview) && (
                <div>
                  {planContent.title && (
                    <h3 className="text-xl font-bold text-gray-800 mb-2">
                      {planContent.title}
                    </h3>
                  )}
                  {planContent.overview && (
                    <p className="text-gray-600">
                      {planContent.overview}
                    </p>
                  )}
                </div>
              )}

              {/* Learning Goals */}
              {goals.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <Target className="h-5 w-5 mr-2 text-teal-500" />
                    Learning Goals
                  </h4>
                  <div className="space-y-2">
                    {goals.map((goal: string, index: number) => (
                      <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                        <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-gray-700">{goal}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Weekly Schedule with Progress */}
              {weeklySchedule.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <Calendar className="h-5 w-5 mr-2 text-blue-500" />
                    Weekly Schedule Preview
                  </h4>
                  
                  {/* Pagination Controls */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm text-gray-600">
                      Showing weeks {currentPage * weeksPerPage + 1}-{Math.min((currentPage + 1) * weeksPerPage, weeklySchedule.length)} of {weeklySchedule.length}
                    </span>
                    <div className="flex items-center space-x-2">
                      <button 
                        onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                        disabled={currentPage === 0}
                        className="p-1 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      <span className="text-sm text-gray-600">{currentPage + 1}/{totalPages}</span>
                      <button 
                        onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                        disabled={currentPage >= totalPages - 1}
                        className="p-1 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  {/* Weekly Schedule Grid - Fixed Layout */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(() => {
                      // Sort weeks by week number to ensure proper order
                      const sortedWeeks = [...weeklySchedule].sort((a, b) => (a.week || 0) - (b.week || 0));
                      
                      // Get weeks for current page
                      const startIndex = currentPage * weeksPerPage;
                      const endIndex = startIndex + weeksPerPage;
                      const currentWeeks = sortedWeeks.slice(startIndex, endIndex);
                      
                      return currentWeeks.map((week: any, index: number) => {
                        // Calculate week progress based on sessions completed
                        const weekSessionsCompleted = week.sessions_completed || 0;
                        const weekTotalSessions = week.total_sessions || 2;
                        const weekProgress = weekTotalSessions > 0 ? (weekSessionsCompleted / weekTotalSessions) * 100 : 0;
                        
                        // Determine week status based on completion
                        const isCompleted = weekSessionsCompleted >= weekTotalSessions;
                        const isCurrent = weekSessionsCompleted > 0 && weekSessionsCompleted < weekTotalSessions;
                        const isUpcoming = weekSessionsCompleted === 0;
                      
                        return (
                          <div key={index} className={`rounded-lg p-3 border-2 overflow-hidden ${
                            isCompleted ? 'bg-green-50 border-green-200' :
                            isCurrent ? 'bg-blue-50 border-blue-200' :
                            'bg-gray-50 border-gray-200'
                          }`}>
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <span className={`text-sm font-medium ${
                                  isCompleted ? 'text-green-700' :
                                  isCurrent ? 'text-blue-700' :
                                  'text-gray-600'
                                }`}>
                                  Week {week.week}
                                </span>
                                {isCompleted && (
                                  <CheckCircle className="h-4 w-4 text-green-500" />
                                )}
                                {isCurrent && (
                                  <div className="flex items-center space-x-1">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                    <span className="text-xs text-blue-600 font-medium">Current</span>
                                  </div>
                                )}
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full truncate max-w-[200px] ${
                                isCompleted ? 'text-green-600 bg-green-100' :
                                isCurrent ? 'text-blue-600 bg-blue-100' :
                                'text-gray-600 bg-gray-100'
                              }`}>
                                {week.focus}
                              </span>
                            </div>
                            
                            {/* Week Progress Bar */}
                            <div className="mb-2">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className={`${
                                  isCompleted ? 'text-green-600' :
                                  isCurrent ? 'text-blue-600' :
                                  'text-gray-500'
                                }`}>
                                  Progress
                                </span>
                                <span className={`${
                                  isCompleted ? 'text-green-600' :
                                  isCurrent ? 'text-blue-600' :
                                  'text-gray-500'
                                }`}>
                                  {isCompleted ? `${weekTotalSessions}/${weekTotalSessions}` : isCurrent ? `${weekSessionsCompleted}/${weekTotalSessions}` : `0/${weekTotalSessions}`} sessions
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                <div 
                                  className={`h-2 rounded-full transition-all duration-500 ${
                                    isCompleted ? 'bg-green-500' :
                                    isCurrent ? 'bg-blue-500' :
                                    'bg-gray-300'
                                  }`}
                                  style={{ width: `${Math.min(weekProgress, 100)}%` }}
                                />
                              </div>
                            </div>
                            
                            <div className="space-y-1">
                              {week.activities && week.activities.slice(0, 2).map((activity: string, actIndex: number) => (
                                <div key={actIndex} className="flex items-center space-x-2">
                                  <Circle className={`h-2 w-2 flex-shrink-0 ${
                                    isCompleted ? 'text-green-500' :
                                    isCurrent ? 'text-blue-500' :
                                    'text-gray-400'
                                  }`} />
                                  <span className={`text-xs ${
                                    isCompleted ? 'text-green-700' :
                                    isCurrent ? 'text-blue-700' :
                                    'text-gray-600'
                                  }`}>
                                    {activity}
                                  </span>
                                </div>
                              ))}
                              {week.activities && week.activities.length > 2 && (
                                <div className={`text-xs ${
                                  isCompleted ? 'text-green-600' :
                                  isCurrent ? 'text-blue-600' :
                                  'text-gray-500'
                                }`}>
                                  +{week.activities.length - 2} more activities
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>
              )}

              {/* Resources */}
              {resources && (typeof resources === 'object') && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <BookOpen className="h-5 w-5 mr-2 text-purple-500" />
                    Learning Resources
                  </h4>
                  <div className="bg-purple-50 rounded-lg p-4">
                    {Array.isArray(resources) ? (
                      <div className="space-y-1">
                        {resources.slice(0, 3).map((resource: string, index: number) => (
                          <div key={index} className="flex items-center space-x-2">
                            <Circle className="h-2 w-2 text-purple-500 flex-shrink-0" />
                            <span className="text-sm text-gray-700">{resource}</span>
                          </div>
                        ))}
                        {resources.length > 3 && (
                          <div className="text-xs text-purple-600">
                            +{resources.length - 3} more resources
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-4">
                        {(resources as any).apps && (resources as any).apps.length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-gray-700">Apps:</span>
                            <div className="mt-1 space-y-1">
                              {(resources as any).apps.slice(0, 2).map((app: string, index: number) => (
                                <div key={index} className="text-xs text-gray-600">• {app}</div>
                              ))}
                            </div>
                          </div>
                        )}
                        {(resources as any).books && (resources as any).books.length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-gray-700">Books:</span>
                            <div className="mt-1 space-y-1">
                              {(resources as any).books.slice(0, 2).map((book: string, index: number) => (
                                <div key={index} className="text-xs text-gray-600">• {book}</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Milestones */}
              {milestones.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <Award className="h-5 w-5 mr-2 text-yellow-500" />
                    Milestones
                  </h4>
                  <div className="space-y-2">
                    {milestones.slice(0, 3).map((milestone: any, index: number) => (
                      <div key={index} className="bg-yellow-50 rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <span className="text-sm font-medium text-gray-800">{milestone.milestone}</span>
                          <span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full">
                            {milestone.timeline}
                          </span>
                        </div>
                        {milestone.assessment && (
                          <p className="text-xs text-gray-600 mt-1">{milestone.assessment}</p>
                        )}
                      </div>
                    ))}
                    {milestones.length > 3 && (
                      <div className="text-center text-sm text-gray-500">
                        +{milestones.length - 3} more milestones
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* AI-Generated Flashcards */}
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                  <Brain className="h-5 w-5 mr-2 text-indigo-500" />
                  AI-Generated Flashcards
                </h4>
                <div className="bg-indigo-50 rounded-lg p-4">
                  <p className="text-sm text-gray-700 mb-3">
                    Review flashcards automatically generated from your speaking sessions to reinforce learning and improve retention.
                  </p>

                  {loadingFlashcards ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
                      <span className="ml-2 text-sm text-gray-600">Loading flashcards...</span>
                    </div>
                  ) : flashcardSets.length > 0 ? (
                    <div className="space-y-3">
                      {flashcardSets.slice(0, 3).map((set) => (
                        <div key={set.id} className="bg-white rounded-lg p-3 border border-indigo-200">
                          <div className="flex items-center justify-between">
                            <div>
                              <h5 className="font-medium text-gray-800">{set.title}</h5>
                              <p className="text-xs text-gray-600">{set.total_cards} cards • {set.language} • {set.level}</p>
                            </div>
                            <Button
                              size="sm"
                              onClick={() => setSelectedFlashcardSet(set)}
                              className="bg-indigo-600 hover:bg-indigo-700"
                            >
                              <Book className="h-3 w-3 mr-1" />
                              Study
                            </Button>
                          </div>
                        </div>
                      ))}
                      {flashcardSets.length > 3 && (
                        <p className="text-xs text-indigo-600 text-center">
                          +{flashcardSets.length - 3} more flashcard sets available
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <Book className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">
                        Complete speaking sessions to generate AI-powered flashcards
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Plan Creation Date */}
              <div className="text-xs text-gray-500 pt-4 border-t border-gray-200">
                Created on {new Date(plan.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningPlanDetailsModal;
