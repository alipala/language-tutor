import { GrammarIssue, AssessmentResult } from '@/components/sentence-construction-assessment';

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

export interface SentenceAssessmentRequest {
  audio_base64?: string;
  transcript?: string;
  language: string;
  level: string;
  exercise_type: string;
  target_grammar?: string[];
  context?: string;
}

// Function to fetch assessment from the backend
export const assessSentence = async (
  audioBlob: Blob,
  language: string,
  level: string,
  exerciseType: string = 'free',
  targetGrammar?: string[],
  transcript?: string
): Promise<AssessmentResult> => {
  try {
    // Prepare the request body
    const requestBody: SentenceAssessmentRequest = {
      language,
      level,
      exercise_type: exerciseType,
      target_grammar: targetGrammar,
      transcript: transcript // Include the transcript
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
    
    // Get the API URL from environment or default to localhost
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Make the API request
    const response = await fetch(`${apiUrl}/api/sentence/assess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Error assessing sentence: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    return data as AssessmentResult;
  } catch (error) {
    console.error('Error in sentence assessment:', error);
    throw error;
  }
};

export interface ExerciseRequest {
  language: string;
  level: string;
  exercise_type: string;
  target_grammar?: string[];
}

export interface Exercise {
  prompt: string;
  example?: string;
  notes?: string;
}

export interface ExerciseResponse {
  exercises: Exercise[];
}

// Function to fetch exercises from the backend
export const fetchExercises = async (
  language: string,
  level: string,
  exerciseType: string = 'free',
  targetGrammar?: string[]
): Promise<ExerciseResponse> => {
  try {
    // Prepare the request body
    const requestBody: ExerciseRequest = {
      language,
      level,
      exercise_type: exerciseType,
      target_grammar: targetGrammar
    };
    
    // Get the API URL from environment or default to localhost
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Make the API request
    const response = await fetch(`${apiUrl}/api/sentence/exercises`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Error fetching exercises: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    return data as ExerciseResponse;
  } catch (error) {
    console.error('Error fetching exercises:', error);
    throw error;
  }
};
