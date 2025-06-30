'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { RealtimeMessage } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { isAuthenticated } from '@/lib/auth-utils';
import { getConversationDuration, formatTime, getGuestLimitationsDescription, getRemainingTime, checkAndMarkSessionExpired } from '@/lib/guest-utils';
import SentenceConstructionAssessment from '@/components/sentence-construction-assessment';
import ModernTimer from '@/components/modern-timer';
import SaveProgressButton from '@/components/save-progress-button';
import LeaveConversationModal from '@/components/leave-conversation-modal';
import SessionCompletionModal from '@/components/session-completion-modal';

interface SpeechClientProps {
  language: string;
  level: string;
  topic?: string;
  userPrompt?: string;
}

export default function SpeechClient({ language, level, topic, userPrompt }: SpeechClientProps) {
  // Moving the console.log out of the component body to prevent excessive logging
  const initialRenderRef = useRef(true);
  
  // All conversation saving and timer issues have been resolved
  
  const router = useRouter();
  const { user } = useAuth();
  
  // Extract the user's first name from their full name
  const firstName = useMemo(() => {
    if (!user?.name) return 'You';
    return user.name.split(' ')[0]; // Get the first part of the name
  }, [user?.name]);
  
  // Guest user conversation timer state - simplified to only track state, not duplicate timing
  const [isConversationTimerActive, setIsConversationTimerActive] = useState(false);
  const [conversationTimeUp, setConversationTimeUp] = useState(false);
  const [conversationDuration] = useState(() => getConversationDuration(isAuthenticated()));
  
  // Initialize conversation timer and check for expired sessions
  useEffect(() => {
    const hasAssessmentData = sessionStorage.getItem('speakingAssessmentData') !== null;
    
    // Check for existing plan and validate timer immediately on component mount
    const urlParams = new URLSearchParams(window.location.search);
    const planParam = urlParams.get('plan');
    
    if (planParam) {
      console.log('Checking plan timer validity on speech client mount:', planParam);
      
      // For registered users with learning plans, always allow conversation
      if (isAuthenticated()) {
        console.log('Registered user with learning plan - allowing full conversation duration');
        setConversationTimeUp(false);
      } else {
        // For guest users, use the enhanced validation function to check if session is expired
        const isExpired = checkAndMarkSessionExpired(planParam, isAuthenticated());
        
        if (isExpired) {
          console.log('Guest plan session has expired, preventing conversation');
          setConversationTimeUp(true);
          return;
        } else {
          console.log('Guest plan session is valid, allowing conversation');
          setConversationTimeUp(false);
        }
      }
    } else if (!isAuthenticated() && hasAssessmentData) {
      console.log('Guest user has assessment data, allowing limited conversation');
      // Always allow the conversation for guest users who completed an assessment
      setConversationTimeUp(false);
    }
  }, []);
  
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(true); // Always show conversation interface
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const micPermissionDeniedRef = useRef(false);
  const analyzeButtonRef = useRef<(() => void) | null>(null);
  // Track which messages have been analyzed
  const [analyzedMessageIds, setAnalyzedMessageIds] = useState<string[]>([]);
  
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
  
  // Leave conversation modal state
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [conversationStartTime, setConversationStartTime] = useState<number | null>(null);
  
  // Session completion modal state
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [sessionCompleted, setSessionCompleted] = useState(false);
  const [showSavingLoader, setShowSavingLoader] = useState(false);
  
  // Only log on initial render, not on every re-render
  useEffect(() => {
    if (initialRenderRef.current) {
      console.log('SpeechClient initializing with language:', language, 'level:', level, 'topic:', topic, 'at:', new Date().toISOString());
      console.log('🎯 USER SELECTION SUMMARY - Language:', language, 'Level:', level, 'Topic:', topic, 'UserPrompt:', userPrompt);
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
  
  // Process messages for display and deduplicate both user and assistant messages
  const processedMessages = useMemo(() => {
    // First, map the messages to add consistent IDs
    const mappedMessages = messages.map((message, index) => ({
      ...message,
      itemId: `message-${index}`,
      role: message.role === 'assistant' ? 'assistant' : 'user'
    }));

    // Deduplicate messages by filtering out those with very similar content
    const filteredMessages: typeof mappedMessages = [];
    const seenContents: {content: string, index: number, role: string}[] = [];

    // First pass: collect all messages and their indices
    mappedMessages.forEach((message, index) => {
      seenContents.push({
        content: message.content.trim(),
        index,
        role: message.role
      });
    });

    // Second pass: identify duplicates and keep only the most complete version
    const duplicateIndices = new Set<number>();
    
    // Compare each message with others to find duplicates or subsets
    for (let i = 0; i < seenContents.length; i++) {
      for (let j = i + 1; j < seenContents.length; j++) {
        const messageA = seenContents[i];
        const messageB = seenContents[j];
        
        // Only compare messages from the same role
        if (messageA.role !== messageB.role) continue;
        
        const contentA = messageA.content;
        const contentB = messageB.content;
        
        // Check for exact duplicates first
        if (contentA === contentB) {
          // Mark the later one as duplicate
          duplicateIndices.add(messageB.index);
          continue;
        }
        
        // If one message is a subset of another
        if (contentA.includes(contentB)) {
          // Mark the shorter one as duplicate
          duplicateIndices.add(messageB.index);
        } else if (contentB.includes(contentA)) {
          // Mark the shorter one as duplicate
          duplicateIndices.add(messageA.index);
        } 
        // If messages are very similar (more than 90% overlap for user messages, 80% for assistant)
        else if (contentA.length > 10 && contentB.length > 10) {
          // Check for significant overlap using a simple similarity check
          const shorterContent = contentA.length < contentB.length ? contentA : contentB;
          const longerContent = contentA.length >= contentB.length ? contentA : contentB;
          
          // If the shorter content appears mostly in the longer content
          const words = shorterContent.split(/\s+/);
          let matchCount = 0;
          
          for (const word of words) {
            if (word.length > 2 && longerContent.includes(word)) {
              matchCount++;
            }
          }
          
          // Use higher threshold for user messages (90%) since they're usually shorter and more precise
          const threshold = messageA.role === 'user' ? 0.9 : 0.8;
          
          // If more than threshold of words match
          if (words.length > 0 && matchCount / words.length > threshold) {
            // Mark the shorter message as duplicate
            if (contentA.length < contentB.length) {
              duplicateIndices.add(messageA.index);
            } else {
              duplicateIndices.add(messageB.index);
            }
          }
        }
      }
    }

    // Add all non-duplicate messages to the filtered list
    for (let i = 0; i < mappedMessages.length; i++) {
      const message = mappedMessages[i];
      if (!duplicateIndices.has(i)) {
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
  
  // This effect is no longer needed since we always show messages container
  // But we'll keep a modified version to handle any edge cases
  useEffect(() => {
    // Ensure messages are always shown
    if (!showMessages) {
      setShowMessages(true);
    }
  }, [showMessages]);
  
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
        
        // Check if we have assessment data - prioritize learning plan data over user profile data
        let assessmentData = null;
        
        // First, check if we're accessing a specific learning plan
        const urlParams = new URLSearchParams(window.location.search);
        const planParam = urlParams.get('plan');
        
        if (planParam) {
          console.log('Found plan ID in URL, attempting to retrieve plan-specific assessment data:', planParam);
          try {
            // Import the API function dynamically to avoid circular dependencies
            const { getLearningPlan } = await import('@/lib/learning-api');
            const plan = await getLearningPlan(planParam);
            
            if (plan && plan.assessment_data) {
              // Check if the assessment data is recent and relevant
              const assessmentAge = plan.assessment_data.recognized_text;
              if (assessmentAge && assessmentAge !== 'Me too. Me too.' && assessmentAge.trim().length > 5) {
                // Include both assessment data and learning plan data
                assessmentData = {
                  ...plan.assessment_data,
                  learning_plan_data: {
                    plan_content: plan.plan_content,
                    duration_months: plan.duration_months,
                    goals: plan.goals,
                    total_sessions: plan.total_sessions,
                    completed_sessions: plan.completed_sessions,
                    progress_percentage: plan.progress_percentage,
                    session_summaries: plan.session_summaries || []
                  }
                };
                console.log('Retrieved valid assessment data and learning plan data from learning plan:', planParam);
                console.log('Learning plan data included:', {
                  title: plan.plan_content?.title,
                  weekly_schedule_length: plan.plan_content?.weekly_schedule?.length,
                  first_week_focus: plan.plan_content?.weekly_schedule?.[0]?.focus
                });
              } else {
                console.log('Skipping old/invalid assessment data from learning plan');
              }
            } else {
              console.log('Learning plan found but no assessment data available in plan');
            }
          } catch (planError) {
            console.error('Error retrieving learning plan assessment data:', planError);
            // Continue to fallback methods if plan retrieval fails
          }
        }
        
        // If no plan-specific assessment data, try session storage (most recent assessment)
        if (!assessmentData) {
          const storedAssessmentData = sessionStorage.getItem('speakingAssessmentData');
          if (storedAssessmentData) {
            try {
              const parsedData = JSON.parse(storedAssessmentData);
              // Check if the assessment data is recent and relevant
              if (parsedData.recognized_text && parsedData.recognized_text !== 'Me too. Me too.' && parsedData.recognized_text.trim().length > 5) {
                assessmentData = parsedData;
                console.log('Retrieved valid speaking assessment data from session storage');
              } else {
                console.log('Skipping old/invalid assessment data from session storage');
              }
            } catch (e) {
              console.error('Error parsing speaking assessment data from session storage:', e);
            }
          }
        }
        
        // Skip user profile assessment data as it's likely to be old
        // We only want fresh assessment data for the current session
        console.log('Skipping user profile assessment data to avoid old cached data');
        
        // Retrieve custom topic research data if available
        let researchData = null;
        if (topic === 'custom') {
          const storedResearchData = sessionStorage.getItem('customTopicResearch');
          if (storedResearchData) {
            try {
              const parsedResearch = JSON.parse(storedResearchData);
              if (parsedResearch.success && parsedResearch.research) {
                researchData = parsedResearch.research;
                console.log('🔍 Retrieved custom topic research data:', researchData.length, 'characters');
                console.log('📄 Research preview:', researchData.substring(0, 200) + '...');
              } else {
                console.log('⚠️ Research data found but not successful or empty');
              }
            } catch (error) {
              console.error('❌ Error parsing stored research data:', error);
            }
          } else {
            console.log('ℹ️ No research data found in session storage for custom topic');
          }
        }
        
        // Pass the language, level, topic, userPrompt, and assessment data to the initialize function
        // Note: Research data is handled separately in the realtime service
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

  // Start timer when AI begins speaking (first assistant message)
  useEffect(() => {
    const assistantMessages = messages.filter(msg => msg.role === 'assistant');
    
    // If we have the first assistant message and timer is not active
    if (assistantMessages.length > 0 && 
        !isConversationTimerActive && 
        !conversationTimeUp &&
        isRecording) {
      
      console.log('🎯 AI has started speaking - starting conversation timer now!');
      setIsConversationTimerActive(true);
    }
  }, [messages, isConversationTimerActive, conversationTimeUp, isRecording]);

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
  
  // Auto-save conversation progress function
  const saveConversationProgress = async () => {
    if (!user || processedMessages.length === 0) {
      console.log('Cannot save: no user or no messages');
      return;
    }

    try {
      // Check if this is a learning plan conversation
      const urlParams = new URLSearchParams(window.location.search);
      const planParam = urlParams.get('plan');

      // Calculate conversation duration
      const durationMinutes = conversationStartTime 
        ? (Date.now() - conversationStartTime) / (1000 * 60)
        : 0;

      // Prepare messages for saving
      const messagesToSave = processedMessages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString()
      }));

      console.log('[AUTO_SAVE] Saving conversation:', {
        language,
        level,
        topic,
        messageCount: messagesToSave.length,
        duration: durationMinutes,
        isLearningPlan: !!planParam,
        planId: planParam
      });

      const { getApiUrl } = await import('@/lib/api-utils');
      const token = localStorage.getItem('token');
      
      // If this is a learning plan session, use the session summary endpoint
      if (planParam) {
        console.log('[AUTO_SAVE] 📚 This is a learning plan session - using session summary endpoint');
        
        // Generate a session summary for the learning plan
        const sessionSummary = `Session completed: ${durationMinutes.toFixed(1)} minutes, ${messagesToSave.length} messages exchanged. Focus: ${topic || 'general conversation'} at ${level} level in ${language}.`;
        
        // Save session summary to learning plan using the correct endpoint
        const summaryResponse = await fetch(`${getApiUrl()}/api/learning/session-summary?plan_id=${planParam}&session_summary=${encodeURIComponent(sessionSummary)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (!summaryResponse.ok) {
          const errorData = await summaryResponse.json();
          throw new Error(errorData.detail || 'Failed to save learning plan session');
        }

        const summaryResult = await summaryResponse.json();
        console.log('[AUTO_SAVE] ✅ Learning plan session saved successfully:', summaryResult);
        return;
      }

      // This is a practice mode conversation - save to conversation history
      console.log('[AUTO_SAVE] 💬 This is a practice session - saving to conversation history');
      
      const response = await fetch(`${getApiUrl()}/api/progress/save-conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          language,
          level,
          topic,
          messages: messagesToSave,
          duration_minutes: durationMinutes,
          learning_plan_id: null, // Explicitly mark as practice mode
          conversation_type: 'practice'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save conversation');
      }

      const result = await response.json();
      console.log('[AUTO_SAVE] ✅ Practice conversation saved successfully:', result);

      // Track usage for subscription limits (only for practice sessions >= 5 minutes)
      if (durationMinutes >= 5) {
        try {
          console.log('[SUBSCRIPTION] Tracking practice session usage for subscription limits');
          const usageResponse = await fetch(`${getApiUrl()}/api/stripe/track-usage`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              usage_type: 'practice_session',
              duration_minutes: durationMinutes
            })
          });

          if (usageResponse.ok) {
            const usageResult = await usageResponse.json();
            console.log('[SUBSCRIPTION] ✅ Practice session usage tracked:', usageResult);
          } else {
            const usageError = await usageResponse.json();
            console.warn('[SUBSCRIPTION] ⚠️ Failed to track usage:', usageError);
          }
        } catch (usageError) {
          console.error('[SUBSCRIPTION] ❌ Error tracking usage:', usageError);
        }
      }

    } catch (error) {
      console.error('[AUTO_SAVE] ❌ Error auto-saving conversation:', error);
    }
  };
  
  // Note: Timer logic is now handled entirely by the ModernTimer component
  // No duplicate timer effects needed here
  
  // Handle recording toggle
  const handleToggleRecording = async (e: React.MouseEvent) => {
    e.preventDefault();
    
    // If current conversation time is up, show message but allow starting a new one
    if (!isAuthenticated() && conversationTimeUp) {
      // Reset the conversation timer to allow a new attempt
      setConversationTimeUp(false);
      
      // Show notification about starting a new limited conversation
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <div>
            <p class="font-medium">Starting new conversation</p>
            <p class="text-sm opacity-90">As a guest, you have a 1-minute time limit</p>
          </div>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 5000);
    }
    
    if (isRecording) {
      // Stop recording and pause the timer
      console.log('🛑 Stopping recording - pausing timer');
      setIsConversationTimerActive(false);
      handleEndConversation();
      return;
    }

    // Check subscription limits for authenticated users before starting a new session
    if (user && !conversationStartTime) { // Only check when starting a new session
      try {
        console.log('[SUBSCRIPTION] Checking practice session access before starting...');
        const { getApiUrl } = await import('@/lib/api-utils');
        const token = localStorage.getItem('token');
        
        const response = await fetch(`${getApiUrl()}/api/stripe/can-access/practice_session`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const result = await response.json();
          if (!result.can_access) {
            console.log('[SUBSCRIPTION] ❌ Practice session access denied:', result.message);
            
            // Show subscription limit modal/notification
            const limitNotification = document.createElement('div');
            limitNotification.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md';
            limitNotification.innerHTML = `
              <div class="text-center">
                <div class="flex items-center justify-center mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <h3 class="font-bold">Practice Limit Reached</h3>
                </div>
                <p class="text-sm mb-3">${result.message}</p>
                <a href="/profile" class="inline-block bg-white text-red-600 px-4 py-2 rounded-md font-medium hover:bg-gray-100 transition-colors">
                  View Subscription
                </a>
              </div>
            `;
            document.body.appendChild(limitNotification);
            
            setTimeout(() => {
              if (document.body.contains(limitNotification)) {
                document.body.removeChild(limitNotification);
              }
            }, 8000);
            
            return; // Don't start the session
          } else {
            console.log('[SUBSCRIPTION] ✅ Practice session access granted');
          }
        } else {
          console.warn('[SUBSCRIPTION] ⚠️ Could not check subscription limits, allowing session');
        }
      } catch (error) {
        console.error('[SUBSCRIPTION] ❌ Error checking subscription limits:', error);
        // Allow session to continue if check fails
      }
    }
    
    // Timer logic is now handled entirely by ModernTimer component
    // Just ensure conversation is not marked as time up when starting
    setConversationTimeUp(false);
    console.log('🔄 Starting/resuming conversation - timer managed by ModernTimer');
    
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
    // Check if the conversation time is up
    if (conversationTimeUp) {
      // Different messages for guest and registered users
      const message = isAuthenticated() 
        ? "Your 5-minute conversation time has ended. Please start a new conversation." 
        : "Your conversation time has ended. Sign up for unlimited time.";
      
      // Time's up notification is now handled by the TimeUpModal component in the parent
      console.log('Conversation time is up:', message);
      
      return; // Prevent continuing the conversation
    }
    
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
        
        // For guest users, make sure the timer continues if it was active
        if (!isAuthenticated() && !conversationTimeUp) {
          setIsConversationTimerActive(true);
        }
      } else {
        // Only if not paused (fully ended), start a new conversation
        toggleConversation();
      }
    }, 300);
  };
  
  // Set conversation start time when the first message is received (conversation actually starts)
  useEffect(() => {
    // Set conversation start time when we have the first message and haven't set it yet
    if (messages.length > 0 && !conversationStartTime) {
      console.log('🕐 Setting conversation start time - first message received');
      setConversationStartTime(Date.now());
    }
  }, [messages.length, conversationStartTime]);
  
  // Browser navigation protection - disabled when session is completed
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Only show warning if there are messages, user is authenticated, and session is not completed
      if (user && processedMessages.length > 0 && !sessionCompleted) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    const handlePopState = (e: PopStateEvent) => {
      // Only intercept if there are messages, user is authenticated, and session is not completed
      if (user && processedMessages.length > 0 && !sessionCompleted) {
        e.preventDefault();
        // Push the current state back to prevent navigation
        window.history.pushState(null, '', window.location.href);
        // Show our custom modal instead
        setShowLeaveModal(true);
      }
    };

    // Add event listeners
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);

    // Push a state to handle back button (only if session not completed)
    if (user && processedMessages.length > 0 && !sessionCompleted) {
      window.history.pushState(null, '', window.location.href);
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [user, processedMessages.length, sessionCompleted]);
  
  // Handle leave conversation
  const handleLeaveConversation = () => {
    // Navigate away from the conversation
    router.push('/');
  };
  
  // Calculate practice time for modal
  const getPracticeTime = () => {
    if (!conversationStartTime) return '0:00';
    const elapsed = Math.floor((Date.now() - conversationStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Handle session completion modal actions
  const handleGoHome = () => {
    console.log('🏠 Redirecting to dashboard to view progress');
    router.push('/');
  };

  const handleStartNewSession = () => {
    console.log('🔄 Starting new session');
    // Reset all session states
    setSessionCompleted(false);
    setShowCompletionModal(false);
    setConversationTimeUp(false);
    setConversationStartTime(null);
    setAnalyzedMessageIds([]);
    
    // Redirect to language selection to start fresh
    router.push('/language-selection');
  };
  
  return (
    <main className="flex flex-col text-white p-3 sm:p-4 md:p-6 lg:p-8 overflow-x-hidden min-h-screen">
      <div className="w-full max-w-7xl mx-auto h-full flex flex-col">
        {/* Language alert notification with animation states */}
        {showLanguageAlert && (
          <div 
            className={`fixed top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-amber-600 to-amber-500 text-white px-6 py-3 rounded-lg border border-amber-400/20 z-50 flex items-center space-x-3 max-w-md
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
        
        {/* Timer positioned aligned with Conversation Transcript container top line */}
        <div className="fixed top-32 sm:top-36 md:top-40 lg:top-44 right-2 sm:right-4 z-40">
          <div className="scale-75 sm:scale-90 md:scale-100">
            <ModernTimer
              initialTime={getConversationDuration(isAuthenticated())}
              isActive={isConversationTimerActive}
              onTimeUp={async () => {
                console.log('⏰ Timer reached 0 - immediately stopping conversation');
                setConversationTimeUp(true);
                setIsConversationTimerActive(false);
                
                // Immediately stop the conversation to prevent AI from continuing to speak
                stopConversation();
                
                // Auto-save conversation when time is up (5 minutes completed)
                if (user && processedMessages.length > 0) {
                  console.log('🔄 Auto-saving conversation at timer end...');
                  
                  // Show loading state while saving
                  setShowSavingLoader(true);
                  
                  const saveResult = await saveConversationProgress();
                  
                  // Hide loading state and show completion modal
                  setShowSavingLoader(false);
                  setSessionCompleted(true);
                  setShowCompletionModal(true);
                } else {
                  // For guests or no messages, just end normally
                  handleEndConversation();
                }
              }}
              className=""
            />
          </div>
        </div>

        {/* Header - Redesigned */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            {language.charAt(0).toUpperCase() + language.slice(1)} Conversation
          </h1>
          <p className="text-white/80 mt-2">
            Level: {level.toUpperCase()} - Click the microphone button to start talking
          </p>
        </div>

        {/* User Selection Summary */}
        <div className="bg-white border-2 border-[#4ECFBF] rounded-xl p-4 mb-4 mx-auto max-w-4xl relative z-10 shadow-lg">
          <div className="flex flex-wrap items-center justify-center gap-4 text-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733 18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98A1 1 0 0117 18H10a1 1 0 01-.894-1.447l.99-1.98.019-.038 2.991-5.982A1 1 0 0114 8h-1z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold text-lg">
                {language.charAt(0).toUpperCase() + language.slice(1)}
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#FFD63A] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-gray-800" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold text-lg">Level {level.toUpperCase()}</span>
            </div>
            
            {topic && (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center shadow-lg">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="font-semibold text-lg">
                  {topic === 'custom' ? (
                    userPrompt ? `Custom: ${userPrompt.length > 30 ? userPrompt.substring(0, 30) + '...' : userPrompt}` : 'Custom Topic'
                  ) : (
                    topic.charAt(0).toUpperCase() + topic.slice(1).replace(/([A-Z])/g, ' $1')
                  )}
                </span>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#F75A5A] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold text-lg drop-shadow-sm">
                {isAuthenticated() ? 'Unlimited Time' : `${Math.floor(conversationDuration / 60)} min limit`}
              </span>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-stretch justify-center w-full">
          {/* Main Content Area - Redesigned for better responsiveness and alignment */}
          <div className="w-full">
            {/* Transcript Sections - Now shown immediately */}
            {showMessages && (
              <div className="w-full transition-all duration-700 ease-in-out opacity-100 translate-y-0">
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 sm:gap-4 lg:gap-6 w-full">
                  {/* Real-time Transcript Component */}
                  <div className="relative bg-white border border-gray-200 rounded-lg p-3 sm:p-4 lg:p-6 shadow-lg flex flex-col min-h-[450px] sm:min-h-[500px] md:min-h-[550px] lg:min-h-[650px]">
                    <h3 className="text-base sm:text-lg lg:text-xl font-semibold mb-2 sm:mb-4 text-[#F75A5A] flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                      Real-time Transcript
                    </h3>
                    <div className="bg-[#F0FAFA] rounded-lg border border-[#4ECFBF]/30 p-3 sm:p-4 lg:p-6 flex-grow overflow-y-auto pb-16">
                      <SentenceConstructionAssessment
                        transcript={currentTranscript}
                        isRecording={isRecording}
                        onStopRecording={handleEndConversation}
                        onContinueLearning={handleContinueLearning}
                        language={language}
                        level={level}
                        exerciseType={exerciseType}
                        onChangeExerciseType={setExerciseType}
                        onAnalyzeRef={analyzeButtonRef}
                        onMessageAnalyzed={(messageId) => setAnalyzedMessageIds(prev => [...prev, messageId])}
                        currentMessageId={messages.length > 0 ? `${messages[messages.length - 1].role}-${messages.length - 1}` : undefined}
                      />
                    </div>
                    
                    <div className="sticky bottom-0 left-0 right-0 w-full mt-auto py-3 bg-transparent border-t border-slate-700/30 backdrop-blur-sm z-10">
                      {/* Sign in prompt for guest users when time is up */}
                      {!isAuthenticated() && conversationTimeUp && (
                        <div className="mb-3 p-4 bg-red-50 border border-red-200 rounded-lg text-center">
                          <h4 className="text-red-800 font-medium mb-1">Guest time limit reached</h4>
                          <p className="text-red-700 text-sm mb-3">
                            Your guest conversation time has ended.
                            <span className="block mt-1 font-medium">
                              Try a new assessment or sign in for longer conversations
                            </span>
                          </p>
                          <a 
                            href="/auth/login"
                            className="inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                            </svg>
                            Sign in for unlimited time
                          </a>
                        </div>
                      )}
                      <Button
                        type="button"
                        onClick={(e) => handleToggleRecording(e)}
                        onTouchStart={(e) => e.preventDefault()}
                        aria-label={isRecording ? "Stop recording" : "Start recording"}
                        className={`w-full py-3 sm:py-4 relative flex items-center justify-center gap-2 sm:gap-3 transition-all duration-300 rounded-lg ${isRecording 
                          ? 'bg-[#F75A5A] hover:bg-[#E55252]' 
                          : (!isAuthenticated() && conversationTimeUp) 
                            ? 'bg-gray-400 cursor-not-allowed' 
                            : 'bg-[#FFD63A] hover:bg-[#ECC235]'} 
                          ${isAttemptingToRecord ? 'opacity-80 cursor-wait' : 'opacity-100'}`}
                        disabled={isAttemptingToRecord || (!isAuthenticated() && conversationTimeUp)}
                      >
                        {isAttemptingToRecord ? (
                          <>
                            <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span className="font-medium text-white">Initializing microphone...</span>
                          </>
                        ) : isRecording ? (
                          <>
                            <div className="relative h-6 w-6 flex items-center justify-center">
                              <div className="audio-wave">
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                              </div>
                            </div>
                            <span className="font-medium text-white">Recording... Click to stop</span>
                          </>
                        ) : (
                          <>
                            <MicrophoneIcon isRecording={false} size={20} />
                            <span className="font-medium text-gray-800 font-bold">Click to start speaking</span>
                          </>
                        )}
                      </Button>
                    </div>
                    
                    {/* Error message */}
                    {localError && (
                      <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-200 max-w-md text-center mx-auto">
                        <p>{localError}</p>
                      </div>
                    )}
                    
                    {/* Warning message when content is not in target language */}
                    {isRecording && messages.length > 0 && messages[messages.length - 1].role === 'user' && 
                     !isInTargetLanguage(messages[messages.length - 1].content) && (
                      <div className="mt-4 px-4 py-3 bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-200 text-center">
                        <p className="text-sm">Please speak in {language.charAt(0).toUpperCase() + language.slice(1)} to analyze your sentence.</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Conversation Transcript Section */}
                  <div className="relative bg-white border border-gray-200 rounded-lg p-3 sm:p-4 lg:p-6 shadow-lg flex flex-col h-[450px] sm:h-[500px] md:h-[550px] lg:h-[650px]">
                    <div className="flex items-center justify-between mb-2 sm:mb-4">
                      <h3 className="text-base sm:text-lg lg:text-xl font-semibold text-[#F75A5A] flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        Conversation Transcript
                      </h3>
                    </div>
                    <div className="bg-[#F0FAFA] rounded-lg border border-[#4ECFBF]/30 p-3 sm:p-4 lg:p-6 flex-1 min-h-[300px] sm:min-h-[350px] md:min-h-[400px] lg:min-h-[450px] max-h-[60vh] sm:max-h-[65vh] md:max-h-[70vh] overflow-y-auto custom-scrollbar flex flex-col">
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
                              
                              return (
                                <div 
                                  key={`${message.role}-${index}-${message.itemId || messageTime.getTime()}`}
                                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                                >
                                  {message.role !== 'user' ? (
                                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-[#AFF4EB] flex items-center justify-center mr-2 shadow-md">
                                      <span className="text-xs font-bold text-gray-800">T</span>
                                    </div>
                                  ) : (
                                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-[#D6E6FF] flex items-center justify-center ml-2 order-last shadow-md">
                                      <span className="text-xs font-bold text-gray-800">{firstName.charAt(0)}</span>
                                    </div>
                                  )}
                                  <div 
                                    className={`max-w-[85%] sm:max-w-[80%] break-words p-3 sm:p-4 lg:p-5 rounded-2xl shadow-md ${
                                      message.role === 'user' 
                                        ? 'bg-[#D6E6FF] text-gray-800 ml-2 rounded-tr-none'
                                        : 'bg-[#AFF4EB] text-gray-800 mr-2 rounded-tl-none'
                                    }`}
                                    style={{
                                      wordBreak: 'break-word',
                                      overflowWrap: 'break-word',
                                      whiteSpace: 'pre-wrap'
                                    }}
                                  >
                                    <div className="flex items-center justify-between mb-1 text-gray-800">
                                      <span className="text-xs font-semibold">
                                        {message.role === 'user' ? firstName : 'Tutor'}
                                      </span>
                                      <span className="text-xs opacity-75 ml-2">
                                        {timeDisplay}
                                      </span>
                                    </div>
                                    <p className="text-xs sm:text-sm leading-relaxed mt-1 text-gray-800">{message.content}</p>
                                    
                                    {/* Analyze button in user message bubble - only show for messages that haven't been analyzed yet */}
                                    {message.role === 'user' && 
                                     message.content.trim().length > 0 && 
                                     analyzeButtonRef.current && 
                                     !analyzedMessageIds.includes(`${message.role}-${index}`) && (
                                      <div className="mt-2 flex justify-end">
                                          <button
                                            onClick={() => {
                                              // Mark this specific message as analyzed
                                              setAnalyzedMessageIds(prev => [...prev, `${message.role}-${index}`]);
                                              // Call the analyze function
                                              if (analyzeButtonRef.current) analyzeButtonRef.current();
                                            }}
                                            className="px-2 py-1.5 sm:py-1 bg-[#FFD63A] hover:bg-[#FFA955] text-gray-800 text-xs rounded-md shadow-sm transition-all duration-300 flex items-center space-x-1"
                                          >
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                            </svg>
                                            <span>Analyze Sentence</span>
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })
                        ) : (
                          <div className="flex justify-center items-center h-full flex-1">
                            <div className="text-center p-6 rounded-lg bg-[#4ECFBF]/10 border border-[#4ECFBF]/20 animate-fadeIn w-full">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-4 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                              </svg>
                              <p className="text-[#4ECFBF] font-medium text-lg">Your conversation will appear here</p>
                              <p className="text-slate-400 text-base mt-2">Click the microphone button to start talking</p>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} className="mt-auto" />
                      </div>
                    </div>
                    <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 bg-[#4ECFBF] h-1 w-1/3 rounded-full opacity-70"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Leave Conversation Modal */}
      <LeaveConversationModal
        isOpen={showLeaveModal}
        onClose={() => setShowLeaveModal(false)}
        onLeave={handleLeaveConversation}
        messages={processedMessages}
        language={language}
        level={level}
        topic={topic}
        conversationStartTime={conversationStartTime || undefined}
        practiceTime={getPracticeTime()}
      />

      {/* Session Completion Modal */}
      <SessionCompletionModal
        isOpen={showCompletionModal}
        onGoHome={handleGoHome}
        onStartNew={handleStartNewSession}
        sessionDuration={getPracticeTime()}
        messageCount={processedMessages.length}
        language={language}
        level={level}
      />

      {/* Saving Progress Loading Modal */}
      {showSavingLoader && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 mx-4 max-w-sm w-full text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Saving Your Progress</h3>
            <p className="text-gray-600">Please wait while we save your conversation...</p>
          </div>
        </div>
      )}
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
      className="text-gray-800"
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}
