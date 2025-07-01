'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { isAuthenticated } from '@/lib/auth-utils';
import { isPlanValid, getRemainingTime, checkAndMarkSessionExpired } from '@/lib/guest-utils';
import PendingLearningPlanHandler from '@/components/pending-learning-plan-handler';
import TimeUpModal from '@/components/time-up-modal';
import LeaveConfirmationModal from '@/components/leave-confirmation-modal';

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
  
  // State for showing the leave site warning modal
  const [showLeaveWarning, setShowLeaveWarning] = useState(false);
  const [pendingNavigationUrl, setPendingNavigationUrl] = useState<string | null>(null);
  
  // State for showing the time's up modal
  const [showTimeUpModal, setShowTimeUpModal] = useState(false);
  
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
        
        // Check if this plan has been marked as expired (from back button navigation)
        const isPlanExpired = sessionStorage.getItem(`plan_${planParam}_expired`) === 'true';
        if (isPlanExpired) {
          console.log('[SpeechPage] Plan was previously expired, redirecting to home');
          window.location.href = '/';
          return;
        }
        
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
              
              // Immediately check if the plan is still valid based on time limits
              const userAuthenticated = isAuthenticated();
              
              // Use the enhanced validation function that also marks as expired
              const isExpired = checkAndMarkSessionExpired(planParam, userAuthenticated);
              
              if (isExpired) {
                console.log('[SpeechPage] Plan has expired on page load, showing time up modal');
                // Show the time's up modal instead of redirecting
                setShowTimeUpModal(true);
                return;
              }
            }
            
            setSelectedLanguage(plan.language);
            setSelectedLevel(plan.proficiency_level);
            // These properties might be stored elsewhere or need to be handled differently
            // since they don't exist directly on the LearningPlan interface
            const topic = sessionStorage.getItem('selectedTopic');
            const customPrompt = sessionStorage.getItem('customTopicText');
            
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
      const customPrompt = sessionStorage.getItem('customTopicText');
      
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
      if (topic === 'custom' && customPrompt) {
        console.log('[SpeechPage] Found custom topic prompt:', customPrompt);
        setCustomTopicPrompt(customPrompt);
      }
      
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
    
    // Clear any navigation flags that might cause issues
    sessionStorage.removeItem('intentionalNavigation');
    sessionStorage.removeItem('backButtonNavigation');
    sessionStorage.removeItem('popStateToTopicSelection');
    sessionStorage.removeItem('navigationInProgress');
    
    // Reset the refresh count to prevent false loop detection
    sessionStorage.setItem(refreshCountKey, '0');
    
    // Initialize the page with parameters
    initializePage();
  }, [user]);
  
  // Override browser's default "Leave site?" modal with custom modal
  useEffect(() => {
    // Only set up navigation protection after the page has fully loaded
    if (isLoading || authLoading) {
      return;
    }

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Always show custom modal for page refresh/close when on speech page
      if (!allowBackNavigation) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    // Handle browser back/forward navigation
    const handlePopState = (e: PopStateEvent) => {
      console.log('[SpeechPage] Back button pressed, showing confirmation modal');
      
      // Always show modal for back navigation unless explicitly allowed
      if (!allowBackNavigation) {
        // Prevent the navigation
        e.preventDefault();
        
        // Push the current state back to prevent actual navigation
        window.history.pushState(null, '', window.location.href);
        
        // Show our custom modal
        setShowLeaveWarning(true);
        setPendingNavigationUrl('/language-selection');
      }
    };

    // Push a state to handle back button - only after page is loaded
    window.history.pushState(null, '', window.location.href);
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [allowBackNavigation, isLoading, authLoading]);
  
  // Effect to periodically check plan validity
  useEffect(() => {
    if (selectedPlanId && planCreationTime) {
      const checkPlanValidity = () => {
        const userAuthenticated = isAuthenticated();
        if (!isPlanValid(userAuthenticated, planCreationTime)) {
          console.log('[SpeechPage] Plan has expired during session, showing time up modal');
          // Show the time's up modal instead of redirecting
          setShowTimeUpModal(true);
          
          // Set a flag in session storage to indicate this plan has expired
          sessionStorage.setItem(`plan_${selectedPlanId}_expired`, 'true');
        }
      };
      
      // Check plan validity every 10 seconds
      const intervalId = setInterval(checkPlanValidity, 10000);
      
      return () => {
        clearInterval(intervalId);
      };
    }
  }, [selectedPlanId, planCreationTime]);
  
  // Handle change language action - show a warning if needed
  const handleChangeLanguage = () => {
    // Check if we're in the middle of a conversation
    if (sessionStorage.getItem('isInConversation') === 'true') {
      // Show warning modal
      setShowLeaveWarning(true);
      setPendingNavigationUrl('/language-selection');
    } else {
      // No active conversation, navigate directly
      router.push('/language-selection');
    }
  };
  
  // Confirm navigation after warning
  const handleConfirmNavigation = () => {
    if (pendingNavigationUrl) {
      // Set a flag to indicate intentional navigation
      sessionStorage.setItem('intentionalNavigation', 'true');
      
      // Clear conversation flag
      sessionStorage.removeItem('isInConversation');
      
      // Navigate after a short delay to ensure flag is set
      setTimeout(() => {
        router.push(pendingNavigationUrl);
      }, 100);
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
      
      {/* Enhanced Leave Confirmation Modal */}
      <LeaveConfirmationModal
        isOpen={showLeaveWarning}
        onStay={handleCancelNavigation}
        onLeave={handleConfirmNavigation}
        userType={user ? 'authenticated' : 'guest'}
      />
      
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
      
      {/* Time's Up Modal */}
      <TimeUpModal 
        isOpen={showTimeUpModal}
        onClose={() => {
          // Mark the plan as expired even when closing the modal
          if (selectedPlanId) {
            sessionStorage.setItem(`plan_${selectedPlanId}_expired`, 'true');
          }
          setShowTimeUpModal(false);
        }}
        onSignIn={() => {
          // Mark the plan as expired to prevent back button navigation
          if (selectedPlanId) {
            sessionStorage.setItem(`plan_${selectedPlanId}_expired`, 'true');
            sessionStorage.removeItem(`plan_${selectedPlanId}_creationTime`);
          }
          router.push('/login');
        }}
        onSignUp={() => {
          // Mark the plan as expired to prevent back button navigation
          if (selectedPlanId) {
            sessionStorage.setItem(`plan_${selectedPlanId}_expired`, 'true');
            sessionStorage.removeItem(`plan_${selectedPlanId}_creationTime`);
          }
          router.push('/signup');
        }}
        onNewAssessment={() => {
          // Mark the plan as expired to prevent back button navigation
          if (selectedPlanId) {
            sessionStorage.setItem(`plan_${selectedPlanId}_expired`, 'true');
            sessionStorage.removeItem(`plan_${selectedPlanId}_creationTime`);
          }
          router.push('/');
        }}
      />
    </div>
  );
}
