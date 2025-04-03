'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { AuthForm } from '@/components/auth-form';
import { motion } from 'framer-motion';

export default function SignupPage() {
  const router = useRouter();
  const { signup, googleLogin, error: authError, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
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
      
      // Check if there's a pending learning plan
      const pendingLearningPlanId = sessionStorage.getItem('pendingLearningPlanId');
      
      // Store navigation intent in sessionStorage before authentication
      sessionStorage.setItem('pendingRedirect', 'true');
      sessionStorage.setItem('redirectTarget', pendingLearningPlanId ? '/speech' : '/language-selection');
      sessionStorage.setItem('redirectAttemptTime', Date.now().toString());
      
      // Perform signup
      await signup(name, email, password);
      
      // Force hard navigation to avoid client-side routing issues in Railway
      const redirectTarget = pendingLearningPlanId ? '/speech' : '/language-selection';
      console.log(`Signup successful, forcing navigation to ${redirectTarget}`);
      window.location.href = redirectTarget;
      
      // Safety net: if we're still on this page after 1.5 seconds, force navigation again
      setTimeout(() => {
        if (window.location.pathname.includes('auth/signup')) {
          const safetyRedirectTarget = pendingLearningPlanId ? '/speech' : '/language-selection';
          console.log('Safety net navigation triggered to', safetyRedirectTarget);
          window.location.href = safetyRedirectTarget;
        }
      }, 1500);
    } catch (err: any) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to create account. Please try again.');
      setIsLoading(false);
      // Clear navigation intent on error
      sessionStorage.removeItem('pendingRedirect');
      sessionStorage.removeItem('redirectTarget');
      sessionStorage.removeItem('redirectAttemptTime');
    }
  };

  // This function is now handled by the GoogleAuthButton component
  const handleGoogleSignup = async () => {
    // This is just a placeholder as the actual authentication is handled by the GoogleAuthButton component
    console.log('Google signup button clicked');
    // We keep this function to maintain compatibility with the AuthForm component
  };

  return (
    <div className="min-h-screen flex flex-col">
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
              Language Tutor
            </h1>
          </Link>
        </div>
      </motion.header>

      {/* Main content */}
      <main className="flex-grow flex items-center justify-center p-4">
        <AuthForm 
          type="signup"
          onSubmit={handleSignup}
          onGoogleAuth={handleGoogleSignup}
          isLoading={isLoading}
          error={error}
        />
      </main>

      {/* We don't need background elements as we're using the global gradient background */}
    </div>
  );
}
