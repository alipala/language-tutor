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
    if (!subscriptionStatus || dismissed || loading) return false;
    
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
    
    return false;
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
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6 shadow-lg">
          <div className="flex items-start space-x-4">
            {/* Icon */}
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Crown className="h-6 w-6 text-blue-600" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-bold text-blue-900 mb-2">
                🚀 Ready to Unlock More Learning?
              </h3>
              
              <p className="text-blue-800 mb-4">
                You're currently on the <strong>Try & Learn</strong> plan (3 sessions/month). 
                Upgrade to get unlimited practice sessions and advanced features!
              </p>


              {/* Two-column layout for options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Continue with Free */}
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <h4 className="font-semibold text-gray-800 mb-2">Continue Free</h4>
                  <ul className="text-sm text-gray-600 space-y-1 mb-3">
                    <li>• 3 practice sessions/month</li>
                    <li>• 1 assessment/month</li>
                    <li>• Basic progress tracking</li>
                  </ul>
                  <p className="text-xs text-gray-500">Perfect for trying out the platform</p>
                </div>

                {/* Upgrade Option */}
                <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg p-4 text-white relative overflow-hidden">
                  <div className="relative z-10">
                    <h4 className="font-semibold mb-2">Upgrade to Premium</h4>
                    <ul className="text-sm space-y-1 mb-3">
                      <li>• 30+ sessions/month</li>
                      <li>• Unlimited assessments</li>
                      <li>• Advanced analytics</li>
                    </ul>
                    <button
                      onClick={handleUpgrade}
                      className="bg-white text-blue-600 font-semibold px-4 py-2 rounded-lg hover:bg-gray-100 transition-all duration-300 text-sm flex items-center space-x-2 w-full justify-center"
                    >
                      <span>View Plans</span>
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="absolute -top-2 -right-2 w-16 h-16 bg-white/10 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Choose Your Plan</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
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

              {/* Pricing Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Fluency Builder */}
                <div className="border-2 border-[#4ECFBF] rounded-2xl p-6 relative bg-gradient-to-br from-[#4ECFBF]/5 to-[#4ECFBF]/10">
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <div className="bg-[#4ECFBF] text-white px-4 py-1 rounded-full text-sm font-bold">
                      MOST POPULAR
                    </div>
                  </div>
                  
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Fluency Builder</h3>
                    <div className="mb-2">
                      {isAnnual && (
                        <div className="text-sm text-gray-500 line-through">$239.88</div>
                      )}
                      <div className="flex items-end justify-center">
                        <span className="text-4xl font-bold text-gray-900">
                          {isAnnual ? '$199.99' : '$19.99'}
                        </span>
                        <span className="text-gray-600 ml-2 mb-1">
                          {isAnnual ? '/year' : '/month'}
                        </span>
                      </div>
                      {isAnnual && (
                        <div className="text-green-600 font-semibold text-sm">
                          Save $39.89 (17% off)
                        </div>
                      )}
                    </div>
                    <p className="text-gray-600">Ideal for serious language learners</p>
                  </div>

                  <ul className="space-y-3 mb-6">
                    {[
                      `${isAnnual ? '360' : '30'} practice sessions ${isAnnual ? 'annually' : 'monthly'}`,
                      `${isAnnual ? '24' : '2'} speaking assessments ${isAnnual ? 'annually' : 'monthly'}`,
                      'Advanced progress tracking',
                      'Learning plan progression',
                      'Achievement badges',
                      'All conversation topics + custom topics',
                      'Conversation history & analytics',
                      'Priority email support'
                    ].map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="w-5 h-5 text-[#4ECFBF] mt-0.5 mr-3 flex-shrink-0" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handlePlanSelect('fluency_builder')}
                    className="w-full py-3 px-6 bg-[#4ECFBF] text-white font-semibold rounded-xl hover:bg-[#3a9e92] transition-colors duration-300"
                  >
                    Get Started
                  </button>
                </div>

                {/* Team Mastery */}
                <div className="border-2 border-gray-200 rounded-2xl p-6">
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Team Mastery</h3>
                    <div className="mb-2">
                      {isAnnual && (
                        <div className="text-sm text-gray-500 line-through">$479.88</div>
                      )}
                      <div className="flex items-end justify-center">
                        <span className="text-4xl font-bold text-gray-900">
                          {isAnnual ? '$399.99' : '$39.99'}
                        </span>
                        <span className="text-gray-600 ml-2 mb-1">
                          {isAnnual ? '/year per user' : '/month per user'}
                        </span>
                      </div>
                      {isAnnual && (
                        <div className="text-green-600 font-semibold text-sm">
                          Save $79.89 (17% off)
                        </div>
                      )}
                    </div>
                    <p className="text-gray-600">For teams and organizations</p>
                  </div>

                  <ul className="space-y-3 mb-6">
                    {[
                      'Unlimited practice sessions',
                      'Unlimited assessments',
                      'Premium learning plans',
                      'Advanced analytics',
                      'Priority support',
                      'Team collaboration features',
                      'API access & LMS integrations',
                      'SSO & admin controls'
                    ].map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="w-5 h-5 text-[#4ECFBF] mt-0.5 mr-3 flex-shrink-0" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handlePlanSelect('team_mastery')}
                    className="w-full py-3 px-6 bg-white text-[#4ECFBF] border-2 border-[#4ECFBF] font-semibold rounded-xl hover:bg-[#4ECFBF] hover:text-white transition-colors duration-300"
                  >
                    Get Started
                  </button>
                  
                  <p className="text-xs text-gray-500 mt-3 text-center">
                    Minimum 5 users
                  </p>
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
