'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/nav-bar';

// Export the main component
export default function Home() {
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Wait for auth to be checked
    if (authLoading) return;
    
    // Log environment information for debugging
    console.log('Home page loaded at:', new Date().toISOString());
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Base path:', process.env.NEXT_PUBLIC_BASE_PATH || '/');
    console.log('Auth status:', user ? 'Logged in' : 'Not logged in');
    
    // Get current location info for debugging
    console.log('Current pathname:', window.location.pathname);
    console.log('Current URL:', window.location.href);
    console.log('Full origin:', window.location.origin);
    
    // RAILWAY SPECIFIC: Check for the unusual routing situation
    // where URL is language-selection but we're still on the home page component
    if (window.location.pathname === '/language-selection') {
      console.log('URL is /language-selection but still on home page component - force reload');
      
      // We're in a strange state where the URL is language-selection but we're 
      // still on the home page component. Let's try to recover by forcing a reload
      // which should properly render the language selection component
      const fullUrl = `${window.location.origin}/language-selection`;
      window.location.replace(fullUrl);
      return;
    }
    
    // Check for reset parameter
    const urlParams = new URLSearchParams(window.location.search);
    const shouldReset = urlParams.get('reset') === 'true';
    
    if (shouldReset) {
      console.log('Reset parameter detected, clearing session storage');
      sessionStorage.clear();
    }
    
    // Check if we should continue to a specific page based on stored data or user preferences
    const hasLanguage = sessionStorage.getItem('selectedLanguage') || (user?.preferred_language || null);
    const hasLevel = sessionStorage.getItem('selectedLevel') || (user?.preferred_level || null);
    
    // If user is logged in, use their preferences if available
    if (user) {
      console.log('User is logged in:', user.email);
      
      // Store user preferences in session if not already there
      if (user.preferred_language && !sessionStorage.getItem('selectedLanguage')) {
        console.log('Using user preferred language:', user.preferred_language);
        sessionStorage.setItem('selectedLanguage', user.preferred_language);
      }
      
      if (user.preferred_level && !sessionStorage.getItem('selectedLevel')) {
        console.log('Using user preferred level:', user.preferred_level);
        sessionStorage.setItem('selectedLevel', user.preferred_level);
      }
    }
    
    if (hasLanguage && hasLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      window.location.href = '/speech';
      return;
    } else if (hasLanguage) {
      console.log('Found existing language, redirecting to level selection');
      window.location.href = '/level-selection';
      return;
    }
    
    // Check if we're on the root path and should show the welcome page
    if (window.location.pathname === '/' || window.location.pathname === '') {
      // On root path, show the UI instead of auto-redirecting
      console.log('On root path, showing welcome page');
      setIsLoading(false);
      return;
    }
    
    // If we're not on a recognized path, normalize to home page
    console.log('Unrecognized path, normalizing to home');
    window.location.replace('/');
  }, [user, authLoading]);
  
  // Return loading state while redirecting or manual navigation option if we hit the redirect limit
  return (
    <div className="min-h-screen flex flex-col app-background">
      <NavBar />
      <div className="flex-grow flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center justify-center space-y-4">
        <h1 className="text-4xl font-bold text-center gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">Language Tutor</h1>
        
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
            <p className="text-center text-gray-500 dark:text-gray-400">Redirecting to language selection...</p>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-6 mt-8">
            <p className="text-center text-gray-600 dark:text-gray-300 max-w-md">
              Welcome to Language Tutor! Choose a language and level to start practicing your conversation skills with an AI tutor.
            </p>
            
            <div className="flex flex-col space-y-4 w-full max-w-xs">
              <button 
                onClick={() => {
                  try {
                    // Show loading state
                    setIsLoading(true);
                    setError(null);
                    
                    // Clear any existing session data except user preferences
                    // We don't want to clear the entire sessionStorage as it might contain user data
                    if (!user) {
                      sessionStorage.clear();
                    }
                    
                    // Log the navigation attempt
                    console.log('Start Learning button clicked at:', new Date().toISOString());
                    console.log('Current pathname before navigation:', window.location.pathname);
                    console.log('User authenticated:', user ? 'Yes' : 'No');
                    
                    // Use the most direct and reliable navigation approach
                    // By using the full URL with origin, we ensure proper navigation in Railway
                    const fullUrl = `${window.location.origin}/language-selection`;
                    console.log('Navigating to:', fullUrl);
                    
                    // IMPORTANT: For Railway, use direct window.location.href navigation
                    // This bypasses Next.js client-side routing which may be causing issues
                    window.location.href = fullUrl;
                    
                    // Set a fallback timer to detect navigation failures
                    setTimeout(() => {
                      if (window.location.pathname === '/' || window.location.pathname === '') {
                        console.error('Navigation failed, still on homepage after timeout');
                        setIsLoading(false);
                        setError('Navigation to language selection failed. Please try again.');
                      }
                    }, 3000);
                  } catch (e) {
                    console.error('Navigation error:', e);
                    setIsLoading(false);
                    setError(`Navigation error: ${e instanceof Error ? e.message : 'Unknown error'}`);
                  }
                }}
                className="w-full app-button flex items-center justify-center"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    <span>Navigating...</span>
                  </>
                ) : (
                  <>
                    <span>Start Learning</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-1" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </button>
              
              {!user && (
                <div className="flex flex-col space-y-2 mt-4">
                  <button
                    onClick={() => {
                      const fullUrl = `${window.location.origin}/auth/login`;
                      window.location.href = fullUrl;
                    }}
                    className="w-full py-2 px-4 border border-indigo-500 text-indigo-600 rounded-md hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 flex items-center justify-center"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => {
                      const fullUrl = `${window.location.origin}/auth/signup`;
                      window.location.href = fullUrl;
                    }}
                    className="w-full py-2 px-4 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-600 dark:text-gray-200 dark:hover:bg-slate-700 flex items-center justify-center"
                  >
                    Create Account
                  </button>
                </div>
              )}
              
              {parseInt(sessionStorage.getItem('homePageRedirectAttempt') || '0') > 2 && (
                <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg mt-4">
                  <p className="text-sm text-amber-700 dark:text-amber-400">
                    We detected navigation issues. If you're having trouble, try clearing your browser cache or using a different browser.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
