'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/nav-bar';
import { TypeAnimation } from 'react-type-animation';
import './landing-sections.css';
import { motion } from 'framer-motion';

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
  // Scroll to section function
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Handle start learning button click
  const handleStartLearning = () => {
    try {
      // Show loading state
      setIsLoading(true);
      setError(null);
      
      // Clear any existing session data except user preferences
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
  };

  // Handle sign in button click
  const handleSignIn = () => {
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
  };

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      
      {isLoading ? (
        <div className="flex-grow flex flex-col items-center justify-center p-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
          <p className="text-center text-white/80">Redirecting to language selection...</p>
        </div>
      ) : (
        <div id="startScreen" className="start-screen">
          {/* First Section */}
          <section id="section1" className="landing-section landing-first">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h1
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                <TypeAnimation
                  sequence={[
                    'Master Languages with AI',
                    2000,
                    'Speak with Confidence',
                    1500,
                    'Learn at Your Own Pace',
                    1500,
                    'Practice Real Conversations',
                    1500,
                  ]}
                  wrapper="span"
                  speed={50}
                  repeat={Infinity}
                  cursor={true}
                />
              </motion.h1>
              
              <motion.p 
                className="section-description"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              >
                Your personal AI language tutor that adapts to your learning style and helps you become fluent through natural conversations.
              </motion.p>
              
              <motion.button
                className="start-button"
                onClick={handleStartLearning}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
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
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </motion.button>
              
              {!user && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.9 }}
                  className="mt-4"
                >
                  <button
                    onClick={handleSignIn}
                    className="text-white/90 hover:text-white underline text-sm font-medium transition-colors"
                    disabled={isLoading}
                  >
                    Already have an account? Sign in
                  </button>
                </motion.div>
              )}
            </div>
            
            <div className="scroll-indicator" onClick={() => scrollToSection('section2')}>
              <span>Scroll to explore</span>
              <div className="scroll-arrow"></div>
            </div>
          </section>

          {/* Second Section */}
          <section id="section2" className="landing-section landing-second">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl font-bold text-white mb-8"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                Why Language Tutor is Different
              </motion.h2>
              
              <div className="feature-cards">
                <motion.div 
                  className="feature-card"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  viewport={{ once: true }}
                >
                  <div className="card-number">1</div>
                  <h3>AI-Powered Conversations</h3>
                  <p>Practice speaking with our advanced AI tutor that responds naturally, corrects your mistakes, and adapts to your learning pace. Experience real-world conversations that prepare you for actual language use.</p>
                </motion.div>
                
                <motion.div 
                  className="feature-card"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  viewport={{ once: true }}
                >
                  <div className="card-number">2</div>
                  <h3>Personalized Learning Path</h3>
                  <p>Our system adapts to your proficiency level, learning style, and interests. Get customized lessons, vocabulary, and speaking exercises that focus on your specific needs and goals in language learning.</p>
                </motion.div>
                
                <motion.div 
                  className="feature-card"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.5 }}
                  viewport={{ once: true }}
                >
                  <div className="card-number">3</div>
                  <h3>Instant Feedback & Progress</h3>
                  <p>Receive immediate feedback on pronunciation, grammar, and vocabulary usage. Track your improvement over time with detailed progress reports and see how your language skills evolve with each practice session.</p>
                </motion.div>
              </div>
              
              <motion.button
                className="start-button mt-12"
                onClick={handleStartLearning}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.7 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                viewport={{ once: true }}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    <span>Navigating...</span>
                  </>
                ) : (
                  <>
                    <span>Start Your Journey</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </motion.button>
            </div>
          </section>

          {/* Third Section */}
          <section id="section3" className="landing-section landing-third">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl font-bold text-white mb-8"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                Ready to Become Fluent?
              </motion.h2>
              
              <motion.p 
                className="text-white/90 text-lg max-w-2xl mx-auto mb-10"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                viewport={{ once: true }}
              >
                Join thousands of language learners who have improved their speaking skills with our AI-powered platform. Start your free trial today and experience the future of language learning.
              </motion.p>
              
              <motion.button
                className="start-button"
                onClick={handleStartLearning}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                viewport={{ once: true }}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    <span>Navigating...</span>
                  </>
                ) : (
                  <>
                    <span>Get Started for Free</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </motion.button>
              
              <div className="contact-info">
                <p className="email">Questions? Contact us at: support@languagetutor.ai</p>
                <p className="project-info">Powered by advanced AI language models</p>
                <p className="copyright">© 2025 Language Tutor. All rights reserved.</p>
              </div>
              
              {error && (
                <div className="p-4 glass-card rounded-lg mt-8 border border-white/20 max-w-md mx-auto">
                  <p className="text-sm text-white/80">
                    {error}
                  </p>
                </div>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
