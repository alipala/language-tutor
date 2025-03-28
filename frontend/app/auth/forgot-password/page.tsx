'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const { forgotPassword, error: authError, loading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Sync auth state with local state
  useEffect(() => {
    if (authError) {
      setError(authError);
    }
    setIsLoading(authLoading);
  }, [authError, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      console.log('Password reset requested for:', email);
      await forgotPassword(email);
      
      // Show success message
      setIsLoading(false);
      setIsSubmitted(true);
    } catch (err: any) {
      console.error('Password reset error:', err);
      setError(err.message || 'Failed to send reset link. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col app-background">
      {/* Header with logo */}
      <header className="w-full p-4 md:p-6">
        <div className="container mx-auto">
          <Link href="/">
            <h1 className="text-2xl md:text-3xl font-bold gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
              Language Tutor
            </h1>
          </Link>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-grow flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white dark:bg-slate-800 rounded-lg shadow-lg overflow-hidden">
          <div className="p-8">
            <h2 className="text-2xl font-bold text-center mb-6 text-slate-900 dark:text-white">
              {isSubmitted ? 'Check Your Email' : 'Forgot Password'}
            </h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                {error}
              </div>
            )}
            
            {isSubmitted ? (
              <div className="text-center">
                <div className="mb-4 mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-600 dark:text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  We've sent a password reset link to <strong>{email}</strong>. Please check your email and follow the instructions to reset your password.
                </p>
                <div className="flex flex-col space-y-3">
                  <Link href="/auth/login">
                    <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                      Return to Sign In
                    </Button>
                  </Link>
                  <button 
                    onClick={() => setIsSubmitted(false)}
                    className="text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    Try another email
                  </button>
                </div>
              </div>
            ) : (
              <>
                <p className="mb-6 text-gray-600 dark:text-gray-300">
                  Enter your email address and we'll send you a link to reset your password.
                </p>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="email" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      Email address
                    </label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email"
                      required
                      className="w-full"
                    />
                  </div>
                  
                  <Button 
                    type="submit" 
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                        <span>Sending...</span>
                      </>
                    ) : 'Send Reset Link'}
                  </Button>
                </form>
                
                <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
                  Remember your password?{' '}
                  <Link href="/auth/login" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
                    Sign in
                  </Link>
                </p>
              </>
            )}
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="w-full p-4 text-center text-xs text-gray-500 dark:text-gray-400">
        <p>
          Need help?{' '}
          <a href="#" className="text-indigo-600 hover:underline dark:text-indigo-400">
            Contact support
          </a>
        </p>
      </footer>
    </div>
  );
}
