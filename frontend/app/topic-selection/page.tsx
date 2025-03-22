'use client';

import { useState, useEffect, KeyboardEvent, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface Topic {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export default function TopicSelection() {
  const router = useRouter();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCustomTopicActive, setIsCustomTopicActive] = useState(false);
  const [customTopicText, setCustomTopicText] = useState('');
  const [isExtendingKnowledge, setIsExtendingKnowledge] = useState(false);
  const customInputRef = useRef<HTMLTextAreaElement>(null);

  // Define topics - these can be expanded later
  const topics: Topic[] = [
    {
      id: 'travel',
      name: 'Travel',
      description: 'Discuss travel destinations, experiences, and planning trips.',
      icon: '✈️'
    },
    {
      id: 'food',
      name: 'Food & Cooking',
      description: 'Talk about cuisines, recipes, restaurants, and cooking techniques.',
      icon: '🍲'
    },
    {
      id: 'hobbies',
      name: 'Hobbies & Interests',
      description: 'Share your favorite activities, sports, games, or pastimes.',
      icon: '🎨'
    },
    {
      id: 'culture',
      name: 'Culture & Traditions',
      description: 'Explore cultural aspects, traditions, festivals, and customs.',
      icon: '🏛️'
    },
    {
      id: 'movies',
      name: 'Movies & TV Shows',
      description: 'Discuss films, series, actors, directors, and entertainment.',
      icon: '🎬'
    },
    {
      id: 'music',
      name: 'Music',
      description: 'Talk about music genres, artists, concerts, and preferences.',
      icon: '🎵'
    },
    {
      id: 'technology',
      name: 'Technology',
      description: 'Discuss gadgets, apps, innovations, and digital trends.',
      icon: '💻'
    },
    {
      id: 'environment',
      name: 'Environment & Nature',
      description: 'Explore environmental issues, sustainability, and the natural world.',
      icon: '🌳'
    },
    {
      id: 'custom',
      name: 'Custom Topic',
      description: 'Create your own topic for a personalized conversation experience.',
      icon: '🔍'
    },
  ];

  // Add a useEffect to handle page initialization and react to state changes
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    console.log('Topic selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Retrieve the selected language from session storage
    const language = sessionStorage.getItem('selectedLanguage');
    if (!language) {
      // If no language is selected, redirect to language selection
      console.log('No language selected, redirecting to language selection');
      window.location.href = '/language-selection';
      return;
    }
    
    setSelectedLanguage(language);
    
    // Check if we came from level selection page intentionally
    const fromLevelSelection = sessionStorage.getItem('fromLevelSelection');
    if (fromLevelSelection) {
      // Clear the flag as we've now handled it
      sessionStorage.removeItem('fromLevelSelection');
      console.log('Detected navigation from level selection, staying on topic selection page');
      // We intentionally came here to change the topic, so don't redirect
      return;
    }
    
    // If we already have a topic selected and language, go to level selection
    // but only if we didn't explicitly navigate here to change the topic
    const existingTopic = sessionStorage.getItem('selectedTopic');
    if (existingTopic) {
      console.log('Topic already selected, redirecting to level selection');
      // Use direct navigation for reliability
      window.location.href = '/level-selection';
      
      // Fallback navigation in case the first attempt fails
      setTimeout(() => {
        if (window.location.pathname.includes('topic-selection')) {
          console.log('Still on topic selection page, using fallback navigation');
          window.location.replace('/level-selection');
        }
      }, 1000);
    }
  }, [router]);

  const handleStartOver = () => {
    // Clear all session storage
    sessionStorage.clear();
    // Navigate to home page
    console.log('Starting over - cleared session storage');
    window.location.href = '/';
  };

  const handleChangeLanguage = () => {
    // Go back to language selection
    sessionStorage.removeItem('selectedTopic');
    // Navigate to language selection
    window.location.href = '/language-selection';
  };

  const handleSkipTopic = () => {
    // Skip topic selection (no topic)
    sessionStorage.removeItem('selectedTopic');
    // Navigate to level selection
    window.location.href = '/level-selection';
  };

  const handleTopicSelect = (topicId: string) => {
    // If custom topic is selected, show the modal input overlay instead of navigating
    if (topicId === 'custom') {
      setIsCustomTopicActive(true);
      // Focus the input field after a short delay to ensure it's rendered
      setTimeout(() => {
        if (customInputRef.current) {
          customInputRef.current.focus();
        }
      }, 100);
      return;
    }
    
    // Set loading state while navigating
    setIsLoading(true);
    setSelectedTopic(topicId);
    
    // Store the selection in session storage
    sessionStorage.setItem('selectedTopic', topicId);
    
    // Mark that we're intentionally navigating
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Add detailed logging
    console.log('Topic selected:', topicId);
    console.log('Session storage state:', {
      selectedLanguage: sessionStorage.getItem('selectedLanguage'),
      selectedTopic: topicId,
      intentionalNavigation: true
    });
    
    // Navigate to level selection
    console.log('Navigating to level selection with topic:', topicId);
    
    // Use direct navigation for reliability
    setTimeout(() => {
      console.log('Executing navigation to level selection');
      window.location.href = '/level-selection';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('topic-selection')) {
          console.log('Still on topic selection page, using fallback navigation');
          window.location.replace('/level-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 300);
  };

  const handleCustomTopicSubmit = () => {
    if (!customTopicText.trim()) return;
    
    // Show the extending knowledge message
    setIsExtendingKnowledge(true);
    
    // Store the custom topic in session storage
    sessionStorage.setItem('selectedTopic', 'custom');
    sessionStorage.setItem('customTopicText', customTopicText);
    sessionStorage.setItem('intentionalNavigation', 'true');
    
    // Add detailed logging
    console.log('Custom topic submitted:', customTopicText);
    console.log('Session storage state:', {
      selectedLanguage: sessionStorage.getItem('selectedLanguage'),
      selectedTopic: 'custom',
      customTopicText: customTopicText,
      intentionalNavigation: true
    });
    
    // Navigate to level selection after a short delay to show the message
    setTimeout(() => {
      console.log('Executing navigation to level selection with custom topic');
      window.location.href = '/level-selection';
      
      // Fallback navigation in case the first attempt fails
      const fallbackTimer = setTimeout(() => {
        if (window.location.pathname.includes('topic-selection')) {
          console.log('Still on topic selection page, using fallback navigation');
          window.location.replace('/level-selection');
        }
      }, 1000);
      
      return () => clearTimeout(fallbackTimer);
    }, 2000); // Longer delay to show the message
  };
  
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleCustomTopicSubmit();
    } else if (e.key === 'Escape') {
      setIsCustomTopicActive(false);
      setCustomTopicText('');
    }
  };

  return (
    <main className="flex min-h-screen flex-col app-background text-white p-4 md:p-8">
      <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 mb-4 animate-fade-in">
            Choose a Topic
          </h1>
          <p className="text-slate-300 text-lg mb-8 animate-fade-in" style={{animationDelay: '100ms'}}>
            Select a topic for your {selectedLanguage && selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)} conversation (optional)
          </p>
          <div className="flex space-x-4 justify-center mb-10 animate-fade-in" style={{animationDelay: '200ms'}}>
            <button 
              onClick={handleChangeLanguage}
              className="app-button flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              <span>Change Language</span>
            </button>
            <button 
              onClick={handleSkipTopic}
              className="app-button flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Skip Topic</span>
            </button>
            <button 
              onClick={handleStartOver}
              className="app-button flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Start Over</span>
            </button>
          </div>
        </div>

        {/* Topics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in" style={{animationDelay: '300ms'}}>
          {topics.map((topic) => (
            <button
              key={topic.id}
              onClick={() => handleTopicSelect(topic.id)}
              disabled={isLoading || isExtendingKnowledge}
              className={`group relative overflow-hidden rounded-xl transition-all duration-300 bg-gradient-to-br from-slate-800 to-slate-700 hover:from-indigo-900 hover:to-blue-900 border border-slate-700 hover:border-indigo-500 shadow-lg hover:shadow-indigo-500/20 flex flex-col p-6 text-left min-h-44 transform hover:translate-y-[-2px] ${
                (isLoading || isExtendingKnowledge) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              } ${
                isCustomTopicActive && topic.id === 'custom' ? 'from-indigo-900 to-blue-900 border-indigo-500 shadow-indigo-500/20' : ''
              }`}
            >
              {/* Glow effect on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Icon */}
              <div className="text-4xl mb-4">{topic.icon}</div>
              
              {/* Title */}
              <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-blue-300 transition-colors duration-300">
                {topic.name}
              </h3>
              
              {/* Description */}
              <p className="text-slate-300 text-sm group-hover:text-slate-200 transition-colors duration-300">
                {topic.description}
              </p>
              
              {/* We no longer show the input field inside the topic box */}
            </button>
          ))}
        </div>
        
        {/* Custom Topic Input Modal - Only show when active */}
        {isCustomTopicActive && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/70 z-50 animate-fade-in">
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-6 md:p-8 rounded-xl border border-indigo-500 shadow-lg shadow-indigo-500/20 w-full max-w-md mx-4">
              <h3 className="text-xl md:text-2xl font-semibold text-white mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                Create Your Custom Topic
              </h3>
              <p className="text-slate-300 text-sm md:text-base mb-6">
                What would you like to talk about in your {selectedLanguage && selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)} conversation?
              </p>
              
              <div className="mb-6">
                <textarea
                  ref={customInputRef}
                  value={customTopicText}
                  onChange={(e) => setCustomTopicText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleCustomTopicSubmit();
                    } else if (e.key === 'Escape') {
                      setIsCustomTopicActive(false);
                      setCustomTopicText('');
                    }
                  }}
                  placeholder="Describe your topic here..."
                  className="w-full p-3 rounded-lg bg-slate-700 border border-indigo-500 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all duration-300 min-h-[100px] resize-none"
                  disabled={isExtendingKnowledge}
                />
                <p className="text-xs text-slate-400 mt-2">
                  Press Enter to submit or Shift+Enter for a new line
                </p>
              </div>
              
              <div className="flex justify-between">
                <button
                  onClick={() => setIsCustomTopicActive(false)}
                  className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition-colors duration-300 text-sm md:text-base"
                  disabled={isExtendingKnowledge}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCustomTopicSubmit}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white transition-colors duration-300 text-sm md:text-base"
                  disabled={!customTopicText.trim() || isExtendingKnowledge}
                >
                  Submit
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Knowledge Extension Message */}
        {isExtendingKnowledge && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/70 z-50 animate-fade-in">
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-6 md:p-8 rounded-xl border border-indigo-500 shadow-lg shadow-indigo-500/20 w-full max-w-md mx-4 text-center">
              <div className="text-4xl mb-4 animate-pulse">🧠</div>
              <h3 className="text-xl md:text-2xl font-semibold text-white mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                Your taalcoach knowledge is being extended. Hold on please!
              </h3>
              <div className="flex justify-center">
                <div className="w-12 h-1 bg-indigo-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
} 