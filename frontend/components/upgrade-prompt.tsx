'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Crown, Star, Zap, ArrowRight, X, Check } from 'lucide-react';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';
import { usePlanModal } from '@/components/modals/plan-modal-context';

interface UpgradePromptProps {
  className?: string;
}

export const UpgradePrompt: React.FC<UpgradePromptProps> = ({ className = "" }) => {
  const { subscriptionStatus, loading, refreshSubscriptionStatus } = useSubscriptionStatus();
  const [dismissed, setDismissed] = useState(false);
  const [isAnnual, setIsAnnual] = useState(false);
  const router = useRouter();
  const { openPlanModal } = usePlanModal();

  // Check if user should see upgrade prompt
  const shouldShowUpgrade = () => {
    if (dismissed || loading) return false;
    
    // If no subscription status, show the prompt (likely free user)
    if (!subscriptionStatus) return true;
    
    // Don't show for premium users
    if (subscriptionStatus.plan === 'fluency_builder' || subscriptionStatus.plan === 'team_mastery') {
      return false;
    }
    
    // Show for free users
    if (subscriptionStatus.plan === 'try_learn') {
      return true;
    }
    
    // Show if user is running low on sessions/assessments
    if (subscriptionStatus.limits) {
      const { sessions_remaining, assessments_remaining } = subscriptionStatus.limits;
      return sessions_remaining <= 1 || assessments_remaining <= 0;
    }
    
    // Default to showing the prompt if we're unsure
    return true;
  };

  // Handle upgrade click - Show modal for better UX
  const handleUpgrade = () => {
    openPlanModal();
  };

  // Handle dismiss
  const handleDismiss = () => {
    setDismissed(true);
    // Store dismissal in session storage (resets on page refresh)
    sessionStorage.setItem('upgradePromptDismissed', 'true');
  };

  // Check if already dismissed in this session
  useEffect(() => {
    const isDismissed = sessionStorage.getItem('upgradePromptDismissed');
    if (isDismissed) {
      setDismissed(true);
    }
  }, []);

  // Don't show while loading or if conditions aren't met
  if (loading || !shouldShowUpgrade()) {
    return null;
  }

  const isFreePlan = subscriptionStatus?.plan === 'try_learn';
  const isLowUsage = subscriptionStatus?.limits && 
    (subscriptionStatus.limits.sessions_remaining <= 1 || subscriptionStatus.limits.assessments_remaining <= 0);

  return (
    <>
      <div className={`relative ${className}`}>
        {/* 🎯 COMPACT MOBILE-FIRST DESIGN */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl shadow-sm">
          {/* 🎯 IMPROVED DISMISS BUTTON */}
          <button
            onClick={handleDismiss}
            className="absolute top-3 right-3 z-10 w-6 h-6 bg-white/80 hover:bg-white rounded-full flex items-center justify-center text-gray-500 hover:text-gray-700 transition-all duration-200 shadow-sm hover:shadow-md"
            aria-label="Dismiss upgrade prompt"
          >
            <X className="h-3 w-3" />
          </button>

          {/* 📱 MOBILE LAYOUT (default) */}
          <div className="p-4 md:hidden">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Crown className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-blue-900 leading-tight">
                  🚀 Ready to Unlock More?
                </h3>
                <p className="text-xs text-blue-700 mt-1">
                  Try & Learn plan • 3 sessions/month
                </p>
              </div>
            </div>
            
            {/* Compact action buttons */}
            <div className="flex space-x-2">
              <button
                onClick={handleUpgrade}
                className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-xs font-semibold py-2 px-3 rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 flex items-center justify-center space-x-1"
              >
                <Zap className="h-3 w-3" />
                <span>Upgrade</span>
              </button>
              <div className="flex-1 text-center">
                <div className="text-xs text-gray-600 font-medium">Continue Free</div>
                <div className="text-xs text-gray-500">3 sessions left</div>
              </div>
            </div>
          </div>

          {/* 🖥️ ULTRA-COMPACT DESKTOP LAYOUT */}
          <div className="hidden md:block p-3">
            <div className="flex items-center justify-between max-w-2xl mx-auto">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Crown className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-blue-900">
                    🚀 Ready to Unlock More?
                  </h3>
                  <p className="text-xs text-blue-700">
                    Try & Learn • Upgrade for unlimited access
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <div className="text-center px-2">
                  <div className="text-xs font-medium text-gray-700">Continue Free</div>
                  <div className="text-xs text-gray-500">3 sessions left</div>
                </div>
                <button
                  onClick={handleUpgrade}
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold px-3 py-1.5 rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 flex items-center space-x-1 text-xs"
                >
                  <Zap className="h-3 w-3" />
                  <span>Upgrade</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </>
  );
};

export default UpgradePrompt;
