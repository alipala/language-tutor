'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/nav-bar';
import { TypeAnimation } from 'react-type-animation';

// Export the main component
export default function Home() {
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Wait for auth to be checked
    if (authLoading) return;
    
    // Log environment information for debugging
    console.log('Home page loaded at:', new Date().toISOString());
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Base path:', process.env.NEXT_PUBLIC_BASE_PATH || '/');
    console.log('Auth status:', user ? 'Logged in' : 'Not logged in');
    
    // Get current location info for debugging
    console.log('Current pathname:', window.location.pathname);
    console.log('Current URL:', window.location.href);
    console.log('Full origin:', window.location.origin);
    
    // IMPORTANT: Check if we're on the speaking assessment path but home page component loaded
    if (window.location.pathname === '/assessment/speaking') {
      console.log('On speaking assessment path but home page component loaded - force reload');
      
      // Force a hard reload of the current URL to try to get the correct component
      window.location.replace(window.location.href);
      return;
    }
    
    // Check for speaking assessment navigation in progress
    const navigatingToSpeakingAssessment = sessionStorage.getItem('navigatingToSpeakingAssessment');
    
    // If we have a speaking assessment navigation in progress and we're on the home page
    if (navigatingToSpeakingAssessment === 'true' && (window.location.pathname === '/' || window.location.pathname === '')) {
      console.log('Detected pending speaking assessment navigation');
      
      // Clear the flag to prevent loops
      sessionStorage.removeItem('navigatingToSpeakingAssessment');
      
      // Force navigation to speaking assessment
      const fullUrl = `${window.location.origin}/assessment/speaking`;
      console.log('Forcing navigation to speaking assessment:', fullUrl);
      window.location.replace(fullUrl);
      return;
    }
    
    // Check for auth navigation in progress
    const authNavigation = sessionStorage.getItem('authNavigation');
    const authNavigationAttemptTime = sessionStorage.getItem('authNavigationAttemptTime');
    
    // If we have an auth navigation in progress and we're still on the home page, retry it
    if (authNavigation && window.location.pathname === '/') {
      console.log('Detected pending auth navigation to:', authNavigation);
      
      // Check if the navigation attempt is recent (within last 5 seconds)
      const attemptTime = authNavigationAttemptTime ? parseInt(authNavigationAttemptTime) : 0;
      const currentTime = Date.now();
      const timeDiff = currentTime - attemptTime;
      
      if (timeDiff < 5000) { // 5 seconds
        console.log('Recovering from failed auth navigation');
        // Force navigation to the target
        if (authNavigation === 'login') {
          window.location.href = `${window.location.origin}/auth/login`;
        } else if (authNavigation === 'signup') {
          window.location.href = `${window.location.origin}/auth/signup`;
        }
        return;
      } else {
        // Clear stale navigation data
        console.log('Clearing stale auth navigation data');
        sessionStorage.removeItem('authNavigation');
        sessionStorage.removeItem('authNavigationAttemptTime');
      }
    }
    
    // Check for pending redirects from authentication process
    const pendingRedirect = sessionStorage.getItem('pendingRedirect');
    const redirectTarget = sessionStorage.getItem('redirectTarget');
    const redirectAttemptTime = sessionStorage.getItem('redirectAttemptTime');
    
    // If we have a pending redirect and we're on the home page, handle it
    if (pendingRedirect === 'true' && redirectTarget && window.location.pathname === '/') {
      console.log('Detected pending redirect to:', redirectTarget);
      
      // Check if the redirect attempt is recent (within last 10 seconds)
      const attemptTime = redirectAttemptTime ? parseInt(redirectAttemptTime) : 0;
      const currentTime = Date.now();
      const timeDiff = currentTime - attemptTime;
      
      if (timeDiff < 10000) { // 10 seconds
        console.log('Recovering from failed navigation after authentication');
        // Clear the pending redirect to prevent loops
        sessionStorage.removeItem('pendingRedirect');
        // Force navigation to the target
        window.location.href = redirectTarget;
        return;
      } else {
        // Clear stale redirect data
        console.log('Clearing stale redirect data');
        sessionStorage.removeItem('pendingRedirect');
        sessionStorage.removeItem('redirectTarget');
        sessionStorage.removeItem('redirectAttemptTime');
      }
    }
    
    // RAILWAY SPECIFIC: Check for the unusual routing situation
    // where URL is language-selection but we're still on the home page component
    if (window.location.pathname === '/language-selection') {
      console.log('URL is /language-selection but still on home page component - force reload');
      
      // We're in a strange state where the URL is language-selection but we're 
      // still on the home page component. Let's try to recover by forcing a reload
      // which should properly render the language selection component
      window.location.href = '/language-selection';
      return;
    }
    
    // Check for reset parameter
    const urlParams = new URLSearchParams(window.location.search);
    const shouldReset = urlParams.get('reset') === 'true';
    
    if (shouldReset) {
      console.log('Reset parameter detected, clearing session storage');
      sessionStorage.clear();
    }
    
    // Check if we should continue to a specific page based on stored data or user preferences
    // But only if we're not explicitly navigating to speaking assessment
    const hasLanguage = sessionStorage.getItem('selectedLanguage') || (user?.preferred_language || null);
    const hasLevel = sessionStorage.getItem('selectedLevel') || (user?.preferred_level || null);
    
    // If we're explicitly navigating to speaking assessment, don't redirect elsewhere
    if (sessionStorage.getItem('navigatingToSpeakingAssessment') === 'true') {
      console.log('Skipping automatic redirects due to pending speaking assessment navigation');
      return;
    }
    
    // If user is logged in, use their preferences if available
    if (user) {
      console.log('User is logged in:', user.email);
      
      // Store user preferences in session if not already there
      if (user.preferred_language && !sessionStorage.getItem('selectedLanguage')) {
        console.log('Using user preferred language:', user.preferred_language);
        sessionStorage.setItem('selectedLanguage', user.preferred_language);
      }
      
      if (user.preferred_level && !sessionStorage.getItem('selectedLevel')) {
        console.log('Using user preferred level:', user.preferred_level);
        sessionStorage.setItem('selectedLevel', user.preferred_level);
      }
    }
    
    if (hasLanguage && hasLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      window.location.href = '/speech';
      return;
    } else if (hasLanguage) {
      console.log('Found existing language, redirecting to level selection');
      window.location.href = '/level-selection';
      return;
    }
    
    // Check if we're on the root path and should show the welcome page
    if (window.location.pathname === '/' || window.location.pathname === '') {
      // On root path, show the UI instead of auto-redirecting
      console.log('On root path, showing welcome page');
      setIsLoading(false);
      return;
    }
    
    // If we're not on a recognized path, normalize to home page
    console.log('Unrecognized path, normalizing to home');
    window.location.replace('/');
  }, [user, authLoading]);
  
  // Return loading state while redirecting or manual navigation option if we hit the redirect limit
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      <div className="flex-grow flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center justify-center space-y-4">
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
            <p className="text-center text-gray-500 dark:text-gray-400">Redirecting to language selection...</p>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-6 mt-8">
            {/* Header with animated elements */}
            <div className="text-center mb-8 relative">
              {/* Animated background effects */}
              <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-20 bg-white/10 blur-xl animate-pulse"></div>
              
              <h1 className="text-5xl font-bold tracking-tight relative z-10 min-h-[5rem] text-white">
                <TypeAnimation
                  sequence={[
                    'Welcome to Language Tutor! 🌍',
                    2000,
                    'Welkom bij Language Tutor! 🇳🇱',
                    1500,
                    '¡Bienvenido a Language Tutor! 🇪🇸',
                    1500,
                    'Willkommen bei Language Tutor! 🇩🇪',
                    1500,
                    'Bienvenue à Language Tutor! 🇫🇷',
                    1500,
                    'Bem-vindo ao Language Tutor! 🇵🇹',
                    1500,
                  ]}
                  wrapper="span"
                  speed={50}
                  style={{ display: 'inline-block' }}
                  repeat={Infinity}
                  cursor={true}
                  className="text-white drop-shadow-sm"
                />
              </h1>
              <div className="text-white/80 mt-6 text-lg max-w-md mx-auto" style={{ height: '3rem', minHeight: '3rem' }}>
                <TypeAnimation
                  sequence={[
                    'Choose a language to start your journey 🚀',
                    2000,
                    'Oefen gesprekken met een AI-tutor 🤖',
                    1500,
                    'Practica con un tutor de IA ✨',
                    1500,
                    'Üben Sie mit einem KI-Tutor 🕒',
                    1500,
                    'Pratiquez avec un tuteur IA 🎯',
                    1500,
                  ]}
                  wrapper="p"
                  speed={55}
                  style={{ display: 'inline-block' }}
                  repeat={Infinity}
                  cursor={true}
                  className="text-white/80 animate-fade-in"
                />
              </div>
            </div>
            
            <div className="flex flex-col space-y-4 w-[320px] mt-8 mx-auto" style={{ height: '180px' }}>
              <button 
                onClick={() => {
                  try {
                    // Show loading state
                    setIsLoading(true);
                    setError(null);
                    
                    // Clear any existing session data except user preferences
                    // We don't want to clear the entire sessionStorage as it might contain user data
                    if (!user) {
                      sessionStorage.clear();
                    }
                    
                    // Set a navigation attempt counter to track potential issues
                    const attemptCount = parseInt(sessionStorage.getItem('homePageNavigationAttempt') || '0');
                    sessionStorage.setItem('homePageNavigationAttempt', (attemptCount + 1).toString());
                    
                    // Log the navigation attempt
                    console.log('Start Learning button clicked at:', new Date().toISOString());
                    console.log('Current pathname before navigation:', window.location.pathname);
                    console.log('User authenticated:', user ? 'Yes' : 'No');
                    console.log('Navigation attempt count:', attemptCount + 1);
                    
                    // IMPORTANT: Use absolute URL with origin for Railway
                    const fullUrl = `${window.location.origin}/language-selection`;
                    console.log('Navigating to:', fullUrl);
                    
                    // Force a hard navigation instead of client-side routing
                    // window.location.replace() is more reliable than href for full page navigation
                    window.location.replace(fullUrl);
                    
                    // Set a fallback timer with longer timeout
                    setTimeout(() => {
                      if (window.location.pathname === '/' || window.location.pathname === '') {
                        console.error('Navigation failed, still on homepage after timeout');
                        setIsLoading(false);
                        setError('Navigation to language selection failed. Please try again.');
                        
                        // If we've tried multiple times, suggest a hard refresh
                        if (attemptCount >= 2) {
                          setError('Navigation issues detected. Please try refreshing your browser or clearing cache.');
                        }
                      }
                    }, 5000); // Increased timeout for Railway environment
                  } catch (e) {
                    console.error('Navigation error:', e);
                    setIsLoading(false);
                    setError(`Navigation error: ${e instanceof Error ? e.message : 'Unknown error'}`);
                  }
                }}
                className="w-[320px] h-[52px] primary-button px-4 py-3 rounded-lg flex items-center justify-center"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    <span>Navigating...</span>
                  </>
                ) : (
                  <>
                    <span>Start Learning</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-1" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </button>
              
              {!user && (
                <div className="flex flex-col space-y-2 mt-4 w-[320px]">
                  <button
                    onClick={() => {
                      try {
                        // Show loading state
                        setIsLoading(true);
                        setError(null);
                        
                        // Log the navigation attempt
                        console.log('Sign In button clicked at:', new Date().toISOString());
                        console.log('Current pathname before navigation:', window.location.pathname);
                        
                        // Store navigation intent in session storage
                        sessionStorage.setItem('authNavigation', 'login');
                        sessionStorage.setItem('authNavigationAttemptTime', Date.now().toString());
                        
                        // Use the most direct and reliable navigation approach
                        const fullUrl = `${window.location.origin}/auth/login`;
                        console.log('Navigating to:', fullUrl);
                        
                        // IMPORTANT: For Railway, use direct window.location.href navigation
                        window.location.href = fullUrl;
                        
                        // Set a fallback timer to detect navigation failures
                        setTimeout(() => {
                          if (window.location.pathname === '/' || window.location.pathname === '') {
                            console.error('Navigation failed, still on homepage after timeout');
                            setIsLoading(false);
                            setError('Navigation to login page failed. Please try again.');
                            // Clear navigation intent
                            sessionStorage.removeItem('authNavigation');
                            sessionStorage.removeItem('authNavigationAttemptTime');
                          }
                        }, 1500);
                      } catch (e) {
                        console.error('Navigation error:', e);
                        setIsLoading(false);
                        setError(`Navigation error: ${e instanceof Error ? e.message : 'Unknown error'}`);
                      }
                    }}
                    className="w-[320px] h-[44px] py-2 px-4 glass-card border border-white/20 text-white rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center"
                    disabled={isLoading}
                  >
                    {isLoading && sessionStorage.getItem('authNavigation') === 'login' ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-indigo-500 border-t-transparent rounded-full mr-2"></div>
                        <span>Navigating...</span>
                      </>
                    ) : (
                      'Sign In'
                    )}
                  </button>
                  <button
                    onClick={() => {
                      try {
                        // Show loading state
                        setIsLoading(true);
                        setError(null);
                        
                        // Log the navigation attempt
                        console.log('Create Account button clicked at:', new Date().toISOString());
                        console.log('Current pathname before navigation:', window.location.pathname);
                        
                        // Store navigation intent in session storage
                        sessionStorage.setItem('authNavigation', 'signup');
                        sessionStorage.setItem('authNavigationAttemptTime', Date.now().toString());
                        
                        // Use the most direct and reliable navigation approach
                        const fullUrl = `${window.location.origin}/auth/signup`;
                        console.log('Navigating to:', fullUrl);
                        
                        // IMPORTANT: For Railway, use direct window.location.href navigation
                        window.location.href = fullUrl;
                        
                        // Set a fallback timer to detect navigation failures
                        setTimeout(() => {
                          if (window.location.pathname === '/' || window.location.pathname === '') {
                            console.error('Navigation failed, still on homepage after timeout');
                            setIsLoading(false);
                            setError('Navigation to signup page failed. Please try again.');
                            // Clear navigation intent
                            sessionStorage.removeItem('authNavigation');
                            sessionStorage.removeItem('authNavigationAttemptTime');
                          }
                        }, 1500);
                      } catch (e) {
                        console.error('Navigation error:', e);
                        setIsLoading(false);
                        setError(`Navigation error: ${e instanceof Error ? e.message : 'Unknown error'}`);
                      }
                    }}
                    className="w-[320px] h-[44px] py-2 px-4 secondary-button rounded-lg flex items-center justify-center"
                    disabled={isLoading}
                  >
                    {isLoading && sessionStorage.getItem('authNavigation') === 'signup' ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-gray-300 border-t-transparent rounded-full mr-2"></div>
                        <span>Navigating...</span>
                      </>
                    ) : (
                      'Create Account'
                    )}
                  </button>
                </div>
              )}
              
              {parseInt(sessionStorage.getItem('homePageRedirectAttempt') || '0') > 2 && (
                <div className="p-4 glass-card rounded-lg mt-4 border border-white/20">
                  <p className="text-sm text-white/80">
                    We detected navigation issues. If you're having trouble, try clearing your browser cache or using a different browser.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
