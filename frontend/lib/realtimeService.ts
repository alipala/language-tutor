import { RealtimeEvent, RealtimeResponseCreateEvent } from './types';

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
  private currentLanguageIsoCode: string = '';
  private sessionUpdated: boolean = false;

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
      console.log('Initializing realtime service...');
      // Clean up any existing connections first
      this.disconnect();
      
      this.onMessageCallback = onMessage;
      this.onConnectedCallback = onConnected || null;
      this.onDisconnectedCallback = onDisconnected || null;
      this.reconnectAttempts = 0;
      
      // Store the language for use in transcription
      if (language) {
        this.currentLanguage = language.toLowerCase();
        this.currentLanguageIsoCode = this.getLanguageIsoCode(this.currentLanguage);
        console.log('Language set for transcription:', this.currentLanguage, 'ISO code:', this.currentLanguageIsoCode);
      }
      
      // Use the correct backend URL (default to localhost:8000 if running locally)
      this.backendUrl = '';
      if (typeof window !== 'undefined') {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          this.backendUrl = 'http://localhost:8000';
        }
      }
      
      console.log('Using backend URL:', this.backendUrl);
      
      // Test the connection to the backend first
      try {
        const testResponse = await fetch(`${this.backendUrl}/api/test`, {
        credentials: 'same-origin'
      });
        if (!testResponse.ok) {
          console.error('Backend connection test failed:', await testResponse.text());
          return false;
        }
        const testData = await testResponse.json();
        console.log('Backend connection test successful:', testData.message);
      } catch (err) {
        console.error('Error connecting to backend:', err);
        return false;
      }
      
      try {
        // Get ephemeral key from backend with language and level if provided
        const token = await this.getEphemeralKey(language, level, topic, userPrompt, assessmentData);
        if (!token) {
          console.error('Failed to get ephemeral key (empty token)');
          return false;
        }
        
        console.log('Ephemeral key obtained successfully');
        this.ephemeralKey = token;
        return true;
      } catch (err) {
        console.error('Error getting ephemeral key:', err);
        return false;
      }
    } catch (error) {
      console.error('Error initializing realtime service:', error);
      return false;
    }
  }
  
  /**
   * Set up WebRTC connection
   */
  private setupWebRTC(): boolean {
    try {
      // Create peer connection with STUN servers
      this.peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
        ]
      });
      
      // Set up audio handling
      this.peerConnection.ontrack = (e) => {
        console.log('Received remote track', e.streams);
        if (this.audioElement && e.streams && e.streams[0]) {
          this.audioElement.srcObject = e.streams[0];
        }
      };
      
      // Set up data channel with specific configuration for transcription
      this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
        ordered: true,
        maxRetransmits: 3  // Add retry mechanism for reliability
      });
      
      this.dataChannel.onopen = () => {
        console.log('Data channel opened');
        this.isConnected = true;
        
        // As soon as the data channel opens, send a session.update event to enable transcription
        // This is critical for ensuring transcription works from the beginning
        this.updateSession();
        
        // Mark that we've already sent the session update
        this.sessionUpdated = true;
        
        if (this.onConnectedCallback) this.onConnectedCallback();
      };
      
      this.dataChannel.onclose = () => {
        console.log('Data channel closed');
        this.isConnected = false;
        if (this.onDisconnectedCallback) this.onDisconnectedCallback();
      };
      
      this.dataChannel.onmessage = (e) => {
        if (this.onMessageCallback) {
          try {
            const eventData = JSON.parse(e.data) as RealtimeEvent;
            console.log('Received message type:', eventData.type);
            
            // Log specific details for transcription events
            if (eventData.type === 'conversation.item.created') {
              console.log('Conversation item created:', 
                eventData.item?.role, 
                eventData.item?.content ? 'Content array present' : 'No content array',
                eventData.item?.input ? 'Input present' : 'No input');
            } else if (eventData.type === 'conversation.item.input_audio_transcription.completed') {
              console.log('Transcription completed:', eventData.transcription?.text);
            }
            
            this.onMessageCallback(eventData);
          } catch (error) {
            console.error('Error parsing message:', error);
          }
        }
      };
      
      // Set up ICE candidate handling
      this.peerConnection.onicecandidate = (event) => {
        console.log('ICE candidate', event.candidate);
      };
      
      this.peerConnection.oniceconnectionstatechange = () => {
        console.log('ICE connection state:', this.peerConnection?.iceConnectionState);
        if (this.peerConnection?.iceConnectionState === 'failed' || 
            this.peerConnection?.iceConnectionState === 'disconnected') {
          console.warn('ICE connection failed or disconnected');
        }
      };
      
      return true;
    } catch (error) {
      console.error('Error setting up WebRTC:', error);
      return false;
    }
  }
  
  /**
   * Request microphone access and add tracks to peer connection
   */
  public async startMicrophone(): Promise<boolean> {
    try {
      console.log('Requesting microphone access...');
      if (typeof window === 'undefined') return false;
      
      // Set up WebRTC if not already done
      if (!this.peerConnection) {
        console.log('Setting up WebRTC connection first...');
        const setupSuccess = this.setupWebRTC();
        if (!setupSuccess) {
          console.error('Failed to set up WebRTC connection');
          return false;
        }
        
        // Add a small delay after WebRTC setup to ensure it's ready
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      // Release any existing stream to avoid resource leaks
      if (this.localStream) {
        console.log('Releasing existing media stream...');
        this.localStream.getTracks().forEach(track => {
          track.stop();
          console.log(`Stopped track: ${track.kind}`);
        });
        this.localStream = null;
        
        // Add a small delay after stopping tracks to ensure they're fully released
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      // Request microphone access with constraints
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      };
      
      console.log('Requesting user media with constraints:', JSON.stringify(constraints));
      
      try {
        // First try with a timeout to prevent hanging if permission dialog is ignored
        const getUserMediaPromise = navigator.mediaDevices.getUserMedia(constraints);
        const timeoutPromise = new Promise<MediaStream>((_, reject) => {
          setTimeout(() => reject(new Error('Microphone access request timed out')), 10000);
        });
        
        this.localStream = await Promise.race([getUserMediaPromise, timeoutPromise]);
        console.log('Microphone access granted', this.localStream);
      } catch (mediaError) {
        console.error('First attempt to get user media failed:', mediaError);
        
        // Wait a moment and try again with a simpler constraint
        await new Promise(resolve => setTimeout(resolve, 500));
        console.log('Retrying with simpler constraints...');
        
        try {
          this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          console.log('Microphone access granted on second attempt');
        } catch (retryError) {
          console.error('Second attempt to get user media failed:', retryError);
          throw retryError; // Re-throw to be caught by the outer catch block
        }
      }
      
      // Add audio track to peer connection
      if (this.peerConnection && this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        if (audioTracks.length === 0) {
          console.error('No audio tracks found in media stream');
          return false;
        }
        
        console.log('Adding audio track to peer connection', audioTracks[0].label);
        
        try {
          const sender = this.peerConnection.addTrack(audioTracks[0], this.localStream);
          console.log('Track added successfully, sender created:', sender ? 'Yes' : 'No');
          
          // Add a small delay after adding track to ensure it's properly registered
          await new Promise(resolve => setTimeout(resolve, 200));
          return true;
        } catch (trackError) {
          console.error('Error adding track to peer connection:', trackError);
          return false;
        }
      }
      
      return false;
    } catch (error) {
      console.error('Error starting microphone:', error);
      
      // Specific error handling for common issues
      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          console.error('Microphone permission denied by user');
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
          console.error('No microphone found on this device');
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
          console.error('Microphone is already in use by another application');
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
      console.log('Connecting to OpenAI...');
      if (!this.peerConnection) {
        console.error('Peer connection not initialized');
        return false;
      }
      
      // Clear any existing timeout
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
      }
      
      // Set connection timeout
      this.connectionAttemptTimeout = setTimeout(() => {
        console.error('Connection attempt timed out');
        this.disconnect();
      }, 15000);
      
      // Make sure data channel is created before creating the offer
      if (!this.dataChannel || this.dataChannel.readyState === 'closed') {
        console.log('Creating new data channel before offer...');
        try {
          this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
            ordered: true
          });
          
          console.log('Data channel created successfully');
          
          this.dataChannel.onopen = () => {
            console.log('Data channel opened');
            this.isConnected = true;
            if (this.onConnectedCallback) this.onConnectedCallback();
          };
          
          this.dataChannel.onclose = () => {
            console.log('Data channel closed');
            this.isConnected = false;
            if (this.onDisconnectedCallback) this.onDisconnectedCallback();
          };
          
          this.dataChannel.onmessage = (e) => {
            if (this.onMessageCallback) {
              try {
                const eventData = JSON.parse(e.data) as RealtimeEvent;
                this.onMessageCallback(eventData);
              } catch (error) {
                console.error('Error parsing message:', error);
              }
            }
          };
          
          // Add a small delay after creating the data channel
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (channelError) {
          console.error('Error creating data channel:', channelError);
          return false;
        }
      }
      
      // Create offer
      console.log('Creating offer...');
      // Variable to store the complete offer with ICE candidates
      let completeOffer: RTCSessionDescriptionInit | null = null;
      
      try {
        const offer = await this.peerConnection.createOffer({
          offerToReceiveAudio: true
        });
        
        console.log('Setting local description...');
        await this.peerConnection.setLocalDescription(offer);
        console.log('Local description set successfully');
        
        // Add a small delay after setting local description
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Wait for ICE gathering to complete
        console.log('Waiting for ICE gathering to complete...');
        completeOffer = await this.waitForIceComplete();
        if (!completeOffer) {
          console.error('Failed to gather ICE candidates');
          return false;
        }
        
        console.log('ICE gathering completed successfully');
      } catch (offerError) {
        console.error('Error creating or processing offer:', offerError);
        return false;
      }
      
      // Send offer to OpenAI
      console.log('Sending offer to OpenAI...');
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
        console.error('Error connecting to OpenAI:', errorText);
        return false;
      }
      
      // Set remote description
      console.log('Setting remote description...');
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
      
      console.log('Connected to OpenAI successfully');
      return true;
    } catch (error) {
      console.error('Error connecting to OpenAI:', error);
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
        console.warn('ICE gathering timed out, proceeding with available candidates');
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
      console.error('Data channel not available, cannot send message');
      return false;
    }
    
    // If data channel is connecting, wait for it to open
    if (this.dataChannel.readyState === 'connecting') {
      console.log('Data channel is connecting, waiting for it to open...');
      return false;
    }
    
    // If data channel is not open, cannot send message
    if (this.dataChannel.readyState !== 'open') {
      console.error(`Data channel not open (state: ${this.dataChannel.readyState}), cannot send message`);
      return false;
    }
    
    try {
      const messageString = JSON.stringify(message);
      console.log('Sending message:', message.type);
      this.dataChannel.send(messageString);
      return true;
    } catch (error) {
      console.error('Error sending message:', error);
      return false;
    }
  }
  
  /**
   * Start a conversation with OpenAI
   */
  public async startConversation(instructions?: string): Promise<boolean> {
    console.log('Starting conversation...');
    
    // Check if data channel is ready
    if (!this.dataChannel) {
      console.error('Data channel not initialized');
      return false;
    }
    
    // If data channel is connecting, wait for it to open
    if (this.dataChannel.readyState !== 'open') {
      console.log(`Data channel not open (state: ${this.dataChannel.readyState}), waiting before starting conversation...`);
      
      // Wait for the data channel to open
      try {
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Timed out waiting for data channel to open'));
          }, 5000);
          
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
        console.error('Error waiting for data channel to open:', error);
        return false;
      }
    }
    
    // Add a small delay to ensure the data channel is fully ready
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Only send session.update if we haven't already sent it when the data channel opened
    if (!this.sessionUpdated) {
      console.log('Sending initial session update...');
      const updateSuccess = this.updateSession();
      if (!updateSuccess) {
        console.error('Failed to send session update event');
        return false;
      }
      
      this.sessionUpdated = true;
      
      // Add a small delay after sending the session update
      await new Promise(resolve => setTimeout(resolve, 300));
    } else {
      console.log('Session already updated, skipping duplicate update');
    }
    
    // Add a small delay after sending the session update
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Then send the response.create event to start the conversation
    const event: RealtimeResponseCreateEvent = {
      type: 'response.create',
      response: {
        modalities: ['text', 'audio'],
        instructions: instructions || 'Have a conversation with me.',
      },
    };
    
    return this.sendMessage(event);
  }
  
  /**
   * Update the session configuration with transcription settings
   */
  private updateSession(): boolean {
    console.log('Updating session with transcription language:', this.currentLanguage || 'auto-detect', 'ISO code:', this.currentLanguageIsoCode || 'auto-detect');
    
    // Create session update event with language parameter
    const sessionUpdateEvent = {
      type: 'session.update',
      session: {
        modalities: ['text', 'audio'],
        input_audio_transcription: {
          model: 'gpt-4o-mini-transcribe', // Using the newer model for better transcription accuracy
          language: this.currentLanguageIsoCode || undefined // Pass language in ISO-639-1 format if available
        },
        turn_detection: {
          type: 'semantic_vad' // Using improved voice activity detection
        }
      }
    };
    
    // Send the session update event
    const sent = this.sendMessage(sessionUpdateEvent);
    console.log('Session update event sent:', sent);
    
    return sent;
  }
  
  /**
   * Disconnect and clean up all resources
   */
  public disconnect(): void {
    console.log('Disconnecting...');
    try {
      // Clear any pending timeouts
      if (this.connectionAttemptTimeout) {
        clearTimeout(this.connectionAttemptTimeout);
        this.connectionAttemptTimeout = null;
      }
      
      // Reset session updated flag
      this.sessionUpdated = false;
      
      // Stop all media tracks first
      if (this.localStream) {
        console.log('Stopping local stream tracks...');
        const tracks = this.localStream.getTracks();
        tracks.forEach(track => {
          try {
            track.stop();
            console.log('Stopped track:', track.kind, track.label);
          } catch (e) {
            console.error('Error stopping track:', e);
          }
        });
        this.localStream = null;
      }
      
      // Close data channel
      if (this.dataChannel) {
        console.log('Closing data channel...');
        try {
          this.dataChannel.close();
        } catch (e) {
          console.error('Error closing data channel:', e);
        }
        this.dataChannel = null;
      }
      
      // Close peer connection
      if (this.peerConnection) {
        console.log('Closing peer connection...');
        try {
          this.peerConnection.close();
        } catch (e) {
          console.error('Error closing peer connection:', e);
        }
        this.peerConnection = null;
      }
      
      // Clear audio element
      if (this.audioElement) {
        this.audioElement.srcObject = null;
      }
    } catch (e) {
      console.error('Error during disconnect:', e);
    } finally {
      this.isConnected = false;
      console.log('Disconnected');
      if (this.onDisconnectedCallback) this.onDisconnectedCallback();
    }
  }
  
  /**
   * Get an ephemeral key from the backend
   */
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
  private async getEphemeralKey(language?: string, level?: string, topic?: string, userPrompt?: string, assessmentData?: any): Promise<string> {
    // Flag to track if we're using the mock token endpoint
    let usedMockToken = false;
    
    try {
      console.log('Getting ephemeral key from backend...');
      console.log('Language:', language);
      console.log('Level:', level);
      console.log('Topic:', topic);
      
      // Ensure we have both language and level
      if (!language || !level) {
        console.error('Missing language or level parameters');
        throw new Error('Language and level are required parameters');
      }
      
      // First try the real endpoint
      let endpoint = `${this.backendUrl}/api/realtime/token`;
      console.log('Fetching ephemeral key from:', endpoint);
      
      // Prepare request body with language and level
      const requestBody = {
        language: language,
        level: level,
        voice: 'alloy', // Default voice
        topic: topic || null, // Add topic if provided
        user_prompt: userPrompt || null, // Add user prompt for custom topics
        assessment_data: assessmentData || null // Add assessment data if provided
      };
      
      // Log if assessment data is provided
      if (assessmentData) {
        console.log('Including assessment data in token request');
      }
      
      // Log if we're using a custom topic with user prompt
      if (topic === 'custom' && userPrompt) {
        console.log('Using custom topic with user prompt:', userPrompt.substring(0, 50) + (userPrompt.length > 50 ? '...' : ''));
      }
      
      console.log('Request body:', JSON.stringify(requestBody));
      
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
          console.log('Received response from backend:', data);
          
          if (data.ephemeral_key) {
            console.log('Successfully obtained real ephemeral key');
            return data.ephemeral_key;
          } else if (data.client_secret && data.client_secret.value) {
            console.log('Successfully obtained client secret value');
            return data.client_secret.value;
          } else {
            console.error('Response did not contain expected token format:', data);
            throw new Error('Invalid response format from token endpoint');
          }
        } else {
          // Try to parse the error as JSON first
          let errorData: any = null;
          try {
            errorData = await response.json();
            console.error('Error response from token endpoint:', response.status, errorData);
          } catch (jsonError) {
            // If it's not JSON, get it as text
            const errorText = await response.text();
            console.error('Error from real endpoint (status ' + response.status + '):', errorText);
            errorData = errorText;
          }
          
          realEndpointError = {
            status: response.status,
            data: errorData
          };
          
          throw new Error(`Token endpoint returned ${response.status}`);
        }
      } catch (error) {
        console.error('Error with real endpoint:', error);
        realEndpointError = error;
        console.log('Real endpoint failed, trying mock endpoint as fallback...');
      }
      
      // Try the mock endpoint as a fallback
      usedMockToken = true;
      endpoint = `${this.backendUrl}/api/mock-token`;
      console.log('Fetching mock ephemeral key from:', endpoint);
      console.log('Mock request body:', JSON.stringify(requestBody));
      
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
          
          console.error(`Failed to get mock ephemeral key (status ${mockResponse.status}):`, errorInfo);
          
          // If both real and mock endpoints failed, provide comprehensive error
          if (realEndpointError) {
            throw new Error(`Real endpoint failed: ${realEndpointError.message || JSON.stringify(realEndpointError)}. Mock endpoint also failed (${mockResponse.status}): ${errorInfo}`);
          }
          
          throw new Error(`Failed to get mock token: ${errorInfo}`);
        }
        
        const mockData = await mockResponse.json();
        console.log('Received mock response from backend');
        
        if (mockData.ephemeral_key) {
          console.log('Using mock ephemeral key for testing');
          return mockData.ephemeral_key;
        } else {
          console.error('Invalid mock response format:', mockData);
          throw new Error('Invalid mock response format');
        }
      } catch (mockError) {
        console.error('Error with mock endpoint:', mockError);
        
        // If both endpoints failed, provide a comprehensive error message
        if (realEndpointError) {
          throw new Error(`Real endpoint error: ${realEndpointError.message || JSON.stringify(realEndpointError)}. Mock endpoint error: ${mockError instanceof Error ? mockError.message : String(mockError)}`);
        }
        
        throw mockError;
      }
    } catch (error) {
      console.error('Error getting ephemeral key:', error);
      
      // Log detailed debugging information
      console.error('Detailed error context:', {
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
