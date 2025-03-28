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
      await signup(name, email, password);
      
      // Use direct window.location.href for reliable navigation in Railway
      console.log('Signup successful, redirecting to language selection');
      const fullUrl = `${window.location.origin}/language-selection`;
      window.location.href = fullUrl;
      
      // Fallback navigation with setTimeout to ensure it happens
      setTimeout(() => {
        if (window.location.pathname.includes('auth/signup')) {
          console.log('Fallback navigation triggered');
          window.location.href = fullUrl;
        }
      }, 2000);
    } catch (err: any) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to create account. Please try again.');
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Note: In a real implementation, you would get the Google OAuth token
      // For now, we'll just simulate it with a mock token
      const mockGoogleToken = 'mock-google-token';
      console.log('Google signup clicked');
      await googleLogin(mockGoogleToken);
      
      // Use direct window.location.href for reliable navigation in Railway
      const fullUrl = `${window.location.origin}/language-selection`;
      window.location.href = fullUrl;
    } catch (err: any) {
      console.error('Google signup error:', err);
      setError(err.message || 'Google signup failed. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col app-background">
      {/* Header with logo */}
      <motion.header 
        className="w-full p-4 md:p-6"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="container mx-auto">
          <Link href="/">
            <h1 className="text-2xl md:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-300 dark:to-purple-400">
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

      {/* Background elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <motion.div 
          className="absolute -top-[10%] -right-[10%] w-[35%] h-[35%] rounded-full bg-gradient-to-br from-purple-300/20 to-indigo-500/20 blur-3xl"
          animate={{
            x: [0, 30, 0],
            y: [0, -30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            repeatType: "reverse"
          }}
        />
        <motion.div 
          className="absolute -bottom-[10%] -left-[10%] w-[25%] h-[25%] rounded-full bg-gradient-to-tr from-indigo-300/20 to-purple-500/20 blur-3xl"
          animate={{
            x: [0, -20, 0],
            y: [0, 20, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            repeatType: "reverse"
          }}
        />
      </div>
    </div>
  );
}
