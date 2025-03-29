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
    const hasLanguage = sessionStorage.getItem('selectedLanguage') || (user?.preferred_language || null);
    const hasLevel = sessionStorage.getItem('selectedLevel') || (user?.preferred_level || null);
    
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
    <div className="min-h-screen flex flex-col app-background">
      <NavBar />
      <div className="flex-grow flex flex-col items-center justify-center p-4">
        {/* Animated background effects */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/3 left-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse opacity-70"></div>
        <div className="absolute top-2/3 right-1/4 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl animate-pulse opacity-70"></div>
        
        <div className="flex flex-col items-center justify-center space-y-6 relative z-10">
        {/* Multilingual greeting header with animation */}
        <div className="text-center mb-4">
          <h1 className="text-5xl font-bold tracking-tight relative z-10 min-h-[4rem] inline-block">
            <div className="relative">
              <TypeAnimation
                sequence={[
                  'Language Tutor',
                  2000,
                  'Taaltutor', // Dutch
                  1500,
                  'Tutor de Idiomas', // Spanish
                  1500,
                  'Sprachtutor', // German
                  1500,
                  'Tuteur de Langue', // French
                  1500,
                  'Tutor de Idiomas', // Portuguese
                  1500,
                  'Language Tutor',
                  1000,
                ]}
                wrapper="span"
                speed={50}
                style={{ display: 'inline-block' }}
                repeat={Infinity}
                cursor={true}
                className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-violet-400 drop-shadow-sm"
              />
              {/* Animated underline effect */}
              <div className="absolute -bottom-2 left-0 w-full h-[3px] bg-gradient-to-r from-blue-400/0 via-violet-400/70 to-blue-400/0 animate-pulse"></div>
            </div>
          </h1>
        </div>
        
        {/* Multilingual welcome message */}
        <div className="text-slate-300 text-lg max-w-md mx-auto min-h-[3rem] text-center mb-4">
          <TypeAnimation
            sequence={[
              'Welcome! Learn languages with AI conversation practice',
              2000,
              'Welkom! Leer talen met AI-conversatieoefening', // Dutch
              1500,
              '¡Bienvenido! Aprende idiomas con práctica de conversación con IA', // Spanish
              1500,
              'Willkommen! Lerne Sprachen mit KI-Konversationsübungen', // German
              1500,
              'Bienvenue! Apprenez des langues avec des exercices de conversation IA', // French
              1500,
              'Bem-vindo! Aprenda idiomas com prática de conversação com IA', // Portuguese
              1500,
              'Welcome! Learn languages with AI conversation practice',
              1000,
            ]}
            wrapper="p"
            speed={55}
            style={{ display: 'inline-block' }}
            repeat={Infinity}
            cursor={true}
            className="text-slate-300"
          />
        </div>
        
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
            <p className="text-center text-gray-500 dark:text-gray-400">Redirecting to language selection...</p>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-6 mt-8">
            <div className="text-center text-gray-600 dark:text-gray-300 max-w-md px-6 py-4 bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 shadow-lg">
              <p className="mb-2">
                <span className="font-semibold text-blue-400">Hello</span> • <span className="font-semibold text-indigo-400">Hallo</span> • <span className="font-semibold text-violet-400">Hola</span> • <span className="font-semibold text-purple-400">Bonjour</span> • <span className="font-semibold text-pink-400">Olá</span>
              </p>
              <p>
                Choose a language and level to start practicing your conversation skills with an AI tutor.
              </p>
            </div>
            
            <div className="flex flex-col space-y-4 w-full max-w-xs">
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
                    
                    // Log the navigation attempt
                    console.log('Start Learning button clicked at:', new Date().toISOString());
                    console.log('Current pathname before navigation:', window.location.pathname);
                    console.log('User authenticated:', user ? 'Yes' : 'No');
                    
                    // Use the most direct and reliable navigation approach
                    // By using the full URL with origin, we ensure proper navigation in Railway
                    const fullUrl = `${window.location.origin}/language-selection`;
                    console.log('Navigating to:', fullUrl);
                    
                    // IMPORTANT: For Railway, use direct window.location.href navigation
                    // This bypasses Next.js client-side routing which may be causing issues
                    window.location.href = fullUrl;
                    
                    // Set a fallback timer to detect navigation failures
                    setTimeout(() => {
                      if (window.location.pathname === '/' || window.location.pathname === '') {
                        console.error('Navigation failed, still on homepage after timeout');
                        setIsLoading(false);
                        setError('Navigation to language selection failed. Please try again.');
                      }
                    }, 3000);
                  } catch (e) {
                    console.error('Navigation error:', e);
                    setIsLoading(false);
                    setError(`Navigation error: ${e instanceof Error ? e.message : 'Unknown error'}`);
                  }
                }}
                className="w-full app-button flex items-center justify-center relative overflow-hidden group"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    <span>Navigating...</span>
                  </>
                ) : (
                  <>
                    <span className="relative z-10">Start Learning</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-1 relative z-10" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-violet-500/20 transform translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                  </>
                )}
              </button>
              
              {!user && (
                <div className="flex flex-col space-y-2 mt-4">
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
                    className="w-full py-2 px-4 border border-indigo-500 text-indigo-600 rounded-md hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 flex items-center justify-center relative overflow-hidden group transition-all duration-300 hover:shadow-md hover:shadow-indigo-500/20"
                    disabled={isLoading}
                  >
                    {isLoading && sessionStorage.getItem('authNavigation') === 'login' ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-indigo-500 border-t-transparent rounded-full mr-2"></div>
                        <span>Navigating...</span>
                      </>
                    ) : (
                      <>
                        <span className="relative z-10">Sign In</span>
                        <div className="absolute inset-0 bg-indigo-500/10 transform translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                      </>
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
                    className="w-full py-2 px-4 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-600 dark:text-gray-200 dark:hover:bg-slate-700 flex items-center justify-center relative overflow-hidden group transition-all duration-300 hover:shadow-md hover:shadow-slate-500/20"
                    disabled={isLoading}
                  >
                    {isLoading && sessionStorage.getItem('authNavigation') === 'signup' ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-gray-300 border-t-transparent rounded-full mr-2"></div>
                        <span>Navigating...</span>
                      </>
                    ) : (
                      <>
                        <span className="relative z-10">Create Account</span>
                        <div className="absolute inset-0 bg-slate-500/10 transform translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                      </>
                    )}
                  </button>
                </div>
              )}
              
              {parseInt(sessionStorage.getItem('homePageRedirectAttempt') || '0') > 2 && (
                <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg mt-4">
                  <p className="text-sm text-amber-700 dark:text-amber-400">
                    We detected navigation issues. If you're having trouble, try clearing your browser cache or using a different browser.
                  </p>
                </div>
              )}
              
              {/* Language icons with staggered float animation */}
              <div className="flex justify-center space-x-4 mt-6 animate-fade-in">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-sm animate-float stagger-1 transition-all duration-300 hover:scale-110 hover:shadow-md hover:shadow-blue-500/20">
                  <span className="text-lg font-semibold">EN</span>
                </div>
                <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shadow-sm animate-float stagger-2 transition-all duration-300 hover:scale-110 hover:shadow-md hover:shadow-indigo-500/20">
                  <span className="text-lg font-semibold">NL</span>
                </div>
                <div className="w-10 h-10 rounded-full bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 dark:text-violet-400 shadow-sm animate-float stagger-3 transition-all duration-300 hover:scale-110 hover:shadow-md hover:shadow-violet-500/20">
                  <span className="text-lg font-semibold">ES</span>
                </div>
                <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400 shadow-sm animate-float stagger-4 transition-all duration-300 hover:scale-110 hover:shadow-md hover:shadow-purple-500/20">
                  <span className="text-lg font-semibold">DE</span>
                </div>
                <div className="w-10 h-10 rounded-full bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center text-pink-600 dark:text-pink-400 shadow-sm animate-float stagger-5 transition-all duration-300 hover:scale-110 hover:shadow-md hover:shadow-pink-500/20">
                  <span className="text-lg font-semibold">FR</span>
                </div>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
