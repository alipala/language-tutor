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
    // Clear the language and level to ensure proper navigation
    sessionStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLevel');
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    // Clear any navigation flags
    sessionStorage.removeItem('fromLevelSelection');
    sessionStorage.removeItem('intentionalNavigation');
    
    // Navigate to language selection
    console.log('Navigating to language selection from level selection, cleared selections');
    window.location.href = '/language-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('level-selection')) {
        console.log('Still on level selection page, using fallback navigation to language selection');
        window.location.replace('/language-selection');
      }
    }, 1000);
  };
  
  const handleChangeTopic = () => {
    // Keep language but clear the topic
    sessionStorage.removeItem('selectedTopic');
    // Set a flag to indicate we're intentionally going to topic selection
    sessionStorage.setItem('fromLevelSelection', 'true');
    // Navigate to topic selection
    console.log('Navigating to topic selection with fromLevelSelection flag');
    
    // Use direct navigation for reliability
    window.location.href = '/topic-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('level-selection')) {
        console.log('Still on level selection page, using fallback navigation to topic selection');
        window.location.replace('/topic-selection');
      }
    }, 1000);
  };

  const handleLevelSelect = (level: string) => {
    // Set loading state while navigating
    setIsLoading(true);
    setSelectedLevel(level);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLevel', level);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Navigating to speech with level:', level);
    
    // Use direct navigation for reliability
    setTimeout(() => {
      console.log('Executing navigation to speech page');
      window.location.href = '/speech';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
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
    <main className="flex min-h-screen flex-col app-background text-white p-4 md:p-8">
      <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 mb-4 animate-fade-in">
            Select Your Level
          </h1>
          <p className="text-slate-300 text-lg mb-8 animate-fade-in" style={{animationDelay: '100ms'}}>
            Choose your proficiency level in {selectedLanguage && selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)}
          </p>
          <div className="flex space-x-4 justify-center mb-10 animate-fade-in" style={{animationDelay: '200ms'}}>
            <button 
              onClick={handleChangeLanguage}
              className="app-button flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              <span>Change Language</span>
            </button>
            <button 
              onClick={handleChangeTopic}
              className="app-button flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              <span>Change Topic</span>
            </button>
            <button 
              onClick={handleStartOver}
              className="app-button flex items-center space-x-2" 
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
            <div className="relative w-20 h-20 mb-6">
              <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-indigo-200/20 animate-pulse"></div>
              <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-transparent border-t-indigo-500 animate-spin"></div>
            </div>
            <p className="text-indigo-200 animate-pulse">Loading available levels...</p>
            {backendConnected === false && (
              <div className="mt-8 p-5 bg-gradient-to-r from-amber-900/30 to-red-900/30 border border-amber-700/50 rounded-xl shadow-lg">
                <p className="text-amber-400 text-sm font-medium">Warning: Backend connectivity issues detected.</p>
              </div>
            )}
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-8 bg-gradient-to-br from-red-900/30 to-red-900/10 border border-red-700/30 rounded-xl shadow-lg backdrop-blur-sm max-w-md animate-fade-in">
              <div className="relative w-20 h-20 mx-auto mb-6">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-red-500 absolute top-0 left-0 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="absolute inset-0 bg-red-500/20 rounded-full blur-xl animate-pulse"></div>
              </div>
              <p className="text-red-400 font-medium mb-6 text-lg">{error}</p>
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
                className="app-button"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-3xl">
              {formattedLevels.map((level) => {
                // Determine level color scheme based on level code
                const getLevelColors = (code: string) => {
                  if (code.startsWith('A')) return {
                    bg: 'from-green-500 to-emerald-600',
                    border: 'border-green-500',
                    glow: 'shadow-green-500/20',
                    ring: 'ring-green-400',
                    icon: 'bg-gradient-to-r from-green-500 to-emerald-600',
                    badge: 'bg-gradient-to-br from-green-400 to-emerald-500 via-green-500',
                    badgeShadow: 'shadow-green-500/30'
                  };
                  if (code.startsWith('B')) return {
                    bg: 'from-blue-500 to-indigo-600',
                    border: 'border-blue-500',
                    glow: 'shadow-blue-500/20',
                    ring: 'ring-blue-400',
                    icon: 'bg-gradient-to-r from-blue-500 to-indigo-600',
                    badge: 'bg-gradient-to-br from-blue-400 to-indigo-500 via-blue-500',
                    badgeShadow: 'shadow-blue-500/30'
                  };
                  return {
                    bg: 'from-purple-500 to-violet-600',
                    border: 'border-purple-500',
                    glow: 'shadow-purple-500/20',
                    ring: 'ring-purple-400',
                    icon: 'bg-gradient-to-r from-purple-500 to-violet-600',
                    badge: 'bg-gradient-to-br from-purple-400 to-violet-500 via-purple-500',
                    badgeShadow: 'shadow-purple-500/30'
                  };
                };
                
                const colors = getLevelColors(level.code);
                
                return (
                  <button
                    key={level.code}
                    onClick={() => handleLevelSelect(level.code)}
                    className={`
                      relative overflow-hidden flex flex-col items-start p-6 rounded-xl text-left
                      transition-all duration-300 transform hover:scale-105 hover:shadow-xl
                      backdrop-blur-sm animate-fade-in h-[220px]
                      ${
                        selectedLevel === level.code
                          ? `bg-slate-800/80 border border-slate-700 shadow-xl shadow-${colors.bg.split(' ')[1]}/20 ring-2 ${colors.ring}/50`
                          : 'bg-slate-800/60 border border-slate-700/50 hover:border-slate-600 shadow-lg hover:shadow-lg hover:shadow-slate-700/50'
                      }
                    `}
                    style={{animationDelay: `${300 + parseInt(level.code.charAt(1)) * 100}ms`}}
                  >
                    {/* Level badge */}
                    <div className={`absolute -top-3 -right-3 w-16 h-16 flex items-center justify-center overflow-hidden`}>
                      <div className={`absolute transform rotate-45 w-24 h-8 ${colors.badge} top-2 right-[-6px] shadow-lg ${colors.badgeShadow}`}>
                        <div className="absolute inset-0 opacity-20 animate-pulse"></div>
                      </div>
                      <span className="relative text-white font-bold text-xs">{level.code}</span>
                    </div>
                    
                    <h2 className="text-xl font-bold mb-3 text-white bg-clip-text">
                      {level.code === 'A1' || level.code === 'A2' ? 'Beginner' : 
                       level.code === 'B1' || level.code === 'B2' ? 'Intermediate' : 'Advanced'}
                    </h2>
                    <p className="text-sm text-slate-300 mb-4">
                      {level.description}
                    </p>
                    
                    {/* Skill indicators */}
                    <div className="flex flex-wrap gap-2 mt-auto">
                      {level.code.startsWith('A') && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-green-500/20 to-green-600/20 border border-green-500/30 text-green-400 rounded-full shadow-sm">Basic Vocabulary</span>
                      )}
                      {(level.code === 'A2' || level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-blue-500/20 to-blue-600/20 border border-blue-500/30 text-blue-400 rounded-full shadow-sm">Conversation</span>
                      )}
                      {(level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-indigo-500/20 to-indigo-600/20 border border-indigo-500/30 text-indigo-400 rounded-full shadow-sm">Complex Topics</span>
                      )}
                      {level.code.startsWith('C') && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-purple-500/20 to-purple-600/20 border border-purple-500/30 text-purple-400 rounded-full shadow-sm">Fluent Expression</span>
                      )}
                    </div>
                    
                    {selectedLevel === level.code && (
                      <div className="absolute top-4 left-4">
                        <div className={`w-8 h-8 rounded-full ${colors.icon} flex items-center justify-center shadow-lg ${colors.glow} animate-pulse`}>
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="white"
                            className="w-5 h-5 animate-fade-in"
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
