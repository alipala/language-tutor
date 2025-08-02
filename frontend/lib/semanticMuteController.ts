/**
 * SemanticMuteController - Universal muting controller for semantic VAD
 * Implements dual-layer muting and semantic processing delays to prevent AI self-hearing
 * Works on ALL browsers and devices: Desktop (Chrome, Firefox, Safari, Edge), Mobile (iOS Safari, Android Chrome), etc.
 */

export interface SemanticMuteState {
  isMuted: boolean;
  isAISpeaking: boolean;
  delayedUnmuteTimeout: NodeJS.Timeout | null;
  semanticProcessingDelay: number;
  lastMuteReason: string;
}

export class SemanticMuteController {
  private audioContext: AudioContext | null = null;
  private gainNode: GainNode | null = null;
  private mediaStream: MediaStream | null = null;
  private audioTracks: MediaStreamTrack[] = [];
  private state: SemanticMuteState;
  
  // ✅ PHASE 1: Reduced semantic VAD delays
  private readonly SEMANTIC_PROCESSING_DELAY = 100; // Reduced from 300ms
  private readonly AI_SPEECH_TAIL_PROTECTION = 100; // Reduced from 500ms
  private readonly FADE_DURATION = 50; // 50ms fade to prevent audio pops
  
  constructor() {
    this.state = {
      isMuted: false,
      isAISpeaking: false,
      delayedUnmuteTimeout: null,
      semanticProcessingDelay: this.SEMANTIC_PROCESSING_DELAY,
      lastMuteReason: 'initialized'
    };
    
    console.log('🔇 [SEMANTIC_MUTE] Controller initialized with semantic VAD optimizations');
  }
  
  /**
   * Initialize the mute controller with a media stream
   */
  public async initialize(mediaStream: MediaStream): Promise<boolean> {
    try {
      console.log('🔇 [SEMANTIC_MUTE] Initializing with media stream...');
      
      this.mediaStream = mediaStream;
      this.audioTracks = mediaStream.getAudioTracks();
      
      if (this.audioTracks.length === 0) {
        console.error('❌ [SEMANTIC_MUTE] No audio tracks found in media stream');
        return false;
      }
      
      // Initialize Web Audio API for gain control
      if (typeof window !== 'undefined' && window.AudioContext) {
        try {
          this.audioContext = new AudioContext();
          this.gainNode = this.audioContext.createGain();
          
          // Create media stream source and connect to gain node
          const source = this.audioContext.createMediaStreamSource(mediaStream);
          source.connect(this.gainNode);
          
          // Set initial gain to 1.0 (unmuted)
          this.gainNode.gain.setValueAtTime(1.0, this.audioContext.currentTime);
          
          console.log('✅ [SEMANTIC_MUTE] Web Audio API initialized successfully');
        } catch (audioError) {
          console.warn('⚠️ [SEMANTIC_MUTE] Web Audio API initialization failed:', audioError);
          // Continue without Web Audio API - will use track.enabled only
        }
      }
      
      console.log(`✅ [SEMANTIC_MUTE] Initialized with ${this.audioTracks.length} audio tracks`);
      return true;
    } catch (error) {
      console.error('❌ [SEMANTIC_MUTE] Initialization failed:', error);
      return false;
    }
  }
  
  /**
   * Immediate muting when AI starts speaking (dual-layer approach)
   */
  public muteForAISpeech(reason: string = 'AI speaking'): void {
    console.log(`🔇 [SEMANTIC_MUTE] Immediate mute for AI speech: ${reason}`);
    
    this.state.isAISpeaking = true;
    this.state.lastMuteReason = reason;
    
    // Clear any pending unmute operations
    this.clearDelayedUnmute();
    
    // Apply dual-layer muting immediately
    this.applyMute(true);
  }
  
