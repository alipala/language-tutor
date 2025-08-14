'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { isAuthenticated } from '@/lib/auth-utils';
import { getConversationDuration } from '@/lib/guest-utils';
import DraggableTimer from '@/components/draggable-timer';
import LeaveConversationModal from '@/components/leave-conversation-modal';
import SessionCompletionModal from '@/components/session-completion-modal';
import ConversationHelpModal from '@/components/conversation-help-modal';
import ConversationHelpHintButton from '@/components/conversation-help-hint-button';
import ConversationHelpTimeoutNotification from '@/components/conversation-help-timeout-notification';
import { useConversationHelpSystem } from '@/hooks/useConversationHelpSystem';
import { getApiUrl } from '@/lib/api-utils';
import { type StoryWorld } from '@/lib/world-building-api';

// Custom hook for responsive detection
function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(false);
  
  useEffect(() => {
    const checkIsDesktop = () => {
      setIsDesktop(window.innerWidth >= 1024);
    };
    
    checkIsDesktop();
    window.addEventListener('resize', checkIsDesktop);
    return () => window.removeEventListener('resize', checkIsDesktop);
  }, []);
  
  return isDesktop;
}

interface StoryConversationClientProps {
  worldId: string;
  world: StoryWorld;
}

export default function StoryConversationClient({ worldId, world }: StoryConversationClientProps) {
  const router = useRouter();
  const { user } = useAuth();
  const isDesktop = useIsDesktop();
  
  // Extract the user's first name from their full name
  const firstName = useMemo(() => {
    if (!user?.name) return 'You';
    return user.name.split(' ')[0];
  }, [user?.name]);
  
  // Map language codes to full names
  const getLanguageName = (code: string): string => {
    const languageMap: Record<string, string> = {
      'en': 'english',
      'nl': 'dutch', 
      'es': 'spanish',
      'de': 'german',
      'fr': 'french',
      'pt': 'portuguese'
    };
    return languageMap[code] || code;
  };

  const languageName = getLanguageName(world.language);
  
  // State management
  const [isConversationTimerActive, setIsConversationTimerActive] = useState(false);
  const [conversationTimeUp, setConversationTimeUp] = useState(false);
  const [conversationDuration] = useState(() => getConversationDuration(isAuthenticated()));
  const [localError, setLocalError] = useState<string | null>(null);
  const [showMessages, setShowMessages] = useState(true);
  const [isAttemptingToRecord, setIsAttemptingToRecord] = useState(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [conversationStartTime, setConversationStartTime] = useState<number | null>(null);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [sessionCompleted, setSessionCompleted] = useState(false);
  const [showSavingLoader, setShowSavingLoader] = useState(false);
  const [mobileSessionEnded, setMobileSessionEnded] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<string>('alloy');
  const [voiceLoading, setVoiceLoading] = useState(true);
  const [showInfoModal, setShowInfoModal] = useState(true);
  const [modalDismissed, setModalDismissed] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const conversationHistoryRef = useRef<string>('');
  
  // Initialize conversation help system
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
  } = useConversationHelpSystem(languageName, world.target_level, 'story');
  
  // Voice data mapping
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
  
  // Initialize realtime service
  const { 
    isRecording, 
    messages, 
    error, 
    toggleConversation, 
    stopConversation, 
    startConversation, 
    initialize, 
    getFormattedConversationHistory,
    microphoneState,
    isUserMuted,
    muteMicrophone,
    unmuteMicrophone,
    toggleMicrophone
  } = useRealtime();
  
  // Track user speaking state for modal fade-out
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const previousRecordingState = useRef(false);

  useEffect(() => {
    if (isRecording && !previousRecordingState.current && isHelpModalOpen) {
      setIsUserSpeaking(true);
    } else if (!isRecording) {
      setIsUserSpeaking(false);
    }
    previousRecordingState.current = isRecording;
  }, [isRecording, isHelpModalOpen]);
  
  // Process messages for display
  const processedMessages = useMemo(() => {
    return messages.map((message, index) => ({
      ...message,
      itemId: message.itemId || `message-${index}`,
      role: message.role === 'assistant' ? 'assistant' : 'user'
    }));
  }, [messages]);
  
  // Build story-enhanced prompt for AI tutor
  const buildStoryEnhancedPrompt = useCallback(() => {
    const baseInstructions = `You are an AI language tutor helping a student practice ${languageName} through collaborative storytelling.`;
    
    const storyContext = `
COLLABORATIVE STORY CONTEXT:
- Story World: "${world.title}" (${world.genre} genre)
- Current Scene: "${world.world_state.current_plot_point}"
- Active Characters: ${world.world_state.active_characters.map(c => `${c.name} (${c.role})`).join(', ')}
- Key Locations: ${world.world_state.locations.map(l => l.name).join(', ')}
- Important Items: ${world.world_state.important_items.map(i => i.name).join(', ')}

LEARNING OBJECTIVES:
- Primary Focus: ${world.learning_objectives.primary_focus}
- Target Grammar: ${world.learning_objectives.target_structures.join(', ')}
- Vocabulary Themes: ${world.learning_objectives.vocabulary_themes.join(', ')}
- Student Level: ${world.target_level}

INSTRUCTIONS:
1. Help the student continue this collaborative story naturally
2. Provide language learning feedback (70% education, 30% story)
3. Encourage creative storytelling while practicing ${languageName}
4. Correct errors within the story context
5. Ask questions that develop characters and advance the plot
6. Use vocabulary from the themes: ${world.learning_objectives.vocabulary_themes.join(', ')}
7. Focus on ${world.learning_objectives.primary_focus} skills
8. Keep responses engaging and story-focused

Begin by asking the student how they'd like to continue the story from the current scene.`;

    return baseInstructions + '\n\n' + storyContext;
  }, [world, languageName]);
  
  // Initialize the realtime service
  useEffect(() => {
    const initializeService = async () => {
      try {
        if (!world || !world.language || !world.target_level) {
          console.error('Missing required world parameters');
          setLocalError('Missing world data. Please try again.');
          return;
        }
        
        console.log('Initializing story conversation with parameters - language:', languageName, 'level:', world.target_level, 'world:', world.title);
        
        const storyPrompt = buildStoryEnhancedPrompt();
        await initialize(languageName, world.target_level, 'story', storyPrompt, null);
        console.log('Realtime service initialized successfully for story conversation');
      } catch (err) {
        console.error('Failed to initialize realtime service:', err);
        setLocalError('Failed to initialize the speech service. Please try again.');
      }
    };
    
    initializeService();
  }, [initialize, languageName, world.target_level, buildStoryEnhancedPrompt]);

  // Handle errors
  useEffect(() => {
    if (error) {
      console.error('Realtime error:', error);
      setLocalError(error);
    } else {
      setLocalError(null);
    }
  }, [error]);

  // Start timer when AI begins speaking
  useEffect(() => {
    const assistantMessages = messages.filter(msg => msg.role === 'assistant');
    
    if (assistantMessages.length > 0 && 
        !isConversationTimerActive && 
        !conversationTimeUp &&
        isRecording) {
      
      console.log('🎯 AI has started speaking - starting conversation timer now!');
      setIsConversationTimerActive(true);
    }
  }, [messages, isConversationTimerActive, conversationTimeUp, isRecording]);

  // Set conversation start time when first message is received
  useEffect(() => {
    if (messages.length > 0 && !conversationStartTime) {
      console.log('🕐 Setting story conversation start time - first message received');
      setConversationStartTime(Date.now());
    }
  }, [messages.length, conversationStartTime]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Auto-save conversation progress
  const saveConversationProgress = async () => {
    if (!user || processedMessages.length === 0) {
      console.log('Cannot save: no user or no messages');
      return;
    }

    try {
      const durationMinutes = conversationStartTime 
        ? (Date.now() - conversationStartTime) / (1000 * 60)
        : 0;

      const messagesToSave = processedMessages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString()
      }));

      console.log('[AUTO_SAVE] Saving story conversation:', {
        worldId,
        worldTitle: world.title,
        language: languageName,
        level: world.target_level,
        messageCount: messagesToSave.length,
        duration: durationMinutes
      });

      const token = localStorage.getItem('token');
      
      const response = await fetch(`${getApiUrl()}/api/progress/save-conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          language: languageName,
          level: world.target_level,
          topic: `Story: ${world.title}`,
          messages: messagesToSave,
          duration_minutes: durationMinutes,
          learning_plan_id: null,
          conversation_type: 'story',
          story_world_id: worldId
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save story conversation');
      }

      const result = await response.json();
      console.log('[AUTO_SAVE] ✅ Story conversation saved successfully:', result);

    } catch (error) {
      console.error('[AUTO_SAVE] ❌ Error auto-saving story conversation:', error);
    }
  };
  
  // Handle recording toggle
  const handleToggleRecording = async (e: React.MouseEvent) => {
    e.preventDefault();
    
    if (isRecording) {
      console.log('🛑 Stopping recording - pausing timer');
      setIsConversationTimerActive(false);
      handleEndConversation();
      return;
    }

    setConversationTimeUp(false);
    console.log('🔄 Starting/resuming story conversation - timer managed by DraggableTimer');
    
    setIsPaused(false);
    setIsAttemptingToRecord(true);
    
    try {
      await toggleConversation();
      setIsAttemptingToRecord(false);
    } catch (err) {
      console.error('Error toggling conversation:', err);
      setIsAttemptingToRecord(false);
      setLocalError('Failed to start recording. Please try again.');
    }
  };
  
  // Handle end conversation
  const handleEndConversation = () => {
    conversationHistoryRef.current = getFormattedConversationHistory();
    console.log('Storing conversation history before pausing:', conversationHistoryRef.current);
    
    window.dispatchEvent(new CustomEvent('conversation-ended'));
    setIsPaused(true);
    stopConversation();
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
    console.log('🔄 Starting new story session');
    setSessionCompleted(false);
    setShowCompletionModal(false);
    setConversationTimeUp(false);
    setConversationStartTime(null);
    setMobileSessionEnded(false);
    router.push('/worlds');
  };

  const handleLeaveConversation = () => {
    router.push('/');
  };
  
  return (
    <main className="flex flex-col text-white p-3 sm:p-4 md:p-6 lg:p-8 overflow-x-hidden min-h-screen">
      <div className="w-full max-w-7xl mx-auto h-full flex flex-col">
        
        {/* Draggable Timer */}
        <DraggableTimer
          initialTime={getConversationDuration(isAuthenticated())}
          isActive={isConversationTimerActive}
          onTimeUp={async () => {
            console.log('⏰ Timer reached 0 - immediately stopping story conversation');
            setConversationTimeUp(true);
            setIsConversationTimerActive(false);
            
            window.dispatchEvent(new CustomEvent('conversation-time-up'));
            stopConversation();
            
            setMobileSessionEnded(true);
            setSessionCompleted(true);
            
            if (user && processedMessages.length > 0) {
              console.log('🔄 Auto-saving story conversation at timer end...');
              setShowSavingLoader(true);
              await saveConversationProgress();
              setShowSavingLoader(false);
              setShowCompletionModal(true);
            } else {
              handleEndConversation();
            }
          }}
        />

        {/* Header - Story-specific */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            {world.title}
          </h1>
          <p className="text-white/80 mt-2">
            {languageName.charAt(0).toUpperCase() + languageName.slice(1)} • Level: {world.target_level.toUpperCase()} • {world.genre}
          </p>
          <p className="text-white/60 mt-1 text-sm">
            Click the microphone button to continue the story
          </p>
        </div>

        {/* Information Modal */}
        {showInfoModal && !modalDismissed && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">📖 Story Conversation Tips</h3>
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
              
              <div className="p-4">
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-4 mb-4">
                  <h4 className="font-semibold text-purple-900 mb-2">🌟 Your Story World</h4>
                  <div className="space-y-2 text-sm">
                    <div><span className="font-medium text-purple-800">Title:</span> <span className="text-purple-700">{world.title}</span></div>
                    <div><span className="font-medium text-purple-800">Genre:</span> <span className="text-purple-700">{world.genre}</span></div>
                    <div><span className="font-medium text-purple-800">Current Scene:</span> <span className="text-purple-700">{world.world_state.current_plot_point}</span></div>
                    <div><span className="font-medium text-purple-800">Characters:</span> <span className="text-purple-700">{world.world_state.active_characters.map(c => c.name).join(', ')}</span></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="flex flex-col items-center text-center p-3 bg-green-50 rounded-lg border border-green-100">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg">✨</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Be Creative</h4>
                    <p className="text-xs text-gray-600">Let your imagination flow while practicing {languageName}!</p>
                  </div>
                  
                  <div className="flex flex-col items-center text-center p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg">🗣️</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Practice Speaking</h4>
                    <p className="text-xs text-gray-600">Focus on {world.learning_objectives.primary_focus} skills.</p>
                  </div>
                  
                  <div className="flex flex-col items-center text-center p-3 bg-orange-50 rounded-lg border border-orange-100">
                    <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg">📚</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Continue the Story</h4>
                    <p className="text-xs text-gray-600">Build on the current scene and develop the characters.</p>
                  </div>
                  
                  <div className="flex flex-col items-center text-center p-3 bg-purple-50 rounded-lg border border-purple-100">
                    <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg">🤖</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Get AI Feedback</h4>
                    <p className="text-xs text-gray-600">Receive language corrections within the story context.</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-center gap-2 text-gray-600 mb-4">
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm">Ready to continue your {languageName} story?</span>
                </div>
                
                <div className="flex justify-center">
                  <button
                    onClick={() => {
                      setModalDismissed(true);
                      setShowInfoModal(false);
                    }}
                    className="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white text-sm font-semibold rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 shadow-md hover:shadow-lg"
                  >
                    Let's continue the story!
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Story World Summary - Desktop Only */}
        <div className="hidden sm:block bg-white border-2 border-[#4ECFBF] rounded-xl p-2 sm:p-3 md:p-4 mb-3 sm:mb-4 w-full relative z-10 shadow-lg">
          <div className="flex flex-wrap items-center justify-center gap-4 text-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#4ECFBF] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733a18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98A1 1 0 0117 18H10a1 1 0 01-.894-1.447l.99-1.98.019-.038 2.991-5.982A1 1 0 0114 8h-1z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold text-lg">
                {languageName.charAt(0).toUpperCase() + languageName.slice(1)}
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#FFD63A] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-gray-800" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold text-lg">Level {world.target_level.toUpperCase()}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#9333EA] rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="font-semibold text-lg">{world.genre}</span>
            </div>
            
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
                  
                  {/* Real Time Sentence Analysis Component - Mobile: Show only when session ended */}
                  <div 
                    className="relative bg-white border border-gray-200 rounded-lg shadow-lg flex flex-col lg:h-[650px]"
                    style={{
                      // Desktop: Always show with fixed height
                      display: isDesktop ? 'flex' : 
                        // Mobile: Show when session ended OR when we have analyses to show after session completion
                        (mobileSessionEnded || sessionCompleted || isPaused || 
                         (conversationTimeUp)) ? 'flex' : 'none',
                      // Mobile: Full screen height minus header and padding
                      height: isDesktop ? '650px' : 'calc(100vh - 200px)'
                    }}
                  >
                    
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
                        <span className="text-xs sm:text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                          Story Mode
                        </span>
                      </div>
                    </div>
                    
                    {/* Analysis Display */}
                    <div className="flex-1 p-3 sm:p-4 lg:p-6 pt-0 overflow-hidden">
                      <div className="bg-[#F0FAFA] rounded-lg border border-[#4ECFBF]/30 h-full flex flex-col">
                        <div className="flex items-center justify-center h-full text-gray-500 p-3">
                          <div className="text-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 sm:h-12 sm:w-12 lg:h-16 lg:w-16 mx-auto mb-2 sm:mb-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                            <p className="text-sm sm:text-lg font-medium mb-1 sm:mb-2">Story Analysis</p>
                            <p className="text-xs sm:text-sm text-gray-400">AI feedback for your story contributions</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Desktop Recording Button - Under Analysis Section */}
                    <div className="hidden lg:block sticky bottom-0 left-0 right-0 w-full mt-auto py-3 px-3 sm:px-4 lg:px-6 bg-transparent border-t border-slate-700/30 backdrop-blur-sm z-10">
                      <div className="flex items-center gap-3">
                        {/* Main Recording Button */}
                        <Button
                          type="button"
                          onClick={(e) => {
                            // Only allow clicking when idle (not recording)
                            if (microphoneState === 'idle') {
                              handleToggleRecording(e);
                            }
                          }}
                          onTouchStart={(e) => e.preventDefault()}
                          aria-label={microphoneState === 'idle' ? "Start recording" : microphoneState === 'recording' ? "Recording in progress" : "Recording (muted)"}
                          className={`flex-1 py-3 sm:py-4 relative flex items-center justify-center gap-2 sm:gap-3 transition-all duration-300 rounded-lg ${
                            microphoneState === 'recording' && !isUserMuted
                              ? 'bg-[#F75A5A] cursor-default' 
                              : microphoneState === 'muted'
                                ? 'bg-orange-500 cursor-default'
                                : (!isAuthenticated() && conversationTimeUp) 
                                  ? 'bg-gray-400 cursor-not-allowed' 
                                  : 'bg-[#FFD63A] hover:bg-[#ECC235]'} 
                            ${isAttemptingToRecord ? 'opacity-80 cursor-wait' : 'opacity-100'}`}
                          disabled={isAttemptingToRecord || conversationTimeUp || microphoneState !== 'idle'}
                        >
                          {isAttemptingToRecord ? (
                            <>
                              <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <span className="font-medium text-white">Initializing microphone...</span>
                            </>
                          ) : microphoneState === 'recording' && !isUserMuted ? (
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
                          ) : microphoneState === 'muted' ? (
                            <>
                              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                              </svg>
                              <span className="font-medium text-white">Muted</span>
                            </>
                          ) : (
                            <>
                              <MicrophoneIcon isRecording={false} size={20} />
                              <span className="font-medium text-gray-800">Click to start speaking</span>
                            </>
                          )}
                        </Button>
                        
                        {/* Mute Toggle Button - Only show when recording */}
                        {(microphoneState === 'recording' || microphoneState === 'muted') && (
                          <Button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              toggleMicrophone();
                            }}
                            aria-label={isUserMuted ? "Unmute microphone" : "Mute microphone"}
                            className={`px-4 py-3 sm:py-4 flex items-center justify-center gap-2 transition-all duration-300 rounded-lg ${
                              isUserMuted 
                                ? 'bg-orange-500 hover:bg-orange-600 text-white' 
                                : 'bg-green-500 hover:bg-green-600 text-white'
                            }`}
                            title={isUserMuted ? "Click to unmute your microphone" : "Click to mute your microphone"}
                          >
                            {isUserMuted ? (
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                              </svg>
                            ) : (
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                              </svg>
                            )}
                          </Button>
                        )}
                      </div>
                      
                      {/* Error message */}
                      {localError && (
                        <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-200 max-w-md text-center mx-auto">
                          <p>{localError}</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Conversation Transcript Section - Mobile: Show only during active session */}
                  <div 
                    className="relative bg-white border border-gray-200 rounded-lg shadow-lg flex flex-col lg:h-[650px]"
                    style={{
                      // Desktop: Always show with fixed height
                      display: isDesktop ? 'flex' : 
                        // Mobile: Hide when session ended
                        (mobileSessionEnded || sessionCompleted) ? 'none' : 'flex',
                      // Mobile: Full screen height minus header and padding
                      height: isDesktop ? '650px' : 'calc(100vh - 200px)'
                    }}
                  >
                    
                    {/* Conversation Help Hint Button - Bottom Right - Desktop Only */}
                    <div className="absolute bottom-4 right-4 z-20 hidden lg:block">
                      <ConversationHelpHintButton
                        isHelpReady={isHelpReady}
                        isHelpEnabled={helpSettings.help_enabled}
                        isLoading={isHelpLoading}
                        helpLanguage={helpSettings.help_language}
                        onToggleHelp={(enabled) => updateHelpSettings({ help_enabled: enabled })}
                        onChangeLanguage={(language) => updateHelpSettings({ help_language: language })}
                        onShowHelp={showHelpModal}
                        className="group"
                        sessionEnded={mobileSessionEnded || sessionCompleted || isPaused || conversationTimeUp}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between p-3 sm:p-4 lg:p-6 pb-2 sm:pb-3 lg:pb-4 border-b border-gray-100">
                      <h3 className="text-sm sm:text-base lg:text-xl font-semibold text-[#F75A5A] flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <span className="hidden sm:inline">Story Conversation</span>
                        <span className="sm:hidden">Conversation</span>
                      </h3>
                      
                      <div className="flex items-center gap-2">
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
                            processedMessages.map((message: any, index: number) => {
                              const messageTime = message.timestamp 
                                ? new Date(message.timestamp) 
                                : new Date();
                              
                              const timeDisplay = messageTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                              
                              return (
                                <div 
                                  key={`${message.role}-${index}-${message.itemId || messageTime.getTime()}`}
                                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn mt-4`}
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
                                <p className="text-[#4ECFBF] font-medium text-sm sm:text-lg">Your story conversation will appear here</p>
                                <p className="text-slate-400 text-xs sm:text-base mt-1 sm:mt-2">Click the microphone button to start talking</p>
                              </div>
                            </div>
                          )}
                          
                          {/* Conversation Help Modal */}
                          <ConversationHelpModal
                            isOpen={isHelpModalOpen}
                            onClose={closeHelpModal}
                            helpData={helpData}
                            isLoading={isHelpLoading}
                            onResponseSelect={selectSuggestedResponse}
                            targetLanguage={languageName}
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
                    <div className="flex items-center gap-2">
                      {/* Recording Button - Main button */}
                      <Button
                        type="button"
                        onClick={(e) => {
                          if (microphoneState === 'idle') {
                            handleToggleRecording(e);
                          }
                        }}
                        onTouchStart={(e) => e.preventDefault()}
                        aria-label={microphoneState === 'idle' ? "Start recording" : microphoneState === 'recording' ? "Recording in progress" : "Recording (muted)"}
                        className={`flex-1 py-4 relative flex items-center justify-center gap-2 transition-all duration-300 rounded-lg text-sm font-semibold ${
                          microphoneState === 'recording' && !isUserMuted
                            ? 'bg-[#F75A5A] cursor-default text-white' 
                            : microphoneState === 'muted'
                              ? 'bg-orange-500 cursor-default text-white'
                              : (!isAuthenticated() && conversationTimeUp) 
                                ? 'bg-gray-400 cursor-not-allowed text-white' 
                                : 'bg-[#FFD63A] hover:bg-[#ECC235] text-gray-800'} 
                          ${isAttemptingToRecord ? 'opacity-80 cursor-wait' : 'opacity-100'}`}
                        disabled={isAttemptingToRecord || conversationTimeUp || microphoneState !== 'idle'}
                      >
                        {isAttemptingToRecord ? (
                          <>
                            <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span className="font-medium text-xs">Initializing...</span>
                          </>
                        ) : microphoneState === 'recording' && !isUserMuted ? (
                          <>
                            <div className="relative h-5 w-5 flex items-center justify-center">
                              <div className="audio-wave">
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                                <span className="audio-wave-bar"></span>
                              </div>
                            </div>
                            <span className="font-medium text-xs">Recording...</span>
                          </>
                        ) : microphoneState === 'muted' ? (
                          <>
                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                            </svg>
                            <span className="font-medium text-xs">Muted</span>
                          </>
                        ) : (
                          <>
                            <MicrophoneIcon isRecording={false} size={18} />
                            <span className="font-medium text-xs">Start speaking</span>
                          </>
                        )}
                      </Button>
                      
                      {/* Mute Toggle Button - Only show when recording */}
                      {(microphoneState === 'recording' || microphoneState === 'muted') && (
                        <Button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            toggleMicrophone();
                          }}
                          aria-label={isUserMuted ? "Unmute microphone" : "Mute microphone"}
                          className={`px-3 py-4 flex items-center justify-center transition-all duration-300 rounded-lg ${
                            isUserMuted 
                              ? 'bg-orange-500 hover:bg-orange-600 text-white' 
                              : 'bg-green-500 hover:bg-green-600 text-white'
                          }`}
                          title={isUserMuted ? "Tap to unmute" : "Tap to mute"}
                        >
                          {isUserMuted ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                            </svg>
                          )}
                        </Button>
                      )}
                      
                      {/* Help Button - Always show */}
                      <div className="flex items-center justify-center">
                        <ConversationHelpHintButton
                          isHelpReady={isHelpReady}
                          isHelpEnabled={helpSettings.help_enabled}
                          isLoading={isHelpLoading}
                          helpLanguage={helpSettings.help_language}
                          onToggleHelp={(enabled) => updateHelpSettings({ help_enabled: enabled })}
                          onChangeLanguage={(language) => updateHelpSettings({ help_language: language })}
                          onShowHelp={showHelpModal}
                          className="relative"
                          sessionEnded={mobileSessionEnded || sessionCompleted || isPaused || conversationTimeUp}
                        />
                      </div>
                    </div>
                    
                    {/* Error message */}
                    {localError && (
                      <div className="mt-3 p-3 bg-red-500/20 border border-red-500/30 rounded-md text-red-600 text-center">
                        <p className="text-sm">{localError}</p>
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
        language={languageName}
        level={world.target_level}
        topic={`Story: ${world.title}`}
        conversationStartTime={conversationStartTime || undefined}
        practiceTime={getPracticeTime()}
      />

      {/* Session Completion Modal */}
      <SessionCompletionModal
        isOpen={showCompletionModal}
        onGoHome={handleGoHome}
        onStartNew={handleStartNewSession}
        onCheckAnalysis={() => {
          console.log('🔍 User wants to check analyzed sentences - closing modal');
          setShowCompletionModal(false);
        }}
        sessionDuration={getPracticeTime()}
        messageCount={processedMessages.length}
        language={languageName}
        level={world.target_level}
      />

      {/* Saving Progress Loading Modal */}
      {showSavingLoader && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 mx-4 max-w-sm w-full text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Saving Your Progress</h3>
            <p className="text-gray-600">Please wait while we save your story conversation...</p>
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

// Microphone icon component
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
