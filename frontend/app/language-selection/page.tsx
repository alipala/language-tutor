'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAudio } from '@/lib/useAudio';

interface Language {
  code: string;
  name: string;
  flagSrc: string;
}

export default function LanguageSelection() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { playSelectionSound, playSuccessSound } = useAudio();

  const languages: Language[] = [
    {
      code: 'dutch',
      name: 'Dutch',
      flagSrc: '/images/netherlands-flag.svg',
    },
    {
      code: 'english',
      name: 'English',
      flagSrc: '/images/uk-flag.svg',
    },
  ];

  const handleLanguageSelect = (languageCode: string) => {
    // Play selection sound effect
    playSelectionSound();
    
    setSelectedLanguage(languageCode);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedLanguage', languageCode);
    
    // Add a slight delay before navigation for the sound to play and animation to complete
    setTimeout(() => {
      // Play success sound when navigating
      playSuccessSound();
      
      // Navigate to level selection
      router.push('/level-selection');
    }, 500);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-[hsl(var(--background))] via-[hsl(250,70%,97%)] to-[hsl(var(--background-end))] dark:from-slate-900 dark:via-indigo-950/90 dark:to-purple-950/90 bg-pattern">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold tracking-tight gradient-text dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-indigo-200 dark:to-purple-300">
            Select Your Language
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2 text-improved">
            Choose the language you want to practice
          </p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-2xl">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className={`
                  relative flex flex-col items-center justify-center p-6 rounded-xl 
                  transition-all duration-300 transform hover:scale-105
                  ${
                    selectedLanguage === language.code
                      ? 'bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border-2 border-indigo-500/50 shadow-lg'
                      : 'bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20'
                  }
                `}
              >
                <div className="relative w-40 h-40 mb-4 overflow-hidden rounded-lg shadow-md transition-transform duration-300 transform hover:scale-105">
                  <Image
                    src={language.flagSrc}
                    alt={`${language.name} flag`}
                    fill
                    priority
                    style={{ objectFit: 'cover' }}
                    className="transition-opacity duration-300"
                  />
                </div>
                <h2 className="text-2xl font-semibold text-center gradient-text dark:from-indigo-300 dark:to-purple-300">
                  {language.name}
                </h2>
                {selectedLanguage === language.code && (
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
      </div>
    </main>
  );
}
