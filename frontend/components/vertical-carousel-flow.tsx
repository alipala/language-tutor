'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useNavigation } from '@/lib/navigation';
import { useAuth } from '@/lib/auth';
import LanguageOptionsModal from '@/components/language-options-modal';
import LoadingModal from '@/components/loading-modal';
import NavBar from '@/components/nav-bar';

// Types
interface Language {
  code: string;
  name: string;
  description?: string;
  flagComponent: React.ReactNode;
}

interface Topic {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface Level {
  code: string;
  name: string;
  description: string;
}

// Flow steps enum
enum FlowStep {
  LANGUAGE = 0,
  CHOICE = 1,
  TOPIC = 2,
  LEVEL = 3
}

export default function VerticalCarouselFlow() {
  const router = useRouter();
  const navigation = useNavigation();
  const { user } = useAuth();
  const searchParams = useSearchParams();
  
  // State management
  const [currentStep, setCurrentStep] = useState<FlowStep>(FlowStep.LANGUAGE);
  const [skipChoiceStep, setSkipChoiceStep] = useState(false);
  const [preselectedMode, setPreselectedMode] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<FlowStep>>(new Set());
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCustomTopicActive, setIsCustomTopicActive] = useState(false);
  const [customTopicText, setCustomTopicText] = useState('');
  const [isExtendingKnowledge, setIsExtendingKnowledge] = useState(false);
  
  // Refs for smooth scrolling
  const containerRef = useRef<HTMLDivElement>(null);
  const customInputRef = useRef<HTMLTextAreaElement>(null);

  // Handle mode parameter on component mount
  useEffect(() => {
    const mode = searchParams.get('mode');
    if (mode === 'assessment' || mode === 'practice') {
      setSkipChoiceStep(true);
      setPreselectedMode(mode);
    }
  }, [searchParams]);

  // Helper function to check if a step is available
  const isStepAvailable = (step: FlowStep): boolean => {
    if (step === FlowStep.LANGUAGE) return true;
    
    if (skipChoiceStep) {
      // When skipping choice step, adjust step requirements
      if (step === FlowStep.TOPIC) return selectedLanguage !== null;
      if (step === FlowStep.LEVEL) return selectedLanguage !== null && selectedTopic !== null;
    } else {
      // Normal flow
      if (step === FlowStep.CHOICE) return selectedLanguage !== null;
      if (step === FlowStep.TOPIC) return selectedLanguage !== null && completedSteps.has(FlowStep.CHOICE);
      if (step === FlowStep.LEVEL) return selectedLanguage !== null && selectedTopic !== null;
    }
    
    return false;
  };

  // Helper function to mark step as completed
  const markStepCompleted = (step: FlowStep) => {
    setCompletedSteps(prev => new Set([...Array.from(prev), step]));
  };