  /**
   * Delayed unmuting after AI speech ends (with semantic processing buffer)
   */
  public scheduleUnmuteAfterAISpeech(reason: string = 'AI speech ended'): void {
    console.log(`🔊 [SEMANTIC_MUTE] Scheduling delayed unmute: ${reason}`);
    
    this.state.isAISpeaking = false;
    this.state.lastMuteReason = `delayed unmute: ${reason}`;
    
    // Clear any existing delayed unmute
    this.clearDelayedUnmute();
    
    // Calculate total delay: semantic processing + AI speech tail protection
    const totalDelay = this.SEMANTIC_PROCESSING_DELAY + this.AI_SPEECH_TAIL_PROTECTION;
    
    console.log(`⏱️ [SEMANTIC_MUTE] Unmuting in ${totalDelay}ms (semantic processing + tail protection)`);
    
    this.state.delayedUnmuteTimeout = setTimeout(() => {
      console.log('🔊 [SEMANTIC_MUTE] Executing delayed unmute');
      this.applyMute(false);
      this.state.delayedUnmuteTimeout = null;
    }, totalDelay);
  }
  
  /**
   * Ensure unmuted state for user speech (semantic VAD detected user speaking)
   */
  public ensureUnmutedForUserSpeech(reason: string = 'User speech detected'): void {
    console.log(`🔊 [SEMANTIC_MUTE] Ensuring unmuted for user speech: ${reason}`);
    
    // Clear any pending delayed unmute operations
    this.clearDelayedUnmute();
    
    this.state.isAISpeaking = false;
    this.state.lastMuteReason = reason;
    
    // Immediately unmute for user speech
    this.applyMute(false);
  }
  
  /**
   * Apply dual-layer muting (track.enabled + gain node)
   */
  private applyMute(shouldMute: boolean): void {
    const action = shouldMute ? 'Muting' : 'Unmuting';
    console.log(`🎛️ [SEMANTIC_MUTE] ${action} with dual-layer approach...`);
    
    // Layer 1: MediaStreamTrack.enabled (immediate hardware-level muting)
    this.audioTracks.forEach((track, index) => {
      if (track.readyState === 'live') {
        track.enabled = !shouldMute;
        console.log(`🎤 [SEMANTIC_MUTE] Track ${index} enabled: ${!shouldMute}`);
      }
    });
    
    // Layer 2: Web Audio API gain control (smooth fading)
    if (this.audioContext && this.gainNode) {
      const currentTime = this.audioContext.currentTime;
      const targetGain = shouldMute ? 0.0 : 1.0;
      const fadeDuration = this.FADE_DURATION / 1000; // Convert to seconds
      
      // Cancel any scheduled changes and set smooth transition
      this.gainNode.gain.cancelScheduledValues(currentTime);
      this.gainNode.gain.setValueAtTime(this.gainNode.gain.value, currentTime);
      this.gainNode.gain.linearRampToValueAtTime(targetGain, currentTime + fadeDuration);
      
      console.log(`🎚️ [SEMANTIC_MUTE] Gain ramping to ${targetGain} over ${this.FADE_DURATION}ms`);
    }
    
    this.state.isMuted = shouldMute;
    
    // Emit custom events for UI updates
    if (typeof window !== 'undefined') {
      const eventType = shouldMute ? 'semantic-mute-engaged' : 'semantic-mute-released';
      const event = new CustomEvent(eventType, {
        detail: {
          reason: this.state.lastMuteReason,
          isAISpeaking: this.state.isAISpeaking,
          timestamp: Date.now()
        }
      });
      window.dispatchEvent(event);
    }
  }
  
  /**
   * Clear any pending delayed unmute operations
   */
  private clearDelayedUnmute(): void {
    if (this.state.delayedUnmuteTimeout) {
      clearTimeout(this.state.delayedUnmuteTimeout);
      this.state.delayedUnmuteTimeout = null;
      console.log('⏹️ [SEMANTIC_MUTE] Cleared pending delayed unmute');
    }
  }
  
