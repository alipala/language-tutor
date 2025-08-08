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
import DraggableTimer from '@/components/draggable-timer';
import SaveProgressButton from '@/components/save-progress-button';
import LeaveConversationModal from '@/components/leave-conversation-modal';
import SessionCompletionModal from '@/components/session-completion-modal';
import BackgroundAnalysisCard from '@/components/background-analysis-card';
import ConversationHelpModal from '@/components/conversation-help-modal';
import ConversationHelpHintButton from '@/components/conversation-help-hint-button';
import ConversationHelpTimeoutNotification from '@/components/conversation-help-timeout-notification';
import { useConversationHelpSystem } from '@/hooks/useConversationHelpSystem';
import { getApiUrl } from '@/lib/api-utils';
import { 
  processBackgroundSentence, 
  shouldConsiderForAnalysis, 
  getCachedAnalysis,
  setCachedAnalysis,
  BackgroundAnalysisResponse,
  submitAnalysisFeedback,
  markAsRejected,
  isRejected,
  SentenceAnalysisFeedback
} from '@/lib/background-sentence-api';

interface SpeechClientProps {
  language: string;
  level: string;
  topic?: string;
  userPrompt?: string;
  onTimeUp?: () => void; // Callback to trigger TimeUpModal in parent
}

export default function SpeechClient({ language, level, topic, userPrompt, onTimeUp }: SpeechClientProps) {
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
  
  // Background sentence analysis state
  const [backgroundAnalyses, setBackgroundAnalyses] = useState<BackgroundAnalysisResponse[]>([]);
  const [isProcessingBackground, setIsProcessingBackground] = useState(false);
  const [currentAnalysisIndex, setCurrentAnalysisIndex] = useState(0);
  
  // Feedback system state
  const [feedbackModal, setFeedbackModal] = useState<{
    isOpen: boolean;
    type: 'rejection' | 'timeout' | 'quality';
    context: {
      sentence: string;
      reason?: string;
      duration?: number;
    };
  } | null>(null);
  
  // Timeout management for stuck analyses
  const [analysisTimeouts, setAnalysisTimeouts] = useState<Map<string, NodeJS.Timeout>>(new Map());
  
  // Reset current analysis index when new analyses are added
  useEffect(() => {
    if (backgroundAnalyses.length > 0) {
      setCurrentAnalysisIndex(backgroundAnalyses.length - 1); // Always show the latest analysis
    }
  }, [backgroundAnalyses.length]);
  
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
  const [isReviewingAnalysis, setIsReviewingAnalysis] = useState(false);
  
  // Voice selection state for displaying tutor avatar
  const [selectedVoice, setSelectedVoice] = useState<string>('alloy');
  const [voiceLoading, setVoiceLoading] = useState(true);
  
  // Information modal state
  const [showInfoModal, setShowInfoModal] = useState(true);
  const [modalDismissed, setModalDismissed] = useState(false);
  
  // Initialize new conversation help system
  const {
    helpSettings,
    updateHelpSettings,
    helpData,
    isLoading: isHelpLoading,
    error: helpError,
    isHelpReady,
    isModalOpen: isHelpModalOpen,
    showHelpModal,
    closeHelpModal,
    selectSuggestedResponse,
    trackHelpUsage,
    timeoutNotification
  } = useConversationHelpSystem(language, level, topic);
  
  // Voice data mapping for avatars and names
  const VOICE_DATA = {
    alloy: { name: 'Alloy', avatar: '/images/tutors/alloy.svg', personality: 'Professional and encouraging' },
    ash: { name: 'Ash', avatar: '/images/tutors/ash.svg', personality: 'Warm and approachable' },
    ballad: { name: 'Ballad', avatar: '/images/tutors/ballad.svg', personality: 'Expressive and articulate' },
    coral: { name: 'Coral', avatar: '/images/tutors/coral.svg', personality: 'Energetic and motivating' },
    echo: { name: 'Echo', avatar: '/images/tutors/echo.svg', personality: 'Patient and supportive' },
    sage: { name: 'Sage', avatar: '/images/tutors/sage.svg', personality: 'Engaging storyteller' },
    shimmer: { name: 'Shimmer', avatar: '/images/tutors/shimmer.svg', personality: 'Confident and authoritative' },
    verse: { name: 'Verse', avatar: '/images/tutors/verse.svg', personality: 'Dynamic and modern' }
  };
  
  // Fetch user's voice preference
  useEffect(() => {
    const fetchVoicePreference = async () => {
      if (!user) {
        setVoiceLoading(false);
        return;
      }

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setVoiceLoading(false);
          return;
        }

        const response = await fetch(`${getApiUrl()}/auth/get-voice`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          console.log('[VOICE_DISPLAY] Fetched voice preference:', data.voice);
          setSelectedVoice(data.voice || 'alloy');
        } else {
          console.error('[VOICE_DISPLAY] Failed to fetch voice preference');
          setSelectedVoice('alloy');
        }
      } catch (error) {
        console.error('[VOICE_DISPLAY] Error fetching voice preference:', error);
        setSelectedVoice('alloy');
      } finally {
        setVoiceLoading(false);
      }
    };

    fetchVoicePreference();
  }, [user]);

  // Fetch subscription information for the modal
  useEffect(() => {
    const fetchSubscriptionInfo = async () => {
      if (!user) return;

      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch(`${getApiUrl()}/api/stripe/subscription-status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          const displayElement = document.getElementById('subscription-info-display');
          
          if (displayElement && data.limits) {
            const { limits } = data;
            let infoText = '';
            
            if (limits.is_unlimited) {
              infoText = '✨ You have unlimited speaking time! Practice as much as you want.';
            } else {
              const minutesRemaining = Math.round(limits.minutes_remaining || 0);
              const minutesLimit = limits.minutes_limit || 0;
              const minutesUsed = Math.round(limits.minutes_used || 0);
              
              infoText = `You have ${minutesRemaining} minutes remaining this ${data.period || 'month'}. (${minutesUsed}/${minutesLimit} minutes used)`;
            }
            
            displayElement.textContent = infoText;
          }
        } else {
          console.error('[SUBSCRIPTION_INFO] Failed to fetch subscription status');
          const displayElement = document.getElementById('subscription-info-display');
          if (displayElement) {
            displayElement.textContent = 'Unable to load subscription information.';
          }
        }
      } catch (error) {
        console.error('[SUBSCRIPTION_INFO] Error fetching subscription info:', error);
        const displayElement = document.getElementById('subscription-info-display');
        if (displayElement) {
          displayElement.textContent = 'Unable to load subscription information.';
        }
      }
    };

    // Only fetch when the modal is shown and user is authenticated
    if (showInfoModal && user) {
      fetchSubscriptionInfo();
    }
  }, [showInfoModal, user]);
  
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
  const { 
    isRecording, 
    messages, 
    error, 
    toggleConversation, 
    stopConversation, 
    startConversation, 
    initialize, 
    getFormattedConversationHistory,
    pauseConversation,      // NEW
    resumeConversation,     // NEW
    isPaused: isRealtimePaused  // NEW - renamed to avoid conflict
  } = useRealtime();
  
  // Track user speaking state for modal fade-out - only when modal is open
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const previousRecordingState = useRef(false);

  // Detect when user STARTS speaking (recording transitions from false to true) while modal is open
  useEffect(() => {
    // Only trigger when recording state changes from false to true AND modal is open
    if (isRecording && !previousRecordingState.current && isHelpModalOpen) {
      console.log('[USER_SPEAKING] User started NEW recording session while modal is open - setting isUserSpeaking to true');
      setIsUserSpeaking(true);
    } else if (!isRecording) {
      console.log('[USER_SPEAKING] User stopped speaking - setting isUserSpeaking to false');
      setIsUserSpeaking(false);
    }
    
    // Update the previous state
    previousRecordingState.current = isRecording;
  }, [isRecording, isHelpModalOpen]);
  
  // Process messages for display and group sentences from the same speech segment
  const processedMessages = useMemo(() => {
    // First, map the messages to add consistent IDs and group information
    const mappedMessages = messages.map((message, index) => {
      // Extract base item ID to identify groups from the same speech segment
      const baseItemId = message.itemId?.split('-group-')[0] || `message-${index}`;
      const isGroupPart = message.itemId?.includes('-group-') || false;
      
      return {
        ...message,
        itemId: message.itemId || `message-${index}`,
        role: message.role === 'assistant' ? 'assistant' : 'user',
        baseItemId,
        isGroupPart
      };
    });

    // Group messages by baseItemId and role to identify speech segment groups
    const groupedMessages = mappedMessages.reduce((acc, message, index) => {
      const key = `${message.baseItemId}-${message.role}`;
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push({ ...message, originalIndex: index });
      return acc;
    }, {} as Record<string, Array<typeof mappedMessages[0] & { originalIndex: number }>>);

    // Add grouping information to messages
    const messagesWithGrouping = mappedMessages.map((message, index) => {
      const key = `${message.baseItemId}-${message.role}`;
      const group = groupedMessages[key];
      const isGrouped = group && group.length > 1;
      const groupIndex = isGrouped ? group.findIndex(m => m.originalIndex === index) : 0;
      const isFirstInGroup = groupIndex === 0;
      const isLastInGroup = groupIndex === group.length - 1;
      
      return {
        ...message,
        isGrouped,
        isFirstInGroup,
        isLastInGroup,
        groupSize: group ? group.length : 1,
        groupIndex
      };
    });

    // Deduplicate messages by filtering out those with very similar content
    const filteredMessages: typeof messagesWithGrouping = [];
    const seenContents: {content: string, index: number, role: string}[] = [];

    // First pass: collect all messages and their indices
    messagesWithGrouping.forEach((message, index) => {
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
    for (let i = 0; i < messagesWithGrouping.length; i++) {
      const message = messagesWithGrouping[i];
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
    
    // Enhanced language detection patterns with more comprehensive vocabulary
    const languagePatterns: Record<string, RegExp[]> = {
      dutch: [
        // Core Dutch words - pronouns, articles, common verbs
        /\b(ik|je|hij|zij|het|de|een|en|is|zijn|ben|was|waren|hebben|heeft|had|mijn|jouw|zijn|haar)\b/i,
        // Common Dutch verbs and adjectives
        /\b(goed|slecht|mooi|lelijk|groot|klein|nieuw|oud|veel|weinig|kom|komt|ga|gaat|zie|ziet|doe|doet)\b/i,
        // Dutch greetings and common phrases
        /\b(hallo|dag|goedemorgen|goedemiddag|goedenavond|doei|tot ziens|dankjewel|alsjeblieft|graag)\b/i,
        // Dutch-specific words from the conversation
        /\b(sta|staat|ontbijt|ontbijten|lees|lezen|boek|school|huiswerk|vrienden|middag|ochtend|avond)\b/i,
        // Dutch prepositions and conjunctions
        /\b(van|naar|met|voor|door|over|onder|tussen|na|om|uit|in|op|aan|bij|tot|als|dat|omdat)\b/i
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
    const targetPatterns = languagePatterns[currentLanguage] || [];
    const containsTargetLanguage = targetPatterns.some((pattern: RegExp) => pattern.test(lowerText));
    
    // Check if text contains English patterns (for non-English languages)
    const containsEnglish = language !== 'english' ? 
      languagePatterns.english.some((pattern: RegExp) => pattern.test(lowerText)) : false;
    
    // For English mode, simple check
    if (language === 'english') {
      const hasEnglishPatterns = languagePatterns.english.some((pattern: RegExp) => pattern.test(lowerText));
      const hasNonEnglishCharacters = /[áàâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]/i.test(lowerText);
      return hasEnglishPatterns && !hasNonEnglishCharacters;
    }
    
    // For Dutch and other languages - be more permissive
    if (language === 'dutch') {
      // If it contains Dutch patterns, it's likely Dutch
      if (containsTargetLanguage) return true;
      
      // Check for Dutch-specific letter combinations
      const hasDutchCombinations = /\b(ij|aa|ee|oo|uu|eu|oe|ui)\b/i.test(lowerText);
      if (hasDutchCombinations) return true;
      
      // Check for Dutch-specific words that might not be in patterns
      const dutchSpecificWords = /\b(het|een|van|naar|met|voor|door|over|onder|tussen|na|om|uit|in|op|aan|bij|tot|als|dat|omdat|maar|ook|nog|wel|niet|geen|alle|deze|die|dit|zo|zeer|heel|erg|best|goed|slecht|mooi|lelijk|groot|klein|nieuw|oud|veel|weinig|weinig|weinig)\b/i;
      if (dutchSpecificWords.test(lowerText)) return true;
      
      // Only reject if it's clearly English AND has no Dutch characteristics
      const hasStrongEnglishIndicators = /\b(the|and|or|but|with|from|they|this|that|have|will|would|could|should)\b/i.test(lowerText);
      const hasNonDutchCharacters = /[qwxyz]/i.test(lowerText) && lowerText.length > 5;
      
      // Be permissive - only reject if clearly English
      return !(hasStrongEnglishIndicators && !containsTargetLanguage && hasNonDutchCharacters);
    }
    
    // For other languages, use similar permissive logic
    if (containsTargetLanguage) return true;
    
    // Language-specific permissive checks
    if (language === 'spanish') {
      const hasSpanishCharacters = /[ñáéíóúü]/i.test(lowerText);
      if (hasSpanishCharacters) return true;
      
      const hasStrongEnglishIndicators = /\b(the|and|or|but|with|from|they|this|that|have|will|would|could|should)\b/i.test(lowerText);
      return !(hasStrongEnglishIndicators && !containsTargetLanguage);
    }
    
    if (language === 'german') {
      const hasGermanCharacters = /[äöüß]/i.test(lowerText);
      if (hasGermanCharacters) return true;
      
      const hasStrongEnglishIndicators = /\b(the|and|or|but|with|from|they|this|that|have|will|would|could|should)\b/i.test(lowerText);
      return !(hasStrongEnglishIndicators && !containsTargetLanguage);
    }
    
    if (language === 'french') {
      const hasFrenchCharacters = /[éèêëàâçîïôùûüÿ]/i.test(lowerText);
      if (hasFrenchCharacters) return true;
      
      const hasStrongEnglishIndicators = /\b(the|and|or|but|with|from|they|this|that|have|will|would|could|should)\b/i.test(lowerText);
      return !(hasStrongEnglishIndicators && !containsTargetLanguage);
    }
    
    if (language === 'portuguese') {
      const hasPortugueseCharacters = /[áàâãéêíóôõúç]/i.test(lowerText);
      if (hasPortugueseCharacters) return true;
      
      const hasStrongEnglishIndicators = /\b(the|and|or|but|with|from|they|this|that|have|will|would|could|should)\b/i.test(lowerText);
      return !(hasStrongEnglishIndicators && !containsTargetLanguage);
    }
    
    // Default: be permissive and allow the text through
    return true;
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

  // Enhanced background sentence analysis function with caching and smart filtering
  const handleBackgroundAnalysis = useCallback(async (text: string, messageIndex: number) => {
    console.log(`🔄 [BACKGROUND] Starting analysis check for: "${text.substring(0, 50)}..."`);
    
    // Build conversation context for enhanced filtering - but exclude the current message to avoid false repetition detection
    const recentUserMessages = messages
      .filter(msg => msg.role === 'user')
      .slice(-5) // Get last 5 user messages
      .map(msg => msg.content)
      .filter(content => content !== text); // Exclude current message to avoid false repetition

    console.log(`🔍 [BACKGROUND] Recent user messages for context:`, recentUserMessages);

    // Enhanced client-side check with conversation context and language awareness
    const analysisDecision = shouldConsiderForAnalysis(text, recentUserMessages, language);
    
    if (!analysisDecision.shouldAnalyze) {
      console.log(`⏭️ [BACKGROUND] Skipping analysis - ${analysisDecision.reason}:`, text.substring(0, 50) + '...');
      return;
    }

    console.log(`🎯 [BACKGROUND] Analysis approved - ${analysisDecision.reason} (confidence: ${analysisDecision.confidence}):`, text.substring(0, 50) + '...');

    // Check cache first to avoid duplicate API calls
    const cachedResult = getCachedAnalysis(text, language, level);
    if (cachedResult) {
      console.log('⚡ [CACHE] Using cached analysis result');
      setBackgroundAnalyses(prev => {
        // Check if we already have this analysis in the UI
        const isDuplicate = prev.some(existing => 
          existing.recognized_text.toLowerCase().trim() === cachedResult.recognized_text.toLowerCase().trim()
        );
        
        if (isDuplicate) {
          console.log('⏭️ [CACHE] Skipping duplicate cached analysis for UI:', cachedResult.recognized_text.substring(0, 50) + '...');
          return prev; // Don't add duplicate
        }
        
        const newAnalyses = [...prev, cachedResult];
        return newAnalyses.slice(-5); // Keep only last 5
      });
      return;
    }

    // Don't analyze if already processing or if we already have too many analyses
    if (isProcessingBackground || backgroundAnalyses.length >= 8) {
      console.log('⏭️ [BACKGROUND] Skipping analysis - already processing or too many analyses');
      return;
    }

    // Create a unique key for this analysis to track timeouts
    const analysisKey = `${text.substring(0, 30)}-${Date.now()}`;
    
    try {
      setIsProcessingBackground(true);
      console.log('🔄 [BACKGROUND] Starting background analysis for:', text.substring(0, 50) + '...');

      // Set up a timeout to prevent stuck analyses
      const timeoutId = setTimeout(() => {
        console.log('⏰ [BACKGROUND] Analysis timeout for:', text.substring(0, 50) + '...');
        setIsProcessingBackground(false);
        
        // Clean up the timeout from our tracking
        setAnalysisTimeouts(prev => {
          const newTimeouts = new Map(prev);
          newTimeouts.delete(analysisKey);
          return newTimeouts;
        });
      }, 15000); // 15 second timeout

      // Track this timeout
      setAnalysisTimeouts(prev => {
        const newTimeouts = new Map(prev);
        newTimeouts.set(analysisKey, timeoutId);
        return newTimeouts;
      });

      // Build conversation context from recent messages
      const recentMessages = messages.slice(-5); // Last 5 messages for context
      const conversationContext = recentMessages
        .map(msg => `${msg.role === 'user' ? 'Student' : 'Tutor'}: ${msg.content}`)
        .join('\n');

      const result = await processBackgroundSentence({
        text: text,
        language: language,
        level: level,
        exercise_type: 'free',
        conversation_context: conversationContext
      });

      // Clear the timeout since we got a result
      clearTimeout(timeoutId);
      setAnalysisTimeouts(prev => {
        const newTimeouts = new Map(prev);
        newTimeouts.delete(analysisKey);
        return newTimeouts;
      });

      if (result.analyzed && result.analysis) {
        console.log('✅ [BACKGROUND] Analysis completed:', result.analysis.analysis_id);
        
        // Cache the result for future use
        setCachedAnalysis(text, language, level, result.analysis);
        
        // Add to background analyses with deduplication and limit
        setBackgroundAnalyses(prev => {
          // Check if we already have an analysis for this exact text
          const isDuplicate = prev.some(existing => 
            existing.recognized_text.toLowerCase().trim() === result.analysis!.recognized_text.toLowerCase().trim()
          );
          
          if (isDuplicate) {
            console.log('⏭️ [BACKGROUND] Skipping duplicate analysis result for UI:', result.analysis!.recognized_text.substring(0, 50) + '...');
            return prev; // Don't add duplicate
          }
          
          const newAnalyses = [...prev, result.analysis!];
          // Keep only the last 5 analyses to prevent UI clutter
          return newAnalyses.slice(-5);
        });
      } else {
        console.log('⏭️ [BACKGROUND] Analysis skipped by backend:', result.reason);
      }
    } catch (error) {
      console.error('❌ [BACKGROUND] Error in background analysis:', error);
      
      // Clear any pending timeout for this analysis
      setAnalysisTimeouts(prev => {
        const newTimeouts = new Map(prev);
        const timeoutId = newTimeouts.get(analysisKey);
        if (timeoutId) {
          clearTimeout(timeoutId);
          newTimeouts.delete(analysisKey);
        }
        return newTimeouts;
      });
    } finally {
      setIsProcessingBackground(false);
    }
  }, [language, level, messages, isProcessingBackground, backgroundAnalyses.length]);

  // Handle transcript updates and language detection
  useEffect(() => {
    // Extract the latest user message for the transcript
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const latestUserMessage = userMessages[userMessages.length - 1];
      const messageIndex = userMessages.length - 1;
      
      console.log('🔍 [TRANSCRIPT] Processing user message:', latestUserMessage.content.substring(0, 50) + '...');
      
      // For English conversations, always process the message
      // For other languages, check if it's in the target language
      const shouldProcessMessage = language === 'english' || isInTargetLanguage(latestUserMessage.content);
      
      if (shouldProcessMessage) {
        setCurrentTranscript(latestUserMessage.content);
        
        // Always trigger background analysis for user messages (remove restrictive timing)
        if (latestUserMessage.content.trim().length > 0) {
          console.log('🎯 [TRANSCRIPT] Triggering background analysis for:', latestUserMessage.content.substring(0, 50) + '...');
          
          // Reduced delay to make analysis more responsive
          setTimeout(() => {
            handleBackgroundAnalysis(latestUserMessage.content, messageIndex);
          }, 1000); // Reduced from 3000ms to 1000ms for faster response
        }
      } else {
        // Clear the transcript or set a placeholder message
        setCurrentTranscript('');
        console.log('⏭️ [TRANSCRIPT] Skipping message - not in target language:', latestUserMessage.content.substring(0, 50) + '...');
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
          },
          body: JSON.stringify({
            messages: messagesToSave,
            duration_minutes: durationMinutes,
            language: language,
            level: level,
            topic: topic
          })
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

      // Track speaking time for subscription limits (new duration-based tracking)
      try {
        console.log('[SUBSCRIPTION] Tracking speaking time for subscription limits');
        const speakingTimeResponse = await fetch(`${getApiUrl()}/api/stripe/track-speaking-time`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            speaking_minutes: durationMinutes,
            session_completed: durationMinutes >= 5 // Only count as completed session if >= 5 minutes
          })
        });

        if (speakingTimeResponse.ok) {
          const speakingTimeResult = await speakingTimeResponse.json();
          console.log('[SUBSCRIPTION] ✅ Speaking time tracked:', speakingTimeResult);
        } else {
          const speakingTimeError = await speakingTimeResponse.json();
          console.warn('[SUBSCRIPTION] ⚠️ Failed to track speaking time:', speakingTimeError);
        }
      } catch (speakingTimeError) {
        console.error('[SUBSCRIPTION] ❌ Error tracking speaking time:', speakingTimeError);
      }

    } catch (error) {
      console.error('[AUTO_SAVE] ❌ Error auto-saving conversation:', error);
    }
  };
  
  // Note: Timer logic is now handled entirely by the DraggableTimer component
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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03 8-9 8s9 3.582 9 8z" />
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

    // Start the conversation timer when user clicks "Click to start speaking"
    if (!conversationStartTime && !isAuthenticated()) {
      console.log('🎯 User clicked start speaking - setting conversation start time for timer');
      const urlParams = new URLSearchParams(window.location.search);
      const planParam = urlParams.get('plan');
      
      if (planParam) {
        const startTime = new Date().toISOString();
        sessionStorage.setItem(`plan_${planParam}_conversationStartTime`, startTime);
        setConversationStartTime(Date.now());
        console.log('🕐 Conversation timer will start when AI responds');
      }
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
    
    // Timer logic is now handled entirely by DraggableTimer component
    // Just ensure conversation is not marked as time up when starting
    setConversationTimeUp(false);
    console.log('🔄 Starting/resuming conversation - timer managed by DraggableTimer');
    
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
    
    // Emit conversation ended event for help system
    window.dispatchEvent(new CustomEvent('conversation-ended'));
    
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
      // Auto-save conversation and track speaking time for partial sessions
      if (user && processedMessages.length > 0 && !sessionCompleted && conversationStartTime) {
        // Calculate duration for partial session
        const durationMinutes = (Date.now() - conversationStartTime) / (1000 * 60);
        
        // Only track if session is meaningful (>30 seconds)
        if (durationMinutes > 0.5) {
          console.log('[PARTIAL_SESSION] Auto-saving partial session on page unload:', durationMinutes.toFixed(1), 'minutes');
          
          // Use sendBeacon for reliable tracking during page unload
          const token = localStorage.getItem('token');
          const trackingData = {
            speaking_minutes: durationMinutes,
            session_completed: false, // Mark as partial session
            token: token // Include token for authentication
          };
          
          if (token && navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(trackingData)], { type: 'application/json' });
            const success = navigator.sendBeacon(
              `${window.location.origin}/api/stripe/track-speaking-time`,
              blob
            );
            console.log('[PARTIAL_SESSION] Beacon sent:', success);
          }
        }
        
        // Still show warning for user experience
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    const handlePopState = (e: PopStateEvent) => {
      // Auto-track speaking time for partial sessions BEFORE showing modal
      if (user && processedMessages.length > 0 && !sessionCompleted && conversationStartTime) {
        // Calculate duration for partial session
        const durationMinutes = (Date.now() - conversationStartTime) / (1000 * 60);
        
        // Only track if session is meaningful (>30 seconds)
        if (durationMinutes > 0.5) {
          console.log('[PARTIAL_SESSION] Auto-saving partial session on back button:', durationMinutes.toFixed(1), 'minutes');
          
          // Use sendBeacon for reliable tracking during navigation
          const token = localStorage.getItem('token');
          const trackingData = {
            speaking_minutes: durationMinutes,
            session_completed: false, // Mark as partial session
            token: token // Include token for authentication
          };
          
          if (token && navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(trackingData)], { type: 'application/json' });
            const success = navigator.sendBeacon(
              `${window.location.origin}/api/stripe/track-speaking-time`,
              blob
            );
            console.log('[PARTIAL_SESSION] Back button beacon sent:', success);
          }
        }
        
        // Then handle the navigation prevention
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
  }, [user, processedMessages.length, sessionCompleted, conversationStartTime]);
  
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
        
        {/* Draggable Timer - Now floating and draggable */}
        <DraggableTimer
          initialTime={getConversationDuration(isAuthenticated())}
          isActive={isConversationTimerActive}
          onTimeUp={async () => {
            console.log('⏰ Timer reached 0 - immediately stopping conversation');
            setConversationTimeUp(true);
            setIsConversationTimerActive(false);
            
            // Emit conversation time-up event for help system
            window.dispatchEvent(new CustomEvent('conversation-time-up'));
            
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
              // For guests or no messages, trigger the TimeUpModal via parent callback
              if (onTimeUp) {
                console.log('🎯 Calling parent onTimeUp callback to show TimeUpModal');
                onTimeUp();
              } else {
                handleEndConversation();
              }
            }
          }}
        />

        {/* Header - Redesigned */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            {language.charAt(0).toUpperCase() + language.slice(1)} Conversation
          </h1>
          <p className="text-white/80 mt-2">
            Level: {level.toUpperCase()} - Click the microphone button to start talking
          </p>
        </div>

        {/* Information Modal - Speech Optimization Tips */}
        {showInfoModal && !modalDismissed && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">💡 Important Information</h3>
                </div>
                <button
                  onClick={() => {
                    setModalDismissed(true);
                    setShowInfoModal(false);
                  }}
                  className="p-1 rounded-full hover:bg-gray-100 transition-colors"
                  aria-label="Close modal"
                >
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Modal Content */}
              <div className="p-4">
                {/* 2x2 Grid Layout */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {/* Quiet Environment */}
                  <div className="flex flex-col items-center text-center p-3 bg-green-50 rounded-lg border border-green-100">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mb-2">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Find a Quiet Space</h4>
                    <p className="text-xs text-gray-600">Choose a location with minimal background noise for better speech recognition.</p>
                  </div>
                  
                  {/* Headphones */}
                  <div className="flex flex-col items-center text-center p-3 bg-purple-50 rounded-lg border border-purple-100">
                    <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg">🎧</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Use Headphones</h4>
                    <p className="text-xs text-gray-600">Headphones prevent audio feedback and provide clearer AI tutor responses.</p>
                  </div>
                  
                  {/* Clear Speech */}
                  <div className="flex flex-col items-center text-center p-3 bg-orange-50 rounded-lg border border-orange-100">
                    <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center mb-2">
                      <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Speak Clearly</h4>
                    <p className="text-xs text-gray-600">Speak at a normal pace and volume. Practice makes progress!</p>
                  </div>
                  
                  {/* Device Position */}
                  <div className="flex flex-col items-center text-center p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Position Your Device</h4>
                    <p className="text-xs text-gray-600">Keep your device 6-12 inches from your mouth for optimal pickup.</p>
                  </div>
                </div>
                
                {/* Subscription Info for Authenticated Users */}
                {user && (
                  <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200 rounded-lg p-3 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-medium text-teal-800">Your Speaking Time</span>
                    </div>
                    <div id="subscription-info-display" className="text-xs text-teal-700">
                      Loading your subscription details...
                    </div>
                  </div>
                )}

                {/* Ready Message */}
                <div className="flex items-center justify-center gap-2 text-gray-600 mb-4">
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm">Ready to start your {language} conversation?</span>
                </div>
                
                {/* Action Button */}
                <div className="flex justify-center">
                  <button
                    onClick={() => {
                      setModalDismissed(true);
                      setShowInfoModal(false);
                    }}
                    className="px-6 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all duration-200 shadow-md hover:shadow-lg"
                  >
                    Got it! Let's start
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* User Selection Summary - Desktop Only */}
        <div className="hidden sm:block bg-white border-2 border-[#4ECFBF] rounded-xl p-2 sm:p-3 md:p-4 mb-3 sm:mb-4 w-full relative z-10 shadow-lg">
          {/* Desktop: Original layout */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733a18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98A1 1 0 0117 18H10a1 1 0 01-.894-1.447l.99-1.98.019-.038 2.991-5.982A1 1 0 0114 8h-1z" clipRule="evenodd" />
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
                {Math.floor(conversationDuration / 60)} min
              </span>
            </div>
            
            {!voiceLoading && (
              <div className="relative">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg overflow-hidden">
                  <img 
                    src={VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.avatar || '/images/tutors/alloy.svg'} 
                    alt={`${VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.name || 'Alloy'} Avatar`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      console.error('Failed to load summary avatar:', e);
                      (e.target as HTMLImageElement).src = '/images/tutors/alloy.svg';
                    }}
                  />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full shadow-sm"></div>
              </div>
            )}
            
            
          </div>
        </div>


        <div className="flex-1 flex flex-col items-stretch justify-center w-full">
          {/* Main Content Area - Mobile-Optimized Layout */}
          <div className="w-full">
            {/* Transcript Sections - Responsive Design */}
            {showMessages && (
              <div className="w-full transition-all duration-700 ease-in-out opacity-100 translate-y-0">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 lg:gap-6 w-full">
                  {/* Real Time Sentence Analysis Component */}
                  <div className="relative bg-white border border-gray-200 rounded-lg shadow-lg flex flex-col 
                    h-[280px] sm:h-[320px] md:h-[380px] lg:h-[650px]">
                    
                    {/* Header */}
                    <div className="flex items-center justify-between p-3 sm:p-4 lg:p-6 pb-2 sm:pb-3 lg:pb-4 border-b border-gray-100">
                      <h3 className="text-sm sm:text-base lg:text-xl font-semibold text-[#F75A5A] flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <span className="hidden sm:inline">Real Time Sentence Analysis</span>
                        <span className="sm:hidden">Sentence Analysis</span>
                      </h3>
                      
                      {/* Analysis Counter and Status */}
                      <div className="flex items-center gap-2">
                        {isProcessingBackground && (
                          <div className="w-3 h-3 sm:w-4 sm:h-4 border-2 border-[#F75A5A] border-t-transparent rounded-full animate-spin"></div>
                        )}
                        {backgroundAnalyses.length > 0 && (
                          <span className="text-xs sm:text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                            {backgroundAnalyses.length}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Analysis Display */}
                    <div className="flex-1 p-3 sm:p-4 lg:p-6 pt-0 overflow-hidden">
                      <div className="bg-[#F0FAFA] rounded-lg border border-[#4ECFBF]/30 h-full flex flex-col">
                        {backgroundAnalyses.length > 0 ? (
                          <div className="flex-1 overflow-hidden">
                            {/* Mobile: Show one analysis at a time with navigation */}
                            <div className="h-full flex flex-col lg:hidden">
                              <div className="flex-1 p-3 overflow-y-auto">
                                <BackgroundAnalysisCard
                                  analysis={backgroundAnalyses[currentAnalysisIndex] || backgroundAnalyses[backgroundAnalyses.length - 1]}
                                  language={language}
                                  level={level}
                                  sessionId={user?.email || 'guest'}
                                  onClose={() => {
                                    setBackgroundAnalyses(prev => prev.filter((_, i) => i !== currentAnalysisIndex));
                                    // Adjust current index if needed
                                    setCurrentAnalysisIndex(prev => 
                                      prev >= backgroundAnalyses.length - 1 ? Math.max(0, backgroundAnalyses.length - 2) : prev
                                    );
                                  }}
                                />
                              </div>
                              
                              {/* Navigation for multiple analyses on mobile */}
                              {backgroundAnalyses.length > 1 && (
                                <div className="border-t border-[#4ECFBF]/20 p-2 flex items-center justify-between bg-white/50">
                                  <button
                                    onClick={() => {
                                      setCurrentAnalysisIndex(prev => 
                                        prev > 0 ? prev - 1 : backgroundAnalyses.length - 1
                                      );
                                    }}
                                    className="flex items-center gap-1 text-xs text-[#4ECFBF] font-medium"
                                  >
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                    </svg>
                                    Previous
                                  </button>
                                  
                                  <span className="text-xs text-gray-500">
                                    {currentAnalysisIndex + 1} of {backgroundAnalyses.length}
                                  </span>
                                  
                                  <button
                                    onClick={() => {
                                      setCurrentAnalysisIndex(prev => 
                                        prev < backgroundAnalyses.length - 1 ? prev + 1 : 0
                                      );
                                    }}
                                    className="flex items-center gap-1 text-xs text-[#4ECFBF] font-medium"
                                  >
                                    Next
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                  </button>
                                </div>
                              )}
                            </div>
                            
                            {/* Desktop: Show all analyses with scrolling */}
                            <div className="hidden lg:block h-full p-3 sm:p-4 lg:p-6 overflow-y-auto space-y-3">
                              {backgroundAnalyses.map((analysis, index) => (
                                <BackgroundAnalysisCard
                                  key={analysis.analysis_id}
                                  analysis={analysis}
                                  language={language}
                                  level={level}
                                  sessionId={user?.email || 'guest'}
                                  onClose={() => {
                                    setBackgroundAnalyses(prev => prev.filter((_, i) => i !== index));
                                  }}
                                />
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center h-full text-gray-500 p-3">
                            {isProcessingBackground ? (
                              <div className="flex flex-col items-center text-center">
                                <div className="w-6 h-6 sm:w-8 sm:h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2 sm:mb-4"></div>
                                <span className="text-sm sm:text-lg font-medium">Analyzing...</span>
                                <span className="text-xs sm:text-sm text-gray-400 mt-1 sm:mt-2">AI is evaluating your speech</span>
                              </div>
                            ) : (
                              <div className="text-center">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 sm:h-12 sm:w-12 lg:h-16 lg:w-16 mx-auto mb-2 sm:mb-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                </svg>
                                <p className="text-sm sm:text-lg font-medium mb-1 sm:mb-2">Analysis Results</p>
                                <p className="text-xs sm:text-sm text-gray-400">Start speaking to see AI feedback</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Desktop Recording Button - Under Analysis Section */}
                    <div className="hidden lg:block sticky bottom-0 left-0 right-0 w-full mt-auto py-3 px-3 sm:px-4 lg:px-6 bg-transparent border-t border-slate-700/30 backdrop-blur-sm z-10">
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
                        disabled={isAttemptingToRecord || isRecording || isReviewingAnalysis || conversationTimeUp}
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
                            <span className="font-medium text-white">Recording...</span>
                          </>
                        ) : (
                          <>
                            <MicrophoneIcon isRecording={false} size={20} />
                            <span className="font-medium text-gray-800">Click to start speaking</span>
                          </>
                        )}
                      </Button>
                      
                      {/* Error message */}
                      {localError && (
                        <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-200 max-w-md text-center mx-auto">
                          <p>{localError}</p>
                        </div>
                      )}
                      
                    </div>
                  </div>
                  
                  {/* Conversation Transcript Section */}
                  <div className="relative bg-white border border-gray-200 rounded-lg shadow-lg flex flex-col 
                    h-[320px] sm:h-[380px] md:h-[420px] lg:h-[650px]">
                    
                    {/* Conversation Help Hint Button - Bottom Right */}
                    <div className="absolute bottom-4 right-4 z-20">
                      <ConversationHelpHintButton
                        isHelpReady={isHelpReady}
                        isHelpEnabled={helpSettings.help_enabled}
                        isLoading={isHelpLoading}
                        helpLanguage={helpSettings.help_language}
                        onToggleHelp={(enabled) => updateHelpSettings({ help_enabled: enabled })}
                        onChangeLanguage={(language) => updateHelpSettings({ help_language: language })}
                        onShowHelp={showHelpModal}
                        className="group"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between p-3 sm:p-4 lg:p-6 pb-2 sm:pb-3 lg:pb-4 border-b border-gray-100">
                      <h3 className="text-sm sm:text-base lg:text-xl font-semibold text-[#F75A5A] flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <span className="hidden sm:inline">Conversation Transcript</span>
                        <span className="sm:hidden">Conversation</span>
                      </h3>
                      
                      <div className="flex items-center gap-2">
                        {/* Message Counter */}
                        {processedMessages.length > 0 && (
                          <span className="text-xs sm:text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                            {processedMessages.length}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex-1 p-3 sm:p-4 lg:p-6 pt-0 overflow-hidden">
                      <div className="bg-[#F0FAFA] rounded-lg border border-[#4ECFBF]/30 h-full overflow-y-auto custom-scrollbar flex flex-col">
                        <div className="space-y-4 flex-1 flex flex-col p-3">
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
                                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn ${
                                      message.isGrouped && !message.isFirstInGroup ? 'mt-1' : 'mt-4'
                                    }`}
                                  >
                                    {message.role !== 'user' ? (
                                      <div className="flex-shrink-0 h-6 w-6 sm:h-8 sm:w-8 rounded-full bg-[#AFF4EB] flex items-center justify-center mr-2 shadow-md overflow-hidden">
                                        {!voiceLoading ? (
                                          <img 
                                            src={VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.avatar || '/images/tutors/alloy.svg'} 
                                            alt={`${VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.name || 'Alloy'} Avatar`}
                                            className="w-full h-full object-cover"
                                            onError={(e) => {
                                              console.error('Failed to load tutor avatar:', e);
                                              (e.target as HTMLImageElement).src = '/images/tutors/alloy.svg';
                                            }}
                                          />
                                        ) : (
                                          <span className="text-xs font-bold text-gray-800">T</span>
                                        )}
                                      </div>
                                    ) : (
                                      <div className="flex-shrink-0 h-6 w-6 sm:h-8 sm:w-8 rounded-full bg-[#D6E6FF] flex items-center justify-center ml-2 order-last shadow-md">
                                        <span className="text-xs font-bold text-gray-800">{firstName.charAt(0)}</span>
                                      </div>
                                    )}
                                    <div 
                                      className={`max-w-[85%] sm:max-w-[80%] break-words p-2 sm:p-3 lg:p-4 rounded-2xl shadow-md ${
                                        message.role === 'user' 
                                          ? 'bg-[#FFA955] text-white ml-2 rounded-tr-none'
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
                                          {message.role === 'user' ? firstName : `${VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.name || 'Alloy'} - AI Tutor`}
                                        </span>
                                        <span className="text-xs opacity-75 ml-2">
                                          {timeDisplay}
                                        </span>
                                      </div>
                                      <p className="text-xs sm:text-sm leading-relaxed mt-1 text-gray-800">{message.content}</p>
                                      
                                      {/* Analysis indicator for user messages */}
                                      {message.role === 'user' && message.content.trim().length > 0 && (
                                        <div className="mt-2 flex justify-end">
                                          {/* Check if this message was analyzed in background */}
                                          {backgroundAnalyses.some(analysis => 
                                            analysis.recognized_text.toLowerCase().includes(message.content.toLowerCase().substring(0, 20))
                                          ) ? (
                                            <div className="flex items-center space-x-1 text-green-600">
                                              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                              <span className="text-xs font-medium">Analyzed</span>
                                            </div>
                                          ) : (() => {
                                            // Use the same logic as the actual analysis function to avoid UI/logic mismatch
                                            const recentUserMessages = processedMessages
                                              .filter(msg => msg.role === 'user')
                                              .slice(-5)
                                              .map(msg => msg.content)
                                              .filter(content => content !== message.content); // Exclude current message
                                            
                                            const analysisDecision = shouldConsiderForAnalysis(message.content, recentUserMessages, language);
                                            
                                            if (analysisDecision.shouldAnalyze) {
                                              // Check if this message is currently being processed
                                              const isCurrentlyProcessing = isProcessingBackground && 
                                                processedMessages.filter(msg => msg.role === 'user').slice(-1)[0]?.content === message.content;
                                              
                                              if (isCurrentlyProcessing) {
                                                return (
                                                  <div className="flex items-center space-x-1 text-blue-600">
                                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                                    <span className="text-xs font-medium">Being analyzed...</span>
                                                  </div>
                                                );
                                              } else {
                                                // Check if analysis was attempted but not found in results
                                                // This could mean it was skipped by backend or is still processing
                                                return (
                                                  <div className="flex items-center space-x-1 text-gray-500">
                                                    <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                                                    <span className="text-xs font-medium">Not analyzed</span>
                                                  </div>
                                                );
                                              }
                                            } else {
                                              return (
                                                <div className="flex items-center space-x-1 text-gray-500">
                                                  <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                                                  <span className="text-xs font-medium">Skipped - {analysisDecision.reason}</span>
                                                </div>
                                              );
                                            }
                                          })()}
                                        </div>
                                      )}

                                    </div>
                                  </div>
                                );
                              })
                          ) : (
                            <div className="flex justify-center items-center h-full flex-1">
                              <div className="text-center p-4 sm:p-6 rounded-lg bg-[#4ECFBF]/10 border border-[#4ECFBF]/20 animate-fadeIn w-full">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 sm:h-12 sm:w-12 mx-auto mb-2 sm:mb-4 text-[#4ECFBF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                                <p className="text-[#4ECFBF] font-medium text-sm sm:text-lg">Your conversation will appear here</p>
                                <p className="text-slate-400 text-xs sm:text-base mt-1 sm:mt-2">Click the microphone button to start talking</p>
                              </div>
                            </div>
                          )}
                          
                          {/* Inline Conversation Help Modal - Always render, let modal handle visibility */}
                          <ConversationHelpModal
                            isOpen={isHelpModalOpen}
                            onClose={closeHelpModal}
                            helpData={helpData}
                            isLoading={isHelpLoading}
                            onResponseSelect={selectSuggestedResponse}
                            targetLanguage={language}
                            isUserSpeaking={isUserSpeaking}
                          />
                          
                          <div ref={messagesEndRef} className="mt-auto" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Mobile Recording Button - Under Conversation Section */}
                <div className="lg:hidden mt-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
                    <Button
                      type="button"
                      onClick={(e) => handleToggleRecording(e)}
                      onTouchStart={(e) => e.preventDefault()}
                      aria-label={isRecording ? "Stop recording" : "Start recording"}
                      className={`w-full py-4 relative flex items-center justify-center gap-3 transition-all duration-300 rounded-lg text-base font-semibold ${isRecording 
                        ? 'bg-[#F75A5A] hover:bg-[#E55252] text-white' 
                        : (!isAuthenticated() && conversationTimeUp) 
                          ? 'bg-gray-400 cursor-not-allowed text-white' 
                          : 'bg-[#FFD63A] hover:bg-[#ECC235] text-gray-800'} 
                        ${isAttemptingToRecord ? 'opacity-80 cursor-wait' : 'opacity-100'}`}
                        disabled={isAttemptingToRecord || isRecording || isReviewingAnalysis || conversationTimeUp}
                    >
                      {isAttemptingToRecord ? (
                        <>
                          <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          <span className="font-medium">Initializing...</span>
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
                          <span className="font-medium">Recording...</span>
                        </>
                      ) : (
                        <>
                          <MicrophoneIcon isRecording={false} size={24} />
                          <span className="font-medium">Click to start speaking</span>
                        </>
                      )}
                    </Button>
                    
                    {/* Error message */}
                    {localError && (
                      <div className="mt-3 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-600 text-center">
                        <p className="text-sm">{localError}</p>
                      </div>
                    )}
                    
                    {/* Warning message when content is not in target language */}
                    {isRecording && messages.length > 0 && messages[messages.length - 1].role === 'user' && 
                     !isInTargetLanguage(messages[messages.length - 1].content) && (
                      <div className="mt-3 px-3 py-2 bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-700 text-center">
                        <p className="text-sm">Please speak in {language.charAt(0).toUpperCase() + language.slice(1)}</p>
                      </div>
                    )}
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
        onCheckAnalysis={() => {
          console.log('🔍 User wants to check analyzed sentences - closing modal to show analysis');
          setShowCompletionModal(false);
          setIsReviewingAnalysis(true); // Disable recording button
        }}
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

      {/* Conversation Help Timeout Notification */}
      <ConversationHelpTimeoutNotification
        show={timeoutNotification.show}
        message={timeoutNotification.message}
        type={timeoutNotification.type}
      />
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
