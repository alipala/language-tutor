'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import NavBar from '@/components/nav-bar';
import SpeakingAssessment from '@/components/speaking-assessment';
import { SpeakingAssessmentResult } from '@/lib/speaking-assessment-api';
import { verifyBackendConnectivity } from '@/lib/healthCheck';

export default function SpeakingAssessmentPage() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  useEffect(() => {
    // Retrieve the selected language from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    if (!language) {
      // If no language is selected, redirect to language selection
      router.push('/language-selection');
      return;
    }
    
    setSelectedLanguage(language);
    
    // Verify backend connectivity
    verifyBackendConnectivity()
      .then(connected => {
        console.log('Backend connectivity check result:', connected);
        setBackendConnected(connected);
        
        if (!connected) {
          // If not connected, show an error
          setError('Unable to connect to the backend server. Please try again later.');
        }
        
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Backend connectivity check failed:', err);
        setBackendConnected(false);
        setError('Failed to verify backend connectivity. Please refresh the page or try again later.');
        setIsLoading(false);
      });
  }, [router]);

  const handleAssessmentComplete = (result: SpeakingAssessmentResult) => {
    console.log('Assessment completed:', result);
    // You can save the result to user profile or perform other actions here
  };

  const handleSelectLevel = (level: string) => {
    // Store the selected level in session storage
    sessionStorage.setItem('selectedLevel', level);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Log the navigation attempt
    console.log('Navigating to speech with AI-assessed level:', level);
    
    // Use direct navigation for reliability (based on your existing pattern)
    setTimeout(() => {
      console.log('Executing navigation to speech page');
      window.location.href = '/speech';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('assessment/speaking')) {
          console.log('Still on speaking assessment page, using fallback navigation');
          window.location.replace('/speech');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 300);
  };

  const handleStartOver = () => {
    // Clear all session storage
    sessionStorage.clear();
    // Navigate to home page
    console.log('Starting over - cleared session storage');
    window.location.href = '/';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('assessment/speaking')) {
        console.log('Still on speaking assessment page, using fallback navigation for start over');
        window.location.replace('/');
      }
    }, 1000);
  };

  const handleManualSelection = () => {
    // Navigate to level selection page
    console.log('Navigating to manual level selection');
    window.location.href = '/level-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('assessment/speaking')) {
        console.log('Still on speaking assessment page, using fallback navigation to level selection');
        window.location.replace('/level-selection');
      }
    }, 1000);
  };

  return (
    <div className="min-h-screen flex flex-col text-white">
      <NavBar />
      <main className="flex-grow flex flex-col p-4 md:p-8">
        <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white mb-4 animate-fade-in">
              Speaking Assessment
            </h1>
            <p className="text-white/80 text-lg mb-8 animate-fade-in" style={{animationDelay: '100ms'}}>
              {selectedLanguage === 'dutch' && 'Beoordeel je spreekvaardigheid in het Nederlands'}
              {selectedLanguage === 'english' && 'Assess your speaking proficiency in English'}
              {selectedLanguage === 'spanish' && 'Evalúa tu habilidad para hablar en español'}
              {selectedLanguage === 'german' && 'Bewerte deine Sprechfähigkeit auf Deutsch'}
              {selectedLanguage === 'french' && 'Évaluez votre compétence orale en français'}
              {selectedLanguage === 'portuguese' && 'Avalie sua proficiência oral em português'}
              {!selectedLanguage && 'Assess your speaking proficiency'}
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : error ? (
            <div className="bg-red-900/50 border border-red-500 text-red-200 p-6 rounded-lg text-center">
              <h3 className="text-xl font-bold mb-2">Connection Error</h3>
              <p>{error}</p>
              <div className="mt-6 flex justify-center space-x-4">
                <button 
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg"
                >
                  Retry Connection
                </button>
                <button 
                  onClick={handleStartOver}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
                >
                  Start Over
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Assessment Component */}
              <SpeakingAssessment 
                language={selectedLanguage || 'english'} 
                onComplete={handleAssessmentComplete}
                onSelectLevel={handleSelectLevel}
              />
              
              {/* Alternative Option */}
              <div className="text-center mt-8 pt-6 border-t border-gray-700">
                <p className="text-gray-400 mb-4">Prefer to select your level manually?</p>
                <button 
                  onClick={handleManualSelection}
                  className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white"
                >
                  Go to Manual Level Selection
                </button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
