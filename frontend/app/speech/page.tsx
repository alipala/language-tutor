'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// Define the props interface to match the SpeechClient component
interface SpeechClientProps {
  language: string;
  level: string;
}

// Import the component with no SSR and specify the props type
const SpeechClient = dynamic<SpeechClientProps>(() => import('@/app/speech/speech-client'), {
  ssr: false
});

export default function SpeechPage() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Add a reference to track if we've already handled navigation
  const navigationHandledRef = useRef(false);
  
  useEffect(() => {
    // Prevent multiple executions of this effect
    if (navigationHandledRef.current) {
      console.log('Navigation already handled, skipping');
      return;
    }
    
    // Debug information about the current page
    console.log('Speech page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Check if we're in a refresh loop
    const refreshCountKey = 'speechPageRefreshCount';
    const refreshCount = parseInt(sessionStorage.getItem(refreshCountKey) || '0');
    console.log('Current refresh count:', refreshCount);
    
    if (refreshCount > 3) {
      console.log('Detected potential refresh loop, resetting session storage');
      // Clear only navigation-related items, not the language/level selections
      sessionStorage.removeItem(refreshCountKey);
      sessionStorage.removeItem('speechPageLoadTime');
      sessionStorage.removeItem('hasNavigatedFromSpeechPage');
    } else {
      // Increment refresh count
      sessionStorage.setItem(refreshCountKey, (refreshCount + 1).toString());
    }
    
    // Retrieve the selected language and level from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    const level = sessionStorage.getItem('selectedLevel');
    
    console.log('Retrieved from sessionStorage - language:', language, 'level:', level);
    
    // Mark that we've handled navigation
    navigationHandledRef.current = true;
    
    if (!language || !level) {
      // If no language or level is selected, redirect to language selection
      console.log('Missing language or level, redirecting to language selection');
      
      // Use direct window.location for reliable navigation in Railway
      // But wrap in setTimeout to ensure we don't interrupt the current render cycle
      setTimeout(() => {
        console.log('Executing navigation to language selection');
        window.location.href = '/language-selection';
        
        // Fallback navigation in case the first attempt fails (for Railway)
        const fallbackTimer = setTimeout(() => {
          if (window.location.pathname.includes('speech')) {
            console.log('Still on speech page, using fallback navigation to language selection');
            window.location.replace('/language-selection');
          }
        }, 1000);
        
        return () => clearTimeout(fallbackTimer);
      }, 100);
      return;
    }
    
    // If we have language and level, update the state
    setSelectedLanguage(language);
    setSelectedLevel(level);
    setIsLoading(false);
    
    // Reset refresh count when successfully loaded
    setTimeout(() => {
      sessionStorage.setItem(refreshCountKey, '0');
    }, 2000);
  }, []);
  
  // State for showing the leave site warning modal
  const [showLeaveWarning, setShowLeaveWarning] = useState(false);
  const [pendingNavigationUrl, setPendingNavigationUrl] = useState<string | null>(null);
  
  // Add a separate effect for handling beforeunload events
  useEffect(() => {
    // Add an event listener to prevent page refreshes from F5 or browser refresh
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Only prevent unload if we're in a conversation
      const isInConversation = sessionStorage.getItem('isInConversation') === 'true';
      if (isInConversation) {
        console.log('User attempted to refresh during conversation');
        // Standard way to show a confirmation dialog before page unload
        const message = 'Leave site? Changes that you made may not be saved.';
        e.preventDefault();
        e.returnValue = message;
        return message;
      }
    };
    
    // Custom warning dialog for navigation within the app
    const handleLinkClick = (e: MouseEvent) => {
      const isInConversation = sessionStorage.getItem('isInConversation') === 'true';
      if (isInConversation) {
        const linkElement = (e.target as HTMLElement).closest('a');
        if (linkElement && linkElement.getAttribute('href')) {
          const href = linkElement.getAttribute('href');
          // Only intercept internal navigation, not external links
          if (href && (href.startsWith('/') || href.startsWith('#'))) {
            e.preventDefault();
            setPendingNavigationUrl(href);
            setShowLeaveWarning(true);
          }
        }
      }
    };
    
    // Add the event listeners
    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('click', handleLinkClick);
    
    // Clean up the event listeners when component unmounts
    return () => {
      console.log('Speech page component unmounting');
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('click', handleLinkClick);
    };
  }, []);
  
  // Function to handle navigation after warning
  const handleLeaveConfirmation = (confirmed: boolean) => {
    setShowLeaveWarning(false);
    
    if (confirmed && pendingNavigationUrl) {
      // Navigate to the pending URL
      window.location.href = pendingNavigationUrl;
    }
    
    // Reset the pending URL
    setPendingNavigationUrl(null);
  };

  if (isLoading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-b from-slate-900 to-slate-800 text-white">
        <div className="relative w-20 h-20 mb-6">
          <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-indigo-200/20 animate-pulse"></div>
          <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-transparent border-t-indigo-500 animate-spin"></div>
        </div>
        <p className="mt-4 text-indigo-200 animate-pulse">Loading conversation...</p>
      </main>
    );
  }

  return (
    <>
      <SpeechClient language={selectedLanguage!} level={selectedLevel!} />
      
      {/* Modern Leave Site Warning Modal */}
      {showLeaveWarning && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-xl max-w-md w-full overflow-hidden transform transition-all border border-slate-700">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-amber-500/20 to-amber-600/20 border border-amber-500/30 flex items-center justify-center mr-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white">Leave site?</h3>
              </div>
              <p className="text-slate-300 mb-6">Changes that you made may not be saved.</p>
              <div className="flex justify-end space-x-3">
                <button 
                  onClick={() => handleLeaveConfirmation(false)}
                  className="px-5 py-3 text-sm font-medium text-white bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 rounded-full shadow-lg transition-all duration-300 transform hover:translate-y-[-2px]" 
                >
                  Cancel
                </button>
                <button 
                  onClick={() => handleLeaveConfirmation(true)}
                  className="px-5 py-3 text-sm font-medium text-white bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 rounded-full shadow-lg hover:shadow-red-500/20 transition-all duration-300 transform hover:translate-y-[-2px]" 
                >
                  Leave
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
