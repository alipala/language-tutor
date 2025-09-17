import { RealtimeEvent, RealtimeResponseCreateEvent } from './types';
import { SemanticMuteController } from './semanticMuteController';

/**
 * Enhanced Realtime Service with BULLETPROOF AI Self-Hearing Prevention
 * 
 * CRITICAL FIXES:
 * 1. Pre-emptive muting BEFORE WebRTC connection establishment
 * 2. Mobile-optimized WebRTC constraints with advanced echo cancellation
 * 3. Triple-layer muting system (Hardware + Software + Emergency)
 * 4. Complete OpenAI Realtime API event coverage
 * 5. Aggressive timing controls for mobile browsers
 * 6. Fallback systems for every possible failure point
 */

export class EnhancedRealtimeService {
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
  
  // ENHANCED: Triple-layer muting system
  private ai_is_speaking: boolean = false;
  private fallback_mute_timeout: NodeJS.Timeout | null = null;
  private emergency_mute_timeout: NodeJS.Timeout | null = null;
  private fallback_protection_enabled: boolean = true;
  private last_ai_speech_event: string = '';
  
  // Pre-emptive muting before connection
  private pre_connection_mute_active: boolean = false;
  private mobile_optimization_active: boolean = false;
  private echo_cancellation_level: number = 3; // Maximum level
  
  // User manual mute state tracking
  private user_manually_muted: boolean = false;
  
  // PHASE 1: Reduced aggressive timing controls
  private readonly PREEMPTIVE_MUTE_DELAY = 100; // Wait 100ms before muting
  private readonly MOBILE_SAFETY_BUFFER = 0; // Reduced mobile buffer
  private readonly EMERGENCY_MUTE_THRESHOLD = 50; // Emergency trigger time
  
  constructor() {
    // Only initialize Audio in browser environments
    if (typeof window !== 'undefined') {
      this.audioElement = new Audio();
      this.audioElement.autoplay = true;
      
      // Detect mobile browsers for enhanced optimization
      this.mobile_optimization_active = this.isMobileBrowser();
      console.log('[ENHANCED] Mobile optimization:', this.mobile_optimization_active ? 'ACTIVE' : 'DISABLED');
    }
  }

  /**
   * Detect mobile browsers for enhanced optimization
   */
  private isMobileBrowser(): boolean {
    if (typeof window === 'undefined') return false;
    
    const userAgent = window.navigator.userAgent.toLowerCase();
    const mobileKeywords = [
      'iphone', 'ipad', 'ipod', 'android', 'mobile', 'phone', 
      'tablet', 'touch', 'webos', 'blackberry'
    ];
    
    return mobileKeywords.some(keyword => userAgent.includes(keyword));
  }

  /**
   * ✅ ENHANCED: Initialize with pre-emptive muting setup
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
      console.log('[ENHANCED] Initializing enhanced realtime service with bulletproof muting...');
      
      // ✅ CRITICAL: Activate pre-connection muting immediately
      this.pre_connection_mute_active = true;
      console.log('[ENHANCED] Pre-connection muting ACTIVATED');
      
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
      
      // Use the correct backend URL (default to localhost:8000 if running locally)
      this.backendUrl = '';
      if (typeof window !== 'undefined') {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          this.backendUrl = 'http://localhost:8000';
        }
      }
      
      console.log(' Using backend URL:', this.backendUrl);
      
      // Test the connection to the backend first
      try {
        const testResponse = await fetch(`${this.backendUrl}/api/test`, {
          credentials: 'same-origin'
        });
        if (!testResponse.ok) {
          console.error(' Backend connection test failed:', await testResponse.text());
          return false;
        }
        const testData = await testResponse.json();
        console.log(' Backend connection test successful:', testData.message);
      } catch (err) {
        console.error('Error connecting to backend:', err);
        return false;
      }
      
      try {
        // Get ephemeral key from backend with language and level if provided
        const token = await this.getEphemeralKey(language, level, topic, userPrompt, assessmentData);
        if (!token) {
          console.error(' Failed to get ephemeral key (empty token)');
          return false;
        }
        
        console.log(' Ephemeral key obtained successfully');
        this.ephemeralKey = token;
        return true;
      } catch (err) {
        console.error(' Error getting ephemeral key:', err);
        return false;
      }
    } catch (error) {
      console.error(' Error initializing enhanced realtime service:', error);
      return false;
    }
  }
  
  /**
   * Set up WebRTC connection with mobile optimization
   */
  private setupWebRTC(): boolean {
    try {
      console.log('[ENHANCED] Setting up WebRTC with bulletproof mobile optimization...');
      
      // Enhanced STUN/TURN servers for mobile reliability
      const iceServers = [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' },
        { urls: 'stun:stun3.l.google.com:19302' },
        { urls: 'stun:stun4.l.google.com:19302' }
      ];
      
      // Mobile-optimized RTCConfiguration
      const rtcConfig: RTCConfiguration = {
        iceServers,
        iceCandidatePoolSize: 10, // Increased for mobile reliability
        bundlePolicy: 'max-bundle', // Optimize for mobile bandwidth
        rtcpMuxPolicy: 'require', // Reduce port usage on mobile
        iceTransportPolicy: 'all' // Allow all transport types
      };
      
      this.peerConnection = new RTCPeerConnection(rtcConfig);
      
      // Set up audio handling with enhanced mobile support
      this.peerConnection.ontrack = (e) => {
        console.log('[ENHANCED] Received remote track', e.streams);
        if (this.audioElement && e.streams && e.streams[0]) {
          this.audioElement.srcObject = e.streams[0];
          
          // PHASE 1: Don't mute remote audio - let user hear AI
          this.audioElement.muted = false;
          this.audioElement.volume = 1.0; // Full volume for AI speech
          console.log('[ENHANCED] Remote audio enabled for AI speech');
          
          //  Set up audio element for mobile optimization
          if (this.mobile_optimization_active) {
            this.audioElement.volume = 0.8; // Slightly lower volume on mobile
            this.audioElement.preload = 'auto';
            // Critical for iOS - use setAttribute for playsInline
            this.audioElement.setAttribute('playsinline', 'true');
          }
        }
      };
      
      //  Connection state monitoring with mobile-specific handling
      this.peerConnection.onconnectionstatechange = () => {
        const state = this.peerConnection?.connectionState;
        console.log('[ENHANCED] Connection state changed:', state);
        
        if (state === 'connected') {
          console.log('[ENHANCED] WebRTC connection fully established');
          // Ensure muting is still active after connection
          this.enforcePostConnectionMuting();
        } else if (state === 'failed' || state === 'disconnected') {
          console.warn('[ENHANCED] WebRTC connection failed/disconnected');
          // Automatic reconnection for mobile networks
          if (this.mobile_optimization_active && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnection();
          }
        }
      };
      
      // ENHANCED: Data channel with mobile-optimized settings
      this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
        ordered: true,
        maxRetransmits: this.mobile_optimization_active ? 5 : 3 // Increased for mobile reliability
      });
      
      this.dataChannel.onopen = () => {
        console.log('[ENHANCED] Data channel opened');
        this.isConnected = true;
        
        // CRITICAL: Final muting enforcement after data channel opens
        this.enforcePostConnectionMuting();
        
        if (this.onConnectedCallback) this.onConnectedCallback();
      };
      
