'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { ProgressRing } from './ProgressRing';
import { LearningPlan } from '@/lib/learning-api';
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
  TrendingUp
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

  // Parse plan content
  const planContent = plan.plan_content || {};
  const goals = plan.goals || [];
  const weeklySchedule = planContent.weekly_schedule || [];
  const resources = planContent.resources || {};
  const milestones = planContent.milestones || [];

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
                className="w-full bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-medium py-3 rounded-xl transition-all duration-300 shadow-md hover-shadow-lg"
              >
                <Play className="h-4 w-4 mr-2" />
                Continue Learning
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
                  <div className="space-y-3">
                    {(() => {
                      // Calculate which weeks to show (current week and next week)
                      const sessionsPerWeek = 2;
                      let currentWeekNumber = 1;
                      
                      if (completedSessions > 0) {
                        currentWeekNumber = Math.floor((completedSessions - 1) / sessionsPerWeek) + 1;
                      }
                      
                      // Show current week and next week (max 2 weeks)
                      const weeksToShow = weeklySchedule.filter((week: any) => 
                        week.week >= currentWeekNumber && week.week <= currentWeekNumber + 1
                      );
                      
                      // If no weeks match (edge case), show first 2 weeks
                      const finalWeeksToShow = weeksToShow.length > 0 ? weeksToShow : weeklySchedule.slice(0, 2);
                      
                      return finalWeeksToShow.map((week: any, index: number) => {
                        // Calculate week progress based on individual week's sessions_completed
                        const sessionsPerWeek = 2;
                        const weekSessionsCompleted = week.sessions_completed || 0;
                        const weekTotalSessions = week.total_sessions || sessionsPerWeek;
                        
                        // Determine week status based on individual week data
                        let weekStatus = 'upcoming';
                        let weekProgress = 0;
                        
                        if (weekSessionsCompleted >= weekTotalSessions) {
                          // Week is fully completed
                          weekStatus = 'completed';
                          weekProgress = 100;
                        } else if (weekSessionsCompleted > 0) {
                          // Week is in progress
                          weekStatus = 'current';
                          weekProgress = (weekSessionsCompleted / weekTotalSessions) * 100;
                        } else {
                          // Week is upcoming
                          weekStatus = 'upcoming';
                          weekProgress = 0;
                        }
                        
                        const isCompleted = weekStatus === 'completed';
                        const isCurrent = weekStatus === 'current';
                      
                      return (
                        <div key={index} className={`rounded-lg p-3 border-2 ${
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
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full transition-all duration-500 ${
                                  isCompleted ? 'bg-green-500' :
                                  isCurrent ? 'bg-blue-500' :
                                  'bg-gray-300'
                                }`}
                                style={{ width: `${weekProgress}%` }}
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-1">
                            {week.activities.slice(0, 2).map((activity: string, actIndex: number) => (
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
                            {week.activities.length > 2 && (
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
                    {weeklySchedule.length > 2 && (
                      <div className="text-center text-sm text-gray-500">
                        +{weeklySchedule.length - 2} more weeks in your plan
                      </div>
                    )}
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
