import { RealtimeEvent, RealtimeResponseCreateEvent } from './types';
import { SemanticMuteController } from './semanticMuteController';

export class RealtimeService {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private localStream: MediaStream | null = null;
  private isConnected: boolean = false;
  private ephemeralKey: string = '';
  private backendUrl: string = '';
  private onMessageCallback: ((event: RealtimeEvent) => void) | null = null;
  private onConnectedCallback: (() => void) | null = null;
  private onDisconnectedCallback: (() => void) | null = null;
  private connectionAttemptTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 3;
  private currentLanguage: string = '';
  private currentLevel: string = '';
  private currentTopic: string = '';
  private currentUserPrompt: string = '';
  private currentAssessmentData: any = null;
  private currentLanguageIsoCode: string = '';
  private isPaused: boolean = false;
  private pauseStartTime: number | null = null;
  private semanticMuteController: SemanticMuteController | null = null;
  
  // ✅ CRITICAL: Fallback AI speaking state tracking for when SemanticMuteController fails
  private ai_is_speaking: boolean = false;
  private fallback_mute_timeout: NodeJS.Timeout | null = null;
  private fallback_protection_enabled: boolean = true;
  private last_ai_speech_event: string = '';

  constructor() {
    // Only initialize Audio in browser environments
    if (typeof window !== 'undefined') {
      this.audioElement = new Audio();
      this.audioElement.autoplay = true;
    }
  }

