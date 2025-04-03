'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import PendingLearningPlanHandler from '@/components/pending-learning-plan-handler';
// Animation temporarily commented out
// import { TypeAnimation } from 'react-type-animation';
// Sound effects temporarily disabled
// import { useAudio } from '@/lib/useAudio';

interface Language {
  code: string;
  name: string;
  description?: string;
  flagSrc: string;
}

export default function LanguageSelection() {
  const router = useRouter();
  const { user } = useAuth();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // Sound effects temporarily disabled
  // const { playSelectionSound, playSuccessSound } = useAudio();

  const languages: Language[] = [
    {
      code: 'dutch',
      name: 'Dutch',
      flagSrc: '/images/flags/netherlands.svg',
    },
    {
      code: 'english',
      name: 'English',
      flagSrc: '/images/flags/uk.svg',
    },
    {
      code: 'spanish',
      name: 'Spanish',
      flagSrc: '/images/flags/spain.svg',
    },
    {
      code: 'german',
      name: 'German',
      flagSrc: '/images/flags/germany.svg',
    },
    {
      code: 'french',
      name: 'French',
      flagSrc: '/images/flags/france.svg',
    },
    {
      code: 'portuguese',
      name: 'Portuguese',
      flagSrc: '/images/flags/portugal.svg',
    },
  ];

  // Add a useEffect to handle page initialization and react to state changes
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    // Log debug information
    console.log('Language selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    console.log('Full origin:', window.location.origin);
    
    // RAILWAY SPECIFIC: Check if we're in Railway environment
    const isRailway = window.location.hostname.includes('railway.app');
    console.log('Is Railway environment:', isRailway);
    
    // Normalize URL if needed to ensure consistent path format
    const currentPath = window.location.pathname;
    if (isRailway) {
      // Different path handling for Railway
      // If URL doesn't end with /language-selection (accounting for trailing slashes)
      const normalizedPath = currentPath.endsWith('/') 
        ? currentPath.slice(0, -1) 
        : currentPath;
        
      if (normalizedPath !== '/language-selection') {
        // Only fix the path if we're not already on the correct one
        console.log('Path appears incorrect, normalizing to /language-selection');
        window.location.replace('/language-selection');
        return;
      }
    }
    
    // Check if we should redirect based on existing state
    const storedLanguage = sessionStorage.getItem('selectedLanguage');
    const storedLevel = sessionStorage.getItem('selectedLevel');
    
    // Handle case where this is an initial direct load of the language selection page
    // This is the expected behavior: user coming from home page
    if (!storedLanguage && !storedLevel) {
      console.log('Fresh visit to language selection page, allowing normal flow');
      // Let the normal component render proceed
      return;
    }
    
    // If we have both language and level, we should go to speech page
    if (storedLanguage && storedLevel) {
      console.log('Found existing language and level, redirecting to speech page');
      // Use the most direct approach with a delay to avoid navigation race conditions
      setTimeout(() => {
        const fullUrl = `${window.location.origin}/speech`;
        console.log('Navigating to speech page:', fullUrl);
        window.location.href = fullUrl;
      }, 300);
      return;
    }
    
    // If we have just language selected, we should pre-select it but not auto-redirect
    // This allows users to see the new speaking assessment option
    const fromTopicSelection = sessionStorage.getItem('fromTopicSelection');
    const fromLevelSelection = sessionStorage.getItem('fromLevelSelection');
    const fromSpeechPage = sessionStorage.getItem('fromSpeechPage');
    
    if (storedLanguage && !storedLevel && !fromTopicSelection && !fromLevelSelection && !fromSpeechPage) {
      console.log('Found existing language, pre-selecting it without redirect');
      setSelectedLanguage(storedLanguage);
      return;
    }
    
    // Clear the navigation flags if they exist
    if (fromTopicSelection) {
      console.log('Clearing fromTopicSelection flag');
      sessionStorage.removeItem('fromTopicSelection');
    }
    if (fromLevelSelection) {
      console.log('Clearing fromLevelSelection flag');
      sessionStorage.removeItem('fromLevelSelection');
    }
    if (fromSpeechPage) {
      console.log('Clearing fromSpeechPage flag');
      sessionStorage.removeItem('fromSpeechPage');
    }
  }, []);
  
  // No need for handleStartOver since this is the starting screen

  const handleLanguageSelect = (languageCode: string) => {
    // Just set the selected language without redirecting
    setSelectedLanguage(languageCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLanguage', languageCode);
    
    // Log the selection
    console.log('Language selected:', languageCode);
    
    // Important: No redirection here - we want to stay on this page
    // to show the assessment options
    
    // Reset loading state if it was set
    setIsLoading(false);
  };

  // Function to continue to topic selection
  const handleContinue = () => {
    if (!selectedLanguage) return;
    
    // Set loading state while navigating
    setIsLoading(true);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Continuing to topic selection with language:', selectedLanguage);
    
    // RAILWAY SPECIFIC: Detect Railway environment
    const isRailway = window.location.hostname.includes('railway.app');
    
    // For Railway, use a more direct approach with full URL
    if (isRailway) {
      const fullUrl = `${window.location.origin}/topic-selection`;
      window.location.replace(fullUrl);
      return;
    }
    
    // Standard navigation for non-Railway environments
    setTimeout(() => {
      window.location.href = '/topic-selection';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('language-selection')) {
          window.location.replace('/topic-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 300);
  };

  return (
    <div className="min-h-screen gradient-background flex flex-col">
      <NavBar />
      <PendingLearningPlanHandler />
      <main className="flex-grow flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header with animated elements */}
        <div className="text-center mb-12 relative">
          {/* Animated background effects */}
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-20 bg-purple-500/10 blur-xl animate-pulse"></div>
          
          <h1 className="text-5xl font-bold tracking-tight relative z-10 min-h-[4rem] inline-block">
            <div className="relative">
              <span className="text-white drop-shadow-sm">Choose Your Language</span>
              {/* Animated underline effect */}
              <div className="absolute -bottom-2 left-0 w-full h-[3px] bg-white/50 animate-pulse"></div>
            </div>
          </h1>
          <div className="text-white/80 mt-4 text-lg max-w-md mx-auto min-h-[2rem]">
            <p className="text-white/80 animate-fade-in">Select a language to begin</p>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center relative">
          {/* Decorative elements */}
          <div className="absolute -top-40 -right-20 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-20 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl"></div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-5xl relative z-10">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className={`
                  group relative overflow-hidden rounded-xl 
                  transition-all duration-500 ease-out 
                  glass-card
                  hover:shadow-lg hover:shadow-black/20
                  ${
                    selectedLanguage === language.code
                      ? 'ring-2 ring-purple-300/50 shadow-purple-500/20 shadow-md'
                      : 'hover:border-white/30'
                  }
                `}
              >
                {/* Interactive card content with animations */}
                <div className="relative z-10 p-6">
                  <div className="flex items-start gap-5">
                    {/* Modern animated language symbol */}
                    <div 
                      className={`
                        flex-shrink-0 w-20 h-20 flex items-center justify-center rounded-lg 
                        bg-black/20 backdrop-blur-sm
                        shadow-lg group-hover:shadow-xl transition-all duration-500
                        border border-white/20 group-hover:border-white/40
                        overflow-hidden relative
                        ${
                          selectedLanguage === language.code
                            ? 'bg-white/10 border-white/30'
                            : ''
                        }
                      `}
                    >
                      {/* Animated pulsing background */}
                      <div className="absolute inset-0 opacity-20 overflow-hidden">
                        <div className="w-full h-full relative">
                          {/* Top left gradient blob */}
                          <div className="absolute -top-10 -left-10 w-20 h-20 bg-purple-500/30 rounded-full blur-xl animate-pulse"></div>
                          {/* Bottom right gradient blob */}
                          <div className="absolute -bottom-10 -right-10 w-20 h-20 bg-indigo-500/30 rounded-full blur-xl animate-pulse delay-700"></div>
                        </div>
                      </div>
                      
                      {/* Flag only with modern design - animated on hover */}
                      <div className="relative z-10 w-full h-full flex items-center justify-center">
                        {/* Flag with enhanced styling */}
                        <div className="relative w-4/5 h-4/5 overflow-hidden rounded-lg shadow-lg group-hover:shadow-xl transition-all duration-300 transform group-hover:scale-105">
                          {/* Glossy overlay effect */}
                          <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent z-10 pointer-events-none"></div>
                          
                          {/* Flag image */}
                          <Image 
                            src={language.flagSrc}
                            alt={`${language.name} flag`}
                            fill
                            className="object-cover transition-transform duration-500"
                            priority
                          />
                          
                          {/* Bottom shadow effect */}
                          <div className="absolute bottom-0 left-0 right-0 h-1/4 bg-gradient-to-t from-black/20 to-transparent pointer-events-none"></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Language details */}
                    <div className="flex-1 text-left pt-1">
                      <h3 className="text-xl font-bold text-white mb-2 group-hover:text-white transition-colors duration-300">
                        {language.name}
                      </h3>
                      
                      <p className="text-white/70 text-sm group-hover:text-white transition-colors duration-300">
                        {language.code === 'dutch' && 'Leer Nederlandse woordenschat en conversatie'}
                        {language.code === 'english' && 'Practice English speaking and listening'}
                        {language.code === 'spanish' && 'Domina habilidades de conversación en español'}
                        {language.code === 'german' && 'Entwickle deutsche Sprachkenntnisse'}
                        {language.code === 'french' && 'Améliorez vos compétences en français'}
                        {language.code === 'portuguese' && 'Aprenda vocabulário e expressões em português'}
                      </p>
                    </div>
                    
                    {/* Selection indicator */}
                    {selectedLanguage === language.code && (
                      <div className="absolute top-4 right-4 animate-fade-in">
                        <div className="w-7 h-7 rounded-full bg-white/80 flex items-center justify-center shadow-md">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="purple"
                            className="w-4 h-4"
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
                  </div>
                </div>
                
                {/* Bottom flowing accent line with animation */}
                <div 
                  className={`
                    absolute bottom-0 left-0 h-0.5 bg-white/60
                    transition-all duration-700 ease-out opacity-80
                    ${
                      selectedLanguage === language.code
                        ? 'w-full'
                        : 'w-0 group-hover:w-full'
                    }
                  `}
                ></div>
                
                {/* Additional hover effects */}
                <div className="absolute inset-0 bg-gradient-to-tr from-purple-500/5 via-transparent to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              </button>
            ))}
          </div>

          {/* Assessment Options */}
          {selectedLanguage && (
            <div className="mt-8 animate-fade-in">
              <h3 className="text-center text-white/80 mb-4">How would you like to proceed?</h3>
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                {/* Speaking Assessment Option */}
                <button
                  onClick={() => {
                    // Set loading state while navigating
                    setIsLoading(true);
                    
                    // Store the selection in session storage
                    sessionStorage.setItem('selectedLanguage', selectedLanguage);
                    
                    // Set a flag to indicate we're going to speaking assessment
                    sessionStorage.setItem('navigatingToSpeakingAssessment', 'true');
                    
                    // Log the navigation attempt
                    console.log('Navigating to speaking assessment with language:', selectedLanguage);
                    
                    // IMPORTANT: Use absolute URL with origin for Railway
                    const isRailway = window.location.hostname.includes('railway.app');
                    const fullUrl = `${window.location.origin}/assessment/speaking`;
                    console.log('Navigating to:', fullUrl);
                    
                    // Force a hard navigation instead of client-side routing
                    window.location.replace(fullUrl);
                    
                    // Set a fallback timer to detect navigation failures
                    setTimeout(() => {
                      if (window.location.pathname.includes('language-selection')) {
                        console.error('Navigation failed, still on language selection after timeout');
                        setIsLoading(false);
                        sessionStorage.removeItem('navigatingToSpeakingAssessment');
                        alert('Navigation to speaking assessment failed. Please try again.');
                      }
                    }, 3000);
                  }}
                  className="px-6 py-3 rounded-xl font-medium 
                    bg-gradient-to-r from-purple-600 to-indigo-500 
                    hover:from-purple-500 hover:to-indigo-400
                    text-white shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  <div className="flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    Assess My Speaking Level
                  </div>
                  <p className="text-xs mt-1 text-white/80">AI will evaluate your speaking proficiency</p>
                </button>

                {/* Standard Path Option */}
                <button
                  onClick={handleContinue}
                  className="px-6 py-3 rounded-xl font-medium 
                    bg-white text-black hover:bg-white/90 
                    shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  <div className="flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                    Continue to Topics
                  </div>
                  <p className="text-xs mt-1 text-black/70">Select topics and set your level manually</p>
                </button>
              </div>
            </div>
          )}
        </div>
        </div>
      </main>
    </div>
  );
}
