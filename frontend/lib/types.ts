// WebRTC and Realtime API Types
export interface RealtimeMessage {
  role: 'user' | 'assistant';
  content: string;
  itemId?: string; // Optional ID to track which conversation item this message belongs to
  timestamp?: string; // ISO string timestamp for message ordering
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

export interface RealtimeConversationItemCreatedEvent extends RealtimeEvent {
  type: 'conversation.item.created';
  item: {
    role: 'user' | 'assistant';
    input?: {
      content: {
        text: string;
      };
    };
    content?: Array<{
      type: string;
      transcript?: string;
      [key: string]: any;
    }>;
  };
}

export interface RealtimeAudioTranscriptDeltaEvent extends RealtimeEvent {
  type: 'response.audio_transcript.delta';
  delta: {
    text: string;
  };
}
