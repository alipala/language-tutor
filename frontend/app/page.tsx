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
      <div className="flex-grow flex flex-col items-center justify-center p-4 w-full">
        {/* Simple background effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-7xl bg-blue-500/5 rounded-3xl blur-3xl"></div>
        
        <div className="w-full max-w-7xl mx-auto flex flex-col items-center justify-center space-y-8 relative z-10 px-8">
        {/* Main title with animation */}
        <div className="text-center mb-2 w-full">
          <h1 className="text-6xl font-bold tracking-tight relative z-10 min-h-[5rem] inline-block">
            <TypeAnimation
              sequence={[
                'Language Tutor',
                3000
              ]}
              wrapper="span"
              speed={50}
              style={{ display: 'inline-block' }}
              repeat={0}
              cursor={true}
              className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-violet-400"
            />
          </h1>
        </div>
        
        {/* Simple subtitle */}
        <div className="text-slate-300 text-xl max-w-2xl mx-auto text-center mb-6 w-full">
          <TypeAnimation
            sequence={[
              'Choose a language and level to start practicing your conversation skills with an AI tutor.',
              3000
            ]}
            wrapper="p"
            speed={50}
            style={{ display: 'inline-block' }}
            repeat={0}
            cursor={false}
            className="text-slate-300"
          />
        </div>
        
        {/* Animated language greetings */}
        <div className="relative h-12 max-w-2xl mx-auto text-center mb-12 w-full overflow-hidden">
          <div className="absolute inset-0 flex justify-center items-center animate-fade-in opacity-0" style={{ animationDelay: '0s', animationDuration: '4s', animationFillMode: 'forwards' }}>
            <p className="text-slate-300 text-lg font-medium">Welcome to your language learning journey</p>
          </div>
          <div className="absolute inset-0 flex justify-center items-center animate-fade-in opacity-0" style={{ animationDelay: '4s', animationDuration: '4s', animationFillMode: 'forwards' }}>
            <p className="text-slate-300 text-lg font-medium">Welkom bij je taalreis</p>
          </div>
          <div className="absolute inset-0 flex justify-center items-center animate-fade-in opacity-0" style={{ animationDelay: '8s', animationDuration: '4s', animationFillMode: 'forwards' }}>
            <p className="text-slate-300 text-lg font-medium">Bienvenido a tu viaje de aprendizaje de idiomas</p>
          </div>
          <div className="absolute inset-0 flex justify-center items-center animate-fade-in opacity-0" style={{ animationDelay: '12s', animationDuration: '4s', animationFillMode: 'forwards' }}>
            <p className="text-slate-300 text-lg font-medium">Willkommen auf deiner Sprachlernreise</p>
          </div>
          <div className="absolute inset-0 flex justify-center items-center animate-fade-in opacity-0" style={{ animationDelay: '16s', animationDuration: '4s', animationFillMode: 'forwards' }}>
            <p className="text-slate-300 text-lg font-medium">Bienvenue dans votre parcours d'apprentissage des langues</p>
          </div>
          <div className="absolute inset-0 flex justify-center items-center animate-fade-in opacity-0" style={{ animationDelay: '20s', animationDuration: '4s', animationFillMode: 'forwards' }}>
            <p className="text-slate-300 text-lg font-medium">Bem-vindo à sua jornada de aprendizado de idiomas</p>
          </div>
        </div>
        
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
            <p className="text-center text-gray-500 dark:text-gray-400">Redirecting to language selection...</p>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-6 mt-8">

            
            <div className="flex flex-col space-y-8 w-full max-w-xl mt-8">
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
                className="w-full flex items-center justify-center relative overflow-hidden group bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold py-5 px-8 rounded-lg shadow-sm transition-all duration-300 hover:shadow-md text-lg"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    <span>Navigating...</span>
                  </>
                ) : (
                  <>
                    <span className="relative z-10">Explore Languages</span>
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
                    className="w-full py-5 px-8 border border-indigo-500 text-indigo-600 rounded-lg hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 flex items-center justify-center relative overflow-hidden group transition-all duration-300 hover:shadow-md hover:shadow-indigo-500/20 font-semibold text-lg"
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
                    className="w-full py-5 px-8 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-600 dark:text-gray-200 dark:hover:bg-slate-700 flex items-center justify-center relative overflow-hidden group transition-all duration-300 hover:shadow-md hover:shadow-slate-500/20 font-semibold text-lg"
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
              

            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
