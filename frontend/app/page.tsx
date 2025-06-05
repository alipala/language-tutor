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
          <section id="features" className="landing-section landing-first pt-2">
            <div className="section-background"></div>
            <div className="section-content">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-10 border-2 border-white/30 shadow-[0_10px_40px_-15px_rgba(0,0,0,0.2)] hover:shadow-[0_20px_60px_-15px_rgba(255,255,255,0.15)] transition-shadow duration-300 w-[125%] max-w-none -mx-[12.5%] py-16">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                  {/* Left Column - Content */}
                  <div className="text-left">
                  <motion.h1 
                    className="text-4xl md:text-5xl lg:text-6xl font-bold text-left"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6 }}
                  >
                    <span className="block mb-2 animated-gradient-text">Welcome to</span>
                    <span className="animated-gradient-text">Your Smart Language Coach</span>
                  </motion.h1>
                  
                  <motion.div 
                    className="section-description max-w-xl text-left mb-8 text-gray-600 text-lg"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                  >
                    Your personal AI language tutor that adapts to your learning style and helps you become fluent through natural conversations.
                  </motion.div>
                  
                  <motion.div
                    className="flex flex-col sm:flex-row justify-start gap-4 mb-8 w-full"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.6 }}
                  >
                    <button
                      onClick={handleStartLearning}
                      className="start-button self-start"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                          <span>Loading...</span>
                        </>
                      ) : (
                        <>
                          <span>Start Your Journey</span>
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </>
                      )}
                    </button>
                  </motion.div>
                  
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.6, delay: 0.8 }}
                    className="flex flex-wrap gap-3 text-sm text-white/80"
                  >
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Personalized feedback</span>
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>6 languages available</span>
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Real-time corrections</span>
                    </div>
                  </motion.div>
                </div>
                
                {/* Right Column - Conversation Demo */}
                <motion.div
                  className="hidden md:block rounded-xl bg-white border border-gray-200 p-4 shadow-[0_10px_40px_-15px_rgba(0,0,0,0.2)] hover:shadow-[0_20px_60px_-15px_rgba(58,158,146,0.25)] transition-shadow duration-300"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8, delay: 0.4 }}
                >
                  <div className="bg-gray-100 rounded-t-lg p-2 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#FF5F57] mr-2"></div>
                      <div className="w-3 h-3 rounded-full bg-[#FFBD2E] mr-2"></div>
                      <div className="w-3 h-3 rounded-full bg-[#28CA41]"></div>
                    </div>
                    <div className="text-center text-sm text-gray-700 font-medium">AI Language Coach</div>
                    <div className="w-12"></div>
                  </div>
                  
                  <div className="max-h-80 overflow-y-auto p-4 space-y-4">
                    {/* Coach Message */}
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded-full bg-[#3a9e92] flex items-center justify-center text-white shrink-0 mr-3">
                        AI
                      </div>
                      <div className="bg-[#e6f7f5] rounded-lg p-3 text-gray-700 max-w-[80%] border border-[#3a9e92]/20">
                        <p>Hi there! I'd love to help you practice your English today. Let's talk about your hobbies. What do you enjoy doing in your free time?</p>
                      </div>
                    </div>
                    
                    {/* User Message */}
                    <div className="flex items-start justify-end">
                      <div className="bg-[#edf2fd] rounded-lg p-3 text-gray-700 max-w-[80%] mr-3 border border-blue-500/20">
                        <p>I enjoy playing tennis and reading books about history.</p>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white shrink-0">
                        You
                      </div>
                    </div>
                    
                    {/* Feedback */}
                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <div className="text-xs text-gray-600 font-medium mb-1">Feedback:</div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <span className="text-green-600 font-medium">Pronunciation: </span>
                          <span className="text-gray-700">90%</span>
                        </div>
                        <div>
                          <span className="text-amber-600 font-medium">Grammar: </span>
                          <span className="text-gray-700">85%</span>
                        </div>
                        <div>
                          <span className="text-blue-600 font-medium">Vocabulary: </span>
                          <span className="text-gray-700">80%</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Coach Reply */}
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded-full bg-[#3a9e92] flex items-center justify-center text-white shrink-0 mr-3">
                        AI
                      </div>
                      <div className="bg-[#e6f7f5] rounded-lg p-3 text-gray-700 max-w-[80%] border border-[#3a9e92]/20">
                        <p>That's great! Tennis is excellent for fitness. What period of history interests you the most?</p>
                      </div>
                    </div>
                    
                    {/* Input Area */}
                    <div className="mt-auto border-t border-gray-200 pt-3">
                      <div className="bg-gray-100 rounded-full flex items-center p-1 pr-3">
                        <button className="w-8 h-8 rounded-full bg-[#3a9e92] flex items-center justify-center text-white mr-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                          </svg>
                        </button>
                        <div className="text-gray-500 text-sm">Press to speak...</div>
                      </div>
                    </div>
                  </div>
                </motion.div>
                </div>
              </div>
            </div>
            
            <div className="scroll-indicator" onClick={() => scrollToSection('how-it-works')}>
              <span>Scroll to learn more</span>
              <div className="scroll-arrow"></div>
            </div>
          </section>

          {/* How It Works Section */}
          <section id="how-it-works" className="landing-section landing-second">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl md:text-4xl font-bold text-gray-800 mb-6"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                How Our Platform Works
              </motion.h2>
              
              <motion.p 
                className="text-gray-600 text-lg max-w-2xl mx-auto mb-12"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                viewport={{ once: true }}
              >
                Your Smart Language Coach uses advanced AI to create a personalized learning experience that adapts to your needs and helps you improve quickly.
              </motion.p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <motion.div 
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-white/20 flex flex-col items-center text-center h-full"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  viewport={{ once: true }}
                >
                  <div className="w-16 h-16 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-800 mb-3">1. Choose Your Language</h3>
                  <p className="text-gray-600">Select from multiple languages including Spanish, French, German, Dutch, and Portuguese. Each language offers comprehensive learning material tailored to your needs.</p>
                </motion.div>
                
                <motion.div 
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-white/20 flex flex-col items-center text-center h-full"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="w-16 h-16 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-800 mb-3">2. Assess Your Level</h3>
                  <p className="text-gray-600">Our AI assessment tool determines your current proficiency and suggests the perfect starting point. From beginner (A1) to advanced (C2), we adapt to your skills.</p>
                </motion.div>
                
                <motion.div 
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-white/20 flex flex-col items-center text-center h-full"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  viewport={{ once: true }}
                >
                  <div className="w-16 h-16 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3 drop-shadow-[0_1px_1px_rgba(0,0,0,0.3)]">3. Practice Through Conversation</h3>
                  <p className="text-white/90">Engage in natural, meaningful conversations with our AI tutor on various topics. Receive real-time feedback on pronunciation, grammar, and vocabulary usage.</p>
                </motion.div>
              </div>
              
              <motion.div
                className="bg-white/10 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-white/20 max-w-4xl mx-auto mb-8"
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                viewport={{ once: true }}
              >
                <h3 className="text-xl font-bold text-white mb-4 text-center drop-shadow-[0_1px_1px_rgba(0,0,0,0.3)]">The AI-Powered Learning Process</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-center">
                  <div className="flex flex-col items-center p-4">
                    <div className="w-12 h-12 rounded-full bg-[#4ECFBF] text-white flex items-center justify-center mb-2 text-lg font-bold">1</div>
                    <p className="text-white font-medium">Speak & Practice</p>
                    <p className="text-sm text-white/80">Practice speaking in real conversations</p>
                  </div>
                  
                  <div className="flex flex-col items-center p-4">
                    <div className="w-12 h-12 rounded-full bg-[#4ECFBF] text-white flex items-center justify-center mb-2 text-lg font-bold">2</div>
                    <p className="text-white font-medium">Get Feedback</p>
                    <p className="text-sm text-white/80">Receive instant corrections and tips</p>
                  </div>
                  
                  <div className="flex flex-col items-center p-4">
                    <div className="w-12 h-12 rounded-full bg-[#4ECFBF] text-white flex items-center justify-center mb-2 text-lg font-bold">3</div>
                    <p className="text-white font-medium">Track Progress</p>
                    <p className="text-sm text-white/80">Monitor your improvement over time</p>
                  </div>
                  
                  <div className="flex flex-col items-center p-4">
                    <div className="w-12 h-12 rounded-full bg-[#4ECFBF] text-white flex items-center justify-center mb-2 text-lg font-bold">4</div>
                    <p className="text-white font-medium">Master Language</p>
                    <p className="text-sm text-white/80">Achieve fluency through regular practice</p>
                  </div>
                </div>
              </motion.div>
              
              <motion.button
                className="px-6 py-3 bg-[#FFD63A] text-white font-medium rounded-lg hover:bg-[#ECC235] transition-colors shadow-md flex items-center mx-auto border-2 border-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.5)]"
                onClick={handleStartLearning}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.5 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                style={{ color: '#ffffff', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
              >
                Start Your Learning Journey
                <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </motion.button>
            </div>
          </section>

          {/* Pricing Section */}
          <section id="pricing" className="landing-section landing-first">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl md:text-4xl font-bold text-gray-800 mb-6"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                Choose Your Plan
              </motion.h2>
              
              <motion.p 
                className="text-gray-600 text-lg max-w-2xl mx-auto mb-12"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                viewport={{ once: true }}
              >
                Select the perfect plan for your language learning journey. All plans include unlimited AI conversations and personalized feedback.
              </motion.p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
                {/* Basic Plan */}
                <motion.div
                  className="bg-[#1a4d47]/90 backdrop-blur-sm rounded-xl shadow-lg overflow-hidden border border-[#4ECFBF]/20 transition-transform duration-300 hover:shadow-xl"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -5 }}
                >
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-[#4ECFBF] mb-2">Basic</h3>
                    <div className="flex items-end mb-4">
                      <span className="text-4xl font-bold text-white">$9</span>
                      <span className="text-white/70 ml-1">/month</span>
                    </div>
                    <p className="text-white/80 mb-6">Perfect for casual learners</p>
                    
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>2 language options</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>2 practice sessions daily</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Basic progress tracking</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Email support</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="px-6 pb-6">
                    <button 
                      className="w-full py-3 bg-[#4ECFBF]/10 text-[#4ECFBF] font-medium rounded-lg hover:bg-[#4ECFBF]/20 transition-colors"
                      onClick={handleStartLearning}
                    >
                      Get Started
                    </button>
                  </div>
                </motion.div>
                
                {/* Premium Plan - Most Popular */}
                <motion.div
                  className="bg-[#1a4d47]/90 backdrop-blur-sm rounded-xl shadow-xl overflow-hidden border-2 border-[#4ECFBF] relative transition-transform duration-300 scale-105 md:scale-110 z-10"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -5 }}
                >
                  <div className="absolute top-0 right-0 left-0 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white text-center py-1 font-medium text-sm">
                    MOST POPULAR
                  </div>
                  
                  <div className="p-6 pt-10">
                    <h3 className="text-xl font-bold text-[#4ECFBF] mb-2">Premium</h3>
                    <div className="flex items-end mb-4">
                      <span className="text-4xl font-bold text-white">$19</span>
                      <span className="text-white/70 ml-1">/month</span>
                    </div>
                    <p className="text-white/80 mb-6">Ideal for serious language learners</p>
                    
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>All 6 language options</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Unlimited practice sessions</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Advanced progress tracking</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Priority email support</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Downloadable lessons</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="px-6 pb-6">
                    <button 
                      className="w-full py-3 bg-[#4ECFBF] text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors"
                      onClick={handleStartLearning}
                    >
                      Get Started
                    </button>
                  </div>
                </motion.div>
                
                {/* Business Plan */}
                <motion.div
                  className="bg-[#1a4d47]/90 backdrop-blur-sm rounded-xl shadow-lg overflow-hidden border border-[#4ECFBF]/20 transition-transform duration-300 hover:shadow-xl"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -5 }}
                >
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-[#4ECFBF] mb-2">Business</h3>
                    <div className="flex items-end mb-4">
                      <span className="text-4xl font-bold text-white">$49</span>
                      <span className="text-white/70 ml-1">/month</span>
                    </div>
                    <p className="text-white/80 mb-6">For teams and organizations</p>
                    
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>All Premium features</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Up to 5 team members</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Team progress dashboard</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Dedicated account manager</span>
                      </li>
                      <li className="flex items-center text-white/90">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Custom learning paths</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="px-6 pb-6">
                    <button 
                      className="w-full py-3 bg-[#4ECFBF]/10 text-[#4ECFBF] font-medium rounded-lg hover:bg-[#4ECFBF]/20 transition-colors"
                      onClick={handleStartLearning}
                    >
                      Contact Sales
                    </button>
                  </div>
                </motion.div>
              </div>
              
              <motion.div
                className="bg-[#1a4d47]/90 backdrop-blur-sm rounded-xl p-6 border border-[#4ECFBF]/30 max-w-4xl mx-auto text-center"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                viewport={{ once: true }}
              >
                <h3 className="text-xl font-bold text-[#4ECFBF] mb-3">Need a custom solution?</h3>
                <p className="text-white/80 mb-4">Contact us for enterprise pricing and customized language training programs for larger organizations.</p>
                <button 
                  className="px-6 py-2 border border-[#4ECFBF] text-[#4ECFBF] rounded-lg hover:bg-[#4ECFBF] hover:text-white transition-colors inline-flex items-center"
                  onClick={() => window.location.href = "mailto:contact@yoursmartlanguagecoach.com"}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Contact Us
                </button>
              </motion.div>
            </div>
          </section>

          {/* Features Section */}
          <section id="features" className="landing-section landing-third">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl md:text-4xl font-bold text-gray-800 mb-6"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                Powerful Features for Language Mastery
              </motion.h2>
              
              <motion.p 
                className="text-gray-600 text-lg max-w-2xl mx-auto mb-12"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                viewport={{ once: true }}
              >
                Discover the innovative features that make Your Smart Language Coach the most effective way to achieve fluency in a new language.
              </motion.p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
                {/* Feature 1 */}
                <motion.div
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 h-full"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  viewport={{ once: true }}
                >
                  <div className="w-14 h-14 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-5">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Speech Recognition</h3>
                  <p className="text-white/80">Advanced AI technology accurately recognizes your speech patterns, accents, and pronunciations, providing instant feedback on how to improve.</p>
                </motion.div>
                
                {/* Feature 2 */}
                <motion.div
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 h-full"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="w-14 h-14 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-5">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Personalized Learning Plans</h3>
                  <p className="text-white/80">Custom learning paths adapt to your goals, schedule, and proficiency level. Our AI continuously adjusts to focus on areas where you need the most improvement.</p>
                </motion.div>
                
                {/* Feature 3 */}
                <motion.div
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 h-full"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  viewport={{ once: true }}
                >
                  <div className="w-14 h-14 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-5">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Smart Vocabulary Building</h3>
                  <p className="text-white/80">Our platform intelligently introduces new vocabulary based on your current knowledge, ensuring you learn relevant words that match your interests and goals.</p>
                </motion.div>
                
                {/* Feature 4 */}
                <motion.div
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 h-full"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                  viewport={{ once: true }}
                >
                  <div className="w-14 h-14 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-5">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Real Native Speakers</h3>
                  <p className="text-white/80">Learn from AI tutors that mimic the speech patterns, expressions, and cultural nuances of native speakers, giving you authentic language exposure.</p>
                </motion.div>
                
                {/* Feature 5 */}
                <motion.div
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 h-full"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.5 }}
                  viewport={{ once: true }}
                >
                  <div className="w-14 h-14 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-5">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Grammar Analysis</h3>
                  <p className="text-white/80">Receive detailed explanations of grammar rules and corrections in real-time as you speak or write, with examples that help you understand and remember.</p>
                </motion.div>
                
                {/* Feature 6 */}
                <motion.div
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 h-full"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.6 }}
                  viewport={{ once: true }}
                >
                  <div className="w-14 h-14 rounded-full bg-[#4ECFBF]/20 flex items-center justify-center mb-5">
                    <svg className="w-8 h-8 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Progress Analytics</h3>
                  <p className="text-white/80">Track your improvement with detailed analytics showing your fluency level, vocabulary size, grammar accuracy, and conversation confidence over time.</p>
                </motion.div>
              </div>
              
              <motion.div
                className="text-center"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.7 }}
                viewport={{ once: true }}
              >
                <p className="text-white/90 text-lg mb-8">Join thousands of language learners who have improved their speaking skills with our AI-powered platform.</p>
              </motion.div>
              
              {/* FAQ Section */}
              <section id="faq" className="mt-16">
                <motion.h2 
                  className="text-3xl md:text-4xl font-bold text-white mb-10 text-center"
                  initial={{ opacity: 0, y: -20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  viewport={{ once: true }}
                >
                  Frequently Asked Questions
                </motion.h2>
                <FAQSection />
              </section>
              
              <motion.button
                className="px-6 py-3 bg-[#F75A5A] text-white rounded-lg hover:bg-[#E55252] transition-colors shadow-md flex items-center mx-auto border-2 border-white"
                onClick={handleStartLearning}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                viewport={{ once: true }}
                disabled={isLoading}
                style={{ marginTop: '2rem' }}
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
                <p className="copyright">© 2025 Your Smart Language Coach. All rights reserved.</p>
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
