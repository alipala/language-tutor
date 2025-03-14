'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Export the main component
export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Check if we're already on the language selection page to prevent loops
    const currentPath = window.location.pathname;
    if (currentPath.includes('language-selection')) return;
    
    // Try Next.js router first
    router.push('/language-selection');
    
    // Fallback to direct navigation after a delay if router doesn't work
    const fallbackTimer = setTimeout(() => {
      // If we're still on the home page, use direct navigation
      if (!window.location.pathname.includes('language-selection')) {
        window.location.href = '/language-selection';
      }
    }, 500);
    
    return () => clearTimeout(fallbackTimer);
  }, [router]);
  
  // Return loading state while redirecting
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      <p className="mt-4 text-muted-foreground dark:text-slate-400">Loading...</p>
    </div>
  );
}
