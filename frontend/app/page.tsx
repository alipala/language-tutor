'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Import the component with no SSR
const ClientHome = dynamic(() => import('./client-home'), {
  ssr: false
});

// Export the main component
export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to language selection page
    router.push('/language-selection');
  }, [router]);
  
  // Return loading state while redirecting
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      <p className="mt-4 text-muted-foreground dark:text-slate-400">Loading...</p>
    </div>
  );
}
