'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Crown, Star, Zap, ArrowRight, X, Check } from 'lucide-react';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';

interface UpgradePromptProps {
  className?: string;
}

export const UpgradePrompt: React.FC<UpgradePromptProps> = ({ className = "" }) => {
  const { subscriptionStatus, loading, refreshSubscriptionStatus } = useSubscriptionStatus();
  const [dismissed, setDismissed] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isAnnual, setIsAnnual] = useState(false);
  const router = useRouter();

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
    setShowModal(true);
  };

  // Handle plan selection
  const handlePlanSelect = (planId: string) => {
    const period = isAnnual ? 'annual' : 'monthly';
    
    // Store the current location for post-checkout redirect
    sessionStorage.setItem('checkoutReturnUrl', window.location.pathname);
    
    router.push(`/checkout?plan=${planId}&period=${period}`);
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

      {/* 🎯 COMPACT DESKTOP MODAL - Optimized Width */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 md:p-4">
          <div className="bg-white rounded-xl md:rounded-2xl max-w-3xl w-full max-h-[95vh] md:max-h-[90vh] overflow-y-auto">
            {/* Modal Header - Compact */}
            <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200">
              <h2 className="text-lg md:text-2xl font-bold text-gray-900">Choose Your Plan</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1"
              >
                <X className="h-5 w-5 md:h-6 md:w-6" />
              </button>
            </div>

            {/* Modal Content - Responsive Padding */}
            <div className="p-4 md:p-6">
              {/* Billing Toggle */}
              <div className="flex items-center justify-center mb-8">
                <span className={`text-lg font-medium transition-colors duration-300 ${!isAnnual ? 'text-gray-900' : 'text-gray-500'}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setIsAnnual(!isAnnual)}
                  className="mx-4 relative inline-flex h-8 w-14 items-center rounded-full bg-gray-200 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:ring-offset-2"
                  style={{ backgroundColor: isAnnual ? '#4ECFBF' : '#e5e7eb' }}
                >
                  <span
                    className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform duration-300 ${
                      isAnnual ? 'translate-x-7' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-lg font-medium transition-colors duration-300 ${isAnnual ? 'text-gray-900' : 'text-gray-500'}`}>
                  Annual
                </span>
                {isAnnual && (
                  <div className="ml-3 px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                    Save up to 17%
                  </div>
                )}
              </div>

              {/* 📱 MOBILE-OPTIMIZED PRICING CARDS */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                {/* Fluency Builder */}
                <div className="border-2 border-[#4ECFBF] rounded-xl md:rounded-2xl p-4 md:p-6 relative bg-gradient-to-br from-[#4ECFBF]/5 to-[#4ECFBF]/10 flex flex-col h-full">
                  <div className="absolute -top-2 md:-top-3 left-1/2 transform -translate-x-1/2">
                    <div className="bg-[#4ECFBF] text-white px-3 md:px-4 py-1 rounded-full text-xs md:text-sm font-bold">
                      MOST POPULAR
                    </div>
                  </div>
                  
                  <div className="text-center mb-4 md:mb-6">
                    <h3 className="text-lg md:text-xl font-bold text-gray-900 mb-2">Fluency Builder</h3>
                    <div className="mb-2">
                      {isAnnual && (
                        <div className="text-xs md:text-sm text-gray-500 line-through">$239.88</div>
                      )}
                      <div className="flex items-end justify-center">
                        <span className="text-2xl md:text-4xl font-bold text-gray-900">
                          {isAnnual ? '$199.99' : '$19.99'}
                        </span>
                        <span className="text-gray-600 ml-2 mb-1 text-sm md:text-base">
                          {isAnnual ? '/year' : '/month'}
                        </span>
                      </div>
                      {isAnnual && (
                        <div className="text-green-600 font-semibold text-xs md:text-sm">
                          Save $39.89 (17% off)
                        </div>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm md:text-base">Ideal for serious language learners</p>
                  </div>

                  <ul className="space-y-2 md:space-y-3 mb-4 md:mb-6 flex-grow">
                    {[
                      '🎉 7-day free trial included',
                      `${isAnnual ? '360' : '30'} practice sessions (5 minutes each) ${isAnnual ? 'annually' : 'monthly'}`,
                      `${isAnnual ? '24' : '2'} speaking assessments ${isAnnual ? 'annually' : 'monthly'}`,
                      'Advanced progress tracking',
                      'Learning plan progression',
                      'Achievement badges',
                      'All conversation topics + custom topics',
                      '🎤 Choose from multiple AI tutor voices',
                      'Conversation history & analytics',
                      'Priority email support'
                    ].map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="w-4 h-4 md:w-5 md:h-5 text-[#4ECFBF] mt-0.5 mr-2 md:mr-3 flex-shrink-0" />
                        <span className="text-gray-700 text-sm md:text-base">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-auto">
                    <button
                      onClick={() => handlePlanSelect('fluency_builder')}
                      className="w-full py-3 px-6 bg-[#4ECFBF] text-white font-semibold rounded-xl hover:bg-[#3a9e92] transition-colors duration-300"
                    >
                      Start Free Trial
                    </button>
                  </div>
                </div>

                {/* Language Mastery */}
                <div className="border-2 border-gray-200 rounded-xl md:rounded-2xl p-4 md:p-6 flex flex-col h-full">
                  <div className="text-center mb-4 md:mb-6">
                    <h3 className="text-lg md:text-xl font-bold text-gray-900 mb-2">Language Mastery</h3>
                    <div className="mb-2">
                      {isAnnual && (
                        <div className="text-xs md:text-sm text-gray-500 line-through">$479.88</div>
                      )}
                      <div className="flex items-end justify-center">
                        <span className="text-2xl md:text-4xl font-bold text-gray-900">
                          {isAnnual ? '$399.99' : '$39.99'}
                        </span>
                        <span className="text-gray-600 ml-2 mb-1 text-sm md:text-base">
                          {isAnnual ? '/year' : '/month'}
                        </span>
                      </div>
                      {isAnnual && (
                        <div className="text-green-600 font-semibold text-xs md:text-sm">
                          Save $79.89 (17% off)
                        </div>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm md:text-base">For advanced learners seeking fluency</p>
                  </div>

                  <ul className="space-y-2 md:space-y-3 mb-4 md:mb-6 flex-grow">
                    {[
                      '🎉 7-day free trial included',
                      'Unlimited practice sessions',
                      'Unlimited speaking assessments',
                      'Premium learning plans with advanced topics',
                      '🎤 Choose from multiple AI tutor voices',
                      '📊 Advanced analytics & detailed insights',
                      '🎯 Personalized learning recommendations',
                      '📝 Writing practice & correction',
                      '🌍 Cultural context & idiom explanations',
                      '⚡ Priority support & faster response times'
                    ].map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="w-4 h-4 md:w-5 md:h-5 text-[#4ECFBF] mt-0.5 mr-2 md:mr-3 flex-shrink-0" />
                        <span className="text-gray-700 text-sm md:text-base">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-auto">
                    <button
                      onClick={() => handlePlanSelect('team_mastery')}
                      className="w-full py-3 px-6 bg-white text-[#4ECFBF] border-2 border-[#4ECFBF] font-semibold rounded-xl hover:bg-[#4ECFBF] hover:text-white transition-colors duration-300"
                    >
                      Start Free Trial
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default UpgradePrompt;
