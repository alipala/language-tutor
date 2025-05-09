'use client';

import { useState, useEffect, KeyboardEvent, useRef } from 'react';
import { useRouter } from 'next/navigation';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';

interface Topic {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export default function TopicSelection() {
  const router = useRouter();
  const { user } = useAuth();
  const navigation = useNavigation();
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCustomTopicActive, setIsCustomTopicActive] = useState(false);
  const [customTopicText, setCustomTopicText] = useState('');
  const [isExtendingKnowledge, setIsExtendingKnowledge] = useState(false);
  const customInputRef = useRef<HTMLTextAreaElement>(null);

  // Define topics with multilingual descriptions
  const getTopics = (language: string | null): Topic[] => {
    // Default to English if no language is selected
    const lang = language || 'english';
    
    // Base topics structure
    const baseTopics = [
      {
        id: 'travel',
        name: 'Travel',
        icon: '✈️',
        descriptions: {
          english: 'Discuss travel destinations, experiences, and planning trips.',
          dutch: 'Bespreek reisbestemmingen, ervaringen en het plannen van reizen.',
          spanish: 'Habla sobre destinos de viaje, experiencias y planificación de viajes.',
          german: 'Diskutiere über Reiseziele, Erfahrungen und Reiseplanung.',
          french: 'Discutez des destinations de voyage, des expériences et de la planification des voyages.',
          portuguese: 'Converse sobre destinos de viagem, experiências e planejamento de viagens.'
        }
      },
      {
        id: 'food',
        name: 'Food & Cooking',
        icon: '🍲',
        descriptions: {
          english: 'Talk about cuisines, recipes, restaurants, and cooking techniques.',
          dutch: 'Praat over keukens, recepten, restaurants en kooktechnieken.',
          spanish: 'Habla sobre cocinas, recetas, restaurantes y técnicas culinarias.',
          german: 'Sprich über Küchen, Rezepte, Restaurants und Kochtechniken.',
          french: 'Parlez des cuisines, des recettes, des restaurants et des techniques de cuisine.',
          portuguese: 'Fale sobre culinárias, receitas, restaurantes e técnicas de cozinha.'
        }
      },
      {
        id: 'hobbies',
        name: 'Hobbies & Interests',
        icon: '🎨',
        descriptions: {
          english: 'Share your favorite activities, sports, games, or pastimes.',
          dutch: 'Deel je favoriete activiteiten, sporten, spellen of hobbys.',
          spanish: 'Comparte tus actividades, deportes, juegos o pasatiempos favoritos.',
          german: 'Teile deine Lieblingsaktivitäten, Sportarten, Spiele oder Hobbys.',
          french: 'Partagez vos activités, sports, jeux ou passe-temps préférés.',
          portuguese: 'Compartilhe suas atividades, esportes, jogos ou passatempos favoritos.'
        }
      },
      {
        id: 'culture',
        name: 'Culture & Traditions',
        icon: '🏛️',
        descriptions: {
          english: 'Explore cultural aspects, traditions, festivals, and customs.',
          dutch: 'Verken culturele aspecten, tradities, festivals en gebruiken.',
          spanish: 'Explora aspectos culturales, tradiciones, festivales y costumbres.',
          german: 'Erkunde kulturelle Aspekte, Traditionen, Feste und Bräuche.',
          french: 'Explorez les aspects culturels, les traditions, les festivals et les coutumes.',
          portuguese: 'Explore aspectos culturais, tradições, festivais e costumes.'
        }
      },
      {
        id: 'movies',
        name: 'Movies & TV Shows',
        icon: '🎬',
        descriptions: {
          english: 'Discuss films, series, actors, directors, and entertainment.',
          dutch: 'Bespreek films, series, acteurs, regisseurs en entertainment.',
          spanish: 'Habla sobre películas, series, actores, directores y entretenimiento.',
          german: 'Diskutiere über Filme, Serien, Schauspieler, Regisseure und Unterhaltung.',
          french: 'Discutez des films, des séries, des acteurs, des réalisateurs et du divertissement.',
          portuguese: 'Converse sobre filmes, séries, atores, diretores e entretenimento.'
        }
      },
      {
        id: 'music',
        name: 'Music',
        icon: '🎵',
        descriptions: {
          english: 'Talk about music genres, artists, concerts, and preferences.',
          dutch: 'Praat over muziekgenres, artiesten, concerten en voorkeuren.',
          spanish: 'Habla sobre géneros musicales, artistas, conciertos y preferencias.',
          german: 'Sprich über Musikgenres, Künstler, Konzerte und Vorlieben.',
          french: 'Parlez des genres musicaux, des artistes, des concerts et des préférences.',
          portuguese: 'Fale sobre gêneros musicais, artistas, concertos e preferências.'
        }
      },
      {
        id: 'technology',
        name: 'Technology',
        icon: '💻',
        descriptions: {
          english: 'Discuss gadgets, apps, innovations, and digital trends.',
          dutch: 'Bespreek gadgets, apps, innovaties en digitale trends.',
          spanish: 'Habla sobre gadgets, aplicaciones, innovaciones y tendencias digitales.',
          german: 'Diskutiere über Gadgets, Apps, Innovationen und digitale Trends.',
          french: 'Discutez des gadgets, des applications, des innovations et des tendances numériques.',
          portuguese: 'Converse sobre gadgets, aplicativos, inovações e tendências digitais.'
        }
      },
      {
        id: 'environment',
        name: 'Environment & Nature',
        icon: '🌳',
        descriptions: {
          english: 'Explore environmental issues, sustainability, and the natural world.',
          dutch: 'Verken milieukwesties, duurzaamheid en de natuurlijke wereld.',
          spanish: 'Explora temas ambientales, sostenibilidad y el mundo natural.',
          german: 'Erkunde Umweltthemen, Nachhaltigkeit und die natürliche Welt.',
          french: 'Explorez les questions environnementales, la durabilité et le monde naturel.',
          portuguese: 'Explore questões ambientais, sustentabilidade e o mundo natural.'
        }
      },
      {
        id: 'custom',
        name: 'Custom Topic',
        icon: '🔍',
        descriptions: {
          english: 'Create your own topic for a personalized conversation experience.',
          dutch: 'Maak je eigen onderwerp voor een gepersonaliseerde gespreks-ervaring.',
          spanish: 'Crea tu propio tema para una experiencia de conversación personalizada.',
          german: 'Erstelle dein eigenes Thema für ein personalisiertes Gesprächserlebnis.',
          french: 'Créez votre propre sujet pour une expérience de conversation personnalisée.',
          portuguese: 'Crie seu próprio tópico para uma experiência de conversa personalizada.'
        }
      }
    ];
    
    // Map to the expected Topic format with the correct language description
    return baseTopics.map(topic => ({
      id: topic.id,
      name: topic.name,
      description: topic.descriptions[lang as keyof typeof topic.descriptions] || topic.descriptions.english,
      icon: topic.icon
    }));
  };
  
