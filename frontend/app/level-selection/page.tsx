'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { verifyBackendConnectivity } from '../../lib/healthCheck';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';
// Sound effects temporarily disabled
// import { useAudio } from '@/lib/useAudio';

interface Level {
  code: string;
  name: string;
  description: string;
}

export default function LevelSelection() {
  const router = useRouter();
  const { user } = useAuth();
  const navigation = useNavigation();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [levels, setLevels] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  // Sound effects temporarily disabled
  // const { playSelectionSound, playSuccessSound } = useAudio();

  useEffect(() => {
    console.log('Level selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Set up a listener for the popstate event (browser back button)
    const handlePopState = (event: PopStateEvent) => {
      console.log('Detected browser back button navigation');
      // Set a flag to indicate we're navigating back to topic selection
      sessionStorage.setItem('popStateToTopicSelection', 'true');
    };
    
    // Add the event listener
    window.addEventListener('popstate', handlePopState);
    
    // Retrieve the selected language from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    if (!language) {
      // If no language is selected, redirect to language selection
      console.log('No language selected, redirecting to language selection');
      window.location.href = '/language-selection';
      return;
    }
    
    // Set the selected language in state
    setSelectedLanguage(language);
    
    // Set loading to false to show the UI
    setIsLoading(false);
    
    // Clean up the event listener when the component unmounts
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
    
    setSelectedLanguage(language);
    
    // First verify backend connectivity
    verifyBackendConnectivity()
      .then(connected => {
        console.log('Backend connectivity check result:', connected);
        setBackendConnected(connected);
        
        if (connected) {
          // If connected, proceed to fetch languages and levels
          fetchLanguagesAndLevels(language);
        } else {
          // If not connected, show an error
          setError('Unable to connect to the backend server. Please try again later.');
          setIsLoading(false);
        }
      })
      .catch(err => {
        console.error('Backend connectivity check failed:', err);
        setBackendConnected(false);
        setError('Failed to verify backend connectivity. Please refresh the page or try again later.');
        setIsLoading(false);
      });
  }, [router]);

  const fetchLanguagesAndLevels = async (language: string | null) => {
    if (!language) {
      setError('No language selected');
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      
      // Determine the API URL based on the environment
      let baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
      
      // Handle localhost and 127.0.0.1 cases
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        baseUrl = 'http://localhost:8000';
      }
      
      // Log the environment and API URL for debugging
      console.log('Environment:', process.env.NODE_ENV);
      console.log('Using API base URL:', baseUrl);
      
      console.log('Using API base URL:', baseUrl);
      
      // Add retry logic for better reliability
      let response;
      let retries = 0;
      const maxRetries = 3;
      
      while (retries < maxRetries) {
        try {
          // Make sure we're using the correct endpoint format
          response = await fetch(`${baseUrl}/api/languages`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Cache-Control': 'no-cache'
            }
          });
          
          if (response.ok) break;
          
        } catch (fetchError) {
          console.log(`Fetch attempt ${retries + 1} failed:`, fetchError);
        }
        
        retries++;
        if (retries < maxRetries) {
          console.log(`Retrying fetch (${retries}/${maxRetries})...`);
          // Wait a bit before retrying
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      // Check if response exists and is ok
      if (!response || !response.ok) {
        throw new Error('Failed to fetch languages and levels');
      }
      
      const data = await response.json();
      
      if (!data[language]) {
        throw new Error(`Language ${language} not found`);
      }
      
      setLevels(data[language].levels || {});
    } catch (err) {
      console.error('Error fetching languages and levels:', err);
      setError('Failed to load language levels. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Add a useEffect to check if we're stuck on this page
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    console.log('Level selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    console.log('Document referrer:', document.referrer);
    
    // IMPORTANT: Disable all automatic redirects to fix back button navigation
    // We'll only redirect if there's no language selected
    
    // Retrieve the selected language from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    
    // If no language is selected, redirect to language selection
    if (!language) {
      console.log('No language selected, redirecting to language selection');
      window.location.href = '/language-selection';
      return;
    }
    
    // Set the selected language in state
    setSelectedLanguage(language);
    
    // Set loading to false to show the UI
    setIsLoading(false);
    
    // Clear any navigation flags that might cause issues
    sessionStorage.removeItem('intentionalNavigation');
    sessionStorage.removeItem('backButtonNavigation');
    sessionStorage.removeItem('popStateToTopicSelection');
  }, []);
  
  const handleStartOver = () => {
    // Clear all session storage
    sessionStorage.clear();
    // Navigate to home page
    console.log('Starting over - cleared session storage');
    navigation.navigateToHome();
  };
  
  const handleChangeLanguage = () => {
    // Clear the language and level to ensure proper navigation
    sessionStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLevel');
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    // Clear any navigation flags
    sessionStorage.removeItem('fromLevelSelection');
    sessionStorage.removeItem('intentionalNavigation');
    
    // Set a flag to indicate we're intentionally going to language selection
    sessionStorage.setItem('fromLevelSelection', 'true');
    
    // Navigate to language selection
    console.log('Navigating to language selection from level selection, cleared selections');
    navigation.navigateToLanguageSelection();
  };
  
  const handleChangeTopic = () => {
    // Keep language but clear the topic
    sessionStorage.removeItem('selectedTopic');
    // Set a flag to indicate we're intentionally going to topic selection
    sessionStorage.setItem('fromLevelSelection', 'true');
    // Navigate to topic selection
    console.log('Navigating to topic selection with fromLevelSelection flag');
    
    // Use direct navigation for reliability in this critical path
    window.location.href = '/topic-selection';
  };

  const handleLevelSelect = (level: string) => {
    // Set loading state while navigating
    setIsLoading(true);
    setSelectedLevel(level);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLevel', level);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Navigating to speech with level:', level);
    
    // Use direct navigation for reliability in this critical path
    window.location.href = '/speech';
  };

  // Define levels with multilingual descriptions
  const getLevels = (language: string | null): Level[] => {
    // Default to English if no language is selected
    const lang = language || 'english';
    
    // Define all levels with descriptions in each language
    const levelDescriptions = {
      'A1': {
        english: 'Basic vocabulary and simple phrases for everyday situations.',
        dutch: 'Basiswoordenschat en eenvoudige zinnen voor alledaagse situaties.',
        spanish: 'Vocabulario básico y frases simples para situaciones cotidianas.',
        german: 'Grundwortschatz und einfache Sätze für Alltagssituationen.',
        french: 'Vocabulaire de base et phrases simples pour les situations quotidiennes.',
        portuguese: 'Vocabulário básico e frases simples para situações cotidianas.'
      },
      'A2': {
        english: 'Communicate in simple and routine tasks on familiar topics.',
        dutch: 'Communiceren in eenvoudige en routinematige taken over bekende onderwerpen.',
        spanish: 'Comunicarse en tareas simples y rutinarias sobre temas familiares.',
        german: 'Kommunikation in einfachen und routinemäßigen Aufgaben zu vertrauten Themen.',
        french: 'Communiquer lors de tâches simples et habituelles sur des sujets familiers.',
        portuguese: 'Comunicar em tarefas simples e rotineiras sobre tópicos familiares.'
      },
      'B1': {
        english: 'Deal with most situations likely to arise while traveling.',
        dutch: 'Omgaan met de meeste situaties die zich kunnen voordoen tijdens het reizen.',
        spanish: 'Enfrentar la mayoría de las situaciones que pueden surgir durante un viaje.',
        german: 'Mit den meisten Situationen umgehen, die während des Reisens auftreten können.',
        french: 'Faire face à la plupart des situations susceptibles de se produire en voyage.',
        portuguese: 'Lidar com a maioria das situações que podem surgir durante uma viagem.'
      },
      'B2': {
        english: 'Interact with a degree of fluency that makes regular interaction possible.',
        dutch: 'Communiceren met een mate van vloeiendheid die regelmatige interactie mogelijk maakt.',
        spanish: 'Interactuar con un grado de fluidez que hace posible la interacción regular.',
        german: 'Mit einem Grad an Flüssigkeit interagieren, der regelmäßige Interaktion ermöglicht.',
        french: 'Interagir avec un degré de fluidité qui rend possible une interaction régulière.',
        portuguese: 'Interagir com um grau de fluência que torna possível a interação regular.'
      },
      'C1': {
        english: 'Express ideas fluently and spontaneously without much searching for expressions.',
        dutch: 'Ideeën vloeiend en spontaan uitdrukken zonder veel te zoeken naar uitdrukkingen.',
        spanish: 'Expresar ideas con fluidez y espontaneidad sin tener que buscar expresiones.',
        german: 'Ideen fließend und spontan ausdrücken, ohne viel nach Ausdrücken suchen zu müssen.',
        french: 'Exprimer des idées avec fluidité et spontanéité sans trop chercher ses mots.',
        portuguese: 'Expressar ideias com fluência e espontaneidade sem precisar procurar expressões.'
      },
      'C2': {
        english: 'Express yourself spontaneously, very fluently and precisely in complex situations.',
        dutch: 'Jezelf spontaan, zeer vloeiend en nauwkeurig uitdrukken in complexe situaties.',
        spanish: 'Expresarte de forma espontánea, muy fluida y precisa en situaciones complejas.',
        german: 'Dich spontan, sehr fließend und präzise in komplexen Situationen ausdrücken.',
        french: 'Vous exprimer spontanément, très couramment et avec précision dans des situations complexes.',
        portuguese: 'Expressar-se espontaneamente, com muita fluência e precisão em situações complexas.'
      }
    };
    
    // Create formatted levels with proper descriptions in the selected language
    return Object.entries(levelDescriptions).map(([code, descriptions]) => ({
      code,
      name: code,
      description: descriptions[lang as keyof typeof descriptions] || descriptions.english
    }));
  };
  
  // Get formatted levels based on selected language
  const formattedLevels = getLevels(selectedLanguage);

  return (
    <div className="min-h-screen text-[#4ECFBF] level-selection-container">
      <NavBar activeSection="section1" />
      <main className="flex-grow flex flex-col p-4 md:p-8 main-content-with-navbar">
        <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-800 mb-4 animate-fade-in">
            Select Your Level
          </h1>
          <p className="text-gray-600 text-lg mb-8 animate-fade-in" style={{animationDelay: '100ms'}}>
            {selectedLanguage === 'dutch' && 'Kies je vaardigheidsniveau in het Nederlands'}
            {selectedLanguage === 'english' && 'Choose your proficiency level in English'}
            {selectedLanguage === 'spanish' && 'Elige tu nivel de competencia en español'}
            {selectedLanguage === 'german' && 'Wähle dein Kenntnissniveau in Deutsch'}
            {selectedLanguage === 'french' && 'Choisissez votre niveau de compétence en français'}
            {selectedLanguage === 'portuguese' && 'Escolha seu nível de proficiência em português'}
            {!selectedLanguage && 'Choose your proficiency level'}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-10 animate-fade-in max-w-2xl mx-auto" style={{animationDelay: '200ms'}}>
            {/* Change Language Button */}
            <button 
              onClick={handleChangeLanguage}
              className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 w-full sm:w-48 h-14 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:shadow-[#4ECFBF]/20 transform hover:translate-y-[-1px] touch-target" 
            >
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Text */}
              <span className="relative z-10 font-medium text-gray-800 group-hover:text-[#4ECFBF] transition-colors duration-300 text-sm sm:text-base">Change Language</span>
              
              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
            </button>

            {/* Change Topic Button */}
            <button 
              onClick={handleChangeTopic}
              className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 w-full sm:w-48 h-14 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:shadow-[#4ECFBF]/20 transform hover:translate-y-[-1px] touch-target" 
            >
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Text */}
              <span className="relative z-10 font-medium text-gray-800 group-hover:text-[#4ECFBF] transition-colors duration-300 text-sm sm:text-base">Change Topic</span>
              
              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
            </button>

            {/* Start Over Button */}
            <button 
              onClick={handleStartOver}
              className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 w-full sm:w-48 h-14 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:shadow-[#4ECFBF]/20 transform hover:translate-y-[-1px] touch-target" 
            >
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Text */}
              <span className="relative z-10 font-medium text-gray-800 group-hover:text-[#4ECFBF] transition-colors duration-300 text-sm sm:text-base">Start Over</span>
              
              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="relative w-20 h-20 mb-6">
              <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-indigo-200/20 animate-pulse"></div>
              <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-transparent border-t-indigo-500 animate-spin"></div>
            </div>
            <p className="text-white/80 animate-pulse">Loading available levels...</p>
            {backendConnected === false && (
              <div className="mt-8 p-5 glass-card border border-white/20 rounded-xl shadow-lg">
                <p className="text-white/80 text-sm font-medium">Warning: Backend connectivity issues detected.</p>
              </div>
            )}
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-8 glass-card border border-white/20 rounded-xl shadow-lg backdrop-blur-sm max-w-md animate-fade-in">
              <div className="relative w-20 h-20 mx-auto mb-6">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-red-500 absolute top-0 left-0 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="absolute inset-0 bg-red-500/20 rounded-full blur-xl animate-pulse"></div>
              </div>
              <p className="text-red-400 font-medium mb-6 text-lg">{error}</p>
              <button
                onClick={() => {
                  setIsLoading(true);
                  setError(null);
                  // First verify connectivity, then fetch data
                  verifyBackendConnectivity()
                    .then(connected => {
                      setBackendConnected(connected);
                      if (connected) {
                        fetchLanguagesAndLevels(selectedLanguage || 'english');
                      } else {
                        setError('Still unable to connect to the backend server.');
                        setIsLoading(false);
                      }
                    })
                    .catch(() => {
                      setBackendConnected(false);
                      setError('Failed to verify backend connectivity.');
                      setIsLoading(false);
                    });
                }}
                className="app-button"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-3xl">
              {formattedLevels.map((level) => {
                // Determine level color scheme based on level code
                const getLevelColors = (code: string) => {
                  if (code.startsWith('A')) return {
                    bg: 'from-green-500 to-emerald-600',
                    border: 'border-green-500',
                    glow: 'shadow-green-500/20',
                    ring: 'ring-green-400',
                    icon: 'bg-gradient-to-r from-green-500 to-emerald-600',
                    badge: 'bg-gradient-to-br from-green-400 to-emerald-500 via-green-500',
                    badgeShadow: 'shadow-green-500/30'
                  };
                  if (code.startsWith('B')) return {
                    bg: 'from-blue-500 to-indigo-600',
                    border: 'border-blue-500',
                    glow: 'shadow-blue-500/20',
                    ring: 'ring-blue-400',
                    icon: 'bg-gradient-to-r from-blue-500 to-indigo-600',
                    badge: 'bg-gradient-to-br from-blue-400 to-indigo-500 via-blue-500',
                    badgeShadow: 'shadow-blue-500/30'
                  };
                  return {
                    bg: 'from-purple-500 to-violet-600',
                    border: 'border-purple-500',
                    glow: 'shadow-purple-500/20',
                    ring: 'ring-purple-400',
                    icon: 'bg-gradient-to-r from-purple-500 to-violet-600',
                    badge: 'bg-gradient-to-br from-purple-400 to-violet-500 via-purple-500',
                    badgeShadow: 'shadow-purple-500/30'
                  };
                };
                
                const colors = getLevelColors(level.code);
                
                return (
                  <button
                    key={level.code}
                    onClick={() => handleLevelSelect(level.code)}
                    className={`
                      relative overflow-hidden flex flex-col items-start p-6 rounded-xl text-left
                      transition-all duration-300 transform hover:scale-105 hover:shadow-xl
                      bg-white animate-fade-in h-[220px] border-2
                      ${
                        selectedLevel === level.code
                          ? `border-[#4ECFBF] shadow-xl shadow-[#4ECFBF]/20 ring-2 ring-[#4ECFBF]/50`
                          : 'border-[#4ECFBF] hover:border-[#4ECFBF]/80 shadow-lg hover:shadow-[#4ECFBF]/20'
                      }
                    `}
                    style={{animationDelay: `${300 + parseInt(level.code.charAt(1)) * 100}ms`}}
                  >
                    {/* Level badge */}
                    <div className={`absolute -top-3 -right-3 w-16 h-16 flex items-center justify-center overflow-hidden`}>
                      <div className={`absolute transform rotate-45 w-24 h-8 ${colors.badge} top-2 right-[-6px] shadow-lg ${colors.badgeShadow}`}>
                        <div className="absolute inset-0 opacity-20 animate-pulse"></div>
                      </div>
                      <span className="relative text-white font-bold text-xs">{level.code}</span>
                    </div>
                    
                    <h2 className="text-xl font-bold mb-3 text-gray-800">
                      {selectedLanguage === 'dutch' && (
                        level.code === 'A1' ? 'Absolute Beginner' : 
                        level.code === 'A2' ? 'Basis Beginner' :
                        level.code === 'B1' ? 'Laag Gemiddeld' :
                        level.code === 'B2' ? 'Hoog Gemiddeld' :
                        level.code === 'C1' ? 'Gevorderd' : 'Zeer Gevorderd'
                      )}
                      {selectedLanguage === 'english' && (
                        level.code === 'A1' ? 'Beginner' : 
                        level.code === 'A2' ? 'Elementary' :
                        level.code === 'B1' ? 'Intermediate' :
                        level.code === 'B2' ? 'Upper Intermediate' :
                        level.code === 'C1' ? 'Advanced' : 'Proficient'
                      )}
                      {selectedLanguage === 'spanish' && (
                        level.code === 'A1' ? 'Principiante' : 
                        level.code === 'A2' ? 'Elemental' :
                        level.code === 'B1' ? 'Intermedio' :
                        level.code === 'B2' ? 'Intermedio Alto' :
                        level.code === 'C1' ? 'Avanzado' : 'Dominio'
                      )}
                      {selectedLanguage === 'german' && (
                        level.code === 'A1' ? 'Anfänger' : 
                        level.code === 'A2' ? 'Grundstufe' :
                        level.code === 'B1' ? 'Mittelstufe' :
                        level.code === 'B2' ? 'Fortgeschrittene Mittelstufe' :
                        level.code === 'C1' ? 'Fortgeschritten' : 'Kompetente Sprachverwendung'
                      )}
                      {selectedLanguage === 'french' && (
                        level.code === 'A1' ? 'Débutant' : 
                        level.code === 'A2' ? 'Élémentaire' :
                        level.code === 'B1' ? 'Intermédiaire' :
                        level.code === 'B2' ? 'Intermédiaire Avancé' :
                        level.code === 'C1' ? 'Avancé' : 'Maîtrise'
                      )}
                      {selectedLanguage === 'portuguese' && (
                        level.code === 'A1' ? 'Iniciante' : 
                        level.code === 'A2' ? 'Básico' :
                        level.code === 'B1' ? 'Intermediário' :
                        level.code === 'B2' ? 'Intermediário Superior' :
                        level.code === 'C1' ? 'Avançado' : 'Proficiente'
                      )}
                      {!selectedLanguage && (
                        level.code === 'A1' ? 'Beginner' : 
                        level.code === 'A2' ? 'Elementary' :
                        level.code === 'B1' ? 'Intermediate' :
                        level.code === 'B2' ? 'Upper Intermediate' :
                        level.code === 'C1' ? 'Advanced' : 'Proficient'
                      )}
                    </h2>
                    <p className="text-sm text-gray-600 mb-4">
                      {level.description}
                    </p>
                    
                    {/* Skill indicators */}
                    <div className="flex flex-wrap gap-2 mt-auto">
                      {level.code.startsWith('A') && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-green-500/20 to-green-600/20 border border-green-500/30 text-green-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Basiswoordenschat'}
                          {selectedLanguage === 'english' && 'Basic Vocabulary'}
                          {selectedLanguage === 'spanish' && 'Vocabulario Básico'}
                          {selectedLanguage === 'german' && 'Grundwortschatz'}
                          {selectedLanguage === 'french' && 'Vocabulaire de Base'}
                          {selectedLanguage === 'portuguese' && 'Vocabulário Básico'}
                          {!selectedLanguage && 'Basic Vocabulary'}
                        </span>
                      )}
                      {(level.code === 'A2' || level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-blue-500/20 to-blue-600/20 border border-blue-500/30 text-blue-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Conversatie'}
                          {selectedLanguage === 'english' && 'Conversation'}
                          {selectedLanguage === 'spanish' && 'Conversación'}
                          {selectedLanguage === 'german' && 'Konversation'}
                          {selectedLanguage === 'french' && 'Conversation'}
                          {selectedLanguage === 'portuguese' && 'Conversação'}
                          {!selectedLanguage && 'Conversation'}
                        </span>
                      )}
                      {(level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-indigo-500/20 to-indigo-600/20 border border-indigo-500/30 text-indigo-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Complexe Onderwerpen'}
                          {selectedLanguage === 'english' && 'Complex Topics'}
                          {selectedLanguage === 'spanish' && 'Temas Complejos'}
                          {selectedLanguage === 'german' && 'Komplexe Themen'}
                          {selectedLanguage === 'french' && 'Sujets Complexes'}
                          {selectedLanguage === 'portuguese' && 'Tópicos Complexos'}
                          {!selectedLanguage && 'Complex Topics'}
                        </span>
                      )}
                      {level.code.startsWith('C') && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-purple-500/20 to-purple-600/20 border border-purple-500/30 text-purple-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Vloeiende Expressie'}
                          {selectedLanguage === 'english' && 'Fluent Expression'}
                          {selectedLanguage === 'spanish' && 'Expresión Fluida'}
                          {selectedLanguage === 'german' && 'Fließender Ausdruck'}
                          {selectedLanguage === 'french' && 'Expression Fluide'}
                          {selectedLanguage === 'portuguese' && 'Expressão Fluente'}
                          {!selectedLanguage && 'Fluent Expression'}
                        </span>
                      )}
                    </div>
                    
                    {selectedLevel === level.code && (
                      <div className="absolute top-4 left-4">
                        <div className={`w-8 h-8 rounded-full ${colors.icon} flex items-center justify-center shadow-lg ${colors.glow} animate-pulse`}>
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="white"
                            className="w-5 h-5 animate-fade-in"
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
                    
                    {/* Bottom accent bar */}
                    <div className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${colors.bg} transition-all duration-500 ${selectedLevel === level.code ? 'w-full' : 'w-0'}`} />
                  </button>
                );
              })}
            </div>
          </div>
        )}
        </div>
      </main>
    </div>
  );
}
