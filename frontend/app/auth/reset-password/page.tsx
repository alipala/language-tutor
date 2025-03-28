'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { resetPassword, error: authError, loading: authLoading } = useAuth();
  const [token, setToken] = useState<string>('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Get token from URL on component mount
  useEffect(() => {
    const tokenFromUrl = searchParams?.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
    }
  }, [searchParams]);
  
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

    // Basic validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      setIsLoading(false);
      return;
    }

    try {
      console.log('Resetting password with token:', token);
      await resetPassword(token, password);
      
      // Show success message
      setIsLoading(false);
      setIsSuccess(true);
      
      // Redirect to login page after 3 seconds
      setTimeout(() => {
        // Use direct window.location.href for reliable navigation in Railway
        const fullUrl = `${window.location.origin}/auth/login`;
        window.location.href = fullUrl;
      }, 3000);
    } catch (err: any) {
      console.error('Password reset error:', err);
      setError(err.message || 'Failed to reset password. The link may be invalid or expired.');
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
              {isSuccess ? 'Password Reset Successful' : 'Reset Your Password'}
            </h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                {error}
              </div>
            )}
            
            {isSuccess ? (
              <div className="text-center">
                <div className="mb-4 mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-600 dark:text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Your password has been reset successfully. You will be redirected to the login page in a few seconds.
                </p>
                <Link href="/auth/login">
                  <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                    Go to Login
                  </Button>
                </Link>
              </div>
            ) : (
              <>
                {!token ? (
                  <div className="text-center">
                    <p className="text-red-600 dark:text-red-400 mb-6">
                      No reset token found. Please make sure you clicked the correct link from your email.
                    </p>
                    <Link href="/auth/forgot-password">
                      <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                        Request New Reset Link
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <>
                    <p className="mb-6 text-gray-600 dark:text-gray-300">
                      Enter your new password below.
                    </p>
                    
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <label htmlFor="password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                          New Password
                        </label>
                        <Input
                          id="password"
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="Enter new password"
                          required
                          className="w-full"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <label htmlFor="confirm-password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                          Confirm New Password
                        </label>
                        <Input
                          id="confirm-password"
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Confirm new password"
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
                            <span>Resetting...</span>
                          </>
                        ) : 'Reset Password'}
                      </Button>
                    </form>
                  </>
                )}
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
