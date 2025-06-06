'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useNavigation } from '@/lib/navigation';
import NavBar from '@/components/nav-bar';
import PendingLearningPlanHandler from '@/components/pending-learning-plan-handler';
import { useAuth } from '@/lib/auth';
import LanguageOptionsModal from '@/components/language-options-modal';
import './language-selection.css';
// Animation temporarily commented out
// import { TypeAnimation } from 'react-type-animation';
// Sound effects temporarily disabled
// import { useAudio } from '@/lib/useAudio';

interface Language {
  code: string;
  name: string;
  description?: string;
  flagComponent: React.ReactNode;
}

export default function LanguageSelection() {
  const router = useRouter();
  const navigation = useNavigation();
  const { user } = useAuth();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // Sound effects temporarily disabled
  // const { playSelectionSound, playSuccessSound } = useAudio();

  // Flag SVG components directly embedded to avoid loading issues
const FlagComponents: Record<string, React.ReactNode> = {
  dutch: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="dutch-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#21468B" stopOpacity="1" />
          <stop offset="100%" stopColor="#1a3a70" stopOpacity="1" />
        </linearGradient>
        <filter id="dutch-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.3" />
        </filter>
      </defs>
      <rect fill="url(#dutch-grad)" width="3" height="2" filter="url(#dutch-shadow)" />
      <rect fill="#FFF" width="3" height="1.33" />
      <rect fill="#AE1C28" width="3" height="0.67" />
    </svg>
  ),
  english: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="uk-blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#012169" stopOpacity="1" />
          <stop offset="100%" stopColor="#001a4d" stopOpacity="1" />
        </linearGradient>
        <filter id="uk-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1" stdDeviation="1" floodColor="#000" floodOpacity="0.3" />
        </filter>
      </defs>
      <g filter="url(#uk-shadow)">
        <rect width="3" height="2" fill="url(#uk-blue-grad)" />
        <path d="M0,0 L3,2 M3,0 L0,2" stroke="#fff" strokeWidth="0.3" />
        <path d="M1.5,0 v2 M0,1 h3" stroke="#fff" strokeWidth="0.5" />
        <path d="M1.5,0 v2 M0,1 h3" stroke="#C8102E" strokeWidth="0.3" />
        <path d="M0,0 L3,2 M3,0 L0,2" stroke="#C8102E" strokeWidth="0.2" clipPath="url(#t)" />
      </g>
    </svg>
  ),
  spanish: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="spanish-red-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#c60b1e" stopOpacity="1" />
          <stop offset="100%" stopColor="#a00918" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="spanish-yellow-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ffc400" stopOpacity="1" />
          <stop offset="100%" stopColor="#e6b000" stopOpacity="1" />
        </linearGradient>
        <filter id="spanish-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.3" />
        </filter>
      </defs>
      <rect width="3" height="2" fill="url(#spanish-red-grad)" filter="url(#spanish-shadow)" />
      <rect width="3" height="1" fill="url(#spanish-yellow-grad)" y="0.5" />
    </svg>
  ),
  german: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="german-black-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#000" stopOpacity="1" />
          <stop offset="100%" stopColor="#111" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="german-red-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#D00" stopOpacity="1" />
          <stop offset="100%" stopColor="#b00" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="german-yellow-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFCE00" stopOpacity="1" />
          <stop offset="100%" stopColor="#e6b800" stopOpacity="1" />
        </linearGradient>
        <filter id="german-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1" stdDeviation="0.1" floodColor="#000" floodOpacity="0.3" />
        </filter>
      </defs>
      <rect width="3" height="2" fill="url(#german-black-grad)" filter="url(#german-shadow)" />
      <rect width="3" height="1.33" fill="url(#german-red-grad)" />
      <rect width="3" height="0.67" fill="url(#german-yellow-grad)" />
    </svg>
  ),
  french: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="french-blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#002395" stopOpacity="1" />
          <stop offset="100%" stopColor="#001c75" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="french-red-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ED2939" stopOpacity="1" />
          <stop offset="100%" stopColor="#c61a29" stopOpacity="1" />
        </linearGradient>
        <filter id="french-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.3" />
        </filter>
      </defs>
      <rect width="1" height="2" fill="url(#french-blue-grad)" filter="url(#french-shadow)" />
      <rect width="1" height="2" fill="#FFFFFF" x="1" />
      <rect width="1" height="2" fill="url(#french-red-grad)" x="2" />
    </svg>
  ),
  portuguese: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="portuguese-green-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#006600" stopOpacity="1" />
          <stop offset="100%" stopColor="#004d00" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="portuguese-red-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FF0000" stopOpacity="1" />
          <stop offset="100%" stopColor="#cc0000" stopOpacity="1" />
        </linearGradient>
        <radialGradient id="portuguese-yellow-grad" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
          <stop offset="0%" stopColor="#FFFF00" stopOpacity="1" />
          <stop offset="100%" stopColor="#e6e600" stopOpacity="1" />
        </radialGradient>
        <filter id="portuguese-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.3" />
        </filter>
        <filter id="portuguese-emblem-shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="1" stdDeviation="1" floodColor="#000" floodOpacity="0.5" />
        </filter>
      </defs>
      <rect width="3" height="2" fill="url(#portuguese-green-grad)" filter="url(#portuguese-shadow)" />
      <rect width="1.2" height="2" fill="url(#portuguese-red-grad)" />
      <circle cx="1.2" cy="1" r="0.3" fill="url(#portuguese-yellow-grad)" stroke="#000000" strokeWidth="0.03" filter="url(#portuguese-emblem-shadow)" />
    </svg>
  ),
};

