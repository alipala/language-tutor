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
        baseUrl = 'http://localhost:8000';
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
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600 dark:from-blue-400 dark:to-violet-400">
            Select Your Level
          </h1>
          <p className="text-slate-600 dark:text-slate-300 mt-3 text-lg">
            Choose your proficiency level in {selectedLanguage && selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)}
          </p>
          <div className="flex justify-center mt-6 space-x-6">
            <button 
              onClick={handleChangeLanguage}
              className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 bg-white/80 dark:bg-slate-800/80 rounded-full shadow-sm hover:shadow transition-all duration-200 flex items-center space-x-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              <span>Change Language</span>
            </button>
            <button 
              onClick={handleStartOver}
              className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 bg-white/80 dark:bg-slate-800/80 rounded-full shadow-sm hover:shadow transition-all duration-200 flex items-center space-x-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Start Over</span>
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-14 w-14 border-4 border-blue-200 border-t-blue-600 mb-6"></div>
            <p className="text-slate-600 dark:text-slate-300">Loading available levels...</p>
            {backendConnected === false && (
              <div className="mt-6 p-4 bg-amber-100 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-xl shadow-sm">
                <p className="text-amber-700 dark:text-amber-400 text-sm font-medium">Warning: Backend connectivity issues detected.</p>
              </div>
            )}
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl shadow-sm max-w-md">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-red-500 dark:text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-red-700 dark:text-red-400 font-medium mb-4">{error}</p>
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
                className="mt-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-sm hover:shadow transition-all duration-200 font-medium"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
              {formattedLevels.map((level) => {
                // Determine level color scheme based on level code
                const getLevelColors = (code: string) => {
                  if (code.startsWith('A')) return {
                    bg: 'from-green-500 to-emerald-600',
                    border: 'border-green-500',
                    ring: 'ring-green-400',
                    icon: 'bg-gradient-to-r from-green-500 to-emerald-600'
                  };
                  if (code.startsWith('B')) return {
                    bg: 'from-blue-500 to-indigo-600',
                    border: 'border-blue-500',
                    ring: 'ring-blue-400',
                    icon: 'bg-gradient-to-r from-blue-500 to-indigo-600'
                  };
                  return {
                    bg: 'from-purple-500 to-violet-600',
                    border: 'border-purple-500',
                    ring: 'ring-purple-400',
                    icon: 'bg-gradient-to-r from-purple-500 to-violet-600'
                  };
                };
                
                const colors = getLevelColors(level.code);
                
                return (
                  <button
                    key={level.code}
                    onClick={() => handleLevelSelect(level.code)}
                    className={`
                      relative overflow-hidden flex flex-col items-start p-6 rounded-xl text-left
                      transition-all duration-300 transform hover:scale-102 hover:shadow-xl
                      ${
                        selectedLevel === level.code
                          ? `bg-white dark:bg-slate-800 shadow-lg ring-4 ${colors.ring}/50 dark:${colors.ring}/30`
                          : 'bg-white dark:bg-slate-800 shadow-md hover:ring-2 hover:ring-blue-400/30 dark:hover:ring-blue-500/30'
                      }
                    `}
                  >
                    {/* Level badge */}
                    <div className={`absolute -top-3 -right-3 w-16 h-16 flex items-center justify-center overflow-hidden`}>
                      <div className={`absolute transform rotate-45 w-24 h-8 bg-gradient-to-r ${colors.bg} top-2 right-[-6px]`}></div>
                      <span className="relative text-white font-bold text-xs">{level.code}</span>
                    </div>
                    
                    <h2 className="text-xl font-bold mb-3 text-slate-800 dark:text-white">
                      {level.code === 'A1' || level.code === 'A2' ? 'Beginner' : 
                       level.code === 'B1' || level.code === 'B2' ? 'Intermediate' : 'Advanced'}
                    </h2>
                    <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
                      {level.description}
                    </p>
                    
                    {/* Skill indicators */}
                    <div className="flex flex-wrap gap-2 mt-auto">
                      {level.code.startsWith('A') && (
                        <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 rounded-full">Basic Vocabulary</span>
                      )}
                      {(level.code === 'A2' || level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 rounded-full">Conversation</span>
                      )}
                      {(level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-400 rounded-full">Complex Topics</span>
                      )}
                      {level.code.startsWith('C') && (
                        <span className="text-xs px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400 rounded-full">Fluent Expression</span>
                      )}
                    </div>
                    
                    {selectedLevel === level.code && (
                      <div className="absolute top-4 left-4">
                        <div className={`w-8 h-8 rounded-full ${colors.icon} flex items-center justify-center shadow-md`}>
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
                    
                    {/* Bottom accent bar */}
                    <div className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${colors.bg} transition-all duration-500 ${selectedLevel === level.code ? 'w-full' : 'w-0'}`} />
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
