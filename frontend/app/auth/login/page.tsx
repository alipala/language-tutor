'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { AuthForm } from '@/components/auth-form';
import { AuthSuccessTransition } from '@/components/auth-success-transition';
import NavBar from '@/components/nav-bar';
import { motion } from 'framer-motion';
import '../auth-styles.css';
import './login-theme.css'; // Turquoise theme overrides

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, googleLogin, error: authError, loading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessTransition, setShowSuccessTransition] = useState(false);
  const [showVerificationToast, setShowVerificationToast] = useState(false);

  // Check for verification success parameter
  useEffect(() => {
    const verified = searchParams.get('verified');
    if (verified === 'true') {
      console.log('[LOGIN] Email verification success detected, showing toast');
      setShowVerificationToast(true);
      
      // Auto-hide toast after 5 seconds
      setTimeout(() => {
        setShowVerificationToast(false);
      }, 5000);
      
      // Clean up URL parameter
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
    }
  }, [searchParams]);

  // Sync auth state with local state
  useEffect(() => {
    if (authError) {
      setError(authError);
    }
    setIsLoading(authLoading);
  }, [authError, authLoading]);

  const handleLogin = async (data: any) => {
    setIsLoading(true);
    setError(null);

    try {
      const { email, password } = data;
      console.log('Logging in with:', email);
      
      // Check if there's a pending learning plan
      const pendingLearningPlanId = sessionStorage.getItem('pendingLearningPlanId');
      
      // Store navigation intent in sessionStorage before authentication
      sessionStorage.setItem('pendingRedirect', 'true');
      sessionStorage.setItem('redirectTarget', pendingLearningPlanId ? '/speech' : '/');
      sessionStorage.setItem('redirectAttemptTime', Date.now().toString());
      
      // Perform login - wait for it to complete
      await login(email, password);
      
      // Show success transition
      setIsLoading(false);
      setShowSuccessTransition(true);
    } catch (err: any) {
      console.error('Login error:', err);
      if (err.message === 'EMAIL_NOT_VERIFIED') {
        setError('Your email address has not been verified. Please check your email for a verification link or request a new one.');
        // Store email for potential resend
        sessionStorage.setItem('unverifiedEmail', email);
      } else {
        setError(err.message || 'Invalid email or password. Please try again.');
      }
      setIsLoading(false);
      // Clear navigation intent on error
      sessionStorage.removeItem('pendingRedirect');
      sessionStorage.removeItem('redirectTarget');
      sessionStorage.removeItem('redirectAttemptTime');
    }
  };

  // Handle Google login success
  const handleGoogleLoginSuccess = async () => {
    console.log('Google login successful, checking for selected plan...');
    
    // Check if user came from pricing page
    const selectedPlan = sessionStorage.getItem('selectedPlan');
    if (selectedPlan) {
      console.log('Found selected plan, redirecting to checkout...');
      const plan = JSON.parse(selectedPlan);
      sessionStorage.removeItem('selectedPlan'); // Clean up
      
      // Redirect to checkout with plan details
      const planId = plan.name === 'Fluency Builder' ? 'fluency_builder' : 'team_mastery';
      const period = plan.period === 'year' ? 'annual' : 'monthly';
      router.push(`/checkout?plan=${planId}&period=${period}`);
      return;
    }
    
    setShowSuccessTransition(true);
  };

  // Handle Google login error
  const handleGoogleLoginError = (err: Error) => {
    console.error('Google login error:', err);
    setError(err.message || 'Google login failed. Please try again.');
  };

  const handleTransitionComplete = () => {
    // Check if user came from pricing page
    const selectedPlan = sessionStorage.getItem('selectedPlan');
    if (selectedPlan) {
      const plan = JSON.parse(selectedPlan);
      sessionStorage.removeItem('selectedPlan'); // Clean up
      
      // Redirect to checkout with plan details
      const planId = plan.name === 'Fluency Builder' ? 'fluency_builder' : 'team_mastery';
      const period = plan.period === 'year' ? 'annual' : 'monthly';
      router.push(`/checkout?plan=${planId}&period=${period}`);
      return;
    }
    
    // Navigate to the appropriate page after transition completes
    const pendingLearningPlanId = sessionStorage.getItem('pendingLearningPlanId');
    const redirectTarget = pendingLearningPlanId ? '/speech' : '/';
    console.log(`Transition complete, navigating to ${redirectTarget}`);
    router.push(redirectTarget);
  };

  return (
    <div className="auth-page">
      {/* Navigation Bar */}
      <NavBar />

      {/* Main content */}
      <main className="flex-grow flex items-center justify-center p-4 pt-20">
        <AuthForm 
          type="login"
          onSubmit={handleLogin}
          onGoogleAuth={handleGoogleLoginSuccess}
          isLoading={isLoading}
          error={error}
        />
      </main>

      {/* Success Transition */}
      <AuthSuccessTransition
        isVisible={showSuccessTransition}
        type="login"
        onComplete={handleTransitionComplete}
      />

      {/* Email Verification Success Toast */}
      {showVerificationToast && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.9 }}
          className="fixed top-4 right-4 z-50 max-w-md"
        >
          <div className="bg-white border border-green-200 rounded-lg shadow-lg p-4 flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-900">Email Verified Successfully!</h3>
              <p className="text-sm text-gray-600 mt-1">
                Your email has been verified. You can now log in to your account.
              </p>
            </div>
            <button
              onClick={() => setShowVerificationToast(false)}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </motion.div>
      )}

      {/* We don't need background elements as we're using the global gradient background */}
    </div>
  );
}
