'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { TypeAnimation } from 'react-type-animation';
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
    
    // If we have just language selected, we should go to level selection,
    // but only if we didn't explicitly navigate here to change the language
    const fromTopicSelection = sessionStorage.getItem('fromTopicSelection');
    const fromLevelSelection = sessionStorage.getItem('fromLevelSelection');
    const fromSpeechPage = sessionStorage.getItem('fromSpeechPage');
    
    if (storedLanguage && !storedLevel && !fromTopicSelection && !fromLevelSelection && !fromSpeechPage) {
      console.log('Found existing language, redirecting to level selection');
      // Use the most direct approach with a delay to avoid navigation race conditions
      setTimeout(() => {
        const fullUrl = `${window.location.origin}/level-selection`;
        console.log('Navigating to level selection page:', fullUrl);
        window.location.href = fullUrl;
      }, 300);
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
    // Set loading state while navigating
    setIsLoading(true);
    setSelectedLanguage(languageCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLanguage', languageCode);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Navigating to topic selection with language:', languageCode);
    
    // RAILWAY SPECIFIC: Detect Railway environment
    const isRailway = window.location.hostname.includes('railway.app');
    console.log('Is Railway environment:', isRailway);
    
    // For Railway, use a more direct approach with full URL
    if (isRailway) {
      console.log('Using Railway-specific navigation approach');
      // Use the full URL to ensure proper navigation in Railway
      const fullUrl = `${window.location.origin}/topic-selection`;
      console.log('Navigating to full URL:', fullUrl);
      
      // Use direct location replacement which is most reliable
      window.location.replace(fullUrl);
      
      // Fallback with hard refresh if needed
      setTimeout(() => {
        if (window.location.pathname.includes('language-selection')) {
          console.log('Still on language selection page, forcing hard refresh to:', fullUrl);
          window.location.href = fullUrl + '?t=' + new Date().getTime();
        }
      }, 1000);
      
      return;
    }
    
    // Standard navigation for non-Railway environments
    // Use a direct window.location approach with a small delay
    // This bypasses any client-side routing issues
    setTimeout(() => {
      console.log('Executing navigation to topic selection');
      window.location.href = '/topic-selection';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        console.log('Checking if fallback navigation is needed');
        if (window.location.pathname.includes('language-selection')) {
          console.log('Still on language selection page, using fallback navigation');
          window.location.replace('/topic-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 300);
  };

  return (
    <div className="min-h-screen flex flex-col app-background">
      <NavBar />
      <main className="flex-grow flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header with animated elements */}
        <div className="text-center mb-12 relative">
          {/* Animated background effects */}
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-20 bg-gradient-to-r from-blue-500/0 via-violet-500/10 to-blue-500/0 blur-xl animate-pulse"></div>
          
          <h1 className="text-5xl font-bold tracking-tight relative z-10 min-h-[4rem] inline-block">
            <div className="relative">
              <TypeAnimation
                sequence={[
                  'Choose Your Language',
                  2000,
                  'Kies je taal', // Dutch
                  1500,
                  'Elige tu idioma', // Spanish
                  1500,
                  'Wähle deine Sprache', // German
                  1500,
                  'Choisissez votre langue', // French
                  1500,
                  'Escolha seu idioma', // Portuguese
                  1500,
                  'Choose Your Language',
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
          <div className="text-slate-300 mt-4 text-lg max-w-md mx-auto min-h-[2rem]">
            <TypeAnimation
              sequence={[
                'Select a language to begin',
                2000,
                'Selecteer een taal om te beginnen', // Dutch
                1500,
                'Selecciona un idioma para empezar', // Spanish
                1500,
                'Wähle eine Sprache zum Starten', // German
                1500,
                'Choisissez une langue pour commencer', // French
                1500,
                'Selecione um idioma para começar', // Portuguese
                1500,
                'Select a language to begin',
                1000,
              ]}
              wrapper="p"
              speed={55}
              style={{ display: 'inline-block' }}
              repeat={Infinity}
              cursor={true}
              className="text-slate-300 animate-fade-in"
            />
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center relative">
          {/* Decorative elements */}
          <div className="absolute -top-40 -right-20 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-20 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl"></div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-5xl relative z-10">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className={`
                  group relative overflow-hidden rounded-xl 
                  transition-all duration-500 ease-out 
                  border border-slate-700/50 backdrop-blur-sm
                  bg-slate-800/40 hover:bg-slate-700/40
                  hover:shadow-lg hover:shadow-blue-900/20
                  ${
                    selectedLanguage === language.code
                      ? 'ring-2 ring-blue-500/50 shadow-blue-500/20 shadow-md'
                      : 'hover:border-blue-500/30'
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
                        bg-gradient-to-br from-slate-700/80 to-slate-800/80 
                        shadow-lg group-hover:shadow-xl transition-all duration-500
                        border border-slate-600/30 group-hover:border-blue-500/30
                        overflow-hidden relative
                        ${
                          selectedLanguage === language.code
                            ? 'from-blue-900/30 to-indigo-900/30 border-blue-500/40'
                            : ''
                        }
                      `}
                    >
                      {/* Animated pulsing background */}
                      <div className="absolute inset-0 opacity-20 overflow-hidden">
                        <div className="w-full h-full relative">
                          {/* Top left gradient blob */}
                          <div className="absolute -top-10 -left-10 w-20 h-20 bg-blue-600/40 rounded-full blur-xl animate-pulse"></div>
                          {/* Bottom right gradient blob */}
                          <div className="absolute -bottom-10 -right-10 w-20 h-20 bg-violet-600/40 rounded-full blur-xl animate-pulse delay-700"></div>
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
                      <h3 className="text-xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors duration-300">
                        {language.name}
                      </h3>
                      
                      <p className="text-slate-300 text-sm group-hover:text-slate-100 transition-colors duration-300">
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
                        <div className="w-7 h-7 rounded-full bg-blue-500/80 flex items-center justify-center shadow-md">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="white"
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
                    absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-blue-500 to-violet-500
                    transition-all duration-700 ease-out opacity-80
                    ${
                      selectedLanguage === language.code
                        ? 'w-full'
                        : 'w-0 group-hover:w-full'
                    }
                  `}
                ></div>
                
                {/* Additional hover effects */}
                <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/5 via-transparent to-violet-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              </button>
            ))}
          </div>
        </div>
        </div>
      </main>
    </div>
  );
}
