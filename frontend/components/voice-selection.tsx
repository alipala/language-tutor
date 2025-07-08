'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { CheckCircle, Volume2, Play, Pause, Loader2 } from 'lucide-react';
import { getApiUrl } from '@/lib/api-utils';

const API_URL = getApiUrl();

// Voice data with descriptions
const VOICES = [
  {
    id: 'alloy',
    name: 'Alloy',
    description: 'Balanced and clear voice, great for general learning',
    avatar: '/images/tutors/alloy.svg',
    personality: 'Professional and encouraging'
  },
  {
    id: 'ash',
    name: 'Ash',
    description: 'Warm and friendly voice, perfect for conversational practice',
    avatar: '/images/tutors/ash.svg',
    personality: 'Warm and approachable'
  },
  {
    id: 'ballad',
    name: 'Ballad',
    description: 'Melodic and expressive voice, ideal for pronunciation work',
    avatar: '/images/tutors/ballad.svg',
    personality: 'Expressive and articulate'
  },
  {
    id: 'coral',
    name: 'Coral',
    description: 'Bright and energetic voice, motivating for active learning',
    avatar: '/images/tutors/coral.svg',
    personality: 'Energetic and motivating'
  },
  {
    id: 'echo',
    name: 'Echo',
    description: 'Calm and patient voice, excellent for beginners',
    avatar: '/images/tutors/echo.svg',
    personality: 'Patient and supportive'
  },
  {
    id: 'sage',
    name: 'Sage',
    description: 'Storytelling voice, engaging for immersive conversations',
    avatar: '/images/tutors/sage.svg',
    personality: 'Engaging storyteller'
  },
  {
    id: 'shimmer',
    name: 'Shimmer',
    description: 'Deep and confident voice, great for advanced learners',
    avatar: '/images/tutors/shimmer.svg',
    personality: 'Confident and authoritative'
  },
  {
    id: 'verse',
    name: 'Verse',
    description: 'Modern and dynamic voice, perfect for contemporary topics',
    avatar: '/images/tutors/verse.svg',
    personality: 'Dynamic and modern'
  }
];

