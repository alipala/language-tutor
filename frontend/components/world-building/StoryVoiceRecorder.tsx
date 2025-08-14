'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Play, Pause, Volume2, Clock, Users, BookOpen, Target } from 'lucide-react';
import { useRealtime } from '@/lib/useRealtime';
import { worldBuildingAPI, type StoryVoiceSessionConfig } from '@/lib/world-building-api';

interface StoryVoiceRecorderProps {
  worldId: string;
  sessionType: 'practice' | 'contribution' | 'review';
  storyContext: {
    world_title: string;
    genre: string;
    language: string;
    target_level: string;
    current_plot_point: string;
    previous_contribution?: {
      transcript: string;
      contributor_name: string;
    };
    active_characters: Array<{ name: string; role: string; description: string }>;
    locations: Array<{ name: string; description: string }>;
    primary_focus: string;
    vocabulary_themes: string[];
    session_limits: {
      min_duration: number;
      max_duration: number;
      saves_to_story: boolean;
    };
  };
  onSessionComplete: (result: {
    transcript: string;
    duration: number;
    contribution_id?: string;
  }) => void;
  onCancel: () => void;
}

export default function StoryVoiceRecorder({
  worldId,
  sessionType,
  storyContext,
  onSessionComplete,
  onCancel
}: StoryVoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionConfig, setSessionConfig] = useState<StoryVoiceSessionConfig | null>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);

  const durationRef = useRef<NodeJS.Timeout | null>(null);

  // Load session configuration on mount
  useEffect(() => {
    const loadSessionConfig = async () => {
      try {
        setIsLoadingConfig(true);
        setError(null);
        
        // Get session configuration from backend
        const config = await worldBuildingAPI.getStoryVoiceSessionConfig(worldId, sessionType);
        setSessionConfig(config);
        
        console.log('✅ [STORY_VOICE] Session config loaded:', config);
      } catch (err) {
        console.error('❌ [STORY_VOICE] Error loading session config:', err);
        setError(err instanceof Error ? err.message : 'Failed to load session configuration');
      } finally {
        setIsLoadingConfig(false);
      }
    };

    loadSessionConfig();
  }, [worldId, sessionType]);

  // Enhanced realtime configuration for story worlds
  const realtimeConfig = sessionConfig ? {
    language: sessionConfig.story_context.language || 'english',
    level: sessionConfig.story_context.target_level || 'B1',
    voice: 'alloy',
    topic: 'custom',
    user_prompt: `Collaborative storytelling in ${sessionConfig.story_context.world_title}`,
    // Story world specific parameters
    world_id: worldId,
    session_type: sessionType
  } : null;

  const {
    isConnected,
    isRecording: isRealtimeRecording,
    isInitialized,
    error: realtimeError,
    messages,
    initialize,
    startConversation,
    stopConversation
  } = useRealtime();

  // Duration tracking
  useEffect(() => {
    if (isRecording) {
      durationRef.current = setInterval(() => {
        setDuration(prev => {
          const newDuration = prev + 1;
      // Auto-stop at max duration
      if (sessionConfig && newDuration >= sessionConfig.session_limits.max_duration) {
        handleStopRecording();
      }
          return newDuration;
        });
      }, 1000);
    } else {
      if (durationRef.current) {
        clearInterval(durationRef.current);
        durationRef.current = null;
      }
    }

    return () => {
      if (durationRef.current) {
        clearInterval(durationRef.current);
      }
    };
  }, [isRecording, storyContext.session_limits.max_duration]);

  // Extract transcript from messages
  useEffect(() => {
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const latestTranscript = userMessages[userMessages.length - 1].content;
      setTranscript(latestTranscript);
    }
  }, [messages]);

  const handleStartRecording = async () => {
    try {
      setError(null);
      setDuration(0);
      setTranscript('');
      
      if (!sessionConfig || !realtimeConfig) {
        setError('Session configuration not loaded');
        return;
      }
      
      if (!isInitialized) {
        await initialize(
          realtimeConfig.language,
          realtimeConfig.level,
          'custom',
          realtimeConfig.user_prompt,
          { world_id: worldId, session_type: sessionType }
        );
      }
      
      await startConversation();
      setIsRecording(true);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to start recording. Please check your microphone permissions.');
    }
  };

  const handleStopRecording = async () => {
    try {
      setIsRecording(false);
      stopConversation();
      
      // Process the session
      setIsProcessing(true);
      
      if (!sessionConfig) {
        setError('Session configuration not available');
        setIsProcessing(false);
        return;
      }

      // Validate minimum duration
      if (duration < sessionConfig.session_limits.min_duration) {
        setError(`Recording must be at least ${sessionConfig.session_limits.min_duration} seconds`);
        setIsProcessing(false);
        return;
      }

      // Use the API client to complete the session
      try {
        const result = await worldBuildingAPI.completeStoryVoiceSession(
          worldId,
          sessionType,
          transcript,
          duration
        );

        onSessionComplete({
          transcript,
          duration,
          contribution_id: result.contribution_id
        });
      } catch (apiError) {
        throw new Error(apiError instanceof Error ? apiError.message : 'Failed to complete session');
      }
    } catch (err) {
      console.error('Error processing session:', err);
      setError(err instanceof Error ? err.message : 'Failed to process session');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSessionTypeInfo = () => {
    switch (sessionType) {
      case 'practice':
        return {
          title: 'Story Practice Session',
          description: 'Explore story ideas and practice language skills',
          color: 'blue',
          icon: Target
        };
      case 'contribution':
        return {
          title: 'Story Contribution Session',
          description: 'Add your contribution to the collaborative story',
          color: 'green',
          icon: BookOpen
        };
      case 'review':
        return {
          title: 'Story Review Session',
          description: 'Review and analyze the collaborative story',
          color: 'purple',
          icon: Volume2
        };
      default:
        return {
          title: 'Story Session',
          description: 'Collaborative storytelling session',
          color: 'gray',
          icon: BookOpen
        };
    }
  };

  const sessionInfo = getSessionTypeInfo();
  const SessionIcon = sessionInfo.icon;

  const isValidDuration = sessionConfig ? 
    (duration >= sessionConfig.session_limits.min_duration && 
     duration <= sessionConfig.session_limits.max_duration) : false;

  // Show loading state while configuration is loading
  if (isLoadingConfig) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <p className="text-gray-600">Loading session configuration...</p>
        </div>
      </div>
    );
  }

  // Show error state if configuration failed to load
  if (!sessionConfig) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
        <div className="text-center py-12">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration Error</h3>
          <p className="text-gray-600 mb-4">{error || 'Failed to load session configuration'}</p>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center mb-3">
          <SessionIcon className={`h-6 w-6 mr-3 text-${sessionInfo.color}-600`} />
          <h2 className="text-2xl font-bold text-gray-800">{sessionInfo.title}</h2>
        </div>
        <p className="text-gray-600">{sessionInfo.description}</p>
      </div>

      {/* Story Context Display */}
      <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-l-4 border-blue-500">
        <h3 className="font-bold text-gray-800 mb-2">📚 {sessionConfig.story_context.world_title}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-700 mb-2">
              <span className="font-medium">Genre:</span> {sessionConfig.story_context.genre}
            </p>
            <p className="text-gray-700 mb-2">
              <span className="font-medium">Focus:</span> {sessionConfig.story_context.primary_focus}
            </p>
            {sessionConfig.story_context.vocabulary_themes.length > 0 && (
              <p className="text-gray-700">
                <span className="font-medium">Vocabulary:</span> {sessionConfig.story_context.vocabulary_themes.join(', ')}
              </p>
            )}
          </div>
          <div>
            <p className="text-gray-700 mb-2">
              <span className="font-medium">Characters:</span> {
                sessionConfig.story_context.active_characters.length > 0 
                  ? sessionConfig.story_context.active_characters.map(c => c.name).join(', ')
                  : 'None established yet'
              }
            </p>
            <p className="text-gray-700">
              <span className="font-medium">Locations:</span> {
                sessionConfig.story_context.locations.length > 0
                  ? sessionConfig.story_context.locations.map(l => l.name).join(', ')
                  : 'None established yet'
              }
            </p>
          </div>
        </div>
      </div>

      {/* Current Plot Point */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-semibold text-gray-800 mb-2">📖 Current Story State</h4>
        <p className="text-gray-700 italic">"{sessionConfig.story_context.current_plot_point}"</p>
      </div>

      {/* Previous Contribution Context */}
      {sessionConfig.story_context.previous_contribution && (
        <div className="mb-6 p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-500">
          <h4 className="font-semibold text-gray-800 mb-2">💬 Previous Contribution</h4>
          <p className="text-sm text-gray-600 mb-2">
            By {sessionConfig.story_context.previous_contribution.contributor_name}
          </p>
          <p className="text-gray-700 italic">"{sessionConfig.story_context.previous_contribution.transcript}"</p>
        </div>
      )}

      {/* Recording Interface */}
      <div className="mb-6 p-6 border-2 border-dashed border-gray-300 rounded-lg text-center">
        {/* Connection Status */}
        {!isConnected && !isInitialized && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-yellow-800">Click "Start Recording" to connect to the AI tutor</p>
          </div>
        )}

        {isInitialized && !isConnected && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <p className="text-blue-800">Connecting to AI tutor...</p>
            </div>
          </div>
        )}

        {/* Recording Controls */}
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            disabled={isProcessing || (isInitialized && !isConnected)}
            className={`flex items-center px-8 py-4 rounded-full font-medium text-lg transition-all duration-200 ${
              isRecording
                ? 'bg-red-500 text-white hover:bg-red-600 shadow-lg'
                : 'bg-green-500 text-white hover:bg-green-600 shadow-lg'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                Processing...
              </>
            ) : isRecording ? (
              <>
                <MicOff className="h-6 w-6 mr-3" />
                Stop Recording
              </>
            ) : (
              <>
                <Mic className="h-6 w-6 mr-3" />
                Start Recording
              </>
            )}
          </button>

          {/* Duration Display */}
          <div className="flex items-center space-x-4 text-lg">
            <div className="flex items-center">
              <Clock className="h-5 w-5 mr-2 text-gray-600" />
              <span className={`font-mono ${isValidDuration ? 'text-green-600' : 'text-red-500'}`}>
                {formatDuration(duration)}
              </span>
            </div>
            <span className="text-gray-400">|</span>
            <span className="text-sm text-gray-600">
              {formatDuration(sessionConfig.session_limits.min_duration)} - {formatDuration(sessionConfig.session_limits.max_duration)}
            </span>
          </div>

          {/* Recording Status */}
          {isRecording && (
            <div className="flex items-center space-x-2 text-red-500">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="font-medium">Recording in progress...</span>
            </div>
          )}
        </div>
      </div>

      {/* Live Transcript */}
      {transcript && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-2">📝 Live Transcript</h4>
          <p className="text-gray-700">{transcript}</p>
        </div>
      )}

      {/* AI Tutor Messages */}
      {messages.filter(msg => msg.role === 'assistant').length > 0 && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold text-blue-800 mb-2">🤖 AI Tutor Feedback</h4>
          <div className="space-y-2">
            {messages.filter(msg => msg.role === 'assistant').slice(-3).map((msg, index) => (
              <p key={index} className="text-blue-700">{msg.content}</p>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {(error || realtimeError) && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error || realtimeError}</p>
        </div>
      )}

      {/* Session Guidelines */}
      <div className="mb-6 p-4 bg-green-50 rounded-lg">
        <h4 className="font-medium text-green-800 mb-2">💡 Session Guidelines</h4>
        <ul className="text-sm text-green-700 space-y-1">
          {sessionType === 'contribution' ? (
            <>
              <li>• Continue the story naturally from the previous contribution</li>
              <li>• Stay consistent with established characters and locations</li>
              <li>• Focus on {sessionConfig.story_context.primary_focus} while storytelling</li>
              <li>• This contribution will be saved to the collaborative story</li>
            </>
          ) : sessionType === 'practice' ? (
            <>
              <li>• Explore story ideas and practice language skills</li>
              <li>• Experiment with vocabulary and grammar</li>
              <li>• This session will NOT be saved to the story</li>
              <li>• Focus on learning and improvement</li>
            </>
          ) : (
            <>
              <li>• Review and analyze the collaborative story</li>
              <li>• Discuss language use and story development</li>
              <li>• Learn from the collaborative narrative</li>
              <li>• Focus on understanding and analysis</li>
            </>
          )}
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-4">
        <button
          onClick={onCancel}
          disabled={isRecording || isProcessing}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
