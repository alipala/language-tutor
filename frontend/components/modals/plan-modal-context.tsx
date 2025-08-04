'use client';

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../lib/auth';
import { X, Check } from 'lucide-react';

// Modal state type
type PlanModalState = {
  open: boolean;
  planId?: string | null;
  period?: 'monthly' | 'annual' | null;
};

type PlanModalContextType = {
  openPlanModal: (opts?: { planId?: string; period?: 'monthly' | 'annual' }) => void;
  closePlanModal: () => void;
  modalState: PlanModalState;
};

const PlanModalContext = createContext<PlanModalContextType | undefined>(undefined);

export function PlanModalProvider({ children }: { children: ReactNode }) {
  const [modalState, setModalState] = useState<PlanModalState>({ open: false, planId: null, period: null });

  const openPlanModal = useCallback(
    (opts?: { planId?: string; period?: 'monthly' | 'annual' }) => {
      setModalState({
        open: true,
        planId: opts?.planId ?? null,
        period: opts?.period ?? null,
      });
    },
    []
  );

  const closePlanModal = useCallback(() => {
    setModalState({ open: false, planId: null, period: null });
  }, []);

  return (
    <PlanModalContext.Provider value={{ openPlanModal, closePlanModal, modalState }}>
      {children}
      <PlanModal />
    </PlanModalContext.Provider>
  );
}

export function usePlanModal() {
  const ctx = useContext(PlanModalContext);
  if (!ctx) throw new Error('usePlanModal must be used within PlanModalProvider');
  return ctx;
}

// The actual modal component
function PlanModal() {
  const { modalState, closePlanModal } = usePlanModal();
  const router = useRouter();
  const { user } = useAuth();
  
  // Initialize period based on modalState or default to monthly
  const [isAnnual, setIsAnnual] = useState(false);

  // Update period when modal state changes
  useEffect(() => {
    if (modalState.open) {
      setIsAnnual(modalState.period === 'annual');
    }
  }, [modalState.open, modalState.period]);

  // Only render if open
  if (!modalState.open) return null;

  // Handle plan selection
  const handlePlanSelect = (planId: string) => {
    const period = isAnnual ? 'annual' : 'monthly';
    
    // Store the current location for post-checkout redirect
    sessionStorage.setItem('checkoutReturnUrl', window.location.pathname);
    
    // Close modal first
    closePlanModal();
    
    // Navigate to checkout with plan details
    router.push(`/checkout?plan=${planId}&period=${period}`);
  };

  // Handle guest checkout
  const handleGuestCheckout = (planId: string) => {
    const period = isAnnual ? 'annual' : 'monthly';
    
    // Store the current location for post-checkout redirect
    sessionStorage.setItem('checkoutReturnUrl', window.location.pathname);
    
    // Close modal first
    closePlanModal();
    
    // Navigate to checkout as guest
    router.push(`/checkout?plan=${planId}&period=${period}`);
  };

  // Handle sign in
  const handleSignIn = () => {
    // Store plan selection for after login
    if (modalState.planId) {
      const period = isAnnual ? 'annual' : 'monthly';
      sessionStorage.setItem('selectedPlan', JSON.stringify({
        name: modalState.planId === 'fluency_builder' ? 'Fluency Builder' : 'Language Mastery',
        planId: modalState.planId,
        period: period
      }));
    }
    
    closePlanModal();
    router.push('/auth/login?from=pricing');
  };

  // Handle sign up
  const handleSignUp = () => {
    // Store plan selection for after signup
    if (modalState.planId) {
      const period = isAnnual ? 'annual' : 'monthly';
      sessionStorage.setItem('selectedPlan', JSON.stringify({
        name: modalState.planId === 'fluency_builder' ? 'Fluency Builder' : 'Language Mastery',
        planId: modalState.planId,
        period: period
      }));
    }
    
    closePlanModal();
    router.push('/auth/signup?from=pricing');
  };

  // If user is not authenticated, show auth options
  if (!user) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 md:p-4">
        <div className="bg-white rounded-xl md:rounded-2xl max-w-md w-full shadow-2xl">
          {/* Modal Header */}
          <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200">
            <h2 className="text-lg md:text-xl font-bold text-gray-900">Sign In or Create Account to Continue</h2>
            <button
              onClick={closePlanModal}
              className="text-gray-400 hover:text-gray-600 transition-colors p-1"
              aria-label="Close"
            >
              <X className="h-5 w-5 md:h-6 md:w-6" />
            </button>
          </div>

          {/* Modal Content */}
          <div className="p-4 md:p-6">
            <div className="text-center mb-6">
              <p className="text-gray-600 mb-4">
                {modalState.planId === 'fluency_builder' ? 'Fluency Builder' : 'Language Mastery'} - {modalState.period === 'annual' ? 'Annual' : 'Monthly'}
              </p>
              <p className="text-sm text-gray-500">
                Create an account or sign in to start your free trial and access premium features.
              </p>
            </div>

            <div className="space-y-3">
              <button
                onClick={handleSignUp}
                className="w-full py-3 px-4 bg-[#4ECFBF] text-white font-semibold rounded-lg hover:bg-[#3a9e92] transition-colors duration-300"
              >
                Create Account & Start Free Trial
              </button>
              
              <button
                onClick={handleSignIn}
                className="w-full py-3 px-4 bg-white text-[#4ECFBF] border-2 border-[#4ECFBF] font-semibold rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors duration-300"
              >
                Sign In
              </button>

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">or</span>
                </div>
              </div>

              <button
                onClick={() => handleGuestCheckout(modalState.planId || 'fluency_builder')}
                className="w-full py-3 px-4 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors duration-300"
              >
                Continue as Guest
              </button>
            </div>

            <p className="text-xs text-gray-500 text-center mt-4">
              Guest checkout: You'll create an account after payment to access your subscription.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 md:p-4">
      <div className="bg-white rounded-xl md:rounded-2xl max-w-3xl w-full max-h-[95vh] md:max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200">
          <h2 className="text-lg md:text-2xl font-bold text-gray-900">Choose Your Plan</h2>
          <button
            onClick={closePlanModal}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1"
            aria-label="Close"
          >
            <X className="h-5 w-5 md:h-6 md:w-6" />
          </button>
        </div>

        {/* Modal Content */}
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

          {/* Pricing Cards */}
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
  );
}
