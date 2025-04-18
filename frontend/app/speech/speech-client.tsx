'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { RealtimeMessage } from '@/lib/types';
import { useRouter } from 'next/navigation';
import SentenceConstructionAssessment from '@/components/sentence-construction-assessment';

interface SpeechClientProps {
  language: string;
  level: string;
  topic?: string;
  userPrompt?: string;
}

export default function SpeechClient({ language, level, topic, userPrompt }: SpeechClientProps) {
  // Moving the console.log out of the component body to prevent excessive logging
  const initialRenderRef = useRef(true);
  
  const router = useRouter();
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(false);
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const micPermissionDeniedRef = useRef(false);
  
  // Language alert state - simplified
  const [showLanguageAlert, setShowLanguageAlert] = useState(false);
  const languageAlertTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const globalSafetyTimeoutRef = useRef<NodeJS.Timeout | null>(null); // Backup safety mechanism
  
  // Add state for transcript processing
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  // State to track if conversation is paused for review (not ended)
  const [isPaused, setIsPaused] = useState<boolean>(false);
  // Ref to store conversation history when pausing
  const conversationHistoryRef = useRef<string>('');
  // State for exercise type in sentence construction assessment
  const [exerciseType, setExerciseType] = useState<string>('free');
  
  // Only log on initial render, not on every re-render
  useEffect(() => {
    if (initialRenderRef.current) {
      console.log('SpeechClient initializing with language:', language, 'level:', level, 'topic:', topic, 'at:', new Date().toISOString());
      if (topic === 'custom' && userPrompt) {
        console.log('Custom topic prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
      }
      initialRenderRef.current = false;
    }
  }, [language, level, topic, userPrompt]);
  
  // Add a useEffect to track component mounting and unmounting
  useEffect(() => {
    console.log('SpeechClient component mounted at:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Store a flag to detect if the component unmounts unexpectedly
    const mountTimestamp = Date.now();
    sessionStorage.setItem('speechClientMountTime', mountTimestamp.toString());
    
    return () => {
      console.log('SpeechClient component unmounted at:', new Date().toISOString());
      console.log('Component was mounted for:', (Date.now() - mountTimestamp) / 1000, 'seconds');
      sessionStorage.removeItem('speechClientMountTime');
    };
  }, []);
  
  // Initialize the realtime service and handle messages
  const { isRecording, messages, error, toggleConversation, stopConversation, startConversation, initialize, getFormattedConversationHistory } = useRealtime();
  
  // Process messages for display and deduplicate assistant messages
  const processedMessages = useMemo(() => {
    // First, map the messages to add consistent IDs
    const mappedMessages = messages.map((message, index) => ({
      ...message,
      itemId: `message-${index}`,
      role: message.role === 'assistant' ? 'assistant' : 'user'
    }));

    // Deduplicate assistant messages by filtering out those with very similar content
    const filteredMessages: typeof mappedMessages = [];
    const seenContents: {content: string, index: number}[] = [];

    // First pass: collect all assistant messages and their indices
    mappedMessages.forEach((message, index) => {
      if (message.role === 'assistant') {
        seenContents.push({
          content: message.content.trim(),
          index
        });
      }
    });

    // Second pass: identify duplicates and keep only the most complete version
    const duplicateIndices = new Set<number>();
    
    // Compare each message with others to find duplicates or subsets
    for (let i = 0; i < seenContents.length; i++) {
      for (let j = i + 1; j < seenContents.length; j++) {
        const contentA = seenContents[i].content;
        const contentB = seenContents[j].content;
        
        // If one message is a subset of another
        if (contentA.includes(contentB)) {
          // Mark the shorter one as duplicate
          duplicateIndices.add(seenContents[j].index);
        } else if (contentB.includes(contentA)) {
          // Mark the shorter one as duplicate
          duplicateIndices.add(seenContents[i].index);
        } 
        // If messages are very similar (more than 80% overlap)
        else if (contentA.length > 20 && contentB.length > 20) {
          // Check for significant overlap using a simple similarity check
          const shorterContent = contentA.length < contentB.length ? contentA : contentB;
          const longerContent = contentA.length >= contentB.length ? contentA : contentB;
          
          // If the shorter content appears mostly in the longer content
          const words = shorterContent.split(/\s+/);
          let matchCount = 0;
          
          for (const word of words) {
            if (word.length > 3 && longerContent.includes(word)) {
              matchCount++;
            }
          }
          
          // If more than 80% of significant words match
          if (words.length > 0 && matchCount / words.length > 0.8) {
            // Mark the shorter message as duplicate
            if (contentA.length < contentB.length) {
              duplicateIndices.add(seenContents[i].index);
            } else {
              duplicateIndices.add(seenContents[j].index);
            }
          }
        }
      }
    }

    // Add all non-duplicate messages to the filtered list
    for (let i = 0; i < mappedMessages.length; i++) {
      const message = mappedMessages[i];
      if (message.role === 'user' || !duplicateIndices.has(i)) {
        filteredMessages.push(message);
      }
    }

    return filteredMessages;
  }, [messages]);
  
  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Show messages container when conversation starts
  useEffect(() => {
    if (messages.length > 0 && !showMessages) {
      setShowMessages(true);
    }
  }, [messages, showMessages]);
  
  // Track detected language for language alert
  const [detectedWrongLanguage, setDetectedWrongLanguage] = useState(false);
  // Add state for animation with better naming for clarity
  const [alertAnimationState, setAlertAnimationState] = useState<'entering' | 'visible' | 'exiting' | 'hidden'>('hidden');
  // Add ref to track if animation is in progress
  const animationInProgressRef = useRef(false);
  // Add ref to track the last time we showed an alert to prevent rapid re-triggering
  const lastAlertTimeRef = useRef<number>(0);
  // Add ref to track if the tutor is currently speaking
  const tutorIsSpeakingRef = useRef<boolean>(false);

  // Simplified function to show and auto-hide the language alert
  const showAndHideLanguageAlert = useCallback(() => {
    // Don't show alert if tutor is currently speaking
    if (tutorIsSpeakingRef.current) {
      console.log('Not showing language alert because tutor is speaking');
      return;
    }
    
    // Implement debouncing - don't show alert if we've shown one recently (within 5 seconds)
    const now = Date.now();
    const timeSinceLastAlert = now - lastAlertTimeRef.current;
    if (timeSinceLastAlert < 5000) { // 5 seconds debounce
      console.log(`Not showing language alert - debounced (${timeSinceLastAlert}ms since last alert)`);
      return;
    }
    
    console.log('Showing language alert notification');
    lastAlertTimeRef.current = now;
    
    // Clear any existing timeouts first
    if (languageAlertTimeoutRef.current) {
      clearTimeout(languageAlertTimeoutRef.current);
      languageAlertTimeoutRef.current = null;
    }
    
    // Clear any existing global safety timeout
    if (globalSafetyTimeoutRef.current) {
      clearTimeout(globalSafetyTimeoutRef.current);
      globalSafetyTimeoutRef.current = null;
    }
    
    // Show the alert with enter animation
    setShowLanguageAlert(true);
    setAlertAnimationState('entering');
    
    // Wait a tiny bit for entering animation to apply
    setTimeout(() => {
      // Set to visible state
      setAlertAnimationState('visible');
      
      // Set primary timeout to hide after exactly 3 seconds
      languageAlertTimeoutRef.current = setTimeout(() => {
        // Start exit animation
        setAlertAnimationState('exiting');
        
        // Wait for exit animation to complete
        setTimeout(() => {
          // Hide alert entirely
          setShowLanguageAlert(false);
          setAlertAnimationState('hidden');
          setDetectedWrongLanguage(false);
        }, 350); // Slightly longer than animation duration for safety
      }, 3000); // Show for exactly 3 seconds
      
      // Set a guaranteed fallback timeout that will force-hide regardless
      // This is our safety net in case animations fail
      globalSafetyTimeoutRef.current = setTimeout(() => {
        // If we're still showing the alert after 3.5 seconds, force hide it
        console.log('Global safety timeout check');
        
        // Force hide the alert regardless of state
        setShowLanguageAlert(false);
        setAlertAnimationState('hidden');
        setDetectedWrongLanguage(false);
        
        // Direct DOM manipulation as last resort
        const alertElement = document.getElementById('language-alert-notification');
        if (alertElement) {
          alertElement.style.display = 'none';
        }
      }, 3500); // 3.5 seconds total (3s display + 0.5s buffer)
    }, 10);
  }, []);
  
  // Handle language alert - only show when user speaks a different language
  useEffect(() => {
    // Only proceed if we're recording, using a non-English language, detected wrong language, and not currently animating/showing alert
    const nonEnglishLanguages = ['dutch', 'spanish', 'german', 'french', 'portuguese'];
    
    // Additional check to ensure tutor is not currently speaking
    if (isRecording && 
        nonEnglishLanguages.includes(language) && 
        detectedWrongLanguage && 
        !showLanguageAlert && 
        !tutorIsSpeakingRef.current) {
      
      console.log('Triggering language alert display');
      showAndHideLanguageAlert();
    }
    
    // Cleanup function to prevent memory leaks
    return () => {
      if (languageAlertTimeoutRef.current) {
        clearTimeout(languageAlertTimeoutRef.current);
        languageAlertTimeoutRef.current = null;
      }
      
      // Also clear the global safety timeout
      if (globalSafetyTimeoutRef.current) {
        clearTimeout(globalSafetyTimeoutRef.current);
        globalSafetyTimeoutRef.current = null;
      }
    };
  }, [isRecording, language, showLanguageAlert, detectedWrongLanguage, showAndHideLanguageAlert]);
  
  // Handle errors
  useEffect(() => {
    if (error) {
      console.error('Realtime error:', error);
      setLocalError(error);
    } else {
      setLocalError(null);
    }
  }, [error]);
  
  // Initialize the realtime service
  useEffect(() => {
    const initializeService = async () => {
      try {
        // Make sure language and level are defined before initializing
        if (!language || !level) {
          console.error('Missing required parameters: language or level');
          setLocalError('Missing language or level. Please try again.');
          return;
        }
        
        // Log the parameters being passed to the initialize function
        console.log('Initializing with parameters - language:', language, 'level:', level, 'topic:', topic || 'none');
        if (topic === 'custom' && userPrompt) {
          console.log('Custom topic prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
        }
        
        // Check if we have assessment data in session storage or user profile
        let assessmentData = null;
        
        // First try to get from session storage (most recent assessment)
        const storedAssessmentData = sessionStorage.getItem('speakingAssessmentData');
        if (storedAssessmentData) {
          try {
            assessmentData = JSON.parse(storedAssessmentData);
            console.log('Retrieved speaking assessment data from session storage');
          } catch (e) {
            console.error('Error parsing speaking assessment data from session storage:', e);
          }
        }
        
        // If not found in session storage, try to get from user profile
        if (!assessmentData) {
          try {
            const userData = localStorage.getItem('userData');
            if (userData) {
              const user = JSON.parse(userData);
              if (user.last_assessment_data) {
                assessmentData = user.last_assessment_data;
                console.log('Retrieved speaking assessment data from user profile');
              }
            }
          } catch (e) {
            console.error('Error retrieving assessment data from user profile:', e);
          }
        }
        
        // Pass the language, level, topic, userPrompt, and assessment data parameters to the initialize function
        await initialize(language, level, topic, userPrompt, assessmentData);
        console.log('Realtime service initialized successfully');
      } catch (err) {
        console.error('Failed to initialize realtime service:', err);
        setLocalError('Failed to initialize the speech service. Please try again.');
      }
    };
    
    initializeService();
  }, [initialize, language, level, topic, userPrompt]);
  
  // Function to check if text is in the target language
  const isInTargetLanguage = (text: string): boolean => {
    if (!text || text.trim() === '') return false;
    
    const lowerText = text.toLowerCase();
    
    // Language detection patterns
    const languagePatterns: Record<string, RegExp[]> = {
      dutch: [
        /\b(ik|je|het|de|een|en|is|zijn|hebben|mijn|jouw|hoe|wat|waar|waarom|wanneer|wie)\b/i,
        /\b(goed|slecht|mooi|lelijk|groot|klein|nieuw|oud|veel|weinig)\b/i,
        /\b(hallo|dag|goedemorgen|goedemiddag|goedenavond|doei|tot ziens)\b/i
      ],
      spanish: [
        /\b(yo|tu|el|ella|nosotros|ellos|es|son|tengo|tiene|mi|tu|como|que|donde|por que|cuando|quien)\b/i,
        /\b(bueno|malo|bonito|feo|grande|pequeño|nuevo|viejo|mucho|poco)\b/i,
        /\b(hola|buenos dias|buenas tardes|buenas noches|adios|hasta luego)\b/i
      ],
      german: [
        /\b(ich|du|er|sie|es|wir|sie|bin|ist|sind|habe|hat|mein|dein|wie|was|wo|warum|wann|wer)\b/i,
        /\b(gut|schlecht|schön|hässlich|groß|klein|neu|alt|viel|wenig)\b/i,
        /\b(hallo|guten tag|guten morgen|guten abend|auf wiedersehen|tschüss)\b/i
      ],
      french: [
        /\b(je|tu|il|elle|nous|ils|elles|suis|est|sont|ai|a|mon|ton|comment|quoi|où|pourquoi|quand|qui)\b/i,
        /\b(bon|mauvais|beau|laid|grand|petit|nouveau|vieux|beaucoup|peu)\b/i,
        /\b(bonjour|salut|bonsoir|au revoir|à bientôt)\b/i
      ],
      portuguese: [
        /\b(eu|tu|ele|ela|nós|eles|elas|sou|é|são|tenho|tem|meu|teu|como|que|onde|por que|quando|quem)\b/i,
        /\b(bom|mau|bonito|feio|grande|pequeno|novo|velho|muito|pouco)\b/i,
        /\b(olá|bom dia|boa tarde|boa noite|adeus|até logo)\b/i
      ],
      english: [
        /\b(i|you|he|she|it|we|they|am|is|are|was|were|have|has|had|my|your|how|what|where|why|when|who)\b/i,
        /\b(good|bad|nice|ugly|big|small|new|old|many|few)\b/i,
        /\b(hello|hi|morning|afternoon|evening|goodbye|bye|see you)\b/i
      ]
    };
    
    // Check if text contains patterns from the target language
    const currentLanguage = language as keyof typeof languagePatterns;
    const containsTargetLanguage = languagePatterns[currentLanguage]?.some((pattern: RegExp) => pattern.test(lowerText)) || false;
    
    // Check if text contains English patterns (common wrong language)
    const containsEnglish = languagePatterns.english.some((pattern: RegExp) => pattern.test(lowerText));
    
    // Additional language-specific checks
    let isLikelyWrongLanguage = false;
    
    if (language === 'dutch') {
      // Dutch-specific detection
      const hasNonDutchCharacters = /[qwxyz]/i.test(lowerText) && lowerText.length > 3; // These characters are rare in Dutch
      const hasDutchSpecificCombinations = /\b(ij|aa|ee|oo|uu|eu|oe|ui)\b/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasDutchSpecificCombinations) ||
                           hasNonDutchCharacters;
    } else if (language === 'spanish') {
      // Spanish-specific detection
      const hasNonSpanishCharacters = /[kw]/i.test(lowerText) && lowerText.length > 3; // These are uncommon in Spanish
      const hasSpanishSpecificCharacters = /[ñáéíóúü]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasSpanishSpecificCharacters) ||
                           hasNonSpanishCharacters;
    } else if (language === 'german') {
      // German-specific detection
      const hasGermanSpecificCharacters = /[äöüß]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasGermanSpecificCharacters);
    } else if (language === 'french') {
      // French-specific detection
      const hasFrenchSpecificCharacters = /[éèêëàâçîïôùûüÿ]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasFrenchSpecificCharacters);
    } else if (language === 'portuguese') {
      // Portuguese-specific detection
      const hasPortugueseSpecificCharacters = /[áàâãéêíóôõúç]/i.test(lowerText);
      isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                           (lowerText.length > 5 && !containsTargetLanguage && !hasPortugueseSpecificCharacters);
    }
    
    // For English mode, we need to check if the text is actually in English
    if (language === 'english') {
      // Check if text contains English patterns
      const containsEnglish = languagePatterns.english.some((pattern: RegExp) => pattern.test(lowerText));
      
      // Check for non-English characters that are uncommon in English
      const hasNonEnglishCharacters = /[áàâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]/i.test(lowerText);
      
      // For English, we consider text to be in the target language if it contains English patterns
      // and doesn't have too many non-English characters
      return containsEnglish && !hasNonEnglishCharacters;
    }
    
    // For other languages, return true if it's likely in the target language (not wrong language)
    return !isLikelyWrongLanguage;
  };

  // Handle transcript updates and language detection
  useEffect(() => {
    // Extract the latest user message for the transcript
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const latestUserMessage = userMessages[userMessages.length - 1];
      
      // Only set the transcript if it's in the target language or if we're in English mode
      if (isInTargetLanguage(latestUserMessage.content)) {
        setCurrentTranscript(latestUserMessage.content);
      } else {
        // Clear the transcript or set a placeholder message
        setCurrentTranscript('');
      }
      
      // Check if this is a recent message (within the last 5 seconds)
      const now = Date.now();
      // Safely handle timestamp which might be undefined
      const messageTime = latestUserMessage.timestamp ? new Date(latestUserMessage.timestamp as string).getTime() : now;
      const messageAge = now - messageTime;
      const isRecentMessage = messageAge < 5000; // Only process messages less than 5 seconds old
      
      // Check if the tutor is currently speaking by looking at the most recent assistant message
      const assistantMessages = messages.filter(msg => msg.role === 'assistant');
      const isTutorSpeaking = assistantMessages.length > 0 && 
                             (assistantMessages[assistantMessages.length - 1].timestamp ? 
                              new Date(assistantMessages[assistantMessages.length - 1].timestamp as string).getTime() > messageTime : false);
      
      // Update the ref for use in other functions
      tutorIsSpeakingRef.current = isTutorSpeaking;
      
      // Only proceed with language detection if:
      // 1. This is a recent message
      // 2. The tutor is not currently speaking
      // 3. We're in a non-English lesson
      if (isRecentMessage && !isTutorSpeaking && language !== 'english') {
        // Language detection for all supported languages
        const text = latestUserMessage.content.toLowerCase();
        
        // Common patterns for each language
        const languagePatterns = {
          dutch: [
            /\b(ik|je|het|de|een|en|is|zijn|hebben|mijn|jouw|hoe|wat|waar|waarom|wanneer|wie)\b/i,
            /\b(goed|slecht|mooi|lelijk|groot|klein|nieuw|oud|veel|weinig)\b/i,
            /\b(hallo|dag|goedemorgen|goedemiddag|goedenavond|doei|tot ziens)\b/i
          ],
          spanish: [
            /\b(yo|tu|el|ella|nosotros|ellos|es|son|tengo|tiene|mi|tu|como|que|donde|por que|cuando|quien)\b/i,
            /\b(bueno|malo|bonito|feo|grande|pequeño|nuevo|viejo|mucho|poco)\b/i,
            /\b(hola|buenos dias|buenas tardes|buenas noches|adios|hasta luego)\b/i
          ],
          german: [
            /\b(ich|du|er|sie|es|wir|sie|bin|ist|sind|habe|hat|mein|dein|wie|was|wo|warum|wann|wer)\b/i,
            /\b(gut|schlecht|schön|hässlich|groß|klein|neu|alt|viel|wenig)\b/i,
            /\b(hallo|guten tag|guten morgen|guten abend|auf wiedersehen|tschüss)\b/i
          ],
          french: [
            /\b(je|tu|il|elle|nous|ils|elles|suis|est|sont|ai|a|mon|ton|comment|quoi|où|pourquoi|quand|qui)\b/i,
            /\b(bon|mauvais|beau|laid|grand|petit|nouveau|vieux|beaucoup|peu)\b/i,
            /\b(bonjour|salut|bonsoir|au revoir|à bientôt)\b/i
          ],
          portuguese: [
            /\b(eu|tu|ele|ela|nós|eles|elas|sou|é|são|tenho|tem|meu|teu|como|que|onde|por que|quando|quem)\b/i,
            /\b(bom|mau|bonito|feio|grande|pequeno|novo|velho|muito|pouco)\b/i,
            /\b(olá|bom dia|boa tarde|boa noite|adeus|até logo)\b/i
          ],
          english: [
            /\b(i|you|he|she|it|we|they|am|is|are|was|were|have|has|had|my|your|how|what|where|why|when|who)\b/i,
            /\b(good|bad|nice|ugly|big|small|new|old|many|few)\b/i,
            /\b(hello|hi|morning|afternoon|evening|goodbye|bye|see you)\b/i
          ]
        };
        
        // Check if text contains patterns from the target language
        const currentLanguage = language as keyof typeof languagePatterns;
        const containsTargetLanguage = languagePatterns[currentLanguage].some((pattern: RegExp) => pattern.test(text));
        
        // Check if text contains English patterns (common wrong language)
        const containsEnglish = languagePatterns.english.some((pattern: RegExp) => pattern.test(text));
        
        // Only proceed with detection if the message has enough content to analyze
        if (text.length > 3) {
          // For each language, check for specific characters or combinations
          let isLikelyWrongLanguage = false;
          
          if (language === 'dutch') {
            // Dutch-specific detection
            const hasNonDutchCharacters = /[qwxyz]/i.test(text) && text.length > 3; // These characters are rare in Dutch
            const hasDutchSpecificCombinations = /\b(ij|aa|ee|oo|uu|eu|oe|ui)\b/i.test(text);
            isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                                   (text.length > 5 && !containsTargetLanguage && !hasDutchSpecificCombinations) ||
                                   hasNonDutchCharacters;
          } else if (language === 'spanish') {
            // Spanish-specific detection
            const hasNonSpanishCharacters = /[kw]/i.test(text) && text.length > 3; // These are uncommon in Spanish
            const hasSpanishSpecificCharacters = /[ñáéíóúü]/i.test(text);
            isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                                   (text.length > 5 && !containsTargetLanguage && !hasSpanishSpecificCharacters) ||
                                   hasNonSpanishCharacters;
          } else if (language === 'german') {
            // German-specific detection
            const hasGermanSpecificCharacters = /[äöüß]/i.test(text);
            isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                                   (text.length > 5 && !containsTargetLanguage && !hasGermanSpecificCharacters);
          } else if (language === 'french') {
            // French-specific detection
            const hasFrenchSpecificCharacters = /[éèêëàâçîïôùûüÿ]/i.test(text);
            isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                                   (text.length > 5 && !containsTargetLanguage && !hasFrenchSpecificCharacters);
          } else if (language === 'portuguese') {
            // Portuguese-specific detection
            const hasPortugueseSpecificCharacters = /[áàâãéêíóôõúç]/i.test(text);
            isLikelyWrongLanguage = (containsEnglish && !containsTargetLanguage) || 
                                   (text.length > 5 && !containsTargetLanguage && !hasPortugueseSpecificCharacters);
          }
          
          // If we detect the wrong language is being used
          if (isLikelyWrongLanguage) {
            console.log('Detected wrong language use:', text);
            // Only set to true if we're not already showing the alert
            if (!showLanguageAlert || alertAnimationState === 'hidden') {
              setDetectedWrongLanguage(true);
            }
          } else if (containsTargetLanguage && !containsEnglish) {
            // If the user is now speaking the target language, hide the alert with animation
            if (showLanguageAlert && alertAnimationState !== 'exiting' && alertAnimationState !== 'hidden') {
              console.log('User switched to correct language, hiding alert');
              // Start exit animation
              setAlertAnimationState('exiting');
              
              // After exit animation completes, hide the alert
              setTimeout(() => {
                setShowLanguageAlert(false);
                setAlertAnimationState('hidden');
                setDetectedWrongLanguage(false);
              }, 300); // Match this with CSS animation duration
            }
          }
        }
      }
    }
  }, [messages, language, alertAnimationState, showLanguageAlert]);
  
  // Handle recording toggle
  const handleToggleRecording = async (e: React.MouseEvent) => {
    e.preventDefault();
    
    if (isRecording) {
      handleEndConversation();
      return;
    }
    
    // If starting a brand new conversation, reset the paused state
    setIsPaused(false);
    setIsAttemptingToRecord(true);
    
    try {
      await toggleConversation();
      setIsAttemptingToRecord(false);
    } catch (err) {
      console.error('Error toggling conversation:', err);
      setIsAttemptingToRecord(false);
      
      if (err instanceof Error && err.message.includes('Permission denied')) {
        micPermissionDeniedRef.current = true;
        setLocalError('Microphone permission denied. Please allow microphone access and try again.');
      } else {
        setLocalError('Failed to start recording. Please try again.');
      }
    }
  };
  
  // Handle end conversation
  const handleEndConversation = () => {
    // Store the conversation history before pausing
    conversationHistoryRef.current = getFormattedConversationHistory();
    console.log('Storing conversation history before pausing:', conversationHistoryRef.current);
    
    // Set the conversation as paused for pronunciation review
    setIsPaused(true);
    stopConversation();
  };
  
  // Handle continue learning
  const handleContinueLearning = () => {
    // Slight delay to allow the UI to update
    setTimeout(async () => {
      console.log('Continuing conversation from where we left off');
      
      if (isPaused && conversationHistoryRef.current) {
        console.log('Resuming paused conversation with previous context:', conversationHistoryRef.current);
        // Instead of toggling conversation (which would reset everything),
        // we use startConversation with the saved conversation history
        setShowMessages(true);
        await startConversation(conversationHistoryRef.current);
        setIsPaused(false);
      } else {
        // Only if not paused (fully ended), start a new conversation
        toggleConversation();
      }
    }, 300);
  };
  
  // Handle change language
  const handleChangeLanguage = () => {
    // Clear all selections except language which will be reselected
    sessionStorage.removeItem('selectedLevel');
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    // Clear any navigation flags
    sessionStorage.removeItem('fromLevelSelection');
    sessionStorage.removeItem('intentionalNavigation');
    
    // Set a flag to indicate we're intentionally going to language selection
    sessionStorage.setItem('fromSpeechPage', 'true');
    
    console.log('Navigating to language selection from speech client');
    window.location.href = '/language-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('speech')) {
        console.log('Still on speech page, using fallback navigation to language selection');
        window.location.replace('/language-selection');
      }
    }, 1000);
  };
  
  // Handle change topic
  const handleChangeTopic = () => {
    // Keep language but clear topic and level
    sessionStorage.removeItem('selectedTopic');
    sessionStorage.removeItem('customTopicText');
    sessionStorage.removeItem('selectedLevel');
    // Set a flag to indicate we're intentionally going to topic selection
    sessionStorage.setItem('fromLevelSelection', 'true');
    // Clear any other navigation flags
    sessionStorage.removeItem('intentionalNavigation');
    
    console.log('Navigating to topic selection from speech client');
    window.location.href = '/topic-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('speech')) {
        console.log('Still on speech page, using fallback navigation to topic selection');
        window.location.replace('/topic-selection');
      }
    }, 1000);
  };
  
  // Handle change level
  const handleChangeLevel = () => {
    // Clear level selection but keep language and topic
    sessionStorage.removeItem('selectedLevel');
    // Clear any navigation flags
    sessionStorage.removeItem('intentionalNavigation');
    
    console.log('Navigating to level selection from speech client');
    window.location.href = '/level-selection';
    
    // Fallback navigation in case the first attempt fails
    setTimeout(() => {
      if (window.location.pathname.includes('speech')) {
        console.log('Still on speech page, using fallback navigation to level selection');
        window.location.replace('/level-selection');
      }
    }, 1000);
  };
  
  return (
    <main className="flex flex-col text-white p-4 overflow-x-hidden">
      <div className="w-full max-w-5xl mx-auto h-full flex flex-col">
        {/* Language alert notification with animation states */}
        {showLanguageAlert && (
          <div 
            className={`fixed top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-amber-600 to-amber-500 text-white px-6 py-3 rounded-lg border border-amber-400/20 z-50 flex items-center space-x-3 max-w-md
              ${alertAnimationState === 'entering' ? 'animate-slide-in-top' : ''}
              ${alertAnimationState === 'exiting' ? 'animate-slide-out-top' : ''}
            `}
            role="alert"
            aria-live="assertive"
            id="language-alert-notification"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 flex-shrink-0 text-amber-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex flex-col">
              {language === 'dutch' && (
                <>
                  <span className="text-sm md:text-base font-medium">Dit is een Nederlandse les.</span>
                  <span className="text-xs md:text-sm text-amber-100">Probeer alsjeblieft in het Nederlands te spreken.</span>
                </>
              )}
              {language === 'spanish' && (
                <>
                  <span className="text-sm md:text-base font-medium">Esta es una clase de español.</span>
                  <span className="text-xs md:text-sm text-amber-100">Por favor, intenta hablar en español.</span>
                </>
              )}
              {language === 'german' && (
                <>
                  <span className="text-sm md:text-base font-medium">Dies ist ein Deutschunterricht.</span>
                  <span className="text-xs md:text-sm text-amber-100">Bitte versuche, auf Deutsch zu sprechen.</span>
                </>
              )}
              {language === 'french' && (
                <>
                  <span className="text-sm md:text-base font-medium">C'est un cours de français.</span>
                  <span className="text-xs md:text-sm text-amber-100">S'il vous plaît, essayez de parler en français.</span>
                </>
              )}
              {language === 'portuguese' && (
                <>
                  <span className="text-sm md:text-base font-medium">Esta é uma aula de português.</span>
                  <span className="text-xs md:text-sm text-amber-100">Por favor, tente falar em português.</span>
                </>
              )}
            </div>
          </div>
        )}
        
        {/* Header - Redesigned */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            {language.charAt(0).toUpperCase() + language.slice(1)} Conversation
          </h1>
          <p className="text-white/80 mt-2">
            Level: {level.toUpperCase()} - Click the microphone to start talking
          </p>
          
          {/* Redesigned Navigation Controls */}
          <div className="flex flex-wrap justify-center gap-3 mt-5 mb-6 animate-fade-in" style={{animationDelay: '200ms'}}>
            <button 
              type="button"
              onClick={handleChangeLanguage}
              className="primary-button px-4 py-2 rounded-lg"
            >
              Change Language
            </button>
            <button 
              type="button"
              onClick={handleChangeTopic}
              className="primary-button px-4 py-2 rounded-lg"
            >
              Change Topic
            </button>
            <button 
              type="button"
              onClick={handleChangeLevel}
              className="primary-button px-4 py-2 rounded-lg"
            >
              Change Level
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Main Content Area - Redesigned for better responsiveness and alignment */}
          <div className="w-full max-w-6xl mx-auto relative">
            {/* Microphone Section - Centered when no conversation, animates out when recording starts */}
            <div className={`flex flex-col items-center justify-center transition-all duration-700 ease-in-out ${isRecording || showMessages ? 'opacity-0 scale-90 pointer-events-none absolute top-0 left-1/2 transform -translate-x-1/2' : 'opacity-100 mb-12'}`}>
              {/* Microphone UI with improved animations */}
              <div className="relative flex items-center justify-center transform transition-all duration-500">
                {/* Decorative rings with improved animations */}
                <div className="absolute w-40 h-40 rounded-full mic-btn-ring"></div>
                <div className="absolute w-36 h-36 rounded-full mic-btn-ring" style={{ animationDelay: '0.5s' }}></div>
                <div className="absolute w-32 h-32 rounded-full mic-btn-ring" style={{ animationDelay: '1s' }}></div>
                
                {/* Enhanced overlay for initializing state */}
                {isAttemptingToRecord && !isRecording && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm rounded-full z-20 flex items-center justify-center">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-xs text-white/80 animate-pulse">Initializing...</span>
                    </div>
                  </div>
                )}
                
                {/* Microphone Button with gradient */}
                <Button
                  type="button"
                  onClick={(e) => handleToggleRecording(e)}
                  onTouchStart={(e) => e.preventDefault()}
                  aria-label="Start recording"
                  className={`mic-btn relative z-10 rounded-full w-28 h-28 flex items-center justify-center transition-all duration-500 touch-target ${isAttemptingToRecord && !isRecording ? 'opacity-70' : 'opacity-100'}`}
                  disabled={isAttemptingToRecord && !isRecording}
                >
                  <div className="absolute inset-0 rounded-full bg-white/20 backdrop-blur-sm opacity-90"></div>
                  <div className="absolute inset-0 rounded-full bg-white/30 opacity-0 hover:opacity-90 transition-opacity duration-300"></div>
                  
                  {/* Microphone icon with animation */}
                  <div className="relative z-10 flex items-center justify-center">
                    <div className="relative">
                      {/* Animated rings when recording */}
                      {isRecording && (
                        <>
                          <div className="absolute w-full h-full rounded-full bg-purple-500/5 animate-ping-slow"></div>
                          <div className="absolute w-[110%] h-[110%] rounded-full bg-blue-500/5 animate-ping-slower"></div>
                        </>
                      )}
                      
                      {/* Audio wave animation when recording */}
                      {isRecording ? (
                        <div className="flex items-center justify-center h-10 w-10">
                          <div className="relative h-10 w-10">
                            <div className="audio-wave">
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                              <span className="audio-wave-bar"></span>
                            </div>
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="h-3 w-3 rounded-full bg-red-500 animate-pulse"></div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <MicrophoneIcon isRecording={isRecording} size={32} />
                      )}
                    </div>
                  </div>
                </Button>
              </div>
              
              <p className="mt-6 text-lg text-white/80 animate-fade-in">
                {isAttemptingToRecord ? 'Initializing microphone...' : 'Click to start speaking'}
              </p>
              
              {/* Error message */}
              {localError && (
                <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-200 max-w-md text-center animate-fade-in">
                  <p>{localError}</p>
                </div>
              )}
            </div>
            
            {/* Transcript Sections - Animate in when conversation starts */}
            {showMessages && (
              <div className="w-full transition-all duration-700 ease-in-out opacity-100 translate-y-0">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
                  {/* Real-time Transcript Component */}
                  <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-3 shadow-lg animate-fade-in" style={{animationDelay: '200ms'}}>
                    <h3 className="text-sm font-semibold mb-2 text-blue-400 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                      Real-time Transcript
                    </h3>
                    <SentenceConstructionAssessment
                      transcript={currentTranscript}
                      isRecording={isRecording}
                      onStopRecording={handleEndConversation}
                      onContinueLearning={handleContinueLearning}
                      language={language}
                      level={level}
                      exerciseType={exerciseType}
                      onChangeExerciseType={setExerciseType}
                    />
                    
                    {/* Warning message when content is not in target language */}
                    {isRecording && messages.length > 0 && messages[messages.length - 1].role === 'user' && 
                     !isInTargetLanguage(messages[messages.length - 1].content) && (
                      <div className="mt-4 px-4 py-3 bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-200 text-center animate-fade-in">
                        <p className="text-sm">Please speak in {language.charAt(0).toUpperCase() + language.slice(1)} to analyze your sentence.</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Conversation Transcript Section */}
                  <div className="relative bg-slate-800/50 border border-slate-700/50 rounded-lg p-3 shadow-lg animate-fade-in flex flex-col" style={{animationDelay: '300ms'}}>
                    <h3 className="text-sm font-semibold mb-2 text-indigo-400 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      Conversation Transcript
                    </h3>
                    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/80 backdrop-blur-sm rounded-lg border border-slate-700/50 p-3 flex-1 min-h-[250px] md:min-h-[320px] max-h-[60vh] overflow-y-auto custom-scrollbar flex flex-col">
                      <div className="space-y-4 flex-1 flex flex-col">
                        {processedMessages.length > 0 ? (
                          // Sort messages by timestamp if available, otherwise use the array order
                          processedMessages
                            .sort((a: any, b: any) => {
                              if (a.timestamp && b.timestamp) {
                                return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
                              }
                              return 0;
                            })
                            .map((message: any, index: number) => {
                              // Parse timestamp for display or use current time as fallback
                              const messageTime = message.timestamp 
                                ? new Date(message.timestamp) 
                                : new Date();
                              
                              // Format the time for display
                              const timeDisplay = messageTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                              
                              // Log message for debugging
                              console.log(`Rendering message ${index}: ${message.role}, content: ${message.content.substring(0, 30)}..., timestamp: ${timeDisplay}`);
                              
                              return (
                                <div 
                                  key={`${message.role}-${index}-${message.itemId || messageTime.getTime()}`}
                                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                                >
                                  {message.role !== 'user' && (
                                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mr-2 shadow-md">
                                      <span className="text-xs font-bold text-white">T</span>
                                    </div>
                                  )}
                                  <div 
                                    className={`max-w-[75%] break-words p-4 rounded-2xl shadow-md ${
                                      message.role === 'user' 
                                        ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white ml-2 rounded-tr-none' 
                                        : 'bg-gradient-to-r from-purple-500 to-purple-600 text-white mr-2 rounded-tl-none'
                                    }`}
                                    style={{
                                      wordBreak: 'break-word',
                                      overflowWrap: 'break-word',
                                      whiteSpace: 'pre-wrap'
                                    }}
                                  >
                                    <div className="flex items-center justify-between mb-1 text-white/90">
                                      <span className="text-xs font-semibold">
                                        {message.role === 'user' ? 'You' : 'Tutor'}
                                      </span>
                                      <span className="text-xs opacity-75 ml-2">
                                        {timeDisplay}
                                      </span>
                                    </div>
                                    <p className="text-sm leading-relaxed text-white/95 mt-1">{message.content}</p>
                                  </div>
                                  {message.role === 'user' && (
                                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center ml-2 shadow-md">
                                      <span className="text-xs font-bold text-white">U</span>
                                    </div>
                                  )}
                                </div>
                              );
                            })
                        ) : (
                          <div className="flex justify-center items-center h-full flex-1">
                            <div className="text-center p-6 rounded-lg bg-indigo-500/10 border border-indigo-500/20 animate-fadeIn w-full">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto mb-3 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                              </svg>
                              <p className="text-indigo-300 font-medium">Your conversation will appear here</p>
                              <p className="text-indigo-200/70 text-sm mt-2">Click the microphone button to start talking</p>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} className="mt-auto" />
                      </div>
                    </div>
                    <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-indigo-500 to-purple-500 h-1 w-1/3 rounded-full opacity-70"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

// Microphone icon component with audio wave animation
function MicrophoneIcon({ isRecording, size = 20 }: { isRecording: boolean; size?: number }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="text-white"
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" x2="12" y1="19" y2="22"></line>
    </svg>
  );
}
