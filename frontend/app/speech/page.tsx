'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Define the props interface to match the SpeechClient component
interface SpeechClientProps {
  language: string;
  level: string;
}

// Import the component with no SSR and specify the props type
const SpeechClient = dynamic<SpeechClientProps>(() => import('@/app/speech/speech-client'), {
  ssr: false
});

export default function SpeechPage() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Add a reference to track if we've already handled navigation
  const navigationHandledRef = useRef(false);
  
  useEffect(() => {
    // Prevent multiple executions of this effect
    if (navigationHandledRef.current) {
      console.log('Navigation already handled, skipping');
      return;
    }
    
    // Debug information about the current page
    console.log('Speech page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Check if we're in a refresh loop
    const refreshCountKey = 'speechPageRefreshCount';
    const refreshCount = parseInt(sessionStorage.getItem(refreshCountKey) || '0');
    console.log('Current refresh count:', refreshCount);
    
    if (refreshCount > 3) {
      console.log('Detected potential refresh loop, resetting session storage');
      // Clear only navigation-related items, not the language/level selections
      sessionStorage.removeItem(refreshCountKey);
      sessionStorage.removeItem('speechPageLoadTime');
      sessionStorage.removeItem('hasNavigatedFromSpeechPage');
    } else {
      // Increment refresh count
      sessionStorage.setItem(refreshCountKey, (refreshCount + 1).toString());
    }
    
    // Retrieve the selected language and level from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    const level = sessionStorage.getItem('selectedLevel');
    
    console.log('Retrieved from sessionStorage - language:', language, 'level:', level);
    
    // Mark that we've handled navigation
    navigationHandledRef.current = true;
    
    if (!language || !level) {
      // If no language or level is selected, redirect to language selection
      console.log('Missing language or level, redirecting to language selection');
      
      // Use direct window.location for reliable navigation in Railway
      // But wrap in setTimeout to ensure we don't interrupt the current render cycle
      setTimeout(() => {
        console.log('Executing navigation to language selection');
        window.location.href = '/language-selection';
      }, 100);
      return;
    }
    
    // If we have language and level, update the state
    setSelectedLanguage(language);
    setSelectedLevel(level);
    setIsLoading(false);
    
    // Reset refresh count when successfully loaded
    setTimeout(() => {
      sessionStorage.setItem(refreshCountKey, '0');
    }, 2000);
  }, []);
  
  // Add a separate effect for handling beforeunload events
  useEffect(() => {
    // Add an event listener to prevent page refreshes from F5 or browser refresh
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Only prevent unload if we're in a conversation
      const isInConversation = sessionStorage.getItem('isInConversation') === 'true';
      if (isInConversation) {
        console.log('User attempted to refresh during conversation');
        // Standard way to show a confirmation dialog before page unload
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };
    
    // Add the event listener
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Clean up the event listener when component unmounts
    return () => {
      console.log('Speech page component unmounting');
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  if (isLoading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
        <p className="mt-4 text-muted-foreground dark:text-slate-400">Loading conversation...</p>
      </main>
    );
  }

  return <SpeechClient language={selectedLanguage!} level={selectedLevel!} />;
}
