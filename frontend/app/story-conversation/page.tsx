'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { isAuthenticated } from '@/lib/auth-utils';
import { worldBuildingAPI, type StoryWorld } from '@/lib/world-building-api';

// Dynamically import StoryConversationClient with no SSR
const StoryConversationClient = dynamic(() => import('./story-conversation-client'), { ssr: false });

export default function StoryConversationPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [worldId, setWorldId] = useState<string | null>(null);
  const [world, setWorld] = useState<StoryWorld | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigationHandledRef = useRef(false);
  const initializationCompleteRef = useRef(false);

  // Initialize the page parameters
  const initializePage = async () => {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const worldParam = urlParams.get('world');
      
      if (!worldParam) {
        console.log('[StoryConversationPage] Missing world parameter, redirecting to worlds page');
        window.location.href = '/worlds';
        return;
      }

      console.log('[StoryConversationPage] Found world ID in URL:', worldParam);
      setWorldId(worldParam);

      try {
        // Fetch world details
        const worldData = await worldBuildingAPI.getWorldDetails(worldParam);
        setWorld(worldData);
        
        console.log('[StoryConversationPage] Retrieved world details:', worldData);
        
        initializationCompleteRef.current = true;
        setIsLoading(false);
      } catch (worldError) {
        console.error('[StoryConversationPage] Error retrieving world:', worldError);
        setError('Failed to load story world. Please try again.');
        setIsLoading(false);
      }
    } catch (error) {
      console.error('[StoryConversationPage] Error during initialization:', error);
      setError('Failed to initialize story conversation. Please try again.');
      setIsLoading(false);
    }
  };

  // Initialize the story conversation page with parameters from URL
  useEffect(() => {
    // Prevent multiple executions of this effect
    if (navigationHandledRef.current || initializationCompleteRef.current) {
      return;
    }
    
    console.log('[StoryConversationPage] Initializing story conversation page');
    navigationHandledRef.current = true;
    
    // Initialize the page with parameters
    initializePage();
  }, []);
  
  if (isLoading || authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92]">
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
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
              </svg>
            </div>
            <p className="text-white text-xl font-medium">Loading Story World...</p>
            <p className="text-white/70 text-sm mt-2">
              Preparing your collaborative storytelling experience
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !world || !worldId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92]">
        <div className="text-center">
          <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full mx-4">
            <div className="text-center">
              <svg className="h-12 w-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Story World Not Found
              </h3>
              <p className="text-gray-600 mb-4">
                {error || 'The requested story world could not be loaded.'}
              </p>
              <button
                onClick={() => router.push('/worlds')}
                className="px-6 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors"
              >
                Back to Worlds
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen text-white story-conversation-page bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92]">
      <NavBar activeSection="section1" />
      
      {/* Main Content */}
      <div className="flex-grow">
        <StoryConversationClient 
          worldId={worldId}
          world={world}
        />
      </div>
    </div>
  );
}