export default function VoiceSelectionComponent() {
  const [selectedVoice, setSelectedVoice] = useState<string>('alloy');
  const [currentVoice, setCurrentVoice] = useState<string>('alloy');
  const [isLoading, setIsLoading] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingVoice, setPendingVoice] = useState<string>('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [loadingVoices, setLoadingVoices] = useState(true);

  // Load current voice preference
  useEffect(() => {
    fetchCurrentVoice();
  }, []);

  const fetchCurrentVoice = async () => {
    setLoadingVoices(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.log('[VOICE_SELECTION] No token found');
        setLoadingVoices(false);
        return;
      }

      const response = await fetch(`${API_URL}/auth/get-voice`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[VOICE_SELECTION] Current voice:', data.voice);
        setSelectedVoice(data.voice);
        setCurrentVoice(data.voice);
      } else {
        console.error('[VOICE_SELECTION] Failed to fetch current voice');
      }
    } catch (error) {
      console.error('[VOICE_SELECTION] Error fetching current voice:', error);
    } finally {
      setLoadingVoices(false);
    }
  };

  const handleVoiceSelect = (voiceId: string) => {
    if (voiceId === currentVoice) {
      return; // Already selected
    }
    
    setPendingVoice(voiceId);
    setShowConfirmModal(true);
  };

  const handleConfirmVoiceChange = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/auth/select-voice`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          voice: pendingVoice
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[VOICE_SELECTION] Voice updated successfully:', data);
        
        setSelectedVoice(pendingVoice);
        setCurrentVoice(pendingVoice);
        setMessage({
          type: 'success',
          text: data.message || `AI Tutor voice successfully updated to ${pendingVoice}`
        });
        
        // Clear message after 5 seconds
        setTimeout(() => setMessage(null), 5000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update voice preference');
      }
    } catch (error: any) {
      console.error('[VOICE_SELECTION] Error updating voice:', error);
      setMessage({
        type: 'error',
        text: error.message || 'Failed to update voice preference. Please try again.'
      });
      
      // Reset selection on error
      setSelectedVoice(currentVoice);
      
      // Clear error message after 5 seconds
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setIsLoading(false);
      setShowConfirmModal(false);
      setPendingVoice('');
    }
  };

  const handlePlayVoicePreview = async (voiceId: string) => {
    if (playingVoice) {
      console.log('[VOICE_PREVIEW] Already playing a voice sample, ignoring request');
      return;
    }

    setPlayingVoice(voiceId);
    
    try {
      console.log(`[VOICE_PREVIEW] Starting voice sample for: ${voiceId}`);
      
      // Get voice sample data from backend
      const response = await fetch(`${API_URL}/api/voice/sample`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          voice_id: voiceId,
          language: 'english',
          level: 'intermediate'
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to get voice sample: ${response.status}`);
      }

      const sampleData = await response.json();
      console.log('[VOICE_PREVIEW] Voice sample data received:', sampleData);

      if (!sampleData.success || !sampleData.ephemeral_key) {
        throw new Error('Invalid voice sample response');
      }

      // Create WebRTC connection for voice sample playback
      await playVoiceSample(sampleData.ephemeral_key, sampleData.sample_text, voiceId);
      
    } catch (error) {
      console.error('[VOICE_PREVIEW] Error playing voice sample:', error);
      // Show visual feedback for 3 seconds even on error
      setTimeout(() => {
        setPlayingVoice(null);
      }, 3000);
    }
  };

  const playVoiceSample = async (ephemeralKey: string, sampleText: string, voiceId: string) => {
    return new Promise<void>((resolve, reject) => {
      let peerConnection: RTCPeerConnection | null = null;
      let dataChannel: RTCDataChannel | null = null;
      let audioElement: HTMLAudioElement | null = null;
      let sampleTimeout: NodeJS.Timeout | null = null;

      const cleanup = () => {
        console.log('[VOICE_PREVIEW] Cleaning up voice sample connection');
        
        if (sampleTimeout) {
          clearTimeout(sampleTimeout);
          sampleTimeout = null;
        }

        if (audioElement) {
          audioElement.pause();
          audioElement.srcObject = null;
          audioElement = null;
        }

        if (dataChannel) {
          dataChannel.close();
          dataChannel = null;
        }

        if (peerConnection) {
          peerConnection.close();
          peerConnection = null;
        }

        setPlayingVoice(null);
      };

      const startSample = async () => {
        try {
          console.log('[VOICE_PREVIEW] Setting up WebRTC connection for voice sample');
          
          // Create peer connection
          peerConnection = new RTCPeerConnection({
            iceServers: [
              { urls: 'stun:stun.l.google.com:19302' },
              { urls: 'stun:stun1.l.google.com:19302' }
            ]
          });

          // Set up audio element
          audioElement = new Audio();
          audioElement.autoplay = true;
          audioElement.volume = 0.8;

          // Handle incoming audio stream
          peerConnection.ontrack = (event) => {
            console.log('[VOICE_PREVIEW] Received audio track for voice sample');
            if (audioElement && event.streams && event.streams[0]) {
              audioElement.srcObject = event.streams[0];
            }
          };

          // Create data channel
          dataChannel = peerConnection.createDataChannel('oai-events', { ordered: true });
          
          dataChannel.onopen = () => {
            console.log('[VOICE_PREVIEW] Data channel opened, sending sample request');
            
            // Wait a moment for the session to be fully ready
            setTimeout(() => {
              // Send a simple response.create message to trigger the voice sample
              const message = {
                type: 'response.create',
                response: {
                  modalities: ['audio']
                }
              };
              
              if (dataChannel && dataChannel.readyState === 'open') {
                dataChannel.send(JSON.stringify(message));
                console.log('[VOICE_PREVIEW] Sent response.create message');
              }
            }, 500);
          };

          dataChannel.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);
              console.log('[VOICE_PREVIEW] Received message:', message.type);
              
              // Handle different message types
              if (message.type === 'session.created') {
                console.log('[VOICE_PREVIEW] Session created successfully');
              } else if (message.type === 'error') {
                console.error('[VOICE_PREVIEW] Received error from OpenAI:', message);
                cleanup();
                reject(new Error(`OpenAI error: ${message.error?.message || 'Unknown error'}`));
                return;
              } else if (message.type === 'response.audio.delta') {
                console.log('[VOICE_PREVIEW] Receiving audio data...');
              } else if (message.type === 'response.audio.done' || message.type === 'response.done') {
                console.log('[VOICE_PREVIEW] Voice sample completed');
                sampleTimeout = setTimeout(() => {
                  cleanup();
                  resolve();
                }, 2000); // Give more time for audio to finish
              }
            } catch (e) {
              console.error('[VOICE_PREVIEW] Error parsing message:', e);
            }
          };

          dataChannel.onerror = (error) => {
            console.error('[VOICE_PREVIEW] Data channel error:', error);
            cleanup();
            reject(error);
          };

          dataChannel.onclose = () => {
            console.log('[VOICE_PREVIEW] Data channel closed');
          };

          // Create offer
          const offer = await peerConnection.createOffer({ offerToReceiveAudio: true });
          await peerConnection.setLocalDescription(offer);

          // Wait for ICE gathering
          await new Promise<void>((resolve) => {
            const checkIceGathering = () => {
              if (peerConnection?.iceGatheringState === 'complete') {
                resolve();
              } else {
                setTimeout(checkIceGathering, 100);
              }
            };
            checkIceGathering();
          });

          // Send offer to OpenAI
          const response = await fetch(`https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17`, {
            method: 'POST',
            body: peerConnection.localDescription?.sdp,
            headers: {
              'Authorization': `Bearer ${ephemeralKey}`,
              'Content-Type': 'application/sdp'
            }
          });

          if (!response.ok) {
            throw new Error(`OpenAI connection failed: ${response.status}`);
          }

          // Set remote description
          const answerSdp = await response.text();
          await peerConnection.setRemoteDescription({
            type: 'answer',
            sdp: answerSdp
          });

          console.log('[VOICE_PREVIEW] WebRTC connection established for voice sample');

          // Set a maximum duration for the sample (10 seconds)
          sampleTimeout = setTimeout(() => {
            console.log('[VOICE_PREVIEW] Voice sample timeout reached');
            cleanup();
            resolve();
          }, 10000);

        } catch (error) {
          console.error('[VOICE_PREVIEW] Error in voice sample setup:', error);
          cleanup();
          reject(error);
        }
      };

      startSample();
    });
  };

  const getVoiceData = (voiceId: string) => {
    return VOICES.find(v => v.id === voiceId) || VOICES[0];
  };

  if (loadingVoices) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="flex items-center space-x-3">
          <Loader2 className="h-6 w-6 animate-spin text-teal-500" />
          <span className="text-gray-600">Loading voice preferences...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success/Error Message */}
      {message && (
        <div className={`p-4 rounded-xl border ${
          message.type === 'success' 
            ? 'bg-green-50 border-green-200 text-green-700' 
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          <div className="flex items-center space-x-2">
            {message.type === 'success' ? (
              <CheckCircle className="h-5 w-5" />
            ) : (
              <div className="h-5 w-5 rounded-full bg-red-500 flex items-center justify-center">
                <span className="text-white text-xs">!</span>
              </div>
            )}
            <span className="font-medium">{message.text}</span>
          </div>
        </div>
      )}

      {/* Current Voice Display */}
      <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200 rounded-xl p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl overflow-hidden bg-white shadow-sm">
            <img 
              src={getVoiceData(currentVoice).avatar} 
              alt={getVoiceData(currentVoice).name}
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <h4 className="font-semibold text-gray-800">
              Current Voice: {getVoiceData(currentVoice).name}
            </h4>
            <p className="text-sm text-gray-600">
              {getVoiceData(currentVoice).description}
            </p>
          </div>
        </div>
      </div>

      {/* Voice Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {VOICES.map((voice) => (
          <div
            key={voice.id}
            className={`relative group cursor-pointer transition-all duration-200 ${
              selectedVoice === voice.id
                ? 'ring-2 ring-teal-500 shadow-lg'
                : 'hover:shadow-md hover:scale-105'
            }`}
            onClick={() => handleVoiceSelect(voice.id)}
          >
            <div className={`bg-white rounded-xl p-4 border-2 transition-all ${
              selectedVoice === voice.id
                ? 'border-teal-500 bg-teal-50'
                : 'border-gray-200 hover:border-teal-300'
            }`}>
              {/* Avatar */}
              <div className="relative mb-3">
                <div className="w-16 h-16 mx-auto rounded-xl overflow-hidden bg-gray-100 shadow-sm">
                  <img 
                    src={voice.avatar} 
                    alt={voice.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* Selection Indicator */}
                {selectedVoice === voice.id && (
                  <div className="absolute -top-1 -right-1 w-6 h-6 bg-teal-500 rounded-full flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-white" />
                  </div>
                )}
                
                {/* Play Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlayVoicePreview(voice.id);
                  }}
                  className="absolute inset-0 bg-black/50 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                >
                  {playingVoice === voice.id ? (
                    <div className="flex items-center space-x-1 text-white">
                      <div className="w-1 h-4 bg-white animate-pulse"></div>
                      <div className="w-1 h-6 bg-white animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1 h-4 bg-white animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  ) : (
                    <Play className="h-6 w-6 text-white" />
                  )}
                </button>
              </div>
              
              {/* Voice Info */}
              <div className="text-center">
                <h4 className="font-semibold text-gray-800 mb-1">{voice.name}</h4>
                <p className="text-xs text-gray-600 mb-2">{voice.personality}</p>
                <p className="text-xs text-gray-500 leading-tight">{voice.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info Section */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="flex items-start space-x-3">
          <Volume2 className="h-5 w-5 text-gray-500 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="font-medium text-gray-800 mb-1">🎤 How Voice Selection Works</h5>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Your selected voice will be used for all AI tutor conversations</li>
              <li>• Voice changes apply immediately to new practice sessions</li>
              <li>• Each voice has a unique personality and speaking style</li>
              <li>• You can change your voice preference anytime from this page</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      <Dialog open={showConfirmModal} onOpenChange={setShowConfirmModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Volume2 className="h-5 w-5 text-teal-500" />
              <span>Confirm Voice Change</span>
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto rounded-xl overflow-hidden bg-gray-100 shadow-sm mb-3">
                <img 
                  src={getVoiceData(pendingVoice).avatar} 
                  alt={getVoiceData(pendingVoice).name}
                  className="w-full h-full object-cover"
                />
              </div>
              <h4 className="font-semibold text-gray-800 mb-1">
                {getVoiceData(pendingVoice).name}
              </h4>
              <p className="text-sm text-gray-600 mb-2">
                {getVoiceData(pendingVoice).personality}
              </p>
              <p className="text-sm text-gray-500">
                {getVoiceData(pendingVoice).description}
              </p>
            </div>
            
            <div className="bg-teal-50 border border-teal-200 rounded-lg p-3">
              <p className="text-sm text-teal-700">
                <strong>🎤 Voice Update:</strong> This voice will be used for all your future AI tutor conversations. 
                You can change it again anytime from your profile settings.
              </p>
            </div>
            
            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShowConfirmModal(false);
                  setPendingVoice('');
                  setSelectedVoice(currentVoice);
                }}
                disabled={isLoading}
                className="flex-1 border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900"
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmVoiceChange}
                disabled={isLoading}
                className="flex-1 text-white"
                style={{ backgroundColor: '#4ECFBF' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Updating...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Confirm Change
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
