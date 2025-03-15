'use client';

import { useEffect, useState } from 'react';

// Export the main component
export default function Home() {
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Log environment information for debugging
    console.log('Home page loaded at:', new Date().toISOString());
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Base path:', process.env.NEXT_PUBLIC_BASE_PATH || '/');
    
    // Add a flag to detect and prevent redirect loops
    const redirectAttemptKey = 'homePageRedirectAttempt';
    const redirectAttempts = parseInt(sessionStorage.getItem(redirectAttemptKey) || '0');
    console.log('Home page loaded, redirect attempts:', redirectAttempts);
    
    // If we've tried to redirect too many times, reset the counter and stay on this page
    if (redirectAttempts > 3) {
      console.log('Too many redirect attempts detected, resetting counter');
      sessionStorage.setItem(redirectAttemptKey, '0');
      // Clear any potentially problematic session data
      sessionStorage.removeItem('intentionalNavigation');
      // Display the page instead of redirecting
      setIsLoading(false);
      
      // Add a manual navigation button for the user
      // This will be shown in the UI when isLoading is false
      return;
    }
    
    // Increment the redirect attempt counter
    sessionStorage.setItem(redirectAttemptKey, (redirectAttempts + 1).toString());
    
    // Check if we're already on the language selection page to prevent loops
    const currentPath = window.location.pathname;
    if (currentPath.includes('language-selection')) {
      console.log('Already on language selection page, preventing redirect');
      setIsLoading(false);
      return;
    }
    
    // Check for Railway-specific path issues
    // In Railway, sometimes the path might have unexpected formats
    if (currentPath !== '/' && !currentPath.endsWith('/') && !currentPath.includes('.')) {
      console.log('Detected non-standard path in Railway:', currentPath);
      // Try to normalize the path
      if (!sessionStorage.getItem('pathNormalized')) {
        sessionStorage.setItem('pathNormalized', 'true');
        window.location.replace('/');
        return;
      }
    }
    
    // Debug information for Railway deployment
    console.log('Current pathname:', window.location.pathname);
    console.log('Current URL:', window.location.href);
    console.log('Document referrer:', document.referrer);
    
    // Check for reset parameter or if user explicitly navigated to home page
    const urlParams = new URLSearchParams(window.location.search);
    const shouldReset = urlParams.get('reset') === 'true';
    const isDirectHomeNavigation = document.referrer && !document.referrer.includes(window.location.host);
    
    // Clear session storage if reset is requested or direct navigation to home
    if (shouldReset || isDirectHomeNavigation) {
      console.log('Clearing session storage due to reset request or direct navigation');
      sessionStorage.clear();
      // Make sure to reset the redirect attempt counter too
      sessionStorage.setItem(redirectAttemptKey, '1');
    }
    
    // Check if we should continue to speech page
    const hasLanguage = sessionStorage.getItem('selectedLanguage');
    const hasLevel = sessionStorage.getItem('selectedLevel');
    
    if (hasLanguage && hasLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      window.location.href = '/speech';
      return;
    }
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // RAILWAY SPECIFIC: Add a flag to indicate we're in Railway environment
    const isRailway = window.location.hostname.includes('railway.app');
    console.log('Is Railway environment:', isRailway);
    
    // For Railway, use a more direct approach with full URL
    if (isRailway) {
      console.log('Using Railway-specific navigation approach');
      // Use the full URL to ensure proper navigation in Railway
      const fullUrl = `${window.location.origin}/language-selection`;
      console.log('Navigating to full URL:', fullUrl);
      
      // Try with a form submission approach which is more reliable in some environments
      const form = document.createElement('form');
      form.method = 'GET';
      form.action = fullUrl;
      document.body.appendChild(form);
      
      // Add a small delay to ensure the form is in the DOM
      setTimeout(() => {
        console.log('Submitting form for navigation');
        try {
          form.submit();
        } catch (e) {
          console.error('Form submission failed, falling back to direct navigation', e);
          // Fallback to direct navigation
          window.location.href = fullUrl;
        }
      }, 100);
      
      return;
    }
    
    // Standard navigation for non-Railway environments
    // Add a small delay before redirecting for better UX
    const redirectTimer = setTimeout(() => {
      console.log('Redirecting from home page to language selection');
      // Use direct window.location for most reliable navigation
      window.location.href = '/language-selection';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        console.log('Fallback navigation triggered');
        if (window.location.pathname === '/' || window.location.pathname === '') {
          console.log('Still on home page, using fallback navigation');
          // Try a different navigation method
          window.location.replace('/language-selection');
        }
      }, 1000);
      
      // Clear the fallback timer if the component unmounts
      return () => clearTimeout(fallbackTimer);
    }, 500);
    
    return () => {
      clearTimeout(redirectTimer);
      console.log('Home page navigation effect cleanup');
    };
  }, []);
  
  // Return loading state while redirecting or manual navigation option if we hit the redirect limit
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
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
                  // Clear session storage and redirect
                  sessionStorage.clear();
                  window.location.href = '/language-selection';
                }}
                className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all"
              >
                Start Learning
              </button>
              
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
  );
}
