'use client';

import { useState, useEffect, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, X, Clock, Users, BookOpen, Target, Loader2 } from 'lucide-react';
import { useRealtime } from '@/lib/useRealtime';
import { worldBuildingAPI, type StoryWorld } from '@/lib/world-building-api';

interface StoryConversationSessionProps {
  world: StoryWorld;
  onComplete: (result: { success: boolean; message: string; duration_seconds: number }) => void;
  onCancel: () => void;
}

export default function StoryConversationSession({ 
  world, 
  onComplete, 
  onCancel 
}: StoryConversationSessionProps) {
  const [sessionStartTime] = useState(Date.now());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionActive, setSessionActive] = useState(false);

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

  // Initialize the story conversation session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Debug: Log world object to see what's available
        console.log('🔍 [DEBUG] World object:', world);
        console.log('🔍 [DEBUG] World ID:', world.id);
        console.log('🔍 [DEBUG] World _id:', (world as any)._id);

        // Check if world.id exists, if not try _id
        const worldId = world.id || (world as any)._id;
        if (!worldId) {
          throw new Error('World ID is missing from world object');
        }

        console.log('🔍 [DEBUG] Using world ID:', worldId);

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
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
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

        {/* Story Context */}
        <div className="p-4 bg-gradient-to-br from-[#4ECFBF]/5 to-[#FFD63A]/5 border-b">
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
          <div className="mt-3 p-3 bg-white/50 rounded-lg">
            <p className="text-sm text-gray-700 italic">
              <strong>Current Scene:</strong> "{world.world_state.current_plot_point}"
            </p>
          </div>
        </div>

        {/* Error Display */}
        {(error || realtimeError) && (
          <div className="p-4 bg-red-50 border-b border-red-200">
            <p className="text-red-800 text-sm">{error || realtimeError}</p>
          </div>
        )}

        {/* Conversation Area */}
        <div className="flex-1 overflow-y-auto p-6">
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
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
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
                {messages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Mic className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Start speaking to continue the story...</p>
                  </div>
                ) : (
                  messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.role === 'user'
                            ? 'bg-[#4ECFBF] text-white'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
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
      </div>
    </div>
  );
}