  // Flag components
  const FlagComponents: Record<string, React.ReactNode> = {
    dutch: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full">
        <rect fill="#21468B" width="3" height="2" />
        <rect fill="#FFF" width="3" height="1.33" />
        <rect fill="#AE1C28" width="3" height="0.67" />
      </svg>
    ),
    english: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full">
        <rect width="3" height="2" fill="#012169" />
        <path d="M0,0 L3,2 M3,0 L0,2" stroke="#fff" strokeWidth="0.3" />
        <path d="M1.5,0 v2 M0,1 h3" stroke="#fff" strokeWidth="0.5" />
        <path d="M1.5,0 v2 M0,1 h3" stroke="#C8102E" strokeWidth="0.3" />
      </svg>
    ),
    spanish: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full">
        <rect width="3" height="2" fill="#c60b1e" />
        <rect width="3" height="1" fill="#ffc400" y="0.5" />
      </svg>
    ),
    german: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full">
        <rect width="3" height="2" fill="#000" />
        <rect width="3" height="1.33" fill="#D00" />
        <rect width="3" height="0.67" fill="#FFCE00" />
      </svg>
    ),
    french: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full">
        <rect width="1" height="2" fill="#002395" />
        <rect width="1" height="2" fill="#FFFFFF" x="1" />
        <rect width="1" height="2" fill="#ED2939" x="2" />
      </svg>
    ),
    portuguese: (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2" className="w-full h-full">
        <rect width="3" height="2" fill="#006600" />
        <rect width="1.2" height="2" fill="#FF0000" />
        <circle cx="1.2" cy="1" r="0.3" fill="#FFFF00" stroke="#000000" strokeWidth="0.03" />
      </svg>
    ),
  };

  // Languages data
  const languages: Language[] = [
    { code: 'dutch', name: 'Dutch', flagComponent: FlagComponents.dutch },
    { code: 'english', name: 'English', flagComponent: FlagComponents.english },
    { code: 'spanish', name: 'Spanish', flagComponent: FlagComponents.spanish },
    { code: 'german', name: 'German', flagComponent: FlagComponents.german },
    { code: 'french', name: 'French', flagComponent: FlagComponents.french },
    { code: 'portuguese', name: 'Portuguese', flagComponent: FlagComponents.portuguese },
  ];

  // Topics data
  const getTopics = (language: string | null): Topic[] => {
    const lang = language || 'english';
    
    const baseTopics = [
      {
        id: 'travel', name: 'Travel', icon: '✈️',
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
        id: 'food', name: 'Food & Cooking', icon: '🍲',
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
        id: 'hobbies', name: 'Hobbies & Interests', icon: '🎨',
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
        id: 'culture', name: 'Culture & Traditions', icon: '🏛️',
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
        id: 'movies', name: 'Movies & TV Shows', icon: '🎬',
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
        id: 'music', name: 'Music', icon: '🎵',
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
        id: 'technology', name: 'Technology', icon: '💻',
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
        id: 'environment', name: 'Environment & Nature', icon: '🌳',
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
        id: 'custom', name: 'Custom Topic', icon: '🔍',
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
    
    return baseTopics.map(topic => ({
      id: topic.id,
      name: topic.name,
      description: topic.descriptions[lang as keyof typeof topic.descriptions] || topic.descriptions.english,
      icon: topic.icon
    }));
  };

  // Levels data
  const getLevels = (language: string | null): Level[] => {
    const lang = language || 'english';
    
    const levelDescriptions = {
      'A1': {
        english: 'Basic vocabulary and simple phrases for everyday situations.',
        dutch: 'Basiswoordenschat en eenvoudige zinnen voor alledaagse situaties.',
        spanish: 'Vocabulario básico y frases simples para situaciones cotidianas.',
        german: 'Grundwortschatz und einfache Sätze für Alltagssituationen.',
        french: 'Vocabulaire de base et phrases simples pour les situations quotidiennes.',
        portuguese: 'Vocabulário básico e frases simples para situações cotidianas.'
      },
      'A2': {
        english: 'Communicate in simple and routine tasks on familiar topics.',
        dutch: 'Communiceren in eenvoudige en routinematige taken over bekende onderwerpen.',
        spanish: 'Comunicarse en tareas simples y rutinarias sobre temas familiares.',
        german: 'Kommunikation in einfachen und routinemäßigen Aufgaben zu vertrauten Themen.',
        french: 'Communiquer lors de tâches simples et habituelles sur des sujets familiers.',
        portuguese: 'Comunicar em tarefas simples e rotineiras sobre tópicos familiares.'
      },
      'B1': {
        english: 'Deal with most situations likely to arise while traveling.',
        dutch: 'Omgaan met de meeste situaties die zich kunnen voordoen tijdens het reizen.',
        spanish: 'Enfrentar la mayoría de las situaciones que pueden surgir durante un viaje.',
        german: 'Mit den meisten Situationen umgehen, die während des Reisens auftreten können.',
        french: 'Faire face à la plupart des situations susceptibles de se produire en voyage.',
        portuguese: 'Lidar com a maioria das situações que podem surgir durante uma viagem.'
      },
      'B2': {
        english: 'Interact with a degree of fluency that makes regular interaction possible.',
        dutch: 'Communiceren met een mate van vloeiendheid die regelmatige interactie mogelijk maakt.',
        spanish: 'Interactuar con un grado de fluidez que hace posible la interacción regular.',
        german: 'Mit einem Grad an Flüssigkeit interagieren, der regelmäßige Interaktion ermöglicht.',
        french: 'Interagir avec un degré de fluidité qui rend possible une interaction régulière.',
        portuguese: 'Interagir com um grau de fluência que torna possível a interação regular.'
      },
      'C1': {
        english: 'Express ideas fluently and spontaneously without much searching for expressions.',
        dutch: 'Ideeën vloeiend en spontaan uitdrukken zonder veel te zoeken naar uitdrukkingen.',
        spanish: 'Expresar ideas con fluidez y espontaneidad sin tener que buscar expresiones.',
        german: 'Ideen fließend und spontan ausdrücken, ohne viel nach Ausdrücken suchen zu müssen.',
        french: 'Exprimer des idées avec fluidité et spontanéité sans trop chercher ses mots.',
        portuguese: 'Expressar ideias com fluência e espontaneidade sem precisar procurar expressões.'
      },
      'C2': {
        english: 'Express yourself spontaneously, very fluently and precisely in complex situations.',
        dutch: 'Jezelf spontaan, zeer vloeiend en nauwkeurig uitdrukken in complexe situaties.',
        spanish: 'Expresarte de forma espontánea, muy fluida y precisa en situaciones complejas.',
        german: 'Dich spontan, sehr fließend und präzise in komplexen Situationen ausdrücken.',
        french: 'Vous exprimer spontanément, très couramment et avec précision dans des situations complexes.',
        portuguese: 'Expressar-se espontaneamente, com muita fluência e precisão em situações complexas.'
      }
    };
    
    return Object.entries(levelDescriptions).map(([code, descriptions]) => ({
      code,
      name: code,
      description: descriptions[lang as keyof typeof descriptions] || descriptions.english
    }));
  };

  // Smooth transition between steps
  const transitionToNextStep = () => {
    if (containerRef.current) {
      const nextStepIndex = currentStep + 1;
      const stepHeight = containerRef.current.clientHeight;
      
      containerRef.current.scrollTo({
        top: nextStepIndex * stepHeight,
        behavior: 'smooth'
      });
      
      setTimeout(() => {
        setCurrentStep(nextStepIndex);
      }, 300);
    }
  };

  // Handle language selection
  const handleLanguageSelect = (languageCode: string) => {
    setSelectedLanguage(languageCode);
    navigation.setSelectedLanguage(languageCode);
    markStepCompleted(FlowStep.LANGUAGE);
    
    setTimeout(() => {
      if (skipChoiceStep && preselectedMode) {
        // Skip the choice step and go directly to the appropriate flow
        if (preselectedMode === 'assessment') {
          setIsLoading(true);
          window.location.href = '/assessment/speaking';
        } else if (preselectedMode === 'practice') {
          // Skip directly to topic selection since choice step is hidden
          transitionToNextStep(); // This will go to topic selection since choice step is conditionally hidden
        }
      } else {
        // Normal flow - go to choice step
        transitionToNextStep();
      }
    }, 300);
  };

  // Handle modal option selection
  const handleModalOptionSelect = (option: string) => {
    setIsModalOpen(false);
    
    if (option === 'assessment') {
      setIsLoading(true);
      window.location.href = '/assessment/speaking';
    } else if (option === 'practice') {
      setTimeout(() => {
        transitionToNextStep();
      }, 300);
    }
  };

  // Handle topic selection
  const handleTopicSelect = (topicId: string) => {
    if (topicId === 'custom') {
      setIsCustomTopicActive(true);
      setTimeout(() => {
        if (customInputRef.current) {
          customInputRef.current.focus();
        }
      }, 100);
      return;
    }
    
    setSelectedTopic(topicId);
    sessionStorage.setItem('selectedTopic', topicId);
    
    setTimeout(() => {
      transitionToNextStep();
    }, 300);
  };

  // Handle custom topic submission
  const handleCustomTopicSubmit = async () => {
    if (!customTopicText.trim()) return;
    
    setIsExtendingKnowledge(true);
    
    try {
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
      
      if (response.ok) {
        const researchData = await response.json();
        sessionStorage.setItem('customTopicResearch', JSON.stringify(researchData));
      }
      
      sessionStorage.setItem('selectedTopic', 'custom');
      sessionStorage.setItem('customTopicText', customTopicText);
      setSelectedTopic('custom');
      setIsCustomTopicActive(false);
      
      setTimeout(() => {
        setIsExtendingKnowledge(false);
        transitionToNextStep();
      }, 1000);
      
    } catch (error) {
      console.error('Topic research failed:', error);
      sessionStorage.setItem('selectedTopic', 'custom');
      sessionStorage.setItem('customTopicText', customTopicText);
      setSelectedTopic('custom');
      setIsCustomTopicActive(false);
      
      setTimeout(() => {
        setIsExtendingKnowledge(false);
        transitionToNextStep();
      }, 1000);
    }
  };

  // Handle level selection
  const handleLevelSelect = (level: string) => {
    setSelectedLevel(level);
    sessionStorage.setItem('selectedLevel', level);
    
    setIsLoading(true);
    setTimeout(() => {
      window.location.href = '/speech';
    }, 500);
  };

  // Get current step data
  const topics = getTopics(selectedLanguage);
  const levels = getLevels(selectedLanguage);

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
      {/* Vertical Carousel Container */}
      <div 
        ref={containerRef}
        className="h-full overflow-y-auto snap-y snap-mandatory scroll-smooth"
        style={{ scrollSnapType: 'y mandatory' }}
      >
        {/* Step 1: Language Selection */}
        <div className="min-h-screen snap-start flex flex-col justify-center items-center p-8">
          <div className="w-full max-w-4xl mx-auto">
            <div className="text-center mb-12 animate-fade-in">
              <h1 className="text-5xl font-bold tracking-tight text-gray-800 mb-4">
                Choose Your Language
              </h1>
              <p className="text-lg text-gray-600">Select a language to begin your journey</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {languages.map((language, index) => (
                <button
                  key={language.code}
                  onClick={() => handleLanguageSelect(language.code)}
                  className={`
                    group relative overflow-hidden rounded-xl 
                    transition-all duration-500 ease-out 
                    bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40
                    hover:shadow-lg hover:shadow-[#4ECFBF]/20 hover:scale-105 hover:-translate-y-2
                    animate-slide-up
                    ${
                      selectedLanguage === language.code
                        ? 'ring-2 ring-[#4ECFBF]/50 shadow-[#4ECFBF]/30 shadow-md border-[#4ECFBF]/60'
                        : 'hover:border-[#4ECFBF]/60'
                    }
                  `}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="relative z-10 p-6">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-20 h-14 flex items-center justify-center rounded-lg bg-gradient-to-br from-black/5 to-black/20 backdrop-blur-sm shadow-lg border border-white/30 overflow-hidden relative">
                        <div className="relative w-full h-full overflow-hidden rounded-lg transition-all duration-300 transform group-hover:scale-105">
                          <div className="w-full h-full relative">
                            {language.flagComponent}
                          </div>
                          <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-black/10 pointer-events-none"></div>
                        </div>
                      </div>
                      
                      <div className="flex-1 text-left">
                        <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-[#4ECFBF] transition-colors duration-300">
                          {language.name}
                        </h3>
                        <p className="text-gray-600 text-sm group-hover:text-gray-700 transition-colors duration-300">
                          Start your {language.name.toLowerCase()} learning journey
                        </p>
                      </div>
                      
                      {selectedLanguage === language.code && (
                        <div className="absolute top-4 right-4">
                          <div className="w-7 h-7 rounded-full bg-[#4ECFBF] flex items-center justify-center shadow-md">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-4 h-4">
                              <path fillRule="evenodd" d="M19.916 4.626a.75.75 0 01.208 1.04l-9 13.5a.75.75 0 01-1.154.114l-6-6a.75.75 0 011.06-1.06l5.353 5.353 8.493-12.739a.75.75 0 011.04-.208z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className={`absolute bottom-0 left-0 h-0.5 bg-[#4ECFBF] transition-all duration-700 ease-out opacity-80 ${selectedLanguage === language.code ? 'w-full' : 'w-0 group-hover:w-full'}`}></div>
                  <div className="absolute inset-0 bg-gradient-to-tr from-purple-500/5 via-transparent to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Step 2: Assessment or Practice Choice - Only show if no mode is preselected */}
        {!skipChoiceStep && (
        <div className="min-h-screen snap-start flex flex-col justify-center items-center p-8">
          <div className="w-full max-w-4xl mx-auto">
            <div className="text-center mb-12 animate-fade-in">
              <h1 className="text-5xl font-bold tracking-tight text-gray-800 mb-4">
                {selectedLanguage && (
                  <span className="text-[#4ECFBF] capitalize">{selectedLanguage}</span>
                )} Selected
              </h1>
              <p className="text-lg text-gray-600">Choose how you want to start your language journey</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
              {/* Assessment Option */}
              <button
                onClick={() => {
                  setIsLoading(true);
                  window.location.href = '/assessment/speaking';
                }}
                className="group relative overflow-hidden rounded-xl transition-all duration-500 ease-out bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:shadow-lg hover:shadow-[#4ECFBF]/20 hover:scale-105 hover:-translate-y-2 animate-slide-up p-8 text-left min-h-[280px]"
                style={{ animationDelay: '100ms' }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                <div className="relative z-10">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6 shadow-lg">
                    <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                    </svg>
                  </div>
                  
                  <h3 className="text-2xl font-bold text-gray-800 mb-4 group-hover:text-[#4ECFBF] transition-colors duration-300">
                    Assess my speaking level
                  </h3>
                  
                  <p className="text-gray-600 text-base group-hover:text-gray-700 transition-colors duration-300 mb-6">
                    Take a quick assessment to determine your current language proficiency level.
                  </p>
                  
                  <div className="flex items-center text-sm text-[#4ECFBF] font-medium">
                    <span>10M+ learners</span>
                    <div className="ml-2 flex">
                      {[...Array(5)].map((_, i) => (
                        <svg key={i} className="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-purple-600 w-0 group-hover:w-full transition-all duration-700"></div>
              </button>

              {/* Practice Option */}
              <button
                onClick={() => {
                  setTimeout(() => {
                    transitionToNextStep();
                  }, 300);
                }}
                className="group relative overflow-hidden rounded-xl transition-all duration-500 ease-out bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 hover:shadow-lg hover:shadow-[#4ECFBF]/20 hover:scale-105 hover:-translate-y-2 animate-slide-up p-8 text-left min-h-[280px]"
                style={{ animationDelay: '200ms' }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-transparent to-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                <div className="relative z-10">
                  <div className="w-16 h-16 bg-gradient-to-br from-[#4ECFBF] to-green-500 rounded-full flex items-center justify-center mb-6 shadow-lg">
                    <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  
                  <h3 className="text-2xl font-bold text-gray-800 mb-4 group-hover:text-[#4ECFBF] transition-colors duration-300">
                    Do a Practice
                  </h3>
                  
                  <p className="text-gray-600 text-base group-hover:text-gray-700 transition-colors duration-300 mb-6">
                    Start a conversation practice session on topics of your choice.
                  </p>
                  
                  <div className="flex items-center text-sm text-[#4ECFBF] font-medium">
                    <span>2M+ learners</span>
                    <div className="ml-2 flex">
                      {[...Array(5)].map((_, i) => (
                        <svg key={i} className="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-[#4ECFBF] to-green-500 w-0 group-hover:w-full transition-all duration-700"></div>
              </button>
            </div>
          </div>
        </div>
        )}

        {/* Step 3: Topic Selection */}
        <div className="min-h-screen snap-start flex flex-col justify-center items-center p-8">
          <div className="w-full max-w-4xl mx-auto">
            <div className="text-center mb-12 animate-fade-in">
              <h1 className="text-5xl font-bold tracking-tight text-gray-800 mb-4">
                Choose a Topic
              </h1>
              <p className="text-lg text-gray-600">What would you like to talk about? (Optional)</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {topics.map((topic, index) => (
                <button
                  key={topic.id}
                  onClick={() => handleTopicSelect(topic.id)}
                  disabled={isLoading || isExtendingKnowledge}
                  className={`
                    group relative overflow-hidden rounded-xl transition-all duration-300 
                    bg-white border-2 border-[#4ECFBF] flex flex-col p-6 text-left min-h-44 
                    transform hover:translate-y-[-2px] shadow-lg hover:shadow-[#4ECFBF]/20
                    animate-slide-up
                    ${(isLoading || isExtendingKnowledge) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:scale-105'}
                    ${isCustomTopicActive && topic.id === 'custom' ? 'ring-2 ring-[#4ECFBF]/50 shadow-[#4ECFBF]/20' : ''}
                  `}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="absolute inset-0 bg-[#4ECFBF]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  
                  <div className="text-4xl mb-4">{topic.icon}</div>
                  
                  <h3 className="text-xl font-semibold text-gray-800 mb-2 group-hover:text-[#4ECFBF] transition-colors duration-300">
                    {topic.name}
                  </h3>
                  
                  <p className="text-gray-600 text-sm group-hover:text-gray-700 transition-colors duration-300">
                    {topic.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Step 4: Level Selection */}
        <div className="min-h-screen snap-start flex flex-col justify-center items-center p-8">
          <div className="w-full max-w-4xl mx-auto">
            <div className="text-center mb-12 animate-fade-in">
              <h1 className="text-5xl font-bold tracking-tight text-gray-800 mb-4">
                Select Your Level
              </h1>
              <p className="text-lg text-gray-600">Choose your proficiency level</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {levels.map((level, index) => {
                const getLevelColors = (code: string) => {
                  if (code.startsWith('A')) return {
                    bg: 'from-green-500 to-emerald-600',
                    badge: 'bg-gradient-to-br from-green-400 to-emerald-500 via-green-500',
                    badgeShadow: 'shadow-green-500/30'
                  };
                  if (code.startsWith('B')) return {
                    bg: 'from-blue-500 to-indigo-600',
                    badge: 'bg-gradient-to-br from-blue-400 to-indigo-500 via-blue-500',
                    badgeShadow: 'shadow-blue-500/30'
                  };
                  return {
                    bg: 'from-purple-500 to-violet-600',
                    badge: 'bg-gradient-to-br from-purple-400 to-violet-500 via-purple-500',
                    badgeShadow: 'shadow-purple-500/30'
                  };
                };
                
                const colors = getLevelColors(level.code);
                
                return (
                  <button
                    key={level.code}
                    onClick={() => handleLevelSelect(level.code)}
                    className={`
                      relative overflow-hidden flex flex-col items-start p-6 rounded-xl text-left
                      transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:-translate-y-2
                      bg-white h-[220px] border-2 border-[#4ECFBF] hover:border-[#4ECFBF]/80 
                      shadow-lg hover:shadow-[#4ECFBF]/20 animate-slide-up
                      ${selectedLevel === level.code ? 'border-[#4ECFBF] shadow-xl shadow-[#4ECFBF]/20 ring-2 ring-[#4ECFBF]/50' : ''}
                    `}
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className={`absolute -top-3 -right-3 w-16 h-16 flex items-center justify-center overflow-hidden`}>
                      <div className={`absolute transform rotate-45 w-24 h-8 ${colors.badge} top-2 right-[-6px] shadow-lg ${colors.badgeShadow}`}>
                        <div className="absolute inset-0 opacity-20 animate-pulse"></div>
                      </div>
                      <span className="relative text-white font-bold text-xs">{level.code}</span>
                    </div>
                    
                    <h2 className="text-xl font-bold mb-3 text-gray-800">
                      {selectedLanguage === 'dutch' && (
                        level.code === 'A1' ? 'Absolute Beginner' : 
                        level.code === 'A2' ? 'Basis Beginner' :
                        level.code === 'B1' ? 'Laag Gemiddeld' :
                        level.code === 'B2' ? 'Hoog Gemiddeld' :
                        level.code === 'C1' ? 'Gevorderd' : 'Zeer Gevorderd'
                      )}
                      {selectedLanguage === 'english' && (
                        level.code === 'A1' ? 'Beginner' : 
                        level.code === 'A2' ? 'Elementary' :
                        level.code === 'B1' ? 'Intermediate' :
                        level.code === 'B2' ? 'Upper Intermediate' :
                        level.code === 'C1' ? 'Advanced' : 'Proficient'
                      )}
                      {selectedLanguage === 'spanish' && (
                        level.code === 'A1' ? 'Principiante' : 
                        level.code === 'A2' ? 'Elemental' :
                        level.code === 'B1' ? 'Intermedio' :
                        level.code === 'B2' ? 'Intermedio Alto' :
                        level.code === 'C1' ? 'Avanzado' : 'Dominio'
                      )}
                      {selectedLanguage === 'german' && (
                        level.code === 'A1' ? 'Anfänger' : 
                        level.code === 'A2' ? 'Grundstufe' :
                        level.code === 'B1' ? 'Mittelstufe' :
                        level.code === 'B2' ? 'Fortgeschrittene Mittelstufe' :
                        level.code === 'C1' ? 'Fortgeschritten' : 'Kompetente Sprachverwendung'
                      )}
                      {selectedLanguage === 'french' && (
                        level.code === 'A1' ? 'Débutant' : 
                        level.code === 'A2' ? 'Élémentaire' :
                        level.code === 'B1' ? 'Intermédiaire' :
                        level.code === 'B2' ? 'Intermédiaire Avancé' :
                        level.code === 'C1' ? 'Avancé' : 'Maîtrise'
                      )}
                      {selectedLanguage === 'portuguese' && (
                        level.code === 'A1' ? 'Iniciante' : 
                        level.code === 'A2' ? 'Básico' :
                        level.code === 'B1' ? 'Intermediário' :
                        level.code === 'B2' ? 'Intermediário Superior' :
                        level.code === 'C1' ? 'Avançado' : 'Proficiente'
                      )}
                      {!selectedLanguage && (
                        level.code === 'A1' ? 'Beginner' : 
                        level.code === 'A2' ? 'Elementary' :
                        level.code === 'B1' ? 'Intermediate' :
                        level.code === 'B2' ? 'Upper Intermediate' :
                        level.code === 'C1' ? 'Advanced' : 'Proficient'
                      )}
                    </h2>
                    
                    <p className="text-sm text-gray-600 mb-4">
                      {level.description}
                    </p>
                    
                    <div className="flex flex-wrap gap-2 mt-auto">
                      {level.code.startsWith('A') && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-green-500/20 to-green-600/20 border border-green-500/30 text-green-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Basiswoordenschat'}
                          {selectedLanguage === 'english' && 'Basic Vocabulary'}
                          {selectedLanguage === 'spanish' && 'Vocabulario Básico'}
                          {selectedLanguage === 'german' && 'Grundwortschatz'}
                          {selectedLanguage === 'french' && 'Vocabulaire de Base'}
                          {selectedLanguage === 'portuguese' && 'Vocabulário Básico'}
                          {!selectedLanguage && 'Basic Vocabulary'}
                        </span>
                      )}
                      {(level.code === 'A2' || level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-blue-500/20 to-blue-600/20 border border-blue-500/30 text-blue-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Conversatie'}
                          {selectedLanguage === 'english' && 'Conversation'}
                          {selectedLanguage === 'spanish' && 'Conversación'}
                          {selectedLanguage === 'german' && 'Konversation'}
                          {selectedLanguage === 'french' && 'Conversation'}
                          {selectedLanguage === 'portuguese' && 'Conversação'}
                          {!selectedLanguage && 'Conversation'}
                        </span>
                      )}
                      {(level.code.startsWith('B') || level.code.startsWith('C')) && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-indigo-500/20 to-indigo-600/20 border border-indigo-500/30 text-indigo-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Complexe Onderwerpen'}
                          {selectedLanguage === 'english' && 'Complex Topics'}
                          {selectedLanguage === 'spanish' && 'Temas Complejos'}
                          {selectedLanguage === 'german' && 'Komplexe Themen'}
                          {selectedLanguage === 'french' && 'Sujets Complexes'}
                          {selectedLanguage === 'portuguese' && 'Tópicos Complexos'}
                          {!selectedLanguage && 'Complex Topics'}
                        </span>
                      )}
                      {level.code.startsWith('C') && (
                        <span className="text-xs px-3 py-1 bg-gradient-to-r from-purple-500/20 to-purple-600/20 border border-purple-500/30 text-purple-400 rounded-full shadow-sm">
                          {selectedLanguage === 'dutch' && 'Vloeiende Expressie'}
                          {selectedLanguage === 'english' && 'Fluent Expression'}
                          {selectedLanguage === 'spanish' && 'Expresión Fluida'}
                          {selectedLanguage === 'german' && 'Fließender Ausdruck'}
                          {selectedLanguage === 'french' && 'Expression Fluide'}
                          {selectedLanguage === 'portuguese' && 'Expressão Fluente'}
                          {!selectedLanguage && 'Fluent Expression'}
                        </span>
                      )}
                    </div>
                    
                    {selectedLevel === level.code && (
                      <div className="absolute top-4 left-4">
                        <div className="w-8 h-8 rounded-full bg-[#4ECFBF] flex items-center justify-center shadow-lg animate-pulse">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-5 h-5">
                            <path fillRule="evenodd" d="M19.916 4.626a.75.75 0 01.208 1.04l-9 13.5a.75.75 0 01-1.154.114l-6-6a.75.75 0 011.06-1.06l5.353 5.353 8.493-12.739a.75.75 0 011.04-.208z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    )}
                    
                    <div className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${colors.bg} transition-all duration-500 ${selectedLevel === level.code ? 'w-full' : 'w-0'}`} />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Custom Topic Input Modal */}
      {isCustomTopicActive && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50">
          <div className="bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 rounded-xl shadow-lg w-full max-w-lg mx-4 p-6 md:p-8 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-50"></div>
            
            <div className="relative z-10 text-center mb-6">
              <h3 className="text-2xl md:text-3xl font-bold text-gray-800 mb-3">
                Create Your Custom Topic
              </h3>
              <p className="text-gray-600 text-sm md:text-base">
                What would you like to talk about in your conversation?
              </p>
            </div>
            
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
            
            <div className="flex flex-col sm:flex-row gap-3 relative z-10">
              <button
                onClick={() => setIsCustomTopicActive(false)}
                className="group relative overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-gray-300 hover:border-gray-400 w-full sm:flex-1 h-12 rounded-xl flex items-center justify-center transition-all duration-300 hover:shadow-md transform hover:translate-y-[-1px]"
                disabled={isExtendingKnowledge}
              >
                <span className="relative z-10 font-medium text-gray-700 group-hover:text-gray-800 transition-colors duration-300">Cancel</span>
                <div className="absolute bottom-0 left-0 h-0.5 bg-gray-400 w-0 group-hover:w-full transition-all duration-500"></div>
              </button>
              
              <button
                onClick={handleCustomTopicSubmit}
                className={`group relative overflow-hidden border-2 w-full sm:flex-1 h-12 rounded-xl flex items-center justify-center transition-all duration-300 transform hover:translate-y-[-1px] ${
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

      {/* Language Options Modal */}
      <LanguageOptionsModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        selectedLanguage={selectedLanguage || ''}
        onContinue={handleModalOptionSelect}
      />

      {/* Loading Modal */}
      <LoadingModal isOpen={isExtendingKnowledge} />

      {/* Global Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white/95 backdrop-blur-sm rounded-xl p-8 shadow-lg">
            <div className="relative w-20 h-20 mb-6 mx-auto">
              <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-[#4ECFBF]/20 animate-pulse"></div>
              <div className="absolute top-0 left-0 w-full h-full rounded-full border-8 border-transparent border-t-[#4ECFBF] animate-spin"></div>
            </div>
            <p className="text-gray-800 text-center animate-pulse">Starting your conversation...</p>
          </div>
        </div>
      )}
    </div>
  );
}