  // Get topics based on selected language
  const topics = getTopics(selectedLanguage);

  // Add a useEffect to handle page initialization and react to state changes
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;
    
    console.log('Topic selection page loaded at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // IMPORTANT: Disable all automatic redirects to fix back button navigation
    // We'll only redirect if there's no language selected
    
    // Set up a listener for the popstate event (browser back button)
    const handlePopState = (event: PopStateEvent) => {
      console.log('Detected browser back button navigation to language selection');
      // Set a flag to indicate we're navigating with back button
      sessionStorage.setItem('backButtonNavigation', 'true');
    };
    
    // Add the event listener
    window.addEventListener('popstate', handlePopState);
    
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
    setIsLoading(false);
    
    // Clear any navigation flags that might cause issues
    sessionStorage.removeItem('intentionalNavigation');
    sessionStorage.removeItem('backButtonNavigation');
    sessionStorage.removeItem('popStateToTopicSelection');
    sessionStorage.removeItem('intentionalTopicChange');
    
    // Clean up the event listener when the component unmounts
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const handleStartOver = () => {
    // Clear all session storage
    sessionStorage.clear();
    // Navigate to home page
    console.log('Starting over - cleared session storage');
    navigation.navigateToHome();
  };

  const handleChangeLanguage = () => {
    // Go back to language selection
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    
    // Set a flag to indicate we're intentionally going to language selection
    sessionStorage.setItem('fromTopicSelection', 'true');
    
    // Navigate to language selection
    console.log('Navigating to language selection from topic selection');
    navigation.navigateToLanguageSelection();
  };

  const handleSkipTopic = () => {
    // Skip topic selection (no topic)
    sessionStorage.removeItem('selectedTopic');
    // Navigate to level selection
    navigation.navigateToLevelSelection();
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
    
    // Use direct navigation for reliability in this critical path
    // This ensures we actually navigate to the next page
    window.location.href = '/level-selection';
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
      // Use direct navigation for reliability in this critical path
      window.location.href = '/level-selection';
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
    <div className="min-h-screen flex flex-col text-white">
      <NavBar />
      <main className="flex-grow flex flex-col p-4 md:p-8">
        <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-bold text-white mb-4 animate-fade-in">
            Choose a Topic
          </h1>
          <p className="text-white/80 text-lg mb-8 animate-fade-in" style={{animationDelay: '100ms'}}>
            {selectedLanguage === 'dutch' && 'Selecteer een onderwerp voor je Nederlandse conversatie (optioneel)'}
            {selectedLanguage === 'english' && 'Select a topic for your English conversation (optional)'}
            {selectedLanguage === 'spanish' && 'Selecciona un tema para tu conversación en español (opcional)'}
            {selectedLanguage === 'german' && 'Wähle ein Thema für dein Gespräch auf Deutsch (optional)'}
            {selectedLanguage === 'french' && 'Sélectionnez un sujet pour votre conversation en français (facultatif)'}
            {selectedLanguage === 'portuguese' && 'Selecione um tópico para sua conversa em português (opcional)'}
            {!selectedLanguage && 'Select a topic for your conversation (optional)'}
          </p>
          <div className="flex space-x-4 justify-center mb-10 animate-fade-in" style={{animationDelay: '200ms'}}>
            <button 
              onClick={handleChangeLanguage}
              className="primary-button px-4 py-2 rounded-lg flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              <span>Change Language</span>
            </button>
            <button 
              onClick={handleSkipTopic}
              className="primary-button px-4 py-2 rounded-lg flex items-center space-x-2" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Skip Topic</span>
            </button>
            <button 
              onClick={handleStartOver}
              className="primary-button px-4 py-2 rounded-lg flex items-center space-x-2" 
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
              className={`group relative overflow-hidden rounded-xl transition-all duration-300 glass-card flex flex-col p-6 text-left min-h-44 transform hover:translate-y-[-2px] ${
                (isLoading || isExtendingKnowledge) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              } ${
                isCustomTopicActive && topic.id === 'custom' ? 'ring-2 ring-white/50 shadow-white/20' : ''
              }`}
            >
              {/* Glow effect on hover */}
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Icon */}
              <div className="text-4xl mb-4">{topic.icon}</div>
              
              {/* Title */}
              <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-white transition-colors duration-300">
                {topic.name}
              </h3>
              
              {/* Description */}
              <p className="text-white/70 text-sm group-hover:text-white transition-colors duration-300">
                {topic.description}
              </p>
              
              {/* We no longer show the input field inside the topic box */}
            </button>
          ))}
        </div>
        
        {/* Custom Topic Input Modal - Only show when active */}
        {isCustomTopicActive && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/70 z-50 animate-fade-in">
            <div className="glass-card p-6 md:p-8 rounded-xl border border-white/20 shadow-lg w-full max-w-md mx-4">
              {/* Decorative elements */}
              <div className="absolute -top-20 -right-20 w-60 h-60 bg-white/5 rounded-full blur-3xl"></div>
              <div className="absolute -bottom-20 -left-20 w-60 h-60 bg-white/5 rounded-full blur-3xl"></div>
              
              <h3 className="text-xl md:text-2xl font-bold text-white mb-4 relative z-10">
                {selectedLanguage === 'dutch' && 'Maak je eigen onderwerp'}
                {selectedLanguage === 'english' && 'Create Your Custom Topic'}
                {selectedLanguage === 'spanish' && 'Crea tu tema personalizado'}
                {selectedLanguage === 'german' && 'Erstelle dein eigenes Thema'}
                {selectedLanguage === 'french' && 'Créez votre sujet personnalisé'}
                {selectedLanguage === 'portuguese' && 'Crie seu tópico personalizado'}
                {!selectedLanguage && 'Create Your Custom Topic'}
              </h3>
              <p className="text-white/80 text-sm md:text-base mb-6 relative z-10">
                {selectedLanguage === 'dutch' && 'Waarover wil je praten in je Nederlandse conversatie?'}
                {selectedLanguage === 'english' && 'What would you like to talk about in your English conversation?'}
                {selectedLanguage === 'spanish' && '¿De qué te gustaría hablar en tu conversación en español?'}
                {selectedLanguage === 'german' && 'Worüber möchtest du in deinem Gespräch auf Deutsch sprechen?'}
                {selectedLanguage === 'french' && 'De quoi aimeriez-vous parler dans votre conversation en français?'}
                {selectedLanguage === 'portuguese' && 'Sobre o que você gostaria de falar em sua conversa em português?'}
                {!selectedLanguage && 'What would you like to talk about in your conversation?'}
              </p>
              
              <div className="mb-6 relative z-10">
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
                  className="w-full p-3 rounded-lg glass-card border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30 transition-all duration-300 min-h-[100px] resize-none"
                  disabled={isExtendingKnowledge}
                />
                <p className="text-xs text-white/60 mt-2">
                  Press Enter to submit or Shift+Enter for a new line
                </p>
              </div>
              
              <div className="flex justify-between relative z-10">
                <button
                  onClick={() => setIsCustomTopicActive(false)}
                  className="px-4 py-2 rounded-lg glass-card border border-white/20 hover:bg-white/10 text-white transition-all duration-300 text-sm md:text-base shadow-lg hover:shadow-white/10 transform hover:translate-y-[-1px]"
                  disabled={isExtendingKnowledge}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCustomTopicSubmit}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white transition-all duration-300 text-sm md:text-base shadow-lg shadow-purple-500/20 hover:shadow-purple-500/30 transform hover:translate-y-[-1px]"
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
            <div className="glass-card p-6 md:p-8 rounded-xl border border-white/20 shadow-lg w-full max-w-md mx-4 text-center">
              <div className="text-4xl mb-4 animate-pulse">🧠</div>
              <h3 className="text-xl md:text-2xl font-bold text-white mb-4">
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
    </div>
  );
} 