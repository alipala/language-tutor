'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
// Sound effects temporarily disabled
// import { useAudio } from '@/lib/useAudio';

interface Language {
  code: string;
  name: string;
  flagSrc: string;
}

export default function LanguageSelection() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // Sound effects temporarily disabled
  // const { playSelectionSound, playSuccessSound } = useAudio();

  const languages: Language[] = [
    {
      code: 'dutch',
      name: 'Dutch',
      flagSrc: '/images/netherlands-flag.svg',
    },
    {
      code: 'english',
      name: 'English',
      flagSrc: '/images/uk-flag.svg',
    },
  ];

  // Add a useEffect to handle page initialization and react to state changes
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Log debug information
    console.log('Language selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    console.log('Full origin:', window.location.origin);
    
    // RAILWAY SPECIFIC: Check if we're in Railway environment
    const isRailway = window.location.hostname.includes('railway.app');
    console.log('Is Railway environment:', isRailway);
    
    // Normalize URL if needed to ensure consistent path format
    const currentPath = window.location.pathname;
    if (isRailway) {
      // Different path handling for Railway
      // If URL doesn't end with /language-selection (accounting for trailing slashes)
      const normalizedPath = currentPath.endsWith('/') 
        ? currentPath.slice(0, -1) 
        : currentPath;
        
      if (normalizedPath !== '/language-selection') {
        // Only fix the path if we're not already on the correct one
        console.log('Path appears incorrect, normalizing to /language-selection');
        window.location.replace('/language-selection');
        return;
      }
    }
    
    // Check if we should redirect based on existing state
    const storedLanguage = sessionStorage.getItem('selectedLanguage');
    const storedLevel = sessionStorage.getItem('selectedLevel');
    
    // Handle case where this is an initial direct load of the language selection page
    // This is the expected behavior: user coming from home page
    if (!storedLanguage && !storedLevel) {
      console.log('Fresh visit to language selection page, allowing normal flow');
      // Let the normal component render proceed
      return;
    }
    
    // If we have both language and level, we should go to speech page
    if (storedLanguage && storedLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      // Use the most direct approach with a delay to avoid navigation race conditions
      setTimeout(() => {
        const fullUrl = `${window.location.origin}/speech`;
        console.log('Navigating to speech page:', fullUrl);
        window.location.href = fullUrl;
      }, 300);
      return;
    }
    
    // If we have just language selected, we should go to level selection
    if (storedLanguage && !storedLevel) {
      console.log('Found existing language, redirecting to level selection');
      // Use the most direct approach with a delay to avoid navigation race conditions
      setTimeout(() => {
        const fullUrl = `${window.location.origin}/level-selection`;
        console.log('Navigating to level selection page:', fullUrl);
        window.location.href = fullUrl;
      }, 300);
      return;
    }
  }, []);
  
  // No need for handleStartOver since this is the starting screen

  const handleLanguageSelect = (languageCode: string) => {
    // Set loading state while navigating
    setIsLoading(true);
    setSelectedLanguage(languageCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLanguage', languageCode);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Navigating to level selection with language:', languageCode);
    
    // RAILWAY SPECIFIC: Detect Railway environment
    const isRailway = window.location.hostname.includes('railway.app');
    console.log('Is Railway environment:', isRailway);
    
    // For Railway, use a more direct approach with full URL
    if (isRailway) {
      console.log('Using Railway-specific navigation approach');
      // Use the full URL to ensure proper navigation in Railway
      const fullUrl = `${window.location.origin}/level-selection`;
      console.log('Navigating to full URL:', fullUrl);
      
      // Use direct location replacement which is most reliable
      window.location.replace(fullUrl);
      
      // Fallback with hard refresh if needed
      setTimeout(() => {
        if (window.location.pathname.includes('language-selection')) {
          console.log('Still on language selection page, forcing hard refresh to:', fullUrl);
          window.location.href = fullUrl + '?t=' + new Date().getTime();
        }
      }, 1000);
      
      return;
    }
    
    // Standard navigation for non-Railway environments
    // Use a direct window.location approach with a small delay
    // This bypasses any client-side routing issues
    setTimeout(() => {
      console.log('Executing navigation to level selection');
      window.location.href = '/level-selection';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        console.log('Checking if fallback navigation is needed');
        if (window.location.pathname.includes('language-selection')) {
          console.log('Still on language selection page, using fallback navigation');
          window.location.replace('/level-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 300);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600 dark:from-blue-400 dark:to-violet-400">
            Choose Your Language
          </h1>
          <p className="text-slate-600 dark:text-slate-300 mt-3 text-lg">
            Select a language to start your learning journey
          </p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className={`
                  relative overflow-hidden flex flex-col items-center justify-center p-8 rounded-2xl 
                  transition-all duration-300 transform hover:scale-102 hover:shadow-xl
                  ${
                    selectedLanguage === language.code
                      ? 'bg-white dark:bg-slate-800 shadow-lg ring-4 ring-blue-500/50 dark:ring-blue-400/50'
                      : 'bg-white/90 dark:bg-slate-800/90 shadow-md hover:ring-2 hover:ring-blue-400/30 dark:hover:ring-blue-500/30'
                  }
                `}
              >
                {/* Background pattern */}
                <div className="absolute inset-0 opacity-5 dark:opacity-10 bg-[radial-gradient(circle_at_center,rgba(120,119,198,0.8),transparent_70%)]" />
                
                <div className="relative w-32 h-32 mb-6 overflow-hidden rounded-full shadow-md transition-all duration-300 transform hover:scale-105 border-4 border-white dark:border-slate-700">
                  <Image
                    src={language.flagSrc}
                    alt={`${language.name} flag`}
                    fill
                    priority
                    style={{ objectFit: 'cover' }}
                    className="transition-all duration-300"
                  />
                </div>
                <h2 className="text-2xl font-bold text-center text-slate-800 dark:text-white mb-2">
                  {language.name}
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {language.code === 'dutch' ? 'Learn Dutch vocabulary and conversation' : 'Practice English speaking and listening'}
                </p>
                {selectedLanguage === language.code && (
                  <div className="absolute top-4 right-4">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-violet-600 flex items-center justify-center shadow-md">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="white"
                        className="w-5 h-5"
                      >
                        <path
                          fillRule="evenodd"
                          d="M19.916 4.626a.75.75 0 01.208 1.04l-9 13.5a.75.75 0 01-1.154.114l-6-6a.75.75 0 011.06-1.06l5.353 5.353 8.493-12.739a.75.75 0 011.04-.208z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  </div>
                )}
                
                {/* Animated accent */}
                <div className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-violet-600 transition-all duration-500 ${selectedLanguage === language.code ? 'w-full' : 'w-0'}`} />
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
