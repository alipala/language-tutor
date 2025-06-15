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
          <section id="features" className="landing-section landing-first">
            <div className="section-background"></div>
            <div className="section-content">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-10 border-2 border-white/30 shadow-[0_10px_40px_-15px_rgba(0,0,0,0.2)] w-[125%] max-w-none -mx-[12.5%] py-16">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                  {/* Left Column - Content */}
                  <div className="text-left">
                  <motion.h1 
                    className="text-4xl md:text-5xl lg:text-6xl font-bold text-left"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6 }}
                  >
                    <span className="block mb-2 text-gray-800">Welcome to</span>
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
            
            <motion.div 
              className="flex flex-col items-center justify-center mt-16 cursor-pointer group"
              onClick={() => scrollToSection('how-it-works')}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1.2 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <motion.div
                className="relative bg-white/10 backdrop-blur-md rounded-full p-4 border border-white/20 shadow-lg group-hover:bg-white/20 transition-all duration-300"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <motion.svg 
                  className="w-6 h-6 text-[#4ECFBF] group-hover:text-[#3a9e92]" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                  animate={{ y: [0, 4, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </motion.svg>
                
                {/* Ripple effect */}
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-white/30"
                  animate={{ scale: [1, 1.5, 1], opacity: [0.7, 0, 0.7] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                />
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-white/20"
                  animate={{ scale: [1, 2, 1], opacity: [0.5, 0, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                />
              </motion.div>
              
              <motion.span 
                className="mt-4 text-white/80 text-sm font-medium tracking-wide group-hover:text-white transition-colors duration-300"
                animate={{ opacity: [0.8, 1, 0.8] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                Discover How It Works
              </motion.span>
              
              <motion.div
                className="mt-2 w-16 h-0.5 bg-gradient-to-r from-transparent via-white/50 to-transparent"
                animate={{ scaleX: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
            </motion.div>
          </section>

          {/* How It Works Section */}
          <section id="how-it-works" className="landing-section landing-second">
            <div className="section-background"></div>
            <div className="section-content">
              <motion.h2 
                className="text-3xl md:text-4xl font-bold text-white mb-6"
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                How It Works
              </motion.h2>
              
              
              {/* Learning Journey Flow */}
              <div className="max-w-7xl mx-auto mb-20">
                {/* Assessment Path */}
                <motion.div
                  className="mb-16"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                >
                  <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold text-gray-800 mb-3">🎯 Assessment Mode</h3>
                    <p className="text-gray-600 text-lg">Discover your current level with AI-powered speaking assessment</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">Speak Naturally</h4>
                      <p className="text-gray-600 text-sm">Record yourself speaking for 15-60 seconds on any topic</p>
                    </div>
                    
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">AI Analysis</h4>
                      <p className="text-gray-600 text-sm">Advanced AI evaluates pronunciation, grammar, vocabulary & fluency</p>
                    </div>
                    
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">CEFR Level</h4>
                      <p className="text-gray-600 text-sm">Get your official language level from A1 (beginner) to C2 (native)</p>
                    </div>
                    
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">Start Practicing</h4>
                      <p className="text-gray-600 text-sm">Begin personalized conversations based on your assessed level</p>
                    </div>
                  </div>
                </motion.div>

                {/* Practice Mode Path */}
                <motion.div
                  className="mb-16"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold text-gray-800 mb-3">💬 Practice Mode</h3>
                    <p className="text-gray-600 text-lg">Engage in real-time conversations with your AI language tutor</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 0h10m-10 0a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2M9 12h6m-6 4h6" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">Choose Your Topic</h4>
                      <p className="text-gray-600 text-sm">Select from popular topics like travel, food, work, or create your own custom conversation theme</p>
                    </div>
                    
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">Real-Time Conversation</h4>
                      <p className="text-gray-600 text-sm">Speak naturally with our AI tutor using WebRTC technology for instant voice interaction - just like talking to a real person</p>
                    </div>
                    
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">Instant Feedback</h4>
                      <p className="text-gray-600 text-sm">Get immediate corrections and suggestions as you speak, with detailed analysis of your pronunciation, grammar, and vocabulary</p>
                    </div>
                    
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 text-center shadow-lg">
                      <div className="w-16 h-16 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                      <h4 className="text-gray-800 font-semibold mb-2">Adaptive Learning</h4>
                      <p className="text-gray-600 text-sm">Personalized lessons that adapt to your learning pace and style</p>
                    </div>
                  </div>
                </motion.div>

                {/* Progress Tracking */}
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.4 }}
                  viewport={{ once: true }}
                >
                  <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold text-gray-800 mb-3">📊 Progress Tracking</h3>
                    <p className="text-gray-600 text-lg">Monitor your improvement with detailed analytics and achievements</p>
                  </div>
                  
                  <div className="bg-white/90 backdrop-blur-sm rounded-xl p-8 border border-gray-200 shadow-lg">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        </div>
                        <h4 className="text-gray-800 font-semibold mb-2">Conversation History</h4>
                        <p className="text-gray-600 text-sm">Save and review all your practice sessions with AI-generated summaries</p>
                      </div>
                      
                      <div className="text-center">
                        <div className="w-16 h-16 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                          </svg>
                        </div>
                        <h4 className="text-gray-800 font-semibold mb-2">Learning Streaks</h4>
                        <p className="text-gray-600 text-sm">Build daily practice habits and maintain your learning momentum</p>
                      </div>
                      
                      <div className="text-center">
                        <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                          </svg>
                        </div>
                        <h4 className="text-gray-800 font-semibold mb-2">Achievements</h4>
                        <p className="text-gray-600 text-sm">Unlock badges and milestones as you reach your language learning goals</p>
                      </div>
                      
                      <div className="text-center">
                        <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                        </div>
                        <h4 className="text-gray-800 font-semibold mb-2">Detailed Analytics</h4>
                        <p className="text-gray-600 text-sm">Track your speaking time, complexity growth, and improvement areas</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </div>
              
            </div>
            
            <motion.div 
              className="flex flex-col items-center justify-center mt-16 cursor-pointer group"
              onClick={() => scrollToSection('pricing')}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <motion.div
                className="relative bg-white/10 backdrop-blur-md rounded-full p-4 border border-white/20 shadow-lg group-hover:bg-white/20 transition-all duration-300"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <motion.svg 
                  className="w-6 h-6 text-[#4ECFBF] group-hover:text-[#3a9e92]" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                  animate={{ y: [0, 4, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </motion.svg>
                
                {/* Ripple effect */}
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-white/30"
                  animate={{ scale: [1, 1.5, 1], opacity: [0.7, 0, 0.7] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                />
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-white/20"
                  animate={{ scale: [1, 2, 1], opacity: [0.5, 0, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                />
              </motion.div>
              
              <motion.span 
                className="mt-4 text-white/80 text-sm font-medium tracking-wide group-hover:text-white transition-colors duration-300"
                animate={{ opacity: [0.8, 1, 0.8] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                Explore Our Plans
              </motion.span>
              
              <motion.div
                className="mt-2 w-16 h-0.5 bg-gradient-to-r from-transparent via-white/50 to-transparent"
                animate={{ scaleX: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
            </motion.div>
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
                  className="bg-white rounded-xl shadow-lg overflow-hidden border-2 border-[#4ECFBF] transition-transform duration-300 hover:shadow-xl"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -5 }}
                >
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-[#4ECFBF] mb-2">Basic</h3>
                    <div className="flex items-end mb-4">
                      <span className="text-4xl font-bold text-gray-800">$9</span>
                      <span className="text-gray-600 ml-1">/month</span>
                    </div>
                    <p className="text-gray-600 mb-6">Perfect for casual learners</p>
                    
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>2 language options</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>2 practice sessions daily</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Basic progress tracking</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Email support</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="px-6 pb-6">
                    <button 
                      className="w-full py-3 bg-[#4ECFBF] text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors shadow-md"
                      onClick={handleStartLearning}
                    >
                      Get Started
                    </button>
                  </div>
                </motion.div>
                
                {/* Premium Plan - Most Popular */}
                <motion.div
                  className="bg-white rounded-xl shadow-xl overflow-hidden border-2 border-[#4ECFBF] relative transition-transform duration-300 scale-105 md:scale-110 z-10"
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
                      <span className="text-4xl font-bold text-gray-800">$19</span>
                      <span className="text-gray-600 ml-1">/month</span>
                    </div>
                    <p className="text-gray-600 mb-6">Ideal for serious language learners</p>
                    
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>All 6 language options</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Unlimited practice sessions</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Advanced progress tracking</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Priority email support</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Downloadable lessons</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="px-6 pb-6">
                    <button 
                      className="w-full py-3 bg-[#4ECFBF] text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors shadow-md"
                      onClick={handleStartLearning}
                    >
                      Get Started
                    </button>
                  </div>
                </motion.div>
                
                {/* Business Plan */}
                <motion.div
                  className="bg-white rounded-xl shadow-lg overflow-hidden border-2 border-[#4ECFBF] transition-transform duration-300 hover:shadow-xl"
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -5 }}
                >
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-[#4ECFBF] mb-2">Business</h3>
                    <div className="flex items-end mb-4">
                      <span className="text-4xl font-bold text-gray-800">$49</span>
                      <span className="text-gray-600 ml-1">/month</span>
                    </div>
                    <p className="text-gray-600 mb-6">For teams and organizations</p>
                    
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>All Premium features</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Up to 5 team members</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Team progress dashboard</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Dedicated account manager</span>
                      </li>
                      <li className="flex items-center text-gray-700">
                        <svg className="w-5 h-5 mr-2 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Custom learning paths</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="px-6 pb-6">
                    <button 
                      className="w-full py-3 bg-[#4ECFBF] text-white font-medium rounded-lg hover:bg-[#3a9e92] transition-colors shadow-md"
                      onClick={handleStartLearning}
                    >
                      Contact Sales
                    </button>
                  </div>
                </motion.div>
              </div>
              
              <motion.div
                className="bg-white rounded-xl p-6 border-2 border-[#4ECFBF] max-w-4xl mx-auto text-center shadow-lg"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                viewport={{ once: true }}
              >
                <h3 className="text-xl font-bold text-[#4ECFBF] mb-3">Need a custom solution?</h3>
                <p className="text-gray-600 mb-4">Contact us for enterprise pricing and customized language training programs for larger organizations.</p>
                <button 
                  className="px-6 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors inline-flex items-center shadow-md"
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

          {/* Final Section with FAQ */}
          <section id="faq" className="landing-section landing-third">
            <div className="section-background"></div>
            <div className="section-content">
              {/* FAQ Section */}
              <FAQSection />
              
              <motion.button
                className="px-6 py-3 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors shadow-md flex items-center mx-auto border-2 border-white"
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
                    <span>Get Started Now</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </>
                )}
              </motion.button>
              
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
