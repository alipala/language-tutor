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

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signup, googleLogin, error: authError, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessTransition, setShowSuccessTransition] = useState(false);
  const [signupEmail, setSignupEmail] = useState<string>('');
  const [showVerificationMessage, setShowVerificationMessage] = useState(false);
  
  // Check if user came from successful checkout
  const checkoutSuccess = searchParams.get('checkout') === 'success';
  const sessionId = searchParams.get('session_id');
  
  // Sync auth state with local state
  useEffect(() => {
    if (authError) {
      setError(authError);
    }
    setIsLoading(authLoading);
  }, [authError, authLoading]);

  const handleSignup = async (data: any) => {
    setIsLoading(true);
    setError(null);

    try {
      const { name, email, password } = data;
      console.log('Signing up with:', { name, email });
      
      // Perform signup - wait for it to complete
      await signup(name, email, password);
      
      // If this is a guest checkout success, try to link the subscription
      if (checkoutSuccess && sessionId) {
        console.log('[SIGNUP] Guest checkout detected, attempting to link subscription...');
        try {
          const token = localStorage.getItem('token');
          if (token) {
            const response = await fetch('/api/stripe/link-guest-subscription', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify({
                customer_email: email,
                session_id: sessionId
              }),
            });

            if (response.ok) {
              const result = await response.json();
              console.log('[SIGNUP] Successfully linked guest subscription:', result);
              
              // Redirect to profile with checkout success to show payment processing modal
              router.push('/profile?checkout=success');
              return;
            } else {
              const errorData = await response.json();
              console.error('[SIGNUP] Failed to link guest subscription:', errorData);
              // Continue with normal flow even if linking fails
            }
          }
        } catch (linkError) {
          console.error('[SIGNUP] Error linking guest subscription:', linkError);
          // Continue with normal flow even if linking fails
        }
      }
      
      // Store email for verification message
      setSignupEmail(email);
      
      // Show verification message instead of success transition
      setIsLoading(false);
      setShowVerificationMessage(true);
    } catch (err: any) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to create account. Please try again.');
      setIsLoading(false);
    }
  };

  // Handle Google signup success
  const handleGoogleSignupSuccess = async () => {
    console.log('Google signup successful, checking for selected plan...');
    
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

  // Handle Google signup error
  const handleGoogleSignupError = (err: Error) => {
    console.error('Google signup error:', err);
    setError(err.message || 'Google signup failed. Please try again.');
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

  const handleResendVerification = () => {
    // Navigate to resend verification page with email
    router.push(`/auth/resend-verification?email=${encodeURIComponent(signupEmail)}`);
  };

  return (
    <div className="auth-page">
      {/* Navigation Bar */}
      <NavBar />

      {/* Main content */}
      <main className="flex-grow flex items-center justify-center p-4 pt-20">
        {/* Checkout Success Banner */}
        {checkoutSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md mx-auto mb-6"
          >
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="text-green-800 font-medium">Payment Successful!</span>
              </div>
              <p className="text-green-700 text-sm">
                Complete your account setup below to access your subscription.
              </p>
            </div>
          </motion.div>
        )}

        {showVerificationMessage ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md mx-auto"
          >
            <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-6 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Check Your Email
              </h2>
              
              <p className="text-gray-600 mb-6">
                We've sent a verification link to <strong>{signupEmail}</strong>. 
                Please check your email and click the link to verify your account.
              </p>
              
              <div className="space-y-4">
                <button
                  onClick={handleResendVerification}
                  className="w-full bg-teal-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-teal-700 transition-colors"
                >
                  Resend Verification Email
                </button>
                
                <Link
                  href="/auth/login"
                  className="block w-full text-center text-teal-600 py-3 px-4 rounded-lg font-medium hover:bg-teal-50 transition-colors"
                >
                  Back to Login
                </Link>
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Tip:</strong> Check your spam folder if you don't see the email within a few minutes.
                </p>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="w-full max-w-md mx-auto">
            <AuthForm 
              type="signup"
              onSubmit={handleSignup}
              onGoogleAuth={handleGoogleSignupSuccess}
              isLoading={isLoading}
              error={error}
            />
          </div>
        )}
      </main>

      {/* Success Transition */}
      <AuthSuccessTransition
        isVisible={showSuccessTransition}
        type="signup"
        onComplete={handleTransitionComplete}
      />

      {/* We don't need background elements as we're using the global gradient background */}
    </div>
  );
}
