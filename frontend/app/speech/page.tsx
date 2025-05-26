'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { isAuthenticated } from '@/lib/auth-utils';
import { isPlanValid } from '@/lib/guest-utils';
import PendingLearningPlanHandler from '@/components/pending-learning-plan-handler';

// Define the props interface to match the SpeechClient component
interface SpeechClientProps {
  language: string;
  level: string;
  topic?: string;
  userPrompt?: string;
}

// Dynamically import SpeechClient with no SSR
const SpeechClient = dynamic(() => import('./speech-client'), { ssr: false });

export default function SpeechPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [customTopicPrompt, setCustomTopicPrompt] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authRedirectTriggered, setAuthRedirectTriggered] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [planCreationTime, setPlanCreationTime] = useState<string | null>(null);
  const navigationHandledRef = useRef(false);
  const initializationCompleteRef = useRef(false);
  
  // Set up session refresh prevention
  const refreshCountKey = 'speechPageRefreshCount';
  const [allowBackNavigation, setAllowBackNavigation] = useState(false);
  
  // Allow non-authenticated users to access the speech page
  useEffect(() => {
    // Only run this check once auth is no longer loading
    if (!authLoading && !user) {
      console.log('[SpeechPage] User not authenticated, but allowing access to speech page');
      
      // Check for URL parameters
      const urlParams = new URLSearchParams(window.location.search);
      const planParam = urlParams.get('plan');
      
      // If there's a plan parameter, store it for potential future login
      if (planParam) {
        console.log('[SpeechPage] Storing plan ID for potential future assignment:', planParam);
        sessionStorage.setItem('pendingLearningPlanId', planParam);
        sessionStorage.setItem('redirectWithPlanId', planParam);
      }
    }
  }, [user, authLoading]);

  // Function to initialize the page parameters
  const initializePage = async () => {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const planParam = urlParams.get('plan');
      
      if (planParam) {
        console.log('[SpeechPage] Found plan ID in URL:', planParam);
        setSelectedPlanId(planParam);
        
        try {
          // Import the API function dynamically to avoid circular dependencies
          const { getLearningPlan } = await import('@/lib/learning-api');
          const plan = await getLearningPlan(planParam);
          
          if (plan) {
            console.log('[SpeechPage] Retrieved plan details:', plan);
            
            // Store plan creation time if not already stored
            const storedCreationTime = sessionStorage.getItem(`plan_${planParam}_creationTime`);
            if (!storedCreationTime) {
              const creationTime = new Date().toISOString();
              sessionStorage.setItem(`plan_${planParam}_creationTime`, creationTime);
              setPlanCreationTime(creationTime);
            } else {
              setPlanCreationTime(storedCreationTime);
              
              // Check if the plan is still valid based on time limits
              const userAuthenticated = isAuthenticated();
              if (!isPlanValid(userAuthenticated, storedCreationTime)) {
                console.log('[SpeechPage] Plan has expired, redirecting to home page');
                sessionStorage.removeItem(`plan_${planParam}_creationTime`);
                router.push('/');
                return;
              }
            }
            
            setSelectedLanguage(plan.language);
            setSelectedLevel(plan.proficiency_level);
            // These properties might be stored elsewhere or need to be handled differently
            // since they don't exist directly on the LearningPlan interface
            const topic = sessionStorage.getItem('selectedTopic');
            const customPrompt = sessionStorage.getItem('customTopicPrompt');
            
            if (topic) setSelectedTopic(topic);
            if (customPrompt) setCustomTopicPrompt(customPrompt);
            
            // Store these in session storage for persistence
            sessionStorage.setItem('selectedLanguage', plan.language);
            sessionStorage.setItem('selectedLevel', plan.proficiency_level);
            // We no longer reference plan.topic and plan.custom_prompt as they don't exist in the interface
            // Keep any existing topic and custom prompt values from session storage
            
            initializationCompleteRef.current = true;
            setIsLoading(false);
            return;
          }
        } catch (planError) {
          console.error('[SpeechPage] Error retrieving plan:', planError);
          // Continue to try session storage if plan retrieval fails
        }
      }
      
      // If no plan ID or plan retrieval failed, try session storage
      const language = sessionStorage.getItem('selectedLanguage');
      const level = sessionStorage.getItem('selectedLevel');
      const topic = sessionStorage.getItem('selectedTopic');
      const customPrompt = sessionStorage.getItem('customTopicPrompt');
      
      console.log(`[SpeechPage] Retrieved from sessionStorage - language: ${language} level: ${level}`);
      
      if (!language || !level) {
        console.log('[SpeechPage] Missing required parameters, redirecting to language selection');
        window.location.href = '/language-selection';
        return;
      }
      
      // Set the parameters from session storage
      setSelectedLanguage(language);
      setSelectedLevel(level);
      if (topic) setSelectedTopic(topic);
      if (topic === 'custom' && customPrompt) setCustomTopicPrompt(customPrompt);
      
      // We've successfully loaded the speech page with session storage parameters
      initializationCompleteRef.current = true;
      setIsLoading(false);
    } catch (error) {
      console.error('[SpeechPage] Error during initialization:', error);
      // If all else fails, redirect to language selection
      window.location.href = '/language-selection';
    }
  };

  // Initialize the speech page with parameters from URL or session storage
  useEffect(() => {
    // Prevent multiple executions of this effect
    if (navigationHandledRef.current || initializationCompleteRef.current) {
      return;
    }
    
    console.log('[SpeechPage] Initializing speech page for user (authenticated: ' + (user !== null) + ')');
    navigationHandledRef.current = true;
    
    // IMPORTANT: Completely disable automatic redirects to fix back button navigation
    // We'll only handle the initialization of speech parameters
    
    // Clear any navigation flags that might cause issues
    sessionStorage.removeItem('intentionalNavigation');
    sessionStorage.removeItem('backButtonNavigation');
    sessionStorage.removeItem('popStateToTopicSelection');
    sessionStorage.removeItem('navigationInProgress');
    
    // Reset the refresh count to prevent false loop detection
    sessionStorage.setItem(refreshCountKey, '0');
    
    // Set up a simple listener for back button that doesn't interfere with navigation
    const handlePopState = (event: PopStateEvent) => {
      console.log('[SpeechPage] Detected browser back button navigation');
      // Don't prevent default navigation
    };
    
    // Add the event listener for back button
    window.addEventListener('popstate', handlePopState);
    
    // Initialize the page with parameters
    initializePage();
    
    // Clean up the event listener when the component unmounts
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [user]);

  // State for showing the leave site warning modal
  const [showLeaveWarning, setShowLeaveWarning] = useState(false);
  const [pendingNavigationUrl, setPendingNavigationUrl] = useState<string | null>(null);
  
  // Show warning before leaving the conversation
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!allowBackNavigation) {
        // Standard way to show a confirmation dialog
        e.preventDefault();
        // Chrome requires returnValue to be set
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [allowBackNavigation]);
  
  // Effect to periodically check plan validity
  useEffect(() => {
    if (selectedPlanId && planCreationTime) {
      const checkPlanValidity = () => {
        const userAuthenticated = isAuthenticated();
        if (!isPlanValid(userAuthenticated, planCreationTime)) {
          console.log('[SpeechPage] Plan has expired during session, redirecting to home page');
          sessionStorage.removeItem(`plan_${selectedPlanId}_creationTime`);
          router.push('/');
        }
      };
      
      // Check plan validity every 10 seconds
      const intervalId = setInterval(checkPlanValidity, 10000);
      
      return () => {
        clearInterval(intervalId);
      };
    }
  }, [selectedPlanId, planCreationTime, router]);
  
  // Handle change language action - show a warning if needed
  const handleChangeLanguage = () => {
    if (sessionStorage.getItem('isInConversation') === 'true') {
      setShowLeaveWarning(true);
      setPendingNavigationUrl('/language-selection');
    } else {
      // Clear all selections except language which will be reselected
      sessionStorage.removeItem('selectedLevel');
      sessionStorage.removeItem('selectedTopic');
      sessionStorage.removeItem('customTopicText');
      // Clear any navigation flags
      sessionStorage.removeItem('fromLevelSelection');
      sessionStorage.removeItem('intentionalNavigation');
      
      console.log('Navigating to language selection from speech page');
      window.location.href = '/language-selection';
      
      // Fallback navigation in case the first attempt fails
      setTimeout(() => {
        if (window.location.pathname.includes('speech')) {
          console.log('Still on speech page, using fallback navigation to language selection');
          window.location.replace('/language-selection');
        }
      }, 1000);
    }
  };
  
  // Handle change level action - show a warning if needed
  const handleChangeLevel = () => {
    if (sessionStorage.getItem('isInConversation') === 'true') {
      setShowLeaveWarning(true);
      setPendingNavigationUrl('/level-selection');
    } else {
      // Clear level selection but keep language and topic
      sessionStorage.removeItem('selectedLevel');
      // Clear any navigation flags
      sessionStorage.removeItem('intentionalNavigation');
      
      console.log('Navigating to level selection from speech page');
      window.location.href = '/level-selection';
      
      // Fallback navigation in case the first attempt fails
      setTimeout(() => {
        if (window.location.pathname.includes('speech')) {
          console.log('Still on speech page, using fallback navigation to level selection');
          window.location.replace('/level-selection');
        }
      }, 1000);
    }
  };
  
  // Handle change topic action - show a warning if needed
  const handleChangeTopic = () => {
    if (sessionStorage.getItem('isInConversation') === 'true') {
      setShowLeaveWarning(true);
      setPendingNavigationUrl('/topic-selection');
    } else {
      // Clear topic selection but keep language
      sessionStorage.removeItem('selectedTopic');
      sessionStorage.removeItem('customTopicText');
      sessionStorage.removeItem('selectedLevel');
      // Set a flag to indicate we're intentionally going to topic selection
      sessionStorage.setItem('fromLevelSelection', 'true');
      // Clear any navigation flags
      sessionStorage.removeItem('intentionalNavigation');
      
      console.log('Navigating to topic selection from speech page');
      window.location.href = '/topic-selection';
      
      // Fallback navigation in case the first attempt fails
      setTimeout(() => {
        if (window.location.pathname.includes('speech')) {
          console.log('Still on speech page, using fallback navigation to topic selection');
          window.location.replace('/topic-selection');
        }
      }, 1000);
    }
  };
  
  // Confirm navigation after warning
  const handleConfirmNavigation = () => {
    sessionStorage.removeItem('isInConversation');
    
    if (pendingNavigationUrl) {
      // If navigating to language selection, clear relevant storage items
      if (pendingNavigationUrl === '/language-selection') {
        // Clear all selections except language which will be reselected
        sessionStorage.removeItem('selectedLevel');
        sessionStorage.removeItem('selectedTopic');
        sessionStorage.removeItem('customTopicText');
        // Clear any navigation flags
        sessionStorage.removeItem('fromLevelSelection');
        sessionStorage.removeItem('intentionalNavigation');
      }
      
      console.log(`Confirming navigation to ${pendingNavigationUrl}`);
      window.location.href = pendingNavigationUrl;
      
      // Fallback navigation in case the first attempt fails
      const currentPath = window.location.pathname;
      setTimeout(() => {
        if (window.location.pathname === currentPath) {
          console.log(`Still on ${currentPath}, using fallback navigation to ${pendingNavigationUrl}`);
          window.location.replace(pendingNavigationUrl);
        }
      }, 1000);
    }
    
    setShowLeaveWarning(false);
  };
  
  // Cancel navigation after warning
  const handleCancelNavigation = () => {
    setPendingNavigationUrl(null);
    setShowLeaveWarning(false);
  };
  
  if (isLoading || authLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <NavBar />
        <div className="flex-grow flex items-center justify-center">
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
                Starting conversation
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen text-white speech-page">
      {/* Handler for pending learning plans - only shown for authenticated users */}
      {user && <PendingLearningPlanHandler />}
      <NavBar activeSection="section1" />
      
      {/* Warning Modal for conversation interruption */}
      {showLeaveWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="glass-card rounded-lg shadow-xl max-w-md w-full p-6 border border-white/20">
            <div className="flex items-center text-amber-500 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-lg font-medium">End current conversation?</h3>
            </div>
            <p className="text-white/80 mb-6">You're currently in a conversation. Leaving this page will end your current session.</p>
            <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
              <button
                type="button"
                className="primary-button px-4 py-2 rounded-lg"
                onClick={handleCancelNavigation}
              >
                Continue Conversation
              </button>
              <button
                type="button"
                className="primary-button px-4 py-2 rounded-lg"
                onClick={handleConfirmNavigation}
              >
                End Conversation
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Main Content */}
      <div className="flex-grow">
        {selectedLanguage && selectedLevel && (
          <SpeechClient 
            language={selectedLanguage} 
            level={selectedLevel} 
            topic={selectedTopic || undefined}
            userPrompt={selectedTopic === 'custom' ? customTopicPrompt || undefined : undefined}
          />
        )}
      </div>
    </div>
  );
}
