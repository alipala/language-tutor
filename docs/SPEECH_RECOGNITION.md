# Speech Recognition System

## Overview

The Language Tutor application implements a sophisticated speech recognition and real-time conversation system using a combination of browser-based APIs and OpenAI's advanced language models. This document details how the speech recognition system works, from audio capture to AI-powered conversation.

## Architecture

The speech recognition system uses a three-part architecture:

1. **Frontend WebRTC Client**: Handles audio capture and streaming
2. **Backend Token Service**: Generates secure ephemeral tokens
3. **OpenAI Realtime API**: Processes audio and generates responses

![Speech Recognition Architecture](https://mermaid.ink/img/pako:eNp1kk1PwzAMhv9KlBOgTdCWD8EBaRKHcUBCaAeucXCTlkZLkypxQKXqf8dpt7EB4hTHz-vYsXMBZTVCCdLo1tqeNMqRsrpDOzpnVhvHfbDWOFLK9mT5HvV4Qs-VeqNgLdLGcS-mXWc6Zy2qwegmWNWh5-Aqo0nxXzIZnQXdUPCqQ8cDVnxJOOGWPPeBVhSsGvDYNzRgPXrHJzRWV6jYxRvNZnbUYzCDdp6_JHkxz_NiMZ_N8myRFdl0Oi2ydJbNF_dZnqfpJE1nWZbOkjSdp-nkUPQQNqTxsKVBu_Bwb7QO9-7JOdNQcB_-Nnr0_KAHdDxgS5Yx0ePgOvLhkXbG1-FVGzpjVVgbpTXWYUEb1NhSsGF_-CJJ4mSS7GXxKLmTJPFOEu8k0U4S7yTRThLtJHt_ACVl3Vc?type=png)

## Frontend Implementation

### Audio Capture with MediaRecorder API

```typescript
// From speaking-assessment.tsx
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];
    
    // Set up event handlers
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };
    
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const audioUrl = URL.createObjectURL(audioBlob);
      setAudioBlob(audioBlob);
      setAudioUrl(audioUrl);
      processRecording(audioBlob);
    };
    
    // Start recording
    mediaRecorder.start();
    setStatus('recording');
    setIsTimerActive(true);
  } catch (error) {
    console.error('Error accessing microphone:', error);
    setError('Could not access your microphone. Please check your browser permissions.');
  }
};
```

The application uses the browser's `MediaRecorder` API to capture audio from the user's microphone. This creates a stream of audio data that's collected in chunks and later combined into a single audio blob.

### WebRTC Implementation

```typescript
// From realtimeService.ts
private setupWebRTC(): boolean {
  try {
    // Create peer connection with STUN servers
    this.peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        // Additional STUN/TURN servers
      ]
    });
    
    // Create data channel for control messages
    this.dataChannel = this.peerConnection.createDataChannel('openai-chat');
    
    // Set up audio handling
    this.peerConnection.ontrack = (e) => {
      if (this.audioElement && e.track.kind === 'audio') {
        const stream = new MediaStream([e.track]);
        this.audioElement.srcObject = stream;
      }
    };
    
    // Handle data channel events
    this.dataChannel.onopen = () => {
      console.log('Data channel opened');
      // Send session configuration
      this.updateSession();
      // Notify connected callback
      if (this.onConnectedCallback) this.onConnectedCallback();
    };
    
    // Process incoming messages
    this.dataChannel.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as RealtimeEvent;
        if (this.onMessageCallback) this.onMessageCallback(event);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
    
    return true;
  } catch (error) {
    console.error('Error setting up WebRTC:', error);
    return false;
  }
}
```

For real-time conversation, the application establishes a WebRTC connection with:
- Peer connection to OpenAI's servers
- Data channel for control messages and text responses
- Audio track handling for the AI's voice responses

### Microphone Access and Audio Streaming

```typescript
// From realtimeService.ts
public async startMicrophone(): Promise<boolean> {
  try {
    // Request microphone access
    this.localStream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      } 
    });
    
    // Add audio tracks to peer connection
    this.localStream.getAudioTracks().forEach(track => {
      if (this.peerConnection) {
        this.peerConnection.addTrack(track, this.localStream!);
      }
    });
    
    return true;
  } catch (error) {
    console.error('Error accessing microphone:', error);
    return false;
  }
}
```

This function:
- Requests microphone access with noise suppression and echo cancellation
- Adds the audio tracks to the WebRTC peer connection
- Enables real-time streaming of the user's voice

### Connection to OpenAI

```typescript
// From realtimeService.ts
public async connect(): Promise<boolean> {
  try {
    // Set up WebRTC
    if (!this.setupWebRTC()) {
      return false;
    }
    
    // Create offer
    const offer = await this.peerConnection!.createOffer();
    await this.peerConnection!.setLocalDescription(offer);
    
    // Wait for ICE gathering to complete
    const completeOffer = await this.waitForIceComplete();
    if (!completeOffer) {
      throw new Error('Failed to gather ICE candidates');
    }
    
    // Connect to OpenAI with the ephemeral key
    const response = await fetch('https://api.openai.com/v1/audio/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.ephemeralKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        stream: true,
        sdp: completeOffer.sdp
      })
    });
    
    // Process the response
    const data = await response.json();
    const { sdp, ice_servers } = data;
    
    // Set remote description
    await this.peerConnection!.setRemoteDescription({
      type: 'answer',
      sdp
    });
    
    return true;
  } catch (error) {
    console.error('Error connecting to OpenAI:', error);
    return false;
  }
}
```

This establishes the connection to OpenAI by:
- Creating a WebRTC offer with ICE candidates
- Sending the offer to OpenAI's API with the ephemeral token
- Setting up the remote description from OpenAI's answer

### React Integration with useRealtime Hook

```typescript
// From useRealtime.ts
export function useRealtime() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  
  // Initialize the service
  const initialize = useCallback(async (language?: string, level?: string, topic?: string, userPrompt?: string, assessmentData?: any) => {
    // Store parameters for potential reconnection
    languageRef.current = language;
    levelRef.current = level;
    topicRef.current = topic;
    
    // Initialize the realtime service
    const success = await realtimeService.initialize(
      handleMessage,
      () => setIsConnected(true),
      () => setIsConnected(false),
      language,
      level,
      topic,
      userPrompt,
      assessmentData
    );
    
    setIsInitialized(success);
    return success;
  }, []);
  
  // Start conversation
  const startConversation = useCallback(async (conversationHistory?: string) => {
    // Implementation details
    // ...
  }, []);
  
  // Additional functions and state management
  // ...
  
  return {
    isConnected,
    isRecording,
    messages,
    error,
    toggleConversation,
    startConversation,
    stopConversation,
    clearError: () => setError(null),
    initialize,
    getFormattedConversationHistory
  };
}
```

This React hook:
- Manages the WebRTC connection state
- Handles messages from the language tutor
- Provides an easy-to-use interface for React components

## Backend Implementation

### Ephemeral Token Generation

```python
# From main.py (implied from code references)
@app.post("/api/token")
async def generate_token(request: TutorSessionRequest):
    try:
        # Create OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Generate ephemeral key with language tutor instructions
        response = client.beta.audio.conversations.ephemeral_keys.create(
            model="gpt-4o",
            voice="alloy",
            instructions=TUTOR_INSTRUCTIONS
        )
        
        return {"ephemeral_key": response.key}
    except Exception as e:
        # Error handling
        # ...
```

This endpoint:
- Creates a short-lived token for secure access to OpenAI
- Includes language tutor-specific instructions
- Configures the AI's voice and behavior

### Speech-to-Text Conversion

```python
# From sentence_assessment.py (referenced in speaking_assessment.py)
async def recognize_speech(audio_base64: str, language: str = "en-US") -> str:
    """Convert speech audio to text using OpenAI Whisper API"""
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file_path = temp_file.name
            # Decode base64 and write to file
            audio_data = base64.b64decode(audio_base64)
            temp_file.write(audio_data)
        
        # Create OpenAI client
        client = create_openai_client()
        
        # Map language to Whisper language code
        language_map = {
            "english": "en",
            "dutch": "nl",
            "spanish": "es",
            "german": "de",
            "french": "fr",
            "portuguese": "pt"
        }
        whisper_lang = language_map.get(language.lower(), "en")
        
        # Call Whisper API
        with open(temp_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=whisper_lang
            )
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return transcription.text
    except Exception as e:
        print(f"Error in speech recognition: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Speech recognition failed: {str(e)}"
        )
```

The backend uses OpenAI's Whisper API for high-quality speech-to-text conversion. The audio is temporarily stored, processed through the API with the appropriate language setting, and then the text is extracted.

### Language Proficiency Assessment

```python
# From speaking_assessment.py
async def evaluate_language_proficiency(text: str, language: str, duration: int = 60) -> Dict:
    """Comprehensive assessment of language proficiency based on spoken text"""
    
    # CEFR level descriptions and criteria
    cefr_levels = {
        "A1": { /* level criteria */ },
        "A2": { /* level criteria */ },
        "B1": { /* level criteria */ },
        "B2": { /* level criteria */ },
        "C1": { /* level criteria */ },
        "C2": { /* level criteria */ }
    }
    
    # Create OpenAI client
    client = create_openai_client()
    
    try:
        # Prepare the analysis prompt
        system_prompt = f"""
        You are an expert language proficiency assessor for {language}. 
        Analyze the following spoken text and provide a detailed assessment.
        """
        
        # Call OpenAI for analysis
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to analyze: {text}\nDuration of speech: {duration} seconds"}
            ],
            temperature=0.1
        )
        
        # Process and return the assessment
        # ...
    except Exception as e:
        # Fallback handling
        # ...
```

After transcription, the text is analyzed using OpenAI's GPT-4o model to assess language proficiency. The system evaluates pronunciation, grammar, vocabulary, fluency, and coherence, then determines a CEFR level (A1-C2) with detailed feedback.

## Real-time Conversation System

### Language Tutor Configuration

```typescript
// From realtimeService.ts
public startConversation(instructions?: string): Promise<boolean> {
  return new Promise((resolve, reject) => {
    try {
      // Prepare conversation parameters
      const conversationConfig = {
        temperature: 0.7,
        max_tokens: 1000,
        tools: [],
        tool_choice: "auto"
      };
      
      // Add custom instructions if provided
      if (instructions) {
        conversationConfig.system_prompt = instructions;
      }
      
      // Create conversation message
      const message: RealtimeResponseCreateEvent = {
        type: "response.create",
        data: conversationConfig
      };
      
      // Send message through data channel
      if (this.sendMessage(message)) {
        resolve(true);
      } else {
        reject(new Error('Failed to send conversation start message'));
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      reject(error);
    }
  });
}
```

This function:
- Configures the language tutor parameters
- Adds custom instructions for conversation context
- Sends the configuration through the WebRTC data channel

### Real-time Transcription Configuration

```typescript
// From realtimeService.ts
private updateSession(): boolean {
  try {
    // Configure transcription with the correct language
    const message = {
      type: "session.update",
      data: {
        transcription: {
          enabled: true,
          language: this.currentLanguageIsoCode || "en",
          model: "whisper-1"
        }
      }
    };
    
    // Send configuration through data channel
    return this.sendMessage(message);
  } catch (error) {
    console.error('Error updating session:', error);
    return false;
  }
}
```

This configures real-time transcription with:
- Language-specific settings based on the user's selected language
- OpenAI's Whisper model for accurate transcription
- Automatic language detection when needed

## Key Features

### 1. Multi-language Support

The system supports multiple languages with appropriate language codes:

```typescript
// From realtimeService.ts
public getLanguageIsoCode(language: string): string {
  // Convert language name to ISO-639-1 code
  const languageMap = {
    "english": "en",
    "dutch": "nl",
    "spanish": "es",
    "german": "de",
    "french": "fr",
    "portuguese": "pt",
    // Additional languages...
  };
  
  return languageMap[language.toLowerCase()] || "en";
}
```

### 2. Secure Token Management

```typescript
// From realtimeService.ts
public async getEphemeralKey(language?: string, level?: string, topic?: string, userPrompt?: string, assessmentData?: any): Promise<string> {
  try {
    // Prepare request body
    const requestBody = {
      language: language || 'english',
      level: level || 'intermediate',
      topic: topic || 'general',
      user_prompt: userPrompt,
      assessment_data: assessmentData
    };
    
    // Determine endpoint
    const endpoint = `${this.backendUrl}/api/token`;
    
    // Fetch token from backend
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
      credentials: 'same-origin',
    });
    
    // Process response
    if (response.ok) {
      const data = await response.json();
      return data.ephemeral_key;
    } else {
      // Error handling and fallback to mock token
      // ...
    }
  } catch (error) {
    console.error('Error getting ephemeral key:', error);
    return '';
  }
}
```

This function:
- Requests a short-lived token from your backend
- Includes language, level, and topic parameters
- Handles errors with fallback to a mock token for testing

### 3. Error Handling and Reliability

```typescript
// From realtimeService.ts
public async connect(): Promise<boolean> {
  try {
    // Connection logic...
  } catch (error) {
    console.error('Error connecting to OpenAI:', error);
    
    // Retry logic
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Retrying connection (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 1000 * this.reconnectAttempts));
      return this.connect();
    }
    
    return false;
  }
}
```

The system implements robust error handling:
- Connection retry mechanisms
- Fallback to mock tokens for testing
- Comprehensive error reporting

## Performance Considerations

### Audio Quality

The system optimizes audio quality with:

```typescript
// Request microphone access with audio processing options
this.localStream = await navigator.mediaDevices.getUserMedia({ 
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
  } 
});
```

These settings improve the quality of the audio for better transcription accuracy.

### Latency Optimization

To minimize latency, the system:

1. Uses WebRTC for low-latency audio streaming
2. Implements efficient data channel communication
3. Processes audio in real-time with streaming responses
4. Uses connection timeouts to prevent hanging operations

### Memory Management

The system implements proper resource cleanup:

```typescript
// From realtimeService.ts
public disconnect(): void {
  try {
    console.log('Disconnecting from OpenAI...');
    
    // Stop all tracks in the local stream
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
    
    // Close data channel
    if (this.dataChannel) {
      this.dataChannel.close();
      this.dataChannel = null;
    }
    
    // Close peer connection
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }
    
    // Clear audio element
    if (this.audioElement) {
      this.audioElement.srcObject = null;
    }
    
    // Reset state
    this.isConnected = false;
    
    // Notify disconnected callback
    if (this.onDisconnectedCallback) {
      this.onDisconnectedCallback();
    }
    
    console.log('Disconnected from OpenAI');
  } catch (error) {
    console.error('Error disconnecting:', error);
  }
}
```

This ensures that all resources are properly released when the conversation ends.

## Security Considerations

1. **Ephemeral Tokens**: Short-lived tokens for secure access to OpenAI
2. **Backend-managed API Keys**: API keys never exposed to the client
3. **Secure WebRTC Connection**: DTLS encryption for audio streaming
4. **HTTPS Requirement**: All communication over secure connections
5. **User Permission**: Explicit microphone permission requests

## Browser Compatibility

The speech recognition system is compatible with modern browsers that support:

- WebRTC (getUserMedia, RTCPeerConnection, RTCDataChannel)
- MediaRecorder API
- Web Audio API

This includes:
- Chrome 55+
- Firefox 44+
- Safari 11+
- Edge 79+

For older browsers, the application could implement a fallback to a text-only interface.
