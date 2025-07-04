'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { LearningPlanCard } from './LearningPlanCard';
import { EmptyState } from './EmptyState';
import { getUserLearningPlans, LearningPlan } from '@/lib/learning-api';
import { getApiUrl } from '@/lib/api-utils';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';
import { 
  ChevronRight, 
  Loader2, 
  RefreshCw,
  TrendingUp,
  Award,
  Calendar,
  Mic,
  Target,
  Play,
  CheckCircle,
  X
} from 'lucide-react';
import UpgradePrompt from '@/components/upgrade-prompt';
import SessionModeModal from '@/components/session-mode-modal';

interface ProgressStats {
  total_sessions: number;
  total_minutes: number;
  current_streak: number;
  longest_streak: number;
  sessions_this_week: number;
  sessions_this_month: number;
}

interface LearningPlanDashboardProps {
  className?: string;
}

// Skeleton loading component
const DashboardSkeleton: React.FC = () => (
  <section className="py-12 bg-gradient-to-br from-gray-50 to-white">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-8">
        <div className="h-8 bg-gray-200 rounded-lg w-64 mx-auto mb-2 animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded-lg w-96 mx-auto animate-pulse"></div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-2xl shadow-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-4"></div>
            <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4"></div>
            <div className="space-y-2 mb-4">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
            <div className="space-y-2">
              <div className="h-10 bg-gray-200 rounded"></div>
              <div className="h-8 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export const LearningPlanDashboard: React.FC<LearningPlanDashboardProps> = ({ 
  className = "" 
}) => {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [plans, setPlans] = useState<LearningPlan[]>([]);
  const [progressStats, setProgressStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);
  const [showSessionModeModal, setShowSessionModeModal] = useState(false);
  
  // Use shared subscription status hook
  const { refreshSubscriptionStatus } = useSubscriptionStatus();

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    if (!user) return;
    
    try {
      setError(null);
      
      // Fetch learning plans and progress stats in parallel
      const [plansData, statsResponse] = await Promise.all([
        getUserLearningPlans(),
        fetch(`${getApiUrl()}/api/progress/stats`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        })
      ]);
      
      // Process stats response
      let statsData: ProgressStats | null = null;
      if (statsResponse.ok) {
        statsData = await statsResponse.json();
      }
      
      // Show max 3 plans on dashboard
      setPlans(plansData.slice(0, 3));
      setProgressStats(statsData);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Check for checkout success
  useEffect(() => {
    const checkoutSuccess = searchParams.get('checkout');
    if (checkoutSuccess === 'success') {
      setShowSuccessNotification(true);
      // Clear the URL parameter
      const url = new URL(window.location.href);
      url.searchParams.delete('checkout');
      window.history.replaceState({}, '', url.toString());
      
      // Clear the stored return URL
      sessionStorage.removeItem('checkoutReturnUrl');
      
      // Force refresh dashboard data and subscription status
      setTimeout(() => {
        fetchDashboardData();
        refreshSubscriptionStatus(); // Refresh subscription status across all components
      }, 2000); // Wait 2 seconds for webhook processing
      
      // Auto-hide notification after 8 seconds
      const hideTimer = setTimeout(() => {
        setShowSuccessNotification(false);
      }, 8000);
      
      // Cleanup timer on unmount
      return () => clearTimeout(hideTimer);
    }
  }, [searchParams]);

  // Initial data fetch
  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  // Refresh function
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
  };

  // Handle view all plans
  const handleViewAllPlans = () => {
    router.push('/profile');
  };

  // Handle session mode selection
  const handleSessionModeSelect = (mode: 'practice' | 'assessment') => {
    setShowSessionModeModal(false);
    
    // Clear any previous selections
    sessionStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLevel');
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('assessmentMode');
    sessionStorage.removeItem('practiceMode');
    sessionStorage.removeItem('assessmentCompleted');
    
    if (mode === 'practice') {
      router.push('/flow?mode=practice');
    } else if (mode === 'assessment') {
      router.push('/flow?mode=assessment');
    }
  };

  // Loading state
  if (loading) {
    return <DashboardSkeleton />;
  }

  // Empty state
  if (plans.length === 0) {
    return <EmptyState className={className} />;
  }

  // Error state
  if (error) {
    return (
      <section className={`py-12 bg-gradient-to-br from-gray-50 to-white ${className}`}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="text-red-500 mb-4">
              <TrendingUp className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Unable to Load Dashboard
            </h3>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button
              onClick={handleRefresh}
              className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={`pt-24 pb-12 bg-gradient-to-br from-gray-50 to-white ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Success Notification */}
        {showSuccessNotification && (
          <motion.div
            initial={{ opacity: 0, y: -50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -50, scale: 0.9 }}
            className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full mx-4"
          >
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-2xl shadow-2xl p-6 border border-green-400">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-lg mb-1">🎉 Subscription Activated!</h3>
                    <p className="text-green-100 text-sm">
                      Welcome to premium! Your subscription is now active and you have access to all features.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowSuccessNotification(false)}
                  className="text-white/80 hover:text-white transition-colors ml-2"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
        {/* Header */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            Your Learning Journey
          </h2>
          <p className="text-gray-600 mb-4">
            Continue your progress and achieve your language goals
          </p>
          
          {/* Quick stats - only show streak if exists */}
          {progressStats && progressStats.current_streak > 0 && (
            <div className="flex flex-wrap justify-center gap-6 text-sm">
              <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-full shadow-sm">
                <Award className="h-4 w-4 text-orange-500" />
                <span className="text-gray-600">
                  <strong className="text-gray-800">{progressStats.current_streak}</strong> day streak
                </span>
              </div>
            </div>
          )}
        </motion.div>

        {/* Upgrade Prompt for Free Users */}
        <UpgradePrompt className="mb-8" />

        {/* Plans Grid - Dynamic centering based on number of plans */}
        <motion.div
          className={`gap-6 mb-12 flex ${
            plans.length === 1 
              ? 'justify-center' 
              : plans.length === 2 
                ? 'justify-center flex-wrap max-w-4xl mx-auto' 
                : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
          }`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {plans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 * index }}
              className={plans.length <= 2 ? 'w-full max-w-sm' : ''}
            >
              <LearningPlanCard
                plan={plan}
                progressStats={progressStats}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* Main Action Button for Registered Users - moved to bottom */}
        <motion.div
          className="flex items-center justify-center mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <button
            onClick={() => setShowSessionModeModal(true)}
            className="bg-white hover:bg-white border-2 border-teal-500 hover:border-teal-400 text-teal-600 hover:text-teal-500 font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 relative overflow-hidden flex items-center justify-center
            
            /* Mobile-Optimized Design */
            px-8 py-4 text-lg min-w-[300px] h-14
            
            /* Desktop Enhancement */
            lg:px-12 lg:text-xl lg:min-w-[320px] lg:h-16"
          >
            {/* Animated gradient text effect */}
            <span className="relative z-10 flex items-center justify-center">
              <span className="animated-gradient-text">Start New Learning Session</span>
            </span>
            
            {/* Animated background shimmer */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-teal-100/30 to-transparent transform -skew-x-12 -translate-x-full animate-shimmer"></div>
          </button>
        </motion.div>

        {/* Motivational message */}
        {progressStats && progressStats.current_streak > 0 && (
          <motion.div
            className="mt-8 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <div className="bg-gradient-to-r from-orange-100 to-yellow-100 rounded-xl p-4 max-w-md mx-auto">
              <p className="text-orange-800 font-medium">
                🔥 Amazing! You're on a {progressStats.current_streak}-day streak!
              </p>
              <p className="text-orange-600 text-sm mt-1">
                Keep practicing to maintain your momentum
              </p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Session Mode Modal */}
      <SessionModeModal
        isOpen={showSessionModeModal}
        onClose={() => setShowSessionModeModal(false)}
        onSelectMode={handleSessionModeSelect}
      />
    </section>
  );
};

export default LearningPlanDashboard;