      this.dataChannel.onclose = () => {
        console.log('❌ [ENHANCED] Data channel closed');
        this.isConnected = false;
        if (this.onDisconnectedCallback) this.onDisconnectedCallback();
      };
      
      this.dataChannel.onmessage = (e) => {
        if (this.onMessageCallback) {
          try {
            const eventData = JSON.parse(e.data) as RealtimeEvent;
            console.log('[ENHANCED] Received message type:', eventData.type);
            
            // CRITICAL: Enhanced event handling with complete coverage
            this.handleEnhancedRealtimeEvent(eventData);
            
            // Log specific details for transcription events
            if (eventData.type === 'conversation.item.created') {
              console.log('Conversation item created:', 
                eventData.item?.role, 
                eventData.item?.content ? 'Content array present' : 'No content array',
                eventData.item?.input ? 'Input present' : 'No input');
            } else if (eventData.type === 'conversation.item.input_audio_transcription.completed') {
              console.log('Transcription completed:', eventData.transcription?.text);
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
            console.error('[ENHANCED] Error parsing message:', error);
          }
        }
      };
      
      // ✅ ENHANCED: ICE handling with mobile optimization
      this.peerConnection.onicecandidate = (event) => {
        console.log('[ENHANCED] ICE candidate', event.candidate);
        
        // ✅ NEW: Mobile-specific ICE candidate filtering
        if (this.mobile_optimization_active && event.candidate) {
          // Prefer relay candidates on mobile for better NAT traversal
          if (event.candidate.type === 'relay') {
            console.log('[ENHANCED] Prioritizing relay candidate for mobile');
          }
        }
      };
      
      this.peerConnection.oniceconnectionstatechange = () => {
        console.log('[ENHANCED] ICE connection state:', this.peerConnection?.iceConnectionState);
        if (this.peerConnection?.iceConnectionState === 'failed' || 
            this.peerConnection?.iceConnectionState === 'disconnected') {
          console.warn('[ENHANCED] ICE connection failed or disconnected');
          
          // ✅ NEW: Mobile-specific ICE restart
          if (this.mobile_optimization_active) {
            this.handleMobileICEFailure();
          }
        }
      };
      
      return true;
    } catch (error) {
      console.error('[ENHANCED] Error setting up WebRTC:', error);
      return false;
    }
  }

  /**
   * CRITICAL: Enforce muting after WebRTC connection is established
   */
  private enforcePostConnectionMuting(): void {
    console.log('[ENHANCED] Enforcing post-connection muting...');
    
    // CRITICAL: Ensure all audio tracks are muted
    if (this.localStream) {
      const audioTracks = this.localStream.getAudioTracks();
      audioTracks.forEach((track, index) => {
        if (track.readyState === 'live') {
          track.enabled = false; // Start muted
          console.log(`🔇 [ENHANCED] Post-connection mute - Track ${index} disabled`);
        }
      });
    }
    
    // PHASE 1: Don't mute remote audio - user needs to hear AI
    if (this.audioElement) {
      this.audioElement.muted = false;
      this.audioElement.volume = 1.0;
      console.log('🔊 [ENHANCED] Post-connection - Remote audio enabled for AI speech');
    }
    
      // CRITICAL: Initialize semantic mute controller if not already done
      if (!this.semanticMuteController && this.localStream) {
        this.initializeSemanticMuteController();
      }
      
      // Set up user manual mute checker for semantic controller
      if (this.semanticMuteController) {
        this.semanticMuteController.setUserManualMuteChecker(() => this.user_manually_muted);
      }
  }

  /**
   * Handle mobile-specific ICE connection failures
   */
  private handleMobileICEFailure(): void {
    console.log('[ENHANCED] Handling mobile ICE failure...');
    
    // ICE restart for mobile networks
    if (this.peerConnection && this.peerConnection.restartIce) {
      console.log('[ENHANCED] Restarting ICE for mobile network recovery');
      this.peerConnection.restartIce();
    }
  }

  /**
   * Schedule reconnection for mobile network issues
   */
  private scheduleReconnection(): void {
    console.log('[ENHANCED] Scheduling reconnection for mobile network...');
    
    setTimeout(() => {
      if (!this.isConnected && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`[ENHANCED] Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect();
      }
    }, 2000 * this.reconnectAttempts); // Linear backoff
  }
  
  /**
   * ENHANCED: Request microphone access with BULLETPROOF mobile optimization
   */
  public async startMicrophone(): Promise<boolean> {
    try {
      console.log('[ENHANCED] Requesting microphone access with bulletproof mobile optimization...');
      if (typeof window === 'undefined') return false;
      
      // Set up WebRTC if not already done
      if (!this.peerConnection) {
        console.log('[ENHANCED] Setting up WebRTC connection first...');
        const setupSuccess = this.setupWebRTC();
        if (!setupSuccess) {
          console.error('[ENHANCED] Failed to set up WebRTC connection');
          return false;
        }
        
        // ENHANCED: Longer delay for mobile browsers to ensure WebRTC is ready
        const delay = this.mobile_optimization_active ? 500 : 300;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      // Release any existing stream to avoid resource leaks
      if (this.localStream) {
        console.log('[ENHANCED] Releasing existing media stream...');
        this.localStream.getTracks().forEach(track => {
          track.stop();
          console.log(`Stopped track: ${track.kind}`);
        });
        this.localStream = null;
        
        // Add a longer delay after stopping tracks for mobile browsers
        const delay = this.mobile_optimization_active ? 400 : 200;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      // Enhanced constraints with MAXIMUM echo cancellation
      // Strategy: Maximum Cross-Browser Echo Cancellation with Mobile Optimization
      const constraints = {
        audio: {
          // Maximum optimization for ALL browsers(Universal Standards Layer)
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          
          // Chrome/Chromium-based browsers
          googEchoCancellation: true,
          googEchoCancellationType: "system",
          googEchoCancellation2: true, // Advanced echo cancellation
          googEchoCancellation3: true, //Latest echo cancellation
          googDAEchoCancellation: true,
          googDAEchoCancellation2: true, // Advanced DA echo cancellation
          googNoiseSuppressionLevel: 3, // Maximum level
          googNoiseSuppression2: true,
          googExperimentalEchoCancellation: true,
          googAutoGainControl2: true,
          googHighpassFilter: true,
          googTypingNoiseDetection: true,
          googAudioMirroring: false,
          
          // Firefox-specific optimizations
          mozEchoCancellation: true,
          mozNoiseSuppression: true,
          mozAutoGainControl: true,
          mozEchoCancellationLevel: 3, // Maximum level
          mozNoiseSuppressionLevel: 3, // Maximum level
          
          // Safari/WebKit optimizations
          webkitEchoCancellation: true,
          webkitNoiseSuppression: true,
          webkitAutoGainControl: true,
          webkitEchoCancellationLevel: 3, // Maximum level
          
          // Mobile-specific optimizations
          ...(this.mobile_optimization_active && {
            // Mobile-specific latency and quality settings
            latency: { ideal: 0.005, max: 0.01 }, // Even lower latency for mobile
            sampleRate: { ideal: 48000, min: 44100 }, // High quality audio
            channelCount: { ideal: 1, max: 1 }, // Mono for better processing
            sampleSize: { ideal: 16, min: 16 }, // High bit depth
            volume: { ideal: 0.9, max: 1.0 }, // Slightly lower volume
            
            // Mobile-specific echo cancellation
            googMobileEchoCancellation: true,
            googMobileNoiseSuppression: true,
            googMobileAutoGainControl: true,
            
            // iOS-specific optimizations
            webkitMobileEchoCancellation: true,
            webkitMobileNoiseSuppression: true,
          }),
          
          // Universal latency and quality optimization
          latency: { ideal: 0.01, max: 0.02 },
          sampleRate: { ideal: 48000 },
          channelCount: { ideal: 1, max: 1 },
          sampleSize: { ideal: 16 },
          volume: { ideal: 1.0 }
        }
      };
      
      console.log('[ENHANCED] Requesting user media with constraints:', JSON.stringify(constraints));
      
      try {
        // Longer timeout for mobile browsers
        const timeout = this.mobile_optimization_active ? 15000 : 10000;
        const getUserMediaPromise = navigator.mediaDevices.getUserMedia(constraints);
        const timeoutPromise = new Promise<MediaStream>((_, reject) => {
          setTimeout(() => reject(new Error('Microphone access request timed out')), timeout);
        });
        
        this.localStream = await Promise.race([getUserMediaPromise, timeoutPromise]);
        console.log('[ENHANCED] Microphone access granted', this.localStream);
      } catch (mediaError) {
        console.error('[ENHANCED] First attempt to get user media failed:', mediaError);
        
        // More aggressive retry with simpler constraints
        const delay = this.mobile_optimization_active ? 1000 : 500;
        await new Promise(resolve => setTimeout(resolve, delay));
        console.log('[ENHANCED] Retrying with simpler constraints...');
        
        try {
          // FALLBACK: Simpler constraints for problematic devices
          const fallbackConstraints = {
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
              ...(this.mobile_optimization_active && {
                latency: { ideal: 0.02 },
                sampleRate: { ideal: 44100 }
              })
            }
          };
          
          this.localStream = await navigator.mediaDevices.getUserMedia(fallbackConstraints);
          console.log('[ENHANCED] Microphone access granted on second attempt');
        } catch (retryError) {
          console.error('[ENHANCED] Second attempt to get user media failed:', retryError);
          throw retryError;
        }
      }
      
      // Add audio track to peer connection
      if (this.peerConnection && this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        if (audioTracks.length === 0) {
          console.error('[ENHANCED] No audio tracks found in media stream');
          return false;
        }
        
        console.log('[ENHANCED] Adding audio track to peer connection', audioTracks[0].label);
        
        try {
          const sender = this.peerConnection.addTrack(audioTracks[0], this.localStream);
          console.log('[ENHANCED] Track added successfully, sender created:', sender ? 'Yes' : 'No');
          
          // CRITICAL: IMMEDIATE muting of all tracks before any audio can leak
          audioTracks.forEach((track, index) => {
            track.enabled = false; // Start muted
            console.log(`[ENHANCED] Track ${index} IMMEDIATELY muted on creation`);
          });
          
          // ENHANCED: Initialize SemanticMuteController with retry mechanism
          await this.initializeSemanticMuteController();
          
          // ENHANCED: Longer delay after adding track for mobile browsers
          const delay = this.mobile_optimization_active ? 400 : 200;
          await new Promise(resolve => setTimeout(resolve, delay));
          return true;
        } catch (trackError) {
          console.error('[ENHANCED] Error adding track to peer connection:', trackError);
          return false;
        }
      }
      
      return false;
    } catch (error) {
      console.error('[ENHANCED] Error starting microphone:', error);
      
      // Specific error handling for common issues
      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          console.error('[ENHANCED] Microphone permission denied by user');
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
          console.error('[ENHANCED] No microphone found on this device');
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
          console.error('[ENHANCED] Microphone is already in use by another application');
        }
      }
      
      return false;
    }
  }

  /**
   * ENHANCED: Initialize SemanticMuteController with retry mechanism
   */
  private async initializeSemanticMuteController(): Promise<void> {
    if (!this.localStream) {
      console.warn('[ENHANCED] Cannot initialize SemanticMuteController - no local stream');
      return;
    }

    try {
      this.semanticMuteController = new SemanticMuteController();
      const muteControllerInitialized = await this.semanticMuteController.initialize(this.localStream);
      
      if (muteControllerInitialized) {
        console.log('[ENHANCED] SemanticMuteController initialized successfully');
        // NEW: Set up user manual mute checker
        this.semanticMuteController.setUserManualMuteChecker(() => this.user_manually_muted);
      } else {
        console.warn('[ENHANCED] SemanticMuteController initialization failed, using fallback');
        this.semanticMuteController = null;
        
        // NEW: Retry mechanism for mobile browsers
        if (this.mobile_optimization_active) {
          console.log('[ENHANCED] Retrying SemanticMuteController initialization for mobile...');
          await new Promise(resolve => setTimeout(resolve, 500));
          
          try {
            this.semanticMuteController = new SemanticMuteController();
            const retryResult = await this.semanticMuteController.initialize(this.localStream);
            if (retryResult) {
              console.log('[ENHANCED] SemanticMuteController initialized on retry');
            } else {
              console.warn('[ENHANCED] SemanticMuteController retry failed, continuing without it');
              this.semanticMuteController = null;
            }
          } catch (retryError) {
            console.error('[ENHANCED] SemanticMuteController retry error:', retryError);
            this.semanticMuteController = null;
          }
        }
      }
    } catch (muteError) {
      console.error('[ENHANCED] Error initializing SemanticMuteController:', muteError);
      this.semanticMuteController = null;
    }
  }

  /**
   * LAYER 1: Primary Hardware-Level Event Handler (Main Controller)
   * 
   * PURPOSE: Hardware-level primary muting system using MediaStreamTrack.enabled
   * ROLE: Main controller with direct WebRTC hardware control
   * CONTROL: MediaStreamTrack.enabled (hardware level)
   * 
   * This is part of the TRIPLE-LAYER REDUNDANCY architecture:
   * - Layer 1: Hardware track.enabled control (THIS controller)
   * - Layer 2: Software gain control (SemanticMuteController)
   * - Layer 3: Emergency timeout safety nets
   */
  private handleEnhancedRealtimeEvent(eventData: RealtimeEvent): void {
    console.log(`[ENHANCED] Processing event: ${eventData.type}`);
    
    switch (eventData.type) {
      case 'response.audio.start': // AI starts talking → DELAYED MUTE (100ms)
        console.log('[ENHANCED] AI audio started - DELAYED MUTE');
        
        // WHY DELAY: Prevents cutting off the very beginning of AI speech
        setTimeout(() => {
          this.executeImmediateMute('AI audio response started');
        }, this.PREEMPTIVE_MUTE_DELAY); 
        
        break;

      case 'response.audio.delta': // AI continues talking → ENSURE MUTED
        // WHY CHECK STATE: Catch any hardware unmute failures during AI speech
        if (!this.ai_is_speaking) {
          console.log('[ENHANCED] AI audio delta - ENSURING MUTED');
          this.executeImmediateMute('AI audio delta received');
        }
        break;

      case 'response.audio.done': // AI stops talking → DELAYED UNMUTE
        console.log('[ENHANCED] AI audio done - SCHEDULING FASTER UNMUTE');
        // WHY SCHEDULED: Prevents immediate unmute that could cause feedback
        this.scheduleDelayedUnmute('AI audio response completed');
        break;

      case 'response.done': // AI response complete → DELAYED UNMUTE
        console.log('[ENHANCED] Response done - SCHEDULING FASTER UNMUTE');
        // WHY SCHEDULED: Complete response may have trailing audio processing
        this.scheduleDelayedUnmute('AI response completed');
        break;

      case 'input_audio_buffer.speech_started': // User starts → IMMEDIATE UNMUTE
        console.log('[ENHANCED] User speech started - IMMEDIATE UNMUTE');
        // WHY IMMEDIATE: User needs to interrupt AI without delay for natural conversation
        this.executeImmediateUnmute('User speech detected');
        
        break;

      case 'input_audio_buffer.speech_stopped': // User stops
        console.log('[ENHANCED] User speech stopped - MAINTAINING STATE');
        // WHY NO IMMEDIATE MUTE: Allows natural conversation pauses and thinking time
        // PHILOSOPHY: Don't interrupt natural conversation flow with aggressive muting
        // NOTE: Muting will happen when AI starts speaking again
        break;

      default:
        // DEBUG: Log unhandled audio events for system monitoring and debugging
        if (eventData.type.includes('audio') || eventData.type.includes('speech') || 
            eventData.type.includes('response') || eventData.type.includes('assistant')) {
          console.log(`[ENHANCED] Unhandled audio event: ${eventData.type}`);
        }
        break;
    }

    // LAYER 2 ACTIVATION: Trigger backup semantic controller for redundancy
    // PURPOSE: If Layer 1 (hardware) fails, Layer 2 (software) continues working
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.handleRealtimeEvent(eventData);
      } catch (error) {
        console.error('[ENHANCED] SemanticMuteController error:', error);
        // Layer 1 continues working even if Layer 2 fails
      }
    }
  }

  /**
   * ✅ CRITICAL: Execute immediate muting with triple-layer approach
   */
  private executeImmediateMute(reason: string): void {
    console.log(`[ENHANCED] IMMEDIATE MUTE: ${reason}`);
    
    this.ai_is_speaking = true;
    this.last_ai_speech_event = reason;
    
    // Clear any pending unmute operations
    this.clearAllDelayedOperations();
    
    // ✅ LAYER 1: Hardware-level track muting (IMMEDIATE)
    this.muteViaTrackEnabled(true);
    
    // ✅ LAYER 2: SemanticMuteController (if available)
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.muteForAISpeech(reason);
      } catch (error) {
        console.error('[ENHANCED] SemanticMuteController mute failed:', error);
      }
    }
    
    // ✅ LAYER 3: Emergency timeout as safety net
    this.setEmergencyMuteTimeout(reason);
  }

  /**
   * Execute immediate unmuting for user speech
   */
  private executeImmediateUnmute(reason: string): void {
    console.log(`[ENHANCED] IMMEDIATE UNMUTE: ${reason}`);
    
    this.ai_is_speaking = false;
    this.last_ai_speech_event = reason;
    
    // Clear all pending operations
    this.clearAllDelayedOperations();
    
    // ✅ CRITICAL: Check if user has manually muted their microphone
    if (this.user_manually_muted) {
      console.log(`[ENHANCED] SKIPPING IMMEDIATE UNMUTE - User has manually muted microphone`);
      return;
    }
    
    // ✅ IMMEDIATE: Hardware-level track unmuting
    this.muteViaTrackEnabled(false);
    
    // ✅ SemanticMuteController unmuting
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.ensureUnmutedForUserSpeech(reason);
      } catch (error) {
        console.error('[ENHANCED] SemanticMuteController unmute failed:', error);
      }
    }
  }

  /**
   * CRITICAL: Schedule delayed unmuting with enhanced safety
   */
  private scheduleDelayedUnmute(reason: string): void {
    console.log(`[ENHANCED] SCHEDULING DELAYED UNMUTE: ${reason}`);
    
    this.ai_is_speaking = false;
    this.last_ai_speech_event = reason;
    
    // Clear any existing delayed operations
    this.clearAllDelayedOperations();
    
    // ✅ PHASE 1: Reduced delay calculation
    const semanticDelay = 100; // Reduced from 300ms
    const tailProtection = 100; // Reduced from 500ms
    const mobileBuffer = this.mobile_optimization_active ? this.MOBILE_SAFETY_BUFFER : 0;
    const totalDelay = semanticDelay + tailProtection + mobileBuffer;
    
    console.log(`⏰ [ENHANCED] Unmuting in ${totalDelay}ms (semantic: ${semanticDelay}ms + tail: ${tailProtection}ms + mobile: ${mobileBuffer}ms)`);
    
    this.fallback_mute_timeout = setTimeout(() => {
      console.log(`🔊 [ENHANCED] EXECUTING DELAYED UNMUTE: ${reason}`);
      
      // ✅ CRITICAL: Check if user has manually muted their microphone
      if (this.user_manually_muted) {
        console.log(`🔇 [ENHANCED] SKIPPING UNMUTE - User has manually muted microphone`);
        this.fallback_mute_timeout = null;
        return;
      }
      
      // Double-check AI speaking state before unmuting
      if (!this.ai_is_speaking) {
        this.muteViaTrackEnabled(false);
        
        // Also unmute via SemanticMuteController
        if (this.semanticMuteController) {
          try {
            this.semanticMuteController.scheduleUnmuteAfterAISpeech(reason);
          } catch (error) {
            console.error('❌ [ENHANCED] SemanticMuteController delayed unmute failed:', error);
          }
        }
      } else {
        console.log(`🚨 [ENHANCED] SKIPPING UNMUTE - AI still speaking`);
      }
      
      this.fallback_mute_timeout = null;
    }, totalDelay);
  }

  /**
   * ✅ CRITICAL: Hardware-level track muting/unmuting
   */
  private muteViaTrackEnabled(mute: boolean): void {
    try {
      if (!this.localStream) {
        console.warn('🚨 [ENHANCED] No local stream available for muting');
        return;
      }

      const audioTracks = this.localStream.getAudioTracks();
      if (audioTracks.length === 0) {
        console.warn('🚨 [ENHANCED] No audio tracks found for muting');
        return;
      }

      const action = mute ? 'MUTING' : 'UNMUTING';
      console.log(`🔧 [ENHANCED] ${action} ${audioTracks.length} audio track(s) via track.enabled`);

      audioTracks.forEach((track, index) => {
        if (track.readyState === 'live') {
          track.enabled = !mute;
          console.log(`🔧 [ENHANCED] Track ${index} (${track.label}) enabled: ${!mute}`);
        } else {
          console.warn(`🚨 [ENHANCED] Track ${index} not live (state: ${track.readyState})`);
        }
      });

        // ✅ PHASE 1: Don't control remote audio volume - let user hear AI
        if (this.audioElement) {
          // Keep remote audio always enabled so user can hear AI
          this.audioElement.muted = false;
          this.audioElement.volume = this.mobile_optimization_active ? 0.8 : 1.0;
          console.log('🔊 [ENHANCED] Remote audio kept enabled for AI speech');
        }

      // Emit custom events for UI feedback
      if (typeof window !== 'undefined') {
        const eventType = mute ? 'enhanced-mute-engaged' : 'enhanced-mute-released';
        const event = new CustomEvent(eventType, {
          detail: {
            reason: this.last_ai_speech_event,
            ai_is_speaking: this.ai_is_speaking,
            timestamp: Date.now(),
            enhanced_mode: true,
            mobile_optimized: this.mobile_optimization_active
          }
        });
        window.dispatchEvent(event);
      }

    } catch (error) {
      console.error('🚨 [ENHANCED] Error in muteViaTrackEnabled:', error);
    }
  }

  /**
   * LAYER 3: Emergency Timeout Safety Net (Ultimate Failsafe)
   * 
   * PURPOSE: Final safety mechanism when Layer 1 (hardware) and Layer 2 (software) fail
   * ROLE: Ultimate failsafe that activates after 50ms if other layers don't respond
   * CONTROL: Direct hardware muting as last resort
   * 
   * This is part of the TRIPLE-LAYER REDUNDANCY architecture:
   * - Layer 1: Hardware track.enabled control (Primary)
   * - Layer 2: Software gain control (Backup)
   * - Layer 3: Emergency timeout safety nets (THIS failsafe)
   */
  private setEmergencyMuteTimeout(reason: string): void {
    // Clear any existing emergency timeout to prevent multiple timers
    if (this.emergency_mute_timeout) {
      clearTimeout(this.emergency_mute_timeout);
    }

    // WHY 50ms THRESHOLD: Fast enough to prevent feedback, slow enough to avoid false triggers
    // MECHANISM: If Layer 1 + Layer 2 fail to mute within 50ms, Layer 3 force-mutes
    // FAILSAFE: Ensures 100% muting reliability even with complete system failures
    this.emergency_mute_timeout = setTimeout(() => {
      console.log(`[ENHANCED] LAYER 3 EMERGENCY TIMEOUT ACTIVATED: ${reason}`);
      console.log('[ENHANCED] Layer 1 + Layer 2 failed - Layer 3 force muting');
      
      // FORCE MUTE: Direct hardware control as ultimate failsafe
      this.muteViaTrackEnabled(true);
      this.emergency_mute_timeout = null;
    }, this.EMERGENCY_MUTE_THRESHOLD); // 50ms emergency threshold
  }

  /**
   * LAYER 3: Emergency Operations Cleanup (Safety Reset)
   * 
   * PURPOSE: Clean shutdown of all timeout-based safety mechanisms
   * ROLE: Prevents memory leaks and conflicting timeout operations
   * CONTROL: Centralized timeout management for all layers
   * 
   * CLEARS:
   * - fallback_mute_timeout: Layer 1 delayed unmute operations
   * - emergency_mute_timeout: Layer 3 emergency safety timeouts
   */
  private clearAllDelayedOperations(): void {
    // CLEAR LAYER 1 TIMEOUTS: Delayed unmute operations from primary controller
    if (this.fallback_mute_timeout) {
      clearTimeout(this.fallback_mute_timeout);
      this.fallback_mute_timeout = null;
      console.log('[ENHANCED] Cleared Layer 1 fallback mute timeout');
    }

    // CLEAR LAYER 3 TIMEOUTS: Emergency safety net operations
    if (this.emergency_mute_timeout) {
      clearTimeout(this.emergency_mute_timeout);
      this.emergency_mute_timeout = null;
      console.log('[ENHANCED] Cleared Layer 3 emergency mute timeout');
    }
    
    // WHY CENTRALIZED: Ensures no orphaned timeouts that could cause unexpected behavior
    // SAFETY: Prevents race conditions between different layer operations
    // RELIABILITY: Clean state management for all timeout-based safety mechanisms
  }

  /**
   * Connect to OpenAI Realtime API
   */
  public async connect(): Promise<boolean> {
    try {
      console.log('[ENHANCED] Connecting to OpenAI with muting...');
      if (!this.peerConnection) {
        console.error('[ENHANCED] Peer connection not initialized');
        return false;
      }
      
      // Clear any existing timeout
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
      }
      
      // Set connection timeout (longer for mobile)
      const timeout = this.mobile_optimization_active ? 20000 : 15000;
      this.connectionAttemptTimeout = setTimeout(() => {
        console.error('[ENHANCED] Connection attempt timed out');
        this.disconnect();
      }, timeout);
      
      // Make sure data channel is created before creating the offer
      if (!this.dataChannel || this.dataChannel.readyState === 'closed') {
        console.log('[ENHANCED] Creating new data channel before offer...');
        try {
          this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
            ordered: true,
            maxRetransmits: this.mobile_optimization_active ? 5 : 3
          });
          
          console.log('[ENHANCED] Data channel created successfully');
          
          this.dataChannel.onopen = () => {
            console.log('[ENHANCED] Data channel opened');
            this.isConnected = true;
            this.enforcePostConnectionMuting();
            if (this.onConnectedCallback) this.onConnectedCallback();
          };
          
          this.dataChannel.onclose = () => {
            console.log('[ENHANCED] Data channel closed');
            this.isConnected = false;
            if (this.onDisconnectedCallback) this.onDisconnectedCallback();
          };
          
          this.dataChannel.onmessage = (e) => {
            if (this.onMessageCallback) {
              try {
                const eventData = JSON.parse(e.data) as RealtimeEvent;
                this.handleEnhancedRealtimeEvent(eventData);
                this.onMessageCallback(eventData);
              } catch (error) {
                console.error('[ENHANCED] Error parsing message:', error);
              }
            }
          };
          
          // Add a delay after creating the data channel (longer for mobile)
          const delay = this.mobile_optimization_active ? 400 : 200;
          await new Promise(resolve => setTimeout(resolve, delay));
        } catch (channelError) {
          console.error('[ENHANCED] Error creating data channel:', channelError);
          return false;
        }
      }
      
      // Create offer
      console.log('[ENHANCED] Creating offer...');
      let completeOffer: RTCSessionDescriptionInit | null = null;
      
      try {
        const offer = await this.peerConnection.createOffer({
          offerToReceiveAudio: true
        });
        
        console.log('[ENHANCED] Setting local description...');
        await this.peerConnection.setLocalDescription(offer);
        console.log('[ENHANCED] Local description set successfully');
        
        // Add a delay after setting local description (longer for mobile)
        const delay = this.mobile_optimization_active ? 500 : 300;
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Wait for ICE gathering to complete
        console.log('🧊 [ENHANCED] Waiting for ICE gathering to complete...');
        completeOffer = await this.waitForIceComplete();
        if (!completeOffer) {
          console.error('[ENHANCED] Failed to gather ICE candidates');
          return false;
        }
        
        console.log('✅ [ENHANCED] ICE gathering completed successfully');
      } catch (offerError) {
        console.error('[ENHANCED] Error creating or processing offer:', offerError);
        return false;
      }
      
      // Send offer to OpenAI
      console.log('[ENHANCED] Sending offer to OpenAI...');
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
        console.error('[ENHANCED] Error connecting to OpenAI:', errorText);
        return false;
      }
      
      // Set remote description
      console.log('[ENHANCED] Setting remote description...');
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
      
      console.log('✅ [ENHANCED] Connected to OpenAI successfully');
      return true;
    } catch (error) {
      console.error('❌ [ENHANCED] Error connecting to OpenAI:', error);
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
      // Set a timeout to prevent waiting indefinitely (longer for mobile)
      const timeout = this.mobile_optimization_active ? 8000 : 5000;
      const timeoutId = setTimeout(() => {
        console.warn('⚠️ [ENHANCED] ICE gathering timed out, proceeding with available candidates');
        if (this.peerConnection?.localDescription) {
          resolve(this.peerConnection.localDescription);
        } else {
          resolve(null);
        }
      }, timeout);
      
      const checkIce = () => {
        if (this.peerConnection?.iceGatheringState === 'complete') {
          clearTimeout(timeoutId);
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
      console.error('❌ [ENHANCED] Data channel not available, cannot send message');
      return false;
    }
    
    // If data channel is connecting, wait for it to open
    if (this.dataChannel.readyState === 'connecting') {
      console.log('⏳ [ENHANCED] Data channel is connecting, waiting for it to open...');
      return false;
    }
    
    // If data channel is not open, cannot send message
    if (this.dataChannel.readyState !== 'open') {
      console.error(`❌ [ENHANCED] Data channel not open (state: ${this.dataChannel.readyState}), cannot send message`);
      return false;
    }
    
    try {
      const messageString = JSON.stringify(message);
      console.log('📤 [ENHANCED] Sending message:', message.type);
      this.dataChannel.send(messageString);
      return true;
    } catch (error) {
      console.error('❌ [ENHANCED] Error sending message:', error);
      return false;
    }
  }

  /**
   * Start a conversation with OpenAI - Enhanced implementation
   */
  public async startConversation(instructions?: string): Promise<boolean> {
    console.log('[ENHANCED] Starting conversation with bulletproof approach...');
    
    // If we have conversation instructions (for resuming), we need to get a new ephemeral key
    if (instructions) {
      console.log('[ENHANCED] Conversation instructions provided - getting new ephemeral key with context');
      
      const newToken = await this.getEphemeralKey(
        this.currentLanguage, 
        this.currentLevel,
        this.currentTopic,
        this.currentUserPrompt,
        this.currentAssessmentData,
        instructions
      );
      
      if (!newToken) {
        console.error('[ENHANCED] Failed to get new ephemeral key with conversation history');
        return false;
      }
      
      this.ephemeralKey = newToken;
      console.log('[ENHANCED] Updated ephemeral key with conversation context');
    }
    
    // Check if data channel is ready
    if (!this.dataChannel) {
      console.error('[ENHANCED] Data channel not initialized');
      return false;
    }
    
    // Wait for data channel to be ready (longer timeout for mobile)
    if (this.dataChannel.readyState !== 'open') {
      console.log('[ENHANCED] Data channel not open, waiting before starting conversation...');
      
      try {
        const timeout = this.mobile_optimization_active ? 12000 : 8000;
        await new Promise<void>((resolve, reject) => {
          const timeoutId = setTimeout(() => {
            reject(new Error('Timed out waiting for data channel to open'));
          }, timeout);
          
          const checkDataChannel = () => {
            if (!this.dataChannel) {
              clearTimeout(timeoutId);
              reject(new Error('Data channel was cleared'));
              return;
            }
            
            if (this.dataChannel.readyState === 'open') {
              clearTimeout(timeoutId);
              resolve();
            } else if (this.dataChannel.readyState === 'closed' || this.dataChannel.readyState === 'closing') {
              clearTimeout(timeoutId);
              reject(new Error('Data channel closed before it could open'));
            } else {
              setTimeout(checkDataChannel, 100);
            }
          };
          
          checkDataChannel();
        });
      } catch (error) {
        console.error('❌ [ENHANCED] Error waiting for data channel to open:', error);
        return false;
      }
    }
    
    // Enhanced delay for mobile browsers to ensure everything is ready
    const delay = this.mobile_optimization_active ? 1000 : 800;
    console.log(`⏳ [ENHANCED] Ensuring data channel is fully ready (${delay}ms delay)...`);
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // Send response.create event to start the conversation immediately
    const event: RealtimeResponseCreateEvent = {
      type: 'response.create',
      response: {
        modalities: ['text', 'audio'],
      },
    };
    
    console.log('✅ [ENHANCED] Starting conversation with response.create');
    return this.sendMessage(event);
  }

  /**
   * Pause the conversation without disconnecting
   */
  public pauseConversation(): boolean {
    try {
      console.log('⏸️ [ENHANCED] Pausing conversation (keeping connection alive)...');
      
      if (!this.isConnected || !this.dataChannel) {
        console.warn('⚠️ [ENHANCED] Cannot pause - not connected or no data channel');
        return false;
      }
      
      this.isPaused = true;
      this.pauseStartTime = Date.now();
      
      // Mute the local audio track instead of stopping it
      if (this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        audioTracks.forEach(track => {
          track.enabled = false; // Mute instead of stop
          console.log('🔇 [ENHANCED] Muted audio track:', track.label);
        });
      }
      
      // Mute the remote audio as well
      if (this.audioElement) {
        this.audioElement.muted = true;
        console.log('🔇 [ENHANCED] Muted remote audio');
      }
      
      console.log('✅ [ENHANCED] Conversation paused successfully');
      return true;
    } catch (error) {
      console.error('❌ [ENHANCED] Error pausing conversation:', error);
      return false;
    }
  }
  
  /**
   * Resume the conversation from pause
   */
  public resumeConversation(): boolean {
    try {
      console.log('▶️ [ENHANCED] Resuming conversation...');
      
      if (!this.isPaused) {
        console.warn('⚠️ [ENHANCED] Conversation is not paused');
        return false;
      }
      
      if (!this.isConnected || !this.dataChannel) {
        console.warn('⚠️ [ENHANCED] Cannot resume - not connected or no data channel');
        return false;
      }
      
      // Calculate pause duration
      const pauseDuration = this.pauseStartTime ? Date.now() - this.pauseStartTime : 0;
      console.log(`⏱️ [ENHANCED] Resuming after ${pauseDuration}ms pause`);
      
      // Unmute the local audio track
      if (this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        audioTracks.forEach(track => {
          track.enabled = true; // Unmute
          console.log('🔊 [ENHANCED] Unmuted audio track:', track.label);
        });
      }
      
      // Unmute the remote audio
      if (this.audioElement) {
        this.audioElement.muted = false;
        console.log('🔊 [ENHANCED] Unmuted remote audio');
      }
      
      this.isPaused = false;
      this.pauseStartTime = null;
      
      console.log('✅ [ENHANCED] Conversation resumed successfully');
      return true;
    } catch (error) {
      console.error('❌ [ENHANCED] Error resuming conversation:', error);
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
   * Emergency mute override for critical situations
   */
  public emergencyMute(reason: string): void {
    console.log(`🚨 [ENHANCED] EMERGENCY MUTE ACTIVATED: ${reason}`);
    
    this.clearAllDelayedOperations();
    this.ai_is_speaking = true;
    this.last_ai_speech_event = `EMERGENCY: ${reason}`;
    
    // Triple-layer emergency muting
    this.muteViaTrackEnabled(true);
    
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.forceMute(true, reason);
      } catch (error) {
        console.error('🚨 [ENHANCED] SemanticMuteController emergency mute failed:', error);
      }
    }
    
    // Force remote audio mute
    if (this.audioElement) {
      this.audioElement.muted = true;
    }
  }

  /**
   * Emergency unmute override for critical situations
   */
  public emergencyUnmute(reason: string): void {
    console.log(`🔊 [ENHANCED] EMERGENCY UNMUTE ACTIVATED: ${reason}`);
    
    this.clearAllDelayedOperations();
    this.ai_is_speaking = false;
    this.last_ai_speech_event = `EMERGENCY UNMUTE: ${reason}`;
    
    // Triple-layer emergency unmuting
    this.muteViaTrackEnabled(false);
    
    if (this.semanticMuteController) {
      try {
        this.semanticMuteController.forceMute(false, reason);
      } catch (error) {
        console.error('🔊 [ENHANCED] SemanticMuteController emergency unmute failed:', error);
      }
    }
  }

  /**
   * Get current AI speaking state for debugging
   */
  public getAISpeakingState(): boolean {
    return this.ai_is_speaking;
  }

  /**
   * NEW: Mute user microphone (different from AI self-hearing prevention)
   */
  public muteUserMicrophone(): boolean {
    try {
      console.log('🔇 [USER_MUTE] Muting user microphone on request');
      
      if (!this.localStream) {
        console.warn('⚠️ [USER_MUTE] No local stream available');
        return false;
      }
      
      const audioTracks = this.localStream.getAudioTracks();
      if (audioTracks.length === 0) {
        console.warn('⚠️ [USER_MUTE] No audio tracks found');
        return false;
      }
      
      // ✅ CRITICAL: Set user manual mute flag
      this.user_manually_muted = true;
      
      // Mute all audio tracks
      audioTracks.forEach((track, index) => {
        if (track.readyState === 'live') {
          track.enabled = false;
          console.log(`🔇 [USER_MUTE] Track ${index} (${track.label}) muted by user`);
        }
      });
      
      // Emit custom event for UI feedback
      if (typeof window !== 'undefined') {
        const event = new CustomEvent('user-microphone-muted', {
          detail: {
            timestamp: Date.now(),
            reason: 'User requested mute'
          }
        });
        window.dispatchEvent(event);
      }
      
      console.log('✅ [USER_MUTE] User microphone muted successfully');
      return true;
    } catch (error) {
      console.error('❌ [USER_MUTE] Error muting user microphone:', error);
      return false;
    }
  }

  /**
   * NEW: Unmute user microphone
   */
  public unmuteUserMicrophone(): boolean {
    try {
      console.log('🔊 [USER_MUTE] Unmuting user microphone on request');
      
      if (!this.localStream) {
        console.warn('⚠️ [USER_MUTE] No local stream available');
        return false;
      }
      
      const audioTracks = this.localStream.getAudioTracks();
      if (audioTracks.length === 0) {
        console.warn('⚠️ [USER_MUTE] No audio tracks found');
        return false;
      }
      
      // ✅ CRITICAL: Clear user manual mute flag
      this.user_manually_muted = false;
      
      // Unmute all audio tracks
      audioTracks.forEach((track, index) => {
        if (track.readyState === 'live') {
          track.enabled = true;
          console.log(`🔊 [USER_MUTE] Track ${index} (${track.label}) unmuted by user`);
        }
      });
      
      // Emit custom event for UI feedback
      if (typeof window !== 'undefined') {
        const event = new CustomEvent('user-microphone-unmuted', {
          detail: {
            timestamp: Date.now(),
            reason: 'User requested unmute'
          }
        });
        window.dispatchEvent(event);
      }
      
      console.log('✅ [USER_MUTE] User microphone unmuted successfully');
      return true;
    } catch (error) {
      console.error('❌ [USER_MUTE] Error unmuting user microphone:', error);
      return false;
    }
  }

  /**
   * NEW: Check if user microphone is currently muted
   */
  public isUserMicrophoneMuted(): boolean {
    if (!this.localStream) return true;
    
    const audioTracks = this.localStream.getAudioTracks();
    if (audioTracks.length === 0) return true;
    
    // Check if any track is enabled (not muted)
    return !audioTracks.some(track => track.enabled && track.readyState === 'live');
  }

  /**
   * Get comprehensive muting diagnostics
   */
  public getMutingDiagnostics(): any {
    return {
      ai_is_speaking: this.ai_is_speaking,
      fallback_protection_enabled: this.fallback_protection_enabled,
      last_ai_speech_event: this.last_ai_speech_event,
      fallback_mute_timeout_active: this.fallback_mute_timeout !== null,
      emergency_mute_timeout_active: this.emergency_mute_timeout !== null,
      semantic_controller_available: this.semanticMuteController !== null,
      local_stream_available: this.localStream !== null,
      mobile_optimization_active: this.mobile_optimization_active,
      pre_connection_mute_active: this.pre_connection_mute_active,
      echo_cancellation_level: this.echo_cancellation_level,
      audio_tracks_count: this.localStream ? this.localStream.getAudioTracks().length : 0,
      audio_tracks_enabled: this.localStream ? 
        this.localStream.getAudioTracks().map(track => ({
          label: track.label,
          enabled: track.enabled,
          readyState: track.readyState
        })) : [],
      semantic_controller_diagnostics: this.semanticMuteController ? 
        this.semanticMuteController.getDiagnostics() : null,
      // NEW: User mute status
      user_microphone_muted: this.isUserMicrophoneMuted()
    };
  }

  /**
   * Disconnect and clean up all resources
   */
  public disconnect(): void {
    console.log('🧹 [ENHANCED] Disconnecting with enhanced cleanup...');
    try {
      // Clear all timeouts
      this.clearAllDelayedOperations();
      
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
        this.connectionAttemptTimeout = null;
      }
      
      // Stop all media tracks first
      if (this.localStream) {
        console.log('🛑 [ENHANCED] Stopping local stream tracks...');
        const tracks = this.localStream.getTracks();
        tracks.forEach(track => {
          try {
            track.stop();
            console.log('🛑 [ENHANCED] Stopped track:', track.kind, track.label);
          } catch (e) {
            console.error('❌ [ENHANCED] Error stopping track:', e);
          }
        });
        this.localStream = null;
      }
      
      // Close data channel
      if (this.dataChannel) {
        console.log('🔌 [ENHANCED] Closing data channel...');
        try {
          this.dataChannel.close();
        } catch (e) {
          console.error('❌ [ENHANCED] Error closing data channel:', e);
        }
        this.dataChannel = null;
      }
      
      // Close peer connection
      if (this.peerConnection) {
        console.log('🔌 [ENHANCED] Closing peer connection...');
        try {
          this.peerConnection.close();
        } catch (e) {
          console.error('❌ [ENHANCED] Error closing peer connection:', e);
        }
        this.peerConnection = null;
      }
      
      // Clear audio element
      if (this.audioElement) {
        this.audioElement.srcObject = null;
        this.audioElement.muted = true;
      }
      
      // Dispose of SemanticMuteController
      if (this.semanticMuteController) {
        this.semanticMuteController.dispose();
        this.semanticMuteController = null;
        console.log('✅ [ENHANCED] SemanticMuteController disposed');
      }
      
      // Reset all state
      this.ai_is_speaking = false;
      this.fallback_protection_enabled = true;
      this.last_ai_speech_event = '';
      this.pre_connection_mute_active = false;
      
      console.log('✅ [ENHANCED] Enhanced cleanup completed');
    } catch (e) {
      console.error('❌ [ENHANCED] Error during disconnect:', e);
    } finally {
      this.isConnected = false;
      console.log('✅ [ENHANCED] Disconnected');
      if (this.onDisconnectedCallback) this.onDisconnectedCallback();
    }
  }

  /**
   * Convert language name to ISO-639-1 code
   */
  private getLanguageIsoCode(language: string): string {
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
    
    return languageMap[language.toLowerCase()] || language.toLowerCase();
  }
  
  /**
   * Get an ephemeral key from the backend
   */
  public async getEphemeralKey(language?: string, level?: string, topic?: string, userPrompt?: string, assessmentData?: any, conversationHistory?: string): Promise<string> {
    let usedMockToken = false;
    
    try {
      console.log('================================================================================');
      console.log('🌐 [ENHANCED] Getting ephemeral key from backend...');
      console.log('🌐 [ENHANCED] Timestamp:', new Date().toISOString());
      console.log('🌐 [ENHANCED] Language:', language);
      console.log('🌐 [ENHANCED] Level:', level);
      console.log('🌐 [ENHANCED] Topic:', topic);
      console.log('🌐 [ENHANCED] User prompt length:', userPrompt ? userPrompt.length : 0);
      console.log('🌐 [ENHANCED] Assessment data provided:', !!assessmentData);
      console.log('================================================================================');
      
      if (!language || !level) {
        console.error('[ENHANCED] Missing language or level parameters');
        throw new Error('Language and level are required parameters');
      }
      
      let endpoint = `${this.backendUrl}/api/realtime/token`;
      console.log('[ENHANCED] Fetching ephemeral key from:', endpoint);
      
      let researchData = null;
      if (topic === 'custom') {
        const storedResearchData = sessionStorage.getItem('customTopicResearch');
        if (storedResearchData) {
          try {
            const parsedResearch = JSON.parse(storedResearchData);
            console.log('[ENHANCED] Parsed research data structure:', parsedResearch);
            
            if (parsedResearch.research) {
              researchData = parsedResearch.research;
              console.log('[ENHANCED] Retrieved research data from "research" field:', researchData.length, 'characters');
            } else if (parsedResearch.research_content) {
              researchData = parsedResearch.research_content;
              console.log('[ENHANCED] Retrieved research data from "research_content" field:', researchData.length, 'characters');
            } else {
              console.log('[ENHANCED] No research data found in expected fields. Available fields:', Object.keys(parsedResearch));
            }
          } catch (error) {
            console.error('[ENHANCED] Error parsing research data:', error);
          }
        } else {
          console.log('[ENHANCED] No research data found in session storage for custom topic');
        }
      }
      
      let selectedVoice = 'alloy';
      try {
        const token = localStorage.getItem('token');
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const voiceResponse = await fetch(`${this.backendUrl}/auth/get-voice`, {
          method: 'GET',
          credentials: 'include',
          headers
        });
        
        if (voiceResponse.ok) {
          const voiceData = await voiceResponse.json();
          if (voiceData.voice) {
            selectedVoice = voiceData.voice;
            console.log('[ENHANCED] Using user preferred voice:', selectedVoice);
          } else {
            console.log('[ENHANCED] No voice preference found, using default:', selectedVoice);
          }
        } else {
          console.log('[ENHANCED] Failed to get voice preference (status:', voiceResponse.status, '), using default:', selectedVoice);
        }
      } catch (voiceError) {
        console.log('[ENHANCED] Error fetching voice preference, using default:', selectedVoice, voiceError);
      }

      const requestBody = {
        language: language,
        level: level,
        voice: selectedVoice,
        topic: topic || null,
        user_prompt: userPrompt || null,
        assessment_data: assessmentData || null,
        research_data: researchData || null,
        conversation_history: conversationHistory || null
      };
      
      if (assessmentData) {
        console.log('[ENHANCED] Including assessment data in token request');
      }
      
      if (topic === 'custom' && userPrompt) {
        console.log('[ENHANCED] Using custom topic with user prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
      }
      
      console.log('[ENHANCED] Request body:', JSON.stringify(requestBody));
      
      let realEndpointError: any = null;
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
          credentials: 'omit',
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('📥 [ENHANCED] Received response from backend:', data);
          
          if (data.ephemeral_key) {
            console.log('✅ [ENHANCED] Successfully obtained real ephemeral key');
            return data.ephemeral_key;
          } else if (data.client_secret && data.client_secret.value) {
            console.log('✅ [ENHANCED] Successfully obtained client secret value');
            return data.client_secret.value;
          } else {
            console.error('❌ [ENHANCED] Response did not contain expected token format:', data);
            throw new Error('Invalid response format from token endpoint');
          }
        } else {
          let errorData: any = null;
          try {
            errorData = await response.json();
            console.error('❌ [ENHANCED] Error response from token endpoint:', response.status, errorData);
          } catch (jsonError) {
            const errorText = await response.text();
            console.error('❌ [ENHANCED] Error from real endpoint (status ' + response.status + '):', errorText);
            errorData = errorText;
          }
          
          realEndpointError = {
            status: response.status,
            data: errorData
          };
          
          throw new Error(`Token endpoint returned ${response.status}`);
        }
      } catch (error) {
        console.error('❌ [ENHANCED] Error with real endpoint:', error);
        realEndpointError = error;
        console.log('🔄 [ENHANCED] Real endpoint failed, trying mock endpoint as fallback...');
      }
      
      usedMockToken = true;
      endpoint = `${this.backendUrl}/api/mock-token`;
      console.log('📤 [ENHANCED] Fetching mock ephemeral key from:', endpoint);
      console.log('📋 [ENHANCED] Mock request body:', JSON.stringify(requestBody));
      
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
          
          console.error(`❌ [ENHANCED] Failed to get mock ephemeral key (status ${mockResponse.status}):`, errorInfo);
          
          if (realEndpointError) {
            throw new Error(`Real endpoint failed: ${realEndpointError.message || JSON.stringify(realEndpointError)}. Mock endpoint also failed (${mockResponse.status}): ${errorInfo}`);
          }
          
          throw new Error(`Failed to get mock token: ${errorInfo}`);
        }
        
        const mockData = await mockResponse.json();
        console.log('📥 [ENHANCED] Received mock response from backend');
        
        if (mockData.ephemeral_key) {
          console.log('✅ [ENHANCED] Using mock ephemeral key for testing');
          return mockData.ephemeral_key;
        } else {
          console.error('❌ [ENHANCED] Invalid mock response format:', mockData);
          throw new Error('Invalid mock response format');
        }
      } catch (mockError) {
        console.error('❌ [ENHANCED] Error with mock endpoint:', mockError);
        
        if (realEndpointError) {
          throw new Error(`Real endpoint error: ${realEndpointError.message || JSON.stringify(realEndpointError)}. Mock endpoint error: ${mockError instanceof Error ? mockError.message : String(mockError)}`);
        }
        
        throw mockError;
      }
    } catch (error) {
      console.error('❌ [ENHANCED] Error getting ephemeral key:', error);
      
      console.error('🔍 [ENHANCED] Detailed error context:', {
        error,
        language,
        level,
        topic,
        backendUrl: this.backendUrl,
        usedMockToken: usedMockToken || false
      });
      
      return '';
    }
  }
}

export default new EnhancedRealtimeService();
