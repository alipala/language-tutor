'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useNavigation } from '@/lib/navigation';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/nav-bar';
import SpeakingAssessment from '@/components/speaking-assessment';
import LeaveConfirmationModal from '@/components/leave-confirmation-modal';
import { SpeakingAssessmentResult } from '@/lib/speaking-assessment-api';
import { verifyBackendConnectivity } from '@/lib/healthCheck';

export default function SpeakingAssessmentPage() {
  const router = useRouter();
  const navigation = useNavigation();
  const { user } = useAuth();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  
  // State for leave confirmation modal
  const [showLeaveWarning, setShowLeaveWarning] = useState(false);

  // Handle back button navigation with confirmation modal
  useEffect(() => {
    const handlePopState = (e: PopStateEvent) => {
      console.log('[SpeakingAssessment] Back button pressed, showing custom modal');
      
      // Prevent the navigation completely
      e.preventDefault();
      
      // Push the current state back to prevent actual navigation
      window.history.pushState(null, '', window.location.href);
      
      // Show our custom modal
      setShowLeaveWarning(true);
    };

    // Push a state to handle back button
    window.history.pushState(null, '', window.location.href);
    
    window.addEventListener('popstate', handlePopState);
    
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  useEffect(() => {
    console.log('Speaking assessment page initialized at:', new Date().toISOString());
    console.log('Current pathname:', window.location.pathname);
    
    // Retrieve the selected language using the navigation service
    const language = navigation.getSelectedLanguage();
    console.log('Retrieved language:', language);
    
    if (!language) {
      console.warn('No language found, redirecting to language selection');
      // If no language is selected, redirect to language selection
      navigation.navigateToLanguageSelection();
      return;
    }
    
    setSelectedLanguage(language);
    
    // Verify backend connectivity
    console.log('Verifying backend connectivity...');
    verifyBackendConnectivity()
      .then(connected => {
        console.log('Backend connectivity check result:', connected);
        setBackendConnected(connected);
        
        if (!connected) {
          // If not connected, show an error
          console.error('Backend connectivity check failed - server unreachable');
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
    // Store the selected level using the navigation service
    navigation.setSelectedLevel(level);
    
    // Check if there's a pending learning plan ID
    const pendingLearningPlanId = navigation.getPendingLearningPlanId();
    
    // Import and use the isAuthenticated function from auth utils
    const { isAuthenticated } = require('@/lib/auth-utils');
    const userAuthenticated = isAuthenticated();
    
    // Log the navigation attempt with authentication status
    console.log('User authenticated status:', userAuthenticated);
    console.log('Pending learning plan ID:', pendingLearningPlanId);
    
    // Allow guest users to proceed to the speech page directly
    // This is the new guest user flow that doesn't require authentication
    console.log(`Navigating to speech page with level: ${level}`);
    navigation.navigateToSpeech(pendingLearningPlanId || undefined);
  };

  const handleStartOver = () => {
    // Clear navigation state and navigate to home page
    try {
      navigation.clearNavigationState();
    } catch (e) {
      console.error('Error clearing navigation state:', e);
    }
    
    console.log('Starting over - cleared navigation state');
    navigation.navigateToHome();
  };

  const handleManualSelection = () => {
    // Navigate to level selection page using the navigation service
    console.log('Navigating to manual level selection');
    navigation.navigateToLevelSelection();
  };

  // Handle leave confirmation modal actions
  const handleCancelNavigation = () => {
    setShowLeaveWarning(false);
  };

  const handleConfirmNavigation = () => {
    // Navigate to flow page with assessment mode
    router.push('/flow?mode=assessment');
    setShowLeaveWarning(false);
  };

  return (
    <div className="min-h-screen flex flex-col text-white bg-[var(--turquoise)]">
      <NavBar />
      <main className="flex-grow flex flex-col p-4 md:p-8 pt-20 md:pt-24">
        <div className="flex flex-col flex-1 items-stretch w-full max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-4">
            <h1 className="text-4xl md:text-5xl font-bold mb-2 text-white">
              Speaking Assessment
            </h1>
            <p className="text-gray-700 text-lg">
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
            </>
          )}
        </div>
      </main>

      {/* Leave Confirmation Modal */}
      <LeaveConfirmationModal
        isOpen={showLeaveWarning}
        onStay={handleCancelNavigation}
        onLeave={handleConfirmNavigation}
        userType={user ? 'authenticated' : 'guest'}
      />
    </div>
  );
}
