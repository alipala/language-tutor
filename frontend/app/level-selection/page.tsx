'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { verifyBackendConnectivity } from '../../lib/healthCheck';
// Sound effects temporarily disabled
// import { useAudio } from '@/lib/useAudio';

interface Level {
  code: string;
  name: string;
  description: string;
}

export default function LevelSelection() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [levels, setLevels] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  // Sound effects temporarily disabled
  // const { playSelectionSound, playSuccessSound } = useAudio();

  useEffect(() => {
    // Retrieve the selected language from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    if (!language) {
      // If no language is selected, redirect to language selection
      router.push('/language-selection');
      return;
    }
    
    setSelectedLanguage(language);
    
    // First verify backend connectivity
    verifyBackendConnectivity()
      .then(connected => {
        console.log('Backend connectivity check result:', connected);
        setBackendConnected(connected);
        
        if (connected) {
          // If connected, proceed to fetch languages and levels
          fetchLanguagesAndLevels(language);
        } else {
          // If not connected, show an error
          setError('Unable to connect to the backend server. Please try again later.');
          setIsLoading(false);
        }
      })
      .catch(err => {
        console.error('Backend connectivity check failed:', err);
        setBackendConnected(false);
        setError('Failed to verify backend connectivity. Please refresh the page or try again later.');
        setIsLoading(false);
      });
  }, [router]);

  const fetchLanguagesAndLevels = async (language: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Determine the API URL based on the environment
      let baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
      
      // Handle localhost and 127.0.0.1 cases
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        baseUrl = 'http://localhost:8001';
      }
      
      // Log the environment and API URL for debugging
      console.log('Environment:', process.env.NODE_ENV);
      console.log('Using API base URL:', baseUrl);
      
      console.log('Using API base URL:', baseUrl);
      
      // Add retry logic for better reliability
      let response;
      let retries = 0;
      const maxRetries = 3;
      
      while (retries < maxRetries) {
        try {
          // Make sure we're using the correct endpoint format
          response = await fetch(`${baseUrl}/api/languages`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Cache-Control': 'no-cache'
            }
          });
          
          if (response.ok) break;
          
        } catch (fetchError) {
          console.log(`Fetch attempt ${retries + 1} failed:`, fetchError);
        }
        
        retries++;
        if (retries < maxRetries) {
          console.log(`Retrying fetch (${retries}/${maxRetries})...`);
          // Wait a bit before retrying
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      // Check if response exists and is ok
      if (!response || !response.ok) {
        throw new Error('Failed to fetch languages and levels');
      }
      
      const data = await response.json();
      
      if (!data[language]) {
        throw new Error(`Language ${language} not found`);
      }
      
      setLevels(data[language].levels || {});
    } catch (err) {
      console.error('Error fetching languages and levels:', err);
      setError('Failed to load language levels. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Add a useEffect to check if we're stuck on this page
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    console.log('Level selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    console.log('Document referrer:', document.referrer);
    
    // Check for redirect loop
    const redirectAttemptKey = 'levelSelectionRedirectAttempt';
    const redirectAttempts = parseInt(sessionStorage.getItem(redirectAttemptKey) || '0');
    console.log('Level selection page loaded, redirect attempts:', redirectAttempts);
    
    // If we've tried to redirect too many times, reset the counter and stay on this page
    if (redirectAttempts > 3) {
      console.log('Too many redirect attempts detected, resetting counter');
      sessionStorage.setItem(redirectAttemptKey, '0');
      // Clear any potentially problematic navigation flags
      sessionStorage.removeItem('intentionalNavigation');
      return;
    }
    
    // Check if we have both language and level in session storage but we're still on this page
    const storedLanguage = sessionStorage.getItem('selectedLanguage');
    const storedLevel = sessionStorage.getItem('selectedLevel');
    const intentionalNavigation = sessionStorage.getItem('intentionalNavigation');
    
    // Only increment the redirect attempt counter if we're trying to redirect
    if ((!storedLanguage) || (storedLanguage && storedLevel)) {
      sessionStorage.setItem(redirectAttemptKey, (redirectAttempts + 1).toString());
    }
    
    // If we don't have a language, we should be on language selection
    if (!storedLanguage && window.location.pathname.includes('level-selection')) {
      console.log('No language selected, redirecting to language selection');
      // Add a small delay before redirecting
      setTimeout(() => {
        console.log('Navigating to language selection page');
        window.location.href = '/language-selection';
        
        // Fallback navigation in case the first attempt fails (for Railway)
        const fallbackTimer = setTimeout(() => {
          if (window.location.pathname.includes('level-selection')) {
            console.log('Still on level selection page, using fallback navigation to language selection');
            window.location.replace('/language-selection');
          }
        }, 1000);
        
        return () => clearTimeout(fallbackTimer);
      }, 300);
      return;
    }
    
    // If we have both language and level, we should be on speech page
    if (storedLanguage && storedLevel && window.location.pathname.includes('level-selection')) {
      console.log('Detected stuck on level selection page with stored selections');
      // Force navigation to speech page with a small delay
      setTimeout(() => {
        console.log('Navigating to speech page');
        window.location.href = '/speech';
        
        // Fallback navigation in case the first attempt fails (for Railway)
        const fallbackTimer = setTimeout(() => {
          if (window.location.pathname.includes('level-selection')) {
            console.log('Still on level selection page, using fallback navigation to speech');
            window.location.replace('/speech');
          }
        }, 1000);
        
        return () => clearTimeout(fallbackTimer);
      }, 300);
    }
    
    // Clear the intentional navigation flag if it exists
    if (intentionalNavigation) {
      console.log('Clearing intentional navigation flag');
      sessionStorage.removeItem('intentionalNavigation');
    }
  }, []);
  
  const handleStartOver = () => {
    // Clear all session storage
    sessionStorage.clear();
    // Navigate to home page
    console.log('Starting over - cleared session storage');
    window.location.href = '/';
    
    // Fallback navigation in case the first attempt fails (for Railway)
    setTimeout(() => {
      if (window.location.pathname.includes('level-selection')) {
        console.log('Still on level selection page, using fallback navigation for start over');
        window.location.replace('/');
      }
    }, 1000);
  };
  
  const handleChangeLanguage = () => {
    // Clear both the language and level to ensure proper navigation
    sessionStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLevel');
    // Navigate to language selection
    console.log('Navigating to language selection, cleared language and level selections');
    window.location.href = '/language-selection';
    
    // Fallback navigation in case the first attempt fails (for Railway)
    setTimeout(() => {
      if (window.location.pathname.includes('level-selection')) {
        console.log('Still on level selection page, using fallback navigation to language selection');
        window.location.replace('/language-selection');
      }
    }, 1000);
  };

  const handleLevelSelect = (levelCode: string) => {
    // Set loading state while navigating
    setIsLoading(true);
    setSelectedLevel(levelCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLevel', levelCode);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Navigating to speech page with level:', levelCode);
    
    // Use a direct window.location approach for Railway with a small delay
    // This bypasses any client-side routing issues
    setTimeout(() => {
      console.log('Executing navigation to speech page');
      window.location.href = '/speech';
      
      // Fallback navigation in case the first attempt fails (for Railway)
      const fallbackTimer = setTimeout(() => {
        console.log('Checking if fallback navigation is needed');
        if (window.location.pathname.includes('level-selection')) {
          console.log('Still on level selection page, using fallback navigation');
          window.location.replace('/speech');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 300);
  };

  // Format the levels for display
  const formattedLevels = Object.entries(levels).map(([code, description]) => ({
    code,
    name: code,
    description: description as string
  }));

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            Select Your Level
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2 text-improved">
            Choose your proficiency level in {selectedLanguage && selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)}
          </p>
          <div className="flex justify-center mt-4 space-x-4">
            <button 
              onClick={handleChangeLanguage}
              className="text-sm text-indigo-500 hover:text-indigo-400 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Change Language
            </button>
            <button 
              onClick={handleStartOver}
              className="text-sm text-red-500 hover:text-red-400 dark:text-red-400 dark:hover:text-red-300"
            >
              Start Over
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
            <p className="text-muted-foreground dark:text-slate-400">Loading available levels...</p>
            {backendConnected === false && (
              <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-amber-500 dark:text-amber-400 text-sm">Warning: Backend connectivity issues detected.</p>
              </div>
            )}
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-500 dark:text-red-400">{error}</p>
              <button
                onClick={() => {
                  setIsLoading(true);
                  setError(null);
                  // First verify connectivity, then fetch data
                  verifyBackendConnectivity()
                    .then(connected => {
                      setBackendConnected(connected);
                      if (connected) {
                        fetchLanguagesAndLevels(selectedLanguage || 'english');
                      } else {
                        setError('Still unable to connect to the backend server.');
                        setIsLoading(false);
                      }
                    })
                    .catch(() => {
                      setBackendConnected(false);
                      setError('Failed to verify backend connectivity.');
                      setIsLoading(false);
                    });
                }}
                className="mt-4 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-md transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-3xl">
              {formattedLevels.map((level) => (
                <button
                  key={level.code}
                  onClick={() => handleLevelSelect(level.code)}
                  className={`
                    relative flex flex-col items-start p-6 rounded-xl text-left
                    transition-all duration-300 transform hover:scale-102
                    ${
                      selectedLevel === level.code
                        ? 'bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border-2 border-indigo-500/50 shadow-lg'
                        : 'bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20'
                    }
                  `}
                >
                  <h2 className="text-xl font-semibold mb-2 gradient-text dark:from-indigo-300 dark:to-purple-300">
                    {level.name} - {level.code === 'A1' || level.code === 'A2' ? 'Beginner' : 
                                    level.code === 'B1' || level.code === 'B2' ? 'Intermediate' : 'Advanced'}
                  </h2>
                  <p className="text-sm text-muted-foreground dark:text-slate-400">
                    {level.description}
                  </p>
                  {selectedLevel === level.code && (
                    <div className="absolute top-3 right-3">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="white"
                          className="w-4 h-4"
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
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
