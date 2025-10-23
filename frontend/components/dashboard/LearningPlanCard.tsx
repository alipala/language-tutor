'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { createPortal } from 'react-dom';
import { Button } from '@/components/ui/button';
import { ProgressRing } from './ProgressRing';
import LearningPlanDetailsModal from './LearningPlanDetailsModal';
import { LearningPlan } from '@/lib/learning-api';
import { useLowMinutesAlert } from '@/hooks/useLowMinutesAlert';
import {
  Play,
  Eye,
  Flame,
  Clock,
  Target,
  BookOpen,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

interface LearningPlanCardProps {
  plan: LearningPlan;
  progressStats?: any;
  className?: string;
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
    'A1': 'bg-green-100 text-green-700',
    'A2': 'bg-blue-100 text-blue-700',
    'B1': 'bg-purple-100 text-purple-700',
    'B2': 'bg-orange-100 text-orange-700',
    'C1': 'bg-red-100 text-red-700',
    'C2': 'bg-gray-100 text-gray-700'
  };
  return colors[level.toUpperCase()] || 'bg-teal-100 text-teal-700';
};

export const LearningPlanCard: React.FC<LearningPlanCardProps> = ({
  plan,
  progressStats,
  className = ""
}) => {
  const router = useRouter();
  const [isHovered, setIsHovered] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  
  // Check low minutes status
  const { lowMinutesStatus } = useLowMinutesAlert();

  const progress = calculateProgress(plan);
  const completedSessions = plan.completed_sessions || 0;
  const totalSessions = plan.total_sessions || 24;
  const currentStreak = progressStats?.current_streak || 0;
  const isCompleted = progress >= 100;
  
  // Determine if we should show low minutes warning
  const hasLowMinutes = lowMinutesStatus?.has_low_minutes && !lowMinutesStatus?.is_unlimited;
  const minutesRemaining = lowMinutesStatus?.minutes_remaining || 0;
  const showCriticalWarning = hasLowMinutes && minutesRemaining <= 1;

  // Check if user has insufficient minutes for a session (< 5 minutes)
  const hasInsufficientMinutes = minutesRemaining < 5 && !lowMinutesStatus?.is_unlimited;

  const handleContinueLearning = () => {
    // Store plan context for speech practice
    sessionStorage.setItem('selectedLanguage', plan.language);
    sessionStorage.setItem('selectedLevel', plan.proficiency_level);
    sessionStorage.setItem('currentPlanId', plan.id);

    // Navigate to speech practice with plan ID parameter
    router.push(`/speech?plan=${plan.id}`);
  };

  const handleViewDetails = () => {
    // Open the details modal
    setShowDetailsModal(true);
  };

  return (
    <>
      <motion.div
        className={`relative bg-white rounded-2xl shadow-lg border border-gray-100 p-4 overflow-hidden ${className}`}
        whileHover={{ scale: 1.02, y: -4 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
      >
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-teal-50 via-blue-50 to-purple-50 opacity-60" />

        {/* Animated border on hover */}
        <motion.div
          className="absolute inset-0 rounded-2xl border-2 border-teal-400 opacity-0"
          animate={{ opacity: isHovered ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        />

        {/* Content */}
        <div className="relative z-10">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <motion.div
                className="text-3xl"
                animate={{ scale: isHovered ? 1.1 : 1 }}
                transition={{ duration: 0.3 }}
              >
                {getLanguageFlag(plan.language)}
              </motion.div>
              <div>
                <h3 className="font-bold text-gray-800 capitalize text-lg">
                  {plan.language}
                </h3>
                <span className={`inline-block text-xs px-3 py-1 rounded-full font-medium ${getLevelColor(plan.proficiency_level)}`}>
                  {plan.proficiency_level} Level
                </span>
              </div>
            </div>

            {/* Streak indicator */}
            {currentStreak > 0 && (
              <motion.div
                className="flex items-center space-x-1 bg-orange-100 px-3 py-1 rounded-full"
                animate={{ scale: isHovered ? 1.05 : 1 }}
                transition={{ duration: 0.3 }}
              >
                <Flame className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-medium text-orange-700">
                  {currentStreak}
                </span>
              </motion.div>
            )}
          </div>

          {/* Progress Ring */}
          <div className="flex justify-center mb-5">
            <ProgressRing
              percentage={progress}
              size={90}
              strokeWidth={6}
              animated={true}
            />
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4 mb-5">
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <Target className="h-4 w-4 text-teal-500" />
              </div>
              <div className="text-lg font-bold text-gray-800">
                {completedSessions}
              </div>
              <div className="text-xs text-gray-600">Sessions</div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <Clock className="h-4 w-4 text-blue-500" />
              </div>
              <div className="text-lg font-bold text-gray-800">
                {Math.round(progress)}%
              </div>
              <div className="text-xs text-gray-600">Complete</div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <BookOpen className="h-4 w-4 text-purple-500" />
              </div>
              <div className="text-lg font-bold text-gray-800">
                {totalSessions}
              </div>
              <div className="text-xs text-gray-600">Total</div>
            </div>
          </div>

          {/* Plan Title */}
          {plan.plan_content?.title && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 line-clamp-2">
                {plan.plan_content.title}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleContinueLearning}
              disabled={isCompleted || hasInsufficientMinutes}
              className={`w-full font-medium py-3 rounded-xl transition-all duration-300 shadow-md relative ${
                isCompleted || hasInsufficientMinutes
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : hasLowMinutes
                    ? 'bg-gradient-to-r from-orange-500 to-yellow-500 hover:from-orange-600 hover:to-yellow-600 text-white hover:shadow-lg'
                    : 'bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white hover:shadow-lg'
              }`}
            >
              {isCompleted ? (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Plan Completed
                </>
              ) : hasInsufficientMinutes ? (
                <>
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Insufficient Minutes
                  <span className="ml-2 text-xs">
                    (Need 5+ min)
                  </span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Continue Learning
                  {hasLowMinutes && minutesRemaining > 0 && (
                    <span className="ml-2 text-xs opacity-90">
                      ({Math.floor(minutesRemaining)} min left)
                    </span>
                  )}
                </>
              )}
            </Button>

            <Button
              onClick={handleViewDetails}
              variant="outline"
              className="w-full border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 py-2 rounded-xl transition-all duration-300"
            >
              <Eye className="h-4 w-4 mr-2" />
              View Details
            </Button>
          </div>

          {/* Progress indicator at bottom */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Progress</span>
              <span>{completedSessions}/{totalSessions} sessions</span>
            </div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-teal-500 to-blue-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 1, delay: 0.5 }}
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Learning Plan Details Modal - Rendered outside the card using portal */}
      {typeof window !== 'undefined' && showDetailsModal && createPortal(
        <LearningPlanDetailsModal
          isOpen={showDetailsModal}
          onClose={() => setShowDetailsModal(false)}
          plan={plan}
          progressStats={progressStats}
          onContinueLearning={() => {
            setShowDetailsModal(false);
            handleContinueLearning();
          }}
        />,
        document.body
      )}
    </>
  );
};

export default LearningPlanCard;