  /**
   * Initialize the realtime service
   */
  public async initialize(
    onMessage: (event: RealtimeEvent) => void, 
    onConnected?: () => void, 
    onDisconnected?: () => void,
    language?: string,
    level?: string,
    topic?: string,
    userPrompt?: string,
    assessmentData?: any
  ): Promise<boolean> {
    try {
      console.log('🌐 [UNIVERSAL] Initializing realtime service...');
      // Clean up any existing connections first
      this.disconnect();
      
      this.onMessageCallback = onMessage;
      this.onConnectedCallback = onConnected || null;
      this.onDisconnectedCallback = onDisconnected || null;
      this.reconnectAttempts = 0;
      
      // Store all parameters for use in conversation resumption
      if (language) {
        this.currentLanguage = language.toLowerCase();
        this.currentLanguageIsoCode = this.getLanguageIsoCode(this.currentLanguage);
        console.log('🌐 Language set for transcription:', this.currentLanguage, 'ISO code:', this.currentLanguageIsoCode);
      }
      if (level) {
        this.currentLevel = level;
      }
      if (topic) {
        this.currentTopic = topic;
      }
      if (userPrompt) {
        this.currentUserPrompt = userPrompt;
      }
      if (assessmentData) {
        this.currentAssessmentData = assessmentData;
      }
      
      // Use the correct backend URL (default to 127.0.0.1:8000 if running locally)
      this.backendUrl = '';
      if (typeof window !== 'undefined') {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          this.backendUrl = 'http://127.0.0.1:8000';
        }
      }
      
      console.log('🌐 Using backend URL:', this.backendUrl);
      
      // Test the connection to the backend first
      try {
        const testResponse = await fetch(`${this.backendUrl}/api/test`, {
          credentials: 'same-origin'
        });
        if (!testResponse.ok) {
          console.error('❌ Backend connection test failed:', await testResponse.text());
          return false;
        }
        const testData = await testResponse.json();
        console.log('✅ Backend connection test successful:', testData.message);
      } catch (err) {
        console.error('❌ Error connecting to backend:', err);
        return false;
      }
      
      try {
        // Get ephemeral key from backend with language and level if provided
        const token = await this.getEphemeralKey(language, level, topic, userPrompt, assessmentData);
        if (!token) {
          console.error('❌ Failed to get ephemeral key (empty token)');
          return false;
        }
        
        console.log('✅ Ephemeral key obtained successfully');
        this.ephemeralKey = token;
        return true;
      } catch (err) {
        console.error('❌ Error getting ephemeral key:', err);
        return false;
      }
    } catch (error) {
      console.error('❌ Error initializing realtime service:', error);
      return false;
    }
  }
  
  /**
   * Set up WebRTC connection with universal browser compatibility
   */
  private setupWebRTC(): boolean {
    try {
      console.log('🌐 Setting up WebRTC for universal browser support...');
      
      // Create peer connection with STUN servers
      this.peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
        ]
      });
      
      // Set up audio handling
      this.peerConnection.ontrack = (e) => {
        console.log('🎵 Received remote track', e.streams);
        if (this.audioElement && e.streams && e.streams[0]) {
          this.audioElement.srcObject = e.streams[0];
        }
      };
      
      // ✅ UNIVERSAL: Listen for connection state changes (recommended by OpenAI)
      this.peerConnection.onconnectionstatechange = () => {
        const state = this.peerConnection?.connectionState;
        console.log('🌐 Connection state changed:', state);
        
        if (state === 'connected') {
          console.log('✅ WebRTC connection fully established');
        } else if (state === 'failed' || state === 'disconnected') {
          console.warn('⚠️ WebRTC connection failed/disconnected');
        }
      };
      
      // Set up data channel with specific configuration for transcription
      this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
        ordered: true,
        maxRetransmits: 3  // Add retry mechanism for reliability
      });
      
      this.dataChannel.onopen = () => {
        console.log('✅ Data channel opened');
        this.isConnected = true;
        
        // ✅ CRITICAL CHANGE: DO NOT send session.update here
        // The ephemeral token already contains all the instructions
        // This eliminates race conditions on mobile browsers
        console.log('✅ Data channel ready - using ephemeral token instructions only');
        
        if (this.onConnectedCallback) this.onConnectedCallback();
      };
      
      this.dataChannel.onclose = () => {
        console.log('❌ Data channel closed');
        this.isConnected = false;
        if (this.onDisconnectedCallback) this.onDisconnectedCallback();
      };
      
      this.dataChannel.onmessage = (e) => {
        if (this.onMessageCallback) {
          try {
            const eventData = JSON.parse(e.data) as RealtimeEvent;
            console.log('📨 Received message type:', eventData.type);
            
            // ✅ SEMANTIC VAD: Handle events with SemanticMuteController
            if (this.semanticMuteController) {
              this.semanticMuteController.handleRealtimeEvent(eventData);
            } else {
              // ✅ CRITICAL: Fallback handling when SemanticMuteController is null
              this.handleFallbackMuting(eventData);
            }
            
            // Log specific details for transcription events
            if (eventData.type === 'conversation.item.created') {
              console.log('💬 Conversation item created:', 
                eventData.item?.role, 
                eventData.item?.content ? 'Content array present' : 'No content array',
                eventData.item?.input ? 'Input present' : 'No input');
            } else if (eventData.type === 'conversation.item.input_audio_transcription.completed') {
              console.log('📝 Transcription completed:', eventData.transcription?.text);
            } else if (eventData.type === 'input_audio_buffer.speech_stopped') {
              // Emit user speaking completion event for conversation help modal hiding
              if (typeof window !== 'undefined') {
                const userSpeakingCompleteEvent = new CustomEvent('user-speaking-complete');
                window.dispatchEvent(userSpeakingCompleteEvent);
                console.log('[CONVERSATION_HELP] Emitted user-speaking-complete event from input_audio_buffer.speech_stopped');
                
                // Also emit input-audio-stop for modal hiding with animation
                const inputAudioStopEvent = new CustomEvent('input-audio-stop');
                window.dispatchEvent(inputAudioStopEvent);
                console.log('[CONVERSATION_HELP] Emitted input-audio-stop event for modal hiding with animation');
              }
            }
            
            this.onMessageCallback(eventData);
          } catch (error) {
            console.error('❌ Error parsing message:', error);
          }
        }
      };
      
      // Set up ICE candidate handling
      this.peerConnection.onicecandidate = (event) => {
        console.log('🧊 ICE candidate', event.candidate);
      };
      
      this.peerConnection.oniceconnectionstatechange = () => {
        console.log('🧊 ICE connection state:', this.peerConnection?.iceConnectionState);
        if (this.peerConnection?.iceConnectionState === 'failed' || 
            this.peerConnection?.iceConnectionState === 'disconnected') {
          console.warn('⚠️ ICE connection failed or disconnected');
        }
      };
      
      return true;
    } catch (error) {
      console.error('❌ Error setting up WebRTC:', error);
      return false;
    }
  }
  
  /**
   * Request microphone access and add tracks to peer connection
   * Universal implementation that works on both desktop and mobile
   */
  public async startMicrophone(): Promise<boolean> {
    try {
      console.log('🎤 Requesting microphone access (universal)...');
      if (typeof window === 'undefined') return false;
      
      // Set up WebRTC if not already done
      if (!this.peerConnection) {
        console.log('🌐 Setting up WebRTC connection first...');
        const setupSuccess = this.setupWebRTC();
        if (!setupSuccess) {
          console.error('❌ Failed to set up WebRTC connection');
          return false;
        }
        
        // ✅ UNIVERSAL: Add delay for all browsers to ensure WebRTC is ready
        await new Promise(resolve => setTimeout(resolve, 300));
      }
      
      // Release any existing stream to avoid resource leaks
      if (this.localStream) {
        console.log('🧹 Releasing existing media stream...');
        this.localStream.getTracks().forEach(track => {
          track.stop();
          console.log(`🛑 Stopped track: ${track.kind}`);
        });
        this.localStream = null;
        
        // Add a small delay after stopping tracks to ensure they're fully released
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      // ✅ UNIVERSAL SEMANTIC VAD: Enhanced constraints for ALL browsers and devices
      // Works on: Desktop (Chrome, Firefox, Safari, Edge), Mobile (iOS Safari, Android Chrome), etc.
      const constraints = {
        audio: {
          // ✅ Standard WebRTC constraints (supported by all browsers)
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          
          // ✅ Chrome/Chromium-based browsers (Chrome, Edge, Opera, Android Chrome)
          googEchoCancellationType: "system",
          googNoiseSuppressionLevel: 2,
          googExperimentalEchoCancellation: true,
          googAutoGainControl2: true,
          googHighpassFilter: true,
          googTypingNoiseDetection: true,
          googAudioMirroring: false,
          googDAEchoCancellation: true,
          googNoiseSuppression2: true,
          
          // ✅ Firefox-specific optimizations
          mozEchoCancellation: true,
          mozNoiseSuppression: true,
          mozAutoGainControl: true,
          
          // ✅ Safari/WebKit optimizations (Desktop Safari, iOS Safari)
          webkitEchoCancellation: true,
          webkitNoiseSuppression: true,
          webkitAutoGainControl: true,
          
          // ✅ Universal latency and quality optimization
          latency: { ideal: 0.01, max: 0.02 },
          sampleRate: { ideal: 48000 },
          channelCount: { ideal: 1, max: 1 },
          
          // ✅ Additional semantic VAD optimizations for all browsers
          sampleSize: { ideal: 16 },
          volume: { ideal: 1.0 }
        }
      };
      
      console.log('🎤 Requesting user media with constraints:', JSON.stringify(constraints));
      
      try {
        // First try with a timeout to prevent hanging if permission dialog is ignored
        const getUserMediaPromise = navigator.mediaDevices.getUserMedia(constraints);
        const timeoutPromise = new Promise<MediaStream>((_, reject) => {
          setTimeout(() => reject(new Error('Microphone access request timed out')), 10000);
        });
        
        this.localStream = await Promise.race([getUserMediaPromise, timeoutPromise]);
        console.log('✅ Microphone access granted', this.localStream);
      } catch (mediaError) {
        console.error('⚠️ First attempt to get user media failed:', mediaError);
        
        // Wait a moment and try again with a simpler constraint
        await new Promise(resolve => setTimeout(resolve, 500));
        console.log('🔄 Retrying with simpler constraints...');
        
        try {
          this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          console.log('✅ Microphone access granted on second attempt');
        } catch (retryError) {
          console.error('❌ Second attempt to get user media failed:', retryError);
          throw retryError; // Re-throw to be caught by the outer catch block
        }
      }
      
      // Add audio track to peer connection
      if (this.peerConnection && this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        if (audioTracks.length === 0) {
          console.error('❌ No audio tracks found in media stream');
          return false;
        }
        
        console.log('🎵 Adding audio track to peer connection', audioTracks[0].label);
        
        try {
          const sender = this.peerConnection.addTrack(audioTracks[0], this.localStream);
          console.log('✅ Track added successfully, sender created:', sender ? 'Yes' : 'No');
          
          // ✅ SEMANTIC VAD: Initialize SemanticMuteController with the media stream
          try {
            this.semanticMuteController = new SemanticMuteController();
            const muteControllerInitialized = await this.semanticMuteController.initialize(this.localStream);
            if (muteControllerInitialized) {
              console.log('✅ [SEMANTIC_VAD] SemanticMuteController initialized successfully');
            } else {
              console.warn('⚠️ [SEMANTIC_VAD] SemanticMuteController initialization failed, continuing without it');
              this.semanticMuteController = null;
            }
          } catch (muteError) {
            console.error('❌ [SEMANTIC_VAD] Error initializing SemanticMuteController:', muteError);
            this.semanticMuteController = null;
          }
          
          // ✅ UNIVERSAL: Add delay after adding track (helps mobile browsers)
          await new Promise(resolve => setTimeout(resolve, 200));
          return true;
        } catch (trackError) {
          console.error('❌ Error adding track to peer connection:', trackError);
          return false;
        }
      }
      
      return false;
    } catch (error) {
      console.error('❌ Error starting microphone:', error);
      
      // Specific error handling for common issues
      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          console.error('🚫 Microphone permission denied by user');
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
          console.error('🔍 No microphone found on this device');
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
          console.error('🔒 Microphone is already in use by another application');
        }
      }
      
      return false;
    }
  }
  
  /**
   * Connect to OpenAI Realtime API
   */
  public async connect(): Promise<boolean> {
    try {
      console.log('🚀 Connecting to OpenAI...');
      if (!this.peerConnection) {
        console.error('❌ Peer connection not initialized');
        return false;
      }
      
      // Clear any existing timeout
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
      }
      
      // Set connection timeout
      this.connectionAttemptTimeout = setTimeout(() => {
        console.error('⏰ Connection attempt timed out');
        this.disconnect();
      }, 15000);
      
      // Make sure data channel is created before creating the offer
      if (!this.dataChannel || this.dataChannel.readyState === 'closed') {
        console.log('🔄 Creating new data channel before offer...');
        try {
          this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
            ordered: true
          });
          
          console.log('✅ Data channel created successfully');
          
          this.dataChannel.onopen = () => {
            console.log('✅ Data channel opened');
            this.isConnected = true;
            if (this.onConnectedCallback) this.onConnectedCallback();
          };
          
          this.dataChannel.onclose = () => {
            console.log('❌ Data channel closed');
            this.isConnected = false;
            if (this.onDisconnectedCallback) this.onDisconnectedCallback();
          };
          
          this.dataChannel.onmessage = (e) => {
            if (this.onMessageCallback) {
              try {
                const eventData = JSON.parse(e.data) as RealtimeEvent;
                this.onMessageCallback(eventData);
              } catch (error) {
                console.error('❌ Error parsing message:', error);
              }
            }
          };
          
          // Add a small delay after creating the data channel
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (channelError) {
          console.error('❌ Error creating data channel:', channelError);
          return false;
        }
      }
      
      // Create offer
      console.log('📝 Creating offer...');
      // Variable to store the complete offer with ICE candidates
      let completeOffer: RTCSessionDescriptionInit | null = null;
      
      try {
        const offer = await this.peerConnection.createOffer({
          offerToReceiveAudio: true
        });
        
        console.log('📝 Setting local description...');
        await this.peerConnection.setLocalDescription(offer);
        console.log('✅ Local description set successfully');
        
        // Add a small delay after setting local description
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Wait for ICE gathering to complete
        console.log('🧊 Waiting for ICE gathering to complete...');
        completeOffer = await this.waitForIceComplete();
        if (!completeOffer) {
          console.error('❌ Failed to gather ICE candidates');
          return false;
        }
        
        console.log('✅ ICE gathering completed successfully');
      } catch (offerError) {
        console.error('❌ Error creating or processing offer:', offerError);
        return false;
      }
      
      // Send offer to OpenAI
      console.log('📤 Sending offer to OpenAI...');
      const baseUrl = 'https://api.openai.com/v1/realtime';
      const model = 'gpt-4o-realtime-preview-2024-12-17';
      const sdpResponse = await fetch(`${baseUrl}?model=${model}`, {
        method: 'POST',
        body: completeOffer.sdp,
        headers: {
          'Authorization': `Bearer ${this.ephemeralKey}`,
          'Content-Type': 'application/sdp'
        },
      });
      
      if (!sdpResponse.ok) {
        const errorText = await sdpResponse.text();
        console.error('❌ Error connecting to OpenAI:', errorText);
        return false;
      }
      
      // Set remote description
      console.log('📝 Setting remote description...');
      const answer = {
        type: 'answer' as RTCSdpType,
        sdp: await sdpResponse.text(),
      };
      
      await this.peerConnection.setRemoteDescription(answer);
      
      // Clear timeout as connection was successful
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
        this.connectionAttemptTimeout = null;
      }
      
      console.log('✅ Connected to OpenAI successfully');
      return true;
    } catch (error) {
      console.error('❌ Error connecting to OpenAI:', error);
      return false;
    }
  }
  
  /**
   * Wait for ICE gathering to complete
   */
  private async waitForIceComplete(): Promise<RTCSessionDescriptionInit | null> {
    if (!this.peerConnection || !this.peerConnection.localDescription) {
      return null;
    }
    
    return new Promise((resolve) => {
      // Set a timeout to prevent waiting indefinitely
      const timeout = setTimeout(() => {
        console.warn('⚠️ ICE gathering timed out, proceeding with available candidates');
        if (this.peerConnection?.localDescription) {
          resolve(this.peerConnection.localDescription);
        } else {
          resolve(null);
        }
      }, 5000);
      
      const checkIce = () => {
        if (this.peerConnection?.iceGatheringState === 'complete') {
          clearTimeout(timeout);
          resolve(this.peerConnection.localDescription);
        } else {
          setTimeout(checkIce, 100);
        }
      };
      
      checkIce();
    });
  }
  
  /**
   * Send a message through the data channel
   */
  public sendMessage(message: RealtimeEvent): boolean {
    if (!this.dataChannel) {
      console.error('❌ Data channel not available, cannot send message');
      return false;
    }
    
    // If data channel is connecting, wait for it to open
    if (this.dataChannel.readyState === 'connecting') {
      console.log('⏳ Data channel is connecting, waiting for it to open...');
      return false;
    }
    
    // If data channel is not open, cannot send message
    if (this.dataChannel.readyState !== 'open') {
      console.error(`❌ Data channel not open (state: ${this.dataChannel.readyState}), cannot send message`);
      return false;
    }
    
    try {
      const messageString = JSON.stringify(message);
      console.log('📤 Sending message:', message.type);
      this.dataChannel.send(messageString);
      return true;
    } catch (error) {
      console.error('❌ Error sending message:', error);
      return false;
    }
  }
  
  /**
   * Start a conversation with OpenAI - Universal implementation
   */
  public async startConversation(instructions?: string): Promise<boolean> {
    console.log('🚀 Starting conversation with universal approach...');
    
    // If we have conversation instructions (for resuming), we need to get a new ephemeral key
    // that includes this conversation history
    if (instructions) {
      console.log('📝 Conversation instructions provided - getting new ephemeral key with context');
      
      // Get a new ephemeral key with the conversation history
      const newToken = await this.getEphemeralKey(
        this.currentLanguage, 
        this.currentLevel, // Use stored level
        this.currentTopic, // Use stored topic
        this.currentUserPrompt, // Use stored userPrompt
        this.currentAssessmentData, // Use stored assessmentData
        instructions // conversationHistory - this is the key addition!
      );
      
      if (!newToken) {
        console.error('❌ Failed to get new ephemeral key with conversation history');
        return false;
      }
      
      this.ephemeralKey = newToken;
      console.log('✅ Updated ephemeral key with conversation context');
    }
    
    // Check if data channel is ready
    if (!this.dataChannel) {
      console.error('❌ Data channel not initialized');
      return false;
    }
    
    // ✅ UNIVERSAL: Wait for data channel to be ready
    if (this.dataChannel.readyState !== 'open') {
      console.log('⏳ Data channel not open, waiting before starting conversation...');
      
      // Wait for the data channel to open
      try {
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Timed out waiting for data channel to open'));
          }, 8000); // Longer timeout for mobile browsers
          
          const checkDataChannel = () => {
            if (!this.dataChannel) {
              clearTimeout(timeout);
              reject(new Error('Data channel was cleared'));
              return;
            }
            
            if (this.dataChannel.readyState === 'open') {
              clearTimeout(timeout);
              resolve();
            } else if (this.dataChannel.readyState === 'closed' || this.dataChannel.readyState === 'closing') {
              clearTimeout(timeout);
              reject(new Error('Data channel closed before it could open'));
            } else {
              setTimeout(checkDataChannel, 100);
            }
          };
          
          checkDataChannel();
        });
      } catch (error) {
        console.error('❌ Error waiting for data channel to open:', error);
        return false;
      }
    }
    
    // ✅ UNIVERSAL: Longer delay for mobile browsers to ensure everything is ready
    console.log('⏳ Ensuring data channel is fully ready...');
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // ✅ CRITICAL CHANGE: NO session.update calls
    // The ephemeral token contains all instructions
    console.log('✅ Skipping session.update - using ephemeral token instructions only');
    
    // ✅ Send response.create event to start the conversation immediately
    const event: RealtimeResponseCreateEvent = {
      type: 'response.create',
      response: {
        modalities: ['text', 'audio'],
        // ✅ IMPORTANT: Do NOT override instructions here
        // Let the ephemeral token instructions take effect
      },
    };
    
    console.log('✅ Starting conversation with response.create (no instruction override)');
    return this.sendMessage(event);
  }
  
  /**
   * Pause the conversation without disconnecting
   * Keeps the WebRTC connection alive but stops processing audio
   */
  public pauseConversation(): boolean {
    try {
      console.log('⏸️ Pausing conversation (keeping connection alive)...');
      
      if (!this.isConnected || !this.dataChannel) {
        console.warn('⚠️ Cannot pause - not connected or no data channel');
        return false;
      }
      
      this.isPaused = true;
      this.pauseStartTime = Date.now();
      
      // Mute the local audio track instead of stopping it
      if (this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        audioTracks.forEach(track => {
          track.enabled = false; // Mute instead of stop
          console.log('🔇 Muted audio track:', track.label);
        });
      }
      
      // Mute the remote audio as well
      if (this.audioElement) {
        this.audioElement.muted = true;
        console.log('🔇 Muted remote audio');
      }
      
      console.log('✅ Conversation paused successfully');
      return true;
    } catch (error) {
      console.error('❌ Error pausing conversation:', error);
      return false;
    }
  }
  
  /**
   * Resume the conversation from pause
   * Unmutes audio and continues with the same session
   */
  public resumeConversation(): boolean {
    try {
      console.log('▶️ Resuming conversation...');
      
      if (!this.isPaused) {
        console.warn('⚠️ Conversation is not paused');
        return false;
      }
      
      if (!this.isConnected || !this.dataChannel) {
        console.warn('⚠️ Cannot resume - not connected or no data channel');
        return false;
      }
      
      // Calculate pause duration
      const pauseDuration = this.pauseStartTime ? Date.now() - this.pauseStartTime : 0;
      console.log(`⏱️ Resuming after ${pauseDuration}ms pause`);
      
      // Unmute the local audio track
      if (this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        audioTracks.forEach(track => {
          track.enabled = true; // Unmute
          console.log('🔊 Unmuted audio track:', track.label);
        });
      }
      
      // Unmute the remote audio
      if (this.audioElement) {
        this.audioElement.muted = false;
        console.log('🔊 Unmuted remote audio');
      }
      
      this.isPaused = false;
      this.pauseStartTime = null;
      
      console.log('✅ Conversation resumed successfully');
      return true;
    } catch (error) {
      console.error('❌ Error resuming conversation:', error);
      return false;
    }
  }
  
  /**
   * Check if the conversation is currently paused
   */
  public isPausedState(): boolean {
    return this.isPaused;
  }
  
  /**
   * Get pause duration in milliseconds
   */
  public getPauseDuration(): number {
    if (!this.isPaused || !this.pauseStartTime) return 0;
    return Date.now() - this.pauseStartTime;
  }
  
  /**
   * ✅ CRITICAL: Universal fallback muting handler with PREEMPTIVE muting
   * Addresses feedback loops on ALL browsers and devices by muting BEFORE AI speech starts
   * Works on: Desktop (Chrome, Firefox, Safari, Edge), Mobile (iOS Safari, Android Chrome), etc.
   */
  private handleFallbackMuting(eventData: RealtimeEvent): void {
    if (!this.fallback_protection_enabled) {
      return;
    }

    console.log(`🚨 [FALLBACK_MUTE] Handling event: ${eventData.type} (SemanticMuteController unavailable)`);
    this.last_ai_speech_event = eventData.type;

    switch (eventData.type) {
      // ✅ CRITICAL: Preemptive muting on response creation
      case 'response.created':
        console.log('🚨 [FALLBACK_MUTE] Response created - PREEMPTIVE MUTE to prevent feedback');
        this.setAISpeaking(true);
        this.muteViaTrackEnabled(true);
        break;

      case 'response.audio.start':
        console.log('🚨 [FALLBACK_MUTE] AI started speaking - ensuring already muted');
        this.setAISpeaking(true);
        this.muteViaTrackEnabled(true);
        break;

      case 'response.audio.done':
      case 'response.done':
        console.log('🚨 [FALLBACK_MUTE] AI finished speaking - delayed unmute');
        this.setAISpeaking(false);
        this.scheduleDelayedUnmute('AI speech completed');
        break;

      case 'response.audio.delta':
        // Ensure we stay muted during AI speech chunks
        if (!this.ai_is_speaking) {
          console.log('🚨 [FALLBACK_MUTE] AI audio delta - ensuring muted');
          this.setAISpeaking(true);
          this.muteViaTrackEnabled(true);
        }
        break;

      // ✅ CRITICAL: Enhanced user speech detection
      case 'input_audio_buffer.speech_started':
        console.log('🚨 [FALLBACK_MUTE] User started speaking - IMMEDIATE unmute');
        this.clearDelayedUnmute();
        this.setAISpeaking(false);
        this.muteViaTrackEnabled(false);
        break;

      case 'input_audio_buffer.speech_stopped':
        // Don't immediately mute when user stops speaking
        // Let natural conversation flow handle this
        console.log('🚨 [FALLBACK_MUTE] User stopped speaking - maintaining current state');
        break;

      // ✅ CRITICAL: Additional events that indicate AI is about to speak
      case 'response.output_item.added':
        if (eventData.item && eventData.item.type === 'message' && 
            eventData.item.role === 'assistant') {
          console.log('🚨 [FALLBACK_MUTE] Assistant message added - preemptive mute');
          this.setAISpeaking(true);
          this.muteViaTrackEnabled(true);
        }
        break;

      case 'response.content_part.added':
        if (eventData.part && eventData.part.type === 'audio') {
          console.log('🚨 [FALLBACK_MUTE] Audio content part added - preemptive mute');
          this.setAISpeaking(true);
          this.muteViaTrackEnabled(true);
        }
        break;

      default:
        // Log other audio events for debugging
        if (eventData.type.includes('audio') || eventData.type.includes('speech')) {
          console.log(`🚨 [FALLBACK_MUTE] Unhandled audio event: ${eventData.type}`);
        }
        break;
    }
  }

  /**
   * ✅ CRITICAL: Direct microphone muting via MediaStreamTrack.enabled
   * Essential fallback when SemanticMuteController fails
   */
  private muteViaTrackEnabled(mute: boolean): void {
    try {
      if (!this.localStream) {
        console.warn('🚨 [FALLBACK_MUTE] No local stream available for muting');
        return;
      }

      const audioTracks = this.localStream.getAudioTracks();
      if (audioTracks.length === 0) {
        console.warn('🚨 [FALLBACK_MUTE] No audio tracks found for muting');
        return;
      }

      const action = mute ? 'Muting' : 'Unmuting';
      console.log(`🚨 [FALLBACK_MUTE] ${action} ${audioTracks.length} audio track(s) via track.enabled`);

      audioTracks.forEach((track, index) => {
        if (track.readyState === 'live') {
          track.enabled = !mute;
          console.log(`🚨 [FALLBACK_MUTE] Track ${index} (${track.label}) enabled: ${!mute}`);
        } else {
          console.warn(`🚨 [FALLBACK_MUTE] Track ${index} not live (state: ${track.readyState})`);
        }
      });

      // Emit custom events for UI feedback
      if (typeof window !== 'undefined') {
        const eventType = mute ? 'fallback-mute-engaged' : 'fallback-mute-released';
        const event = new CustomEvent(eventType, {
          detail: {
            reason: this.last_ai_speech_event,
            ai_is_speaking: this.ai_is_speaking,
            timestamp: Date.now(),
            fallback_mode: true
          }
        });
        window.dispatchEvent(event);
      }

    } catch (error) {
      console.error('🚨 [FALLBACK_MUTE] Error in muteViaTrackEnabled:', error);
    }
  }

  /**
   * ✅ CRITICAL: Set AI speaking state with logging
   */
  private setAISpeaking(speaking: boolean): void {
    const previousState = this.ai_is_speaking;
    this.ai_is_speaking = speaking;
    
    if (previousState !== speaking) {
      console.log(`🚨 [FALLBACK_MUTE] AI speaking state changed: ${previousState} → ${speaking}`);
    }
  }

  /**
   * ✅ CRITICAL: Schedule delayed unmuting with semantic processing buffer
   */
  private scheduleDelayedUnmute(reason: string): void {
    // Clear any existing delayed unmute
    this.clearDelayedUnmute();

    // Use semantic processing delay (300ms) + AI speech tail protection (500ms)
    const SEMANTIC_PROCESSING_DELAY = 300;
    const AI_SPEECH_TAIL_PROTECTION = 500;
    const totalDelay = SEMANTIC_PROCESSING_DELAY + AI_SPEECH_TAIL_PROTECTION;

    console.log(`🚨 [FALLBACK_MUTE] Scheduling delayed unmute in ${totalDelay}ms: ${reason}`);

    this.fallback_mute_timeout = setTimeout(() => {
      console.log(`🚨 [FALLBACK_MUTE] Executing delayed unmute: ${reason}`);
      
      // Double-check AI speaking state before unmuting
      if (!this.ai_is_speaking) {
        this.muteViaTrackEnabled(false);
      } else {
        console.log(`🚨 [FALLBACK_MUTE] Skipping unmute - AI still speaking`);
      }
      
      this.fallback_mute_timeout = null;
    }, totalDelay);
  }

  /**
   * ✅ CRITICAL: Clear any pending delayed unmute operations
   */
  private clearDelayedUnmute(): void {
    if (this.fallback_mute_timeout) {
      clearTimeout(this.fallback_mute_timeout);
      this.fallback_mute_timeout = null;
      console.log('🚨 [FALLBACK_MUTE] Cleared pending delayed unmute');
    }
  }

  /**
   * ✅ CRITICAL: Emergency mute override for critical situations
   */
  public emergencyMute(reason: string): void {
    console.log(`🚨 [EMERGENCY_MUTE] Emergency mute activated: ${reason}`);
    
    this.clearDelayedUnmute();
    this.setAISpeaking(true);
    
    // Try SemanticMuteController first
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.forceMute(true, reason);
        console.log('🚨 [EMERGENCY_MUTE] Used SemanticMuteController for emergency mute');
      } catch (error) {
        console.error('🚨 [EMERGENCY_MUTE] SemanticMuteController failed, using fallback:', error);
        this.muteViaTrackEnabled(true);
      }
    } else {
      // Use fallback muting
      this.muteViaTrackEnabled(true);
    }
  }

  /**
   * ✅ CRITICAL: Emergency unmute override for critical situations
   */
  public emergencyUnmute(reason: string): void {
    console.log(`🚨 [EMERGENCY_UNMUTE] Emergency unmute activated: ${reason}`);
    
    this.clearDelayedUnmute();
    this.setAISpeaking(false);
    
    // Try SemanticMuteController first
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.forceMute(false, reason);
        console.log('🚨 [EMERGENCY_UNMUTE] Used SemanticMuteController for emergency unmute');
      } catch (error) {
        console.error('🚨 [EMERGENCY_UNMUTE] SemanticMuteController failed, using fallback:', error);
        this.muteViaTrackEnabled(false);
      }
    } else {
      // Use fallback unmuting
      this.muteViaTrackEnabled(false);
    }
  }

  /**
   * ✅ CRITICAL: Get current AI speaking state for debugging
   */
  public getAISpeakingState(): boolean {
    return this.ai_is_speaking;
  }

  /**
   * ✅ CRITICAL: Get comprehensive muting diagnostics
   */
  public getMutingDiagnostics(): any {
    return {
      ai_is_speaking: this.ai_is_speaking,
      fallback_protection_enabled: this.fallback_protection_enabled,
      last_ai_speech_event: this.last_ai_speech_event,
      fallback_mute_timeout_active: this.fallback_mute_timeout !== null,
      semantic_controller_available: this.semanticMuteController !== null,
      local_stream_available: this.localStream !== null,
      audio_tracks_count: this.localStream ? this.localStream.getAudioTracks().length : 0,
      audio_tracks_enabled: this.localStream ? 
        this.localStream.getAudioTracks().map(track => ({
          label: track.label,
          enabled: track.enabled,
          readyState: track.readyState
        })) : [],
      semantic_controller_diagnostics: this.semanticMuteController ? 
        this.semanticMuteController.getDiagnostics() : null
    };
  }

  /**
   * Disconnect and clean up all resources
   */
  public disconnect(): void {
    console.log('🧹 Disconnecting...');
    try {
      // Clear any pending timeouts
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
        this.connectionAttemptTimeout = null;
      }
      
      // Stop all media tracks first
      if (this.localStream) {
        console.log('🛑 Stopping local stream tracks...');
        const tracks = this.localStream.getTracks();
        tracks.forEach(track => {
          try {
            track.stop();
            console.log('🛑 Stopped track:', track.kind, track.label);
          } catch (e) {
            console.error('❌ Error stopping track:', e);
          }
        });
        this.localStream = null;
      }
      
      // Close data channel
      if (this.dataChannel) {
        console.log('🔌 Closing data channel...');
        try {
          this.dataChannel.close();
        } catch (e) {
          console.error('❌ Error closing data channel:', e);
        }
        this.dataChannel = null;
      }
      
      // Close peer connection
      if (this.peerConnection) {
        console.log('🔌 Closing peer connection...');
        try {
          this.peerConnection.close();
        } catch (e) {
          console.error('❌ Error closing peer connection:', e);
        }
        this.peerConnection = null;
      }
      
      // Clear audio element
      if (this.audioElement) {
        this.audioElement.srcObject = null;
      }
      
      // ✅ SEMANTIC VAD: Dispose of SemanticMuteController
      if (this.semanticMuteController) {
        this.semanticMuteController.dispose();
        this.semanticMuteController = null;
        console.log('✅ [SEMANTIC_VAD] SemanticMuteController disposed');
      }
      
      // ✅ CRITICAL: Clean up fallback system
      this.clearDelayedUnmute();
      this.ai_is_speaking = false;
      this.fallback_protection_enabled = true;
      this.last_ai_speech_event = '';
      console.log('✅ [FALLBACK_MUTE] Fallback system reset');
    } catch (e) {
      console.error('❌ Error during disconnect:', e);
    } finally {
      this.isConnected = false;
      console.log('✅ Disconnected');
      if (this.onDisconnectedCallback) this.onDisconnectedCallback();
    }
  }
  
  /**
   * Convert language name to ISO-639-1 code
   */
  private getLanguageIsoCode(language: string): string {
    // Map common language names to ISO-639-1 codes
    const languageMap: {[key: string]: string} = {
      'english': 'en',
      'dutch': 'nl',
      'nederlands': 'nl',
      'french': 'fr',
      'français': 'fr',
      'german': 'de',
      'deutsch': 'de',
      'spanish': 'es',
      'español': 'es',
      'italian': 'it',
      'italiano': 'it',
      'portuguese': 'pt',
      'português': 'pt',
      'russian': 'ru',
      'chinese': 'zh',
      'japanese': 'ja',
      'korean': 'ko',
      'arabic': 'ar',
      'hindi': 'hi',
      'bengali': 'bn',
      'turkish': 'tr',
      'swedish': 'sv',
      'norwegian': 'no',
      'danish': 'da',
      'finnish': 'fi',
      'polish': 'pl',
      'romanian': 'ro',
      'greek': 'el',
      'hungarian': 'hu',
      'czech': 'cs',
      'thai': 'th',
      'vietnamese': 'vi',
      'indonesian': 'id',
      'malay': 'ms',
      'hebrew': 'he',
      'ukrainian': 'uk'
    };
    
    // Return the ISO code if found, otherwise return the original language name
    // This allows for direct ISO code input as well
    return languageMap[language.toLowerCase()] || language.toLowerCase();
  }
  
  /**
   * Get an ephemeral key from the backend
   */
  public async getEphemeralKey(language?: string, level?: string, topic?: string, userPrompt?: string, assessmentData?: any, conversationHistory?: string): Promise<string> {
    // Flag to track if we're using the mock token endpoint
    let usedMockToken = false;
    
    try {
      console.log('================================================================================');
      console.log('🌐 [UNIVERSAL] Getting ephemeral key from backend...');
      console.log('🌐 [UNIVERSAL] Timestamp:', new Date().toISOString());
      console.log('🌐 [UNIVERSAL] Language:', language);
      console.log('🌐 [UNIVERSAL] Level:', level);
      console.log('🌐 [UNIVERSAL] Topic:', topic);
      console.log('🌐 [UNIVERSAL] User prompt length:', userPrompt ? userPrompt.length : 0);
      console.log('🌐 [UNIVERSAL] User prompt preview:', userPrompt ? userPrompt.substring(0, 100) + '...' : 'None');
      console.log('🌐 [UNIVERSAL] Assessment data provided:', !!assessmentData);
      console.log('================================================================================');
      
      // Ensure we have both language and level
      if (!language || !level) {
        console.error('❌ Missing language or level parameters');
        throw new Error('Language and level are required parameters');
      }
      
      // First try the real endpoint
      let endpoint = `${this.backendUrl}/api/realtime/token`;
      console.log('📤 Fetching ephemeral key from:', endpoint);
      
      // Get research data from session storage if it's a custom topic
      let researchData = null;
      if (topic === 'custom') {
        const storedResearchData = sessionStorage.getItem('customTopicResearch');
        if (storedResearchData) {
          try {
            const parsedResearch = JSON.parse(storedResearchData);
            console.log('🔍 [REALTIME_SERVICE] Parsed research data structure:', parsedResearch);
            
            // Check for research data in multiple possible fields
            if (parsedResearch.research) {
              researchData = parsedResearch.research;
              console.log('✅ [REALTIME_SERVICE] Retrieved research data from "research" field:', researchData.length, 'characters');
            } else if (parsedResearch.research_content) {
              researchData = parsedResearch.research_content;
              console.log('✅ [REALTIME_SERVICE] Retrieved research data from "research_content" field:', researchData.length, 'characters');
            } else {
              console.log('⚠️ [REALTIME_SERVICE] No research data found in expected fields. Available fields:', Object.keys(parsedResearch));
            }
          } catch (error) {
            console.error('❌ [REALTIME_SERVICE] Error parsing research data:', error);
          }
        } else {
          console.log('⚠️ [REALTIME_SERVICE] No research data found in session storage for custom topic');
        }
      }
      
      // 🎤 Get user's preferred voice from backend
      let selectedVoice = 'alloy'; // Default fallback voice
      try {
        const token = localStorage.getItem('token');
        
        // Only attempt to fetch voice preference if user is authenticated
        if (token) {
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          };
          
          const voiceResponse = await fetch(`${this.backendUrl}/api/auth/get-voice`, {
            method: 'GET',
            credentials: 'include',
            headers
          });
          
          if (voiceResponse.ok) {
            const voiceData = await voiceResponse.json();
            if (voiceData.voice) {
              selectedVoice = voiceData.voice;
              console.log('🎤 [REALTIME_SERVICE] Using user preferred voice:', selectedVoice);
            } else {
              console.log('🎤 [REALTIME_SERVICE] No voice preference found, using default:', selectedVoice);
            }
          } else {
            console.log('🎤 [REALTIME_SERVICE] Failed to get voice preference (status:', voiceResponse.status, '), using default:', selectedVoice);
          }
        } else {
          console.log('🎤 [REALTIME_SERVICE] No auth token found, using default voice:', selectedVoice);
        }
      } catch (voiceError) {
        console.log('🎤 [REALTIME_SERVICE] Error fetching voice preference, using default:', selectedVoice);
      }

      // Prepare request body with language and level
      const requestBody = {
        language: language,
        level: level,
        voice: selectedVoice, // Use user's preferred voice or default
        topic: topic || null, // Add topic if provided
        user_prompt: userPrompt || null, // Add user prompt for custom topics
        assessment_data: assessmentData || null, // Add assessment data if provided
        research_data: researchData || null, // Add research data if available
        conversation_history: conversationHistory || null // Add conversation history for reconnections
      };
      
      // Log if assessment data is provided
      if (assessmentData) {
        console.log('📊 Including assessment data in token request');
      }
      
      // Log if we're using a custom topic with user prompt
      if (topic === 'custom' && userPrompt) {
        console.log('🎯 Using custom topic with user prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
      }
      
      console.log('📋 Request body:', JSON.stringify(requestBody));
      
      // Variable to store error from real endpoint if it fails
      let realEndpointError: any = null;
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
          // Add credentials to ensure cookies are sent
          credentials: 'omit',
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('📥 Received response from backend:', data);
          
          if (data.ephemeral_key) {
            console.log('✅ Successfully obtained real ephemeral key');
            return data.ephemeral_key;
          } else if (data.client_secret && data.client_secret.value) {
            console.log('✅ Successfully obtained client secret value');
            return data.client_secret.value;
          } else {
            console.error('❌ Response did not contain expected token format:', data);
            throw new Error('Invalid response format from token endpoint');
          }
        } else {
          // Try to parse the error as JSON first
          let errorData: any = null;
          try {
            errorData = await response.json();
            console.error('❌ Error response from token endpoint:', response.status, errorData);
          } catch (jsonError) {
            // If it's not JSON, get it as text
            const errorText = await response.text();
            console.error('❌ Error from real endpoint (status ' + response.status + '):', errorText);
            errorData = errorText;
          }
          
          realEndpointError = {
            status: response.status,
            data: errorData
          };
          
          throw new Error(`Token endpoint returned ${response.status}`);
        }
      } catch (error) {
        console.error('❌ Error with real endpoint:', error);
        realEndpointError = error;
        console.log('🔄 Real endpoint failed, trying mock endpoint as fallback...');
      }
      
      // Try the mock endpoint as a fallback
      usedMockToken = true;
      endpoint = `${this.backendUrl}/api/mock-token`;
      console.log('📤 Fetching mock ephemeral key from:', endpoint);
      console.log('📋 Mock request body:', JSON.stringify(requestBody));
      
      try {
        const mockResponse = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
          credentials: 'omit',
        });
        
        if (!mockResponse.ok) {
          let errorInfo = '';
          try {
            const errorData = await mockResponse.json();
            errorInfo = JSON.stringify(errorData);
          } catch (e) {
            errorInfo = await mockResponse.text();
          }
          
          console.error(`❌ Failed to get mock ephemeral key (status ${mockResponse.status}):`, errorInfo);
          
          // If both real and mock endpoints failed, provide comprehensive error
          if (realEndpointError) {
            throw new Error(`Real endpoint failed: ${realEndpointError.message || JSON.stringify(realEndpointError)}. Mock endpoint also failed (${mockResponse.status}): ${errorInfo}`);
          }
          
          throw new Error(`Failed to get mock token: ${errorInfo}`);
        }
        
        const mockData = await mockResponse.json();
        console.log('📥 Received mock response from backend');
        
        if (mockData.ephemeral_key) {
          console.log('✅ Using mock ephemeral key for testing');
          return mockData.ephemeral_key;
        } else {
          console.error('❌ Invalid mock response format:', mockData);
          throw new Error('Invalid mock response format');
        }
      } catch (mockError) {
        console.error('❌ Error with mock endpoint:', mockError);
        
        // If both endpoints failed, provide a comprehensive error message
        if (realEndpointError) {
          throw new Error(`Real endpoint error: ${realEndpointError.message || JSON.stringify(realEndpointError)}. Mock endpoint error: ${mockError instanceof Error ? mockError.message : String(mockError)}`);
        }
        
        throw mockError;
      }
    } catch (error) {
      console.error('❌ Error getting ephemeral key:', error);
      
      // Log detailed debugging information
      console.error('🔍 Detailed error context:', {
        error,
        language,
        level,
        topic,
        backendUrl: this.backendUrl,
        usedMockToken: usedMockToken || false
      });
      
      // Return empty string to indicate failure
      return '';
    }
  }
}

export default new RealtimeService();
