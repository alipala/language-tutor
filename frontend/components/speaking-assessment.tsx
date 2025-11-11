'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, RotateCw, Volume2, ChevronRight, AlertCircle, ThumbsUp, Check, Target, ArrowUpRight, Footprints, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { assessSpeaking, fetchSpeakingPrompts, saveSpeakingAssessment, SpeakingAssessmentResult, SpeakingPrompt } from '@/lib/speaking-assessment-api';
import { isAuthenticated } from '@/lib/auth-utils';
import { getAssessmentDuration, formatTime, getMaxAssessmentDetails, getGuestLimitationsDescription, ASSESSMENT_DURATION_GUEST, ASSESSMENT_DURATION_REGISTERED, CONVERSATION_DURATION_GUEST, CONVERSATION_DURATION_REGISTERED } from '@/lib/guest-utils';
import { useNotification } from '@/components/ui/notification';
import { useMobile } from '@/hooks/use-mobile';
import EnhancedLearningPlanModal from './enhanced-learning-plan-modal';

interface SpeakingAssessmentProps {
  language: string;
  onComplete?: (result: SpeakingAssessmentResult) => void;
  onSelectLevel?: (level: string) => void;
}

export default function SpeakingAssessment({ 
  language, 
  onComplete, 
  onSelectLevel 
}: SpeakingAssessmentProps) {
  // Access notification context
  const { showNotification } = useNotification();
  const isMobile = useMobile();
  
  // State for recording and assessment
  const [status, setStatus] = useState<'idle' | 'topic-selection' | 'preparation' | 'recording' | 'processing' | 'complete'>('topic-selection');
  const [showLearningPlanModal, setShowLearningPlanModal] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<any>(null);
  const [showTopicSelection, setShowTopicSelection] = useState(true);
  const [showPreparation, setShowPreparation] = useState(false);
  const [currentTopicIndex, setCurrentTopicIndex] = useState(0);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);
  const [timer, setTimer] = useState(60);
  const [initialDuration, setInitialDuration] = useState(60); // Track initial duration for progress calculation
  const [isTimerActive, setIsTimerActive] = useState(false);
  const [canStopRecording, setCanStopRecording] = useState(false); // New state for stop button logic
  const [showOptimalNotification, setShowOptimalNotification] = useState(false); // New state for bottom-right notification
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [transcription, setTranscription] = useState('');
  const [assessment, setAssessment] = useState<SpeakingAssessmentResult | null>(null);
  const [error, setError] = useState('');
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const promptRef = useRef('');

  // Initialize the component
  useEffect(() => {
    // Clear any error message
    setError('');
    
    // REMOVED: Assessment completion check that was preventing multiple assessments
    // Users should be able to take multiple assessments to create up to 10 learning plans
  }, [language]);
  
  // No longer checking for guest time expiration

  // Timer effect with stop button logic and notification
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isTimerActive && timer > 0) {
      interval = setInterval(() => {
        setTimer((prevTimer) => {
          const newTimer = prevTimer - 1;
          const elapsed = initialDuration - newTimer;
          
          // Enable stop button after 45 seconds for registered users
          if (isAuthenticated() && elapsed >= 45 && !canStopRecording) {
            setCanStopRecording(true);
            setShowOptimalNotification(true);
            
            // Auto-hide notification after 3 seconds
            setTimeout(() => {
              setShowOptimalNotification(false);
            }, 3000);
          }
          
          return newTimer;
        });
      }, 1000);
    } else if (isTimerActive && timer === 0) {
      setIsTimerActive(false);
      stopRecording();
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isTimerActive, timer, initialDuration, canStopRecording]);

  // Clean up audio URL when component unmounts
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startRecording = async () => {
    // Check user status and set appropriate limitations
    const isUserAuthenticated = isAuthenticated();
    const assessmentDuration = getAssessmentDuration(isUserAuthenticated); // Get duration from utility function
    
    // Check subscription limits for authenticated users before starting assessment
    if (isUserAuthenticated) {
      try {
        console.log('[SUBSCRIPTION] Checking speaking assessment access before starting...');
        const { getApiUrl } = await import('@/lib/api-utils');
        const token = localStorage.getItem('token');
        
        const response = await fetch(`${getApiUrl()}/api/stripe/can-access/assessment`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const result = await response.json();
          if (!result.can_access) {
            console.log('[SUBSCRIPTION] ❌ Speaking assessment access denied:', result.message);
            
            // Show subscription limit error
            setError(`Assessment Limit Reached: ${result.message}`);
            
            // Show notification with upgrade option
            if (showNotification) {
              showNotification(result.message, 'error');
            }
            
            return; // Don't start the assessment
          } else {
            console.log('[SUBSCRIPTION] ✅ Speaking assessment access granted');
          }
        } else {
          console.warn('[SUBSCRIPTION] ⚠️ Could not check subscription limits, allowing assessment');
        }
      } catch (error) {
        console.error('[SUBSCRIPTION] ❌ Error checking subscription limits:', error);
        // Allow assessment to continue if check fails
      }
    }
    
    try {
      // Reset state
      setAudioBlob(null);
      setAudioUrl(null);
      setTranscription('');
      setAssessment(null);
      setError('');
      
      // Start timer with appropriate duration
      setTimer(assessmentDuration);
      setInitialDuration(assessmentDuration); // Update initial duration
      setIsTimerActive(true);
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Set up event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        setAudioBlob(audioBlob);
        setAudioUrl(audioUrl);
        
        // Process recording
        processRecording(audioBlob);
      };
      
      // Start recording
      mediaRecorder.start(100);
      setStatus('recording');
    } catch (err: any) {
      console.error('Error starting recording:', err);
      setError(`Error accessing microphone: ${err.message || 'Please check your microphone permissions.'}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsTimerActive(false);
      
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const processRecording = async (blob: Blob) => {
    try {
      setStatus('processing');
      
      // Use selected topic's prompt or fallback to general prompt
      const assessmentPrompt = selectedTopic?.prompt || `Please speak naturally in ${language} about any topic you're comfortable with. You can talk about your hobbies, daily life, experiences, or anything that interests you.`;
      
      // Get assessment from API
      const result = await assessSpeaking(
        blob, 
        language, 
        initialDuration - timer,
        assessmentPrompt
      );
      
      // Set assessment result
      setAssessment(result);
      setStatus('complete');
      
      // Mark assessment as completed in session storage
      sessionStorage.setItem('assessmentCompleted', 'true');
      
      // Call onComplete callback if provided
      if (onComplete) {
        onComplete(result);
      }
      
      // Save assessment data to user profile if authenticated
      if (isAuthenticated()) {
        try {
          const saved = await saveSpeakingAssessment(result);
          if (saved) {
            console.log('Assessment data saved to user profile');
          } else {
            console.warn('Failed to save assessment data to user profile');
          }
        } catch (saveErr) {
          console.error('Error saving assessment data:', saveErr);
          // Don't show this error to the user as it's not critical
        }

        // Track usage for subscription limits
        try {
          console.log('[SUBSCRIPTION] Tracking speaking assessment usage for subscription limits');
          const { getApiUrl } = await import('@/lib/api-utils');
          const token = localStorage.getItem('token');
          
          const usageResponse = await fetch(`${getApiUrl()}/api/stripe/track-usage`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              usage_type: 'assessment',
              duration_minutes: (initialDuration - timer) / 60 // Convert seconds to minutes
            })
          });

          if (usageResponse.ok) {
            const usageResult = await usageResponse.json();
            console.log('[SUBSCRIPTION] ✅ Speaking assessment usage tracked:', usageResult);
          } else {
            const usageError = await usageResponse.json();
            console.warn('[SUBSCRIPTION] ⚠️ Failed to track assessment usage:', usageError);
          }
        } catch (usageError) {
          console.error('[SUBSCRIPTION] ❌ Error tracking assessment usage:', usageError);
        }
      }
    } catch (err: any) {
      console.error('Error processing recording:', err);
      setError(`Error processing recording: ${err.message || 'Unknown error'}`);
      setStatus('idle');
    }
  };

  // No longer need prompt selection handlers

  const handlePlayAudio = () => {
    if (audioPlayerRef.current) {
      if (isAudioPlaying) {
        audioPlayerRef.current.pause();
      } else {
        audioPlayerRef.current.play();
      }
      setIsAudioPlaying(!isAudioPlaying);
    }
  };

  const handleTryAgain = () => {
    // Remove the completed flag to allow a new assessment
    sessionStorage.removeItem('assessmentCompleted');
    
    setStatus('topic-selection');
    setSelectedTopic(null);
    setTimer(60);
    setInitialDuration(60); // Reset initial duration
    setCanStopRecording(false); // Reset stop button state
    setShowOptimalNotification(false); // Reset notification state
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAssessment(null);
    setTranscription('');
    setError('');
  };

  const handleSelectLevel = () => {
    // Store the assessment data in session storage for use in the speech client
    if (assessment) {
      try {
        sessionStorage.setItem('speakingAssessmentData', JSON.stringify(assessment));
        console.log('Stored speaking assessment data in session storage');
      } catch (e) {
        console.error('Error storing speaking assessment data:', e);
      }
    }
    
    setShowLearningPlanModal(true);
  };

  const handleLearningPlanModalClose = () => {
    setShowLearningPlanModal(false);
    console.log('Learning plan modal closed without creating a plan');
    // Keep the assessmentCompleted flag to prevent restarting after refresh
  };

  const handlePlanCreated = (planId: string) => {
    console.log('Learning plan created with ID:', planId);
    sessionStorage.setItem('pendingLearningPlanId', planId);
    
    // Ensure the assessment is marked as completed
    sessionStorage.setItem('assessmentCompleted', 'true');
    
    // If onSelectLevel callback is provided, use it to trigger redirection
    if (onSelectLevel) {
      console.log('Triggering onSelectLevel callback with recommended level:', assessment?.recommended_level);
      onSelectLevel(assessment?.recommended_level || 'A1');
    } else {
      console.warn('No onSelectLevel callback provided, redirection may not work as expected');
    }
  };

  // Format time from seconds to MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Helper function to get color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Helper function to get progress color based on score
  const getProgressColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Check if user is authenticated
  const userIsAuthenticated = isAuthenticated();

  // Define speaking topics with translations
  const getTopics = (): Array<{id: string; icon: string; title: string; prompt: string; hints: string[]}> => {
    const topics: Record<string, Array<{id: string; icon: string; title: string; prompt: string; hints: string[]}>> = {
      english: [
        {
          id: 'about-you',
          icon: '🙋',
          title: 'About You',
          prompt: 'Tell me about yourself and your daily life',
          hints: [
            'Where are you from and where do you live now?',
            'What do you do for work or study?',
            'What does a typical day look like for you?',
            'What are your main responsibilities or activities?'
          ]
        },
        {
          id: 'travel-places',
          icon: '🌍',
          title: 'Travel & Places',
          prompt: 'Describe a place that is special to you',
          hints: [
            'What place comes to mind? (hometown, vacation spot, favorite city)',
            'What does this place look like?',
            'Why is it meaningful to you?',
            'What do you like to do there?'
          ]
        },
        {
          id: 'interests-hobbies',
          icon: '🎨',
          title: 'Interests & Hobbies',
          prompt: 'Talk about something you enjoy doing',
          hints: [
            'What hobby or interest do you have?',
            'How did you get started with it?',
            'How often do you do this activity?',
            'What do you like most about it?'
          ]
        },
        {
          id: 'experiences-memories',
          icon: '💭',
          title: 'Experiences & Memories',
          prompt: 'Share a memorable experience from your life',
          hints: [
            'What experience stands out to you?',
            'When and where did it happen?',
            'Who was involved?',
            'Why was it memorable?'
          ]
        },
        {
          id: 'future-goals',
          icon: '🎯',
          title: 'Future & Goals',
          prompt: 'Discuss your plans or dreams for the future',
          hints: [
            'What are you hoping to achieve?',
            'What steps are you taking toward this goal?',
            'Why is this important to you?',
            'How do you imagine your life in the future?'
          ]
        },
        {
          id: 'work-professional',
          icon: '💼',
          title: 'Work & Professional Life',
          prompt: 'Talk about your work or professional experiences',
          hints: [
            'What kind of work do you do or want to do?',
            'What do you find challenging or rewarding about your work?',
            'How did you get into your current field?',
            'What are your professional goals or aspirations?'
          ]
        }
      ],
      dutch: [
        {
          id: 'about-you',
          icon: '🙋',
          title: 'Over Jezelf',
          prompt: 'Vertel me over jezelf en je dagelijks leven',
          hints: [
            'Waar kom je vandaan en waar woon je nu?',
            'Wat doe je voor werk of studie?',
            'Hoe ziet een typische dag eruit voor jou?',
            'Wat zijn je belangrijkste verantwoordelijkheden of activiteiten?'
          ]
        },
        {
          id: 'travel-places',
          icon: '🌍',
          title: 'Reizen & Plaatsen',
          prompt: 'Beschrijf een plek die speciaal voor je is',
          hints: [
            'Welke plek komt in je op? (geboorteplaats, vakantieplek, favoriete stad)',
            'Hoe ziet deze plek eruit?',
            'Waarom is het belangrijk voor je?',
            'Wat doe je daar graag?'
          ]
        },
        {
          id: 'interests-hobbies',
          icon: '🎨',
          title: 'Interesses & Hobbys',
          prompt: 'Praat over iets wat je graag doet',
          hints: [
            'Welke hobby of interesse heb je?',
            'Hoe ben je ermee begonnen?',
            'Hoe vaak doe je deze activiteit?',
            'Wat vind je er het leukst aan?'
          ]
        },
        {
          id: 'experiences-memories',
          icon: '💭',
          title: 'Ervaringen & Herinneringen',
          prompt: 'Deel een gedenkwaardige ervaring uit je leven',
          hints: [
            'Welke ervaring springt eruit?',
            'Wanneer en waar gebeurde het?',
            'Wie waren erbij betrokken?',
            'Waarom was het gedenkwaardig?'
          ]
        },
        {
          id: 'future-goals',
          icon: '🎯',
          title: 'Toekomst & Doelen',
          prompt: 'Bespreek je plannen of dromen voor de toekomst',
          hints: [
            'Wat hoop je te bereiken?',
            'Welke stappen neem je naar dit doel?',
            'Waarom is dit belangrijk voor je?',
            'Hoe stel je je leven in de toekomst voor?'
          ]
        },
        {
          id: 'work-professional',
          icon: '💼',
          title: 'Werk & Professioneel Leven',
          prompt: 'Praat over je werk of professionele ervaringen',
          hints: [
            'Wat voor werk doe je of wil je doen?',
            'Wat vind je uitdagend of lonend aan je werk?',
            'Hoe ben je in je huidige vakgebied terechtgekomen?',
            'Wat zijn je professionele doelen of ambities?'
          ]
        }
      ],
      spanish: [
        {
          id: 'about-you',
          icon: '🙋',
          title: 'Sobre Ti',
          prompt: 'Cuéntame sobre ti y tu vida diaria',
          hints: [
            '¿De dónde eres y dónde vives ahora?',
            '¿A qué te dedicas o qué estudias?',
            '¿Cómo es un día típico para ti?',
            '¿Cuáles son tus principales responsabilidades o actividades?'
          ]
        },
        {
          id: 'travel-places',
          icon: '🌍',
          title: 'Viajes y Lugares',
          prompt: 'Describe un lugar que sea especial para ti',
          hints: [
            '¿Qué lugar te viene a la mente? (ciudad natal, lugar de vacaciones, ciudad favorita)',
            '¿Cómo es este lugar?',
            '¿Por qué es significativo para ti?',
            '¿Qué te gusta hacer allí?'
          ]
        },
        {
          id: 'interests-hobbies',
          icon: '🎨',
          title: 'Intereses y Pasatiempos',
          prompt: 'Habla sobre algo que disfrutas hacer',
          hints: [
            '¿Qué pasatiempo o interés tienes?',
            '¿Cómo empezaste con ello?',
            '¿Con qué frecuencia haces esta actividad?',
            '¿Qué es lo que más te gusta de ello?'
          ]
        },
        {
          id: 'experiences-memories',
          icon: '💭',
          title: 'Experiencias y Recuerdos',
          prompt: 'Comparte una experiencia memorable de tu vida',
          hints: [
            '¿Qué experiencia te destaca?',
            '¿Cuándo y dónde sucedió?',
            '¿Quién estuvo involucrado?',
            '¿Por qué fue memorable?'
          ]
        },
        {
          id: 'future-goals',
          icon: '🎯',
          title: 'Futuro y Metas',
          prompt: 'Discute tus planes o sueños para el futuro',
          hints: [
            '¿Qué esperas lograr?',
            '¿Qué pasos estás tomando hacia esta meta?',
            '¿Por qué es importante para ti?',
            '¿Cómo imaginas tu vida en el futuro?'
          ]
        },
        {
          id: 'work-professional',
          icon: '💼',
          title: 'Trabajo y Vida Profesional',
          prompt: 'Habla sobre tu trabajo o experiencias profesionales',
          hints: [
            '¿Qué tipo de trabajo haces o quieres hacer?',
            '¿Qué encuentras desafiante o gratificante en tu trabajo?',
            '¿Cómo llegaste a tu campo actual?',
            '¿Cuáles son tus metas o aspiraciones profesionales?'
          ]
        }
      ],
      german: [
        {
          id: 'about-you',
          icon: '🙋',
          title: 'Über Dich',
          prompt: 'Erzähl mir über dich und dein tägliches Leben',
          hints: [
            'Woher kommst du und wo wohnst du jetzt?',
            'Was machst du beruflich oder was studierst du?',
            'Wie sieht ein typischer Tag für dich aus?',
            'Was sind deine Hauptverantwortlichkeiten oder Aktivitäten?'
          ]
        },
        {
          id: 'travel-places',
          icon: '🌍',
          title: 'Reisen & Orte',
          prompt: 'Beschreibe einen Ort, der dir besonders ist',
          hints: [
            'Welcher Ort fällt dir ein? (Heimatstadt, Urlaubsort, Lieblingsstadt)',
            'Wie sieht dieser Ort aus?',
            'Warum ist er bedeutsam für dich?',
            'Was machst du dort gerne?'
          ]
        },
        {
          id: 'interests-hobbies',
          icon: '🎨',
          title: 'Interessen & Hobbys',
          prompt: 'Sprich über etwas, das du gerne machst',
          hints: [
            'Welches Hobby oder Interesse hast du?',
            'Wie hast du damit angefangen?',
            'Wie oft machst du diese Aktivität?',
            'Was gefällt dir am meisten daran?'
          ]
        },
        {
          id: 'experiences-memories',
          icon: '💭',
          title: 'Erfahrungen & Erinnerungen',
          prompt: 'Teile eine unvergessliche Erfahrung aus deinem Leben',
          hints: [
            'Welche Erfahrung sticht heraus?',
            'Wann und wo ist es passiert?',
            'Wer war beteiligt?',
            'Warum war es unvergesslich?'
          ]
        },
        {
          id: 'future-goals',
          icon: '🎯',
          title: 'Zukunft & Ziele',
          prompt: 'Diskutiere deine Pläne oder Träume für die Zukunft',
          hints: [
            'Was hoffst du zu erreichen?',
            'Welche Schritte unternimmst du zu diesem Ziel?',
            'Warum ist das wichtig für dich?',
            'Wie stellst du dir dein Leben in der Zukunft vor?'
          ]
        },
        {
          id: 'work-professional',
          icon: '💼',
          title: 'Arbeit & Berufsleben',
          prompt: 'Sprich über deine Arbeit oder beruflichen Erfahrungen',
          hints: [
            'Was für eine Arbeit machst du oder möchtest du machen?',
            'Was findest du herausfordernd oder lohnend an deiner Arbeit?',
            'Wie bist du in dein aktuelles Feld gekommen?',
            'Was sind deine beruflichen Ziele oder Bestrebungen?'
          ]
        }
      ],
      french: [
        {
          id: 'about-you',
          icon: '🙋',
          title: 'À Propos de Toi',
          prompt: 'Parle-moi de toi et de ta vie quotidienne',
          hints: [
            "D'où viens-tu et où habites-tu maintenant?",
            'Que fais-tu comme travail ou études?',
            'À quoi ressemble une journée typique pour toi?',
            'Quelles sont tes principales responsabilités ou activités?'
          ]
        },
        {
          id: 'travel-places',
          icon: '🌍',
          title: 'Voyages & Lieux',
          prompt: 'Décris un endroit qui est spécial pour toi',
          hints: [
            'Quel endroit te vient à l\'esprit? (ville natale, lieu de vacances, ville préférée)',
            'À quoi ressemble cet endroit?',
            'Pourquoi est-il significatif pour toi?',
            "Qu'aimes-tu y faire?"
          ]
        },
        {
          id: 'interests-hobbies',
          icon: '🎨',
          title: 'Intérêts & Loisirs',
          prompt: 'Parle de quelque chose que tu aimes faire',
          hints: [
            'Quel loisir ou intérêt as-tu?',
            'Comment as-tu commencé?',
            'À quelle fréquence fais-tu cette activité?',
            "Qu'est-ce que tu aimes le plus?"
          ]
        },
        {
          id: 'experiences-memories',
          icon: '💭',
          title: 'Expériences & Souvenirs',
          prompt: 'Partage une expérience mémorable de ta vie',
          hints: [
            'Quelle expérience te marque?',
            'Quand et où est-ce arrivé?',
            'Qui était impliqué?',
            'Pourquoi était-ce mémorable?'
          ]
        },
        {
          id: 'future-goals',
          icon: '🎯',
          title: 'Avenir & Objectifs',
          prompt: 'Discute de tes plans ou rêves pour l\'avenir',
          hints: [
            "Qu'espères-tu accomplir?",
            'Quelles étapes prends-tu vers cet objectif?',
            'Pourquoi est-ce important pour toi?',
            'Comment imagines-tu ta vie dans le futur?'
          ]
        },
        {
          id: 'work-professional',
          icon: '💼',
          title: 'Travail & Vie Professionnelle',
          prompt: 'Parle de ton travail ou de tes expériences professionnelles',
          hints: [
            'Quel type de travail fais-tu ou veux-tu faire?',
            'Que trouves-tu difficile ou gratifiant dans ton travail?',
            'Comment es-tu arrivé dans ton domaine actuel?',
            'Quels sont tes objectifs ou aspirations professionnels?'
          ]
        }
      ],
      portuguese: [
        {
          id: 'about-you',
          icon: '🙋',
          title: 'Sobre Você',
          prompt: 'Conte-me sobre você e sua vida diária',
          hints: [
            'De onde você é e onde mora agora?',
            'O que você faz no trabalho ou estuda?',
            'Como é um dia típico para você?',
            'Quais são suas principais responsabilidades ou atividades?'
          ]
        },
        {
          id: 'travel-places',
          icon: '🌍',
          title: 'Viagens & Lugares',
          prompt: 'Descreva um lugar que é especial para você',
          hints: [
            'Que lugar vem à mente? (cidade natal, lugar de férias, cidade favorita)',
            'Como é este lugar?',
            'Por que é significativo para você?',
            'O que você gosta de fazer lá?'
          ]
        },
        {
          id: 'interests-hobbies',
          icon: '🎨',
          title: 'Interesses & Hobbies',
          prompt: 'Fale sobre algo que você gosta de fazer',
          hints: [
            'Que hobby ou interesse você tem?',
            'Como você começou com isso?',
            'Com que frequência você faz esta atividade?',
            'O que você mais gosta nisso?'
          ]
        },
        {
          id: 'experiences-memories',
          icon: '💭',
          title: 'Experiências & Memórias',
          prompt: 'Compartilhe uma experiência memorável da sua vida',
          hints: [
            'Que experiência se destaca?',
            'Quando e onde aconteceu?',
            'Quem estava envolvido?',
            'Por que foi memorável?'
          ]
        },
        {
          id: 'future-goals',
          icon: '🎯',
          title: 'Futuro & Objetivos',
          prompt: 'Discuta seus planos ou sonhos para o futuro',
          hints: [
            'O que você espera alcançar?',
            'Que passos você está tomando em direção a este objetivo?',
            'Por que isso é importante para você?',
            'Como você imagina sua vida no futuro?'
          ]
        },
        {
          id: 'work-professional',
          icon: '💼',
          title: 'Trabalho & Vida Profissional',
          prompt: 'Fale sobre seu trabalho ou experiências profissionais',
          hints: [
            'Que tipo de trabalho você faz ou quer fazer?',
            'O que você acha desafiador ou gratificante no seu trabalho?',
            'Como você entrou no seu campo atual?',
            'Quais são seus objetivos ou aspirações profissionais?'
          ]
        }
      ]
    };

    return topics[language.toLowerCase()] || topics.english;
  };

  const topics = getTopics();

  // Handler for topic selection
  const handleTopicSelect = (topic: any) => {
    setSelectedTopic(topic);
    setShowTopicSelection(false);
    setShowPreparation(true);
    setStatus('preparation');
  };

  // Touch handlers for mobile swipe
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    if (touchStartX.current - touchEndX.current > 75) {
      // Swiped left - next topic
      setCurrentTopicIndex((prev) => (prev + 1) % topics.length);
    }
    if (touchStartX.current - touchEndX.current < -75) {
      // Swiped right - previous topic
      setCurrentTopicIndex((prev) => (prev - 1 + topics.length) % topics.length);
    }
  };

  // Handler for starting recording from preparation screen
  const handleStartFromPreparation = () => {
    setShowPreparation(false);
    promptRef.current = selectedTopic.prompt;
    startRecording();
  };

  // Handler for changing topic
  const handleChangeTopic = () => {
    setShowPreparation(false);
    setShowTopicSelection(true);
    setSelectedTopic(null);
    setStatus('topic-selection');
  };

  return (
    <div className="bg-white text-[#333333] rounded-lg p-8 w-full mx-auto space-y-8 border border-[#4ECFBF]/30 shadow-md">
      {/* Hidden audio player*/}
      {/* audioUrl && (
        <audio 
          ref={audioPlayerRef} 
          src={audioUrl} 
          onEnded={() => setIsAudioPlaying(false)}
          className="hidden" 
        />
      )}
      
      {/* Centered Guest User Mode Banner */}
      {!isAuthenticated() && (
        <div className={`relative overflow-hidden bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] rounded-xl shadow-lg mb-4 ${isMobile ? 'p-4' : 'p-6 mb-6'}`}>
          <div className="text-center">
            <div className="flex items-center justify-center mb-3">
              <div className="bg-white/20 p-2 rounded-full mr-3">
                <Mic className={`${isMobile ? 'h-4 w-4' : 'h-5 w-5'} text-white`} />
              </div>
              <h3 className={`${isMobile ? 'text-base' : 'text-lg'} font-bold text-white`}>Guest Mode</h3>
            </div>
            
            <div className={`text-white/90 ${isMobile ? 'text-xs' : 'text-sm'} leading-relaxed`}>
              {isMobile ? (
                <p>Free mode • Results not saved</p>
              ) : (
                <>
                  <p>You're using the free guest mode with limited features:</p>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>Results not saved to your profile</li>
                  </ul>
                </>
              )}
            </div>
            
            <div className={`${isMobile ? 'mt-2' : 'mt-4'} flex justify-center`}>
              <a 
                href="/auth/login" 
                className={`inline-flex items-center ${isMobile ? 'px-4 py-2 text-xs' : 'px-6 py-3 text-sm'} bg-white text-[#3AA8B1] font-medium rounded-lg shadow-md hover:bg-white/90 transition-all duration-200 group`}
              >
                Sign In
                <ChevronRight className={`ml-1 ${isMobile ? 'h-3 w-3' : 'h-4 w-4'} group-hover:translate-x-1 transition-transform`} />
              </a>
            </div>
          </div>
        </div>
      )}
      


      {/* TOPIC SELECTION SCREEN */}
      {status === 'topic-selection' && (
        <div className="space-y-6">
          <div className="text-center mb-8">
            <h2 className={`${isMobile ? 'text-2xl' : 'text-3xl'} font-bold text-[#333333] mb-3`}>
              Choose Your Speaking Topic
            </h2>
            <p className={`text-[#555555] ${isMobile ? 'text-sm' : 'text-lg'} max-w-2xl mx-auto`}>
              {isMobile ? 'Swipe to browse topics' : 'Select a topic you\'re comfortable discussing. This will help you speak more naturally and get better results.'}
            </p>
          </div>

          {isMobile ? (
            /* Mobile: Horizontal Swipe Cards with Arrow Navigation */
            <div className="relative px-12">
              {/* Left Arrow */}
              <button
                onClick={() => setCurrentTopicIndex((prev) => (prev - 1 + topics.length) % topics.length)}
                disabled={currentTopicIndex === 0}
                className={`absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  currentTopicIndex === 0
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed opacity-50'
                    : 'bg-white text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white shadow-lg hover:shadow-xl hover:scale-110'
                }`}
                aria-label="Previous topic"
              >
                <ChevronRight className="h-6 w-6 rotate-180" />
              </button>

              {/* Right Arrow */}
              <button
                onClick={() => setCurrentTopicIndex((prev) => (prev + 1) % topics.length)}
                disabled={currentTopicIndex === topics.length - 1}
                className={`absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  currentTopicIndex === topics.length - 1
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed opacity-50'
                    : 'bg-white text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white shadow-lg hover:shadow-xl hover:scale-110'
                }`}
                aria-label="Next topic"
              >
                <ChevronRight className="h-6 w-6" />
              </button>

              {/* Card Container */}
              <div 
                className="overflow-hidden"
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
              >
                <div 
                  className="flex transition-transform duration-300 ease-out"
                  style={{ transform: `translateX(-${currentTopicIndex * 100}%)` }}
                >
                  {topics.map((topic, index) => (
                    <div key={topic.id} className="w-full flex-shrink-0 px-2">
                      <button
                        onClick={() => handleTopicSelect(topic)}
                        className="w-full bg-gradient-to-br from-white to-[#F8FDFC] p-6 rounded-2xl border-2 border-[#4ECFBF]/20 active:border-[#4ECFBF] shadow-lg active:shadow-xl transition-all duration-200 text-left"
                      >
                        <div className="flex flex-col items-center text-center space-y-4">
                          <div className="text-6xl">{topic.icon}</div>
                          <h3 className="text-xl font-bold text-[#333333]">
                            {topic.title}
                          </h3>
                          <p className="text-sm text-[#555555]">
                            {topic.prompt}
                          </p>
                          <div className="flex items-center text-sm text-[#4ECFBF] font-medium pt-2">
                            <span>Tap to select</span>
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </div>
                        </div>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Topic Counter */}
              <div className="text-center mt-6">
                <p className="text-sm font-medium text-[#4ECFBF]">
                  {currentTopicIndex + 1} / {topics.length}
                </p>
              </div>
            </div>
          ) : (
            /* Desktop: Grid Layout */
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {topics.map((topic) => (
                <button
                  key={topic.id}
                  onClick={() => handleTopicSelect(topic)}
                  className="group bg-gradient-to-br from-white to-[#F8FDFC] p-6 rounded-2xl border-2 border-[#4ECFBF]/20 hover:border-[#4ECFBF] shadow-md hover:shadow-xl transition-all duration-300 transform hover:scale-105 text-left"
                >
                  <div className="flex items-start space-x-4">
                    <div className="text-4xl">{topic.icon}</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-[#333333] mb-2 group-hover:text-[#4ECFBF] transition-colors">
                        {topic.title}
                      </h3>
                      <p className="text-sm text-[#555555] mb-3">
                        {topic.prompt}
                      </p>
                      <div className="flex items-center text-xs text-[#4ECFBF] font-medium">
                        <span>Select topic</span>
                        <ChevronRight className="h-3 w-3 ml-1 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* PREPARATION SCREEN */}
      {status === 'preparation' && selectedTopic && (
        <div className="space-y-4">
          <button
            onClick={handleChangeTopic}
            className="flex items-center text-[#4ECFBF] hover:text-[#3AA8B1] transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            <span>Change Topic</span>
          </button>

          <div className={`bg-gradient-to-br from-[#F0FDFB] to-white ${isMobile ? 'p-6' : 'p-8'} rounded-2xl border-2 border-[#4ECFBF] shadow-lg`}>
            <div className="flex items-center mb-6">
              <div className={`${isMobile ? 'text-5xl mr-3' : 'text-5xl mr-4'}`}>{selectedTopic.icon}</div>
              <div>
                <h2 className={`${isMobile ? 'text-xl' : 'text-2xl'} font-bold text-[#333333]`}>
                  {selectedTopic.title}
                </h2>
                {!isMobile && (
                  <p className="text-lg text-[#555555] mt-1">
                    {selectedTopic.prompt}
                  </p>
                )}
              </div>
            </div>

            <div className={`bg-white ${isMobile ? 'p-4' : 'p-6'} rounded-xl border border-[#4ECFBF]/30 mb-6`}>
              <h3 className={`${isMobile ? 'text-base' : 'text-lg'} font-semibold text-[#333333] ${isMobile ? 'mb-3' : 'mb-4'} flex items-center`}>
                <Target className={`${isMobile ? 'h-4 w-4' : 'h-5 w-5'} mr-2 text-[#4ECFBF]`} />
                Things you can talk about:
              </h3>
              <ul className={`${isMobile ? 'space-y-2' : 'space-y-3'}`}>
                {selectedTopic.hints.map((hint: string, index: number) => (
                  <li key={index} className={`flex items-start ${isMobile ? 'space-x-2' : 'space-x-3'}`}>
                    <div className={`${isMobile ? 'w-5 h-5' : 'w-6 h-6'} bg-[#4ECFBF] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5`}>
                      <span className="text-white text-xs font-bold">{index + 1}</span>
                    </div>
                    <p className={`${isMobile ? 'text-sm' : 'text-base'} text-[#555555]`}>{hint}</p>
                  </li>
                ))}
              </ul>
            </div>

            {!isMobile && (
              <div className="bg-[#FFFBEB] p-4 rounded-lg border border-[#FFD63A]/30 mb-6">
                <p className="text-sm text-[#555555]">
                  💡 <strong>Tip:</strong> Take a moment to think about what you want to say. 
                  You don't need to answer all the questions - just speak naturally about the topic.
                </p>
              </div>
            )}

            {/* Animated Microphone Button for Both Mobile and Desktop */}
            <div className="flex flex-col items-center">
              <div className="relative mb-4 group">
                {!isMobile && (
                  <>
                    <div className="absolute -inset-6 bg-gradient-to-r from-[#4ECFBF]/20 via-[#3AA8B1]/20 to-[#4ECFBF]/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500 animate-pulse"></div>
                    <div className="absolute -inset-3 bg-gradient-to-r from-[#4ECFBF]/30 to-[#3AA8B1]/30 rounded-full blur-lg opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
                  </>
                )}
                {isMobile && (
                  <div className="absolute -inset-3 bg-gradient-to-r from-[#4ECFBF]/30 to-[#3AA8B1]/30 rounded-full blur-lg opacity-75"></div>
                )}
                <button
                  onClick={handleStartFromPreparation}
                  className={`relative ${isMobile ? 'w-32 h-32' : 'w-40 h-40'} rounded-full flex items-center justify-center bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] text-white shadow-2xl hover:shadow-3xl transform hover:scale-110 transition-all duration-300 group-hover:from-[#5CCFC0] group-hover:to-[#4BB8C1] border-0 cursor-pointer ${isMobile ? 'active:scale-95' : ''}`}
                  type="button"
                >
                  <Mic className={`${isMobile ? 'h-12 w-12' : 'h-14 w-14'} group-hover:scale-110 transition-transform duration-300`} />
                </button>
                
                {/* Pulse rings */}
                <div className="absolute inset-0 rounded-full border-2 border-[#4ECFBF]/30 animate-ping pointer-events-none"></div>
                <div className={`absolute ${isMobile ? 'inset-1' : 'inset-2'} rounded-full border-2 border-[#4ECFBF]/20 animate-ping pointer-events-none`} style={{animationDelay: '0.5s'}}></div>
              </div>
              
              <p className={`${isMobile ? 'text-sm' : 'text-base'} font-medium text-[#333333] text-center`}>
                {isMobile ? 'Tap to start recording' : 'Click to start recording'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Assessment Interface - Mobile-First Redesigned Layout */}
      {status === 'idle' && (
        <div className={`${isMobile ? 'space-y-4' : 'grid grid-cols-1 lg:grid-cols-3 gap-8'}`}>
          {/* Primary Recording Section - Compact for Mobile */}
          <div className={`${isMobile ? 'order-1' : 'lg:col-span-2 order-1 lg:order-1'}`}>
            <div className={`flex flex-col items-center justify-center ${isMobile ? 'p-6' : 'p-12'} bg-gradient-to-br from-white via-[#F8FDFC] to-[#F0FDFB] rounded-2xl shadow-xl border border-[#4ECFBF]/20 relative overflow-hidden`}>
              {/* Background decoration - smaller on mobile */}
              {!isMobile && (
                <>
                  <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-[#4ECFBF]/10 to-transparent rounded-full -mr-16 -mt-16"></div>
                  <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-[#FFD63A]/10 to-transparent rounded-full -ml-12 -mb-12"></div>
                </>
              )}
              
              <div className={`text-center ${isMobile ? 'mb-4' : 'mb-8'} relative z-10`}>
                <h2 className={`${isMobile ? 'text-xl' : 'text-3xl'} font-bold text-[#333333] ${isMobile ? 'mb-2' : 'mb-4'}`}>
                  Ready to assess your {language} skills?
                </h2>
                <p className={`text-[#555555] ${isMobile ? 'text-sm' : 'text-lg'} max-w-lg mx-auto leading-relaxed`}>
                  {isMobile ? (
                    <>Tap the mic and speak for <span className="font-semibold text-[#4ECFBF]">{formatTime(getAssessmentDuration(isAuthenticated()))}</span></>
                  ) : (
                    <>Press the microphone button below and speak naturally in {language} for {isAuthenticated() ? 'up to ' : ''}
                    <span className="font-semibold text-[#4ECFBF]">{formatTime(getAssessmentDuration(isAuthenticated()))}</span>.</>
                  )}
                </p>
              </div>
              
              {/* Enhanced Microphone Button - Smaller on Mobile */}
              <div className={`relative ${isMobile ? 'mb-4' : 'mb-8'} group`}>
                {!isMobile && (
                  <>
                    <div className="absolute -inset-6 bg-gradient-to-r from-[#4ECFBF]/20 via-[#3AA8B1]/20 to-[#4ECFBF]/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500 animate-pulse"></div>
                    <div className="absolute -inset-3 bg-gradient-to-r from-[#4ECFBF]/30 to-[#3AA8B1]/30 rounded-full blur-lg opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
                  </>
                )}
                <button
                  onClick={startRecording}
                  className={`relative ${isMobile ? 'w-24 h-24' : 'w-40 h-40'} rounded-full flex items-center justify-center bg-gradient-to-r from-[#4ECFBF] to-[#3AA8B1] text-white shadow-2xl hover:shadow-3xl transform hover:scale-110 transition-all duration-300 group-hover:from-[#5CCFC0] group-hover:to-[#4BB8C1] border-0 cursor-pointer`}
                  type="button"
                >
                  <Mic className={`${isMobile ? 'h-8 w-8' : 'h-14 w-14'} group-hover:scale-110 transition-transform duration-300`} />
                </button>
                
                {/* Pulse rings - smaller on mobile */}
                <div className={`absolute inset-0 rounded-full border-2 border-[#4ECFBF]/30 animate-ping pointer-events-none`}></div>
                <div className={`absolute ${isMobile ? 'inset-1' : 'inset-2'} rounded-full border-2 border-[#4ECFBF]/20 animate-ping pointer-events-none`} style={{animationDelay: '0.5s'}}></div>
              </div>
              
              {/* Status Indicator - Compact on Mobile */}
              <div className={`flex items-center justify-center space-x-2 ${isMobile ? 'text-xs' : 'text-sm'} text-[#555555] bg-white/80 backdrop-blur-sm ${isMobile ? 'px-4 py-2' : 'px-6 py-3'} rounded-lg shadow-md border border-[#4ECFBF]/20`}>
                <div className={`${isMobile ? 'w-2 h-2' : 'w-3 h-3'} rounded-full bg-[#4ECFBF] animate-pulse shadow-sm`}></div>
                <p className="font-medium">
                  {isMobile ? 'Ready' : 'Microphone ready'} • {isAuthenticated() ? 'Up to ' : ''}{formatTime(getAssessmentDuration(isAuthenticated()))}
                </p>
              </div>
              
              {/* Quick tip - Only show on desktop */}
              {!isMobile && (
                <div className="mt-6 text-center">
                  <p className="text-sm text-[#777777] italic">💡 Speak about any topic you're comfortable with</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Tips Section - Collapsible on Mobile */}
          <div className={`${isMobile ? 'order-2' : 'lg:col-span-1 order-2 lg:order-2'}`}>
            {isMobile ? (
              /* Mobile: Compact Tips */
              <div className="bg-gradient-to-r from-[#FFFBEB] to-[#FFF8E1] rounded-xl p-4 shadow-md border border-[#FFD63A]/30">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <div className="w-6 h-6 bg-[#FFD63A] rounded-lg flex items-center justify-center mr-2 shadow-sm">
                      <Target className="h-4 w-4 text-[#333333]" />
                    </div>
                    <h3 className="text-sm font-bold text-[#333333]">Quick Tips</h3>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-[#333333]">
                  <div className="bg-white/70 p-2 rounded-lg border border-[#FFD63A]/20 text-center">
                    <p className="text-xs font-medium">🔇 Quiet space</p>
                  </div>
                  <div className="bg-white/70 p-2 rounded-lg border border-[#FFD63A]/20 text-center">
                    <p className="text-xs font-medium">💬 Speak naturally</p>
                  </div>
                  <div className="bg-white/70 p-2 rounded-lg border border-[#FFD63A]/20 text-center">
                    <p className="text-xs font-medium">📚 Varied vocab</p>
                  </div>
                  <div className="bg-white/70 p-2 rounded-lg border border-[#FFD63A]/20 text-center">
                    <p className="text-xs font-medium">😌 Stay relaxed</p>
                  </div>
                </div>
              </div>
            ) : (
              /* Desktop: Full Tips Sidebar */
              <div className="bg-gradient-to-br from-[#FFFBEB] via-[#FFF8E1] to-[#FFFBEB] rounded-2xl p-6 shadow-lg border border-[#FFD63A]/30 h-full">
                <div className="flex items-center mb-4">
                  <div className="w-8 h-8 bg-[#FFD63A] rounded-lg flex items-center justify-center mr-3 shadow-sm">
                    <Target className="h-5 w-5 text-[#333333]" />
                  </div>
                  <h3 className="text-lg font-bold text-[#333333]">Assessment Tips</h3>
                </div>
                
                <div className="space-y-3 text-[#333333]">
                  <div className="bg-white/70 backdrop-blur-sm p-3 rounded-xl border border-[#FFD63A]/20 shadow-sm hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-start space-x-2">
                      <div className="w-6 h-6 bg-[#FFD63A] rounded-full flex items-center justify-center mt-0.5 shadow-sm">
                        <span className="text-xs font-bold text-[#333333]">1</span>
                      </div>
                      <p className="text-sm leading-relaxed">Find a <strong>quiet space</strong> with minimal background noise</p>
                    </div>
                  </div>
                  
                  <div className="bg-white/70 backdrop-blur-sm p-3 rounded-xl border border-[#FFD63A]/20 shadow-sm hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-start space-x-2">
                      <div className="w-6 h-6 bg-[#FFD63A] rounded-full flex items-center justify-center mt-0.5 shadow-sm">
                        <span className="text-xs font-bold text-[#333333]">2</span>
                      </div>
                      <p className="text-sm leading-relaxed">Speak <strong>naturally</strong> about topics you enjoy</p>
                    </div>
                  </div>
                  
                  <div className="bg-white/70 backdrop-blur-sm p-3 rounded-xl border border-[#FFD63A]/20 shadow-sm hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-start space-x-2">
                      <div className="w-6 h-6 bg-[#FFD63A] rounded-full flex items-center justify-center mt-0.5 shadow-sm">
                        <span className="text-xs font-bold text-[#333333]">3</span>
                      </div>
                      <p className="text-sm leading-relaxed">Use <strong>varied vocabulary</strong> and sentence structures</p>
                    </div>
                  </div>
                  
                  <div className="bg-white/70 backdrop-blur-sm p-3 rounded-xl border border-[#FFD63A]/20 shadow-sm hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-start space-x-2">
                      <div className="w-6 h-6 bg-[#FFD63A] rounded-full flex items-center justify-center mt-0.5 shadow-sm">
                        <span className="text-xs font-bold text-[#333333]">4</span>
                      </div>
                      <p className="text-sm leading-relaxed"><strong>Relax and be yourself</strong> for accurate results</p>
                    </div>
                  </div>
                </div>
                
                {/* Encouragement section */}
                <div className="mt-6 p-4 bg-gradient-to-r from-[#4ECFBF]/10 to-[#FFD63A]/10 rounded-xl border border-[#4ECFBF]/20">
                  <div className="flex items-center mb-2">
                    <ThumbsUp className="h-4 w-4 text-[#4ECFBF] mr-2" />
                    <span className="text-sm font-semibold text-[#333333]">You've got this!</span>
                  </div>
                  <p className="text-xs text-[#555555] leading-relaxed">
                    Our AI will analyze your pronunciation, fluency, vocabulary, and grammar to provide personalized feedback.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Recording State - Animated Transition from Microphone */}
      {status === 'recording' && (
        <div className="bg-white rounded-2xl shadow-xl border border-[#4ECFBF]/20 p-8 animate-in fade-in duration-500">
          {/* Show selected topic at top */}
          {selectedTopic && (
            <div className="bg-[#F0FDFB] p-4 rounded-xl border border-[#4ECFBF]/30 mb-6">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">{selectedTopic.icon}</span>
                <h3 className="text-lg font-bold text-[#333333]">{selectedTopic.title}</h3>
              </div>
              <p className="text-sm text-[#555555] italic">{selectedTopic.prompt}</p>
            </div>
          )}
          
          <div className="flex flex-col md:flex-row items-center justify-between mb-8">
            <div className="flex items-center mb-6 md:mb-0">
              <div className="relative">
                <div className="absolute inset-0 bg-[#F75A5A]/30 rounded-full blur-lg animate-pulse"></div>
                <div className="relative w-16 h-16 flex items-center justify-center bg-[#F75A5A] rounded-full shadow-lg">
                  <Mic className="h-8 w-8 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center shadow-md">
                  <div className="w-2 h-2 rounded-full bg-[#F75A5A] animate-pulse"></div>
                </div>
              </div>
              <div className="ml-6">
                <h3 className="text-xl font-bold text-[#333333]">Recording...</h3>
                <p className="text-[#555555]">Speak naturally</p>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-[#F75A5A]/10 rounded-xl blur-md"></div>
              <div className="relative text-4xl font-bold text-[#F75A5A] bg-white px-6 py-3 rounded-xl shadow-md border border-[#F75A5A]/20">
                {formatTime(timer)}
              </div>
            </div>
          </div>
          
          <div className="mb-6">
            <div className="flex justify-between text-sm text-[#555555] mb-2">
              <span>0:00</span>
              <span>{formatTime(initialDuration)}</span>
            </div>
            <Progress 
              value={(initialDuration - timer) / initialDuration * 100} 
              className="h-4 bg-gray-100 rounded-full" 
              indicatorClassName="bg-gradient-to-r from-[#F75A5A] to-[#FF8A8A] rounded-full" 
            />
          </div>
          
          <div className="flex justify-center mt-4">
            {isAuthenticated() ? (
              <Button 
                onClick={stopRecording}
                disabled={!canStopRecording}
                className={`font-medium px-6 py-3 rounded-lg flex items-center space-x-2 shadow-md transition-all duration-300 ${
                  canStopRecording 
                    ? 'bg-white hover:bg-gray-100 text-[#F75A5A] border border-[#F75A5A]/30' 
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed border border-gray-300'
                }`}
              >
                <Square className="h-5 w-5" />
                <span>{canStopRecording ? 'Stop Recording' : 'Recording...'}</span>
              </Button>
            ) : (
              <div className="bg-[#4ECFBF]/10 backdrop-blur-sm px-4 py-2 rounded-lg border border-[#4ECFBF]/30 inline-block">
                <p className="text-[#555555] text-sm">
                  🎯 Recording will stop automatically when time reaches zero
                </p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Processing State - Mobile Optimized */}
      {status === 'processing' && (
        <div className={`relative overflow-hidden bg-gradient-to-br from-[#FFF8E1] to-[#FFEDB3] ${isMobile ? 'p-4' : 'p-8'} rounded-xl shadow-lg`}>
          {/* Background decoration - only show on desktop */}
          {!isMobile && (
            <div className="absolute inset-0 opacity-10">
              <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">
                    <circle cx="10" cy="10" r="1.5" fill="#FFD63A" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#dots)" />
              </svg>
            </div>
          )}
          
          <div className={`flex flex-col items-center justify-center ${isMobile ? 'py-4' : 'py-8'} relative z-10`}>
            <div className={`relative ${isMobile ? 'mb-4' : 'mb-8'}`}>
              {!isMobile && <div className="absolute -inset-3 bg-[#FFD63A]/30 rounded-full blur-lg"></div>}
              <div className="relative">
                <div className={`${isMobile ? 'w-16 h-16 border-3' : 'w-24 h-24 border-4'} border-[#FFD63A] border-t-[#FFD63A]/20 rounded-full animate-spin shadow-lg`}></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className={`${isMobile ? 'w-10 h-10' : 'w-16 h-16'} bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center`}>
                    <Target className={`${isMobile ? 'h-5 w-5' : 'h-8 w-8'} text-[#FFD63A]`} />
                  </div>
                </div>
              </div>
            </div>
            
            <h3 className={`${isMobile ? 'text-lg' : 'text-2xl'} font-bold text-[#333333] ${isMobile ? 'mb-3' : 'mb-4'} bg-white/80 backdrop-blur-sm ${isMobile ? 'px-4 py-2' : 'px-6 py-3'} rounded-xl shadow-md border border-[#FFD63A]/30 text-center`}>
              Analyzing your speaking skills...
            </h3>
            
            <div className={`${isMobile ? 'grid grid-cols-2 gap-2 max-w-xs' : 'grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl'} w-full ${isMobile ? 'mb-4' : 'mb-6'}`}>
              {['Pronunciation', 'Fluency', 'Vocabulary', 'Grammar'].map((skill, index) => (
                <div key={skill} className={`bg-white/80 backdrop-blur-sm ${isMobile ? 'p-2' : 'p-4'} rounded-lg border border-[#FFD63A]/30 shadow-sm flex items-center ${isMobile ? 'justify-center' : ''}`}>
                  <div className={`${isMobile ? 'w-2 h-2' : 'w-3 h-3'} rounded-full bg-[#FFD63A] ${isMobile ? 'mr-2' : 'mr-3'} animate-pulse`} style={{ animationDelay: `${index * 0.2}s` }}></div>
                  <span className={`font-medium text-[#333333] ${isMobile ? 'text-xs' : 'text-sm'}`}>{skill}</span>
                </div>
              ))}
            </div>
            
            <p className={`text-[#555555] text-center ${isMobile ? 'max-w-xs text-xs' : 'max-w-md text-sm'} bg-white/80 backdrop-blur-sm ${isMobile ? 'p-3' : 'p-4'} rounded-lg border border-[#FFD63A]/30 shadow-md`}>
              Our AI is carefully evaluating your {language} speaking skills to provide an accurate assessment of your current proficiency level.
            </p>
          </div>
        </div>
      )}
      
      {/* Assessment Results*/}
      {status === 'complete' && assessment && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {isAuthenticated() ? (
            <>
              {/* Left Column: General Information - Authenticated User*/}
              <div className="space-y-6">
                {/* Playback Controls - Commented out as requested*/}
                {/* audioUrl && (
                  <div className="flex items-center justify-center space-x-4 bg-[#F0FDFB] p-3 rounded-lg border border-[#4ECFBF] shadow-md">
                    <Button 
                      onClick={handlePlayAudio}
                      className="bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white rounded-full w-12 h-12 flex items-center justify-center shadow-md transition-all duration-300"
                    >
                      {isAudioPlaying ? <Square className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                    </Button>
                    <div className="text-[#333333] text-lg">Listen to your recording</div>
                  </div>
                )}
                
                {/* Recommended Level*/}
                <div className="bg-[#F0FDFB] p-6 rounded-lg text-center border border-[#4ECFBF] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Recommended Level</h3>
                  <div className="text-5xl font-bold text-[#333333] mb-3">{assessment.recommended_level}</div>
                  <div className="inline-block bg-[#4ECFBF] px-4 py-2 rounded-full text-white text-sm font-medium shadow-md">
                    Confidence: {assessment.confidence.toFixed(1)}%
                  </div>
                </div>
                
                {/* Overall Score*/}
                <div className="bg-[#FFFBEB] p-6 rounded-lg border border-[#FFD63A] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Overall Score</h3>
                  <div className="flex items-center space-x-4">
                    <div className="text-4xl font-bold text-[#333333] bg-[#FFD63A] rounded-lg px-4 py-2 shadow-md">
                      {assessment.overall_score.toFixed(1)}
                    </div>
                    <Progress 
                      value={assessment.overall_score} 
                      className="h-4 bg-white flex-1 rounded-full border border-[#FFD63A]/30"
                      indicatorClassName={`${assessment.overall_score < 25 ? 'bg-[#F75A5A]' : 
                        assessment.overall_score < 50 ? 'bg-[#FFD63A]' : 
                        assessment.overall_score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                    />
                  </div>
                </div>
                
                {/* Strengths*/}
                <div className="bg-[#F0FDFB] p-5 rounded-lg border border-[#4ECFBF] shadow-md">
                  <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                    <ThumbsUp className="h-5 w-5 mr-2 text-[#4ECFBF]" /> Strengths
                  </h3>
                  <ul className="space-y-3">
                    {assessment.strengths.map((strength, index) => (
                      <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#4ECFBF]/30 shadow-sm">
                        <div className="bg-[#4ECFBF] rounded-full p-1 mt-0.5 flex-shrink-0">
                          <Check className="h-4 w-4 text-white" />
                        </div>
                        <p className="text-[#333333]">{strength}</p>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Transcription*/}
                <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Your Speech</h3>
                  <p className="text-[#333333] bg-white p-4 rounded-lg border border-[#F75A5A]/30 shadow-inner">
                    {assessment.recognized_text || "No speech detected"}
                  </p>
                </div>
              </div>
              
              {/* Right Column: Detailed Assessment - Authenticated User*/}
              <div className="space-y-6">
                {/* Skill Scores*/}
                <div className="bg-[#F8F9FA] p-6 rounded-lg border border-gray-200 shadow-md overflow-auto">
                  <h3 className="text-lg text-[#333333] mb-3 font-medium">Skill Breakdown</h3>
                  
                  <div className="space-y-4 max-h-[600px] overflow-auto pr-2">
                    {/* Pronunciation*/}
                    <div className="bg-white p-3 rounded-lg border border-[#4ECFBF] shadow-sm">
                      <div className="flex justify-between mb-2">
                        <span className="text-[#333333] font-medium">Pronunciation</span>
                        <span className={`text-white px-3 py-1 rounded-md font-medium shadow-sm ${assessment.pronunciation.score < 25 ? 'bg-[#F75A5A]' : 
                          assessment.pronunciation.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                          assessment.pronunciation.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}>
                          {assessment.pronunciation.score.toFixed(1)}
                        </span>
                      </div>
                      <Progress 
                        value={assessment.pronunciation.score} 
                        className="h-3 bg-gray-100 rounded-full"
                        indicatorClassName={`${assessment.pronunciation.score < 25 ? 'bg-[#F75A5A]' : 
                          assessment.pronunciation.score < 50 ? 'bg-[#FFD63A]' : 
                          assessment.pronunciation.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                      />
                      <p className="text-[#555555] mt-1 text-sm bg-[#F0FDFB] p-2 rounded-md border border-[#4ECFBF]/20">{assessment.pronunciation.feedback}</p>
                    </div>
                    
                    {/* Vocabulary*/}
                    <div className="bg-white p-3 rounded-lg border border-[#FFD63A] shadow-sm">
                      <div className="flex justify-between mb-2">
                        <span className="text-[#333333] font-medium">Vocabulary</span>
                        <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.vocabulary.score < 25 ? 'bg-[#F75A5A] text-white' : 
                          assessment.vocabulary.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                          assessment.vocabulary.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                          {assessment.vocabulary.score.toFixed(1)}
                        </span>
                      </div>
                      <Progress 
                        value={assessment.vocabulary.score} 
                        className="h-3 bg-gray-100 rounded-full"
                        indicatorClassName={`${assessment.vocabulary.score < 25 ? 'bg-[#F75A5A]' : 
                          assessment.vocabulary.score < 50 ? 'bg-[#FFD63A]' : 
                          assessment.vocabulary.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                      />
                      <p className="text-[#555555] mt-1 text-sm bg-[#FFFBEB] p-2 rounded-md border border-[#FFD63A]/20">{assessment.vocabulary.feedback}</p>
                    </div>
                    
                    {/* Grammar*/}
                    <div className="bg-white p-3 rounded-lg border border-[#F75A5A] shadow-sm">
                      <div className="flex justify-between mb-2">
                        <span className="text-[#333333] font-medium">Grammar</span>
                        <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.grammar.score < 25 ? 'bg-[#F75A5A] text-white' : 
                          assessment.grammar.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                          assessment.grammar.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                          {assessment.grammar.score.toFixed(1)}
                        </span>
                      </div>
                      <Progress 
                        value={assessment.grammar.score} 
                        className="h-3 bg-gray-100 rounded-full"
                        indicatorClassName={`${assessment.grammar.score < 25 ? 'bg-[#F75A5A]' : 
                          assessment.grammar.score < 50 ? 'bg-[#FFD63A]' : 
                          assessment.grammar.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                      />
                      <p className="text-[#555555] mt-1 text-sm bg-[#FFF8F8] p-2 rounded-md border border-[#F75A5A]/20">{assessment.grammar.feedback}</p>
                    </div>
                    
                    {/* Fluency*/}
                    <div className="bg-white p-3 rounded-lg border border-[#4ECFBF] shadow-sm">
                      <div className="flex justify-between mb-2">
                        <span className="text-[#333333] font-medium">Fluency</span>
                        <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.fluency.score < 25 ? 'bg-[#F75A5A] text-white' : 
                          assessment.fluency.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                          assessment.fluency.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                          {assessment.fluency.score.toFixed(1)}
                        </span>
                      </div>
                      <Progress 
                        value={assessment.fluency.score} 
                        className="h-3 bg-gray-100 rounded-full"
                        indicatorClassName={`${assessment.fluency.score < 25 ? 'bg-[#F75A5A]' : 
                          assessment.fluency.score < 50 ? 'bg-[#FFD63A]' : 
                          assessment.fluency.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                      />
                      <p className="text-[#555555] mt-1 text-sm bg-[#F0FDFB] p-2 rounded-md border border-[#4ECFBF]/20">{assessment.fluency.feedback}</p>
                    </div>
                    
                    {/* Coherence*/}
                    <div className="bg-white p-3 rounded-lg border border-[#FFD63A] shadow-sm">
                      <div className="flex justify-between mb-2">
                        <span className="text-[#333333] font-medium">Coherence</span>
                        <span className={`px-3 py-1 rounded-md font-medium shadow-sm ${assessment.coherence.score < 25 ? 'bg-[#F75A5A] text-white' : 
                          assessment.coherence.score < 50 ? 'bg-[#FFD63A] text-[#333333]' : 
                          assessment.coherence.score < 75 ? 'bg-[#4ECFBF] text-white' : 'bg-[#4CAF50] text-white'}`}>
                          {assessment.coherence.score.toFixed(1)}
                        </span>
                      </div>
                      <Progress 
                        value={assessment.coherence.score} 
                        className="h-3 bg-gray-100 rounded-full"
                        indicatorClassName={`${assessment.coherence.score < 25 ? 'bg-[#F75A5A]' : 
                          assessment.coherence.score < 50 ? 'bg-[#FFD63A]' : 
                          assessment.coherence.score < 75 ? 'bg-[#4ECFBF]' : 'bg-[#4CAF50]'}`}
                      />
                      <p className="text-[#555555] mt-1 text-sm bg-[#FFFBEB] p-2 rounded-md border border-[#FFD63A]/20">{assessment.coherence.feedback}</p>
                    </div>
                  </div>
          </div>
          
            {/* Feedback and Next Steps*/}
            {/* Next Steps*/}
            <div className="bg-[#FFFBEB] p-6 rounded-lg border border-[#FFD63A] shadow-md">
              <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                <Footprints className="h-5 w-5 mr-2 text-[#FFD63A]" /> Next Steps
              </h3>
              <ul className="space-y-3">
                {assessment.next_steps.map((step, index) => (
                  <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
                    <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 flex-shrink-0">
                      <span className="block w-4 h-4 text-[#333333] text-center font-bold text-xs">{index + 1}</span>
                    </div>
                    <p className="text-[#333333]">{step}</p>
                  </li>
                ))}
              </ul>
            </div>
              </div>
            </>
          ) : (
            <>
              {/* Left Column: Limited Information - Guest User*/}
              <div className="space-y-6">
                {/* Playback Controls - Commented out as requested*/}
                {/* audioUrl && (
                  <div className="flex items-center justify-center space-x-4 bg-[#F0FDFB] p-3 rounded-lg border border-[#4ECFBF] shadow-md">
                    <Button 
                      onClick={handlePlayAudio}
                      className="bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white rounded-full w-12 h-12 flex items-center justify-center shadow-md transition-all duration-300"
                    >
                      {isAudioPlaying ? <Square className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                    </Button>
                    <div className="text-[#333333] text-lg">Listen to your recording</div>
                  </div>
                )}
                
                {/* Recommended Level*/}
                <div className="bg-[#F0FDFB] p-6 rounded-lg text-center border border-[#4ECFBF] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Recommended Level</h3>
                  <div className="text-5xl font-bold text-[#333333] mb-3">{assessment.recommended_level}</div>
                </div>
                
                {/* Strengths*/}
                <div className="bg-[#F0FDFB] p-5 rounded-lg border border-[#4ECFBF] shadow-md">
                  <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                    <ThumbsUp className="h-5 w-5 mr-2 text-[#4ECFBF]" /> Strengths
                  </h3>
                  <ul className="space-y-3">
                    {assessment.strengths.map((strength, index) => (
                      <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#4ECFBF]/30 shadow-sm">
                        <div className="bg-[#4ECFBF] rounded-full p-1 mt-0.5 flex-shrink-0">
                          <Check className="h-4 w-4 text-white" />
                        </div>
                        <p className="text-[#333333]">{strength}</p>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Transcription*/}
                <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
                  <h3 className="text-xl text-[#333333] mb-3 font-medium">Your Speech</h3>
                  <p className="text-[#333333] bg-white p-4 rounded-lg border border-[#F75A5A]/30 shadow-inner">
                    {assessment.recognized_text || "No speech detected"}
                  </p>
                </div>


              </div>
              
              {/* Right Column: Feedback and Next Steps - Guest User*/}
              <div className="space-y-6">
                {/* Areas for Improvement*/}
                <div className="bg-[#FFF8F8] p-6 rounded-lg border border-[#F75A5A] shadow-md">
                  <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                    <Target className="h-5 w-5 mr-2 text-[#F75A5A]" /> Areas for Improvement
                  </h3>
                  <ul className="space-y-3">
                    {assessment.areas_for_improvement.map((area, index) => (
                      <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#F75A5A]/30 shadow-sm">
                        <div className="bg-[#F75A5A] rounded-full p-1 mt-0.5 flex-shrink-0">
                          <ArrowUpRight className="h-4 w-4 text-white" />
                        </div>
                        <p className="text-[#333333]">{area}</p>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Next Steps*/}
                <div className="bg-[#FFFBEB] p-6 rounded-lg border border-[#FFD63A] shadow-md">
                  <h3 className="text-lg text-[#333333] mb-3 font-medium flex items-center">
                    <Footprints className="h-5 w-5 mr-2 text-[#FFD63A]" /> Next Steps
                  </h3>
                  <ul className="space-y-3">
                    {assessment.next_steps.map((step, index) => (
                      <li key={index} className="flex items-start space-x-3 bg-white p-3 rounded-lg border border-[#FFD63A]/30 shadow-sm">
                        <div className="bg-[#FFD63A] rounded-full p-1 mt-0.5 flex-shrink-0">
                          <span className="block w-4 h-4 text-[#333333] text-center font-bold text-xs">{index + 1}</span>
                        </div>
                        <p className="text-[#333333]">{step}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}
          
          {/* Action Buttons - Centered at the bottom*/}
          <div className="col-span-1 lg:col-span-2">
            <div className="flex flex-col sm:flex-row justify-center gap-4 mt-6">
              <Button 
                onClick={handleTryAgain}
                className="bg-[#4ECFBF] hover:bg-[#5CCFC0] text-white font-medium px-6 py-3 rounded-lg flex items-center justify-center space-x-2 shadow-md transition-all duration-300 flex-1"
              >
                <RotateCw className="h-5 w-5" />
                <span>New Assessment</span>
              </Button>
              
              <Button 
                onClick={handleSelectLevel}
                className="bg-[#FFD63A] hover:bg-[#ECC235] text-[#333333] font-medium px-6 py-3 rounded-lg flex items-center justify-center space-x-2 shadow-md transition-all duration-300 flex-1"
              >
                <Volume2 className="h-5 w-5" />
                <span>{isAuthenticated() ? 'Save & Proceed' : 'Proceed to Speak'}</span>
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* Error messages are now handled by the top-right notification system */}
      
      {/* Manual Level Selection button removed*/}
      
      {/* Bottom-right notification for optimal recording duration */}
      {showOptimalNotification && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-right duration-300">
          <div className="bg-white border-l-4 border-[#4ECFBF] rounded-lg shadow-xl p-4 max-w-sm">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center">
                  <Check className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">
                  Speaking duration is optimal!
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  You can now stop recording for analysis
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Learning Plan Modal*/}
      {assessment && (
        <EnhancedLearningPlanModal 
          isOpen={showLearningPlanModal}
          onClose={handleLearningPlanModalClose}
          proficiencyLevel={assessment.recommended_level}
          language={language}
          onPlanCreated={handlePlanCreated}
          assessmentData={assessment}
        />
      )}
    </div>
  );
}
