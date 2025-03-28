'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';

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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      console.log('Logging in with:', email);
      await login(email, password);
      
      // Use direct window.location.href for reliable navigation in Railway
      console.log('Login successful, redirecting to language selection');
      const fullUrl = `${window.location.origin}/language-selection`;
      window.location.href = fullUrl;
      
      // Fallback navigation with setTimeout to ensure it happens
      setTimeout(() => {
        if (window.location.pathname.includes('auth/login')) {
          console.log('Fallback navigation triggered');
          window.location.href = fullUrl;
        }
      }, 2000);
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Invalid email or password. Please try again.');
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Note: In a real implementation, you would get the Google OAuth token
      // For now, we'll just simulate it with a mock token
      const mockGoogleToken = 'mock-google-token';
      console.log('Google login clicked');
      await googleLogin(mockGoogleToken);
      
      // Use direct window.location.href for reliable navigation in Railway
      const fullUrl = `${window.location.origin}/language-selection`;
      window.location.href = fullUrl;
    } catch (err: any) {
      console.error('Google login error:', err);
      setError(err.message || 'Google login failed. Please try again.');
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
            <h2 className="text-2xl font-bold text-center mb-6 text-slate-900 dark:text-white">Sign In</h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                {error}
              </div>
            )}
            
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                  Email or phone number
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
              
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
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
                    <span>Signing in...</span>
                  </>
                ) : 'Sign In'}
              </Button>
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-slate-700 dark:text-slate-300">
                    Remember me
                  </label>
                </div>
                <Link href="/auth/forgot-password" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
                  Need help?
                </Link>
              </div>
            </form>
            
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white dark:bg-slate-800 text-gray-500 dark:text-gray-400">
                    Or continue with
                  </span>
                </div>
              </div>
              
              <div className="mt-6">
                <button
                  onClick={handleGoogleLogin}
                  className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600"
                >
                  <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" width="24" height="24">
                    <g transform="matrix(1, 0, 0, 1, 27.009001, -39.238998)">
                      <path fill="#4285F4" d="M -3.264 51.509 C -3.264 50.719 -3.334 49.969 -3.454 49.239 L -14.754 49.239 L -14.754 53.749 L -8.284 53.749 C -8.574 55.229 -9.424 56.479 -10.684 57.329 L -10.684 60.329 L -6.824 60.329 C -4.564 58.239 -3.264 55.159 -3.264 51.509 Z"/>
                      <path fill="#34A853" d="M -14.754 63.239 C -11.514 63.239 -8.804 62.159 -6.824 60.329 L -10.684 57.329 C -11.764 58.049 -13.134 58.489 -14.754 58.489 C -17.884 58.489 -20.534 56.379 -21.484 53.529 L -25.464 53.529 L -25.464 56.619 C -23.494 60.539 -19.444 63.239 -14.754 63.239 Z"/>
                      <path fill="#FBBC05" d="M -21.484 53.529 C -21.734 52.809 -21.864 52.039 -21.864 51.239 C -21.864 50.439 -21.724 49.669 -21.484 48.949 L -21.484 45.859 L -25.464 45.859 C -26.284 47.479 -26.754 49.299 -26.754 51.239 C -26.754 53.179 -26.284 54.999 -25.464 56.619 L -21.484 53.529 Z"/>
                      <path fill="#EA4335" d="M -14.754 43.989 C -12.984 43.989 -11.404 44.599 -10.154 45.789 L -6.734 42.369 C -8.804 40.429 -11.514 39.239 -14.754 39.239 C -19.444 39.239 -23.494 41.939 -25.464 45.859 L -21.484 48.949 C -20.534 46.099 -17.884 43.989 -14.754 43.989 Z"/>
                    </g>
                  </svg>
                  Sign in with Google
                </button>
              </div>
            </div>
            
            <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
              New to Language Tutor?{' '}
              <Link href="/auth/signup" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
                Sign up now
              </Link>
            </p>
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="w-full p-4 text-center text-xs text-gray-500 dark:text-gray-400">
        <p>
          This page is protected by reCAPTCHA to ensure you're not a bot.{' '}
          <a href="#" className="text-indigo-600 hover:underline dark:text-indigo-400">
            Learn more
          </a>
        </p>
      </footer>
    </div>
  );
}
