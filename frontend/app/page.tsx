'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';
import NavBar from '@/components/nav-bar';
import { TypeAnimation } from 'react-type-animation';
import FAQSection from '@/components/faq-section';
import LearningPlanDashboard from '@/components/dashboard/LearningPlanDashboard';
import ProjectKnowledgeChatbot from '@/components/project-knowledge-chatbot';
import SubscriptionPlans from '@/components/subscription-plans';
import SoundWaveLoader from '@/components/sound-wave-loader';
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
  
  // Video player state
  const [showVideo, setShowVideo] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  
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

  // Show dashboard for authenticated users
  if (!authLoading && user) {
    return (
      <div className="min-h-screen overflow-x-hidden w-full">
        <NavBar />
        <LearningPlanDashboard />
        {/* Project Knowledge Chatbot - Available for authenticated users too */}
        <ProjectKnowledgeChatbot />
      </div>
    );
  }
  
  // Show landing page for guests
  return (
    <div className="min-h-screen overflow-x-hidden w-full">
      <NavBar />
      
      {isLoading ? (
        <div className="min-h-screen flex items-center justify-center bg-white">
          <SoundWaveLoader 
            size="lg"
            color="#4ECFBF"
            text="Loading..."
            subtext="Preparing your language learning experience"
          />
        </div>
      ) : (
        <main className="start-screen">
          {/* First Section */}
          <section id="features" className="landing-section landing-first">
            <div className="section-background"></div>
            <div className="section-content">
              <div className="bg-white rounded-xl p-10 border-2 border-gray-200 shadow-[0_10px_40px_-15px_rgba(0,0,0,0.2)] w-[125%] max-w-none -mx-[12.5%] py-16">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                  {/* Left Column - Content */}
                  <div className="text-left">
                  <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-left">
                    <span className="block mb-2 text-gray-800">Hey there! 👋</span>
                    <span className="animated-gradient-text">Speak Fluently in 5 Minutes Daily</span>
                  </h1>
                  
                  <div className="section-description max-w-xl text-left mb-8 text-gray-600 text-lg font-medium">
                    Master any language through real-time AI conversations that adapt to your schedule. From beginner to confident speaker in weeks, not years.
                  </div>
                  
                  <div className="flex flex-col sm:flex-row justify-start gap-4 mb-8 w-full">
                    {/* PRIMARY BUTTON - Start Speaking Today */}
                    <button
                      onClick={() => window.location.href = '/flow'}
                      className="inline-flex items-center justify-center px-5 py-3 min-h-[48px] w-full sm:w-fit text-base font-medium text-white bg-[#4ECFBF] border-2 border-[#4ECFBF] rounded-xl hover:bg-[#3a9e92] hover:border-[#3a9e92] transition-all duration-300 transform hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:ring-offset-2"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                          <span>Loading...</span>
                        </>
                      ) : (
                        <>
                          <span>Start Speaking Today</span>
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </>
                      )}
                    </button>
                    
                    {/* SECONDARY BUTTON - See How It Works */}
                    <button
                      onClick={() => scrollToSection('how-it-works')}
                      className="inline-flex items-center justify-center px-5 py-3 min-h-[48px] w-full sm:w-fit text-base font-medium text-[#4ECFBF] bg-white border-2 border-[#4ECFBF] rounded-xl hover:bg-[#4ECFBF] hover:text-white transition-all duration-300 transform hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:ring-offset-2"
                    >
                      <span>See How It Works</span>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="flex flex-wrap gap-6 text-sm text-gray-600">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"/>
                      </svg>
                      <span>Real-time voice conversations</span>
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2 text-[#4ECFBF]" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"/>
                      </svg>
                      <span>6 languages available</span>
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2 text-[#4ECFBF]" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"/>
                      </svg>
                      <span>Available 24/7</span>
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2 text-gray-800" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"/>
                      </svg>
                      <span>Personalized learning plans</span>
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"/>
                      </svg>
                      <span>Instant feedback & corrections</span>
                    </div>
                  </div>
                </div>
                
                {/* Right Column - Conversation Demo with Video */}
                <div 
                  className="hidden md:block rounded-xl bg-white border border-gray-200 p-4 shadow-[0_10px_40px_-15px_rgba(0,0,0,0.2)] hover:shadow-[0_20px_60px_-15px_rgba(58,158,146,0.25)] transition-all duration-300 transform scale-110 -mt-8 relative cursor-pointer group"
                  onMouseEnter={() => setIsHovering(true)}
                  onMouseLeave={() => setIsHovering(false)}
                  onClick={() => setShowVideo(true)}
                >
                  <div className="bg-gray-100 rounded-t-lg p-2 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#FF5F57] mr-2"></div>
                      <div className="w-3 h-3 rounded-full bg-[#FFBD2E] mr-2"></div>
                      <div className="w-3 h-3 rounded-full bg-[#28CA41]"></div>
                    </div>
                    <div className="text-center text-sm text-gray-700 font-medium">
                      {showVideo ? 'Live Demo Video' : 'Realtime Conversation'}
                    </div>
                    <div className="w-12"></div>
                  </div>
                  
                  {!showVideo ? (
                    <>
                      {/* Conversation Demo Content */}
                      <div className="h-80 overflow-hidden p-3 space-y-2 relative">
                        {/* Coach Message */}
                        <div className="flex items-start">
                          <div className="w-6 h-6 rounded-full bg-[#3a9e92] flex items-center justify-center shrink-0 mr-2 overflow-hidden">
                            <img src="/images/tutors/alloy.svg" alt="Alloy" className="w-full h-full object-cover" />
                          </div>
                          <div className="bg-[#e6f7f5] rounded-lg p-2 text-gray-700 max-w-[75%] border border-[#3a9e92]/20">
                            <p className="text-sm">Hi there! Let's talk about your hobbies. What do you enjoy doing?</p>
                          </div>
                        </div>
                        
                        {/* User Message */}
                        <div className="flex items-start justify-end">
                          <div className="bg-[#edf2fd] rounded-lg p-2 text-gray-700 max-w-[75%] mr-2 border border-blue-500/20">
                            <p className="text-sm">I enjoy playing tennis and reading history books.</p>
                          </div>
                          <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white shrink-0 text-xs">
                            You
                          </div>
                        </div>
                        
                        {/* Feedback */}
                        <div className="bg-gray-50 rounded-lg p-2 border border-gray-200">
                          <div className="text-xs text-gray-600 font-medium mb-1">Feedback:</div>
                          <div className="grid grid-cols-3 gap-1 text-xs">
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
                          <div className="w-6 h-6 rounded-full bg-[#3a9e92] flex items-center justify-center shrink-0 mr-2 overflow-hidden">
                            <img src="/images/tutors/alloy.svg" alt="Alloy" className="w-full h-full object-cover" />
                          </div>
                          <div className="bg-[#e6f7f5] rounded-lg p-2 text-gray-700 max-w-[75%] border border-[#3a9e92]/20">
                            <p className="text-sm">Great! What period of history interests you most?</p>
                          </div>
                        </div>
                        
                        {/* User Reply */}
                        <div className="flex items-start justify-end">
                          <div className="bg-[#edf2fd] rounded-lg p-2 text-gray-700 max-w-[75%] mr-2 border border-blue-500/20">
                            <p className="text-sm">I'm fascinated by ancient Rome and medieval Europe.</p>
                          </div>
                          <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white shrink-0 text-xs">
                            You
                          </div>
                        </div>
                        
                        {/* Input Area */}
                        <div className="mt-auto border-t border-gray-200 pt-2">
                          <div className="bg-gray-100 rounded-full flex items-center p-1 pr-2 w-1/2">
                            <div className="relative">
                              <button className="w-6 h-6 rounded-full bg-[#F75A5A] flex items-center justify-center text-white mr-2 relative z-10">
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                                </svg>
                              </button>
                              {/* Sound Circle Animation */}
                              <div className="absolute inset-0 rounded-full bg-[#F75A5A] opacity-30 animate-ping"></div>
                              <div className="absolute inset-0 rounded-full bg-[#F75A5A] opacity-20 animate-pulse" style={{animationDelay: '0.5s'}}></div>
                            </div>
                            <div className="text-gray-500 text-xs">Press to speak...</div>
                          </div>
                        </div>
                        
                        {/* Video Play Button Overlay */}
                        <div className={`absolute inset-0 bg-black/40 backdrop-blur-sm rounded-lg flex items-center justify-center transition-all duration-300 ${
                          isHovering ? 'opacity-100' : 'opacity-0'
                        }`}>
                          <div className="bg-white/90 backdrop-blur-sm rounded-full p-6 shadow-2xl transform transition-all duration-300 hover:scale-110 group-hover:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.3)]">
                            <svg className="w-12 h-12 text-[#4ECFBF] ml-1" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z"/>
                            </svg>
                          </div>
                          <div className="absolute -bottom-16 left-1/2 transform -translate-x-1/2 bg-white/90 backdrop-blur-sm rounded-lg px-4 py-2 shadow-lg">
                            <p className="text-sm font-medium text-gray-800 whitespace-nowrap">
                              🎥 Watch Live Demo
                            </p>
                            <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1 w-2 h-2 bg-white/90 rotate-45"></div>
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    /* YouTube Video Player */
                    <div className="h-80 relative">
                      <iframe
                        src="https://www.youtube.com/embed/64N7w2dFfDw?autoplay=1&rel=0&modestbranding=1"
                        title="Language Tutor Demo"
                        className="w-full h-full rounded-b-lg"
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      ></iframe>
                      
                      {/* Close Video Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowVideo(false);
                        }}
                        className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white rounded-full p-2 transition-all duration-200 z-10"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
                </div>
              </div>
            </div>
            
            <div 
              className="flex flex-col items-center justify-center mt-16 cursor-pointer group hover:scale-105 active:scale-95 transition-transform duration-300"
              onClick={() => scrollToSection('how-it-works')}
            >
              <div className="relative bg-white/10 backdrop-blur-md rounded-full p-4 border border-white/20 shadow-lg group-hover:bg-white/20 transition-all duration-300">
                <svg 
                  className="w-6 h-6 text-[#4ECFBF] group-hover:text-[#3a9e92]" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
              
              <span className="mt-4 text-white/80 text-sm font-medium tracking-wide group-hover:text-white transition-colors duration-300">
                Discover How It Works
              </span>
              
              <div className="mt-2 w-16 h-0.5 bg-gradient-to-r from-transparent via-white/50 to-transparent"></div>
            </div>
          </section>

          {/* How It Works Section */}
          <section id="how-it-works" className="landing-section landing-second">
            <div className="section-background"></div>
            <div className="section-content">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                How It Works
              </h2>
              
              
              {/* Learning Journey Flow */}
              <div className="max-w-7xl mx-auto mb-20">
                {/* Assessment Path */}
                <div className="mb-16">
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
                </div>

                {/* Practice Mode Path */}
                <div className="mb-16">
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
                </div>

                {/* Progress Tracking */}
                <div>
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
                </div>
              </div>
              
            </div>
            
            <div 
              className="flex flex-col items-center justify-center mt-16 cursor-pointer group hover:scale-105 active:scale-95 transition-transform duration-300"
              onClick={() => scrollToSection('pricing')}
            >
              <div className="relative bg-white/10 backdrop-blur-md rounded-full p-4 border border-white/20 shadow-lg group-hover:bg-white/20 transition-all duration-300">
                <svg 
                  className="w-6 h-6 text-[#4ECFBF] group-hover:text-[#3a9e92]" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
              
              <span className="mt-4 text-white/80 text-sm font-medium tracking-wide group-hover:text-white transition-colors duration-300">
                Explore Our Plans
              </span>
              
              <div className="mt-2 w-16 h-0.5 bg-gradient-to-r from-transparent via-white/50 to-transparent"></div>
            </div>
          </section>

          {/* Pricing Section - New Subscription Plans Component */}
          <SubscriptionPlans />

          {/* Final Section with FAQ */}
          <section id="faq" className="landing-section landing-third">
            <div className="section-background"></div>
            <div className="section-content">
              {/* FAQ Section */}
              <FAQSection />
              
              <button
                className="px-6 py-3 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors shadow-md flex items-center mx-auto border-2 border-white hover:scale-105 active:scale-98"
                onClick={handleStartLearning}
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
              </button>
              
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
      
      {/* Project Knowledge Chatbot - Available on all pages */}
      <ProjectKnowledgeChatbot />
    </div>
  );
}
