'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { useRealtime } from '@/lib/useRealtime';
import { RealtimeMessage, MicrophoneState } from '@/lib/types';
import { worldBuildingAPI, type StoryWorld } from '@/lib/world-building-api';
import { BookOpen, Users, Target, Clock, Mic, MicOff, Volume2, VolumeX, X, Loader2 } from 'lucide-react';

interface StoryConversationInterfaceProps {
  world: StoryWorld;
  onComplete: (result: { success: boolean; message: string; duration_seconds: number }) => void;
  onCancel: () => void;
}

export default function StoryConversationInterface({ 
  world, 
  onComplete, 
  onCancel 
}: StoryConversationInterfaceProps) {
  const [sessionStartTime] = useState(Date.now());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionActive, setSessionActive] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<string>('alloy');
  const [voiceLoading, setVoiceLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Use existing real-time voice system
  const {
    isConnected,
    isRecording,
    isInitialized,
    error: realtimeError,
    messages,
    initialize,
    startConversation,
    stopConversation,
    toggleMicrophone,
    isUserMuted,
    microphoneState
  } = useRealtime();

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

  // Build story-enhanced prompt for AI tutor
  const buildStoryEnhancedPrompt = useCallback(() => {
    const baseInstructions = `You are an AI language tutor helping a student practice ${world.language} through collaborative storytelling.`;
    
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
3. Encourage creative storytelling while practicing ${world.language}
4. Correct errors within the story context
5. Ask questions that develop characters and advance the plot
6. Use vocabulary from the themes: ${world.learning_objectives.vocabulary_themes.join(', ')}
7. Focus on ${world.learning_objectives.primary_focus} skills
8. Keep responses engaging and story-focused
9. Automatically identify meaningful story contributions for saving

STORY CONTINUATION RULES:
- Build upon: "${world.world_state.current_plot_point}"
- Involve characters: ${world.world_state.active_characters.map(c => c.name).join(', ')}
- Maintain ${world.genre} genre elements
- Encourage natural conversation that advances the plot

Begin by asking the student how they'd like to continue the story from the current scene.`;

    return baseInstructions + '\n\n' + storyContext;
  }, [world]);

  // Fetch user's voice preference
  useEffect(() => {
    const fetchVoicePreference = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setVoiceLoading(false);
          return;
        }

        const response = await fetch(`/api/auth/get-voice`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          setSelectedVoice(data.voice || 'alloy');
        }
      } catch (error) {
        console.error('Error fetching voice preference:', error);
      } finally {
        setVoiceLoading(false);
      }
    };

    fetchVoicePreference();
  }, []);

  // Initialize the story conversation session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const worldId = world.id || (world as any)._id;
        if (!worldId) {
          throw new Error('World ID is missing from world object');
        }

        // Validate session access
        const validation = await worldBuildingAPI.validateStoryVoiceSession(worldId, 'contribution');
        if (!validation.can_access) {
          throw new Error(validation.message);
        }

        // Initialize real-time service with story context
        const storyPrompt = buildStoryEnhancedPrompt();
        const success = await initialize(
          world.language,
          world.target_level,
          `Story: ${world.title}`,
          storyPrompt,
          { world_id: worldId, session_type: 'contribution' }
        );

        if (!success) {
          throw new Error('Failed to initialize voice session');
        }

        setIsLoading(false);
      } catch (err) {
        console.error('Error initializing story session:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize session');
        setIsLoading(false);
      }
    };

    initializeSession();
  }, [world, initialize, buildStoryEnhancedPrompt]);

  // Start the conversation
  const handleStartConversation = useCallback(async () => {
    try {
      setError(null);
      const success = await startConversation();
      if (success) {
        setSessionActive(true);
      } else {
        setError('Failed to start conversation');
      }
    } catch (err) {
      console.error('Error starting conversation:', err);
      setError(err instanceof Error ? err.message : 'Failed to start conversation');
    }
  }, [startConversation]);

  // End the session and process results
  const handleEndSession = useCallback(async () => {
    try {
      stopConversation();
      
      const durationSeconds = Math.floor((Date.now() - sessionStartTime) / 1000);
      const worldId = world.id || (world as any)._id;
      
      // Extract meaningful story content from conversation
      const storyContent = messages
        .filter(m => m.role === 'user' && m.content.length > 20)
        .map(m => m.content)
        .join(' ');

      if (storyContent.trim()) {
        // Submit story contribution automatically
        try {
          const result = await worldBuildingAPI.completeStoryVoiceSession(
            worldId,
            'contribution',
            storyContent,
            durationSeconds
          );
          
          onComplete({
            success: true,
            message: `Story contribution saved! Added ${Math.round(durationSeconds / 60)} minutes of practice.`,
            duration_seconds: durationSeconds
          });
        } catch (submitError) {
          console.error('Error submitting story contribution:', submitError);
          onComplete({
            success: false,
            message: 'Session completed but failed to save story contribution.',
            duration_seconds: durationSeconds
          });
        }
      } else {
        onComplete({
          success: true,
          message: `Practice session completed! ${Math.round(durationSeconds / 60)} minutes of conversation practice.`,
          duration_seconds: durationSeconds
        });
      }
    } catch (err) {
      console.error('Error ending session:', err);
      onComplete({
        success: false,
        message: 'Error ending session',
        duration_seconds: Math.floor((Date.now() - sessionStartTime) / 1000)
      });
    }
  }, [stopConversation, sessionStartTime, messages, world, onComplete]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    stopConversation();
    onCancel();
  }, [stopConversation, onCancel]);

  // Process messages for display (same logic as speech-client)
  const processedMessages = useMemo(() => {
    const mappedMessages = messages.map((message, index) => {
      const baseItemId = message.itemId?.split('-group-')[0] || `message-${index}`;
      return {
        ...message,
        itemId: message.itemId || `message-${index}`,
        role: message.role === 'assistant' ? 'assistant' : 'user',
        baseItemId
      };
    });

    // Deduplicate messages
    const filteredMessages: typeof mappedMessages = [];
    const seenContents: {content: string, index: number, role: string}[] = [];

    mappedMessages.forEach((message, index) => {
      seenContents.push({
        content: message.content.trim(),
        index,
        role: message.role
      });
    });

    const duplicateIndices = new Set<number>();
    
    for (let i = 0; i < seenContents.length; i++) {
      for (let j = i + 1; j < seenContents.length; j++) {
        const messageA = seenContents[i];
        const messageB = seenContents[j];
        
        if (messageA.role !== messageB.role) continue;
        
        const contentA = messageA.content;
        const contentB = messageB.content;
        
        if (contentA === contentB) {
          duplicateIndices.add(messageB.index);
          continue;
        }
        
        if (contentA.includes(contentB)) {
          duplicateIndices.add(messageB.index);
        } else if (contentB.includes(contentA)) {
          duplicateIndices.add(messageA.index);
        }
      }
    }

    for (let i = 0; i < mappedMessages.length; i++) {
      if (!duplicateIndices.has(i)) {
        filteredMessages.push(mappedMessages[i]);
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

  // Calculate session duration
  const sessionDuration = Math.floor((Date.now() - sessionStartTime) / 1000);
  const minutes = Math.floor(sessionDuration / 60);
  const seconds = sessionDuration % 60;

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <Loader2 className="h-12 w-12 text-[#4ECFBF] animate-spin mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Preparing Story Session
            </h3>
            <p className="text-gray-600">
              Setting up your collaborative storytelling experience...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header - Story-themed */}
        <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="h-6 w-6" />
              <div>
                <h2 className="text-xl font-bold">{world.title}</h2>
                <p className="text-[#4ECFBF]/80 text-sm">Collaborative Story Session</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4" />
                <span>{minutes}:{seconds.toString().padStart(2, '0')}</span>
              </div>
              <button
                onClick={handleCancel}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Story Context - Same as original but more prominent */}
        <div className="p-6 bg-gradient-to-br from-[#4ECFBF]/5 to-[#FFD63A]/5 border-b">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-[#4ECFBF]" />
              <span className="font-medium">Focus:</span>
              <span className="capitalize">{world.learning_objectives.primary_focus}</span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-[#FFD63A]" />
              <span className="font-medium">Characters:</span>
              <span>{world.world_state.active_characters.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-[#F75A5A]" />
              <span className="font-medium">Genre:</span>
              <span className="capitalize">{world.genre}</span>
            </div>
          </div>
          <div className="mt-4 p-4 bg-white/50 rounded-lg">
            <p className="text-sm text-gray-700 italic">
              <strong>Current Scene:</strong> "{world.world_state.current_plot_point}"
            </p>
          </div>
        </div>

        {/* Main Content Area - Two Column Layout like speech-client */}
        <div className="flex-1 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full p-6">
            
            {/* Left Column: Conversation Transcript */}
            <div className="bg-[#F0FAFA] rounded-lg border border-[#4ECFBF]/30 flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-[#4ECFBF]/20">
                <h3 className="text-lg font-semibold text-[#4ECFBF] flex items-center">
                  <BookOpen className="h-5 w-5 mr-2" />
                  Story Conversation
                </h3>
                {processedMessages.length > 0 && (
                  <span className="text-sm text-gray-500 bg-white px-2 py-1 rounded-full">
                    {processedMessages.length}
                  </span>
                )}
              </div>
              
              <div className="flex-1 overflow-y-auto p-4">
                {!sessionActive ? (
                  <div className="text-center py-12">
                    <div className="mb-6">
                      <div className="w-20 h-20 bg-gradient-to-br from-[#4ECFBF] to-[#3a9e92] rounded-full flex items-center justify-center mx-auto mb-4">
                        <Mic className="h-10 w-10 text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-gray-800 mb-2">
                        Ready to Continue the Story?
                      </h3>
                      <p className="text-gray-600 max-w-md mx-auto">
                        Join the collaborative story and practice your {world.language} skills. 
                        The AI tutor will help you continue the story while providing language feedback.
                      </p>
                    </div>
                    
                    <button
                      onClick={handleStartConversation}
                      disabled={!isInitialized || !!error}
                      className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white rounded-lg font-medium hover:from-[#3a9e92] hover:to-[#2d7a6e] transition-all duration-300 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Mic className="h-5 w-5" />
                      Join Story Conversation
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Connection Status */}
                    <div className="flex items-center justify-between p-3 bg-white/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
                        <span className="text-sm font-medium">
                          {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={toggleMicrophone}
                          className={`p-2 rounded-full transition-colors ${
                            isUserMuted 
                              ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                              : 'bg-green-100 text-green-600 hover:bg-green-200'
                          }`}
                        >
                          {isUserMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                        </button>
                        <span className="text-sm text-gray-600">
                          {isUserMuted ? 'Muted' : 'Listening'}
                        </span>
                      </div>
                    </div>

                    {/* Messages */}
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {processedMessages.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                          <Mic className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p>Start speaking to continue the story...</p>
                        </div>
                      ) : (
                        processedMessages.map((message, index) => {
                          const messageTime = message.timestamp 
                            ? new Date(message.timestamp) 
                            : new Date();
                          const timeDisplay = messageTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                          
                          return (
                            <div
                              key={`${message.role}-${index}-${message.itemId || messageTime.getTime()}`}
                              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              {message.role !== 'user' ? (
                                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-[#AFF4EB] flex items-center justify-center mr-2 shadow-md overflow-hidden">
                                  {!voiceLoading ? (
                                    <img 
                                      src={VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.avatar || '/images/tutors/alloy.svg'} 
                                      alt={`${VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.name || 'Alloy'} Avatar`}
                                      className="w-full h-full object-cover"
                                      onError={(e) => {
                                        (e.target as HTMLImageElement).src = '/images/tutors/alloy.svg';
                                      }}
                                    />
                                  ) : (
                                    <span className="text-xs font-bold text-gray-800">AI</span>
                                  )}
                                </div>
                              ) : (
                                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-[#D6E6FF] flex items-center justify-center ml-2 order-last shadow-md">
                                  <span className="text-xs font-bold text-gray-800">You</span>
                                </div>
                              )}
                              <div 
                                className={`max-w-[80%] break-words p-3 rounded-2xl shadow-md ${
                                  message.role === 'user' 
                                    ? 'bg-[#FFA955] text-white ml-2 rounded-tr-none'
                                    : 'bg-[#AFF4EB] text-gray-800 mr-2 rounded-tl-none'
                                }`}
                              >
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs font-semibold text-gray-800">
                                    {message.role === 'user' ? 'You' : `${VOICE_DATA[selectedVoice as keyof typeof VOICE_DATA]?.name || 'AI Tutor'}`}
                                  </span>
                                  <span className="text-xs opacity-75 ml-2 text-gray-800">
                                    {timeDisplay}
                                  </span>
                                </div>
                                <p className="text-sm leading-relaxed text-gray-800">{message.content}</p>
                              </div>
                            </div>
                          );
                        })
                      )}
                      <div ref={messagesEndRef} />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Story Context & Controls */}
            <div className="bg-gradient-to-br from-[#FFD63A]/10 to-[#F75A5A]/10 rounded-lg border border-[#FFD63A]/30 flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-[#FFD63A]/20">
                <h3 className="text-lg font-semibold text-[#F75A5A] flex items-center">
                  <Users className="h-5 w-5 mr-2" />
                  Story Elements
                </h3>
              </div>
              
              <div className="flex-1 p-4 space-y-4">
                {/* Characters */}
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-800 mb-2 flex items-center">
                    <Users className="h-4 w-4 mr-1 text-[#4ECFBF]" />
                    Active Characters
                  </h4>
                  <div className="space-y-2">
                    {world.world_state.active_characters.map((character, index) => (
                      <div key={index} className="text-sm">
                        <span className="font-medium">{character.name}</span>
                        <span className="text-gray-600 ml-2">({character.role})</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Locations */}
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-800 mb-2 flex items-center">
                    <Target className="h-4 w-4 mr-1 text-[#FFD63A]" />
                    Key Locations
                  </h4>
                  <div className="space-y-1">
                    {world.world_state.locations.map((location, index) => (
                      <div key={index} className="text-sm text-gray-700">
                        {location.name}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Learning Focus */}
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-800 mb-2 flex items-center">
                    <BookOpen className="h-4 w-4 mr-1 text-[#F75A5A]" />
                    Learning Focus
                  </h4>
                  <div className="text-sm space-y-1">
                    <div><strong>Primary:</strong> {world.learning_objectives.primary_focus}</div>
                    <div><strong>Vocabulary:</strong> {world.learning_objectives.vocabulary_themes.join(', ')}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Controls */}
        {sessionActive && (
          <div className="border-t bg-gray-50 p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <p>Speak naturally to continue the story. The AI will provide feedback and help advance the plot.</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEndSession}
                  className="px-4 py-2 bg-[#4ECFBF] text-white rounded-lg hover:bg-[#3a9e92] transition-colors"
                >
                  Complete Session
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {(error || realtimeError) && (
          <div className="p-4 bg-red-50 border-t border-red-200">
            <p className="text-red-800 text-sm">{error || realtimeError}</p>
          </div>
        )}
      </div>
    </div>
  );
}
