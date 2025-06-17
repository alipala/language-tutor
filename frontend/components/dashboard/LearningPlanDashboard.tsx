'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { LearningPlanCard } from './LearningPlanCard';
import { EmptyState } from './EmptyState';
import { getUserLearningPlans, LearningPlan } from '@/lib/learning-api';
import { getApiUrl } from '@/lib/api-utils';
import { 
  ChevronRight, 
  Loader2, 
  RefreshCw,
  TrendingUp,
  Award,
  Calendar,
  Mic,
  Target,
  Play
} from 'lucide-react';

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
  
  const [plans, setPlans] = useState<LearningPlan[]>([]);
  const [progressStats, setProgressStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

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
    <section className={`py-12 bg-gradient-to-br from-gray-50 to-white ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
          
          {/* Quick stats - removed minutes, kept sessions and streak */}
          {progressStats && (
            <div className="flex flex-wrap justify-center gap-6 text-sm">
              <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-full shadow-sm">
                <TrendingUp className="h-4 w-4 text-teal-500" />
                <span className="text-gray-600">
                  <strong className="text-gray-800">{progressStats.total_sessions}</strong> sessions
                </span>
              </div>
              
              {progressStats.current_streak > 0 && (
                <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-full shadow-sm">
                  <Award className="h-4 w-4 text-orange-500" />
                  <span className="text-gray-600">
                    <strong className="text-gray-800">{progressStats.current_streak}</strong> day streak
                  </span>
                </div>
              )}
            </div>
          )}
        </motion.div>

        {/* Plans Grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
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
          <Button
            onClick={() => {
              // Clear any previous selections and navigate to language selection
              sessionStorage.removeItem('selectedLanguage');
              sessionStorage.removeItem('selectedLevel');
              sessionStorage.removeItem('selectedTopic');
              sessionStorage.removeItem('assessmentMode');
              sessionStorage.removeItem('practiceMode');
              router.push('/language-selection');
            }}
            className="bg-gradient-to-r from-teal-500 via-blue-500 to-purple-500 hover:from-teal-600 hover:via-blue-600 hover:to-purple-600 text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 text-lg relative overflow-hidden"
          >
            {/* Animated gradient text effect */}
            <span className="relative z-10 flex items-center">
              <Play className="h-6 w-6 mr-3" />
              <span className="animated-gradient-text">Start New Learning Session</span>
              <ChevronRight className="h-5 w-5 ml-2" />
            </span>
            
            {/* Animated background shimmer */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 -translate-x-full animate-shimmer"></div>
          </Button>
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
    </section>
  );
};

export default LearningPlanDashboard;
