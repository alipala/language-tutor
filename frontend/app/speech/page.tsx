'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Define the props interface to match the SpeechClient component
interface SpeechClientProps {
  language: string;
  level: string;
}

// Import the component with no SSR and specify the props type
const SpeechClient = dynamic<SpeechClientProps>(() => import('./speech-client'), {
  ssr: false
});

export default function SpeechPage() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Retrieve the selected language and level from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    const level = sessionStorage.getItem('selectedLevel');
    
    console.log('Retrieved from sessionStorage - language:', language, 'level:', level);
    
    if (!language || !level) {
      // If no language or level is selected, redirect to language selection
      console.log('Missing language or level, redirecting to language selection');
      router.push('/language-selection');
      return;
    }
    
    setSelectedLanguage(language);
    setSelectedLevel(level);
    setIsLoading(false);
  }, [router]);

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
