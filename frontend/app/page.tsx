'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';

// Export the main component
// Language interface for type safety
interface Language {
  code: string;
  name: string;
  flagSrc: string;
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(true);
  const [showLanguageSelection, setShowLanguageSelection] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  
  // Define available languages
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
  
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Log environment information for debugging
    console.log('Home page loaded at:', new Date().toISOString());
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Current pathname:', window.location.pathname);
    console.log('Current URL:', window.location.href);
    
    // Check if we should continue to speech page
    const hasLanguage = sessionStorage.getItem('selectedLanguage');
    const hasLevel = sessionStorage.getItem('selectedLevel');
    
    if (hasLanguage && hasLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      window.location.replace('/speech');
      return;
    }
    
    // Check if we should continue to level selection
    if (hasLanguage && !hasLevel) {
      console.log('Found existing language, redirecting to level selection');
      window.location.replace('/level-selection');
      return;
    }
    
    // Display the page after a short delay
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500);
    
    return () => {
      clearTimeout(timer);
    };
  }, []);
  
  // Function to handle language selection
  const handleLanguageSelect = (languageCode: string) => {
    console.log('Language selected:', languageCode);
    setSelectedLanguage(languageCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLanguage', languageCode);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Navigate to level selection
    const isRailway = window.location.hostname.includes('railway.app');
    const fullUrl = `${window.location.origin}/level-selection`;
    console.log('Navigating to level selection:', fullUrl);
    
    // Use direct location replacement which is most reliable
    window.location.replace(fullUrl);
  };
  
  // Return loading state while redirecting or language selection if we hit the redirect limit
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="flex flex-col items-center justify-center space-y-4">
        <h1 className="text-4xl font-bold text-center gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">Language Tutor</h1>
        
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
            <p className="text-center text-gray-500 dark:text-gray-400">Loading...</p>
          </>
        ) : showLanguageSelection ? (
          // Language selection view
          <div className="flex flex-col items-center space-y-6 mt-8">
            <h2 className="text-2xl font-semibold text-center">Select a Language</h2>
            <p className="text-center text-gray-600 dark:text-gray-300 max-w-md">
              Choose a language to start practicing your conversation skills with an AI tutor.
            </p>
            
            <div className="grid grid-cols-2 gap-6 mt-4 w-full max-w-md">
              {languages.map((language) => (
                <button
                  key={language.code}
                  onClick={() => handleLanguageSelect(language.code)}
                  className={`flex flex-col items-center p-4 rounded-lg transition-all ${selectedLanguage === language.code ? 'ring-2 ring-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'}`}
                >
                  <div className="relative w-24 h-24 mb-3 overflow-hidden rounded-md shadow-md">
                    <Image
                      src={language.flagSrc}
                      alt={`${language.name} flag`}
                      fill
                      style={{ objectFit: 'cover' }}
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                  </div>
                  <span className="font-medium text-lg">{language.name}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          // Welcome view with start button
          <div className="flex flex-col items-center space-y-6 mt-8">
            <p className="text-center text-gray-600 dark:text-gray-300 max-w-md">
              Welcome to Language Tutor! Choose a language and level to start practicing your conversation skills with an AI tutor.
            </p>
            
            <div className="flex flex-col space-y-4 w-full max-w-xs">
              <button 
                onClick={() => {
                  // Clear session storage and show language selection
                  sessionStorage.clear();
                  console.log('Start Learning button clicked, showing language selection');
                  setShowLanguageSelection(true);
                }}
                className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all"
              >
                Start Learning
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
