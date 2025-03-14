// WebRTC and Realtime API Types
export interface RealtimeMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface RealtimeEvent {
  type: string;
  [key: string]: any;
}

export interface RealtimeTextDeltaEvent extends RealtimeEvent {
  type: 'response.text.delta';
  delta: {
    text: string;
  };
}

export interface RealtimeAudioTranscriptionEvent extends RealtimeEvent {
  type: 'conversation.item.input_audio_transcription.completed';
  transcription: {
    text: string;
  };
}

export interface RealtimeResponseCreateEvent extends RealtimeEvent {
  type: 'response.create';
  response: {
    modalities: string[];
    instructions?: string;
  };
}
