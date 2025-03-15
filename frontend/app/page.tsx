'use client';

import { useEffect, useState } from 'react';

// Export the main component
export default function Home() {
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Check if we're already on the language selection page to prevent loops
    const currentPath = window.location.pathname;
    if (currentPath.includes('language-selection')) return;
    
    // Check for reset parameter or if user explicitly navigated to home page
    const urlParams = new URLSearchParams(window.location.search);
    const shouldReset = urlParams.get('reset') === 'true';
    const isDirectHomeNavigation = document.referrer && !document.referrer.includes(window.location.host);
    
    // Clear session storage if reset is requested or direct navigation to home
    if (shouldReset || isDirectHomeNavigation) {
      console.log('Clearing session storage due to reset request or direct navigation');
      sessionStorage.clear();
    }
    
    // Check if we should continue to speech page
    const hasLanguage = sessionStorage.getItem('selectedLanguage');
    const hasLevel = sessionStorage.getItem('selectedLevel');
    
    if (hasLanguage && hasLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      window.location.href = '/speech';
      return;
    }
    
    // Add a small delay before redirecting for better UX
    const redirectTimer = setTimeout(() => {
      console.log('Redirecting from home page to language selection');
      // Use direct window.location for most reliable navigation in Railway
      window.location.href = '/language-selection';
    }, 300);
    
    return () => clearTimeout(redirectTimer);
  }, []);
  
  // Return loading state while redirecting
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
        <h1 className="text-2xl font-bold text-center">Language Tutor</h1>
        <p className="text-center text-gray-500 dark:text-gray-400">Redirecting to language selection...</p>
      </div>
    </div>
  );
}
