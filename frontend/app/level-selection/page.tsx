'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
// Sound effects temporarily disabled
// import { useAudio } from '@/lib/useAudio';

interface Level {
  code: string;
  name: string;
  description: string;
}

export default function LevelSelection() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [levels, setLevels] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Sound effects temporarily disabled
  // const { playSelectionSound, playSuccessSound } = useAudio();

  useEffect(() => {
    // Retrieve the selected language from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    if (!language) {
      // If no language is selected, redirect to language selection
      router.push('/language-selection');
      return;
    }
    
    setSelectedLanguage(language);
    
    // Fetch the available languages and levels from the backend
    fetchLanguagesAndLevels(language);
  }, [router]);

  const fetchLanguagesAndLevels = async (language: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Determine the API URL based on the environment
      let baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
      
      // Handle localhost and 127.0.0.1 cases
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        baseUrl = 'http://localhost:8001';
      }
      
      console.log('Using API base URL:', baseUrl);
      
      // Make sure we're using the correct endpoint format
      // The backend expects direct calls to /api/languages
      const response = await fetch(`${baseUrl}/api/languages`);
      
      if (!response.ok) {
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

  const handleLevelSelect = (levelCode: string) => {
    setSelectedLevel(levelCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLevel', levelCode);
    
    // Sound effects temporarily disabled
    /*
    // Try to play the selection sound, but don't wait if it fails
    try {
      // Play selection sound effect and handle navigation
      const soundPromise = playSelectionSound() || Promise.resolve();
      
      // Use the sound promise to coordinate navigation
      soundPromise
        .then(() => {
          // Add a minimal delay for better UX
          setTimeout(() => {
            // Try to play success sound but don't block navigation if it fails
            try {
              playSuccessSound();
            } catch (error) {
              console.warn('Error playing success sound:', error);
            }
            
            // Navigate to the conversation page
            router.push('/speech');
          }, 100);
        })
        .catch(() => {
          // If sound fails, still navigate after a short delay
          setTimeout(() => {
            router.push('/speech');
          }, 100);
        });
    } catch (error) {
      console.warn('Error in level selection:', error);
      // If anything fails, ensure navigation still happens
      setTimeout(() => {
        router.push('/speech');
      }, 100);
    }
    */
    
    // Direct navigation without sound effects
    router.push('/speech');
  };

  // Format the levels for display
  const formattedLevels = Object.entries(levels).map(([code, description]) => ({
    code,
    name: code,
    description: description as string
  }));

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            Select Your Level
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2 text-improved">
            Choose your proficiency level in {selectedLanguage && selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)}
          </p>
        </div>

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-500 dark:text-red-400">{error}</p>
              <button
                onClick={() => fetchLanguagesAndLevels(selectedLanguage || 'english')}
                className="mt-4 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-md transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-3xl">
              {formattedLevels.map((level) => (
                <button
                  key={level.code}
                  onClick={() => handleLevelSelect(level.code)}
                  className={`
                    relative flex flex-col items-start p-6 rounded-xl text-left
                    transition-all duration-300 transform hover:scale-102
                    ${
                      selectedLevel === level.code
                        ? 'bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border-2 border-indigo-500/50 shadow-lg'
                        : 'bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20'
                    }
                  `}
                >
                  <h2 className="text-xl font-semibold mb-2 gradient-text dark:from-indigo-300 dark:to-purple-300">
                    {level.name} - {level.code === 'A1' || level.code === 'A2' ? 'Beginner' : 
                                    level.code === 'B1' || level.code === 'B2' ? 'Intermediate' : 'Advanced'}
                  </h2>
                  <p className="text-sm text-muted-foreground dark:text-slate-400">
                    {level.description}
                  </p>
                  {selectedLevel === level.code && (
                    <div className="absolute top-3 right-3">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center">
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
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
