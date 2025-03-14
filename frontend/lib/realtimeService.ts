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
  public async initialize(onMessage: (event: RealtimeEvent) => void, onConnected?: () => void, onDisconnected?: () => void): Promise<boolean> {
    try {
      console.log('Initializing realtime service...');
      // Clean up any existing connections first
      this.disconnect();
      
      this.onMessageCallback = onMessage;
      this.onConnectedCallback = onConnected || null;
      this.onDisconnectedCallback = onDisconnected || null;
      this.reconnectAttempts = 0;
      
      // Use the correct backend URL (default to localhost:3001 if running locally)
      this.backendUrl = typeof window !== 'undefined' ? 
        (window.location.hostname === 'localhost' ? 'http://localhost:3001' : '') : '';
      
      console.log('Using backend URL:', this.backendUrl);
      
      // Test the connection to the backend first
      try {
        const testResponse = await fetch(`${this.backendUrl}/api/test`);
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
        // Get ephemeral key from backend
        const token = await this.getEphemeralKey();
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
      
      // Set up data channel
      this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
        ordered: true
      });
      
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
        const setupSuccess = this.setupWebRTC();
        if (!setupSuccess) return false;
      }
      
      // Release any existing stream
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => track.stop());
        this.localStream = null;
      }
      
      // Request microphone access with constraints
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      };
      
      this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
      console.log('Microphone access granted', this.localStream);
      
      // Add audio track to peer connection
      if (this.peerConnection && this.localStream) {
        const audioTracks = this.localStream.getAudioTracks();
        if (audioTracks.length === 0) {
          console.error('No audio tracks found in media stream');
          return false;
        }
        
        console.log('Adding audio track to peer connection', audioTracks[0].label);
        this.peerConnection.addTrack(audioTracks[0], this.localStream);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error starting microphone:', error);
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
      
      // Set connection timeout
      this.connectionAttemptTimeout = setTimeout(() => {
        console.error('Connection attempt timed out');
        this.disconnect();
      }, 15000);
      
      // Make sure data channel is created before creating the offer
      if (!this.dataChannel || this.dataChannel.readyState === 'closed') {
        console.log('Creating new data channel before offer...');
        this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
          ordered: true
        });
        
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
      }
      
      // Create offer
      console.log('Creating offer...');
      const offer = await this.peerConnection.createOffer({
        offerToReceiveAudio: true
      });
      
      console.log('Setting local description...');
      await this.peerConnection.setLocalDescription(offer);
      
      // Wait for ICE gathering to complete
      console.log('Waiting for ICE gathering to complete...');
      const completeOffer = await this.waitForIceComplete();
      if (!completeOffer) {
        console.error('Failed to gather ICE candidates');
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
  private async getEphemeralKey(): Promise<string> {
    try {
      console.log('Getting ephemeral key from backend...');
      
      // First try the real endpoint
      let endpoint = `${this.backendUrl}/api/realtime/token`;
      console.log('Fetching ephemeral key from:', endpoint);
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          // Add credentials to ensure cookies are sent
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Received response from backend:', data);
          
          if (data.ephemeral_key) {
            return data.ephemeral_key;
          } else if (data.client_secret && data.client_secret.value) {
            return data.client_secret.value;
          }
        }
        
        // If we get here, the real endpoint failed, so try the mock endpoint
        console.log('Real endpoint failed, trying mock endpoint...');
      } catch (error) {
        console.error('Error with real endpoint:', error);
        console.log('Trying mock endpoint...');
      }
      
      // Try the mock endpoint as a fallback
      endpoint = `${this.backendUrl}/api/mock-token`;
      console.log('Fetching mock ephemeral key from:', endpoint);
      
      const mockResponse = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      if (!mockResponse.ok) {
        const errorText = await mockResponse.text();
        console.error('Failed to get mock ephemeral key:', errorText);
        throw new Error(`Failed to get ephemeral key: ${errorText}`);
      }
      
      const mockData = await mockResponse.json();
      console.log('Received mock response from backend:', mockData);
      
      if (mockData.ephemeral_key) {
        console.log('Using mock ephemeral key for testing');
        return mockData.ephemeral_key;
      } else {
        console.error('Invalid mock response format:', mockData);
        throw new Error('Invalid mock response format');
      }
    } catch (error) {
      console.error('Error getting ephemeral key:', error);
      return '';
    }
  }
}

export default new RealtimeService();
