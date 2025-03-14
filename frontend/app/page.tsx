'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Import the component with no SSR
const ClientHome = dynamic(() => import('./client-home'), {
  ssr: false
});

// Export the main component
export default function Home() {
  const router = useRouter();
  const hasRedirected = useRef(false);
  
  useEffect(() => {
    // Check if we're already on the language selection page to prevent loops
    const isLanguageSelectionPath = window.location.pathname.includes('language-selection');
    
    // Only redirect if we're not already on the language selection page and haven't redirected yet
    if (!hasRedirected.current && !isLanguageSelectionPath) {
      hasRedirected.current = true;
      
      // Use a timeout to ensure the router is fully initialized
      setTimeout(() => {
        router.replace('/language-selection');
      }, 100);
    }
  }, [router]);
  
  // Return loading state while redirecting
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      <p className="mt-4 text-muted-foreground dark:text-slate-400">Loading...</p>
    </div>
  );
}
