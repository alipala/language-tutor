'use client';

import { useState, useEffect } from 'react';
import { Crown, Star, Users, Zap, Clock, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

interface SubscriptionStatus {
  status: string | null;
  plan: string | null;
  period: string | null;
  limits: {
    sessions_remaining: number;
    assessments_remaining: number;
    sessions_limit: number;
    assessments_limit: number;
    is_unlimited: boolean;
  } | null;
  is_preserved: boolean;
  days_until_expiry: number | null;
}

interface MembershipBadgeProps {
  className?: string;
  showDetails?: boolean;
}

export default function MembershipBadge({ className = "", showDetails = true }: MembershipBadgeProps) {
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const fetchSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch('/api/stripe/subscription-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPlanConfig = (plan: string | null) => {
    switch (plan) {
      case 'try_learn':
        return {
          name: 'Try & Learn',
          icon: <Zap className="w-4 h-4" />,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          gradient: 'from-gray-100 to-gray-200',
          textColor: 'text-gray-800'
        };
      case 'fluency_builder':
        return {
          name: 'Fluency Builder',
          icon: <Star className="w-4 h-4" />,
          color: 'bg-gradient-to-r from-blue-500 to-purple-600 text-white border-blue-500',
          gradient: 'from-blue-500 to-purple-600',
          textColor: 'text-white'
        };
      case 'team_mastery':
        return {
          name: 'Team Mastery',
          icon: <Crown className="w-4 h-4" />,
          color: 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white border-yellow-400',
          gradient: 'from-yellow-400 to-orange-500',
          textColor: 'text-white'
        };
      default:
        return {
          name: 'Free',
          icon: <Zap className="w-4 h-4" />,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          gradient: 'from-gray-100 to-gray-200',
          textColor: 'text-gray-800'
        };
    }
  };

  const getStatusIndicator = () => {
    if (!subscriptionStatus) return null;

    const { status, is_preserved, days_until_expiry } = subscriptionStatus;

    if (is_preserved) {
      return (
        <div className="flex items-center text-amber-600 text-xs">
          <AlertTriangle className="w-3 h-3 mr-1" />
          <span>Preserved</span>
        </div>
      );
    }

    if (status === 'expired') {
      return (
        <div className="flex items-center text-red-600 text-xs">
          <Clock className="w-3 h-3 mr-1" />
          <span>Expired</span>
        </div>
      );
    }

    if (days_until_expiry !== null && days_until_expiry <= 7) {
      return (
        <div className="flex items-center text-amber-600 text-xs">
          <Clock className="w-3 h-3 mr-1" />
          <span>{days_until_expiry}d left</span>
        </div>
      );
    }

    if (status === 'active') {
      return (
        <div className="flex items-center text-green-600 text-xs">
          <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
          <span>Active</span>
        </div>
      );
    }

    if (status === 'canceling') {
      return (
        <div className="flex items-center text-orange-600 text-xs">
          <div className="w-2 h-2 bg-orange-500 rounded-full mr-1"></div>
          <span>Canceling</span>
        </div>
      );
    }

    if (status === 'canceled') {
      return (
        <div className="flex items-center text-red-600 text-xs">
          <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
          <span>Canceled</span>
        </div>
      );
    }

    return null;
  };

  const getUsageInfo = () => {
    if (!subscriptionStatus?.limits) return null;

    const { sessions_remaining, assessments_remaining, is_unlimited } = subscriptionStatus.limits;

    if (is_unlimited) {
      return (
        <div className="text-xs text-gray-600 mt-1">
          <div>Sessions: Unlimited</div>
          <div>Assessments: Unlimited</div>
        </div>
      );
    }

    return (
      <div className="text-xs text-gray-600 mt-1">
        <div>Sessions: {sessions_remaining >= 0 ? sessions_remaining : 0} left</div>
        <div>Assessments: {assessments_remaining >= 0 ? assessments_remaining : 0} left</div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`animate-pulse bg-gray-200 rounded-lg h-16 w-48 ${className}`}></div>
    );
  }

  if (!subscriptionStatus) {
    return null;
  }

  const planConfig = getPlanConfig(subscriptionStatus.plan);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`relative overflow-hidden rounded-lg border-2 ${planConfig.color} ${className}`}
    >
      {/* Background gradient for premium plans */}
      {subscriptionStatus.plan !== 'try_learn' && (
        <div className={`absolute inset-0 bg-gradient-to-r ${planConfig.gradient} opacity-90`}></div>
      )}
      
      <div className="relative p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {planConfig.icon}
            <div>
              <div className={`font-semibold text-sm ${planConfig.textColor}`}>
                {planConfig.name}
              </div>
              {subscriptionStatus.period && (
                <div className={`text-xs opacity-75 ${planConfig.textColor}`}>
                  {subscriptionStatus.period === 'monthly' ? 'Monthly' : 'Annual'}
                </div>
              )}
            </div>
          </div>
          
          {getStatusIndicator()}
        </div>

        {showDetails && getUsageInfo()}

        {/* Preservation message */}
        {subscriptionStatus.is_preserved && showDetails && (
          <div className="mt-2 text-xs text-amber-700 bg-amber-50 rounded p-2 border border-amber-200">
            <div className="font-medium">Learning Plan Preserved</div>
            <div>Your progress is safely stored. Resubscribe to continue!</div>
          </div>
        )}

        {/* Canceling warning */}
        {subscriptionStatus.status === 'canceling' && showDetails && (
          <div className="mt-2 text-xs text-orange-700 bg-orange-50 rounded p-2 border border-orange-200">
            <div className="font-medium">Subscription Canceling</div>
            <div>You can reactivate anytime before your billing period ends!</div>
          </div>
        )}

        {/* Expiry warning */}
        {subscriptionStatus.days_until_expiry !== null && 
         subscriptionStatus.days_until_expiry <= 7 && 
         subscriptionStatus.days_until_expiry > 0 && 
         showDetails && (
          <div className="mt-2 text-xs text-amber-700 bg-amber-50 rounded p-2 border border-amber-200">
            <div className="font-medium">Subscription Expiring Soon</div>
            <div>Renew now to keep your learning plan active!</div>
          </div>
        )}
      </div>

      {/* Premium plan sparkle effect */}
      {subscriptionStatus.plan === 'team_mastery' && (
        <div className="absolute top-1 right-1">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          >
            <Crown className="w-4 h-4 text-yellow-300" />
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}

// Compact version for navigation or smaller spaces
export function MembershipBadgeCompact({ className = "" }: { className?: string }) {
  return (
    <MembershipBadge 
      className={`w-auto ${className}`} 
      showDetails={false}
    />
  );
}

// Usage indicator component
export function UsageIndicator({ className = "" }: { className?: string }) {
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const fetchSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch('/api/stripe/subscription-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !subscriptionStatus?.limits) {
    return null;
  }

  const { sessions_remaining, assessments_remaining, sessions_limit, assessments_limit, is_unlimited } = subscriptionStatus.limits;

  if (is_unlimited) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center text-green-800">
          <Users className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium">Unlimited Access</span>
        </div>
      </div>
    );
  }

  const sessionsPercentage = sessions_limit > 0 ? (sessions_remaining / sessions_limit) * 100 : 0;
  const assessmentsPercentage = assessments_limit > 0 ? (assessments_remaining / assessments_limit) * 100 : 0;

  const getProgressColor = (percentage: number) => {
    if (percentage > 50) return 'bg-green-500';
    if (percentage > 20) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Practice Sessions</span>
            <span className="font-medium">{sessions_remaining}/{sessions_limit}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(sessionsPercentage)}`}
              style={{ width: `${Math.max(0, sessionsPercentage)}%` }}
            ></div>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Assessments</span>
            <span className="font-medium">{assessments_remaining}/{assessments_limit}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(assessmentsPercentage)}`}
              style={{ width: `${Math.max(0, assessmentsPercentage)}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
}
