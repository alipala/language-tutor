'use client';

import { useState, useEffect, KeyboardEvent, useRef } from 'react';
import { useRouter } from 'next/navigation';
import NavBar from '@/components/nav-bar';
import { useAuth } from '@/lib/auth';
import { useNavigation } from '@/lib/navigation';
import LoadingModal from '@/components/loading-modal';

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

  // Enhanced topics with 24 engaging options for language learning
  const getTopics = (language: string | null): Topic[] => {
    // Default to English if no language is selected
    const lang = language || 'english';
    
    // Enhanced topics structure with 24 topics
    const baseTopics = [
      // Core Topics (8 original + enhanced)
      {
        id: 'travel',
        names: {
          english: 'Travel & Tourism',
          dutch: 'Reizen & Toerisme',
          spanish: 'Viajes y Turismo',
          german: 'Reisen & Tourismus',
          french: 'Voyage & Tourisme',
          portuguese: 'Viagem & Turismo'
        },
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
        names: {
          english: 'Food & Cooking',
          dutch: 'Eten & Koken',
          spanish: 'Comida y Cocina',
          german: 'Essen & Kochen',
          french: 'Nourriture & Cuisine',
          portuguese: 'Comida & Culinária'
        },
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
        id: 'work',
        names: {
          english: 'Work & Career',
          dutch: 'Werk & Carrière',
          spanish: 'Trabajo y Carrera',
          german: 'Arbeit & Karriere',
          french: 'Travail & Carrière',
          portuguese: 'Trabalho & Carreira'
        },
        icon: '💼',
        descriptions: {
          english: 'Discuss jobs, career goals, workplace situations, and professional development.',
          dutch: 'Bespreek banen, carrièredoelen, werksituaties en professionele ontwikkeling.',
          spanish: 'Habla sobre trabajos, objetivos profesionales, situaciones laborales y desarrollo profesional.',
          german: 'Diskutiere über Jobs, Karriereziele, Arbeitsplatzsituationen und berufliche Entwicklung.',
          french: 'Discutez des emplois, des objectifs de carrière, des situations de travail et du développement professionnel.',
          portuguese: 'Converse sobre empregos, objetivos de carreira, situações de trabalho e desenvolvimento profissional.'
        }
      },
      {
        id: 'education',
        names: {
          english: 'Education & Learning',
          dutch: 'Onderwijs & Leren',
          spanish: 'Educación y Aprendizaje',
          german: 'Bildung & Lernen',
          french: 'Éducation & Apprentissage',
          portuguese: 'Educação & Aprendizagem'
        },
        icon: '📚',
        descriptions: {
          english: 'Talk about school, university, learning experiences, and educational goals.',
          dutch: 'Praat over school, universiteit, leerervaringen en educatieve doelen.',
          spanish: 'Habla sobre la escuela, universidad, experiencias de aprendizaje y objetivos educativos.',
          german: 'Sprich über Schule, Universität, Lernerfahrungen und Bildungsziele.',
          french: 'Parlez de l\'école, de l\'université, des expériences d\'apprentissage et des objectifs éducatifs.',
          portuguese: 'Fale sobre escola, universidade, experiências de aprendizado e objetivos educacionais.'
        }
      },
      
      // Daily Life Topics (8 new)
      {
        id: 'daily-routine',
        names: {
          english: 'Daily Routines',
          dutch: 'Dagelijkse Routines',
          spanish: 'Rutinas Diarias',
          german: 'Tägliche Routinen',
          french: 'Routines Quotidiennes',
          portuguese: 'Rotinas Diárias'
        },
        icon: '⏰',
        descriptions: {
          english: 'Share your daily schedule, morning routines, and everyday activities.',
          dutch: 'Deel je dagelijkse schema, ochtendroutines en alledaagse activiteiten.',
          spanish: 'Comparte tu horario diario, rutinas matutinas y actividades cotidianas.',
          german: 'Teile deinen Tagesablauf, Morgenroutinen und alltägliche Aktivitäten.',
          french: 'Partagez votre emploi du temps quotidien, vos routines matinales et vos activités quotidiennes.',
          portuguese: 'Compartilhe sua rotina diária, rotinas matinais e atividades do dia a dia.'
        }
      },
      {
        id: 'family',
        names: {
          english: 'Family & Relationships',
          dutch: 'Familie & Relaties',
          spanish: 'Familia y Relaciones',
          german: 'Familie & Beziehungen',
          french: 'Famille & Relations',
          portuguese: 'Família & Relacionamentos'
        },
        icon: '👨‍👩‍👧‍👦',
        descriptions: {
          english: 'Discuss family members, relationships, friendships, and social connections.',
          dutch: 'Bespreek familieleden, relaties, vriendschappen en sociale verbindingen.',
          spanish: 'Habla sobre miembros de la familia, relaciones, amistades y conexiones sociales.',
          german: 'Diskutiere über Familienmitglieder, Beziehungen, Freundschaften und soziale Verbindungen.',
          french: 'Discutez des membres de la famille, des relations, des amitiés et des connexions sociales.',
          portuguese: 'Converse sobre membros da família, relacionamentos, amizades e conexões sociais.'
        }
      },
      {
        id: 'health',
        names: {
          english: 'Health & Fitness',
          dutch: 'Gezondheid & Fitness',
          spanish: 'Salud y Fitness',
          german: 'Gesundheit & Fitness',
          french: 'Santé & Fitness',
          portuguese: 'Saúde & Fitness'
        },
        icon: '🏃‍♂️',
        descriptions: {
          english: 'Talk about exercise, healthy habits, medical topics, and wellness.',
          dutch: 'Praat over beweging, gezonde gewoonten, medische onderwerpen en welzijn.',
          spanish: 'Habla sobre ejercicio, hábitos saludables, temas médicos y bienestar.',
          german: 'Sprich über Sport, gesunde Gewohnheiten, medizinische Themen und Wohlbefinden.',
          french: 'Parlez d\'exercice, d\'habitudes saines, de sujets médicaux et de bien-être.',
          portuguese: 'Fale sobre exercícios, hábitos saudáveis, tópicos médicos e bem-estar.'
        }
      },
      {
        id: 'shopping',
        names: {
          english: 'Shopping & Money',
          dutch: 'Winkelen & Geld',
          spanish: 'Compras y Dinero',
          german: 'Einkaufen & Geld',
          french: 'Shopping & Argent',
          portuguese: 'Compras & Dinheiro'
        },
        icon: '🛍️',
        descriptions: {
          english: 'Discuss shopping experiences, prices, budgeting, and financial topics.',
          dutch: 'Bespreek winkelervaringen, prijzen, budgetteren en financiële onderwerpen.',
          spanish: 'Habla sobre experiencias de compras, precios, presupuestos y temas financieros.',
          german: 'Diskutiere über Einkaufserfahrungen, Preise, Budgetierung und Finanzthemen.',
          french: 'Discutez des expériences d\'achat, des prix, de la budgétisation et des sujets financiers.',
          portuguese: 'Converse sobre experiências de compras, preços, orçamento e tópicos financeiros.'
        }
      },
      
      // Entertainment & Culture (4 enhanced + 4 new)
      {
        id: 'movies',
        names: {
          english: 'Movies & TV Shows',
          dutch: 'Films & TV-shows',
          spanish: 'Películas y Series',
          german: 'Filme & TV-Serien',
          french: 'Films & Séries TV',
          portuguese: 'Filmes & Séries'
        },
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
        names: {
          english: 'Music & Arts',
          dutch: 'Muziek & Kunst',
          spanish: 'Música y Artes',
          german: 'Musik & Kunst',
          french: 'Musique & Arts',
          portuguese: 'Música & Artes'
        },
        icon: '🎵',
        descriptions: {
          english: 'Talk about music genres, artists, concerts, and creative arts.',
          dutch: 'Praat over muziekgenres, artiesten, concerten en creatieve kunsten.',
          spanish: 'Habla sobre géneros musicales, artistas, conciertos y artes creativas.',
          german: 'Sprich über Musikgenres, Künstler, Konzerte und kreative Künste.',
          french: 'Parlez des genres musicaux, des artistes, des concerts et des arts créatifs.',
          portuguese: 'Fale sobre gêneros musicais, artistas, concertos e artes criativas.'
        }
      },
      {
        id: 'sports',
        names: {
          english: 'Sports & Games',
          dutch: 'Sport & Spellen',
          spanish: 'Deportes y Juegos',
          german: 'Sport & Spiele',
          french: 'Sports & Jeux',
          portuguese: 'Esportes & Jogos'
        },
        icon: '⚽',
        descriptions: {
          english: 'Discuss sports, games, competitions, and physical activities.',
          dutch: 'Bespreek sporten, spellen, competities en fysieke activiteiten.',
          spanish: 'Habla sobre deportes, juegos, competiciones y actividades físicas.',
          german: 'Diskutiere über Sport, Spiele, Wettkämpfe und körperliche Aktivitäten.',
          french: 'Discutez des sports, des jeux, des compétitions et des activités physiques.',
          portuguese: 'Converse sobre esportes, jogos, competições e atividades físicas.'
        }
      },
      {
        id: 'hobbies',
        names: {
          english: 'Hobbies & Interests',
          dutch: 'Hobbys & Interesses',
          spanish: 'Aficiones e Intereses',
          german: 'Hobbys & Interessen',
          french: 'Loisirs & Intérêts',
          portuguese: 'Hobbies & Interesses'
        },
        icon: '🎨',
        descriptions: {
          english: 'Share your favorite activities, creative pursuits, and personal interests.',
          dutch: 'Deel je favoriete activiteiten, creatieve bezigheden en persoonlijke interesses.',
          spanish: 'Comparte tus actividades favoritas, actividades creativas e intereses personales.',
          german: 'Teile deine Lieblingsaktivitäten, kreativen Beschäftigungen und persönlichen Interessen.',
          french: 'Partagez vos activités préférées, vos activités créatives et vos intérêts personnels.',
          portuguese: 'Compartilhe suas atividades favoritas, atividades criativas e interesses pessoais.'
        }
      },
      
      // Modern Life Topics (4 new)
      {
        id: 'technology',
        names: {
          english: 'Technology & Digital Life',
          dutch: 'Technologie & Digitaal Leven',
          spanish: 'Tecnología y Vida Digital',
          german: 'Technologie & Digitales Leben',
          french: 'Technologie & Vie Numérique',
          portuguese: 'Tecnologia & Vida Digital'
        },
        icon: '💻',
        descriptions: {
          english: 'Discuss gadgets, apps, social media, and digital trends.',
          dutch: 'Bespreek gadgets, apps, sociale media en digitale trends.',
          spanish: 'Habla sobre gadgets, aplicaciones, redes sociales y tendencias digitales.',
          german: 'Diskutiere über Gadgets, Apps, soziale Medien und digitale Trends.',
          french: 'Discutez des gadgets, des applications, des médias sociaux et des tendances numériques.',
          portuguese: 'Converse sobre gadgets, aplicativos, mídias sociais e tendências digitais.'
        }
      },
      {
        id: 'news',
        names: {
          english: 'News & Current Events',
          dutch: 'Nieuws & Actualiteiten',
          spanish: 'Noticias y Eventos Actuales',
          german: 'Nachrichten & Aktuelles',
          french: 'Actualités & Événements',
          portuguese: 'Notícias & Eventos Atuais'
        },
        icon: '📰',
        descriptions: {
          english: 'Talk about current events, news stories, and global happenings.',
          dutch: 'Praat over actuele gebeurtenissen, nieuwsverhalen en wereldwijde gebeurtenissen.',
          spanish: 'Habla sobre eventos actuales, noticias y acontecimientos globales.',
          german: 'Sprich über aktuelle Ereignisse, Nachrichten und weltweite Geschehnisse.',
          french: 'Parlez des événements actuels, des nouvelles et des événements mondiaux.',
          portuguese: 'Fale sobre eventos atuais, notícias e acontecimentos globais.'
        }
      },
      {
        id: 'weather',
        names: {
          english: 'Weather & Seasons',
          dutch: 'Weer & Seizoenen',
          spanish: 'Clima y Estaciones',
          german: 'Wetter & Jahreszeiten',
          french: 'Météo & Saisons',
          portuguese: 'Clima & Estações'
        },
        icon: '🌤️',
        descriptions: {
          english: 'Discuss weather conditions, seasons, climate, and outdoor activities.',
          dutch: 'Bespreek weersomstandigheden, seizoenen, klimaat en buitenactiviteiten.',
          spanish: 'Habla sobre condiciones climáticas, estaciones, clima y actividades al aire libre.',
          german: 'Diskutiere über Wetterbedingungen, Jahreszeiten, Klima und Outdoor-Aktivitäten.',
          french: 'Discutez des conditions météorologiques, des saisons, du climat et des activités de plein air.',
          portuguese: 'Converse sobre condições climáticas, estações, clima e atividades ao ar livre.'
        }
      },
      {
        id: 'transportation',
        names: {
          english: 'Transportation & Travel',
          dutch: 'Vervoer & Reizen',
          spanish: 'Transporte y Viajes',
          german: 'Transport & Reisen',
          french: 'Transport & Voyage',
          portuguese: 'Transporte & Viagem'
        },
        icon: '🚗',
        descriptions: {
          english: 'Talk about vehicles, public transport, commuting, and getting around.',
          dutch: 'Praat over voertuigen, openbaar vervoer, woon-werkverkeer en verplaatsingen.',
          spanish: 'Habla sobre vehículos, transporte público, desplazamientos y movilidad.',
          german: 'Sprich über Fahrzeuge, öffentliche Verkehrsmittel, Pendeln und Fortbewegung.',
          french: 'Parlez des véhicules, des transports publics, des déplacements domicile-travail et de la mobilité.',
          portuguese: 'Fale sobre veículos, transporte público, deslocamentos e locomoção.'
        }
      },
      
      // Lifestyle & Personal Topics (4 new)
      {
        id: 'culture',
        names: {
          english: 'Culture & Traditions',
          dutch: 'Cultuur & Tradities',
          spanish: 'Cultura y Tradiciones',
          german: 'Kultur & Traditionen',
          french: 'Culture & Traditions',
          portuguese: 'Cultura & Tradições'
        },
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
        id: 'environment',
        names: {
          english: 'Environment & Nature',
          dutch: 'Milieu & Natuur',
          spanish: 'Medio Ambiente y Naturaleza',
          german: 'Umwelt & Natur',
          french: 'Environnement & Nature',
          portuguese: 'Meio Ambiente & Natureza'
        },
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
        id: 'home',
        names: {
          english: 'Home & Living',
          dutch: 'Thuis & Wonen',
          spanish: 'Hogar y Vida',
          german: 'Zuhause & Wohnen',
          french: 'Maison & Vie',
          portuguese: 'Casa & Vida'
        },
        icon: '🏠',
        descriptions: {
          english: 'Discuss housing, home decoration, household tasks, and living spaces.',
          dutch: 'Bespreek huisvesting, woninginrichting, huishoudelijke taken en woonruimtes.',
          spanish: 'Habla sobre vivienda, decoración del hogar, tareas domésticas y espacios habitables.',
          german: 'Diskutiere über Wohnen, Wohnungseinrichtung, Haushaltsaufgaben und Wohnräume.',
          french: 'Discutez du logement, de la décoration intérieure, des tâches ménagères et des espaces de vie.',
          portuguese: 'Converse sobre habitação, decoração de casa, tarefas domésticas e espaços de convivência.'
        }
      },
      {
        id: 'pets',
        names: {
          english: 'Pets & Animals',
          dutch: 'Huisdieren & Dieren',
          spanish: 'Mascotas y Animales',
          german: 'Haustiere & Tiere',
          french: 'Animaux & Compagnie',
          portuguese: 'Animais & Pets'
        },
        icon: '🐕',
        descriptions: {
          english: 'Talk about pets, animals, wildlife, and animal care.',
          dutch: 'Praat over huisdieren, dieren, wilde dieren en dierenverzorging.',
          spanish: 'Habla sobre mascotas, animales, vida silvestre y cuidado de animales.',
          german: 'Sprich über Haustiere, Tiere, Wildtiere und Tierpflege.',
          french: 'Parlez des animaux de compagnie, des animaux, de la faune et des soins aux animaux.',
          portuguese: 'Fale sobre animais de estimação, animais, vida selvagem e cuidados com animais.'
        }
      },
      
      // Special Topics (1 enhanced)
      {
        id: 'custom',
        name: '✨ Create Your Own Topic',
        icon: '🔍',
        descriptions: {
          english: 'Create your own personalized topic for a unique conversation experience.',
          dutch: 'Maak je eigen gepersonaliseerde onderwerp voor een unieke gespreks-ervaring.',
          spanish: 'Crea tu propio tema personalizado para una experiencia de conversación única.',
          german: 'Erstelle dein eigenes personalisiertes Thema für ein einzigartiges Gesprächserlebnis.',
          french: 'Créez votre propre sujet personnalisé pour une expérience de conversation unique.',
          portuguese: 'Crie seu próprio tópico personalizado para uma experiência de conversa única.'
        }
      }
    ];
    
    // Map to the expected Topic format with the correct language description and name
    return baseTopics.map(topic => ({
      id: topic.id,
      name: topic.names 
        ? (topic.names[lang as keyof typeof topic.names] || topic.names.english)
        : topic.name || 'Unknown Topic',
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
      
      // Use dynamic backend URL that works in both development and production
      const backendUrl = process.env.NODE_ENV === 'production' 
        ? 'https://taco.up.railway.app' 
        : 'http://localhost:8000';
      
      const response = await fetch(`${backendUrl}/api/custom-topic/research`, {
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
      <main className="flex-grow flex flex-col p-4 md:p-8 main-content-with-navbar" style={{paddingTop: '220px'}}>
        <div className="flex flex-col flex-1 items-stretch space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-bold text-black mb-4">
            {selectedLanguage === 'dutch' && 'Kies een Onderwerp / Choose a Topic'}
            {selectedLanguage === 'spanish' && 'Elige un Tema / Choose a Topic'}
            {selectedLanguage === 'german' && 'Wähle ein Thema / Choose a Topic'}
            {selectedLanguage === 'french' && 'Choisissez un Sujet / Choose a Topic'}
            {selectedLanguage === 'portuguese' && 'Escolha um Tópico / Choose a Topic'}
            {(selectedLanguage === 'english' || !selectedLanguage) && 'Choose a Topic'}
          </h1>
          <p className="text-gray-600 text-lg mb-8">
            {selectedLanguage === 'dutch' && 'Selecteer een onderwerp voor je Nederlandse conversatie (optioneel)'}
            {selectedLanguage === 'english' && 'Select a topic for your English conversation (optional)'}
            {selectedLanguage === 'spanish' && 'Selecciona un tema para tu conversación en español (opcional)'}
            {selectedLanguage === 'german' && 'Wähle ein Thema für dein Gespräch auf Deutsch (optional)'}
            {selectedLanguage === 'french' && 'Sélectionnez un sujet pour votre conversation en français (facultatif)'}
            {selectedLanguage === 'portuguese' && 'Selecione um tópico para sua conversa em português (opcional)'}
            {!selectedLanguage && 'Select a topic for your conversation (optional)'}
          </p>
        </div>

        {/* Enhanced Topics Grid for 23 Regular Topics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6 max-h-[60vh] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-[#4ECFBF]/30 scrollbar-track-gray-100">
          {topics.filter(topic => topic.id !== 'custom').map((topic, index) => (
            <button
              key={topic.id}
              onClick={() => handleTopicSelect(topic.id)}
              disabled={isLoading || isExtendingKnowledge}
              className="group relative overflow-hidden rounded-xl transition-all duration-300 bg-white border-2 border-[#4ECFBF]/40 hover:border-[#4ECFBF]/60 flex flex-col p-4 sm:p-6 text-left min-h-40 sm:min-h-44 transform hover:translate-y-[-2px] shadow-lg hover:shadow-[#4ECFBF]/20 animate-slide-up touch-target cursor-pointer hover:scale-105"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Hover Effect Background */}
              <div className="absolute inset-0 bg-[#4ECFBF]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Icon */}
              <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">
                {topic.icon}
              </div>
              
              {/* Title */}
              <h3 className="text-lg sm:text-xl font-semibold text-gray-800 group-hover:text-[#4ECFBF] mb-2 transition-colors duration-300">
                {topic.name}
              </h3>
              
              {/* Description */}
              <p className="text-xs sm:text-sm text-gray-600 group-hover:text-gray-700 transition-colors duration-300 line-clamp-3">
                {topic.description}
              </p>
              
              {/* Bottom Accent Line */}
              <div className="absolute bottom-0 left-0 h-1 bg-[#4ECFBF] w-0 group-hover:w-full transition-all duration-500"></div>
            </button>
          ))}
        </div>

        {/* Custom Topic Card - Centered at Bottom with Bigger Size */}
        <div className="flex justify-center mt-8">
          {(() => {
            const customTopic = topics.find(topic => topic.id === 'custom');
            if (!customTopic) return null;
            
            return (
              <button
                onClick={() => handleTopicSelect('custom')}
                disabled={isLoading || isExtendingKnowledge}
                className={`
                  group relative overflow-hidden rounded-xl transition-all duration-300 
                  bg-gradient-to-br from-[#4ECFBF]/10 via-white to-[#4ECFBF]/5 
                  border-2 border-[#4ECFBF] shadow-[#4ECFBF]/10
                  flex flex-col p-6 md:p-8 text-center
                  w-full max-w-md h-48 md:h-56
                  transform hover:translate-y-[-4px] shadow-lg hover:shadow-[#4ECFBF]/30
                  animate-slide-up touch-target cursor-pointer hover:scale-105
                  ${isCustomTopicActive ? 'ring-2 ring-[#4ECFBF]/50 shadow-[#4ECFBF]/20' : ''}
                  ${(isLoading || isExtendingKnowledge) ? 'opacity-50 cursor-not-allowed' : ''}
                `}
                style={{ animationDelay: '1200ms' }}
              >
                {/* Enhanced Hover Effect Background */}
                <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/15 to-[#4ECFBF]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                
                {/* Special Badge */}
                <div className="absolute top-3 right-3 bg-[#4ECFBF] text-white text-xs px-3 py-1 rounded-full font-medium shadow-md">
                  Popular
                </div>
                
                {/* Icon */}
                <div className="text-5xl md:text-6xl mb-4 filter drop-shadow-sm">
                  {customTopic.icon}
                </div>
                
                {/* Title */}
                <h3 className="text-xl md:text-2xl font-bold text-[#4ECFBF] group-hover:text-[#4ECFBF]/80 mb-3 transition-colors duration-300">
                  {customTopic.name}
                </h3>
                
                {/* Description */}
                <p className="text-sm md:text-base text-gray-700 group-hover:text-gray-800 transition-colors duration-300 line-clamp-2">
                  {customTopic.description}
                </p>
                
                {/* Enhanced Bottom Accent Line */}
                <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-[#4ECFBF] to-[#4ECFBF]/60 w-full"></div>
                
                {/* Sparkle Effect */}
                <div className="absolute top-4 left-4 text-[#4ECFBF] opacity-60 group-hover:opacity-100 transition-opacity duration-300">
                  ✨
                </div>
              </button>
            );
          })()}
        </div>
        
        {/* Topic Count Indicator */}
        <div className="text-center mt-6">
          <p className="text-sm text-gray-500">
            {topics.length} topics available • Choose one or create your own
          </p>
        </div>
        
        {/* Custom Topic Input Modal - Only show when active */}
        {isCustomTopicActive && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50">
            <div className="bg-white/95 backdrop-blur-sm border-2 border-[#4ECFBF]/40 rounded-xl shadow-lg w-full max-w-lg mx-4 p-6 md:p-8 relative overflow-hidden">
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4ECFBF]/5 via-[#4ECFBF]/10 to-transparent opacity-50"></div>
              
              {/* Header */}
              <div className="relative z-10 text-center mb-6">
                <h3 className="text-2xl md:text-3xl font-bold text-gray-800 mb-3">
                  {selectedLanguage === 'dutch' && 'Maak je eigen onderwerp / Create Your Custom Topic'}
                  {selectedLanguage === 'spanish' && 'Crea tu tema personalizado / Create Your Custom Topic'}
                  {selectedLanguage === 'german' && 'Erstelle dein eigenes Thema / Create Your Custom Topic'}
                  {selectedLanguage === 'french' && 'Créez votre sujet personnalisé / Create Your Custom Topic'}
                  {selectedLanguage === 'portuguese' && 'Crie seu tópico personalizado / Create Your Custom Topic'}
                  {(selectedLanguage === 'english' || !selectedLanguage) && 'Create Your Custom Topic'}
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
        <LoadingModal isOpen={isExtendingKnowledge} />
        </div>
      </main>
    </div>
  );
}