const languages: Language[] = [
    {
      code: 'dutch',
      name: 'Dutch',
      flagComponent: FlagComponents.dutch,
    },
    {
      code: 'english',
      name: 'English',
      flagComponent: FlagComponents.english,
    },
    {
      code: 'spanish',
      name: 'Spanish',
      flagComponent: FlagComponents.spanish,
    },
    {
      code: 'german',
      name: 'German',
      flagComponent: FlagComponents.german,
    },
    {
      code: 'french',
      name: 'French',
      flagComponent: FlagComponents.french,
    },
    {
      code: 'portuguese',
      name: 'Portuguese',
      flagComponent: FlagComponents.portuguese,
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
    
    // IMPORTANT: COMPLETELY DISABLE ALL REDIRECTS
    // This is a drastic approach to fix back button navigation
    console.log('Language selection page: Disabling all automatic redirects');
    
    // Check if we're coming from back button navigation
    const isBackButtonNavigation = sessionStorage.getItem('backButtonNavigation') === 'true';
    
    // If we're coming from back button navigation, clear session storage to prevent redirects
    if (isBackButtonNavigation) {
      console.log('Coming from back button navigation, clearing session storage');
      // Keep only essential data
      const storedLanguage = sessionStorage.getItem('selectedLanguage');
      // Clear all session storage
      sessionStorage.clear();
      // Restore only the language
      if (storedLanguage) {
        sessionStorage.setItem('selectedLanguage', storedLanguage);
        setSelectedLanguage(storedLanguage);
      }
      return;
    }
    
    // For normal navigation, just pre-select the language if it exists
    const storedLanguage = sessionStorage.getItem('selectedLanguage');
    if (storedLanguage) {
      setSelectedLanguage(storedLanguage);
    }
    
    // Clear any remaining navigation flags
    const fromTopicSelection = sessionStorage.getItem('fromTopicSelection');
    const fromLevelSelection = sessionStorage.getItem('fromLevelSelection');
    const fromSpeechPage = sessionStorage.getItem('fromSpeechPage');
    
    if (fromTopicSelection) {
      sessionStorage.removeItem('fromTopicSelection');
    }
    
    if (fromLevelSelection) {
      sessionStorage.removeItem('fromLevelSelection');
    }
    
    if (fromSpeechPage) {
      sessionStorage.removeItem('fromSpeechPage');
    }
  }, []);
  
  // No need for handleStartOver since this is the starting screen

  const handleLanguageSelect = (languageCode: string) => {
    // Sound effects temporarily disabled
    // playSelectionSound();
    
    // Store the selected language
    setSelectedLanguage(languageCode);
    
    // Save to session storage and navigation context
    navigation.setSelectedLanguage(languageCode);
    
    // Open the modal instead of scrolling
    setIsModalOpen(true);
  };

  // Function to continue to topic selection
  const handleContinue = () => {
    // Sound effects temporarily disabled
    // playSuccessSound();
    // setTimeout(() => {
    //   router.push('/topic-selection');
    // }, 500);
    
    // Set loading state while navigating
    setIsLoading(true);
    
    // Use direct navigation for reliability in this critical path
    window.location.href = '/topic-selection';
    
    // Fallback in case the above doesn't trigger
    setTimeout(() => {
      if (window.location.pathname !== '/topic-selection') {
        router.push('/topic-selection');
      }
    }, 1000);
  };
  
  // Handle modal option selection
  const handleModalOptionSelect = (option: string) => {
    if (option === 'assessment') {
      // Set loading state while navigating
      setIsLoading(true);
      
      // Ensure the language is stored
      if (selectedLanguage) {
        navigation.setSelectedLanguage(selectedLanguage);
      }
      
      // Log the navigation attempt
      console.log('Navigating to speaking assessment with language:', selectedLanguage);
      
      // Use direct navigation for reliability in this critical path
      window.location.href = '/assessment/speaking';
    } else if (option === 'practice') {
      handleContinue();
    }
  };

  return (
    <div className="language-selection-page">
      <NavBar activeSection="section1" />
      <PendingLearningPlanHandler />
      <main className="language-selection-content">
        <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header with animated elements */}
        <div className="text-center mb-12 relative">
          {/* Clean header without background effects */}
          
          <h1 className="text-5xl font-bold tracking-tight relative z-10 min-h-[4rem] inline-block">
            <div className="relative">
              <span className="text-gray-800 drop-shadow-sm">Choose Your Language</span>
              {/* Animated underline effect */}
              <div className="absolute -bottom-2 left-0 w-full h-[3px] bg-[#4ECFBF] animate-pulse"></div>
            </div>
          </h1>
          <div className="mt-4 text-lg max-w-md mx-auto min-h-[2rem]">
            <p className="text-gray-600 animate-fade-in">Select a language to begin</p>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center relative">
          {/* Clean content area without decorative elements */}
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-5xl relative z-10">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className={`
                  group relative overflow-hidden rounded-xl 
                  transition-all duration-500 ease-out 
                  bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40
                  hover:shadow-lg hover:shadow-[#4ECFBF]/20
                  ${
                    selectedLanguage === language.code
                      ? 'ring-2 ring-[#4ECFBF]/50 shadow-[#4ECFBF]/30 shadow-md border-[#4ECFBF]/60'
                      : 'hover:border-[#4ECFBF]/60'
                  }
                `}
              >
                {/* Interactive card content with animations */}
                <div className="relative z-10 p-6">
                  <div className="flex items-start gap-4">
                    {/* Modern animated language symbol */}
                    <div 
                      className={`
                        flex-shrink-0 w-28 h-20 flex items-center justify-center rounded-lg 
                        bg-gradient-to-br from-black/5 to-black/20 backdrop-blur-sm
                        shadow-[0_8px_16px_rgba(0,0,0,0.2)] group-hover:shadow-[0_12px_24px_rgba(0,0,0,0.25)] transition-all duration-500
                        border border-white/30 group-hover:border-white/50
                        overflow-hidden relative
                        ${
                          selectedLanguage === language.code
                            ? 'from-white/10 to-white/5 border-white/50 shadow-[0_0_15px_rgba(255,255,255,0.2)]'
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
                        <div className="relative w-5/6 h-4/5 overflow-hidden rounded-lg transition-all duration-300 transform group-hover:scale-105">
                          {/* Improved flag container with 3D effect */}
                          <div className="w-full h-full relative flag-container">
                            {/* Flag component with enhanced styling */}
                            <div className="w-full h-full relative z-10">
                              {language.flagComponent}
                            </div>
                            
                            {/* Modern glossy overlay */}
                            <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-black/10 z-20 pointer-events-none"></div>
                            
                            {/* Subtle inner border */}
                            <div className="absolute inset-0 rounded-lg border border-white/30 z-30 pointer-events-none"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Language details */}
                    <div className="flex-1 text-left pt-1">
                      <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-[#4ECFBF] transition-colors duration-300">
                        {language.name}
                      </h3>
                      
                      <p className="text-gray-600 text-sm group-hover:text-gray-700 transition-colors duration-300">
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
                        <div className="w-7 h-7 rounded-full flex items-center justify-center shadow-md" style={{ backgroundColor: 'var(--yellow)' }}>
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="var(--text-dark)"
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
                    absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF]
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

          {/* Language Options Modal */}
          <LanguageOptionsModal 
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            selectedLanguage={selectedLanguage || ''}
            onContinue={handleModalOptionSelect}
          />
        </div>
        </div>
      </main>
    </div>
  );
}
