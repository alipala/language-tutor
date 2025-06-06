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

  const handleCustomTopicSubmit = async () => {
    if (!customTopicText.trim()) return;
    
    // Show the extending knowledge message
    setIsExtendingKnowledge(true);
    
    try {
      // Call the research endpoint to perform web search
      console.log('🔍 Starting topic research for:', customTopicText);
      
      const response = await fetch('http://localhost:8000/api/custom-topic/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          language: selectedLanguage || 'english',
          level: 'A1',
          user_prompt: customTopicText,
          topic: 'custom'
        })
      });
      
      if (!response.ok) {
        throw new Error(`Research failed: ${response.status}`);
      }
      
      const researchData = await response.json();
      console.log('✅ Topic research completed:', researchData);
      
      // Store the research results along with the topic
      sessionStorage.setItem('selectedTopic', 'custom');
      sessionStorage.setItem('customTopicText', customTopicText);
      sessionStorage.setItem('customTopicResearch', JSON.stringify(researchData));
      sessionStorage.setItem('intentionalNavigation', 'true');
      
      // Add detailed logging
      console.log('Custom topic submitted with research:', customTopicText);
      console.log('Session storage state:', {
        selectedLanguage: sessionStorage.getItem('selectedLanguage'),
        selectedTopic: 'custom',
        customTopicText: customTopicText,
        researchCompleted: researchData.success,
        intentionalNavigation: true
      });
      
      // Navigate to level selection after research completes
      setTimeout(() => {
        console.log('Executing navigation to level selection with researched custom topic');
        window.location.href = '/level-selection';
      }, 1000);
      
    } catch (error) {
      console.error('❌ Topic research failed:', error);
      
      // Still proceed but without research data
      sessionStorage.setItem('selectedTopic', 'custom');
      sessionStorage.setItem('customTopicText', customTopicText);
      sessionStorage.setItem('intentionalNavigation', 'true');
      
      // Navigate even if research fails
      setTimeout(() => {
        console.log('Executing navigation to level selection (research failed, proceeding anyway)');
        window.location.href = '/level-selection';
      }, 1000);
    }
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
    <div className="min-h-screen text-[#4ECFBF] topic-selection-container">
      <NavBar activeSection="section1" />
      <main className="flex-grow flex flex-col p-4 md:p-8">
        <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-bold text-[#4ECFBF] mb-4 animate-fade-in">
            Choose a Topic
          </h1>
          <p className="text-[#4ECFBF]/80 text-lg mb-8 animate-fade-in" style={{animationDelay: '100ms'}}>
            {selectedLanguage === 'dutch' && 'Selecteer een onderwerp voor je Nederlandse conversatie (optioneel)'}
            {selectedLanguage === 'english' && 'Select a topic for your English conversation (optional)'}
            {selectedLanguage === 'spanish' && 'Selecciona un tema para tu conversación en español (opcional)'}
            {selectedLanguage === 'german' && 'Wähle ein Thema für dein Gespräch auf Deutsch (optional)'}
            {selectedLanguage === 'french' && 'Sélectionnez un sujet pour votre conversation en français (facultatif)'}
            {selectedLanguage === 'portuguese' && 'Selecione um tópico para sua conversa em português (opcional)'}
            {!selectedLanguage && 'Select a topic for your conversation (optional)'}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-10 animate-fade-in max-w-2xl mx-auto" style={{animationDelay: '200ms'}}>
            {/* Change Language Button */}
            <button 
              onClick={handleChangeLanguage}
              className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 w-full sm:w-48 h-14 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:shadow-[#4ECFBF]/20 transform hover:translate-y-[-1px] touch-target" 
            >
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Text */}
              <span className="relative z-10 font-medium text-gray-800 group-hover:text-[#4ECFBF] transition-colors duration-300 text-sm sm:text-base">Change Language</span>
              
              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
            </button>

            {/* Skip Topic Button */}
            <button 
              onClick={handleSkipTopic}
              className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 w-full sm:w-48 h-14 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:shadow-[#4ECFBF]/20 transform hover:translate-y-[-1px] touch-target" 
            >
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Text */}
              <span className="relative z-10 font-medium text-gray-800 group-hover:text-[#4ECFBF] transition-colors duration-300 text-sm sm:text-base">Skip Topic</span>
              
              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
            </button>

            {/* Start Over Button */}
            <button 
              onClick={handleStartOver}
              className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 w-full sm:w-48 h-14 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:shadow-[#4ECFBF]/20 transform hover:translate-y-[-1px] touch-target" 
            >
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Text */}
              <span className="relative z-10 font-medium text-gray-800 group-hover:text-[#4ECFBF] transition-colors duration-300 text-sm sm:text-base">Start Over</span>
              
              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
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
              className={`group relative overflow-hidden rounded-xl transition-all duration-300 bg-white border-2 border-[#4ECFBF] flex flex-col p-6 text-left min-h-44 transform hover:translate-y-[-2px] shadow-lg hover:shadow-[#4ECFBF]/20 ${
                (isLoading || isExtendingKnowledge) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              } ${
                isCustomTopicActive && topic.id === 'custom' ? 'ring-2 ring-[#4ECFBF]/50 shadow-[#4ECFBF]/20' : ''
              }`}
            >
              {/* Glow effect on hover */}
              <div className="absolute inset-0 bg-[#4ECFBF]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Icon */}
              <div className="text-4xl mb-4">{topic.icon}</div>
              
              {/* Title */}
              <h3 className="text-xl font-semibold text-gray-800 mb-2 group-hover:text-[#4ECFBF] transition-colors duration-300">
                {topic.name}
              </h3>
              
              {/* Description */}
              <p className="text-gray-600 text-sm group-hover:text-gray-700 transition-colors duration-300">
                {topic.description}
              </p>
              
              {/* We no longer show the input field inside the topic box */}
            </button>
          ))}
        </div>
        
        {/* Custom Topic Input Modal - Only show when active */}
        {isCustomTopicActive && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50 animate-fade-in">
            <div className="bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 rounded-xl shadow-lg w-full max-w-lg mx-4 p-6 md:p-8 relative overflow-hidden">
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-50"></div>
              
              {/* Header */}
              <div className="relative z-10 text-center mb-6">
                <h3 className="text-2xl md:text-3xl font-bold text-gray-800 mb-3">
                  {selectedLanguage === 'dutch' && 'Maak je eigen onderwerp'}
                  {selectedLanguage === 'english' && 'Create Your Custom Topic'}
                  {selectedLanguage === 'spanish' && 'Crea tu tema personalizado'}
                  {selectedLanguage === 'german' && 'Erstelle dein eigenes Thema'}
                  {selectedLanguage === 'french' && 'Créez votre sujet personnalisé'}
                  {selectedLanguage === 'portuguese' && 'Crie seu tópico personalizado'}
                  {!selectedLanguage && 'Create Your Custom Topic'}
                </h3>
                <p className="text-gray-600 text-sm md:text-base">
                  {selectedLanguage === 'dutch' && 'Waarover wil je praten in je Nederlandse conversatie?'}
                  {selectedLanguage === 'english' && 'What would you like to talk about in your English conversation?'}
                  {selectedLanguage === 'spanish' && '¿De qué te gustaría hablar en tu conversación en español?'}
                  {selectedLanguage === 'german' && 'Worüber möchtest du in deinem Gespräch auf Deutsch sprechen?'}
                  {selectedLanguage === 'french' && 'De quoi aimeriez-vous parler dans votre conversation en français?'}
                  {selectedLanguage === 'portuguese' && 'Sobre o que você gostaria de falar em sua conversa em português?'}
                  {!selectedLanguage && 'What would you like to talk about in your conversation?'}
                </p>
              </div>
              
              {/* Input Section */}
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
                  className="w-full p-4 rounded-xl border-2 border-[#4ECFBF]/30 focus:border-[#4ECFBF]/60 bg-white/80 backdrop-blur-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF]/20 transition-all duration-300 min-h-[120px] resize-none shadow-sm"
                  disabled={isExtendingKnowledge}
                />
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Press Enter to submit or Shift+Enter for a new line
                </p>
              </div>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 relative z-10">
                <button
                  onClick={() => setIsCustomTopicActive(false)}
                  className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-gray-300 hover:border-gray-400 w-full sm:flex-1 h-12 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-md transform hover:translate-y-[-1px] touch-target"
                  disabled={isExtendingKnowledge}
                >
                  <span className="relative z-10 font-medium text-gray-700 group-hover:text-gray-800 transition-colors duration-300">Cancel</span>
                  <div className="absolute bottom-0 left-0 h-0.5 bg-gray-400 w-0 group-hover:w-full transition-all duration-500"></div>
                </button>
                
                <button
                  onClick={handleCustomTopicSubmit}
                  className={`group relative overflow-hidden border-2 w-full sm:flex-1 h-12 rounded-xl flex items-center justify-center transition-all duration-300 transform hover:translate-y-[-1px] touch-target ${
                    customTopicText.trim() && !isExtendingKnowledge
                      ? 'bg-[#4ECFBF] hover:bg-[#4ECFBF]/90 border-[#4ECFBF] hover:shadow-lg hover:shadow-[#4ECFBF]/30'
                      : 'bg-white/95 backdrop-blur-sm border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 hover:shadow-md'
                  }`}
                  disabled={!customTopicText.trim() || isExtendingKnowledge}
                >
                  <span className={`relative z-10 font-medium transition-colors duration-300 ${
                    customTopicText.trim() && !isExtendingKnowledge
                      ? 'text-white'
                      : 'text-[#4ECFBF] group-hover:text-[#4ECFBF]'
                  }`}>Submit</span>
                  <div className={`absolute bottom-0 left-0 h-0.5 w-0 group-hover:w-full transition-all duration-500 ${
                    customTopicText.trim() && !isExtendingKnowledge
                      ? 'bg-white/50'
                      : 'bg-[#4ECFBF]'
                  }`}></div>
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