  /**
   * ✅ PHASE 1: Less aggressive semantic VAD event handling
   */
  public handleRealtimeEvent(event: any): void {
    switch (event.type) {
      // ✅ PHASE 1: Only mute on actual audio start, not preemptive
      case 'response.audio.start':
        console.log('🔇 [SEMANTIC_MUTE] Audio started - DELAYED MUTE');
        // Add small delay to prevent cutting off beginning of AI speech
        setTimeout(() => {
          this.muteForAISpeech('OpenAI audio response started');
        }, 100);
        break;
        
      case 'response.audio.done':
        this.scheduleUnmuteAfterAISpeech('OpenAI audio response completed');
        break;
        
      case 'input_audio_buffer.speech_started':
        this.ensureUnmutedForUserSpeech('User speech detected by semantic VAD');
        break;
        
      case 'response.audio.delta':
        // Ensure we stay muted during AI speech chunks
        if (!this.state.isMuted) {
          this.muteForAISpeech('AI audio delta received');
        }
        break;
        
      case 'input_audio_buffer.speech_stopped':
        // Don't immediately mute when user stops speaking
        // Let semantic VAD and natural conversation flow handle this
        console.log('👤 [SEMANTIC_MUTE] User speech stopped - maintaining current mute state');
        break;
        
      default:
        // Log other events for debugging
        if (event.type.includes('audio') || event.type.includes('speech')) {
          console.log(`🎵 [SEMANTIC_MUTE] Unhandled audio event: ${event.type}`);
        }
        break;
    }
  }
  
  /**
   * Get current mute state for debugging and UI updates
   */
  public getState(): SemanticMuteState {
    return { ...this.state };
  }
  
  /**
   * Force mute/unmute (for emergency situations)
   */
  public forceMute(shouldMute: boolean, reason: string): void {
    console.log(`🚨 [SEMANTIC_MUTE] Force ${shouldMute ? 'mute' : 'unmute'}: ${reason}`);
    
    this.clearDelayedUnmute();
    this.state.lastMuteReason = `force: ${reason}`;
    this.applyMute(shouldMute);
  }
  
  /**
   * Update semantic processing delay (for fine-tuning)
   */
  public setSemanticProcessingDelay(delayMs: number): void {
    this.state.semanticProcessingDelay = Math.max(100, Math.min(1000, delayMs));
    console.log(`⏱️ [SEMANTIC_MUTE] Semantic processing delay updated to ${this.state.semanticProcessingDelay}ms`);
  }
  
  /**
   * Cleanup and dispose of resources
   */
  public dispose(): void {
    console.log('🧹 [SEMANTIC_MUTE] Disposing controller...');
    
    this.clearDelayedUnmute();
    
    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch (error) {
        console.warn('⚠️ [SEMANTIC_MUTE] Error closing audio context:', error);
      }
      this.audioContext = null;
    }
    
    this.gainNode = null;
    this.mediaStream = null;
    this.audioTracks = [];
    
    console.log('✅ [SEMANTIC_MUTE] Controller disposed');
  }
  
  /**
   * Get diagnostic information for troubleshooting
   */
  public getDiagnostics(): any {
    return {
      state: this.getState(),
      audioContext: {
        available: !!this.audioContext,
        state: this.audioContext?.state,
        sampleRate: this.audioContext?.sampleRate
      },
      gainNode: {
        available: !!this.gainNode,
        currentGain: this.gainNode?.gain.value
      },
      tracks: this.audioTracks.map((track, index) => ({
        index,
        enabled: track.enabled,
        readyState: track.readyState,
        label: track.label
      })),
      delays: {
        semanticProcessing: this.SEMANTIC_PROCESSING_DELAY,
        aiSpeechTailProtection: this.AI_SPEECH_TAIL_PROTECTION,
        fadeDuration: this.FADE_DURATION
      }
    };
  }
}

export default SemanticMuteController;
