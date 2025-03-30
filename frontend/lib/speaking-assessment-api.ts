import { getApiUrl } from './api-utils';

// Types for speaking assessment
export interface SkillScore {
  score: number;
  feedback: string;
  examples: string[];
}

export interface SpeakingAssessmentResult {
  recognized_text: string;
  recommended_level: string;
  overall_score: number;
  confidence: number;
  pronunciation: SkillScore;
  grammar: SkillScore;
  vocabulary: SkillScore;
  fluency: SkillScore;
  coherence: SkillScore;
  strengths: string[];
  areas_for_improvement: string[];
  next_steps: string[];
}

export interface SpeakingAssessmentRequest {
  audio_base64?: string;
  transcript?: string;
  language: string;
  duration?: number;
  prompt?: string;
}

export interface SpeakingPrompt {
  general: string[];
  travel: string[];
  education: string[];
  [key: string]: string[];
}

// Function to encode audio data as base64
export const encodeAudioData = (audioBlob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      // Extract the base64 data from the result
      const base64data = reader.result?.toString().split(',')[1];
      if (base64data) {
        resolve(base64data);
      } else {
        reject(new Error('Failed to encode audio as base64'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(audioBlob);
  });
};

// Function to fetch speaking assessment from the backend
export const assessSpeaking = async (
  audioBlob: Blob,
  language: string,
  duration: number,
  prompt?: string,
  transcript?: string
): Promise<SpeakingAssessmentResult> => {
  try {
    // Prepare the request body
    const requestBody: SpeakingAssessmentRequest = {
      language,
      duration,
      prompt,
      transcript
    };
    
    // Only encode and include audio if the blob has content
    if (audioBlob.size > 0) {
      try {
        const audioBase64 = await encodeAudioData(audioBlob);
        requestBody.audio_base64 = audioBase64;
      } catch (error) {
        console.warn('Failed to encode audio, will rely on transcript:', error);
      }
    }
    
    // Get the API URL
    const apiUrl = getApiUrl();
    
    // Make the API request
    const response = await fetch(`${apiUrl}/api/assessment/speaking`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Error assessing speaking: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    return data as SpeakingAssessmentResult;
  } catch (error) {
    console.error('Error in speaking assessment:', error);
    throw error;
  }
};

// Default speaking prompts to use as fallback
const DEFAULT_PROMPTS: SpeakingPrompt = {
  general: [
    'Tell me about yourself and your language learning experience.',
    'Describe your hometown and what you like about it.',
    'What are your hobbies and interests?',
    'Talk about your favorite book, movie, or TV show.',
    'Describe your typical day.'
  ],
  travel: [
    'Describe a memorable trip you\'ve taken.',
    'What\'s your favorite place to visit and why?',
    'Talk about a place you would like to visit in the future.',
    'Describe your ideal vacation.',
    'What do you usually do when you travel?'
  ],
  education: [
    'Talk about your educational background.',
    'Describe a teacher who influenced you.',
    'What subjects did you enjoy studying?',
    'How do you think education has changed in recent years?',
    'Describe your learning style.'
  ]
};

// Function to fetch speaking prompts from the backend
export const fetchSpeakingPrompts = async (
  language: string
): Promise<SpeakingPrompt> => {
  try {
    // Get the API URL
    const apiUrl = getApiUrl();
    
    // Try both endpoints in sequence with a timeout
    const fetchWithTimeout = async (url: string, options: RequestInit, timeout: number) => {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeout);
      
      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal
        });
        clearTimeout(id);
        return response;
      } catch (error) {
        clearTimeout(id);
        throw error;
      }
    };
    
    // Try the first endpoint
    try {
      const response = await fetchWithTimeout(
        `${apiUrl}/api/speaking-prompts?language=${encodeURIComponent(language)}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        },
        3000 // 3 second timeout
      );
      
      if (response.ok) {
        const data = await response.json();
        return data.prompts as SpeakingPrompt;
      }
    } catch (error) {
      console.warn('First endpoint failed or timed out:', error);
    }
    
    // Try the second endpoint
    try {
      const response = await fetchWithTimeout(
        `${apiUrl}/api/assessment/speaking/prompts?language=${encodeURIComponent(language)}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        },
        3000 // 3 second timeout
      );
      
      if (response.ok) {
        const data = await response.json();
        return data.prompts as SpeakingPrompt;
      }
    } catch (error) {
      console.warn('Second endpoint failed or timed out:', error);
    }
    
    // If both endpoints fail, use default prompts
    console.log('Using default prompts as fallback');
    return DEFAULT_PROMPTS;
  } catch (error) {
    console.error('Error fetching speaking prompts:', error);
    // Return default prompts instead of throwing
    return DEFAULT_PROMPTS;
  }
};
