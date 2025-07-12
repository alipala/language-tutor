'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { X, Crown, Zap, Star } from 'lucide-react';

interface AuthRequiredModalProps {
  isOpen: boolean;
  onClose: () => void;
  planName: string;
  planPrice: string;
  planPeriod: string;
}

export const AuthRequiredModal: React.FC<AuthRequiredModalProps> = ({
  isOpen,
  onClose,
  planName,
  planPrice,
  planPeriod
}) => {
  const router = useRouter();

  const handleSignUp = () => {
    // Store plan selection for after signup
    sessionStorage.setItem('selectedPlan', JSON.stringify({
      name: planName,
      price: planPrice,
      period: planPeriod
    }));
    
    // Navigate to signup
    router.push('/auth/signup?from=pricing');
  };

  const handleLogin = () => {
    // Store plan selection for after login
    sessionStorage.setItem('selectedPlan', JSON.stringify({
      name: planName,
      price: planPrice,
      period: planPeriod
    }));
    
    // Navigate to login
    router.push('/auth/login?from=pricing');
  };

  const getPlanIcon = () => {
    switch (planName) {
      case 'Fluency Builder':
        return <Star className="w-8 h-8 text-blue-500" />;
      case 'Team Mastery':
        return <Crown className="w-8 h-8 text-purple-500" />;
      default:
        return <Zap className="w-8 h-8 text-teal-500" />;
    }
  };

  const getPlanColor = () => {
    switch (planName) {
      case 'Fluency Builder':
        return 'from-blue-500 to-indigo-600';
      case 'Team Mastery':
        return 'from-purple-500 to-pink-600';
      default:
        return 'from-teal-500 to-cyan-600';
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", duration: 0.5 }}
            className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden relative"
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Header with Gradient */}
            <div className={`bg-gradient-to-r ${getPlanColor()} p-8 text-white text-center relative overflow-hidden`}>
              {/* Background decoration */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
              
              <div className="relative z-10">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center mx-auto mb-4">
                  {getPlanIcon()}
                </div>
                <h2 className="text-2xl font-bold mb-2">Sign In or Create Account to Continue</h2>
                <p className="text-white/90 text-lg">
                  Sign in or create an account to start your <strong>7-day free trial</strong> of {planName} - no payment required now
                </p>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              {/* Plan Summary */}
              <div className="bg-gray-50 rounded-xl p-4 mb-6 text-center">
                <h3 className="font-semibold text-gray-800 mb-1">{planName}</h3>
                <div className="text-2xl font-bold text-gray-900">
                  {planPrice}
                  <span className="text-sm text-gray-600 ml-1">/{planPeriod}</span>
                </div>
              </div>

              {/* Benefits */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-800 mb-3">Why create an account?</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-3"></div>
                    Secure payment processing
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-3"></div>
                    Track your learning progress
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-3"></div>
                    Access your subscription anytime
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-3"></div>
                    Manage billing and preferences
                  </li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="space-y-4">
                {/* Sign In Button - Now equally prominent */}
                <div className="space-y-2">
                  <button
                    onClick={handleLogin}
                    className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-3 px-4 rounded-xl font-semibold hover:shadow-lg transition-all transform hover:scale-105 flex items-center justify-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-3.586l6.879-6.879A6 6 0 0121 9z" />
                    </svg>
                    <span>Sign In</span>
                  </button>
                  <p className="text-xs text-gray-600 text-center">
                    Already have an account? Quick access - proceed directly to checkout
                  </p>
                </div>

                {/* Create Account Button */}
                <div className="space-y-2">
                  <button
                    onClick={handleSignUp}
                    className={`w-full bg-gradient-to-r ${getPlanColor()} text-white py-3 px-4 rounded-xl font-semibold hover:shadow-lg transition-all transform hover:scale-105 flex items-center justify-center space-x-2`}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    <span>Create Account</span>
                  </button>
                  <p className="text-xs text-gray-600 text-center">
                    New user? Create account + email verification required
                  </p>
                </div>
              </div>

              {/* Trust Indicators */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center">
                    <svg className="w-4 h-4 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                    Secure & Encrypted
                  </div>
                  <div className="flex items-center">
                    <svg className="w-4 h-4 text-blue-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    30-Day Money Back
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default AuthRequiredModal;
