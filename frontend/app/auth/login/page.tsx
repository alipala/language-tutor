'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { AuthForm } from '@/components/auth-form';
import { AuthSuccessTransition } from '@/components/auth-success-transition';
import { motion } from 'framer-motion';
import '../auth-styles.css';
import './login-theme.css'; // Turquoise theme overrides

export default function LoginPage() {
  const router = useRouter();
  const { login, googleLogin, error: authError, loading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessTransition, setShowSuccessTransition] = useState(false);

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
      sessionStorage.setItem('redirectTarget', pendingLearningPlanId ? '/speech' : '/language-selection');
      sessionStorage.setItem('redirectAttemptTime', Date.now().toString());
      
      // Perform login - wait for it to complete
      await login(email, password);
      
      // Show success transition
      setIsLoading(false);
      setShowSuccessTransition(true);
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Invalid email or password. Please try again.');
      setIsLoading(false);
      // Clear navigation intent on error
      sessionStorage.removeItem('pendingRedirect');
      sessionStorage.removeItem('redirectTarget');
      sessionStorage.removeItem('redirectAttemptTime');
    }
  };

  // Handle Google login success
  const handleGoogleLoginSuccess = async () => {
    console.log('Google login successful, showing transition');
    setShowSuccessTransition(true);
  };

  // Handle Google login error
  const handleGoogleLoginError = (err: Error) => {
    console.error('Google login error:', err);
    setError(err.message || 'Google login failed. Please try again.');
  };

  const handleTransitionComplete = () => {
    // Navigate to the appropriate page after transition completes
    const pendingLearningPlanId = sessionStorage.getItem('pendingLearningPlanId');
    const redirectTarget = pendingLearningPlanId ? '/speech' : '/language-selection';
    console.log(`Transition complete, navigating to ${redirectTarget}`);
    router.push(redirectTarget);
  };

  return (
    <div className="auth-page">
      {/* Header with logo */}
      <motion.header 
        className="w-full p-4 md:p-6"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="container mx-auto">
          <Link href="/">
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              Your Smart Language Coach
            </h1>
          </Link>
        </div>
      </motion.header>

      {/* Main content */}
      <main className="flex-grow flex items-center justify-center p-4">
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

      {/* We don't need background elements as we're using the global gradient background */}
    </div>
  );
}
