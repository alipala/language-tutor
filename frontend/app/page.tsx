'use client';

import { useEffect } from 'react';

// Export the main component
export default function Home() {
  // Using a simple loading state for the initial render
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
        <h1 className="text-2xl font-bold text-center">Language Tutor</h1>
        <p className="text-center text-gray-500 dark:text-gray-400">Redirecting to language selection...</p>
      </div>
      <RedirectComponent />
    </div>
  );
}

// Separate component for redirection logic
function RedirectComponent() {
  useEffect(() => {
    // Ensure we're in the browser
    if (typeof window === 'undefined') return;
    
    // Check if we're already on the language selection page to prevent loops
    const currentPath = window.location.pathname;
    if (currentPath.includes('language-selection')) return;
    
    // Use a more reliable approach with a delay and a hard redirect
    const redirectTimer = setTimeout(() => {
      // Force a hard navigation instead of using Next.js router
      window.location.href = '/language-selection';
    }, 500);
    
    // Clean up timer if component unmounts
    return () => clearTimeout(redirectTimer);
  }, []);
  
  return null;
}
