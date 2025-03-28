'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { AuthForm } from '@/components/auth-form';
import { motion } from 'framer-motion';

export default function LoginPage() {
  const router = useRouter();
  const { login, googleLogin, error: authError, loading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      
      // Store navigation intent in sessionStorage before authentication
      sessionStorage.setItem('pendingRedirect', 'true');
      sessionStorage.setItem('redirectTarget', '/language-selection');
      sessionStorage.setItem('redirectAttemptTime', Date.now().toString());
      
      // Perform login
      await login(email, password);
      
      // Force hard navigation to avoid client-side routing issues in Railway
      console.log('Login successful, forcing navigation to language selection');
      window.location.href = '/language-selection';
      
      // Safety net: if we're still on this page after 1.5 seconds, force navigation again
      setTimeout(() => {
        if (window.location.pathname.includes('auth/login')) {
          console.log('Safety net navigation triggered');
          window.location.href = '/language-selection';
        }
      }, 1500);
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

  // This function is now handled by the GoogleAuthButton component
  const handleGoogleLogin = async () => {
    // This is just a placeholder as the actual authentication is handled by the GoogleAuthButton component
    console.log('Google login button clicked');
    // We keep this function to maintain compatibility with the AuthForm component
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
          type="login"
          onSubmit={handleLogin}
          onGoogleAuth={handleGoogleLogin}
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
