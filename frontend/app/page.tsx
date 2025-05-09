'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';
import NavBar from '@/components/nav-bar';
import { TypeAnimation } from 'react-type-animation';
import FAQSection from '@/components/faq-section';
import './landing-sections.css';
import { motion } from 'framer-motion';

// Export the main component
export default function Home() {
  const { user, loading: authLoading } = useAuth();
  const navigation = useNavigation();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // For automatic navigation if needed
  const [shouldAutoNavigate, setShouldAutoNavigate] = useState(false);
  const [maxRedirectAttempts] = useState(3);
  const redirectAttemptsRef = useRef(0);
  
  // Scroll to section function
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  // Handle automatic navigation based on conditions
  const handleAutomaticNavigation = () => {
    redirectAttemptsRef.current += 1;
    
    if (redirectAttemptsRef.current > maxRedirectAttempts) {
      console.log('Hit max redirect attempts, showing manual navigation options');
      setShouldAutoNavigate(false);
      setIsLoading(false);
      return;
    }
    
    // Check for active practice session
    const hasPendingPractice = localStorage.getItem('pendingPractice') === 'true';
    if (hasPendingPractice && user) {
      console.log('User has pending practice, redirecting to profile');
      // Use an available navigation method
      navigation.navigateToProfile();
      return;
    }
    
    // More navigation logic can be added here
    
    // If no automatic navigation is needed
    setShouldAutoNavigate(false);
    setIsLoading(false);
  };
  
  // Handle start learning button click
  const handleStartLearning = () => {
    setIsLoading(true);
    
    // Clear any previous selections
    sessionStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLevel');
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicPrompt');
    
    // Set a flag to prevent automatic redirects
    sessionStorage.setItem('manualNavigation', 'true');
    
    // Navigate to language selection
    try {
      navigation.navigateToLanguageSelection();
    } catch (err) {
      console.error('Navigation failed:', err);
      setError('Navigation failed. Please try again or refresh the page.');
      setIsLoading(false);
    }
  };
  
  // Handle sign in button click
  const handleSignIn = () => {
    setIsLoading(true);
    
    // Set a flag to prevent automatic redirects
    sessionStorage.setItem('manualNavigation', 'true');
    
    // Navigate to login page
    try {
      navigation.navigateToLogin();
    } catch (err) {
      console.error('Navigation failed:', err);
      setError('Navigation failed. Please try again or refresh the page.');
      setIsLoading(false);
    }
  };
  
  // Initial useEffect for auth checking and redirects
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Wait for auth to be checked
    if (authLoading) return;
    
    // Log environment information for debugging
    console.log('Home page loaded at:', new Date().toISOString());
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Auth status:', user ? 'Logged in' : 'Not logged in');
    console.log('Current pathname:', window.location.pathname);
    
    // Check if we should continue with normal page loading
    if (shouldAutoNavigate) {
      handleAutomaticNavigation();
    } else {
      // Clear loading state if we're not redirecting
      setIsLoading(false);
    }
  }, [authLoading, user, shouldAutoNavigate]);
  
  return (
    <div className="min-h-screen overflow-x-hidden w-full">
      <NavBar />
      
      {isLoading ? (
        <div className="min-h-screen flex items-center justify-center bg-[var(--turquoise)]">
          <div className="text-center">
            <div className="animate-pulse flex flex-col items-center">
              <div className="rounded-full h-16 w-16 bg-white/20 mb-4 flex items-center justify-center">
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-8 w-8 text-white animate-pulse" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                >
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  <line x1="12" x2="12" y1="19" y2="22"></line>
                </svg>
              </div>
              <p className="text-white text-xl font-medium">Loading...</p>
              <p className="text-white/70 text-sm mt-2">
                Preparing your language learning experience
              </p>
            </div>
          </div>
        </div>
      ) : (
        <main className="start-screen">
          {/* First Section */}
          <section id="section1" className="landing-section landing-first pt-16">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h1 
                className="text-4xl md:text-5xl lg:text-6xl font-bold"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <span className="block mb-2">Welcome to</span>
                <span className="text-white">Language Tutor</span>
              </motion.h1>
              
              <motion.div 
                className="mt-4 mb-8 text-white/90 text-xl md:text-2xl"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <TypeAnimation
                  sequence={[
                    'Practice speaking a new language',
                    2000,
                    'Get real-time pronunciation feedback',
                    2000,
                    'Learn through natural conversations',
                    2000,
                  ]}
                  wrapper="span"
                  speed={50}
                  repeat={Infinity}
                  className="block"
                />
              </motion.div>
              
              <motion.p 
                className="text-white/90 text-lg max-w-2xl mx-auto mb-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.5 }}
              >
                Your personal AI language tutor that adapts to your learning style and helps you become fluent through natural conversations.
              </motion.p>
              
              <motion.button
                className="start-button"
                onClick={handleStartLearning}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.7 }}
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
                    <span>Start Your Journey</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </motion.button>
              
              <div className="scroll-indicator" onClick={() => scrollToSection('section2')}>
                <span>Scroll to learn more</span>
                <div className="scroll-arrow"></div>
              </div>
            </div>
          </section>

          {/* Second Section */}
          <section id="section2" className="landing-section landing-second">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl font-bold text-gray-800 mb-8"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                How It Works
              </motion.h2>
              
              <div className="feature-cards">
                <motion.div 
                  className="feature-card"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  viewport={{ once: true }}
                >
                  <div className="card-number">1</div>
                  <h3>Choose Your Language</h3>
                  <p>Select from multiple languages including Spanish, French, German, Dutch, and more.</p>
                </motion.div>
                
                <motion.div 
                  className="feature-card"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="card-number">2</div>
                  <h3>Select Your Level</h3>
                  <p>From beginner to advanced, our system adapts to your proficiency level.</p>
                </motion.div>
                
                <motion.div 
                  className="feature-card"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  viewport={{ once: true }}
                >
                  <div className="card-number">3</div>
                  <h3>Practice Conversations</h3>
                  <p>Engage in natural conversations with our AI tutor on various topics, with real-time feedback.</p>
                </motion.div>
              </div>
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
              
              {/* FAQ Accordion Section */}
              <FAQSection />
              
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
                style={{ marginTop: '2rem', backgroundColor: 'var(--turquoise)' }}
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
        </main>
      )}
    </div>
  );
}
